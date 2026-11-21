"""
Magazine Editorial Banner & Social Thumbnail Engine for Naser AI Media Engine.
Creates high-contrast, premium documentary-style covers with:
- Authentic public-domain archival sourcing (Wikimedia Commons / Open Access)
- Free cloud generative fallback (Pollinations.ai / Hugging Face free tier)
- Professional Pillow typography compositor (Playfair Display & Cinzel)
- Dual dimensions: 1200x600 (horizontal banner) and 1080x1080 (square social card)
"""

import os
import textwrap
import urllib.parse
import logging
from typing import Dict, Any, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import httpx

from integrations.wiki_archive import WikiArchive

logger = logging.getLogger("media_engine.image_engine")

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS_DIR = os.path.join(ROOT_DIR, "assets", "fonts")
BANNERS_DIR = os.path.join(ROOT_DIR, "images", "banners")
SOCIAL_DIR = os.path.join(ROOT_DIR, "images", "social")
RAW_DIR = os.path.join(ROOT_DIR, "images", "raw")


class ImageEngine:
    def __init__(self):
        os.makedirs(BANNERS_DIR, exist_ok=True)
        os.makedirs(SOCIAL_DIR, exist_ok=True)
        os.makedirs(RAW_DIR, exist_ok=True)
        self.wiki_archive = WikiArchive(raw_images_dir=RAW_DIR)

    def _get_font(self, font_name: str, size: int) -> ImageFont.FreeTypeFont:
        """Loads a font from assets/fonts or falls back to system fonts."""
        custom_path = os.path.join(FONTS_DIR, font_name)
        if os.path.exists(custom_path):
            try:
                return ImageFont.truetype(custom_path, size)
            except Exception:
                pass

        # Windows system font fallbacks
        for fallback in [
            "C:\\Windows\\Fonts\\georgia.ttf",
            "C:\\Windows\\Fonts\\times.ttf",
            "C:\\Windows\\Fonts\\arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]:
            if os.path.exists(fallback):
                try:
                    return ImageFont.truetype(fallback, size)
                except Exception:
                    pass

        return ImageFont.load_default()

    def source_image(self, subject: str, category: str, fallback_prompt: str) -> str:
        """
        Sourcing Priority:
        1. Authentic public domain portrait/artwork from Wikimedia Commons
        2. Wikipedia main article thumbnail
        3. Free cloud generative AI (Pollinations.ai)
        """
        raw_slug = subject.lower().replace(" ", "_").replace("'", "")
        local_raw = os.path.join(RAW_DIR, f"{raw_slug}_source.jpg")

        if os.path.exists(local_raw):
            return local_raw

        # Step 1: Search Wikimedia Commons
        search_query = f"{subject} portrait painting OR photograph"
        commons_results = self.wiki_archive.search_commons_imagery(search_query, limit=3)
        if commons_results:
            for item in commons_results:
                url = item.get("url")
                if url and (url.endswith(".jpg") or url.endswith(".jpeg") or url.endswith(".png")):
                    path = self.wiki_archive.download_image(url, f"{raw_slug}_source.jpg")
                    if path and os.path.getsize(path) > 20000:
                        return path

        # Step 2: Try Wikipedia main summary image
        summary = self.wiki_archive.fetch_topic_summary(subject)
        if summary and summary.get("original_image_url"):
            path = self.wiki_archive.download_image(summary["original_image_url"], f"{raw_slug}_source.jpg")
            if path and os.path.getsize(path) > 20000:
                return path

        # Step 3: Cloud Generative Fallback (Pollinations.ai)
        logger.info(f"Using generative AI fallback for subject '{subject}'...")
        encoded = urllib.parse.quote(fallback_prompt)
        gen_url = f"https://image.pollinations.ai/prompt/{encoded}?width=1200&height=800&nologo=true&seed=42"
        try:
            with httpx.Client(timeout=45.0, follow_redirects=True) as client:
                resp = client.get(gen_url)
                if resp.status_code == 200:
                    with open(local_raw, "wb") as f:
                        f.write(resp.content)
                    return local_raw
        except Exception as e:
            logger.warning(f"Generative image fallback failed: {e}")

        # Ultimate fallback: return a solid dark editorial canvas
        blank = Image.new("RGB", (1200, 800), color=(18, 22, 28))
        blank.save(local_raw, "JPEG")
        return local_raw

    def _apply_cinematic_grade(self, img: Image.Image) -> Image.Image:
        """Applies subtle documentary tone and contrast curve."""
        img = ImageEnhance.Contrast(img).enhance(1.15)
        img = ImageEnhance.Color(img).enhance(0.92)  # Slight desaturation for timeless aesthetic
        return img

    def _create_vignette(self, size: Tuple[int, int]) -> Image.Image:
        """Creates a smooth directional gradient from dark bottom to semi-dark top."""
        width, height = size
        gradient = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(gradient)

        # Bottom dark band for maximum text contrast
        for y in range(height):
            # Alpha ramps up steeply in the lower 55%
            ratio = y / height
            if ratio < 0.35:
                alpha = int(90 * (1 - ratio / 0.35))
            elif ratio > 0.45:
                progress = (ratio - 0.45) / 0.55
                alpha = int(40 + 215 * (progress ** 1.6))
            else:
                alpha = 40
            draw.line([(0, y), (width, y)], fill=(8, 10, 14, min(255, alpha)))

        return gradient

    def composite_banner(
        self,
        source_image_path: str,
        subject: str,
        category: str,
        hook: str,
        slug: str,
    ) -> Tuple[str, str]:
        """
        Creates both:
        1. 1200x600 Horizontal Editorial Banner
        2. 1080x1080 Square Social Card
        Returns: (banner_path, social_card_path)
        """
        banner_path = os.path.join(BANNERS_DIR, f"{slug}_banner_1200x600.jpg")
        social_path = os.path.join(SOCIAL_DIR, f"{slug}_social_1080x1080.jpg")

        with Image.open(source_image_path).convert("RGBA") as src:
            # 1. Render 1200x600 Banner
            self._render_composition(
                src=src,
                target_size=(1200, 600),
                subject=subject,
                category=category,
                hook=hook,
                out_path=banner_path,
                is_square=False,
            )

            # 2. Render 1080x1080 Social Card
            self._render_composition(
                src=src,
                target_size=(1080, 1080),
                subject=subject,
                category=category,
                hook=hook,
                out_path=social_path,
                is_square=True,
            )

        logger.info(f"Generated banner: {banner_path}")
        logger.info(f"Generated social card: {social_path}")
        return banner_path, social_path

    def _render_composition(
        self,
        src: Image.Image,
        target_size: Tuple[int, int],
        subject: str,
        category: str,
        hook: str,
        out_path: str,
        is_square: bool = False,
    ):
        tw, th = target_size
        # Intelligent cover crop
        src_w, src_h = src.size
        scale = max(tw / src_w, th / src_h)
        nw, nh = int(src_w * scale), int(src_h * scale)
        scaled = src.resize((nw, nh), Image.Resampling.LANCZOS)
        
        # Center-crop
        left = (nw - tw) // 2
        top = (nh - th) // 2
        cropped = scaled.crop((left, top, left + tw, top + th))

        # Color grade
        graded = self._apply_cinematic_grade(cropped.convert("RGB")).convert("RGBA")

        # Vignette overlay
        vignette = self._create_vignette(target_size)
        base = Image.alpha_composite(graded, vignette)

        draw = ImageDraw.Draw(base)

        # Fonts
        font_hook = self._get_font("PlayfairDisplay-Bold.ttf", 46 if is_square else 38)
        font_title = self._get_font("Cinzel-Bold.ttf", 32 if is_square else 26)
        font_badge = self._get_font("Cinzel-Bold.ttf", 15)
        font_brand = self._get_font("Cinzel-Bold.ttf", 13)

        # 1. Category Badge (Top Left)
        badge_text = f"◆ {category.upper().replace('_', ' ')} ◆"
        badge_x, badge_y = 50, 45
        draw.text((badge_x, badge_y), badge_text, font=font_badge, fill=(229, 161, 0, 240))

        # 2. Subtle top brand tag (Top Right)
        brand_tag = "NASER JOURNAL"
        brand_bbox = draw.textbbox((0, 0), brand_tag, font=font_brand)
        bw = brand_bbox[2] - brand_bbox[0]
        draw.text((tw - bw - 50, badge_y), brand_tag, font=font_brand, fill=(180, 185, 195, 200))

        # 3. Subject Name (Above Hook)
        subject_y = th - (420 if is_square else 240)
        draw.text((50, subject_y), subject.upper(), font=font_title, fill=(212, 175, 55, 255))

        # 4. Gold Divider Line
        line_y = subject_y + (45 if is_square else 38)
        draw.line([(50, line_y), (140, line_y)], fill=(212, 175, 55, 255), width=3)

        # 5. Curiosity Hook (Textwrapped with shadow for readability)
        hook_y = line_y + 18
        wrapped_hook = textwrap.fill(f'"{hook}"', width=28 if is_square else 38)
        
        # Shadow
        draw.multiline_text(
            (52, hook_y + 2),
            wrapped_hook,
            font=font_hook,
            fill=(0, 0, 0, 220),
            spacing=10,
        )
        # Main text
        draw.multiline_text(
            (50, hook_y),
            wrapped_hook,
            font=font_hook,
            fill=(255, 255, 255, 255),
            spacing=10,
        )

        # 6. Bottom Edge Subtitle / Tagline
        bottom_tag = "AN INTELLECTUAL EXPLORATION OF HISTORY & EXISTENCE"
        draw.text((50, th - 35), bottom_tag, font=font_brand, fill=(140, 145, 155, 210))

        # Final Save
        final_rgb = base.convert("RGB")
        final_rgb.save(out_path, "JPEG", quality=92, optimize=True)
