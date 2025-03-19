-- Oracle I Ching Complete SQL Setup
-- This file combines all SQL scripts needed to set up the database for the Oracle I Ching application

-- 1. Create the iching_texts table
CREATE TABLE IF NOT EXISTS iching_texts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    parent_coord TEXT NOT NULL,
    child_coord TEXT NOT NULL,
    parent_text TEXT,
    child_text TEXT,
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
USING (auth.role() = 'service_role');

-- 2. Create the user_readings table
CREATE TABLE IF NOT EXISTS user_readings (
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
USING (auth.uid() = user_id);

-- 3. Create the user_quotas table to track membership and remaining queries
CREATE TABLE user_quotas (
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
-- This uses the free plan quota value from the application config (10)
CREATE OR REPLACE FUNCTION initialize_user_quota()
RETURNS TRIGGER AS $$
DECLARE
    free_plan_default INTEGER := 10;  -- Default quota value from application config
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
EXECUTE FUNCTION initialize_user_quota();

-- Note: After running this SQL, you must manually create the 'iching-images' bucket in the Supabase dashboard.
-- Instructions:
-- 1. Log in to your Supabase dashboard
-- 2. Navigate to the Storage section from the left sidebar
-- 3. Click the "New Bucket" button
-- 4. Enter "iching-images" as the bucket name
-- 5. Check the "Public bucket" option to make it publicly accessible
-- 6. Click "Create bucket"