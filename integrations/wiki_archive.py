"""
Wikimedia Commons and Wikipedia Archive Integration for Naser AI Media Engine.
Provides factual verification from Wikipedia REST API and high-resolution public-domain
image discovery from Wikimedia Commons API.
"""

import os
import urllib.parse
import logging
from typing import Dict, Any, Optional, List
import httpx

logger = logging.getLogger("media_engine.wiki_archive")

USER_AGENT = "NaserAIMediaEngine/1.0 (https://naserkhan.substack.com; contact: editorial@naserkhan.com)"


class WikiArchive:
    def __init__(self, raw_images_dir: str = "images/raw"):
        self.raw_images_dir = raw_images_dir
        os.makedirs(self.raw_images_dir, exist_ok=True)
        self.headers = {"User-Agent": USER_AGENT}

    def fetch_topic_summary(self, topic_title: str) -> Optional[Dict[str, Any]]:
        """
        Fetches official Wikipedia page summary, thumbnail, extract, and canonical URL.
        """
        encoded_title = urllib.parse.quote(topic_title.replace(" ", "_"))
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded_title}"

        try:
            with httpx.Client(timeout=15.0, headers=self.headers, follow_redirects=True) as client:
                resp = client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    return {
                        "title": data.get("title"),
                        "displaytitle": data.get("displaytitle"),
                        "description": data.get("description", ""),
                        "extract": data.get("extract", ""),
                        "page_url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
                        "thumbnail_url": data.get("thumbnail", {}).get("source", ""),
                        "original_image_url": data.get("originalimage", {}).get("source", ""),
                    }
        except Exception as e:
            logger.warning(f"Failed to fetch Wikipedia summary for '{topic_title}': {e}")

        return None

    def search_commons_imagery(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Searches Wikimedia Commons for public domain or CC-licensed historical paintings,
        portraits, and high-res imagery.
        """
        params = {
            "action": "query",
            "format": "json",
            "generator": "search",
            "gsrsearch": f"{query} filetype:bitmap",
            "gsrnamespace": 6,  # File namespace
            "gsrlimit": limit,
            "prop": "imageinfo",
            "iiprop": "url|size|mime|extmetadata",
        }
        url = "https://commons.wikimedia.org/w/api.php"

        results = []
        try:
            with httpx.Client(timeout=20.0, headers=self.headers) as client:
                resp = client.get(url, params=params)
                if resp.status_code == 200:
                    pages = resp.json().get("query", {}).get("pages", {})
                    for page_id, page_data in pages.items():
                        imageinfo = page_data.get("imageinfo", [])
                        if not imageinfo:
                            continue
                        info = imageinfo[0]
                        extmetadata = info.get("extmetadata", {})
                        license_short = extmetadata.get("LicenseShortName", {}).get("value", "Public Domain")
                        results.append({
                            "title": page_data.get("title", ""),
                            "url": info.get("url", ""),
                            "width": info.get("width", 0),
                            "height": info.get("height", 0),
                            "mime": info.get("mime", ""),
                            "license": license_short,
                            "artist": extmetadata.get("Artist", {}).get("value", "Unknown"),
                            "date": extmetadata.get("DateTimeOriginal", {}).get("value", ""),
                        })
        except Exception as e:
            logger.warning(f"Error querying Wikimedia Commons for '{query}': {e}")

        return results

    def download_image(self, image_url: str, filename: str) -> Optional[str]:
        """
        Downloads a remote image to the local raw images directory.
        """
        dest_path = os.path.join(self.raw_images_dir, filename)
        try:
            with httpx.Client(timeout=30.0, headers=self.headers, follow_redirects=True) as client:
                resp = client.get(image_url)
                if resp.status_code == 200:
                    with open(dest_path, "wb") as f:
                        f.write(resp.content)
                    logger.info(f"Downloaded archival image to: {dest_path}")
                    return dest_path
        except Exception as e:
            logger.warning(f"Failed to download image from {image_url}: {e}")

        return None
