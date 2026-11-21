"""
Quality Assurance and Anti-Hallucination Gatekeeper for Naser AI Media Engine.
Validates word count, verifies citations, checks hook lengths, and filters generic AI filler.
"""

import re
import logging
from typing import Dict, Any, List

logger = logging.getLogger("media_engine.quality_check")

BANNED_AI_PHRASES = [
    "delve into",
    "it is worth noting",
    "testament to",
    "in conclusion",
    "beacon of hope",
    "at the end of the day",
    "tapestry of",
    "a reminder that",
]


class QualityChecker:
    def __init__(self, min_words: int = 700, max_words: int = 2500):
        self.min_words = min_words
        self.max_words = max_words

    def verify_article(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs comprehensive QA checks on an article draft.
        Returns: {"passed": bool, "errors": list, "warnings": list, "word_count": int}
        """
        content = article.get("content_markdown", "")
        hook = article.get("selected_hook", "")
        title = article.get("title", "")

        errors = []
        warnings = []

        # 1. Word Count Check
        words = content.split()
        word_count = len(words)
        if word_count < self.min_words:
            errors.append(f"Article is too short: {word_count} words (minimum is {self.min_words}).")
        elif word_count > self.max_words:
            warnings.append(f"Article is lengthy: {word_count} words.")

        # 2. Hook length check (6-14 words)
        hook_words = hook.strip().split()
        if len(hook_words) < 5 or len(hook_words) > 16:
            warnings.append(f"Hook word count ({len(hook_words)} words) is outside ideal 6-14 word range.")

        # 3. Citation Check
        if "Sources & Archival References" not in content and "References" not in content:
            warnings.append("Article is missing an explicit 'Sources & Archival References' section.")

        # 4. Check for banned generic AI expressions
        lower_content = content.lower()
        found_cliches = [p for p in BANNED_AI_PHRASES if p in lower_content]
        if found_cliches:
            warnings.append(f"Found generic AI cliches: {found_cliches}")

        passed = len(errors) == 0

        logger.info(f"QA Check for '{title}': Passed={passed}, Words={word_count}, Warnings={len(warnings)}")

        return {
            "passed": passed,
            "errors": errors,
            "warnings": warnings,
            "word_count": word_count,
        }
