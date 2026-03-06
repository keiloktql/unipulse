import logging
import re

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from app.services.supabase_client import (
    send_verification_email,
    supabase,
    verify_email_otp,
)

logger = logging.getLogger(__name__)

EMAIL = 0
OTP_CODE = 1

NUS_EMAIL_PATTERN = re.compile(r"^[^@]+@(u\.nus\.edu|nus\.edu\.sg)$", re.IGNORECASE)


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

    try:
        send_verification_email(
            email,
            tele_id=user.id,
            tele_handle=user.username,
        )
        logger.info("OTP email sent to %s for user @%s", email, user.username)
    except Exception as e:
        logger.exception("Failed to send OTP email: %s", e)
        await update.message.reply_text(
            "Failed to send verification email. Please try again later.\n"
            "Use /verify to restart."
        )
        return ConversationHandler.END

    context.user_data["verify_email"] = email
    await update.message.reply_text(
        f"A verification code has been sent to {email}\n\n"
        "Please check your inbox (and spam folder) and enter the code here:"
    )
    return OTP_CODE


async def receive_otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    otp_code = update.message.text.strip()
    email = context.user_data.get("verify_email")

    if not email:
        await update.message.reply_text("Session expired. Please use /verify to start again.")
        return ConversationHandler.END

    if not re.match(r"^\d{6,8}$", otp_code):
        await update.message.reply_text("Please enter the code from your email:")
        return OTP_CODE

    try:
        result = verify_email_otp(email, otp_code)
    except Exception as e:
        logger.exception("OTP verification failed for %s: %s", email, e)
        await update.message.reply_text(
            "Invalid or expired code. Please try /verify again."
        )
        return ConversationHandler.END

    auth_user = result.user if result else None
    if not auth_user:
        await update.message.reply_text("Verification failed. Please try /verify again.")
        return ConversationHandler.END

    meta = auth_user.user_metadata or {}
    tele_id = meta.get("tele_id")
    tele_handle = meta.get("tele_handle")
    account_id = str(auth_user.id)

    try:
        supabase.table("accounts").upsert({
            "account_id": account_id,
            "tele_id": tele_id,
            "tele_handle": tele_handle,
        }, on_conflict="account_id").execute()
        logger.info("User verified: @%s (%s)", tele_handle, email)
    except Exception as e:
        logger.error("Failed to save account: %s", e)
        await update.message.reply_text("Verification succeeded but failed to save. Please contact support.")
        return ConversationHandler.END

    try:
        from app.handlers.onboarding import send_onboarding
        await send_onboarding(update.effective_chat.get_bot(), tele_id, account_id)
    except Exception as e:
        logger.error("Failed to send onboarding to %s: %s", tele_id, e)

    await update.message.reply_text("You're verified! Welcome to UniPulse.")
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Verification cancelled. Use /verify to try again.")
    return ConversationHandler.END
