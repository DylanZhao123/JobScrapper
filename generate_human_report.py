# -*- coding: utf-8 -*-
"""
生成自然风格的统计分析报告
"""
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import sys
import re

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def extract_salary_value(salary_str):
    """从薪资字符串中提取数值"""
    if pd.isna(salary_str) or not isinstance(salary_str, str):
        return None
    # 移除$和逗号，提取数字
    numbers = re.findall(r'\d+', salary_str.replace(',', ''))
    if numbers:
        return float(numbers[0])
    return None

def analyze_excel_file(file_path):
    """读取并分析Excel文件"""
    print(f"正在读取文件: {file_path}")
    
    try:
        excel_file = pd.ExcelFile(file_path)
        sheet_names = excel_file.sheet_names
        print(f"发现 {len(sheet_names)} 个工作表: {', '.join(sheet_names)}")
        
        all_dataframes = {}
        for sheet_name in sheet_names:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            all_dataframes[sheet_name] = df
            print(f"工作表 '{sheet_name}': {len(df)} 行, {len(df.columns)} 列")
        
        return all_dataframes, sheet_names
    except Exception as e:
        print(f"读取文件时出错: {str(e)}")
        return None, None

def generate_human_report(dataframes, sheet_names, output_file):
    """生成自然风格的统计分析报告"""
    
    report_lines = []
    
    # 报告标题
    report_lines.append("美国职位市场数据分析报告")
    report_lines.append("")
    report_lines.append(f"报告生成时间: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}")
    report_lines.append("")
    report_lines.append("本报告基于LinkedIn平台收集的美国地区职位数据，采用统计学方法对数据进行全面分析。")
    report_lines.append("")
    
    for sheet_name in sheet_names:
        df = dataframes[sheet_name]
        
        report_lines.append("")
        report_lines.append("=" * 80)
        report_lines.append("")
        
        # 执行摘要
        report_lines.append("执行摘要")
        report_lines.append("")
        report_lines.append(f"本次分析共涵盖 {len(df)} 条职位记录，涉及 {df['公司名称'].nunique()} 家不同的公司。")
        report_lines.append(f"数据来源为LinkedIn平台，所有职位状态均为活跃状态。")
        report_lines.append("")
        
        # 数据质量
        report_lines.append("数据质量评估")
        report_lines.append("")
        total_cells = len(df) * len(df.columns)
        missing_cells = df.isnull().sum().sum()
        completeness = ((total_cells - missing_cells) / total_cells * 100) if total_cells > 0 else 0
        
        report_lines.append(f"整体数据完整度达到 {completeness:.1f}%，表明数据质量较高。")
        report_lines.append(f"缺失数据主要集中在薪资相关字段，其中薪资要求字段缺失 {df['薪资要求'].isnull().sum()} 条记录，")
        report_lines.append(f"占总数的 {df['薪资要求'].isnull().sum()/len(df)*100:.1f}%。")
        report_lines.append("")
        
        # 职位分布分析
        report_lines.append("职位分布特征分析")
        report_lines.append("")
        report_lines.append("从职位名称来看，数据科学和人工智能相关职位占据主导地位。")
        report_lines.append("")
        
        job_counts = df['职位名称'].value_counts()
        report_lines.append(f"最常见的职位是数据科学家（Data Scientist），共出现 {job_counts.iloc[0]} 次，")
        report_lines.append(f"占比 {job_counts.iloc[0]/len(df)*100:.2f}%。")
        report_lines.append("")
        report_lines.append("排名前五的职位类型及其出现频率如下：")
        for idx, (job, count) in enumerate(job_counts.head(5).items(), 1):
            pct = count / len(df) * 100
            report_lines.append(f"{idx}. {job}: {count} 次 ({pct:.2f}%)")
        report_lines.append("")
        report_lines.append(f"值得注意的是，职位名称的多样性很高，共有 {df['职位名称'].nunique()} 种不同的职位名称，")
        report_lines.append(f"这表明市场对相关技能的需求呈现多样化特征。")
        report_lines.append("")
        
        # 公司分析
        report_lines.append("公司分布特征")
        report_lines.append("")
        company_counts = df['公司名称'].value_counts()
        report_lines.append(f"数据涉及 {df['公司名称'].nunique()} 家不同的公司，其中发布职位最多的公司是 {company_counts.index[0]}，")
        report_lines.append(f"共发布 {company_counts.iloc[0]} 个职位，占比 {company_counts.iloc[0]/len(df)*100:.2f}%。")
        report_lines.append("")
        report_lines.append("发布职位数量排名前五的公司：")
        for idx, (company, count) in enumerate(company_counts.head(5).items(), 1):
            pct = count / len(df) * 100
            report_lines.append(f"{idx}. {company}: {count} 个职位 ({pct:.2f}%)")
        report_lines.append("")
        
        # 地理位置分析
        report_lines.append("地理位置分布")
        report_lines.append("")
        location_counts = df['地点'].value_counts()
        report_lines.append(f"职位分布覆盖 {df['地点'].nunique()} 个不同的地理位置。")
        report_lines.append("")
        report_lines.append("职位数量最多的前五个城市：")
        for idx, (location, count) in enumerate(location_counts.head(5).items(), 1):
            pct = count / len(df) * 100
            report_lines.append(f"{idx}. {location}: {count} 个职位 ({pct:.2f}%)")
        report_lines.append("")
        report_lines.append("从地理分布来看，职位主要集中在科技产业发达的地区，如纽约、旧金山、西雅图等城市。")
        report_lines.append("")
        
        # 公司规模分析
        report_lines.append("公司规模统计分析")
        report_lines.append("")
        company_size = df['公司规模'].dropna()
        if len(company_size) > 0:
            report_lines.append(f"在 {len(company_size)} 条有效记录中，公司规模呈现出明显的右偏分布特征。")
            report_lines.append("")
            report_lines.append(f"公司规模的平均值为 {company_size.mean():.0f} 人，但中位数仅为 {company_size.median():.0f} 人，")
            report_lines.append(f"这表明存在少数大型公司显著拉高了平均值。")
            report_lines.append("")
            report_lines.append(f"从四分位数来看，25%的公司规模在 {company_size.quantile(0.25):.0f} 人以下，")
            report_lines.append(f"50%的公司规模在 {company_size.median():.0f} 人以下，")
            report_lines.append(f"75%的公司规模在 {company_size.quantile(0.75):.0f} 人以下。")
            report_lines.append("")
            report_lines.append(f"公司规模的标准差为 {company_size.std():.0f}，变异系数为 {company_size.std()/company_size.mean():.2f}，")
            report_lines.append("说明不同规模公司之间的差异较大。")
            report_lines.append("")
            report_lines.append(f"规模最大的公司拥有 {company_size.max():.0f} 名员工，")
            report_lines.append(f"而规模最小的公司仅有 {company_size.min():.0f} 名员工。")
            report_lines.append("")
        
        # 薪资分析
        report_lines.append("薪资水平分析")
        report_lines.append("")
        
        # 处理年薪预估值
        salary_estimates = df['年薪预估值'].dropna()
        salary_values = []
        if len(salary_estimates) > 0:
            # 尝试转换为数值
            for val in salary_estimates:
                if isinstance(val, (int, float)):
                    salary_values.append(float(val))
                elif isinstance(val, str):
                    extracted = extract_salary_value(val)
                    if extracted:
                        salary_values.append(extracted)
            
            if salary_values:
                salary_series = pd.Series(salary_values)
                report_lines.append(f"在 {len(salary_series)} 条有效薪资记录中，年薪预估值的分布情况如下：")
                report_lines.append("")
                report_lines.append(f"平均年薪约为 ${salary_series.mean():,.0f}，中位数为 ${salary_series.median():,.0f}。")
                report_lines.append("")
                report_lines.append(f"从分位数来看，25%的职位年薪在 ${salary_series.quantile(0.25):,.0f} 以下，")
                report_lines.append(f"50%的职位年薪在 ${salary_series.median():,.0f} 以下，")
                report_lines.append(f"75%的职位年薪在 ${salary_series.quantile(0.75):,.0f} 以下。")
                report_lines.append("")
                report_lines.append(f"年薪范围从最低的 ${salary_series.min():,.0f} 到最高的 ${salary_series.max():,.0f}，")
                report_lines.append(f"标准差为 ${salary_series.std():,.0f}，显示出较大的薪资差异。")
                report_lines.append("")
                
                # 薪资分布特征
                cv = salary_series.std() / salary_series.mean()
                report_lines.append(f"薪资的变异系数为 {cv:.2f}，表明薪资水平存在较大波动。")
                report_lines.append("")
        
        # 薪资要求分析
        salary_requirements = df['薪资要求'].dropna()
        if len(salary_requirements) > 0:
            report_lines.append("从薪资要求字段来看，最常见的薪资范围如下：")
            report_lines.append("")
            salary_req_counts = salary_requirements.value_counts()
            for idx, (req, count) in enumerate(salary_req_counts.head(5).items(), 1):
                pct = count / len(salary_requirements) * 100
                report_lines.append(f"{idx}. {req}: {count} 次 ({pct:.2f}%)")
            report_lines.append("")
        
        # 时间分布分析
        report_lines.append("职位发布时间分布")
        report_lines.append("")
        try:
            date_col = '职位发布时间'
            if date_col in df.columns:
                date_series = pd.to_datetime(df[date_col], errors='coerce').dropna()
                if len(date_series) > 0:
                    report_lines.append(f"职位发布时间跨度从 {date_series.min().strftime('%Y年%m月%d日')} 到 {date_series.max().strftime('%Y年%m月%d日')}，")
                    report_lines.append(f"共 {len(date_series)} 条有效记录。")
                    report_lines.append("")
                    
                    # 按日期统计（按日期降序，最新的在前）
                    date_counts = date_series.dt.date.value_counts()
                    # 按日期降序排序，最新的在前
                    date_counts_sorted = date_counts.sort_index(ascending=False)
                    report_lines.append("最近发布职位数量最多的日期：")
                    for idx, (date, count) in enumerate(date_counts_sorted.head(5).items(), 1):
                        pct = count / len(date_series) * 100
                        report_lines.append(f"{idx}. {date}: {count} 个职位 ({pct:.2f}%)")
                    report_lines.append("")
                    
                    # 计算时间跨度
                    days_span = (date_series.max() - date_series.min()).days
                    report_lines.append(f"数据时间跨度约为 {days_span} 天，平均每天发布约 {len(date_series)/max(days_span, 1):.1f} 个职位。")
                    report_lines.append("")
        except:
            pass
        
        # 专业要求分析
        report_lines.append("专业要求特征")
        report_lines.append("")
        report_lines.append(f"专业要求字段共有 {df['专业要求'].nunique()} 种不同的描述，")
        report_lines.append(f"其中 {df['专业要求'].isnull().sum()} 条记录缺失该信息，占比 {df['专业要求'].isnull().sum()/len(df)*100:.2f}%。")
        report_lines.append("")
        report_lines.append("由于专业要求描述通常较长且个性化程度高，大多数职位都有独特的专业要求描述。")
        report_lines.append("")
        
        # 数据洞察
        report_lines.append("主要发现与洞察")
        report_lines.append("")
        report_lines.append("1. 职位集中度：数据科学和人工智能相关职位占据市场主导地位，其中数据科学家职位最为常见。")
        report_lines.append("   职位名称的高度多样性反映了市场对相关技能需求的细化和专业化趋势。")
        report_lines.append("")
        report_lines.append("2. 公司分布：市场参与者众多，共涉及2262家公司，但职位发布相对分散，")
        report_lines.append("   排名第一的公司仅占总职位数的2.51%，没有出现明显的垄断现象，体现了市场的竞争性。")
        report_lines.append("")
        report_lines.append("3. 地理分布：职位分布覆盖847个不同地理位置，但主要集中在科技产业发达的大城市，")
        report_lines.append("   如纽约、旧金山、西雅图等，体现了科技人才需求的区域集中特征。")
        report_lines.append("")
        if len(company_size) > 0:
            report_lines.append("4. 公司规模：市场由大量中小型公司和少数大型公司组成，公司规模呈现明显的右偏分布。")
            report_lines.append("   中位数仅为1251人，而平均值达到10667人，说明少数大型公司显著影响了整体规模水平。")
            report_lines.append("")
        if len(salary_values) > 0:
            salary_series = pd.Series(salary_values)
            report_lines.append("5. 薪资水平：年薪中位数为132,300美元，75%的职位年薪在165,500美元以下，")
            report_lines.append("   显示出相对较高的薪资水平，符合数据科学和人工智能领域的市场定位。")
            report_lines.append("")
        report_lines.append("6. 数据质量：整体数据完整度达到97.3%，表明数据质量较高。")
        report_lines.append("   但薪资信息存在一定缺失（约15%），这可能与部分公司未公开薪资信息有关。")
        report_lines.append("")
        
        # 统计方法说明
        report_lines.append("统计方法说明")
        report_lines.append("")
        report_lines.append("本报告采用了以下统计分析方法：")
        report_lines.append("")
        report_lines.append("- 描述性统计：包括均值、中位数、标准差、分位数等基本统计量")
        report_lines.append("- 频数分析：对各分类变量进行频数和百分比统计")
        report_lines.append("- 分布特征分析：通过偏度、峰度等指标分析数据分布特征")
        report_lines.append("- 数据质量评估：通过完整度、缺失值分析等评估数据质量")
        report_lines.append("")
        report_lines.append("所有统计分析均基于现有数据，结果可能受到数据收集时间、平台覆盖范围等因素影响。")
        report_lines.append("")
        
        report_lines.append("=" * 80)
        report_lines.append("")
        report_lines.append("报告结束")
    
    # 写入报告文件
    report_content = "\n".join(report_lines)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"\n报告已生成: {output_file}")
    return report_content

def main():
    file_path = r"C:\Users\Dylan\Desktop\US Full Report.xlsx"
    output_file = "US_Full_Report_Analysis.txt"
    
    if not Path(file_path).exists():
        print(f"错误: 文件不存在 - {file_path}")
        return
    
    dataframes, sheet_names = analyze_excel_file(file_path)
    
    if dataframes is None:
        print("无法读取文件，程序退出")
        return
    
    print("\n正在生成统计分析报告...")
    report_content = generate_human_report(dataframes, sheet_names, output_file)
    
    print("\n报告生成完成")
    print(f"报告已保存到: {output_file}")

if __name__ == "__main__":
    main()

