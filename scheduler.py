from datetime import datetime, timedelta, timezone
from typing import Callable

from apscheduler.schedulers.background import BackgroundScheduler


class JobScheduler:
    def __init__(self, links_task: Callable[[], None],
                 products_task: Callable[[], None]) -> None:
        self._links_task = links_task
        self._products_task = products_task
        self._scheduler = BackgroundScheduler(timezone="UTC")

    def _add(self, func, job_id: str, first_run: datetime, **interval) -> None:
        self._scheduler.add_job(
            func, trigger="interval", next_run_time=first_run, id=job_id,
            replace_existing=True, max_instances=1, coalesce=True,
            misfire_grace_time=3600, **interval)

    def start(self) -> None:
        now = datetime.now(timezone.utc)
        self._add(self._links_task, "refresh_product_links", now, days=1)
        self._add(self._products_task, "refresh_products",
                  now + timedelta(minutes=3), hours=12)
        self._scheduler.start()

    def shutdown(self) -> None:
        self._scheduler.shutdown(wait=True)
