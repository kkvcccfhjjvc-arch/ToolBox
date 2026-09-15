from pathlib import Path

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, MessageHandler, filters

from bot.services.access import check_access

from .processor import (
    fancy_fonts,
    circled,
    squared,
    reverse_text,
    clean_text,
    count_text,
    unicode_encode,
    unicode_decode,
    url_encode,
    url_decode,
    format_text,
    text_to_image,
)


MENU_BUTTONS = [
    ["✨ Fancy Fonts", "🔠 Case Converter"],
    ["⭕ Circled", "🟦 Squared"],
    ["🖋 Script", "🕯 Fraktur"],
    ["Ｆ Full-width", "🔄 Reverse"],
    ["🧹 Clean Text", "🔢 Text Counter"],
    ["🔐 Unicode Encode", "🔓 Unicode Decode"],
    ["🔗 URL Encode", "🔗 URL Decode"],
    ["📝 Text → Image", "🇮🇷 Persian Text → Image"],
    ["📋 Telegram Format", "🏠 Home"],
]

MENU_SET = {
    item
    for row in MENU_BUTTONS
    for item in row
}


def font_menu():
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton(x) for x in row]
            for row in MENU_BUTTONS
        ],
        resize_keyboard=True,
        is_persistent=True,
    )


async def delete_message(update):
    try:
        await update.message.delete()
    except Exception:
        pass


async def font_text_menu(update, context):
    if not await check_access(update, context):
        return

    context.user_data.pop("font_text_action", None)

    await delete_message(update)

    await update.effective_chat.send_message(
        "🔤 Font & Text Lab\n\n"
        "ابزار موردنظرت رو انتخاب کن 👇",
        reply_markup=font_menu(),
    )


async def handle_font_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()

    # ورود از منوی اصلی
    if text == "🔤 Font & Text":
        await font_text_menu(update, context)
        return

    # اگر دکمه‌ای از Font & Text زده شده
    if text in MENU_SET:

        if text == "🏠 Home":
            from bot.menu import main_menu

            context.user_data.pop("font_text_action", None)

            await delete_message(update)

            await update.effective_chat.send_message(
                "🧰 TOOL BOX\n\n"
                "👇 یک بخش را انتخاب کنید:",
                reply_markup=main_menu(),
            )
            return

        if not await check_access(update, context):
            return

        context.user_data["font_text_action"] = text

        await delete_message(update)

        prompts = {
            "✨ Fancy Fonts":
                "✨ متن خودت رو بفرست تا چند مدل فونت مختلف برات بسازم:",

            "🔠 Case Converter":
                "🔠 متن رو بفرست تا حالت‌های مختلف حروف ساخته بشه:",

            "⭕ Circled":
                "⭕ متن رو بفرست:",

            "🟦 Squared":
                "🟦 متن رو بفرست:",

            "🖋 Script":
                "🖋 متن انگلیسی رو بفرست:",

            "🕯 Fraktur":
                "🕯 متن انگلیسی رو بفرست:",

            "Ｆ Full-width":
                "Ｆ متن رو بفرست:",

            "🔄 Reverse":
                "🔄 متن رو بفرست:",

            "🧹 Clean Text":
                "🧹 متن رو بفرست:",

            "🔢 Text Counter":
                "🔢 متن رو بفرست:",

            "🔐 Unicode Encode":
                "🔐 متن رو بفرست:",

            "🔓 Unicode Decode":
                "🔓 کدهای Unicode رو بفرست.\n"
                "مثال: U+0048 U+0069",

            "🔗 URL Encode":
                "🔗 متن یا URL رو بفرست:",

            "🔗 URL Decode":
                "🔗 متن Encode شده رو بفرست:",

            "📝 Text → Image":
                "📝 متن رو بفرست تا به تصویر PNG تبدیلش کنم:",

            "🇮🇷 Persian Text → Image":
                "🇮🇷 متن فارسی رو بفرست تا به تصویر تبدیلش کنم:",

            "📋 Telegram Format":
                "📋 متن رو بفرست تا فرمت‌های تلگرام رو برات بسازم:",
        }

        await update.effective_chat.send_message(
            prompts.get(text, "📝 متن رو بفرست:")
        )

        return

    # اگر منتظر متن هستیم
    action = context.user_data.get("font_text_action")

    if not action:
        return

    if not await check_access(update, context):
        return

    try:
        await delete_message(update)

        if action == "✨ Fancy Fonts":
            fonts = fancy_fonts(text)

            result = (
                "✨ Fancy Fonts\n\n"
                f"Normal:\n{fonts['Normal']}\n\n"
                f"Bold:\n{fonts['Bold']}\n\n"
                f"Italic:\n{fonts['Italic']}\n\n"
                f"Fraktur:\n{fonts['Fraktur']}\n\n"
                f"Script:\n{fonts['Script']}\n\n"
                f"Full-width:\n{fonts['Full-width']}"
            )

            await update.effective_chat.send_message(result)

        elif action == "🔠 Case Converter":
            await update.effective_chat.send_message(
                "🔠 Case Converter\n\n"
                f"UPPER:\n{text.upper()}\n\n"
                f"lower:\n{text.lower()}\n\n"
                f"Title:\n{text.title()}"
            )

        elif action == "⭕ Circled":
            await update.effective_chat.send_message(
                circled(text)
            )

        elif action == "🟦 Squared":
            await update.effective_chat.send_message(
                squared(text)
            )

        elif action == "🖋 Script":
            await update.effective_chat.send_message(
                fancy_fonts(text)["Script"]
            )

        elif action == "🕯 Fraktur":
            await update.effective_chat.send_message(
                fancy_fonts(text)["Fraktur"]
            )

        elif action == "Ｆ Full-width":
            await update.effective_chat.send_message(
                fancy_fonts(text)["Full-width"]
            )

        elif action == "🔄 Reverse":
            await update.effective_chat.send_message(
                reverse_text(text)
            )

        elif action == "🧹 Clean Text":
            await update.effective_chat.send_message(
                clean_text(text)
            )

        elif action == "🔢 Text Counter":
            stats = count_text(text)

            await update.effective_chat.send_message(
                "🔢 Text Counter\n\n"
                f"Characters: {stats['characters']}\n"
                f"Without spaces: {stats['characters_no_spaces']}\n"
                f"Words: {stats['words']}\n"
                f"Lines: {stats['lines']}"
            )

        elif action == "🔐 Unicode Encode":
            await update.effective_chat.send_message(
                unicode_encode(text)
            )

        elif action == "🔓 Unicode Decode":
            await update.effective_chat.send_message(
                unicode_decode(text)
            )

        elif action == "🔗 URL Encode":
            await update.effective_chat.send_message(
                url_encode(text)
            )

        elif action == "🔗 URL Decode":
            await update.effective_chat.send_message(
                url_decode(text)
            )

        elif action in {
            "📝 Text → Image",
            "🇮🇷 Persian Text → Image",
        }:
            output = (
                Path("temp")
                / f"text_{update.effective_user.id}.png"
            )

            output.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            text_to_image(
                text,
                str(output),
            )

            with open(output, "rb") as photo:
                await update.effective_chat.send_photo(
                    photo=photo,
                    caption="📝 Text → Image",
                )

        elif action == "📋 Telegram Format":
            result = (
                "📋 Telegram Formatting\n\n"
                f"Bold:\n{format_text(text, 'bold')}\n\n"
                f"Italic:\n{format_text(text, 'italic')}\n\n"
                f"Underline:\n{format_text(text, 'underline')}\n\n"
                f"Strike:\n{format_text(text, 'strike')}\n\n"
                f"Spoiler:\n{format_text(text, 'spoiler')}\n\n"
                f"Code:\n{format_text(text, 'code')}"
            )

            await update.effective_chat.send_message(
                result,
                parse_mode=ParseMode.HTML,
            )

    except Exception as e:
        print("FONT TEXT ERROR:", repr(e))

        await update.effective_chat.send_message(
            f"❌ خطا در پردازش:\n{e}"
        )

    finally:
        context.user_data.pop("font_text_action", None)


def register_font_text_handlers(app):
    # فقط یک Handler برای کل Font & Text
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_font_text,
        ),
        group=4,
    )
