# -*- coding: utf-8 -*-
"""
对新增职位获取详情
1. 读取两个列表页数据（AI_Related_Test001 和 BunchTest017）
2. 去重，找出新增职位
3. 清除checkpoint
4. 对新增职位获取详情
5. 保存结果
"""
import pandas as pd
import os
import sys

# 在导入scraper之前，设置独立的缓存文件路径
AI_RELATED_DIR = r"C:\Users\Dylan\JobScrapper\outputs\AI_Related_Test001"
AI_RELATED_CACHE_FILE = os.path.join(AI_RELATED_DIR, "company_cache.json")

# 临时修改config模块的CACHE_FILE（在导入scraper之前）
import config
original_cache_file = config.CACHE_FILE
config.CACHE_FILE = AI_RELATED_CACHE_FILE

# 现在导入scraper（它会使用修改后的CACHE_FILE）
from scraper_linkedin_checkpoint import enrich_job_details_with_checkpoint
import scraper_linkedin_checkpoint as scraper_module

# 确保scraper模块也使用新的CACHE_FILE
scraper_module.CACHE_FILE = AI_RELATED_CACHE_FILE

from checkpoint_manager import (
    set_country_paths, reset_paths,
    save_checkpoint, load_checkpoint
)
from exporter import export_to_excel
from config import DETAIL_LIMIT, FIELDS
import json
import shutil

# 文件路径配置（已在上面定义AI_RELATED_DIR）
ORIGINAL_DIR = r"C:\Users\Dylan\JobScrapper\outputs\BunchTest017"

AI_RELATED_LIST_FILE = os.path.join(AI_RELATED_DIR, "report_stage1_list.xlsx")
ORIGINAL_LIST_FILE = os.path.join(ORIGINAL_DIR, "report_stage1_list.xlsx")

AI_RELATED_DETAIL_OUTPUT = os.path.join(AI_RELATED_DIR, "report_stage2_detail_new.xlsx")

def clear_checkpoint_files(output_dir):
    """清除checkpoint相关文件"""
    checkpoint_files = [
        "checkpoint.json",
        "stage1_raw_data.json",
        "stage1_unique_data.json",
        "stage2_detail_data.json"
    ]
    
    cleared = []
    for filename in checkpoint_files:
        filepath = os.path.join(output_dir, filename)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                cleared.append(filename)
            except Exception as e:
                print(f"警告: 无法删除 {filename}: {str(e)}")
    
    if cleared:
        print(f"已清除checkpoint文件: {', '.join(cleared)}")
    else:
        print("没有找到checkpoint文件")

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

def find_new_jobs(ai_related_jobs, original_jobs):
    """
    找出在AI_Related中但不在Original中的职位
    基于 (职位名称, 公司名称) 去重
    """
    # 构建原始数据的键集合
    original_keys = set()
    for job in original_jobs:
        job_title = job.get("职位名称", "")
        company_name = job.get("公司名称", "")
        if job_title and company_name:
            key = (job_title.strip(), company_name.strip())
            original_keys.add(key)
    
    # 找出新职位
    new_jobs = []
    seen_keys = set()
    
    for job in ai_related_jobs:
        job_title = job.get("职位名称", "")
        company_name = job.get("公司名称", "")
        if job_title and company_name:
            key = (job_title.strip(), company_name.strip())
            
            # 如果不在原始数据中，且在当前批次中未见过，则添加
            if key not in original_keys and key not in seen_keys:
                new_jobs.append(job)
                seen_keys.add(key)
    
    return new_jobs

def main():
    print("="*60)
    print("新增职位详情抓取程序")
    print("="*60)
    
    # 1. 加载两个列表页数据
    print("\n【步骤1】加载列表页数据")
    print("-" * 60)
    ai_related_jobs = load_excel_data(AI_RELATED_LIST_FILE)
    original_jobs = load_excel_data(ORIGINAL_LIST_FILE)
    
    if not ai_related_jobs:
        print("错误: AI_Related_Test001 列表页数据为空")
        return
    
    if not original_jobs:
        print("警告: BunchTest017 列表页数据为空，将处理所有AI_Related职位")
    
    print(f"AI_Related_Test001: {len(ai_related_jobs)} 条")
    print(f"BunchTest017: {len(original_jobs)} 条")
    
    # 2. 找出新增职位
    print("\n【步骤2】查找新增职位")
    print("-" * 60)
    new_jobs = find_new_jobs(ai_related_jobs, original_jobs)
    print(f"新增职位数量: {len(new_jobs)} 条")
    
    if len(new_jobs) == 0:
        print("没有新增职位，程序结束")
        return
    
    # 3. 设置checkpoint路径
    set_country_paths(AI_RELATED_DIR)
    
    # 4. 清除旧的stage2_detail_data.json（重要：避免使用之前main_ai_related.py的处理记录）
    # 但保留checkpoint.json以便断点续传
    stage2_detail_file = os.path.join(AI_RELATED_DIR, "stage2_detail_data.json")
    if os.path.exists(stage2_detail_file):
        try:
            os.remove(stage2_detail_file)
            print(f"\n【步骤3】已清除旧的详情数据文件（避免使用之前的处理记录）")
        except Exception as e:
            print(f"警告: 无法删除 stage2_detail_data.json: {str(e)}")
    
    # 5. 检查是否存在checkpoint
    checkpoint = load_checkpoint()
    start_index = 0
    
    if checkpoint and checkpoint.get('stage') == 'stage2_detail':
        # 从checkpoint恢复
        processed_count = checkpoint.get('processed_count', 0)
        total_count = checkpoint.get('total_count', len(new_jobs))
        print(f"\n【步骤4】发现checkpoint，从断点恢复")
        print("-" * 60)
        print(f"已处理: {processed_count}/{total_count} 条")
        print(f"从第 {processed_count+1} 条继续...")
        start_index = processed_count
    else:
        # 没有checkpoint，清除旧的（如果有）并初始化新的
        print("\n【步骤4】初始化checkpoint")
        print("-" * 60)
        # 只清除checkpoint.json，stage2_detail_data.json已经在上面清除了
        checkpoint_file = os.path.join(AI_RELATED_DIR, "checkpoint.json")
        if os.path.exists(checkpoint_file):
            try:
                os.remove(checkpoint_file)
            except:
                pass
        save_checkpoint(
            stage="stage2_detail",
            processed_count=0,
            total_count=len(new_jobs)
        )
        print("已初始化新的checkpoint")
    
    # 6. 限制详情抓取数量（使用DETAIL_LIMIT）
    detail_jobs = new_jobs[:DETAIL_LIMIT]
    print(f"\n【步骤5】开始抓取详情（共 {len(detail_jobs)} 条，限制: {DETAIL_LIMIT}，从第 {start_index+1} 条开始）")
    print("-" * 60)
    
    # 7. 获取详情（支持从checkpoint恢复）
    enrich_job_details_with_checkpoint(detail_jobs, start_index=start_index)
    
    # 8. 导出结果
    print("\n【步骤6】导出结果")
    print("-" * 60)
    export_to_excel(detail_jobs, AI_RELATED_DETAIL_OUTPUT)
    print(f"已导出详情数据: {AI_RELATED_DETAIL_OUTPUT}")
    print(f"总职位数: {len(detail_jobs)} 条")
    
    # 9. 重置路径和恢复CACHE_FILE
    reset_paths()
    config.CACHE_FILE = original_cache_file
    scraper_module.CACHE_FILE = original_cache_file
    
    print("\n" + "="*60)
    print("新增职位详情抓取完成")
    print("="*60)
    print(f"输出文件: {AI_RELATED_DETAIL_OUTPUT}")

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

