from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
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


def main():
    init_db()

    app = Application.builder().token(BOT_TOKEN).build()

    # Commands
    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CommandHandler("admin", admin)
    )

    app.add_handler(
        CommandHandler("help", help_command)
    )

    # Lab handlers
    # هر ماژول فقط مسئول قابلیت‌های خودش است.
    register_audio_handlers(app)
    register_image_handlers(app)
    register_pdf_handlers(app)
    register_font_text_handlers(app)
    register_file_handlers(app)
    register_video_handlers(app)

    # Main Lab Router
    # باید بعد از handlerهای اختصاصی باشد.
    from telegram.ext import MessageHandler, filters

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            lab_menu,
        ),
        group=10,
    )

    # Callback handlers
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
