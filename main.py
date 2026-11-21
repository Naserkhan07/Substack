"""
Main Orchestrator CLI for Naser AI Media Engine.
Entry point for GitHub Actions workflows and local manual execution.
"""

import sys
import argparse
import logging
from database import db
from engine.discovery import TopicDiscoveryEngine
from engine.writer import ArticleWriter
from engine.image_engine import ImageEngine
from engine.publisher import MasterPublisher
from engine.notes_generator import NotesGenerator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("media_engine.main")


def cmd_init():
    """Initializes the database schema."""
    db.init_db()
    logger.info("Database schema verified and ready.")


def cmd_discover():
    """Discovers and scores candidate topics across all editorial categories."""
    db.init_db()
    discovery = TopicDiscoveryEngine()
    batch = discovery.discover_batch()
    logger.info(f"Discovered and registered {len(batch)} topics in database.")


def cmd_publish():
    """Runs the daily long-form publishing cycle."""
    db.init_db()
    
    # 1. Fetch next top-priority topic
    topic = db.get_next_topic_for_publication()
    if not topic:
        logger.info("No discovered topics ready. Running discovery pass first...")
        discovery = TopicDiscoveryEngine()
        discovery.discover_batch()
        topic = db.get_next_topic_for_publication()

    if not topic:
        logger.error("No topics available for publication.")
        return

    logger.info(f"Selected topic for publication: {topic['title']} (Score: {topic['total_score']})")

    # 2. Write article & hooks
    writer = ArticleWriter()
    article = writer.write_article(topic)
    logger.info(f"Drafted article: '{article['title']}' ({article['word_count']} words)")

    # 3. Sourcing and compositing banners
    image_engine = ImageEngine()
    source_img = image_engine.source_image(
        subject=topic["title"],
        category=topic["category"],
        fallback_prompt=f"Editorial historical painting of {topic['title']}, dramatic natural lighting, high detail, photorealistic museum art",
    )
    banner_path, social_path = image_engine.composite_banner(
        source_image_path=source_img,
        subject=topic["title"],
        category=topic["category"],
        hook=article["selected_hook"],
        slug=article["slug"],
    )

    # 4. Dispatch multi-platform publishing
    publisher = MasterPublisher()
    result = publisher.publish_article(article, banner_path, social_path)
    logger.info(f"Publishing completed successfully for article ID: {result['article_id']}")
    logger.info(f"Results summary: {result['results']}")


def cmd_note(slot: str):
    """Publishes a scheduled short-form update to Substack Notes, Twitter, and Telegram."""
    db.init_db()
    generator = NotesGenerator()
    res = generator.publish_scheduled_note(slot=slot)
    logger.info(f"Dispatched slot '{slot}' note: {res['results']}")


def cmd_test_auth():
    """Verifies authentication status for all configured platforms."""
    from integrations.cookie_manager import CookieManager
    from integrations.substack_publisher import SubstackPublisher
    from integrations.twitter_publisher import TwitterPublisher
    from integrations.buttondown_publisher import ButtondownPublisher
    from integrations.telegram_publisher import TelegramPublisher

    mgr = CookieManager()
    logger.info(f"CookieManager loaded: {mgr.is_loaded}")

    sub = SubstackPublisher()
    logger.info(f"Substack configured: {sub.is_configured}")

    tw = TwitterPublisher()
    logger.info(f"X/Twitter configured: {tw.is_configured}")

    bd = ButtondownPublisher()
    logger.info(f"Buttondown configured: {bd.is_configured}")

    tg = TelegramPublisher()
    logger.info(f"Telegram configured: {tg.is_configured}")


def main():
    parser = argparse.ArgumentParser(description="Naser AI Media Engine Autonomous Publishing System")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init", help="Initialize the database")
    subparsers.add_parser("discover", help="Discover and score topics")
    subparsers.add_parser("publish", help="Run full article generation & publishing pipeline")
    
    note_p = subparsers.add_parser("note", help="Publish a scheduled short-form note")
    note_p.add_argument("--slot", choices=["midday", "afternoon", "evening", "night"], default="afternoon")

    subparsers.add_parser("test-auth", help="Test platform authentication")

    args = parser.parse_args()

    if args.command == "init":
        cmd_init()
    elif args.command == "discover":
        cmd_discover()
    elif args.command == "publish":
        cmd_publish()
    elif args.command == "note":
        cmd_note(args.slot)
    elif args.command == "test-auth":
        cmd_test_auth()


if __name__ == "__main__":
    main()
