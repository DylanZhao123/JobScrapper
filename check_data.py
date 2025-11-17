# -*- coding: utf-8 -*-
"""检查抓取数据"""
import json
import os
from config import OUTPUT_DIR

raw_file = f"{OUTPUT_DIR}/stage1_raw_data.json"
unique_file = f"{OUTPUT_DIR}/stage1_unique_data.json"
checkpoint_file = f"{OUTPUT_DIR}/checkpoint.json"

print("="*60)
print("数据检查")
print("="*60)

if os.path.exists(raw_file):
    with open(raw_file, "r", encoding="utf-8") as f:
        raw_data = json.load(f)
    print(f"原始数据: {len(raw_data)} 条")
    
    # 统计每个关键词的数量
    keywords_count = {}
    for job in raw_data:
        # 无法直接知道是哪个关键词，但可以看总数
        pass
else:
    print("原始数据文件不存在")
    raw_data = []

if os.path.exists(unique_file):
    with open(unique_file, "r", encoding="utf-8") as f:
        unique_data = json.load(f)
    print(f"去重后数据: {len(unique_data)} 条")
else:
    print("去重数据文件不存在")
    unique_data = None

if os.path.exists(checkpoint_file):
    with open(checkpoint_file, "r", encoding="utf-8") as f:
        checkpoint = json.load(f)
    print(f"\nCheckpoint信息:")
    print(f"  阶段: {checkpoint.get('stage')}")
    print(f"  当前关键词索引: {checkpoint.get('current_keyword_index', 'N/A')}")
    print(f"  当前页: {checkpoint.get('current_page', 'N/A')}")
    print(f"  总职位数: {checkpoint.get('total_jobs_count', 'N/A')}")

print("\n" + "="*60)
print("分析:")
print("="*60)

if raw_data:
    # 检查是否有职位链接
    with_link = sum(1 for job in raw_data if job.get("职位链接"))
    print(f"有链接的职位: {with_link}/{len(raw_data)}")
    
    # 检查是否有重复
    seen = set()
    duplicates = 0
    for job in raw_data:
        key = (job.get("职位名称"), job.get("公司名称"), job.get("地点"))
        if key in seen:
            duplicates += 1
        seen.add(key)
    print(f"重复职位: {duplicates} 条")

