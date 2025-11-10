# -*- coding: utf-8 -*-
import pandas as pd
import requests
import time
import re
import json
from bs4 import BeautifulSoup
import os
import sys

# 设置输出编码
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

def test_method_1(company_name, job_link, cache):
    """方法1: 基础方法 - 只查找dd标签和employees字符串"""
    if not company_name or not job_link:
        return ''
    
    cache_key = f"{company_name}_method1"
    if cache_key in cache:
        cached = cache[cache_key]
        if cached:
            num = extract_employee_number(cached)
            if num:
                return num
        return ''
    
    # 先从职位页获取公司URL
    company_url = extract_company_url_from_job_page(job_link)
    if not company_url:
        cache[cache_key] = ''
        save_test_cache(cache)
        return ''
    
    # 访问公司页面
    full_url = "https://www.linkedin.com" + company_url if company_url.startswith("/company/") else company_url
    html = zenrows_get(full_url)
    if not html:
        cache[cache_key] = ''
        save_test_cache(cache)
        return ''
    
    soup = BeautifulSoup(html, "html.parser")
    
    tag = soup.find("dd", class_="org-about-company-module__company-size-definition-text")
    if not tag:
        tag = soup.find(string=re.compile(r"employees", re.I))
        if tag and tag.parent:
            tag = tag.parent
    
    if tag:
        text = tag.get_text(strip=True) if hasattr(tag, "get_text") else str(tag).strip()
        cache[cache_key] = text
        save_test_cache(cache)
        return extract_employee_number(text)
    
    cache[cache_key] = ''
    save_test_cache(cache)
    return ''

def test_method_2(company_name, job_link, cache):
    """方法2: 扩展搜索 - 查找更多可能的标签和位置"""
    if not company_name or not job_link:
        return ''
    
    cache_key = f"{company_name}_method2"
    if cache_key in cache:
        cached = cache[cache_key]
        if cached:
            num = extract_employee_number(cached)
            if num:
                return num
        return ''
    
    # 先从职位页获取公司URL
    company_url = extract_company_url_from_job_page(job_link)
    if not company_url:
        cache[cache_key] = ''
        save_test_cache(cache)
        return ''
    
    # 访问公司页面
    full_url = "https://www.linkedin.com" + company_url if company_url.startswith("/company/") else company_url
    html = zenrows_get(full_url)
    if not html:
        cache[cache_key] = ''
        save_test_cache(cache)
        return ''
    
    soup = BeautifulSoup(html, "html.parser")
    
    tag = None
    
    # 方法1: 标准dd标签
    tag = soup.find("dd", class_="org-about-company-module__company-size-definition-text")
    
    # 方法2: 查找包含employees的链接
    if not tag:
        for link in soup.find_all('a', href=True):
            link_text = link.get_text(strip=True)
            if re.search(r'\d+.*employee', link_text, re.I):
                tag = link
                break
    
    # 方法3: 查找包含employees的span/div
    if not tag:
        for elem in soup.find_all(['span', 'div', 'p', 'li']):
            text = elem.get_text(strip=True)
            if re.search(r'\d+.*employee', text, re.I):
                tag = elem
                break
    
    # 方法4: 查找包含employees的字符串节点
    if not tag:
        tag = soup.find(string=re.compile(r"employees", re.I))
        if tag and tag.parent:
            tag = tag.parent
    
    if tag:
        text = tag.get_text(strip=True) if hasattr(tag, "get_text") else str(tag).strip()
        cache[cache_key] = text
        save_test_cache(cache)
        return extract_employee_number(text)
    
    cache[cache_key] = ''
    save_test_cache(cache)
    return ''

def test_method_3(company_name, job_link, cache):
    """方法3: JSON-LD优先 + 扩展搜索"""
    if not company_name or not job_link:
        return ''
    
    cache_key = f"{company_name}_method3"
    if cache_key in cache:
        cached = cache[cache_key]
        if cached:
            num = extract_employee_number(cached)
            if num:
                return num
        return ''
    
    # 先从职位页获取公司URL
    company_url = extract_company_url_from_job_page(job_link)
    if not company_url:
        cache[cache_key] = ''
        save_test_cache(cache)
        return ''
    
    # 访问公司页面
    full_url = "https://www.linkedin.com" + company_url if company_url.startswith("/company/") else company_url
    html = zenrows_get(full_url)
    if not html:
        cache[cache_key] = ''
        save_test_cache(cache)
        return ''
    
    soup = BeautifulSoup(html, "html.parser")
    
    # 方法1: 优先从JSON-LD提取
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
    
    # 方法3: 查找链接
    if not tag:
        for link in soup.find_all('a', href=True):
            link_text = link.get_text(strip=True)
            if re.search(r'\d+.*employee', link_text, re.I):
                tag = link
                break
    
    # 方法4: 查找其他元素
    if not tag:
        for elem in soup.find_all(['span', 'div', 'p']):
            text = elem.get_text(strip=True)
            if re.search(r'\d+.*employee', text, re.I):
                tag = elem
                break
    
    # 方法5: 字符串节点
    if not tag:
        tag = soup.find(string=re.compile(r"employees", re.I))
        if tag and tag.parent:
            tag = tag.parent
    
    if tag:
        text = tag.get_text(strip=True) if hasattr(tag, "get_text") else str(tag).strip()
        cache[cache_key] = text
        save_test_cache(cache)
        return extract_employee_number(text)
    
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
        
        # 运行测试
        methods = [
            (test_method_1, "方法1_基础搜索"),
            (test_method_2, "方法2_扩展搜索"),
            (test_method_3, "方法3_JSON优先"),
        ]
        
        all_results = []
        
        for method_func, method_name in methods:
            print(f"\n{'='*60}")
            print(f"测试方法: {method_name}")
            print(f"{'='*60}")
            
            cache = load_test_cache()
            results = []
            success_count = 0
            
            for idx, (company_name, job_link) in enumerate(companies, 1):
                print(f"\n[{idx}/{len(companies)}] {company_name}")
                try:
                    employee_count = method_func(company_name, job_link, cache)
                    if employee_count:
                        print(f"  ✓ 成功: {employee_count} 人")
                        success_count += 1
                    else:
                        print(f"  ✗ 失败: 未获取到人数")
                    results.append({
                        '方法': method_name,
                        '公司名称': company_name,
                        '职位链接': job_link,
                        '员工数量': employee_count,
                        '状态': '成功' if employee_count else '失败'
                    })
                    time.sleep(2)  # 增加延迟避免请求过快
                except Exception as e:
                    print(f"  ✗ 错误: {str(e)}")
                    results.append({
                        '方法': method_name,
                        '公司名称': company_name,
                        '职位链接': job_link,
                        '员工数量': '',
                        '状态': f'错误: {str(e)}'
                    })
            
            all_results.extend(results)
            
            print(f"\n{'='*60}")
            print(f"测试完成: {method_name}")
            print(f"成功率: {success_count}/{len(companies)} ({success_count/len(companies)*100:.1f}%)")
            print(f"{'='*60}\n")
        
        # 保存所有结果
        df_results = pd.DataFrame(all_results)
        output_file = f"{TEST_OUTPUT_DIR}/all_test_results.xlsx"
        df_results.to_excel(output_file, index=False)
        print(f"所有结果已保存: {output_file}")
        
        # 统计每个方法的成功率
        print("\n方法成功率统计:")
        for method_name in [m[1] for m in methods]:
            method_results = df_results[df_results['方法'] == method_name]
            success = len(method_results[method_results['状态'] == '成功'])
            total = len(method_results)
            print(f"  {method_name}: {success}/{total} ({success/total*100:.1f}%)")
        
    except Exception as e:
        print(f"错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

