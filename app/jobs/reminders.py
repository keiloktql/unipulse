import logging
from datetime import datetime, timezone

from telegram import Bot

from app.services.supabase_client import supabase

logger = logging.getLogger(__name__)


async def check_due_reminders(bot: Bot):
    """Runs every minute. Finds and sends reminders where remind_at <= now and sent = false."""
    now = datetime.now(timezone.utc).isoformat()
    result = (
        supabase.table("reminders")
        .select("*, accounts(telegram_id), events(text, date)")
        .eq("sent", False)
        .lte("remind_at", now)
        .limit(100)
        .execute()
    )

    for reminder in result.data:
        account = reminder.get("accounts")
        event = reminder.get("events")
        if not account or not event:
            continue

        telegram_id = account.get("telegram_id")
        if not telegram_id:
            continue

        event_text = event.get("text", "an event")
        event_date = event.get("date", "")

        try:
            await bot.send_message(
                chat_id=telegram_id,
                text=(
                    f"⏰ Reminder: {event_text}\n\n"
                    f"📅 {event_date}\n\n"
                    "This event is coming up soon!"
                ),
            )
            # Mark as sent
            (
                supabase.table("reminders")
                .update({"sent": True})
                .eq("reminder_id", reminder["reminder_id"])
                .execute()
            )
            logger.info("Sent reminder %s to telegram_id %s", reminder["reminder_id"], telegram_id)
        except Exception as e:
            logger.error("Failed to send reminder %s: %s", reminder["reminder_id"], e)
