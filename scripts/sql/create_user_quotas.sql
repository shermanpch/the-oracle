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