# JobSpy 完整实现总结

## JobSpy 抓取逻辑分析

### 1. 基本工作原理

JobSpy 使用 `scrape_jobs()` 函数进行抓取：

```python
scrape_jobs(
    site_name="indeed",           # 目标网站
    search_term="AI Engineer",    # 搜索关键词
    location="San Francisco, CA", # 地点
    results_wanted=50,            # 想要的结果数量
    country_indeed="usa"          # 国家代码
)
```

### 2. 关键特点

- **一次性返回**：不像我们的爬虫那样分页，JobSpy一次性返回指定数量的结果
- **返回DataFrame**：直接返回pandas DataFrame，包含所有字段
- **速度快**：平均每个请求约1.5秒，比我们的爬虫快约10倍
- **内置字段**：包含title, company, location, description, job_url, salary信息等
- **不提供Requirements**：需要从description中提取

### 3. 限制

- **results_wanted限制**：虽然可以设置较大的值（如50-100），但Indeed可能限制实际返回数量
- **去重需要自己实现**：需要基于job_url去重
- **部分字段缺失**：Requirements、Team Size等需要自己提取

## 实现方案

### 策略：多关键词+多地点组合

1. **关键词组合**
   - 核心关键词（高相关性）：AI Engineer, ML Engineer, Data Scientist等
   - AI相关关键词（低相关性）：AI Sales, AI Training, AI Product Manager等
   - 可以组合使用，最大化覆盖

2. **地点组合**
   - 使用多个US城市
   - 每个关键词+地点组合独立搜索
   - 通过去重避免重复

3. **Requirements提取**
   - 使用和LinkedIn爬虫完全相同的逻辑
   - 从job description中提取
   - 支持多种模式匹配

### 测试结果

**测试配置：**
- 关键词：6个核心关键词
- 地点：10个US城市
- 每个组合请求50个结果
- 总组合数：60个

**结果：**
- 总职位数：**1844个**
- 运行时间：87.47秒
- 平均每个请求：1.46秒
- **总体完整度：89.1%**

**各字段完整度：**
- Job Title: 100.0%
- Company Name: 98.7%
- **Requirements: 100.0%** (从description提取)
- Location: 100.0%
- Salary Range: 85.9%
- Estimated Annual Salary: 85.9%
- Job Description: 100.0%
- Company Size: 87.4%
- Posted Date: 100.0%
- Job Status: 100.0%
- Platform: 100.0%
- Job Link: 100.0%

## 优势

1. **速度快**：比自定义爬虫快约10倍
2. **覆盖广**：通过多关键词+多地点组合，可以抓取大量职位
3. **Requirements完整**：使用LinkedIn逻辑提取，完整度100%
4. **易于使用**：API简单，返回DataFrame

## 如何最大化抓取

### 方法1：增加关键词
```python
keywords = CORE_KEYWORDS + AI_RELATED_KEYWORDS  # 总共约60个关键词
```

### 方法2：增加地点
```python
# 使用所有US locations
from locations_config import get_us_locations_only
locations = get_us_locations_only()  # 约395个地点
```

### 方法3：增加results_wanted
```python
results_per_search = 100  # 增加到100
```

### 方法4：组合使用
- 60个关键词 × 395个地点 × 100个结果 = 理论上可抓取大量职位
- 实际受Indeed限制和去重影响

## 与自定义爬虫对比

| 特性 | JobSpy | 自定义爬虫 |
|------|--------|-----------|
| 速度 | 快（~1.5s/请求） | 慢（~1s/职位） |
| 数据完整度 | 89.1% | 85-90% |
| Requirements | 100%（提取） | 100%（提取） |
| 公司规模 | 87.4% | 60-70% |
| 可扩展性 | 高（易扩展关键词/地点） | 中（需要修改代码） |
| 成本 | 免费（开源） | 需要ZenRows API |

## 建议

1. **快速批量抓取**：使用JobSpy
2. **高质量数据**：使用自定义爬虫补充缺失字段
3. **混合方案**：JobSpy快速抓取 + 自定义爬虫补充细节

