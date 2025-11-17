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
from config import KEYWORDS, TARGET_SITE, DETAIL_LIMIT, MAX_PAGES, USE_MERGED_KEYWORDS, get_country_output_paths, OUTPUT_DIR
import traceback
import os
import json
import shutil

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
    
    # Set country-specific paths in checkpoint_manager
    from checkpoint_manager import set_country_paths, load_checkpoint
    set_country_paths(country_paths["dir"])
    
    # Load checkpoint for this country
    checkpoint = load_checkpoint()
    
    if checkpoint:
        print(f"\n发现checkpoint，从断点恢复...")
        print(f"阶段: {checkpoint.get('stage')}")
        print(f"最后更新: {checkpoint.get('last_update')}")
        
        stage = checkpoint.get('stage')
        
        if stage == "stage1_list":
            # Resume stage 1
            location_index = checkpoint.get('current_location_index', 0)
            keyword_index = checkpoint.get('current_keyword_index', 0)
            page = checkpoint.get('current_page', 0)
            search_keyword_count = 1 if USE_MERGED_KEYWORDS else len(KEYWORDS)
            print(f"从地点 {location_index+1}/{len(country_locations)} 关键词 {keyword_index+1}/{search_keyword_count} 第 {page+1} 页继续...")
            
            try:
                all_jobs, completed_locations, completed_keywords, final_location_idx, final_keyword_idx, final_page = fetch_linkedin_list_with_checkpoint(
                    KEYWORDS, country_locations, location_index, keyword_index, page, USE_MERGED_KEYWORDS
                )
                
                expected_keyword_count = 1 if USE_MERGED_KEYWORDS else len(KEYWORDS)
                if final_location_idx >= len(country_locations) and final_keyword_idx >= expected_keyword_count:
                    unique_jobs = load_stage1_unique_data()
                    
                    if unique_jobs is None:
                        seen = set()
                        unique_jobs = []
                        for job in all_jobs:
                            key = (job.get("职位名称", ""), job.get("公司名称", ""))
                            if key[0] and key[1] and key not in seen:
                                seen.add(key)
                                unique_jobs.append(job)
                        
                        save_stage1_unique_data(unique_jobs)
                    
                    export_to_excel(unique_jobs, country_paths["list_report"])
                    
                    if supabase_initialized and unique_jobs:
                        try:
                            upsert_jobs(unique_jobs, batch_size=100, country_code=country_code)
                        except Exception:
                            pass
                    
                    from checkpoint_manager import save_checkpoint
                    save_checkpoint("stage2_detail", processed_count=0, total_count=len(unique_jobs))
                    
                    detail_jobs = unique_jobs[:DETAIL_LIMIT]
                    enrich_job_details_with_checkpoint(detail_jobs, start_index=0)
                    export_to_excel(detail_jobs, country_paths["detail_report"])
                    
                    if supabase_initialized and detail_jobs:
                        try:
                            upsert_jobs(detail_jobs, batch_size=100, country_code=country_code)
                        except Exception:
                            pass
                    
                    print(f"\n✓ {country_names.get(country_code, country_code.upper())} 抓取完成")
                else:
                    print("阶段1尚未完成，请继续运行程序")
            finally:
                # Reset to default paths
                from checkpoint_manager import reset_paths
                reset_paths()
            
        elif stage == "stage2_detail":
            processed_count = checkpoint.get('processed_count', 0)
            unique_jobs = load_stage1_unique_data()
            
            if unique_jobs is None:
                print("错误：找不到去重后的数据，请重新运行阶段1")
                return
            
            detail_data = load_stage2_detail_data()
            processed_jobs = detail_data.get("jobs", [])
            
            print(f"已处理 {len(processed_jobs)} 条职位")
            print(f"从第 {processed_count+1} 条继续抓取详情...")
            
            detail_jobs = unique_jobs[:DETAIL_LIMIT]
            enrich_job_details_with_checkpoint(detail_jobs, start_index=processed_count)
            
            final_jobs = {}
            for job in processed_jobs + detail_jobs:
                url = job.get("职位链接", "")
                if url:
                    final_jobs[url] = job
            
            final_job_list = []
            processed_urls = set()
            for job in detail_jobs:
                url = job.get("职位链接", "")
                if url and url not in processed_urls:
                    if url in final_jobs:
                        final_job_list.append(final_jobs[url])
                        processed_urls.add(url)
            
            export_to_excel(final_job_list, country_paths["detail_report"])
            print(f"\n✓ {country_names.get(country_code, country_code.upper())} 抓取完成")
        
        return
    
    # No checkpoint, start from beginning
    # Set country-specific paths in checkpoint_manager
    from checkpoint_manager import set_country_paths
    set_country_paths(country_paths["dir"])
    
    try:
        if USE_MERGED_KEYWORDS:
            print(f"\n阶段1: 列表页抓取 ({len(country_locations)} 个地点，{len(KEYWORDS)} 个关键词合并搜索)")
        else:
            print(f"\n阶段1: 列表页抓取 ({len(country_locations)} 个地点，{len(KEYWORDS)} 个关键词分别搜索)")
        
        all_jobs, completed_locations, completed_keywords, final_location_idx, final_keyword_idx, final_page = fetch_linkedin_list_with_checkpoint(
            KEYWORDS, country_locations, start_location_index=0, start_keyword_index=0, start_page=0, use_merged_keywords=USE_MERGED_KEYWORDS
        )
        
        seen = set()
        unique_jobs = []
        for job in all_jobs:
            key = (job.get("职位名称", ""), job.get("公司名称", ""))
            if key[0] and key[1] and key not in seen:
                seen.add(key)
                unique_jobs.append(job)
        
        if len(unique_jobs) != len(all_jobs):
            print(f"数据验证: 发现重复，已去重 {len(all_jobs)} -> {len(unique_jobs)} 条")
        
        save_stage1_unique_data(unique_jobs)
        export_to_excel(unique_jobs, country_paths["list_report"])
        
        from checkpoint_manager import save_checkpoint
        save_checkpoint("stage2_detail", processed_count=0, total_count=len(unique_jobs))
        
        print(f"\n阶段2: 详情页抓取 ({len(unique_jobs[:DETAIL_LIMIT])} 条)")
        detail_jobs = unique_jobs[:DETAIL_LIMIT]
        
        enrich_job_details_with_checkpoint(detail_jobs, start_index=0)
        export_to_excel(detail_jobs, country_paths["detail_report"])
        
        if supabase_initialized and detail_jobs:
            try:
                upsert_jobs(detail_jobs, batch_size=100, country_code=country_code)
            except Exception:
                pass
        
        print(f"\n✓ {country_names.get(country_code, country_code.upper())} 抓取完成")
    finally:
        # Reset to default paths
        from checkpoint_manager import reset_paths
        reset_paths()

def main():
    print(f"启动抓取程序（目标网站: {TARGET_SITE}）")
    
    if TARGET_SITE != "linkedin":
        print("当前版本仅支持LinkedIn，请设置 TARGET_SITE = 'linkedin'")
        return
    
    # Group locations by country
    country_groups = group_locations_by_country()
    country_names = {"us": "美国", "uk": "英国", "ca": "加拿大", "sg": "新加坡", "hk": "香港"}
    
    print(f"\n检测到 {len([c for c, locs in country_groups.items() if locs])} 个国家/地区:")
    for country_code, locations in country_groups.items():
        if locations:
            print(f"  - {country_names.get(country_code, country_code.upper())}: {len(locations)} 个地点")
    
    # Process each country
    for country_code, country_locations in country_groups.items():
        if not country_locations:
            continue
        
        try:
            process_single_country(country_code, country_locations, country_names)
        except Exception as e:
            print(f"\n✗ {country_names.get(country_code, country_code.upper())} 处理失败: {str(e)}")
            import traceback
            traceback.print_exc()
            continue
    
    print(f"\n{'='*60}")
    print("所有国家抓取完成！")
    print(f"{'='*60}")

if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("程序出错：")
        print(traceback.format_exc())

