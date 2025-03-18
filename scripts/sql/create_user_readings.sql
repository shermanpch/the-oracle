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