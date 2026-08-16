"""
Tayyor postni Telegram Bot API orqali kanalga yuboradi.
"""
import logging
import os

import requests

logger = logging.getLogger("telegram_poster")

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHANNEL_ID = os.environ["TELEGRAM_CHANNEL_ID"]
API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"

TELEGRAM_CAPTION_LIMIT = 1024
TELEGRAM_TEXT_LIMIT = 4096


def _build_caption(headline: str, body: str, source_name: str, source_url: str, limit: int) -> str:
    footer = f"\n\n🔗 Manba: {source_name}\n{source_url}"
    text = f"<b>{headline}</b>\n\n{body}"
    max_body_len = limit - len(footer) - len(f"<b>{headline}</b>\n\n") - 10
    if len(text) + len(footer) > limit:
        body = body[:max_body_len].rsplit(" ", 1)[0] + "…"
        text = f"<b>{headline}</b>\n\n{body}"
    return text + footer


def post_to_channel(headline: str, body: str, source_name: str, source_url: str, media: dict) -> bool:
    caption_limit = TELEGRAM_CAPTION_LIMIT if media["type"] in ("photo", "video") else TELEGRAM_TEXT_LIMIT
    text = _build_caption(headline, body, source_name, source_url, caption_limit)

    try:
        if media["type"] == "photo":
            with open(media["path"], "rb") as f:
                resp = requests.post(
                    f"{API_BASE}/sendPhoto",
                    data={"chat_id": CHANNEL_ID, "caption": text, "parse_mode": "HTML"},
                    files={"photo": f},
                    timeout=60,
                )
        elif media["type"] == "video":
            with open(media["path"], "rb") as f:
                resp = requests.post(
                    f"{API_BASE}/sendVideo",
                    data={"chat_id": CHANNEL_ID, "caption": text, "parse_mode": "HTML"},
                    files={"video": f},
                    timeout=120,
                )
        else:
            resp = requests.post(
                f"{API_BASE}/sendMessage",
                data={"chat_id": CHANNEL_ID, "text": text, "parse_mode": "HTML"},
                timeout=30,
            )

        resp.raise_for_status()
        result = resp.json()
        if not result.get("ok"):
            logger.error("Telegram xatosi: %s", result)
            return False
        logger.info("Post muvaffaqiyatli yuborildi: %s", headline)
        return True
    except requests.RequestException as e:
        logger.error("Telegramga yuborishda xatolik: %s", e)
        return False
    finally:
        if media.get("path") and os.path.exists(media["path"]):
            os.remove(media["path"])
