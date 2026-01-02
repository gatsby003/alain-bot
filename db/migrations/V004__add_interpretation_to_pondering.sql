-- Migration: Add interpretation column to pondering table

ALTER TABLE pondering ADD COLUMN IF NOT EXISTS interpretation TEXT;

