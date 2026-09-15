from telegram import Update
from telegram.ext import ContextTypes

from bot.services.access import check_access
from bot.menu import main_menu


LABS = {
    "🔤 Font & Text": "🔤 Font & Text Lab",
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
    if not update.message:
        return

    if not await check_access(update, context):
        return

    text = update.message.text

    if text not in LABS:
        return

    try:
        await update.message.delete()
    except Exception:
        pass

    if text == "🖼️ Image Lab":
        from bot.labs.image.handler import image_menu
        await image_menu(update, context)
        return

    if text == "🔤 Font & Text":
        from bot.labs.font_text.handler import font_text_menu
        await font_text_menu(update, context)
        return

    if text == "📄 PDF Lab":
        from bot.labs.pdf.handler import pdf_menu
        await pdf_menu(update, context)
        return

    await update.message.reply_text(
        f"{LABS[text]}\n\n"
        "🚧 این بخش در حال ساخت است.",
        reply_markup=main_menu(),
    )
