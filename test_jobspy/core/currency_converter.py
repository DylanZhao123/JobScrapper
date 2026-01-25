# -*- coding: utf-8 -*-
"""
Currency Converter with real-time exchange rate API support.
Uses exchangerate-api.com (free tier) with local caching.
"""

import time
import json
import os
from typing import Dict, Optional
from pathlib import Path

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class CurrencyConverter:
    """Currency converter with real-time exchange rates and caching."""

    # Default cache duration: 1 hour
    CACHE_DURATION = 3600

    # Fallback exchange rates (used when API is unavailable)
    FALLBACK_RATES = {
        'USD': 1.0,
        'GBP': 1.27,   # 1 GBP = 1.27 USD
        'AUD': 0.67,   # 1 AUD = 0.67 USD
        'SGD': 0.74,   # 1 SGD = 0.74 USD
        'HKD': 0.13,   # 1 HKD = 0.13 USD
        'EUR': 1.09,   # 1 EUR = 1.09 USD
        'CAD': 0.73,   # 1 CAD = 0.73 USD
        'JPY': 0.0067, # 1 JPY = 0.0067 USD
        'CNY': 0.14,   # 1 CNY = 0.14 USD
        'INR': 0.012,  # 1 INR = 0.012 USD
    }

    # Currency code aliases
    CURRENCY_ALIASES = {
        'US$': 'USD', '$': 'USD',
        'GB£': 'GBP', '£': 'GBP',
        'A$': 'AUD', 'AU$': 'AUD',
        'S$': 'SGD', 'SG$': 'SGD',
        'HK$': 'HKD',
        '€': 'EUR', 'EU€': 'EUR',
        'C$': 'CAD', 'CA$': 'CAD',
        '¥': 'JPY', 'JP¥': 'JPY',
        '¥': 'CNY', 'CN¥': 'CNY',  # Ambiguous, defaults to CNY in context
        '₹': 'INR',
    }

    def __init__(
        self,
        cache_file: Optional[str] = None,
        cache_duration: int = CACHE_DURATION,
        auto_initialize: bool = True,
    ):
        """
        Initialize currency converter.

        Args:
            cache_file: Path to cache file (optional)
            cache_duration: Cache duration in seconds
            auto_initialize: If True, fetch rates immediately
        """
        self.cache_duration = cache_duration
        self.cache_file = cache_file or self._get_default_cache_path()
        self._rates: Dict[str, float] = {}
        self._cache_time: Optional[float] = None
        self._using_fallback = False

        if auto_initialize:
            self.initialize()

    def _get_default_cache_path(self) -> str:
        """Get default cache file path."""
        # Store in test_jobspy/output directory
        cache_dir = Path(__file__).parent.parent / "output"
        cache_dir.mkdir(parents=True, exist_ok=True)
        return str(cache_dir / "exchange_rates_cache.json")

    def initialize(self) -> bool:
        """
        Initialize exchange rates.

        Returns:
            True if real-time rates were fetched, False if using fallback
        """
        # Try to load from cache first
        if self._load_from_cache():
            print(f"[CurrencyConverter] Loaded rates from cache (age: {self._get_cache_age():.0f}s)")
            return not self._using_fallback

        # Fetch from API
        print("[CurrencyConverter] Fetching real-time exchange rates...")
        if self._fetch_from_api():
            self._save_to_cache()
            return True

        # Fall back to default rates
        print("[CurrencyConverter] Using fallback exchange rates")
        self._rates = self.FALLBACK_RATES.copy()
        self._cache_time = time.time()
        self._using_fallback = True
        return False

    def _fetch_from_api(self) -> bool:
        """
        Fetch exchange rates from API.

        Returns:
            True if successful
        """
        if not HAS_REQUESTS:
            print("[CurrencyConverter] requests library not available")
            return False

        try:
            # Using exchangerate-api.com free endpoint (no API key required)
            url = "https://api.exchangerate-api.com/v4/latest/USD"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            if 'rates' not in data:
                print("[CurrencyConverter] Invalid API response format")
                return False

            # API returns: 1 USD = X currency
            # We need: 1 currency = X USD
            self._rates = {'USD': 1.0}
            for currency, rate in data['rates'].items():
                if rate > 0:
                    self._rates[currency] = 1.0 / rate

            self._cache_time = time.time()
            self._using_fallback = False
            print(f"[CurrencyConverter] Fetched {len(self._rates)} exchange rates from API")
            return True

        except requests.exceptions.RequestException as e:
            print(f"[CurrencyConverter] API request failed: {str(e)[:50]}")
            return False
        except Exception as e:
            print(f"[CurrencyConverter] Error: {str(e)[:50]}")
            return False

    def _load_from_cache(self) -> bool:
        """
        Load rates from cache file if valid.

        Returns:
            True if cache was loaded and is still valid
        """
        if not os.path.exists(self.cache_file):
            return False

        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)

            cache_time = cache_data.get('timestamp', 0)
            rates = cache_data.get('rates', {})

            # Check if cache is still valid
            if time.time() - cache_time < self.cache_duration and rates:
                self._rates = rates
                self._cache_time = cache_time
                self._using_fallback = cache_data.get('is_fallback', False)
                return True

        except Exception as e:
            print(f"[CurrencyConverter] Cache load error: {str(e)[:50]}")

        return False

    def _save_to_cache(self) -> bool:
        """
        Save rates to cache file.

        Returns:
            True if successful
        """
        try:
            cache_data = {
                'timestamp': self._cache_time,
                'rates': self._rates,
                'is_fallback': self._using_fallback,
            }
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2)
            return True
        except Exception as e:
            print(f"[CurrencyConverter] Cache save error: {str(e)[:50]}")
            return False

    def _get_cache_age(self) -> float:
        """Get cache age in seconds."""
        if self._cache_time is None:
            return float('inf')
        return time.time() - self._cache_time

    def _normalize_currency(self, currency: str) -> str:
        """Normalize currency code."""
        currency = str(currency).upper().strip()
        return self.CURRENCY_ALIASES.get(currency, currency)

    def get_rate(self, from_currency: str, to_currency: str = "USD") -> float:
        """
        Get exchange rate from one currency to another.

        Args:
            from_currency: Source currency code
            to_currency: Target currency code (default: USD)

        Returns:
            Exchange rate (1 from_currency = X to_currency)
        """
        from_curr = self._normalize_currency(from_currency)
        to_curr = self._normalize_currency(to_currency)

        if from_curr == to_curr:
            return 1.0

        # Ensure rates are initialized
        if not self._rates:
            self.initialize()

        # Both currencies to USD, then convert
        from_to_usd = self._rates.get(from_curr, 1.0)
        to_to_usd = self._rates.get(to_curr, 1.0)

        if to_curr == 'USD':
            return from_to_usd
        elif from_curr == 'USD':
            return 1.0 / to_to_usd if to_to_usd != 0 else 1.0
        else:
            return from_to_usd / to_to_usd if to_to_usd != 0 else from_to_usd

    def convert(
        self,
        amount: float,
        from_currency: str,
        to_currency: str = "USD",
    ) -> float:
        """
        Convert amount from one currency to another.

        Args:
            amount: Amount to convert
            from_currency: Source currency code
            to_currency: Target currency code

        Returns:
            Converted amount
        """
        rate = self.get_rate(from_currency, to_currency)
        return amount * rate

    def refresh(self) -> bool:
        """
        Force refresh exchange rates from API.

        Returns:
            True if refresh was successful
        """
        if self._fetch_from_api():
            self._save_to_cache()
            return True
        return False

    @property
    def is_using_fallback(self) -> bool:
        """Check if using fallback rates."""
        return self._using_fallback

    @property
    def available_currencies(self) -> list:
        """Get list of available currency codes."""
        return list(self._rates.keys())
