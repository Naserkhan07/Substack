"""
Substack Publishing Integration for Naser AI Media Engine.
Handles article drafts, live publishing, and Substack Notes via authenticated session cookies.
Target Publication: https://naserkhan.substack.com
"""

import os
import json
import base64
import logging
from typing import Dict, Any, Optional, List
import httpx
from integrations.cookie_manager import CookieManager

logger = logging.getLogger("media_engine.substack")


class SubstackPublisher:
    def __init__(self, publication_url: str = "https://naserkhan.substack.com"):
        self.publication_url = publication_url.rstrip("/")
        self.cookie_mgr = CookieManager()
        self.cookies = self.cookie_mgr.get_substack_cookies()
        self.user_id = self._extract_user_id()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Referer": f"{self.publication_url}/publish",
        }

    def _extract_user_id(self) -> int:
        """Extracts numeric user_id from substack.lli JWT cookie or falls back to known ID."""
        lli = self.cookies.get("substack.lli", "")
        if lli and "." in lli:
            try:
                payload_part = lli.split(".")[1]
                # Pad base64
                padded = payload_part + "=" * (-len(payload_part) % 4)
                decoded = json.loads(base64.urlsafe_b64decode(padded).decode("utf-8"))
                uid = decoded.get("userId")
                if uid:
                    return int(uid)
            except Exception:
                pass
        return 567782241  # Default authenticated user ID for naserkhan

    @property
    def is_configured(self) -> bool:
        return bool(self.cookies.get("substack.sid"))

    def _markdown_to_prosemirror(self, markdown: str) -> Dict[str, Any]:
        """Converts Markdown into Substack's ProseMirror doc schema."""
        nodes = []
        for block in markdown.split("\n\n"):
            block = block.strip()
            if not block:
                continue

            if block.startswith("# "):
                nodes.append({
                    "type": "heading",
                    "attrs": {"level": 1},
                    "content": [{"type": "text", "text": block[2:].strip()}],
                })
            elif block.startswith("### "):
                nodes.append({
                    "type": "heading",
                    "attrs": {"level": 3},
                    "content": [{"type": "text", "text": block[4:].strip()}],
                })
            elif block.startswith("## "):
                nodes.append({
                    "type": "heading",
                    "attrs": {"level": 2},
                    "content": [{"type": "text", "text": block[3:].strip()}],
                })
            elif block.startswith("> "):
                nodes.append({
                    "type": "blockquote",
                    "content": [{"type": "paragraph", "content": [{"type": "text", "text": block[2:].strip()}]}],
                })
            else:
                nodes.append({
                    "type": "paragraph",
                    "content": [{"type": "text", "text": block}],
                })

        return {"type": "doc", "content": nodes}

    def create_draft(
        self,
        title: str,
        subtitle: str,
        content_markdown: str,
        cover_image_url: Optional[str] = None,
        publish_immediately: bool = False,
    ) -> Dict[str, Any]:
        """
        Creates a new post draft on Substack and optionally publishes it live.
        """
        if not self.is_configured:
            return {"success": False, "error": "Substack session cookies not configured."}

        url = f"{self.publication_url}/api/v1/drafts"
        body_json = self._markdown_to_prosemirror(content_markdown)

        payload = {
            "draft_title": title,
            "draft_subtitle": subtitle,
            "draft_body": json.dumps(body_json),
            "draft_bylines": [{"id": self.user_id, "is_guest": False}],
            "type": "newsletter",
        }
        if cover_image_url:
            payload["cover_image"] = cover_image_url

        try:
            with httpx.Client(timeout=30.0, cookies=self.cookies, headers=self.headers) as client:
                resp = client.post(url, json=payload)
                if resp.status_code in [200, 201]:
                    data = resp.json()
                    draft_id = data.get("id")
                    logger.info(f"Substack draft created! ID: {draft_id}")

                    if publish_immediately and draft_id:
                        pub_res = self.publish_draft(draft_id)
                        return pub_res

                    return {
                        "success": True,
                        "post_id": str(draft_id),
                        "post_url": f"{self.publication_url}/publish/post/{draft_id}",
                        "raw": data,
                    }
                else:
                    logger.warning(f"Failed to create Substack draft: {resp.status_code} - {resp.text[:300]}")
                    return {"success": False, "error": f"HTTP {resp.status_code}: {resp.text[:300]}"}
        except Exception as e:
            logger.error(f"Error publishing to Substack: {e}")
            return {"success": False, "error": str(e)}

    def publish_draft(self, draft_id: int, send_email: bool = False) -> Dict[str, Any]:
        """
        Transitions an existing draft into a published post.
        """
        url = f"{self.publication_url}/api/v1/drafts/{draft_id}/publish"
        payload = {"send_email": send_email}

        try:
            with httpx.Client(timeout=30.0, cookies=self.cookies, headers=self.headers) as client:
                resp = client.post(url, json=payload)
                if resp.status_code in [200, 201]:
                    data = resp.json()
                    logger.info(f"Substack draft {draft_id} published successfully!")
                    return {
                        "success": True,
                        "post_id": str(draft_id),
                        "post_url": f"{self.publication_url}/p/{data.get('slug', '')}",
                        "raw": data,
                    }
                else:
                    return {"success": False, "error": f"HTTP {resp.status_code}: {resp.text[:300]}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def publish_note(self, text: str) -> Dict[str, Any]:
        """
        Publishes a micro-content update or quote directly to Substack Notes!
        """
        if not self.is_configured:
            return {"success": False, "error": "Substack session cookies not configured."}

        url = "https://substack.com/api/v1/comment/feed"
        body_json = {
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": text}],
                }
            ],
        }
        payload = {"body": body_json}

        try:
            with httpx.Client(timeout=30.0, cookies=self.cookies, headers=self.headers) as client:
                resp = client.post(url, json=payload)
                if resp.status_code in [200, 201]:
                    data = resp.json()
                    note_id = data.get("id")
                    logger.info(f"Published Substack Note successfully! ID: {note_id}")
                    return {"success": True, "post_id": str(note_id), "raw": data}
                else:
                    return {"success": False, "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
