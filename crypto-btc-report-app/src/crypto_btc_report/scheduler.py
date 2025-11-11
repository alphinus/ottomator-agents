from __future__ import annotations

from apscheduler.schedulers.background import BackgroundScheduler
from pytz import timezone

from .builder import ReportBuilder
from .config import get_settings


def start_scheduler() -> BackgroundScheduler:
    settings = get_settings()
    scheduler = BackgroundScheduler(timezone=timezone(settings.report_timezone))
    builder = ReportBuilder(settings)

    def job() -> None:
        payload = builder.build()
        builder.persist_json(payload)
        builder.render_html(payload)

    scheduler.add_job(
        job,
        trigger="cron",
        hour=settings.report_hour,
        minute=0,
        id="daily-report",
        replace_existing=True,
    )
    scheduler.start()
    return scheduler


if __name__ == "__main__":
    import time

    sched = start_scheduler()
    print("Scheduler running. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        sched.shutdown()
