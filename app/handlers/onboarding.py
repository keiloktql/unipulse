import logging

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

from app.services.user_service import (
    get_all_categories,
    get_account_subscriptions,
    get_category_subscriber_counts,
)

logger = logging.getLogger(__name__)

WELCOME_TEXT = (
    "You're now part of UniPulse! \U0001f389\n\n"
    "UniPulse is your single feed for NUS campus life — "
    "never miss an event again.\n\n"
    "Here's what you can do:\n"
    "\u2022 /events \u2014 browse upcoming events\n"
    "\u2022 /trending \u2014 see what's popular\n"
    "\u2022 /find #sports \u2014 filter by category\n"
    "\u2022 /find <keyword> \u2014 search by text\n"
    "\u2022 /subscribe \u2014 manage your interests\n"
    "\u2022 /newslettertime 09:00 \u2014 set daily digest time\n\n"
    "To post an event, send a message with #unipulse in any group chat.\n\n"
    "Start by picking the topics you care about \u2193"
)


def _build_category_keyboard(
    categories: list, subscribed_ids: set, counts: dict
) -> InlineKeyboardMarkup:
    buttons = []
    for cat in categories:
        cid = cat["category_id"]
        is_subscribed = cid in subscribed_ids
        check = "x" if is_subscribed else "  "
        sub_count = counts.get(cid, 0)
        buttons.append([
            InlineKeyboardButton(
                f"[{check}] #{cat['name']}  ({sub_count} subs)",
                callback_data=f"sub:{cid}",
            )
        ])
    buttons.append([
        InlineKeyboardButton("Done \u2705", callback_data="sub:done"),
    ])
    return InlineKeyboardMarkup(buttons)


async def send_onboarding(bot: Bot, telegram_id: int, account_id: str):
    """Send welcome message followed by category subscription keyboard."""
    try:
        await bot.send_message(chat_id=telegram_id, text=WELCOME_TEXT)
    except Exception as e:
        logger.error("Failed to send onboarding welcome to %s: %s", telegram_id, e)
        return

    categories = get_all_categories()
    if not categories:
        # No categories yet; just end with a hint
        try:
            await bot.send_message(
                chat_id=telegram_id,
                text="No categories exist yet — they're created automatically when events are posted. Use /subscribe later to follow topics.",
            )
        except Exception as e:
            logger.error("Failed to send onboarding category hint to %s: %s", telegram_id, e)
        return

    subscribed_ids = {s["fk_category_id"] for s in get_account_subscriptions(account_id)}
    counts = get_category_subscriber_counts()
    keyboard = _build_category_keyboard(categories, subscribed_ids, counts)

    try:
        await bot.send_message(
            chat_id=telegram_id,
            text="Tap a category to subscribe:",
            reply_markup=keyboard,
        )
    except Exception as e:
        logger.error("Failed to send onboarding category keyboard to %s: %s", telegram_id, e)
