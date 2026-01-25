# JobSpy Maximum Scraper - 使用说明

## 程序位置

**主程序：** `test_jobspy/jobspy_max_scraper.py`

## 功能特点

1. **最大化抓取**
   - 使用所有关键词（核心关键词 + AI相关关键词，共约60个）
   - 使用所有US地点（约395个地点）
   - 每个组合请求100个结果
   - 总组合数：约 60 × 395 = 23,700 个组合

2. **Checkpoint支持**
   - 自动保存进度（每10个请求或每5分钟）
   - 中断后可以继续运行，自动从上次停止的地方继续
   - 保存位置：`test_jobspy/output/jobspy_max_checkpoint.json`

3. **Requirements提取**
   - 使用和LinkedIn爬虫完全相同的逻辑
   - 从job description中提取
   - 完整度：100%

4. **输出格式**
   - 完全按照 `example_output.xlsx` 格式
   - 输出文件：`test_jobspy/output/jobspy_max_output.xlsx`

## 运行方法

```bash
cd C:\Users\Dylan\JobScrapper
python test_jobspy\jobspy_max_scraper.py
```

## 预计时间

- 总组合数：约 23,700 个
- 每个请求：约 1.5 秒
- 预计总时间：约 10 小时（可以中断后继续）

## 中断和恢复

如果程序被中断：
1. 程序会自动保存checkpoint
2. 再次运行相同命令即可
3. 程序会自动从上次停止的地方继续

## 输出文件

- `jobspy_max_output.xlsx` - 最终输出（Excel格式）
- `jobspy_max_checkpoint.json` - 进度文件（自动生成）
- `jobspy_max_raw_data.json` - 原始数据（自动生成）

## 配置修改

如需修改配置，编辑 `jobspy_max_scraper.py`：

```python
# 修改每个组合请求的结果数
results_per_search = 100  # 可以改为 50, 100, 150 等

# 限制总职位数（可选）
max_total_jobs = None  # 或设置为 10000, 20000 等

# 只使用核心关键词（更快）
keywords = CORE_KEYWORDS  # 只使用6个核心关键词

# 使用部分地点（更快）
locations = locations[:50]  # 只使用前50个地点
```

## 注意事项

1. 首次运行会需要很长时间（数小时）
2. 建议在稳定的网络环境下运行
3. 程序会自动保存进度，可以安全中断
4. 如果遇到错误，检查JobSpy是否正常安装

