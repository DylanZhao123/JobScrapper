# -*- coding: utf-8 -*-
"""
JobSpy Test - Indeed Job Scraping
Test JobSpy tool to see if it can produce complete job data like example_output.xlsx
"""
import os
import sys
import time
import pandas as pd
from datetime import datetime

# Test configuration
TEST_OUTPUT_DIR = "test_jobspy/output"
TEST_OUTPUT_FILE = f"{TEST_OUTPUT_DIR}/jobspy_indeed_output.xlsx"

# Expected fields from example_output.xlsx
EXPECTED_FIELDS = [
    "Job Title", "Company Name", "Requirements", "Location",
    "Salary Range", "Estimated Annual Salary", "Job Description",
    "Team Size/Business Line Size", "Company Size",
    "Posted Date", "Job Status",
    "Platform", "Job Link"
]

def test_jobspy_indeed():
    """Test JobSpy for Indeed job scraping"""
    print("="*60)
    print("JobSpy Test - Indeed Job Scraping")
    print("="*60)
    
    start_time = time.time()
    
    try:
        # Try to import JobSpy
        scrape_jobs = None
        try:
            from jobspy import scrape_jobs
            print("[OK] JobSpy imported successfully")
        except ImportError as e1:
            try:
                # Try alternative import
                import jobspy
                if hasattr(jobspy, 'scrape_jobs'):
                    scrape_jobs = jobspy.scrape_jobs
                    print("[OK] JobSpy imported successfully (alternative method)")
                else:
                    print(f"[ERROR] JobSpy module found but scrape_jobs function not available")
                    print(f"[INFO] Available attributes: {[x for x in dir(jobspy) if not x.startswith('_')]}")
                    return None
            except ImportError as e2:
                print(f"[ERROR] JobSpy not available. Import errors:")
                print(f"  Primary: {str(e1)}")
                print(f"  Alternative: {str(e2)}")
                print("[INFO] JobSpy may require additional dependencies.")
                print("[INFO] Try: pip install markdownify regex")
                return None
        
        if scrape_jobs is None:
            print("[ERROR] Could not find scrape_jobs function")
            return None
        
        # Test parameters - similar to our test
        print("\nTest Parameters:")
        print("  Site: Indeed")
        print("  Keywords: ['AI Engineer', 'Machine Learning Engineer', 'Data Scientist']")
        print("  Location: 'San Francisco, CA'")
        print("  Results per keyword: 10")
        print()
        
        # Test with Indeed
        all_jobs = []
        
        keywords = ["AI Engineer", "Machine Learning Engineer", "Data Scientist"]
        location = "San Francisco, CA"
        
        for keyword in keywords:
            print(f"Scraping: '{keyword}' in '{location}'...")
            try:
                jobs = scrape_jobs(
                    site_name="indeed",
                    search_term=keyword,
                    location=location,
                    results_wanted=10
                )
                
                # JobSpy returns a DataFrame
                if isinstance(jobs, pd.DataFrame):
                    if not jobs.empty:
                        print(f"  Found {len(jobs)} jobs")
                        # Convert DataFrame to list of dicts
                        jobs_list = jobs.to_dict('records')
                        all_jobs.extend(jobs_list)
                    else:
                        print(f"  No jobs found")
                elif jobs:
                    # If it's a list
                    print(f"  Found {len(jobs)} jobs")
                    all_jobs.extend(jobs)
                else:
                    print(f"  No jobs found")
            except Exception as e:
                print(f"  Error: {str(e)}")
                import traceback
                traceback.print_exc()
        
        elapsed_time = time.time() - start_time
        
        if not all_jobs:
            print("\n[ERROR] No jobs found. JobSpy may not support Indeed or there was an error.")
            return
        
        print(f"\n{'='*60}")
        print(f"Scraping completed in {elapsed_time:.2f} seconds")
        print(f"Total jobs found: {len(all_jobs)}")
        print(f"{'='*60}\n")
        
        # Analyze job data structure
        print("Analyzing job data structure...")
        if all_jobs:
            sample_job = all_jobs[0]
            print(f"\nSample job fields:")
            for key in sample_job.keys():
                value = sample_job.get(key, "")
                value_preview = str(value)[:50] if value else ""
                print(f"  {key}: {value_preview}")
        
        # Convert to DataFrame
        print(f"\nConverting to DataFrame...")
        df = pd.DataFrame(all_jobs)
        
        # Map JobSpy fields to our expected fields
        print(f"\nMapping fields to expected format...")
        mapped_data = {}
        
        # Field mapping (JobSpy -> Our format)
        field_mapping = {
            "title": "Job Title",
            "company": "Company Name",
            "location": "Location",
            "description": "Job Description",
            "job_url": "Job Link",
            "date_posted": "Posted Date",
            "salary_min": "Salary Range",  # Will combine with salary_max
            "salary_max": None,  # Will combine with salary_min
            "salary": "Salary Range",
            "employment_type": "Job Status",
        }
        
        # Initialize all expected fields
        for field in EXPECTED_FIELDS:
            mapped_data[field] = []
        
        # Map data
        for idx, job in enumerate(all_jobs):
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
            
            # Requirements (extract from description if available)
            description = job.get("description", "")
            requirements = ""
            if description:
                # Try to extract requirements section
                desc_lower = description.lower()
                req_keywords = ["requirements", "qualifications", "required", "must have"]
                for keyword in req_keywords:
                    if keyword in desc_lower:
                        idx = desc_lower.find(keyword)
                        requirements = description[idx:idx+500] if idx >= 0 else ""
                        break
            mapped_data["Requirements"].append(requirements)
            
            # Salary Range - JobSpy uses min_amount, max_amount, interval, currency
            min_amount = job.get("min_amount", "")
            max_amount = job.get("max_amount", "")
            interval = job.get("interval", "")
            currency = job.get("currency", "USD")
            
            salary_range = ""
            estimated_annual = ""
            
            # Handle NaN values
            if pd.notna(min_amount) and pd.notna(max_amount):
                try:
                    min_val = float(min_amount)
                    max_val = float(max_amount)
                    
                    # Format salary range
                    if interval:
                        salary_range = f"${int(min_val):,} - ${int(max_val):,} ({interval})"
                    else:
                        salary_range = f"${int(min_val):,} - ${int(max_val):,}"
                    
                    # Calculate estimated annual
                    avg = (min_val + max_val) / 2
                    estimated_annual = f"${int(avg)}"
                except (ValueError, TypeError):
                    pass
            elif pd.notna(min_amount):
                try:
                    min_val = float(min_amount)
                    if interval:
                        salary_range = f"${int(min_val):,}+ ({interval})"
                    else:
                        salary_range = f"${int(min_val):,}+"
                    estimated_annual = f"${int(min_val)}"
                except (ValueError, TypeError):
                    pass
            elif pd.notna(max_amount):
                try:
                    max_val = float(max_amount)
                    if interval:
                        salary_range = f"Up to ${int(max_val):,} ({interval})"
                    else:
                        salary_range = f"Up to ${int(max_val):,}"
                    estimated_annual = f"${int(max_val)}"
                except (ValueError, TypeError):
                    pass
            
            mapped_data["Salary Range"].append(salary_range)
            mapped_data["Estimated Annual Salary"].append(estimated_annual)
            
            # Team Size/Business Line Size (not available in JobSpy)
            mapped_data["Team Size/Business Line Size"].append("")
            
            # Company Size - JobSpy has company_num_employees
            company_size = job.get("company_num_employees", "")
            if pd.notna(company_size) and company_size:
                mapped_data["Company Size"].append(str(company_size))
            else:
                mapped_data["Company Size"].append("")
            
            # Posted Date
            date_posted = job.get("date_posted", "")
            mapped_data["Posted Date"].append(str(date_posted) if date_posted else "")
            
            # Job Status
            employment_type = job.get("employment_type", "")
            mapped_data["Job Status"].append(employment_type if employment_type else "Active")
            
            # Platform
            mapped_data["Platform"].append("Indeed")
            
            # Job Link
            mapped_data["Job Link"].append(job.get("job_url", ""))
        
        # Create DataFrame with expected fields
        df_mapped = pd.DataFrame(mapped_data)
        
        # Calculate completeness statistics
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
        
        # Overall completeness
        total_fields = len(EXPECTED_FIELDS) * total_jobs
        filled_fields = sum(stats[f]["count"] for f in EXPECTED_FIELDS)
        overall_completeness = (filled_fields / total_fields * 100) if total_fields > 0 else 0
        print(f"\n  Overall Completeness: {overall_completeness:.1f}%")
        
        # Save to Excel
        os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)
        df_mapped.to_excel(TEST_OUTPUT_FILE, index=False)
        
        print(f"\n{'='*60}")
        print("Test Results")
        print(f"{'='*60}")
        print(f"Output file: {TEST_OUTPUT_FILE}")
        print(f"Total jobs: {total_jobs}")
        print(f"Elapsed time: {elapsed_time:.2f} seconds")
        print(f"Average time per job: {elapsed_time/total_jobs:.2f} seconds" if total_jobs > 0 else "N/A")
        print(f"Overall completeness: {overall_completeness:.1f}%")
        print(f"{'='*60}\n")
        
        # Show sample data
        print("Sample jobs (first 3):")
        for idx in range(min(3, len(df_mapped))):
            print(f"\n  Job {idx+1}:")
            print(f"    Title: {df_mapped.iloc[idx]['Job Title']}")
            print(f"    Company: {df_mapped.iloc[idx]['Company Name']}")
            print(f"    Location: {df_mapped.iloc[idx]['Location']}")
            print(f"    Description length: {len(str(df_mapped.iloc[idx]['Job Description']))} chars")
            print(f"    Salary: {df_mapped.iloc[idx]['Salary Range']}")
            print(f"    Link: {df_mapped.iloc[idx]['Job Link'][:60]}...")
        
        return {
            "total_jobs": total_jobs,
            "elapsed_time": elapsed_time,
            "overall_completeness": overall_completeness,
            "field_stats": stats
        }
        
    except Exception as e:
        print(f"\n[ERROR] Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    result = test_jobspy_indeed()
    if result:
        print("\n[OK] Test completed successfully!")
    else:
        print("\n[ERROR] Test failed!")

