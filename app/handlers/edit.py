import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from app.services.event_card import send_event_card
from app.services.supabase_client import get_event, update_event
from app.services.user_service import VERIFY_MSG, get_verified_account

logger = logging.getLogger(__name__)

# Conversation states
CHOOSE_FIELD = 0
ENTER_VALUE = 1

# Maps field keys to display names and DB column names
FIELDS = {
    "title": ("Title", "title"),
    "date": ("Date", "date"),
    "location": ("Location", "location"),
    "description": ("Description", "description"),
}


def _field_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✏️ Title", callback_data="edit_field:title"),
            InlineKeyboardButton("📅 Date", callback_data="edit_field:date"),
        ],
        [
            InlineKeyboardButton("📍 Location", callback_data="edit_field:location"),
            InlineKeyboardButton("📝 Description", callback_data="edit_field:description"),
        ],
        [InlineKeyboardButton("✅ Done", callback_data="edit_field:done")],
    ])


def _current_values_text(event: dict) -> str:
    lines = ["Current values:"]
    lines.append(f"  Title: {event.get('title') or '—'}")
    lines.append(f"  Date: {event.get('date') or '—'}")
    lines.append(f"  Location: {event.get('location') or '—'}")
    desc = event.get("description") or "—"
    if len(desc) > 80:
        desc = desc[:77] + "..."
    lines.append(f"  Description: {desc}")
    lines.append("\nWhich field do you want to edit?")
    return "\n".join(lines)


async def edit_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point: /edit <event_id>"""
    account = get_verified_account(update.effective_user.id)
    if not account:
        await update.message.reply_text(VERIFY_MSG)
        return ConversationHandler.END

    if not context.args:
        await update.message.reply_text("Usage: /edit <event_id>")
        return ConversationHandler.END

    event_id = context.args[0]
    event = get_event(event_id)
    if not event or event.get("is_deleted"):
        await update.message.reply_text("Event not found.")
        return ConversationHandler.END

    if event.get("fk_account_id") != account["account_id"]:
        await update.message.reply_text("You can only edit your own events.")
        return ConversationHandler.END

    context.user_data["edit_event_id"] = event_id
    await update.message.reply_text(
        _current_values_text(event),
        reply_markup=_field_keyboard(),
    )
    return CHOOSE_FIELD


async def start_edit_from_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    event_id: str,
    account: dict,
) -> int:
    """Entry point triggered from the /manage moderation panel."""
    event = get_event(event_id)
    if not event or event.get("is_deleted"):
        await update.callback_query.edit_message_text("Event not found.")
        return ConversationHandler.END

    if event.get("fk_account_id") != account["account_id"]:
        await update.callback_query.edit_message_text("You can only edit your own events.")
        return ConversationHandler.END

    context.user_data["edit_event_id"] = event_id
    await update.callback_query.edit_message_text(
        _current_values_text(event),
        reply_markup=_field_keyboard(),
    )
    return CHOOSE_FIELD


async def choose_field(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle field selection button press."""
    query = update.callback_query
    await query.answer()

    field_key = query.data.split(":", 1)[1]

    if field_key == "done":
        event_id = context.user_data.get("edit_event_id")
        context.user_data.pop("edit_event_id", None)
        context.user_data.pop("edit_field", None)
        await query.edit_message_text("Edits saved.")
        if event_id:
            event = get_event(event_id)
            if event:
                await send_event_card(query.get_bot(), query.message.chat_id, event)
        return ConversationHandler.END

    if field_key not in FIELDS:
        return CHOOSE_FIELD

    display_name, _ = FIELDS[field_key]
    context.user_data["edit_field"] = field_key

    prompts = {
        "title": "Enter the new title:",
        "date": "Enter the new date (ISO format, e.g. 2026-03-15T18:00:00+08:00):",
        "location": "Enter the new location:",
        "description": "Enter the new description:",
    }
    await query.edit_message_text(prompts[field_key])
    return ENTER_VALUE


async def enter_value(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive the new value, save it, return to field selection."""
    field_key = context.user_data.get("edit_field")
    event_id = context.user_data.get("edit_event_id")

    if not field_key or not event_id:
        await update.message.reply_text("Something went wrong. Please use /edit <event_id> again.")
        return ConversationHandler.END

    _, db_column = FIELDS[field_key]
    new_value = update.message.text.strip()

    try:
        update_event(event_id, **{db_column: new_value})
    except Exception as e:
        logger.error("Failed to update event %s field %s: %s", event_id, db_column, e)
        await update.message.reply_text("Failed to save. Please try again.")
        return ENTER_VALUE

    event = get_event(event_id)
    if not event:
        await update.message.reply_text("Event updated but could not reload it.")
        return ConversationHandler.END

    await update.message.reply_text(
        _current_values_text(event),
        reply_markup=_field_keyboard(),
    )
    return CHOOSE_FIELD


async def cancel_edit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("edit_event_id", None)
    context.user_data.pop("edit_field", None)
    await update.message.reply_text("Edit cancelled.")
    return ConversationHandler.END
