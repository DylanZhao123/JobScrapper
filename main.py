from scraper_linkedin import fetch_linkedin_jobs, fetch_details_for_subset
from exporter import export_to_excel
from config import KEYWORDS, LIST_REPORT, DETAIL_REPORT
import traceback

def main():
    print("启动测试阶段（同步抓取公司规模 + 年薪估算）")
    all_jobs = []
    for kw in KEYWORDS:
        print(f"抓取关键词：{kw}")
        jobs = fetch_linkedin_jobs(kw)
        print(f"关键词「{kw}」抓取 {len(jobs)} 条")
        all_jobs.extend(jobs)

    seen = set()
    unique_jobs = []
    for job in all_jobs:
        key = (job["职位名称"], job["公司名称"], job["地点"])
        if key not in seen:
            seen.add(key)
            unique_jobs.append(job)
    print(f"去重后剩余 {len(unique_jobs)} 条")

    # 表1（列表）
    export_to_excel(unique_jobs, LIST_REPORT)

    # 表2（详情 + 公司规模）
    detail_jobs = fetch_details_for_subset(unique_jobs)
    export_to_excel(detail_jobs, DETAIL_REPORT)
    print("测试运行完成")

if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("程序出错：")
        print(traceback.format_exc())
