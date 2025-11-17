# -*- coding: utf-8 -*-
"""
Indeed基础抓取测试
测试最基础的URL和HTML获取
"""
import requests
import time
import sys
import os

# 添加父目录到路径
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)
os.chdir(parent_dir)

from config import ZENROWS_API_KEY, ZENROWS_BASE_URL

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def zenrows_get(url, retries=1, delay=1):
    """简化的ZenRows请求，用于测试"""
    print(f"\n测试URL: {url}")
    print(f"ZenRows API Key: {ZENROWS_API_KEY[:10]}...")
    
    for attempt in range(retries):
        try:
            params = {
                'url': url,
                'apikey': ZENROWS_API_KEY
            }
            print(f"请求参数: {params}")
            
            r = requests.get(ZENROWS_BASE_URL, params=params, timeout=30)
            print(f"状态码: {r.status_code}")
            print(f"响应头: {dict(r.headers)}")
            
            if r.status_code == 200:
                print(f"✓ 成功获取HTML，长度: {len(r.text)} 字符")
                print(f"HTML前500字符: {r.text[:500]}")
                return r.text
            else:
                print(f"✗ 请求失败[{r.status_code}]")
                print(f"响应内容: {r.text[:500]}")
        except Exception as e:
            print(f"✗ 请求异常: {str(e)}")
            import traceback
            traceback.print_exc()
        time.sleep(delay)
    return None

def test_basic_urls():
    """测试不同的Indeed URL格式"""
    test_urls = [
        # 格式1: 基础搜索
        "https://www.indeed.com/jobs?q=AI+Engineer&l=United+States",
        # 格式2: 带start参数
        "https://www.indeed.com/jobs?q=AI+Engineer&l=United+States&start=0",
        # 格式3: 编码后的URL
        "https://www.indeed.com/jobs?q=AI%20Engineer&l=United%20States",
        # 格式4: 简化搜索（无地点）
        "https://www.indeed.com/jobs?q=AI+Engineer",
    ]
    
    print("="*60)
    print("开始测试Indeed基础URL抓取")
    print("="*60)
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n{'='*60}")
        print(f"测试 {i}/{len(test_urls)}")
        print(f"{'='*60}")
        
        html = zenrows_get(url, retries=1, delay=1)
        
        if html:
            print(f"✓ 测试 {i} 成功")
            # 检查是否包含职位信息
            if 'job' in html.lower() or 'indeed' in html.lower():
                print("✓ HTML内容看起来正常")
            else:
                print("⚠ HTML内容可能异常")
        else:
            print(f"✗ 测试 {i} 失败")
        
        # 只测试第一个URL，避免浪费API
        if i == 1:
            print("\n[仅测试第一个URL，避免浪费API]")
            break
        
        time.sleep(2)

if __name__ == "__main__":
    test_basic_urls()

