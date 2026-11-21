"""
X (Twitter) Publishing Integration for Naser AI Media Engine.
Posts curiosity hooks, quotes, and article teaser links using session cookies (auth_token & ct0).
Bypasses the $100/mo X API fee for ₹0.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
import httpx
from integrations.cookie_manager import CookieManager

logger = logging.getLogger("media_engine.twitter")


class TwitterPublisher:
    def __init__(self):
        self.cookie_mgr = CookieManager()
        self.auth = self.cookie_mgr.get_twitter_auth()
        self.cookies = self.auth["cookies"]
        self.headers = self.auth["headers"]

    @property
    def is_configured(self) -> bool:
        return bool(self.cookies.get("auth_token") and self.cookies.get("ct0"))

    def post_tweet(self, text: str) -> Dict[str, Any]:
        """
        Publishes a tweet using X's internal GraphQL CreateTweet endpoint.
        """
        if not self.is_configured:
            return {"success": False, "error": "X/Twitter cookies (auth_token/ct0) not configured."}

        url = "https://x.com/i/api/graphql/xTflhVy0LgHGgahSoFdYTw/CreateTweet"
        
        payload = {
            "variables": {
                "tweet_text": text,
                "dark_request": False,
                "media": {"media_entities": [], "possibly_sensitive": False},
                "semantic_annotation_ids": [],
            },
            "features": {
                "communities_web_enable_tweet_community_results_fetch": True,
                "c9s_tweet_anatomy_moderator_badge_enabled": True,
                "tweetypie_unmention_optimization_enabled": True,
                "responsive_web_edit_tweet_api_enabled": True,
                "graphql_is_translatable_rweb_tweet_is_translatable_enabled": True,
                "view_counts_everywhere_api_enabled": True,
                "longform_notetweets_consumption_enabled": True,
                "responsive_web_twitter_article_tweet_consumption_enabled": True,
                "tweet_awards_web_tipping_enabled": False,
                "creator_subscriptions_quote_tweet_preview_enabled": False,
                "freedom_of_speech_not_reach_fetch_enabled": True,
                "standardized_nudges_misinfo": True,
                "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": True,
                "rweb_video_timestamps_enabled": True,
                "longform_notetweets_rich_text_read_enabled": True,
                "longform_notetweets_inline_media_enabled": True,
                "rweb_tipjar_consumption_enabled": True,
                "responsive_web_graphql_exclude_directive_enabled": True,
                "verified_phone_label_enabled": False,
                "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
                "responsive_web_graphql_timeline_navigation_enabled": True,
                "responsive_web_enhance_cards_enabled": False,
            },
            "queryId": "xTflhVy0LgHGgahSoFdYTw",
        }

        try:
            with httpx.Client(timeout=30.0, cookies=self.cookies, headers=self.headers) as client:
                resp = client.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    tweet_results = data.get("data", {}).get("create_tweet", {}).get("tweet_results", {}).get("result", {})
                    tweet_id = tweet_results.get("rest_id", "")
                    logger.info(f"Published to X/Twitter successfully! Tweet ID: {tweet_id}")
                    return {
                        "success": True,
                        "post_id": tweet_id,
                        "post_url": f"https://x.com/i/status/{tweet_id}" if tweet_id else "",
                        "raw": data,
                    }
                else:
                    logger.warning(f"X/Twitter post failed: {resp.status_code} - {resp.text}")
                    return {"success": False, "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
        except Exception as e:
            logger.error(f"Error publishing to X/Twitter: {e}")
            return {"success": False, "error": str(e)}
