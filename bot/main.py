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

def main():
    init_db()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CommandHandler("help", help_command))

    app.add_handler(
        CallbackQueryHandler(callbacks)
    )

    print("🧰 Tool Box is running...")
    print("📢 Force Join:", __import__("config").CHANNEL)

    app.run_polling(
        allowed_updates=[
            "message",
            "callback_query"
        ]
    )

if __name__ == "__main__":
    main()
