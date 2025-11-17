# -*- coding: utf-8 -*-
"""
Indeed完整爬取测试 - 主程序
测试完整的爬取流程：列表页 -> 去重 -> 详情页 -> 导出
"""
import sys
import os
import pandas as pd
from test_config import (
    TEST_KEYWORDS, TEST_MAX_PAGES, TEST_LIST_LIMIT, TEST_DETAIL_LIMIT,
    TEST_LIST_REPORT, TEST_DETAIL_REPORT, FIELDS
)
from test_indeed_scraper import fetch_indeed_list, enrich_job_details

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def export_to_excel(job_list, path):
    """导出到Excel"""
    if not job_list:
        print("没有数据可导出")
        return
    
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df = pd.DataFrame(job_list, columns=FIELDS)
    df.to_excel(path, index=False)
    print(f"✓ 已导出：{os.path.abspath(path)}")
    print(f"  共 {len(job_list)} 条记录")

def main():
    print("="*60)
    print("Indeed完整爬取测试")
    print("="*60)
    
    # 阶段1: 列表页抓取
    print("\n【阶段1】列表页抓取")
    print("-"*60)
    all_jobs = []
    
    for kw in TEST_KEYWORDS:
        print(f"\n抓取关键词：{kw}")
        jobs = fetch_indeed_list(kw, max_pages=TEST_MAX_PAGES, list_limit=TEST_LIST_LIMIT)
        print(f"关键词「{kw}」抓取 {len(jobs)} 条")
        all_jobs.extend(jobs)
    
    print(f"\n所有关键词共抓取 {len(all_jobs)} 条职位")
    
    # 去重
    print("\n【去重处理】")
    print("-"*60)
    seen = set()
    unique_jobs = []
    for job in all_jobs:
        key = (job["职位名称"], job["公司名称"], job["地点"])
        if key not in seen:
            seen.add(key)
            unique_jobs.append(job)
    
    print(f"去重前: {len(all_jobs)} 条")
    print(f"去重后: {len(unique_jobs)} 条")
    
    # 导出列表页报告
    print("\n【导出列表页报告】")
    print("-"*60)
    export_to_excel(unique_jobs, TEST_LIST_REPORT)
    
    # 阶段2: 详情页抓取
    print("\n【阶段2】详情页抓取")
    print("-"*60)
    detail_jobs = unique_jobs[:TEST_DETAIL_LIMIT]
    print(f"将抓取前 {len(detail_jobs)} 条的详情")
    
    detail_jobs = enrich_job_details(detail_jobs)
    
    # 导出详情页报告
    print("\n【导出详情页报告】")
    print("-"*60)
    export_to_excel(detail_jobs, TEST_DETAIL_REPORT)
    
    # 统计信息
    print("\n【统计信息】")
    print("-"*60)
    print(f"列表页职位数: {len(unique_jobs)}")
    print(f"详情页职位数: {len(detail_jobs)}")
    
    # 检查字段完整性
    print("\n【字段完整性检查】")
    print("-"*60)
    for field in FIELDS:
        filled_count = sum(1 for job in detail_jobs if job.get(field))
        percentage = (filled_count / len(detail_jobs) * 100) if detail_jobs else 0
        print(f"{field}: {filled_count}/{len(detail_jobs)} ({percentage:.1f}%)")
    
    print("\n" + "="*60)
    print("测试完成！")
    print("="*60)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n程序出错：{str(e)}")
        import traceback
        traceback.print_exc()

