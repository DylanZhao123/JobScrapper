# -*- coding: utf-8 -*-
"""
Indeed完整爬取测试 - 爬虫模块
测试列表页和详情页的完整抓取，确保所有字段都能正确提取
"""
import requests
import time
import re
import json
import urllib.parse
from bs4 import BeautifulSoup
from test_config import (
    ZENROWS_API_KEY, ZENROWS_BASE_URL, REQUEST_DELAY,
    TEST_CACHE_FILE
)

def zenrows_get(url, retries=3, delay=2, use_js_render=True):
    """
    ZenRows请求函数
    根据测试结果，Indeed需要使用JS渲染+高级代理
    """
    for attempt in range(retries):
        try:
            # 根据测试结果，Indeed需要使用JS渲染+高级代理
            params = {
                'url': url,
                'apikey': ZENROWS_API_KEY
            }
            
            # Indeed需要JS渲染和高级代理
            if use_js_render:
                params['js_render'] = 'true'
                params['premium_proxy'] = 'true'
            
            r = requests.get(ZENROWS_BASE_URL, params=params, timeout=60)
            
            if r.status_code == 200:
                return r.text
            elif r.status_code == 400:
                # 400错误，尝试不使用JS渲染
                if use_js_render:
                    print(f"ZenRows 400错误，尝试不使用JS渲染...")
                    params_simple = {
                        'url': url,
                        'apikey': ZENROWS_API_KEY
                    }
                    r2 = requests.get(ZENROWS_BASE_URL, params=params_simple, timeout=60)
                    if r2.status_code == 200:
                        return r2.text
                    else:
                        print(f"ZenRows 请求失败[{r2.status_code}] 第{attempt+1}次: {url}")
                else:
                    print(f"ZenRows 请求失败[{r.status_code}] 第{attempt+1}次: {url}")
            else:
                print(f"ZenRows 请求失败[{r.status_code}] 第{attempt+1}次: {url}")
                if r.status_code >= 400:
                    print(f"错误响应: {r.text[:200]}")
        except Exception as e:
            print(f"请求异常 第{attempt+1}次: {str(e)}")
        time.sleep(delay * (attempt + 1))
    return None


def load_cache():
    """加载公司规模缓存"""
    try:
        with open(TEST_CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_cache(cache):
    """保存公司规模缓存"""
    with open(TEST_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def fetch_indeed_list(keyword, max_pages=3, list_limit=50):
    """
    抓取Indeed列表页
    返回职位列表（基本信息）
    """
    results = []
    print(f"\n开始抓取关键词: {keyword}")
    
    for page in range(max_pages):
        start = page * 10  # Indeed每页10条
        if len(results) >= list_limit:
            break
        
        # 构建URL
        query_params = {
            'q': keyword,
            'l': 'United States',
            'start': str(start)
        }
        base_url = "https://www.indeed.com/jobs"
        url = f"{base_url}?{urllib.parse.urlencode(query_params)}"
        
        print(f"  抓取第 {page + 1} 页 (start={start})")
        print(f"  URL: {url}")
        
        # 根据测试结果，Indeed需要使用JS渲染+高级代理
        html = zenrows_get(url, use_js_render=True)
        
        if not html:
            print(f"  ✗ 第 {page + 1} 页抓取失败，跳过")
            continue
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # 尝试多种选择器来找到职位卡片
        cards = []
        
        # 方法1: 查找data-jk属性的元素
        cards = soup.find_all('div', {'data-jk': True})
        if not cards:
            # 方法2: 查找class包含job的元素
            cards = soup.find_all('div', class_=re.compile(r'job', re.I))
        if not cards:
            # 方法3: 查找包含职位链接的a标签
            cards = soup.find_all('a', href=re.compile(r'/viewjob'))
        
        print(f"  找到 {len(cards)} 个职位卡片")
        
        if not cards:
            print(f"  ⚠ 未找到职位卡片，可能页面结构变化或需要JS渲染")
            # 保存HTML用于调试
            with open(f"test_indeed_full/debug_page_{page}.html", "w", encoding="utf-8") as f:
                f.write(html)
            print(f"  已保存HTML到 debug_page_{page}.html 用于调试")
            continue
        
        page_jobs = 0
        for card in cards:
            if len(results) >= list_limit:
                break
            
            # 提取职位标题
            title = ''
            title_elem = (
                card.find('h2', class_='jobTitle') or
                card.find('a', class_='jcs-JobTitle') or
                card.find('span', {'id': re.compile(r'jobTitle', re.I)}) or
                card.find('h2') or
                card.find('a', href=re.compile(r'/viewjob'))
            )
            if title_elem:
                title = title_elem.get_text(strip=True)
                # 如果是链接，尝试从title属性获取
                if not title and title_elem.has_attr('title'):
                    title = title_elem['title']
            
            # 提取公司名称
            company = ''
            company_elem = (
                card.find('span', class_='companyName') or
                card.find('a', {'data-testid': 'company-name'}) or
                card.find('span', {'data-testid': 'company-name'}) or
                card.find('span', class_=re.compile(r'company', re.I))
            )
            if company_elem:
                company = company_elem.get_text(strip=True)
            
            # 提取地点
            location = ''
            location_elem = (
                card.find('div', class_='companyLocation') or
                card.find('div', {'data-testid': 'job-location'}) or
                card.find('span', class_='location') or
                card.find('div', class_=re.compile(r'location', re.I))
            )
            if location_elem:
                location = location_elem.get_text(strip=True)
            
            # 提取发布时间
            date_text = ''
            date_elem = (
                card.find('span', class_='date') or
                card.find('span', {'data-testid': 'myJobsStateDate'}) or
                card.find('span', class_=re.compile(r'date', re.I))
            )
            if date_elem:
                date_text = date_elem.get_text(strip=True)
            
            # 提取职位链接
            job_link = ''
            link_elem = (
                card.find('a', {'data-jk': True}) or
                card.find('a', class_='jcs-JobTitle') or
                card.find('a', href=re.compile(r'/viewjob'))
            )
            
            if link_elem:
                if link_elem.has_attr('href'):
                    href = link_elem['href']
                    if href.startswith('/'):
                        job_link = f"https://www.indeed.com{href}"
                    else:
                        job_link = href
                elif link_elem.has_attr('data-jk'):
                    jk = link_elem['data-jk']
                    job_link = f"https://www.indeed.com/viewjob?jk={jk}"
            
            # 提取薪资（列表页可能显示）
            salary_text = ''
            salary_elem = (
                card.find('span', class_='salary-snippet') or
                card.find('div', class_='salary-snippet-container') or
                card.find('span', {'data-testid': 'attribute_snippet_testid'}) or
                card.find('span', class_=re.compile(r'salary', re.I))
            )
            if salary_elem:
                salary_text = salary_elem.get_text(strip=True)
            
            # 只保存有职位名称和链接的记录
            if title and job_link:
                job = {
                    "职位名称": title,
                    "公司名称": company,
                    "专业要求": '',
                    "地点": location,
                    "薪资要求": salary_text,
                    "年薪预估值": '',
                    "工作描述": '',
                    "团队规模/业务线规模": '',
                    "公司规模": '',
                    "职位发布时间": date_text,
                    "职位状态": 'Active',
                    "招聘平台": 'Indeed',
                    "职位链接": job_link
                }
                results.append(job)
                page_jobs += 1
        
        print(f"  ✓ 第 {page + 1} 页提取到 {page_jobs} 条职位")
        time.sleep(REQUEST_DELAY)
    
    print(f"关键词 '{keyword}' 共抓取 {len(results)} 条职位")
    return results[:list_limit]


def parse_salary(salary_text):
    """
    解析薪资文本，返回 (薪资类型, 年薪预估值)
    复用LinkedIn的逻辑
    """
    if not salary_text:
        return ('未知', '')
    
    text_lower = salary_text.lower()
    
    def extract_number(s):
        s = s.replace(',', '').replace('$', '').strip()
        multiplier = 1
        if s.endswith('k') or s.endswith('K'):
            multiplier = 1000
            s = s[:-1]
        elif s.endswith('m') or s.endswith('M'):
            multiplier = 1000000
            s = s[:-1]
        try:
            return float(s) * multiplier
        except:
            return None
    
    numbers = []
    for match in re.finditer(r'\$?\s*(\d{1,3}(?:[,\.]\d{3})*(?:\.\d{2})?)\s*([kKmM]?)\b', salary_text):
        num_str = match.group(1).replace(',', '')
        suffix = match.group(2)
        num = extract_number(num_str + suffix)
        if num is not None and num > 0:
            numbers.append(num)
    
    if not numbers:
        return ('未知', '')
    
    # 判断薪资类型
    is_annual = any(x in text_lower for x in ['year', 'annual', 'per annum', 'yr', '/yr', 'per year'])
    is_monthly = any(x in text_lower for x in ['month', 'mo', '/m', 'per month', 'monthly'])
    is_hourly = any(x in text_lower for x in ['hour', 'hr', '/h', 'per hour', 'hourly', '/hr'])
    
    # 如果没有明确标识，根据数值范围推断
    if not (is_annual or is_monthly or is_hourly):
        avg_num = sum(numbers) / len(numbers)
        if avg_num < 200:
            is_hourly = True
        elif avg_num < 50000:
            is_monthly = True
        else:
            is_annual = True
    
    def round_to_tens(num):
        return round(num / 10) * 10
    
    if is_annual:
        if len(numbers) >= 2:
            annual_estimate = (min(numbers) + max(numbers)) / 2
        else:
            annual_estimate = numbers[0]
        return ('年薪', round_to_tens(annual_estimate))
    elif is_monthly:
        if len(numbers) >= 2:
            monthly_avg = (min(numbers) + max(numbers)) / 2
            annual_estimate = monthly_avg * 12
        else:
            annual_estimate = numbers[0] * 12
        return ('月薪', round_to_tens(annual_estimate))
    elif is_hourly:
        if len(numbers) >= 2:
            hourly_avg = (min(numbers) + max(numbers)) / 2
            annual_estimate = hourly_avg * 40 * 52
        else:
            annual_estimate = numbers[0] * 40 * 52
        return ('时薪', round_to_tens(annual_estimate))
    else:
        return ('未知', '')


def extract_employee_number(text):
    """从文本中提取员工数量"""
    if not text:
        return ''
    
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


def get_company_size_indeed(company_name, company_url, cache):
    """
    从Indeed公司页面获取公司规模
    """
    if not company_name or not company_url:
        return ''
    
    # 检查缓存
    if company_name in cache:
        cached_value = cache[company_name]
        if cached_value:
            if isinstance(cached_value, str) and cached_value.isdigit():
                return cached_value
            if isinstance(cached_value, (int, float)):
                return str(int(cached_value))
            num = extract_employee_number(str(cached_value))
            if num:
                return num
    
    # 访问公司页面（使用JS渲染）
    html = zenrows_get(company_url, use_js_render=True)
    if not html:
        cache[company_name] = ''
        save_cache(cache)
        return ''
    
    soup = BeautifulSoup(html, "html.parser")
    
    # 方法1: 查找包含员工数的文本
    employee_texts = soup.find_all(string=re.compile(r'\d+.*employee', re.I))
    for text_node in employee_texts:
        if text_node.parent:
            text = text_node.parent.get_text(strip=True)
            num = extract_employee_number(text)
            if num:
                cache[company_name] = num
                save_cache(cache)
                return num
    
    # 方法2: 查找公司信息卡片
    info_sections = soup.find_all(['div', 'span'], class_=re.compile(r'company|info|about', re.I))
    for section in info_sections:
        text = section.get_text(strip=True)
        if re.search(r'\d+.*employee', text, re.I):
            num = extract_employee_number(text)
            if num:
                cache[company_name] = num
                save_cache(cache)
                return num
    
    cache[company_name] = ''
    save_cache(cache)
    return ''


def enrich_job_details(job_list):
    """
    丰富职位详情
    提取工作描述、专业要求、薪资、公司规模等
    """
    cache = load_cache()
    print(f"\n开始抓取详情页（共 {len(job_list)} 条）")
    
    for idx, job in enumerate(job_list):
        url = job.get("职位链接")
        if not url:
            if (idx + 1) % 5 == 0 or idx == len(job_list) - 1:
                print(f"详情页进度：{idx + 1}/{len(job_list)}")
            continue
        
        print(f"  处理 {idx + 1}/{len(job_list)}: {job.get('职位名称', 'N/A')[:50]}")
        
        # 根据测试结果，Indeed需要使用JS渲染+高级代理
        html = zenrows_get(url, use_js_render=True)
        
        if not html:
            print(f"    ✗ 无法获取HTML，跳过")
            if (idx + 1) % 5 == 0 or idx == len(job_list) - 1:
                print(f"详情页进度：{idx + 1}/{len(job_list)}")
            continue
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # 提取工作描述 - 改进选择器，尝试多种方法
        description = ''
        
        # Method 1: 标准Indeed选择器
        desc = (
            soup.find('div', {'id': 'jobDescriptionText'}) or
            soup.find('div', class_='jobsearch-jobDescriptionText') or
            soup.find('div', class_='jobsearch-JobComponent-description')
        )
        if desc:
            description = desc.get_text(separator=' ', strip=True)
        
        # Method 2: 如果没找到，尝试查找包含description的div
        if not description:
            desc_divs = soup.find_all('div', class_=re.compile(r'description', re.I))
            for div in desc_divs:
                text = div.get_text(separator=' ', strip=True)
                if len(text) > 200:  # 确保是完整的描述
                    description = text
                    break
        
        # Method 3: 如果还没找到，尝试查找包含job description的section
        if not description:
            sections = soup.find_all(['section', 'div'], class_=re.compile(r'job|description', re.I))
            for section in sections:
                text = section.get_text(separator=' ', strip=True)
                if len(text) > 200 and ('job' in text.lower() or 'responsibilities' in text.lower()):
                    description = text
                    break
        
        job["工作描述"] = description
        
        # 提取专业要求
        requirements_text = ''
        
        if description:
            # 方法1: 查找明确的requirements部分
            req_patterns = [
                r'(?:requirements?|qualifications?|required|must have|minimum requirements?)[\s:]*\n?([^\n]{100,800})',
                r"(?:what you['']?ll need|what we['']?re looking for|you should have)[\s:]*\n?([^\n]{100,800})",
                r'(?:education|experience|skills?)[\s:]*\n?([^\n]{100,600})',
            ]
            
            for pattern in req_patterns:
                matches = re.finditer(pattern, description, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    req_section = match.group(1).strip()
                    req_section = re.sub(r'\s+', ' ', req_section)
                    if len(req_section) > 50:
                        requirements_text = req_section[:500]
                        break
                if requirements_text:
                    break
            
            # 方法2: 提取包含关键技能的句子
            if not requirements_text:
                skill_sentences = []
                sentences = re.split(r'[.!?]\s+', description)
                for sent in sentences:
                    sent_lower = sent.lower()
                    if any(keyword in sent_lower for keyword in [
                        'years of experience', 'degree', 'bachelor', 'master', 'phd',
                        'proficiency', 'experience with', 'knowledge of', 'familiar with',
                        'required', 'must have', 'should have', 'qualifications'
                    ]):
                        if len(sent.strip()) > 30:
                            skill_sentences.append(sent.strip())
                
                if skill_sentences:
                    requirements_text = ' | '.join(skill_sentences[:5])
                    requirements_text = requirements_text[:500]
            
            # 方法3: 如果前一半包含年限要求，使用前一半
            if not requirements_text:
                first_half = description[:len(description)//2]
                if re.search(r'\d+\+?\s*(?:years?|months?|yr)', first_half, re.I):
                    requirements_text = first_half[:500].strip()
        
        job["专业要求"] = requirements_text
        
        # 提取薪资 - 参考LinkedIn的多方法策略
        salary_raw = ''
        
        # Method 1: Find salary elements containing $ symbol (参考LinkedIn)
        salary_tags = soup.find_all(string=re.compile(r'\$'))
        for tag in salary_tags:
            parent = tag.parent
            if parent:
                text = parent.get_text(strip=True)
                if '$' in text and (re.search(r'\d', text)):
                    salary_raw = text
                    break
        
        # Method 2: Find common salary selectors (参考LinkedIn)
        if not salary_raw:
            # Try finding elements with keywords like "salary", "compensation"
            for elem in soup.find_all(['span', 'div', 'li', 'p']):
                text = elem.get_text(strip=True)
                if '$' in text and re.search(r'\d', text):
                    parent_text = ''
                    if elem.parent:
                        parent_text = elem.parent.get_text(strip=True).lower()
                    if any(keyword in parent_text for keyword in ['salary', 'compensation', 'pay', 'wage', 'range']):
                        salary_raw = text
                        break
        
        # Method 3: Find salary information in description (参考LinkedIn)
        if not salary_raw and description:
            salary_matches = re.findall(r'\$[\d,]+(?:[kKmM])?\s*[-–—]\s*\$[\d,]+(?:[kKmM])?', description)
            if not salary_matches:
                salary_matches = re.findall(r'\$[\d,]+(?:[kKmM])?', description)
            if salary_matches:
                # Take first matched salary information
                salary_raw = salary_matches[0]
                idx = description.find(salary_raw)
                if idx >= 0:
                    context = description[max(0, idx-50):idx+len(salary_raw)+50]
                    # If context contains time unit, add to salary text
                    if re.search(r'(year|month|hour|annual|monthly|hourly)', context, re.I):
                        salary_raw = context.strip()
        
        # Method 4: Indeed特定的薪资选择器
        if not salary_raw:
            salary_section = (
                soup.find('div', {'id': 'salaryInfoAndJobType'}) or
                soup.find('div', class_='jobsearch-JobMetadataHeader-item') or
                soup.find('span', class_='jobsearch-JobMetadataHeader-iconLabel') or
                soup.find('div', class_=re.compile(r'salary', re.I))
            )
            if salary_section:
                salary_text = salary_section.get_text(strip=True)
                if '$' in salary_text and re.search(r'\d', salary_text):
                    salary_raw = salary_text
        
        # Method 5: 如果列表页已有薪资，优先使用
        if not salary_raw and job.get("薪资要求"):
            salary_raw = job["薪资要求"]
        
        # 处理薪资文本 - 参考LinkedIn的完整逻辑
        if salary_raw:
            def clean_salary_text(text):
                # Remove JSON format data (if contains @context, @type, etc.) - 参考LinkedIn
                if '@context' in text or '@type' in text or 'schema.org' in text:
                    # Try extracting salary information from JSON
                    try:
                        # Find baseSalary field
                        if 'baseSalary' in text:
                            salary_match = re.search(r'"baseSalary"[^}]*"minValue":(\d+)[^}]*"maxValue":(\d+)', text)
                            if salary_match:
                                min_val = int(salary_match.group(1))
                                max_val = int(salary_match.group(2))
                                return f"${min_val:,} - ${max_val:,}"
                        # Find salary range in value field
                        salary_match = re.search(r'"value"[^}]*"minValue":(\d+)[^}]*"maxValue":(\d+)', text)
                        if salary_match:
                            min_val = int(salary_match.group(1))
                            max_val = int(salary_match.group(2))
                            return f"${min_val:,} - ${max_val:,}"
                    except:
                        pass
                    return ''
                
                # Remove newlines and extra whitespace
                text = re.sub(r'\s+', ' ', text)
                text = text.strip()
                
                # Remove HTML tags
                text = re.sub(r'<[^>]+>', '', text)
                
                # Keep only salary-related text (parts containing $ and numbers)
                # Extract all salary ranges or single salary - 参考LinkedIn
                salary_patterns = [
                    r'\$[\d,]+(?:\.\d{2})?\s*[-–—]\s*\$[\d,]+(?:\.\d{2})?',  # Range
                    r'\$[\d,]+(?:\.\d{2})?',  # Single
                ]
                
                for pattern in salary_patterns:
                    matches = re.findall(pattern, text)
                    if matches:
                        cleaned = matches[0]
                        idx = text.find(cleaned)
                        if idx >= 0:
                            context = text[max(0, idx-30):idx+len(cleaned)+30].lower()
                            if 'year' in context or 'annual' in context:
                                return f"{cleaned} (年薪)"
                            elif 'month' in context or 'monthly' in context:
                                return f"{cleaned} (月薪)"
                            elif 'hour' in context or 'hourly' in context:
                                return f"{cleaned} (时薪)"
                        return cleaned
                
                return text[:200]
            
            cleaned_salary = clean_salary_text(salary_raw)
            
            if cleaned_salary:
                salary_type, annual_estimate = parse_salary(cleaned_salary)
                if '(年薪)' in cleaned_salary or '(月薪)' in cleaned_salary or '(时薪)' in cleaned_salary:
                    job["薪资要求"] = cleaned_salary
                elif salary_type != '未知':
                    job["薪资要求"] = f"{cleaned_salary} ({salary_type})"
                else:
                    job["薪资要求"] = cleaned_salary
                
                if annual_estimate:
                    job["年薪预估值"] = f"${annual_estimate}"
                else:
                    job["年薪预估值"] = ''
            else:
                job["薪资要求"] = ''
                job["年薪预估值"] = ''
        else:
            job["薪资要求"] = ''
            job["年薪预估值"] = ''
        
        # 获取公司规模 - 改进方法
        company_name = job.get("公司名称", "")
        if company_name:
            # 方法1: 尝试从职位详情页直接提取公司信息
            company_info = soup.find_all(['div', 'span', 'a'], class_=re.compile(r'company|employer', re.I))
            for elem in company_info:
                text = elem.get_text(strip=True)
                if re.search(r'\d+.*employee', text, re.I):
                    num = extract_employee_number(text)
                    if num:
                        job["公司规模"] = num
                        break
            
            # 方法2: 如果详情页没有，访问公司页面
            if not job.get("公司规模"):
                # Indeed公司页面URL格式
                company_slug = company_name.lower().replace(' ', '-').replace('.', '').replace(',', '')
                company_url = f"https://www.indeed.com/cmp/{company_slug}"
                size = get_company_size_indeed(company_name, company_url, cache)
                job["公司规模"] = size
        
        if (idx + 1) % 5 == 0 or idx == len(job_list) - 1:
            print(f"详情页进度：{idx + 1}/{len(job_list)}")
        
        time.sleep(REQUEST_DELAY)
    
    print("详情页抓取完成")
    return job_list

