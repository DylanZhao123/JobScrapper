# -*- coding: utf-8 -*-
"""
LinkedIn scraper - checkpoint version
"""
import requests
import time
import re
import json
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
from config import (
    MAX_PAGES, REQUEST_DELAY, ZENROWS_BASE_URL,
    LIST_LIMIT, DETAIL_LIMIT, CACHE_FILE, ERROR_LOG,
    get_zenrows_api_key
)
from checkpoint_manager import (
    save_checkpoint, load_checkpoint, save_stage1_raw_data, load_stage1_raw_data,
    get_processed_urls, add_processed_job
)

# Basic utilities
def zenrows_get(url, retries=3, delay=2):
    """ZenRows request with retry mechanism"""
    api_key = get_zenrows_api_key()  # Validate API key when actually used
    for attempt in range(retries):
        try:
            params = {'url': url, 'apikey': api_key}
            r = requests.get(ZENROWS_BASE_URL, params=params, timeout=30)
            if r.status_code == 200:
                return r.text
            else:
                print(f"ZenRows 请求失败[{r.status_code}] 第{attempt+1}次: {url}")
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


# Scrape LinkedIn job listings with checkpoint support
def fetch_linkedin_list_with_checkpoint(keywords, locations, start_location_index=0, start_keyword_index=0, start_page=0, use_merged_keywords=True):
    """
    Scrape LinkedIn job listings page, supports multiple locations, resume from specified location/keyword/page
    If use_merged_keywords=True, combine all keywords with OR logic to reduce duplicate API calls
    Returns: (all_jobs, completed_locations, completed_keywords, final_location_index, final_keyword_index, final_page)
    """
    all_jobs = load_stage1_raw_data()  # Load existing data
    
    # Build seen set from existing data (real-time deduplication)
    seen = set()
    for job in all_jobs:
        key = (job.get("职位名称", ""), job.get("公司名称", ""))
        if key[0] and key[1]:  # Ensure job title and company name are not empty
            seen.add(key)
    
    initial_unique_count = len(seen)
    
    # If using merged keywords, combine all keywords with OR logic
    if use_merged_keywords:
        # Combine keywords with OR: "keyword1" OR "keyword2" OR ...
        merged_keyword = " OR ".join([f'"{kw}"' for kw in keywords])
        search_keywords = [merged_keyword]  # Single merged keyword search
        print(f"开始抓取列表页（共 {len(locations)} 个地点，使用合并关键词搜索：{len(keywords)} 个关键词合并为1个）")
    else:
        search_keywords = keywords  # Search each keyword separately
        print(f"开始抓取列表页（共 {len(locations)} 个地点，{len(keywords)} 个关键词）")
    
    print(f"从地点 {start_location_index+1}/{len(locations)} 关键词 {start_keyword_index+1}/{len(search_keywords)} 第 {start_page+1} 页继续")
    print(f"已加载 {len(all_jobs)} 条职位，去重后 {initial_unique_count} 条唯一职位")
    
    completed_locations = []
    completed_keywords = []
    total_skipped = 0  # Count total skipped duplicate jobs
    last_progress_report = start_location_index  # Track last progress report
    
    for loc_idx, location in enumerate(locations):
        # Skip completed locations
        if loc_idx < start_location_index:
            completed_locations.append(location)
            continue
        
        # Display current state information (if available)
        state_info = ""
        if ", " in location:
            state_code = location.split(", ")[-1]
            state_info = f" (州: {state_code})"
        
        # If this is the current location, start from specified keyword
        start_from_keyword = start_keyword_index if loc_idx == start_location_index else 0
        
        for kw_idx, keyword in enumerate(search_keywords):
            # Skip completed keywords
            if loc_idx == start_location_index and kw_idx < start_keyword_index:
                continue
            
            # If this is the current keyword, start from the next page of specified page
            if loc_idx == start_location_index and kw_idx == start_keyword_index:
                start_from_page = start_page + 1  # Continue from next page
            else:
                start_from_page = 0
            
            results = []
            consecutive_zero_pages = 0  # Track consecutive pages with 0 new jobs
            location_new_count = 0  # Track new jobs for this location
            
            for page in range(start_from_page, MAX_PAGES):
                start = page * 25
                if len(all_jobs) + len(results) >= LIST_LIMIT:
                    break
                
                # URL encode the keyword (handle OR logic and quotes)
                if use_merged_keywords:
                    # For merged keywords with OR, use quote_plus for proper encoding
                    keyword_encoded = quote_plus(keyword)
                else:
                    keyword_encoded = keyword.replace(' ', '%20')
                
                location_encoded = location.replace(' ', '%20')
                url = f"https://www.linkedin.com/jobs/search?keywords={keyword_encoded}&location={location_encoded}&start={start}"
                
                html = zenrows_get(url)
                if not html:
                    print(f"地点 {loc_idx+1}/{len(locations)} {location}: 第 {page + 1} 页抓取失败")
                    continue
                
                soup = BeautifulSoup(html, 'html.parser')
                cards = soup.find_all('div', class_='base-card')
                
                # Check if there are still results
                if not cards or len(cards) == 0:
                    # If no results on first page, this keyword has no search results in this location
                    if page == start_from_page:
                        break
                    # If subsequent pages have no results, scraping is complete, break keyword loop
                    break
                
                page_jobs = 0
                page_skipped = 0  # Duplicate jobs skipped on this page
                for card in cards:
                    # Check if limit is reached (based on deduplicated count)
                    if len(seen) >= LIST_LIMIT:
                        break
                    
                    title = card.find('h3', class_='base-search-card__title')
                    company = card.find('h4', class_='base-search-card__subtitle')
                    job_location = card.find('span', class_='job-search-card__location')
                    date = card.find('time')
                    link = card.find('a', class_='base-card__full-link')
                    
                    job_title = title.get_text(strip=True) if title else ''
                    company_name = company.get_text(strip=True) if company else ''
                    
                    # Real-time deduplication check
                    key = (job_title, company_name)
                    if not key[0] or not key[1]:
                        # Job title or company name is empty, skip
                        continue
                    
                    if key in seen:
                        # Duplicate job, skip
                        page_skipped += 1
                        total_skipped += 1
                        continue
                    
                    # New job, add to seen set and results
                    seen.add(key)
                    job = {
                        "职位名称": job_title,
                        "公司名称": company_name,
                        "专业要求": '',
                        "地点": job_location.get_text(strip=True) if job_location else location,
                        "薪资要求": '',
                        "年薪预估值": '',
                        "工作描述": '',
                        "团队规模/业务线规模": '',
                        "公司规模": '',
                        "职位发布时间": date['datetime'] if date and date.has_attr('datetime') else '',
                        "职位状态": 'Active',
                        "招聘平台": 'LinkedIn',
                        "职位链接": link['href'] if link and link.has_attr('href') else ''
                    }
                    results.append(job)
                    page_jobs += 1
                    location_new_count += 1
                
                # Track consecutive pages with 0 new jobs
                if page_jobs == 0:
                    consecutive_zero_pages += 1
                    if consecutive_zero_pages >= 2:
                        break
                else:
                    consecutive_zero_pages = 0  # Reset counter if found new jobs
                
                # Save checkpoint and data after each page (only save unique jobs)
                all_jobs.extend(results)
                save_stage1_raw_data(all_jobs)
                # Save checkpoint: save current completed page (resume from page+1 next time)
                save_checkpoint(
                    stage="stage1_list",
                    current_location_index=loc_idx,
                    current_keyword_index=kw_idx,
                    current_page=page,  # Current completed page (0-based), resume from page+1 next time
                    completed_locations=completed_locations,
                    completed_keywords=completed_keywords + [keyword] if page == MAX_PAGES - 1 else completed_keywords,
                    total_jobs_count=len(all_jobs)
                )
                results = []  # Clear, already saved to all_jobs
                
                time.sleep(REQUEST_DELAY)
            
            # Display location summary (only if new jobs found)
            if location_new_count > 0:
                print(f"地点 {loc_idx+1}/{len(locations)} {location}: 新增 {location_new_count} 条，累计唯一 {len(seen)} 条")
        
        # Progress reporting: every 10 locations or on last location
        if loc_idx + 1 - last_progress_report >= 10 or loc_idx + 1 == len(locations):
            progress_percent = ((loc_idx + 1) / len(locations)) * 100
            print(f"[进度] 地点: {loc_idx + 1}/{len(locations)} ({progress_percent:.1f}%) - 累计唯一职位: {len(seen)} 条")
            last_progress_report = loc_idx + 1
            
            # If limit reached (based on unique job count), end early
            if len(seen) >= LIST_LIMIT:
                print(f"  已达到列表限制 {LIST_LIMIT} 条唯一职位，停止抓取")
                break
    
    # Return deduplicated data (all_jobs already contains only unique jobs)
    final_unique_count = len(seen)
    total_fetched = len(all_jobs) + total_skipped
    print(f"\n阶段1完成统计：")
    print(f"  总抓取: {total_fetched} 条")
    print(f"  唯一职位: {final_unique_count} 条")
    print(f"  跳过重复: {total_skipped} 条")
    if total_fetched > 0:
        print(f"  重复率: {total_skipped/total_fetched*100:.1f}%")
    else:
        print(f"  重复率: 0%")
    
    return all_jobs, completed_locations, completed_keywords, len(locations), len(search_keywords), 0


# Salary parsing and estimation (keep original logic)
def parse_salary(salary_text):
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
    
    is_annual = any(x in text_lower for x in ['year', 'annual', 'per annum', 'yr', '/yr', 'per year'])
    is_monthly = any(x in text_lower for x in ['month', 'mo', '/m', 'per month', 'monthly'])
    is_hourly = any(x in text_lower for x in ['hour', 'hr', '/h', 'per hour', 'hourly', '/hr'])
    
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


# Company size scraping (keep original logic)
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

def normalize_company_url(company_url):
    """Normalize company URL"""
    if not company_url:
        return ''
    
    if '?' in company_url:
        company_url = company_url.split('?')[0]
    
    if company_url.startswith('http'):
        match = re.search(r'/company/([^/?]+)', company_url)
        if match:
            return f"/company/{match.group(1)}"
        return company_url
    
    if company_url.startswith('/company/'):
        return company_url
    
    return company_url

def get_company_size(company_name, company_url, cache):
    """Get company size (employee count)"""
    if not company_name or not company_url:
        return ''
    
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
    
    normalized_url = normalize_company_url(company_url)
    full_url = "https://www.linkedin.com" + normalized_url if normalized_url.startswith("/company/") else normalized_url
    html = zenrows_get(full_url)
    if not html:
        cache[company_name] = ''
        save_cache(cache)
        return ''
    
    soup = BeautifulSoup(html, "html.parser")
    
    # Method 1: JSON-LD
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
                                save_cache(cache)
                                return str(employee_num)
            elif isinstance(data, dict) and data.get('@type') == 'Organization':
                if 'numberOfEmployees' in data:
                    emp_data = data['numberOfEmployees']
                    if isinstance(emp_data, dict) and 'value' in emp_data:
                        employee_num = int(emp_data['value'])
                        cache[company_name] = str(employee_num)
                        save_cache(cache)
                        return str(employee_num)
        except:
            continue
    
    # Method 2: Standard dd tag
    tag = soup.find("dd", class_="org-about-company-module__company-size-definition-text")
    if tag:
        text = tag.get_text(strip=True)
        num = extract_employee_number(text)
        if num:
            cache[company_name] = num
            save_cache(cache)
            return num
    
    # Method 3: Find all elements containing "employees"
    for elem in soup.find_all(['span', 'div', 'p', 'li', 'a', 'dt', 'dd']):
        text = elem.get_text(strip=True)
        if re.search(r'\d+.*employee', text, re.I):
            num = extract_employee_number(text)
            if num:
                cache[company_name] = num
                save_cache(cache)
                return num
    
    # Method 4: String node
    tag = soup.find(string=re.compile(r"employees", re.I))
    if tag and tag.parent:
        text = tag.parent.get_text(strip=True)
        num = extract_employee_number(text)
        if num:
            cache[company_name] = num
            save_cache(cache)
            return num
    
    cache[company_name] = ''
    save_cache(cache)
    return ''


def enrich_job_details_with_checkpoint(job_list, start_index=0):
    """
    Enrich job details, supports resuming from specified index
    Automatically skip already processed jobs
    """
    cache = load_cache()
    processed_urls = get_processed_urls()
    
    print(f"\n开始抓取详情页（共 {len(job_list)} 条，从第 {start_index+1} 条开始）")
    
    consecutive_failures = 0  # Track consecutive failures
    last_report_index = start_index  # Track last report index
    
    # Simple progress bar function
    def print_progress(current, total, bar_length=30):
        """打印简单的进度条"""
        percent = (current / total) * 100
        filled = int(bar_length * current / total)
        bar = '█' * filled + '░' * (bar_length - filled)
        return f"[{bar}] {current}/{total} ({percent:.1f}%)"
    
    for idx, job in enumerate(job_list):
        # Skip already processed
        if idx < start_index:
            continue
        
        job_url = job.get("职位链接")
        if not job_url:
            # Save checkpoint even if no URL (to track progress)
            if (idx + 1) % 5 == 0 or idx == len(job_list) - 1:
                save_checkpoint(
                    stage="stage2_detail",
                    processed_count=idx + 1,
                    total_count=len(job_list)
                )
            continue
        
        # Check if already processed
        if job_url in processed_urls:
            continue
        
        html = zenrows_get(job_url)
        if not html:
            consecutive_failures += 1
            # Report each failure in PowerShell
            print(f"[失败] 详情页 {idx + 1}/{len(job_list)}: 抓取失败 (连续失败 {consecutive_failures} 次)")
            
            # Report after 3 consecutive failures
            if consecutive_failures >= 3:
                print(f"⚠ 警告: 连续 {consecutive_failures} 次请求失败，请检查网络连接或API状态")
            
            if (idx + 1) % 5 == 0 or idx == len(job_list) - 1:
                save_checkpoint(
                    stage="stage2_detail",
                    processed_count=idx + 1,
                    total_count=len(job_list)
                )
            continue
        
        # Reset consecutive failures on success
        consecutive_failures = 0
        
        soup = BeautifulSoup(html, 'html.parser')

        # Job description
        desc = soup.find('div', class_='show-more-less-html__markup')
        description = desc.get_text(separator=' ', strip=True) if desc else ''
        job["工作描述"] = description

        # Professional requirements
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

        # Salary logic (keep original complete logic)
        salary_raw = ''
        salary_tags = soup.find_all(string=re.compile(r'\$'))
        for tag in salary_tags:
            parent = tag.parent
            if parent:
                text = parent.get_text(strip=True)
                if '$' in text and (re.search(r'\d', text)):
                    salary_raw = text
                    break
        
        if not salary_raw:
            for elem in soup.find_all(['span', 'div', 'li', 'p']):
                text = elem.get_text(strip=True)
                if '$' in text and re.search(r'\d', text):
                    parent_text = ''
                    if elem.parent:
                        parent_text = elem.parent.get_text(strip=True).lower()
                    if any(keyword in parent_text for keyword in ['salary', 'compensation', 'pay', 'wage', 'range']):
                        salary_raw = text
                        break
        
        if not salary_raw and description:
            salary_matches = re.findall(r'\$[\d,]+(?:[kKmM])?\s*[-–—]\s*\$[\d,]+(?:[kKmM])?', description)
            if not salary_matches:
                salary_matches = re.findall(r'\$[\d,]+(?:[kKmM])?', description)
            if salary_matches:
                salary_raw = salary_matches[0]
                idx_pos = description.find(salary_raw)
                if idx_pos >= 0:
                    context = description[max(0, idx_pos-50):idx_pos+len(salary_raw)+50]
                    if re.search(r'(year|month|hour|annual|monthly|hourly)', context, re.I):
                        salary_raw = context.strip()
        
        if salary_raw:
            def clean_salary_text(text):
                if '@context' in text or '@type' in text or 'schema.org' in text:
                    try:
                        if 'baseSalary' in text:
                            salary_match = re.search(r'"baseSalary"[^}]*"minValue":(\d+)[^}]*"maxValue":(\d+)', text)
                            if salary_match:
                                min_val = int(salary_match.group(1))
                                max_val = int(salary_match.group(2))
                                return f"${min_val:,} - ${max_val:,}"
                        salary_match = re.search(r'"value"[^}]*"minValue":(\d+)[^}]*"maxValue":(\d+)', text)
                        if salary_match:
                            min_val = int(salary_match.group(1))
                            max_val = int(salary_match.group(2))
                            return f"${min_val:,} - ${max_val:,}"
                    except:
                        pass
                    return ''
                
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
                        idx_pos = text.find(cleaned)
                        if idx_pos >= 0:
                            context = text[max(0, idx_pos-30):idx_pos+len(cleaned)+30].lower()
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

        # Company size
        company_tag = soup.find('a', href=re.compile(r'/company/'))
        if company_tag:
            company_url = company_tag['href']
            size = get_company_size(job["公司名称"], company_url, cache)
            job["公司规模"] = size
        
        # Save processed job
        add_processed_job(job)
        
        # Progress reporting: every 50 jobs or on last job
        current_progress = idx + 1
        if current_progress - last_report_index >= 50 or current_progress == len(job_list):
            print(f"\r{print_progress(current_progress, len(job_list))} - 已处理详情页", end='', flush=True)
            if current_progress == len(job_list):
                print()  # New line when complete
            last_report_index = current_progress
        
        # Save checkpoint every 5 jobs or on last job
        if (idx + 1) % 5 == 0 or idx == len(job_list) - 1:
            save_checkpoint(
                stage="stage2_detail",
                processed_count=idx + 1,
                total_count=len(job_list)
            )

        time.sleep(REQUEST_DELAY)
    
    print(f"\n详情页抓取完成: 共处理 {len(job_list)} 条职位")
    return job_list

