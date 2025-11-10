# -*- coding: utf-8 -*-
import pandas as pd
import re
import os
import sys

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# 读取test008数据
df = pd.read_excel('outputs/test008/report_stage2_detail.xlsx')

print("公司信息检查:\n")
for idx, row in df.iterrows():
    company_name = row.get('公司名称', '')
    job_link = row.get('职位链接', '')
    
    # 提取公司URL
    company_url = ''
    if job_link:
        # 尝试多种方式提取
        match1 = re.search(r'/company/([^/?]+)', job_link)
        match2 = re.search(r'company/([^/?]+)', job_link)
        if match1:
            company_url = f"/company/{match1.group(1)}"
        elif match2:
            company_url = f"/company/{match2.group(1)}"
    
    print(f"{idx+1}. {company_name}")
    print(f"   职位链接: {job_link[:80] if job_link else 'N/A'}...")
    print(f"   提取的公司URL: {company_url}")
    print()

