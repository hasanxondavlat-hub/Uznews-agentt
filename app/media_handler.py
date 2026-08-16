"""
Post uchun media (rasm/video) tayyorlaydi.
"""
import logging
import os
import tempfile

import requests

logger = logging.getLogger("media_handler")

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; UzNewsAgent/1.0)"}
UNSPLASH_ACCESS_KEY = os.environ.get("UNSPLASH_ACCESS_KEY", "")


def _download_to_temp(url: str, suffix: str):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30, stream=True)
        resp.raise_for_status()
        fd, path = tempfile.mkstemp(suffix=suffix)
        with os.fdopen(fd, "wb") as f:
            for chunk in resp.iter_content(8192):
                f.write(chunk)
        return path
    except requests.RequestException as e:
        logger.error("Media yuklab olinmadi %s: %s", url, e)
        return None


def search_unsplash_image(query: str):
    if not UNSPLASH_ACCESS_KEY:
        logger.warning("UNSPLASH_ACCESS_KEY sozlanmagan, ochiq-manba rasm qidirish o'tkazib yuborildi")
        return None
    try:
        resp = requests.get(
            "https://api.unsplash.com/search/photos",
            params={"query": query, "per_page": 1, "orientation": "landscape"},
            headers={"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"},
            timeout=15,
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
        if results:
            return results[0]["urls"]["regular"]
    except requests.RequestException as e:
        logger.error("Unsplash qidiruvi muvaffaqiyatsiz: %s", e)
    return None


def prepare_media(article, image_query_fn) -> dict:
    if article.video_url:
        path = _download_to_temp(article.video_url, ".mp4")
        if path:
            return {"type": "video", "path": path, "source_url": article.url}

    if article.image_url and not article.has_watermark:
        path = _download_to_temp(article.image_url, ".jpg")
        if path:
            return {"type": "photo", "path": path}

    query = image_query_fn(article)
    alt_url = search_unsplash_image(query)
    if alt_url:
        path = _download_to_temp(alt_url, ".jpg")
        if path:
            return {"type": "photo", "path": path}

    return {"type": "none"}
