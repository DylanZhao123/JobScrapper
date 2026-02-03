# JobSpy 抓取逻辑分析

## JobSpy 的工作方式

### 1. 基本API
```python
scrape_jobs(
    site_name="indeed",
    search_term="AI Engineer",  # 搜索关键词
    location="San Francisco, CA",  # 地点
    results_wanted=15,  # 想要的结果数量（默认15）
    country_indeed="usa",  # 国家
    # 其他可选参数...
)
```

### 2. 返回格式
- 返回 `pandas.DataFrame`
- 包含字段：title, company, location, description, job_url, date_posted, salary信息等

### 3. 限制和特点
- **一次性返回**：不像我们的爬虫那样分页，JobSpy一次性返回指定数量的结果
- **results_wanted参数**：可以设置想要的结果数量，但实际返回可能受Indeed限制
- **速度很快**：不需要访问详情页就能获取description等基本信息
- **去重需要自己处理**：需要基于job_url去重

### 4. 与我们的爬虫对比

| 特性 | JobSpy | 我们的爬虫 |
|------|--------|-----------|
| 速度 | 很快（~0.1s/职位） | 较慢（~1s/职位） |
| 数据完整度 | 中等（79-85%） | 高（85-90%） |
| 分页支持 | 不支持，一次性返回 | 支持分页 |
| Requirements | 不提供 | 从description提取 |
| 公司规模 | 部分提供 | 通过API补充 |
| 去重 | 需要自己实现 | 内置去重 |

## 实现思路

### 目标
1. 使用JobSpy快速抓取Indeed职位
2. 支持多个关键词和多个地点组合
3. 尽可能多地抓取匹配的岗位
4. 从description中提取Requirements（使用LinkedIn的逻辑）
5. 输出格式完全按照example_output.xlsx

### 策略

#### 1. 多关键词+多地点组合
- 遍历所有关键词和地点的组合
- 对每个组合调用JobSpy
- 设置较大的results_wanted（如50-100）来获取更多结果

#### 2. 去重机制
- 基于job_url去重
- 维护一个seen_urls集合
- 只保留新的职位

#### 3. Requirements提取
- 使用和LinkedIn爬虫完全相同的逻辑
- 从job description中提取
- 支持多种模式匹配

#### 4. 数据映射
- 将JobSpy的字段映射到example_output.xlsx格式
- 确保字段顺序完全一致

#### 5. 优化策略
- 可以尝试增加results_wanted来获取更多结果
- 如果某个关键词+地点组合返回结果较少，可以尝试调整参数
- 使用缓存避免重复请求

### 实现步骤

1. **初始化**
   - 定义关键词列表（核心+AI相关）
   - 定义地点列表（US locations）
   - 设置results_wanted参数

2. **抓取循环**
   - 对每个关键词+地点组合：
     - 调用scrape_jobs
     - 去重
     - 添加到总列表

3. **Requirements提取**
   - 遍历所有职位
   - 从description中提取requirements
   - 使用LinkedIn的逻辑

4. **数据映射和输出**
   - 映射到example_output.xlsx格式
   - 保存为Excel

