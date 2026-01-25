# -*- coding: utf-8 -*-
"""
================================================================================
JobScrapper 统一入口程序
================================================================================

所有配置都在 config_unified.py 中设置，直接运行此文件即可：

    python main_unified.py

配置文件位置: test_jobspy/config_unified.py

支持多地区自动循环爬取：
- 美国 (United States)
- 英国 (United Kingdom)
- 澳大利亚 (Australia)
- 新加坡 (Singapore)
- 香港 (Hong Kong)

================================================================================
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import List

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd

# Import all configuration from config_unified.py
from config_unified import (
    # Basic config
    RUN_ID, OUTPUT_DIR,
    # Multi-region config
    ENABLE_MULTI_REGION, REGIONS, DEFAULT_REGION,
    # Platform and search config
    PLATFORMS, KEYWORDS,
    # Scraping limits
    RESULTS_PER_SEARCH, MAX_TOTAL_JOBS, REQUEST_DELAY,
    # Test mode
    TEST_MODE,
    # Filtering
    FILTER_AI_RELATED, MIN_POSTED_DATE,
    # AI config
    ENABLE_AI_ANALYSIS, GEMINI_API_KEY, GEMINI_MODEL,
    AI_RATE_LIMIT_PER_MINUTE, AI_DAILY_LIMIT,
    PROMPT_TEMPLATE, RESUME_FROM_CHECKPOINT, CHECKPOINT_INTERVAL,
    # Realtime AI config
    ENABLE_REALTIME_AI, AI_BATCH_SIZE, REALTIME_CHECKPOINT_INTERVAL,
    # Output config
    OUTPUT_FIELDS, AI_ANALYSIS_FIELDS,
    # Helper functions
    get_effective_config, print_config,
)

from core.job_data import JobData, JobDataCollection
from core.currency_converter import CurrencyConverter
from scrapers.jobspy_scraper import JobSpyScraper
from ai_analysis.gemini_client import GeminiClient
from ai_analysis.prompts import PromptManager
from ai_analysis.batch_processor import BatchProcessor


# =============================================================================
# 实时AI分析检查点工具函数
# =============================================================================

def load_realtime_checkpoint(filepath: str) -> tuple:
    """
    加载实时分析检查点。

    Args:
        filepath: 检查点文件路径

    Returns:
        (processed_ids: set, results: list) - 已处理的职位ID集合和已有结果列表
    """
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return set(data.get('processed_ids', [])), data.get('results', [])
        except Exception as e:
            print(f"[WARNING] 加载检查点失败: {e}")
    return set(), []


def save_realtime_checkpoint(filepath: str, processed_ids: set, results: list, stats: dict = None):
    """
    保存实时分析检查点。

    Args:
        filepath: 检查点文件路径
        processed_ids: 已处理的职位ID集合
        results: 职位结果列表（包含AI分析）
        stats: 可选的统计信息
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    checkpoint_data = {
        'processed_ids': list(processed_ids),
        'results': results,
        'timestamp': datetime.now().isoformat(),
        'count': len(results),
    }
    if stats:
        checkpoint_data['stats'] = stats

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(checkpoint_data, f, ensure_ascii=False, indent=2, default=str)
    except Exception as e:
        print(f"[WARNING] 保存检查点失败: {e}")


def analyze_job_batch(
    jobs: List[JobData],
    gemini_client: GeminiClient,
    prompt: str,
    verbose: bool = True
) -> List[JobData]:
    """
    对一批职位进行AI分析。

    Args:
        jobs: 待分析的职位列表
        gemini_client: Gemini客户端
        prompt: Prompt模板
        verbose: 是否打印详细信息

    Returns:
        已分析的职位列表
    """
    for job in jobs:
        # 准备职位数据
        job_data = {
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "salary_range": job.salary_range or "Not specified",
            "description": job.description[:4000] if job.description else "No description",
        }

        # 调用AI分析
        result = gemini_client.analyze(prompt, job_data)

        if result:
            job.ai_analysis = result
            job.ai_analyzed = True
            if verbose:
                is_chinese = result.get('is_chinese_company_overseas', 'N/A')
                category = result.get('job_category', 'N/A')
                print(f"    [AI] {job.title[:30]}... -> 中企出海:{is_chinese}, 类别:{category}")
        else:
            if verbose:
                print(f"    [AI] {job.title[:30]}... -> 分析失败")

    return jobs


def get_locations_for_region(region_name: str) -> List[str]:
    """获取指定地区的所有搜索地点。"""
    try:
        from locations_config import LOCATIONS_BY_REGION

        if region_name in LOCATIONS_BY_REGION:
            locations = []
            for area, locs in LOCATIONS_BY_REGION[region_name].items():
                locations.extend(locs)
            return locations
    except ImportError:
        pass

    # 默认地点
    fallback = {
        "United States": ["United States"],
        "United Kingdom": ["United Kingdom"],
        "Australia": ["Australia"],
        "Singapore": ["Singapore"],
        "Hong Kong": ["Hong Kong"],
    }
    return fallback.get(region_name, [region_name])


def run_scraping_for_region(region_name: str) -> JobDataCollection:
    """运行单个地区的爬取。"""
    print("\n" + "=" * 60)
    print(f"爬取地区: {region_name}")
    print("=" * 60 + "\n")

    # Get effective configuration (considers TEST_MODE)
    effective = get_effective_config()

    # Get locations for this region
    locations = get_locations_for_region(region_name)
    if TEST_MODE:
        locations = locations[:effective.get('locations_limit', 2)]

    print(f"  关键词数量: {len(effective['keywords'])}")
    print(f"  地点数量: {len(locations)}")
    print(f"  搜索组合: {len(effective['keywords'])} × {len(locations)} = {len(effective['keywords']) * len(locations)}")
    print()

    # Configure scraper
    scraper = JobSpyScraper(
        platforms=PLATFORMS,
        request_delay=REQUEST_DELAY,
        results_per_search=effective['results_per_search'],
    )

    # Run scraping
    collection = scraper.scrape(
        keywords=effective['keywords'],
        locations=locations,
        region_name=region_name,
        min_posted_date=MIN_POSTED_DATE,
        filter_ai_related=FILTER_AI_RELATED,
        max_total_jobs=effective['max_total_jobs'],
        verbose=True,
    )

    print(f"\n{region_name} 爬取完成: {len(collection)} 个职位")

    return collection


def run_scraping_with_realtime_ai(region_name: str) -> JobDataCollection:
    """
    运行边爬边分析模式：抓取职位的同时进行AI分析。

    优势：
    - 减少内存占用（流式处理）
    - 中断损失更小（每批保存检查点）
    - 可以实时看到分析结果
    - 充分利用爬虫的等待时间

    Args:
        region_name: 地区名称

    Returns:
        包含AI分析结果的JobDataCollection
    """
    print("\n" + "=" * 60)
    print(f"实时爬取+分析: {region_name}")
    print("=" * 60 + "\n")

    # 获取有效配置
    effective = get_effective_config()

    # 获取地区的搜索地点
    locations = get_locations_for_region(region_name)
    if TEST_MODE:
        locations = locations[:effective.get('locations_limit', 2)]

    print(f"  模式: 边爬边分析 (实时AI分析)")
    print(f"  关键词数量: {len(effective['keywords'])}")
    print(f"  地点数量: {len(locations)}")
    print(f"  AI批处理大小: {AI_BATCH_SIZE}")
    print()

    # 初始化检查点路径
    region_safe = region_name.replace(' ', '_').lower()
    checkpoint_dir = OUTPUT_DIR / "realtime_checkpoints"
    checkpoint_file = str(checkpoint_dir / f"{region_safe}_realtime.json")

    # 加载检查点
    processed_ids, saved_results = load_realtime_checkpoint(checkpoint_file)
    print(f"  检查点: 已处理 {len(processed_ids)} 个职位")

    # 初始化结果集合
    collection = JobDataCollection()

    # 恢复已保存的结果
    for result in saved_results:
        try:
            job = JobData.from_dict(result)
            collection.add(job, deduplicate=False)
        except Exception as e:
            print(f"[WARNING] 恢复职位失败: {e}")

    # 初始化AI客户端（如果启用）
    gemini_client = None
    prompt = None
    if ENABLE_AI_ANALYSIS and GEMINI_API_KEY:
        try:
            gemini_client = GeminiClient(
                api_key=GEMINI_API_KEY,
                model=GEMINI_MODEL,
                rate_limit_per_minute=AI_RATE_LIMIT_PER_MINUTE,
                daily_limit=AI_DAILY_LIMIT,
            )
            prompt_manager = PromptManager()
            prompt = prompt_manager.get_template(PROMPT_TEMPLATE)
            if not prompt:
                prompt = prompt_manager.get_default_template()
            print(f"  AI分析: 已启用 (模型: {GEMINI_MODEL})")
        except Exception as e:
            print(f"  AI分析: 初始化失败 - {e}")
            gemini_client = None
    else:
        print(f"  AI分析: {'未启用' if not ENABLE_AI_ANALYSIS else 'API Key未设置'}")

    print()

    # 初始化爬虫
    from scrapers.jobspy_scraper import JobSpyScraper
    scraper = JobSpyScraper(
        platforms=PLATFORMS,
        request_delay=REQUEST_DELAY,
        results_per_search=effective['results_per_search'],
    )
    scraper.currency_converter.initialize()

    # 批处理缓冲区
    batch_buffer = []
    seen_keys = set(processed_ids)  # 用于去重
    total_scraped = 0
    total_analyzed = 0
    batch_count = 0

    # 循环爬取
    total_combinations = len(effective['keywords']) * len(locations) * len(PLATFORMS)
    current_combo = 0

    for keyword in effective['keywords']:
        if effective['max_total_jobs'] and len(collection) >= effective['max_total_jobs']:
            break

        for location in locations:
            if effective['max_total_jobs'] and len(collection) >= effective['max_total_jobs']:
                break

            for platform in PLATFORMS:
                if effective['max_total_jobs'] and len(collection) >= effective['max_total_jobs']:
                    break

                current_combo += 1
                progress = f"[{current_combo}/{total_combinations}]"
                print(f"{progress} {platform.upper()}: '{keyword}' in '{location}'...", end=" ")

                # 爬取
                try:
                    jobs = scraper._scrape_with_retry(
                        keyword=keyword,
                        location=location,
                        platform=platform,
                        region_name=region_name,
                    )
                except Exception as e:
                    print(f"[ERROR] {e}")
                    continue

                if jobs is None:
                    print("[FAILED]")
                    continue

                # 处理职位
                new_count = 0
                for job_dict in jobs:
                    # 转换为JobData
                    job = JobData.from_jobspy_dict(job_dict, platform)

                    # 去重
                    if job._dedup_key in seen_keys:
                        continue
                    seen_keys.add(job._dedup_key)

                    # 日期过滤
                    if MIN_POSTED_DATE and job.posted_date:
                        if job.posted_date < MIN_POSTED_DATE:
                            continue

                    # AI相关性过滤
                    if FILTER_AI_RELATED:
                        if not scraper._is_ai_related(job):
                            continue

                    # 处理薪资
                    scraper._process_salary(job, region_name)

                    # 提取要求
                    job.requirements = scraper.salary_processor.extract_requirements(job.description)

                    # 添加到批处理缓冲区
                    batch_buffer.append(job)
                    new_count += 1
                    total_scraped += 1

                print(f"[OK] {len(jobs)} found, {new_count} new")

                # 检查是否需要进行批量AI分析
                if len(batch_buffer) >= AI_BATCH_SIZE and gemini_client:
                    print(f"  -> 批量AI分析 ({len(batch_buffer)} 个职位)...")

                    # AI分析
                    analyzed_jobs = analyze_job_batch(
                        batch_buffer,
                        gemini_client,
                        prompt,
                        verbose=True
                    )

                    # 添加到集合
                    for job in analyzed_jobs:
                        collection.add(job, deduplicate=False)
                        processed_ids.add(job._dedup_key)

                    total_analyzed += len(analyzed_jobs)
                    batch_count += 1

                    # 保存检查点
                    if batch_count % REALTIME_CHECKPOINT_INTERVAL == 0:
                        results_to_save = [job.to_dict() for job in collection]
                        save_realtime_checkpoint(
                            checkpoint_file,
                            processed_ids,
                            results_to_save,
                            stats={
                                'total_scraped': total_scraped,
                                'total_analyzed': total_analyzed,
                                'batch_count': batch_count,
                            }
                        )
                        print(f"  -> 检查点已保存 ({len(collection)} 个职位)")

                    # 清空缓冲区
                    batch_buffer = []

                # 请求延迟
                import time
                time.sleep(REQUEST_DELAY)

    # 处理剩余的职位
    if batch_buffer:
        if gemini_client:
            print(f"\n处理剩余 {len(batch_buffer)} 个职位...")
            analyzed_jobs = analyze_job_batch(
                batch_buffer,
                gemini_client,
                prompt,
                verbose=True
            )
            for job in analyzed_jobs:
                collection.add(job, deduplicate=False)
                processed_ids.add(job._dedup_key)
            total_analyzed += len(analyzed_jobs)
        else:
            # 没有AI分析，直接添加
            for job in batch_buffer:
                collection.add(job, deduplicate=False)

    # 最终保存检查点
    results_to_save = [job.to_dict() for job in collection]
    save_realtime_checkpoint(
        checkpoint_file,
        processed_ids,
        results_to_save,
        stats={
            'total_scraped': total_scraped,
            'total_analyzed': total_analyzed,
            'batch_count': batch_count,
            'completed': True,
        }
    )

    # 打印统计信息
    print("\n" + "=" * 60)
    print(f"实时爬取+分析完成: {region_name}")
    print("=" * 60)
    print(f"  总爬取: {total_scraped} 个职位")
    print(f"  AI分析: {total_analyzed} 个职位")
    print(f"  最终结果: {len(collection)} 个职位")
    if gemini_client:
        stats = gemini_client.stats
        print(f"  API调用: {stats['request_count']} 次")
        print(f"  Token用量: {stats['input_tokens']:,} 输入, {stats['output_tokens']:,} 输出")
        print(f"  预估成本: ${stats['estimated_cost_usd']:.4f}")
    print("=" * 60)

    return collection


def run_ai_analysis(collection: JobDataCollection, region_name: str) -> JobDataCollection:
    """运行AI分析阶段。"""
    if not ENABLE_AI_ANALYSIS:
        print(f"\n[INFO] AI分析已禁用，跳过 {region_name}")
        return collection

    if not GEMINI_API_KEY:
        print(f"\n[WARNING] GEMINI_API_KEY 未设置，跳过 {region_name} AI分析")
        return collection

    if len(collection) == 0:
        print(f"\n[INFO] {region_name} 无职位数据，跳过AI分析")
        return collection

    print("\n" + "-" * 40)
    print(f"AI 分析: {region_name}")
    print("-" * 40 + "\n")

    # Initialize Gemini client
    try:
        client = GeminiClient(
            api_key=GEMINI_API_KEY,
            model=GEMINI_MODEL,
            rate_limit_per_minute=AI_RATE_LIMIT_PER_MINUTE,
            daily_limit=AI_DAILY_LIMIT,
        )
    except Exception as e:
        print(f"[ERROR] 初始化Gemini客户端失败: {e}")
        return collection

    # Initialize prompt manager
    prompt_manager = PromptManager()

    # Check if template exists
    if not prompt_manager.get_template(PROMPT_TEMPLATE):
        print(f"[INFO] 模板 '{PROMPT_TEMPLATE}' 不存在，创建默认模板...")
        prompt_manager.create_default_template_file()

    # Initialize batch processor
    region_safe = region_name.replace(' ', '_').lower()
    batch_id = f"{RUN_ID}_{region_safe}"
    processor = BatchProcessor(
        gemini_client=client,
        prompt_manager=prompt_manager,
        checkpoint_dir=str(OUTPUT_DIR / "checkpoints"),
        checkpoint_interval=CHECKPOINT_INTERVAL,
    )

    # Process collection
    collection = processor.process_collection(
        collection=collection,
        template_name=PROMPT_TEMPLATE,
        batch_id=batch_id,
        resume=RESUME_FROM_CHECKPOINT,
    )

    return collection


def save_region_results(collection: JobDataCollection, region_name: str) -> Path:
    """保存单个地区的结果。"""
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Generate output path
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    region_safe = region_name.replace(' ', '_').lower()
    output_path = OUTPUT_DIR / f"jobs_{region_safe}_{timestamp}.xlsx"

    # Convert to DataFrame
    df = collection.to_dataframe(export_format=True)

    # Add AI analysis fields if available
    if ENABLE_AI_ANALYSIS:
        for field in AI_ANALYSIS_FIELDS:
            df[f"AI_{field}"] = ""

        for i, job in enumerate(collection):
            if job.ai_analysis:
                for field in AI_ANALYSIS_FIELDS:
                    value = job.ai_analysis.get(field, "")
                    if isinstance(value, list):
                        value = ", ".join(str(v) for v in value)
                    df.at[i, f"AI_{field}"] = value

    # Save to Excel
    df.to_excel(output_path, index=False, engine='openpyxl')

    # Also save raw JSON for backup
    json_path = output_path.with_suffix('.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        records = []
        for job in collection:
            record = job.to_dict()
            if record.get('posted_date'):
                record['posted_date'] = record['posted_date'].isoformat()
            records.append(record)
        json.dump(records, f, ensure_ascii=False, indent=2)

    print(f"  已保存: {output_path.name} ({len(df)} 条)")

    return output_path


def main():
    """主入口函数。"""
    # Print configuration
    print_config()

    # Determine regions to process
    if ENABLE_MULTI_REGION:
        regions_to_process = REGIONS
        print(f"\n多地区模式: 将爬取 {len(regions_to_process)} 个地区")
        for i, r in enumerate(regions_to_process, 1):
            locations = get_locations_for_region(r)
            print(f"  {i}. {r} ({len(locations)} 个地点)")
    else:
        regions_to_process = [DEFAULT_REGION]
        print(f"\n单地区模式: {DEFAULT_REGION}")

    # Process each region
    all_results = {}
    total_jobs = 0

    for region_idx, region_name in enumerate(regions_to_process, 1):
        print("\n" + "=" * 60)
        print(f"地区 {region_idx}/{len(regions_to_process)}: {region_name}")
        print("=" * 60)

        # 根据配置选择处理模式
        if ENABLE_REALTIME_AI and ENABLE_AI_ANALYSIS:
            # 模式A: 实时爬取+分析（边爬边分析）
            print("[模式] 实时爬取+分析")
            collection = run_scraping_with_realtime_ai(region_name)
        else:
            # 模式B: 传统模式（先爬取，后分析）
            print("[模式] 传统分阶段处理")

            # Phase 1: Scraping
            collection = run_scraping_for_region(region_name)

            if len(collection) == 0:
                print(f"\n[WARNING] {region_name} 未收集到任何职位，跳过...")
                continue

            # Phase 2: AI Analysis
            collection = run_ai_analysis(collection, region_name)

        if len(collection) == 0:
            print(f"\n[WARNING] {region_name} 未收集到任何职位，跳过...")
            continue

        # Phase 3: Save results
        print(f"\n保存 {region_name} 结果...")
        output_path = save_region_results(collection, region_name)

        all_results[region_name] = {
            "count": len(collection),
            "file": output_path,
        }
        total_jobs += len(collection)

    # Final Summary
    print("\n" + "=" * 60)
    print("全部完成!")
    print("=" * 60)
    print(f"  处理地区: {len(all_results)}/{len(regions_to_process)}")
    print(f"  职位总数: {total_jobs}")
    print("-" * 40)
    for region, info in all_results.items():
        print(f"  {region}: {info['count']} 条 -> {info['file'].name}")
    print("-" * 40)
    print(f"  输出目录: {OUTPUT_DIR}")
    print(f"  配置文件: test_jobspy/config_unified.py")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
