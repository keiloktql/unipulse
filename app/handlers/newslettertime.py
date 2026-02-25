import re

from telegram import Update
from telegram.ext import ContextTypes

from app.services.user_service import VERIFY_MSG, get_verified_account, update_newsletter_time


async def newslettertime_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set preferred newsletter time. Usage: /newslettertime HH:MM"""
    account = get_verified_account(update.effective_user.id)
    if not account:
        await update.message.reply_text(VERIFY_MSG)
        return

    if not context.args:
        current = account.get("newsletter_time", "09:00:00")
        await update.message.reply_text(
            f"Your current newsletter time: {current[:5]}\n\n"
            "Usage: /newslettertime HH:MM (24-hour format)\n"
            "Example: /newslettertime 08:30"
        )
        return

    time_str = context.args[0]
    if not re.match(r"^\d{2}:\d{2}$", time_str):
        await update.message.reply_text("Please use HH:MM format (e.g., 08:30)")
        return

    hours, minutes = int(time_str[:2]), int(time_str[3:5])
    if hours > 23 or minutes > 59:
        await update.message.reply_text("Invalid time. Use 00:00 to 23:59.")
        return

    update_newsletter_time(account["account_id"], time_str + ":00")
    await update.message.reply_text(f"Newsletter time updated to {time_str} (GMT+08)")
