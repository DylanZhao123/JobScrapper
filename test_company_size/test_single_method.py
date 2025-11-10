# -*- coding: utf-8 -*-
import pandas as pd
import requests
import time
import re
import json
from bs4 import BeautifulSoup
import os
import sys

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# 添加父目录到路径
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)
os.chdir(parent_dir)

from scraper_linkedin import zenrows_get
from config import ZENROWS_API_KEY, ZENROWS_BASE_URL

# 测试配置
TEST_OUTPUT_DIR = "test_company_size"
os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)
TEST_CACHE_FILE = f"{TEST_OUTPUT_DIR}/test_cache.json"

def load_test_cache():
    try:
        with open(TEST_CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_test_cache(cache):
    with open(TEST_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def extract_employee_number(text):
    """从文本中提取纯数字（员工数量）"""
    if not text:
        return ''
    
    # 匹配紧邻"employee"的数字
    employee_pattern = re.search(r'(\d{1,2}(?:,\d{3})+|\d{1,3})\s*employees?', text, re.I)
    if employee_pattern:
        employee_count = employee_pattern.group(1).replace(',', '').replace('.', '')
        try:
            employee_num = int(employee_count)
            if 1 <= employee_num <= 1000000 and not (2020 <= employee_num <= 2030):
                return str(employee_num)
        except ValueError:
            pass
    
    return ''

def extract_company_url_from_job_page(job_link):
    """从职位详情页提取公司URL"""
    print(f"    正在获取职位页: {job_link[:60]}...")
    html = zenrows_get(job_link)
    if not html:
        print(f"    职位页获取失败")
        return ''
    
    soup = BeautifulSoup(html, "html.parser")
    company_tag = soup.find('a', href=re.compile(r'/company/'))
    if company_tag:
        company_url = company_tag['href']
        print(f"    找到公司URL: {company_url}")
        return company_url
    print(f"    未找到公司URL")
    return ''

def test_improved_method(company_name, job_link, cache):
    """改进的方法：先获取公司URL，然后多种方式查找员工数"""
    if not company_name or not job_link:
        return ''
    
    cache_key = f"{company_name}_improved"
    if cache_key in cache:
        cached = cache[cache_key]
        if isinstance(cached, str) and cached.isdigit():
            print(f"    使用缓存: {cached}")
            return cached
        if cached:
            num = extract_employee_number(cached)
            if num:
                print(f"    从缓存提取: {num}")
                return num
    
    # 步骤1: 从职位页获取公司URL
    company_url = extract_company_url_from_job_page(job_link)
    if not company_url:
        cache[cache_key] = ''
        save_test_cache(cache)
        return ''
    
    # 步骤2: 访问公司页面
    full_url = "https://www.linkedin.com" + company_url if company_url.startswith("/company/") else company_url
    print(f"    正在获取公司页: {full_url[:60]}...")
    html = zenrows_get(full_url)
    if not html:
        print(f"    公司页获取失败")
        cache[cache_key] = ''
        save_test_cache(cache)
        return ''
    
    soup = BeautifulSoup(html, "html.parser")
    
    # 方法1: JSON-LD优先
    json_scripts = soup.find_all('script', type='application/ld+json')
    for script in json_scripts:
        try:
            data = json.loads(script.string)
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and item.get('@type') == 'Organization':
                        if 'numberOfEmployees' in item:
                            emp_data = item['numberOfEmployees']
                            if isinstance(emp_data, dict) and 'value' in emp_data:
                                employee_num = int(emp_data['value'])
                                print(f"    从JSON-LD获取: {employee_num}")
                                cache[cache_key] = str(employee_num)
                                save_test_cache(cache)
                                return str(employee_num)
            elif isinstance(data, dict) and data.get('@type') == 'Organization':
                if 'numberOfEmployees' in data:
                    emp_data = data['numberOfEmployees']
                    if isinstance(emp_data, dict) and 'value' in emp_data:
                        employee_num = int(emp_data['value'])
                        print(f"    从JSON-LD获取: {employee_num}")
                        cache[cache_key] = str(employee_num)
                        save_test_cache(cache)
                        return str(employee_num)
        except Exception as e:
            continue
    
    # 方法2: 标准dd标签
    tag = soup.find("dd", class_="org-about-company-module__company-size-definition-text")
    if tag:
        text = tag.get_text(strip=True)
        print(f"    从dd标签获取文本: {text[:50]}")
        num = extract_employee_number(text)
        if num:
            cache[cache_key] = text
            save_test_cache(cache)
            return num
    
    # 方法3: 查找所有包含employees的元素
    for elem in soup.find_all(['span', 'div', 'p', 'li', 'a', 'dt', 'dd']):
        text = elem.get_text(strip=True)
        if re.search(r'\d+.*employee', text, re.I):
            print(f"    从元素获取文本: {text[:50]}")
            num = extract_employee_number(text)
            if num:
                cache[cache_key] = text
                save_test_cache(cache)
                return num
    
    # 方法4: 字符串节点
    tag = soup.find(string=re.compile(r"employees", re.I))
    if tag and tag.parent:
        text = tag.parent.get_text(strip=True)
        print(f"    从字符串节点获取文本: {text[:50]}")
        num = extract_employee_number(text)
        if num:
            cache[cache_key] = text
            save_test_cache(cache)
            return num
    
    print(f"    未找到员工数")
    cache[cache_key] = ''
    save_test_cache(cache)
    return ''

def main():
    # 读取test008的stage2数据
    try:
        df = pd.read_excel('outputs/test008/report_stage2_detail.xlsx')
        print(f"读取到 {len(df)} 条记录\n")
        
        # 提取公司名称和职位链接
        companies = []
        for _, row in df.iterrows():
            company_name = row.get('公司名称', '')
            job_link = row.get('职位链接', '')
            
            if company_name and job_link:
                companies.append((company_name, job_link))
        
        print(f"提取到 {len(companies)} 个公司\n")
        print("开始测试改进的方法...\n")
        
        cache = load_test_cache()
        results = []
        success_count = 0
        
        for idx, (company_name, job_link) in enumerate(companies, 1):
            print(f"\n[{idx}/{len(companies)}] {company_name}")
            try:
                start_time = time.time()
                employee_count = test_improved_method(company_name, job_link, cache)
                elapsed = time.time() - start_time
                
                if employee_count:
                    print(f"  ✓ 成功: {employee_count} 人 (耗时: {elapsed:.1f}秒)")
                    success_count += 1
                else:
                    print(f"  ✗ 失败: 未获取到人数 (耗时: {elapsed:.1f}秒)")
                
                results.append({
                    '公司名称': company_name,
                    '职位链接': job_link,
                    '员工数量': employee_count,
                    '状态': '成功' if employee_count else '失败',
                    '耗时(秒)': f"{elapsed:.1f}"
                })
                
                # 避免请求过快
                if idx < len(companies):
                    time.sleep(2)
                    
            except Exception as e:
                print(f"  ✗ 错误: {str(e)}")
                import traceback
                traceback.print_exc()
                results.append({
                    '公司名称': company_name,
                    '职位链接': job_link,
                    '员工数量': '',
                    '状态': f'错误: {str(e)}',
                    '耗时(秒)': 'N/A'
                })
        
        # 保存结果
        df_results = pd.DataFrame(results)
        output_file = f"{TEST_OUTPUT_DIR}/test_improved_result.xlsx"
        df_results.to_excel(output_file, index=False)
        
        print(f"\n{'='*60}")
        print(f"测试完成")
        print(f"成功率: {success_count}/{len(companies)} ({success_count/len(companies)*100:.1f}%)")
        print(f"结果已保存: {output_file}")
        print(f"{'='*60}\n")
        
    except Exception as e:
        print(f"错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

