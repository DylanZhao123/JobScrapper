# -*- coding: utf-8 -*-
"""
JobSpy Data Detailed Enrichment - Supplement with API calls
Only fetches details for jobs missing company name or company size
"""
import os
import sys
import time
import re
import json
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import requests

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_zenrows_api_key, ZENROWS_BASE_URL

# Test configuration
TEST_OUTPUT_DIR = "test_jobspy/output"
TEST_INPUT_FILE = f"{TEST_OUTPUT_DIR}/jobspy_indeed_200_enriched.xlsx"
TEST_FINAL_FILE = f"{TEST_OUTPUT_DIR}/jobspy_indeed_200_final.xlsx"
TEST_CACHE_FILE = f"{TEST_OUTPUT_DIR}/company_cache.json"
REQUEST_DELAY = 0.5

# Expected fields
EXPECTED_FIELDS = [
    "Job Title", "Company Name", "Requirements", "Location",
    "Salary Range", "Estimated Annual Salary", "Job Description",
    "Team Size/Business Line Size", "Company Size",
    "Posted Date", "Job Status",
    "Platform", "Job Link"
]


def zenrows_get(url, retries=3, delay=2):
    """ZenRows request with retry mechanism"""
    api_key = get_zenrows_api_key()
    for attempt in range(retries):
        try:
            params = {
                'url': url,
                'apikey': api_key,
                'js_render': 'true',
                'premium_proxy': 'true',
            }
            r = requests.get(ZENROWS_BASE_URL, params=params, timeout=60)
            if r.status_code == 200:
                return r.text
            elif r.status_code == 400:
                params_simple = {'url': url, 'apikey': api_key}
                r2 = requests.get(ZENROWS_BASE_URL, params=params_simple, timeout=60)
                if r2.status_code == 200:
                    return r2.text
        except:
            pass
        if attempt < retries - 1:
            time.sleep(delay * (attempt + 1))
    return None


def load_cache():
    """Load company cache"""
    try:
        with open(TEST_CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def save_cache(cache):
    """Save company cache"""
    os.makedirs(os.path.dirname(TEST_CACHE_FILE), exist_ok=True)
    with open(TEST_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def extract_company_name_from_page(job_url, cache):
    """Extract company name from job detail page"""
    if not job_url or pd.isna(job_url):
        return ""
    
    cache_key = f"company_name_{job_url}"
    if cache_key in cache:
        return cache[cache_key]
    
    html = zenrows_get(job_url)
    if not html:
        cache[cache_key] = ""
        save_cache(cache)
        return ""
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Try multiple selectors
    company_selectors = [
        ('a', {'data-testid': 'job-company-name'}),
        ('span', {'data-testid': 'job-company-name'}),
        ('div', {'data-testid': 'job-company-name'}),
        ('a', {'class': re.compile(r'company', re.I)}),
        ('span', {'class': re.compile(r'company', re.I)}),
    ]
    
    for tag, attrs in company_selectors:
        elem = soup.find(tag, attrs)
        if elem:
            company = elem.get_text(strip=True)
            if company and len(company) > 1 and len(company) < 50:
                cache[cache_key] = company
                save_cache(cache)
                return company
    
    cache[cache_key] = ""
    save_cache(cache)
    return ""


def extract_employee_number(text):
    """Extract employee count from text"""
    if not text or pd.isna(text):
        return ""
    
    employee_pattern = re.search(r'(\d{1,2}(?:,\d{3})+|\d{1,3})\s*employees?', str(text), re.I)
    if employee_pattern:
        employee_count = employee_pattern.group(1).replace(',', '').replace('.', '')
        try:
            employee_num = int(employee_count)
            if 1 <= employee_num <= 1000000 and not (2020 <= employee_num <= 2030):
                return str(employee_num)
        except ValueError:
            pass
    
    return ""


def get_company_size_from_page(company_name, job_url, cache):
    """Get company size from company page"""
    if not company_name or pd.isna(company_name) or not str(company_name).strip():
        return ""
    
    if company_name in cache and isinstance(cache[company_name], str) and cache[company_name].isdigit():
        return cache[company_name]
    
    # Try Indeed company page
    if company_name:
        company_slug = str(company_name).lower().replace(' ', '-').replace('.', '').replace(',', '').replace("'", "").replace('&', 'and')
        company_url = f"https://www.indeed.com/cmp/{company_slug}"
        
        html = zenrows_get(company_url)
        if html:
            soup = BeautifulSoup(html, "html.parser")
            
            employee_texts = soup.find_all(string=re.compile(r'\d+.*employee', re.I))
            for text_node in employee_texts:
                if text_node.parent:
                    text = text_node.parent.get_text(strip=True)
                    num = extract_employee_number(text)
                    if num:
                        cache[company_name] = num
                        save_cache(cache)
                        return num
            
            info_sections = soup.find_all(['div', 'span'], class_=re.compile(r'company|info|about', re.I))
            for section in info_sections:
                text = section.get_text(strip=True)
                if re.search(r'\d+.*employee', text, re.I):
                    num = extract_employee_number(text)
                    if num:
                        cache[company_name] = num
                        save_cache(cache)
                        return num
    
    cache[company_name] = ""
    save_cache(cache)
    return ""


def enrich_jobspy_data_detailed(input_file, output_file, max_jobs=200):
    """Detailed enrichment - fetch details for missing data only"""
    print("="*60)
    print("JobSpy Detailed Data Enrichment (API Calls for Missing Data)")
    print("="*60)
    
    start_time = time.time()
    
    # Load data
    print(f"\nLoading data from: {input_file}")
    df = pd.read_excel(input_file)
    df = df.replace({np.nan: ''})
    
    total_jobs = len(df)
    jobs_to_process = min(max_jobs, total_jobs)
    
    print(f"Total jobs in file: {total_jobs}")
    print(f"Jobs to process: {jobs_to_process}")
    print()
    
    cache = load_cache()
    jobs = df.to_dict('records')
    
    enriched_jobs = []
    stats = {
        "company_name_added": 0,
        "company_size_added": 0,
        "jobs_processed": 0,
    }
    
    for idx, job in enumerate(jobs[:jobs_to_process]):
        enriched = job.copy()
        needs_processing = False
        
        # Check what's missing
        needs_company_name = not (enriched.get("Company Name") and str(enriched.get("Company Name")).strip())
        needs_company_size = not (enriched.get("Company Size") and str(enriched.get("Company Size")).strip())
        
        if needs_company_name or needs_company_size:
            needs_processing = True
            stats["jobs_processed"] += 1
            
            if (idx + 1) % 10 == 0:
                print(f"Processing {idx + 1}/{jobs_to_process} (fetched details for {stats['jobs_processed']} jobs)...")
        
        # Fetch company name if missing
        if needs_company_name and enriched.get("Job Link"):
            company_name = extract_company_name_from_page(enriched.get("Job Link"), cache)
            if company_name:
                enriched["Company Name"] = company_name
                stats["company_name_added"] += 1
                time.sleep(REQUEST_DELAY)
        
        # Fetch company size if missing and we have company name
        if needs_company_size:
            company_name = enriched.get("Company Name", "")
            if company_name and str(company_name).strip():
                company_size = get_company_size_from_page(company_name, enriched.get("Job Link", ""), cache)
                if company_size:
                    enriched["Company Size"] = company_size
                    stats["company_size_added"] += 1
                    time.sleep(REQUEST_DELAY)
        
        enriched_jobs.append(enriched)
    
    # Create DataFrame
    df_enriched = pd.DataFrame(enriched_jobs)
    
    # Ensure all expected fields exist
    for field in EXPECTED_FIELDS:
        if field not in df_enriched.columns:
            df_enriched[field] = ""
    
    # Reorder columns
    df_enriched = df_enriched[EXPECTED_FIELDS]
    
    # Save
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    df_enriched.to_excel(output_file, index=False)
    
    elapsed_time = time.time() - start_time
    
    # Calculate completeness
    print(f"\n{'='*60}")
    print("Enrichment Statistics")
    print(f"{'='*60}")
    print(f"Jobs requiring API calls: {stats['jobs_processed']}/{jobs_to_process}")
    print(f"Company names added: {stats['company_name_added']}")
    print(f"Company sizes added: {stats['company_size_added']}")
    
    print(f"\n{'='*60}")
    print("Final Completeness Statistics")
    print(f"{'='*60}")
    
    total_fields = len(EXPECTED_FIELDS) * jobs_to_process
    filled_fields = 0
    
    for field in EXPECTED_FIELDS:
        non_empty = df_enriched[field].notna() & (df_enriched[field] != "")
        count = non_empty.sum()
        percentage = (count / jobs_to_process * 100) if jobs_to_process > 0 else 0
        filled_fields += count
        print(f"  {field}: {count}/{jobs_to_process} ({percentage:.1f}%)")
    
    overall_completeness = (filled_fields / total_fields * 100) if total_fields > 0 else 0
    print(f"\n  Overall Completeness: {overall_completeness:.1f}%")
    
    print(f"\n{'='*60}")
    print("Results")
    print(f"{'='*60}")
    print(f"Output file: {output_file}")
    print(f"Jobs processed: {jobs_to_process}")
    print(f"Elapsed time: {elapsed_time:.2f} seconds")
    print(f"Average time per job: {elapsed_time/jobs_to_process:.2f} seconds" if jobs_to_process > 0 else "N/A")
    print(f"Overall completeness: {overall_completeness:.1f}%")
    print(f"{'='*60}\n")
    
    return df_enriched


if __name__ == "__main__":
    if not os.path.exists(TEST_INPUT_FILE):
        print(f"Error: Input file not found: {TEST_INPUT_FILE}")
        print("Please run enrich_jobspy_fast.py first.")
        sys.exit(1)
    
    print("Starting detailed enrichment (API calls for missing data only)...")
    df_enriched = enrich_jobspy_data_detailed(
        TEST_INPUT_FILE,
        TEST_FINAL_FILE,
        max_jobs=200
    )
    
    print("[OK] Detailed enrichment completed!")

