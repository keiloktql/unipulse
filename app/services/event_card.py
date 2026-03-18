from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

from app.services.calendar import build_gcal_url


def build_event_text(event: dict) -> str:
    lines = []
    if event.get("title"):
        lines.append(f"*{_escape_md(event['title'])}*")
    if event.get("text"):
        lines.append(_escape_md(event["text"]))
    if event.get("date"):
        lines.append(f"\n📅 {_escape_md(str(event['date']))}")
    if event.get("location"):
        lines.append(f"📍 {_escape_md(event['location'])}")
    return "\n".join(lines)


def build_event_keyboard(event: dict, going: int = 0) -> InlineKeyboardMarkup:
    event_id = event["event_id"]

    rows = [
        [
            InlineKeyboardButton(
                f"Going ({going})",
                callback_data=f"rsvp:going:{event_id}",
            ),
        ],
        [
            InlineKeyboardButton(
                "⏰ Remind Me",
                callback_data=f"remind:{event_id}",
            ),
        ],
    ]

    # Add GCal button if event has a date
    gcal_url = build_gcal_url(event)
    if gcal_url:
        rows.append([
            InlineKeyboardButton("📅 Add to Calendar", url=gcal_url),
        ])

    return InlineKeyboardMarkup(rows)


async def send_event_card(bot: Bot, chat_id: int, event: dict):
    from app.services.supabase_client import get_rsvp_counts

    text = build_event_text(event)
    count = get_rsvp_counts(event["event_id"])
    keyboard = build_event_keyboard(event, going=count)

    image_url = event.get("image_url")
    if not image_url:
        images = event.get("event_images")
        if images and isinstance(images, list) and len(images) > 0:
            image_url = images[0].get("url")

    if image_url:
        await bot.send_photo(
            chat_id=chat_id,
            photo=image_url,
            caption=text,
            parse_mode="MarkdownV2",
            reply_markup=keyboard,
        )
    else:
        await bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="MarkdownV2",
            reply_markup=keyboard,
        )


def _escape_md(text: str) -> str:
    """Escape special Markdown characters."""
    for char in ("_", "*", "[", "]", "(", ")", "~", "`", ">", "#", "+", "-", "=", "|", "{", "}", ".", "!"):
        text = text.replace(char, f"\\{char}")
    return text
