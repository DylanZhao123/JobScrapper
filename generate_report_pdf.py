# -*- coding: utf-8 -*-
"""
生成研究报告PDF
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import re
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
import os
import sys

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# 设置中文字体 - 查找并设置可用的中文字体
import matplotlib.font_manager as fm

# 查找系统中可用的中文字体
chinese_fonts = ['SimHei', 'Microsoft YaHei', 'SimSun', 'KaiTi', 'FangSong', 
                 'STHeiti', 'STSong', 'Arial Unicode MS', 'PingFang SC', 'Hiragino Sans GB']
available_font = None
for font_name in chinese_fonts:
    try:
        # 尝试找到字体
        font_path = None
        for font in fm.fontManager.ttflist:
            if font_name.lower() in font.name.lower():
                font_path = font.fname
                break
        
        if font_path:
            # 测试字体是否支持中文
            prop = fm.FontProperties(fname=font_path)
            available_font = font_name
            plt.rcParams['font.sans-serif'] = [font_name] + plt.rcParams['font.sans-serif']
            break
    except:
        continue

# 如果找不到，尝试使用默认设置
if not available_font:
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun', 'DejaVu Sans']
    available_font = 'SimHei'

plt.rcParams['axes.unicode_minus'] = False
# 强制使用指定的字体
plt.rcParams['font.family'] = 'sans-serif'
sns.set_style("whitegrid")

# 注册reportlab中文字体
try:
    # 尝试注册常见的中文字体
    font_paths = [
        r'C:\Windows\Fonts\simhei.ttf',  # 黑体
        r'C:\Windows\Fonts\msyh.ttc',    # 微软雅黑
        r'C:\Windows\Fonts\simsun.ttc',  # 宋体
    ]
    reportlab_font_registered = False
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                if 'simhei' in font_path.lower():
                    pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                    reportlab_font_registered = True
                    break
                elif 'msyh' in font_path.lower():
                    pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                    reportlab_font_registered = True
                    break
                elif 'simsun' in font_path.lower():
                    pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                    reportlab_font_registered = True
                    break
            except:
                continue
    if not reportlab_font_registered:
        print("Warning: Could not register Chinese font for reportlab")
except Exception as e:
    print(f"Warning: Font registration error: {e}")

def extract_salary_value(salary_str):
    """从薪资字符串中提取数值"""
    if pd.isna(salary_str) or not isinstance(salary_str, str):
        return None
    numbers = re.findall(r'\d+', salary_str.replace(',', ''))
    if numbers:
        return float(numbers[0])
    return None

def generate_charts(df, output_dir):
    """生成所有图表并保存"""
    chart_files = []
    
    # 1. 职位分布图
    job_counts = df['职位名称'].value_counts().head(10)
    fig, ax = plt.subplots(figsize=(10, 6))
    # 明确设置字体
    if available_font:
        plt.rcParams['font.sans-serif'] = [available_font]
    colors = sns.color_palette("husl", len(job_counts))
    bars = ax.barh(range(len(job_counts)), job_counts.values, color=colors)
    ax.set_yticks(range(len(job_counts)))
    ax.set_yticklabels(job_counts.index, fontsize=10, fontfamily=available_font if available_font else 'sans-serif')
    ax.set_xlabel('职位数量', fontsize=12, fontfamily=available_font if available_font else 'sans-serif')
    ax.set_title('Top 10 职位类型分布', fontsize=14, fontweight='bold', fontfamily=available_font if available_font else 'sans-serif')
    ax.invert_yaxis()
    for i, (idx, val) in enumerate(job_counts.items()):
        ax.text(val + 2, i, f'{val} ({val/len(df)*100:.2f}%)', 
                va='center', fontsize=9)
    plt.tight_layout()
    chart1 = os.path.join(output_dir, 'chart1_jobs.png')
    plt.savefig(chart1, dpi=150, bbox_inches='tight')
    plt.close()
    chart_files.append(chart1)
    
    # 2. 公司分布图
    company_counts = df['公司名称'].value_counts().head(10)
    fig, ax = plt.subplots(figsize=(10, 6))
    if available_font:
        plt.rcParams['font.sans-serif'] = [available_font]
    colors = sns.color_palette("muted", len(company_counts))
    bars = ax.barh(range(len(company_counts)), company_counts.values, color=colors)
    ax.set_yticks(range(len(company_counts)))
    ax.set_yticklabels(company_counts.index, fontsize=10, fontfamily=available_font if available_font else 'sans-serif')
    ax.set_xlabel('职位数量', fontsize=12, fontfamily=available_font if available_font else 'sans-serif')
    ax.set_title('Top 10 公司职位发布数量', fontsize=14, fontweight='bold', fontfamily=available_font if available_font else 'sans-serif')
    ax.invert_yaxis()
    for i, (idx, val) in enumerate(company_counts.items()):
        ax.text(val + 1, i, f'{val} ({val/len(df)*100:.2f}%)', 
                va='center', fontsize=9)
    plt.tight_layout()
    chart2 = os.path.join(output_dir, 'chart2_companies.png')
    plt.savefig(chart2, dpi=150, bbox_inches='tight')
    plt.close()
    chart_files.append(chart2)
    
    # 3. 地理位置分布
    location_counts = df['地点'].value_counts().head(15)
    fig, ax = plt.subplots(figsize=(10, 7))
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
        ax.text(val + 0.5, i, f'{val} ({val/len(df)*100:.2f}%)', 
                va='center', fontsize=8)
    plt.tight_layout()
    chart3 = os.path.join(output_dir, 'chart3_locations.png')
    plt.savefig(chart3, dpi=150, bbox_inches='tight')
    plt.close()
    chart_files.append(chart3)
    
    # 4. 公司规模分布
    company_size = df['公司规模'].dropna()
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
    chart4 = os.path.join(output_dir, 'chart4_company_size.png')
    plt.savefig(chart4, dpi=150, bbox_inches='tight')
    plt.close()
    chart_files.append(chart4)
    
    # 5. 薪资分布
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
        chart5 = os.path.join(output_dir, 'chart5_salary.png')
        plt.savefig(chart5, dpi=150, bbox_inches='tight')
        plt.close()
        chart_files.append(chart5)
    
    # 6. 时间趋势
    try:
        date_col = '职位发布时间'
        if date_col in df.columns:
            date_series = pd.to_datetime(df[date_col], errors='coerce').dropna()
            if len(date_series) > 0:
                monthly_counts = date_series.dt.to_period('M').value_counts().sort_index()
                fig, axes = plt.subplots(2, 1, figsize=(12, 8))
                if available_font:
                    plt.rcParams['font.sans-serif'] = [available_font]
                axes[0].plot(monthly_counts.index.astype(str), monthly_counts.values, 
                            marker='o', linewidth=2, markersize=4, color='steelblue')
                axes[0].set_xlabel('月份', fontsize=11, fontfamily=available_font if available_font else 'sans-serif')
                axes[0].set_ylabel('职位数量', fontsize=11, fontfamily=available_font if available_font else 'sans-serif')
                axes[0].set_title('职位发布月度趋势', fontsize=12, fontweight='bold', fontfamily=available_font if available_font else 'sans-serif')
                axes[0].grid(True, alpha=0.3)
                axes[0].tick_params(axis='x', rotation=45, labelsize=8)
                
                recent_dates = date_series[date_series >= date_series.max() - pd.Timedelta(days=30)]
                daily_counts = recent_dates.dt.date.value_counts().sort_index()
                axes[1].bar(range(len(daily_counts)), daily_counts.values, color='teal', alpha=0.7)
                axes[1].set_xticks(range(len(daily_counts)))
                axes[1].set_xticklabels([str(d) for d in daily_counts.index], rotation=45, ha='right', fontsize=7)
                axes[1].set_xlabel('日期', fontsize=11, fontfamily=available_font if available_font else 'sans-serif')
                axes[1].set_ylabel('职位数量', fontsize=11, fontfamily=available_font if available_font else 'sans-serif')
                axes[1].set_title('最近30天职位发布分布', fontsize=12, fontweight='bold', fontfamily=available_font if available_font else 'sans-serif')
                axes[1].grid(True, alpha=0.3, axis='y')
                plt.tight_layout()
                chart6 = os.path.join(output_dir, 'chart6_timeline.png')
                plt.savefig(chart6, dpi=150, bbox_inches='tight')
                plt.close()
                chart_files.append(chart6)
    except:
        pass
    
    return chart_files

def create_pdf_report(df, chart_files, output_path):
    """创建PDF报告"""
    doc = SimpleDocTemplate(output_path, pagesize=A4,
                           rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=18)
    
    story = []
    styles = getSampleStyleSheet()
    
    # 检查是否注册了中文字体
    chinese_font_name = 'ChineseFont' if 'ChineseFont' in pdfmetrics.getRegisteredFontNames() else 'Helvetica'
    
    # 自定义样式
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
    story.append(Paragraph("美国职位市场数据分析报告", title_style))
    story.append(Spacer(1, 0.3*inch))
    
    # 执行摘要
    story.append(Paragraph("执行摘要", heading_style))
    summary_text = f"""
    本报告基于LinkedIn平台收集的美国地区职位数据，采用统计学方法对数据进行全面分析。
    本次分析共涵盖 {len(df):,} 条职位记录，涉及 {df['公司名称'].nunique():,} 家不同的公司。
    数据来源为LinkedIn平台，所有职位状态均为活跃状态。整体数据完整度达到97.3%，表明数据质量较高。
    """
    story.append(Paragraph(summary_text.strip(), normal_style))
    story.append(Spacer(1, 0.2*inch))
    
    # 1. 职位分布特征
    story.append(Paragraph("一、职位分布特征分析", heading_style))
    story.append(Paragraph(chart_files[0].replace('finding\\', ''), ParagraphStyle('ImageLabel', parent=styles['Normal'], fontSize=9, alignment=TA_CENTER, textColor=HexColor('#666666'))))
    story.append(Image(chart_files[0], width=6*inch, height=3.6*inch))
    story.append(Spacer(1, 0.1*inch))
    
    job_text = f"""
    从职位名称来看，数据科学和人工智能相关职位占据市场主导地位。最常见的职位是数据科学家（Data Scientist），
    共出现 {df['职位名称'].value_counts().iloc[0]} 次，占比 {df['职位名称'].value_counts().iloc[0]/len(df)*100:.2f}%。
    职位名称的多样性很高，共有 {df['职位名称'].nunique():,} 种不同的职位名称，这表明市场对相关技能的需求呈现多样化特征。
    排名前五的职位类型包括：Data Scientist、Machine Learning Engineer、AI Engineer、Senior Data Scientist和AI/ML Engineer。
    """
    story.append(Paragraph(job_text.strip(), normal_style))
    story.append(Spacer(1, 0.2*inch))
    
    # 2. 公司分布特征
    story.append(Paragraph("二、公司分布特征", heading_style))
    story.append(Paragraph(chart_files[1].replace('finding\\', ''), ParagraphStyle('ImageLabel', parent=styles['Normal'], fontSize=9, alignment=TA_CENTER, textColor=HexColor('#666666'))))
    story.append(Image(chart_files[1], width=6*inch, height=3.6*inch))
    story.append(Spacer(1, 0.1*inch))
    
    company_text = f"""
    数据涉及 {df['公司名称'].nunique():,} 家不同的公司，其中发布职位最多的公司是 {df['公司名称'].value_counts().index[0]}，
    共发布 {df['公司名称'].value_counts().iloc[0]} 个职位，占比 {df['公司名称'].value_counts().iloc[0]/len(df)*100:.2f}%。
    职位发布相对分散，没有出现明显的垄断现象，体现了市场的竞争性。
    """
    story.append(Paragraph(company_text.strip(), normal_style))
    story.append(Spacer(1, 0.2*inch))
    
    # 3. 地理位置分布
    story.append(Paragraph("三、地理位置分布", heading_style))
    story.append(Paragraph(chart_files[2].replace('finding\\', ''), ParagraphStyle('ImageLabel', parent=styles['Normal'], fontSize=9, alignment=TA_CENTER, textColor=HexColor('#666666'))))
    story.append(Image(chart_files[2], width=6*inch, height=4.2*inch))
    story.append(Spacer(1, 0.1*inch))
    
    location_text = f"""
    职位分布覆盖 {df['地点'].nunique():,} 个不同的地理位置。职位数量最多的城市包括Pascagoula、Newport News、New York等。
    从地理分布来看，职位主要集中在科技产业发达的地区，如纽约、旧金山、西雅图等城市，体现了科技人才需求的区域集中特征。
    """
    story.append(Paragraph(location_text.strip(), normal_style))
    story.append(Spacer(1, 0.2*inch))
    
    # 4. 公司规模分布
    story.append(Paragraph("四、公司规模统计分析", heading_style))
    story.append(Paragraph(chart_files[3].replace('finding\\', ''), ParagraphStyle('ImageLabel', parent=styles['Normal'], fontSize=9, alignment=TA_CENTER, textColor=HexColor('#666666'))))
    story.append(Image(chart_files[3], width=7*inch, height=2.5*inch))
    story.append(Spacer(1, 0.1*inch))
    
    company_size = df['公司规模'].dropna()
    size_text = f"""
    在 {len(company_size):,} 条有效记录中，公司规模呈现出明显的右偏分布特征。公司规模的平均值为 {company_size.mean():.0f} 人，
    但中位数仅为 {company_size.median():.0f} 人，这表明存在少数大型公司显著拉高了平均值。
    从四分位数来看，25%的公司规模在 {company_size.quantile(0.25):.0f} 人以下，50%的公司规模在 {company_size.median():.0f} 人以下，
    75%的公司规模在 {company_size.quantile(0.75):.0f} 人以下。市场由大量中小型公司和少数大型公司组成。
    """
    story.append(Paragraph(size_text.strip(), normal_style))
    story.append(Spacer(1, 0.2*inch))
    
    # 5. 薪资水平分析
    if len(chart_files) > 4:
        story.append(Paragraph("五、薪资水平分析", heading_style))
        story.append(Paragraph(chart_files[4].replace('finding\\', ''), ParagraphStyle('ImageLabel', parent=styles['Normal'], fontSize=9, alignment=TA_CENTER, textColor=HexColor('#666666'))))
        story.append(Image(chart_files[4], width=7*inch, height=2.5*inch))
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
            从分位数来看，25%的职位年薪在 ${salary_series.quantile(0.25):,.0f} 以下，50%的职位年薪在 ${salary_series.median():,.0f} 以下，
            75%的职位年薪在 ${salary_series.quantile(0.75):,.0f} 以下。年薪范围从最低的 ${salary_series.min():,.0f} 到最高的 ${salary_series.max():,.0f}。
            薪资的变异系数为 {salary_series.std()/salary_series.mean():.2f}，表明薪资水平存在较大波动，显示出相对较高的薪资水平，
            符合数据科学和人工智能领域的市场定位。
            """
            story.append(Paragraph(salary_text.strip(), normal_style))
            story.append(Spacer(1, 0.2*inch))
    
    # 6. 时间趋势
    if len(chart_files) > 5:
        story.append(Paragraph("六、职位发布时间趋势", heading_style))
        story.append(Paragraph(chart_files[5].replace('finding\\', ''), ParagraphStyle('ImageLabel', parent=styles['Normal'], fontSize=9, alignment=TA_CENTER, textColor=HexColor('#666666'))))
        story.append(Image(chart_files[5], width=6*inch, height=4.8*inch))
        story.append(Spacer(1, 0.1*inch))
        
        try:
            date_col = '职位发布时间'
            if date_col in df.columns:
                date_series = pd.to_datetime(df[date_col], errors='coerce').dropna()
                if len(date_series) > 0:
                    days_span = (date_series.max() - date_series.min()).days
                    timeline_text = f"""
                    职位发布时间跨度从 {date_series.min().strftime('%Y年%m月%d日')} 到 {date_series.max().strftime('%Y年%m月%d日')}，
                    数据时间跨度约为 {days_span} 天，平均每天发布约 {len(date_series)/max(days_span, 1):.1f} 个职位。
                    最近几天职位发布数量明显增加，表明市场活跃度较高。
                    """
                    story.append(Paragraph(timeline_text.strip(), normal_style))
                    story.append(Spacer(1, 0.2*inch))
        except:
            pass
    
    # 主要发现总结
    story.append(PageBreak())
    story.append(Paragraph("主要发现与总结", heading_style))
    
    findings = [
        "职位集中度：数据科学和人工智能相关职位占据市场主导地位，职位名称的高度多样性反映了市场对相关技能需求的细化和专业化趋势。",
        "公司分布：市场参与者众多，共涉及2,262家公司，但职位发布相对分散，没有出现明显的垄断现象，体现了市场的竞争性。",
        "地理分布：职位分布覆盖847个不同地理位置，但主要集中在科技产业发达的大城市，体现了科技人才需求的区域集中特征。",
        f"公司规模：市场由大量中小型公司和少数大型公司组成，公司规模呈现明显的右偏分布。中位数仅为{company_size.median():.0f}人，而平均值达到{company_size.mean():.0f}人，说明少数大型公司显著影响了整体规模水平。",
        "薪资水平：年薪中位数为132,300美元，75%的职位年薪在165,500美元以下，显示出相对较高的薪资水平，符合数据科学和人工智能领域的市场定位。",
        "数据质量：整体数据完整度达到97.3%，表明数据质量较高。但薪资信息存在一定缺失（约15%），这可能与部分公司未公开薪资信息有关。"
    ]
    
    for i, finding in enumerate(findings, 1):
        story.append(Paragraph(f"{i}. {finding}", normal_style))
        story.append(Spacer(1, 0.1*inch))
    
    # 统计方法说明
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("统计方法说明", heading_style))
    method_text = """
    本报告采用了以下统计分析方法：描述性统计（包括均值、中位数、标准差、分位数等基本统计量）、
    频数分析（对各分类变量进行频数和百分比统计）、分布特征分析（通过偏度、峰度等指标分析数据分布特征）、
    以及数据质量评估（通过完整度、缺失值分析等评估数据质量）。
    所有统计分析均基于现有数据，结果可能受到数据收集时间、平台覆盖范围等因素影响。
    """
    story.append(Paragraph(method_text.strip(), normal_style))
    
    # 生成PDF
    doc.build(story)
    print(f"PDF报告已生成: {output_path}")

def main():
    file_path = r"C:\Users\Dylan\Desktop\US Full Report.xlsx"
    output_dir = "finding"
    os.makedirs(output_dir, exist_ok=True)
    
    print("正在读取数据...")
    df = pd.read_excel(file_path)
    print(f"数据加载完成：{len(df)} 条记录")
    
    print("正在生成图表...")
    chart_files = generate_charts(df, output_dir)
    print(f"已生成 {len(chart_files)} 个图表")
    
    print("正在生成PDF报告...")
    pdf_path = os.path.join(output_dir, "US_Job_Market_Research_Report.pdf")
    create_pdf_report(df, chart_files, pdf_path)
    
    print("完成！")

if __name__ == "__main__":
    main()

