# -*- coding: utf-8 -*-
"""
单次请求测试 - 最小化API消耗
"""
import requests
import urllib.parse
import sys
import os

# 添加父目录到路径
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)
os.chdir(parent_dir)

from config import ZENROWS_API_KEY, ZENROWS_BASE_URL, LOCATION

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def test_single_request():
    """测试单个Indeed请求"""
    
    keyword = "AI Engineer"
    
    # 使用正确的URL编码
    query_params = {
        'q': keyword,
        'l': LOCATION,
        'start': '0'
    }
    base_url = "https://www.indeed.com/jobs"
    target_url = f"{base_url}?{urllib.parse.urlencode(query_params)}"
    
    print("="*60)
    print("单次Indeed请求测试")
    print("="*60)
    print(f"关键词: {keyword}")
    print(f"地点: {LOCATION}")
    print(f"目标URL: {target_url}")
    print()
    
    # 方法1: 带JS渲染和高级代理
    print("方法1: 带JS渲染和高级代理")
    params1 = {
        'url': target_url,
        'apikey': ZENROWS_API_KEY,
        'js_render': 'true',
        'premium_proxy': 'true',
    }
    
    try:
        r1 = requests.get(ZENROWS_BASE_URL, params=params1, timeout=30)
        print(f"状态码: {r1.status_code}")
        if r1.status_code == 200:
            print(f"✓ 成功！HTML长度: {len(r1.text)}")
            print(f"HTML前500字符:\n{r1.text[:500]}")
            return True
        elif r1.status_code == 400:
            print(f"✗ 400错误")
            print(f"错误响应: {r1.text[:500]}")
            print("\n尝试方法2...")
        else:
            print(f"✗ 失败，状态码: {r1.status_code}")
            print(f"响应: {r1.text[:200]}")
    except Exception as e:
        print(f"✗ 异常: {str(e)}")
        print("\n尝试方法2...")
    
    print()
    
    # 方法2: 简化参数（如果方法1失败）
    print("方法2: 简化参数")
    params2 = {
        'url': target_url,
        'apikey': ZENROWS_API_KEY,
    }
    
    try:
        r2 = requests.get(ZENROWS_BASE_URL, params=params2, timeout=30)
        print(f"状态码: {r2.status_code}")
        if r2.status_code == 200:
            print(f"✓ 成功！HTML长度: {len(r2.text)}")
            print(f"HTML前500字符:\n{r2.text[:500]}")
            return True
        else:
            print(f"✗ 失败，状态码: {r2.status_code}")
            print(f"响应: {r2.text[:500]}")
    except Exception as e:
        print(f"✗ 异常: {str(e)}")
    
    return False

if __name__ == "__main__":
    success = test_single_request()
    if success:
        print("\n✓ 测试成功！可以继续使用Indeed抓取器")
    else:
        print("\n✗ 测试失败，需要进一步调试")

