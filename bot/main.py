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
from bot.handlers.lab_menu import lab_menu

from bot.labs.audio import register_audio_handlers
from bot.labs.image import register_image_handlers
from bot.labs.pdf import register_pdf_handlers
from bot.labs.font_text import register_font_text_handlers
from bot.labs.file import register_file_handlers


def main():
    init_db()

    app = Application.builder().token(BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CommandHandler("help", help_command))

    # Labs
    register_audio_handlers(app)
    register_image_handlers(app)
    register_pdf_handlers(app)
    register_font_text_handlers(app)
    register_file_handlers(app)

    # Main menu
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            lab_menu,
        ),
        group=10,
    )

    # Callback queries
    app.add_handler(
        CallbackQueryHandler(callbacks),
        group=20,
    )

    print("🧰 Tool Box is running...")
    print(
        "📢 Force Join:",
        __import__("config").CHANNEL
    )

    app.run_polling(
        allowed_updates=[
            "message",
            "callback_query",
        ]
    )


if __name__ == "__main__":
    main()
