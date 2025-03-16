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