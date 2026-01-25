# -*- coding: utf-8 -*-
"""
Unified Salary Processor for JobScrapper.
Handles salary extraction, interval conversion, and normalization.
"""

import re
from typing import Dict, Any, Optional, Tuple
import pandas as pd


class SalaryProcessor:
    """Process and normalize salary data from job postings."""

    # Interval conversion multipliers to annual salary
    INTERVAL_MULTIPLIERS = {
        "yearly": 1,
        "annually": 1,
        "annual": 1,
        "year": 1,
        "monthly": 12,
        "month": 12,
        "weekly": 52,
        "week": 52,
        "hourly": 2080,  # US standard: 40 hours/week * 52 weeks
        "hour": 2080,
        "daily": 260,  # ~5 days/week * 52 weeks
        "day": 260,
    }

    # Currency symbols mapping
    CURRENCY_SYMBOLS = {
        'USD': '$',
        'GBP': '£',
        'AUD': 'A$',
        'SGD': 'S$',
        'HKD': 'HK$',
        'EUR': '€',
        'CAD': 'C$',
    }

    # Region to default currency mapping
    REGION_CURRENCY_MAP = {
        'United States': 'USD',
        'United Kingdom': 'GBP',
        'Australia': 'AUD',
        'Singapore': 'SGD',
        'Hong Kong': 'HKD',
        'Europe': 'EUR',
        'Canada': 'CAD',
    }

    def __init__(self, currency_converter=None):
        """
        Initialize salary processor.

        Args:
            currency_converter: Optional CurrencyConverter instance for USD conversion
        """
        self.currency_converter = currency_converter

    def process_structured_salary(
        self,
        min_amount: Optional[float],
        max_amount: Optional[float],
        currency: str = "USD",
        interval: str = "yearly",
    ) -> Dict[str, Any]:
        """
        Process structured salary data from JobSpy.

        Args:
            min_amount: Minimum salary amount
            max_amount: Maximum salary amount
            currency: Currency code
            interval: Salary interval (yearly, monthly, hourly, etc.)

        Returns:
            Dict with processed salary info
        """
        result = {
            'min_amount': None,
            'max_amount': None,
            'currency': currency or 'USD',
            'interval': interval or 'yearly',
            'salary_range': '',
            'estimated_annual': None,
            'estimated_annual_usd': None,
        }

        if min_amount is None or pd.isna(min_amount):
            return result

        # Normalize interval
        interval_lower = str(interval).lower().strip() if interval else 'yearly'
        multiplier = self.INTERVAL_MULTIPLIERS.get(interval_lower, 1)

        # Convert to annual
        annual_min = float(min_amount) * multiplier
        annual_max = float(max_amount) * multiplier if max_amount and not pd.isna(max_amount) else annual_min

        result['min_amount'] = annual_min
        result['max_amount'] = annual_max
        result['estimated_annual'] = (annual_min + annual_max) / 2

        # Format salary range string
        symbol = self.CURRENCY_SYMBOLS.get(currency, currency)
        if annual_min != annual_max:
            result['salary_range'] = f"{symbol}{int(annual_min):,} - {symbol}{int(annual_max):,}"
        else:
            result['salary_range'] = f"{symbol}{int(annual_min):,}"

        # Add interval note if not yearly
        if multiplier != 1:
            result['salary_range'] += f" (from {interval_lower})"

        # Convert to USD if converter available
        if self.currency_converter and currency != 'USD':
            rate = self.currency_converter.get_rate(currency, 'USD')
            result['estimated_annual_usd'] = result['estimated_annual'] * rate
        elif currency == 'USD':
            result['estimated_annual_usd'] = result['estimated_annual']

        return result

    def extract_from_description(
        self,
        description: str,
        region_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Extract salary information from job description text.

        Args:
            description: Job description text
            region_name: Region name to help identify default currency

        Returns:
            Dict with extracted salary info
        """
        result = {
            'min_amount': None,
            'max_amount': None,
            'currency': None,
            'interval': 'yearly',
            'salary_range': '',
            'estimated_annual': None,
            'estimated_annual_usd': None,
        }

        if not description or pd.isna(description):
            return result

        desc = str(description)
        desc_lower = desc.lower()

        # Determine default currency from region
        default_currency = self.REGION_CURRENCY_MAP.get(region_name, 'USD')

        # Try to find salary patterns
        min_amount, max_amount, currency = self._extract_salary_amounts(desc, default_currency)

        if min_amount is None:
            return result

        # Detect interval from context
        interval = self._detect_interval(desc, min_amount)
        multiplier = self.INTERVAL_MULTIPLIERS.get(interval, 1)

        # Convert to annual
        annual_min = min_amount * multiplier
        annual_max = max_amount * multiplier if max_amount else annual_min

        result['min_amount'] = annual_min
        result['max_amount'] = annual_max
        result['currency'] = currency
        result['interval'] = interval
        result['estimated_annual'] = (annual_min + annual_max) / 2

        # Format salary range string
        symbol = self.CURRENCY_SYMBOLS.get(currency, currency)
        if annual_min != annual_max:
            result['salary_range'] = f"{symbol}{int(annual_min):,} - {symbol}{int(annual_max):,}"
        else:
            result['salary_range'] = f"{symbol}{int(annual_min):,}"

        if multiplier != 1:
            result['salary_range'] += f" (from {interval})"

        # Convert to USD
        if self.currency_converter and currency != 'USD':
            rate = self.currency_converter.get_rate(currency, 'USD')
            result['estimated_annual_usd'] = result['estimated_annual'] * rate
        elif currency == 'USD':
            result['estimated_annual_usd'] = result['estimated_annual']

        return result

    def _safe_parse_amount(self, amount_str: str) -> Optional[float]:
        """Safely parse amount string to float."""
        if not amount_str:
            return None
        try:
            cleaned = amount_str.replace(',', '').strip()
            if not cleaned or not cleaned.replace('.', '').isdigit():
                return None
            return float(cleaned)
        except (ValueError, AttributeError):
            return None

    def _extract_salary_amounts(
        self,
        description: str,
        default_currency: str = 'USD',
    ) -> Tuple[Optional[float], Optional[float], str]:
        """
        Extract salary amounts from description text.

        Returns:
            Tuple of (min_amount, max_amount, currency)
        """
        # Pattern for range with currency: $50,000 - $80,000 or £40,000-£60,000
        pattern_range = r'(HK\$|A\$|S\$|C\$|[\$£€]|USD|GBP|AUD|SGD|HKD|EUR|CAD)\s*([\d,]+)\s*[-–—]\s*(HK\$|A\$|S\$|C\$|[\$£€]|USD|GBP|AUD|SGD|HKD|EUR|CAD)?\s*([\d,]+)'

        # Pattern for K notation: $50K - $80K
        pattern_k_range = r'(HK\$|A\$|S\$|C\$|[\$£€]|USD|GBP|AUD|SGD|HKD|EUR|CAD)?\s*([\d,]+)\s*[kK]\s*[-–—]\s*(HK\$|A\$|S\$|C\$|[\$£€]|USD|GBP|AUD|SGD|HKD|EUR|CAD)?\s*([\d,]+)\s*[kK]'

        # Pattern for single amount: $100,000
        pattern_single = r'(HK\$|A\$|S\$|C\$|[\$£€]|USD|GBP|AUD|SGD|HKD|EUR|CAD)\s*([\d,]+)'

        # Try range pattern first
        match = re.search(pattern_range, description, re.IGNORECASE)
        if match:
            min_val = self._safe_parse_amount(match.group(2))
            max_val = self._safe_parse_amount(match.group(4))
            if min_val is not None and max_val is not None:
                currency = self._detect_currency_from_symbol(match.group(1), default_currency)
                return min_val, max_val, currency

        # Try K notation range
        match = re.search(pattern_k_range, description, re.IGNORECASE)
        if match:
            min_val = self._safe_parse_amount(match.group(2))
            max_val = self._safe_parse_amount(match.group(4))
            if min_val is not None and max_val is not None:
                currency_symbol = match.group(1) or match.group(3)
                currency = self._detect_currency_from_symbol(currency_symbol, default_currency) if currency_symbol else default_currency
                return min_val * 1000, max_val * 1000, currency

        # Try single amount near salary keywords
        salary_keywords = ['salary', 'compensation', 'pay', 'wage', 'remuneration', 'package']
        desc_lower = description.lower()

        for kw in salary_keywords:
            kw_idx = desc_lower.find(kw)
            if kw_idx >= 0:
                # Look for amounts near this keyword (within 500 chars)
                search_area = description[max(0, kw_idx - 200):min(len(description), kw_idx + 500)]
                matches = list(re.finditer(pattern_single, search_area, re.IGNORECASE))
                for match in matches:
                    amount = self._safe_parse_amount(match.group(2))
                    if amount is not None and 1000 <= amount <= 2000000:
                        currency = self._detect_currency_from_symbol(match.group(1), default_currency)
                        return amount, amount, currency

        # Try first reasonable amount in description
        matches = list(re.finditer(pattern_single, description[:3000], re.IGNORECASE))
        for match in matches:
            amount = self._safe_parse_amount(match.group(2))
            if amount is not None and 1000 <= amount <= 2000000:
                currency = self._detect_currency_from_symbol(match.group(1), default_currency)
                return amount, amount, currency

        return None, None, default_currency

    def _detect_currency_from_symbol(self, symbol: str, default: str = 'USD') -> str:
        """Detect currency code from symbol."""
        if not symbol:
            return default

        symbol_upper = symbol.upper()
        symbol_map = {
            'HK$': 'HKD', 'HKD': 'HKD',
            'A$': 'AUD', 'AUD': 'AUD',
            'S$': 'SGD', 'SGD': 'SGD',
            'C$': 'CAD', 'CAD': 'CAD',
            '£': 'GBP', 'GBP': 'GBP',
            '€': 'EUR', 'EUR': 'EUR',
            '$': default, 'USD': 'USD',
        }

        return symbol_map.get(symbol_upper, symbol_map.get(symbol, default))

    def _detect_interval(self, description: str, amount: float) -> str:
        """Detect salary interval from description context."""
        # Find position of amount in description
        amount_str = str(int(amount))
        amount_idx = description.lower().find(amount_str)

        if amount_idx < 0:
            return 'yearly'

        # Look at context around the amount
        start = max(0, amount_idx - 50)
        end = min(len(description), amount_idx + 200)
        context = description[start:end].lower()

        # Check for interval keywords
        if any(x in context for x in ['per year', 'annually', 'annual', '/year', 'yearly', 'p.a.']):
            return 'yearly'
        elif any(x in context for x in ['per month', 'monthly', '/month', 'p.m.']):
            return 'monthly'
        elif any(x in context for x in ['per hour', 'hourly', '/hour', '/hr', 'p.h.']):
            return 'hourly'
        elif any(x in context for x in ['per week', 'weekly', '/week']):
            return 'weekly'
        elif any(x in context for x in ['per day', 'daily', '/day']):
            return 'daily'

        # Default based on amount size
        if amount < 500:  # Likely hourly
            return 'hourly'
        elif amount < 10000:  # Likely monthly
            return 'monthly'
        else:
            return 'yearly'

    def extract_requirements(self, description: str) -> str:
        """
        Extract requirements from job description.

        Args:
            description: Job description text

        Returns:
            Extracted requirements string
        """
        if not description or pd.isna(description):
            return ""

        desc = str(description)
        requirements_text = ''

        # Method 1: Find explicit sections
        req_patterns = [
            r'(?:requirements?|qualifications?|required|must have|minimum requirements?)[\s:]*\n?([^\n]{100,800})',
            r"(?:what you['']?ll need|what we['']?re looking for|you should have)[\s:]*\n?([^\n]{100,800})",
            r'(?:education|experience|skills?)[\s:]*\n?([^\n]{100,600})',
        ]

        for pattern in req_patterns:
            matches = re.finditer(pattern, desc, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                req_section = match.group(1).strip()
                req_section = re.sub(r'\s+', ' ', req_section)
                if len(req_section) > 50:
                    requirements_text = req_section[:500]
                    break
            if requirements_text:
                break

        # Method 2: Extract skill sentences
        if not requirements_text:
            skill_sentences = []
            sentences = re.split(r'[.!?]\s+', desc)
            for sent in sentences:
                sent_lower = sent.lower()
                if any(keyword in sent_lower for keyword in [
                    'years of experience', 'degree', 'bachelor', 'master', 'phd',
                    'proficiency', 'experience with', 'knowledge of', 'familiar with',
                    'required', 'must have', 'should have', 'qualifications'
                ]):
                    if len(sent.strip()) > 30:
                        skill_sentences.append(sent.strip())

            if skill_sentences:
                requirements_text = ' | '.join(skill_sentences[:5])
                requirements_text = requirements_text[:500]

        # Method 3: Extract first half if contains experience indicators
        if not requirements_text and desc:
            first_half = desc[:len(desc) // 2]
            if re.search(r'\d+\+?\s*(?:years?|months?|yr)', first_half, re.I):
                requirements_text = first_half[:500].strip()

        return requirements_text
