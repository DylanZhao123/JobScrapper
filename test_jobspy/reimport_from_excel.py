# -*- coding: utf-8 -*-
"""Re-import data from Excel files to Supabase"""
import sys
import io
import pandas as pd
import os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Import the save function from main scraper
from jobspy_max_scraper import save_to_supabase

# Get RUN_ID from config
try:
    import config_jobspy
    RUN_ID = getattr(config_jobspy, 'JOBSPY_RUN_ID', 'BunchIndeedGlobal_2025_12_20')
except:
    RUN_ID = 'BunchIndeedGlobal_2025_12_20'

# Define Excel file paths based on RUN_ID
base_dir = f"output/{RUN_ID}"
excel_files = {
    "United States": f"{base_dir}/united_states/jobspy_max_output.xlsx",
    "United Kingdom": f"{base_dir}/united_kingdom/jobspy_max_output.xlsx",
    "Australia": f"{base_dir}/australia/jobspy_max_output.xlsx",
    "Hong Kong": f"{base_dir}/hong_kong/jobspy_max_output.xlsx",
    "Singapore": f"{base_dir}/singapore/jobspy_max_output.xlsx",
}

print("="*60)
print("Re-importing Data from Excel to Supabase")
print("="*60)
print(f"Looking for Excel files in: {base_dir}")
print()

total_imported = 0
for region_name, excel_path in excel_files.items():
    if not os.path.exists(excel_path):
        print(f"[SKIP] {region_name}: Excel file not found at {excel_path}")
        continue
    
    print(f"\n{'='*60}")
    print(f"Processing: {region_name}")
    print(f"{'='*60}")
    
    try:
        # Read Excel file
        df = pd.read_excel(excel_path)
        print(f"  Loaded {len(df)} records from Excel")
        
        # Save to Supabase
        save_to_supabase(df, region_name)
        total_imported += len(df)
        print(f"  [OK] {region_name} completed")
    except Exception as e:
        print(f"  [ERROR] {region_name}: {str(e)[:200]}")
        import traceback
        traceback.print_exc()

print("\n" + "="*60)
print(f"Re-import completed! Total records processed: {total_imported}")
print("="*60)

