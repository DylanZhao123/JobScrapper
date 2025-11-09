import requests
import time
import re
import json
from bs4 import BeautifulSoup
from config import (
    LOCATION, MAX_PAGES, REQUEST_DELAY, ZENROWS_API_KEY, ZENROWS_BASE_URL,
    LIST_LIMIT, DETAIL_LIMIT, CACHE_FILE, ERROR_LOG
)

#基础工具
def zenrows_get(url, retries=3, delay=2):
    """带重试的 ZenRows 请求"""
    for attempt in range(retries):
        try:
            params = {'url': url, 'apikey': ZENROWS_API_KEY}
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


#抓取 LinkedIn 列表页
def fetch_linkedin_list(keyword):
    results = []
    for page in range(MAX_PAGES):
        start = page * 25
        if len(results) >= LIST_LIMIT:
            break
        url = f"https://www.linkedin.com/jobs/search?keywords={keyword.replace(' ', '%20')}&location={LOCATION.replace(' ', '%20')}&start={start}"
        print(f"抓取列表页：{keyword} 第 {page + 1} 页")
        html = zenrows_get(url)
        if not html:
            continue
        soup = BeautifulSoup(html, 'html.parser')
        cards = soup.find_all('div', class_='base-card')
        for card in cards:
            if len(results) >= LIST_LIMIT:
                break
            title = card.find('h3', class_='base-search-card__title')
            company = card.find('h4', class_='base-search-card__subtitle')
            location = card.find('span', class_='job-search-card__location')
            date = card.find('time')
            link = card.find('a', class_='base-card__full-link')
            job = {
                "职位名称": title.get_text(strip=True) if title else '',
                "公司名称": company.get_text(strip=True) if company else '',
                "专业要求": '',
                "地点": location.get_text(strip=True) if location else '',
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
        time.sleep(REQUEST_DELAY)
    return results[:LIST_LIMIT]


#薪资解析和估算
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
    
    # 提取所有数字 - 改进正则表达式以更好地处理各种格式
    numbers = []
    # 匹配 $150,000.00 或 $150k 或 150000 等格式
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
    
    # 如果都没有明确标识，根据数值范围推断（年薪通常>50000，月薪通常<50000，时薪通常<200）
    if not (is_annual or is_monthly or is_hourly):
        avg_num = sum(numbers) / len(numbers)
        if avg_num < 200:
            is_hourly = True
        elif avg_num < 50000:
            is_monthly = True
        else:
            is_annual = True
    
    # 计算年薪预估值（round到十位）
    def round_to_tens(num):
        """将数字round到十位，例如 165123 -> 165120"""
        return round(num / 10) * 10
    
    if is_annual:
        if len(numbers) >= 2:
            # 区间，取中间值
            annual_estimate = (min(numbers) + max(numbers)) / 2
        else:
            annual_estimate = numbers[0]
        return ('年薪', round_to_tens(annual_estimate))
    elif is_monthly:
        if len(numbers) >= 2:
            # 月薪区间，取中间值后乘以12
            monthly_avg = (min(numbers) + max(numbers)) / 2
            annual_estimate = monthly_avg * 12
        else:
            annual_estimate = numbers[0] * 12
        return ('月薪', round_to_tens(annual_estimate))
    elif is_hourly:
        if len(numbers) >= 2:
            # 时薪区间，取中间值后乘以2080（40小时*52周）
            hourly_avg = (min(numbers) + max(numbers)) / 2
            annual_estimate = hourly_avg * 40 * 52
        else:
            annual_estimate = numbers[0] * 40 * 52
        return ('时薪', round_to_tens(annual_estimate))
    else:
        return ('未知', '')


#公司规模抓取
def get_company_size(company_name, company_url, cache):
    if not company_name or not company_url:
        return ''
    
    if company_name in cache:
        return cache[company_name]
    
    full_url = "https://www.linkedin.com" + company_url if company_url.startswith("/company/") else company_url
    html = zenrows_get(full_url)
    if not html:
        return ''
    
    soup = BeautifulSoup(html, "html.parser")
    
    tag = soup.find("dd", class_="org-about-company-module__company-size-definition-text")
    if not tag:
        tag = soup.find(string=re.compile(r"employees"))
    
    if tag:
        text = tag.get_text(strip=True) if hasattr(tag, "get_text") else str(tag).strip()
        cache[company_name] = text
        save_cache(cache)
        return text
    
    cache[company_name] = ''
    save_cache(cache)
    return ''


def enrich_job_details(job_list):
    cache = load_cache()
    for idx, job in enumerate(job_list):
        url = job.get("职位链接")
        if not url:
            # 即使没有链接，也保留记录，只是详情字段为空
            if (idx + 1) % 5 == 0 or idx == len(job_list) - 1:
                print(f"详情页进度：{idx + 1}/{len(job_list)}")
            continue

        html = zenrows_get(url)
        if not html:
            # 即使无法获取HTML，也保留记录
            if (idx + 1) % 5 == 0 or idx == len(job_list) - 1:
                print(f"详情页进度：{idx + 1}/{len(job_list)}")
            continue
        
        soup = BeautifulSoup(html, 'html.parser')

        # 工作描述
        desc = soup.find('div', class_='show-more-less-html__markup')
        description = desc.get_text(separator=' ', strip=True) if desc else ''
        job["工作描述"] = description

        # 专业要求 - 改进提取逻辑
        requirements_text = ''
        
        # 方法1: 查找明确的 "Requirements", "Qualifications", "Required" 等章节
        req_patterns = [
            r'(?:requirements?|qualifications?|required|must have|minimum requirements?)[\s:]*\n?([^\n]{100,800})',
            r"(?:what you['']?ll need|what we['']?re looking for|you should have)[\s:]*\n?([^\n]{100,800})",
            r'(?:education|experience|skills?)[\s:]*\n?([^\n]{100,600})',
        ]
        
        for pattern in req_patterns:
            matches = re.finditer(pattern, description, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                req_section = match.group(1).strip()
                # 清理文本，移除多余空白
                req_section = re.sub(r'\s+', ' ', req_section)
                if len(req_section) > 50:  # 确保有足够内容
                    requirements_text = req_section[:500]  # 限制长度
                    break
            if requirements_text:
                break
        
        # 方法2: 如果没找到明确章节，尝试提取包含关键技能/要求的句子
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

        # 薪资逻辑
        salary_raw = ''
        
        # 方法1: 查找包含 $ 符号的薪资元素
        salary_tags = soup.find_all(string=re.compile(r'\$'))
        for tag in salary_tags:
            parent = tag.parent
            if parent:
                text = parent.get_text(strip=True)
                if '$' in text and (re.search(r'\d', text)):
                    salary_raw = text
                    break
        
        # 方法2: 查找常见的薪资选择器
        if not salary_raw:
            # 尝试查找包含 "salary", "compensation" 等关键词
            for elem in soup.find_all(['span', 'div', 'li', 'p']):
                text = elem.get_text(strip=True)
                if '$' in text and re.search(r'\d', text):
                    parent_text = ''
                    if elem.parent:
                        parent_text = elem.parent.get_text(strip=True).lower()
                    if any(keyword in parent_text for keyword in ['salary', 'compensation', 'pay', 'wage', 'range']):
                        salary_raw = text
                        break
        
        # 方法3: 在描述中查找薪资信息
        if not salary_raw and description:
            salary_matches = re.findall(r'\$[\d,]+(?:[kKmM])?\s*[-–—]\s*\$[\d,]+(?:[kKmM])?', description)
            if not salary_matches:
                salary_matches = re.findall(r'\$[\d,]+(?:[kKmM])?', description)
            if salary_matches:
                # 取第一个匹配的薪资信息
                salary_raw = salary_matches[0]
                idx = description.find(salary_raw)
                if idx >= 0:
                    context = description[max(0, idx-50):idx+len(salary_raw)+50]
                    # 如果上下文包含时间单位，添加到薪资文本中
                    if re.search(r'(year|month|hour|annual|monthly|hourly)', context, re.I):
                        salary_raw = context.strip()
        
        if salary_raw:
            def clean_salary_text(text):
                # 移除JSON格式的数据（如果包含 @context, @type 等）
                if '@context' in text or '@type' in text or 'schema.org' in text:
                    # 尝试从JSON中提取薪资信息
                    import json
                    try:
                        # 查找 baseSalary 字段
                        if 'baseSalary' in text:
                            salary_match = re.search(r'"baseSalary"[^}]*"minValue":(\d+)[^}]*"maxValue":(\d+)', text)
                            if salary_match:
                                min_val = int(salary_match.group(1))
                                max_val = int(salary_match.group(2))
                                return f"${min_val:,} - ${max_val:,}"
                        # 查找 value 字段中的薪资范围
                        salary_match = re.search(r'"value"[^}]*"minValue":(\d+)[^}]*"maxValue":(\d+)', text)
                        if salary_match:
                            min_val = int(salary_match.group(1))
                            max_val = int(salary_match.group(2))
                            return f"${min_val:,} - ${max_val:,}"
                    except:
                        pass
                    return ''
                
                # 移除换行符和多余空白
                text = re.sub(r'\s+', ' ', text)
                text = text.strip()
                
                # 移除HTML标签
                text = re.sub(r'<[^>]+>', '', text)
                
                # 只保留薪资相关的文本（包含$和数字的部分）
                # 提取所有薪资范围或单个薪资
                salary_patterns = [
                    r'\$[\d,]+(?:\.\d{2})?\s*[-–—]\s*\$[\d,]+(?:\.\d{2})?',  # 范围
                    r'\$[\d,]+(?:\.\d{2})?',  # 单个
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
                # 如果清理后的文本已经包含类型标注，就不重复添加
                if '(年薪)' in cleaned_salary or '(月薪)' in cleaned_salary or '(时薪)' in cleaned_salary:
                    job["薪资要求"] = cleaned_salary
                elif salary_type != '未知':
                    job["薪资要求"] = f"{cleaned_salary} ({salary_type})"
                else:
                    job["薪资要求"] = cleaned_salary
                
                # 年薪预估值（前面加$符号）
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

        # 公司主页链接
        company_tag = soup.find('a', href=re.compile(r'/company/'))
        if company_tag:
            company_url = company_tag['href']
            size = get_company_size(job["公司名称"], company_url, cache)
            job["公司规模"] = size

        if (idx + 1) % 5 == 0 or idx == len(job_list) - 1:
            print(f"详情页进度：{idx + 1}/{len(job_list)}")

        time.sleep(REQUEST_DELAY)


#外部接口
def fetch_linkedin_jobs(keyword):
    return fetch_linkedin_list(keyword)

def fetch_details_for_subset(unique_jobs):
    subset = unique_jobs[:DETAIL_LIMIT]
    print(f"开始抓取详情页（{len(subset)} 条）")
    enrich_job_details(subset)
    print("详情页抓取完成")
    return subset
