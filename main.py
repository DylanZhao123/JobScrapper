from scraper_linkedin import fetch_linkedin_jobs, fetch_details_for_all_jobs
from exporter import export_to_excel
from config import KEYWORDS
import traceback

def main():
    print("启动 AI 职位抓取程序...")
    all_jobs = []
    for kw in KEYWORDS:
        print("=" * 60)
        print(f"开始抓取关键词：{kw}")
        jobs = fetch_linkedin_jobs(kw)
        print(f"关键词「{kw}」抓取完成，共 {len(jobs)} 条数据")
        all_jobs.extend(jobs)

    if not all_jobs:
        print("没有抓到任何数据，检查 ZenRows 或网络连接")
        return

    #去重
    seen = set()
    unique_jobs = []
    for job in all_jobs:
        key = (job.get("职位名称"), job.get("公司名称"), job.get("地点"))
        if key not in seen:
            seen.add(key)
            unique_jobs.append(job)
    print(f"去重后剩余 {len(unique_jobs)} 条数据")

    #详情页补全
    fetch_details_for_all_jobs(unique_jobs)

    #导出
    export_to_excel(unique_jobs)
    print("程序执行完毕！")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("程序运行出错：")
        print(traceback.format_exc())
