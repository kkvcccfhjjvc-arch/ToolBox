from telegram import Update
from telegram.ext import ContextTypes
from bot.menu import main_menu
from bot.services.access import check_access

LAB_NAMES = {
    "lab_text": "🔤 Font & Text Lab",
    "lab_audio": "🎛️ Audio Lab",
    "lab_image": "🖼️ Image Lab",
    "lab_pdf": "📄 PDF Lab",
    "lab_file": "📦 File Lab",
    "lab_video": "🎬 Video Lab",
    "lab_qr": "🔲 QR & Barcode Lab",
    "lab_web": "🌐 Web Lab",
    "lab_dev": "🛠️ Developer Lab",
    "lab_util": "🧮 Utility Lab",
}

async def callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "check_membership":
        if await check_access(update, context):
            await query.message.reply_text(
                "✅ عضویت تأیید شد!\n\n"
                "👇 ابزار موردنظر را انتخاب کنید:",
                reply_markup=main_menu()
            )
        return

    if query.data in LAB_NAMES:
        if not await check_access(update, context):
            return

        await query.message.reply_text(
            f"{LAB_NAMES[query.data]}\n\n"
            "🚧 این بخش در حال ساخت است.\n"
            "قابلیت‌های این Lab به‌صورت ماژولار اضافه می‌شوند."
        )
