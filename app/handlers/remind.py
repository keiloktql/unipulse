from datetime import datetime, timedelta

from telegram import Update
from telegram.ext import ContextTypes

from app.config import SGT
from app.services.supabase_client import supabase, get_event
from app.services.user_service import VERIFY_MSG, get_verified_account


async def handle_remind_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback_data like 'remind:<event_id>'."""
    query = update.callback_query
    await query.answer()

    parts = query.data.split(":")
    if len(parts) != 2:
        return
    _, event_id = parts

    account = get_verified_account(query.from_user.id)
    if not account:
        await query.answer(VERIFY_MSG, show_alert=True)
        return

    event = get_event(event_id)
    if not event or not event.get("date"):
        await query.answer("This event has no date set — can't create reminder.", show_alert=True)
        return

    event_dt = datetime.fromisoformat(event["date"])
    created = create_reminders_for_event(account["account_id"], event_id, event_dt)

    if created:
        await query.answer("Reminders set for 24h and 1h before the event!", show_alert=True)
    else:
        await query.answer("Reminders already set for this event.", show_alert=True)


def create_reminders_for_event(account_id: str, event_id: str, event_dt: datetime) -> bool:
    """Create 24h and 1h reminders for an event. Returns True if any were created."""
    now = datetime.now(SGT)
    created_any = False

    for delta in [timedelta(hours=24), timedelta(hours=1)]:
        remind_at = event_dt - delta
        if remind_at <= now:
            continue

        # Check if reminder already exists
        existing = (
            supabase.table("reminders")
            .select("reminder_id")
            .eq("fk_account_id", account_id)
            .eq("fk_event_id", event_id)
            .eq("remind_at", remind_at.isoformat())
            .maybe_single()
            .execute()
        )
        if not existing.data:
            supabase.table("reminders").insert({
                "fk_account_id": account_id,
                "fk_event_id": event_id,
                "remind_at": remind_at.isoformat(),
            }).execute()
            created_any = True

    return created_any
