# -*- coding: utf-8 -*-
"""
JobSpy Complete Scraper - Indeed Jobs
Complete solution using JobSpy to scrape Indeed jobs with multiple keywords and locations
Extracts Requirements from job description using LinkedIn logic
Output format: example_output.xlsx
"""
import os
import sys
import time
import re
import pandas as pd
import numpy as np

# Test configuration
TEST_OUTPUT_DIR = "test_jobspy/output"
TEST_OUTPUT_FILE = f"{TEST_OUTPUT_DIR}/jobspy_complete_output.xlsx"

# Expected fields from example_output.xlsx - exact order
EXPECTED_FIELDS = [
    "Job Title", "Company Name", "Requirements", "Location",
    "Salary Range", "Estimated Annual Salary", "Job Description",
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

# Test locations (US cities) - can be expanded
TEST_LOCATIONS = [
    "San Francisco, CA",
    "New York, NY",
    "Seattle, WA",
    "Boston, MA",
    "Austin, TX",
    "Los Angeles, CA",
    "Chicago, IL",
    "Washington, DC",
    "Denver, CO",
    "Atlanta, GA"
]


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


def scrape_jobspy_complete(keywords, locations, results_per_search=50, max_total_jobs=None):
    """
    Complete JobSpy scraper with multiple keywords and locations
    
    Args:
        keywords: List of keywords to search
        locations: List of locations to search
        results_per_search: Number of results to request per keyword+location combination
        max_total_jobs: Maximum total jobs to collect (None = no limit)
    
    Returns:
        List of job dictionaries
    """
    print("="*60)
    print("JobSpy Complete Scraper - Indeed Jobs")
    print("="*60)
    
    start_time = time.time()
    
    try:
        from jobspy import scrape_jobs
        print("[OK] JobSpy imported successfully")
    except ImportError:
        print("[ERROR] JobSpy not available. Please install: pip install python-jobspy")
        return None
    
    print(f"\nConfiguration:")
    print(f"  Keywords: {len(keywords)} keywords")
    print(f"  Locations: {len(locations)} locations")
    print(f"  Results per search: {results_per_search}")
    print(f"  Total combinations: {len(keywords) * len(locations)}")
    if max_total_jobs:
        print(f"  Max total jobs: {max_total_jobs}")
    print()
    
    all_jobs = []
    seen_urls = set()  # Deduplicate by job_url
    total_requests = 0
    successful_requests = 0
    failed_requests = 0
    
    # Scrape all keyword+location combinations
    for location_idx, location in enumerate(locations):
        if max_total_jobs and len(all_jobs) >= max_total_jobs:
            print(f"\nReached max total jobs limit ({max_total_jobs}), stopping...")
            break
        
        for keyword_idx, keyword in enumerate(keywords):
            if max_total_jobs and len(all_jobs) >= max_total_jobs:
                break
            
            total_requests += 1
            progress = f"[{total_requests}/{len(keywords)*len(locations)}]"
            
            print(f"{progress} Scraping: '{keyword}' in '{location}'...", end=" ")
            
            try:
                jobs = scrape_jobs(
                    site_name="indeed",
                    search_term=keyword,
                    location=location,
                    results_wanted=results_per_search,
                    country_indeed="usa"
                )
                
                if isinstance(jobs, pd.DataFrame):
                    if not jobs.empty:
                        new_jobs = jobs.to_dict('records')
                        # Deduplicate
                        unique_new = []
                        for job in new_jobs:
                            job_url = job.get("job_url", "")
                            if job_url and job_url not in seen_urls:
                                seen_urls.add(job_url)
                                unique_new.append(job)
                        
                        all_jobs.extend(unique_new)
                        successful_requests += 1
                        print(f"[OK] Found {len(new_jobs)} jobs, {len(unique_new)} new unique (total: {len(all_jobs)})")
                    else:
                        print(f"[SKIP] No jobs found")
                else:
                    print(f"[ERROR] Unexpected return type")
                
            except Exception as e:
                failed_requests += 1
                print(f"[ERROR] {str(e)[:50]}")
            
            # Small delay between requests
            time.sleep(0.3)
    
    elapsed_time = time.time() - start_time
    
    print(f"\n{'='*60}")
    print("Scraping Summary")
    print(f"{'='*60}")
    print(f"Total requests: {total_requests}")
    print(f"Successful: {successful_requests}")
    print(f"Failed: {failed_requests}")
    print(f"Total unique jobs: {len(all_jobs)}")
    print(f"Elapsed time: {elapsed_time:.2f} seconds")
    print(f"Average time per request: {elapsed_time/total_requests:.2f} seconds" if total_requests > 0 else "N/A")
    print(f"{'='*60}\n")
    
    return all_jobs


def map_to_template_format(jobs):
    """
    Map JobSpy jobs to example_output.xlsx format
    Extract Requirements from description
    """
    print("Mapping to template format and extracting Requirements...")
    
    mapped_data = {}
    for field in EXPECTED_FIELDS:
        mapped_data[field] = []
    
    for idx, job in enumerate(jobs):
        if (idx + 1) % 100 == 0:
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
        
        # Platform
        mapped_data["Platform"].append("Indeed")
        
        # Job Link
        mapped_data["Job Link"].append(job.get("job_url", ""))
    
    # Create DataFrame with exact field order
    df_mapped = pd.DataFrame(mapped_data)
    df_mapped = df_mapped[EXPECTED_FIELDS]  # Ensure exact order
    
    return df_mapped


def main():
    """Main function"""
    print("="*60)
    print("JobSpy Complete Scraper")
    print("="*60)
    
    # Configuration
    # Use core keywords for initial test, can expand to AI_RELATED_KEYWORDS
    keywords = CORE_KEYWORDS  # Start with core keywords
    # keywords = CORE_KEYWORDS + AI_RELATED_KEYWORDS  # For full coverage
    
    locations = TEST_LOCATIONS  # Can expand to all US locations
    
    results_per_search = 50  # Request 50 results per keyword+location
    max_total_jobs = None  # No limit, or set to 200, 500, etc.
    
    # Step 1: Scrape jobs
    all_jobs = scrape_jobspy_complete(
        keywords=keywords,
        locations=locations,
        results_per_search=results_per_search,
        max_total_jobs=max_total_jobs
    )
    
    if not all_jobs:
        print("[ERROR] No jobs scraped")
        return
    
    # Step 2: Map to template format and extract Requirements
    print(f"\n{'='*60}")
    print("Processing and Formatting Data")
    print(f"{'='*60}\n")
    
    df_final = map_to_template_format(all_jobs)
    
    # Step 3: Calculate completeness
    print(f"\n{'='*60}")
    print("Final Completeness Statistics")
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
    
    # Step 4: Save to Excel
    os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)
    df_final.to_excel(TEST_OUTPUT_FILE, index=False)
    
    print(f"\n{'='*60}")
    print("Results")
    print(f"{'='*60}")
    print(f"Output file: {TEST_OUTPUT_FILE}")
    print(f"Total jobs: {total_jobs}")
    print(f"Overall completeness: {overall_completeness:.1f}%")
    print(f"{'='*60}\n")
    
    # Show sample
    print("Sample jobs (first 3):")
    for idx in range(min(3, len(df_final))):
        print(f"\n  Job {idx+1}:")
        print(f"    Title: {df_final.iloc[idx]['Job Title']}")
        print(f"    Company: {df_final.iloc[idx]['Company Name']}")
        print(f"    Location: {df_final.iloc[idx]['Location']}")
        print(f"    Requirements length: {len(str(df_final.iloc[idx]['Requirements']))} chars")
        print(f"    Salary: {df_final.iloc[idx]['Salary Range']}")
    
    print(f"\n[OK] Complete! Output saved to: {TEST_OUTPUT_FILE}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()

