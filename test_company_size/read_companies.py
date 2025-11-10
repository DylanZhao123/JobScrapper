# -*- coding: utf-8 -*-
import pandas as pd
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

# 读取test008的stage2数据
df = pd.read_excel('../outputs/test008/report_stage2_detail.xlsx')

print(f"总记录数: {len(df)}")
print("\n公司列表:")
companies_data = []
for idx, row in df.iterrows():
    company_name = row.get('公司名称', '')
    job_link = row.get('职位链接', '')
    current_size = row.get('公司规模', '')
    
    # 从职位链接中提取公司URL
    company_url = ''
    if job_link and '/company/' in job_link:
        match = re.search(r'/company/([^/?]+)', job_link)
        if match:
            company_url = f"/company/{match.group(1)}"
    
    companies_data.append({
        '公司名称': company_name,
        '公司URL': company_url,
        '职位链接': job_link,
        '当前公司规模': current_size
    })
    print(f"  {idx+1}. {company_name} - {company_url} - 当前: {current_size}")

# 保存公司列表
df_companies = pd.DataFrame(companies_data)
df_companies.to_excel('companies_list.xlsx', index=False)
print(f"\n已保存公司列表到: companies_list.xlsx")

