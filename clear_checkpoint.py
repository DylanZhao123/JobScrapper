# -*- coding: utf-8 -*-
"""
清空Checkpoint脚本
删除所有checkpoint和数据文件，让程序从头开始
"""
import os
import sys
from config import OUTPUT_DIR

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

CHECKPOINT_FILE = f"{OUTPUT_DIR}/checkpoint.json"
STAGE1_RAW_DATA = f"{OUTPUT_DIR}/stage1_raw_data.json"
STAGE1_UNIQUE_DATA = f"{OUTPUT_DIR}/stage1_unique_data.json"
STAGE2_DETAIL_DATA = f"{OUTPUT_DIR}/stage2_detail_data.json"

def clear_checkpoint():
    """清空所有checkpoint和数据文件"""
    files_to_delete = [
        CHECKPOINT_FILE,
        STAGE1_RAW_DATA,
        STAGE1_UNIQUE_DATA,
        STAGE2_DETAIL_DATA
    ]
    
    print("清空Checkpoint")
    
    deleted_count = 0
    for file_path in files_to_delete:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"✓ 已删除: {os.path.basename(file_path)}")
                deleted_count += 1
            except Exception as e:
                print(f"✗ 删除失败 {os.path.basename(file_path)}: {str(e)}")
        else:
            print(f"- 不存在: {os.path.basename(file_path)}")
    
    print(f"\n共删除 {deleted_count} 个文件")
    print("\n✓ Checkpoint已清空，下次运行程序将从头开始")
    
    # 注意：company_cache.json 不会被删除，保留公司规模缓存

if __name__ == "__main__":
    try:
        response = input("Clear all checkpoints and data? (yes/no): ")
    except:
        # 如果输入有编码问题，直接执行
        response = 'yes'
    
    if response.lower() in ['yes', 'y']:
        clear_checkpoint()
    else:
        print("Cancelled")

