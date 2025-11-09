# config.py
# 搜索关键词
KEYWORDS = ["AI Engineer", "Machine Learning", "Deep Learning", "NLP", "Data Scientist"]

# 目标地区
LOCATION = "United States"

# 抓取页数上限（每个关键词）
MAX_PAGES = 2

# 抓取间隔（秒）
REQUEST_DELAY = 3

#ZenRows
ZENROWS_API_KEY = "08c8d8cd14d834b61c2f05db07e7a52c5f99955c"
ZENROWS_BASE_URL = "https://api.zenrows.com/v1/"

#输出设置
OUTPUT_EXCEL = "ai_jobs_report.xlsx"
RAW_DATA_DIR = "raw_data"

#字段映射
FIELDS = [
    "职位名称",         # job_title
    "公司名称",         # company_name
    "专业要求",         # requirements / qualifications
    "地点",             # location
    "薪资要求",         # salary
    "工作描述",         # description
    "团队规模/业务线规模", # team_size
    "公司规模",         # company_size
    "职位发布时间",     # posted_date
    "职位状态",         # active/closed
    "招聘平台",         # source (LinkedIn / Indeed)
]
