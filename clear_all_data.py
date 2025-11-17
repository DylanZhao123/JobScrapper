#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
清空所有checkpoints和数据库数据
"""
import os
import sys
import io
from dotenv import load_dotenv

# Set UTF-8 encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()

print("=" * 60)
print("Clear All Data - Checkpoints and Database")
print("=" * 60)

# 1. Clear checkpoints (all countries)
print("\n[1] Clearing checkpoints...")
from config import OUTPUT_DIR, get_country_output_paths

country_codes = ["us", "uk", "ca", "sg", "hk"]
checkpoint_count = 0

for country_code in country_codes:
    country_paths = get_country_output_paths(country_code)
    checkpoint_file = os.path.join(country_paths["dir"], "checkpoint.json")
    if os.path.exists(checkpoint_file):
        try:
            os.remove(checkpoint_file)
            checkpoint_count += 1
            print(f"  ✓ Deleted checkpoint: {country_code.upper()}")
        except Exception as e:
            print(f"  ✗ Failed to delete {country_code.upper()} checkpoint: {str(e)}")

if checkpoint_count == 0:
    print("  ℹ No checkpoint files found")

# 2. Clear stage data files (all countries)
print("\n[2] Clearing stage data files...")
stage_file_names = ["stage1_raw_data.json", "stage1_unique_data.json", "stage2_detail_data.json"]
file_count = 0

for country_code in country_codes:
    country_paths = get_country_output_paths(country_code)
    for file_name in stage_file_names:
        file_path = os.path.join(country_paths["dir"], file_name)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                file_count += 1
            except Exception as e:
                print(f"  ✗ Failed to delete {country_code.upper()}/{file_name}: {str(e)}")

if file_count > 0:
    print(f"  ✓ Deleted {file_count} data files")
else:
    print("  ℹ No data files found")

# 3. Clear database (optional)
print("\n[3] Clearing database tables...")
try:
    from supabase_storage import init_supabase, get_country_table
    from supabase import create_client
    
    supabase_url = os.getenv("SUPABASE_URL", "")
    supabase_key = os.getenv("SUPABASE_KEY", "")
    
    if supabase_url and supabase_key:
        supabase = create_client(supabase_url, supabase_key)
        
        tables = ["jobs", "jobs_uk", "jobs_ca", "jobs_sg", "jobs_hk"]
        country_names = {
            "jobs": "美国 (USA)",
            "jobs_uk": "英国 (UK)",
            "jobs_ca": "加拿大 (Canada)",
            "jobs_sg": "新加坡 (Singapore)",
            "jobs_hk": "香港 (Hong Kong)",
        }
        
        for table_name in tables:
            try:
                # Delete all records
                result = supabase.table(table_name).delete().neq("id", 0).execute()
                # Count remaining
                count_result = supabase.table(table_name).select("id", count="exact").execute()
                count = count_result.count if hasattr(count_result, 'count') else (len(count_result.data) if count_result.data else 0)
                print(f"  ✓ Cleared {country_names.get(table_name, table_name)}: {count} records remaining")
            except Exception as e:
                print(f"  ✗ Failed to clear {table_name}: {str(e)}")
    else:
        print("  ℹ Supabase credentials not found, skipping database cleanup")
        
except ImportError:
    print("  ℹ Supabase module not available, skipping database cleanup")
except Exception as e:
    print(f"  ✗ Database cleanup error: {str(e)}")

print("\n" + "=" * 60)
print("Cleanup Complete!")
print("=" * 60)
print("\nAll checkpoints and data files have been cleared.")
print("You can now run the scraper from scratch.")

