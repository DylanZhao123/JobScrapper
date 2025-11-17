# Indeed完整爬取测试

这是一个独立的测试环境，用于测试Indeed的完整爬取功能，确保所有字段都能正确提取。

## 文件结构

```
test_indeed_full/
├── test_config.py          # 测试配置文件
├── test_indeed_scraper.py  # Indeed爬虫模块
├── test_main.py            # 主测试程序
├── outputs/                # 输出文件夹（自动创建）
│   ├── test_stage1_list.xlsx      # 列表页报告
│   ├── test_stage2_detail.xlsx    # 详情页报告
│   └── company_cache.json         # 公司规模缓存
└── README.md               # 本文件
```

## 功能特性

1. **列表页抓取**
   - 支持多个关键词
   - 支持多页抓取
   - 自动提取：职位名称、公司名称、地点、发布时间、职位链接、薪资（如果列表页有）

2. **详情页抓取**
   - 提取完整工作描述
   - 智能提取专业要求
   - 提取薪资信息（多种方法）
   - 获取公司规模（带缓存）

3. **数据导出**
   - Excel格式输出
   - 包含所有规定的字段
   - 字段完整性统计

## 使用方法

1. **运行测试**
   ```bash
   cd test_indeed_full
   python test_main.py
   ```

2. **查看结果**
   - 列表页数据：`outputs/test_stage1_list.xlsx`
   - 详情页数据：`outputs/test_stage2_detail.xlsx`

## 配置说明

在 `test_config.py` 中可以修改：

- `TEST_KEYWORDS`: 测试关键词列表
- `TEST_MAX_PAGES`: 每个关键词抓取的页数
- `TEST_LIST_LIMIT`: 列表页最多抓取条数
- `TEST_DETAIL_LIMIT`: 详情页测试条数
- `REQUEST_DELAY`: 请求延迟（秒）

## 注意事项

1. **ZenRows API**: 使用与主程序相同的API密钥
2. **JS渲染**: 如果普通请求失败，会自动尝试使用JS渲染
3. **调试**: 如果抓取失败，会保存HTML到 `debug_page_*.html` 用于调试
4. **缓存**: 公司规模信息会缓存到 `company_cache.json`

## 测试目标

确保能够：
- ✅ 成功抓取Indeed列表页
- ✅ 成功抓取Indeed详情页
- ✅ 提取所有规定的字段
- ✅ 正确解析薪资信息
- ✅ 获取公司规模信息
- ✅ 导出完整的Excel报告

