-- Oracle I Ching SQL Setup

-- 1. Create the iching_texts table
CREATE TABLE IF NOT EXISTS iching_texts (
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
WITH CHECK (auth.uid() = user_id);

-- Note: After running this SQL, you must create the 'iching-images' bucket in the Supabase dashboard.
