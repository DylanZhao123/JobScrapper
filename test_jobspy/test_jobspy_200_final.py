# -*- coding: utf-8 -*-
"""
JobSpy Test - 200 Jobs Final
Scrape 200 Indeed jobs using JobSpy and output in example_output.xlsx format
No data enrichment - only use JobSpy's original data
"""
import os
import sys
import time
import pandas as pd
import numpy as np

# Test configuration
TEST_OUTPUT_DIR = "test_jobspy/output"
TEST_OUTPUT_FILE = f"{TEST_OUTPUT_DIR}/jobspy_indeed_200_final.xlsx"

# Expected fields from example_output.xlsx - exact order
EXPECTED_FIELDS = [
    "Job Title", "Company Name", "Requirements", "Location",
    "Salary Range", "Estimated Annual Salary", "Job Description",
    "Team Size/Business Line Size", "Company Size",
    "Posted Date", "Job Status",
    "Platform", "Job Link"
]

def test_jobspy_200_final():
    """Test JobSpy for 200 Indeed jobs - output in template format"""
    print("="*60)
    print("JobSpy Test - 200 Jobs (Final Output)")
    print("="*60)
    
    start_time = time.time()
    
    try:
        from jobspy import scrape_jobs
        print("[OK] JobSpy imported successfully")
    except ImportError:
        print("[ERROR] JobSpy not available")
        return None
        
    # Test parameters - multiple keywords and locations to get ~200 jobs
    print("\nTest Parameters:")
    print("  Site: Indeed")
    print("  Target: 200 jobs")
    print()
    
    keywords = [
        "AI Engineer", "Machine Learning Engineer", "Data Scientist",
        "Deep Learning Engineer", "NLP Engineer", "Computer Vision Engineer",
        "AI Researcher", "ML Engineer", "Data Engineer"
    ]
    
    locations = [
        "San Francisco, CA",
        "New York, NY", 
        "Seattle, WA",
        "Boston, MA",
        "Austin, TX"
    ]
    
    all_jobs = []
    target_jobs = 200
    
    print(f"Scraping jobs from {len(keywords)} keywords and {len(locations)} locations...")
    print(f"Target: {target_jobs} jobs\n")
    
    for location in locations:
        if len(all_jobs) >= target_jobs:
            break
            
        for keyword in keywords:
            if len(all_jobs) >= target_jobs:
                break
                
            results_needed = min(25, target_jobs - len(all_jobs))
            
            print(f"Scraping: '{keyword}' in '{location}' (need {results_needed} more)...")
            try:
                jobs = scrape_jobs(
                    site_name="indeed",
                    search_term=keyword,
                    location=location,
                    results_wanted=results_needed
                )
                
                if isinstance(jobs, pd.DataFrame):
                    if not jobs.empty:
                        new_jobs = jobs.to_dict('records')
                        # Deduplicate by job_url
                        existing_urls = {job.get("job_url", "") for job in all_jobs}
                        unique_new = [j for j in new_jobs if j.get("job_url", "") not in existing_urls]
                        all_jobs.extend(unique_new)
                        print(f"  Found {len(new_jobs)} jobs, {len(unique_new)} new unique jobs (total: {len(all_jobs)})")
                    else:
                        print(f"  No jobs found")
                elif jobs:
                    existing_urls = {job.get("job_url", "") for job in all_jobs}
                    unique_new = [j for j in jobs if j.get("job_url", "") not in existing_urls]
                    all_jobs.extend(unique_new)
                    print(f"  Found {len(jobs)} jobs, {len(unique_new)} new unique jobs (total: {len(all_jobs)})")
                else:
                    print(f"  No jobs found")
            except Exception as e:
                print(f"  Error: {str(e)}")
            
            time.sleep(0.5)
    
    elapsed_time = time.time() - start_time
    
    if not all_jobs:
        print("\n[ERROR] No jobs found")
        return None
    
    print(f"\n{'='*60}")
    print(f"Scraping completed in {elapsed_time:.2f} seconds")
    print(f"Total unique jobs found: {len(all_jobs)}")
    print(f"{'='*60}\n")
    
    # Map to template format - use JobSpy's original data only
    print("Mapping to template format (using JobSpy original data only)...")
    mapped_data = {}
    
    for field in EXPECTED_FIELDS:
        mapped_data[field] = []
    
    for job in all_jobs:
        # Job Title - from title
        mapped_data["Job Title"].append(job.get("title", ""))
        
        # Company Name - from company (handle NaN)
        company = job.get("company", "")
        if pd.isna(company):
            company = ""
        mapped_data["Company Name"].append(str(company))
        
        # Requirements - empty (JobSpy doesn't provide this separately)
        mapped_data["Requirements"].append("")
        
        # Location - from location
        mapped_data["Location"].append(job.get("location", ""))
        
        # Salary Range - from min_amount, max_amount, interval
        min_amount = job.get("min_amount", "")
        max_amount = job.get("max_amount", "")
        interval = job.get("interval", "")
        
        salary_range = ""
        estimated_annual = ""
        
        if pd.notna(min_amount) and pd.notna(max_amount):
            try:
                min_val = float(min_amount)
                max_val = float(max_amount)
                if interval:
                    salary_range = f"${int(min_val):,} - ${int(max_val):,} ({interval})"
                else:
                    salary_range = f"${int(min_val):,} - ${int(max_val):,}"
                avg = (min_val + max_val) / 2
                estimated_annual = f"${int(avg)}"
            except (ValueError, TypeError):
                pass
        
        mapped_data["Salary Range"].append(salary_range)
        mapped_data["Estimated Annual Salary"].append(estimated_annual)
        
        # Job Description - from description
        mapped_data["Job Description"].append(job.get("description", ""))
        
        # Team Size/Business Line Size - empty (JobSpy doesn't provide)
        mapped_data["Team Size/Business Line Size"].append("")
        
        # Company Size - from company_num_employees
        company_size = job.get("company_num_employees", "")
        if pd.notna(company_size) and company_size:
            mapped_data["Company Size"].append(str(company_size))
        else:
            mapped_data["Company Size"].append("")
        
        # Posted Date - from date_posted
        date_posted = job.get("date_posted", "")
        mapped_data["Posted Date"].append(str(date_posted) if pd.notna(date_posted) else "")
        
        # Job Status - from employment_type or default to "Active"
        employment_type = job.get("employment_type", "")
        if pd.notna(employment_type) and employment_type:
            mapped_data["Job Status"].append(employment_type)
        else:
            mapped_data["Job Status"].append("Active")
        
        # Platform - always "Indeed"
        mapped_data["Platform"].append("Indeed")
        
        # Job Link - from job_url
        mapped_data["Job Link"].append(job.get("job_url", ""))
    
    # Create DataFrame with exact field order
    df_mapped = pd.DataFrame(mapped_data)
    df_mapped = df_mapped[EXPECTED_FIELDS]  # Ensure exact order
    
    # Calculate completeness
    print(f"\n{'='*60}")
    print("Completeness Statistics")
    print(f"{'='*60}")
    
    total_jobs = len(df_mapped)
    stats = {}
    
    for field in EXPECTED_FIELDS:
        non_empty = df_mapped[field].notna() & (df_mapped[field] != "")
        count = non_empty.sum()
        percentage = (count / total_jobs * 100) if total_jobs > 0 else 0
        stats[field] = {"count": count, "percentage": percentage}
        print(f"  {field}: {count}/{total_jobs} ({percentage:.1f}%)")
    
    total_fields = len(EXPECTED_FIELDS) * total_jobs
    filled_fields = sum(stats[f]["count"] for f in EXPECTED_FIELDS)
    overall_completeness = (filled_fields / total_fields * 100) if total_fields > 0 else 0
    print(f"\n  Overall Completeness: {overall_completeness:.1f}%")
    
    # Save to Excel
    os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)
    df_mapped.to_excel(TEST_OUTPUT_FILE, index=False)
    
    print(f"\n{'='*60}")
    print("Results")
    print(f"{'='*60}")
    print(f"Output file: {TEST_OUTPUT_FILE}")
    print(f"Total jobs: {total_jobs}")
    print(f"Elapsed time: {elapsed_time:.2f} seconds")
    print(f"Average time per job: {elapsed_time/total_jobs:.2f} seconds" if total_jobs > 0 else "N/A")
    print(f"Overall completeness: {overall_completeness:.1f}%")
    print(f"{'='*60}\n")
    
    return {
        "total_jobs": total_jobs,
        "elapsed_time": elapsed_time,
        "overall_completeness": overall_completeness,
        "field_stats": stats
    }


if __name__ == "__main__":
    result = test_jobspy_200_final()
    if result:
        print("[OK] Test completed successfully!")
        print(f"\nOutput saved to: {TEST_OUTPUT_FILE}")
    else:
        print("[ERROR] Test failed!")

