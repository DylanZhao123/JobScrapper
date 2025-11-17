# -*- coding: utf-8 -*-
"""
简单直接的API测试
找到能成功抓取Indeed的方法
"""
import requests
import time
import json
import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_config import ZENROWS_API_KEY, ZENROWS_BASE_URL

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

def test_method(name, params):
    """测试一种方法"""
    print(f"\n{'='*70}")
    print(f"测试: {name}")
    print(f"参数: {json.dumps(params, indent=2, ensure_ascii=False)}")
    print(f"{'='*70}")
    
    try:
        start_time = time.time()
        r = requests.get(ZENROWS_BASE_URL, params=params, timeout=60)
        elapsed = time.time() - start_time
        
        print(f"状态码: {r.status_code}")
        print(f"耗时: {elapsed:.2f}秒")
        
        if r.status_code == 200:
            html = r.text
            print(f"HTML长度: {len(html)} 字符")
            
            # 检查内容
            checks = {
                "包含'job'": 'job' in html.lower(),
                "包含'indeed'": 'indeed' in html.lower(),
                "包含'data-jk'": 'data-jk' in html,
                "包含'jobTitle'": 'jobTitle' in html,
                "包含'viewjob'": 'viewjob' in html,
                "包含'Sign In'": 'Sign In' in html or 'sign in' in html.lower(),
                "包含'login'": 'login' in html.lower(),
            }
            
            print("\n内容检查:")
            for check_name, result in checks.items():
                status = "✓" if result else "✗"
                print(f"  {status} {check_name}: {result}")
            
            # 判断是否成功
            has_job_data = checks["包含'data-jk'"] or checks["包含'jobTitle'"] or checks["包含'viewjob'"]
            is_login_page = checks["包含'Sign In'"] or checks["包含'login'"]
            
            if has_job_data and not is_login_page:
                print("\n✓✓✓ 成功！包含职位数据")
                # 保存成功的HTML
                filename = f"test_indeed_full/success_{name.replace(' ', '_').replace('/', '_')}.html"
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(html)
                print(f"已保存到: {filename}")
                return True, html
            elif is_login_page:
                print("\n✗ 失败：返回登录页面（被检测为爬虫）")
                return False, html
            else:
                print("\n⚠ 不确定：可能不是职位列表页")
                return False, html
        else:
            print(f"✗ 失败，状态码: {r.status_code}")
            print(f"响应: {r.text[:500]}")
            return False, None
    except Exception as e:
        print(f"✗ 异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, None

def main():
    """主测试"""
    print("="*70)
    print("Indeed API 测试 - 寻找可行方法")
    print("="*70)
    
    test_url = "https://www.indeed.com/jobs?q=AI+Engineer&l=United+States"
    
    # 测试方法列表
    methods = [
        {
            "name": "1. 基础请求",
            "params": {
                'url': test_url,
                'apikey': ZENROWS_API_KEY
            }
        },
        {
            "name": "2. JS渲染",
            "params": {
                'url': test_url,
                'apikey': ZENROWS_API_KEY,
                'js_render': 'true'
            }
        },
        {
            "name": "3. JS渲染+等待3秒",
            "params": {
                'url': test_url,
                'apikey': ZENROWS_API_KEY,
                'js_render': 'true',
                'js_render_wait': '3000'
            }
        },
        {
            "name": "4. JS渲染+等待5秒",
            "params": {
                'url': test_url,
                'apikey': ZENROWS_API_KEY,
                'js_render': 'true',
                'js_render_wait': '5000'
            }
        },
        {
            "name": "5. JS渲染+高级代理",
            "params": {
                'url': test_url,
                'apikey': ZENROWS_API_KEY,
                'js_render': 'true',
                'premium_proxy': 'true'
            }
        },
        {
            "name": "6. JS渲染+高级代理+等待5秒",
            "params": {
                'url': test_url,
                'apikey': ZENROWS_API_KEY,
                'js_render': 'true',
                'premium_proxy': 'true',
                'js_render_wait': '5000'
            }
        },
        {
            "name": "7. JS渲染+高级代理+等待10秒",
            "params": {
                'url': test_url,
                'apikey': ZENROWS_API_KEY,
                'js_render': 'true',
                'premium_proxy': 'true',
                'js_render_wait': '10000'
            }
        },
    ]
    
    successful_methods = []
    
    for method in methods:
        success, html = test_method(method["name"], method["params"])
        if success:
            successful_methods.append({
                "name": method["name"],
                "params": method["params"]
            })
        
        # 避免请求过快
        if not success:
            time.sleep(3)
        else:
            time.sleep(1)
    
    # 总结
    print(f"\n\n{'='*70}")
    print("测试总结")
    print(f"{'='*70}")
    
    if successful_methods:
        print(f"\n找到 {len(successful_methods)} 种可行方法:\n")
        for i, method in enumerate(successful_methods, 1):
            print(f"{i}. {method['name']}")
            print(f"   参数: {json.dumps(method['params'], indent=4, ensure_ascii=False)}")
        
        # 保存最佳方法
        best_method = successful_methods[0]
        with open("test_indeed_full/best_method.json", "w", encoding="utf-8") as f:
            json.dump(best_method, f, indent=2, ensure_ascii=False)
        print(f"\n✓ 已保存最佳方法到 best_method.json")
        print(f"最佳方法: {best_method['name']}")
    else:
        print("\n✗ 未找到可行的方法")
        print("\n建议:")
        print("1. 检查ZenRows API密钥是否有效")
        print("2. 检查ZenRows账户是否有足够的配额")
        print("3. 查看ZenRows控制台是否有错误信息")
        print("4. 尝试访问其他网站测试API是否正常工作")

if __name__ == "__main__":
    main()

