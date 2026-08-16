"""
Yangilik manbalari konfiguratsiyasi.
"""

SOURCES = [
    {
        "id": "kun",
        "name": "Kun.uz",
        "base_url": "https://kun.uz",
        "rss_urls": [
            "https://kun.uz/uz/rss",
            "https://kun.uz/news/rss",
        ],
        "fallback_list_url": "https://kun.uz/uz",
        "link_selector": "a.article-link, article a[href*='/uz/news/']",
        "has_watermark": True,
    },
    {
        "id": "daryo",
        "name": "Daryo.uz",
        "base_url": "https://daryo.uz",
        "rss_urls": [
            "https://daryo.uz/rss",
            "https://daryo.uz/uz/rss",
        ],
        "fallback_list_url": "https://daryo.uz/uz",
        "link_selector": "a.news-card, article a",
        "has_watermark": False,
    },
    {
        "id": "gazeta",
        "name": "Gazeta.uz",
        "base_url": "https://www.gazeta.uz",
        "rss_urls": [
            "https://www.gazeta.uz/uz/rss/",
            "https://www.gazeta.uz/rss/",
        ],
        "fallback_list_url": "https://www.gazeta.uz/uz/",
        "link_selector": "a.gzt-teaser__link, article a",
        "has_watermark": False,
    },
]

MAX_POSTS_PER_DAY = 10
MAX_CANDIDATES_PER_RUN = 25
CHECK_INTERVAL_HOURS = 2
