"""
Railway/Render'da worker process sifatida doimiy ishlaydi va har
CHECK_INTERVAL_HOURS soatda bir marta app.main.run_once() ni chaqiradi.
"""
import json
import logging
import os

# Firebase kaliti Railway'da JSON matni sifatida saqlanadi (FIREBASE_SERVICE_ACCOUNT_JSON).
# Uni vaqtinchalik faylga yozib, dasturga fayl yo'li sifatida beramiz.
if os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON") and not os.environ.get("FIREBASE_SERVICE_ACCOUNT_PATH"):
    _tmp_path = "/tmp/firebase-service-account.json"
    with open(_tmp_path, "w") as _f:
        _f.write(os.environ["FIREBASE_SERVICE_ACCOUNT_JSON"])
    os.environ["FIREBASE_SERVICE_ACCOUNT_PATH"] = _tmp_path

from apscheduler.schedulers.blocking import BlockingScheduler

from app.main import run_once
from app.sources import CHECK_INTERVAL_HOURS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("scheduler")

if __name__ == "__main__":
    logger.info("Scheduler ishga tushdi. Har %d soatda tekshiradi.", CHECK_INTERVAL_HOURS)
    run_once()

    sched = BlockingScheduler(timezone="Asia/Tashkent")
    sched.add_job(run_once, "interval", hours=CHECK_INTERVAL_HOURS)
    sched.start()
