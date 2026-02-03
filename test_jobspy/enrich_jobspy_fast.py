# -*- coding: utf-8 -*-
"""
JobSpy Data Fast Enrichment - Quick text-based enrichment only
Fast enrichment without API calls - only text extraction from existing data
"""
import os
import sys
import time
import re
import pandas as pd
import numpy as np

# Test configuration
TEST_OUTPUT_DIR = "test_jobspy/output"
TEST_INPUT_FILE = f"{TEST_OUTPUT_DIR}/jobspy_indeed_200.xlsx"
TEST_ENRICHED_FILE = f"{TEST_OUTPUT_DIR}/jobspy_indeed_200_enriched.xlsx"

# Expected fields from example_output.xlsx
EXPECTED_FIELDS = [
    "Job Title", "Company Name", "Requirements", "Location",
    "Salary Range", "Estimated Annual Salary", "Job Description",
    "Team Size/Business Line Size", "Company Size",
    "Posted Date", "Job Status",
    "Platform", "Job Link"
]


def extract_company_name_from_description(description):
    """Extract company name from job description"""
    if not description or pd.isna(description):
        return ""
    
    desc = str(description)
    
    # Look for patterns like "About [Company Name]" or "[Company Name] is..."
    patterns = [
        r'About\s+([A-Z][a-zA-Z0-9\s&.,-]+?)(?:\s+is|\s+was|\s+are|\.|$)',
        r'([A-Z][a-zA-Z0-9\s&.,-]+?)\s+is\s+(?:a|an|the)',
        r'at\s+([A-Z][a-zA-Z0-9\s&.,-]+?)(?:\s+we|\s+our|,|\.|$)',
        r'Join\s+([A-Z][a-zA-Z0-9\s&.,-]+?)(?:\s+as|\s+to|\s+and|,|\.|$)',
        r'([A-Z][a-zA-Z0-9\s&.,-]+?)\s+was\s+founded',
        r'([A-Z][a-zA-Z0-9\s&.,-]+?)\s+is\s+a\s+(?:leading|fast-growing|innovative)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, desc[:1000], re.IGNORECASE)
        if match:
            company = match.group(1).strip()
            # Clean up common false positives
            if len(company) > 2 and len(company) < 50:
                if company.lower() not in ['the', 'a', 'an', 'we', 'our', 'you', 'your', 'this', 'that']:
                    # Remove common suffixes
                    company = re.sub(r'\s+(?:is|was|are|were|has|have|had)$', '', company, flags=re.I)
                    if len(company) > 2:
                        return company
    
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
        r'(\d+)\s+people\s+team',
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


def enrich_jobspy_data_fast(input_file, output_file, max_jobs=200):
    """Fast enrichment - text extraction only, no API calls"""
    print("="*60)
    print("JobSpy Fast Data Enrichment (Text Extraction Only)")
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
    
    # Convert to list of dicts
    jobs = df.to_dict('records')
    
    # Process jobs
    enriched_jobs = []
    stats = {
        "company_name_added": 0,
        "requirements_improved": 0,
        "team_size_added": 0,
    }
    
    for idx, job in enumerate(jobs[:jobs_to_process]):
        if (idx + 1) % 50 == 0:
            print(f"Processing {idx + 1}/{jobs_to_process}...")
        
        enriched = job.copy()
        
        # Track what was missing
        had_company = bool(enriched.get("Company Name") and str(enriched.get("Company Name")).strip())
        had_requirements = bool(enriched.get("Requirements") and str(enriched.get("Requirements")).strip())
        had_team_size = bool(enriched.get("Team Size/Business Line Size") and str(enriched.get("Team Size/Business Line Size")).strip())
        
        # 1. Company Name - extract from description
        if not had_company:
            company_from_desc = extract_company_name_from_description(enriched.get("Job Description", ""))
            if company_from_desc:
                enriched["Company Name"] = company_from_desc
                stats["company_name_added"] += 1
        
        # 2. Requirements - improve extraction
        if not had_requirements:
            requirements = extract_requirements_improved(enriched.get("Job Description", ""))
            if requirements:
                enriched["Requirements"] = requirements
                stats["requirements_improved"] += 1
        
        # 3. Team Size
        if not had_team_size:
            team_size = extract_team_size(enriched.get("Job Description", ""))
            if team_size:
                enriched["Team Size/Business Line Size"] = team_size
                stats["team_size_added"] += 1
        
        enriched_jobs.append(enriched)
    
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
    print(f"Overall completeness: {overall_completeness:.1f}%")
    print(f"{'='*60}\n")
    
    return df_enriched


if __name__ == "__main__":
    if not os.path.exists(TEST_INPUT_FILE):
        print(f"Error: Input file not found: {TEST_INPUT_FILE}")
        print("Please run test_jobspy_200.py first to generate the input file.")
        sys.exit(1)
    
    print("Starting fast enrichment (text extraction only, no API calls)...")
    df_enriched = enrich_jobspy_data_fast(
        TEST_INPUT_FILE,
        TEST_ENRICHED_FILE,
        max_jobs=200
    )
    
    print("[OK] Fast enrichment completed!")

