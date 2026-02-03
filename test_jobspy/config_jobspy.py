# -*- coding: utf-8 -*-
"""
JobSpy Maximum Scraper Configuration
This is a separate config file for jobspy_max_scraper.py
If you want to use different settings for JobSpy scraper, modify this file.
Otherwise, it will fall back to the main config.py
"""

# Run ID for JobSpy scraper (output folder name)
# If set to None, will use RUN_ID from main config.py
JOBSPY_RUN_ID = "BunchGlobal_2025_01_18"  # Set to None to use main config, or set to a string like "BunchIndeed_2025_12_17"

# Scraping parameters
RESULTS_PER_SEARCH = 1000  # Number of results to request per keyword+location combination
MAX_TOTAL_JOBS = None  # Maximum total jobs to collect (None = no limit)

# Date filter (optional)
# Only jobs posted on or after this date will be included
# Format: "YYYY-MM-DD" (e.g., "2024-01-15") or None (no filtering)
MIN_POSTED_DATE = "2025-12-18"  # Set to None to disable date filtering, or set to a date string like "2024-01-15"

# AI relevance filter (optional)
# If True, only jobs that are AI-related will be kept (filters out non-AI jobs)
# If False, all jobs matching the search        
# Platform selection (optional)
# Set to True to enable scraping from that platform, False to disable
# Options: ENABLE_INDEED, ENABLE_LINKEDIN
# If both are True, will scrape from both platforms and combine results
ENABLE_INDEED = True  # Indeed platform
ENABLE_LINKEDIN = True  # LinkedIn platform

# Region selection (optional)
# Set to True to enable scraping for that region, False to disable
# If all are False, only US will be scraped
ENABLE_US = True  # United States
ENABLE_UK = True  # United Kingdom
ENABLE_AUSTRALIA = True  # Australia
ENABLE_HONG_KONG = True  # Hong Kong
ENABLE_SINGAPORE = True  # Singapore

# Supabase integration (optional)
# Set to True to enable saving data to Supabase database
# Make sure to configure supabase_config.py first
ENABLE_SUPABASE = True  # Set to True after configuring Supabase

