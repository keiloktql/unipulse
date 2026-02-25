import logging
import re

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from app.services.supabase_client import supabase

logger = logging.getLogger(__name__)

EMAIL, OTP = range(2)

NUS_EMAIL_PATTERN = re.compile(r"^[^@]+@(u\.nus\.edu|nus\.edu\.sg)$", re.IGNORECASE)


async def start_verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Only allow in DMs
    if update.effective_chat.type != "private":
        await update.message.reply_text("Please DM me to verify. Send /verify in our private chat.")
        return ConversationHandler.END

    await update.message.reply_text(
        "Let's verify your NUS identity! 🎓\n\n"
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

    context.user_data["verify_email"] = email

    # Use Supabase Auth to send OTP email
    try:
        supabase.auth.sign_in_with_otp({"email": email})
        logger.info("OTP sent to %s for user @%s", email, update.effective_user.username)
    except Exception as e:
        logger.error("Failed to send OTP: %s", e)
        await update.message.reply_text(
            "Failed to send verification email. Please try again later.\n"
            "Use /verify to restart."
        )
        return ConversationHandler.END

    await update.message.reply_text(
        f"📧 A verification code has been sent to {email}\n\n"
        "Please check your inbox (and spam folder) and enter the 6-digit code:"
    )
    return OTP


async def receive_otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip()
    email = context.user_data.get("verify_email")

    if not email:
        await update.message.reply_text("Something went wrong. Please restart with /verify")
        return ConversationHandler.END

    if not code.isdigit() or len(code) != 6:
        await update.message.reply_text("Please enter a valid 6-digit code:")
        return OTP

    # Verify OTP with Supabase Auth
    try:
        auth_response = supabase.auth.verify_otp({
            "email": email,
            "token": code,
            "type": "email",
        })
    except Exception as e:
        logger.error("OTP verification failed: %s", e)
        await update.message.reply_text(
            "Invalid or expired code. Please try again or use /verify to restart."
        )
        return OTP

    if not auth_response.user:
        await update.message.reply_text(
            "Verification failed. Please try again with /verify"
        )
        return ConversationHandler.END

    # Insert into accounts table
    user = update.effective_user
    tele_handle = user.username

    if not tele_handle:
        await update.message.reply_text(
            "Please set a Telegram username first, then try /verify again."
        )
        return ConversationHandler.END

    try:
        # Upsert account: create if new, update if re-verifying
        supabase.table("accounts").upsert({
            "account_id": str(auth_response.user.id),
            "telegram_id": user.id,
            "tele_handle": tele_handle,
            "is_verified": True,
            "auth_user_id": str(auth_response.user.id),
        }, on_conflict="account_id").execute()
        logger.info("User verified: @%s (%s)", tele_handle, email)
    except Exception as e:
        logger.error("Failed to save account: %s", e)
        await update.message.reply_text("Verification succeeded but failed to save account. Please contact support.")
        return ConversationHandler.END

    await update.message.reply_text(
        "✅ You're verified!\n\n"
        "You now have full access to UniPulse.\n"
        "Use /events to browse, /subscribe to follow categories,\n"
        "and post events in group chats with #unipulse."
    )

    # Clean up
    context.user_data.pop("verify_email", None)
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Verification cancelled. Use /verify to try again.")
    context.user_data.pop("verify_email", None)
    return ConversationHandler.END
