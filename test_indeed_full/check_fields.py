# -*- coding: utf-8 -*-
"""检查字段完整性"""
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

file_path = "test_indeed_full/outputs/test_stage2_detail.xlsx"
if not os.path.exists(file_path):
    file_path = "test_indeed_full/test_indeed_full/outputs/test_stage2_detail.xlsx"

if os.path.exists(file_path):
    df = pd.read_excel(file_path)
    print(f"总记录数: {len(df)}")
    print("\n字段完整性:")
    print("-" * 60)
    for col in df.columns:
        filled = df[col].notna().sum() & (df[col].astype(str).str.strip() != '').sum()
        pct = (filled / len(df) * 100) if len(df) > 0 else 0
        print(f"{col:20s}: {filled:2d}/{len(df):2d} ({pct:5.1f}%)")
else:
    print(f"文件不存在: {file_path}")

