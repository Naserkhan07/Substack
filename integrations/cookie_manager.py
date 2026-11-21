"""
Multi-Cookie Manager for Naser AI Media Engine.
Seamlessly handles both:
1. A single combined cookies.txt file or COOKIES_TXT secret.
2. Separate per-platform cookie files:
   - substack.com_cookies.txt (or SUBSTACK_COOKIES)
   - x.com_cookies.txt (or TWITTER_COOKIES)
   - medium.com_cookies.txt (or MEDIUM_COOKIES)
   - buttondown.com_cookies.txt (or BUTTONDOWN_COOKIES)
3. Any *_cookies.txt files located in the project or a cookies/ folder.
"""

import os
import glob
import tempfile
import http.cookiejar
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("media_engine.cookies")

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class CookieManager:
    def __init__(self, cookies_path: Optional[str] = None):
        self.jar = http.cookiejar.MozillaCookieJar()
        self._loaded = False
        self._load_all_cookies(cookies_path)

    def _load_cookie_content(self, raw_content: str):
        """Loads Netscape cookie text from a string."""
        if not raw_content or not raw_content.strip():
            return
        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as tmp:
            tmp.write(raw_content)
            tmp_path = tmp.name
        try:
            self.jar.load(tmp_path, ignore_discard=True, ignore_expires=True)
            self._loaded = True
        except Exception as e:
            logger.debug(f"Error parsing raw cookie text: {e}")
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def _load_cookie_file(self, file_path: str):
        """Loads a Netscape cookie file into the jar."""
        if os.path.exists(file_path) and os.path.getsize(file_path) > 10:
            try:
                self.jar.load(file_path, ignore_discard=True, ignore_expires=True)
                self._loaded = True
                logger.info(f"Loaded cookie file: {os.path.basename(file_path)}")
            except Exception as e:
                logger.warning(f"Could not load {file_path}: {e}")

    def _load_all_cookies(self, explicit_path: Optional[str] = None):
        """Discovers and merges all single or multiple cookie sources."""
        # 1. Explicit path if provided
        if explicit_path and os.path.exists(explicit_path):
            self._load_cookie_file(explicit_path)

        # 2. Main cookies.txt
        main_cookies = os.path.join(ROOT_DIR, "cookies.txt")
        if os.path.exists(main_cookies):
            self._load_cookie_file(main_cookies)

        # 3. Separate per-platform cookie files in root directory
        for pattern in ["*_cookies.txt", "*_cookies.json", "cookies/*.txt", "cookies/*.json"]:
            for match in glob.glob(os.path.join(ROOT_DIR, pattern)):
                self._load_cookie_file(match)

        # 4. Check user Downloads folder if files exist there (convenience for local runs)
        downloads_dir = os.path.expanduser("~/Downloads")
        if os.path.exists(downloads_dir):
            for candidate in [
                "substack.com_cookies.txt",
                "x.com_cookies.txt",
                "medium.com_cookies.txt",
                "buttondown.com_cookies.txt",
            ]:
                dl_path = os.path.join(downloads_dir, candidate)
                if os.path.exists(dl_path):
                    self._load_cookie_file(dl_path)

        # 5. Environment variables (for GitHub Secrets)
        env_vars = [
            "COOKIES_TXT",
            "SUBSTACK_COOKIES",
            "TWITTER_COOKIES",
            "MEDIUM_COOKIES",
            "BUTTONDOWN_COOKIES",
        ]
        for var in env_vars:
            val = os.getenv(var)
            if val:
                self._load_cookie_content(val)

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def get_cookies_for_domain(self, domain_keyword: str) -> Dict[str, str]:
        """Returns key-value cookies for any domain containing domain_keyword."""
        cookies = {}
        for c in self.jar:
            if domain_keyword in c.domain:
                cookies[c.name] = c.value
        return cookies

    def get_substack_cookies(self) -> Dict[str, str]:
        """Returns dictionary of cookies needed for Substack."""
        cookies = self.get_cookies_for_domain("substack.com")
        if not cookies.get("substack.sid") and os.getenv("SUBSTACK_SID"):
            cookies["substack.sid"] = os.getenv("SUBSTACK_SID", "")
        return cookies

    def get_twitter_auth(self) -> Dict[str, Any]:
        """Returns cookies and essential headers for X/Twitter."""
        cookies = self.get_cookies_for_domain("x.com")
        cookies.update(self.get_cookies_for_domain("twitter.com"))
        
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
        """Returns dictionary of cookies needed for Buttondown."""
        return self.get_cookies_for_domain("buttondown.com")
