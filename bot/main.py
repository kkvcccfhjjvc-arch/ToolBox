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
from bot.labs.video.handler import register_video_handlers
from bot.labs.qr import register_qr_handlers
from bot.labs.web import register_web_handlers
from bot.labs.developer import register_developer_handlers
from bot.labs.utility import register_utility_handlers


def main():
    init_db()

    app = Application.builder().token(BOT_TOKEN).build()

    # =========================
    # COMMANDS
    # =========================

    app.add_handler(
        CommandHandler("start", start),
        group=0,
    )

    app.add_handler(
        CommandHandler("admin", admin),
        group=0,
    )

    app.add_handler(
        CommandHandler("help", help_command),
        group=0,
    )

    # =========================
    # CENTRAL LAB ROUTER
    # MUST RUN BEFORE LAB HANDLERS
    # =========================

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            lab_menu,
        ),
        group=0,
    )

    # =========================
    # LAB HANDLERS
    # =========================

    register_audio_handlers(app)
    register_image_handlers(app)
    register_pdf_handlers(app)
    register_font_text_handlers(app)
    register_file_handlers(app)
    register_video_handlers(app)
    register_qr_handlers(app)
    register_web_handlers(app)
    register_developer_handlers(app)
    register_utility_handlers(app)

    # =========================
    # CALLBACKS
    # =========================

    app.add_handler(
        CallbackQueryHandler(callbacks),
        group=2,
    )

    print("🧰 Tool Box is running...")
    print(
        "📢 Force Join:",
        __import__("config").CHANNEL,
    )

    app.run_polling(
        allowed_updates=[
            "message",
            "callback_query",
        ]
    )


if __name__ == "__main__":
    main()
