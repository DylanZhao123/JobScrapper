# -*- coding: utf-8 -*-
"""
合并和分类程序
1. 读取新抓取的AI弱相关岗位数据
2. 读取原有的BunchTest017数据
3. 去重合并
4. 添加职位类别
5. 导出最终报告
"""
import pandas as pd
import os
from job_classifier import classify_jobs, get_category_statistics
from config import FIELDS

# 文件路径配置
AI_RELATED_FILE = r"C:\Users\Dylan\JobScrapper\outputs\AI_Related_Test001\report_stage2_detail.xlsx"
ORIGINAL_FILE = r"C:\Users\Dylan\JobScrapper\outputs\BunchTest017\report_stage2_detail.xlsx"
OUTPUT_DIR = r"C:\Users\Dylan\JobScrapper\outputs\AI_Related_Test001"
MERGED_OUTPUT = os.path.join(OUTPUT_DIR, "merged_final_report.xlsx")

def load_excel_data(file_path):
    """加载Excel文件数据"""
    if not os.path.exists(file_path):
        print(f"警告: 文件不存在: {file_path}")
        return []
    
    try:
        df = pd.read_excel(file_path)
        # 转换为字典列表
        jobs = df.to_dict('records')
        print(f"成功加载: {file_path} ({len(jobs)} 条)")
        return jobs
    except Exception as e:
        print(f"加载文件失败 {file_path}: {str(e)}")
        return []

def calculate_completeness(job):
    """计算职位数据的完整度（非空字段数量）"""
    non_empty_count = 0
    for field in FIELDS:
        value = job.get(field, "")
        if value and str(value).strip():
            non_empty_count += 1
    return non_empty_count

def deduplicate_jobs(jobs1, jobs2):
    """
    合并两个职位列表并去重
    如果重复，保留更完整的数据
    
    参数:
        jobs1: 第一个职位列表
        jobs2: 第二个职位列表
    
    返回:
        去重后的职位列表
    """
    # 使用 (职位名称, 公司名称) 作为唯一键
    unique_jobs = {}
    
    # 处理第一个列表
    for job in jobs1:
        job_title = job.get("职位名称", "")
        company_name = job.get("公司名称", "")
        key = (job_title, company_name)
        
        if key[0] and key[1]:
            if key not in unique_jobs:
                unique_jobs[key] = job
            else:
                # 如果已存在，比较完整度，保留更完整的
                existing_completeness = calculate_completeness(unique_jobs[key])
                new_completeness = calculate_completeness(job)
                if new_completeness > existing_completeness:
                    unique_jobs[key] = job
    
    # 处理第二个列表
    for job in jobs2:
        job_title = job.get("职位名称", "")
        company_name = job.get("公司名称", "")
        key = (job_title, company_name)
        
        if key[0] and key[1]:
            if key not in unique_jobs:
                unique_jobs[key] = job
            else:
                # 如果已存在，比较完整度，保留更完整的
                existing_completeness = calculate_completeness(unique_jobs[key])
                new_completeness = calculate_completeness(job)
                if new_completeness > existing_completeness:
                    unique_jobs[key] = job
    
    # 转换为列表
    return list(unique_jobs.values())

def main():
    print("="*60)
    print("合并和分类程序")
    print("="*60)
    
    # 1. 加载数据
    print("\n【步骤1】加载数据")
    print("-" * 60)
    ai_related_jobs = load_excel_data(AI_RELATED_FILE)
    original_jobs = load_excel_data(ORIGINAL_FILE)
    
    if not ai_related_jobs and not original_jobs:
        print("错误: 没有找到任何数据文件")
        return
    
    print(f"AI弱相关岗位: {len(ai_related_jobs)} 条")
    print(f"原有岗位数据: {len(original_jobs)} 条")
    print(f"总计: {len(ai_related_jobs) + len(original_jobs)} 条")
    
    # 2. 去重合并
    print("\n【步骤2】去重合并")
    print("-" * 60)
    merged_jobs = deduplicate_jobs(ai_related_jobs, original_jobs)
    print(f"去重前: {len(ai_related_jobs) + len(original_jobs)} 条")
    print(f"去重后: {len(merged_jobs)} 条")
    print(f"重复数量: {len(ai_related_jobs) + len(original_jobs) - len(merged_jobs)} 条")
    
    # 3. 添加职位类别
    print("\n【步骤3】添加职位类别")
    print("-" * 60)
    classified_jobs = classify_jobs(merged_jobs)
    print(f"已分类: {len(classified_jobs)} 条职位")
    
    # 4. 统计信息
    print("\n【步骤4】类别统计")
    print("-" * 60)
    stats = get_category_statistics(classified_jobs)
    for category, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
        print(f"  {category}: {count} 条")
    
    # 5. 导出最终报告
    print("\n【步骤5】导出最终报告")
    print("-" * 60)
    
    # 构建DataFrame，确保"职位类别"在最前面
    category_column = [job.get("职位类别", "Unknown") for job in classified_jobs]
    
    # 创建DataFrame，先添加职位类别，然后添加其他字段
    df_data = {"职位类别": category_column}
    for field in FIELDS:
        df_data[field] = [job.get(field, "") for job in classified_jobs]
    
    df = pd.DataFrame(df_data)
    
    # 确保输出目录存在
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 导出Excel
    df.to_excel(MERGED_OUTPUT, index=False)
    print(f"已导出: {MERGED_OUTPUT}")
    print(f"总职位数: {len(classified_jobs)} 条")
    
    print("\n" + "="*60)
    print("合并和分类完成")
    print("="*60)
    print(f"最终报告: {MERGED_OUTPUT}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"程序出错: {str(e)}")
        import traceback
        print(traceback.format_exc())

