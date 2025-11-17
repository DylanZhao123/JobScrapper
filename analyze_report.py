# -*- coding: utf-8 -*-
"""
统计分析脚本 - 读取Excel文件并生成详实报告
"""
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import sys

# 设置输出编码
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def analyze_excel_file(file_path):
    """读取并分析Excel文件"""
    print(f"正在读取文件: {file_path}")
    
    # 读取Excel文件
    try:
        # 尝试读取所有工作表
        excel_file = pd.ExcelFile(file_path)
        sheet_names = excel_file.sheet_names
        print(f"发现 {len(sheet_names)} 个工作表: {', '.join(sheet_names)}")
        
        # 读取所有工作表
        all_dataframes = {}
        for sheet_name in sheet_names:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            all_dataframes[sheet_name] = df
            print(f"工作表 '{sheet_name}': {len(df)} 行, {len(df.columns)} 列")
        
        return all_dataframes, sheet_names
    except Exception as e:
        print(f"读取文件时出错: {str(e)}")
        return None, None

def generate_statistical_report(dataframes, sheet_names, output_file):
    """生成统计分析报告"""
    
    report_lines = []
    
    # 报告标题
    report_lines.append("=" * 80)
    report_lines.append("数据统计分析报告")
    report_lines.append("=" * 80)
    report_lines.append(f"生成时间: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}")
    report_lines.append("")
    
    # 对每个工作表进行分析
    for sheet_name in sheet_names:
        df = dataframes[sheet_name]
        
        report_lines.append("")
        report_lines.append("-" * 80)
        report_lines.append(f"工作表: {sheet_name}")
        report_lines.append("-" * 80)
        report_lines.append("")
        
        # 基本信息
        report_lines.append("一、数据基本信息")
        report_lines.append("")
        report_lines.append(f"总记录数: {len(df)} 条")
        report_lines.append(f"字段数量: {len(df.columns)} 个")
        report_lines.append("")
        
        # 字段列表
        report_lines.append("字段列表:")
        for i, col in enumerate(df.columns, 1):
            report_lines.append(f"  {i}. {col}")
        report_lines.append("")
        
        # 数据概览
        report_lines.append("二、数据概览")
        report_lines.append("")
        
        # 缺失值统计
        missing_data = df.isnull().sum()
        missing_percent = (missing_data / len(df) * 100).round(2)
        
        if missing_data.sum() > 0:
            report_lines.append("缺失值统计:")
            for col in df.columns:
                if missing_data[col] > 0:
                    report_lines.append(f"  {col}: {missing_data[col]} 条 ({missing_percent[col]}%)")
            report_lines.append("")
        else:
            report_lines.append("缺失值统计: 无缺失值")
            report_lines.append("")
        
        # 数值型字段的统计分析
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if numeric_cols:
            report_lines.append("三、数值型字段统计分析")
            report_lines.append("")
            
            for col in numeric_cols:
                report_lines.append(f"字段: {col}")
                series = df[col].dropna()
                
                if len(series) > 0:
                    report_lines.append(f"  有效数据量: {len(series)} 条")
                    report_lines.append(f"  平均值: {series.mean():.2f}")
                    report_lines.append(f"  中位数: {series.median():.2f}")
                    report_lines.append(f"  标准差: {series.std():.2f}")
                    report_lines.append(f"  最小值: {series.min():.2f}")
                    report_lines.append(f"  最大值: {series.max():.2f}")
                    
                    # 四分位数
                    q25 = series.quantile(0.25)
                    q75 = series.quantile(0.75)
                    iqr = q75 - q25
                    report_lines.append(f"  第一四分位数 (Q1): {q25:.2f}")
                    report_lines.append(f"  第三四分位数 (Q3): {q75:.2f}")
                    report_lines.append(f"  四分位距 (IQR): {iqr:.2f}")
                    
                    # 偏度和峰度
                    if len(series) > 2:
                        from scipy import stats
                        try:
                            skewness = stats.skew(series)
                            kurtosis = stats.kurtosis(series)
                            report_lines.append(f"  偏度: {skewness:.2f}")
                            report_lines.append(f"  峰度: {kurtosis:.2f}")
                        except:
                            pass
                    
                    report_lines.append("")
        
        # 分类型字段的统计分析
        categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
        if categorical_cols:
            report_lines.append("四、分类型字段统计分析")
            report_lines.append("")
            
            for col in categorical_cols:
                report_lines.append(f"字段: {col}")
                value_counts = df[col].value_counts()
                total = len(df[col].dropna())
                
                if total > 0:
                    report_lines.append(f"  唯一值数量: {df[col].nunique()} 个")
                    report_lines.append(f"  有效数据量: {total} 条")
                    report_lines.append("")
                    
                    # 显示前10个最常见的值
                    top_n = min(10, len(value_counts))
                    report_lines.append(f"  前 {top_n} 个最常见的值:")
                    for idx, (value, count) in enumerate(value_counts.head(top_n).items(), 1):
                        percentage = (count / total * 100)
                        report_lines.append(f"    {idx}. {value}: {count} 次 ({percentage:.2f}%)")
                    
                    report_lines.append("")
        
        # 日期型字段分析
        date_cols = []
        for col in df.columns:
            if df[col].dtype == 'datetime64[ns]' or 'date' in col.lower() or 'time' in col.lower():
                date_cols.append(col)
        
        if date_cols:
            report_lines.append("五、日期型字段分析")
            report_lines.append("")
            
            for col in date_cols:
                try:
                    # 尝试转换为日期
                    date_series = pd.to_datetime(df[col], errors='coerce').dropna()
                    if len(date_series) > 0:
                        report_lines.append(f"字段: {col}")
                        report_lines.append(f"  最早日期: {date_series.min()}")
                        report_lines.append(f"  最晚日期: {date_series.max()}")
                        report_lines.append(f"  时间跨度: {date_series.max() - date_series.min()}")
                        report_lines.append("")
                except:
                    pass
        
        # 相关性分析（如果有多个数值型字段）
        if len(numeric_cols) > 1:
            report_lines.append("六、字段相关性分析")
            report_lines.append("")
            
            # 计算相关系数矩阵
            corr_matrix = df[numeric_cols].corr()
            
            # 找出强相关的字段对（相关系数绝对值 > 0.7）
            strong_correlations = []
            for i in range(len(corr_matrix.columns)):
                for j in range(i+1, len(corr_matrix.columns)):
                    corr_value = corr_matrix.iloc[i, j]
                    if abs(corr_value) > 0.7 and not np.isnan(corr_value):
                        strong_correlations.append((
                            corr_matrix.columns[i],
                            corr_matrix.columns[j],
                            corr_value
                        ))
            
            if strong_correlations:
                report_lines.append("强相关字段对 (|相关系数| > 0.7):")
                for col1, col2, corr in strong_correlations:
                    report_lines.append(f"  {col1} 与 {col2}: {corr:.3f}")
                report_lines.append("")
            else:
                report_lines.append("未发现强相关字段对 (|相关系数| > 0.7)")
                report_lines.append("")
        
        # 数据质量评估
        report_lines.append("七、数据质量评估")
        report_lines.append("")
        
        total_cells = len(df) * len(df.columns)
        missing_cells = df.isnull().sum().sum()
        completeness = ((total_cells - missing_cells) / total_cells * 100) if total_cells > 0 else 0
        
        report_lines.append(f"数据完整度: {completeness:.2f}%")
        report_lines.append(f"缺失数据占比: {100 - completeness:.2f}%")
        report_lines.append("")
        
        # 重复数据检查
        duplicate_count = df.duplicated().sum()
        if duplicate_count > 0:
            report_lines.append(f"重复记录数: {duplicate_count} 条 ({duplicate_count/len(df)*100:.2f}%)")
        else:
            report_lines.append("重复记录数: 0 条")
        report_lines.append("")
    
    # 写入报告文件
    report_content = "\n".join(report_lines)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"\n报告已生成: {output_file}")
    return report_content

def main():
    file_path = r"C:\Users\Dylan\Desktop\US Full Report.xlsx"
    output_file = "US_Full_Report_Analysis.txt"
    
    # 检查文件是否存在
    if not Path(file_path).exists():
        print(f"错误: 文件不存在 - {file_path}")
        return
    
    # 读取和分析文件
    dataframes, sheet_names = analyze_excel_file(file_path)
    
    if dataframes is None:
        print("无法读取文件，程序退出")
        return
    
    # 生成报告
    print("\n正在生成统计分析报告...")
    report_content = generate_statistical_report(dataframes, sheet_names, output_file)
    
    # 在控制台显示报告
    print("\n" + "=" * 80)
    print("报告内容预览:")
    print("=" * 80)
    print(report_content[:2000])  # 显示前2000个字符
    if len(report_content) > 2000:
        print("\n... (完整报告已保存到文件)")

if __name__ == "__main__":
    main()

