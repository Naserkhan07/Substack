"""
Autonomous Topic Discovery Engine for Naser AI Media Engine.
Continuously discovers subjects across the 7 editorial categories with:
- Deep discovery of historical personalities (50% allocation)
- Science, AI & Technology (15%)
- Philosophy & Psychology (12%)
- Entrepreneurship (8%)
- Nature & Biology (5%)
- Horror & Sci-Fi (5%)
- Puzzles & Quotes (5%)
"""

import logging
import random
from typing import List, Dict, Any
from database import db
from engine.topic_scoring import TopicScorer

logger = logging.getLogger("media_engine.discovery")

# Seed bank of diverse, extraordinary historical personalities across civilizations
HISTORICAL_PERSONALITIES = [
    # Conquerors & Leaders
    {"name": "Alexander the Great", "civilization": "Macedonian", "angle": "The psychological hubris that doomed his empire at age 32"},
    {"name": "Hannibal Barca", "civilization": "Carthaginian", "angle": "The tactical genius who crossed the Alps and trapped Rome in its own fears"},
    {"name": "Cyrus the Great", "civilization": "Persian", "angle": "The conqueror who founded the first human rights charter in history"},
    {"name": "Saladin", "civilization": "Ayyubid", "angle": "The chivalrous sultan whose mercy stunned his Crusader enemies"},
    {"name": "Genghis Khan", "civilization": "Mongol", "angle": "How an exiled orphan engineered the most formidable meritocracy on Earth"},
    {"name": "Ashoka the Great", "civilization": "Maurya", "angle": "The bloody conquest of Kalinga that birthed the world's first pacifist emperor"},
    {"name": "Julius Caesar", "civilization": "Roman", "angle": "The single crossing of the Rubicon that liquidated a 500-year republic"},
    {"name": "Napoleon Bonaparte", "civilization": "French", "angle": "The Corsican outsider who reshaped European law from the battlefield"},
    {"name": "Richard the Lionheart", "civilization": "English", "angle": "The warrior king who bankrupt his kingdom for chivalric glory"},
    {"name": "Catherine the Great", "civilization": "Russian", "angle": "The German princess who seized Russia and annexed the Enlightenment"},
    {"name": "Cleopatra VII", "civilization": "Ptolemaic Egyptian", "angle": "The polyglot diplomat erased by Roman propaganda into a seductress"},
    {"name": "Akbar the Great", "civilization": "Mughal", "angle": "The illiterate emperor who synthesized the religions of Hindustan"},
    
    # Scientists, Inventors & Visionaries
    {"name": "Nikola Tesla", "civilization": "Serbian-American", "angle": "The solitary prophet who envisioned wireless energy a century too early"},
    {"name": "Marie Curie", "civilization": "Polish-French", "angle": "The relentless pioneer who discovered radium in a freezing shed and paid with her life"},
    {"name": "Alan Turing", "civilization": "British", "angle": "The mathematical genius who decoded Nazi ciphers and invented the modern mind"},
    {"name": "Leonardo da Vinci", "civilization": "Italian Renaissance", "angle": "The insatiable anatomical notebooks that anticipated five centuries of engineering"},
    {"name": "Galileo Galilei", "civilization": "Italian", "angle": "The defiant telescope that shattered celestial dogma and faced the Inquisition"},
    {"name": "Ada Lovelace", "civilization": "British", "angle": "The visionary poetess of computing who wrote the world's first algorithm"},
    {"name": "Ibn al-Haytham", "civilization": "Islamic Golden Age", "angle": "The father of optics who proved how light moves and forged the scientific method"},
    {"name": "Charles Darwin", "civilization": "British", "angle": "The twenty-year silence before publishing natural selection out of moral dread"},

    # Philosophers & Thinkers
    {"name": "Marcus Aurelius", "civilization": "Roman", "angle": "The private journal of the master of the world battling despair and plague"},
    {"name": "Friedrich Nietzsche", "civilization": "German", "angle": "The lonely wanderer of Sils-Maria who prophesied the 20th century's crisis of meaning"},
    {"name": "Socrates", "civilization": "Greek", "angle": "The gadfly of Athens whose suicide turned questioning into an immortal virtue"},
    {"name": "Sun Tzu", "civilization": "Chinese", "angle": "The paradoxical art of winning without ever fighting a single battle"},
    {"name": "Baruch Spinoza", "civilization": "Dutch-Jewish", "angle": "The lens grinder excommunicated by everyone for identifying God with nature"},
]

SCIENCE_TOPICS = [
    {"title": "The Mystery of the Fourth Dimension", "angle": "What higher-dimensional geometry reveals about the boundaries of human perception"},
    {"title": "The Quantum Eraser and the Illusion of Time", "angle": "How delayed-choice experiments prove the past is not as fixed as common sense demands"},
    {"title": "Black Hole Event Horizons and the Holographic Universe", "angle": "Could three-dimensional reality be an encoded projection from a cosmic boundary?"},
    {"title": "The Limits of Artificial General Intelligence", "angle": "Why predictive token synthesis may hit the Gödelian limits of true comprehension"},
]

PHILOSOPHY_TOPICS = [
    {"title": "Stoic Amor Fati: Loving Your Inevitable Destiny", "angle": "How Marcus Aurelius and Epictetus turned catastrophic events into psychological armor"},
    {"title": "The Ship of Theseus and the Illusion of the Self", "angle": "If every cell in your brain renews, who is the conscious entity reading this sentence?"},
    {"title": "The Dark Psychology of Cognitive Dissonance", "angle": "Why human minds defend demonstrable falsehoods to protect their fragile self-image"},
]

ENTREPRENEURSHIP_TOPICS = [
    {"title": "John D. Rockefeller and Asymmetric Strategic Moats", "angle": "How Standard Oil achieved 90% refining dominance not through drilling, but barrel logistics"},
    {"title": "Steve Jobs and the Cruelty of Creative Focus", "angle": "The ruthless decision-making framework that slashed 70% of Apple's products to save the company"},
]

NATURE_BIOLOGY_TOPICS = [
    {"title": "The Human Brain's Dark Energy Consumption", "angle": "Why your brain burns 20% of your metabolic caloric budget even while deep in dreamless sleep"},
    {"title": "Fibonacci Spirals and Phyllotaxis in Nature", "angle": "The inescapable mathematical constant governing sun-flower florets, nautilus shells, and galaxies"},
]


class TopicDiscoveryEngine:
    def __init__(self):
        self.scorer = TopicScorer()

    def discover_batch(self, count: int = 10) -> List[Dict[str, Any]]:
        """
        Discovers a fresh batch of topics and registers them in the persistent SQLite DB.
        """
        discovered = []

        # History candidates (50% target)
        for p in HISTORICAL_PERSONALITIES:
            topic_key = f"hist_{p['name'].lower().replace(' ', '_')}"
            if not db.is_topic_already_covered(topic_key):
                scores = self.scorer.score_topic(
                    title=p["name"],
                    category="history_extraordinary_personalities",
                    suggested_angle=p["angle"],
                    is_seed=True,
                    has_archival_imagery=True,
                )
                topic_id = db.save_topic(
                    topic_key=topic_key,
                    category="history_extraordinary_personalities",
                    title=p["name"],
                    description=f"{p['civilization']} historical figure: {p['angle']}",
                    suggested_angle=p["angle"],
                    curiosity_score=scores["curiosity_score"],
                    historical_importance=scores["historical_importance"],
                    uniqueness_score=scores["uniqueness_score"],
                    total_score=scores["total_score"],
                    source_url=f"https://en.wikipedia.org/wiki/{p['name'].replace(' ', '_')}",
                )
                discovered.append({"id": topic_id, "title": p["name"], "category": "history_extraordinary_personalities", "score": scores["total_score"]})

        # Science candidates
        for s in SCIENCE_TOPICS:
            topic_key = f"sci_{s['title'].lower().replace(' ', '_')[:30]}"
            if not db.is_topic_already_covered(topic_key):
                scores = self.scorer.score_topic(
                    title=s["title"],
                    category="science_ai_technology",
                    suggested_angle=s["angle"],
                    is_seed=True,
                    has_archival_imagery=False,
                )
                topic_id = db.save_topic(
                    topic_key=topic_key,
                    category="science_ai_technology",
                    title=s["title"],
                    description=s["angle"],
                    suggested_angle=s["angle"],
                    curiosity_score=scores["curiosity_score"],
                    historical_importance=scores["historical_importance"],
                    uniqueness_score=scores["uniqueness_score"],
                    total_score=scores["total_score"],
                    source_url="",
                )
                discovered.append({"id": topic_id, "title": s["title"], "category": "science_ai_technology", "score": scores["total_score"]})

        # Philosophy candidates
        for ph in PHILOSOPHY_TOPICS:
            topic_key = f"phil_{ph['title'].lower().replace(' ', '_')[:30]}"
            if not db.is_topic_already_covered(topic_key):
                scores = self.scorer.score_topic(
                    title=ph["title"],
                    category="philosophy_psychology",
                    suggested_angle=ph["angle"],
                    is_seed=True,
                    has_archival_imagery=False,
                )
                topic_id = db.save_topic(
                    topic_key=topic_key,
                    category="philosophy_psychology",
                    title=ph["title"],
                    description=ph["angle"],
                    suggested_angle=ph["angle"],
                    curiosity_score=scores["curiosity_score"],
                    historical_importance=scores["historical_importance"],
                    uniqueness_score=scores["uniqueness_score"],
                    total_score=scores["total_score"],
                    source_url="",
                )
                discovered.append({"id": topic_id, "title": ph["title"], "category": "philosophy_psychology", "score": scores["total_score"]})

        logger.info(f"Discovery engine registered {len(discovered)} new topics into database.")
        return discovered
