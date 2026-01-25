"""Test Supabase connection"""
from supabase import create_client
from supabase_config import SUPABASE_URL, SUPABASE_KEY

try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # 测试查询
    result = supabase.table('jobs_united_states').select("*").limit(1).execute()
    print("✅ Supabase连接成功！")
    print(f"   表: jobs_united_states")
    print(f"   查询结果: {len(result.data)} 条记录")
    
except Exception as e:
    print(f"❌ 连接失败: {str(e)}")
    print("\n请检查：")
    print("1. supabase_config.py 中的 URL 和 KEY 是否正确")
    print("2. 是否已创建数据库表")
    print("3. 网络连接是否正常")