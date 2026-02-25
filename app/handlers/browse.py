from telegram import Update
from telegram.ext import ContextTypes

from app.services.event_card import send_event_card
from app.services.supabase_client import get_all_events, get_trending_events
from app.services.user_service import VERIFY_MSG, get_verified_account


async def list_events(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not get_verified_account(update.effective_user.id):
        await update.message.reply_text(VERIFY_MSG)
        return

    events = get_all_events()

    if not events:
        await update.message.reply_text("No upcoming events found. Check back later! 🔍")
        return

    await update.message.reply_text(f"📋 Showing {len(events)} events:")
    for event in events:
        await send_event_card(context.bot, update.effective_chat.id, event)


async def trending_events(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not get_verified_account(update.effective_user.id):
        await update.message.reply_text(VERIFY_MSG)
        return

    events = get_trending_events()

    if not events:
        await update.message.reply_text("No trending events yet! 🔥")
        return

    await update.message.reply_text("🔥 Trending events in UTown:")
    for event in events:
        await send_event_card(context.bot, update.effective_chat.id, event)
