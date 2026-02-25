import logging
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from app.config import SGT
from app.services.supabase_client import get_events_by_account, supabase
from app.services.user_service import VERIFY_MSG, get_verified_account

logger = logging.getLogger(__name__)


def _event_summary(event: dict) -> str:
    title = event.get("title") or event.get("text", "")[:40] + "..."
    date_str = ""
    if event.get("date"):
        try:
            dt = datetime.fromisoformat(event["date"])
            date_str = dt.strftime("%d %b %Y")
        except (ValueError, TypeError):
            date_str = event["date"][:10]
    deleted = " [deleted]" if event.get("is_deleted") else ""
    return f"{title} — {date_str}{deleted}" if date_str else f"{title}{deleted}"


async def manage_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List the user's own events with Edit and Delete inline buttons."""
    account = get_verified_account(update.effective_user.id)
    if not account:
        await update.message.reply_text(VERIFY_MSG)
        return

    events = get_events_by_account(account["account_id"], limit=10)
    if not events:
        await update.message.reply_text(
            "You haven't posted any events yet.\n"
            "Post one in a group chat with #unipulse!"
        )
        return

    await update.message.reply_text(
        f"Your last {len(events)} event(s). Tap an action to manage:"
    )

    for event in events:
        event_id = event["event_id"]
        summary = _event_summary(event)
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✏️ Edit", callback_data=f"mod:edit:{event_id}"),
                InlineKeyboardButton("🗑 Delete", callback_data=f"mod:delete:{event_id}"),
            ]
        ])
        await update.message.reply_text(summary, reply_markup=keyboard)


async def handle_moderation_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle mod:edit:<id>, mod:delete:<id>, mod:confirm:<id>, mod:cancel callbacks."""
    query = update.callback_query
    await query.answer()

    parts = query.data.split(":", 2)
    if len(parts) < 3:
        return

    _, action, event_id = parts

    account = get_verified_account(query.from_user.id)
    if not account:
        await query.answer(VERIFY_MSG, show_alert=True)
        return

    if action == "edit":
        # Trigger the edit flow as if the user ran /edit <event_id>
        context.args = [event_id]
        from app.handlers.edit import start_edit_from_callback
        await start_edit_from_callback(update, context, event_id, account)
        return

    if action == "delete":
        # Show confirmation
        result = supabase.table("events").select("title, text").eq("event_id", event_id).maybe_single().execute()
        event = result.data
        if not event:
            await query.edit_message_text("Event not found.")
            return
        title = event.get("title") or (event.get("text", "")[:40] + "...")
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Yes, delete", callback_data=f"mod:confirm:{event_id}"),
                InlineKeyboardButton("Cancel", callback_data=f"mod:cancel:{event_id}"),
            ]
        ])
        await query.edit_message_text(
            f"Delete \"{title}\"?\nThis cannot be undone.",
            reply_markup=keyboard,
        )
        return

    if action == "confirm":
        # Verify ownership before deleting
        result = supabase.table("events").select("fk_account_id").eq("event_id", event_id).maybe_single().execute()
        event = result.data
        if not event or event.get("fk_account_id") != account["account_id"]:
            await query.edit_message_text("You can only delete your own events.")
            return
        supabase.table("events").update({
            "is_deleted": True,
            "deleted_at": datetime.now(SGT).isoformat(),
        }).eq("event_id", event_id).execute()
        await query.edit_message_text("Event deleted.")
        logger.info("Event %s soft-deleted by account %s", event_id, account["account_id"])
        return

    if action == "cancel":
        await query.edit_message_text("Deletion cancelled.")
        return
