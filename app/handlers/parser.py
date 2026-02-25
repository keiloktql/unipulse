import logging
import re

from telegram import Update
from telegram.ext import ContextTypes

from app.services.gemini import parse_event
from app.services.supabase_client import (
    get_account_by_handle,
    get_or_create_category,
    is_verified_admin,
    link_event_category,
    save_event,
    save_event_image,
    update_event_refs,
    upload_image,
)
from app.services.event_card import send_event_card

logger = logging.getLogger(__name__)

# Common category subtags
CATEGORY_TAGS = {
    "sports", "ai", "tech", "freefood", "culture", "social",
    "academic", "arts", "music", "hackathon", "wellness",
}


def _extract_category(text: str) -> str:
    """Extract category from subtags like #sports, #ai, etc."""
    tags = re.findall(r"#(\w+)", text.lower())
    for tag in tags:
        if tag != "unipulse" and tag in CATEGORY_TAGS:
            return tag
    for tag in tags:
        if tag != "unipulse":
            return tag
    return "general"


async def handle_event_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if not message or not message.text:
        return

    user = message.from_user
    if not user or not user.username:
        await message.reply_text("Please set a Telegram username to post events.")
        return

    # Check if poster is a verified admin
    if not is_verified_admin(user.username):
        await message.reply_text(
            "⚠️ You need to verify as an admin first. DM me with /verify"
        )
        return

    logger.info("Processing #unipulse message from @%s in chat %s", user.username, update.effective_chat.id)

    # Extract category from subtags
    category_name = _extract_category(message.text)

    # Download image if present
    image_bytes = None
    if message.photo:
        photo = message.photo[-1]  # Highest resolution
        file = await photo.get_file()
        image_bytes = bytes(await file.download_as_bytearray())

    # Parse event with Gemini (text first, image fallback) to extract date
    parsed = parse_event(message.text, image_bytes)
    logger.info("Parsed event: %s", parsed)

    # Get admin account
    account = get_account_by_handle(user.username)
    account_id = account["account_id"] if account else None

    # Save event to database
    event = save_event(
        text=message.text,
        date=parsed.get("date"),
        account_id=account_id,
    )

    event_id = event["event_id"]

    # Upload image to storage and save reference
    if image_bytes:
        image_url = upload_image(image_bytes)
        ei = save_event_image(event_id, image_url)
        update_event_refs(event_id, ei_id=ei["ei_id"])
        event["image_url"] = image_url

    # Create/link category
    category = get_or_create_category(category_name)
    ec = link_event_category(event_id, category["category_id"])
    update_event_refs(event_id, ec_id=ec["ec_id"])

    # Send event card back to the group
    await send_event_card(context.bot, update.effective_chat.id, event)
