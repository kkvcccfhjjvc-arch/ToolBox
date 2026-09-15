from telegram import Update
from telegram.ext import ContextTypes
from bot.services.access import check_access


LABS = {
    "🔤 Font & Text": "🔤 Font & Text Lab",
    "🎛️ Audio Lab": "🎛️ Audio Lab",
    "🖼️ Image Lab": "🖼️ Image Lab",
    "📄 PDF Lab": "📄 PDF Lab",
    "📦 File Lab": "📦 File Lab",
    "🎬 Video Lab": "🎬 Video Lab",
    "🔲 QR & Barcode": "🔲 QR & Barcode Lab",
    "🌐 Web Lab": "🌐 Web Lab",
    "🛠️ Developer Lab": "🛠️ Developer Lab",
    "🧮 Utility Lab": "🧮 Utility Lab",
}


async def lab_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update, context):
        return

    text = update.message.text

    if text not in LABS:
        return

    if text == "🎛️ Audio Lab":
        await update.message.reply_text(
            "🎛️ Audio Lab\n\n"
            "ابزارهای صوتی را انتخاب کنید 👇"
        )
        return

    await update.message.reply_text(
        f"{LABS[text]}\n\n"
        "🚧 این بخش در حال ساخت است."
    )
