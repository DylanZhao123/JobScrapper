# -*- coding: utf-8 -*-
"""
职位分类模块
根据职位名称自动分类职位类别
"""

def classify_job(job_title):
    """
    根据职位名称分类职位
    
    参数:
        job_title: 职位名称字符串
    
    返回:
        职位类别字符串
    """
    if not job_title:
        return "Unknown"
    
    title_lower = job_title.lower()
    
    # 优先级匹配：更具体的类别优先
    
    # Data Science相关（最优先，因为可能与AI相关职位重叠）
    if any(keyword in title_lower for keyword in [
        "data scientist", "data science", "data analyst", 
        "data engineer", "data science senior", "data science lead"
    ]):
        return "Data Science"
    
    # AI销售相关
    if any(keyword in title_lower for keyword in [
        "ai sales", "artificial intelligence sales", 
        "ai business development", "ai account manager",
        "ai sales representative", "ai sales manager"
    ]):
        return "AI Sales"
    
    # AI会话师相关
    if any(keyword in title_lower for keyword in [
        "ai conversation", "ai conversational", "ai chatbot",
        "ai dialogue", "conversational ai", "ai voice assistant",
        "chatbot designer", "conversational designer"
    ]):
        return "AI Conversation"
    
    # AI训练师相关
    if any(keyword in title_lower for keyword in [
        "ai training", "ai trainer", "ai model training",
        "ai data training", "ai training specialist",
        "machine learning trainer"
    ]):
        return "AI Training"
    
    # AI产品经理相关
    if any(keyword in title_lower for keyword in [
        "ai product manager", "ai pm", "ai product owner",
        "ai product lead", "ai product"
    ]):
        return "AI Product Manager"
    
    # AI+行业相关（需要检查是否包含行业关键词）
    industry_keywords = [
        "ai healthcare", "ai finance", "ai education", "ai retail",
        "ai manufacturing", "ai agriculture", "ai transportation",
        "ai energy", "ai legal", "ai marketing"
    ]
    if any(keyword in title_lower for keyword in industry_keywords):
        return "AI+Industry"
    
    # AI艺术相关
    if any(keyword in title_lower for keyword in [
        "ai art", "ai artist", "ai painting", "ai illustrator",
        "ai creative", "ai digital art", "ai visual artist"
    ]):
        return "AI Art"
    
    # AI设计相关
    if any(keyword in title_lower for keyword in [
        "ai design", "ai designer", "ai ux designer", "ai ui designer",
        "ai interaction designer", "ai design specialist"
    ]):
        return "AI Design"
    
    # AI架构相关
    if any(keyword in title_lower for keyword in [
        "ai architecture", "ai architect", "ai system architecture",
        "ai solution architect", "ai platform architect"
    ]):
        return "AI Architecture"
    
    # AI治理相关
    if any(keyword in title_lower for keyword in [
        "ai governance", "ai governance specialist", "ai compliance",
        "ai risk management", "ai policy"
    ]):
        return "AI Governance"
    
    # AI伦理相关
    if any(keyword in title_lower for keyword in [
        "ai ethics", "ai ethical", "ai ethics researcher",
        "responsible ai", "ai fairness", "ai bias"
    ]):
        return "AI Ethics"
    
    # AI硬件相关
    if any(keyword in title_lower for keyword in [
        "ai hardware", "ai hardware engineer", "ai chip design",
        "ai accelerator", "ai processor"
    ]):
        return "AI Hardware"
    
    # AI运维相关
    if any(keyword in title_lower for keyword in [
        "ai operations", "ai ops", "ai devops", "ai infrastructure",
        "ai mlops", "ai platform engineer", "ai systems engineer"
    ]):
        return "AI Operations"
    
    # 数据标注相关
    if any(keyword in title_lower for keyword in [
        "data annotation", "data labeling", "data annotator",
        "data tagging", "data quality", "data curation"
    ]):
        return "Data Annotation"
    
    # 机器人相关
    if any(keyword in title_lower for keyword in [
        "robotics", "robot engineer", "robotics engineer",
        "autonomous systems", "robotic process automation", "rpa"
    ]):
        return "Robotics"
    
    # 其他AI相关（包含AI但不在上述类别中）
    if "ai" in title_lower or "artificial intelligence" in title_lower:
        return "Other AI Related"
    
    # 默认类别
    return "Other"

def classify_jobs(job_list):
    """
    批量分类职位列表
    
    参数:
        job_list: 职位字典列表
    
    返回:
        添加了"职位类别"字段的职位列表
    """
    classified_jobs = []
    for job in job_list:
        job_title = job.get("职位名称", "")
        job_category = classify_job(job_title)
        
        # 创建新字典，在最前面添加职位类别
        classified_job = {"职位类别": job_category}
        classified_job.update(job)
        classified_jobs.append(classified_job)
    
    return classified_jobs

def get_category_statistics(job_list):
    """
    获取职位类别统计信息
    
    参数:
        job_list: 已分类的职位列表
    
    返回:
        类别统计字典
    """
    stats = {}
    for job in job_list:
        category = job.get("职位类别", "Unknown")
        stats[category] = stats.get(category, 0) + 1
    
    return stats

