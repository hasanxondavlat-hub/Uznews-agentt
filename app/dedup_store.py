"""
Post qilingan maqolalarni Firestore'da saqlaydi, shu orqali bir xil yangilik
ikki marta kanalga joylanib ketmasligi va kunlik limit hisoblanishi ta'minlanadi.
"""
import hashlib
import logging
from datetime import datetime, timezone

import firebase_admin
from firebase_admin import credentials, firestore

logger = logging.getLogger("dedup_store")

_db = None


def init(service_account_path: str):
    global _db
    if not firebase_admin._apps:
        cred = credentials.Certificate(service_account_path)
        firebase_admin.initialize_app(cred)
    _db = firestore.client()
    return _db


def _url_hash(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:24]


def is_already_posted(url: str) -> bool:
    doc = _db.collection("newsagent_posted").document(_url_hash(url)).get()
    return doc.exists


def mark_as_posted(url: str, title: str, source_id: str):
    _db.collection("newsagent_posted").document(_url_hash(url)).set({
        "url": url,
        "title": title,
        "source_id": source_id,
        "posted_at": datetime.now(timezone.utc).isoformat(),
    })
    _increment_daily_counter()


def _today_key() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _increment_daily_counter():
    ref = _db.collection("newsagent_daily").document(_today_key())
    ref.set({"count": firestore.Increment(1)}, merge=True)


def get_today_post_count() -> int:
    doc = _db.collection("newsagent_daily").document(_today_key()).get()
    if doc.exists:
        return doc.to_dict().get("count", 0)
    return 0
