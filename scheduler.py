"""
Railway/Render'da worker process sifatida doimiy ishlaydi va har
CHECK_INTERVAL_HOURS soatda bir marta app.main.run_once() ni chaqiradi.
"""
import logging

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
    run_once()  # ishga tushishda darhol bir marta tekshiradi

    sched = BlockingScheduler(timezone="Asia/Tashkent")
    sched.add_job(run_once, "interval", hours=CHECK_INTERVAL_HOURS)
    sched.start()
