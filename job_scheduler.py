from datetime import datetime, timedelta, timezone
from typing import Callable

from apscheduler.schedulers.background import BackgroundScheduler

from core.settings import Settings


class JobScheduler:
    def __init__(self, settings: Settings, links_task: Callable[[], None],
                 products_task: Callable[[], None]) -> None:
        self._settings = settings
        self._links_task = links_task
        self._products_task = products_task
        self._scheduler = BackgroundScheduler(timezone="UTC")

    def _add_interval_job(self, func: Callable[[], None], job_id: str,
                          first_run: datetime, **interval) -> None:
        self._scheduler.add_job(
            func,
            trigger="interval",
            next_run_time=first_run,
            id=job_id,
            replace_existing=True,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=3600,
            **interval,
        )

    def start(self) -> None:
        now = datetime.now(timezone.utc)
        s = self._settings
        self._add_interval_job(
            self._links_task, "refresh_product_links", now,
            days=s.links_refresh_days)
        self._add_interval_job(
            self._products_task, "refresh_products",
            now + timedelta(minutes=s.products_first_run_delay_minutes),
            hours=s.products_refresh_hours)
        self._scheduler.start()

    def shutdown(self) -> None:
        self._scheduler.shutdown(wait=True)
