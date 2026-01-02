-- Migration: Add user_profile table for storing onboarding extractions

CREATE TABLE IF NOT EXISTS user_profile (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    daily_intentions JSONB DEFAULT '[]'::jsonb,
    values JSONB DEFAULT '[]'::jsonb,
    goals JSONB DEFAULT '[]'::jsonb,
    raw_extraction JSONB,  -- Full extraction for debugging/analysis
    extracted_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast lookups by user
CREATE INDEX IF NOT EXISTS idx_user_profile_user_id ON user_profile(user_id);

-- Updated_at trigger for user_profile
DO $$ BEGIN
    CREATE TRIGGER update_user_profile_updated_at
        BEFORE UPDATE ON user_profile
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

