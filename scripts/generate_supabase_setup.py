#!/usr/bin/env python3
"""
Script to generate SQL statements for creating Supabase tables and
instructions for setting up the Oracle I Ching application.

This script generates:
1. SQL for creating the iching_texts table
2. SQL for creating the user_readings table
3. Instructions for creating the storage bucket

You can use this script to set up your Supabase project manually.
"""

import os
from pathlib import Path

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
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS user_readings_user_id_idx ON user_readings(user_id);

-- Enable Row Level Security
ALTER TABLE user_readings ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "Users can view their own readings" 
ON user_readings FOR SELECT 
USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own readings" 
ON user_readings FOR INSERT 
WITH CHECK (auth.uid() = user_id);"""

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

with open(sql_dir / "create_bucket_instructions.md", "w") as f:
    f.write(bucket_instructions)

# Generate a combined setup script
with open(sql_dir / "full_setup.sql", "w") as f:
    f.write("-- Oracle I Ching SQL Setup\n\n")
    f.write("-- 1. Create the iching_texts table\n")
    f.write(iching_texts_sql)
    f.write("\n\n-- 2. Create the user_readings table\n")
    f.write(user_readings_sql)
    f.write(
        "\n\n-- Note: After running this SQL, you must create the 'iching-images' bucket in the Supabase dashboard.\n"
    )

# Print success message
print("SQL scripts generated successfully!")
print("\nFiles created:")
print(f"1. {sql_dir}/create_iching_texts.sql - SQL for creating the iching_texts table")
print(
    f"2. {sql_dir}/create_user_readings.sql - SQL for creating the user_readings table"
)
print(
    f"3. {sql_dir}/create_bucket_instructions.md - Instructions for creating the storage bucket"
)
print(f"4. {sql_dir}/full_setup.sql - Combined SQL for creating both tables")

print("\nTo use these scripts:")
print("1. Log in to your Supabase dashboard")
print("2. Navigate to the SQL Editor")
print("3. Create a new query")
print("4. Copy and paste the contents from full_setup.sql")
print("5. Run the query")
print(
    "6. Follow the instructions in create_bucket_instructions.md to create the storage bucket"
)
