# -*- coding: utf-8 -*-
"""
Gemini API Client for job analysis.
Supports rate limiting, retry logic, and cost tracking.
"""

import time
import json
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False
    print("[WARNING] google-generativeai not available. Install with: pip install google-generativeai")


@dataclass
class TokenUsage:
    """Track token usage for cost estimation."""
    input_tokens: int = 0
    output_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def add(self, input_tokens: int, output_tokens: int):
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens

    def estimate_cost(
        self,
        input_price_per_million: float = 0.01875,
        output_price_per_million: float = 0.075,
    ) -> float:
        """Estimate cost in USD based on Gemini 2.0 Flash pricing."""
        input_cost = (self.input_tokens / 1_000_000) * input_price_per_million
        output_cost = (self.output_tokens / 1_000_000) * output_price_per_million
        return input_cost + output_cost


class RateLimiter:
    """Simple rate limiter with sliding window."""

    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.request_times: List[float] = []

    def wait_if_needed(self):
        """Wait if rate limit would be exceeded."""
        now = time.time()
        window_start = now - 60

        # Remove old requests outside the window
        self.request_times = [t for t in self.request_times if t > window_start]

        # Check if we need to wait
        if len(self.request_times) >= self.requests_per_minute:
            # Wait until oldest request exits the window
            wait_time = self.request_times[0] - window_start + 0.1
            if wait_time > 0:
                time.sleep(wait_time)

        # Record this request
        self.request_times.append(time.time())


class GeminiClient:
    """Gemini API client with rate limiting and cost tracking."""

    # Default model
    DEFAULT_MODEL = "gemini-2.0-flash-exp"

    # Retry settings
    MAX_RETRIES = 3
    BASE_RETRY_DELAY = 2.0

    def __init__(
        self,
        api_key: str,
        model: str = None,
        rate_limit_per_minute: int = 60,
        daily_limit: int = 1000,
    ):
        """
        Initialize Gemini client.

        Args:
            api_key: Gemini API key
            model: Model name (default: gemini-2.0-flash-exp)
            rate_limit_per_minute: Maximum requests per minute
            daily_limit: Maximum requests per day
        """
        if not HAS_GENAI:
            raise ImportError(
                "google-generativeai not available. "
                "Install with: pip install google-generativeai"
            )

        self.model_name = model or self.DEFAULT_MODEL
        self.daily_limit = daily_limit

        # Configure API
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(self.model_name)

        # Rate limiting
        self.rate_limiter = RateLimiter(rate_limit_per_minute)

        # Usage tracking
        self.token_usage = TokenUsage()
        self.request_count = 0
        self._daily_count = 0
        self._daily_reset_time = time.time()

    def _check_daily_limit(self) -> bool:
        """Check and reset daily limit if needed."""
        now = time.time()
        # Reset daily count after 24 hours
        if now - self._daily_reset_time > 86400:
            self._daily_count = 0
            self._daily_reset_time = now

        return self._daily_count < self.daily_limit

    def analyze(
        self,
        prompt: str,
        job_data: Dict[str, Any],
        timeout: float = 30.0,
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze a job using the provided prompt.

        Args:
            prompt: The prompt template with {placeholders}
            job_data: Job data dictionary to fill placeholders
            timeout: Request timeout in seconds

        Returns:
            Parsed response as dictionary, or None on failure
        """
        if not self._check_daily_limit():
            print(f"[GeminiClient] Daily limit reached ({self.daily_limit})")
            return None

        # Format prompt with job data
        try:
            formatted_prompt = prompt.format(**job_data)
        except KeyError as e:
            print(f"[GeminiClient] Prompt formatting error: missing key {e}")
            return None

        # Rate limiting
        self.rate_limiter.wait_if_needed()

        # Retry loop
        for attempt in range(self.MAX_RETRIES):
            try:
                response = self.model.generate_content(
                    formatted_prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.3,
                        max_output_tokens=1024,
                    ),
                )

                # Update counters
                self.request_count += 1
                self._daily_count += 1

                # Track token usage if available
                if hasattr(response, 'usage_metadata'):
                    usage = response.usage_metadata
                    self.token_usage.add(
                        input_tokens=getattr(usage, 'prompt_token_count', 0),
                        output_tokens=getattr(usage, 'candidates_token_count', 0),
                    )

                # Parse response
                if response.text:
                    return self._parse_response(response.text)
                else:
                    return None

            except Exception as e:
                error_msg = str(e)

                # Rate limit error - wait and retry
                if "429" in error_msg or "quota" in error_msg.lower():
                    delay = self.BASE_RETRY_DELAY * (2 ** attempt)
                    print(f"[GeminiClient] Rate limited, waiting {delay:.1f}s...")
                    time.sleep(delay)
                    continue

                # Other errors
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.BASE_RETRY_DELAY)
                    continue

                print(f"[GeminiClient] Error: {error_msg[:100]}")
                return None

        return None

    def _parse_response(self, text: str) -> Dict[str, Any]:
        """
        Parse response text to extract structured data.

        Attempts to find and parse JSON from the response.
        """
        # Try to find JSON in response
        text = text.strip()

        # Try direct JSON parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try to find JSON block in markdown
        json_patterns = [
            r'```json\s*([\s\S]*?)\s*```',
            r'```\s*([\s\S]*?)\s*```',
            r'\{[\s\S]*\}',
        ]

        import re
        for pattern in json_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    json_str = match.group(1) if '```' in pattern else match.group(0)
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    continue

        # Return raw text as fallback
        return {"raw_response": text}

    def analyze_batch(
        self,
        prompt: str,
        jobs: List[Dict[str, Any]],
        progress_callback=None,
    ) -> List[Optional[Dict[str, Any]]]:
        """
        Analyze multiple jobs.

        Args:
            prompt: The prompt template
            jobs: List of job data dictionaries
            progress_callback: Optional callback(current, total)

        Returns:
            List of analysis results
        """
        results = []
        total = len(jobs)

        for i, job in enumerate(jobs):
            result = self.analyze(prompt, job)
            results.append(result)

            if progress_callback:
                progress_callback(i + 1, total)

        return results

    @property
    def stats(self) -> Dict[str, Any]:
        """Get client statistics."""
        return {
            "model": self.model_name,
            "request_count": self.request_count,
            "daily_count": self._daily_count,
            "daily_limit": self.daily_limit,
            "input_tokens": self.token_usage.input_tokens,
            "output_tokens": self.token_usage.output_tokens,
            "estimated_cost_usd": self.token_usage.estimate_cost(),
        }

    def print_stats(self):
        """Print usage statistics."""
        stats = self.stats
        print("\n" + "=" * 40)
        print("Gemini API Usage Statistics")
        print("=" * 40)
        print(f"  Model: {stats['model']}")
        print(f"  Requests: {stats['request_count']}")
        print(f"  Daily usage: {stats['daily_count']}/{stats['daily_limit']}")
        print(f"  Input tokens: {stats['input_tokens']:,}")
        print(f"  Output tokens: {stats['output_tokens']:,}")
        print(f"  Estimated cost: ${stats['estimated_cost_usd']:.4f}")
        print("=" * 40)
