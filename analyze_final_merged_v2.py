# -*- coding: utf-8 -*-
"""
对Final_Merged_Report_1的final_merged_report.xlsx进行系统分析（增强版）
包括职位标签、岗位级别、应届生要求、工作经历、文科专业等分析
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
from collections import Counter

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
OUTPUT_DIR = r"C:\Users\Dylan\JobScrapper\finding\Final_Merged_Report_Analysis_v2"
UPDATED_EXCEL_FILE = r"C:\Users\Dylan\JobScrapper\outputs\Final_Merged_Report_1\final_merged_report_updated.xlsx"

# 创建输出目录
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 当前日期（用于应届生分析）
CURRENT_DATE = datetime(2025, 11, 19)
CURRENT_YEAR = 2025

# 职位标签映射规则
def normalize_job_title(job_title):
    """将职位名称标准化为职位标签"""
    if pd.isna(job_title) or not isinstance(job_title, str):
        return "Other"
    
    title_lower = job_title.lower().strip()
    
    # 移除常见的级别前缀和后缀
    prefixes_to_remove = ['junior', 'jr', 'jr.', 'senior', 'sr', 'sr.', 'lead', 'principal', 
                          'staff', 'intern', 'internship', 'entry', 'entry-level', 'associate',
                          'assistant', 'trainee', 'apprentice', 'director', 'manager', 'head',
                          'chief', 'vp', 'vice president', 'executive', 'architect', 'specialist']
    
    # 移除级别前缀
    title_normalized = title_lower
    for prefix in prefixes_to_remove:
        if title_normalized.startswith(prefix + ' '):
            title_normalized = title_normalized[len(prefix):].strip()
        if title_normalized.endswith(' ' + prefix):
            title_normalized = title_normalized[:-len(prefix)-1].strip()
    
    # 标准化常见的职位名称变体
    title_normalized = re.sub(r'\s+', ' ', title_normalized)  # 多个空格变一个
    
    # 职位标签映射
    job_mapping = {
        # Data Scientist相关
        'data scientist': 'Data Scientist',
        'data science': 'Data Scientist',
        'data analytics': 'Data Scientist',
        'data analyst': 'Data Analyst',
        'data engineer': 'Data Engineer',
        'data engineering': 'Data Engineer',
        
        # AI/ML相关
        'ai engineer': 'AI Engineer',
        'artificial intelligence engineer': 'AI Engineer',
        'ml engineer': 'ML Engineer',
        'machine learning engineer': 'ML Engineer',
        'ai/ml engineer': 'AI/ML Engineer',
        'ai engineer': 'AI Engineer',
        'ml engineer': 'ML Engineer',
        'deep learning engineer': 'Deep Learning Engineer',
        'ai researcher': 'AI Researcher',
        'ai scientist': 'AI Scientist',
        'machine learning scientist': 'ML Scientist',
        'ai developer': 'AI Developer',
        'ai specialist': 'AI Specialist',
        
        # Software Engineer相关
        'software engineer': 'Software Engineer',
        'software developer': 'Software Developer',
        'software development engineer': 'Software Engineer',
        'backend engineer': 'Backend Engineer',
        'frontend engineer': 'Frontend Engineer',
        'full stack engineer': 'Full Stack Engineer',
        'full-stack engineer': 'Full Stack Engineer',
        
        # Product相关
        'product manager': 'Product Manager',
        'ai product manager': 'AI Product Manager',
        'product owner': 'Product Manager',
        
        # Research相关
        'research scientist': 'Research Scientist',
        'research engineer': 'Research Engineer',
        
        # Other
        'automation engineer': 'Automation Engineer',
        'manufacturing engineer': 'Manufacturing Engineer',
    }
    
    # 尝试精确匹配
    for key, label in job_mapping.items():
        if key in title_normalized:
            return label
    
    # 如果没有匹配，尝试提取核心职位名称
    # 移除常见的修饰词后，取前两个主要词作为标签
    words = title_normalized.split()
    if len(words) >= 2:
        # 尝试组合前两个词
        potential_label = ' '.join(words[:2]).title()
        return potential_label
    elif len(words) == 1:
        return words[0].title()
    
    return "Other"

def extract_job_level(job_title):
    """提取岗位级别：intern, junior, senior等"""
    if pd.isna(job_title) or not isinstance(job_title, str):
        return "Regular"
    
    title_lower = job_title.lower()
    
    if any(word in title_lower for word in ['intern', 'internship', 'trainee', 'apprentice']):
        return "Intern"
    elif any(word in title_lower for word in ['junior', 'jr', 'jr.', 'entry', 'entry-level', 'assistant', 'associate']):
        return "Junior"
    elif any(word in title_lower for word in ['senior', 'sr', 'sr.', 'lead', 'principal', 'staff']):
        return "Senior"
    elif any(word in title_lower for word in ['director', 'manager', 'head', 'chief', 'vp', 'vice president', 'executive']):
        return "Management"
    else:
        return "Regular"

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

# 文科专业关键词
LIBERAL_ARTS_KEYWORDS = {
    'Liberal Arts': ['liberal arts', 'humanities', 'arts', 'literature', 'english', 'history', 'philosophy'],
    'Social Sciences': ['psychology', 'sociology', 'anthropology', 'political science', 'international relations'],
    'Communication': ['communication', 'journalism', 'media studies', 'public relations'],
    'Education': ['education', 'teaching', 'pedagogy'],
    'Languages': ['linguistics', 'language', 'translation', 'interpretation'],
    'Design': ['design', 'graphic design', 'industrial design', 'user experience', 'ux', 'ui'],
    'Business (Non-STEM)': ['business administration', 'marketing', 'advertising', 'public relations'],
    'Law': ['law', 'legal', 'jurisprudence'],
    'Arts': ['fine arts', 'visual arts', 'performing arts', 'music', 'theater', 'drama']
}

def extract_education(text):
    """从文本中提取学历要求"""
    if pd.isna(text) or not isinstance(text, str):
        return []
    
    text_lower = text.lower()
    found_degrees = []
    
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

def extract_liberal_arts_major(text):
    """从文本中提取文科专业要求"""
    if pd.isna(text) or not isinstance(text, str):
        return []
    
    text_lower = text.lower()
    found_majors = []
    
    for major, keywords in LIBERAL_ARTS_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                found_majors.append(major)
                break
    
    return found_majors

def extract_graduation_year_requirement(text):
    """提取毕业年份要求（对应届生的要求）"""
    if pd.isna(text) or not isinstance(text, str):
        return None
    
    text_lower = text.lower()
    
    # 查找应届生相关关键词
    new_grad_keywords = ['new grad', 'new graduate', 'recent graduate', 'recent grad', 
                         'entry level', 'entry-level', 'college graduate', 'university graduate',
                         'graduating', 'graduation', 'class of']
    
    is_new_grad = any(keyword in text_lower for keyword in new_grad_keywords)
    
    # 查找具体的毕业年份要求
    year_patterns = [
        r'class of\s+(\d{4})',
        r'graduat(?:ed|ing|ion)\s+(?:in|from)\s+(\d{4})',
        r'(\d{4})\s+graduate',
        r'graduate\s+of\s+(\d{4})',
    ]
    
    graduation_year = None
    for pattern in year_patterns:
        match = re.search(pattern, text_lower)
        if match:
            year = int(match.group(1))
            if 2020 <= year <= CURRENT_YEAR + 1:  # 合理的年份范围
                graduation_year = year
                break
    
    # 如果找到应届生关键词但没有具体年份，检查是否要求2024或2025年毕业
    if is_new_grad and graduation_year is None:
        if '2024' in text or '2025' in text:
            if '2025' in text:
                graduation_year = 2025
            elif '2024' in text:
                graduation_year = 2024
    
    return graduation_year if is_new_grad else None

def extract_experience_years(text):
    """提取工作经历年份要求"""
    if pd.isna(text) or not isinstance(text, str):
        return None
    
    text_lower = text.lower()
    
    # 查找经验要求模式
    experience_patterns = [
        r'(\d+)\+?\s*years?\s*(?:of)?\s*(?:experience|exp|work)',
        r'(\d+)\+?\s*years?\s*(?:in|of)',
        r'minimum\s+of\s+(\d+)\s*years?',
        r'at least\s+(\d+)\s*years?',
        r'(\d+)\s*-\s*(\d+)\s*years?\s*(?:of)?\s*(?:experience|exp)',
    ]
    
    years_required = []
    for pattern in experience_patterns:
        matches = re.finditer(pattern, text_lower)
        for match in matches:
            if len(match.groups()) == 2:  # 范围，如 "3-5 years"
                min_years = int(match.group(1))
                max_years = int(match.group(2))
                years_required.append((min_years, max_years))
            else:  # 单个数字
                years = int(match.group(1))
                if 0 <= years <= 20:  # 合理的范围
                    years_required.append(years)
    
    # 返回最常见的年份要求，或者范围
    if years_required:
        # 如果是单个数字，返回最常见的
        single_years = [y for y in years_required if isinstance(y, int)]
        if single_years:
            return Counter(single_years).most_common(1)[0][0]
        # 如果是范围，返回最小值
        ranges = [y for y in years_required if isinstance(y, tuple)]
        if ranges:
            return ranges[0][0]
    
    return None

def update_relevance_level(df):
    """更新relevance level：1是AI+，2是+AI，并且如果一个职位标签已经在Level 1里，就不归类到Level 2"""
    df = df.copy()
    
    # 确保职位标签已存在
    if '职位标签' not in df.columns:
        df['职位标签'] = df['职位名称'].apply(normalize_job_title)
    
    # 获取Level 1的所有职位标签
    level1_labels = set(df[df['relevance level'] == 1]['职位标签'].unique())
    
    # 对于Level 2的职位，如果其职位标签已经在Level 1中出现过，则改为Level 1
    mask = (df['relevance level'] == 2) & (df['职位标签'].isin(level1_labels))
    moved_count = mask.sum()
    df.loc[mask, 'relevance level'] = 1
    
    return df, moved_count

def extract_salary_value(salary_str):
    """从薪资字符串中提取数值"""
    if pd.isna(salary_str) or not isinstance(salary_str, str):
        return None
    numbers = re.findall(r'\d+', salary_str.replace(',', ''))
    if numbers:
        return float(numbers[0])
    return None

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
    degree_percentages = (degree_counts / len(df) * 100).apply(lambda x: round(x, 2))
    
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
    major_percentages = (major_counts / len(df) * 100).apply(lambda x: round(x, 2))
    
    return major_counts, major_percentages

def analyze_liberal_arts_requirements(df):
    """分析文科专业要求"""
    print("正在分析文科专业要求...")
    
    all_liberal_arts = []
    for text in df['专业要求'].dropna():
        majors = extract_liberal_arts_major(text)
        all_liberal_arts.extend(majors)
    
    if not all_liberal_arts:
        return None, None
    
    liberal_arts_counts = pd.Series(all_liberal_arts).value_counts()
    liberal_arts_percentages = (liberal_arts_counts / len(df) * 100).apply(lambda x: round(x, 2))
    
    return liberal_arts_counts, liberal_arts_percentages

def analyze_new_grad_requirements(df):
    """分析应届生要求"""
    print("正在分析应届生要求...")
    
    graduation_years = []
    for text in df['专业要求'].dropna():
        year = extract_graduation_year_requirement(text)
        if year is not None:
            graduation_years.append(year)
    
    new_grad_count = len(graduation_years)
    new_grad_percentage = round(new_grad_count / len(df) * 100, 2)
    
    return new_grad_count, new_grad_percentage, graduation_years

def analyze_experience_requirements(df):
    """分析工作经历要求"""
    print("正在分析工作经历要求...")
    
    experience_years = []
    for text in df['专业要求'].dropna():
        years = extract_experience_years(text)
        if years is not None:
            experience_years.append(years)
    
    experience_count = len(experience_years)
    experience_percentage = round(experience_count / len(df) * 100, 2)
    
    # 统计不同年份要求的分布
    if experience_years:
        experience_dist = Counter(experience_years)
        experience_dist_percentages = {k: round(v / len(df) * 100, 2) for k, v in experience_dist.items()}
    else:
        experience_dist = {}
        experience_dist_percentages = {}
    
    return experience_count, experience_percentage, experience_dist, experience_dist_percentages

def generate_charts(df, df_level1, df_level2, output_dir, degree_counts=None, degree_percentages=None,
                   major_counts=None, major_percentages=None, liberal_arts_counts=None, liberal_arts_percentages=None,
                   experience_dist=None, experience_dist_percentages=None):
    """生成所有图表"""
    chart_files = []
    
    # 1. Relevance Level分布（更新为AI+和+AI）
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
    ax.set_xticklabels(['Level 1 (AI+)', 'Level 2 (+AI)'])
    for i, (idx, val) in enumerate(level_counts.items()):
        ax.text(i, val + 50, f'{val}\n({val/len(df)*100:.1f}%)', 
                ha='center', va='bottom', fontsize=11, fontweight='bold')
    plt.tight_layout()
    chart1 = os.path.join(output_dir, 'chart1_relevance_level.png')
    plt.savefig(chart1, dpi=150, bbox_inches='tight')
    plt.close()
    chart_files.append(chart1)
    
    # 2. 职位标签分布（合并，使用职位标签）
    if '职位标签' in df.columns:
        job_label_counts = df['职位标签'].value_counts().head(15)
        fig, ax = plt.subplots(figsize=(10, 8))
        if available_font:
            plt.rcParams['font.sans-serif'] = [available_font]
        colors = sns.color_palette("husl", len(job_label_counts))
        bars = ax.barh(range(len(job_label_counts)), job_label_counts.values, color=colors)
        ax.set_yticks(range(len(job_label_counts)))
        ax.set_yticklabels(job_label_counts.index, fontsize=9, fontfamily=available_font if available_font else 'sans-serif')
        ax.set_xlabel('职位数量', fontsize=12, fontfamily=available_font if available_font else 'sans-serif')
        ax.set_title('Top 15 职位标签分布（合并分析）', fontsize=14, fontweight='bold', fontfamily=available_font if available_font else 'sans-serif')
        ax.invert_yaxis()
        for i, (idx, val) in enumerate(job_label_counts.items()):
            ax.text(val + 5, i, f'{val} ({val/len(df)*100:.2f}%)', 
                    va='center', fontsize=9)
        plt.tight_layout()
        chart2 = os.path.join(output_dir, 'chart2_job_labels_merged.png')
        plt.savefig(chart2, dpi=150, bbox_inches='tight')
        plt.close()
        chart_files.append(chart2)
    
    # 3. 职位标签对比（Level 1 vs Level 2）
    if '职位标签' in df.columns:
        label1 = df_level1['职位标签'].value_counts().head(10)
        label2 = df_level2['职位标签'].value_counts().head(10)
        fig, axes = plt.subplots(1, 2, figsize=(16, 6))
        if available_font:
            plt.rcParams['font.sans-serif'] = [available_font]
        
        colors1 = sns.color_palette("Reds", len(label1))
        axes[0].barh(range(len(label1)), label1.values, color=colors1)
        axes[0].set_yticks(range(len(label1)))
        axes[0].set_yticklabels(label1.index, fontsize=8, fontfamily=available_font if available_font else 'sans-serif')
        axes[0].set_xlabel('职位数量', fontsize=11, fontfamily=available_font if available_font else 'sans-serif')
        axes[0].set_title('Level 1 (AI+) Top 10 职位标签', fontsize=12, fontweight='bold', fontfamily=available_font if available_font else 'sans-serif')
        axes[0].invert_yaxis()
        
        colors2 = sns.color_palette("Blues", len(label2))
        axes[1].barh(range(len(label2)), label2.values, color=colors2)
        axes[1].set_yticks(range(len(label2)))
        axes[1].set_yticklabels(label2.index, fontsize=8, fontfamily=available_font if available_font else 'sans-serif')
        axes[1].set_xlabel('职位数量', fontsize=11, fontfamily=available_font if available_font else 'sans-serif')
        axes[1].set_title('Level 2 (+AI) Top 10 职位标签', fontsize=12, fontweight='bold', fontfamily=available_font if available_font else 'sans-serif')
        axes[1].invert_yaxis()
        
        plt.tight_layout()
        chart3 = os.path.join(output_dir, 'chart3_job_labels_comparison.png')
        plt.savefig(chart3, dpi=150, bbox_inches='tight')
        plt.close()
        chart_files.append(chart3)
    
    # 4. 岗位级别分布
    if '岗位级别' in df.columns:
        level_counts = df['岗位级别'].value_counts()
        fig, ax = plt.subplots(figsize=(10, 6))
        if available_font:
            plt.rcParams['font.sans-serif'] = [available_font]
        colors = sns.color_palette("Set3", len(level_counts))
        bars = ax.bar(range(len(level_counts)), level_counts.values, color=colors, alpha=0.7, edgecolor='black')
        ax.set_xticks(range(len(level_counts)))
        ax.set_xticklabels(level_counts.index, fontsize=10, fontfamily=available_font if available_font else 'sans-serif', rotation=15, ha='right')
        ax.set_ylabel('职位数量', fontsize=12, fontfamily=available_font if available_font else 'sans-serif')
        ax.set_title('岗位级别分布', fontsize=14, fontweight='bold', fontfamily=available_font if available_font else 'sans-serif')
        for i, (idx, val) in enumerate(level_counts.items()):
            ax.text(i, val + max(level_counts.values)*0.01, f'{val}\n({val/len(df)*100:.1f}%)', 
                    ha='center', va='bottom', fontsize=10, fontweight='bold')
        plt.tight_layout()
        chart4 = os.path.join(output_dir, 'chart4_job_levels.png')
        plt.savefig(chart4, dpi=150, bbox_inches='tight')
        plt.close()
        chart_files.append(chart4)
    
    # 5. 公司分布
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
    chart5 = os.path.join(output_dir, 'chart5_companies.png')
    plt.savefig(chart5, dpi=150, bbox_inches='tight')
    plt.close()
    chart_files.append(chart5)
    
    # 6. 地理位置分布
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
    chart6 = os.path.join(output_dir, 'chart6_locations.png')
    plt.savefig(chart6, dpi=150, bbox_inches='tight')
    plt.close()
    chart_files.append(chart6)
    
    # 7. 薪资分布
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
        chart7 = os.path.join(output_dir, 'chart7_salary.png')
        plt.savefig(chart7, dpi=150, bbox_inches='tight')
        plt.close()
        chart_files.append(chart7)
    
    # 8. 学历要求分布
    if degree_counts is None:
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
        chart8 = os.path.join(output_dir, 'chart8_education.png')
        plt.savefig(chart8, dpi=150, bbox_inches='tight')
        plt.close()
        chart_files.append(chart8)
    
    # 9. 专业要求分布
    if major_counts is None:
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
        chart9 = os.path.join(output_dir, 'chart9_major.png')
        plt.savefig(chart9, dpi=150, bbox_inches='tight')
        plt.close()
        chart_files.append(chart9)
    
    # 10. 文科专业要求分布
    if liberal_arts_counts is None:
        liberal_arts_counts, liberal_arts_percentages = analyze_liberal_arts_requirements(df)
    if liberal_arts_counts is not None and len(liberal_arts_counts) > 0:
        fig, ax = plt.subplots(figsize=(10, 6))
        if available_font:
            plt.rcParams['font.sans-serif'] = [available_font]
        colors = sns.color_palette("pastel", len(liberal_arts_counts))
        bars = ax.barh(range(len(liberal_arts_counts)), liberal_arts_counts.values, color=colors, alpha=0.7, edgecolor='black')
        ax.set_yticks(range(len(liberal_arts_counts)))
        ax.set_yticklabels(liberal_arts_counts.index, fontsize=10, fontfamily=available_font if available_font else 'sans-serif')
        ax.set_xlabel('职位数量', fontsize=12, fontfamily=available_font if available_font else 'sans-serif')
        ax.set_title('文科专业要求分布', fontsize=14, fontweight='bold', fontfamily=available_font if available_font else 'sans-serif')
        ax.invert_yaxis()
        for i, (idx, val) in enumerate(liberal_arts_counts.items()):
            ax.text(val + max(liberal_arts_counts.values)*0.01, i, f'{val} ({liberal_arts_percentages[idx]:.1f}%)', 
                    va='center', fontsize=9)
        plt.tight_layout()
        chart10 = os.path.join(output_dir, 'chart10_liberal_arts.png')
        plt.savefig(chart10, dpi=150, bbox_inches='tight')
        plt.close()
        chart_files.append(chart10)
    
    # 11. 工作经历要求分布
    if experience_dist is None:
        _, _, experience_dist, experience_dist_percentages = analyze_experience_requirements(df)
    if experience_dist and len(experience_dist) > 0:
        sorted_exp = sorted(experience_dist.items())
        years_list = [str(k) for k, v in sorted_exp]
        counts_list = [v for k, v in sorted_exp]
        fig, ax = plt.subplots(figsize=(10, 6))
        if available_font:
            plt.rcParams['font.sans-serif'] = [available_font]
        colors = sns.color_palette("YlOrRd", len(years_list))
        bars = ax.bar(range(len(years_list)), counts_list, color=colors, alpha=0.7, edgecolor='black')
        ax.set_xticks(range(len(years_list)))
        ax.set_xticklabels(years_list, fontsize=10, fontfamily=available_font if available_font else 'sans-serif', rotation=45, ha='right')
        ax.set_ylabel('职位数量', fontsize=12, fontfamily=available_font if available_font else 'sans-serif')
        ax.set_xlabel('工作经历要求（年）', fontsize=12, fontfamily=available_font if available_font else 'sans-serif')
        ax.set_title('工作经历要求分布', fontsize=14, fontweight='bold', fontfamily=available_font if available_font else 'sans-serif')
        for i, (years, count) in enumerate(sorted_exp):
            ax.text(i, count + max(counts_list)*0.01, f'{count}\n({experience_dist_percentages[years]:.1f}%)', 
                    ha='center', va='bottom', fontsize=9, fontweight='bold')
        plt.tight_layout()
        chart11 = os.path.join(output_dir, 'chart11_experience.png')
        plt.savefig(chart11, dpi=150, bbox_inches='tight')
        plt.close()
        chart_files.append(chart11)
    
    # 12. 公司规模分布
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
        chart12 = os.path.join(output_dir, 'chart12_company_size.png')
        plt.savefig(chart12, dpi=150, bbox_inches='tight')
        plt.close()
        chart_files.append(chart12)
    
    return chart_files

def generate_text_report(df, df_level1, df_level2, degree_counts, degree_percentages,
                        major_counts, major_percentages, liberal_arts_counts, liberal_arts_percentages,
                        new_grad_count, new_grad_percentage, graduation_years,
                        experience_count, experience_percentage, experience_dist, experience_dist_percentages,
                        output_file):
    """生成文本分析报告（增强版）"""
    report_lines = []
    
    report_lines.append("=" * 80)
    report_lines.append("Final Merged Report 系统分析报告（增强版 v2）")
    report_lines.append("=" * 80)
    report_lines.append(f"报告生成时间: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}")
    report_lines.append("")
    report_lines.append("本报告基于Final_Merged_Report_1的final_merged_report.xlsx数据，")
    report_lines.append("采用统计学方法对AI相关职位数据进行全面分析。")
    report_lines.append("本版本增加了职位标签、岗位级别、应届生要求、工作经历、文科专业等分析。")
    report_lines.append("")
    report_lines.append("=" * 80)
    report_lines.append("")
    
    # 执行摘要
    report_lines.append("执行摘要")
    report_lines.append("")
    report_lines.append(f"本次分析共涵盖 {len(df):,} 条职位记录，涉及 {df['公司名称'].nunique():,} 家不同的公司。")
    report_lines.append(f"其中，Relevance Level 1（AI+）职位 {len(df_level1):,} 条，占比 {len(df_level1)/len(df)*100:.2f}%；")
    report_lines.append(f"Relevance Level 2（+AI）职位 {len(df_level2):,} 条，占比 {len(df_level2)/len(df)*100:.2f}%。")
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
    report_lines.append("一、Relevance Level 分析（AI+ vs +AI）")
    report_lines.append("=" * 80)
    report_lines.append("")
    report_lines.append("1. 整体分布")
    report_lines.append("")
    level_counts = df['relevance level'].value_counts().sort_index()
    for level, count in level_counts.items():
        level_name = "AI+" if level == 1 else "+AI"
        report_lines.append(f"  Relevance Level {level} ({level_name}): {count:,} 条 ({count/len(df)*100:.2f}%)")
    report_lines.append("")
    report_lines.append("注：Level 1 (AI+) 表示与AI最相关的职业，Level 2 (+AI) 表示与AI关联的职业。")
    report_lines.append("如果一个职位标签已经在Level 1中出现，则不会归类到Level 2。")
    report_lines.append("")
    
    # 职位标签分析（合并）
    report_lines.append("2. 职位标签分布（合并分析）")
    report_lines.append("")
    if '职位标签' in df.columns:
        job_label_counts = df['职位标签'].value_counts()
        report_lines.append(f"通过职位标签标准化，共有 {df['职位标签'].nunique():,} 个不同的职位标签。")
        report_lines.append("排名前五的职位标签及其出现频率如下：")
        for i, (label, count) in enumerate(job_label_counts.head(5).items(), 1):
            report_lines.append(f"  {i}. {label}: {count} 次 ({count/len(df)*100:.2f}%)")
        report_lines.append("")
    
    # 分别分析
    report_lines.append("3. 分别分析")
    report_lines.append("")
    
    report_lines.append("3.1 Level 1 (AI+) 职位标签分析")
    report_lines.append("")
    if '职位标签' in df_level1.columns:
        label1_counts = df_level1['职位标签'].value_counts()
        report_lines.append(f"共有 {df_level1['职位标签'].nunique():,} 种不同的职位标签。")
        report_lines.append("排名前五的职位标签：")
        for i, (label, count) in enumerate(label1_counts.head(5).items(), 1):
            report_lines.append(f"  {i}. {label}: {count} 次 ({count/len(df_level1)*100:.2f}%)")
        report_lines.append("")
    
    report_lines.append("3.2 Level 2 (+AI) 职位标签分析")
    report_lines.append("")
    if '职位标签' in df_level2.columns:
        label2_counts = df_level2['职位标签'].value_counts()
        report_lines.append(f"共有 {df_level2['职位标签'].nunique():,} 种不同的职位标签。")
        report_lines.append("排名前五的职位标签：")
        for i, (label, count) in enumerate(label2_counts.head(5).items(), 1):
            report_lines.append(f"  {i}. {label}: {count} 次 ({count/len(df_level2)*100:.2f}%)")
        report_lines.append("")
    
    # 岗位级别分析
    report_lines.append("=" * 80)
    report_lines.append("二、岗位级别分析")
    report_lines.append("=" * 80)
    report_lines.append("")
    if '岗位级别' in df.columns:
        level_dist = df['岗位级别'].value_counts()
        report_lines.append("岗位级别分布如下：")
        report_lines.append("")
        for level, count in level_dist.items():
            report_lines.append(f"  {level}: {count} 个职位 ({count/len(df)*100:.2f}%)")
        report_lines.append("")
        report_lines.append("注：岗位级别通过职位名称中的关键词提取，包括Intern（实习）、Junior（初级）、")
        report_lines.append("Regular（常规）、Senior（高级）、Management（管理）等。")
        report_lines.append("")
    
    # 应届生要求分析
    report_lines.append("=" * 80)
    report_lines.append("三、应届生要求分析")
    report_lines.append("=" * 80)
    report_lines.append("")
    report_lines.append(f"通过关键词筛选方法，从专业要求字段中提取到 {new_grad_count} 个职位对应届生有要求，")
    report_lines.append(f"占比 {new_grad_percentage:.2f}%。")
    report_lines.append("")
    if graduation_years:
        year_dist = Counter(graduation_years)
        report_lines.append("毕业年份要求分布：")
        for year, count in sorted(year_dist.items(), reverse=True):
            report_lines.append(f"  {year}年毕业: {count} 个职位 ({count/len(df)*100:.2f}%)")
        report_lines.append("")
    report_lines.append("")
    
    # 工作经历要求分析
    report_lines.append("=" * 80)
    report_lines.append("四、工作经历要求分析")
    report_lines.append("=" * 80)
    report_lines.append("")
    report_lines.append(f"通过关键词筛选方法，从专业要求字段中提取到 {experience_count} 个职位对工作经历有要求，")
    report_lines.append(f"占比 {experience_percentage:.2f}%。")
    report_lines.append("")
    if experience_dist:
        report_lines.append("工作经历年份要求分布：")
        for years, count in sorted(experience_dist.items()):
            report_lines.append(f"  {years}年: {count} 个职位 ({experience_dist_percentages[years]:.2f}%)")
        report_lines.append("")
    report_lines.append("")
    
    # 文科专业要求分析
    report_lines.append("=" * 80)
    report_lines.append("五、文科专业要求分析")
    report_lines.append("=" * 80)
    report_lines.append("")
    if liberal_arts_counts is not None and len(liberal_arts_counts) > 0:
        report_lines.append("通过关键词筛选方法，从专业要求字段中提取的文科专业要求分布如下：")
        report_lines.append("")
        total_liberal_arts_jobs = len(df[df['专业要求'].apply(lambda x: len(extract_liberal_arts_major(x)) > 0 if pd.notna(x) else False)])
        report_lines.append(f"包含文科专业要求的职位总数: {total_liberal_arts_jobs} 个 ({total_liberal_arts_jobs/len(df)*100:.2f}%)")
        report_lines.append("")
        for major, count in liberal_arts_counts.items():
            report_lines.append(f"  {major}: {count} 次 ({liberal_arts_percentages[major]:.2f}%)")
        report_lines.append("")
        report_lines.append("注：一个职位可能包含多个文科专业要求关键词，因此总数可能超过职位总数。")
        report_lines.append("")
    else:
        report_lines.append("未能从专业要求字段中提取到明确的文科专业要求信息。")
        report_lines.append("")
    
    # 学历和专业要求分析（复用原逻辑）
    report_lines.append("=" * 80)
    report_lines.append("六、学历和专业要求分析")
    report_lines.append("=" * 80)
    report_lines.append("")
    
    if degree_counts is not None and len(degree_counts) > 0:
        report_lines.append("6.1 学历要求统计")
        report_lines.append("")
        report_lines.append("通过关键词筛选方法，从专业要求字段中提取的学历要求分布如下：")
        report_lines.append("")
        for degree, count in degree_counts.items():
            report_lines.append(f"  {degree}: {count} 次 ({degree_percentages[degree]:.2f}%)")
        report_lines.append("")
        report_lines.append("注：一个职位可能包含多个学历要求关键词，因此总数可能超过职位总数。")
        report_lines.append("")
    
    if major_counts is not None and len(major_counts) > 0:
        report_lines.append("6.2 专业要求统计")
        report_lines.append("")
        report_lines.append("通过关键词筛选方法，从专业要求字段中提取的专业要求分布如下：")
        report_lines.append("")
        for major, count in major_counts.head(15).items():
            report_lines.append(f"  {major}: {count} 次 ({major_percentages[major]:.2f}%)")
        report_lines.append("")
        report_lines.append("注：一个职位可能包含多个专业要求关键词，因此总数可能超过职位总数。")
        report_lines.append("")
    
    # 主要发现
    report_lines.append("=" * 80)
    report_lines.append("主要发现与洞察")
    report_lines.append("=" * 80)
    report_lines.append("")
    findings = [
        f"职位标签标准化：通过职位标签标准化，将相似的职位归类，共有{df['职位标签'].nunique() if '职位标签' in df.columns else 'N/A':,}个不同的职位标签。",
        f"Relevance Level分布：Level 1（AI+）职位占比{len(df_level1)/len(df)*100:.2f}%，Level 2（+AI）职位占比{len(df_level2)/len(df)*100:.2f}%。",
        f"岗位级别：Regular级别职位占比最高，为{df['岗位级别'].value_counts()['Regular']/len(df)*100:.2f}%{'（如果存在）' if '岗位级别' in df.columns else ''}。",
        f"应届生要求：{new_grad_percentage:.2f}%的职位对应届生有要求。",
        f"工作经历要求：{experience_percentage:.2f}%的职位对工作经历有明确要求。",
    ]
    if liberal_arts_counts is not None and len(liberal_arts_counts) > 0:
        total_liberal_arts_jobs = len(df[df['专业要求'].apply(lambda x: len(extract_liberal_arts_major(x)) > 0 if pd.notna(x) else False)])
        findings.append(f"文科专业需求：{total_liberal_arts_jobs/len(df)*100:.2f}%的职位包含文科专业要求，表明市场对跨学科背景的需求。")
    
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
                     major_counts, major_percentages, liberal_arts_counts, liberal_arts_percentages,
                     new_grad_count, new_grad_percentage, graduation_years,
                     experience_count, experience_percentage, experience_dist, experience_dist_percentages,
                     output_path):
    """创建PDF报告（增强版）"""
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
    story.append(Paragraph("Final Merged Report 系统分析报告（增强版 v2）", title_style))
    story.append(Spacer(1, 0.3*inch))
    
    # 执行摘要
    story.append(Paragraph("执行摘要", heading_style))
    summary_text = f"""
    本报告基于Final_Merged_Report_1的final_merged_report.xlsx数据，采用统计学方法对AI相关职位数据进行全面分析。
    本次分析共涵盖 {len(df):,} 条职位记录，涉及 {df['公司名称'].nunique():,} 家不同的公司。
    其中，Relevance Level 1（AI+）职位 {len(df_level1):,} 条，占比 {len(df_level1)/len(df)*100:.2f}%；
    Relevance Level 2（+AI）职位 {len(df_level2):,} 条，占比 {len(df_level2)/len(df)*100:.2f}%。
    本版本增加了职位标签、岗位级别、应届生要求、工作经历、文科专业等深度分析。
    """
    story.append(Paragraph(summary_text.strip(), normal_style))
    story.append(Spacer(1, 0.2*inch))
    
    # 1. Relevance Level分析
    story.append(Paragraph("一、Relevance Level 分析（AI+ vs +AI）", heading_style))
    if len(chart_files) > 0:
        story.append(Image(chart_files[0], width=5*inch, height=3.75*inch))
        story.append(Spacer(1, 0.1*inch))
    
    level_text = f"""
    Relevance Level分布显示，Level 1（AI+）职位 {len(df_level1):,} 条，Level 2（+AI）职位 {len(df_level2):,} 条。
    如果一个职位标签已经在Level 1中出现，则不会归类到Level 2，确保了分类的准确性。
    """
    story.append(Paragraph(level_text.strip(), normal_style))
    story.append(Spacer(1, 0.2*inch))
    
    # 2. 职位标签分布（合并）
    story.append(Paragraph("二、职位标签分布特征分析（合并）", heading_style))
    if len(chart_files) > 1:
        story.append(Image(chart_files[1], width=6*inch, height=4.8*inch))
        story.append(Spacer(1, 0.1*inch))
    
    if '职位标签' in df.columns:
        job_label_counts = df['职位标签'].value_counts()
        label_text = f"""
        通过职位标签标准化，将相似的职位归类，共有 {df['职位标签'].nunique():,} 个不同的职位标签。
        最常见的职位标签是 {job_label_counts.index[0]}，共出现 {job_label_counts.iloc[0]} 次，占比 {job_label_counts.iloc[0]/len(df)*100:.2f}%。
        """
        story.append(Paragraph(label_text.strip(), normal_style))
        story.append(Spacer(1, 0.2*inch))
    
    # 3. 职位标签对比
    story.append(Paragraph("三、职位标签对比（Level 1 vs Level 2）", heading_style))
    if len(chart_files) > 2:
        story.append(Image(chart_files[2], width=7*inch, height=3*inch))
        story.append(Spacer(1, 0.1*inch))
    
    if '职位标签' in df_level1.columns and '职位标签' in df_level2.columns:
        comparison_text = f"""
        Level 1（AI+）职位共有 {df_level1['职位标签'].nunique():,} 种不同的职位标签，
        最常见的职位标签是 {df_level1['职位标签'].value_counts().index[0]}。
        Level 2（+AI）职位共有 {df_level2['职位标签'].nunique():,} 种不同的职位标签，
        最常见的职位标签是 {df_level2['职位标签'].value_counts().index[0]}。
        """
        story.append(Paragraph(comparison_text.strip(), normal_style))
        story.append(Spacer(1, 0.2*inch))
    
    # 4. 岗位级别分布
    story.append(Paragraph("四、岗位级别分析", heading_style))
    if len(chart_files) > 3:
        story.append(Image(chart_files[3], width=6*inch, height=3.6*inch))
        story.append(Spacer(1, 0.1*inch))
    
    if '岗位级别' in df.columns:
        level_dist = df['岗位级别'].value_counts()
        level_text = f"""
        岗位级别分布显示，Regular级别职位占比最高，为 {level_dist.get('Regular', 0)/len(df)*100:.2f}%，
        Senior级别职位占比 {level_dist.get('Senior', 0)/len(df)*100:.2f}%，
        Management级别职位占比 {level_dist.get('Management', 0)/len(df)*100:.2f}%，
        Junior级别职位占比 {level_dist.get('Junior', 0)/len(df)*100:.2f}%，
        Intern级别职位占比 {level_dist.get('Intern', 0)/len(df)*100:.2f}%。
        """
        story.append(Paragraph(level_text.strip(), normal_style))
        story.append(Spacer(1, 0.2*inch))
    
    # 5. 公司分布
    story.append(Paragraph("五、公司分布特征", heading_style))
    if len(chart_files) > 4:
        story.append(Image(chart_files[4], width=6*inch, height=4.8*inch))
        story.append(Spacer(1, 0.1*inch))
    
    company_counts = df['公司名称'].value_counts()
    company_text = f"""
    数据涉及 {df['公司名称'].nunique():,} 家不同的公司，其中发布职位最多的公司是 {company_counts.index[0]}，
    共发布 {company_counts.iloc[0]} 个职位，占比 {company_counts.iloc[0]/len(df)*100:.2f}%。
    """
    story.append(Paragraph(company_text.strip(), normal_style))
    story.append(Spacer(1, 0.2*inch))
    
    # 6. 地理位置分布
    story.append(Paragraph("六、地理位置分布", heading_style))
    if len(chart_files) > 5:
        story.append(Image(chart_files[5], width=6*inch, height=4.8*inch))
        story.append(Spacer(1, 0.1*inch))
    
    location_counts = df['地点'].value_counts()
    location_text = f"""
    职位分布覆盖 {df['地点'].nunique():,} 个不同的地理位置。
    职位数量最多的城市是 {location_counts.index[0]}，共 {location_counts.iloc[0]} 个职位。
    """
    story.append(Paragraph(location_text.strip(), normal_style))
    story.append(Spacer(1, 0.2*inch))
    
    # 7. 薪资分析
    if len(chart_files) > 6:
        story.append(Paragraph("七、薪资水平分析", heading_style))
        story.append(Image(chart_files[6], width=7*inch, height=2.5*inch))
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
    
    # 8. 学历要求
    if len(chart_files) > 7 and degree_counts is not None and len(degree_counts) > 0:
        story.append(Paragraph("八、学历要求分析", heading_style))
        story.append(Image(chart_files[7], width=6*inch, height=3.6*inch))
        story.append(Spacer(1, 0.1*inch))
        
        degree_text = "通过关键词筛选方法，从专业要求字段中提取的学历要求分布如下："
        for degree, count in degree_counts.items():
            degree_text += f" {degree} ({degree_percentages[degree]:.2f}%)；"
        degree_text = degree_text.rstrip('；') + "。"
        story.append(Paragraph(degree_text.strip(), normal_style))
        story.append(Spacer(1, 0.2*inch))
    
    # 9. 专业要求
    if len(chart_files) > 8 and major_counts is not None and len(major_counts) > 0:
        story.append(Paragraph("九、专业要求分析", heading_style))
        story.append(Image(chart_files[8], width=6*inch, height=3.6*inch))
        story.append(Spacer(1, 0.1*inch))
        
        major_text = "通过关键词筛选方法，从专业要求字段中提取的专业要求分布如下："
        for major, count in major_counts.head(5).items():
            major_text += f" {major} ({major_percentages[major]:.2f}%)；"
        major_text = major_text.rstrip('；') + "。"
        story.append(Paragraph(major_text.strip(), normal_style))
        story.append(Spacer(1, 0.2*inch))
    
    # 10. 文科专业要求
    if len(chart_files) > 9 and liberal_arts_counts is not None and len(liberal_arts_counts) > 0:
        story.append(Paragraph("十、文科专业要求分析", heading_style))
        story.append(Image(chart_files[9], width=6*inch, height=3.6*inch))
        story.append(Spacer(1, 0.1*inch))
        
        total_liberal_arts_jobs = len(df[df['专业要求'].apply(lambda x: len(extract_liberal_arts_major(x)) > 0 if pd.notna(x) else False)])
        liberal_text = f"""
        通过关键词筛选方法，从专业要求字段中提取的文科专业要求分布如下。
        包含文科专业要求的职位总数: {total_liberal_arts_jobs} 个 ({total_liberal_arts_jobs/len(df)*100:.2f}%)。
        """
        story.append(Paragraph(liberal_text.strip(), normal_style))
        story.append(Spacer(1, 0.2*inch))
    
    # 11. 工作经历要求
    if len(chart_files) > 10 and experience_dist and len(experience_dist) > 0:
        story.append(Paragraph("十一、工作经历要求分析", heading_style))
        story.append(Image(chart_files[10], width=6*inch, height=3.6*inch))
        story.append(Spacer(1, 0.1*inch))
        
        exp_text = f"""
        通过关键词筛选方法，从专业要求字段中提取到 {experience_count} 个职位对工作经历有要求，占比 {experience_percentage:.2f}%。
        最常见的工作经历要求是 {sorted(experience_dist.items(), key=lambda x: x[1], reverse=True)[0][0]} 年。
        """
        story.append(Paragraph(exp_text.strip(), normal_style))
        story.append(Spacer(1, 0.2*inch))
    
    # 12. 公司规模
    if len(chart_files) > 11:
        story.append(Paragraph("十二、公司规模统计分析", heading_style))
        story.append(Image(chart_files[11], width=7*inch, height=2.5*inch))
        story.append(Spacer(1, 0.1*inch))
        
        company_size = df['公司规模'].dropna()
        if len(company_size) > 0:
            size_text = f"""
            在 {len(company_size):,} 条有效记录中，公司规模的平均值为 {company_size.mean():.0f} 人，
            中位数为 {company_size.median():.0f} 人，呈现出明显的右偏分布特征。
            """
            story.append(Paragraph(size_text.strip(), normal_style))
            story.append(Spacer(1, 0.2*inch))
    
    # 13. 应届生要求
    story.append(PageBreak())
    story.append(Paragraph("十三、应届生要求分析", heading_style))
    new_grad_text = f"""
    通过关键词筛选方法，从专业要求字段中提取到 {new_grad_count} 个职位对应届生有要求，占比 {new_grad_percentage:.2f}%。
    """
    story.append(Paragraph(new_grad_text.strip(), normal_style))
    if graduation_years:
        year_dist = Counter(graduation_years)
        year_text = "毕业年份要求分布："
        for year, count in sorted(year_dist.items(), reverse=True)[:5]:
            year_text += f" {year}年毕业 ({count} 个职位)；"
        year_text = year_text.rstrip('；') + "。"
        story.append(Paragraph(year_text.strip(), normal_style))
    story.append(Spacer(1, 0.2*inch))
    
    # 主要发现总结
    story.append(Paragraph("主要发现与总结", heading_style))
    
    findings = [
        f"职位标签标准化：通过职位标签标准化，将相似的职位归类，共有{df['职位标签'].nunique() if '职位标签' in df.columns else 'N/A':,}个不同的职位标签。",
        f"Relevance Level分布：Level 1（AI+）职位占比{len(df_level1)/len(df)*100:.2f}%，Level 2（+AI）职位占比{len(df_level2)/len(df)*100:.2f}%。",
    ]
    if '岗位级别' in df.columns:
        level_dist = df['岗位级别'].value_counts()
        findings.append(f"岗位级别：Regular级别职位占比最高，为{level_dist.get('Regular', 0)/len(df)*100:.2f}%。")
    findings.append(f"应届生要求：{new_grad_percentage:.2f}%的职位对应届生有要求。")
    findings.append(f"工作经历要求：{experience_percentage:.2f}%的职位对工作经历有明确要求。")
    if liberal_arts_counts is not None and len(liberal_arts_counts) > 0:
        total_liberal_arts_jobs = len(df[df['专业要求'].apply(lambda x: len(extract_liberal_arts_major(x)) > 0 if pd.notna(x) else False)])
        findings.append(f"文科专业需求：{total_liberal_arts_jobs/len(df)*100:.2f}%的职位包含文科专业要求，表明市场对跨学科背景的需求。")
    
    for i, finding in enumerate(findings, 1):
        story.append(Paragraph(f"{i}. {finding}", normal_style))
        story.append(Spacer(1, 0.1*inch))
    
    # 生成PDF
    doc.build(story)
    print(f"PDF报告已生成: {output_path}")

def main():
    print("="*80)
    print("Final Merged Report 系统分析（增强版 v2）")
    print("="*80)
    
    # 读取数据
    print(f"\n正在读取文件: {EXCEL_FILE}")
    df = pd.read_excel(EXCEL_FILE)
    print(f"数据加载完成：{len(df)} 条记录，{len(df.columns)} 个字段")
    
    # 添加职位标签列
    print("\n正在添加职位标签...")
    df['职位标签'] = df['职位名称'].apply(normalize_job_title)
    print(f"已生成 {df['职位标签'].nunique()} 个不同的职位标签")
    
    # 添加岗位级别列
    print("正在添加岗位级别...")
    df['岗位级别'] = df['职位名称'].apply(extract_job_level)
    level_dist = df['岗位级别'].value_counts()
    print("岗位级别分布:")
    for level, count in level_dist.items():
        print(f"  {level}: {count} ({count/len(df)*100:.2f}%)")
    
    # 更新relevance level
    print("\n正在更新relevance level...")
    df, moved_count = update_relevance_level(df)
    print(f"已将 {moved_count} 个Level 2职位调整为Level 1（因为职位标签已在Level 1中出现）")
    
    # 保存更新后的Excel
    print(f"\n正在保存更新后的Excel文件: {UPDATED_EXCEL_FILE}")
    # 重新排列列，将职位标签放在relevance level之后
    cols = list(df.columns)
    if '职位标签' in cols:
        cols.remove('职位标签')
        cols.insert(cols.index('relevance level') + 1, '职位标签')
    if '岗位级别' in cols:
        cols.remove('岗位级别')
        cols.insert(cols.index('职位标签') + 1, '岗位级别')
    df = df[cols]
    df.to_excel(UPDATED_EXCEL_FILE, index=False)
    print("已保存更新后的Excel文件")
    
    # 按relevance level分组
    df_level1 = df[df['relevance level'] == 1].copy()
    df_level2 = df[df['relevance level'] == 2].copy()
    print(f"\n更新后的Relevance Level分布:")
    print(f"  Level 1 (AI+): {len(df_level1)} 条 ({len(df_level1)/len(df)*100:.2f}%)")
    print(f"  Level 2 (+AI): {len(df_level2)} 条 ({len(df_level2)/len(df)*100:.2f}%)")
    
    # 分析专业要求
    degree_counts, degree_percentages = analyze_education_requirements(df)
    major_counts, major_percentages = analyze_major_requirements(df)
    liberal_arts_counts, liberal_arts_percentages = analyze_liberal_arts_requirements(df)
    
    # 分析应届生要求
    new_grad_count, new_grad_percentage, graduation_years = analyze_new_grad_requirements(df)
    
    # 分析工作经历要求
    experience_count, experience_percentage, experience_dist, experience_dist_percentages = analyze_experience_requirements(df)
    
    # 生成图表
    print("\n正在生成图表...")
    chart_files = generate_charts(df, df_level1, df_level2, OUTPUT_DIR,
                                  degree_counts, degree_percentages,
                                  major_counts, major_percentages,
                                  liberal_arts_counts, liberal_arts_percentages,
                                  experience_dist, experience_dist_percentages)
    print(f"已生成 {len(chart_files)} 个图表")
    
    # 生成文本报告
    print("\n正在生成文本报告...")
    text_report_path = os.path.join(OUTPUT_DIR, "Final_Merged_Report_Analysis_v2.txt")
    generate_text_report(df, df_level1, df_level2, degree_counts, degree_percentages,
                        major_counts, major_percentages, liberal_arts_counts, liberal_arts_percentages,
                        new_grad_count, new_grad_percentage, graduation_years,
                        experience_count, experience_percentage, experience_dist, experience_dist_percentages,
                        text_report_path)
    
    # 生成PDF报告
    print("\n正在生成PDF报告...")
    pdf_path = os.path.join(OUTPUT_DIR, "Final_Merged_Report_Analysis_v2.pdf")
    create_pdf_report(df, df_level1, df_level2, chart_files, degree_counts, degree_percentages,
                     major_counts, major_percentages, liberal_arts_counts, liberal_arts_percentages,
                     new_grad_count, new_grad_percentage, graduation_years,
                     experience_count, experience_percentage, experience_dist, experience_dist_percentages,
                     pdf_path)
    
    print("\n" + "="*80)
    print("分析完成！所有结果已保存到:")
    print(f"  更新后的Excel: {UPDATED_EXCEL_FILE}")
    print(f"  分析结果: {OUTPUT_DIR}")
    print("="*80)

if __name__ == "__main__":
    main()

