#全局配置

# 测试编号（输出文件夹名）
RUN_ID = "test010"

# 搜索关键词与地区
KEYWORDS = ["AI Engineer", "Machine Learning", "Deep Learning", "NLP", "Data Scientist"]
LOCATION = "United States"

# 爬取参数
MAX_PAGES = 1
REQUEST_DELAY = 1      # ZenRows 请求延迟（秒）
ZENROWS_API_KEY = "08c8d8cd14d834b61c2f05db07e7a52c5f99955c"
ZENROWS_BASE_URL = "https://api.zenrows.com/v1/"

# 输出路径
OUTPUT_DIR = f"outputs/{RUN_ID}"
LIST_REPORT = f"{OUTPUT_DIR}/report_stage1_list.xlsx"
DETAIL_REPORT = f"{OUTPUT_DIR}/report_stage2_detail.xlsx"
ERROR_LOG = f"{OUTPUT_DIR}/error_log.txt"
CACHE_FILE = f"{OUTPUT_DIR}/company_cache.json"

# 测试阶段：表1抓100条，表2补全20条
LIST_LIMIT = 30
DETAIL_LIMIT = 10

# 字段顺序（Excel 输出列）
FIELDS = [
    "职位名称", "公司名称", "专业要求", "地点",
    "薪资要求", "年薪预估值", "工作描述",
    "团队规模/业务线规模", "公司规模",
    "职位发布时间", "职位状态",
    "招聘平台", "职位链接"
]
