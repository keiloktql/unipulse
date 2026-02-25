from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from app.config import settings
from app.handlers import (
    admin,
    browse,
    edit,
    find,
    help,
    moderation,
    newslettertime,
    parser,
    remind,
    rsvp,
    start,
    subscribe,
    verify,
)


def create_application():
    application = (
        ApplicationBuilder()
        .token(settings.TOKEN)
        .updater(None)
        .build()
    )

    # Verification conversation (DM only)
    verify_conv = ConversationHandler(
        entry_points=[CommandHandler("verify", verify.start_verify)],
        states={
            verify.EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, verify.receive_email)],
        },
        fallbacks=[CommandHandler("cancel", verify.cancel)],
    )

    # Event edit conversation
    edit_conv = ConversationHandler(
        entry_points=[CommandHandler("edit", edit.edit_command)],
        states={
            edit.CHOOSE_FIELD: [
                CallbackQueryHandler(edit.choose_field, pattern=r"^edit_field:"),
            ],
            edit.ENTER_VALUE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, edit.enter_value),
            ],
        },
        fallbacks=[CommandHandler("cancel", edit.cancel_edit)],
        per_message=False,
    )

    # /start and /help
    application.add_handler(CommandHandler("start", start.start_command))
    application.add_handler(CommandHandler("help", help.help_command))

    # Verification
    application.add_handler(verify_conv)

    # Edit (must come before generic message handler)
    application.add_handler(edit_conv)

    # Subscribe command
    application.add_handler(CommandHandler("subscribe", subscribe.subscribe_command))

    # Browse and search commands
    application.add_handler(CommandHandler("events", browse.list_events))
    application.add_handler(CommandHandler("trending", browse.trending_events))
    application.add_handler(CommandHandler("find", find.find_command))
    application.add_handler(CommandHandler("newslettertime", newslettertime.newslettertime_command))
    application.add_handler(CommandHandler("delete", admin.delete_event_command))

    # Moderation panel
    application.add_handler(CommandHandler("manage", moderation.manage_command))

    # Smart Parser: listen for #unipulse in group chats
    application.add_handler(MessageHandler(
        filters.ChatType.GROUPS & filters.Regex(r"(?i)#unipulse"),
        parser.handle_event_message,
    ))

    # Callback query handlers (order matters: most specific patterns first)
    application.add_handler(CallbackQueryHandler(rsvp.handle_rsvp, pattern=r"^rsvp:"))
    application.add_handler(CallbackQueryHandler(subscribe.handle_subscription_toggle, pattern=r"^sub:"))
    application.add_handler(CallbackQueryHandler(remind.handle_remind_button, pattern=r"^remind:"))
    application.add_handler(CallbackQueryHandler(moderation.handle_moderation_callback, pattern=r"^mod:"))
    application.add_handler(CallbackQueryHandler(help.handle_help_callback, pattern=r"^help:"))

    return application
