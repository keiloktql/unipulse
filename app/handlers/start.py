from telegram import Update
from telegram.ext import ContextTypes


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to UniPulse! 🎉\n"
        "The heartbeat of NUS UTown — never miss an event again.\n\n"
        "Use /events to browse upcoming events\n"
        "Use /trending to see what's hot"
    )
