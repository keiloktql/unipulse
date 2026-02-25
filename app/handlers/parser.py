import hashlib
import logging
import re

from telegram import Update
from telegram.ext import ContextTypes

from app.middleware.rate_limit import check_rate_limit
from app.services.gemini import parse_event
from app.services.supabase_client import (
    get_account_by_telegram_id,
    get_event_by_hash,
    get_or_create_category,
    is_verified_admin_by_telegram_id,
    link_event_category,
    save_event,
    save_event_image,
    update_event_refs,
    upload_image,
)
from app.services.event_card import send_event_card
from app.services.user_service import get_all_categories

logger = logging.getLogger(__name__)


def _compute_event_hash(text: str, date: str | None) -> str:
    """Hash event text + date to detect duplicates."""
    content = f"{text.strip().lower()}|{date or ''}"
    return hashlib.sha256(content.encode()).hexdigest()[:32]


def _extract_category(text: str) -> str:
    """Extract category from subtags like #sports, #ai, etc."""
    known_names = {c["name"] for c in get_all_categories()}
    tags = re.findall(r"#(\w+)", text.lower())
    for tag in tags:
        if tag != "unipulse" and tag in known_names:
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
    if not user:
        return

    # Check if poster is a verified user
    if not is_verified_admin_by_telegram_id(user.id):
        await message.reply_text(
            "⚠️ You need to verify as an admin first. DM me with /verify"
        )
        return

    # Fetch account early so we can pass account_id to rate limiter
    account = get_account_by_telegram_id(user.id)
    account_id = account["account_id"] if account else None

    # Rate limiting (DB-backed, persists across restarts)
    if account_id and not check_rate_limit(account_id):
        await message.reply_text("⚠️ You've reached the posting limit (5/hour). Please wait before posting more events.")
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

    # Deduplication check
    text_hash = _compute_event_hash(message.text, parsed.get("date"))
    if get_event_by_hash(text_hash):
        await message.reply_text("This event has already been posted!")
        return

    # Save event to database
    event = save_event(
        text=message.text,
        date=parsed.get("date"),
        account_id=account_id,
        title=parsed.get("title"),
        location=parsed.get("location"),
        description=parsed.get("description"),
        end_date=parsed.get("end_date"),
        text_hash=text_hash,
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
