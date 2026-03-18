import logging
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from app.handlers.remind import create_reminders_for_event
from app.services.event_card import build_event_keyboard
from app.services.supabase_client import get_event, upsert_rsvp
from app.services.user_service import VERIFY_MSG, get_verified_account

logger = logging.getLogger(__name__)


async def handle_rsvp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Parse callback data: "rsvp:going:<event_uuid>" or legacy "rsvp:<event_uuid>"
    parts = query.data.split(":")
    if len(parts) == 2:
        event_id = parts[1]
    elif len(parts) == 3:
        event_id = parts[2]
    else:
        return

    account = get_verified_account(query.from_user.id)
    if not account:
        await query.answer(VERIFY_MSG, show_alert=True)
        return

    # Atomic RSVP toggle via Supabase RPC — returns updated count
    new_count = upsert_rsvp(event_id, account["account_id"])
    logger.info("RSVP toggled: event=%s account=%s new_count=%s", event_id, account["account_id"], new_count)

    # Re-fetch event for full data
    event = get_event(event_id)
    if not event:
        return

    # Auto-create reminders on RSVP (create_reminders_for_event guards against duplicates)
    if event.get("date"):
        try:
            event_dt = datetime.fromisoformat(event["date"])
            create_reminders_for_event(account["account_id"], event_id, event_dt)
        except (ValueError, TypeError):
            pass

    # Rebuild keyboard with updated count
    new_keyboard = build_event_keyboard(event, going=new_count)

    try:
        await query.edit_message_reply_markup(reply_markup=new_keyboard)
    except Exception:
        pass
