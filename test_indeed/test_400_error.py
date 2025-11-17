# -*- coding: utf-8 -*-
"""
专门测试400错误
检查URL格式和参数问题
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

def test_url_variations():
    """测试不同的URL格式"""
    
    base_url = ZENROWS_BASE_URL
    api_key = ZENROWS_API_KEY
    
    # 测试不同的URL格式
    test_cases = [
        {
            'name': '原始格式（带+号）',
            'url': 'https://www.indeed.com/jobs?q=AI+Engineer&l=United+States&start=0'
        },
        {
            'name': 'URL编码格式',
            'url': urllib.parse.quote('https://www.indeed.com/jobs?q=AI+Engineer&l=United+States&start=0', safe='')
        },
        {
            'name': '空格用%20',
            'url': 'https://www.indeed.com/jobs?q=AI%20Engineer&l=United%20States&start=0'
        },
        {
            'name': '简化搜索（无地点）',
            'url': 'https://www.indeed.com/jobs?q=AI+Engineer&start=0'
        },
        {
            'name': '最简格式',
            'url': 'https://www.indeed.com/jobs?q=AI+Engineer'
        },
    ]
    
    print("="*60)
    print("测试Indeed URL格式（针对400错误）")
    print("="*60)
    print(f"ZenRows Base URL: {base_url}")
    print(f"API Key: {api_key[:15]}...\n")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"测试 {i}: {test_case['name']}")
        print(f"{'='*60}")
        print(f"URL: {test_case['url']}")
        
        try:
            params = {
                'url': test_case['url'],
                'apikey': api_key
            }
            
            print(f"发送请求...")
            r = requests.get(base_url, params=params, timeout=30)
            
            print(f"状态码: {r.status_code}")
            print(f"响应头: {dict(r.headers)}")
            
            if r.status_code == 200:
                print(f"✓ 成功！HTML长度: {len(r.text)}")
                # 检查是否包含职位信息
                if 'job' in r.text.lower()[:1000] or 'indeed' in r.text.lower()[:1000]:
                    print("✓ HTML内容看起来正常（包含job或indeed关键词）")
                    print(f"HTML前500字符:\n{r.text[:500]}")
                else:
                    print("⚠ HTML内容可能异常")
                    print(f"HTML前500字符:\n{r.text[:500]}")
            elif r.status_code == 400:
                print(f"✗ 400错误 - 请求格式问题")
                print(f"响应内容: {r.text[:500]}")
                # 尝试解析错误信息
                try:
                    error_json = r.json()
                    print(f"错误详情: {error_json}")
                except:
                    pass
            else:
                print(f"✗ 失败，状态码: {r.status_code}")
                print(f"响应内容: {r.text[:500]}")
                
        except requests.exceptions.ConnectionError as e:
            print(f"✗ 连接错误: {str(e)}")
            print("（可能是网络问题，跳过此测试）")
        except Exception as e:
            print(f"✗ 异常: {str(e)}")
            import traceback
            traceback.print_exc()
        
        # 只测试第一个，避免浪费API
        if i == 1:
            print("\n[仅测试第一个URL格式，避免浪费API]")
            break
        
        import time
        time.sleep(1)

if __name__ == "__main__":
    test_url_variations()

