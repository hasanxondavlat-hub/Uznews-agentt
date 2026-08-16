"""
Manbalardan (RSS yoki HTML) so'nggi maqolalar ro'yxatini yig'ib oladi.
Har bir maqola uchun to'liq matn va asosiy rasm/video ham ajratib olinadi.
"""
import time
import logging
from dataclasses import dataclass, field
from typing import Optional

import requests
import feedparser
from bs4 import BeautifulSoup

logger = logging.getLogger("scraper")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; UzNewsAgent/1.0; +https://t.me/)"
}
REQUEST_TIMEOUT = 15


@dataclass
class Article:
    source_id: str
    source_name: str
    url: str
    title: str
    published: Optional[str] = None
    summary: str = ""
    full_text: str = ""
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    has_watermark: bool = False


def _find_working_rss(rss_urls: list[str]) -> Optional[str]:
    for url in rss_urls:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
            if resp.status_code == 200 and resp.content:
                parsed = feedparser.parse(resp.content)
                if parsed.entries:
                    return url
        except requests.RequestException as e:
            logger.warning("RSS urinishi muvaffaqiyatsiz %s: %s", url, e)
    return None


def fetch_links_via_rss(source: dict, limit: int = 15) -> list[str]:
    working_url = _find_working_rss(source["rss_urls"])
    if not working_url:
        return []
    resp = requests.get(working_url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
    parsed = feedparser.parse(resp.content)
    return [entry.link for entry in parsed.entries[:limit] if getattr(entry, "link", None)]


def fetch_links_via_html(source: dict, limit: int = 15) -> list[str]:
    try:
        resp = requests.get(source["fallback_list_url"], headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.error("HTML ro'yxat sahifasini olib bo'lmadi %s: %s", source["fallback_list_url"], e)
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    links = []
    for a in soup.select(source["link_selector"]):
        href = a.get("href")
        if not href:
            continue
        if href.startswith("/"):
            href = source["base_url"].rstrip("/") + href
        if href.startswith(source["base_url"]) and href not in links:
            links.append(href)
        if len(links) >= limit:
            break
    return links


def fetch_article_links(source: dict, limit: int = 15) -> list[str]:
    """RSS bo'lsa RSS orqali, bo'lmasa HTML sahifadan link terib chiqadi."""
    links = fetch_links_via_rss(source, limit=limit)
    if links:
        logger.info("%s: RSS orqali %d ta link topildi", source["name"], len(links))
        return links
    links = fetch_links_via_html(source, limit=limit)
    logger.info("%s: HTML fallback orqali %d ta link topildi", source["name"], len(links))
    return links


def fetch_article_content(source: dict, url: str) -> Optional[Article]:
    """Bitta maqola sahifasidan sarlavha, matn, rasm va video (bo'lsa) ni ajratib oladi."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.error("Maqolani olib bo'lmadi %s: %s", url, e)
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    title = None
    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        title = og_title["content"].strip()
    elif soup.find("h1"):
        title = soup.find("h1").get_text(strip=True)
    if not title:
        return None

    paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
    full_text = "\n".join(p for p in paragraphs if len(p) > 30)

    image_url = None
    og_image = soup.find("meta", property="og:image")
    if og_image and og_image.get("content"):
        image_url = og_image["content"].strip()

    video_url = None
    og_video = soup.find("meta", property="og:video") or soup.find("meta", property="og:video:url")
    if og_video and og_video.get("content"):
        video_url = og_video["content"].strip()
    else:
        video_tag = soup.find("video")
        if video_tag:
            source_tag = video_tag.find("source")
            if source_tag and source_tag.get("src"):
