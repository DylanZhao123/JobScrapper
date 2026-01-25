# -*- coding: utf-8 -*-
"""
AI Analysis module for JobScrapper.
Provides Gemini API integration for job analysis.
"""

from .gemini_client import GeminiClient
from .prompts import PromptManager
from .batch_processor import BatchProcessor

__all__ = [
    'GeminiClient',
    'PromptManager',
    'BatchProcessor',
]
