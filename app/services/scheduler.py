import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import SGT

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def init_scheduler(bot):
    """Initialize scheduler with background jobs."""
    from app.jobs.digest import check_newsletter_due
    from app.jobs.newsletter import send_weekly_newsletter
    from app.jobs.reminders import check_due_reminders

    scheduler.add_job(
        check_due_reminders,
        "interval",
        minutes=1,
        args=[bot],
        id="check_reminders",
        replace_existing=True,
    )

    scheduler.add_job(
        check_newsletter_due,
        "interval",
        minutes=1,
        args=[bot],
        id="check_newsletter",
        replace_existing=True,
    )

    scheduler.add_job(
        send_weekly_newsletter,
        "cron",
        day_of_week="sun",
        hour=18,
        minute=0,
        timezone=SGT,
        args=[bot],
        id="weekly_newsletter",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Scheduler started with reminder and newsletter jobs")


def shutdown_scheduler():
    scheduler.shutdown(wait=False)
    logger.info("Scheduler shut down")
