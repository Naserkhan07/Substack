"""
Master Publishing Coordinator for Naser AI Media Engine.
Coordinates multi-platform syndication across:
- Substack (Drafts, Articles & Notes)
- X / Twitter (Teasers & Hooks)
- Buttondown (Email Newsletters)
- Telegram (Subscriber Channel Broadcast)
- Git-backed Markdown Archive (articles/YYYY-MM-DD-slug.md)
"""

import os
from datetime import datetime
import logging
from typing import Dict, Any, List

from integrations.substack_publisher import SubstackPublisher
from integrations.twitter_publisher import TwitterPublisher
from integrations.buttondown_publisher import ButtondownPublisher
from integrations.telegram_publisher import TelegramPublisher
from database import db

logger = logging.getLogger("media_engine.publisher")

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTICLES_DIR = os.path.join(ROOT_DIR, "articles")


class MasterPublisher:
    def __init__(self):
        os.makedirs(ARTICLES_DIR, exist_ok=True)
        self.substack = SubstackPublisher()
        self.twitter = TwitterPublisher()
        self.buttondown = ButtondownPublisher()
        self.telegram = TelegramPublisher()

    def publish_article(self, article: Dict[str, Any], banner_path: str, social_path: str) -> Dict[str, Any]:
        """
        Coordinates full publishing cycle across all platforms and saves versioned Markdown.
        """
        title = article["title"]
        slug = article["slug"]
        category = article["category"]
        hook = article["selected_hook"]
        content_markdown = article["content_markdown"]
        sources = article.get("sources", [])
        article_id = article.get("id")

        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        md_filename = f"{date_str}-{slug}.md"
        md_filepath = os.path.join(ARTICLES_DIR, md_filename)

        # 1. Save local versioned Markdown with rich Frontmatter
        frontmatter = f"""---
title: "{title}"
slug: "{slug}"
category: "{category}"
selected_hook: "{hook}"
date: "{date_str}"
banner_image: "{os.path.basename(banner_path)}"
social_image: "{os.path.basename(social_path)}"
---

"""
        with open(md_filepath, "w", encoding="utf-8") as f:
            f.write(frontmatter + content_markdown)
        logger.info(f"Saved versioned article markdown to: {md_filepath}")

        # Update article in database if needed
        if not article_id:
            article_id = db.save_article(
                topic_id=article.get("topic_id"),
                slug=slug,
                category=category,
                title=title,
                subtitle=article.get("subtitle", ""),
                selected_hook=hook,
                candidate_hooks=article.get("candidate_hooks", []),
                content_markdown=content_markdown,
                sources=sources,
                word_count=article.get("word_count", 0),
                banner_image_path=banner_path,
                social_card_path=social_path,
                status="drafted",
            )

        results = {}

        # 2. Publish to Substack
        if self.substack.is_configured:
            sub_res = self.substack.create_draft(
                title=title,
                subtitle=hook,
                content_markdown=content_markdown,
            )
            results["substack"] = sub_res
            db.record_publication(
                article_id=article_id,
                platform="substack",
                post_id=sub_res.get("post_id", ""),
                post_url=sub_res.get("post_url", ""),
                status="published" if sub_res.get("success") else "failed",
                error_message=sub_res.get("error", ""),
            )
        else:
            results["substack"] = {"success": False, "status": "skipped", "reason": "No credentials"}

        # Determine best reading URL
        reading_url = results.get("substack", {}).get("post_url") or f"https://naserkhan.substack.com"

        # 3. Publish to X / Twitter
        if self.twitter.is_configured:
            tweet_text = f"✨ {title}\n\n\"{hook}\"\n\nRead the full essay on Naser Journal:\n{reading_url}"
            tw_res = self.twitter.post_tweet(tweet_text)
            results["twitter"] = tw_res
            db.record_publication(
                article_id=article_id,
                platform="twitter",
                post_id=tw_res.get("post_id", ""),
                post_url=tw_res.get("post_url", ""),
                status="published" if tw_res.get("success") else "failed",
                error_message=tw_res.get("error", ""),
            )

        # 4. Broadcast to Telegram Channel
        if self.telegram.is_configured:
            tg_res = self.telegram.broadcast_article(
                title=title,
                hook=hook,
                article_url=reading_url,
                image_path=social_path,
            )
            results["telegram"] = tg_res
            db.record_publication(
                article_id=article_id,
                platform="telegram",
                post_id=tg_res.get("post_id", ""),
                post_url="",
                status="published" if tg_res.get("success") else "failed",
                error_message=tg_res.get("error", ""),
            )

        # 5. Dispatch to Buttondown Newsletter
        if self.buttondown.is_configured:
            bd_res = self.buttondown.publish_email(
                subject=f"{title} — {hook}",
                body_markdown=content_markdown,
            )
            results["buttondown"] = bd_res
            db.record_publication(
                article_id=article_id,
                platform="buttondown",
                post_id=bd_res.get("post_id", ""),
                post_url=bd_res.get("post_url", ""),
                status="published" if bd_res.get("success") else "failed",
                error_message=bd_res.get("error", ""),
            )

        return {
            "article_id": article_id,
            "markdown_path": md_filepath,
            "banner_path": banner_path,
            "social_path": social_path,
            "results": results,
        }
