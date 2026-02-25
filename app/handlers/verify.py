import logging
import re

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from app.config import settings
from app.services.supabase_client import send_verification_email

logger = logging.getLogger(__name__)

EMAIL = 0

NUS_EMAIL_PATTERN = re.compile(r"^[^@]+@(u\.nus\.edu|nus\.edu\.sg)$", re.IGNORECASE)

# Pending verifications: email -> {telegram_id, tele_handle}
pending_verifications: dict[str, dict] = {}


async def start_verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        await update.message.reply_text("Please DM me to verify. Send /verify in our private chat.")
        return ConversationHandler.END

    if not update.effective_user.username:
        await update.message.reply_text(
            "Please set a Telegram username first, then try /verify again."
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "Let's verify your NUS identity!\n\n"
        "Please enter your NUS email address (e.g. e0123456@u.nus.edu):"
    )
    return EMAIL


async def receive_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text.strip().lower()

    if not NUS_EMAIL_PATTERN.match(email):
        await update.message.reply_text(
            "That doesn't look like a valid NUS email.\n"
            "Please enter an email ending in @u.nus.edu or @nus.edu.sg:"
        )
        return EMAIL

    user = update.effective_user

    # Store pending verification
    pending_verifications[email] = {
        "telegram_id": user.id,
        "tele_handle": user.username,
    }

    # Send magic link email via Supabase Auth
    try:
        send_verification_email(email, f"{settings.WEBHOOK_URL}/auth/callback")
        logger.info("Confirmation email sent to %s for user @%s", email, user.username)
    except Exception as e:
        logger.error("Failed to send confirmation email: %s", e)
        pending_verifications.pop(email, None)
        await update.message.reply_text(
            "Failed to send verification email. Please try again later.\n"
            "Use /verify to restart."
        )
        return ConversationHandler.END

    await update.message.reply_text(
        f"A confirmation email has been sent to {email}\n\n"
        "Please check your inbox (and spam folder) and click the link to verify."
    )
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Verification cancelled. Use /verify to try again.")
    return ConversationHandler.END
