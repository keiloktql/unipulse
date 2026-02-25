from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from app.config import settings
from app.handlers import browse, parser, rsvp, start, verify


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
            verify.OTP: [MessageHandler(filters.TEXT & ~filters.COMMAND, verify.receive_otp)],
        },
        fallbacks=[CommandHandler("cancel", verify.cancel)],
    )

    # /start
    application.add_handler(CommandHandler("start", start.start_command))

    # Admin verification
    application.add_handler(verify_conv)

    # Smart Parser: listen for #unipulse in group chats
    application.add_handler(MessageHandler(
        filters.ChatType.GROUPS & filters.Regex(r"(?i)#unipulse"),
        parser.handle_event_message,
    ))

    # RSVP button callbacks
    application.add_handler(CallbackQueryHandler(rsvp.handle_rsvp, pattern=r"^rsvp:"))

    # Browse commands
    application.add_handler(CommandHandler("events", browse.list_events))
    application.add_handler(CommandHandler("trending", browse.trending_events))

    return application
