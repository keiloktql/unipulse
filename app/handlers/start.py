from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from app.services.event_card import send_event_card
from app.services.supabase_client import get_event
from app.services.user_service import get_verified_account


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    account = get_verified_account(update.effective_user.id)

    # Handle deep link: /start event_<event_id>
    if context.args and context.args[0].startswith("event_"):
        if not account:
            await update.message.reply_text(
                "🔒 Verify your NUS identity to view events.\nDM me with /verify to get started."
            )
            return
        event_id = context.args[0][6:]  # Strip "event_" prefix
        event = get_event(event_id)
        if event and not event.get("is_deleted"):
            await send_event_card(context.bot, update.effective_chat.id, event)
            return

    if account:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Choose categories to follow", callback_data="sub:start")]
        ])
        await update.message.reply_text(
            "Welcome back to UniPulse! 🎉\n\n"
            "Use /events to browse upcoming events\n"
            "Use /trending to see what's hot\n"
            "Use /subscribe to manage your category subscriptions\n"
            "Use /find to search events",
            reply_markup=keyboard,
        )
    else:
        await update.message.reply_text(
            "Welcome to UniPulse! 🎉\n"
            "The heartbeat of NUS UTown — never miss an event again.\n\n"
            "To get started, verify your NUS identity:\n"
            "Send /verify to begin verification."
        )
