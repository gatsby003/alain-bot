-- Migration: Add pondering table for storing post-onboarding thoughts

CREATE TYPE pondering_category AS ENUM ('thought', 'observation', 'feeling', 'invalid');

CREATE TABLE IF NOT EXISTS pondering (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    conversation_id UUID NOT NULL REFERENCES conversation(id) ON DELETE CASCADE,
    raw_content TEXT NOT NULL,           -- Original message from user
    cleaned_content TEXT,                -- LLM-cleaned version
    interpretation TEXT,                 -- LLM's analysis of what this means
    category pondering_category NOT NULL,
    is_valid BOOLEAN NOT NULL DEFAULT true,
    received_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_pondering_user_id ON pondering(user_id);
CREATE INDEX IF NOT EXISTS idx_pondering_conversation_id ON pondering(conversation_id);
CREATE INDEX IF NOT EXISTS idx_pondering_received_at ON pondering(received_at);
CREATE INDEX IF NOT EXISTS idx_pondering_category ON pondering(category);
CREATE INDEX IF NOT EXISTS idx_pondering_valid ON pondering(is_valid) WHERE is_valid = true;

