# -*- coding: utf-8 -*-
"""
Unified JobSpy Scraper for LinkedIn and Indeed.
Provides single interface for scraping both platforms with deduplication.
"""

import time
import re
from typing import List, Optional, Dict, Any, Set
from datetime import datetime
import pandas as pd

try:
    from jobspy import scrape_jobs
    HAS_JOBSPY = True
except ImportError:
    HAS_JOBSPY = False
    print("[WARNING] JobSpy not available. Install with: pip install python-jobspy")

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.job_data import JobData, JobDataCollection
from core.salary_processor import SalaryProcessor
from core.currency_converter import CurrencyConverter


class JobSpyScraper:
    """Unified scraper for LinkedIn and Indeed using JobSpy."""

    # Core AI keywords (high relevance)
    CORE_AI_KEYWORDS = [
        "ai engineer", "machine learning", "deep learning", "ml engineer", "dl engineer",
        "nlp engineer", "natural language processing", "data scientist",
        "computer vision", "cv engineer", "neural network", "tensorflow", "pytorch",
        "artificial intelligence", "ai/ml", "ml/ai", "ai model", "ml model",
        "generative ai", "genai", "llm", "large language model", "transformer",
        "reinforcement learning", "rl engineer", "ai research", "ml research"
    ]

    # AI-related keywords (medium relevance)
    AI_RELATED_KEYWORDS = [
        "ai sales", "ai product", "ai architect", "ai designer", "ai ops", "mlops",
        "ai infrastructure", "ai platform", "ai system", "ai solution",
        "conversational ai", "chatbot", "ai assistant", "ai voice",
        "ai training", "ai data", "ai governance", "ai ethics", "responsible ai",
        "ai hardware", "ai chip", "ai accelerator", "ai processor",
        "robotics", "autonomous", "rpa", "robotic process automation",
        "data annotation", "data labeling", "data curation"
    ]

    # Negative keywords (likely not AI-related)
    NEGATIVE_KEYWORDS = [
        "sales representative", "sales manager", "account manager", "business development",
        "customer service", "call center", "telemarketing", "retail sales",
        "warehouse", "logistics", "shipping", "delivery driver",
        "restaurant", "food service", "hospitality", "cleaning", "janitor"
    ]

    # Region to country code mapping for Indeed
    REGION_COUNTRY_MAP = {
        "United States": "usa",
        "United Kingdom": "uk",
        "Australia": "australia",
        "Singapore": "singapore",
        "Hong Kong": "hong kong",
        "Canada": "canada",
    }

    def __init__(
        self,
        platforms: List[str] = None,
        request_delay: float = 0.5,
        results_per_search: int = 100,
        retry_attempts: int = 3,
        retry_delay: float = 2.0,
    ):
        """
        Initialize JobSpy scraper.

        Args:
            platforms: List of platforms to scrape ["linkedin", "indeed"]
            request_delay: Delay between requests in seconds
            results_per_search: Number of results to request per search
            retry_attempts: Number of retry attempts on failure
            retry_delay: Base delay for exponential backoff
        """
        self.platforms = platforms or ["linkedin", "indeed"]
        self.request_delay = request_delay
        self.results_per_search = results_per_search
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay

        # Initialize processors
        self.currency_converter = CurrencyConverter()
        self.salary_processor = SalaryProcessor(self.currency_converter)

        # Tracking
        self._total_requests = 0
        self._successful_requests = 0
        self._failed_requests = 0

    def scrape(
        self,
        keywords: List[str],
        locations: List[str],
        region_name: str = "United States",
        min_posted_date: Optional[datetime] = None,
        filter_ai_related: bool = True,
        max_total_jobs: Optional[int] = None,
        verbose: bool = True,
    ) -> JobDataCollection:
        """
        Scrape jobs from configured platforms.

        Args:
            keywords: List of search keywords
            locations: List of locations to search
            region_name: Region name for currency detection
            min_posted_date: Filter jobs posted on or after this date
            filter_ai_related: If True, filter to only AI-related jobs
            max_total_jobs: Maximum total jobs to collect
            verbose: Print progress information

        Returns:
            JobDataCollection with scraped jobs
        """
        if not HAS_JOBSPY:
            raise ImportError("JobSpy not available. Install with: pip install python-jobspy")

        collection = JobDataCollection()
        seen_keys: Set[str] = set()

        if verbose:
            print("=" * 60)
            print(f"JobSpy Unified Scraper - {region_name}")
            print("=" * 60)
            print(f"  Platforms: {', '.join([p.upper() for p in self.platforms])}")
            print(f"  Keywords: {len(keywords)}")
            print(f"  Locations: {len(locations)}")
            print(f"  Results per search: {self.results_per_search}")
            if min_posted_date:
                print(f"  Date filter: >= {min_posted_date.strftime('%Y-%m-%d')}")
            if filter_ai_related:
                print(f"  AI filter: Enabled")
            print()

        # Initialize exchange rates
        self.currency_converter.initialize()

        total_combinations = len(keywords) * len(locations) * len(self.platforms)
        current_combo = 0

        for keyword in keywords:
            if max_total_jobs and len(collection) >= max_total_jobs:
                break

            for location in locations:
                if max_total_jobs and len(collection) >= max_total_jobs:
                    break

                for platform in self.platforms:
                    if max_total_jobs and len(collection) >= max_total_jobs:
                        break

                    current_combo += 1
                    self._total_requests += 1

                    if verbose:
                        progress = f"[{current_combo}/{total_combinations}]"
                        print(f"{progress} {platform.upper()}: '{keyword}' in '{location}'...", end=" ")

                    # Scrape with retry
                    jobs = self._scrape_with_retry(
                        keyword=keyword,
                        location=location,
                        platform=platform,
                        region_name=region_name,
                    )

                    if jobs is None:
                        self._failed_requests += 1
                        if verbose:
                            print("[FAILED]")
                        continue

                    self._successful_requests += 1

                    # Process jobs
                    new_count = 0
                    for job_dict in jobs:
                        # Convert to JobData
                        job = JobData.from_jobspy_dict(job_dict, platform)

                        # Deduplicate
                        if job._dedup_key in seen_keys:
                            continue
                        seen_keys.add(job._dedup_key)

                        # Date filter
                        if min_posted_date and job.posted_date:
                            if job.posted_date < min_posted_date:
                                continue

                        # AI relevance filter
                        if filter_ai_related:
                            if not self._is_ai_related(job):
                                continue

                        # Process salary
                        self._process_salary(job, region_name)

                        # Extract requirements
                        job.requirements = self.salary_processor.extract_requirements(job.description)

                        # Add to collection
                        if collection.add(job, deduplicate=False):  # Already deduped above
                            new_count += 1

                    if verbose:
                        print(f"[OK] {len(jobs)} found, {new_count} new (total: {len(collection)})")

                    # Delay between requests
                    time.sleep(self.request_delay)

        if verbose:
            print()
            print("=" * 60)
            print("Scraping Summary")
            print("=" * 60)
            print(f"  Total requests: {self._total_requests}")
            print(f"  Successful: {self._successful_requests}")
            print(f"  Failed: {self._failed_requests}")
            print(f"  Total unique jobs: {len(collection)}")
            print("=" * 60)

        return collection

    def _scrape_with_retry(
        self,
        keyword: str,
        location: str,
        platform: str,
        region_name: str,
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Scrape with exponential backoff retry.

        Returns:
            List of job dictionaries or None on failure
        """
        country_code = self.REGION_COUNTRY_MAP.get(region_name, "usa")

        for attempt in range(self.retry_attempts):
            try:
                # Prepare parameters
                params = {
                    "site_name": platform,
                    "search_term": keyword,
                    "location": location,
                    "results_wanted": self.results_per_search,
                }

                # Add platform-specific parameters
                if platform == "indeed":
                    params["country_indeed"] = country_code
                elif platform == "linkedin":
                    # 必须设置此参数才能获取LinkedIn的job description
                    params["linkedin_fetch_description"] = True

                # Execute scrape
                result = scrape_jobs(**params)

                if isinstance(result, pd.DataFrame) and not result.empty:
                    return result.to_dict('records')
                else:
                    return []

            except Exception as e:
                error_msg = str(e)

                # Check for rate limiting (429 error)
                if "429" in error_msg or "rate" in error_msg.lower():
                    delay = self.retry_delay * (2 ** attempt)
                    if attempt < self.retry_attempts - 1:
                        print(f"[RATE LIMITED] Waiting {delay:.1f}s...", end=" ")
                        time.sleep(delay)
                        continue

                # Other errors
                if attempt < self.retry_attempts - 1:
                    time.sleep(self.retry_delay)
                    continue

                # Final failure
                return None

        return None

    def _is_ai_related(self, job: JobData) -> bool:
        """Check if job is AI-related."""
        title = job.title.lower()
        description = job.description.lower()

        # Check for negative keywords in title
        for neg_kw in self.NEGATIVE_KEYWORDS:
            if neg_kw in title:
                if not any(ai_kw in title for ai_kw in self.CORE_AI_KEYWORDS + self.AI_RELATED_KEYWORDS):
                    return False

        # Check title for core AI keywords
        if any(kw in title for kw in self.CORE_AI_KEYWORDS):
            return True

        # Check description for core AI keywords
        if any(kw in description for kw in self.CORE_AI_KEYWORDS):
            return True

        # Check for AI-related keywords in title with description confirmation
        if any(kw in title for kw in self.AI_RELATED_KEYWORDS):
            if any(kw in description for kw in self.AI_RELATED_KEYWORDS):
                return True

        return False

    def _process_salary(self, job: JobData, region_name: str):
        """Process and normalize salary for a job."""
        # Try structured salary first
        if job.min_amount is not None:
            result = self.salary_processor.process_structured_salary(
                min_amount=job.min_amount,
                max_amount=job.max_amount,
                currency=job.currency,
                interval=job.interval,
            )
        else:
            # Extract from description
            result = self.salary_processor.extract_from_description(
                description=job.description,
                region_name=region_name,
            )

        # Update job with processed salary
        if result['estimated_annual']:
            job.salary_range = result['salary_range']
            job.estimated_annual = result['estimated_annual']
            job.estimated_annual_usd = result['estimated_annual_usd']
            job.currency = result['currency']

    def deduplicate_cross_platform(
        self,
        indeed_jobs: JobDataCollection,
        linkedin_jobs: JobDataCollection,
    ) -> JobDataCollection:
        """
        Deduplicate jobs across platforms (Indeed takes priority).

        Args:
            indeed_jobs: JobDataCollection from Indeed
            linkedin_jobs: JobDataCollection from LinkedIn

        Returns:
            Combined and deduplicated JobDataCollection
        """
        combined = JobDataCollection()

        # Add all Indeed jobs first
        for job in indeed_jobs:
            combined.add(job)

        # Add LinkedIn jobs that aren't duplicates
        linkedin_added = 0
        linkedin_skipped = 0
        for job in linkedin_jobs:
            if not combined.is_cross_platform_duplicate(job):
                combined.add(job)
                linkedin_added += 1
            else:
                linkedin_skipped += 1

        print(f"Cross-platform deduplication:")
        print(f"  Indeed jobs: {len(indeed_jobs)}")
        print(f"  LinkedIn added: {linkedin_added}")
        print(f"  LinkedIn duplicates skipped: {linkedin_skipped}")
        print(f"  Total unique: {len(combined)}")

        return combined

    @property
    def stats(self) -> Dict[str, int]:
        """Get scraping statistics."""
        return {
            "total_requests": self._total_requests,
            "successful_requests": self._successful_requests,
            "failed_requests": self._failed_requests,
        }
