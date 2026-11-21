-- SQLite Schema for Naser AI Media Engine
-- Persistent storage for topics, articles, quotes, publications, and logs

CREATE TABLE IF NOT EXISTS topics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_key TEXT UNIQUE NOT NULL,
    category TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    suggested_angle TEXT,
    curiosity_score REAL DEFAULT 0.0,
    historical_importance REAL DEFAULT 0.0,
    uniqueness_score REAL DEFAULT 0.0,
    total_score REAL DEFAULT 0.0,
    source_url TEXT,
    status TEXT DEFAULT 'discovered', -- discovered, queued, written, published, rejected
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_id INTEGER,
    slug TEXT UNIQUE NOT NULL,
    category TEXT NOT NULL,
    title TEXT NOT NULL,
    subtitle TEXT,
    selected_hook TEXT NOT NULL,
    candidate_hooks_json TEXT,
    content_markdown TEXT NOT NULL,
    sources_json TEXT,
    word_count INTEGER DEFAULT 0,
    banner_image_path TEXT,
    social_card_path TEXT,
    status TEXT DEFAULT 'drafted', -- drafted, verified, published, failed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    published_at TIMESTAMP,
    FOREIGN KEY(topic_id) REFERENCES topics(id)
);

CREATE TABLE IF NOT EXISTS publications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id INTEGER,
    platform TEXT NOT NULL, -- substack, twitter, medium, buttondown, telegram, discord
    post_id TEXT,
    post_url TEXT,
    status TEXT DEFAULT 'pending', -- pending, published, failed, skipped
    error_message TEXT,
    published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(article_id) REFERENCES articles(id)
);

CREATE TABLE IF NOT EXISTS notes_and_quotes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_type TEXT NOT NULL, -- note, quote, puzzle, fact
    category TEXT NOT NULL,
    content_text TEXT NOT NULL,
    author_or_attribution TEXT,
    verified BOOLEAN DEFAULT 1,
    source_citation TEXT,
    card_image_path TEXT,
    status TEXT DEFAULT 'queued', -- queued, published, rejected
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    published_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS system_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    provider_used TEXT,
    duration_ms INTEGER,
    tokens_used INTEGER,
    status TEXT NOT NULL,
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_topics_key ON topics(topic_key);
CREATE INDEX IF NOT EXISTS idx_topics_status ON topics(status);
CREATE INDEX IF NOT EXISTS idx_articles_slug ON articles(slug);
CREATE INDEX IF NOT EXISTS idx_articles_status ON articles(status);
CREATE INDEX IF NOT EXISTS idx_publications_platform ON publications(platform);
