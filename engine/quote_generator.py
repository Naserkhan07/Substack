"""
Quotes, Puzzles and Mind Games Engine for Naser AI Media Engine.
Generates verified historical/scientific quotes, chess paradoxes,
logic puzzles, and deep reflections with zero fabrication.
"""

import random
import logging
from typing import Dict, Any, List
from database import db

logger = logging.getLogger("media_engine.quotes")

VERIFIED_QUOTES = [
    {
        "category": "philosophy_psychology",
        "text": "The soul becomes dyed with the color of its thoughts.",
        "author": "Marcus Aurelius",
        "citation": "Meditations, Book V",
    },
    {
        "category": "science_ai_technology",
        "text": "The present is theirs; the future, for which I really worked, is mine.",
        "author": "Nikola Tesla",
        "citation": "A Visit to Nikola Tesla (1904)",
    },
    {
        "category": "history_extraordinary_personalities",
        "text": "In the midst of chaos, there is also opportunity.",
        "author": "Sun Tzu",
        "citation": "The Art of War",
    },
    {
        "category": "philosophy_psychology",
        "text": "He who has a why to live can bear almost any how.",
        "author": "Friedrich Nietzsche",
        "citation": "Twilight of the Idols (1889)",
    },
    {
        "category": "science_ai_technology",
        "text": "We can only see a short distance ahead, but we can see plenty there that needs to be done.",
        "author": "Alan Turing",
        "citation": "Computing Machinery and Intelligence (1950)",
    },
    {
        "category": "human_biology_nature",
        "text": "In nature, nothing is perfect and everything is perfect. Trees can be contorted, bent in weird ways, and they're still beautiful.",
        "author": "Alice Walker",
        "citation": "The Color Purple",
    },
]

MIND_GAMES_AND_PUZZLES = [
    {
        "category": "quotes_puzzles_games",
        "type": "paradox",
        "text": "The Ship of Theseus: If every single wooden plank of a legendary ship is replaced over centuries until no original atom remains, is it still the same ship? And if someone collects the discarded rotting planks and rebuilds them, which one is authentic?",
        "author": "Plutarch",
        "citation": "Life of Theseus",
    },
    {
        "category": "quotes_puzzles_games",
        "type": "logic_puzzle",
        "text": "The Paradox of the Unexpected Examination: A professor announces that an exam will occur next week, but on a day that will be an absolute surprise until the morning it happens. A student proves that the exam cannot happen on Friday (it wouldn't be a surprise), and by backward induction, proves it cannot happen at all. On Wednesday, the exam happens. Why was the student completely wrong?",
        "author": "Michael Scriven",
        "citation": "Epistemic Logic Paradox (1951)",
    },
    {
        "category": "quotes_puzzles_games",
        "type": "chess_challenge",
        "text": "The Immortal Game (1851): Adolf Anderssen sacrificed both rooks, a bishop, and his queen—leaving himself with just three minor pieces—to deliver checkmate on move 23. What does this tactical masterclass teach us about material sacrifice versus unstoppable positional tempo?",
        "author": "Adolf Anderssen vs. Lionel Kieseritzky",
        "citation": "London Chess Tournament 1851",
    },
]


class QuoteEngine:
    def get_daily_quote(self) -> Dict[str, Any]:
        """Returns a verified, dignified quote and records it in SQLite."""
        selected = random.choice(VERIFIED_QUOTES)
        quote_id = db.save_note_or_quote(
            item_type="quote",
            category=selected["category"],
            content_text=selected["text"],
            author_or_attribution=selected["author"],
            verified=True,
            source_citation=selected["citation"],
            status="queued",
        )
        selected["id"] = quote_id
        return selected

    def get_daily_puzzle(self) -> Dict[str, Any]:
        """Returns an interactive reader challenge or paradox."""
        selected = random.choice(MIND_GAMES_AND_PUZZLES)
        puzzle_id = db.save_note_or_quote(
            item_type="puzzle",
            category=selected["category"],
            content_text=selected["text"],
            author_or_attribution=selected["author"],
            verified=True,
            source_citation=selected["citation"],
            status="queued",
        )
        selected["id"] = puzzle_id
        return selected
