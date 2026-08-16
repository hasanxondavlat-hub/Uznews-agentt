"""
Deploy qilishdan oldin ishga tushirib, har bir manba haqiqatan ham
link va kontent qaytarayotganini tekshirish uchun.

Ishlatish:  python -m app.check_sources
"""
import logging

from .scraper import fetch_article_links, fetch_article_content
from .sources import SOURCES

logging.basicConfig(level=logging.INFO, format="%(message)s")


def main():
    for source in SOURCES:
        print(f"\n=== {source['name']} ===")
        links = fetch_article_links(source, limit=3)
        if not links:
            print("  ❌ Hech qanday link topilmadi. sources.py'dagi rss_urls yoki "
                  "fallback_list_url/link_selector'ni tekshiring.")
            continue
        print(f"  ✅ {len(links)} ta link topildi:")
        for link in links:
            print(f"     - {link}")
        article = fetch_article_content(source, links[0])
        if article and article.full_text:
            print(f"  ✅ Birinchi maqola o'qildi: \"{article.title[:60]}...\"")
            print(f"     Matn uzunligi: {len(article.full_text)} belgi")
            print(f"     Rasm: {article.image_url or 'topilmadi'}")
        else:
            print("  ❌ Maqola matnini o'qib bo'lmadi. scraper.py'dagi selectorlarni tekshiring.")


if __name__ == "__main__":
    main()
