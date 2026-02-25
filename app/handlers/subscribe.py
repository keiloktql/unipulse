from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from app.services.user_service import (
    VERIFY_MSG,
    get_verified_account,
    get_all_categories,
    get_account_subscriptions,
    get_category_subscriber_counts,
    toggle_subscription,
)


async def subscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show category subscription menu with toggle checkmarks."""
    account = get_verified_account(update.effective_user.id)
    if not account:
        await update.message.reply_text(VERIFY_MSG)
        return

    categories = get_all_categories()
    if not categories:
        await update.message.reply_text(
            "No categories available yet. Events will create categories automatically!"
        )
        return
    subscribed_ids = _get_subscribed_ids(account["account_id"])
    counts = get_category_subscriber_counts()
    keyboard = _build_category_keyboard(categories, subscribed_ids, counts)
    await update.message.reply_text(
        "Tap a category to subscribe/unsubscribe:",
        reply_markup=keyboard,
    )


async def handle_subscription_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle sub:<category_id> callback toggles."""
    query = update.callback_query
    await query.answer()

    parts = query.data.split(":")
    if len(parts) != 2:
        return

    _, action = parts

    account = get_verified_account(query.from_user.id)
    if not account:
        await query.answer(VERIFY_MSG, show_alert=True)
        return

    # "start" from /start onboarding button -> show the keyboard
    if action == "start":
        categories = get_all_categories()
        if not categories:
            await query.answer("No categories available yet.", show_alert=True)
            return
        subscribed_ids = _get_subscribed_ids(account["account_id"])
        counts = get_category_subscriber_counts()
        keyboard = _build_category_keyboard(categories, subscribed_ids, counts)
        await query.message.reply_text(
            "Tap a category to subscribe/unsubscribe:",
            reply_markup=keyboard,
        )
        return

    # "done" -> confirm and close
    if action == "done":
        subscribed_ids = _get_subscribed_ids(account["account_id"])
        count = len(subscribed_ids)
        await query.edit_message_text(
            f"Subscriptions saved! You're following {count} category{'s' if count != 1 else ''}."
        )
        return

    # "cancel" -> close without confirmation
    if action == "cancel":
        await query.edit_message_text("Subscription selection cancelled.")
        return

    # Otherwise it's a category_id toggle
    category_id = action
    toggle_subscription(account["account_id"], category_id)

    # Refresh keyboard with updated counts
    categories = get_all_categories()
    subscribed_ids = _get_subscribed_ids(account["account_id"])
    counts = get_category_subscriber_counts()
    keyboard = _build_category_keyboard(categories, subscribed_ids, counts)
    try:
        await query.edit_message_reply_markup(reply_markup=keyboard)
    except Exception:
        pass


def _get_subscribed_ids(account_id: str) -> set:
    subs = get_account_subscriptions(account_id)
    return {s["fk_category_id"] for s in subs}


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
        InlineKeyboardButton("Complete", callback_data="sub:done"),
        InlineKeyboardButton("Cancel", callback_data="sub:cancel"),
    ])
    return InlineKeyboardMarkup(buttons)
