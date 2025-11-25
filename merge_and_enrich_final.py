# -*- coding: utf-8 -*-
"""
合并和补全最终报告
1. 移除AI_Related_Test001中与BunchTest017重复的职位
2. 补全AI_Related_Test001的stage2信息
3. 融合两个stage2结果，添加relevance level
4. 转换薪资单位中英文
"""
import pandas as pd
import os
import sys

# 在导入scraper之前，设置独立的缓存文件路径
FINAL_OUTPUT_DIR = r"C:\Users\Dylan\JobScrapper\outputs\Final_Merged_Report"
FINAL_CACHE_FILE = os.path.join(FINAL_OUTPUT_DIR, "company_cache.json")

# 临时修改config模块的CACHE_FILE（在导入scraper之前）
import config
original_cache_file = config.CACHE_FILE
config.CACHE_FILE = FINAL_CACHE_FILE

# 现在导入scraper（它会使用修改后的CACHE_FILE）
from scraper_linkedin_checkpoint import enrich_job_details_with_checkpoint
import scraper_linkedin_checkpoint as scraper_module

# 确保scraper模块也使用新的CACHE_FILE
scraper_module.CACHE_FILE = FINAL_CACHE_FILE

from checkpoint_manager import (
    set_country_paths, reset_paths,
    save_checkpoint, load_checkpoint,
    load_stage2_detail_data, save_stage2_detail_data
)
from exporter import export_to_excel
from config import DETAIL_LIMIT, FIELDS
import json
import re

# 文件路径配置
AI_RELATED_DIR = r"C:\Users\Dylan\JobScrapper\outputs\AI_Related_Test001"
ORIGINAL_DIR = r"C:\Users\Dylan\JobScrapper\outputs\BunchTest017"

AI_RELATED_STAGE2_FILE = os.path.join(AI_RELATED_DIR, "report_stage2_detail_new.xlsx")
ORIGINAL_STAGE2_FILE = os.path.join(ORIGINAL_DIR, "report_stage2_detail.xlsx")

FINAL_OUTPUT_FILE = os.path.join(FINAL_OUTPUT_DIR, "final_merged_report.xlsx")

def load_excel_data(file_path):
    """加载Excel文件数据"""
    if not os.path.exists(file_path):
        print(f"错误: 文件不存在: {file_path}")
        return []
    
    try:
        df = pd.read_excel(file_path)
        jobs = df.to_dict('records')
        print(f"成功加载: {file_path} ({len(jobs)} 条)")
        return jobs
    except Exception as e:
        print(f"加载文件失败 {file_path}: {str(e)}")
        return []

def safe_get_str(job, key, default=""):
    """安全获取字符串值，处理NaN情况"""
    value = job.get(key, default)
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return default
    return str(value).strip()

def remove_duplicates(ai_related_jobs, original_jobs):
    """
    从AI_Related中移除与Original中重复的职位
    基于 (职位名称, 公司名称) 去重
    """
    # 构建原始数据的键集合
    original_keys = set()
    for job in original_jobs:
        job_title = safe_get_str(job, "职位名称")
        company_name = safe_get_str(job, "公司名称")
        if job_title and company_name:
            key = (job_title, company_name)
            original_keys.add(key)
    
    # 找出非重复的职位
    unique_jobs = []
    removed_count = 0
    
    for job in ai_related_jobs:
        job_title = safe_get_str(job, "职位名称")
        company_name = safe_get_str(job, "公司名称")
        if job_title and company_name:
            key = (job_title, company_name)
            if key not in original_keys:
                unique_jobs.append(job)
            else:
                removed_count += 1
    
    return unique_jobs, removed_count

def check_job_completeness(job):
    """检查职位数据是否完整（是否有工作描述）"""
    # 只要有工作描述就认为基本完整，薪资可能确实没有
    description = job.get("工作描述", "")
    # 处理可能为NaN的情况（pandas读取Excel时，空值可能是float类型的NaN）
    if description is None or (isinstance(description, float) and pd.isna(description)):
        description = ""
    else:
        description = str(description).strip()
    has_description = bool(description)
    return has_description

def translate_salary_unit(text):
    """将薪资单位从中文转换为英文"""
    # 处理可能为NaN的情况
    if text is None or (isinstance(text, float) and pd.isna(text)):
        return ""
    
    text = str(text)
    if not text:
        return text
    
    # 替换中文单位
    text = text.replace("(时薪)", "(hourly)")
    text = text.replace("(年薪)", "(yearly)")
    text = text.replace("(月薪)", "(monthly)")
    text = text.replace("时薪", "hourly")
    text = text.replace("年薪", "yearly")
    text = text.replace("月薪", "monthly")
    
    return text

def translate_salary_in_jobs(job_list):
    """批量转换职位列表中的薪资单位"""
    for job in job_list:
        if "薪资要求" in job:
            job["薪资要求"] = translate_salary_unit(job.get("薪资要求", ""))
    return job_list

def main():
    print("="*60)
    print("合并和补全最终报告程序")
    print("="*60)
    
    # 确保输出目录存在
    os.makedirs(FINAL_OUTPUT_DIR, exist_ok=True)
    
    # 1. 加载两个stage2数据
    print("\n【步骤1】加载stage2数据")
    print("-" * 60)
    ai_related_jobs = load_excel_data(AI_RELATED_STAGE2_FILE)
    original_jobs = load_excel_data(ORIGINAL_STAGE2_FILE)
    
    if not ai_related_jobs:
        print("错误: AI_Related_Test001 stage2数据为空")
        return
    
    if not original_jobs:
        print("警告: BunchTest017 stage2数据为空")
    
    print(f"AI_Related_Test001: {len(ai_related_jobs)} 条")
    print(f"BunchTest017: {len(original_jobs)} 条")
    
    # 2. 移除重复职位
    print("\n【步骤2】移除重复职位")
    print("-" * 60)
    unique_ai_jobs, removed_count = remove_duplicates(ai_related_jobs, original_jobs)
    print(f"移除重复职位: {removed_count} 条")
    print(f"剩余唯一职位: {len(unique_ai_jobs)} 条")
    
    if len(unique_ai_jobs) == 0:
        print("没有剩余职位，程序结束")
        return
    
    # 3. 检查哪些职位需要补全
    print("\n【步骤3】检查需要补全的职位")
    print("-" * 60)
    incomplete_jobs = []
    complete_jobs = []
    
    for job in unique_ai_jobs:
        if check_job_completeness(job):
            complete_jobs.append(job)
        else:
            incomplete_jobs.append(job)
    
    print(f"完整职位: {len(complete_jobs)} 条")
    print(f"需要补全: {len(incomplete_jobs)} 条")
    
    # 4. 补全不完整的职位
    if incomplete_jobs:
        print(f"\n【步骤4】补全职位详情（共 {len(incomplete_jobs)} 条）")
        print("-" * 60)
        
        # 设置checkpoint路径
        set_country_paths(FINAL_OUTPUT_DIR)
        
        # 清除旧的stage2_detail_data.json（避免使用之前的处理记录）
        stage2_detail_file = os.path.join(FINAL_OUTPUT_DIR, "stage2_detail_data.json")
        if os.path.exists(stage2_detail_file):
            try:
                os.remove(stage2_detail_file)
                print("已清除旧的详情数据文件")
            except Exception as e:
                print(f"警告: 无法删除 stage2_detail_data.json: {str(e)}")
        
        # 检查checkpoint
        checkpoint = load_checkpoint()
        start_index = 0
        
        if checkpoint and checkpoint.get('stage') == 'stage2_detail':
            processed_count = checkpoint.get('processed_count', 0)
            print(f"发现checkpoint，从第 {processed_count+1} 条继续...")
            start_index = processed_count
        else:
            # 初始化checkpoint
            checkpoint_file = os.path.join(FINAL_OUTPUT_DIR, "checkpoint.json")
            if os.path.exists(checkpoint_file):
                try:
                    os.remove(checkpoint_file)
                except:
                    pass
            save_checkpoint(
                stage="stage2_detail",
                processed_count=0,
                total_count=len(incomplete_jobs)
            )
        
        # 限制补全数量
        jobs_to_enrich = incomplete_jobs[:DETAIL_LIMIT]
        print(f"开始补全详情（共 {len(jobs_to_enrich)} 条，限制: {DETAIL_LIMIT}）")
        
        # 补全详情
        enrich_job_details_with_checkpoint(jobs_to_enrich, start_index=start_index)
        
        # 合并完整和补全后的职位（按原始顺序）
        # 需要保持原始顺序，所以重新构建列表
        all_ai_jobs = []
        enriched_urls = {job.get("职位链接", "") for job in jobs_to_enrich}
        for job in unique_ai_jobs:
            job_url = job.get("职位链接", "")
            if job_url in enriched_urls:
                # 找到补全后的版本
                for enriched_job in jobs_to_enrich:
                    if enriched_job.get("职位链接", "") == job_url:
                        all_ai_jobs.append(enriched_job)
                        break
            else:
                # 保持原有的完整职位
                all_ai_jobs.append(job)
    else:
        # 没有需要补全的职位，使用所有唯一职位
        all_ai_jobs = unique_ai_jobs
    
    # 5. 添加relevance level并转换薪资单位
    print("\n【步骤5】添加relevance level并转换薪资单位")
    print("-" * 60)
    
    # 为BunchTest017添加relevance level = 1
    for job in original_jobs:
        job["relevance level"] = 1
    original_jobs = translate_salary_in_jobs(original_jobs)
    
    # 为AI_Related添加relevance level = 2
    for job in all_ai_jobs:
        job["relevance level"] = 2
    all_ai_jobs = translate_salary_in_jobs(all_ai_jobs)
    
    # 6. 合并两个列表
    print("\n【步骤6】合并最终报告")
    print("-" * 60)
    merged_jobs = original_jobs + all_ai_jobs
    print(f"BunchTest017: {len(original_jobs)} 条 (relevance level = 1)")
    print(f"AI_Related_Test001: {len(all_ai_jobs)} 条 (relevance level = 2)")
    print(f"总计: {len(merged_jobs)} 条")
    
    # 7. 导出最终报告
    print("\n【步骤7】导出最终报告")
    print("-" * 60)
    
    # 构建DataFrame，确保relevance level在最前面
    relevance_column = [job.get("relevance level", "") for job in merged_jobs]
    
    # 创建DataFrame，先添加relevance level，然后添加其他字段
    df_data = {"relevance level": relevance_column}
    for field in FIELDS:
        df_data[field] = [job.get(field, "") for job in merged_jobs]
    
    df = pd.DataFrame(df_data)
    
    # 导出Excel
    df.to_excel(FINAL_OUTPUT_FILE, index=False)
    print(f"已导出: {FINAL_OUTPUT_FILE}")
    print(f"总职位数: {len(merged_jobs)} 条")
    
    # 8. 重置路径和恢复CACHE_FILE
    reset_paths()
    config.CACHE_FILE = original_cache_file
    scraper_module.CACHE_FILE = original_cache_file
    
    print("\n" + "="*60)
    print("合并和补全完成")
    print("="*60)
    print(f"最终报告: {FINAL_OUTPUT_FILE}")
    print(f"移除重复职位: {removed_count} 条")
    print(f"补全职位: {len(incomplete_jobs) if incomplete_jobs else 0} 条")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"程序出错: {str(e)}")
        import traceback
        print(traceback.format_exc())
        # 确保重置路径和恢复CACHE_FILE
        reset_paths()
        try:
            config.CACHE_FILE = original_cache_file
            scraper_module.CACHE_FILE = original_cache_file
        except:
            pass

