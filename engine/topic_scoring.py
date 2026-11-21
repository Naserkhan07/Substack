"""
Topic Scoring Engine for Naser AI Media Engine.
Ranks candidate topics based on curiosity, historical importance,
uniqueness, and visual storytelling potential.
"""

from typing import Dict, Any


class TopicScorer:
    def __init__(self):
        # Weights for scoring criteria
        self.weights = {
            "curiosity": 0.35,
            "importance": 0.25,
            "uniqueness": 0.25,
            "visual_potential": 0.15,
        }

    def score_topic(
        self,
        title: str,
        category: str,
        suggested_angle: str,
        is_seed: bool = False,
        has_archival_imagery: bool = True,
    ) -> Dict[str, float]:
        """
        Calculates scores for a topic based on category affinity, angle strength, and visual assets.
        """
        # Baseline scores
        curiosity = 8.5 if any(k in suggested_angle.lower() for k in ["psychology", "secret", "fall", "blunder", "unknown", "paradox", "turning point", "mystery"]) else 7.5
        importance = 9.0 if category in ["history_extraordinary_personalities", "science_ai_technology"] else 7.5
        uniqueness = 8.0 if not any(common in title.lower() for common in ["einstein", "musk", "jobs"]) else 7.0
        visual = 9.0 if has_archival_imagery else 6.5

        if is_seed:
            curiosity = min(10.0, curiosity + 0.5)

        total = (
            curiosity * self.weights["curiosity"]
            + importance * self.weights["importance"]
            + uniqueness * self.weights["uniqueness"]
            + visual * self.weights["visual_potential"]
        )

        return {
            "curiosity_score": round(curiosity, 2),
            "historical_importance": round(importance, 2),
            "uniqueness_score": round(uniqueness, 2),
            "total_score": round(total, 2),
        }
