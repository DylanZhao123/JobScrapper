-- ============================================================================
-- Supabase 只读权限快速设置脚本
-- ============================================================================
-- 此脚本为所有工作表创建只读访问策略
-- 执行后，使用 anon public 密钥的用户只能读取数据，不能修改
-- 
-- 重要说明：
-- 1. 此策略只影响使用 anon public 密钥的用户（TO public）
-- 2. service_role 密钥不受RLS限制，可以正常写入和编辑
-- 3. 如果您的代码使用 anon 密钥写入，需要：
--    - 选项A：改用 service_role 密钥（推荐）
--    - 选项B：为 service_role 角色添加写入策略（见下方）
-- ============================================================================

-- 步骤1: 确保RLS已启用（如果未启用，取消下面的注释）
-- ALTER TABLE public.jobs_united_states ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.jobs_united_kingdom ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.jobs_australia ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.jobs_hong_kong ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.jobs_singapore ENABLE ROW LEVEL SECURITY;

-- 步骤2: 为所有表创建只读策略
DO $$
DECLARE
    table_name TEXT;
    tables TEXT[] := ARRAY[
        'jobs_united_states',
        'jobs_united_kingdom',
        'jobs_australia',
        'jobs_hong_kong',
        'jobs_singapore'
    ];
BEGIN
    FOREACH table_name IN ARRAY tables
    LOOP
        -- 删除现有策略（如果存在，避免重复）
        EXECUTE format('DROP POLICY IF EXISTS "Allow read for all" ON public.%I', table_name);
        
        -- 创建新的只读策略
        EXECUTE format('
            CREATE POLICY "Allow read for all" ON public.%I
            FOR SELECT
            TO public
            USING (true)
        ', table_name);
        
        RAISE NOTICE '✅ Created read-only policy for table: %', table_name;
    END LOOP;
    
    RAISE NOTICE '🎉 All read-only policies created successfully!';
    RAISE NOTICE '📋 You can now share the anon public key for read-only access.';
    RAISE NOTICE '⚠️  Note: If your code uses anon key for writes, switch to service_role key.';
END $$;

-- ============================================================================
-- 可选：为 service_role 添加写入权限（如果您的代码使用 anon 密钥）
-- ============================================================================
-- 如果您希望代码继续使用 anon 密钥进行写入，取消下面的注释：
/*
DO $$
DECLARE
    table_name TEXT;
    tables TEXT[] := ARRAY[
        'jobs_united_states',
        'jobs_united_kingdom',
        'jobs_australia',
        'jobs_hong_kong',
        'jobs_singapore'
    ];
BEGIN
    FOREACH table_name IN ARRAY tables
    LOOP
        -- 为 service_role 创建写入策略
        EXECUTE format('
            CREATE POLICY "Allow write for service_role" ON public.%I
            FOR ALL
            TO service_role
            USING (true)
            WITH CHECK (true)
        ', table_name);
        
        RAISE NOTICE '✅ Created write policy for service_role on table: %', table_name;
    END LOOP;
END $$;
*/

-- ============================================================================
-- 验证：检查策略是否创建成功
-- ============================================================================
SELECT 
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual
FROM pg_policies
WHERE tablename LIKE 'jobs_%'
ORDER BY tablename, policyname;

-- ============================================================================
-- 如果需要撤销只读权限，执行以下命令：
-- ============================================================================
-- DROP POLICY IF EXISTS "Allow read for all" ON public.jobs_united_states;
-- DROP POLICY IF EXISTS "Allow read for all" ON public.jobs_united_kingdom;
-- DROP POLICY IF EXISTS "Allow read for all" ON public.jobs_australia;
-- DROP POLICY IF EXISTS "Allow read for all" ON public.jobs_hong_kong;
-- DROP POLICY IF EXISTS "Allow read for all" ON public.jobs_singapore;

