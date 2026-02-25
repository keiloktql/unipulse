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

    # Parse callback data: "rsvp:going:event_uuid" or "rsvp:interested:event_uuid"
    parts = query.data.split(":")
    if len(parts) != 3:
        return

    _, status, event_id = parts

    account = get_verified_account(query.from_user.id)
    if not account:
        await query.answer(VERIFY_MSG, show_alert=True)
        return

    # Atomic upsert via Supabase RPC
    counts = upsert_rsvp(event_id, account["account_id"], status)
    logger.info("RSVP updated: event=%s account=%s status=%s counts=%s", event_id, account["account_id"], status, counts)

    # Re-fetch event for full data
    event = get_event(event_id)
    if not event:
        return

    # Auto-create reminders when user RSVPs "going"
    if status == "going" and event.get("date"):
        try:
            event_dt = datetime.fromisoformat(event["date"])
            create_reminders_for_event(account["account_id"], event_id, event_dt)
        except (ValueError, TypeError):
            pass

    # Rebuild keyboard with updated counts from RPC
    new_keyboard = build_event_keyboard(
        event,
        going=counts["new_going_count"],
        interested=counts["new_interested_count"],
    )

    # Edit the message to update button labels
    try:
        await query.edit_message_reply_markup(reply_markup=new_keyboard)
    except Exception:
        # Message not modified (same counts) — Telegram throws an error, ignore
        pass
