# -*- coding: utf-8 -*-
"""Clear all data from Supabase tables"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

try:
    from supabase import create_client, Client
    import supabase_config
except ImportError as e:
    print(f"[ERROR] Missing dependency: {e}")
    print("Please install: pip install supabase")
    sys.exit(1)

# Connect to Supabase
supabase_url = getattr(supabase_config, 'SUPABASE_URL', None)
supabase_key = getattr(supabase_config, 'SUPABASE_KEY', None)
region_table_map = getattr(supabase_config, 'REGION_TABLE_MAP', {})

if not supabase_url or not supabase_key:
    print("[ERROR] Supabase credentials not configured")
    print("Please check your supabase_config.py file")
    sys.exit(1)

supabase: Client = create_client(supabase_url, supabase_key)

print("="*60)
print("Clearing Supabase Data")
print("="*60)
print(f"Connected to: {supabase_url}")
print()

# Confirm before deletion
response = input("Are you sure you want to delete ALL data from Supabase? (yes/no): ")
if response.lower() != 'yes':
    print("Operation cancelled.")
    sys.exit(0)

# Delete data from each table
total_deleted = 0
for region_name, table_name in region_table_map.items():
    try:
        # Count records before deletion
        result = supabase.table(table_name).select("id", count="exact").execute()
        count_before = result.count if hasattr(result, 'count') else len(result.data) if result.data else 0
        
        if count_before == 0:
            print(f"{region_name} ({table_name}): No records to delete")
            continue
        
        # Delete all records
        # Using .neq("id", 0) to delete all records (since id is always > 0)
        delete_result = supabase.table(table_name).delete().neq("id", 0).execute()
        
        print(f"{region_name} ({table_name}):")
        print(f"  Deleted {count_before} records")
        total_deleted += count_before
    except Exception as e:
        print(f"{region_name} ({table_name}): ERROR - {str(e)[:200]}")

print("\n" + "="*60)
print(f"Total deleted: {total_deleted} records")
print("="*60)
print("\nYou can now re-run jobspy_max_scraper.py to re-import data.")
print("Or use reimport_from_excel.py if you have existing Excel files.")

