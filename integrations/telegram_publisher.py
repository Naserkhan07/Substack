"""
Telegram Channel Publishing Integration for Naser AI Media Engine.
Broadcasts banner image cards, curiosity hooks, and article reading links
directly to your subscribers with 100% free official Telegram Bot API.
"""

import os
import logging
from typing import Dict, Any, Optional
import httpx

logger = logging.getLogger("media_engine.telegram")


class TelegramPublisher:
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()

    @property
    def is_configured(self) -> bool:
        return bool(self.bot_token and self.chat_id)

    def broadcast_article(
        self,
        title: str,
        hook: str,
        article_url: str,
        image_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Sends photo banner with title, hook, and reading button to Telegram channel.
        """
        if not self.is_configured:
            return {"success": False, "error": "TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID not configured."}

        caption = f"✨ *{title}*\n\n_{hook}_\n\n📖 [Read the Full Feature Article]({article_url})"

        if image_path and os.path.exists(image_path):
            url = f"https://api.telegram.org/bot{self.bot_token}/sendPhoto"
            try:
                with open(image_path, "rb") as photo:
                    files = {"photo": photo}
                    data = {
                        "chat_id": self.chat_id,
                        "caption": caption,
                        "parse_mode": "Markdown",
                    }
                    with httpx.Client(timeout=30.0) as client:
                        resp = client.post(url, data=data, files=files)
                        if resp.status_code == 200:
                            msg_id = resp.json().get("result", {}).get("message_id")
                            logger.info(f"Broadcasted to Telegram Channel! Message ID: {msg_id}")
                            return {"success": True, "post_id": str(msg_id)}
                        else:
                            return {"success": False, "error": f"Telegram API error {resp.status_code}: {resp.text}"}
            except Exception as e:
                return {"success": False, "error": str(e)}

        # Fallback to plain text message
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": caption,
            "parse_mode": "Markdown",
        }
        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.post(url, json=payload)
                if resp.status_code == 200:
                    msg_id = resp.json().get("result", {}).get("message_id")
                    return {"success": True, "post_id": str(msg_id)}
                else:
                    return {"success": False, "error": resp.text}
        except Exception as e:
            return {"success": False, "error": str(e)}
