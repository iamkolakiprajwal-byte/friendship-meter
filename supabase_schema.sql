-- ========================================================
-- FRIENDSHIP METER - SUPABASE DATABASE SCHEMA
-- Run this script in the Supabase SQL Editor (1-click setup)
-- ========================================================

-- 1. Game Sessions Table
CREATE TABLE IF NOT EXISTS public.sessions (
    session_id TEXT PRIMARY KEY,
    player_alias TEXT DEFAULT 'Friend',
    quiz_score NUMERIC,
    distance_km NUMERIC,
    distance_score NUMERIC,
    final_score NUMERIC,
    result_band TEXT,
    destination TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Quiz Answers Table
CREATE TABLE IF NOT EXISTS public.answers (
    id BIGSERIAL PRIMARY KEY,
    session_id TEXT REFERENCES public.sessions(session_id) ON DELETE CASCADE,
    question_idx INTEGER,
    question_text TEXT,
    selected_text TEXT,
    score_val NUMERIC,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Consented Locations Table
CREATE TABLE IF NOT EXISTS public.locations (
    id BIGSERIAL PRIMARY KEY,
    session_id TEXT REFERENCES public.sessions(session_id) ON DELETE CASCADE,
    latitude NUMERIC NOT NULL,
    longitude NUMERIC NOT NULL,
    accuracy_m NUMERIC,
    consented INTEGER DEFAULT 1,
    consent_timestamp TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable Row Level Security (RLS) but allow authenticated & service role access
ALTER TABLE public.sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.answers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.locations ENABLE ROW LEVEL SECURITY;

-- Create policies allowing full access via service role or anon key with REST
CREATE POLICY "Allow public insert sessions" ON public.sessions FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow public update sessions" ON public.sessions FOR UPDATE USING (true);
CREATE POLICY "Allow public select sessions" ON public.sessions FOR SELECT USING (true);

CREATE POLICY "Allow public insert answers" ON public.answers FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow public select answers" ON public.answers FOR SELECT USING (true);

CREATE POLICY "Allow public insert locations" ON public.locations FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow public select locations" ON public.locations FOR SELECT USING (true);
