# -*- coding: utf-8 -*-
"""
JobSpy Test - 200 Jobs Scraping
Large-scale test to scrape ~200 Indeed jobs
"""
import os
import sys
import time
import pandas as pd
import numpy as np

# Test configuration
TEST_OUTPUT_DIR = "test_jobspy/output"
TEST_OUTPUT_FILE = f"{TEST_OUTPUT_DIR}/jobspy_indeed_200.xlsx"

# Expected fields from example_output.xlsx
EXPECTED_FIELDS = [
    "Job Title", "Company Name", "Requirements", "Location",
    "Salary Range", "Estimated Annual Salary", "Job Description",
    "Team Size/Business Line Size", "Company Size",
    "Posted Date", "Job Status",
    "Platform", "Job Link"
]

def test_jobspy_200():
    """Test JobSpy for 200 Indeed jobs"""
    print("="*60)
    print("JobSpy Test - 200 Jobs Scraping")
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
    print("  Target: ~200 jobs")
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
                
            results_needed = min(25, target_jobs - len(all_jobs))  # Get up to 25 per search
            
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
            
            time.sleep(0.5)  # Small delay between searches
    
    elapsed_time = time.time() - start_time
    
    if not all_jobs:
        print("\n[ERROR] No jobs found")
        return None
    
    print(f"\n{'='*60}")
    print(f"Scraping completed in {elapsed_time:.2f} seconds")
    print(f"Total unique jobs found: {len(all_jobs)}")
    print(f"{'='*60}\n")
    
    # Convert to DataFrame and map fields
    print("Mapping fields to expected format...")
    mapped_data = {}
    
    for field in EXPECTED_FIELDS:
        mapped_data[field] = []
    
    for job in all_jobs:
        # Job Title
        mapped_data["Job Title"].append(job.get("title", ""))
        
        # Company Name - handle NaN
        company = job.get("company", "")
        if pd.isna(company):
            company = ""
        mapped_data["Company Name"].append(str(company))
        
        # Location
        mapped_data["Location"].append(job.get("location", ""))
        
        # Job Description
        mapped_data["Job Description"].append(job.get("description", ""))
        
        # Requirements (extract from description)
        description = job.get("description", "")
        requirements = ""
        if description:
            desc_lower = str(description).lower()
            req_keywords = ["requirements", "qualifications", "required", "must have"]
            for keyword in req_keywords:
                if keyword in desc_lower:
                    idx = desc_lower.find(keyword)
                    requirements = str(description)[idx:idx+500] if idx >= 0 else ""
                    break
        mapped_data["Requirements"].append(requirements)
        
        # Salary Range
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
        
        # Team Size/Business Line Size
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
        mapped_data["Job Status"].append(employment_type if pd.notna(employment_type) and employment_type else "Active")
        
        # Platform
        mapped_data["Platform"].append("Indeed")
        
        # Job Link
        mapped_data["Job Link"].append(job.get("job_url", ""))
    
    # Create DataFrame
    df_mapped = pd.DataFrame(mapped_data)
    
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
    result = test_jobspy_200()
    if result:
        print("[OK] Test completed successfully!")
    else:
        print("[ERROR] Test failed!")

