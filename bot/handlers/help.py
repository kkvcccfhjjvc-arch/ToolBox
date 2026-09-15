from telegram import Update
from telegram.ext import ContextTypes

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🧰 Tool Box Help\n\n"
        "/start — منوی اصلی\n"
        "/admin — پنل مدیریت\n"
        "/help — راهنما"
    )
