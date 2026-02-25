from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from app.config import settings
from app.handlers import admin, browse, find, newslettertime, parser, remind, rsvp, start, subscribe, verify


def create_application():
    application = (
        ApplicationBuilder()
        .token(settings.TOKEN)
        .updater(None)
        .build()
    )

    # Admin verification conversation (DM only)
    verify_conv = ConversationHandler(
        entry_points=[CommandHandler("verify", verify.start_verify)],
        states={
            verify.EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, verify.receive_email)],
        },
        fallbacks=[CommandHandler("cancel", verify.cancel)],
    )

    # /start
    application.add_handler(CommandHandler("start", start.start_command))

    # Admin verification
    application.add_handler(verify_conv)

    # Subscribe command
    application.add_handler(CommandHandler("subscribe", subscribe.subscribe_command))

    # Browse and search commands
    application.add_handler(CommandHandler("events", browse.list_events))
    application.add_handler(CommandHandler("trending", browse.trending_events))
    application.add_handler(CommandHandler("find", find.find_command))
    application.add_handler(CommandHandler("newslettertime", newslettertime.newslettertime_command))
    application.add_handler(CommandHandler("delete", admin.delete_event_command))

    # Smart Parser: listen for #unipulse in group chats
    application.add_handler(MessageHandler(
        filters.ChatType.GROUPS & filters.Regex(r"(?i)#unipulse"),
        parser.handle_event_message,
    ))

    # Callback query handlers
    application.add_handler(CallbackQueryHandler(rsvp.handle_rsvp, pattern=r"^rsvp:"))
    application.add_handler(CallbackQueryHandler(subscribe.handle_subscription_toggle, pattern=r"^sub:"))
    application.add_handler(CallbackQueryHandler(remind.handle_remind_button, pattern=r"^remind:"))

    return application
