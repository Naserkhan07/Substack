"""
Cookie Manager for Naser AI Media Engine.
Parses Netscape-format cookies.txt or JSON cookie files and provides clean,
platform-specific session cookies and CSRF headers for Substack, X/Twitter, Medium, and Buttondown.
"""

import os
import http.cookiejar
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("media_engine.cookies")

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_COOKIES_TXT = os.path.join(ROOT_DIR, "cookies.txt")


class CookieManager:
    def __init__(self, cookies_path: Optional[str] = None):
        self.cookies_path = cookies_path or os.getenv("COOKIES_TXT_PATH", DEFAULT_COOKIES_TXT)
        self.jar = http.cookiejar.MozillaCookieJar()
        self._loaded = False
        self._load_cookies()

    def _load_cookies(self):
        """Loads cookies from cookies.txt or COOKIES_TXT environment variable."""
        if os.path.exists(self.cookies_path):
            try:
                self.jar.load(self.cookies_path, ignore_discard=True, ignore_expires=True)
                self._loaded = True
                logger.info(f"Loaded cookies from file: {self.cookies_path}")
                return
            except Exception as e:
                logger.warning(f"Failed to load cookies from {self.cookies_path}: {e}")

        # Check if environment variable contains raw Netscape cookies content
        raw_env = os.getenv("COOKIES_TXT")
        if raw_env:
            import tempfile
            with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as tmp:
                tmp.write(raw_env)
                tmp_path = tmp.name
            try:
                self.jar.load(tmp_path, ignore_discard=True, ignore_expires=True)
                self._loaded = True
                logger.info("Loaded cookies from COOKIES_TXT environment variable.")
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def get_cookies_for_domain(self, domain_keyword: str) -> Dict[str, str]:
        """Returns a dictionary of key-value cookies for domains containing domain_keyword."""
        cookies = {}
        for c in self.jar:
            if domain_keyword in c.domain:
                cookies[c.name] = c.value
        return cookies

    def get_substack_cookies(self) -> Dict[str, str]:
        """Returns dictionary of cookies needed for Substack."""
        cookies = self.get_cookies_for_domain("substack.com")
        # Direct fallback to environment variable if set
        if not cookies.get("substack.sid") and os.getenv("SUBSTACK_SID"):
            cookies["substack.sid"] = os.getenv("SUBSTACK_SID", "")
        return cookies

    def get_twitter_auth(self) -> Dict[str, Any]:
        """Returns cookies and essential headers for X/Twitter."""
        cookies = self.get_cookies_for_domain("x.com")
        cookies.update(self.get_cookies_for_domain("twitter.com"))
        
        # Override with explicit env vars if provided
        if os.getenv("TWITTER_AUTH_TOKEN"):
            cookies["auth_token"] = os.getenv("TWITTER_AUTH_TOKEN")
        if os.getenv("TWITTER_CT0"):
            cookies["ct0"] = os.getenv("TWITTER_CT0")

        ct0 = cookies.get("ct0", "")
        headers = {
            "x-csrf-token": ct0,
            "x-twitter-auth-type": "OAuth2Session",
            "authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
        }
        return {"cookies": cookies, "headers": headers}

    def get_medium_cookies(self) -> Dict[str, str]:
        """Returns dictionary of cookies needed for Medium."""
        return self.get_cookies_for_domain("medium.com")

    def get_buttondown_cookies(self) -> Dict[str, str]:
        """Returns dictionary of cookies needed for Buttondown web session."""
        return self.get_cookies_for_domain("buttondown.com")
