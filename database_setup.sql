-- Supabase数据库表结构设置
-- 需要在Supabase SQL Editor中运行这些命令

-- 1. 主表 jobs (已存在，用于美国数据)
-- 如果还没有创建，使用以下SQL：
/*
CREATE TABLE IF NOT EXISTS jobs (
    id BIGSERIAL PRIMARY KEY,
    job_title TEXT NOT NULL,
    company_name TEXT NOT NULL,
    location TEXT,
    job_description TEXT,
    requirements TEXT,
    salary_range TEXT,
    estimated_annual_salary TEXT,
    team_size TEXT,
    company_size TEXT,
    posted_date TEXT,
    job_status TEXT DEFAULT 'Active',
    platform TEXT DEFAULT 'LinkedIn',
    job_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(job_title, company_name)
);

CREATE INDEX IF NOT EXISTS idx_jobs_platform ON jobs(platform);
CREATE INDEX IF NOT EXISTS idx_jobs_location ON jobs(location);
*/

-- 2. 为每个国家创建单独的表
-- 英国表
CREATE TABLE IF NOT EXISTS jobs_uk (
    id BIGSERIAL PRIMARY KEY,
    job_title TEXT NOT NULL,
    company_name TEXT NOT NULL,
    location TEXT,
    job_description TEXT,
    requirements TEXT,
    salary_range TEXT,
    estimated_annual_salary TEXT,
    team_size TEXT,
    company_size TEXT,
    posted_date TEXT,
    job_status TEXT DEFAULT 'Active',
    platform TEXT DEFAULT 'LinkedIn',
    job_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(job_title, company_name)
);

CREATE INDEX IF NOT EXISTS idx_jobs_uk_platform ON jobs_uk(platform);
CREATE INDEX IF NOT EXISTS idx_jobs_uk_location ON jobs_uk(location);

-- 加拿大表
CREATE TABLE IF NOT EXISTS jobs_ca (
    id BIGSERIAL PRIMARY KEY,
    job_title TEXT NOT NULL,
    company_name TEXT NOT NULL,
    location TEXT,
    job_description TEXT,
    requirements TEXT,
    salary_range TEXT,
    estimated_annual_salary TEXT,
    team_size TEXT,
    company_size TEXT,
    posted_date TEXT,
    job_status TEXT DEFAULT 'Active',
    platform TEXT DEFAULT 'LinkedIn',
    job_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(job_title, company_name)
);

CREATE INDEX IF NOT EXISTS idx_jobs_ca_platform ON jobs_ca(platform);
CREATE INDEX IF NOT EXISTS idx_jobs_ca_location ON jobs_ca(location);

-- 新加坡表
CREATE TABLE IF NOT EXISTS jobs_sg (
    id BIGSERIAL PRIMARY KEY,
    job_title TEXT NOT NULL,
    company_name TEXT NOT NULL,
    location TEXT,
    job_description TEXT,
    requirements TEXT,
    salary_range TEXT,
    estimated_annual_salary TEXT,
    team_size TEXT,
    company_size TEXT,
    posted_date TEXT,
    job_status TEXT DEFAULT 'Active',
    platform TEXT DEFAULT 'LinkedIn',
    job_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(job_title, company_name)
);

CREATE INDEX IF NOT EXISTS idx_jobs_sg_platform ON jobs_sg(platform);
CREATE INDEX IF NOT EXISTS idx_jobs_sg_location ON jobs_sg(location);

-- 香港表
CREATE TABLE IF NOT EXISTS jobs_hk (
    id BIGSERIAL PRIMARY KEY,
    job_title TEXT NOT NULL,
    company_name TEXT NOT NULL,
    location TEXT,
    job_description TEXT,
    requirements TEXT,
    salary_range TEXT,
    estimated_annual_salary TEXT,
    team_size TEXT,
    company_size TEXT,
    posted_date TEXT,
    job_status TEXT DEFAULT 'Active',
    platform TEXT DEFAULT 'LinkedIn',
    job_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(job_title, company_name)
);

CREATE INDEX IF NOT EXISTS idx_jobs_hk_platform ON jobs_hk(platform);
CREATE INDEX IF NOT EXISTS idx_jobs_hk_location ON jobs_hk(location);

-- 注意：如果启用了RLS (Row Level Security)，需要为每个表设置策略
-- 例如：
-- ALTER TABLE jobs_uk ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY "Allow all operations" ON jobs_uk FOR ALL USING (true) WITH CHECK (true);
-- 对 jobs_ca, jobs_sg, jobs_hk 执行相同的操作

