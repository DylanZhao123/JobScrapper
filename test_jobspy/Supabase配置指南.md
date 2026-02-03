# Supabase 完整配置指南

本指南将带您完成Supabase的完整配置，从创建项目到运行程序，每一步都有详细说明。

---

## 📋 目录

1. [创建Supabase项目](#第一步创建supabase项目)
2. [获取API密钥](#第二步获取api密钥)
3. [创建数据库表](#第三步创建数据库表)
4. [配置RLS（行级安全策略）](#第四步配置rls行级安全策略)
5. [配置代码](#第五步配置代码)
6. [测试连接](#第六步测试连接)
7. [运行程序](#第七步运行程序)
8. [常见问题](#常见问题)

---

## 第一步：创建Supabase项目

### 1.1 注册账户

1. 访问 [Supabase官网](https://supabase.com/)
2. 点击右上角 "Start your project" 或 "Sign in"
3. 使用 GitHub 账户登录（推荐）或创建新账户

### 1.2 创建新项目

1. 登录后，点击 "New Project"
2. 填写项目信息：
   - **Name**: `JobScraper`（或您喜欢的名称）
   - **Database Password**: 设置数据库密码（**⚠️ 重要：请保存此密码**）
   - **Region**: 选择离您最近的区域（如：Southeast Asia (Singapore)）
   - **Pricing Plan**: 选择 **Free tier**（免费版）
3. 点击 "Create new project"
4. 等待项目创建完成（约2分钟）

---

## 第二步：获取API密钥

### 2.1 进入项目设置

1. 在项目仪表板左侧菜单，点击 **"Settings"**（齿轮图标）
2. 点击 **"API"**

### 2.2 复制所需信息

您需要复制以下信息（稍后会用到）：

- **Project URL**: 在 "Project URL" 部分，复制 URL
  - 格式：`https://xxxxx.supabase.co`
  - 示例：`https://abcdefghijklmnop.supabase.co`

- **anon public key**: 在 "Project API keys" 部分，复制 **"anon" "public"** 密钥
  - 这是一个长字符串，以 `eyJ...` 开头

**⚠️ 重要**：请将这些信息保存好，稍后配置代码时需要用到。

---

## 第三步：创建数据库表

### 3.1 使用SQL Editor创建表（推荐）

1. 在左侧菜单点击 **"SQL Editor"**
2. 点击 **"New query"**
3. 复制以下完整的SQL代码并粘贴到编辑器中：

```sql
-- ============================================
-- 创建所有地区的职位表
-- ============================================

-- 1. 美国职位表
CREATE TABLE IF NOT EXISTS jobs_united_states (
    id BIGSERIAL PRIMARY KEY,
    job_title TEXT NOT NULL,
    company_name TEXT NOT NULL,
    requirements TEXT,
    location TEXT,
    salary_range TEXT,
    estimated_annual_salary TEXT,
    estimated_annual_salary_usd TEXT,
    job_description TEXT,
    team_size TEXT,
    company_size TEXT,
    posted_date DATE,
    job_status TEXT,
    platform TEXT,
    job_link TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(job_title, company_name)
);

-- 2. 英国职位表
CREATE TABLE IF NOT EXISTS jobs_united_kingdom (
    id BIGSERIAL PRIMARY KEY,
    job_title TEXT NOT NULL,
    company_name TEXT NOT NULL,
    requirements TEXT,
    location TEXT,
    salary_range TEXT,
    estimated_annual_salary TEXT,
    estimated_annual_salary_usd TEXT,
    job_description TEXT,
    team_size TEXT,
    company_size TEXT,
    posted_date DATE,
    job_status TEXT,
    platform TEXT,
    job_link TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(job_title, company_name)
);

-- 3. 澳大利亚职位表
CREATE TABLE IF NOT EXISTS jobs_australia (
    id BIGSERIAL PRIMARY KEY,
    job_title TEXT NOT NULL,
    company_name TEXT NOT NULL,
    requirements TEXT,
    location TEXT,
    salary_range TEXT,
    estimated_annual_salary TEXT,
    estimated_annual_salary_usd TEXT,
    job_description TEXT,
    team_size TEXT,
    company_size TEXT,
    posted_date DATE,
    job_status TEXT,
    platform TEXT,
    job_link TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(job_title, company_name)
);

-- 4. 香港职位表
CREATE TABLE IF NOT EXISTS jobs_hong_kong (
    id BIGSERIAL PRIMARY KEY,
    job_title TEXT NOT NULL,
    company_name TEXT NOT NULL,
    requirements TEXT,
    location TEXT,
    salary_range TEXT,
    estimated_annual_salary TEXT,
    estimated_annual_salary_usd TEXT,
    job_description TEXT,
    team_size TEXT,
    company_size TEXT,
    posted_date DATE,
    job_status TEXT,
    platform TEXT,
    job_link TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(job_title, company_name)
);

-- 5. 新加坡职位表
CREATE TABLE IF NOT EXISTS jobs_singapore (
    id BIGSERIAL PRIMARY KEY,
    job_title TEXT NOT NULL,
    company_name TEXT NOT NULL,
    requirements TEXT,
    location TEXT,
    salary_range TEXT,
    estimated_annual_salary TEXT,
    estimated_annual_salary_usd TEXT,
    job_description TEXT,
    team_size TEXT,
    company_size TEXT,
    posted_date DATE,
    job_status TEXT,
    platform TEXT,
    job_link TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(job_title, company_name)
);

-- ============================================
-- 创建索引以提高查询性能
-- ============================================

CREATE INDEX IF NOT EXISTS idx_jobs_us_company ON jobs_united_states(company_name);
CREATE INDEX IF NOT EXISTS idx_jobs_us_title ON jobs_united_states(job_title);
CREATE INDEX IF NOT EXISTS idx_jobs_us_created ON jobs_united_states(created_at);

CREATE INDEX IF NOT EXISTS idx_jobs_uk_company ON jobs_united_kingdom(company_name);
CREATE INDEX IF NOT EXISTS idx_jobs_uk_title ON jobs_united_kingdom(job_title);
CREATE INDEX IF NOT EXISTS idx_jobs_uk_created ON jobs_united_kingdom(created_at);

CREATE INDEX IF NOT EXISTS idx_jobs_au_company ON jobs_australia(company_name);
CREATE INDEX IF NOT EXISTS idx_jobs_au_title ON jobs_australia(job_title);
CREATE INDEX IF NOT EXISTS idx_jobs_au_created ON jobs_australia(created_at);

CREATE INDEX IF NOT EXISTS idx_jobs_hk_company ON jobs_hong_kong(company_name);
CREATE INDEX IF NOT EXISTS idx_jobs_hk_title ON jobs_hong_kong(job_title);
CREATE INDEX IF NOT EXISTS idx_jobs_hk_created ON jobs_hong_kong(created_at);

CREATE INDEX IF NOT EXISTS idx_jobs_sg_company ON jobs_singapore(company_name);
CREATE INDEX IF NOT EXISTS idx_jobs_sg_title ON jobs_singapore(job_title);
CREATE INDEX IF NOT EXISTS idx_jobs_sg_created ON jobs_singapore(created_at);
```

4. 点击右下角 **"Run"** 按钮执行SQL
5. 确认执行成功（应该显示 "Success. No rows returned"）

### 3.2 验证表创建成功

1. 在左侧菜单点击 **"Table Editor"**
2. 您应该能看到5个表：
   - `jobs_united_states`
   - `jobs_united_kingdom`
   - `jobs_australia`
   - `jobs_hong_kong`
   - `jobs_singapore`

---

## 第四步：配置RLS（行级安全策略）

### ⭐ 推荐方法：禁用RLS（最简单）

**对于开发/测试环境，最简单的方法是禁用RLS**：

1. 在 **Table Editor** 中，选择任意一个表（如 `jobs_australia`）
2. 点击 **"Policies"** 标签
3. **关闭 "Enable RLS" 开关**（确保显示为关闭状态）
4. 对其他4个表重复此操作

✅ **完成！** 这样就不需要创建任何策略，程序可以直接插入数据。

### 备选方法：使用SQL创建RLS策略（如果必须启用RLS）

如果您需要启用RLS（生产环境），使用SQL Editor创建策略更可靠：

1. 在左侧菜单点击 **"SQL Editor"**
2. 点击 **"New query"**
3. 复制并执行以下SQL（为每个表执行，替换表名）：

```sql
-- 为 jobs_australia 创建策略（示例）
-- 对其他表重复执行，只需替换表名

-- 策略1：允许插入
CREATE POLICY "Allow insert for all" 
ON public.jobs_australia
FOR INSERT
TO public
WITH CHECK (true);

-- 策略2：允许查询
CREATE POLICY "Allow select for all" 
ON public.jobs_australia
FOR SELECT
TO public
USING (true);

-- 为其他表重复执行（替换表名）：
-- jobs_united_states, jobs_united_kingdom, jobs_hong_kong, jobs_singapore
```

### ⚠️ 如果使用UI创建策略（不推荐，容易出错）

如果您使用UI创建策略，**必须注意**：

**创建INSERT策略时**：
1. **Policy Name**: `Allow insert for all`
2. **Policy Command for clause**: 选择 **"INSERT"**
3. **Target Roles**: 选择 "public" 或留空
4. **Policy definition**（代码编辑器）：
   ```sql
   true
   ```
   或
   ```sql
   WITH CHECK (true)
   ```
   
   ⚠️ **关键错误**：不要写 `INSERT WITH CHECK (true)`！
   - UI已经通过下拉菜单选择了INSERT命令
   - 在Policy definition中只需要写条件表达式

**创建SELECT策略时**：
1. **Policy Name**: `Allow select for all`
2. **Policy Command for clause**: 选择 **"SELECT"**
3. **Target Roles**: 选择 "public" 或留空
4. **Policy definition**：
   ```sql
   true
   ```
   或
   ```sql
   USING (true)
   ```

---

## 第五步：配置代码

### 5.1 安装Supabase Python包

```bash
# 激活虚拟环境
venv\Scripts\activate

# 安装supabase包
pip install supabase
```

### 5.2 创建配置文件

1. **复制模板文件**：
   ```bash
   # 在项目根目录执行
   copy supabase_config.py.template supabase_config.py
   ```

2. **编辑 `supabase_config.py`**，填入您的Supabase信息：

   ```python
   # -*- coding: utf-8 -*-
   """
   Supabase Configuration
   DO NOT commit this file to version control (add to .gitignore)
   """
   
   # Supabase Project URL
   # 从 Supabase Dashboard -> Settings -> API -> Project URL 获取
   SUPABASE_URL = "https://your-project-id.supabase.co"  # 替换为您的URL
   
   # Supabase Anon Public Key
   # 从 Supabase Dashboard -> Settings -> API -> Project API keys -> anon public 获取
   SUPABASE_KEY = "your-anon-public-key-here"  # 替换为您的密钥
   
   # Supabase Service Role Key (可选，用于需要完整权限的操作)
   # 从 Supabase Dashboard -> Settings -> API -> Project API keys -> service_role secret 获取
   SUPABASE_SERVICE_KEY = "your-service-role-key-here"  # 可选
   
   # 地区表名映射
   REGION_TABLE_MAP = {
       "United States": "jobs_united_states",
       "United Kingdom": "jobs_united_kingdom",
       "Australia": "jobs_australia",
       "Hong Kong": "jobs_hong_kong",
       "Singapore": "jobs_singapore",
   }
   ```

   **⚠️ 重要**：
   - 将 `your-project-id.supabase.co` 替换为您在第二步复制的Project URL
   - 将 `your-anon-public-key-here` 替换为您在第二步复制的anon public key

### 5.3 启用Supabase存储

编辑 `config_jobspy.py`，设置：

```python
# Supabase integration
ENABLE_SUPABASE = True  # 设置为 True 启用 Supabase 存储
```

---

## 第六步：测试连接

### 6.1 创建测试脚本

创建一个测试文件 `test_supabase_connection.py`：

```python
# -*- coding: utf-8 -*-
"""Test Supabase connection"""
from supabase import create_client
from supabase_config import SUPABASE_URL, SUPABASE_KEY

try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # 测试查询
    result = supabase.table('jobs_united_states').select("*").limit(1).execute()
    print("✅ Supabase连接成功！")
    print(f"   表: jobs_united_states")
    print(f"   查询结果: {len(result.data)} 条记录")
    
except Exception as e:
    print(f"❌ 连接失败: {str(e)}")
    print("\n请检查：")
    print("1. supabase_config.py 中的 URL 和 KEY 是否正确")
    print("2. 是否已创建数据库表")
    print("3. 网络连接是否正常")
```

### 6.2 运行测试

```bash
python test_supabase_connection.py
```

如果看到 "✅ Supabase连接成功！"，说明配置正确。

---

## 第七步：运行程序

### 7.1 确认配置

在运行程序前，确认：

- ✅ `supabase_config.py` 已创建并填入正确的URL和KEY
- ✅ `config_jobspy.py` 中 `ENABLE_SUPABASE = True`
- ✅ 数据库表已创建
- ✅ RLS已禁用或策略已创建

### 7.2 运行程序

```bash
# 激活虚拟环境
venv\Scripts\activate

# 运行程序
python jobspy_max_scraper.py
```

### 7.3 查看结果

程序运行时会显示：
- 抓取进度
- 跨平台去重统计
- Supabase保存结果

完成后：
- **Excel文件**：保存在 `output/[RUN_ID]/[region_name]/jobspy_max_output.xlsx`
- **Supabase数据库**：在 Supabase Dashboard → Table Editor 中查看

---

## 数据存储说明

### 存储方式

- **Excel文件**：每次运行生成新的合并表格（包含去重后的所有数据）
- **Supabase数据库**：长期累积存储，每次运行自动追加新数据

### 去重机制

1. **跨平台去重**（LinkedIn vs Indeed）：
   - 基于：职位名称 + 公司名称
   - 如果两个平台有相同职位，保留Indeed版本

2. **数据库去重**（防止历史重复）：
   - 基于：job_title + company_name（数据库UNIQUE约束）
   - 插入前检查，如果已存在则跳过

### 数据追加

- 每次运行程序，新数据会自动追加到Supabase表中
- 不会覆盖旧数据
- 每个地区的数据存储在独立的表中

---

## 常见问题

### Q1: RLS策略配置报错怎么办？

**A**: 最简单的方法是**禁用RLS**：
1. Table Editor → 选择表 → Policies
2. 关闭 "Enable RLS" 开关
3. 完成

### Q2: 如何查看已存储的数据？

**A**: 
1. 登录 Supabase Dashboard
2. 点击左侧 "Table Editor"
3. 选择表（如 `jobs_australia`）
4. 查看所有数据

### Q3: 如何导出数据？

**A**: 
1. 在 Table Editor 中，选择表
2. 点击 "Export" 按钮
3. 选择格式（CSV 或 JSON）

### Q4: 免费版有什么限制？

**A**: 免费版限制：
- 500MB 数据库空间
- 2GB 带宽/月
- 50,000 行数据（可申请增加）

### Q5: 数据会重复吗？

**A**: 不会。程序有双重去重机制：
1. 跨平台去重（LinkedIn vs Indeed）
2. 数据库UNIQUE约束（防止历史重复）

### Q6: 如何修改表结构？

**A**: 
1. 在 SQL Editor 中使用 `ALTER TABLE` 语句
2. 或使用 Table Editor 的图形界面

### Q7: 如何备份数据？

**A**: 
- Supabase 免费版提供自动备份
- 也可以手动导出：Table Editor → Export

---

## 安全建议

### 1. 保护密钥

- ⚠️ **不要**将 `supabase_config.py` 提交到公共代码仓库
- ✅ 添加到 `.gitignore`：
  ```
  supabase_config.py
  ```

### 2. 使用环境变量（可选，更安全）

```python
import os
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
```

然后在系统环境变量中设置。

### 3. RLS策略

- 开发/测试：可以禁用RLS
- 生产环境：建议启用RLS并创建适当的策略

---

## 表结构说明

每个地区的表包含以下字段：

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `id` | BIGSERIAL | 自增主键 |
| `job_title` | TEXT | 职位名称（必填） |
| `company_name` | TEXT | 公司名称（必填） |
| `requirements` | TEXT | 职位要求 |
| `location` | TEXT | 工作地点 |
| `salary_range` | TEXT | 薪资范围 |
| `estimated_annual_salary` | TEXT | 估算年薪 |
| `estimated_annual_salary_usd` | TEXT | 美元转换后的年薪 |
| `job_description` | TEXT | 职位描述 |
| `team_size` | TEXT | 团队规模 |
| `company_size` | TEXT | 公司规模 |
| `posted_date` | DATE | 发布日期 |
| `job_status` | TEXT | 职位状态 |
| `platform` | TEXT | 来源平台（Indeed/LinkedIn） |
| `job_link` | TEXT | 职位链接 |
| `created_at` | TIMESTAMP | 数据创建时间（自动） |

**唯一约束**：`UNIQUE(job_title, company_name)` - 防止完全重复的职位

---

## 配置检查清单

在运行程序前，请确认：

- [ ] Supabase项目已创建
- [ ] 数据库表已创建（5个表）
- [ ] RLS已禁用或策略已创建
- [ ] `supabase_config.py` 已创建并填入正确的URL和KEY
- [ ] `config_jobspy.py` 中 `ENABLE_SUPABASE = True`
- [ ] `supabase` 包已安装（`pip install supabase`）
- [ ] 测试连接成功

---

## 完成！

配置完成后，每次运行 `python jobspy_max_scraper.py`，数据会自动：
1. 抓取LinkedIn和Indeed
2. 跨平台去重
3. 保存到Excel
4. 追加到Supabase数据库

数据会长期累积，形成历史数据库！

---

## 需要帮助？

如果遇到问题：
1. 检查配置检查清单
2. 查看程序运行日志
3. 在Supabase Dashboard中查看表和数据
4. 参考错误信息进行排查
