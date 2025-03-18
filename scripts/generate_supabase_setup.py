#!/usr/bin/env python3
"""
Script to generate SQL statements for creating Supabase tables and
instructions for setting up the Oracle I Ching application.

This script generates:
1. SQL for creating the iching_texts table
2. SQL for creating the user_readings table
3. SQL for creating the user_quotas table
4. Instructions for creating the storage bucket
5. A consolidated SQL file with all the above

You can use this script to set up your Supabase project manually.
"""

import os
import sys
from pathlib import Path

# Add project root to path so we can import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config.quotas import FREE_PLAN_QUOTA

# Ensure the sql directory exists
sql_dir = Path("scripts/sql")
sql_dir.mkdir(exist_ok=True)

# SQL for creating the iching_texts table - no newline at beginning
iching_texts_sql = """CREATE TABLE IF NOT EXISTS iching_texts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    path TEXT,
    parent_coord TEXT NOT NULL,
    child_coord TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(parent_coord, child_coord)
);

-- Enable Row Level Security
ALTER TABLE iching_texts ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "Allow public read access" 
ON iching_texts FOR SELECT 
USING (true);

CREATE POLICY "Allow service role write access" 
ON iching_texts FOR ALL 
USING (auth.role() = 'service_role');"""

# SQL for creating the user_readings table - no newline at beginning
user_readings_sql = """CREATE TABLE IF NOT EXISTS user_readings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    question TEXT NOT NULL,
    first_number INTEGER NOT NULL,
    second_number INTEGER NOT NULL,
    third_number INTEGER NOT NULL,
    language TEXT NOT NULL DEFAULT 'English',
    prediction JSONB,
    clarifying_question TEXT,
    clarifying_answer TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS user_readings_user_id_idx ON user_readings(user_id);

CREATE INDEX IF NOT EXISTS user_readings_clarifying_question_idx ON user_readings(clarifying_question);

-- Add comments to the table describing the columns
COMMENT ON COLUMN user_readings.clarifying_question IS 'Follow-up question asked by user after receiving initial prediction';

COMMENT ON COLUMN user_readings.clarifying_answer IS 'Answer to the follow-up question provided by the Oracle';

-- Enable Row Level Security
ALTER TABLE user_readings ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "Users can view their own readings" 
ON user_readings FOR SELECT 
USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own readings" 
ON user_readings FOR INSERT 
WITH CHECK (auth.uid() = user_id);

-- Create policy for updates
CREATE POLICY "Users can update their own readings" 
ON user_readings FOR UPDATE 
USING (auth.uid() = user_id);"""

# SQL for creating the user_quotas table - no newline at beginning
# Use the FREE_PLAN_QUOTA from config instead of hardcoding
user_quotas_sql = f"""CREATE TABLE user_quotas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    membership_type TEXT NOT NULL DEFAULT 'free',
    remaining_queries INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id)
);

-- Create an index on user_id for faster lookups
CREATE INDEX idx_user_quotas_user_id ON user_quotas(user_id);

-- Create or replace function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to update the updated_at column on updates
CREATE TRIGGER update_user_quotas_updated_at
BEFORE UPDATE ON user_quotas
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Create RLS policies to control access to the user_quotas table
ALTER TABLE user_quotas ENABLE ROW LEVEL SECURITY;

-- Policy to allow users to read only their own quota information
CREATE POLICY read_own_quota ON user_quotas
    FOR SELECT
    USING (auth.uid() = user_id);

-- Policy to allow authenticated users to insert their own quota (initial setup)
CREATE POLICY insert_own_quota ON user_quotas
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Policy to allow users to update only their own quota
CREATE POLICY update_own_quota ON user_quotas
    FOR UPDATE
    USING (auth.uid() = user_id);

-- Create a function to initialize a user's quota when they sign up
-- This uses the free plan quota value from the application config ({FREE_PLAN_QUOTA})
CREATE OR REPLACE FUNCTION initialize_user_quota()
RETURNS TRIGGER AS $$
DECLARE
    free_plan_default INTEGER := {FREE_PLAN_QUOTA};  -- Default quota value from application config
BEGIN
    INSERT INTO user_quotas (user_id, membership_type, remaining_queries)
    VALUES (NEW.id, 'free', free_plan_default)
    ON CONFLICT (user_id) DO NOTHING;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop the trigger if it already exists to avoid the error
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;

-- Trigger the function when a new user is created
CREATE TRIGGER on_auth_user_created
AFTER INSERT ON auth.users
FOR EACH ROW
EXECUTE FUNCTION initialize_user_quota();"""

# Instructions for creating the storage bucket - no newline at beginning
bucket_instructions = """# Creating the iching-images Storage Bucket in Supabase

Follow these steps to create the storage bucket for the I Ching images:

1. Log in to your Supabase dashboard
2. Navigate to the Storage section from the left sidebar
3. Click the "New Bucket" button
4. Enter "iching-images" as the bucket name
5. Check the "Public bucket" option to make the bucket publicly accessible
6. Click "Create bucket"

The bucket will be used to store hexagram images for the Oracle I Ching application."""

# Write the SQL files
with open(sql_dir / "create_iching_texts.sql", "w") as f:
    f.write(iching_texts_sql)

with open(sql_dir / "create_user_readings.sql", "w") as f:
    f.write(user_readings_sql)

with open(sql_dir / "create_user_quotas.sql", "w") as f:
    f.write(user_quotas_sql)

with open(sql_dir / "create_bucket_instructions.md", "w") as f:
    f.write(bucket_instructions)

# Generate a combined setup script
with open(sql_dir / "full_setup.sql", "w") as f:
    f.write("-- Oracle I Ching Complete SQL Setup\n")
    f.write(
        "-- This file combines all SQL scripts needed to set up the database for the Oracle I Ching application\n\n"
    )
    f.write("-- 1. Create the iching_texts table\n")
    f.write(iching_texts_sql)
    f.write("\n\n-- 2. Create the user_readings table\n")
    f.write(user_readings_sql)
    f.write(
        "\n\n-- 3. Create the user_quotas table to track membership and remaining queries\n"
    )
    f.write(user_quotas_sql)
    f.write(
        "\n\n-- Note: After running this SQL, you must manually create the 'iching-images' bucket in the Supabase dashboard.\n"
    )
    f.write("-- Instructions:\n")
    f.write("-- 1. Log in to your Supabase dashboard\n")
    f.write("-- 2. Navigate to the Storage section from the left sidebar\n")
    f.write('-- 3. Click the "New Bucket" button\n')
    f.write('-- 4. Enter "iching-images" as the bucket name\n')
    f.write('-- 5. Check the "Public bucket" option to make it publicly accessible\n')
    f.write('-- 6. Click "Create bucket"')

# Print success message
print("SQL scripts generated successfully!")
print("\nFiles created:")
print(f"1. {sql_dir}/create_iching_texts.sql - SQL for creating the iching_texts table")
print(
    f"2. {sql_dir}/create_user_readings.sql - SQL for creating the user_readings table"
)
print(f"3. {sql_dir}/create_user_quotas.sql - SQL for creating the user_quotas table")
print(
    f"4. {sql_dir}/create_bucket_instructions.md - Instructions for creating the storage bucket"
)
print(f"5. {sql_dir}/full_setup.sql - Consolidated SQL for creating all tables")

print("\nTo use these scripts:")
print("1. Log in to your Supabase dashboard")
print("2. Navigate to the SQL Editor")
print("3. Create a new query")
print("4. Copy and paste the contents from full_setup.sql")
print("5. Run the query")
print(
    "6. Follow the instructions in create_bucket_instructions.md to create the storage bucket"
)
