import logging
from datetime import datetime, timedelta

from telegram import Bot

from app.config import SGT
from app.services.supabase_client import supabase

logger = logging.getLogger(__name__)


async def check_newsletter_due(bot: Bot):
    """Runs every minute. Find accounts whose newsletter_time matches the current minute and send newsletter."""
    now = datetime.now(SGT)
    current_time = now.strftime("%H:%M") + ":00"  # Match TIME format HH:MM:SS

    accounts_result = (
        supabase.table("accounts")
        .select("*")
        .eq("newsletter_time", current_time)
        .execute()
    )

    for account in accounts_result.data:
        if not account.get("tele_id"):
            continue
        # Check last_newsletter_sent to prevent double-sends
        last_sent = account.get("last_newsletter_sent")
        if last_sent:
            try:
                last_dt = datetime.fromisoformat(last_sent)
                if (now - last_dt).total_seconds() < 82800:  # 23 hours
                    continue
            except (ValueError, TypeError):
                pass
        await _send_newsletter_to_account(bot, account, now)


async def _send_newsletter_to_account(bot: Bot, account: dict, now: datetime):
    """Compile and send newsletter for a single account."""
    account_id = account["account_id"]
    tele_id = account["tele_id"]

    # Get subscribed category IDs
    subs = (
        supabase.table("account_categories")
        .select("fk_category_id")
        .eq("fk_account_id", account_id)
        .execute()
    )
    category_ids = [s["fk_category_id"] for s in subs.data]
    if not category_ids:
        return  # No subscriptions

    # Get upcoming events in subscribed categories (this week)
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_later = today + timedelta(days=7)

    events_result = (
        supabase.table("event_categories")
        .select("fk_event_id, events(event_id, text, date)")
        .in_("fk_category_id", category_ids)
        .execute()
    )

    # Filter to upcoming events within the week, deduplicate
    events = []
    seen_ids = set()
    for row in events_result.data:
        event = row.get("events")
        if not event or event["event_id"] in seen_ids:
            continue
        seen_ids.add(event["event_id"])
        if event.get("date"):
            try:
                event_dt = datetime.fromisoformat(event["date"])
                if today <= event_dt <= week_later:
                    events.append(event)
            except (ValueError, TypeError):
                continue

    if not events:
        return

    events.sort(key=lambda e: e.get("date", ""))

    # Format newsletter
    lines = ["Your Daily Pulse — Upcoming Events This Week\n"]
    for event in events[:10]:
        date_str = event.get("date", "TBD")
        text_preview = event.get("text", "")
        if len(text_preview) > 80:
            text_preview = text_preview[:80] + "..."
        lines.append(f"{date_str}\n{text_preview}\n")

    try:
        await bot.send_message(chat_id=tele_id, text="\n".join(lines))
        # Update last_newsletter_sent
        (
            supabase.table("accounts")
            .update({"last_newsletter_sent": now.isoformat()})
            .eq("account_id", account_id)
            .execute()
        )
        logger.info("Sent newsletter to tele_id %s", tele_id)
    except Exception as e:
        logger.error("Failed to send newsletter to %s: %s", tele_id, e)
