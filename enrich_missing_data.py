# -*- coding: utf-8 -*-
"""
补全final_merged_report.xlsx中缺失的详细数据
针对第4581-6350行进行补全
"""
import pandas as pd
import os
import sys

# 设置输出编码
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

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

# 文件路径配置
FINAL_OUTPUT_FILE = os.path.join(FINAL_OUTPUT_DIR, "final_merged_report.xlsx")
FINAL_OUTPUT_FILE_BACKUP = os.path.join(FINAL_OUTPUT_DIR, "final_merged_report_backup.xlsx")

def safe_get_str(job, key, default=""):
    """安全获取字符串值，处理NaN情况"""
    value = job.get(key, default)
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return default
    return str(value).strip()

def check_job_completeness(job):
    """检查职位数据是否完整（是否有工作描述）"""
    description = safe_get_str(job, "工作描述")
    has_description = bool(description)
    return has_description

def main():
    print("="*60)
    print("补全final_merged_report.xlsx中缺失的详细数据")
    print("="*60)
    
    # 确保输出目录存在
    os.makedirs(FINAL_OUTPUT_DIR, exist_ok=True)
    
    # 1. 加载Excel文件
    print("\n【步骤1】加载Excel文件")
    print("-" * 60)
    if not os.path.exists(FINAL_OUTPUT_FILE):
        print(f"错误: 文件不存在: {FINAL_OUTPUT_FILE}")
        return
    
    try:
        df = pd.read_excel(FINAL_OUTPUT_FILE)
        # 将NaN值转换为空字符串，确保所有字段都存在
        df = df.fillna('')
        all_jobs = df.to_dict('records')
        print(f"成功加载: {FINAL_OUTPUT_FILE} ({len(all_jobs)} 条)")
        print(f"列数: {len(df.columns)}")
    except Exception as e:
        print(f"加载文件失败: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return
    
    # 2. 检查第4581-6350行的数据完整性
    print("\n【步骤2】检查第4581-6350行的数据完整性")
    print("-" * 60)
    
    # 注意：Excel行号从1开始，但pandas索引从0开始
    # 第4581行对应索引4580，第6350行对应索引6349
    start_idx = 4580  # 第4581行（索引从0开始）
    end_idx = 6349    # 第6350行（索引从0开始）
    
    if start_idx >= len(all_jobs):
        print(f"错误: 起始索引 {start_idx+1} 超出范围（总行数: {len(all_jobs)}）")
        return
    
    if end_idx >= len(all_jobs):
        print(f"警告: 结束索引 {end_idx+1} 超出范围，调整为最后一行 {len(all_jobs)}")
        end_idx = len(all_jobs) - 1
    
    target_jobs = all_jobs[start_idx:end_idx+1]
    print(f"检查范围: 第 {start_idx+1} 行到第 {end_idx+1} 行（共 {len(target_jobs)} 条）")
    
    # 检查哪些职位需要补全
    incomplete_jobs = []
    complete_jobs = []
    
    for idx, job in enumerate(target_jobs):
        if check_job_completeness(job):
            complete_jobs.append((start_idx + idx, job))
        else:
            incomplete_jobs.append((start_idx + idx, job))
    
    print(f"完整职位: {len(complete_jobs)} 条")
    print(f"需要补全: {len(incomplete_jobs)} 条")
    
    if len(incomplete_jobs) == 0:
        print("所有职位都已完整，无需补全")
        return
    
    # 3. 备份原文件
    print("\n【步骤3】备份原文件")
    print("-" * 60)
    try:
        import shutil
        shutil.copy2(FINAL_OUTPUT_FILE, FINAL_OUTPUT_FILE_BACKUP)
        print(f"已备份到: {FINAL_OUTPUT_FILE_BACKUP}")
    except Exception as e:
        print(f"警告: 备份失败: {str(e)}")
    
    # 4. 补全不完整的职位
    print(f"\n【步骤4】补全职位详情（共 {len(incomplete_jobs)} 条）")
    print("-" * 60)
    
    # 设置checkpoint路径
    set_country_paths(FINAL_OUTPUT_DIR)
    
    # 清除旧的stage2_detail_data.json和checkpoint（避免使用之前的处理记录）
    stage2_detail_file = os.path.join(FINAL_OUTPUT_DIR, "stage2_detail_data.json")
    checkpoint_file = os.path.join(FINAL_OUTPUT_DIR, "checkpoint.json")
    
    if os.path.exists(stage2_detail_file):
        try:
            os.remove(stage2_detail_file)
            print("已清除旧的详情数据文件")
        except Exception as e:
            print(f"警告: 无法删除 stage2_detail_data.json: {str(e)}")
    
    if os.path.exists(checkpoint_file):
        try:
            os.remove(checkpoint_file)
            print("已清除旧的checkpoint文件")
        except Exception as e:
            print(f"警告: 无法删除 checkpoint.json: {str(e)}")
    
    # 初始化新的checkpoint
    save_checkpoint(
        stage="stage2_detail",
        processed_count=0,
        total_count=len(incomplete_jobs)
    )
    print("已初始化新的checkpoint")
    start_index = 0
    
    # 提取需要补全的职位列表（只取职位对象，不包含索引）
    jobs_to_enrich = [job for _, job in incomplete_jobs]
    
    # 限制补全数量
    jobs_to_enrich = jobs_to_enrich[:DETAIL_LIMIT]
    print(f"开始补全详情（共 {len(jobs_to_enrich)} 条，限制: {DETAIL_LIMIT}）")
    
    # 补全详情
    enrich_job_details_with_checkpoint(jobs_to_enrich, start_index=start_index)
    
    # 5. 更新原数据中的职位信息
    print("\n【步骤5】更新原数据中的职位信息")
    print("-" * 60)
    
    # 创建已补全职位的URL映射
    enriched_url_map = {}
    for job in jobs_to_enrich:
        job_url = job.get("职位链接", "")
        if job_url:
            enriched_url_map[job_url] = job
    
    # 更新all_jobs中对应的职位
    # 需要保留所有原有字段（特别是relevance level），只更新缺失的字段
    updated_count = 0
    for orig_idx, orig_job in incomplete_jobs:
        orig_url = orig_job.get("职位链接", "")
        if orig_url and orig_url in enriched_url_map:
            # 获取补全后的job对象
            enriched_job = enriched_url_map[orig_url]
            
            # 保留所有原有字段，只更新缺失或需要补全的字段
            # 需要补全的字段：工作描述、专业要求、薪资要求、年薪预估值、公司规模、团队规模/业务线规模
            fields_to_update = ["工作描述", "专业要求", "薪资要求", "年薪预估值", "公司规模", "团队规模/业务线规模"]
            
            for field in fields_to_update:
                enriched_value = enriched_job.get(field, "")
                if enriched_value and str(enriched_value).strip() and str(enriched_value).strip() != "nan":
                    orig_job[field] = enriched_value
            
            # 更新all_jobs
            all_jobs[orig_idx] = orig_job
            updated_count += 1
    
    print(f"已更新 {updated_count} 条职位信息")
    
    # 6. 导出更新后的Excel文件
    print("\n【步骤6】导出更新后的Excel文件")
    print("-" * 60)
    
    # 构建DataFrame，保持原有列顺序
    # 先获取所有列名（包括relevance level）
    all_columns = list(df.columns)
    
    # 创建DataFrame
    df_updated = pd.DataFrame(all_jobs)
    
    # 确保列顺序与原来一致
    df_updated = df_updated[all_columns]
    
    # 导出Excel
    df_updated.to_excel(FINAL_OUTPUT_FILE, index=False)
    print(f"已导出: {FINAL_OUTPUT_FILE}")
    print(f"总职位数: {len(all_jobs)} 条")
    print(f"补全职位数: {updated_count} 条")
    
    # 7. 重置路径和恢复CACHE_FILE
    reset_paths()
    config.CACHE_FILE = original_cache_file
    scraper_module.CACHE_FILE = original_cache_file
    
    print("\n" + "="*60)
    print("补全完成")
    print("="*60)
    print(f"原文件备份: {FINAL_OUTPUT_FILE_BACKUP}")
    print(f"更新后文件: {FINAL_OUTPUT_FILE}")
    print(f"补全职位数: {updated_count} 条")

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

