import re

from telegram import Update
from telegram.ext import ContextTypes

from app.services.event_card import send_event_card
from app.services.supabase_client import search_events
from app.services.user_service import VERIFY_MSG, get_verified_account


async def find_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Search events by category tag or keyword."""
    if not get_verified_account(update.effective_user.id):
        await update.message.reply_text(VERIFY_MSG)
        return

    if not context.args:
        await update.message.reply_text(
            "Usage:\n"
            "/find #sports — search by category\n"
            "/find pizza — search event text"
        )
        return

    query_text = " ".join(context.args)

    # Check if searching by category hashtag
    category_match = re.match(r"^#(\w+)$", query_text)
    if category_match:
        events = search_events(category=category_match.group(1))
    else:
        events = search_events(query=query_text)

    if not events:
        await update.message.reply_text("No matching events found.")
        return

    await update.message.reply_text(f"Found {len(events)} event(s):")
    for event in events:
        await send_event_card(context.bot, update.effective_chat.id, event)
