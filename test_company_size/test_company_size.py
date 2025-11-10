# -*- coding: utf-8 -*-
import pandas as pd
import requests
import time
import re
import json
from bs4 import BeautifulSoup
import os
import sys

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scraper_linkedin import zenrows_get, load_cache, save_cache
from config import ZENROWS_API_KEY, ZENROWS_BASE_URL

# 测试配置
TEST_OUTPUT_DIR = "test_company_size"
TEST_CACHE_FILE = f"{TEST_OUTPUT_DIR}/test_cache.json"

def load_test_cache():
    try:
        with open(TEST_CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_test_cache(cache):
    os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)
    with open(TEST_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def extract_employee_number(text):
    """从文本中提取纯数字（员工数量）"""
    if not text:
        return ''
    
    # 方法1: 匹配紧邻"employee"的数字
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

def test_method_1(company_name, company_url, cache):
    """方法1: 基础方法 - 只查找dd标签和employees字符串"""
    if not company_name or not company_url:
        return ''
    
    if company_name in cache:
        cached = cache[company_name]
        if cached:
            return extract_employee_number(cached)
        return ''
    
    full_url = "https://www.linkedin.com" + company_url if company_url.startswith("/company/") else company_url
    html = zenrows_get(full_url)
    if not html:
        cache[company_name] = ''
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
        cache[company_name] = text
        save_test_cache(cache)
        return extract_employee_number(text)
    
    cache[company_name] = ''
    save_test_cache(cache)
    return ''

def test_method_2(company_name, company_url, cache):
    """方法2: 扩展搜索 - 查找更多可能的标签和位置"""
    if not company_name or not company_url:
        return ''
    
    if company_name in cache:
        cached = cache[company_name]
        if cached:
            return extract_employee_number(cached)
        return ''
    
    full_url = "https://www.linkedin.com" + company_url if company_url.startswith("/company/") else company_url
    html = zenrows_get(full_url)
    if not html:
        cache[company_name] = ''
        save_test_cache(cache)
        return ''
    
    soup = BeautifulSoup(html, "html.parser")
    
    # 尝试多种方法查找
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
        cache[company_name] = text
        save_test_cache(cache)
        return extract_employee_number(text)
    
    cache[company_name] = ''
    save_test_cache(cache)
    return ''

def test_method_3(company_name, company_url, cache):
    """方法3: JSON-LD优先 + 扩展搜索"""
    if not company_name or not company_url:
        return ''
    
    if company_name in cache:
        cached = cache[company_name]
        if cached:
            return extract_employee_number(cached)
        return ''
    
    full_url = "https://www.linkedin.com" + company_url if company_url.startswith("/company/") else company_url
    html = zenrows_get(full_url)
    if not html:
        cache[company_name] = ''
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
                                cache[company_name] = str(employee_num)
                                save_test_cache(cache)
                                return str(employee_num)
            elif isinstance(data, dict) and data.get('@type') == 'Organization':
                if 'numberOfEmployees' in data:
                    emp_data = data['numberOfEmployees']
                    if isinstance(emp_data, dict) and 'value' in emp_data:
                        employee_num = int(emp_data['value'])
                        cache[company_name] = str(employee_num)
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
        cache[company_name] = text
        save_test_cache(cache)
        return extract_employee_number(text)
    
    cache[company_name] = ''
    save_test_cache(cache)
    return ''

def run_test(method_func, method_name, companies):
    """运行测试方法"""
    print(f"\n{'='*60}")
    print(f"测试方法: {method_name}")
    print(f"{'='*60}")
    
    cache = load_test_cache()
    results = []
    success_count = 0
    
    for idx, (company_name, company_url) in enumerate(companies, 1):
        print(f"\n[{idx}/{len(companies)}] 测试: {company_name}")
        try:
            employee_count = method_func(company_name, company_url, cache)
            if employee_count:
                print(f"  ✓ 成功: {employee_count} 人")
                success_count += 1
            else:
                print(f"  ✗ 失败: 未获取到人数")
            results.append({
                '公司名称': company_name,
                '公司URL': company_url,
                '员工数量': employee_count,
                '状态': '成功' if employee_count else '失败'
            })
            time.sleep(1)  # 避免请求过快
        except Exception as e:
            print(f"  ✗ 错误: {str(e)}")
            results.append({
                '公司名称': company_name,
                '公司URL': company_url,
                '员工数量': '',
                '状态': f'错误: {str(e)}'
            })
    
    # 保存结果
    df = pd.DataFrame(results)
    output_file = f"{TEST_OUTPUT_DIR}/test_result_{method_name.replace(' ', '_')}.xlsx"
    df.to_excel(output_file, index=False)
    
    print(f"\n{'='*60}")
    print(f"测试完成: {method_name}")
    print(f"成功率: {success_count}/{len(companies)} ({success_count/len(companies)*100:.1f}%)")
    print(f"结果已保存: {output_file}")
    print(f"{'='*60}\n")
    
    return success_count, len(companies)

def main():
    # 读取test008的stage2数据
    try:
        df = pd.read_excel('outputs/test008/report_stage2_detail.xlsx')
        print(f"读取到 {len(df)} 条记录")
        
        # 提取公司名称和URL
        companies = []
        for _, row in df.iterrows():
            company_name = row.get('公司名称', '')
            company_url = ''  # 需要从职位链接中提取公司URL
            
            # 尝试从职位链接中提取公司信息，或使用公司名称
            job_link = row.get('职位链接', '')
            if job_link and '/company/' in job_link:
                # 从职位链接中提取公司URL
                match = re.search(r'/company/([^/]+)', job_link)
                if match:
                    company_url = f"/company/{match.group(1)}"
            
            if company_name:
                companies.append((company_name, company_url))
        
        print(f"提取到 {len(companies)} 个公司")
        
        # 显示公司列表
        print("\n公司列表:")
        for i, (name, url) in enumerate(companies, 1):
            print(f"  {i}. {name} {url}")
        
        # 运行测试
        methods = [
            (test_method_1, "方法1_基础搜索"),
            (test_method_2, "方法2_扩展搜索"),
            (test_method_3, "方法3_JSON优先"),
        ]
        
        best_method = None
        best_score = 0
        
        for method_func, method_name in methods:
            success, total = run_test(method_func, method_name, companies)
            score = success / total if total > 0 else 0
            if score > best_score:
                best_score = score
                best_method = method_name
        
        print(f"\n最佳方法: {best_method} (成功率: {best_score*100:.1f}%)")
        
    except Exception as e:
        print(f"错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

