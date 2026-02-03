# -*- coding: utf-8 -*-
"""
Supabase Configuration Template
Copy this file to supabase_config.py and fill in your actual values
DO NOT commit supabase_config.py to version control (add to .gitignore)
"""

# Supabase Project URL
# Get this from: Supabase Dashboard -> Settings -> API -> Project URL
SUPABASE_URL = "https://jsjwgivbadhbpngxhqfi.supabase.co"

# Supabase Anon Public Key
# Get this from: Supabase Dashboard -> Settings -> API -> Project API keys -> anon public
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpzandnaXZiYWRoYnBuZ3hocWZpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjY3NzQ1NjEsImV4cCI6MjA4MjM1MDU2MX0.ojMw2OLJnnnwkh-K3_AX4SyeJdiESOWHe84D-jXNiDs"

# Supabase Service Role Key (Optional, for admin operations)
# Get this from: Supabase Dashboard -> Settings -> API -> Project API keys -> service_role secret
# WARNING: This key has full access, keep it secret!
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpzandnaXZiYWRoYnBuZ3hocWZpIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2Njc3NDU2MSwiZXhwIjoyMDgyMzUwNTYxfQ.X4iSTOp0olmp1mE_XNbP4r2aArvFsgXWA3Das0UvkKI"

# Enable Supabase storage
ENABLE_SUPABASE = True

# Table name mapping for regions
# Maps region names to Supabase table names
REGION_TABLE_MAP = {
    "United States": "jobs_united_states",
    "United Kingdom": "jobs_united_kingdom",
    "Australia": "jobs_australia",
    "Hong Kong": "jobs_hong_kong",
    "Singapore": "jobs_singapore",
}

