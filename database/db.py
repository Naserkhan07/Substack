"""
Database Manager for Naser AI Media Engine.
Provides atomic SQLite operations, schema initialization, and deduplication helpers.
"""

import os
import sqlite3
import json
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

logger = logging.getLogger("media_engine.db")

DB_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB_PATH = os.path.join(DB_DIR, "media_engine.db")
SCHEMA_PATH = os.path.join(DB_DIR, "schema.sql")


def get_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Returns a thread-safe connection to the SQLite database with Row factory."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: str = DEFAULT_DB_PATH):
    """Initializes tables and indices from schema.sql."""
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()
    with get_connection(db_path) as conn:
        conn.executescript(schema_sql)
        conn.commit()
    logger.info(f"Database initialized at {db_path}")


def is_topic_already_covered(topic_key: str, db_path: str = DEFAULT_DB_PATH) -> bool:
    """Checks whether a topic key has already been discovered or published."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM topics WHERE topic_key = ?", (topic_key,))
        return cursor.fetchone() is not None


def save_topic(
    topic_key: str,
    category: str,
    title: str,
    description: str,
    suggested_angle: str,
    curiosity_score: float,
    historical_importance: float,
    uniqueness_score: float,
    total_score: float,
    source_url: str = "",
    status: str = "discovered",
    db_path: str = DEFAULT_DB_PATH,
) -> int:
    """Inserts a new discovered topic or updates score if existing."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO topics (
                topic_key, category, title, description, suggested_angle,
                curiosity_score, historical_importance, uniqueness_score,
                total_score, source_url, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(topic_key) DO UPDATE SET
                total_score = excluded.total_score,
                updated_at = CURRENT_TIMESTAMP
            RETURNING id;
            """,
            (
                topic_key, category, title, description, suggested_angle,
                curiosity_score, historical_importance, uniqueness_score,
                total_score, source_url, status
            ),
        )
        row = cursor.fetchone()
        conn.commit()
        return row["id"] if row else -1


def get_next_topic_for_publication(category: Optional[str] = None, db_path: str = DEFAULT_DB_PATH) -> Optional[Dict[str, Any]]:
    """Retrieves the highest-scoring pending topic."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        if category:
            cursor.execute(
                """
                SELECT * FROM topics 
                WHERE status = 'discovered' AND category = ?
                ORDER BY total_score DESC, id ASC LIMIT 1;
                """,
                (category,),
            )
        else:
            cursor.execute(
                """
                SELECT * FROM topics 
                WHERE status = 'discovered'
                ORDER BY total_score DESC, id ASC LIMIT 1;
                """
            )
        row = cursor.fetchone()
        return dict(row) if row else None


def save_article(
    topic_id: Optional[int],
    slug: str,
    category: str,
    title: str,
    subtitle: str,
    selected_hook: str,
    candidate_hooks: List[str],
    content_markdown: str,
    sources: List[Dict[str, str]],
    word_count: int,
    banner_image_path: str = "",
    social_card_path: str = "",
    status: str = "drafted",
    db_path: str = DEFAULT_DB_PATH,
) -> int:
    """Saves a newly generated article into the database."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO articles (
                topic_id, slug, category, title, subtitle,
                selected_hook, candidate_hooks_json, content_markdown,
                sources_json, word_count, banner_image_path, social_card_path, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            RETURNING id;
            """,
            (
                topic_id,
                slug,
                category,
                title,
                subtitle,
                selected_hook,
                json.dumps(candidate_hooks),
                content_markdown,
                json.dumps(sources),
                word_count,
                banner_image_path,
                social_card_path,
                status,
            ),
        )
        article_id = cursor.fetchone()["id"]
        if topic_id:
            cursor.execute(
                "UPDATE topics SET status = 'written', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (topic_id,),
            )
        conn.commit()
        return article_id


def record_publication(
    article_id: int,
    platform: str,
    post_id: str,
    post_url: str,
    status: str = "published",
    error_message: str = "",
    db_path: str = DEFAULT_DB_PATH,
):
    """Records publication outcome on a target platform."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO publications (article_id, platform, post_id, post_url, status, error_message)
            VALUES (?, ?, ?, ?, ?, ?);
            """,
            (article_id, platform, post_id, post_url, status, error_message),
        )
        if status == "published":
            cursor.execute(
                "UPDATE articles SET status = 'published', published_at = CURRENT_TIMESTAMP WHERE id = ?",
                (article_id,),
            )
        conn.commit()


def save_note_or_quote(
    item_type: str,
    category: str,
    content_text: str,
    author_or_attribution: str = "",
    verified: bool = True,
    source_citation: str = "",
    card_image_path: str = "",
    status: str = "queued",
    db_path: str = DEFAULT_DB_PATH,
) -> int:
    """Saves a short-form note, quote, or puzzle."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO notes_and_quotes (
                item_type, category, content_text, author_or_attribution,
                verified, source_citation, card_image_path, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            RETURNING id;
            """,
            (item_type, category, content_text, author_or_attribution, verified, source_citation, card_image_path, status),
        )
        row = cursor.fetchone()
        conn.commit()
        return row["id"] if row else -1


def log_system_event(
    event_type: str,
    provider_used: str,
    duration_ms: int,
    tokens_used: int,
    status: str,
    details: str = "",
    db_path: str = DEFAULT_DB_PATH,
):
    """Appends an operational log event."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO system_logs (event_type, provider_used, duration_ms, tokens_used, status, details)
            VALUES (?, ?, ?, ?, ?, ?);
            """,
            (event_type, provider_used, duration_ms, tokens_used, status, details),
        )
        conn.commit()
