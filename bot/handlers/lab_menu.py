from telegram import Update
from telegram.ext import ContextTypes

from bot.services.access import check_access
from bot.menu import main_menu


LABS = {
    "🔤 Font & Text": ("font_text", "🔤 Font & Text Lab"),
    "🎛️ Audio Lab": ("audio", "🎛️ Audio Lab"),
    "🖼️ Image Lab": ("image", "🖼️ Image Lab"),
    "📄 PDF Lab": ("pdf", "📄 PDF Lab"),
    "📦 File Lab": ("file", "📦 File Lab"),
    "🎬 Video Lab": ("video", "🎬 Video Lab"),
    "🔲 QR & Barcode": ("qr", "🔲 QR & Barcode Lab"),
    "🌐 Web Lab": ("web", "🌐 Web Lab"),
    "🛠️ Developer Lab": ("developer", "🛠️ Developer Lab"),
    "🧮 Utility Lab": ("utility", "🧮 Utility Lab"),
}


async def lab_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()

    if text not in LABS:
        return

    if not await check_access(update, context):
        return

    # این پیام، پیام ورود به Lab است.
    # Handlerهای خود Lab نباید آن را دوباره پردازش کنند.
    lab_id, title = LABS[text]

    context.user_data.clear()
    context.user_data["active_lab"] = lab_id

    try:
        await update.message.delete()
    except Exception:
        pass

    if lab_id == "audio":
        from bot.labs.audio.handler import send_audio_menu
        await send_audio_menu(update)
        return

    if lab_id == "image":
        from bot.labs.image.handler import image_menu
        await image_menu(update, context)
        return

    if lab_id == "pdf":
        from bot.labs.pdf.handler import pdf_menu
        await pdf_menu(update, context)
        return

    if lab_id == "font_text":
        from bot.labs.font_text.handler import font_text_menu
        await font_text_menu(update, context)
        return

    if lab_id == "file":
        from bot.labs.file.handler import file_lab_menu
        await file_lab_menu(update, context)
        return

    if lab_id == "video":
        from bot.labs.video.handler import video_lab_menu
        await video_lab_menu(update, context)
        return

    await update.effective_chat.send_message(
        f"{title}\n\n"
        "🚧 این بخش در حال ساخت است.",
        reply_markup=main_menu(),
    )
