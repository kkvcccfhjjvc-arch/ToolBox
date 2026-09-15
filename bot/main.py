from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from config import BOT_TOKEN
from bot.database import init_db
from bot.handlers.start import start
from bot.handlers.admin import admin
from bot.handlers.help import help_command
from bot.handlers.callbacks import callbacks
from bot.labs.audio import register_audio_handlers
from bot.handlers.lab_menu import lab_menu


def main():
    init_db()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CommandHandler("help", help_command))

    # Audio Lab handlers must be registered before the global callback handler.
    register_audio_handlers(app)

    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, lab_menu)
    )

    # Global callbacks
    app.add_handler(
        CallbackQueryHandler(callbacks)
    )

    print("🧰 Tool Box is running...")
    print(
        "📢 Force Join:",
        __import__("config").CHANNEL
    )

    app.run_polling(
        allowed_updates=[
            "message",
            "callback_query"
        ]
    )


if __name__ == "__main__":
    main()
