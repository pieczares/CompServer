from datetime import datetime, timezone, timedelta

from apscheduler.schedulers.background import BackgroundScheduler

from tasks.productlinks import refresh_product_links
from tasks.produkty import refresh_products


def create_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone="UTC")

    # Linki: przy starcie i co 24 godziny.
    scheduler.add_job(
        refresh_product_links,
        trigger="interval",
        days=1,
        next_run_time=datetime.now(timezone.utc),
        id="refresh_product_links",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=3600,
    )

    # Dane produktów: co 12 godzin.
    scheduler.add_job(
        refresh_products,
        trigger="interval",
        hours=12,
        next_run_time=datetime.now(timezone.utc)+timedelta(minutes=3),
        id="refresh_products",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=3600,
    )

    return scheduler