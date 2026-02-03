# -*- coding: utf-8 -*-
"""
测试只读访问权限
验证anon密钥是否可以读取数据，但不能修改数据
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

try:
    from supabase import create_client
    import supabase_config
except ImportError as e:
    print(f"[ERROR] Missing dependency: {e}")
    print("Please install: pip install supabase")
    sys.exit(1)

print("="*60)
print("Testing Read-Only Access")
print("="*60)

# 使用anon密钥（只读）
supabase_url = getattr(supabase_config, 'SUPABASE_URL', None)
anon_key = getattr(supabase_config, 'SUPABASE_KEY', None)  # anon public key

if not supabase_url or not anon_key:
    print("[ERROR] Supabase credentials not configured")
    sys.exit(1)

supabase = create_client(supabase_url, anon_key)

# 测试读取权限
print("\n1. Testing READ access...")
try:
    result = supabase.table('jobs_united_states').select('job_title, company_name').limit(5).execute()
    if result.data:
        print(f"   ✅ READ access works!")
        print(f"   Found {len(result.data)} records")
        print(f"   Sample: {result.data[0].get('job_title', 'N/A')[:50]}...")
    else:
        print("   ⚠️  READ access works but no data returned")
except Exception as e:
    print(f"   ❌ READ access failed: {str(e)[:200]}")
    print("   This might mean RLS policies are not configured correctly.")

# 测试写入权限（应该失败）
print("\n2. Testing WRITE access (should fail)...")
try:
    result = supabase.table('jobs_united_states').insert({
        'job_title': 'TEST - Should Fail',
        'company_name': 'TEST COMPANY'
    }).execute()
    print("   ❌ WRITE access should NOT work!")
    print("   ⚠️  Security issue: Write access is allowed when it shouldn't be!")
except Exception as e:
    error_msg = str(e).lower()
    if 'permission denied' in error_msg or 'policy' in error_msg or 'forbidden' in error_msg:
        print("   ✅ WRITE access correctly blocked!")
        print(f"   Error (expected): {str(e)[:100]}")
    else:
        print(f"   ⚠️  Unexpected error: {str(e)[:200]}")

# 测试更新权限（应该失败）
print("\n3. Testing UPDATE access (should fail)...")
try:
    result = supabase.table('jobs_united_states').update({
        'job_title': 'TEST UPDATE'
    }).eq('id', 1).execute()
    print("   ❌ UPDATE access should NOT work!")
    print("   ⚠️  Security issue: Update access is allowed when it shouldn't be!")
except Exception as e:
    error_msg = str(e).lower()
    if 'permission denied' in error_msg or 'policy' in error_msg or 'forbidden' in error_msg:
        print("   ✅ UPDATE access correctly blocked!")
    else:
        print(f"   ⚠️  Unexpected error: {str(e)[:200]}")

# 测试删除权限（应该失败）
print("\n4. Testing DELETE access (should fail)...")
try:
    result = supabase.table('jobs_united_states').delete().eq('id', 999999).execute()
    print("   ❌ DELETE access should NOT work!")
    print("   ⚠️  Security issue: Delete access is allowed when it shouldn't be!")
except Exception as e:
    error_msg = str(e).lower()
    if 'permission denied' in error_msg or 'policy' in error_msg or 'forbidden' in error_msg:
        print("   ✅ DELETE access correctly blocked!")
    else:
        print(f"   ⚠️  Unexpected error: {str(e)[:200]}")

print("\n" + "="*60)
print("Test Summary")
print("="*60)
print("If all tests show ✅, your read-only access is configured correctly!")
print("You can safely share the anon public key for read-only access.")
print("="*60)




