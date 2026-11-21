"""
Automated Notes & Short-Form Content Engine for Naser AI Media Engine.
Manages the 3x daily updates (12:30, 15:30, 18:00 IST) across Substack Notes,
X/Twitter, and Telegram.
"""

import random
import logging
from typing import Dict, Any
from integrations.substack_publisher import SubstackPublisher
from integrations.twitter_publisher import TwitterPublisher
from integrations.telegram_publisher import TelegramPublisher
from engine.quote_generator import QuoteEngine
from database import db

logger = logging.getLogger("media_engine.notes")

CURIOSITY_NOTES = [
    {
        "category": "history_extraordinary_personalities",
        "text": "Did you know? In 216 BC at the Battle of Cannae, Hannibal Barca intentionally allowed his center line to bow backward, luring 80,000 Roman legionaries into a convex crescent before snapping his cavalry shut behind them. It remains history's most devastating double-envelopment.",
    },
    {
        "category": "science_ai_technology",
        "text": "A thought experiment: If you entered a room moving at 99.99% the speed of light for one year and stepped back out, several decades would have passed on Earth. Time is not a universal river; it is a personal fabric that stretches with velocity and gravity.",
    },
    {
        "category": "human_biology_nature",
        "text": "Your brain consumes 20% of your total oxygen and metabolic caloric energy, despite accounting for only 2% of your body mass. Even when you are completely unconscious in dreamless sleep, billions of synaptic ion channels burn constant ATP to maintain biological coherence.",
    },
    {
        "category": "philosophy_psychology",
        "text": "The Pygmalion Effect: Human beings unconsciously conform to the positive or negative expectations placed upon them by authoritative figures. What you believe about someone's potential actively alters the neurological reality of their performance.",
    },
]


class NotesGenerator:
    def __init__(self):
        self.substack = SubstackPublisher()
        self.twitter = TwitterPublisher()
        self.telegram = TelegramPublisher()
        self.quote_engine = QuoteEngine()

    def publish_scheduled_note(self, slot: str = "afternoon") -> Dict[str, Any]:
        """
        Publishes a short-form curiosity update based on the time slot:
        - morning/midday: Surprising historical or scientific fact
        - afternoon: Psychological or cognitive curiosity note
        - evening: Verified quote or mind game / puzzle
        """
        if slot == "evening":
            item = self.quote_engine.get_daily_quote()
            post_text = f'"{item["text"]}"\n\n— {item["author"]} ({item.get("citation", "")})\n\n#Philosophy #NaserJournal'
        elif slot == "night":
            item = self.quote_engine.get_daily_puzzle()
            post_text = f"🧩 DAILY INTELLECTUAL CHALLENGE:\n\n{item['text']}\n\nHow do you resolve this paradox? Share your thoughts below."
        else:
            note = random.choice(CURIOSITY_NOTES)
            post_text = f"💡 CURIOSITY ARCHIVE:\n\n{note['text']}\n\n#History #Science #Knowledge"

        results = {}

        # 1. Post to Substack Notes
        if self.substack.is_configured:
            sub_res = self.substack.publish_note(post_text)
            results["substack_note"] = sub_res
        else:
            results["substack_note"] = {"success": False, "reason": "No credentials"}

        # 2. Post to X / Twitter
        if self.twitter.is_configured:
            tw_res = self.twitter.post_tweet(post_text)
            results["twitter"] = tw_res
        else:
            results["twitter"] = {"success": False, "reason": "No credentials"}

        # 3. Post to Telegram
        if self.telegram.is_configured:
            tg_res = self.telegram.broadcast_article(
                title="Curiosity Note",
                hook=post_text[:120] + "...",
                article_url="https://naserkhan.substack.com",
            )
            results["telegram"] = tg_res
        else:
            results["telegram"] = {"success": False, "reason": "No credentials"}

        return {"text": post_text, "results": results}
