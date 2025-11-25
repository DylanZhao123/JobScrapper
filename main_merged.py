# -*- coding: utf-8 -*-
"""
Merged Scraper - Scrape core and AI-related jobs in one run
Output format strictly follows merged_report_2.xlsx
"""
import sys
import os
import json
import traceback
import re
import pandas as pd

# Set independent cache file path before importing scraper
import config
MERGED_RUN_ID = config.RUN_ID  # Read RUN_ID from config
MERGED_OUTPUT_DIR = f"outputs/{MERGED_RUN_ID}"
MERGED_CACHE_FILE = f"{MERGED_OUTPUT_DIR}/company_cache.json"

# Check if RUN_ID has changed, clear old checkpoints if changed
_last_run_id_file = f"{MERGED_OUTPUT_DIR}/.last_run_id"
if os.path.exists(_last_run_id_file):
    try:
        with open(_last_run_id_file, "r", encoding="utf-8") as f:
            last_run_id = f.read().strip()
        if last_run_id != MERGED_RUN_ID:
            # RUN_ID changed, clear old checkpoint files
            print(f"RUN_ID changed detected: {last_run_id} -> {MERGED_RUN_ID}")
            print("Clearing old checkpoint files...")
            checkpoint_files = [
                f"{MERGED_OUTPUT_DIR}/core_jobs/checkpoint.json",
                f"{MERGED_OUTPUT_DIR}/ai_related_jobs/checkpoint.json",
                f"{MERGED_OUTPUT_DIR}/core_jobs/stage1_raw_data.json",
                f"{MERGED_OUTPUT_DIR}/core_jobs/stage1_unique_data.json",
                f"{MERGED_OUTPUT_DIR}/core_jobs/stage2_detail_data.json",
                f"{MERGED_OUTPUT_DIR}/ai_related_jobs/stage1_raw_data.json",
                f"{MERGED_OUTPUT_DIR}/ai_related_jobs/stage1_unique_data.json",
                f"{MERGED_OUTPUT_DIR}/ai_related_jobs/stage2_detail_data.json",
                f"{MERGED_OUTPUT_DIR}/stage1_raw_data_core.json",
                f"{MERGED_OUTPUT_DIR}/stage1_unique_data_core.json",
                f"{MERGED_OUTPUT_DIR}/stage2_detail_data_core.json",
                f"{MERGED_OUTPUT_DIR}/stage1_raw_data_ai_related.json",
                f"{MERGED_OUTPUT_DIR}/stage1_unique_data_ai_related.json",
                f"{MERGED_OUTPUT_DIR}/stage2_detail_data_ai_related.json",
            ]
            for file_path in checkpoint_files:
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        print(f"Deleted: {file_path}")
                    except:
                        pass
    except:
        pass

# Save current RUN_ID
os.makedirs(MERGED_OUTPUT_DIR, exist_ok=True)
with open(_last_run_id_file, "w", encoding="utf-8") as f:
    f.write(MERGED_RUN_ID)

# Temporarily modify config's CACHE_FILE
original_cache_file = config.CACHE_FILE
config.CACHE_FILE = MERGED_CACHE_FILE

# Now import scraper (it will use the modified CACHE_FILE)
from scraper_linkedin_checkpoint import (
    fetch_linkedin_list_with_checkpoint,
    enrich_job_details_with_checkpoint
)
import scraper_linkedin_checkpoint as scraper_module

# Ensure scraper module also uses the new CACHE_FILE
scraper_module.CACHE_FILE = MERGED_CACHE_FILE

from checkpoint_manager import (
    load_checkpoint, save_checkpoint,
    load_stage1_raw_data, save_stage1_raw_data,
    load_stage1_unique_data, save_stage1_unique_data,
    load_stage2_detail_data,
    set_country_paths, reset_paths
)
from exporter import export_to_excel
from config import (
    TARGET_SITE, DETAIL_LIMIT, MAX_PAGES, 
    KEYWORDS, USE_MERGED_KEYWORDS, FIELDS
)

# AI-related job keywords list (copied from main_ai_related.py)
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

# Job title normalization and job level extraction functions (copied from analyze_final_merged_v2.py)
def normalize_job_title(job_title):
    """Normalize job title to job label"""
    if not job_title or not isinstance(job_title, str):
        return "Other"
    
    title_lower = job_title.lower().strip()
    
    # Remove common level prefixes and suffixes
    prefixes_to_remove = ['junior', 'jr', 'jr.', 'senior', 'sr', 'sr.', 'lead', 'principal', 
                          'staff', 'intern', 'internship', 'entry', 'entry-level', 'associate',
                          'assistant', 'trainee', 'apprentice', 'director', 'manager', 'head',
                          'chief', 'vp', 'vice president', 'executive', 'architect', 'specialist']
    
    # Remove level prefixes
    title_normalized = title_lower
    for prefix in prefixes_to_remove:
        if title_normalized.startswith(prefix + ' '):
            title_normalized = title_normalized[len(prefix):].strip()
        if title_normalized.endswith(' ' + prefix):
            title_normalized = title_normalized[:-len(prefix)-1].strip()
    
    # Normalize common job title variants
    title_normalized = re.sub(r'\s+', ' ', title_normalized)  # Multiple spaces to one
    
    # Job label mapping
    job_mapping = {
        # Data Scientist related
        'data scientist': 'Data Scientist',
        'data science': 'Data Scientist',
        'data analytics': 'Data Scientist',
        'data analyst': 'Data Analyst',
        'data engineer': 'Data Engineer',
        'data engineering': 'Data Engineer',
        
        # AI/ML related
        'ai engineer': 'AI Engineer',
        'artificial intelligence engineer': 'AI Engineer',
        'ml engineer': 'ML Engineer',
        'machine learning engineer': 'ML Engineer',
        'ai/ml engineer': 'AI/ML Engineer',
        'deep learning engineer': 'Deep Learning Engineer',
        'ai researcher': 'AI Researcher',
        'ai scientist': 'AI Scientist',
        'machine learning scientist': 'ML Scientist',
        'ai developer': 'AI Developer',
        'ai specialist': 'AI Specialist',
        
        # Software Engineer related
        'software engineer': 'Software Engineer',
        'software developer': 'Software Developer',
        'software development engineer': 'Software Engineer',
        'backend engineer': 'Backend Engineer',
        'frontend engineer': 'Frontend Engineer',
        'full stack engineer': 'Full Stack Engineer',
        'full-stack engineer': 'Full Stack Engineer',
        
        # Product related
        'product manager': 'Product Manager',
        'ai product manager': 'AI Product Manager',
        'product owner': 'Product Manager',
        
        # Research related
        'research scientist': 'Research Scientist',
        'research engineer': 'Research Engineer',
        
        # Other
        'automation engineer': 'Automation Engineer',
        'manufacturing engineer': 'Manufacturing Engineer',
    }
    
    # Try exact match
    for key, label in job_mapping.items():
        if key in title_normalized:
            return label
    
    # If no match, try to extract core job title
    words = title_normalized.split()
    if len(words) >= 2:
        potential_label = ' '.join(words[:2]).title()
        return potential_label
    elif len(words) == 1:
        return words[0].title()
    
    return "Other"

def extract_job_level(job_title):
    """Extract job level: intern, junior, senior, etc."""
    if not job_title or not isinstance(job_title, str):
        return "Regular"
    
    title_lower = job_title.lower()
    
    if any(word in title_lower for word in ['intern', 'internship', 'trainee', 'apprentice']):
        return "Intern"
    elif any(word in title_lower for word in ['junior', 'jr', 'jr.', 'entry', 'entry-level', 'assistant', 'associate']):
        return "Junior"
    elif any(word in title_lower for word in ['senior', 'sr', 'sr.', 'lead', 'principal', 'staff']):
        return "Senior"
    elif any(word in title_lower for word in ['director', 'manager', 'head', 'chief', 'vp', 'vice president', 'executive']):
        return "Management"
    else:
        return "Regular"

def get_us_locations_only():
    """Get US locations only"""
    from locations_config import LOCATIONS_BY_STATE
    
    us_locations = []
    uk_keywords = ["United Kingdom", "England", "Scotland", "Wales", "Northern Ireland"]
    ca_keywords = ["Canada", "Ontario", "British Columbia", "Quebec", "Alberta", "Manitoba", "Saskatchewan", "Nova Scotia", "Newfoundland", "New Brunswick", "Prince Edward Island", "Yukon", "Northwest Territories", "Nunavut"]
    sg_keywords = ["Singapore"]
    hk_keywords = ["Hong Kong"]
    
    for state, locations in LOCATIONS_BY_STATE.items():
        state_lower = state.lower()
        
        # Skip non-US locations
        if any(kw.lower() in state_lower for kw in uk_keywords):
            continue
        elif any(kw.lower() in state_lower for kw in ca_keywords):
            continue
        elif any(kw.lower() in state_lower for kw in sg_keywords):
            continue
        elif any(kw.lower() in state_lower for kw in hk_keywords):
            continue
        
        # Only add US locations
        us_locations.extend(locations)
    
    return us_locations

def calculate_completeness(job):
    """Calculate job data completeness (number of non-empty fields)"""
    non_empty_count = 0
    for field in FIELDS:
        value = job.get(field, "")
        if value and str(value).strip():
            non_empty_count += 1
    return non_empty_count

def deduplicate_jobs(jobs1, jobs2):
    """
    Merge two job lists and deduplicate
    If duplicate, keep the more complete data
    """
    unique_jobs = {}
    
    # Process first list
    for job in jobs1:
        job_title = job.get("Job Title", "")
        company_name = job.get("Company Name", "")
        key = (job_title, company_name)
        
        if key[0] and key[1]:
            if key not in unique_jobs:
                unique_jobs[key] = job
            else:
                existing_completeness = calculate_completeness(unique_jobs[key])
                new_completeness = calculate_completeness(job)
                if new_completeness > existing_completeness:
                    unique_jobs[key] = job
    
    # Process second list
    for job in jobs2:
        job_title = job.get("Job Title", "")
        company_name = job.get("Company Name", "")
        key = (job_title, company_name)
        
        if key[0] and key[1]:
            if key not in unique_jobs:
                unique_jobs[key] = job
            else:
                existing_completeness = calculate_completeness(unique_jobs[key])
                new_completeness = calculate_completeness(job)
                if new_completeness > existing_completeness:
                    unique_jobs[key] = job
    
    return list(unique_jobs.values())

# Note: Since we use set_country_paths, checkpoint_manager will automatically use the correct path
# So we can directly use load_checkpoint and save_checkpoint

def load_stage_data_with_prefix(prefix, stage):
    """Load stage data with prefix"""
    if stage == "stage1_unique":
        file_path = f"{MERGED_OUTPUT_DIR}/stage1_unique_data_{prefix}.json"
    elif stage == "stage2_detail":
        file_path = f"{MERGED_OUTPUT_DIR}/stage2_detail_data_{prefix}.json"
    else:
        return None
    
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return None

def save_stage_data_with_prefix(prefix, stage, data):
    """Save stage data with prefix"""
    if stage == "stage1_unique":
        file_path = f"{MERGED_OUTPUT_DIR}/stage1_unique_data_{prefix}.json"
    elif stage == "stage2_detail":
        file_path = f"{MERGED_OUTPUT_DIR}/stage2_detail_data_{prefix}.json"
    else:
        return
    
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_stage1_raw_data_with_prefix(prefix):
    """Load stage 1 raw data with prefix"""
    file_path = f"{MERGED_OUTPUT_DIR}/stage1_raw_data_{prefix}.json"
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return []

def save_stage1_raw_data_with_prefix(prefix, data):
    """Save stage 1 raw data with prefix"""
    file_path = f"{MERGED_OUTPUT_DIR}/stage1_raw_data_{prefix}.json"
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def scrape_core_jobs(us_locations):
    """Scrape core AI jobs (high relevance)"""
    print("\n" + "="*60)
    print("Stage A: Scraping Core AI Jobs (High Relevance)")
    print("="*60)
    
    # Set independent checkpoint path
    core_dir = f"{MERGED_OUTPUT_DIR}/core_jobs"
    set_country_paths(core_dir)
    
    checkpoint = load_checkpoint()
    
    if checkpoint:
        print(f"\nCheckpoint found, resuming from breakpoint...")
        print(f"Stage: {checkpoint.get('stage')}")
        print(f"Last update: {checkpoint.get('last_update')}")
        
        stage = checkpoint.get('stage')
        
        if stage == "completed":
            # Already completed, directly load saved data
            detail_data = load_stage_data_with_prefix("core", "stage2_detail")
            if detail_data:
                jobs = detail_data.get("jobs", [])
                print(f"Core job scraping completed, loading saved data: {len(jobs)} jobs")
                reset_paths()
                return jobs
            else:
                print("Warning: Checkpoint shows completed, but saved data not found, restarting...")
                # Continue execution, start from beginning
        
        if stage == "stage1_list":
            location_index = checkpoint.get('current_location_index', 0)
            keyword_index = checkpoint.get('current_keyword_index', 0)
            page = checkpoint.get('current_page', 0)
            search_keyword_count = 1 if USE_MERGED_KEYWORDS else len(KEYWORDS)
            print(f"Resuming from location {location_index+1}/{len(us_locations)} keyword {keyword_index+1}/{search_keyword_count} page {page+1}...")
            
            all_jobs, completed_locations, completed_keywords, final_location_idx, final_keyword_idx, final_page = fetch_linkedin_list_with_checkpoint(
                KEYWORDS, us_locations, location_index, keyword_index, page, USE_MERGED_KEYWORDS
            )
            
            # Save raw data
            save_stage1_raw_data_with_prefix("core", all_jobs)
            
            expected_keyword_count = 1 if USE_MERGED_KEYWORDS else len(KEYWORDS)
            if final_location_idx >= len(us_locations) and final_keyword_idx >= expected_keyword_count:
                unique_jobs = load_stage_data_with_prefix("core", "stage1_unique")
                
                if unique_jobs is None:
                    print("\n[Data Validation]")
                    seen = set()
                    unique_jobs = []
                    for job in all_jobs:
                        key = (job.get("Job Title", ""), job.get("Company Name", ""))
                        if key[0] and key[1] and key not in seen:
                            seen.add(key)
                            unique_jobs.append(job)
                    
                    if len(unique_jobs) != len(all_jobs):
                        print(f"Data validation: Duplicates found, deduplicated {len(all_jobs)} -> {len(unique_jobs)} jobs")
                    
                    save_stage_data_with_prefix("core", "stage1_unique", unique_jobs)
                else:
                    print(f"\nUsing saved deduplicated data: {len(unique_jobs)} jobs")
                
                save_checkpoint("stage2_detail", processed_count=0, total_count=len(unique_jobs))
                
                detail_jobs = unique_jobs[:DETAIL_LIMIT]
                enrich_job_details_with_checkpoint(detail_jobs, start_index=0)
                
                # Save detail data
                detail_data = {"jobs": detail_jobs, "processed_urls": [job.get("Job Link", "") for job in detail_jobs]}
                save_stage_data_with_prefix("core", "stage2_detail", detail_data)
                
                # Mark as completed
                save_checkpoint("completed")
                return detail_jobs
            else:
                print("Stage 1 not completed, please continue running the program")
                return None
                
        elif stage == "stage2_detail":
            processed_count = checkpoint.get('processed_count', 0)
            unique_jobs = load_stage_data_with_prefix("core", "stage1_unique")
            
            if unique_jobs is None:
                print("Error: Cannot find deduplicated data, please rerun stage 1")
                return None
            
            detail_data = load_stage_data_with_prefix("core", "stage2_detail")
            processed_jobs = detail_data.get("jobs", []) if detail_data else []
            
            print(f"Processed {len(processed_jobs)} jobs")
            print(f"Resuming detail scraping from job {processed_count+1}...")
            
            detail_jobs = unique_jobs[:DETAIL_LIMIT]
            enrich_job_details_with_checkpoint(detail_jobs, start_index=processed_count)
            
            # Merge processed and new jobs
            final_jobs = {}
            for job in processed_jobs + detail_jobs:
                url = job.get("Job Link", "")
                if url:
                    final_jobs[url] = job
            
            final_job_list = []
            processed_urls = set()
            for job in detail_jobs:
                url = job.get("Job Link", "")
                if url and url not in processed_urls:
                    if url in final_jobs:
                        final_job_list.append(final_jobs[url])
                        processed_urls.add(url)
            
            # Save detail data
            detail_data = {"jobs": final_job_list, "processed_urls": list(processed_urls)}
            save_stage_data_with_prefix("core", "stage2_detail", detail_data)
            
            # Mark as completed
            save_checkpoint("completed")
            reset_paths()
            return final_job_list
    else:
        # No checkpoint, start from beginning
        if USE_MERGED_KEYWORDS:
            print(f"\nStage 1: List page scraping ({len(us_locations)} locations, {len(KEYWORDS)} keywords merged search)")
        else:
            print(f"\nStage 1: List page scraping ({len(us_locations)} locations, {len(KEYWORDS)} keywords separate search)")
        
        all_jobs, completed_locations, completed_keywords, final_location_idx, final_keyword_idx, final_page = fetch_linkedin_list_with_checkpoint(
            KEYWORDS, us_locations, start_location_index=0, start_keyword_index=0, start_page=0, use_merged_keywords=USE_MERGED_KEYWORDS
        )
        
        # Save raw data
        save_stage1_raw_data_with_prefix("core", all_jobs)
        
        # Data validation
        seen = set()
        unique_jobs = []
        for job in all_jobs:
            key = (job.get("Job Title", ""), job.get("Company Name", ""))
            if key[0] and key[1] and key not in seen:
                seen.add(key)
                unique_jobs.append(job)
        
        if len(unique_jobs) != len(all_jobs):
            print(f"Data validation: Duplicates found, deduplicated {len(all_jobs)} -> {len(unique_jobs)} jobs")
        
        # Save deduplicated data
        save_stage_data_with_prefix("core", "stage1_unique", unique_jobs)
        
        # Update checkpoint to stage 2
        save_checkpoint("stage2_detail", processed_count=0, total_count=len(unique_jobs))
        
        # Stage 2: Detail page scraping
        print(f"\nStage 2: Detail page scraping ({len(unique_jobs[:DETAIL_LIMIT])} jobs)")
        detail_jobs = unique_jobs[:DETAIL_LIMIT]
        
        enrich_job_details_with_checkpoint(detail_jobs, start_index=0)
        
        # Save detail data
        detail_data = {"jobs": detail_jobs, "processed_urls": [job.get("Job Link", "") for job in detail_jobs]}
        save_stage_data_with_prefix("core", "stage2_detail", detail_data)
        
        # Mark as completed
        save_checkpoint("completed")
        reset_paths()
        return detail_jobs
    
    reset_paths()
    return None

def scrape_ai_related_jobs(us_locations):
    """Scrape AI-related jobs (low relevance)"""
    print("\n" + "="*60)
    print("Stage B: Scraping AI-Related Jobs (Low Relevance)")
    print("="*60)
    
    # Set independent checkpoint path
    ai_related_dir = f"{MERGED_OUTPUT_DIR}/ai_related_jobs"
    set_country_paths(ai_related_dir)
    
    checkpoint = load_checkpoint()
    
    if checkpoint:
        print(f"\nCheckpoint found, resuming from breakpoint...")
        print(f"Stage: {checkpoint.get('stage')}")
        print(f"Last update: {checkpoint.get('last_update')}")
        
        stage = checkpoint.get('stage')
        
        if stage == "completed":
            # Already completed, directly load saved data
            detail_data = load_stage_data_with_prefix("ai_related", "stage2_detail")
            if detail_data:
                jobs = detail_data.get("jobs", [])
                print(f"AI-related job scraping completed, loading saved data: {len(jobs)} jobs")
                reset_paths()
                return jobs
            else:
                print("Warning: Checkpoint shows completed, but saved data not found, restarting...")
                # Continue execution, start from beginning
        
        if stage == "stage1_list":
            location_index = checkpoint.get('current_location_index', 0)
            keyword_index = checkpoint.get('current_keyword_index', 0)
            page = checkpoint.get('current_page', 0)
            search_keyword_count = 1 if USE_MERGED_KEYWORDS else len(AI_RELATED_KEYWORDS)
            print(f"Resuming from location {location_index+1}/{len(us_locations)} keyword {keyword_index+1}/{search_keyword_count} page {page+1}...")
            
            all_jobs, completed_locations, completed_keywords, final_location_idx, final_keyword_idx, final_page = fetch_linkedin_list_with_checkpoint(
                AI_RELATED_KEYWORDS, us_locations, location_index, keyword_index, page, USE_MERGED_KEYWORDS
            )
            
            # Save raw data
            save_stage1_raw_data_with_prefix("ai_related", all_jobs)
            
            expected_keyword_count = 1 if USE_MERGED_KEYWORDS else len(AI_RELATED_KEYWORDS)
            if final_location_idx >= len(us_locations) and final_keyword_idx >= expected_keyword_count:
                unique_jobs = load_stage_data_with_prefix("ai_related", "stage1_unique")
                
                if unique_jobs is None:
                    print("\n[Data Validation]")
                    seen = set()
                    unique_jobs = []
                    for job in all_jobs:
                        key = (job.get("Job Title", ""), job.get("Company Name", ""))
                        if key[0] and key[1] and key not in seen:
                            seen.add(key)
                            unique_jobs.append(job)
                    
                    if len(unique_jobs) != len(all_jobs):
                        print(f"Data validation: Duplicates found, deduplicated {len(all_jobs)} -> {len(unique_jobs)} jobs")
                    
                    save_stage_data_with_prefix("ai_related", "stage1_unique", unique_jobs)
                else:
                    print(f"\nUsing saved deduplicated data: {len(unique_jobs)} jobs")
                
                save_checkpoint("stage2_detail", processed_count=0, total_count=len(unique_jobs))
                
                detail_jobs = unique_jobs[:DETAIL_LIMIT]
                enrich_job_details_with_checkpoint(detail_jobs, start_index=0)
                
                # Save detail data
                detail_data = {"jobs": detail_jobs, "processed_urls": [job.get("Job Link", "") for job in detail_jobs]}
                save_stage_data_with_prefix("ai_related", "stage2_detail", detail_data)
                
                # Mark as completed
                save_checkpoint("completed")
                return detail_jobs
            else:
                print("Stage 1 not completed, please continue running the program")
                return None
                
        elif stage == "stage2_detail":
            processed_count = checkpoint.get('processed_count', 0)
            unique_jobs = load_stage_data_with_prefix("ai_related", "stage1_unique")
            
            if unique_jobs is None:
                print("Error: Cannot find deduplicated data, please rerun stage 1")
                return None
            
            detail_data = load_stage_data_with_prefix("ai_related", "stage2_detail")
            processed_jobs = detail_data.get("jobs", []) if detail_data else []
            
            print(f"Processed {len(processed_jobs)} jobs")
            print(f"Resuming detail scraping from job {processed_count+1}...")
            
            detail_jobs = unique_jobs[:DETAIL_LIMIT]
            enrich_job_details_with_checkpoint(detail_jobs, start_index=processed_count)
            
            # Merge processed and new jobs
            final_jobs = {}
            for job in processed_jobs + detail_jobs:
                url = job.get("Job Link", "")
                if url:
                    final_jobs[url] = job
            
            final_job_list = []
            processed_urls = set()
            for job in detail_jobs:
                url = job.get("Job Link", "")
                if url and url not in processed_urls:
                    if url in final_jobs:
                        final_job_list.append(final_jobs[url])
                        processed_urls.add(url)
            
            # Save detail data
            detail_data = {"jobs": final_job_list, "processed_urls": list(processed_urls)}
            save_stage_data_with_prefix("ai_related", "stage2_detail", detail_data)
            
            # Mark as completed
            save_checkpoint("completed")
            reset_paths()
            return final_job_list
    else:
        # No checkpoint, start from beginning
        if USE_MERGED_KEYWORDS:
            print(f"\nStage 1: List page scraping ({len(us_locations)} locations, {len(AI_RELATED_KEYWORDS)} keywords merged search)")
        else:
            print(f"\nStage 1: List page scraping ({len(us_locations)} locations, {len(AI_RELATED_KEYWORDS)} keywords separate search)")
        
        all_jobs, completed_locations, completed_keywords, final_location_idx, final_keyword_idx, final_page = fetch_linkedin_list_with_checkpoint(
            AI_RELATED_KEYWORDS, us_locations, start_location_index=0, start_keyword_index=0, start_page=0, use_merged_keywords=USE_MERGED_KEYWORDS
        )
        
        # Save raw data
        save_stage1_raw_data_with_prefix("ai_related", all_jobs)
        
        # Data validation
        seen = set()
        unique_jobs = []
        for job in all_jobs:
            key = (job.get("Job Title", ""), job.get("Company Name", ""))
            if key[0] and key[1] and key not in seen:
                seen.add(key)
                unique_jobs.append(job)
        
        if len(unique_jobs) != len(all_jobs):
            print(f"Data validation: Duplicates found, deduplicated {len(all_jobs)} -> {len(unique_jobs)} jobs")
        
        # Save deduplicated data
        save_stage_data_with_prefix("ai_related", "stage1_unique", unique_jobs)
        
        # Update checkpoint to stage 2
        save_checkpoint("stage2_detail", processed_count=0, total_count=len(unique_jobs))
        
        # Stage 2: Detail page scraping
        print(f"\nStage 2: Detail page scraping ({len(unique_jobs[:DETAIL_LIMIT])} jobs)")
        detail_jobs = unique_jobs[:DETAIL_LIMIT]
        
        enrich_job_details_with_checkpoint(detail_jobs, start_index=0)
        
        # Save detail data
        detail_data = {"jobs": detail_jobs, "processed_urls": [job.get("Job Link", "") for job in detail_jobs]}
        save_stage_data_with_prefix("ai_related", "stage2_detail", detail_data)
        
        # Mark as completed
        save_checkpoint("completed")
        reset_paths()
        return detail_jobs
    
    reset_paths()
    return None

def main():
    print("="*60)
    print("Merged Scraper - Core Jobs + AI-Related Jobs")
    print("="*60)
    print(f"Target site: {TARGET_SITE}")
    print(f"Output directory: {MERGED_OUTPUT_DIR}")
    print(f"Core job keywords: {len(KEYWORDS)} keywords")
    print(f"AI-related job keywords: {len(AI_RELATED_KEYWORDS)} keywords")
    
    if TARGET_SITE != "linkedin":
        print("Current version only supports LinkedIn, please set TARGET_SITE = 'linkedin'")
        return
    
    # Get US locations
    us_locations = get_us_locations_only()
    print(f"\nScraping US locations only: {len(us_locations)} locations")
    
    # Stage A: Scrape core jobs
    core_jobs = scrape_core_jobs(us_locations)
    if core_jobs is None:
        print("\nCore job scraping not completed, please continue running the program")
        return
    
    # Stage B: Scrape AI-related jobs
    ai_related_jobs = scrape_ai_related_jobs(us_locations)
    if ai_related_jobs is None:
        print("\nAI-related job scraping not completed, please continue running the program")
        return
    
    # Stage C: Merge data
    print("\n" + "="*60)
    print("Stage C: Merging Data and Generating Final Report")
    print("="*60)
    
    # Add relevance level
    for job in core_jobs:
        job["relevance level"] = 1
    for job in ai_related_jobs:
        job["relevance level"] = 2
    
    # Deduplicate and merge
    print("\n[Deduplication and Merging]")
    merged_jobs = deduplicate_jobs(core_jobs, ai_related_jobs)
    print(f"Core jobs: {len(core_jobs)} jobs")
    print(f"AI-related jobs: {len(ai_related_jobs)} jobs")
    print(f"Total after deduplication: {len(merged_jobs)} jobs")
    print(f"Duplicates removed: {len(core_jobs) + len(ai_related_jobs) - len(merged_jobs)} jobs")
    
    # Add job label and job level
    print("\n[Adding Job Label and Job Level]")
    for job in merged_jobs:
        job_title = job.get("Job Title", "")
        job["Job Label"] = normalize_job_title(job_title)
        job["Job Level"] = extract_job_level(job_title)
    
    # Build DataFrame according to merged_report_2.xlsx format
    # Column order: relevance level | Job Label | Job Level | Job Title | ... (other FIELDS)
    print("\n[Generating Final Report]")
    df_data = {
        "relevance level": [job.get("relevance level", "") for job in merged_jobs],
        "Job Label": [job.get("Job Label", "") for job in merged_jobs],
        "Job Level": [job.get("Job Level", "") for job in merged_jobs],
    }
    
    # Add other fields
    for field in FIELDS:
        df_data[field] = [job.get(field, "") for job in merged_jobs]
    
    df = pd.DataFrame(df_data)
    
    # Export Excel
    final_output_file = f"{MERGED_OUTPUT_DIR}/merged_report.xlsx"
    os.makedirs(MERGED_OUTPUT_DIR, exist_ok=True)
    df.to_excel(final_output_file, index=False)
    
    print(f"Exported: {final_output_file}")
    print(f"Total jobs: {len(merged_jobs)} jobs")
    print(f"  - Core jobs (relevance level = 1): {sum(1 for j in merged_jobs if j.get('relevance level') == 1)} jobs")
    print(f"  - AI-related jobs (relevance level = 2): {sum(1 for j in merged_jobs if j.get('relevance level') == 2)} jobs")
    
    # Restore original CACHE_FILE
    config.CACHE_FILE = original_cache_file
    scraper_module.CACHE_FILE = original_cache_file
    reset_paths()
    
    print("\n" + "="*60)
    print("Merged Scraping Completed")
    print("="*60)
    print(f"Final report: {final_output_file}")

if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("Program error:")
        print(traceback.format_exc())
        # Ensure reset paths and restore CACHE_FILE
        reset_paths()
        try:
            config.CACHE_FILE = original_cache_file
            scraper_module.CACHE_FILE = original_cache_file
        except:
            pass

