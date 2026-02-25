from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from app.config import SGT
from app.services.supabase_client import is_verified_admin_by_tele_id, supabase


async def delete_event_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Soft-delete an event. Usage: /delete <event_id>"""
    if not context.args:
        await update.message.reply_text("Usage: /delete <event_id>")
        return

    event_id = context.args[0]
    user = update.effective_user

    if not is_verified_admin_by_tele_id(user.id):
        await update.message.reply_text("Only verified admins can delete events.")
        return

    # Soft delete
    result = (
        supabase.table("events")
        .update({"is_deleted": True, "deleted_at": datetime.now(SGT).isoformat()})
        .eq("event_id", event_id)
        .execute()
    )

    if result.data:
        await update.message.reply_text(f"✅ Event deleted.")
    else:
        await update.message.reply_text("Event not found.")
