# -*- coding: utf-8 -*-
"""
对Final_Merged_Report_1的final_merged_report.xlsx进行系统分析
包括relevance level分析和专业要求分析
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import re
from datetime import datetime
from pathlib import Path
import os
import sys
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
import matplotlib.font_manager as fm

# 设置输出编码
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# 设置中文字体
chinese_fonts = ['SimHei', 'Microsoft YaHei', 'SimSun', 'KaiTi', 'FangSong', 
                 'STHeiti', 'STSong', 'Arial Unicode MS', 'PingFang SC', 'Hiragino Sans GB']
available_font = None
for font_name in chinese_fonts:
    try:
        font_path = None
        for font in fm.fontManager.ttflist:
            if font_name.lower() in font.name.lower():
                font_path = font.fname
                break
        if font_path:
            prop = fm.FontProperties(fname=font_path)
            available_font = font_name
            plt.rcParams['font.sans-serif'] = [font_name] + plt.rcParams['font.sans-serif']
            break
    except:
        continue

if not available_font:
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun', 'DejaVu Sans']
    available_font = 'SimHei'

plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.family'] = 'sans-serif'
sns.set_style("whitegrid")

# 注册reportlab中文字体
try:
    font_paths = [
        r'C:\Windows\Fonts\simhei.ttf',
        r'C:\Windows\Fonts\msyh.ttc',
        r'C:\Windows\Fonts\simsun.ttc',
    ]
    reportlab_font_registered = False
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                reportlab_font_registered = True
                break
            except:
                continue
    if not reportlab_font_registered:
        print("Warning: Could not register Chinese font for reportlab")
except Exception as e:
    print(f"Warning: Font registration error: {e}")

# 文件路径
EXCEL_FILE = r"C:\Users\Dylan\JobScrapper\outputs\Final_Merged_Report_1\final_merged_report.xlsx"
OUTPUT_DIR = r"C:\Users\Dylan\JobScrapper\finding\Final_Merged_Report_Analysis"

# 创建输出目录
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 学历关键词
EDUCATION_KEYWORDS = {
    'Bachelor': ['bachelor', "bachelor's", 'bs', 'b.s.', 'ba', 'b.a.', 'undergraduate'],
    'Master': ['master', "master's", 'ms', 'm.s.', 'ma', 'm.a.', 'mba', 'm.sc.', 'meng'],
    'PhD': ['phd', 'ph.d', 'ph.d.', 'doctorate', 'doctoral', 'd.phil'],
    'Associate': ['associate', 'aa', 'a.a.', 'as', 'a.s.'],
    'High School': ['high school', 'hs', 'h.s.', 'diploma']
}

# 专业关键词
MAJOR_KEYWORDS = {
    'Computer Science': ['computer science', 'cs', 'computing', 'software engineering'],
    'Data Science': ['data science', 'data analytics', 'data analysis'],
    'Mathematics': ['mathematics', 'math', 'statistics', 'statistical'],
    'Engineering': ['engineering', 'engineer', 'electrical engineering', 'mechanical engineering'],
    'AI/ML': ['artificial intelligence', 'machine learning', 'ai', 'ml', 'deep learning', 'neural network'],
    'Business': ['business', 'mba', 'management', 'finance', 'economics'],
    'Physics': ['physics', 'physical'],
    'Information Systems': ['information systems', 'information technology', 'it', 'mis']
}

def extract_education(text):
    """从文本中提取学历要求"""
    if pd.isna(text) or not isinstance(text, str):
        return []
    
    text_lower = text.lower()
    found_degrees = []
    
    # 按优先级检查（PhD > Master > Bachelor > Associate > High School）
    for degree, keywords in [('PhD', EDUCATION_KEYWORDS['PhD']),
                             ('Master', EDUCATION_KEYWORDS['Master']),
                             ('Bachelor', EDUCATION_KEYWORDS['Bachelor']),
                             ('Associate', EDUCATION_KEYWORDS['Associate']),
                             ('High School', EDUCATION_KEYWORDS['High School'])]:
        for keyword in keywords:
            if keyword in text_lower:
                found_degrees.append(degree)
                break
    
    return found_degrees

def extract_major(text):
    """从文本中提取专业要求"""
    if pd.isna(text) or not isinstance(text, str):
        return []
    
    text_lower = text.lower()
    found_majors = []
    
    for major, keywords in MAJOR_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                found_majors.append(major)
                break
    
    return found_majors

def analyze_education_requirements(df):
    """分析学历要求"""
    print("\n正在分析学历要求...")
    
    all_degrees = []
    for text in df['专业要求'].dropna():
        degrees = extract_education(text)
        all_degrees.extend(degrees)
    
    if not all_degrees:
        return None, None
    
    degree_counts = pd.Series(all_degrees).value_counts()
    degree_percentages = (degree_counts / len(df) * 100).round(2)
    
    return degree_counts, degree_percentages

def analyze_major_requirements(df):
    """分析专业要求"""
    print("正在分析专业要求...")
    
    all_majors = []
    for text in df['专业要求'].dropna():
        majors = extract_major(text)
        all_majors.extend(majors)
    
    if not all_majors:
        return None, None
    
    major_counts = pd.Series(all_majors).value_counts()
    major_percentages = (major_counts / len(df) * 100).round(2)
    
    return major_counts, major_percentages

def extract_salary_value(salary_str):
    """从薪资字符串中提取数值"""
    if pd.isna(salary_str) or not isinstance(salary_str, str):
        return None
    numbers = re.findall(r'\d+', salary_str.replace(',', ''))
    if numbers:
        return float(numbers[0])
    return None

def generate_charts(df, df_level1, df_level2, output_dir):
    """生成所有图表"""
    chart_files = []
    
    # 1. Relevance Level分布
    fig, ax = plt.subplots(figsize=(8, 6))
    if available_font:
        plt.rcParams['font.sans-serif'] = [available_font]
    level_counts = df['relevance level'].value_counts().sort_index()
    colors = ['#FF6B6B', '#4ECDC4']
    bars = ax.bar(level_counts.index.astype(str), level_counts.values, color=colors, alpha=0.7, edgecolor='black')
    ax.set_xlabel('Relevance Level', fontsize=12, fontfamily=available_font if available_font else 'sans-serif')
    ax.set_ylabel('职位数量', fontsize=12, fontfamily=available_font if available_font else 'sans-serif')
    ax.set_title('AI相关职位Relevance Level分布', fontsize=14, fontweight='bold', fontfamily=available_font if available_font else 'sans-serif')
    ax.set_xticks(range(len(level_counts)))
    ax.set_xticklabels(['Level 1 (最相关)', 'Level 2 (关联)'])
    for i, (idx, val) in enumerate(level_counts.items()):
        ax.text(i, val + 50, f'{val}\n({val/len(df)*100:.1f}%)', 
                ha='center', va='bottom', fontsize=11, fontweight='bold')
    plt.tight_layout()
    chart1 = os.path.join(output_dir, 'chart1_relevance_level.png')
    plt.savefig(chart1, dpi=150, bbox_inches='tight')
    plt.close()
    chart_files.append(chart1)
    
    # 2. 职位分布（合并）
    job_counts = df['职位名称'].value_counts().head(15)
    fig, ax = plt.subplots(figsize=(10, 8))
    if available_font:
        plt.rcParams['font.sans-serif'] = [available_font]
    colors = sns.color_palette("husl", len(job_counts))
    bars = ax.barh(range(len(job_counts)), job_counts.values, color=colors)
    ax.set_yticks(range(len(job_counts)))
    ax.set_yticklabels(job_counts.index, fontsize=9, fontfamily=available_font if available_font else 'sans-serif')
    ax.set_xlabel('职位数量', fontsize=12, fontfamily=available_font if available_font else 'sans-serif')
    ax.set_title('Top 15 职位类型分布（合并分析）', fontsize=14, fontweight='bold', fontfamily=available_font if available_font else 'sans-serif')
    ax.invert_yaxis()
    for i, (idx, val) in enumerate(job_counts.items()):
        ax.text(val + 5, i, f'{val} ({val/len(df)*100:.2f}%)', 
                va='center', fontsize=9)
    plt.tight_layout()
    chart2 = os.path.join(output_dir, 'chart2_jobs_merged.png')
    plt.savefig(chart2, dpi=150, bbox_inches='tight')
    plt.close()
    chart_files.append(chart2)
    
    # 3. 职位分布对比（Level 1 vs Level 2）
    job1 = df_level1['职位名称'].value_counts().head(10)
    job2 = df_level2['职位名称'].value_counts().head(10)
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    if available_font:
        plt.rcParams['font.sans-serif'] = [available_font]
    
    colors1 = sns.color_palette("Reds", len(job1))
    axes[0].barh(range(len(job1)), job1.values, color=colors1)
    axes[0].set_yticks(range(len(job1)))
    axes[0].set_yticklabels(job1.index, fontsize=8, fontfamily=available_font if available_font else 'sans-serif')
    axes[0].set_xlabel('职位数量', fontsize=11, fontfamily=available_font if available_font else 'sans-serif')
    axes[0].set_title('Level 1 (最相关) Top 10 职位', fontsize=12, fontweight='bold', fontfamily=available_font if available_font else 'sans-serif')
    axes[0].invert_yaxis()
    
    colors2 = sns.color_palette("Blues", len(job2))
    axes[1].barh(range(len(job2)), job2.values, color=colors2)
    axes[1].set_yticks(range(len(job2)))
    axes[1].set_yticklabels(job2.index, fontsize=8, fontfamily=available_font if available_font else 'sans-serif')
    axes[1].set_xlabel('职位数量', fontsize=11, fontfamily=available_font if available_font else 'sans-serif')
    axes[1].set_title('Level 2 (关联) Top 10 职位', fontsize=12, fontweight='bold', fontfamily=available_font if available_font else 'sans-serif')
    axes[1].invert_yaxis()
    
    plt.tight_layout()
    chart3 = os.path.join(output_dir, 'chart3_jobs_comparison.png')
    plt.savefig(chart3, dpi=150, bbox_inches='tight')
    plt.close()
    chart_files.append(chart3)
    
    # 4. 公司分布
    company_counts = df['公司名称'].value_counts().head(15)
    fig, ax = plt.subplots(figsize=(10, 8))
    if available_font:
        plt.rcParams['font.sans-serif'] = [available_font]
    colors = sns.color_palette("muted", len(company_counts))
    bars = ax.barh(range(len(company_counts)), company_counts.values, color=colors)
    ax.set_yticks(range(len(company_counts)))
    ax.set_yticklabels(company_counts.index, fontsize=9, fontfamily=available_font if available_font else 'sans-serif')
    ax.set_xlabel('职位数量', fontsize=12, fontfamily=available_font if available_font else 'sans-serif')
    ax.set_title('Top 15 公司职位发布数量', fontsize=14, fontweight='bold', fontfamily=available_font if available_font else 'sans-serif')
    ax.invert_yaxis()
    for i, (idx, val) in enumerate(company_counts.items()):
        ax.text(val + 1, i, f'{val} ({val/len(df)*100:.2f}%)', 
                va='center', fontsize=8)
    plt.tight_layout()
    chart4 = os.path.join(output_dir, 'chart4_companies.png')
    plt.savefig(chart4, dpi=150, bbox_inches='tight')
    plt.close()
    chart_files.append(chart4)
    
    # 5. 地理位置分布
    location_counts = df['地点'].value_counts().head(15)
    fig, ax = plt.subplots(figsize=(10, 8))
    if available_font:
        plt.rcParams['font.sans-serif'] = [available_font]
    colors = sns.color_palette("coolwarm", len(location_counts))
    bars = ax.barh(range(len(location_counts)), location_counts.values, color=colors)
    ax.set_yticks(range(len(location_counts)))
    ax.set_yticklabels(location_counts.index, fontsize=9, fontfamily=available_font if available_font else 'sans-serif')
    ax.set_xlabel('职位数量', fontsize=12, fontfamily=available_font if available_font else 'sans-serif')
    ax.set_title('Top 15 地理位置职位分布', fontsize=14, fontweight='bold', fontfamily=available_font if available_font else 'sans-serif')
    ax.invert_yaxis()
    for i, (idx, val) in enumerate(location_counts.items()):
        ax.text(val + 1, i, f'{val} ({val/len(df)*100:.2f}%)', 
                va='center', fontsize=8)
    plt.tight_layout()
    chart5 = os.path.join(output_dir, 'chart5_locations.png')
    plt.savefig(chart5, dpi=150, bbox_inches='tight')
    plt.close()
    chart_files.append(chart5)
    
    # 6. 薪资分布
    salary_estimates = df['年薪预估值'].dropna()
    salary_values = []
    for val in salary_estimates:
        if isinstance(val, (int, float)):
            salary_values.append(float(val))
        elif isinstance(val, str):
            extracted = extract_salary_value(val)
            if extracted:
                salary_values.append(extracted)
    
    if salary_values:
        salary_series = pd.Series(salary_values)
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        if available_font:
            plt.rcParams['font.sans-serif'] = [available_font]
        axes[0].hist(salary_series, bins=50, color='coral', edgecolor='black', alpha=0.7)
        axes[0].axvline(salary_series.mean(), color='red', linestyle='--', linewidth=2, 
                        label=f'平均值: ${salary_series.mean():,.0f}')
        axes[0].axvline(salary_series.median(), color='green', linestyle='--', linewidth=2, 
                        label=f'中位数: ${salary_series.median():,.0f}')
        axes[0].set_xlabel('年薪（美元）', fontsize=11, fontfamily=available_font if available_font else 'sans-serif')
        axes[0].set_ylabel('频数', fontsize=11, fontfamily=available_font if available_font else 'sans-serif')
        axes[0].set_title('年薪分布直方图', fontsize=12, fontweight='bold', fontfamily=available_font if available_font else 'sans-serif')
        axes[0].legend(fontsize=9, prop={'family': available_font if available_font else 'sans-serif'})
        axes[0].grid(True, alpha=0.3)
        
        box_data = [salary_series]
        axes[1].boxplot(box_data, vert=True, patch_artist=True,
                        boxprops=dict(facecolor='lightcoral', alpha=0.7),
                        medianprops=dict(color='red', linewidth=2))
        axes[1].set_ylabel('年薪（美元）', fontsize=11, fontfamily=available_font if available_font else 'sans-serif')
        axes[1].set_title('年薪箱线图', fontsize=12, fontweight='bold', fontfamily=available_font if available_font else 'sans-serif')
        axes[1].set_xticklabels(['年薪'], fontfamily=available_font if available_font else 'sans-serif')
        axes[1].grid(True, alpha=0.3)
        plt.tight_layout()
        chart6 = os.path.join(output_dir, 'chart6_salary.png')
        plt.savefig(chart6, dpi=150, bbox_inches='tight')
        plt.close()
        chart_files.append(chart6)
    
    # 7. 学历要求分布
    degree_counts, degree_percentages = analyze_education_requirements(df)
    if degree_counts is not None and len(degree_counts) > 0:
        fig, ax = plt.subplots(figsize=(10, 6))
        if available_font:
            plt.rcParams['font.sans-serif'] = [available_font]
        colors = sns.color_palette("Set2", len(degree_counts))
        bars = ax.bar(range(len(degree_counts)), degree_counts.values, color=colors, alpha=0.7, edgecolor='black')
        ax.set_xticks(range(len(degree_counts)))
        ax.set_xticklabels(degree_counts.index, fontsize=10, fontfamily=available_font if available_font else 'sans-serif', rotation=15, ha='right')
        ax.set_ylabel('职位数量', fontsize=12, fontfamily=available_font if available_font else 'sans-serif')
        ax.set_title('学历要求分布', fontsize=14, fontweight='bold', fontfamily=available_font if available_font else 'sans-serif')
        for i, (idx, val) in enumerate(degree_counts.items()):
            ax.text(i, val + max(degree_counts.values)*0.01, f'{val}\n({degree_percentages[idx]:.1f}%)', 
                    ha='center', va='bottom', fontsize=10, fontweight='bold')
        plt.tight_layout()
        chart7 = os.path.join(output_dir, 'chart7_education.png')
        plt.savefig(chart7, dpi=150, bbox_inches='tight')
        plt.close()
        chart_files.append(chart7)
    
    # 8. 专业要求分布
    major_counts, major_percentages = analyze_major_requirements(df)
    if major_counts is not None and len(major_counts) > 0:
        top_majors = major_counts.head(10)
        fig, ax = plt.subplots(figsize=(10, 6))
        if available_font:
            plt.rcParams['font.sans-serif'] = [available_font]
        colors = sns.color_palette("viridis", len(top_majors))
        bars = ax.barh(range(len(top_majors)), top_majors.values, color=colors, alpha=0.7, edgecolor='black')
        ax.set_yticks(range(len(top_majors)))
        ax.set_yticklabels(top_majors.index, fontsize=10, fontfamily=available_font if available_font else 'sans-serif')
        ax.set_xlabel('职位数量', fontsize=12, fontfamily=available_font if available_font else 'sans-serif')
        ax.set_title('Top 10 专业要求分布', fontsize=14, fontweight='bold', fontfamily=available_font if available_font else 'sans-serif')
        ax.invert_yaxis()
        for i, (idx, val) in enumerate(top_majors.items()):
            ax.text(val + max(top_majors.values)*0.01, i, f'{val} ({major_percentages[idx]:.1f}%)', 
                    va='center', fontsize=9)
        plt.tight_layout()
        chart8 = os.path.join(output_dir, 'chart8_major.png')
        plt.savefig(chart8, dpi=150, bbox_inches='tight')
        plt.close()
        chart_files.append(chart8)
    
    # 9. 公司规模分布
    company_size = df['公司规模'].dropna()
    if len(company_size) > 0:
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        if available_font:
            plt.rcParams['font.sans-serif'] = [available_font]
        axes[0].hist(company_size, bins=50, color='steelblue', edgecolor='black', alpha=0.7)
        axes[0].axvline(company_size.mean(), color='red', linestyle='--', linewidth=2, 
                        label=f'平均值: {company_size.mean():.0f}')
        axes[0].axvline(company_size.median(), color='green', linestyle='--', linewidth=2, 
                        label=f'中位数: {company_size.median():.0f}')
        axes[0].set_xlabel('公司规模（员工数）', fontsize=11, fontfamily=available_font if available_font else 'sans-serif')
        axes[0].set_ylabel('频数', fontsize=11, fontfamily=available_font if available_font else 'sans-serif')
        axes[0].set_title('公司规模分布直方图', fontsize=12, fontweight='bold', fontfamily=available_font if available_font else 'sans-serif')
        axes[0].legend(fontsize=9, prop={'family': available_font if available_font else 'sans-serif'})
        axes[0].grid(True, alpha=0.3)
        
        box_data = [company_size]
        axes[1].boxplot(box_data, vert=True, patch_artist=True,
                        boxprops=dict(facecolor='lightblue', alpha=0.7),
                        medianprops=dict(color='red', linewidth=2))
        axes[1].set_ylabel('公司规模（员工数）', fontsize=11, fontfamily=available_font if available_font else 'sans-serif')
        axes[1].set_title('公司规模箱线图', fontsize=12, fontweight='bold', fontfamily=available_font if available_font else 'sans-serif')
        axes[1].set_xticklabels(['公司规模'], fontfamily=available_font if available_font else 'sans-serif')
        axes[1].grid(True, alpha=0.3)
        plt.tight_layout()
        chart9 = os.path.join(output_dir, 'chart9_company_size.png')
        plt.savefig(chart9, dpi=150, bbox_inches='tight')
        plt.close()
        chart_files.append(chart9)
    
    return chart_files

def generate_text_report(df, df_level1, df_level2, degree_counts, degree_percentages, 
                        major_counts, major_percentages, output_file):
    """生成文本分析报告"""
    report_lines = []
    
    report_lines.append("=" * 80)
    report_lines.append("Final Merged Report 系统分析报告")
    report_lines.append("=" * 80)
    report_lines.append(f"报告生成时间: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}")
    report_lines.append("")
    report_lines.append("本报告基于Final_Merged_Report_1的final_merged_report.xlsx数据，")
    report_lines.append("采用统计学方法对AI相关职位数据进行全面分析。")
    report_lines.append("")
    report_lines.append("=" * 80)
    report_lines.append("")
    
    # 执行摘要
    report_lines.append("执行摘要")
    report_lines.append("")
    report_lines.append(f"本次分析共涵盖 {len(df):,} 条职位记录，涉及 {df['公司名称'].nunique():,} 家不同的公司。")
    report_lines.append(f"其中，Relevance Level 1（最相关）职位 {len(df_level1):,} 条，占比 {len(df_level1)/len(df)*100:.2f}%；")
    report_lines.append(f"Relevance Level 2（关联）职位 {len(df_level2):,} 条，占比 {len(df_level2)/len(df)*100:.2f}%。")
    report_lines.append("")
    
    # 数据质量评估
    report_lines.append("数据质量评估")
    report_lines.append("")
    total_cells = len(df) * len(df.columns)
    missing_cells = df.isnull().sum().sum()
    completeness = ((total_cells - missing_cells) / total_cells * 100) if total_cells > 0 else 0
    report_lines.append(f"整体数据完整度达到 {completeness:.2f}%，表明数据质量较高。")
    report_lines.append("")
    
    # Relevance Level分析
    report_lines.append("=" * 80)
    report_lines.append("一、Relevance Level 分析")
    report_lines.append("=" * 80)
    report_lines.append("")
    report_lines.append("1. 整体分布")
    report_lines.append("")
    level_counts = df['relevance level'].value_counts().sort_index()
    for level, count in level_counts.items():
        level_name = "最相关" if level == 1 else "关联"
        report_lines.append(f"  Relevance Level {level} ({level_name}): {count:,} 条 ({count/len(df)*100:.2f}%)")
    report_lines.append("")
    
    # 合并分析
    report_lines.append("2. 合并分析（Level 1 + Level 2）")
    report_lines.append("")
    report_lines.append("2.1 职位分布特征")
    report_lines.append("")
    job_counts = df['职位名称'].value_counts()
    report_lines.append(f"职位名称的多样性很高，共有 {df['职位名称'].nunique():,} 种不同的职位名称。")
    report_lines.append("排名前五的职位类型及其出现频率如下：")
    for i, (job, count) in enumerate(job_counts.head(5).items(), 1):
        report_lines.append(f"  {i}. {job}: {count} 次 ({count/len(df)*100:.2f}%)")
    report_lines.append("")
    
    report_lines.append("2.2 公司分布特征")
    report_lines.append("")
    company_counts = df['公司名称'].value_counts()
    report_lines.append(f"数据涉及 {df['公司名称'].nunique():,} 家不同的公司。")
    report_lines.append("发布职位数量排名前五的公司：")
    for i, (company, count) in enumerate(company_counts.head(5).items(), 1):
        report_lines.append(f"  {i}. {company}: {count} 个职位 ({count/len(df)*100:.2f}%)")
    report_lines.append("")
    
    report_lines.append("2.3 地理位置分布")
    report_lines.append("")
    location_counts = df['地点'].value_counts()
    report_lines.append(f"职位分布覆盖 {df['地点'].nunique():,} 个不同的地理位置。")
    report_lines.append("职位数量最多的前五个城市：")
    for i, (location, count) in enumerate(location_counts.head(5).items(), 1):
        report_lines.append(f"  {i}. {location}: {count} 个职位 ({count/len(df)*100:.2f}%)")
    report_lines.append("")
    
    # 分别分析
    report_lines.append("3. 分别分析")
    report_lines.append("")
    
    report_lines.append("3.1 Level 1 (最相关) 职位分析")
    report_lines.append("")
    job1_counts = df_level1['职位名称'].value_counts()
    report_lines.append(f"共有 {df_level1['职位名称'].nunique():,} 种不同的职位名称。")
    report_lines.append("排名前五的职位类型：")
    for i, (job, count) in enumerate(job1_counts.head(5).items(), 1):
        report_lines.append(f"  {i}. {job}: {count} 次 ({count/len(df_level1)*100:.2f}%)")
    report_lines.append("")
    
    report_lines.append("3.2 Level 2 (关联) 职位分析")
    report_lines.append("")
    job2_counts = df_level2['职位名称'].value_counts()
    report_lines.append(f"共有 {df_level2['职位名称'].nunique():,} 种不同的职位名称。")
    report_lines.append("排名前五的职位类型：")
    for i, (job, count) in enumerate(job2_counts.head(5).items(), 1):
        report_lines.append(f"  {i}. {job}: {count} 次 ({count/len(df_level2)*100:.2f}%)")
    report_lines.append("")
    
    # 薪资分析
    report_lines.append("=" * 80)
    report_lines.append("二、薪资水平分析")
    report_lines.append("=" * 80)
    report_lines.append("")
    salary_estimates = df['年薪预估值'].dropna()
    salary_values = []
    for val in salary_estimates:
        if isinstance(val, (int, float)):
            salary_values.append(float(val))
        elif isinstance(val, str):
            extracted = extract_salary_value(val)
            if extracted:
                salary_values.append(extracted)
    
    if salary_values:
        salary_series = pd.Series(salary_values)
        report_lines.append(f"在 {len(salary_series):,} 条有效薪资记录中，年薪预估值的分布情况如下：")
        report_lines.append("")
        report_lines.append(f"平均年薪约为 ${salary_series.mean():,.0f}，中位数为 ${salary_series.median():,.0f}。")
        report_lines.append(f"从分位数来看，25%的职位年薪在 ${salary_series.quantile(0.25):,.0f} 以下，")
        report_lines.append(f"50%的职位年薪在 ${salary_series.median():,.0f} 以下，")
        report_lines.append(f"75%的职位年薪在 ${salary_series.quantile(0.75):,.0f} 以下。")
        report_lines.append(f"年薪范围从最低的 ${salary_series.min():,.0f} 到最高的 ${salary_series.max():,.0f}。")
        report_lines.append("")
    
    # 公司规模分析
    report_lines.append("=" * 80)
    report_lines.append("三、公司规模统计分析")
    report_lines.append("=" * 80)
    report_lines.append("")
    company_size = df['公司规模'].dropna()
    if len(company_size) > 0:
        report_lines.append(f"在 {len(company_size):,} 条有效记录中，公司规模呈现出明显的右偏分布特征。")
        report_lines.append(f"公司规模的平均值为 {company_size.mean():.0f} 人，但中位数仅为 {company_size.median():.0f} 人，")
        report_lines.append("这表明存在少数大型公司显著拉高了平均值。")
        report_lines.append(f"从四分位数来看，25%的公司规模在 {company_size.quantile(0.25):.0f} 人以下，")
        report_lines.append(f"50%的公司规模在 {company_size.median():.0f} 人以下，")
        report_lines.append(f"75%的公司规模在 {company_size.quantile(0.75):.0f} 人以下。")
        report_lines.append("")
    
    # 专业要求分析
    report_lines.append("=" * 80)
    report_lines.append("四、专业要求分析")
    report_lines.append("=" * 80)
    report_lines.append("")
    
    # 学历要求
    report_lines.append("4.1 学历要求统计")
    report_lines.append("")
    if degree_counts is not None and len(degree_counts) > 0:
        report_lines.append("通过关键词筛选方法，从专业要求字段中提取的学历要求分布如下：")
        report_lines.append("")
        for degree, count in degree_counts.items():
            report_lines.append(f"  {degree}: {count} 次 ({degree_percentages[degree]:.2f}%)")
        report_lines.append("")
        report_lines.append("注：一个职位可能包含多个学历要求关键词，因此总数可能超过职位总数。")
        report_lines.append("")
    else:
        report_lines.append("未能从专业要求字段中提取到明确的学历要求信息。")
        report_lines.append("")
    
    # 专业要求
    report_lines.append("4.2 专业要求统计")
    report_lines.append("")
    if major_counts is not None and len(major_counts) > 0:
        report_lines.append("通过关键词筛选方法，从专业要求字段中提取的专业要求分布如下：")
        report_lines.append("")
        for major, count in major_counts.head(15).items():
            report_lines.append(f"  {major}: {count} 次 ({major_percentages[major]:.2f}%)")
        report_lines.append("")
        report_lines.append("注：一个职位可能包含多个专业要求关键词，因此总数可能超过职位总数。")
        report_lines.append("")
    else:
        report_lines.append("未能从专业要求字段中提取到明确的专业要求信息。")
        report_lines.append("")
    
    # 主要发现
    report_lines.append("=" * 80)
    report_lines.append("主要发现与洞察")
    report_lines.append("=" * 80)
    report_lines.append("")
    findings = [
        f"职位集中度：AI相关职位市场呈现高度多样性，共有{df['职位名称'].nunique():,}种不同的职位名称，反映了市场对AI技能需求的细化和专业化趋势。",
        f"Relevance Level分布：Level 1（最相关）职位占比{len(df_level1)/len(df)*100:.2f}%，Level 2（关联）职位占比{len(df_level2)/len(df)*100:.2f}%，两者分布相对均衡。",
        f"公司分布：市场参与者众多，共涉及{df['公司名称'].nunique():,}家公司，职位发布相对分散，体现了市场的竞争性。",
        f"地理分布：职位分布覆盖{df['地点'].nunique():,}个不同地理位置，主要集中在科技产业发达的大城市。",
        f"公司规模：市场由大量中小型公司和少数大型公司组成，公司规模呈现明显的右偏分布。",
    ]
    if salary_values:
        salary_series = pd.Series(salary_values)
        findings.append(f"薪资水平：年薪中位数为${salary_series.median():,.0f}，显示出相对较高的薪资水平，符合AI领域的市场定位。")
    if degree_counts is not None and len(degree_counts) > 0:
        top_degree = degree_counts.index[0]
        findings.append(f"学历要求：最常见的学历要求是{top_degree}，占比{degree_percentages[top_degree]:.2f}%。")
    if major_counts is not None and len(major_counts) > 0:
        top_major = major_counts.index[0]
        findings.append(f"专业要求：最常见的专业要求是{top_major}，占比{major_percentages[top_major]:.2f}%。")
    
    for i, finding in enumerate(findings, 1):
        report_lines.append(f"{i}. {finding}")
        report_lines.append("")
    
    # 写入文件
    report_content = "\n".join(report_lines)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"\n文本报告已生成: {output_file}")
    return report_content

def create_pdf_report(df, df_level1, df_level2, chart_files, degree_counts, degree_percentages,
                     major_counts, major_percentages, output_path):
    """创建PDF报告"""
    doc = SimpleDocTemplate(output_path, pagesize=A4,
                           rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=18)
    
    story = []
    styles = getSampleStyleSheet()
    
    chinese_font_name = 'ChineseFont' if 'ChineseFont' in pdfmetrics.getRegisteredFontNames() else 'Helvetica'
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=HexColor('#1a1a1a'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName=chinese_font_name
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=HexColor('#2c3e50'),
        spaceAfter=12,
        spaceBefore=20,
        fontName=chinese_font_name
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=11,
        textColor=HexColor('#333333'),
        spaceAfter=12,
        leading=16,
        alignment=TA_JUSTIFY,
        fontName=chinese_font_name
    )
    
    # 标题
    story.append(Paragraph("Final Merged Report 系统分析报告", title_style))
    story.append(Spacer(1, 0.3*inch))
    
    # 执行摘要
    story.append(Paragraph("执行摘要", heading_style))
    summary_text = f"""
    本报告基于Final_Merged_Report_1的final_merged_report.xlsx数据，采用统计学方法对AI相关职位数据进行全面分析。
    本次分析共涵盖 {len(df):,} 条职位记录，涉及 {df['公司名称'].nunique():,} 家不同的公司。
    其中，Relevance Level 1（最相关）职位 {len(df_level1):,} 条，占比 {len(df_level1)/len(df)*100:.2f}%；
    Relevance Level 2（关联）职位 {len(df_level2):,} 条，占比 {len(df_level2)/len(df)*100:.2f}%。
    """
    story.append(Paragraph(summary_text.strip(), normal_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Relevance Level分析
    story.append(Paragraph("一、Relevance Level 分析", heading_style))
    if len(chart_files) > 0:
        story.append(Image(chart_files[0], width=5*inch, height=3.75*inch))
        story.append(Spacer(1, 0.1*inch))
    
    level_text = f"""
    Relevance Level分布显示，Level 1（最相关）职位 {len(df_level1):,} 条，Level 2（关联）职位 {len(df_level2):,} 条。
    两者分布相对均衡，反映了AI相关职位市场的多样性。
    """
    story.append(Paragraph(level_text.strip(), normal_style))
    story.append(Spacer(1, 0.2*inch))
    
    # 职位分布（合并）
    story.append(Paragraph("二、职位分布特征分析（合并）", heading_style))
    if len(chart_files) > 1:
        story.append(Image(chart_files[1], width=6*inch, height=4.8*inch))
        story.append(Spacer(1, 0.1*inch))
    
    job_counts = df['职位名称'].value_counts()
    job_text = f"""
    职位名称的多样性很高，共有 {df['职位名称'].nunique():,} 种不同的职位名称。
    最常见的职位是 {job_counts.index[0]}，共出现 {job_counts.iloc[0]} 次，占比 {job_counts.iloc[0]/len(df)*100:.2f}%。
    排名前五的职位类型包括：{', '.join(job_counts.head(5).index.tolist())}。
    """
    story.append(Paragraph(job_text.strip(), normal_style))
    story.append(Spacer(1, 0.2*inch))
    
    # 职位分布对比
    story.append(Paragraph("三、职位分布对比（Level 1 vs Level 2）", heading_style))
    if len(chart_files) > 2:
        story.append(Image(chart_files[2], width=7*inch, height=3*inch))
        story.append(Spacer(1, 0.1*inch))
    
    comparison_text = f"""
    Level 1（最相关）职位共有 {df_level1['职位名称'].nunique():,} 种不同的职位名称，
    最常见的职位是 {df_level1['职位名称'].value_counts().index[0]}。
    Level 2（关联）职位共有 {df_level2['职位名称'].nunique():,} 种不同的职位名称，
    最常见的职位是 {df_level2['职位名称'].value_counts().index[0]}。
    """
    story.append(Paragraph(comparison_text.strip(), normal_style))
    story.append(Spacer(1, 0.2*inch))
    
    # 公司分布
    story.append(Paragraph("四、公司分布特征", heading_style))
    if len(chart_files) > 3:
        story.append(Image(chart_files[3], width=6*inch, height=4.8*inch))
        story.append(Spacer(1, 0.1*inch))
    
    company_counts = df['公司名称'].value_counts()
    company_text = f"""
    数据涉及 {df['公司名称'].nunique():,} 家不同的公司，其中发布职位最多的公司是 {company_counts.index[0]}，
    共发布 {company_counts.iloc[0]} 个职位，占比 {company_counts.iloc[0]/len(df)*100:.2f}%。
    """
    story.append(Paragraph(company_text.strip(), normal_style))
    story.append(Spacer(1, 0.2*inch))
    
    # 地理位置分布
    story.append(Paragraph("五、地理位置分布", heading_style))
    if len(chart_files) > 4:
        story.append(Image(chart_files[4], width=6*inch, height=4.8*inch))
        story.append(Spacer(1, 0.1*inch))
    
    location_counts = df['地点'].value_counts()
    location_text = f"""
    职位分布覆盖 {df['地点'].nunique():,} 个不同的地理位置。
    职位数量最多的城市是 {location_counts.index[0]}，共 {location_counts.iloc[0]} 个职位。
    """
    story.append(Paragraph(location_text.strip(), normal_style))
    story.append(Spacer(1, 0.2*inch))
    
    # 薪资分析
    if len(chart_files) > 5:
        story.append(Paragraph("六、薪资水平分析", heading_style))
        story.append(Image(chart_files[5], width=7*inch, height=2.5*inch))
        story.append(Spacer(1, 0.1*inch))
        
        salary_estimates = df['年薪预估值'].dropna()
        salary_values = []
        for val in salary_estimates:
            if isinstance(val, (int, float)):
                salary_values.append(float(val))
            elif isinstance(val, str):
                extracted = extract_salary_value(val)
                if extracted:
                    salary_values.append(extracted)
        
        if salary_values:
            salary_series = pd.Series(salary_values)
            salary_text = f"""
            在 {len(salary_series):,} 条有效薪资记录中，年薪预估值的平均值为 ${salary_series.mean():,.0f}，中位数为 ${salary_series.median():,.0f}。
            从分位数来看，25%的职位年薪在 ${salary_series.quantile(0.25):,.0f} 以下，75%的职位年薪在 ${salary_series.quantile(0.75):,.0f} 以下。
            """
            story.append(Paragraph(salary_text.strip(), normal_style))
            story.append(Spacer(1, 0.2*inch))
    
    # 学历要求
    if len(chart_files) > 6 and degree_counts is not None and len(degree_counts) > 0:
        story.append(Paragraph("七、学历要求分析", heading_style))
        story.append(Image(chart_files[6], width=6*inch, height=3.6*inch))
        story.append(Spacer(1, 0.1*inch))
        
        degree_text = "通过关键词筛选方法，从专业要求字段中提取的学历要求分布如下："
        for degree, count in degree_counts.items():
            degree_text += f" {degree} ({degree_percentages[degree]:.2f}%)；"
        degree_text = degree_text.rstrip('；') + "。"
        story.append(Paragraph(degree_text.strip(), normal_style))
        story.append(Spacer(1, 0.2*inch))
    
    # 专业要求
    if len(chart_files) > 7 and major_counts is not None and len(major_counts) > 0:
        story.append(Paragraph("八、专业要求分析", heading_style))
        story.append(Image(chart_files[7], width=6*inch, height=3.6*inch))
        story.append(Spacer(1, 0.1*inch))
        
        major_text = "通过关键词筛选方法，从专业要求字段中提取的专业要求分布如下："
        for major, count in major_counts.head(5).items():
            major_text += f" {major} ({major_percentages[major]:.2f}%)；"
        major_text = major_text.rstrip('；') + "。"
        story.append(Paragraph(major_text.strip(), normal_style))
        story.append(Spacer(1, 0.2*inch))
    
    # 公司规模
    if len(chart_files) > 8:
        story.append(Paragraph("九、公司规模统计分析", heading_style))
        story.append(Image(chart_files[8], width=7*inch, height=2.5*inch))
        story.append(Spacer(1, 0.1*inch))
        
        company_size = df['公司规模'].dropna()
        if len(company_size) > 0:
            size_text = f"""
            在 {len(company_size):,} 条有效记录中，公司规模的平均值为 {company_size.mean():.0f} 人，
            中位数为 {company_size.median():.0f} 人，呈现出明显的右偏分布特征。
            """
            story.append(Paragraph(size_text.strip(), normal_style))
            story.append(Spacer(1, 0.2*inch))
    
    # 主要发现
    story.append(PageBreak())
    story.append(Paragraph("主要发现与总结", heading_style))
    
    findings = [
        f"职位集中度：AI相关职位市场呈现高度多样性，共有{df['职位名称'].nunique():,}种不同的职位名称。",
        f"Relevance Level分布：Level 1和Level 2职位分布相对均衡，反映了市场的多样性。",
        f"公司分布：市场参与者众多，共涉及{df['公司名称'].nunique():,}家公司。",
        f"地理分布：职位分布覆盖{df['地点'].nunique():,}个不同地理位置。",
    ]
    if degree_counts is not None and len(degree_counts) > 0:
        top_degree = degree_counts.index[0]
        findings.append(f"学历要求：最常见的学历要求是{top_degree}，占比{degree_percentages[top_degree]:.2f}%。")
    if major_counts is not None and len(major_counts) > 0:
        top_major = major_counts.index[0]
        findings.append(f"专业要求：最常见的专业要求是{top_major}，占比{major_percentages[top_major]:.2f}%。")
    
    for i, finding in enumerate(findings, 1):
        story.append(Paragraph(f"{i}. {finding}", normal_style))
        story.append(Spacer(1, 0.1*inch))
    
    doc.build(story)
    print(f"PDF报告已生成: {output_path}")

def main():
    print("="*80)
    print("Final Merged Report 系统分析")
    print("="*80)
    
    # 读取数据
    print(f"\n正在读取文件: {EXCEL_FILE}")
    df = pd.read_excel(EXCEL_FILE)
    print(f"数据加载完成：{len(df)} 条记录，{len(df.columns)} 个字段")
    
    # 按relevance level分组
    df_level1 = df[df['relevance level'] == 1].copy()
    df_level2 = df[df['relevance level'] == 2].copy()
    print(f"\nRelevance Level分布:")
    print(f"  Level 1 (最相关): {len(df_level1)} 条 ({len(df_level1)/len(df)*100:.2f}%)")
    print(f"  Level 2 (关联): {len(df_level2)} 条 ({len(df_level2)/len(df)*100:.2f}%)")
    
    # 分析专业要求
    degree_counts, degree_percentages = analyze_education_requirements(df)
    major_counts, major_percentages = analyze_major_requirements(df)
    
    # 生成图表
    print("\n正在生成图表...")
    chart_files = generate_charts(df, df_level1, df_level2, OUTPUT_DIR)
    print(f"已生成 {len(chart_files)} 个图表")
    
    # 生成文本报告
    print("\n正在生成文本报告...")
    text_report_path = os.path.join(OUTPUT_DIR, "Final_Merged_Report_Analysis.txt")
    generate_text_report(df, df_level1, df_level2, degree_counts, degree_percentages,
                        major_counts, major_percentages, text_report_path)
    
    # 生成PDF报告
    print("\n正在生成PDF报告...")
    pdf_path = os.path.join(OUTPUT_DIR, "Final_Merged_Report_Analysis.pdf")
    create_pdf_report(df, df_level1, df_level2, chart_files, degree_counts, degree_percentages,
                     major_counts, major_percentages, pdf_path)
    
    print("\n" + "="*80)
    print("分析完成！所有结果已保存到:")
    print(f"  {OUTPUT_DIR}")
    print("="*80)

if __name__ == "__main__":
    main()
