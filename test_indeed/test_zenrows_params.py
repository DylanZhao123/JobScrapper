# -*- coding: utf-8 -*-
"""
测试ZenRows API的不同参数组合
检查是否需要特殊参数来抓取Indeed
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

def test_with_params(url, extra_params=None):
    """测试带额外参数的请求"""
    params = {
        'url': url,
        'apikey': ZENROWS_API_KEY
    }
    if extra_params:
        params.update(extra_params)
    
    print(f"\n测试URL: {url}")
    print(f"额外参数: {extra_params}")
    print(f"完整参数: {params}")
    
    try:
        r = requests.get(ZENROWS_BASE_URL, params=params, timeout=30)
        print(f"状态码: {r.status_code}")
        
        if r.status_code == 200:
            print(f"✓ 成功！HTML长度: {len(r.text)}")
            print(f"HTML前300字符:\n{r.text[:300]}")
            return r.text
        else:
            print(f"✗ 失败，状态码: {r.status_code}")
            print(f"响应内容: {r.text[:500]}")
            return None
    except Exception as e:
        print(f"✗ 异常: {str(e)}")
        return None

def main():
    """测试不同的参数组合"""
    test_url = "https://www.indeed.com/jobs?q=AI+Engineer&l=United+States"
    
    print("="*60)
    print("测试ZenRows API参数组合")
    print("="*60)
    
    # 测试1: 基础请求（无额外参数）
    print("\n测试1: 基础请求")
    test_with_params(test_url)
    time.sleep(2)
    
    # 测试2: 启用JS渲染（Indeed可能需要JS）
    print("\n测试2: 启用JS渲染")
    test_with_params(test_url, {'js_render': 'true'})
    time.sleep(2)
    
    # 测试3: 使用代理
    print("\n测试3: 使用代理")
    test_with_params(test_url, {'proxy': 'true'})
    time.sleep(2)
    
    # 测试4: 简化URL（测试基础页面是否可访问）
    print("\n测试4: 测试Indeed基础页面")
    simple_url = "https://www.indeed.com"
    test_with_params(simple_url)
    time.sleep(2)
    
    # 测试5: 测试LinkedIn（对比，确认API是否工作）
    print("\n测试5: 对比测试LinkedIn（确认API是否正常）")
    linkedin_url = "https://www.linkedin.com/jobs/search?keywords=AI+Engineer&location=United+States"
    test_with_params(linkedin_url)
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)

if __name__ == "__main__":
    main()

