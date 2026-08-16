"""
Bitta to'liq sikl:
  1. Barcha manbalardan so'nggi maqolalarni yig'ish
  2. Avval post qilinganlarni chiqarib tashlash (dedup)
  3. Kunlik limitdan qancha joy qolganini hisoblash
  4. Claude orqali eng muhim/qiziqarlilarini saralash
  5. Har birini qayta yozish, media tayyorlash va Telegramga yuborish
"""
import logging
import os
import sys
import time

from . import dedup_store, media_handler, telegram_poster, ai_pipeline
from .scraper import collect_candidates
from .sources import SOURCES, MAX_POSTS_PER_DAY, MAX_CANDIDATES_PER_RUN

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("main")


def run_once():
    dedup_store.init(os.environ["FIREBASE_SERVICE_ACCOUNT_PATH"])

    already_today = dedup_store.get_today_post_count()
    remaining = MAX_POSTS_PER_DAY - already_today
    if remaining <= 0:
        logger.info("Bugungi limit (%d) allaqachon to'lgan, sikl o'tkazib yuboriladi.", MAX_POSTS_PER_DAY)
        return

    logger.info("Manbalardan yangiliklar yig'ilmoqda...")
    candidates = collect_candidates(SOURCES, limit_per_source=MAX_CANDIDATES_PER_RUN // len(SOURCES) + 3)

    fresh = [a for a in candidates if not dedup_store.is_already_posted(a.url)]
    logger.info("%d ta yangi (hali post qilinmagan) maqola topildi.", len(fresh))
    if not fresh:
        return

    selected = ai_pipeline.rank_articles(fresh, max_select=remaining)
    logger.info("Claude %d ta maqolani tanladi.", len(selected))

    for item in selected:
        idx = item.get("index")
        if idx is None or idx >= len(fresh):
            continue
        article = fresh[idx]

        try:
            rewritten = ai_pipeline.rewrite_for_telegram(article)
            media = media_handler.prepare_media(article, ai_pipeline.suggest_image_query)

            ok = telegram_poster.post_to_channel(
                headline=rewritten["headline"],
                body=rewritten["body"],
                source_name=article.source_name,
                source_url=article.url,
                media=media,
            )
            if ok:
                dedup_store.mark_as_posted(article.url, article.title, article.source_id)
            time.sleep(3)
        except Exception:
            logger.exception("Maqolani qayta ishlashda xatolik: %s", article.url)


if __name__ == "__main__":
    run_once()
