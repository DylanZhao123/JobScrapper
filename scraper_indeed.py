import requests
import time
import re
import json
import urllib.parse
from bs4 import BeautifulSoup
from config import (
    LOCATION, MAX_PAGES, REQUEST_DELAY, ZENROWS_API_KEY, ZENROWS_BASE_URL,
    LIST_LIMIT, DETAIL_LIMIT, CACHE_FILE, ERROR_LOG
)

# Basic utilities
def zenrows_get(url, retries=3, delay=2):
    """ZenRows request with retry mechanism"""
    for attempt in range(retries):
        try:
            # For Indeed, may need to enable JS rendering
            params = {
                'url': url,
                'apikey': ZENROWS_API_KEY,
                'js_render': 'true',  # Indeed may need JS rendering
                'premium_proxy': 'true',  # Use premium proxy
            }
            r = requests.get(ZENROWS_BASE_URL, params=params, timeout=30)
            if r.status_code == 200:
                return r.text
            elif r.status_code == 400:
                # 400 error, try without extra parameters
                print(f"ZenRows 400错误，尝试简化参数...")
                params_simple = {'url': url, 'apikey': ZENROWS_API_KEY}
                r2 = requests.get(ZENROWS_BASE_URL, params=params_simple, timeout=30)
                if r2.status_code == 200:
                    return r2.text
                else:
                    print(f"ZenRows 请求失败[{r2.status_code}] 第{attempt+1}次: {url}")
                    print(f"错误响应: {r2.text[:200]}")
            else:
                print(f"ZenRows 请求失败[{r.status_code}] 第{attempt+1}次: {url}")
                if r.status_code >= 400:
                    print(f"错误响应: {r.text[:200]}")
        except Exception as e:
            print(f"请求异常 第{attempt+1}次: {str(e)}")
        time.sleep(delay * (attempt + 1))
    return None


def load_cache():
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


# Scrape Indeed job listings
def fetch_indeed_list(keyword):
    results = []
    for page in range(MAX_PAGES):
        start = page * 10  # Indeed usually has 10 jobs per page
        if len(results) >= LIST_LIMIT:
            break
        
        # Indeed search URL format - use urllib.parse for proper encoding
        query_params = {
            'q': keyword,
            'l': LOCATION,
            'start': str(start)
        }
        # Build URL, ensure proper encoding
        base_url = "https://www.indeed.com/jobs"
        url = f"{base_url}?{urllib.parse.urlencode(query_params)}"
        
        print(f"抓取列表页：{keyword} 第 {page + 1} 页")
        print(f"URL: {url}")
        html = zenrows_get(url)
        if not html:
            continue
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Indeed job card selectors (may need adjustment due to page structure changes)
        # Try multiple possible selectors
        cards = soup.find_all('div', class_='job_seen_beacon') or \
                soup.find_all('div', {'data-jk': True}) or \
                soup.find_all('a', {'data-jk': True})
        
        for card in cards:
            if len(results) >= LIST_LIMIT:
                break
            
            # Extract job title
            title_elem = card.find('h2', class_='jobTitle') or \
                        card.find('a', class_='jcs-JobTitle') or \
                        card.find('span', {'id': re.compile(r'jobTitle')})
            title = title_elem.get_text(strip=True) if title_elem else ''
            
            # Extract company name
            company_elem = card.find('span', class_='companyName') or \
                          card.find('a', {'data-testid': 'company-name'}) or \
                          card.find('span', {'data-testid': 'company-name'})
            company = company_elem.get_text(strip=True) if company_elem else ''
            
            # Extract location
            location_elem = card.find('div', class_='companyLocation') or \
                           card.find('div', {'data-testid': 'job-location'}) or \
                           card.find('span', class_='location')
            location = location_elem.get_text(strip=True) if location_elem else ''
            
            # Extract posting date
            date_elem = card.find('span', class_='date') or \
                       card.find('span', {'data-testid': 'myJobsStateDate'})
            date_text = date_elem.get_text(strip=True) if date_elem else ''
            
            # Extract job link
            link_elem = card.find('a', {'data-jk': True}) or \
                       card.find('a', class_='jcs-JobTitle') or \
                       card.find('a', href=re.compile(r'/viewjob'))
            
            job_link = ''
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
            
            # Extract salary (may be shown on listing page)
            salary_elem = card.find('span', class_='salary-snippet') or \
                         card.find('div', class_='salary-snippet-container') or \
                         card.find('span', {'data-testid': 'attribute_snippet_testid'})
            salary_text = salary_elem.get_text(strip=True) if salary_elem else ''
            
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
        
        time.sleep(REQUEST_DELAY)
    return results[:LIST_LIMIT]


# Salary parsing and estimation (reuse LinkedIn logic)
def parse_salary(salary_text):
    """
    解析薪资文本，返回 (薪资类型, 年薪预估值)
    薪资类型: '年薪', '月薪', '时薪', '未知'
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
    
    # Determine salary type
    is_annual = any(x in text_lower for x in ['year', 'annual', 'per annum', 'yr', '/yr', 'per year'])
    is_monthly = any(x in text_lower for x in ['month', 'mo', '/m', 'per month', 'monthly'])
    is_hourly = any(x in text_lower for x in ['hour', 'hr', '/h', 'per hour', 'hourly', '/hr'])
    
    # If no explicit identifier, infer from value range
    if not (is_annual or is_monthly or is_hourly):
        avg_num = sum(numbers) / len(numbers)
        if avg_num < 200:
            is_hourly = True
        elif avg_num < 50000:
            is_monthly = True
        else:
            is_annual = True
    
    # Calculate annual salary estimate (round to tens)
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


# Company size scraping (reuse LinkedIn logic, but adapt for Indeed company pages)
def extract_employee_number(text):
    """Extract pure number (employee count) from text"""
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
    从Indeed公司页面获取公司规模（员工数量）
    """
    if not company_name or not company_url:
        return ''
    
    # Check cache
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
    
    # Access Indeed company page
    html = zenrows_get(company_url)
    if not html:
        cache[company_name] = ''
        save_cache(cache)
        return ''
    
    soup = BeautifulSoup(html, "html.parser")
    
    # Employee count on Indeed company pages may be in multiple locations
    # Method 1: Find text containing employee count
    employee_texts = soup.find_all(string=re.compile(r'\d+.*employee', re.I))
    for text_node in employee_texts:
        if text_node.parent:
            text = text_node.parent.get_text(strip=True)
            num = extract_employee_number(text)
            if num:
                cache[company_name] = num
                save_cache(cache)
                return num
    
    # Method 2: Find company info card
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
    """丰富职位详情（工作描述、专业要求、薪资、公司规模等）"""
    cache = load_cache()
    for idx, job in enumerate(job_list):
        url = job.get("职位链接")
        if not url:
            if (idx + 1) % 5 == 0 or idx == len(job_list) - 1:
                print(f"详情页进度：{idx + 1}/{len(job_list)}")
            continue

        html = zenrows_get(url)
        if not html:
            if (idx + 1) % 5 == 0 or idx == len(job_list) - 1:
                print(f"详情页进度：{idx + 1}/{len(job_list)}")
            continue
        
        soup = BeautifulSoup(html, 'html.parser')

        # Job description
        desc = soup.find('div', {'id': 'jobDescriptionText'}) or \
               soup.find('div', class_='jobsearch-jobDescriptionText') or \
               soup.find('div', class_='jobsearch-JobComponent-description')
        description = desc.get_text(separator=' ', strip=True) if desc else ''
        job["工作描述"] = description

        # Professional requirements - reuse LinkedIn extraction logic
        requirements_text = ''
        
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
        
        if not requirements_text and description:
            first_half = description[:len(description)//2]
            if re.search(r'\d+\+?\s*(?:years?|months?|yr)', first_half, re.I):
                requirements_text = first_half[:500].strip()
        
        job["专业要求"] = requirements_text

        # Salary logic
        salary_raw = ''
        
        # Method 1: Find salary section
        salary_section = soup.find('div', {'id': 'salaryInfoAndJobType'}) or \
                        soup.find('div', class_='jobsearch-JobMetadataHeader-item') or \
                        soup.find('span', class_='jobsearch-JobMetadataHeader-iconLabel')
        if salary_section:
            salary_text = salary_section.get_text(strip=True)
            if '$' in salary_text and re.search(r'\d', salary_text):
                salary_raw = salary_text
        
        # Method 2: Find salary information in description
        if not salary_raw and description:
            salary_matches = re.findall(r'\$[\d,]+(?:[kKmM])?\s*[-–—]\s*\$[\d,]+(?:[kKmM])?', description)
            if not salary_matches:
                salary_matches = re.findall(r'\$[\d,]+(?:[kKmM])?', description)
            if salary_matches:
                salary_raw = salary_matches[0]
                idx = description.find(salary_raw)
                if idx >= 0:
                    context = description[max(0, idx-50):idx+len(salary_raw)+50]
                    if re.search(r'(year|month|hour|annual|monthly|hourly)', context, re.I):
                        salary_raw = context.strip()
        
        # If listing page already has salary, prioritize it
        if not salary_raw and job.get("薪资要求"):
            salary_raw = job["薪资要求"]
        
        if salary_raw:
            def clean_salary_text(text):
                text = re.sub(r'\s+', ' ', text)
                text = text.strip()
                text = re.sub(r'<[^>]+>', '', text)
                
                salary_patterns = [
                    r'\$[\d,]+(?:\.\d{2})?\s*[-–—]\s*\$[\d,]+(?:\.\d{2})?',
                    r'\$[\d,]+(?:\.\d{2})?',
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

        # Company homepage link (Indeed company page URL format)
        company_name = job.get("公司名称", "")
        if company_name:
            # Indeed company page URL format: https://www.indeed.com/cmp/{company-name}
            company_slug = company_name.lower().replace(' ', '-').replace('.', '').replace(',', '')
            company_url = f"https://www.indeed.com/cmp/{company_slug}"
            size = get_company_size_indeed(company_name, company_url, cache)
            job["公司规模"] = size

        if (idx + 1) % 5 == 0 or idx == len(job_list) - 1:
            print(f"详情页进度：{idx + 1}/{len(job_list)}")

        time.sleep(REQUEST_DELAY)


# External interfaces
def fetch_indeed_jobs(keyword):
    return fetch_indeed_list(keyword)

def fetch_details_for_subset(unique_jobs):
    subset = unique_jobs[:DETAIL_LIMIT]
    print(f"开始抓取详情页（{len(subset)} 条）")
    enrich_job_details(subset)
    print("详情页抓取完成")
    return subset

