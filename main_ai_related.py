# -*- coding: utf-8 -*-
"""
AI弱相关岗位独立抓取程序
使用相同的抓取框架，但使用独立的关键词和输出目录
"""
# 在导入scraper之前，设置独立的缓存文件路径
import sys
import os

# 独立输出目录配置
AI_RELATED_RUN_ID = "AI_Related_Test001"
AI_RELATED_OUTPUT_DIR = f"outputs/{AI_RELATED_RUN_ID}"
AI_RELATED_CACHE_FILE = f"{AI_RELATED_OUTPUT_DIR}/company_cache.json"

# 临时修改scraper模块的CACHE_FILE（通过monkey patching）
# 先导入config获取原始值
import config
original_cache_file = config.CACHE_FILE

# 修改config的CACHE_FILE
config.CACHE_FILE = AI_RELATED_CACHE_FILE

# 现在导入scraper（它会使用修改后的CACHE_FILE）
from scraper_linkedin_checkpoint import (
    fetch_linkedin_list_with_checkpoint,
    enrich_job_details_with_checkpoint
)
import scraper_linkedin_checkpoint as scraper_module

# 确保scraper模块也使用新的CACHE_FILE（因为它在导入时可能已经缓存了旧值）
scraper_module.CACHE_FILE = AI_RELATED_CACHE_FILE

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
    get_country_output_paths, FIELDS
)
import traceback
import json

# AI弱相关岗位关键词列表
AI_RELATED_KEYWORDS = [
    # AI销售相关
    "AI Sales", "AI Sales Representative", "AI Sales Manager", 
    "AI Business Development", "AI Account Manager",
    
    # AI会话师相关
    "AI Conversation", "AI Conversational Designer", "AI Chatbot Designer",
    "AI Dialogue Designer", "Conversational AI", "AI Voice Assistant",
    
    # AI训练师相关
    "AI Training", "AI Trainer", "AI Model Training", "AI Data Training",
    "AI Training Specialist", "Machine Learning Trainer",
    
    # AI产品经理相关
    "AI Product Manager", "AI PM", "AI Product Owner", "AI Product Lead",
    
    # AI+行业相关
    "AI Healthcare", "AI Finance", "AI Education", "AI Retail", 
    "AI Manufacturing", "AI Agriculture", "AI Transportation",
    "AI Energy", "AI Legal", "AI Marketing",
    
    # AI艺术相关
    "AI Art", "AI Artist", "AI Painting", "AI Illustrator", 
    "AI Creative", "AI Digital Art", "AI Visual Artist",
    
    # AI设计相关
    "AI Design", "AI Designer", "AI UX Designer", "AI UI Designer",
    "AI Interaction Designer", "AI Design Specialist",
    
    # AI架构相关
    "AI Architecture", "AI Architect", "AI System Architecture",
    "AI Solution Architect", "AI Platform Architect",
    
    # AI治理相关
    "AI Governance", "AI Governance Specialist", "AI Compliance",
    "AI Risk Management", "AI Policy",
    
    # AI伦理相关
    "AI Ethics", "AI Ethical", "AI Ethics Researcher", 
    "Responsible AI", "AI Fairness", "AI Bias",
    
    # AI硬件相关
    "AI Hardware", "AI Hardware Engineer", "AI Chip Design",
    "AI Accelerator", "AI Processor",
    
    # AI运维相关
    "AI Operations", "AI Ops", "AI DevOps", "AI Infrastructure",
    "AI MLOps", "AI Platform Engineer", "AI Systems Engineer",
    
    # 数据标注相关
    "Data Annotation", "Data Labeling", "Data Annotator", 
    "Data Tagging", "Data Quality", "Data Curation",
    
    # 机器人相关
    "Robotics", "Robot Engineer", "Robotics Engineer", 
    "Autonomous Systems", "Robotic Process Automation", "RPA",
]

# 设置输出路径
AI_RELATED_LIST_REPORT = f"{AI_RELATED_OUTPUT_DIR}/report_stage1_list.xlsx"
AI_RELATED_DETAIL_REPORT = f"{AI_RELATED_OUTPUT_DIR}/report_stage2_detail.xlsx"

# 使用合并关键词搜索（减少API调用）
USE_MERGED_KEYWORDS = True

def get_us_locations_only():
    """只获取美国的地点"""
    from locations_config import LOCATIONS_BY_STATE
    
    us_locations = []
    uk_keywords = ["United Kingdom", "England", "Scotland", "Wales", "Northern Ireland"]
    ca_keywords = ["Canada", "Ontario", "British Columbia", "Quebec", "Alberta", "Manitoba", "Saskatchewan", "Nova Scotia", "Newfoundland", "New Brunswick", "Prince Edward Island", "Yukon", "Northwest Territories", "Nunavut"]
    sg_keywords = ["Singapore"]
    hk_keywords = ["Hong Kong"]
    
    for state, locations in LOCATIONS_BY_STATE.items():
        state_lower = state.lower()
        
        # 跳过非美国的地点
        if any(kw.lower() in state_lower for kw in uk_keywords):
            continue
        elif any(kw.lower() in state_lower for kw in ca_keywords):
            continue
        elif any(kw.lower() in state_lower for kw in sg_keywords):
            continue
        elif any(kw.lower() in state_lower for kw in hk_keywords):
            continue
        
        # 只添加美国的地点
        us_locations.extend(locations)
    
    return us_locations

def main():
    print("="*60)
    print("AI弱相关岗位抓取程序")
    print("="*60)
    print(f"目标网站: {TARGET_SITE}")
    print(f"关键词数量: {len(AI_RELATED_KEYWORDS)}")
    if USE_MERGED_KEYWORDS:
        print(f"搜索模式: 合并关键词搜索（减少API调用）")
    else:
        print(f"搜索模式: 分别搜索每个关键词")
    
    if TARGET_SITE != "linkedin":
        print("当前版本仅支持LinkedIn，请设置 TARGET_SITE = 'linkedin'")
        return
    
    # 设置独立的checkpoint路径
    set_country_paths(AI_RELATED_OUTPUT_DIR)
    
    # 获取美国地点
    us_locations = get_us_locations_only()
    print(f"\n只抓取美国地点: {len(us_locations)} 个地点")
    print(f"输出目录: {AI_RELATED_OUTPUT_DIR}")
    
    # 检查checkpoint
    checkpoint = load_checkpoint()
    
    if checkpoint:
        print(f"\n发现checkpoint，从断点恢复...")
        print(f"阶段: {checkpoint.get('stage')}")
        print(f"最后更新: {checkpoint.get('last_update')}")
        
        stage = checkpoint.get('stage')
        
        if stage == "stage1_list":
            # 恢复阶段1
            location_index = checkpoint.get('current_location_index', 0)
            keyword_index = checkpoint.get('current_keyword_index', 0)
            page = checkpoint.get('current_page', 0)
            search_keyword_count = 1 if USE_MERGED_KEYWORDS else len(AI_RELATED_KEYWORDS)
            print(f"从地点 {location_index+1}/{len(us_locations)} 关键词 {keyword_index+1}/{search_keyword_count} 第 {page+1} 页继续...")
            
            all_jobs, completed_locations, completed_keywords, final_location_idx, final_keyword_idx, final_page = fetch_linkedin_list_with_checkpoint(
                AI_RELATED_KEYWORDS, us_locations, location_index, keyword_index, page, USE_MERGED_KEYWORDS
            )
            
            # 检查阶段1是否完成
            expected_keyword_count = 1 if USE_MERGED_KEYWORDS else len(AI_RELATED_KEYWORDS)
            if final_location_idx >= len(us_locations) and final_keyword_idx >= expected_keyword_count:
                # 阶段1完成
                unique_jobs = load_stage1_unique_data()
                
                if unique_jobs is None:
                    # 数据验证
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
                    
                    save_stage1_unique_data(unique_jobs)
                else:
                    print(f"\n使用已保存的去重数据: {len(unique_jobs)} 条")
                
                # 导出列表页报告
                export_to_excel(unique_jobs, AI_RELATED_LIST_REPORT)
                print(f"已导出列表页数据: {AI_RELATED_LIST_REPORT}")
                
                # 更新checkpoint到阶段2
                save_checkpoint(
                    stage="stage2_detail",
                    processed_count=0,
                    total_count=len(unique_jobs)
                )
                
                # 继续阶段2
                detail_jobs = unique_jobs[:DETAIL_LIMIT]
                enrich_job_details_with_checkpoint(detail_jobs, start_index=0)
                export_to_excel(detail_jobs, AI_RELATED_DETAIL_REPORT)
                print(f"已导出详情页数据: {AI_RELATED_DETAIL_REPORT}")
            else:
                print("阶段1尚未完成，请继续运行程序")
            
        elif stage == "stage2_detail":
            # 恢复阶段2
            processed_count = checkpoint.get('processed_count', 0)
            unique_jobs = load_stage1_unique_data()
            
            if unique_jobs is None:
                print("错误：找不到去重后的数据，请重新运行阶段1")
                return
            
            # 加载已处理的职位数据
            detail_data = load_stage2_detail_data()
            processed_jobs = detail_data.get("jobs", [])
            
            print(f"已处理 {len(processed_jobs)} 条职位")
            print(f"从第 {processed_count+1} 条继续抓取详情...")
            
            detail_jobs = unique_jobs[:DETAIL_LIMIT]
            
            # 继续处理剩余的职位
            enrich_job_details_with_checkpoint(detail_jobs, start_index=processed_count)
            
            # 合并已处理和新增的职位（按URL去重）
            final_jobs = {}
            for job in processed_jobs + detail_jobs:
                url = job.get("职位链接", "")
                if url:
                    final_jobs[url] = job
            
            # 转换为列表，保持原始顺序
            final_job_list = []
            processed_urls = set()
            for job in detail_jobs:
                url = job.get("职位链接", "")
                if url and url not in processed_urls:
                    if url in final_jobs:
                        final_job_list.append(final_jobs[url])
                        processed_urls.add(url)
            
            export_to_excel(final_job_list, AI_RELATED_DETAIL_REPORT)
            print(f"已导出详情页数据: {AI_RELATED_DETAIL_REPORT}")
        
        print("\n抓取完成")
        # 重置路径
        reset_paths()
        return
    
    # 没有checkpoint，从头开始
    if USE_MERGED_KEYWORDS:
        print(f"\n阶段1: 列表页抓取 ({len(us_locations)} 个地点，{len(AI_RELATED_KEYWORDS)} 个关键词合并搜索)")
    else:
        print(f"\n阶段1: 列表页抓取 ({len(us_locations)} 个地点，{len(AI_RELATED_KEYWORDS)} 个关键词分别搜索)")
    
    all_jobs, completed_locations, completed_keywords, final_location_idx, final_keyword_idx, final_page = fetch_linkedin_list_with_checkpoint(
        AI_RELATED_KEYWORDS, us_locations, start_location_index=0, start_keyword_index=0, start_page=0, use_merged_keywords=USE_MERGED_KEYWORDS
    )
    
    # 数据验证
    seen = set()
    unique_jobs = []
    for job in all_jobs:
        key = (job.get("职位名称", ""), job.get("公司名称", ""))
        if key[0] and key[1] and key not in seen:
            seen.add(key)
            unique_jobs.append(job)
    
    if len(unique_jobs) != len(all_jobs):
        print(f"数据验证: 发现重复，已去重 {len(all_jobs)} -> {len(unique_jobs)} 条")
    
    # 保存去重后的数据
    save_stage1_unique_data(unique_jobs)
    
    # 导出列表页报告
    export_to_excel(unique_jobs, AI_RELATED_LIST_REPORT)
    print(f"已导出列表页数据: {AI_RELATED_LIST_REPORT}")
    
    # 更新checkpoint到阶段2
    save_checkpoint(
        stage="stage2_detail",
        processed_count=0,
        total_count=len(unique_jobs)
    )
    
    # 阶段2: 详情页抓取
    print(f"\n阶段2: 详情页抓取 ({len(unique_jobs[:DETAIL_LIMIT])} 条)")
    detail_jobs = unique_jobs[:DETAIL_LIMIT]
    
    enrich_job_details_with_checkpoint(detail_jobs, start_index=0)
    
    # 导出详情页报告
    export_to_excel(detail_jobs, AI_RELATED_DETAIL_REPORT)
    print(f"已导出详情页数据: {AI_RELATED_DETAIL_REPORT}")
    
    # 重置路径
    reset_paths()
    
    # 恢复原始CACHE_FILE
    config.CACHE_FILE = original_cache_file
    scraper_module.CACHE_FILE = original_cache_file
    
    print("\n" + "="*60)
    print("AI弱相关岗位抓取完成")
    print("="*60)
    print(f"列表页数据: {AI_RELATED_LIST_REPORT}")
    print(f"详情页数据: {AI_RELATED_DETAIL_REPORT}")
    print(f"\n下一步: 运行 python merge_and_classify.py 进行合并和分类")

if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("程序出错：")
        print(traceback.format_exc())
        # 确保重置路径和恢复CACHE_FILE
        reset_paths()
        try:
            config.CACHE_FILE = original_cache_file
            scraper_module.CACHE_FILE = original_cache_file
        except:
            pass

