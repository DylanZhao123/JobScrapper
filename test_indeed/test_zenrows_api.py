# -*- coding: utf-8 -*-
"""
测试ZenRows API调用方式
检查API参数和URL编码
"""
import requests
import urllib.parse
import sys
import os

# 添加父目录到路径
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)
os.chdir(parent_dir)

from config import ZENROWS_API_KEY, ZENROWS_BASE_URL

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def test_zenrows_api():
    """测试ZenRows API的不同调用方式"""
    
    # 测试URL
    test_url = "https://www.indeed.com/jobs?q=AI+Engineer&l=United+States"
    
    print("="*60)
    print("测试ZenRows API调用")
    print("="*60)
    print(f"目标URL: {test_url}")
    print(f"ZenRows Base URL: {ZENROWS_BASE_URL}")
    print(f"API Key: {ZENROWS_API_KEY[:10]}...")
    print()
    
    # 方法1: 直接传参（当前方式）
    print("方法1: 直接传参")
    try:
        params = {
            'url': test_url,
            'apikey': ZENROWS_API_KEY
        }
        print(f"参数: {params}")
        r = requests.get(ZENROWS_BASE_URL, params=params, timeout=30)
        print(f"状态码: {r.status_code}")
        if r.status_code == 200:
            print(f"✓ 成功，HTML长度: {len(r.text)}")
        else:
            print(f"✗ 失败，响应: {r.text[:200]}")
    except Exception as e:
        print(f"✗ 异常: {str(e)}")
    
    print()
    
    # 方法2: URL编码
    print("方法2: URL编码")
    try:
        encoded_url = urllib.parse.quote(test_url, safe='')
        params = {
            'url': encoded_url,
            'apikey': ZENROWS_API_KEY
        }
        print(f"编码后URL: {encoded_url}")
        print(f"参数: {params}")
        r = requests.get(ZENROWS_BASE_URL, params=params, timeout=30)
        print(f"状态码: {r.status_code}")
        if r.status_code == 200:
            print(f"✓ 成功，HTML长度: {len(r.text)}")
        else:
            print(f"✗ 失败，响应: {r.text[:200]}")
    except Exception as e:
        print(f"✗ 异常: {str(e)}")
    
    print()
    
    # 方法3: 简化URL（不带查询参数）
    print("方法3: 简化URL（先测试基础页面）")
    try:
        simple_url = "https://www.indeed.com"
        params = {
            'url': simple_url,
            'apikey': ZENROWS_API_KEY
        }
        print(f"简化URL: {simple_url}")
        r = requests.get(ZENROWS_BASE_URL, params=params, timeout=30)
        print(f"状态码: {r.status_code}")
        if r.status_code == 200:
            print(f"✓ 成功，HTML长度: {len(r.text)}")
            print(f"HTML前200字符: {r.text[:200]}")
        else:
            print(f"✗ 失败，响应: {r.text[:200]}")
    except Exception as e:
        print(f"✗ 异常: {str(e)}")

if __name__ == "__main__":
    test_zenrows_api()

