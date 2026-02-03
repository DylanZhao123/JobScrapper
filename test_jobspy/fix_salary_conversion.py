# -*- coding: utf-8 -*-
"""
一次性脚本：修复 BunchGlobal_2025_01_18 文件夹中的薪资转换问题
将月薪和时薪统一转换为年薪形式
"""
import os
import pandas as pd
import re
from pathlib import Path

TARGET_DIRECTORY = "output\BunchGlobal_2025_12_26"  # 目标文件夹路径
# ============================================================================

def convert_salary_to_annual(salary_range_str, estimated_annual_str, estimated_annual_usd_str):
    """
    将薪资范围字符串转换为年薪形式
    
    Args:
        salary_range_str: 薪资范围字符串，如 "$6,710 - $14,360 (monthly)"
        estimated_annual_str: 当前估算年薪字符串
        estimated_annual_usd_str: 当前估算年薪USD字符串
    
    Returns:
        tuple: (修正后的estimated_annual, 修正后的estimated_annual_usd)
    """
    if pd.isna(salary_range_str) or not salary_range_str:
        return estimated_annual_str, estimated_annual_usd_str
    
    salary_range_str = str(salary_range_str)
    
    # 检查是否是月薪或时薪
    is_monthly = 'monthly' in salary_range_str.lower()
    is_hourly = 'hourly' in salary_range_str.lower() or '/hr' in salary_range_str.lower() or 'per hour' in salary_range_str.lower()
    
    if not (is_monthly or is_hourly):
        # 已经是年薪或没有指定，返回原值
        return estimated_annual_str, estimated_annual_usd_str
    
    # 提取薪资数值
    # 匹配模式：$6,710 - $14,360 或 $23 - $28
    pattern = r'[\$£€A\$S\$HK\$C\$]?\s*([\d,]+)\s*-\s*[\$£€A\$S\$HK\$C\$]?\s*([\d,]+)'
    match = re.search(pattern, salary_range_str)
    
    if match:
        min_str = match.group(1).replace(',', '')
        max_str = match.group(2).replace(',', '')
        
        try:
            min_val = float(min_str)
            max_val = float(max_str)
            
            # 根据类型转换
            if is_monthly:
                min_val_annual = min_val * 12
                max_val_annual = max_val * 12
            elif is_hourly:
                min_val_annual = min_val * 2080  # 2080 working hours per year
                max_val_annual = max_val * 2080
            
            avg_annual = (min_val_annual + max_val_annual) / 2
            
            # 提取货币符号
            currency_match = re.search(r'([\$£€A\$S\$HK\$C\$])', salary_range_str)
            if currency_match:
                currency_symbol = currency_match.group(1)
            else:
                # 默认使用美元
                currency_symbol = '$'
            
            # 格式化输出
            currency_map = {
                '$': 'USD',
                '£': 'GBP',
                '€': 'EUR',
                'A$': 'AUD',
                'S$': 'SGD',
                'HK$': 'HKD',
                'C$': 'CAD'
            }
            currency_code = currency_map.get(currency_symbol, 'USD')
            
            # 更新估算年薪
            estimated_annual = f"{currency_symbol}{int(avg_annual):,}"
            
            # 转换为USD
            if currency_code == 'USD':
                estimated_annual_usd = f"${int(avg_annual):,}"
            else:
                # 对于非USD货币，尝试从原值推断汇率
                # 如果原estimated_annual_usd和estimated_annual都存在，计算汇率
                exchange_rate = None
                if pd.notna(estimated_annual_usd_str) and estimated_annual_usd_str and pd.notna(estimated_annual_str) and estimated_annual_str:
                    try:
                        # 提取原USD值
                        usd_match = re.search(r'\$?([\d,]+)', str(estimated_annual_usd_str))
                        # 提取原年薪值（可能是月薪或时薪的原始值）
                        old_annual_match = re.search(r'[\$£€A\$S\$HK\$C\$]?([\d,]+)', str(estimated_annual_str))
                        if usd_match and old_annual_match:
                            old_usd_val = float(usd_match.group(1).replace(',', ''))
                            old_annual_val = float(old_annual_match.group(1).replace(',', ''))
                            if old_annual_val > 0:
                                # 计算汇率：原USD值 / 原年薪值
                                exchange_rate = old_usd_val / old_annual_val
                    except:
                        pass
                
                # 如果无法从原值推断，使用固定汇率
                if exchange_rate is None:
                    fallback_rates = {
                        'GBP': 1.27,   # 1 GBP = 1.27 USD
                        'AUD': 0.67,   # 1 AUD = 0.67 USD
                        'SGD': 0.74,   # 1 SGD = 0.74 USD
                        'HKD': 0.13,   # 1 HKD = 0.13 USD
                        'EUR': 1.09,   # 1 EUR = 1.09 USD
                        'CAD': 0.73,   # 1 CAD = 0.73 USD
                    }
                    exchange_rate = fallback_rates.get(currency_code, 1.0)
                
                new_usd_val = avg_annual * exchange_rate
                estimated_annual_usd = f"${int(new_usd_val):,}"
            
            return estimated_annual, estimated_annual_usd
        except (ValueError, TypeError) as e:
            print(f"Error converting salary: {e}")
            return estimated_annual_str, estimated_annual_usd_str
    else:
        # 尝试匹配单个值
        pattern_single = r'[\$£€A\$S\$HK\$C\$]?\s*([\d,]+)'
        match_single = re.search(pattern_single, salary_range_str)
        if match_single:
            val_str = match_single.group(1).replace(',', '')
            try:
                val = float(val_str)
                
                if is_monthly:
                    val_annual = val * 12
                elif is_hourly:
                    val_annual = val * 2080
                else:
                    return estimated_annual_str, estimated_annual_usd_str
                
                currency_match = re.search(r'([\$£€A\$S\$HK\$C\$])', salary_range_str)
                currency_symbol = currency_match.group(1) if currency_match else '$'
                
                # 货币代码映射
                currency_map = {
                    '$': 'USD',
                    '£': 'GBP',
                    '€': 'EUR',
                    'A$': 'AUD',
                    'S$': 'SGD',
                    'HK$': 'HKD',
                    'C$': 'CAD'
                }
                currency_code = currency_map.get(currency_symbol, 'USD')
                
                estimated_annual = f"{currency_symbol}{int(val_annual):,}"
                
                # 转换为USD
                if currency_code == 'USD':
                    estimated_annual_usd = f"${int(val_annual):,}"
                else:
                    # 使用固定汇率
                    fallback_rates = {
                        'GBP': 1.27, 'AUD': 0.67, 'SGD': 0.74,
                        'HKD': 0.13, 'EUR': 1.09, 'CAD': 0.73,
                    }
                    exchange_rate = fallback_rates.get(currency_code, 1.0)
                    val_usd = val_annual * exchange_rate
                    estimated_annual_usd = f"${int(val_usd):,}"
                
                return estimated_annual, estimated_annual_usd
            except (ValueError, TypeError):
                return estimated_annual_str, estimated_annual_usd_str
    
    return estimated_annual_str, estimated_annual_usd_str


def fix_excel_file(file_path):
    """
    修复单个Excel文件中的薪资转换问题
    
    Args:
        file_path: Excel文件路径
    """
    print(f"\nProcessing file: {file_path}")
    
    try:
        # 读取Excel文件
        df = pd.read_excel(file_path)
        
        # 检查必要的列是否存在
        required_columns = ['Salary Range', 'Estimated Annual Salary', 'Estimated Annual Salary (USD)']
        if not all(col in df.columns for col in required_columns):
            print(f"  Warning: File missing required columns, skipping")
            return False
        
        # 统计需要修复的行数
        monthly_count = df['Salary Range'].str.contains('monthly', case=False, na=False).sum()
        hourly_count = df['Salary Range'].str.contains('hourly|/hr|per hour', case=False, na=False, regex=True).sum()
        
        print(f"  Found {monthly_count} monthly salary records, {hourly_count} hourly salary records")
        
        if monthly_count == 0 and hourly_count == 0:
            print(f"  No fixes needed")
            return True
        
        # 修复每一行
        fixed_count = 0
        for idx, row in df.iterrows():
            salary_range = row['Salary Range']
            estimated_annual = row['Estimated Annual Salary']
            estimated_annual_usd = row['Estimated Annual Salary (USD)']
            
            # 检查是否需要修复
            if pd.notna(salary_range):
                is_monthly = 'monthly' in str(salary_range).lower()
                is_hourly = 'hourly' in str(salary_range).lower() or '/hr' in str(salary_range).lower() or 'per hour' in str(salary_range).lower()
                
                if is_monthly or is_hourly:
                    new_annual, new_annual_usd = convert_salary_to_annual(
                        salary_range, estimated_annual, estimated_annual_usd
                    )
                    
                    # 更新DataFrame
                    df.at[idx, 'Estimated Annual Salary'] = new_annual
                    df.at[idx, 'Estimated Annual Salary (USD)'] = new_annual_usd
                    fixed_count += 1
        
        print(f"  Fixed {fixed_count} record(s)")
        
        # 保存修复后的文件
        df.to_excel(file_path, index=False)
        print(f"  File saved: {file_path}")
        
        return True
        
    except Exception as e:
        print(f"  Error: {e}")
        return False


def main():
    """
    主函数：修复指定文件夹中的所有Excel文件
    """
    base_dir = Path(TARGET_DIRECTORY)
    
    if not base_dir.exists():
        print(f"Error: Directory does not exist: {base_dir}")
        return
    
    print("=" * 60)
    print("Salary Conversion Fix Script")
    print("=" * 60)
    print(f"Target directory: {base_dir}")
    
    # 查找所有Excel文件
    excel_files = list(base_dir.rglob("jobspy_max_output.xlsx"))
    
    if not excel_files:
        print("No Excel files found")
        return
    
    print(f"\nFound {len(excel_files)} Excel file(s)")
    
    # 处理每个文件
    success_count = 0
    for excel_file in excel_files:
        if fix_excel_file(excel_file):
            success_count += 1
    
    print("\n" + "=" * 60)
    print(f"Processing complete: {success_count}/{len(excel_files)} file(s) fixed successfully")
    print("=" * 60)


if __name__ == "__main__":
    main()

