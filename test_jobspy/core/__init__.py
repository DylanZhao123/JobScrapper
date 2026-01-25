# -*- coding: utf-8 -*-
"""
Core module for JobScrapper unified system.
Contains data models, salary processing, and currency conversion.
"""

from .job_data import JobData, JobDataCollection
from .salary_processor import SalaryProcessor
from .currency_converter import CurrencyConverter

__all__ = [
    'JobData',
    'JobDataCollection',
    'SalaryProcessor',
    'CurrencyConverter',
]
