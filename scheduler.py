from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler

from tasks.productlinks import refresh_product_links


def create_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone="UTC")

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

    return scheduler