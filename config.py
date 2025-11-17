# Global configuration
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Test run ID (output folder name)
RUN_ID = "BunchTest017"

# Target site settings. Options: "linkedin", "indeed", "mixed" (mixed mode, not implemented yet)
TARGET_SITE = "linkedin"

# Search keywords and location
# Use merged keyword search: combine all keywords with OR logic to reduce duplicate API calls
KEYWORDS = ["AI Engineer", "Machine Learning", "Deep Learning", "NLP", "Data Scientist"]
USE_MERGED_KEYWORDS = True  # If True, search all keywords together with OR logic; If False, search each keyword separately


from locations_config import LOCATIONS, LOCATIONS_BY_STATE

LOCATION = "United States"  # Reserved for backward compatibility

# Scraping parameters
MAX_PAGES = 10  

REQUEST_DELAY = 0.3

# API Key from environment variable (.env file)
# Lazy check: only validate when actually needed (not during import)
def get_zenrows_api_key():
    """Get ZenRows API key, raise error if not found"""
    api_key = os.getenv("ZENROWS_API_KEY")
    if not api_key:
        raise ValueError(
            "ZENROWS_API_KEY not found in environment variables.\n"
            "Please create a .env file in the project root and add:\n"
            "ZENROWS_API_KEY=your_actual_api_key_here\n"
            "You can copy .env.example to .env as a template."
        )
    return api_key

# For backward compatibility, try to get API key but don't raise error during import
# This allows other scripts to import config.py without requiring API key
ZENROWS_API_KEY = os.getenv("ZENROWS_API_KEY")  # May be None, will be checked when used
ZENROWS_BASE_URL = "https://api.zenrows.com/v1/"

# Supabase configuration (optional, for database storage)
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# Output paths
OUTPUT_DIR = f"outputs/{RUN_ID}"
LIST_REPORT = f"{OUTPUT_DIR}/report_stage1_list.xlsx"
DETAIL_REPORT = f"{OUTPUT_DIR}/report_stage2_detail.xlsx"
ERROR_LOG = f"{OUTPUT_DIR}/error_log.txt"
CACHE_FILE = f"{OUTPUT_DIR}/company_cache.json"

# Country-specific output paths
def get_country_output_paths(country_code: str):
    """根据国家代码返回对应的输出路径"""
    country_dir = f"{OUTPUT_DIR}/{country_code.upper()}"
    return {
        "dir": country_dir,
        "list_report": f"{country_dir}/report_stage1_list.xlsx",
        "detail_report": f"{country_dir}/report_stage2_detail.xlsx",
        "cache_file": f"{country_dir}/company_cache.json",
    }

# Data collection limits
LIST_LIMIT = 20000  
DETAIL_LIMIT = 20000  
# Field order (Excel output columns)
FIELDS = [
    "职位名称", "公司名称", "专业要求", "地点",
    "薪资要求", "年薪预估值", "工作描述",
    "团队规模/业务线规模", "公司规模",
    "职位发布时间", "职位状态",
    "招聘平台", "职位链接"
]
