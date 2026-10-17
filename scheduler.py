from apscheduler.schedulers.background import BackgroundScheduler

from tasks.measurements import collect_measurement


def create_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone="UTC")

    scheduler.add_job(
        collect_measurement,
        trigger="interval",
        seconds=30,
        id="collect_measurement",
        max_instances=1,
        coalesce=True,
    )

    return scheduler