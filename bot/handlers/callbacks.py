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


async def callbacks(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query

    await query.answer()

    data = query.data

    # =========================
    # BACK TO MAIN
    # =========================

    if data == "back_main":
        if not await check_access(update, context):
            return

        context.user_data.clear()

        await query.edit_message_text(
            "🧰 Tool Box\n\n"
            "👇 ابزار موردنظر را انتخاب کنید:",
            reply_markup=main_menu()
        )
        return

    # =========================
    # MEMBERSHIP
    # =========================

    if data == "check_membership":
        if await check_access(update, context):
            await query.edit_message_text(
                "✅ عضویت تأیید شد!\n\n"
                "👇 ابزار موردنظر را انتخاب کنید:",
                reply_markup=main_menu()
            )
        return

    # =========================
    # LABS
    # =========================

    if data in LAB_NAMES:

        if not await check_access(update, context):
            return

        # Audio Lab is handled by its own module.
        if data == "lab_audio":
            from bot.labs.audio.handler import audio_menu

            await query.edit_message_text(
                "🎛️ Audio Lab\n\n"
                "ابزار موردنظر را انتخاب کنید:",
                reply_markup=audio_menu()
            )
            return

        await query.edit_message_text(
            f"{LAB_NAMES[data]}\n\n"
            "🚧 این بخش فعلاً در حال ساخت است.",
            reply_markup=__import__(
                "telegram"
            ).InlineKeyboardMarkup([
                [
                    __import__(
                        "telegram"
                    ).InlineKeyboardButton(
                        "🔙 منوی اصلی",
                        callback_data="back_main"
                    )
                ]
            ])
        )
