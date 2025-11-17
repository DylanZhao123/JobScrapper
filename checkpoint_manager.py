# -*- coding: utf-8 -*-
"""
Checkpoint管理器
支持程序中断后从断点恢复
支持国家特定的checkpoint路径
"""
import json
import os
from datetime import datetime
from config import OUTPUT_DIR, CACHE_FILE

# Default paths (can be overridden for country-specific paths)
_checkpoint_file = None
_stage1_raw_data = None
_stage1_unique_data = None
_stage2_detail_data = None

def set_country_paths(country_dir):
    """设置国家特定的路径"""
    global _checkpoint_file, _stage1_raw_data, _stage1_unique_data, _stage2_detail_data
    _checkpoint_file = f"{country_dir}/checkpoint.json"
    _stage1_raw_data = f"{country_dir}/stage1_raw_data.json"
    _stage1_unique_data = f"{country_dir}/stage1_unique_data.json"
    _stage2_detail_data = f"{country_dir}/stage2_detail_data.json"

def reset_paths():
    """重置为默认路径"""
    global _checkpoint_file, _stage1_raw_data, _stage1_unique_data, _stage2_detail_data
    _checkpoint_file = None
    _stage1_raw_data = None
    _stage1_unique_data = None
    _stage2_detail_data = None

def get_checkpoint_file():
    """获取checkpoint文件路径"""
    return _checkpoint_file if _checkpoint_file else f"{OUTPUT_DIR}/checkpoint.json"

def get_stage1_raw_file():
    """获取阶段1原始数据文件路径"""
    return _stage1_raw_data if _stage1_raw_data else f"{OUTPUT_DIR}/stage1_raw_data.json"

def get_stage1_unique_file():
    """获取阶段1去重数据文件路径"""
    return _stage1_unique_data if _stage1_unique_data else f"{OUTPUT_DIR}/stage1_unique_data.json"

def get_stage2_detail_file():
    """获取阶段2详情数据文件路径"""
    return _stage2_detail_data if _stage2_detail_data else f"{OUTPUT_DIR}/stage2_detail_data.json"

# For backward compatibility
CHECKPOINT_FILE = f"{OUTPUT_DIR}/checkpoint.json"
STAGE1_RAW_DATA = f"{OUTPUT_DIR}/stage1_raw_data.json"
STAGE1_UNIQUE_DATA = f"{OUTPUT_DIR}/stage1_unique_data.json"
STAGE2_DETAIL_DATA = f"{OUTPUT_DIR}/stage2_detail_data.json"


def load_checkpoint():
    """加载checkpoint"""
    try:
        checkpoint_file = get_checkpoint_file()
        if os.path.exists(checkpoint_file):
            with open(checkpoint_file, "r", encoding="utf-8") as f:
                return json.load(f)
    except:
        pass
    return None


def save_checkpoint(stage, **kwargs):
    """保存checkpoint"""
    checkpoint = {
        "stage": stage,
        "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        **kwargs
    }
    checkpoint_file = get_checkpoint_file()
    os.makedirs(os.path.dirname(checkpoint_file), exist_ok=True)
    with open(checkpoint_file, "w", encoding="utf-8") as f:
        json.dump(checkpoint, f, indent=2, ensure_ascii=False)


def load_stage1_raw_data():
    """加载阶段1的原始数据"""
    try:
        stage1_file = get_stage1_raw_file()
        if os.path.exists(stage1_file):
            with open(stage1_file, "r", encoding="utf-8") as f:
                return json.load(f)
    except:
        pass
    return []


def save_stage1_raw_data(data):
    """保存阶段1的原始数据"""
    stage1_file = get_stage1_raw_file()
    os.makedirs(os.path.dirname(stage1_file), exist_ok=True)
    with open(stage1_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_stage1_unique_data():
    """加载阶段1去重后的数据"""
    try:
        stage1_unique_file = get_stage1_unique_file()
        if os.path.exists(stage1_unique_file):
            with open(stage1_unique_file, "r", encoding="utf-8") as f:
                return json.load(f)
    except:
        pass
    return None


def save_stage1_unique_data(data):
    """保存阶段1去重后的数据"""
    stage1_unique_file = get_stage1_unique_file()
    os.makedirs(os.path.dirname(stage1_unique_file), exist_ok=True)
    with open(stage1_unique_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_stage2_detail_data():
    """加载阶段2的详情数据"""
    try:
        stage2_file = get_stage2_detail_file()
        if os.path.exists(stage2_file):
            with open(stage2_file, "r", encoding="utf-8") as f:
                return json.load(f)
    except:
        pass
    return {"jobs": [], "processed_urls": []}


def save_stage2_detail_data(data):
    """保存阶段2的详情数据"""
    stage2_file = get_stage2_detail_file()
    os.makedirs(os.path.dirname(stage2_file), exist_ok=True)
    with open(stage2_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_processed_urls():
    """获取已处理的职位链接列表"""
    detail_data = load_stage2_detail_data()
    return set(detail_data.get("processed_urls", []))


def add_processed_job(job):
    """添加已处理的职位到详情数据"""
    detail_data = load_stage2_detail_data()
    if "jobs" not in detail_data:
        detail_data["jobs"] = []
    if "processed_urls" not in detail_data:
        detail_data["processed_urls"] = []
    
    job_url = job.get("职位链接", "")
    if job_url and job_url not in detail_data["processed_urls"]:
        detail_data["jobs"].append(job)
        detail_data["processed_urls"].append(job_url)
        save_stage2_detail_data(detail_data)
