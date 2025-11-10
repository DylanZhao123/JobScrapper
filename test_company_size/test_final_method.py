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

def normalize_company_url(company_url):
    """标准化公司URL，将不同国家的LinkedIn URL转换为www.linkedin.com"""
    if not company_url:
        return ''
    
    # 移除查询参数
    if '?' in company_url:
        company_url = company_url.split('?')[0]
    
    # 如果是完整URL，提取路径
    if company_url.startswith('http'):
        match = re.search(r'/company/([^/?]+)', company_url)
        if match:
            return f"/company/{match.group(1)}"
        return company_url
    
    # 如果已经是路径格式，直接返回
    if company_url.startswith('/company/'):
        return company_url
    
    return company_url

def extract_company_url_from_job_page(job_link):
    """从职位详情页提取公司URL"""
    html = zenrows_get(job_link)
    if not html:
        return ''
    
    soup = BeautifulSoup(html, "html.parser")
    company_tag = soup.find('a', href=re.compile(r'/company/'))
    if company_tag:
        company_url = company_tag['href']
        # 标准化URL
        return normalize_company_url(company_url)
    return ''

def get_company_size_improved(company_name, job_link, cache):
    """
    改进的公司规模获取方法
    1. 从职位页获取公司URL（标准化为www.linkedin.com）
    2. 多种方式查找员工数（JSON-LD -> dd标签 -> 元素搜索 -> 字符串节点）
    """
    if not company_name or not job_link:
        return ''
    
    cache_key = f"{company_name}_final"
    if cache_key in cache:
        cached = cache[cache_key]
        if isinstance(cached, str) and cached.isdigit():
            return cached
        if cached:
            num = extract_employee_number(cached)
            if num:
                return num
    
    # 步骤1: 从职位页获取公司URL
    company_url = extract_company_url_from_job_page(job_link)
    if not company_url:
        cache[cache_key] = ''
        save_test_cache(cache)
        return ''
    
    # 步骤2: 访问公司页面（使用标准www.linkedin.com）
    full_url = "https://www.linkedin.com" + company_url if company_url.startswith("/company/") else company_url
    
    html = zenrows_get(full_url)
    if not html:
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
                                cache[cache_key] = str(employee_num)
                                save_test_cache(cache)
                                return str(employee_num)
            elif isinstance(data, dict) and data.get('@type') == 'Organization':
                if 'numberOfEmployees' in data:
                    emp_data = data['numberOfEmployees']
                    if isinstance(emp_data, dict) and 'value' in emp_data:
                        employee_num = int(emp_data['value'])
                        cache[cache_key] = str(employee_num)
                        save_test_cache(cache)
                        return str(employee_num)
        except:
            continue
    
    # 方法2: 标准dd标签
    tag = soup.find("dd", class_="org-about-company-module__company-size-definition-text")
    if tag:
        text = tag.get_text(strip=True)
        num = extract_employee_number(text)
        if num:
            cache[cache_key] = text
            save_test_cache(cache)
            return num
    
    # 方法3: 查找所有包含employees的元素
    for elem in soup.find_all(['span', 'div', 'p', 'li', 'a', 'dt', 'dd']):
        text = elem.get_text(strip=True)
        if re.search(r'\d+.*employee', text, re.I):
            num = extract_employee_number(text)
            if num:
                cache[cache_key] = text
                save_test_cache(cache)
                return num
    
    # 方法4: 字符串节点
    tag = soup.find(string=re.compile(r"employees", re.I))
    if tag and tag.parent:
        text = tag.parent.get_text(strip=True)
        num = extract_employee_number(text)
        if num:
            cache[cache_key] = text
            save_test_cache(cache)
            return num
    
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
        print("开始测试最终优化方法...\n")
        
        cache = load_test_cache()
        results = []
        success_count = 0
        
        for idx, (company_name, job_link) in enumerate(companies, 1):
            print(f"[{idx}/{len(companies)}] {company_name}")
            try:
                employee_count = get_company_size_improved(company_name, job_link, cache)
                
                if employee_count:
                    print(f"  ✓ 成功: {employee_count} 人")
                    success_count += 1
                else:
                    print(f"  ✗ 失败: 未获取到人数")
                
                results.append({
                    '公司名称': company_name,
                    '职位链接': job_link,
                    '员工数量': employee_count,
                    '状态': '成功' if employee_count else '失败'
                })
                
                if idx < len(companies):
                    time.sleep(2)
                    
            except Exception as e:
                print(f"  ✗ 错误: {str(e)}")
                results.append({
                    '公司名称': company_name,
                    '职位链接': job_link,
                    '员工数量': '',
                    '状态': f'错误: {str(e)}'
                })
        
        # 保存结果
        df_results = pd.DataFrame(results)
        output_file = f"{TEST_OUTPUT_DIR}/test_final_result.xlsx"
        df_results.to_excel(output_file, index=False)
        
        print(f"\n{'='*60}")
        print(f"测试完成")
        print(f"成功率: {success_count}/{len(companies)} ({success_count/len(companies)*100:.1f}%)")
        print(f"结果已保存: {output_file}")
        print(f"{'='*60}\n")
        
        # 显示最佳方法总结
        print("最佳抓取逻辑总结:")
        print("1. 从职位详情页提取公司URL（标准化为www.linkedin.com）")
        print("2. 访问公司页面，按优先级查找:")
        print("   - JSON-LD结构化数据（最快最准确）")
        print("   - dd标签（标准位置）")
        print("   - 所有包含'employees'的元素")
        print("   - 字符串节点搜索")
        print("3. 提取纯数字，排除年份（2020-2030）")
        print("4. 使用缓存避免重复请求")
        
    except Exception as e:
        print(f"错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

