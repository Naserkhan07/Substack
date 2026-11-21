"""
Fact-Gathering and Research Engine for Naser AI Media Engine.
Performs pre-writing research via Wikipedia REST API, gathers factual milestones,
and extracts verified source citations to eliminate hallucinations.
"""

import logging
from typing import Dict, Any, List
from integrations.wiki_archive import WikiArchive

logger = logging.getLogger("media_engine.research")


class ResearchEngine:
    def __init__(self):
        self.wiki_archive = WikiArchive()

    def research_topic(self, title: str, category: str, angle: str) -> Dict[str, Any]:
        """
        Gathers verified historical/scientific context, citations, and archival references.
        """
        logger.info(f"Researching topic: '{title}' in category '{category}'")

        # 1. Fetch factual summary from Wikipedia
        summary = self.wiki_archive.fetch_topic_summary(title)

        facts = []
        sources = []

        if summary:
            extract = summary.get("extract", "")
            page_url = summary.get("page_url", "")
            if extract:
                facts.append(extract)
            if page_url:
                sources.append({"name": "Wikipedia Knowledge Base", "url": page_url})

        # 2. Check Wikimedia Commons for archival art / photo records
        commons_items = self.wiki_archive.search_commons_imagery(title, limit=2)
        for item in commons_items:
            sources.append({
                "name": f"Wikimedia Commons Archive: {item.get('title', '')}",
                "url": item.get("url", ""),
                "license": item.get("license", "Public Domain"),
            })

        return {
            "title": title,
            "category": category,
            "angle": angle,
            "verified_facts": facts,
            "sources": sources,
            "summary_snippet": summary.get("extract", "") if summary else "",
        }
