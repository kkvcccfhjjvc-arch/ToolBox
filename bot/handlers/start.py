from telegram import Update
from telegram.ext import ContextTypes

from bot.database import register_user
from bot.menu import main_menu
from bot.services.access import check_access


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    register_user(user)

    if not await check_access(update, context):
        return

    text = (
        "🧰 TOOL BOX\n\n"
        "یک جعبه‌ابزار چندمنظوره برای متن، صدا، تصویر، PDF، فایل، "
        "QR و ابزارهای کاربردی.\n\n"
        "👇 یک بخش را انتخاب کنید:"
    )

    await update.message.reply_text(
        text=text,
        reply_markup=main_menu()
    )
