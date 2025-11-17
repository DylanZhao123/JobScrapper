# -*- coding: utf-8 -*-
"""
诊断抓取问题
分析为什么只抓取了54条职位
"""
import json
import os
from config import OUTPUT_DIR, KEYWORDS, MAX_PAGES, LIST_LIMIT

print("="*70)
print("抓取诊断分析")
print("="*70)

# 检查数据文件
raw_file = f"{OUTPUT_DIR}/stage1_raw_data.json"
unique_file = f"{OUTPUT_DIR}/stage1_unique_data.json"
checkpoint_file = f"{OUTPUT_DIR}/checkpoint.json"

print("\n1. 数据统计:")
print("-" * 70)

if os.path.exists(raw_file):
    with open(raw_file, "r", encoding="utf-8") as f:
        raw_data = json.load(f)
    print(f"   原始数据: {len(raw_data)} 条")
else:
    print("   原始数据文件不存在")
    raw_data = []

if os.path.exists(unique_file):
    with open(unique_file, "r", encoding="utf-8") as f:
        unique_data = json.load(f)
    print(f"   去重后数据: {len(unique_data)} 条")
else:
    print("   去重数据文件不存在")
    unique_data = None

print("\n2. 配置检查:")
print("-" * 70)
print(f"   关键词数量: {len(KEYWORDS)}")
print(f"   关键词列表: {KEYWORDS}")
print(f"   最大页数: {MAX_PAGES} (每页25条，理论最多 {MAX_PAGES * 25 * len(KEYWORDS)} 条)")
print(f"   列表限制: {LIST_LIMIT} 条")
print(f"   实际抓取: {len(raw_data) if raw_data else 0} 条")

print("\n3. 可能的原因分析:")
print("-" * 70)

if raw_data:
    # 检查是否有职位链接
    with_link = sum(1 for job in raw_data if job.get("职位链接"))
    print(f"   ✓ 有链接的职位: {with_link}/{len(raw_data)}")
    
    # 检查空数据
    empty_title = sum(1 for job in raw_data if not job.get("职位名称"))
    if empty_title > 0:
        print(f"   ⚠ 职位名称为空的: {empty_title} 条")
    
    # 检查重复
    seen = set()
    duplicates = 0
    for job in raw_data:
        key = (job.get("职位名称"), job.get("公司名称"), job.get("地点"))
        if key in seen:
            duplicates += 1
        seen.add(key)
    if duplicates > 0:
        print(f"   ⚠ 重复职位: {duplicates} 条")

if os.path.exists(checkpoint_file):
    with open(checkpoint_file, "r", encoding="utf-8") as f:
        checkpoint = json.load(f)
    print("\n4. Checkpoint信息:")
    print("-" * 70)
    print(f"   阶段: {checkpoint.get('stage')}")
    print(f"   当前关键词索引: {checkpoint.get('current_keyword_index', 'N/A')} (共{len(KEYWORDS)}个)")
    print(f"   当前页: {checkpoint.get('current_page', 'N/A')} (共{MAX_PAGES}页)")
    print(f"   总职位数: {checkpoint.get('total_jobs_count', 'N/A')}")
    completed = checkpoint.get('completed_keywords', [])
    if completed:
        print(f"   已完成关键词: {completed}")

print("\n5. 可能的原因:")
print("-" * 70)

if raw_data and len(raw_data) < 100:
    print("   ⚠ LinkedIn可能对未登录用户或通过代理访问有结果限制")
    print("   ⚠ 某些关键词可能搜索结果较少")
    print("   ⚠ 某些页面可能抓取失败或返回空结果")
    print("   ⚠ LinkedIn可能对某些搜索只返回前几页结果")
    
    # 计算理论值
    expected_per_keyword = len(raw_data) / len(KEYWORDS) if KEYWORDS else 0
    print(f"\n   平均每个关键词: {expected_per_keyword:.1f} 条")
    print(f"   如果每页25条，相当于每个关键词约 {expected_per_keyword/25:.1f} 页")

print("\n6. 建议:")
print("-" * 70)
print("   1. 检查程序运行日志，看是否有页面抓取失败的提示")
print("   2. 检查每页实际提取到的职位数量（应该显示在日志中）")
print("   3. LinkedIn对未登录用户通常限制在1000条左右，但可能更少")
print("   4. 如果某些关键词结果很少，这是正常的（LinkedIn的搜索结果限制）")
print("   5. 可以尝试:")
print("      - 增加更多关键词")
print("      - 使用更具体的地点（如具体城市而非整个国家）")
print("      - 检查ZenRows API是否有请求限制")

print("\n" + "="*70)

