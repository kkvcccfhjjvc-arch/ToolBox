from telegram import Update
from telegram.ext import ContextTypes
from config import ADMIN_ID
from bot.database import stats

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ دسترسی ندارید.")
        return

    users, usages = stats()

    await update.message.reply_text(
        "👑 Admin Panel\n\n"
        f"👥 Users: {users}\n"
        f"📊 Tool Usage: {usages}\n\n"
        "پنل مدیریتی در حال توسعه است."
    )
