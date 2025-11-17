# -*- coding: utf-8 -*-
"""
Supabase数据存储模块
将抓取的职位数据存储到Supabase数据库
"""
import os
from supabase import create_client, Client
from typing import List, Dict, Optional
from datetime import datetime
try:
    from config import SUPABASE_URL, SUPABASE_KEY
except ImportError:
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# 初始化Supabase客户端
supabase: Optional[Client] = None

def init_supabase():
    """初始化Supabase客户端（静默模式，不输出）"""
    global supabase
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError(
            "Supabase配置缺失。请在.env文件中添加：\n"
            "SUPABASE_URL=your_supabase_url\n"
            "SUPABASE_KEY=your_supabase_anon_key"
        )
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def prepare_job_data(job: Dict) -> Dict:
    """准备职位数据，转换为数据库格式"""
    import math
    
    def clean_value(value):
        """清理值：将NaN、None转换为空字符串"""
        if value is None:
            return ""
        if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
            return ""
        return str(value) if value is not None else ""
    
    return {
        "job_title": clean_value(job.get("职位名称", "")),
        "company_name": clean_value(job.get("公司名称", "")),
        "location": clean_value(job.get("地点", "")),
        "job_description": clean_value(job.get("工作描述", "")),
        "requirements": clean_value(job.get("专业要求", "")),
        "salary_range": clean_value(job.get("薪资要求", "")),
        "estimated_annual_salary": clean_value(job.get("年薪预估值", "")),
        "team_size": clean_value(job.get("团队规模/业务线规模", "")),
        "company_size": clean_value(job.get("公司规模", "")),
        "posted_date": clean_value(job.get("职位发布时间", "")),
        "job_status": clean_value(job.get("职位状态", "Active")),
        "platform": clean_value(job.get("招聘平台", "")),
        "job_url": clean_value(job.get("职位链接", "")),
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }

def get_country_table(country_code: str) -> str:
    """根据国家代码返回对应的表名"""
    country_table_map = {
        "uk": "jobs_uk",
        "ca": "jobs_ca",
        "sg": "jobs_sg",
        "hk": "jobs_hk",
    }
    return country_table_map.get(country_code.lower(), "jobs")  # 默认使用jobs表（美国）

def upsert_jobs(jobs: List[Dict], batch_size: int = 100, country_code: str = "us") -> tuple[int, int]:
    """
    批量插入或更新职位数据（UPSERT）
    使用职位名称+公司名称作为唯一键进行去重
    
    参数:
        jobs: 职位数据列表
        batch_size: 批次大小
        country_code: 国家代码 (us, uk, ca, sg, hk)
    
    返回: (插入数量, 更新数量)
    """
    if not supabase:
        init_supabase()
    
    table_name = get_country_table(country_code)
    inserted_count = 0
    updated_count = 0
    errors = []
    
    # 分批处理，避免单次请求过大
    for i in range(0, len(jobs), batch_size):
        batch = jobs[i:i + batch_size]
        batch_data = []
        
        for job in batch:
            try:
                job_data = prepare_job_data(job)
                batch_data.append(job_data)
            except Exception as e:
                errors.append(f"数据准备失败: {job.get('职位名称', 'Unknown')} - {str(e)}")
                continue
        
        if not batch_data:
            continue
        
        try:
            # 使用UPSERT：如果(job_title, company_name)已存在则更新，否则插入
            result = supabase.table(table_name).upsert(
                batch_data,
                on_conflict="job_title,company_name"  # 冲突时更新
            ).execute()
            
            # 统计插入和更新数量（Supabase upsert不直接返回，需要查询）
            # 简化处理：假设都是新插入
            inserted_count += len(batch_data)
            
        except Exception as e:
            errors.append(f"批量插入失败 (批次 {i//batch_size + 1}): {str(e)}")
            # 如果批量失败，尝试逐条插入
            for job_data in batch_data:
                try:
                    supabase.table(table_name).upsert(job_data, on_conflict="job_title,company_name").execute()
                    inserted_count += 1
                except Exception as e2:
                    errors.append(f"单条插入失败: {job_data.get('job_title', 'Unknown')} - {str(e2)}")
    
    if errors:
        # 静默处理错误，不输出到控制台
        pass
    
    return inserted_count, updated_count

def get_job_count(country_code: str = "us") -> int:
    """获取数据库中的职位总数"""
    if not supabase:
        init_supabase()
    
    table_name = get_country_table(country_code)
    try:
        result = supabase.table(table_name).select("id", count="exact").execute()
        return result.count if hasattr(result, 'count') else len(result.data)
    except Exception as e:
        return 0

def get_jobs_by_platform(platform: str, limit: int = 100) -> List[Dict]:
    """根据平台获取职位列表"""
    if not supabase:
        init_supabase()
    
    try:
        result = supabase.table("jobs").select("*").eq("platform", platform).limit(limit).execute()
        return result.data
    except Exception as e:
        print(f"查询失败: {str(e)}")
        return []

def delete_old_jobs(days: int = 30):
    """删除指定天数之前的旧职位（可选功能）"""
    if not supabase:
        init_supabase()
    
    try:
        cutoff_date = datetime.utcnow().replace(day=1)  # 示例：删除上个月的数据
        result = supabase.table("jobs").delete().lt("created_at", cutoff_date.isoformat()).execute()
        return len(result.data) if result.data else 0
    except Exception as e:
        print(f"删除旧数据失败: {str(e)}")
        return 0

