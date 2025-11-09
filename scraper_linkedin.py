import requests
import time
from bs4 import BeautifulSoup
from config import KEYWORDS, LOCATION, MAX_PAGES, REQUEST_DELAY, ZENROWS_API_KEY

ZENROWS_BASE = "https://api.zenrows.com/v1/"

#通用请求函数，带自动重试
def zenrows_get(url, retries=3, delay=2):
    for attempt in range(retries):
        try:
            params = {'url': url, 'apikey': ZENROWS_API_KEY}
            r = requests.get(ZENROWS_BASE, params=params, timeout=30)
            if r.status_code == 200:
                return r.text
            else:
                print(f"ZenRows 请求失败 [{r.status_code}] 第 {attempt + 1} 次: {url}")
        except Exception as e:
            print(f"请求异常 第 {attempt + 1} 次: {str(e)}")
        time.sleep(delay * (attempt + 1))
    return None


#抓取 LinkedIn 搜索结果
def fetch_linkedin_list(keyword):
    results = []
    for page in range(MAX_PAGES):
        start = page * 25
        search_url = (
            f"https://www.linkedin.com/jobs/search?"
            f"keywords={keyword.replace(' ', '%20')}&location={LOCATION.replace(' ', '%20')}&start={start}"
        )
        print(f"📄 抓取列表页：{keyword} - 第 {page + 1} 页")
        html = zenrows_get(search_url)
        if not html:
            continue
        soup = BeautifulSoup(html, 'html.parser')
        cards = soup.find_all('div', class_='base-card')
        for card in cards:
            title_tag = card.find('h3', class_='base-search-card__title')
            company_tag = card.find('h4', class_='base-search-card__subtitle')
            location_tag = card.find('span', class_='job-search-card__location')
            date_tag = card.find('time')
            link_tag = card.find('a', class_='base-card__full-link')

            job = {
                '职位名称': title_tag.get_text(strip=True) if title_tag else '',
                '公司名称': company_tag.get_text(strip=True) if company_tag else '',
                '专业要求': '',
                '地点': location_tag.get_text(strip=True) if location_tag else '',
                '薪资要求': '',
                '工作描述': '',
                '团队规模/业务线规模': '',
                '公司规模': '',
                '职位发布时间': date_tag['datetime'] if date_tag and date_tag.has_attr('datetime') else '',
                '职位状态': 'Active',
                '招聘平台': 'LinkedIn',
                '链接': link_tag['href'] if link_tag and link_tag.has_attr('href') else ''
            }
            results.append(job)
        time.sleep(REQUEST_DELAY)
    return results


#抓取详情页补全
def enrich_job_details(job_list):
    for idx, job in enumerate(job_list):
        url = job.get('链接')
        if not url:
            continue
        html = zenrows_get(url)
        if not html:
            continue
        soup = BeautifulSoup(html, 'html.parser')

        desc_tag = soup.find('div', class_='show-more-less-html__markup')
        description = desc_tag.get_text(separator=' ', strip=True) if desc_tag else ''
        job['工作描述'] = description

        lower_desc = description.lower()
        if "requirement" in lower_desc or "qualification" in lower_desc:
            req_index = lower_desc.find("requirement")
            job['专业要求'] = description[req_index:req_index + 400]

        salary_tag = soup.find('span', string=lambda s: s and '$' in s)
        if salary_tag:
            job['薪资要求'] = salary_tag.get_text(strip=True)

        if (idx + 1) % 10 == 0 or idx == len(job_list) - 1:
            print(f"详情页进度：{idx + 1}/{len(job_list)}")
        time.sleep(REQUEST_DELAY)


def fetch_linkedin_jobs(keyword):
    jobs = fetch_linkedin_list(keyword)
    return jobs


def fetch_details_for_all_jobs(unique_jobs):
    print(f"开始抓取详情页，共 {len(unique_jobs)} 条职位")
    enrich_job_details(unique_jobs)
    print("详情页抓取完成")
