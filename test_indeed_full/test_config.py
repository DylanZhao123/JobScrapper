# -*- coding: utf-8 -*-
"""
Indeed完整爬取测试 - 配置文件
"""
import os

# ZenRows API配置
ZENROWS_API_KEY = "08c8d8cd14d834b61c2f05db07e7a52c5f99955c"
ZENROWS_BASE_URL = "https://api.zenrows.com/v1/"

# 测试参数
TEST_KEYWORDS = ["AI Engineer", "Machine Learning"]  # 先用2个关键词测试
TEST_LOCATION = "United States"
TEST_MAX_PAGES = 3  # 每个关键词抓取3页
TEST_LIST_LIMIT = 50  # 列表页最多抓取50条
TEST_DETAIL_LIMIT = 10  # 详情页测试10条
REQUEST_DELAY = 1  # 请求延迟（秒）

# 输出路径
TEST_OUTPUT_DIR = "test_indeed_full/outputs"
TEST_CACHE_FILE = f"{TEST_OUTPUT_DIR}/company_cache.json"
TEST_LIST_REPORT = f"{TEST_OUTPUT_DIR}/test_stage1_list.xlsx"
TEST_DETAIL_REPORT = f"{TEST_OUTPUT_DIR}/test_stage2_detail.xlsx"

# 字段顺序（与主程序保持一致）
FIELDS = [
    "职位名称", "公司名称", "专业要求", "地点",
    "薪资要求", "年薪预估值", "工作描述",
    "团队规模/业务线规模", "公司规模",
    "职位发布时间", "职位状态",
    "招聘平台", "职位链接"
]

# 确保输出目录存在
os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)

