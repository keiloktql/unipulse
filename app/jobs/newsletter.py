import logging

from telegram import Bot

from app.services.supabase_client import supabase

logger = logging.getLogger(__name__)


async def send_weekly_newsletter(bot: Bot):
    """Compile top events of the week and send to accounts with at least one subscription."""
    # Get top events by RSVP count
    result = supabase.table("rsvps").select("fk_event_id, events(event_id, title, text, date)").execute()

    event_counts = {}
    event_data = {}
    for row in result.data:
        eid = row["fk_event_id"]
        event = row.get("events")
        if not event:
            continue
        event_counts[eid] = event_counts.get(eid, 0) + 1
        if eid not in event_data:
            event_data[eid] = event

    sorted_events = sorted(event_counts, key=event_counts.get, reverse=True)[:10]
    top_events = [event_data[eid] for eid in sorted_events if eid in event_data]

    if not top_events:
        logger.info("No events for weekly newsletter")
        return

    # Format newsletter
    lines = ["UniPulse Weekly Roundup\n", "Here are this week's top events:\n"]
    for i, event in enumerate(top_events, 1):
        title = event.get("title") or event.get("text", "")[:60]
        date = event.get("date", "TBD")
        count = event_counts.get(event["event_id"], 0)
        lines.append(f"{i}. {title}\n   {date} | {count} RSVPs\n")

    newsletter_text = "\n".join(lines)

    # Get accounts that have at least one category subscription
    subs = (
        supabase.table("account_categories")
        .select("fk_account_id")
        .execute()
    )
    subscribed_account_ids = list({s["fk_account_id"] for s in subs.data})

    if not subscribed_account_ids:
        logger.info("No subscribed accounts for weekly newsletter")
        return

    # Get tele_ids for those accounts
    accounts = (
        supabase.table("accounts")
        .select("tele_id")
        .in_("account_id", subscribed_account_ids)
        .execute()
    )

    sent_count = 0
    for account in accounts.data:
        tele_id = account.get("tele_id")
        if not tele_id:
            continue
        try:
            await bot.send_message(chat_id=tele_id, text=newsletter_text)
            sent_count += 1
        except Exception as e:
            logger.error("Failed to send weekly newsletter to %s: %s", tele_id, e)

    logger.info("Weekly newsletter sent to %d accounts", sent_count)
