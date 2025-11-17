#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试数据库表 - 为每个国家表插入3行测试数据
"""
import os
import sys
import io
from dotenv import load_dotenv
from datetime import datetime

# Set UTF-8 encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()

try:
    from supabase import create_client
    from supabase_storage import init_supabase, prepare_job_data
except ImportError as e:
    print(f"ERROR: Failed to import required modules: {str(e)}")
    print("Please install: pip install supabase")
    sys.exit(1)

# Test data for each country
test_data = {
    "us": [
        {
            "职位名称": "Senior AI Engineer",
            "公司名称": "Tech Corp USA",
            "地点": "San Francisco, CA",
            "工作描述": "We are looking for a senior AI engineer to join our team.",
            "专业要求": "5+ years of experience in machine learning",
            "薪资要求": "$150,000 - $200,000 (年薪)",
            "年薪预估值": "$175000",
            "团队规模/业务线规模": "",
            "公司规模": "1000",
            "职位发布时间": "2024-01-15",
            "职位状态": "Active",
            "招聘平台": "LinkedIn",
            "职位链接": "https://www.linkedin.com/jobs/view/test-us-1",
        },
        {
            "职位名称": "Machine Learning Scientist",
            "公司名称": "AI Innovations Inc",
            "地点": "New York, NY",
            "工作描述": "Join our ML research team to develop cutting-edge AI solutions.",
            "专业要求": "PhD in Computer Science or related field",
            "薪资要求": "$180,000 - $220,000 (年薪)",
            "年薪预估值": "$200000",
            "团队规模/业务线规模": "",
            "公司规模": "500",
            "职位发布时间": "2024-01-16",
            "职位状态": "Active",
            "招聘平台": "LinkedIn",
            "职位链接": "https://www.linkedin.com/jobs/view/test-us-2",
        },
        {
            "职位名称": "Data Scientist - AI Team",
            "公司名称": "Data Analytics Co",
            "地点": "Seattle, WA",
            "工作描述": "Work on AI-powered analytics platforms.",
            "专业要求": "3+ years in data science, Python, TensorFlow",
            "薪资要求": "$130,000 - $160,000 (年薪)",
            "年薪预估值": "$145000",
            "团队规模/业务线规模": "",
            "公司规模": "200",
            "职位发布时间": "2024-01-17",
            "职位状态": "Active",
            "招聘平台": "LinkedIn",
            "职位链接": "https://www.linkedin.com/jobs/view/test-us-3",
        },
    ],
    "uk": [
        {
            "职位名称": "AI Research Engineer",
            "公司名称": "London Tech Solutions",
            "地点": "London, England, United Kingdom",
            "工作描述": "Leading AI research position in London.",
            "专业要求": "MSc or PhD in AI/ML, 3+ years experience",
            "薪资要求": "£80,000 - £100,000 (年薪)",
            "年薪预估值": "£90000",
            "团队规模/业务线规模": "",
            "公司规模": "800",
            "职位发布时间": "2024-01-15",
            "职位状态": "Active",
            "招聘平台": "LinkedIn",
            "职位链接": "https://www.linkedin.com/jobs/view/test-uk-1",
        },
        {
            "职位名称": "Senior ML Engineer",
            "公司名称": "Edinburgh AI Labs",
            "地点": "Edinburgh, Scotland, United Kingdom",
            "工作描述": "Develop machine learning models for production systems.",
            "专业要求": "5+ years ML engineering, Python, PyTorch",
            "薪资要求": "£70,000 - £90,000 (年薪)",
            "年薪预估值": "£80000",
            "团队规模/业务线规模": "",
            "公司规模": "300",
            "职位发布时间": "2024-01-16",
            "职位状态": "Active",
            "招聘平台": "LinkedIn",
            "职位链接": "https://www.linkedin.com/jobs/view/test-uk-2",
        },
        {
            "职位名称": "AI Product Manager",
            "公司名称": "Manchester Digital",
            "地点": "Manchester, England, United Kingdom",
            "工作描述": "Lead AI product development initiatives.",
            "专业要求": "Product management experience, AI/ML knowledge",
            "薪资要求": "£60,000 - £75,000 (年薪)",
            "年薪预估值": "£67500",
            "团队规模/业务线规模": "",
            "公司规模": "150",
            "职位发布时间": "2024-01-17",
            "职位状态": "Active",
            "招聘平台": "LinkedIn",
            "职位链接": "https://www.linkedin.com/jobs/view/test-uk-3",
        },
    ],
    "ca": [
        {
            "职位名称": "AI Software Engineer",
            "公司名称": "Toronto Tech Hub",
            "地点": "Toronto, Ontario, Canada",
            "工作描述": "Build AI-powered software solutions in Toronto.",
            "专业要求": "4+ years software engineering, AI/ML experience",
            "薪资要求": "CAD $120,000 - $150,000 (年薪)",
            "年薪预估值": "CAD $135000",
            "团队规模/业务线规模": "",
            "公司规模": "600",
            "职位发布时间": "2024-01-15",
            "职位状态": "Active",
            "招聘平台": "LinkedIn",
            "职位链接": "https://www.linkedin.com/jobs/view/test-ca-1",
        },
        {
            "职位名称": "Deep Learning Researcher",
            "公司名称": "Vancouver AI Research",
            "地点": "Vancouver, British Columbia, Canada",
            "工作描述": "Research position in deep learning and neural networks.",
            "专业要求": "PhD in AI/ML, publications in top conferences",
            "薪资要求": "CAD $140,000 - $170,000 (年薪)",
            "年薪预估值": "CAD $155000",
            "团队规模/业务线规模": "",
            "公司规模": "250",
            "职位发布时间": "2024-01-16",
            "职位状态": "Active",
            "招聘平台": "LinkedIn",
            "职位链接": "https://www.linkedin.com/jobs/view/test-ca-2",
        },
        {
            "职位名称": "ML Engineer - Montreal",
            "公司名称": "Quebec AI Solutions",
            "地点": "Montreal, Quebec, Canada",
            "工作描述": "Machine learning engineering role in Montreal.",
            "专业要求": "3+ years ML engineering, French/English bilingual",
            "薪资要求": "CAD $110,000 - $135,000 (年薪)",
            "年薪预估值": "CAD $122500",
            "团队规模/业务线规模": "",
            "公司规模": "400",
            "职位发布时间": "2024-01-17",
            "职位状态": "Active",
            "招聘平台": "LinkedIn",
            "职位链接": "https://www.linkedin.com/jobs/view/test-ca-3",
        },
    ],
    "sg": [
        {
            "职位名称": "AI Engineer - Singapore",
            "公司名称": "Singapore Tech Innovations",
            "地点": "Singapore, Singapore",
            "工作描述": "AI engineering role in Singapore's tech hub.",
            "专业要求": "3+ years AI/ML experience, Python, TensorFlow",
            "薪资要求": "SGD $90,000 - $120,000 (年薪)",
            "年薪预估值": "SGD $105000",
            "团队规模/业务线规模": "",
            "公司规模": "500",
            "职位发布时间": "2024-01-15",
            "职位状态": "Active",
            "招聘平台": "LinkedIn",
            "职位链接": "https://www.linkedin.com/jobs/view/test-sg-1",
        },
        {
            "职位名称": "Senior Data Scientist",
            "公司名称": "Singapore Analytics Co",
            "地点": "Singapore, Singapore",
            "工作描述": "Lead data science initiatives in Singapore.",
            "专业要求": "5+ years data science, ML expertise",
            "薪资要求": "SGD $100,000 - $130,000 (年薪)",
            "年薪预估值": "SGD $115000",
            "团队规模/业务线规模": "",
            "公司规模": "300",
            "职位发布时间": "2024-01-16",
            "职位状态": "Active",
            "招聘平台": "LinkedIn",
            "职位链接": "https://www.linkedin.com/jobs/view/test-sg-2",
        },
        {
            "职位名称": "ML Research Scientist",
            "公司名称": "Singapore AI Lab",
            "地点": "Singapore, Singapore",
            "工作描述": "Research position in machine learning.",
            "专业要求": "PhD in ML/AI, strong research background",
            "薪资要求": "SGD $110,000 - $140,000 (年薪)",
            "年薪预估值": "SGD $125000",
            "团队规模/业务线规模": "",
            "公司规模": "200",
            "职位发布时间": "2024-01-17",
            "职位状态": "Active",
            "招聘平台": "LinkedIn",
            "职位链接": "https://www.linkedin.com/jobs/view/test-sg-3",
        },
    ],
    "hk": [
        {
            "职位名称": "AI Engineer - Hong Kong",
            "公司名称": "Hong Kong Tech Solutions",
            "地点": "Hong Kong, Hong Kong",
            "工作描述": "AI engineering position in Hong Kong.",
            "专业要求": "3+ years AI/ML, Python, PyTorch",
            "薪资要求": "HKD $600,000 - $800,000 (年薪)",
            "年薪预估值": "HKD $700000",
            "团队规模/业务线规模": "",
            "公司规模": "400",
            "职位发布时间": "2024-01-15",
            "职位状态": "Active",
            "招聘平台": "LinkedIn",
            "职位链接": "https://www.linkedin.com/jobs/view/test-hk-1",
        },
        {
            "职位名称": "Senior ML Engineer",
            "公司名称": "Hong Kong AI Innovations",
            "地点": "Hong Kong, Hong Kong",
            "工作描述": "Senior machine learning engineering role.",
            "专业要求": "5+ years ML engineering, production systems",
            "薪资要求": "HKD $700,000 - $900,000 (年薪)",
            "年薪预估值": "HKD $800000",
            "团队规模/业务线规模": "",
            "公司规模": "250",
            "职位发布时间": "2024-01-16",
            "职位状态": "Active",
            "招聘平台": "LinkedIn",
            "职位链接": "https://www.linkedin.com/jobs/view/test-hk-2",
        },
        {
            "职位名称": "Data Scientist - AI Team",
            "公司名称": "Hong Kong Analytics Hub",
            "地点": "Hong Kong, Hong Kong",
            "工作描述": "Data science role focusing on AI applications.",
            "专业要求": "4+ years data science, ML models",
            "薪资要求": "HKD $550,000 - $700,000 (年薪)",
            "年薪预估值": "HKD $625000",
            "团队规模/业务线规模": "",
            "公司规模": "350",
            "职位发布时间": "2024-01-17",
            "职位状态": "Active",
            "招聘平台": "LinkedIn",
            "职位链接": "https://www.linkedin.com/jobs/view/test-hk-3",
        },
    ],
}

def main():
    print("=" * 60)
    print("Database Tables Test - Inserting Test Data")
    print("=" * 60)
    
    # Initialize Supabase
    try:
        init_supabase()
        print("\n✓ Supabase initialized successfully")
    except Exception as e:
        print(f"\n✗ Failed to initialize Supabase: {str(e)}")
        return
    
    # Table mapping
    table_map = {
        "us": "jobs",
        "uk": "jobs_uk",
        "ca": "jobs_ca",
        "sg": "jobs_sg",
        "hk": "jobs_hk",
    }
    
    country_names = {
        "us": "美国 (USA)",
        "uk": "英国 (UK)",
        "ca": "加拿大 (Canada)",
        "sg": "新加坡 (Singapore)",
        "hk": "香港 (Hong Kong)",
    }
    
    # Get Supabase client
    from supabase_storage import supabase
    if not supabase:
        print("✗ Supabase client not available")
        return
    
    total_inserted = 0
    total_failed = 0
    
    # Insert data for each country
    for country_code, table_name in table_map.items():
        print(f"\n[{country_names[country_code]}] Inserting into table: {table_name}")
        
        country_data = test_data.get(country_code, [])
        if not country_data:
            print(f"  ⚠ No test data for {country_code}")
            continue
        
        country_inserted = 0
        country_failed = 0
        
        for i, job in enumerate(country_data, 1):
            try:
                # Prepare job data
                job_data = prepare_job_data(job)
                
                # Insert into database
                result = supabase.table(table_name).upsert(
                    job_data,
                    on_conflict="job_title,company_name"
                ).execute()
                
                print(f"  ✓ Inserted job {i}: {job['职位名称']} at {job['公司名称']}")
                country_inserted += 1
                total_inserted += 1
                
            except Exception as e:
                print(f"  ✗ Failed to insert job {i}: {str(e)}")
                country_failed += 1
                total_failed += 1
        
        print(f"  Summary: {country_inserted} inserted, {country_failed} failed")
    
    # Verify data
    print("\n" + "=" * 60)
    print("Verification - Checking record counts:")
    print("=" * 60)
    
    for country_code, table_name in table_map.items():
        try:
            result = supabase.table(table_name).select("id", count="exact").execute()
            count = result.count if hasattr(result, 'count') else (len(result.data) if result.data else 0)
            print(f"  {country_names[country_code]} ({table_name}): {count} records")
        except Exception as e:
            print(f"  {country_names[country_code]} ({table_name}): Error - {str(e)}")
    
    # Final summary
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)
    print(f"Total inserted: {total_inserted}")
    print(f"Total failed: {total_failed}")
    print("\nNote: If records already exist (same job_title + company_name),")
    print("      they will be updated instead of creating duplicates.")

if __name__ == "__main__":
    main()

