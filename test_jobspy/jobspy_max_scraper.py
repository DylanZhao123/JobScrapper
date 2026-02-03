# -*- coding: utf-8 -*-
"""
JobSpy Maximum Scraper - Indeed Jobs
Maximum coverage: All keywords + All US locations
With checkpoint support for resuming
Output format: example_output.xlsx
"""
import os
import sys
import time
import re
import json
from datetime import date, datetime
import pandas as pd
import numpy as np
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    print("[WARNING] requests library not found. Install with: pip install requests")

# Import config - try to use jobspy-specific config first, fall back to main config
try:
    import config_jobspy
    # Use jobspy-specific config if available
    if hasattr(config_jobspy, 'JOBSPY_RUN_ID') and config_jobspy.JOBSPY_RUN_ID is not None:
        JOBSPY_RUN_ID = config_jobspy.JOBSPY_RUN_ID
    else:
        # Fall back to main config
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        import config
        JOBSPY_RUN_ID = config.RUN_ID
except ImportError:
    # If jobspy config doesn't exist, use main config
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import config
    JOBSPY_RUN_ID = config.RUN_ID

JOBSPY_OUTPUT_DIR = f"output/{JOBSPY_RUN_ID}"

# Output configuration based on RUN_ID
OUTPUT_DIR = JOBSPY_OUTPUT_DIR
OUTPUT_FILE = f"{OUTPUT_DIR}/jobspy_max_output.xlsx"
CHECKPOINT_FILE = f"{OUTPUT_DIR}/jobspy_max_checkpoint.json"
RAW_DATA_FILE = f"{OUTPUT_DIR}/jobspy_max_raw_data.json"

# Check if RUN_ID has changed, clear old checkpoints if changed
# First, check for .last_run_id in any output subdirectory
_last_run_id_file = f"{OUTPUT_DIR}/.last_run_id"
old_run_id = None
if os.path.exists(_last_run_id_file):
    try:
        with open(_last_run_id_file, "r", encoding="utf-8") as f:
            old_run_id = f.read().strip()
    except:
        pass
else:
    # Also check in old output directories
    if os.path.exists("output"):
        for item in os.listdir("output"):
            item_path = os.path.join("output", item)
            if os.path.isdir(item_path):
                old_id_file = os.path.join(item_path, ".last_run_id")
                if os.path.exists(old_id_file):
                    try:
                        with open(old_id_file, "r", encoding="utf-8") as f:
                            old_run_id = f.read().strip()
                            break
                    except:
                        pass

if old_run_id and old_run_id != JOBSPY_RUN_ID:
    # RUN_ID changed, clear old checkpoint files in all region subdirectories
    print(f"\n{'='*60}")
    print(f"RUN_ID changed detected: {old_run_id} -> {JOBSPY_RUN_ID}")
    print(f"{'='*60}")
    print("Clearing old checkpoint files in all region subdirectories...")
    
    old_output_dir = f"output/{old_run_id}"
    if os.path.exists(old_output_dir):
        # Clear checkpoints in all region subdirectories
        regions = ["united_states", "united_kingdom", "australia", "hong_kong", "singapore"]
        for region in regions:
            region_dir = os.path.join(old_output_dir, region)
            if os.path.exists(region_dir):
                checkpoint_file = os.path.join(region_dir, "jobspy_max_checkpoint.json")
                raw_data_file = os.path.join(region_dir, "jobspy_max_raw_data.json")
                for file_path in [checkpoint_file, raw_data_file]:
                    if os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                            print(f"  Deleted: {file_path}")
                        except Exception as e:
                            print(f"  Warning: Could not delete {file_path}: {e}")
    
    # Also clear root-level checkpoint files (if they exist)
    checkpoint_files = [
        CHECKPOINT_FILE,
        RAW_DATA_FILE,
    ]
    for file_path in checkpoint_files:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"  Deleted: {file_path}")
            except:
                pass
    
    print(f"Old checkpoint files cleared. New output will be saved to: {OUTPUT_DIR}")
    print(f"{'='*60}\n")

# Save current RUN_ID
os.makedirs(OUTPUT_DIR, exist_ok=True)
with open(_last_run_id_file, "w", encoding="utf-8") as f:
    f.write(JOBSPY_RUN_ID)

# Expected fields from example_output.xlsx - exact order
EXPECTED_FIELDS = [
    "Job Title", "Company Name", "Requirements", "Location",
    "Salary Range", "Estimated Annual Salary", "Estimated Annual Salary (USD)", "Job Description",
    "Team Size/Business Line Size", "Company Size",
    "Posted Date", "Job Status",
    "Platform", "Job Link"
]

# Core AI keywords (high relevance)
CORE_KEYWORDS = [
    "AI Engineer", "Machine Learning Engineer", "Deep Learning Engineer",
    "NLP Engineer", "Data Scientist", "Computer Vision Engineer"
]

# AI-related keywords (low relevance) - from main_merged.py
AI_RELATED_KEYWORDS = [
    # AI Sales related
    "AI Sales", "AI Sales Representative", "AI Sales Manager", 
    "AI Business Development", "AI Account Manager",
    
    # AI Conversation related
    "AI Conversation", "AI Conversational Designer", "AI Chatbot Designer",
    "AI Dialogue Designer", "Conversational AI", "AI Voice Assistant",
    
    # AI Training related
    "AI Training", "AI Trainer", "AI Model Training", "AI Data Training",
    "AI Training Specialist", "Machine Learning Trainer",
    
    # AI Product Manager related
    "AI Product Manager", "AI PM", "AI Product Owner", "AI Product Lead",
    
    # AI + Industry related
    "AI Healthcare", "AI Finance", "AI Education", "AI Retail", 
    "AI Manufacturing", "AI Agriculture", "AI Transportation",
    "AI Energy", "AI Legal", "AI Marketing",
    
    # AI Art related
    "AI Art", "AI Artist", "AI Painting", "AI Illustrator", 
    "AI Creative", "AI Digital Art", "AI Visual Artist",
    
    # AI Design related
    "AI Design", "AI Designer", "AI UX Designer", "AI UI Designer",
    "AI Interaction Designer", "AI Design Specialist",
    
    # AI Architecture related
    "AI Architecture", "AI Architect", "AI System Architecture",
    "AI Solution Architect", "AI Platform Architect",
    
    # AI Governance related
    "AI Governance", "AI Governance Specialist", "AI Compliance",
    "AI Risk Management", "AI Policy",
    
    # AI Ethics related
    "AI Ethics", "AI Ethical", "AI Ethics Researcher", 
    "Responsible AI", "AI Fairness", "AI Bias",
    
    # AI Hardware related
    "AI Hardware", "AI Hardware Engineer", "AI Chip Design",
    "AI Accelerator", "AI Processor",
    
    # AI Operations related
    "AI Operations", "AI Ops", "AI DevOps", "AI Infrastructure",
    "AI MLOps", "AI Platform Engineer", "AI Systems Engineer",
    
    # Data Annotation related
    "Data Annotation", "Data Labeling", "Data Annotator", 
    "Data Tagging", "Data Quality", "Data Curation",
    
    # Robotics related
    "Robotics", "Robot Engineer", "Robotics Engineer", 
    "Autonomous Systems", "Robotic Process Automation", "RPA",
]

# Combine all keywords
ALL_KEYWORDS = CORE_KEYWORDS + AI_RELATED_KEYWORDS


def get_locations_by_region(region_name):
    """
    Get locations for a specific region from local locations_config.py
    
    Args:
        region_name: Region name ("United States", "United Kingdom", "Australia", "Hong Kong", "Singapore")
    
    Returns:
        List of location strings
    """
    try:
        # Try to import from local directory first (same folder as this script)
        from locations_config import LOCATIONS_BY_REGION
        
        if region_name not in LOCATIONS_BY_REGION:
            print(f"[WARNING] Region '{region_name}' not found in locations_config.py")
            return []
        
        region_locations = []
        for state, locations in LOCATIONS_BY_REGION[region_name].items():
            region_locations.extend(locations)
        
        print(f"[INFO] Loaded {len(region_locations)} locations for {region_name} from local locations_config.py")
        return region_locations
    except ImportError:
        # Fallback: try parent directory
        try:
            import sys
            parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if parent_dir not in sys.path:
                sys.path.insert(0, parent_dir)
            
            from locations_config import LOCATIONS_BY_REGION
            
            if region_name not in LOCATIONS_BY_REGION:
                print(f"[WARNING] Region '{region_name}' not found in locations_config.py")
                return []
            
            region_locations = []
            for state, locations in LOCATIONS_BY_REGION[region_name].items():
                region_locations.extend(locations)
            
            print(f"[INFO] Loaded {len(region_locations)} locations for {region_name} from parent locations_config.py")
            return region_locations
        except Exception as e:
            print(f"[WARNING] Failed to import locations_config: {e}")
            print(f"[WARNING] Using fallback locations for {region_name}")
            # Return fallback locations based on region
            fallback_map = {
                "United States": ["United States", "California", "New York", "Texas"],
                "United Kingdom": ["London, England, United Kingdom"],
                "Australia": ["Sydney, New South Wales, Australia"],
                "Hong Kong": ["Hong Kong"],
                "Singapore": ["Singapore"],
            }
            return fallback_map.get(region_name, [])
    except Exception as e:
        print(f"[WARNING] Failed to import locations_config: {e}")
        print(f"[WARNING] Using fallback locations for {region_name}")
        fallback_map = {
            "United States": ["United States", "California", "New York", "Texas"],
            "United Kingdom": ["London, England, United Kingdom"],
            "Australia": ["Sydney, New South Wales, Australia"],
            "Hong Kong": ["Hong Kong"],
            "Singapore": ["Singapore"],
        }
        return fallback_map.get(region_name, [])


def get_us_locations_only():
    """Get US locations only - backward compatibility function"""
    return get_locations_by_region("United States")


def generate_job_key(job):
    """
    Generate a unique key for a job based on title + company + location
    Used for deduplication
    
    Args:
        job: Job dictionary with 'title', 'company', 'location' fields
    
    Returns:
        str: Normalized unique key for the job
    """
    title = str(job.get("title", "")).strip().lower()
    company = str(job.get("company", "")).strip().lower()
    location = str(job.get("location", "")).strip().lower()
    
    # Normalize: remove extra spaces, handle NaN/None
    title = re.sub(r'\s+', ' ', title) if title and title != 'nan' else ""
    company = re.sub(r'\s+', ' ', company) if company and company != 'nan' else ""
    location = re.sub(r'\s+', ' ', location) if location and location != 'nan' else ""
    
    # Combine into unique key
    job_key = f"{title}|||{company}|||{location}"
    
    return job_key


def generate_cross_platform_dedup_key(job):
    """
    Generate a deduplication key for cross-platform deduplication
    Based on job_title + company_name only (ignoring location and platform)
    Used to deduplicate between LinkedIn and Indeed
    
    Args:
        job: Job dictionary or DataFrame row with 'title'/'Job Title' and 'company'/'Company Name' fields
    
    Returns:
        str: Normalized unique key based on title + company, or None if missing required fields
    """
    # Handle both raw job dict and DataFrame row
    if isinstance(job, dict):
        title = str(job.get("title") or job.get("Job Title", "")).strip().lower()
        company = str(job.get("company") or job.get("Company Name", "")).strip().lower()
    else:
        # DataFrame row (pandas Series)
        title = str(job.get("Job Title", "")).strip().lower()
        company = str(job.get("Company Name", "")).strip().lower()
    
    # Normalize: remove extra spaces, handle NaN/None
    title = re.sub(r'\s+', ' ', title) if title and title != 'nan' else ""
    company = re.sub(r'\s+', ' ', company) if company and company != 'nan' else ""
    
    # Both title and company are required for cross-platform deduplication
    if not title or not company:
        return None
    
    # Return key based on title + company only
    return f"{title}|||{company}"


def deduplicate_cross_platform(df_indeed, df_linkedin):
    """
    Deduplicate jobs between Indeed and LinkedIn based on job_title + company_name
    
    Args:
        df_indeed: DataFrame with Indeed jobs
        df_linkedin: DataFrame with LinkedIn jobs
    
    Returns:
        tuple: (df_deduplicated_indeed, df_deduplicated_linkedin, df_combined)
    """
    print(f"\n{'='*60}")
    print("Cross-Platform Deduplication")
    print(f"{'='*60}")
    
    indeed_count = len(df_indeed) if df_indeed is not None and not df_indeed.empty else 0
    linkedin_count = len(df_linkedin) if df_linkedin is not None and not df_linkedin.empty else 0
    
    print(f"  Indeed jobs: {indeed_count}")
    print(f"  LinkedIn jobs: {linkedin_count}")
    
    if indeed_count == 0 and linkedin_count == 0:
        print("  No jobs to deduplicate")
        return None, None, pd.DataFrame()
    
    if indeed_count == 0:
        print("  Only LinkedIn jobs, no deduplication needed")
        return None, df_linkedin, df_linkedin.copy()
    
    if linkedin_count == 0:
        print("  Only Indeed jobs, no deduplication needed")
        return df_indeed, None, df_indeed.copy()
    
    # Generate dedup keys for both DataFrames
    indeed_keys = set()
    for idx, row in df_indeed.iterrows():
        key = generate_cross_platform_dedup_key(row)
        if key:
            indeed_keys.add(key)
    
    linkedin_keys = set()
    for idx, row in df_linkedin.iterrows():
        key = generate_cross_platform_dedup_key(row)
        if key:
            linkedin_keys.add(key)
    
    # Find duplicates
    duplicates = indeed_keys & linkedin_keys
    print(f"  Found {len(duplicates)} duplicate jobs (same title + company)")
    
    # Filter out duplicates from LinkedIn (keep Indeed version)
    df_linkedin_dedup = df_linkedin.copy()
    if not df_linkedin_dedup.empty:
        linkedin_dedup_keys = []
        for idx, row in df_linkedin_dedup.iterrows():
            key = generate_cross_platform_dedup_key(row)
            linkedin_dedup_keys.append(key)
        
        df_linkedin_dedup['_dedup_key'] = linkedin_dedup_keys
        df_linkedin_dedup = df_linkedin_dedup[~df_linkedin_dedup['_dedup_key'].isin(duplicates)]
        df_linkedin_dedup = df_linkedin_dedup.drop(columns=['_dedup_key'])
    
    # Combine both DataFrames
    df_combined = pd.concat([df_indeed, df_linkedin_dedup], ignore_index=True)
    
    print(f"  After deduplication:")
    print(f"    Indeed: {len(df_indeed)} jobs")
    print(f"    LinkedIn: {len(df_linkedin_dedup)} jobs (removed {len(duplicates)} duplicates)")
    print(f"    Total: {len(df_combined)} unique jobs")
    print(f"{'='*60}\n")
    
    return df_indeed, df_linkedin_dedup, df_combined
    return job_key


def get_region_output_dir(region_name):
    """Get output directory for a specific region"""
    region_safe_name = region_name.replace(" ", "_").lower()
    return f"{JOBSPY_OUTPUT_DIR}/{region_safe_name}"


def load_checkpoint(region_name):
    """Load checkpoint for a specific region"""
    region_dir = get_region_output_dir(region_name)
    checkpoint_file = f"{region_dir}/jobspy_max_checkpoint.json"
    try:
        with open(checkpoint_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return None


def save_checkpoint(region_name, keyword_idx, location_idx, seen_job_keys, all_jobs):
    """Save checkpoint for a specific region"""
    region_dir = get_region_output_dir(region_name)
    checkpoint_file = f"{region_dir}/jobspy_max_checkpoint.json"
    os.makedirs(os.path.dirname(checkpoint_file), exist_ok=True)
    checkpoint = {
        "region": region_name,
        "keyword_idx": keyword_idx,
        "location_idx": location_idx,
        "seen_job_keys": list(seen_job_keys),
        "total_jobs": len(all_jobs),
        "last_update": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    with open(checkpoint_file, "w", encoding="utf-8") as f:
        json.dump(checkpoint, f, ensure_ascii=False, indent=2)


def load_raw_data(region_name):
    """Load raw job data for a specific region"""
    region_dir = get_region_output_dir(region_name)
    raw_data_file = f"{region_dir}/jobspy_max_raw_data.json"
    try:
        with open(raw_data_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []


def save_raw_data(region_name, all_jobs):
    """Save raw job data for a specific region"""
    region_dir = get_region_output_dir(region_name)
    raw_data_file = f"{region_dir}/jobspy_max_raw_data.json"
    os.makedirs(os.path.dirname(raw_data_file), exist_ok=True)
    
    # Convert all jobs to serializable format
    serializable_jobs = []
    for job in all_jobs:
        serializable_job = {}
        for key, value in job.items():
            serializable_job[key] = convert_to_serializable(value)
        serializable_jobs.append(serializable_job)
    
    with open(raw_data_file, "w", encoding="utf-8") as f:
        json.dump(serializable_jobs, f, ensure_ascii=False, indent=2)


def convert_to_serializable(obj):
    """Convert non-serializable objects to strings"""
    # Handle pandas Timestamp and NaT
    if isinstance(obj, pd.Timestamp):
        return str(obj) if pd.notna(obj) else None
    # Handle datetime.date or datetime.datetime
    elif isinstance(obj, (date, datetime)):
        return obj.isoformat()
    elif hasattr(obj, 'isoformat'):  # Other datetime-like objects
        return obj.isoformat()
    # Handle numpy types
    elif isinstance(obj, (np.integer, np.floating)):
        return int(obj) if isinstance(obj, np.integer) else float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    # Handle NaN/NaT values
    elif pd.isna(obj):
        return None
    return obj


def parse_posted_date(date_str):
    """
    Parse posted date string to datetime object
    Supports multiple formats:
    - ISO format: "2024-01-15T00:00:00" or "2024-01-15"
    - Other common formats
    Returns None if parsing fails
    """
    if not date_str or pd.isna(date_str):
        return None
    
    date_str = str(date_str).strip()
    if not date_str:
        return None
    
    # Try pandas to_datetime (handles most formats)
    try:
        parsed_date = pd.to_datetime(date_str, errors='coerce')
        if pd.notna(parsed_date):
            return parsed_date.to_pydatetime()
    except:
        pass
    
    # Try common date formats
    date_formats = [
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%d/%m/%Y",
    ]
    
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt)
        except:
            continue
    
    return None

def filter_jobs_by_date(jobs, min_date, verbose=False):
    """
    Filter jobs by minimum posted date
    Only keeps jobs with date_posted >= min_date
    Jobs without date_posted are kept (assumed to be recent)
    
    Args:
        jobs: List of job dictionaries (JobSpy format with 'date_posted' field)
        min_date: datetime object or None (no filtering)
        verbose: If True, print detailed statistics
    
    Returns:
        Filtered list of jobs
    """
    if min_date is None:
        return jobs
    
    if not isinstance(min_date, datetime):
        # Try to parse min_date if it's a string
        parsed_min_date = parse_posted_date(str(min_date))
        if parsed_min_date is None:
            if verbose:
                print(f"Warning: Invalid min_date format, skipping date filter")
            return jobs
        min_date = parsed_min_date
    
    filtered_jobs = []
    jobs_without_date = 0
    jobs_before_date = 0
    
    for job in jobs:
        # JobSpy uses 'date_posted' field
        date_posted = job.get("date_posted", "")
        if not date_posted or pd.isna(date_posted) or str(date_posted).strip() == "":
            # No date information, keep it (assumed to be recent)
            filtered_jobs.append(job)
            jobs_without_date += 1
            continue
        
        posted_date = parse_posted_date(str(date_posted))
        if posted_date is None:
            # Could not parse date, keep it (assumed to be recent)
            filtered_jobs.append(job)
            jobs_without_date += 1
            continue
        
        # Compare dates
        if posted_date >= min_date:
            filtered_jobs.append(job)
        else:
            jobs_before_date += 1
    
    if verbose and min_date:
        print(f"\n[Date Filter] Filtering jobs posted on or after {min_date.strftime('%Y-%m-%d')}")
        print(f"  Total jobs before filter: {len(jobs)}")
        print(f"  Jobs without date (kept): {jobs_without_date}")
        print(f"  Jobs before date (removed): {jobs_before_date}")
        print(f"  Jobs after date (kept): {len(filtered_jobs) - jobs_without_date}")
        print(f"  Total jobs after filter: {len(filtered_jobs)}")
    
    return filtered_jobs

def is_ai_related_job(job, verbose=False):
    """
    Check if a job is AI-related by examining title and description
    Returns True if job appears to be AI-related, False otherwise
    
    Args:
        job: Job dictionary with 'title' and 'description' fields
        verbose: If True, print reason for filtering
    
    Returns:
        bool: True if AI-related, False otherwise
    """
    title = str(job.get("title", "")).lower()
    description = str(job.get("description", "")).lower()
    
    # Core AI keywords (high relevance - must appear in title or description)
    core_ai_keywords = [
        "ai engineer", "machine learning", "deep learning", "ml engineer", "dl engineer",
        "nlp engineer", "natural language processing", "data scientist", 
        "computer vision", "cv engineer", "neural network", "tensorflow", "pytorch",
        "artificial intelligence", "ai/ml", "ml/ai", "ai model", "ml model",
        "generative ai", "genai", "llm", "large language model", "transformer",
        "reinforcement learning", "rl engineer", "ai research", "ml research"
    ]
    
    # AI-related keywords (medium relevance - should appear with context)
    ai_related_keywords = [
        "ai sales", "ai product", "ai architect", "ai designer", "ai ops", "mlops",
        "ai infrastructure", "ai platform", "ai system", "ai solution",
        "conversational ai", "chatbot", "ai assistant", "ai voice",
        "ai training", "ai data", "ai governance", "ai ethics", "responsible ai",
        "ai hardware", "ai chip", "ai accelerator", "ai processor",
        "robotics", "autonomous", "rpa", "robotic process automation",
        "data annotation", "data labeling", "data curation"
    ]
    
    # Negative keywords (if these appear prominently, likely not AI-related)
    negative_keywords = [
        "sales representative", "sales manager", "account manager", "business development",
        "customer service", "call center", "telemarketing", "retail sales",
        "warehouse", "logistics", "shipping", "delivery driver",
        "restaurant", "food service", "hospitality", "cleaning", "janitor"
    ]
    
    # Check for negative keywords in title (strong indicator of non-AI job)
    for neg_kw in negative_keywords:
        if neg_kw in title and not any(ai_kw in title for ai_kw in core_ai_keywords + ai_related_keywords):
            if verbose:
                print(f"    [FILTERED] Negative keyword in title: '{neg_kw}'")
            return False
    
    # Check title for core AI keywords (strong indicator)
    title_has_core = any(kw in title for kw in core_ai_keywords)
    if title_has_core:
        return True
    
    # Check description for core AI keywords
    desc_has_core = any(kw in description for kw in core_ai_keywords)
    if desc_has_core:
        return True
    
    # Check for AI-related keywords in title (medium indicator)
    title_has_related = any(kw in title for kw in ai_related_keywords)
    if title_has_related:
        # Also check description to confirm context
        desc_has_related = any(kw in description for kw in ai_related_keywords)
        if desc_has_related:
            return True
    
    # If no AI keywords found, likely not AI-related
    if verbose:
        print(f"    [FILTERED] No AI keywords found in title or description")
    return False


def filter_ai_related_jobs(jobs, verbose=False):
    """
    Filter jobs to keep only AI-related ones
    Uses is_ai_related_job() to check each job
    
    Args:
        jobs: List of job dictionaries
        verbose: If True, print filtering statistics
    
    Returns:
        Filtered list of AI-related jobs
    """
    if not jobs:
        return jobs
    
    filtered_jobs = []
    filtered_count = 0
    
    for job in jobs:
        if is_ai_related_job(job, verbose=False):
            filtered_jobs.append(job)
        else:
            filtered_count += 1
    
    if verbose:
        print(f"\n[AI Filter] Filtering non-AI related jobs")
        print(f"  Total jobs before filter: {len(jobs)}")
        print(f"  Non-AI jobs filtered out: {filtered_count}")
        print(f"  AI-related jobs kept: {len(filtered_jobs)}")
    
    return filtered_jobs


# Global exchange rate cache
_exchange_rate_cache = {}
_exchange_rate_cache_time = None
EXCHANGE_RATE_CACHE_DURATION = 3600  # Cache for 1 hour


def fetch_exchange_rates_from_api():
    """
    Fetch real-time exchange rates from API
    Uses exchangerate-api.com (free tier, no API key required)
    
    Returns:
        dict: Dictionary of currency codes to USD rates, or None if failed
    """
    if not HAS_REQUESTS:
        return None
    
    try:
        # Using exchangerate-api.com free endpoint (no API key required)
        # Alternative: exchangerate.host (also free, no API key)
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'rates' in data:
            # Convert to rates where 1 unit of currency = X USD
            # API returns rates where 1 USD = X currency, so we need to invert
            rates_to_usd = {}
            for currency, rate in data['rates'].items():
                if rate > 0:
                    rates_to_usd[currency] = 1.0 / rate
            
            # Always include USD
            rates_to_usd['USD'] = 1.0
            
            print(f"[INFO] Successfully fetched exchange rates from API")
            return rates_to_usd
        else:
            print(f"[WARNING] Invalid API response format")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"[WARNING] Failed to fetch exchange rates from API: {str(e)[:50]}")
        return None
    except Exception as e:
        print(f"[WARNING] Error fetching exchange rates: {str(e)[:50]}")
        return None


def get_fallback_exchange_rates():
    """
    Get fallback exchange rates (used when API fails)
    
    Returns:
        dict: Dictionary of currency codes to USD rates
    """
    return {
        'USD': 1.0,
        'GBP': 1.27,  # 1 GBP = 1.27 USD (approximate)
        'AUD': 0.67,  # 1 AUD = 0.67 USD (approximate)
        'SGD': 0.74,  # 1 SGD = 0.74 USD (approximate)
        'HKD': 0.13,  # 1 HKD = 0.13 USD (approximate)
        'EUR': 1.09,  # 1 EUR = 1.09 USD (approximate)
        'CAD': 0.73,  # 1 CAD = 0.73 USD (approximate)
    }


def initialize_exchange_rates():
    """
    Initialize exchange rates before scraping
    Fetches from API if available, otherwise uses fallback rates
    """
    global _exchange_rate_cache, _exchange_rate_cache_time
    
    current_time = time.time()
    
    # Check if cache is still valid
    if (_exchange_rate_cache_time is not None and 
        current_time - _exchange_rate_cache_time < EXCHANGE_RATE_CACHE_DURATION and
        _exchange_rate_cache):
        print(f"[INFO] Using cached exchange rates (age: {int(current_time - _exchange_rate_cache_time)}s)")
        return _exchange_rate_cache
    
    # Try to fetch from API
    print(f"[INFO] Fetching real-time exchange rates from API...")
    rates = fetch_exchange_rates_from_api()
    
    if rates:
        _exchange_rate_cache = rates
        _exchange_rate_cache_time = current_time
        return rates
    else:
        # Use fallback rates
        print(f"[WARNING] Using fallback exchange rates (API unavailable)")
        _exchange_rate_cache = get_fallback_exchange_rates()
        _exchange_rate_cache_time = current_time
        return _exchange_rate_cache


def get_exchange_rate(from_currency, to_currency="USD"):
    """
    Get exchange rate from one currency to another
    Uses real-time API rates if available, otherwise fallback rates
    
    Args:
        from_currency: Source currency code (USD, GBP, AUD, SGD, HKD, etc.)
        to_currency: Target currency code (default: USD)
    
    Returns:
        float: Exchange rate, or 1.0 if same currency or error
    """
    if from_currency.upper() == to_currency.upper():
        return 1.0
    
    # Initialize rates if not cached
    if not _exchange_rate_cache:
        initialize_exchange_rates()
    
    # Currency codes mapping
    currency_map = {
        'USD': 'USD', 'US$': 'USD', '$': 'USD',
        'GBP': 'GBP', '£': 'GBP', 'GB£': 'GBP',
        'AUD': 'AUD', 'A$': 'AUD', 'AU$': 'AUD',
        'SGD': 'SGD', 'S$': 'SGD', 'SG$': 'SGD',
        'HKD': 'HKD', 'HK$': 'HKD',
        'EUR': 'EUR', '€': 'EUR', 'EU€': 'EUR',
        'CAD': 'CAD', 'C$': 'CAD', 'CA$': 'CAD',
    }
    
    # Normalize currency
    from_curr = currency_map.get(from_currency.upper(), from_currency.upper())
    to_curr = currency_map.get(to_currency.upper(), to_currency.upper())
    
    # Get rates from cache
    rates_to_usd = _exchange_rate_cache if _exchange_rate_cache else get_fallback_exchange_rates()
    
    if to_currency.upper() == 'USD':
        return rates_to_usd.get(from_curr, 1.0)
    elif from_curr == 'USD':
        # Reverse conversion: USD to target
        target_to_usd = rates_to_usd.get(to_curr, 1.0)
        return 1.0 / target_to_usd if target_to_usd != 0 else 1.0
    else:
        # Convert via USD
        from_to_usd = rates_to_usd.get(from_curr, 1.0)
        to_to_usd = rates_to_usd.get(to_curr, 1.0)
        if to_to_usd != 0:
            return from_to_usd / to_to_usd
        else:
            return 1.0


def extract_salary_from_description(description, region_name=None):
    """
    Extract salary information from job description text
    Supports multiple currencies and formats
    
    Args:
        description: Job description text
        region_name: Region name to help identify currency (optional)
    
    Returns:
        dict: {
            'min_amount': float or None,
            'max_amount': float or None,
            'currency': str or None,
            'interval': str or None,
            'salary_range': str,
            'estimated_annual': float or None
        }
    """
    if not description or pd.isna(description):
        return {
            'min_amount': None,
            'max_amount': None,
            'currency': None,
            'interval': None,
            'salary_range': '',
            'estimated_annual': None
        }
    
    desc = str(description)
    
    # Currency detection based on region
    region_currency_map = {
        'United States': 'USD',
        'United Kingdom': 'GBP',
        'Australia': 'AUD',
        'Singapore': 'SGD',
        'Hong Kong': 'HKD',
    }
    default_currency = region_currency_map.get(region_name, 'USD')
    
    # Currency symbols and codes
    currency_patterns = {
        'USD': [r'\$', r'USD', r'US\$', r'\$\s*'],
        'GBP': [r'£', r'GBP', r'GB£', r'pounds?'],
        'AUD': [r'A\$', r'AUD', r'AU\$', r'Australian\s*dollars?'],
        'SGD': [r'S\$', r'SGD', r'SG\$', r'Singapore\s*dollars?'],
        'HKD': [r'HK\$', r'HKD', r'Hong\s*Kong\s*dollars?'],
        'EUR': [r'€', r'EUR', r'euros?'],
        'CAD': [r'C\$', r'CAD', r'CA\$', r'Canadian\s*dollars?'],
    }
    
    # Salary patterns - various formats
    # Pattern 1: $50,000 - $80,000 per year
    # Pattern 2: £40,000-£60,000
    # Pattern 3: $94,563 - $125,832 + 15.4% super
    # Pattern 4: Salary: $100,000
    # Pattern 5: 50k - 80k
    # Pattern 6: $50K-$80K
    
    salary_patterns = [
        # Range with currency symbol: $50,000 - $80,000
        r'([\$£€A\$S\$HK\$C\$]|USD|GBP|AUD|SGD|HKD|EUR|CAD)\s*([\d,]+)\s*[-–—]\s*([\$£€A\$S\$HK\$C\$]|USD|GBP|AUD|SGD|HKD|EUR|CAD)?\s*([\d,]+)',
        # Range without currency in middle: $50,000-80,000
        r'([\$£€A\$S\$HK\$C\$]|USD|GBP|AUD|SGD|HKD|EUR|CAD)\s*([\d,]+)\s*[-–—]\s*([\d,]+)',
        # Single amount: $100,000
        r'([\$£€A\$S\$HK\$C\$]|USD|GBP|AUD|SGD|HKD|EUR|CAD)\s*([\d,]+)',
        # K notation: $50K - $80K or 50k-80k
        r'([\$£€A\$S\$HK\$C\$]|USD|GBP|AUD|SGD|HKD|EUR|CAD)?\s*([\d,]+)\s*[kK]\s*[-–—]\s*([\$£€A\$S\$HK\$C\$]|USD|GBP|AUD|SGD|HKD|EUR|CAD)?\s*([\d,]+)\s*[kK]',
        r'([\$£€A\$S\$HK\$C\$]|USD|GBP|AUD|SGD|HKD|EUR|CAD)?\s*([\d,]+)\s*[kK]',
    ]
    
    # Try to find salary in description
    # Look for common salary keywords
    salary_keywords = ['salary', 'compensation', 'pay', 'wage', 'remuneration', 'package']
    desc_lower = desc.lower()
    
    # Check if description contains salary keywords
    has_salary_context = any(kw in desc_lower for kw in salary_keywords)
    
    # Extract salary patterns
    min_amount = None
    max_amount = None
    currency = default_currency
    interval = 'yearly'  # Default assumption
    
    # Try pattern 1: Range with currency (e.g., $50,000 - $80,000 or $94,563 - $125,832)
    # Match currency symbol followed by number, dash, optional currency, number
    # Order matters: match longer patterns first (HK$, A$, S$, C$) before single $
    pattern1 = r'(HK\$|A\$|S\$|C\$|[\$£€]|USD|GBP|AUD|SGD|HKD|EUR|CAD)\s*([\d,]+)\s*[-–—]\s*(HK\$|A\$|S\$|C\$|[\$£€]|USD|GBP|AUD|SGD|HKD|EUR|CAD)?\s*([\d,]+)'
    match1 = re.search(pattern1, desc, re.IGNORECASE)
    if match1:
        curr1 = match1.group(1)
        amount1 = match1.group(2).replace(',', '')
        curr2 = match1.group(3) if match1.group(3) else curr1
        amount2 = match1.group(4).replace(',', '')
        
        try:
            min_amount = float(amount1)
            max_amount = float(amount2)
            # Detect currency - check specific symbols first
            if curr1.upper() in ['HK$', 'HKD']:
                currency = 'HKD'
            elif curr1.upper() in ['A$', 'AUD']:
                currency = 'AUD'
            elif curr1.upper() in ['S$', 'SGD']:
                currency = 'SGD'
            elif curr1.upper() in ['C$', 'CAD']:
                currency = 'CAD'
            elif curr1 in ['£', 'GBP']:
                currency = 'GBP'
            elif curr1 in ['€', 'EUR']:
                currency = 'EUR'
            elif curr1 == '$' or curr1.upper() == 'USD':
                # For ambiguous $, use region default if available
                currency = default_currency
            else:
                # Try pattern matching
                for curr_code, patterns in currency_patterns.items():
                    if any(re.search(p, curr1, re.IGNORECASE) for p in patterns):
                        currency = curr_code
                        break
        except:
            pass
    
    # Try pattern 2: K notation range (e.g., $50K - $80K or 50k-80k)
    # Also try without currency symbols (e.g., 50K-80K)
    if min_amount is None:
        # Pattern with currency
        pattern2a = r'(HK\$|A\$|S\$|C\$|[\$£€]|USD|GBP|AUD|SGD|HKD|EUR|CAD)?\s*([\d,]+)\s*[kK]\s*[-–—]\s*(HK\$|A\$|S\$|C\$|[\$£€]|USD|GBP|AUD|SGD|HKD|EUR|CAD)?\s*([\d,]+)\s*[kK]'
        match2a = re.search(pattern2a, desc, re.IGNORECASE)
        # Pattern without currency (e.g., 50K-80K)
        pattern2b = r'([\d,]+)\s*[kK]\s*[-–—]\s*([\d,]+)\s*[kK]'
        match2b = re.search(pattern2b, desc, re.IGNORECASE)
        match2 = match2a or match2b
        if match2:
            if match2a:
                # Pattern with currency
                curr1 = match2.group(1) or '$'
                amount1 = match2.group(2).replace(',', '')
                curr2 = match2.group(3) or curr1
                amount2 = match2.group(4).replace(',', '')
            else:
                # Pattern without currency (match2b)
                curr1 = default_currency
                amount1 = match2.group(1).replace(',', '')
                curr2 = default_currency
                amount2 = match2.group(2).replace(',', '')
            
            try:
                min_amount = float(amount1) * 1000
                max_amount = float(amount2) * 1000
                # Detect currency - check specific symbols first
                if curr1 and curr1.upper() in ['HK$', 'HKD']:
                    currency = 'HKD'
                elif curr1 and curr1.upper() in ['A$', 'AUD']:
                    currency = 'AUD'
                elif curr1 and curr1.upper() in ['S$', 'SGD']:
                    currency = 'SGD'
                elif curr1 and curr1.upper() in ['C$', 'CAD']:
                    currency = 'CAD'
                elif curr1 and curr1 in ['£', 'GBP']:
                    currency = 'GBP'
                elif curr1 and curr1 in ['€', 'EUR']:
                    currency = 'EUR'
                elif curr1 and (curr1 == '$' or curr1.upper() == 'USD'):
                    currency = default_currency
                else:
                    currency = default_currency
            except:
                pass
    
    # Try pattern 3: Single amount (e.g., $100,000)
    # Expanded search - look in entire description, not just first 2000 chars
    if min_amount is None:
        pattern3 = r'(HK\$|A\$|S\$|C\$|[\$£€]|USD|GBP|AUD|SGD|HKD|EUR|CAD)\s*([\d,]+)'
        matches3 = list(re.finditer(pattern3, desc))
        if matches3:
            # First try near salary keywords (within 200 chars)
            found_near_keyword = False
            for kw in salary_keywords:
                kw_idx = desc_lower.find(kw)
                if kw_idx >= 0:
                    # Look for amounts near this keyword
                    search_start = max(0, kw_idx - 200)
                    search_end = min(len(desc), kw_idx + 500)
                    for match in matches3:
                        if search_start <= match.start() < search_end:
                            curr = match.group(1)
                            amount = match.group(2).replace(',', '')
                            try:
                                amount_val = float(amount)
                                # Reasonable salary range check (1k - 2M, expanded range)
                                if 1000 <= amount_val <= 2000000:
                                    min_amount = amount_val
                                    max_amount = amount_val
                                    # Detect currency - check specific symbols first
                                    if curr.upper() in ['HK$', 'HKD']:
                                        currency = 'HKD'
                                    elif curr.upper() in ['A$', 'AUD']:
                                        currency = 'AUD'
                                    elif curr.upper() in ['S$', 'SGD']:
                                        currency = 'SGD'
                                    elif curr.upper() in ['C$', 'CAD']:
                                        currency = 'CAD'
                                    elif curr in ['£', 'GBP']:
                                        currency = 'GBP'
                                    elif curr in ['€', 'EUR']:
                                        currency = 'EUR'
                                    elif curr == '$' or curr.upper() == 'USD':
                                        currency = default_currency
                                    else:
                                        for curr_code, patterns in currency_patterns.items():
                                            if any(re.search(p, curr, re.IGNORECASE) for p in patterns):
                                                currency = curr_code
                                                break
                                    found_near_keyword = True
                                    break
                            except:
                                pass
                    if found_near_keyword:
                        break
            
            # If not found near keywords, try first reasonable amount in description
            if not found_near_keyword:
                for match in matches3:
                    # Look in first 3000 chars (expanded from 2000)
                    if match.start() < 3000:
                        curr = match.group(1)
                        amount = match.group(2).replace(',', '')
                        try:
                            amount_val = float(amount)
                            # Reasonable salary range check (1k - 2M, expanded range)
                            if 1000 <= amount_val <= 2000000:
                                min_amount = amount_val
                                max_amount = amount_val
                                # Detect currency - check specific symbols first
                                if curr.upper() in ['HK$', 'HKD']:
                                    currency = 'HKD'
                                elif curr.upper() in ['A$', 'AUD']:
                                    currency = 'AUD'
                                elif curr.upper() in ['S$', 'SGD']:
                                    currency = 'SGD'
                                elif curr.upper() in ['C$', 'CAD']:
                                    currency = 'CAD'
                                elif curr in ['£', 'GBP']:
                                    currency = 'GBP'
                                elif curr in ['€', 'EUR']:
                                    currency = 'EUR'
                                elif curr == '$' or curr.upper() == 'USD':
                                    currency = default_currency
                                else:
                                    for curr_code, patterns in currency_patterns.items():
                                        if any(re.search(p, curr, re.IGNORECASE) for p in patterns):
                                            currency = curr_code
                                            break
                                break
                        except:
                            pass
    
    # Detect interval (yearly, monthly, hourly, etc.)
    if min_amount is not None:
        desc_lower_snippet = desc[max(0, desc.lower().find(str(int(min_amount)))-50):desc.lower().find(str(int(min_amount)))+200].lower()
        if any(x in desc_lower_snippet for x in ['per year', 'annually', 'annual', '/year', 'yearly']):
            interval = 'yearly'
        elif any(x in desc_lower_snippet for x in ['per month', 'monthly', '/month']):
            interval = 'monthly'
            min_amount = min_amount * 12
            max_amount = max_amount * 12 if max_amount else min_amount
        elif any(x in desc_lower_snippet for x in ['per hour', 'hourly', '/hour', '/hr']):
            interval = 'hourly'
            min_amount = min_amount * 2080  # Assume 2080 working hours per year
            max_amount = max_amount * 2080 if max_amount else min_amount
    
    # Format salary range string
    salary_range = ""
    estimated_annual = None
    
    if min_amount is not None:
        if max_amount and max_amount != min_amount:
            # Format with currency symbol
            currency_symbols = {
                'USD': '$', 'GBP': '£', 'AUD': 'A$', 'SGD': 'S$', 
                'HKD': 'HK$', 'EUR': '€', 'CAD': 'C$'
            }
            symbol = currency_symbols.get(currency, currency)
            salary_range = f"{symbol}{int(min_amount):,} - {symbol}{int(max_amount):,}"
            if interval and interval != 'yearly':
                salary_range += f" ({interval})"
            estimated_annual = (min_amount + max_amount) / 2
        else:
            currency_symbols = {
                'USD': '$', 'GBP': '£', 'AUD': 'A$', 'SGD': 'S$', 
                'HKD': 'HK$', 'EUR': '€', 'CAD': 'C$'
            }
            symbol = currency_symbols.get(currency, currency)
            salary_range = f"{symbol}{int(min_amount):,}"
            if interval and interval != 'yearly':
                salary_range += f" ({interval})"
            estimated_annual = min_amount
    
    return {
        'min_amount': min_amount,
        'max_amount': max_amount,
        'currency': currency,
        'interval': interval,
        'salary_range': salary_range,
        'estimated_annual': estimated_annual
    }


def extract_requirements_from_description(description):
    """
    Extract requirements from job description using LinkedIn logic
    Same logic as scraper_linkedin_checkpoint.py
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
        first_half = desc[:len(desc)//2]
        if re.search(r'\d+\+?\s*(?:years?|months?|yr)', first_half, re.I):
            requirements_text = first_half[:500].strip()
    
    return requirements_text


def scrape_jobspy_maximum(keywords, locations, results_per_search=100, max_total_jobs=None, min_posted_date=None, filter_ai_related=True, region_name="United States", country_indeed="usa", platform="indeed"):
    """
    Maximum JobSpy scraper with checkpoint support
    
    Args:
        keywords: List of keywords to search
        locations: List of locations to search
        results_per_search: Number of results to request per keyword+location combination
        max_total_jobs: Maximum total jobs to collect (None = no limit)
        min_posted_date: datetime object or None - filter jobs posted on or after this date
        filter_ai_related: If True, filter out non-AI related jobs (default: True)
        region_name: Region name for checkpoint and output directory (default: "United States")
        country_indeed: Country code for Indeed search (default: "usa") - only used for Indeed
        platform: Platform to scrape from - "indeed", "linkedin", or "both" (default: "indeed")
    
    Returns:
        List of job dictionaries
    """
    print("="*60)
    platform_display = platform.upper() if platform != "both" else "Indeed + LinkedIn"
    print(f"JobSpy Maximum Scraper - {platform_display} Jobs ({region_name})")
    print("="*60)
    
    # Initialize exchange rates before scraping
    initialize_exchange_rates()
    
    start_time = time.time()
    
    try:
        from jobspy import scrape_jobs
        print("[OK] JobSpy imported successfully")
    except ImportError:
        print("[ERROR] JobSpy not available. Please install: pip install python-jobspy")
        return None
    
    # Load checkpoint for this region
    checkpoint = load_checkpoint(region_name)
    if checkpoint:
        print(f"\n[CHECKPOINT] Resuming from previous run for {region_name}...")
        print(f"  Last position: Keyword {checkpoint['keyword_idx']+1}/{len(keywords)}, Location {checkpoint['location_idx']+1}/{len(locations)}")
        print(f"  Previous jobs: {checkpoint['total_jobs']}")
        start_keyword_idx = checkpoint['keyword_idx']
        start_location_idx = checkpoint['location_idx']
        # Support both old format (seen_urls) and new format (seen_job_keys)
        if 'seen_job_keys' in checkpoint:
            seen_job_keys = set(checkpoint.get('seen_job_keys', []))
        else:
            # Migration: if old checkpoint exists, rebuild seen_job_keys from all_jobs
            print("  [INFO] Migrating from URL-based to key-based deduplication...")
            all_jobs = load_raw_data(region_name)
            seen_job_keys = set()
            for job in all_jobs:
                job_key = generate_job_key(job)
                if job_key:
                    seen_job_keys.add(job_key)
            print(f"  [INFO] Rebuilt {len(seen_job_keys)} job keys from existing jobs")
        all_jobs = load_raw_data(region_name)
    else:
        start_keyword_idx = 0
        start_location_idx = 0
        seen_job_keys = set()
        all_jobs = []
    
    # Determine which platforms to scrape
    platforms_to_scrape = []
    if platform == "both":
        platforms_to_scrape = ["indeed", "linkedin"]
    elif platform in ["indeed", "linkedin"]:
        platforms_to_scrape = [platform]
    else:
        print(f"[WARNING] Unknown platform '{platform}', defaulting to 'indeed'")
        platforms_to_scrape = ["indeed"]
    
    print(f"\nConfiguration:")
    print(f"  Platform(s): {', '.join([p.upper() for p in platforms_to_scrape])}")
    print(f"  Keywords: {len(keywords)} keywords")
    print(f"  Locations: {len(locations)} locations")
    print(f"  Results per search: {results_per_search}")
    total_combinations = len(keywords) * len(locations) * len(platforms_to_scrape)
    print(f"  Total combinations: {total_combinations} (keywords × locations × platforms)")
    if max_total_jobs:
        print(f"  Max total jobs: {max_total_jobs}")
    if min_posted_date:
        print(f"  Date filter: Only jobs posted on or after {min_posted_date.strftime('%Y-%m-%d')} (applied during scraping)")
    if filter_ai_related:
        print(f"  AI filter: Enabled (only AI-related jobs will be kept)")
    else:
        print(f"  AI filter: Disabled (all jobs will be kept)")
    print()
    
    total_requests = 0
    successful_requests = 0
    failed_requests = 0
    last_save_time = time.time()
    
    # Scrape all keyword+location combinations
    for keyword_idx, keyword in enumerate(keywords):
        if max_total_jobs and len(all_jobs) >= max_total_jobs:
            print(f"\nReached max total jobs limit ({max_total_jobs}), stopping...")
            break
        
        # Skip if before checkpoint
        if keyword_idx < start_keyword_idx:
            continue
        
        # Reset location index for new keyword (unless resuming)
        if keyword_idx == start_keyword_idx:
            location_start_idx = start_location_idx
        else:
            location_start_idx = 0
        
        for location_idx, location in enumerate(locations):
            if max_total_jobs and len(all_jobs) >= max_total_jobs:
                break
            
            # Skip if before checkpoint
            if keyword_idx == start_keyword_idx and location_idx < location_start_idx:
                continue
            
            # Scrape from each platform
            for platform_name in platforms_to_scrape:
                if max_total_jobs and len(all_jobs) >= max_total_jobs:
                    break
                
                total_requests += 1
                total_combos = len(keywords) * len(locations) * len(platforms_to_scrape)
                progress = f"[{total_requests}/{total_combos}]"
                current_progress = f"Keyword {keyword_idx+1}/{len(keywords)}, Location {location_idx+1}/{len(locations)}, Platform: {platform_name.upper()}"
                
                print(f"{progress} {current_progress}: '{keyword}' in '{location}'...", end=" ")
                
                try:
                    # Prepare scrape_jobs parameters
                    scrape_params = {
                        "site_name": platform_name,
                        "search_term": keyword,
                        "location": location,
                        "results_wanted": results_per_search,
                    }
                    
                    # Add platform-specific parameters
                    if platform_name == "indeed":
                        scrape_params["country_indeed"] = country_indeed
                    elif platform_name == "linkedin":
                        # LinkedIn-specific parameters (if needed)
                        # scrape_params["linkedin_fetch_description"] = True
                        pass
                    
                    jobs = scrape_jobs(**scrape_params)
                    
                    if isinstance(jobs, pd.DataFrame):
                        if not jobs.empty:
                            new_jobs = jobs.to_dict('records')
                            # Add platform identifier to each job
                            for job in new_jobs:
                                job['_source_platform'] = platform_name
                            
                            # Deduplicate based on title + company + location
                            unique_new = []
                            duplicate_count = 0
                            for job in new_jobs:
                                job_key = generate_job_key(job)
                                if job_key and job_key not in seen_job_keys:
                                    seen_job_keys.add(job_key)
                                    unique_new.append(job)
                                else:
                                    duplicate_count += 1
                            
                            # Apply date filter immediately if specified
                            if min_posted_date:
                                unique_new = filter_jobs_by_date(unique_new, min_posted_date)
                            
                            # Apply AI relevance filter to keep only AI-related jobs
                            if filter_ai_related:
                                before_ai_filter = len(unique_new)
                                unique_new = filter_ai_related_jobs(unique_new, verbose=False)
                                if len(unique_new) < before_ai_filter:
                                    print(f" (AI filtered: {before_ai_filter} -> {len(unique_new)})", end="")
                            
                            all_jobs.extend(unique_new)
                            successful_requests += 1
                            if duplicate_count > 0:
                                print(f"[OK] {len(new_jobs)} jobs, {len(unique_new)} new unique, {duplicate_count} duplicates (total: {len(all_jobs)})")
                            else:
                                print(f"[OK] {len(new_jobs)} jobs, {len(unique_new)} new unique (total: {len(all_jobs)})")
                        else:
                            print(f"[SKIP] No jobs found")
                    else:
                        print(f"[ERROR] Unexpected return type")
                        
                except Exception as e:
                    failed_requests += 1
                    error_msg = str(e)[:50]
                    print(f"[ERROR] {error_msg}")
            
            # Save checkpoint and raw data every 10 requests or every 5 minutes
            current_time = time.time()
            if (total_requests % 10 == 0) or (current_time - last_save_time > 300):
                save_checkpoint(region_name, keyword_idx, location_idx, seen_job_keys, all_jobs)
                save_raw_data(region_name, all_jobs)
                last_save_time = current_time
                print(f"  [SAVED] Checkpoint saved ({len(all_jobs)} jobs, {len(seen_job_keys)} unique keys)")
            
            # Small delay between requests
            time.sleep(0.3)
    
    # Final save
    save_checkpoint(region_name, len(keywords), len(locations), seen_job_keys, all_jobs)
    save_raw_data(region_name, all_jobs)
    
    elapsed_time = time.time() - start_time
    
    print(f"\n{'='*60}")
    print("Scraping Summary")
    print(f"{'='*60}")
    print(f"Total requests: {total_requests}")
    print(f"Successful: {successful_requests}")
    print(f"Failed: {failed_requests}")
    print(f"Total unique jobs: {len(all_jobs)}")
    if min_posted_date:
        print(f"Date filter applied: Only jobs posted on or after {min_posted_date.strftime('%Y-%m-%d')}")
    print(f"Elapsed time: {elapsed_time:.2f} seconds ({elapsed_time/60:.1f} minutes)")
    print(f"Average time per request: {elapsed_time/total_requests:.2f} seconds" if total_requests > 0 else "N/A")
    print(f"{'='*60}\n")
    
    return all_jobs


def map_to_template_format(jobs, region_name=None):
    """
    Map JobSpy jobs to example_output.xlsx format
    Extract Requirements from description
    Extract Salary from description if structured fields are empty
    
    Args:
        jobs: List of job dictionaries
        region_name: Region name to help identify currency (optional)
    """
    print("Mapping to template format and extracting Requirements and Salary...")
    
    mapped_data = {}
    for field in EXPECTED_FIELDS:
        mapped_data[field] = []
    
    # Region to currency mapping
    region_currency_map = {
        'United States': 'USD',
        'United Kingdom': 'GBP',
        'Australia': 'AUD',
        'Singapore': 'SGD',
        'Hong Kong': 'HKD',
    }
    default_currency = region_currency_map.get(region_name, 'USD')
    
    for idx, job in enumerate(jobs):
        if (idx + 1) % 500 == 0:
            print(f"  Processing {idx + 1}/{len(jobs)}...")
        
        # Job Title
        mapped_data["Job Title"].append(job.get("title", ""))
        
        # Company Name
        company = job.get("company", "")
        if pd.isna(company):
            company = ""
        mapped_data["Company Name"].append(str(company))
        
        # Requirements - Extract from description using LinkedIn logic
        description = job.get("description", "")
        requirements = extract_requirements_from_description(description)
        mapped_data["Requirements"].append(requirements)
        
        # Location
        mapped_data["Location"].append(job.get("location", ""))
        
        # Salary Range - Try structured fields first, then extract from description
        min_amount = job.get("min_amount", "")
        max_amount = job.get("max_amount", "")
        interval = job.get("interval", "")
        currency = job.get("currency", "")
        
        salary_range = ""
        estimated_annual = ""
        estimated_annual_usd = ""
        extracted_currency = None
        
        # Method 1: Use structured fields from JobSpy (if available)
        if pd.notna(min_amount) and pd.notna(max_amount):
            try:
                min_val = float(min_amount)
                max_val = float(max_amount)
                # Detect currency from job data or use region default
                if currency and pd.notna(currency):
                    extracted_currency = str(currency).upper()
                else:
                    extracted_currency = default_currency
                
                # Convert to annual salary based on interval
                interval_str = str(interval).lower() if interval and pd.notna(interval) else ""
                original_min = min_val
                original_max = max_val
                
                if 'monthly' in interval_str:
                    # Convert monthly to annual
                    min_val = min_val * 12
                    max_val = max_val * 12 if max_val else min_val
                elif 'hourly' in interval_str or '/hr' in interval_str or 'per hour' in interval_str:
                    # Convert hourly to annual (assume 2080 working hours per year)
                    min_val = min_val * 2080
                    max_val = max_val * 2080 if max_val else min_val
                # If yearly or no interval specified, use values as-is
                
                # Format salary range (show original values with interval for display)
                currency_symbols = {
                    'USD': '$', 'GBP': '£', 'AUD': 'A$', 'SGD': 'S$', 
                    'HKD': 'HK$', 'EUR': '€', 'CAD': 'C$'
                }
                symbol = currency_symbols.get(extracted_currency, extracted_currency)
                
                if interval and pd.notna(interval):
                    salary_range = f"{symbol}{int(original_min):,} - {symbol}{int(original_max):,} ({interval})"
                else:
                    salary_range = f"{symbol}{int(original_min):,} - {symbol}{int(original_max):,}"
                
                # Calculate annual average (using converted values)
                avg = (min_val + max_val) / 2
                estimated_annual = f"{symbol}{int(avg):,}"
                
                # Convert to USD
                if extracted_currency != "USD":
                    exchange_rate = get_exchange_rate(extracted_currency, "USD")
                    avg_usd = avg * exchange_rate
                    estimated_annual_usd = f"${int(avg_usd):,}"
                else:
                    estimated_annual_usd = f"${int(avg):,}"
            except (ValueError, TypeError):
                pass
        
        # Method 2: Extract from description if structured fields are empty
        if not salary_range and description:
            salary_info = extract_salary_from_description(description, region_name)
            
            if salary_info['salary_range']:
                salary_range = salary_info['salary_range']
                if salary_info['estimated_annual']:
                    extracted_currency = salary_info['currency']
                    currency_symbols = {
                        'USD': '$', 'GBP': '£', 'AUD': 'A$', 'SGD': 'S$', 
                        'HKD': 'HK$', 'EUR': '€', 'CAD': 'C$'
                    }
                    symbol = currency_symbols.get(extracted_currency, extracted_currency)
                    estimated_annual = f"{symbol}{int(salary_info['estimated_annual']):,}"
                    
                    # Convert to USD
                    if extracted_currency and extracted_currency != "USD":
                        exchange_rate = get_exchange_rate(extracted_currency, "USD")
                        avg_usd = salary_info['estimated_annual'] * exchange_rate
                        estimated_annual_usd = f"${int(avg_usd):,}"
                    else:
                        estimated_annual_usd = f"${int(salary_info['estimated_annual']):,}"
        
        mapped_data["Salary Range"].append(salary_range)
        mapped_data["Estimated Annual Salary"].append(estimated_annual)
        mapped_data["Estimated Annual Salary (USD)"].append(estimated_annual_usd)
        
        # Job Description
        mapped_data["Job Description"].append(description)
        
        # Team Size/Business Line Size - JobSpy doesn't provide
        mapped_data["Team Size/Business Line Size"].append("")
        
        # Company Size
        company_size = job.get("company_num_employees", "")
        if pd.notna(company_size) and company_size:
            mapped_data["Company Size"].append(str(company_size))
        else:
            mapped_data["Company Size"].append("")
        
        # Posted Date
        date_posted = job.get("date_posted", "")
        mapped_data["Posted Date"].append(str(date_posted) if pd.notna(date_posted) else "")
        
        # Job Status
        employment_type = job.get("employment_type", "")
        if pd.notna(employment_type) and employment_type:
            mapped_data["Job Status"].append(employment_type)
        else:
            mapped_data["Job Status"].append("Active")
        
        # Platform - use actual source platform if available, otherwise default to "Indeed"
        source_platform = job.get("_source_platform", "Indeed")
        # Capitalize first letter for consistency
        if source_platform.lower() == "indeed":
            platform_display = "Indeed"
        elif source_platform.lower() == "linkedin":
            platform_display = "LinkedIn"
        else:
            platform_display = source_platform.capitalize() if source_platform else "Indeed"
        mapped_data["Platform"].append(platform_display)
        
        # Job Link
        mapped_data["Job Link"].append(job.get("job_url", ""))
    
    # Create DataFrame with exact field order
    df_mapped = pd.DataFrame(mapped_data)
    df_mapped = df_mapped[EXPECTED_FIELDS]  # Ensure exact order
    
    return df_mapped


def save_to_supabase(df, region_name):
    """
    Save jobs DataFrame to Supabase database
    Appends new jobs to existing table (does not overwrite)
    Deduplicates based on job_title + company_name
    
    Args:
        df: DataFrame with job data
        region_name: Region name to determine table name
    """
    try:
        from supabase import create_client, Client
    except ImportError:
        print("[WARNING] supabase package not installed. Install with: pip install supabase")
        return
    
    try:
        import supabase_config
        supabase_url = getattr(supabase_config, 'SUPABASE_URL', None)
        # Prefer service_role key for writes (bypasses RLS policies)
        # If service_role is not available, fall back to anon key
        supabase_key = getattr(supabase_config, 'SUPABASE_SERVICE_KEY', None)
        if not supabase_key:
            supabase_key = getattr(supabase_config, 'SUPABASE_KEY', None)
        region_table_map = getattr(supabase_config, 'REGION_TABLE_MAP', {})
    except ImportError:
        print("[WARNING] supabase_config.py not found. Please create it from supabase_config.py.template")
        return
    
    if not supabase_url or not supabase_key:
        print("[WARNING] Supabase URL or Key not configured in supabase_config.py")
        return
    
    # Warn if using anon key (may be blocked by RLS policies)
    try:
        import supabase_config
        if hasattr(supabase_config, 'SUPABASE_SERVICE_KEY') and not supabase_config.SUPABASE_SERVICE_KEY:
            print("[INFO] Using anon key for writes. If RLS policies are enabled, writes may be blocked.")
            print("[INFO] Consider using SUPABASE_SERVICE_KEY for write operations.")
    except:
        pass
    
    # Get table name for this region
    table_name = region_table_map.get(region_name)
    if not table_name:
        # Generate table name from region name
        table_name = f"jobs_{region_name.replace(' ', '_').lower()}"
        print(f"[INFO] Using auto-generated table name: {table_name}")
    
    print(f"\n{'='*60}")
    print(f"Saving to Supabase: {table_name}")
    print(f"{'='*60}")
    
    try:
        supabase: Client = create_client(supabase_url, supabase_key)
        
        print(f"  Total jobs to process: {len(df)}")
        
        # Step 1: Batch fetch all existing job_title + company_name combinations
        # This is much faster than checking each row individually
        print("  Fetching existing records for deduplication...")
        existing_keys = set()
        try:
            # Fetch in batches (Supabase has a limit on how many records can be returned at once)
            # We'll fetch all existing job_title + company_name pairs
            offset = 0
            batch_size_fetch = 1000
            max_fetch = 50000  # Safety limit
            
            while offset < max_fetch:
                try:
                    result = supabase.table(table_name).select("job_title, company_name").range(offset, offset + batch_size_fetch - 1).execute()
                    if not result.data or len(result.data) == 0:
                        break
                    
                    for record in result.data:
                        job_title = str(record.get('job_title', '')).strip()
                        company_name = str(record.get('company_name', '')).strip()
                        if job_title and company_name:
                            # Create a normalized key for comparison (case-insensitive)
                            key = f"{job_title.lower()}|||{company_name.lower()}"
                            existing_keys.add(key)
                    
                    print(f"    Fetched {offset + len(result.data)} existing records...")
                    
                    if len(result.data) < batch_size_fetch:
                        break
                    
                    offset += batch_size_fetch
                except Exception as e:
                    print(f"    Warning: Error fetching batch at offset {offset}: {str(e)[:100]}")
                    break
            
            print(f"  Found {len(existing_keys)} existing job records")
        except Exception as e:
            print(f"  Warning: Could not fetch existing records: {str(e)[:100]}")
            print(f"  Will proceed with insert (duplicates will be handled by database constraints)")
        
        # Step 2: Filter out duplicates and prepare data for insertion
        jobs_to_insert = []
        skipped_invalid = 0
        skipped_duplicates = 0
        
        print("  Processing and filtering jobs...")
        for idx, row in df.iterrows():
            job_title = str(row.get('Job Title', '')).strip()
            company_name = str(row.get('Company Name', '')).strip()
            
            # Skip if missing required fields
            if not job_title or not company_name:
                skipped_invalid += 1
                continue
            
            # Check if already exists (using normalized key)
            key = f"{job_title.lower()}|||{company_name.lower()}"
            if key in existing_keys:
                skipped_duplicates += 1
                continue
            
            # Prepare job data for insertion
            job_data = {
                "job_title": job_title,
                "company_name": company_name,
                "requirements": str(row.get('Requirements', '')) if pd.notna(row.get('Requirements')) else None,
                "location": str(row.get('Location', '')) if pd.notna(row.get('Location')) else None,
                "salary_range": str(row.get('Salary Range', '')) if pd.notna(row.get('Salary Range')) else None,
                "estimated_annual_salary": str(row.get('Estimated Annual Salary', '')) if pd.notna(row.get('Estimated Annual Salary')) else None,
                "estimated_annual_salary_usd": str(row.get('Estimated Annual Salary (USD)', '')) if pd.notna(row.get('Estimated Annual Salary (USD)')) else None,
                "job_description": str(row.get('Job Description', '')) if pd.notna(row.get('Job Description')) else None,
                "team_size": str(row.get('Team Size/Business Line Size', '')) if pd.notna(row.get('Team Size/Business Line Size')) else None,
                "company_size": str(row.get('Company Size', '')) if pd.notna(row.get('Company Size')) else None,
                "posted_date": str(row.get('Posted Date', '')) if pd.notna(row.get('Posted Date')) else None,
                "job_status": str(row.get('Job Status', '')) if pd.notna(row.get('Job Status')) else None,
                "platform": str(row.get('Platform', '')) if pd.notna(row.get('Platform')) else None,
                "job_link": str(row.get('Job Link', '')) if pd.notna(row.get('Job Link')) else None,
            }
            
            jobs_to_insert.append(job_data)
            # Add to existing_keys to avoid duplicates within the same batch
            existing_keys.add(key)
        
        print(f"  Jobs to insert: {len(jobs_to_insert)}")
        print(f"  Skipped (invalid): {skipped_invalid}")
        print(f"  Skipped (duplicates): {skipped_duplicates}")
        
        # Step 3: Insert in batches with retry logic
        batch_size = 100
        total_inserted = 0
        failed_batches = []
        
        print(f"\n  Inserting {len(jobs_to_insert)} jobs in batches of {batch_size}...")
        for i in range(0, len(jobs_to_insert), batch_size):
            batch = jobs_to_insert[i:i+batch_size]
            batch_num = i//batch_size + 1
            total_batches = (len(jobs_to_insert) + batch_size - 1) // batch_size
            
            try:
                result = supabase.table(table_name).insert(batch).execute()
                total_inserted += len(batch)
                if batch_num % 10 == 0 or batch_num == total_batches:
                    print(f"    Batch {batch_num}/{total_batches}: {len(batch)} jobs inserted (total: {total_inserted})")
            except Exception as e:
                error_msg = str(e)
                if "duplicate key" in error_msg.lower() or "unique constraint" in error_msg.lower():
                    # Try inserting one by one to identify which ones are duplicates
                    print(f"    Batch {batch_num}: Duplicate detected, inserting individually...")
                    individual_inserted = 0
                    for job in batch:
                        try:
                            supabase.table(table_name).insert(job).execute()
                            individual_inserted += 1
                            total_inserted += 1
                        except Exception as e2:
                            # Skip this individual job if it's a duplicate
                            if "duplicate" not in str(e2).lower() and "unique constraint" not in str(e2).lower():
                                print(f"      Individual insert error: {str(e2)[:80]}")
                    if individual_inserted > 0:
                        print(f"    Batch {batch_num}: {individual_inserted}/{len(batch)} jobs inserted individually")
                else:
                    # For other errors, try smaller batches or individual inserts
                    print(f"    Batch {batch_num}: Error - {error_msg[:100]}")
                    print(f"    Attempting individual inserts for this batch...")
                    individual_inserted = 0
                    for job in batch:
                        try:
                            supabase.table(table_name).insert(job).execute()
                            individual_inserted += 1
                            total_inserted += 1
                        except Exception as e2:
                            failed_batches.append(job)
                            if len(failed_batches) <= 5:  # Only show first 5 errors
                                print(f"      Failed: {job.get('job_title', 'N/A')[:30]}... - {str(e2)[:60]}")
                    if individual_inserted > 0:
                        print(f"    Batch {batch_num}: {individual_inserted}/{len(batch)} jobs inserted individually")
        
        print(f"\n  Summary:")
        print(f"    Total processed: {len(df)}")
        print(f"    Total inserted: {total_inserted}")
        print(f"    Skipped (invalid): {skipped_invalid}")
        print(f"    Skipped (duplicates): {skipped_duplicates}")
        if failed_batches:
            print(f"    Failed to insert: {len(failed_batches)}")
        print(f"{'='*60}\n")
        
    except Exception as e:
        print(f"[ERROR] Failed to save to Supabase: {str(e)[:200]}")
        import traceback
        traceback.print_exc()


def scrape_region(region_name, country_code, keywords, results_per_search, max_total_jobs, parsed_min_date, filter_ai_related, platform="indeed"):
    """
    Scrape jobs for a specific region with cross-platform deduplication
    
    If platform="both", will scrape from both Indeed and LinkedIn separately,
    then deduplicate based on job_title + company_name, and combine into one table.
    """
    print(f"\n{'='*80}")
    print(f"Processing Region: {region_name}")
    print(f"{'='*80}")
    
    # Get locations for this region
    locations = get_locations_by_region(region_name)
    if not locations:
        print(f"[WARNING] No locations found for {region_name}, skipping...")
        return None
    
    # Get region-specific output directory
    region_dir = get_region_output_dir(region_name)
    region_output_file = f"{region_dir}/jobspy_max_output.xlsx"
    
    print(f"\nRegion Configuration:")
    print(f"  Region: {region_name}")
    print(f"  Country code: {country_code}")
    print(f"  Keywords: {len(keywords)} keywords")
    print(f"  Locations: {len(locations)} locations")
    print(f"  Results per search: {results_per_search}")
    print(f"  Platform: {platform}")
    print(f"  Output directory: {region_dir}")
    print()
    
    # Determine which platforms to scrape
    platforms_to_scrape = []
    if platform == "both":
        platforms_to_scrape = ["indeed", "linkedin"]
    elif platform in ["indeed", "linkedin"]:
        platforms_to_scrape = [platform]
    else:
        platforms_to_scrape = ["indeed"]  # Default
    
    # Scrape from each platform separately
    df_indeed = None
    df_linkedin = None
    
    for platform_name in platforms_to_scrape:
        print(f"\n{'='*60}")
        print(f"Scraping from {platform_name.upper()} for {region_name}")
        print(f"{'='*60}")
        
        all_jobs = scrape_jobspy_maximum(
            keywords=keywords,
            locations=locations,
            results_per_search=results_per_search,
            max_total_jobs=max_total_jobs,
            min_posted_date=parsed_min_date,
            filter_ai_related=filter_ai_related,
            region_name=region_name,
            country_indeed=country_code,
            platform=platform_name
        )
        
        if not all_jobs:
            print(f"[WARNING] No jobs scraped from {platform_name} for {region_name}")
            continue
        
        # Map to template format
        print(f"\nProcessing and Formatting Data from {platform_name.upper()}...")
        df_platform = map_to_template_format(all_jobs, region_name=region_name)
        
        if platform_name == "indeed":
            df_indeed = df_platform
        elif platform_name == "linkedin":
            df_linkedin = df_platform
    
    # Cross-platform deduplication if both platforms were scraped
    if platform == "both" and df_indeed is not None and df_linkedin is not None:
        df_indeed, df_linkedin, df_final = deduplicate_cross_platform(df_indeed, df_linkedin)
    elif df_indeed is not None:
        df_final = df_indeed
    elif df_linkedin is not None:
        df_final = df_linkedin
    else:
        print(f"[WARNING] No jobs scraped for {region_name}")
        return None
    
    # Calculate completeness
    print(f"\n{'='*60}")
    print(f"Final Completeness Statistics for {region_name}")
    print(f"{'='*60}")
    
    total_jobs = len(df_final)
    stats = {}
    
    for field in EXPECTED_FIELDS:
        non_empty = df_final[field].notna() & (df_final[field] != "")
        count = non_empty.sum()
        percentage = (count / total_jobs * 100) if total_jobs > 0 else 0
        stats[field] = {"count": count, "percentage": percentage}
        print(f"  {field}: {count}/{total_jobs} ({percentage:.1f}%)")
    
    total_fields = len(EXPECTED_FIELDS) * total_jobs
    filled_fields = sum(stats[f]["count"] for f in EXPECTED_FIELDS)
    overall_completeness = (filled_fields / total_fields * 100) if total_fields > 0 else 0
    print(f"\n  Overall Completeness: {overall_completeness:.1f}%")
    
    # Save to Excel in region-specific directory
    os.makedirs(region_dir, exist_ok=True)
    df_final.to_excel(region_output_file, index=False)
    
    # Save to Supabase if enabled
    try:
        import config_jobspy
        enable_supabase = getattr(config_jobspy, 'ENABLE_SUPABASE', False)
    except:
        enable_supabase = False
    
    if enable_supabase:
        try:
            save_to_supabase(df_final, region_name)
        except Exception as e:
            print(f"[WARNING] Failed to save to Supabase: {str(e)[:100]}")
            print(f"[INFO] Data still saved to Excel: {region_output_file}")
    
    print(f"\n{'='*60}")
    print(f"Results for {region_name}")
    print(f"{'='*60}")
    print(f"Output file: {region_output_file}")
    print(f"Total jobs: {total_jobs}")
    print(f"Overall completeness: {overall_completeness:.1f}%")
    if enable_supabase:
        print(f"Supabase: Data saved successfully")
    print(f"{'='*60}\n")
    
    print(f"[OK] Complete! Output saved to: {region_output_file}")
    return df_final


def main():
    """Main function"""
    print("="*80)
    print("JobSpy Maximum Scraper - Indeed Jobs (Multi-Region Support)")
    print("="*80)
    print(f"RUN_ID: {JOBSPY_RUN_ID}")
    print(f"Base output directory: {JOBSPY_OUTPUT_DIR}")
    
    # Try to load jobspy-specific config, fall back to defaults
    try:
        import config_jobspy
        results_per_search = getattr(config_jobspy, 'RESULTS_PER_SEARCH', 100)
        max_total_jobs = getattr(config_jobspy, 'MAX_TOTAL_JOBS', None)
        min_posted_date = getattr(config_jobspy, 'MIN_POSTED_DATE', None)
        filter_ai_related = getattr(config_jobspy, 'FILTER_AI_RELATED', True)
        
        # Platform selection
        enable_indeed = getattr(config_jobspy, 'ENABLE_INDEED', True)
        enable_linkedin = getattr(config_jobspy, 'ENABLE_LINKEDIN', False)
        
        # Determine platform string
        if enable_indeed and enable_linkedin:
            platform = "both"
        elif enable_linkedin:
            platform = "linkedin"
        else:
            platform = "indeed"  # Default to indeed if both False
        
        # Region selection
        enable_us = getattr(config_jobspy, 'ENABLE_US', True)
        enable_uk = getattr(config_jobspy, 'ENABLE_UK', False)
        enable_australia = getattr(config_jobspy, 'ENABLE_AUSTRALIA', False)
        enable_hong_kong = getattr(config_jobspy, 'ENABLE_HONG_KONG', False)
        enable_singapore = getattr(config_jobspy, 'ENABLE_SINGAPORE', False)
    except ImportError:
        results_per_search = 100
        max_total_jobs = None
        min_posted_date = None
        filter_ai_related = True
        platform = "indeed"  # Default
        enable_us = True
        enable_uk = False
        enable_australia = False
        enable_hong_kong = False
        enable_singapore = False
    
    # Get country codes
    try:
        from locations_config import COUNTRY_CODES
    except:
        COUNTRY_CODES = {
            "United States": "usa",
            "United Kingdom": "uk",
            "Australia": "australia",
            "Hong Kong": "hong kong",
            "Singapore": "singapore",
        }
    
    # Define regions to process
    regions_to_process = []
    if enable_us:
        regions_to_process.append(("United States", COUNTRY_CODES.get("United States", "usa")))
    if enable_uk:
        regions_to_process.append(("United Kingdom", COUNTRY_CODES.get("United Kingdom", "uk")))
    if enable_australia:
        regions_to_process.append(("Australia", COUNTRY_CODES.get("Australia", "australia")))
    if enable_hong_kong:
        regions_to_process.append(("Hong Kong", COUNTRY_CODES.get("Hong Kong", "hong kong")))
    if enable_singapore:
        regions_to_process.append(("Singapore", COUNTRY_CODES.get("Singapore", "singapore")))
    
    if not regions_to_process:
        print("\n[WARNING] No regions enabled in config. Please enable at least one region in config_jobspy.py")
        return
    
    # Configuration - MAXIMUM settings
    keywords = ALL_KEYWORDS  # All keywords (core + AI-related)
    
    print(f"\nGlobal Configuration:")
    print(f"  Keywords: {len(keywords)} keywords")
    print(f"  Results per search: {results_per_search}")
    if max_total_jobs:
        print(f"  Max total jobs per region: {max_total_jobs}")
    if min_posted_date:
        parsed_min_date = parse_posted_date(str(min_posted_date))
        if parsed_min_date:
            print(f"  Date filter: Only jobs posted on or after {parsed_min_date.strftime('%Y-%m-%d')}")
        else:
            print(f"  Date filter: Invalid date format '{min_posted_date}', will be ignored")
            parsed_min_date = None
    else:
        parsed_min_date = None
        print(f"  Date filter: None (all jobs will be processed)")
    if filter_ai_related:
        print(f"  AI filter: Enabled (only AI-related jobs will be kept)")
    else:
        print(f"  AI filter: Disabled (all jobs will be kept)")
    
    print(f"\nRegions to process: {len(regions_to_process)}")
    for region_name, _ in regions_to_process:
        print(f"  - {region_name}")
    print()
    
    # Parse date filter if specified
    if min_posted_date and not parsed_min_date:
        parsed_min_date = parse_posted_date(str(min_posted_date))
        if parsed_min_date is None:
            print(f"Warning: Invalid date format in config_jobspy.MIN_POSTED_DATE: '{min_posted_date}', ignoring date filter")
            parsed_min_date = None
    
    # Process each region
    all_results = {}
    for region_name, country_code in regions_to_process:
        try:
            result = scrape_region(
                region_name=region_name,
                country_code=country_code,
                keywords=keywords,
                results_per_search=results_per_search,
                max_total_jobs=max_total_jobs,
                parsed_min_date=parsed_min_date,
                filter_ai_related=filter_ai_related,
                platform=platform
            )
            if result is not None:
                all_results[region_name] = result
        except Exception as e:
            print(f"\n[ERROR] Failed to process {region_name}: {str(e)}")
            import traceback
            traceback.print_exc()
            continue
    
    # Final summary
    print(f"\n{'='*80}")
    print("Final Summary")
    print(f"{'='*80}")
    print(f"Total regions processed: {len(all_results)}")
    for region_name, df in all_results.items():
        print(f"  {region_name}: {len(df)} jobs")
    print(f"{'='*80}\n")
    
    print(f"[OK] All regions completed!")
    print(f"\nNote: If interrupted, run again to resume from checkpoint for each region")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Program stopped by user")
        print("Progress has been saved. Run again to resume from checkpoint.")
    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()

