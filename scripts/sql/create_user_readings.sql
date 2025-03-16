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