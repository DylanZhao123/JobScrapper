# -*- coding: utf-8 -*-
"""
JobSpy Data Enrichment - Supplement missing data
Enriches JobSpy output with missing company names, company sizes, and requirements
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
TEST_INPUT_FILE = f"{TEST_OUTPUT_DIR}/jobspy_indeed_200.xlsx"
TEST_ENRICHED_FILE = f"{TEST_OUTPUT_DIR}/jobspy_indeed_enriched.xlsx"
TEST_CACHE_FILE = f"{TEST_OUTPUT_DIR}/company_cache.json"
REQUEST_DELAY = 0.5  # Delay between requests

# Expected fields from example_output.xlsx
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
        except requests.exceptions.Timeout:
            pass
        except Exception as e:
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


def extract_company_name_from_url(job_url):
    """Extract company name from Indeed job URL"""
    if not job_url or pd.isna(job_url):
        return ""
    
    # Try to extract from URL patterns
    # Indeed URLs: https://www.indeed.com/viewjob?jk=...
    # Sometimes company name is in the URL or can be found on the page
    
    # For now, return empty - will fetch from page
    return ""


def extract_company_name_from_description(description):
    """Extract company name from job description"""
    if not description or pd.isna(description):
        return ""
    
    # Look for patterns like "About [Company Name]" or "[Company Name] is..."
    patterns = [
        r'About\s+([A-Z][a-zA-Z0-9\s&.,-]+?)(?:\s+is|\s+was|\s+are|\.|$)',
        r'([A-Z][a-zA-Z0-9\s&.,-]+?)\s+is\s+(?:a|an|the)',
        r'at\s+([A-Z][a-zA-Z0-9\s&.,-]+?)(?:\s+we|\s+our|,|\.|$)',
        r'Join\s+([A-Z][a-zA-Z0-9\s&.,-]+?)(?:\s+as|\s+to|\s+and|,|\.|$)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, description[:500], re.IGNORECASE)
        if match:
            company = match.group(1).strip()
            # Clean up common false positives
            if len(company) > 2 and len(company) < 50:
                if company.lower() not in ['the', 'a', 'an', 'we', 'our', 'you', 'your']:
                    return company
    
    return ""


def extract_company_name_from_page(job_url, cache):
    """Extract company name from job detail page"""
    if not job_url or pd.isna(job_url):
        return ""
    
    # Check cache
    cache_key = f"company_name_{job_url}"
    if cache_key in cache:
        return cache[cache_key]
    
    html = zenrows_get(job_url)
    if not html:
        cache[cache_key] = ""
        save_cache(cache)
        return ""
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Try multiple selectors for company name
    company_selectors = [
        ('a', {'data-testid': 'job-company-name'}),
        ('span', {'data-testid': 'job-company-name'}),
        ('div', {'data-testid': 'job-company-name'}),
        ('a', {'class': re.compile(r'company', re.I)}),
        ('span', {'class': re.compile(r'company', re.I)}),
        ('div', {'class': re.compile(r'company', re.I)}),
    ]
    
    for tag, attrs in company_selectors:
        elem = soup.find(tag, attrs)
        if elem:
            company = elem.get_text(strip=True)
            if company and len(company) > 1:
                cache[cache_key] = company
                save_cache(cache)
                return company
    
    # Try to find in page text
    page_text = soup.get_text()
    company_match = re.search(r'Company[:\s]+([A-Z][a-zA-Z0-9\s&.,-]+)', page_text[:1000], re.IGNORECASE)
    if company_match:
        company = company_match.group(1).strip()
        if len(company) > 1 and len(company) < 50:
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
    """Get company size from company page or job page"""
    if not company_name or pd.isna(company_name) or not company_name.strip():
        return ""
    
    # Check cache
    if company_name in cache and isinstance(cache[company_name], str) and cache[company_name].isdigit():
        return cache[company_name]
    
    # Try to get from Indeed company page
    if company_name:
        company_slug = str(company_name).lower().replace(' ', '-').replace('.', '').replace(',', '').replace("'", "").replace('&', 'and')
        company_url = f"https://www.indeed.com/cmp/{company_slug}"
        
        html = zenrows_get(company_url)
        if html:
            soup = BeautifulSoup(html, "html.parser")
            
            # Find employee count
            employee_texts = soup.find_all(string=re.compile(r'\d+.*employee', re.I))
            for text_node in employee_texts:
                if text_node.parent:
                    text = text_node.parent.get_text(strip=True)
                    num = extract_employee_number(text)
                    if num:
                        cache[company_name] = num
                        save_cache(cache)
                        return num
            
            # Try info sections
            info_sections = soup.find_all(['div', 'span'], class_=re.compile(r'company|info|about', re.I))
            for section in info_sections:
                text = section.get_text(strip=True)
                if re.search(r'\d+.*employee', text, re.I):
                    num = extract_employee_number(text)
                    if num:
                        cache[company_name] = num
                        save_cache(cache)
                        return num
    
    # Try to get from job page
    if job_url and not pd.isna(job_url):
        html = zenrows_get(job_url)
        if html:
            soup = BeautifulSoup(html, "html.parser")
            page_text = soup.get_text()
            num = extract_employee_number(page_text)
            if num:
                cache[company_name] = num
                save_cache(cache)
                return num
    
    cache[company_name] = ""
    save_cache(cache)
    return ""


def extract_requirements_improved(description):
    """Improved requirements extraction from description"""
    if not description or pd.isna(description):
        return ""
    
    desc = str(description)
    requirements_text = ''
    
    # Method 1: Find explicit sections
    req_patterns = [
        r'(?:requirements?|qualifications?|required|must have|minimum requirements?)[\s:]*\n?([^\n]{100,800})',
        r"(?:what you['']?ll need|what we['']?re looking for|you should have)[\s:]*\n?([^\n]{100,800})",
        r'(?:education|experience|skills?)[\s:]*\n?([^\n]{100,600})',
        r'(?:preferred qualifications?|nice to have)[\s:]*\n?([^\n]{100,600})',
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
                'required', 'must have', 'should have', 'qualifications',
                'expertise in', 'strong background', 'proven track record'
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


def extract_team_size(description):
    """Extract team size from description"""
    if not description or pd.isna(description):
        return ""
    
    desc = str(description)
    
    # Look for team size patterns
    patterns = [
        r'team\s+of\s+(\d+)',
        r'(\d+)\s+person\s+team',
        r'(\d+)\s+member\s+team',
        r'team\s+size[:\s]+(\d+)',
        r'(\d+)\s+engineers?',
        r'(\d+)\s+developers?',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, desc, re.IGNORECASE)
        if match:
            size = match.group(1)
            try:
                size_num = int(size)
                if 1 <= size_num <= 1000:
                    return str(size_num)
            except:
                pass
    
    return ""


def enrich_job_data(job, cache, fetch_details=True, fast_mode=True):
    """Enrich a single job with missing data"""
    enriched = job.copy()
    
    # 1. Company Name - highest priority
    if not enriched.get("Company Name") or pd.isna(enriched.get("Company Name")) or not str(enriched.get("Company Name")).strip():
        # Try from description first (fast, no API call)
        company_from_desc = extract_company_name_from_description(enriched.get("Job Description", ""))
        if company_from_desc:
            enriched["Company Name"] = company_from_desc
        elif fetch_details and not fast_mode and enriched.get("Job Link"):
            # Fetch from job page (slower but more accurate) - only in detailed mode
            company_from_page = extract_company_name_from_page(enriched.get("Job Link"), cache)
            if company_from_page:
                enriched["Company Name"] = company_from_page
    
    # 2. Requirements - improve extraction
    if not enriched.get("Requirements") or pd.isna(enriched.get("Requirements")) or not str(enriched.get("Requirements")).strip():
        requirements = extract_requirements_improved(enriched.get("Job Description", ""))
        if requirements:
            enriched["Requirements"] = requirements
    
    # 3. Company Size - only fetch if not in fast mode
    company_name = enriched.get("Company Name", "")
    if company_name and not pd.isna(company_name) and str(company_name).strip():
        if not enriched.get("Company Size") or pd.isna(enriched.get("Company Size")) or not str(enriched.get("Company Size")).strip():
            if fetch_details and not fast_mode:
                company_size = get_company_size_from_page(company_name, enriched.get("Job Link", ""), cache)
                if company_size:
                    enriched["Company Size"] = company_size
    
    # 4. Team Size
    if not enriched.get("Team Size/Business Line Size") or pd.isna(enriched.get("Team Size/Business Line Size")):
        team_size = extract_team_size(enriched.get("Job Description", ""))
        if team_size:
            enriched["Team Size/Business Line Size"] = team_size
    
    return enriched


def enrich_jobspy_data(input_file, output_file, max_jobs=200, fetch_details=True, fast_mode=True):
    """Enrich JobSpy output data"""
    print("="*60)
    print("JobSpy Data Enrichment")
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
    print(f"Fetch details: {fetch_details}")
    print()
    
    # Load cache
    cache = load_cache()
    
    # Convert to list of dicts
    jobs = df.to_dict('records')
    
    # Process jobs
    enriched_jobs = []
    stats = {
        "company_name_added": 0,
        "requirements_improved": 0,
        "company_size_added": 0,
        "team_size_added": 0,
    }
    
    for idx, job in enumerate(jobs[:jobs_to_process]):
        if (idx + 1) % 10 == 0:
            print(f"Processing {idx + 1}/{jobs_to_process}...")
        
        # Track what was missing
        had_company = bool(job.get("Company Name") and str(job.get("Company Name")).strip())
        had_requirements = bool(job.get("Requirements") and str(job.get("Requirements")).strip())
        had_company_size = bool(job.get("Company Size") and str(job.get("Company Size")).strip())
        had_team_size = bool(job.get("Team Size/Business Line Size") and str(job.get("Team Size/Business Line Size")).strip())
        
        # Enrich
        enriched = enrich_job_data(job, cache, fetch_details=fetch_details, fast_mode=fast_mode)
        
        # Update stats
        if not had_company and enriched.get("Company Name") and str(enriched.get("Company Name")).strip():
            stats["company_name_added"] += 1
        if not had_requirements and enriched.get("Requirements") and str(enriched.get("Requirements")).strip():
            stats["requirements_improved"] += 1
        if not had_company_size and enriched.get("Company Size") and str(enriched.get("Company Size")).strip():
            stats["company_size_added"] += 1
        if not had_team_size and enriched.get("Team Size/Business Line Size") and str(enriched.get("Team Size/Business Line Size")).strip():
            stats["team_size_added"] += 1
        
        enriched_jobs.append(enriched)
        
        if fetch_details:
            time.sleep(REQUEST_DELAY)
    
    # Create DataFrame
    df_enriched = pd.DataFrame(enriched_jobs)
    
    # Ensure all expected fields exist
    for field in EXPECTED_FIELDS:
        if field not in df_enriched.columns:
            df_enriched[field] = ""
    
    # Reorder columns to match expected format
    df_enriched = df_enriched[EXPECTED_FIELDS]
    
    # Save
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    df_enriched.to_excel(output_file, index=False)
    
    elapsed_time = time.time() - start_time
    
    # Calculate completeness
    print(f"\n{'='*60}")
    print("Enrichment Statistics")
    print(f"{'='*60}")
    print(f"Company names added: {stats['company_name_added']}/{jobs_to_process}")
    print(f"Requirements improved: {stats['requirements_improved']}/{jobs_to_process}")
    print(f"Company sizes added: {stats['company_size_added']}/{jobs_to_process}")
    print(f"Team sizes added: {stats['team_size_added']}/{jobs_to_process}")
    
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
    print(f"{'='*60}\n")
    
    return df_enriched


if __name__ == "__main__":
    # First, make sure we have JobSpy output
    if not os.path.exists(TEST_INPUT_FILE):
        print(f"Error: Input file not found: {TEST_INPUT_FILE}")
        print("Please run test_jobspy_indeed.py first to generate the input file.")
        sys.exit(1)
    
    # First pass: Fast enrichment (no API calls, just text extraction)
    print("Starting fast enrichment (text extraction only)...")
    fast_output = TEST_ENRICHED_FILE.replace(".xlsx", "_fast.xlsx")
    df_fast = enrich_jobspy_data(
        TEST_INPUT_FILE,
        fast_output,
        max_jobs=200,
        fetch_details=False,
        fast_mode=True
    )
    
    print("\n" + "="*60)
    print("Fast enrichment completed. Starting detailed enrichment...")
    print("="*60 + "\n")
    
    # Second pass: Detailed enrichment (with API calls for missing data)
    # Only process jobs that still need company name or company size
    df_enriched = enrich_jobspy_data(
        fast_output,
        TEST_ENRICHED_FILE,
        max_jobs=200,
        fetch_details=True,
        fast_mode=False
    )
    
    print("[OK] Enrichment completed!")

