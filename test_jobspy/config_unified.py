# -*- coding: utf-8 -*-
"""
================================================================================
JobScrapper 统一配置文件
================================================================================

配置文件位置: test_jobspy/config_unified.py

所有配置都可以在此文件中直接修改，无需使用命令行参数。
运行方式: python main_unified.py

================================================================================
"""

import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# =============================================================================
# 基本运行配置
# =============================================================================

# 运行ID（用于输出目录命名）
RUN_ID = "unified_2025_01_25_major_test1"

# 输出目录（自动生成，基于RUN_ID）
OUTPUT_DIR = Path(__file__).parent / "output" / RUN_ID

# =============================================================================
# 网站选择配置
# =============================================================================

# 要爬取的平台列表
# 可选值: "linkedin", "indeed"
# 可以选择单个或两个都选
PLATFORMS = ["linkedin", "indeed"]  # 同时爬取两个平台
# PLATFORMS = ["linkedin"]  # 只爬取LinkedIn
# PLATFORMS = ["indeed"]  # 只爬取Indeed

# =============================================================================
# 搜索配置
# =============================================================================

# =============================================================================
# 搜索关键词配置
# =============================================================================

# 核心AI关键词（最相关岗位）
CORE_KEYWORDS = [
    "AI Engineer",
    "Machine Learning",
    "Deep Learning",
    "NLP",
    "Data Scientist",
]

# 次要相关岗位关键词
AI_RELATED_KEYWORDS = [
    # AI销售相关
    "AI Sales", "AI Sales Representative", "AI Sales Manager",
    "AI Business Development", "AI Account Manager",

    # AI会话师相关
    "AI Conversation", "AI Conversational Designer", "AI Chatbot Designer",
    "AI Dialogue Designer", "Conversational AI", "AI Voice Assistant",

    # AI训练师相关
    "AI Training", "AI Trainer", "AI Model Training", "AI Data Training",
    "AI Training Specialist", "Machine Learning Trainer",

    # AI产品经理相关
    "AI Product Manager", "AI PM", "AI Product Owner", "AI Product Lead",

    # AI+行业相关
    "AI Healthcare", "AI Finance", "AI Education", "AI Retail",
    "AI Manufacturing", "AI Agriculture", "AI Transportation",
    "AI Energy", "AI Legal", "AI Marketing",

    # AI艺术相关
    "AI Art", "AI Artist", "AI Painting", "AI Illustrator",
    "AI Creative", "AI Digital Art", "AI Visual Artist",

    # AI设计相关
    "AI Design", "AI Designer", "AI UX Designer", "AI UI Designer",
    "AI Interaction Designer", "AI Design Specialist",

    # AI架构相关
    "AI Architecture", "AI Architect", "AI System Architecture",
    "AI Solution Architect", "AI Platform Architect",

    # AI治理相关
    "AI Governance", "AI Governance Specialist", "AI Compliance",
    "AI Risk Management", "AI Policy",

    # AI伦理相关
    "AI Ethics", "AI Ethical", "AI Ethics Researcher",
    "Responsible AI", "AI Fairness", "AI Bias",

    # AI硬件相关
    "AI Hardware", "AI Hardware Engineer", "AI Chip Design",
    "AI Accelerator", "AI Processor",

    # AI运维相关
    "AI Operations", "AI Ops", "AI DevOps", "AI Infrastructure",
    "AI MLOps", "AI Platform Engineer", "AI Systems Engineer",

    # 数据标注相关
    "Data Annotation", "Data Labeling", "Data Annotator",
    "Data Tagging", "Data Quality", "Data Curation",

    # 机器人相关
    "Robotics", "Robot Engineer", "Robotics Engineer",
    "Autonomous Systems", "Robotic Process Automation", "RPA",
]

# 是否包含次要关键词（设为False只搜索核心关键词，减少搜索量）
INCLUDE_RELATED_KEYWORDS = True

# 最终使用的关键词列表
if INCLUDE_RELATED_KEYWORDS:
    KEYWORDS = CORE_KEYWORDS + AI_RELATED_KEYWORDS
else:
    KEYWORDS = CORE_KEYWORDS

# =============================================================================
# 多地区配置
# =============================================================================

# 是否启用多地区模式（自动循环爬取所有配置的地区）
ENABLE_MULTI_REGION = True

# 要爬取的地区列表（多地区模式下使用）
REGIONS = [
    "United States",
    "United Kingdom",
    "Australia",
    "Singapore",
    "Hong Kong",
]

# 单地区模式下的默认地区（ENABLE_MULTI_REGION=False时使用）
DEFAULT_REGION = "United States"

# =============================================================================
# 爬取数量和页数配置
# =============================================================================

# 每个搜索组合（关键词+地点）返回的最大结果数
RESULTS_PER_SEARCH = 100

# 总职位数量限制（设为 None 表示不限制）
MAX_TOTAL_JOBS = None
# MAX_TOTAL_JOBS = 500  # 限制最多爬取500个职位

# 测试模式：快速测试时使用较小的数值
TEST_MODE = False  # 设为True启用测试模式
TEST_RESULTS_PER_SEARCH = 5  # 测试模式下每次搜索的结果数
TEST_MAX_JOBS = 20  # 测试模式下最大职位数
TEST_KEYWORDS_LIMIT = 2  # 测试模式下使用的关键词数量
TEST_LOCATIONS_LIMIT = 2  # 测试模式下使用的地点数量

# =============================================================================
# 请求速率配置
# =============================================================================

# 请求之间的延迟（秒）
REQUEST_DELAY = 0.5

# 失败重试次数
RETRY_ATTEMPTS = 3

# 重试延迟基数（秒，使用指数退避）
RETRY_DELAY = 2.0

# =============================================================================
# 过滤配置
# =============================================================================

# 是否只保留AI相关职位
FILTER_AI_RELATED = True

# 最早发布日期过滤（设为 None 表示不过滤）
MIN_POSTED_DATE = datetime(2025, 12, 25)
# MIN_POSTED_DATE = datetime(2025, 1, 1)  # 只保留2025年1月1日之后发布的职位

# =============================================================================
# Gemini AI 配置
# =============================================================================

# 是否启用AI分析
ENABLE_AI_ANALYSIS = True  # 设为False跳过AI分析

# API Key（建议在.env文件中设置，而不是直接写在这里）
# 方式1: 在.env文件中设置 GEMINI_API_KEY=your_key
# 方式2: 直接在这里设置（不推荐，有安全风险）
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyD7J143kqKq3DBGR8UAVVHDIvlSMD9VMP4")

# Gemini模型选择
GEMINI_MODEL = "gemini-2.5-flash-preview-05-20"
# 其他可选模型:
# GEMINI_MODEL = "gemini-2.0-flash-exp"
# GEMINI_MODEL = "gemini-1.5-flash"
# GEMINI_MODEL = "gemini-1.5-pro"

# 每分钟请求限制
AI_RATE_LIMIT_PER_MINUTE = 60

# 每日请求限制
AI_DAILY_LIMIT = 1000

# 使用的Prompt模板名称（对应 ai_analysis/prompt_templates/ 目录下的文件）
PROMPT_TEMPLATE = "default"

# 是否从checkpoint恢复（用于断点续传）
RESUME_FROM_CHECKPOINT = True

# Checkpoint保存间隔（每处理N个职位保存一次）
CHECKPOINT_INTERVAL = 10

# =============================================================================
# 实时AI分析配置（边爬边分析）
# =============================================================================

# 是否启用实时AI分析（边爬取边分析，而不是爬完再分析）
# 优势：
# - 减少内存占用（流式处理）
# - 中断损失更小（每批保存检查点）
# - 可以实时看到分析结果
# - 充分利用爬虫的等待时间
ENABLE_REALTIME_AI = True

# 每批分析的职位数（累积到这个数量后立即进行AI分析）
# 建议值：5-10，太小会增加检查点开销，太大会增加中断损失
AI_BATCH_SIZE = 5

# 实时分析检查点保存间隔（每处理N批保存一次）
REALTIME_CHECKPOINT_INTERVAL = 1

# =============================================================================
# 地区配置
# =============================================================================

# 地区到Indeed国家代码的映射
REGION_COUNTRY_MAP = {
    "United States": "usa",
    "United Kingdom": "uk",
    "Australia": "australia",
    "Singapore": "singapore",
    "Hong Kong": "hong kong",
    "Canada": "canada",
}

# 地区到默认货币的映射
REGION_CURRENCY_MAP = {
    "United States": "USD",
    "United Kingdom": "GBP",
    "Australia": "AUD",
    "Singapore": "SGD",
    "Hong Kong": "HKD",
    "Canada": "CAD",
}

# =============================================================================
# 输出配置
# =============================================================================

# Excel输出列（按顺序）
OUTPUT_FIELDS = [
    "Job Title",
    "Company Name",
    "Requirements",
    "Location",
    "Salary Range",
    "Estimated Annual Salary",
    "Estimated Annual Salary (USD)",
    "Job Description",
    "Company Size",
    "Posted Date",
    "Job Status",
    "Platform",
    "Job Link",
]

# AI分析结果中要包含在输出中的字段
AI_ANALYSIS_FIELDS = [
    "job_category",
    "seniority_level",
    "required_skills",
    "remote_policy",
    "is_chinese_company_overseas",  # 是否是中国企业出海
]

# =============================================================================
# 地点配置
# =============================================================================

def get_locations_for_region(region_name: str) -> list:
    """
    获取指定地区的搜索地点列表。
    优先从 locations_config.py 加载，否则使用默认值。
    """
    try:
        from locations_config import LOCATIONS_BY_REGION

        if region_name in LOCATIONS_BY_REGION:
            locations = []
            for state, locs in LOCATIONS_BY_REGION[region_name].items():
                locations.extend(locs)
            return locations
    except ImportError:
        pass

    # 默认地点列表
    fallback = {
        "United States": [
            "San Francisco, CA",
            "New York, NY",
            "Seattle, WA",
            "Austin, TX",
            "Boston, MA",
            "Los Angeles, CA",
        ],
        "United Kingdom": [
            "London, England, United Kingdom",
            "Manchester, England, United Kingdom",
            "Cambridge, England, United Kingdom",
        ],
        "Australia": [
            "Sydney, New South Wales, Australia",
            "Melbourne, Victoria, Australia",
        ],
        "Singapore": ["Singapore"],
        "Hong Kong": ["Hong Kong"],
    }

    return fallback.get(region_name, [region_name])


# =============================================================================
# 辅助函数
# =============================================================================

def get_effective_config():
    """
    获取生效的配置（考虑测试模式）。
    返回一个字典包含所有运行时需要的配置值。
    """
    if TEST_MODE:
        return {
            "results_per_search": TEST_RESULTS_PER_SEARCH,
            "max_total_jobs": TEST_MAX_JOBS,
            "keywords": KEYWORDS[:TEST_KEYWORDS_LIMIT],
            "locations": get_locations_for_region(DEFAULT_REGION)[:TEST_LOCATIONS_LIMIT],
        }
    else:
        return {
            "results_per_search": RESULTS_PER_SEARCH,
            "max_total_jobs": MAX_TOTAL_JOBS,
            "keywords": KEYWORDS,
            "locations": get_locations_for_region(DEFAULT_REGION),
        }


def validate_config() -> list:
    """
    验证配置并返回警告列表。
    """
    warnings = []

    if ENABLE_AI_ANALYSIS and not GEMINI_API_KEY:
        warnings.append("GEMINI_API_KEY 未设置 - AI分析将被禁用")

    if not KEYWORDS:
        warnings.append("未配置搜索关键词")

    if not PLATFORMS:
        warnings.append("未配置爬取平台")

    return warnings


def print_config():
    """打印当前配置信息。"""
    effective = get_effective_config()

    print("=" * 60)
    print("JobScrapper 统一配置")
    print("=" * 60)
    print(f"  配置文件: test_jobspy/config_unified.py")
    print("-" * 60)
    print(f"  运行ID: {RUN_ID}")
    print(f"  输出目录: {OUTPUT_DIR}")
    print(f"  测试模式: {'是' if TEST_MODE else '否'}")
    print("-" * 60)
    print(f"  多地区模式: {'是' if ENABLE_MULTI_REGION else '否'}")
    if ENABLE_MULTI_REGION:
        print(f"  爬取地区: {', '.join(REGIONS)}")
    else:
        print(f"  目标地区: {DEFAULT_REGION}")
    print(f"  爬取平台: {', '.join(PLATFORMS)}")
    print(f"  搜索关键词数: {len(effective['keywords'])}")
    print(f"  每次搜索结果数: {effective['results_per_search']}")
    print(f"  最大职位数/地区: {effective['max_total_jobs'] or '无限制'}")
    print("-" * 60)
    print(f"  启用AI分析: {'是' if ENABLE_AI_ANALYSIS else '否'}")
    if ENABLE_AI_ANALYSIS:
        print(f"  AI模型: {GEMINI_MODEL}")
        print(f"  Prompt模板: {PROMPT_TEMPLATE}")
        print(f"  每分钟限制: {AI_RATE_LIMIT_PER_MINUTE}")
        print(f"  每日限制: {AI_DAILY_LIMIT}")
        print(f"  断点续传: {'是' if RESUME_FROM_CHECKPOINT else '否'}")
        print(f"  实时分析模式: {'是' if ENABLE_REALTIME_AI else '否'}")
        if ENABLE_REALTIME_AI:
            print(f"  批处理大小: {AI_BATCH_SIZE}")
            print(f"  检查点间隔: 每 {REALTIME_CHECKPOINT_INTERVAL} 批")

    warnings = validate_config()
    if warnings:
        print("-" * 60)
        print("警告:")
        for w in warnings:
            print(f"  ⚠ {w}")

    print("=" * 60)
