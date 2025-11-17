# -*- coding: utf-8 -*-
"""
测试ZenRows API的不同调用方法
找到最适合Indeed的API参数组合
"""
import requests
import time
import json
import sys
from test_config import ZENROWS_API_KEY, ZENROWS_BASE_URL

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

def test_api_method(url, method_name, params):
    """测试一种API调用方法"""
    print(f"\n{'='*60}")
    print(f"方法: {method_name}")
    print(f"URL: {url}")
    print(f"参数: {params}")
    print(f"{'='*60}")
    
    try:
        r = requests.get(ZENROWS_BASE_URL, params=params, timeout=60)
        print(f"状态码: {r.status_code}")
        
        if r.status_code == 200:
            html = r.text
            print(f"✓ 成功！HTML长度: {len(html)} 字符")
            
            # 检查是否包含职位信息的关键词
            keywords = ['job', 'indeed', 'company', 'salary', 'location']
            found_keywords = [kw for kw in keywords if kw.lower() in html.lower()]
            print(f"包含关键词: {found_keywords}")
            
            # 检查是否包含职位卡片
            if 'data-jk' in html or 'jobTitle' in html or 'viewjob' in html:
                print("✓ 包含职位信息标记")
                return html
            else:
                print("⚠ 未找到职位信息标记")
                # 保存HTML用于分析
                with open(f"test_indeed_full/debug_{method_name.replace(' ', '_')}.html", "w", encoding="utf-8") as f:
                    f.write(html)
                print(f"已保存HTML到 debug_{method_name.replace(' ', '_')}.html")
                return html
        else:
            print(f"✗ 失败，状态码: {r.status_code}")
            print(f"响应内容: {r.text[:500]}")
            return None
    except requests.exceptions.Timeout:
        print("✗ 请求超时")
        return None
    except requests.exceptions.ConnectionError as e:
        print(f"✗ 连接错误: {str(e)}")
        return None
    except Exception as e:
        print(f"✗ 异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """测试不同的API调用方法"""
    print("="*60)
    print("ZenRows API方法测试 - Indeed")
    print("="*60)
    
    # 测试URL
    test_urls = [
        "https://www.indeed.com/jobs?q=AI+Engineer&l=United+States",
        "https://www.indeed.com/jobs?q=AI%20Engineer&l=United%20States",
    ]
    
    # 测试方法列表
    test_methods = [
        # 方法1: 基础请求
        {
            "name": "基础请求",
            "params": {
                'url': None,  # 会在循环中设置
                'apikey': ZENROWS_API_KEY
            }
        },
        # 方法2: 启用JS渲染
        {
            "name": "JS渲染",
            "params": {
                'url': None,
                'apikey': ZENROWS_API_KEY,
                'js_render': 'true'
            }
        },
        # 方法3: JS渲染 + 高级代理
        {
            "name": "JS渲染+高级代理",
            "params": {
                'url': None,
                'apikey': ZENROWS_API_KEY,
                'js_render': 'true',
                'premium_proxy': 'true'
            }
        },
        # 方法4: JS渲染 + 等待时间
        {
            "name": "JS渲染+等待",
            "params": {
                'url': None,
                'apikey': ZENROWS_API_KEY,
                'js_render': 'true',
                'js_render_wait': '3000'  # 等待3秒
            }
        },
        # 方法5: 使用代理轮换
        {
            "name": "代理轮换",
            "params": {
                'url': None,
                'apikey': ZENROWS_API_KEY,
                'proxy': 'true'
            }
        },
        # 方法6: 完整配置
        {
            "name": "完整配置",
            "params": {
                'url': None,
                'apikey': ZENROWS_API_KEY,
                'js_render': 'true',
                'premium_proxy': 'true',
                'js_render_wait': '5000',
                'wait': '2000'
            }
        },
    ]
    
    successful_methods = []
    
    for test_url in test_urls:
        print(f"\n\n{'#'*60}")
        print(f"测试URL: {test_url}")
        print(f"{'#'*60}")
        
        for method in test_methods:
            params = method["params"].copy()
            params['url'] = test_url
            
            html = test_api_method(test_url, method["name"], params)
            
            if html and len(html) > 1000:  # 有意义的HTML
                # 检查是否真的包含职位数据
                if 'data-jk' in html or 'jobTitle' in html or 'viewjob' in html:
                    successful_methods.append({
                        "url": test_url,
                        "method": method["name"],
                        "params": params
                    })
                    print(f"✓✓✓ 找到可行方法: {method['name']}")
            
            time.sleep(3)  # 避免请求过快
    
    # 总结
    print(f"\n\n{'='*60}")
    print("测试总结")
    print(f"{'='*60}")
    if successful_methods:
        print(f"找到 {len(successful_methods)} 种可行方法:")
        for i, method in enumerate(successful_methods, 1):
            print(f"\n{i}. {method['method']}")
            print(f"   URL: {method['url']}")
            print(f"   参数: {json.dumps(method['params'], indent=2, ensure_ascii=False)}")
        
        # 保存最佳方法
        with open("test_indeed_full/best_method.json", "w", encoding="utf-8") as f:
            json.dump(successful_methods[0], f, indent=2, ensure_ascii=False)
        print(f"\n✓ 已保存最佳方法到 best_method.json")
    else:
        print("✗ 未找到可行的方法")
        print("建议:")
        print("1. 检查API密钥是否有效")
        print("2. 检查网络连接")
        print("3. 查看ZenRows控制台是否有错误信息")
        print("4. 尝试访问Indeed基础页面测试")

if __name__ == "__main__":
    main()

