from scraper_linkedin_checkpoint import (
    fetch_linkedin_list_with_checkpoint,
    enrich_job_details_with_checkpoint
)
from checkpoint_manager import (
    load_checkpoint, save_checkpoint,
    load_stage1_raw_data, save_stage1_raw_data,
    load_stage1_unique_data, save_stage1_unique_data,
    load_stage2_detail_data
)
from exporter import export_to_excel
from config import KEYWORDS, LIST_REPORT, DETAIL_REPORT, TARGET_SITE, DETAIL_LIMIT, LOCATIONS, LOCATION, MAX_PAGES, USE_MERGED_KEYWORDS, get_country_output_paths
import traceback
import os

# Optional: Supabase database storage
try:
    from supabase_storage import init_supabase, upsert_jobs, get_job_count
    SUPABASE_ENABLED = True
except ImportError:
    SUPABASE_ENABLED = False
except Exception as e:
    SUPABASE_ENABLED = False

def group_locations_by_country():
    """按国家分组地点"""
    from locations_config import LOCATIONS_BY_STATE
    
    country_groups = {
        "us": [],
        "uk": [],
        "ca": [],
        "sg": [],
        "hk": [],
    }
    
    uk_keywords = ["United Kingdom", "England", "Scotland", "Wales", "Northern Ireland"]
    ca_keywords = ["Canada", "Ontario", "British Columbia", "Quebec", "Alberta", "Manitoba", "Saskatchewan", "Nova Scotia", "Newfoundland", "New Brunswick", "Prince Edward Island", "Yukon", "Northwest Territories", "Nunavut"]
    sg_keywords = ["Singapore"]
    hk_keywords = ["Hong Kong"]
    
    for state, locations in LOCATIONS_BY_STATE.items():
        state_lower = state.lower()
        
        # 检测国家
        if any(kw.lower() in state_lower for kw in uk_keywords):
            country_code = "uk"
        elif any(kw.lower() in state_lower for kw in ca_keywords):
            country_code = "ca"
        elif any(kw.lower() in state_lower for kw in sg_keywords):
            country_code = "sg"
        elif any(kw.lower() in state_lower for kw in hk_keywords):
            country_code = "hk"
        else:
            country_code = "us"  # 默认美国
        
        country_groups[country_code].extend(locations)
    
    return country_groups

def detect_country_from_locations(locations):
    """从地点列表中检测国家（用于单个地点列表）"""
    uk_keywords = ["United Kingdom", "England", "Scotland", "Wales", "Northern Ireland"]
    ca_keywords = ["Canada", "Ontario", "British Columbia", "Quebec", "Alberta"]
    sg_keywords = ["Singapore"]
    hk_keywords = ["Hong Kong"]
    
    for location in locations:
        location_str = str(location).lower()
        if any(kw.lower() in location_str for kw in uk_keywords):
            return "uk"
        elif any(kw.lower() in location_str for kw in ca_keywords):
            return "ca"
        elif any(kw.lower() in location_str for kw in sg_keywords):
            return "sg"
        elif any(kw.lower() in location_str for kw in hk_keywords):
            return "hk"
    return "us"  # Default to US

def process_single_country(country_code, country_locations, country_names):
    """处理单个国家的抓取"""
    print(f"\n{'='*60}")
    print(f"开始处理: {country_names.get(country_code, country_code.upper())} ({len(country_locations)} 个地点)")
    print(f"{'='*60}")
    
    # Get country-specific output paths
    country_paths = get_country_output_paths(country_code)
    os.makedirs(country_paths["dir"], exist_ok=True)
    
    # Initialize Supabase (if enabled) - silent mode
    supabase_initialized = False
    if SUPABASE_ENABLED:
        try:
            init_supabase()
            supabase_initialized = True
        except Exception:
            supabase_initialized = False
    
    # Load checkpoint for this country (stored in country-specific directory)
    from checkpoint_manager import CHECKPOINT_FILE
    country_checkpoint_file = os.path.join(country_paths["dir"], "checkpoint.json")
    checkpoint = None
    if os.path.exists(country_checkpoint_file):
        try:
            import json
            with open(country_checkpoint_file, "r", encoding="utf-8") as f:
                checkpoint = json.load(f)
        except:
            pass
    
    if checkpoint:
        print(f"\n发现checkpoint，从断点恢复...")
        print(f"阶段: {checkpoint.get('stage')}")
        print(f"最后更新: {checkpoint.get('last_update')}")
        
        # Re-detect country for checkpoint resume (in case locations changed)
        country_code = detect_country_from_locations(LOCATIONS)
        country_paths = get_country_output_paths(country_code)
        os.makedirs(country_paths["dir"], exist_ok=True)
        
        stage = checkpoint.get('stage')
        
        if stage == "stage1_list":
            # Resume stage 1
            location_index = checkpoint.get('current_location_index', 0)
            keyword_index = checkpoint.get('current_keyword_index', 0)
            page = checkpoint.get('current_page', 0)
            # When using merged keywords, there's only 1 search keyword
            search_keyword_count = 1 if USE_MERGED_KEYWORDS else len(KEYWORDS)
            print(f"从地点 {location_index+1}/{len(LOCATIONS)} 关键词 {keyword_index+1}/{search_keyword_count} 第 {page+1} 页继续...")
            
            all_jobs, completed_locations, completed_keywords, final_location_idx, final_keyword_idx, final_page = fetch_linkedin_list_with_checkpoint(
                KEYWORDS, LOCATIONS, location_index, keyword_index, page, USE_MERGED_KEYWORDS
            )
            
            # Check if stage 1 is complete
            # When using merged keywords, only need to check if all locations are done (keyword_idx will be 0 or 1)
            expected_keyword_count = 1 if USE_MERGED_KEYWORDS else len(KEYWORDS)
            if final_location_idx >= len(LOCATIONS) and final_keyword_idx >= expected_keyword_count:
                # Stage 1 complete, check if deduplicated data already exists
                unique_jobs = load_stage1_unique_data()
                
                if unique_jobs is None:
                    # Data has been deduplicated in real-time during scraping, only need to verify here
                    print("\n【数据验证】")
                    seen = set()
                    unique_jobs = []
                    for job in all_jobs:
                        key = (job.get("职位名称", ""), job.get("公司名称", ""))
                        if key[0] and key[1] and key not in seen:
                            seen.add(key)
                            unique_jobs.append(job)
                    
                    if len(unique_jobs) != len(all_jobs):
                        print(f"数据验证: 发现重复，已去重 {len(all_jobs)} -> {len(unique_jobs)} 条")
                    
                    # Save deduplicated data
                    save_stage1_unique_data(unique_jobs)
                else:
                    print(f"\n使用已保存的去重数据: {len(unique_jobs)} 条")
                
                # Export list page report (country-specific)
                export_to_excel(unique_jobs, country_paths["list_report"])
                
                # Store to Supabase (if enabled) - silent
                if supabase_initialized and unique_jobs:
                    try:
                        upsert_jobs(unique_jobs, batch_size=100, country_code=country_code)
                    except Exception:
                        pass
                
                # Update checkpoint to stage 2
                save_checkpoint(
                    stage="stage2_detail",
                    processed_count=0,
                    total_count=len(unique_jobs)
                )
                
                # Continue stage 2
                detail_jobs = unique_jobs[:DETAIL_LIMIT]
                enrich_job_details_with_checkpoint(detail_jobs, start_index=0)
                export_to_excel(detail_jobs, country_paths["detail_report"])
                
                # Update detail data in Supabase (if enabled) - silent
                if supabase_initialized and detail_jobs:
                    try:
                        upsert_jobs(detail_jobs, batch_size=100, country_code=country_code)
                    except Exception:
                        pass
            else:
                print("阶段1尚未完成，请继续运行程序")
            
        elif stage == "stage2_detail":
            # Resume stage 2
            processed_count = checkpoint.get('processed_count', 0)
            unique_jobs = load_stage1_unique_data()
            
            if unique_jobs is None:
                print("错误：找不到去重后的数据，请重新运行阶段1")
                return
            
            # Load processed job data
            detail_data = load_stage2_detail_data()
            processed_jobs = detail_data.get("jobs", [])
            
            print(f"已处理 {len(processed_jobs)} 条职位")
            print(f"从第 {processed_count+1} 条继续抓取详情...")
            
            detail_jobs = unique_jobs[:DETAIL_LIMIT]
            
            # Continue processing remaining jobs
            enrich_job_details_with_checkpoint(detail_jobs, start_index=processed_count)
            
            # Merge processed and new jobs (deduplicate by URL)
            final_jobs = {}
            for job in processed_jobs + detail_jobs:
                url = job.get("职位链接", "")
                if url:
                    final_jobs[url] = job
            
            # Convert to list, maintain original order
            final_job_list = []
            processed_urls = set()
            for job in detail_jobs:
                url = job.get("职位链接", "")
                if url and url not in processed_urls:
                    if url in final_jobs:
                        final_job_list.append(final_jobs[url])
                        processed_urls.add(url)
            
            export_to_excel(final_job_list, country_paths["detail_report"])
        
        print("抓取完成")
        return
    
    # No checkpoint, start from beginning
    if USE_MERGED_KEYWORDS:
        print(f"\n阶段1: 列表页抓取 ({len(LOCATIONS)} 个地点，{len(KEYWORDS)} 个关键词合并搜索)")
    else:
        print(f"\n阶段1: 列表页抓取 ({len(LOCATIONS)} 个地点，{len(KEYWORDS)} 个关键词分别搜索)")
    
    all_jobs, completed_locations, completed_keywords, final_location_idx, final_keyword_idx, final_page = fetch_linkedin_list_with_checkpoint(
        KEYWORDS, LOCATIONS, start_location_index=0, start_keyword_index=0, start_page=0, use_merged_keywords=USE_MERGED_KEYWORDS
    )
    
    # Data has been deduplicated in real-time during scraping, all_jobs already contains only unique jobs
    # Only need to verify and save here
    seen = set()
    unique_jobs = []
    for job in all_jobs:
        key = (job.get("职位名称", ""), job.get("公司名称", ""))
        if key[0] and key[1] and key not in seen:
            seen.add(key)
            unique_jobs.append(job)
    
    if len(unique_jobs) != len(all_jobs):
        print(f"数据验证: 发现重复，已去重 {len(all_jobs)} -> {len(unique_jobs)} 条")
    
    # Save deduplicated data
    save_stage1_unique_data(unique_jobs)
    
    # Export list page report (country-specific)
    export_to_excel(unique_jobs, country_paths["list_report"])
    
    # Update checkpoint to stage 2
    save_checkpoint(
        stage="stage2_detail",
        processed_count=0,
        total_count=len(unique_jobs)
    )
    
    # Stage 2: detail page scraping
    print(f"\n阶段2: 详情页抓取 ({len(unique_jobs[:DETAIL_LIMIT])} 条)")
    detail_jobs = unique_jobs[:DETAIL_LIMIT]
    
    enrich_job_details_with_checkpoint(detail_jobs, start_index=0)
    
    # Export detail page report (country-specific)
    export_to_excel(detail_jobs, country_paths["detail_report"])
    
    # Update detail data in Supabase (if enabled) - silent
    if supabase_initialized and detail_jobs:
        try:
            upsert_jobs(detail_jobs, batch_size=100, country_code=country_code)
        except Exception:
            pass
    
    print("抓取完成")

if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("程序出错：")
        print(traceback.format_exc())
