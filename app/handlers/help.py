from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# ── Section content ──────────────────────────────────────────────────────────

_SECTIONS = {
    "main": {
        "text": (
            "🎓 *UniPulse — Help*\n\n"
            "Your single feed for NUS campus life\\. "
            "Tap a topic below to learn more:"
        ),
        "keyboard": [
            [InlineKeyboardButton("🚀 Getting Started", callback_data="help:start")],
            [
                InlineKeyboardButton("📋 Browse Events", callback_data="help:browse"),
                InlineKeyboardButton("🔍 Search", callback_data="help:search"),
            ],
            [
                InlineKeyboardButton("🙋 RSVP & Reminders", callback_data="help:rsvp"),
                InlineKeyboardButton("🔔 Subscriptions", callback_data="help:subs"),
            ],
            [
                InlineKeyboardButton("📢 Post an Event", callback_data="help:post"),
                InlineKeyboardButton("⚙️ Manage Posts", callback_data="help:manage"),
            ],
            [InlineKeyboardButton("📖 All Commands", callback_data="help:commands")],
        ],
    },
    "start": {
        "text": (
            "🚀 *Getting Started*\n\n"
            "1\\. Send /verify in a DM with the bot\\.\n"
            "2\\. Enter your NUS email \\(@u\\.nus\\.edu or @nus\\.edu\\.sg\\)\\.\n"
            "3\\. Click the magic link in your inbox \\(check spam\\!\\)\\.\n"
            "4\\. Pick the categories you care about \\(\\#sports, \\#tech, …\\)\\.\n\n"
            "Once verified, you can browse events, RSVP, post, and receive a "
            "personalised daily digest\\."
        ),
    },
    "browse": {
        "text": (
            "📋 *Browsing Events*\n\n"
            "/events — next 10 upcoming events, sorted by date\\.\n"
            "/trending — top 5 events ranked by RSVP count\\.\n\n"
            "Each event card shows the title, date, location, and description, "
            "plus buttons to RSVP, set a reminder, add to Google Calendar, or share\\."
        ),
    },
    "search": {
        "text": (
            "🔍 *Searching Events*\n\n"
            "*/find \\<keyword\\>* — full\\-text search\\.\n"
            "_Example:_ /find hackathon\n\n"
            "*/find \\#category* — filter by category\\.\n"
            "_Example:_ /find \\#sports\n\n"
            "Categories are created automatically when events are posted\\."
        ),
    },
    "rsvp": {
        "text": (
            "🙋 *RSVP & Reminders*\n\n"
            "*RSVP* — tap *RSVP 🙋 \\(N\\)* on any event card to mark yourself as "
            "attending\\. Tap again to cancel\\.\n\n"
            "*Remind Me* — tap *⏰ Remind Me* to get a DM 24h and 1h before the event\\. "
            "Reminders are also created automatically when you RSVP\\.\n\n"
            "*Add to Calendar* — tap *📅 Add to Calendar* to open Google Calendar "
            "with the event pre\\-filled\\.\n\n"
            "*Share* — tap *🔗 Share* to get a deep link you can forward to friends\\."
        ),
    },
    "subs": {
        "text": (
            "🔔 *Subscriptions & Newsletter*\n\n"
            "*/subscribe* — open the category menu\\. Tap any category to toggle "
            "it on/off\\. \\[x\\] means subscribed\\.\n\n"
            "*Daily digest* — personalised event roundup sent once a day at your "
            "chosen time\\.\n"
            "Set the time with: /newslettertime 09:00 \\(SGT\\)\n\n"
            "*Weekly roundup* — every Sunday at 6 PM SGT, UniPulse sends the "
            "top 10 events ranked by RSVPs to all subscribed users\\."
        ),
    },
    "post": {
        "text": (
            "📢 *Posting an Event*\n\n"
            "In any group where the bot is a member, post your announcement "
            "with *\\#unipulse* in the message\\. Add extra tags for the category:\n\n"
            "```\n"
            "Hackathon Night @ UTown Auditorium\n"
            "Date: 15 March, 6 PM\n"
            "Open to all students\\!\n\n"
            "\\#unipulse \\#tech \\#hackathon\n"
            "```\n\n"
            "You can also attach an image poster — the bot uses AI to extract "
            "the title, date, location, and description automatically\\.\n\n"
            "_Limit: 5 posts per hour\\._"
        ),
    },
    "manage": {
        "text": (
            "⚙️ *Managing Your Posts*\n\n"
            "*/manage* — see all your events with:\n"
            "• *✏️ Edit* — fix AI parsing errors field\\-by\\-field "
            "\\(title, date, location, description\\)\n"
            "• *🗑 Delete* — remove the event from all feeds\n\n"
            "*/edit \\<event\\_id\\>* — edit a specific event directly\\.\n"
            "*/delete \\<event\\_id\\>* — delete a specific event directly\\."
        ),
    },
    "commands": {
        "text": (
            "📖 *All Commands*\n\n"
            "/start — welcome screen\n"
            "/verify — verify NUS identity \\(DM only\\)\n"
            "/events — upcoming events\n"
            "/trending — popular events\n"
            "/find \\<query\\> — search by keyword or \\#category\n"
            "/subscribe — manage category subscriptions\n"
            "/newslettertime HH:MM — set daily digest time \\(SGT\\)\n"
            "/manage — view, edit, delete your posts\n"
            "/edit \\<event\\_id\\> — edit an event\n"
            "/delete \\<event\\_id\\> — delete an event\n"
            "/help — show this guide"
        ),
    },
}

_BACK_ROW = [[InlineKeyboardButton("← Back to Help Menu", callback_data="help:main")]]


def _make_keyboard(key: str) -> InlineKeyboardMarkup:
    section = _SECTIONS[key]
    rows = section.get("keyboard", []) + _BACK_ROW if key != "main" else section.get("keyboard", [])
    return InlineKeyboardMarkup(rows)


# ── Handlers ─────────────────────────────────────────────────────────────────

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send the main help menu."""
    section = _SECTIONS["main"]
    await update.message.reply_text(
        section["text"],
        parse_mode="MarkdownV2",
        reply_markup=_make_keyboard("main"),
    )


async def handle_help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle help:<section> callbacks — edit the message to show the selected section."""
    query = update.callback_query
    await query.answer()

    key = query.data.split(":", 1)[1]
    if key not in _SECTIONS:
        return

    section = _SECTIONS[key]
    await query.edit_message_text(
        section["text"],
        parse_mode="MarkdownV2",
        reply_markup=_make_keyboard(key),
    )
