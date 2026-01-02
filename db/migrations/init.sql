-- Alain AI Database Schema
-- Run automatically on first docker-compose up

-- Enums
CREATE TYPE onboarding_status AS ENUM ('pending', 'started', 'completed');
CREATE TYPE message_role AS ENUM ('user', 'assistant');

-- Users table
CREATE TABLE "user" (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    telegram_user_id BIGINT UNIQUE NOT NULL,
    name VARCHAR(255),
    username VARCHAR(255),
    onboarding_status onboarding_status DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Conversations table (1 per Telegram chat)
CREATE TABLE conversation (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    telegram_chat_id BIGINT UNIQUE NOT NULL,
    user_id UUID REFERENCES "user"(id) ON DELETE CASCADE,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    last_message_at TIMESTAMPTZ
);

-- Messages table
CREATE TABLE message (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversation(id) ON DELETE CASCADE,
    role message_role NOT NULL,
    content TEXT NOT NULL,
    sent_at TIMESTAMPTZ DEFAULT NOW(),
    indexed_at TIMESTAMPTZ  -- NULL = not yet indexed for RAG
);

-- Indexes for fast lookups
CREATE INDEX idx_user_telegram_id ON "user"(telegram_user_id);
CREATE INDEX idx_conversation_telegram_chat ON conversation(telegram_chat_id);
CREATE INDEX idx_conversation_user ON conversation(user_id);
CREATE INDEX idx_message_conversation ON message(conversation_id);
CREATE INDEX idx_message_sent_at ON message(sent_at DESC);
CREATE INDEX idx_message_not_indexed ON message(indexed_at) WHERE indexed_at IS NULL;

-- Updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_user_updated_at
    BEFORE UPDATE ON "user"
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

