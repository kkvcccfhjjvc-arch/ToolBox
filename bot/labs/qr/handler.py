from pathlib import Path

from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, MessageHandler, filters

from bot.services.access import check_access

from bot.labs.qr.processor import (
    new_file,
    make_qr,
    make_wifi,
    make_phone,
    make_email,
    make_geo,
    make_vcard,
    make_barcode,
    image_to_qr_text,
)


ACTIONS = {
    "🔗 URL": "url",
    "📝 Text": "text",
    "📶 Wi-Fi": "wifi",
    "📞 Phone": "phone",
    "📧 Email": "email",
    "📍 Location": "geo",
    "👤 vCard": "vcard",
    "🔐 Password": "password",
    "🏷️ Barcode": "barcode",
    "📚 ISBN": "isbn",
    "📷 Scan QR": "scan",
}


def qr_menu():
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("🔗 URL"), KeyboardButton("📝 Text")],
            [KeyboardButton("📶 Wi-Fi"), KeyboardButton("📞 Phone")],
            [KeyboardButton("📧 Email"), KeyboardButton("📍 Location")],
            [KeyboardButton("👤 vCard"), KeyboardButton("🔐 Password")],
            [KeyboardButton("🏷️ Barcode"), KeyboardButton("📚 ISBN")],
            [KeyboardButton("📷 Scan QR")],
            [KeyboardButton("🏠 Home")],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )


async def qr_lab_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["active_lab"] = "qr"

    for key in (
        "qr_action",
        "qr_step",
        "qr_data",
        "qr_values",
    ):
        context.user_data.pop(key, None)

    await update.effective_chat.send_message(
        "🔲 QR & Barcode Lab\n\n👇 یک ابزار را انتخاب کنید:",
        reply_markup=qr_menu(),
    )


async def delete_selection(update):
    try:
        await update.message.delete()
    except Exception:
        pass


async def send_qr(update, data, caption="✅ QR ساخته شد."):
    output = new_file(".png")
    make_qr(data, output)

    await update.effective_chat.send_photo(
        photo=str(output),
        caption=caption,
    )

    output.unlink(missing_ok=True)


async def handle_qr_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()

    # Central router owns top-level lab buttons.
    if text in {
        "🔤 Font & Text",
        "🎛️ Audio Lab",
        "🖼️ Image Lab",
        "📄 PDF Lab",
        "📦 File Lab",
        "🎬 Video Lab",
        "🔲 QR & Barcode",
        "🌐 Web Lab",
        "🛠️ Developer Lab",
        "🧮 Utility Lab",
    }:
        return

    if context.user_data.get("active_lab") != "qr":
        return

    if not await check_access(update, context):
        return

    if text == "🏠 Home":
        context.user_data.clear()
        await delete_selection(update)

        from bot.menu import main_menu

        await update.effective_chat.send_message(
            "🧰 TOOL BOX\n\n👇 یک بخش را انتخاب کنید:",
            reply_markup=main_menu(),
        )
        return

    action = ACTIONS.get(text)

    if action:
        context.user_data["qr_action"] = action
        context.user_data["qr_step"] = 1
        await delete_selection(update)

        prompts = {
            "url": "🔗 لینک را ارسال کن:",
            "text": "📝 متن موردنظر را ارسال کن:",
            "wifi": (
                "📶 اطلاعات Wi-Fi را در یک پیام بفرست:\n\n"
                "SSID | PASSWORD\n\n"
                "مثال:\n"
                "MyWiFi | 12345678"
            ),
            "phone": "📞 شماره تلفن را ارسال کن:",
            "email": (
                "📧 ایمیل را به این شکل بفرست:\n\n"
                "email | subject | body"
            ),
            "geo": (
                "📍 مختصات را این‌طور بفرست:\n\n"
                "latitude | longitude"
            ),
            "vcard": (
                "👤 اطلاعات مخاطب:\n\n"
                "Name | Phone | Email | Organization"
            ),
            "password": "🔐 متن یا رمز موردنظر را ارسال کن:",
            "barcode": "🏷️ مقدار Barcode را ارسال کن:",
            "isbn": "📚 شماره ISBN را ارسال کن:",
            "scan": "📷 یک تصویر دارای QR ارسال کن:",
        }

        await update.effective_chat.send_message(
            prompts[action]
        )
        return

    action = context.user_data.get("qr_action")

    if not action:
        return

    try:
        if action == "url":
            await send_qr(update, text, "🔗 QR لینک آماده شد.")

        elif action == "text":
            await send_qr(update, text, "📝 QR متن آماده شد.")

        elif action == "password":
            await send_qr(update, text, "🔐 QR رمز آماده شد.")

        elif action == "phone":
            await send_qr(
                update,
                make_phone(text),
                "📞 QR شماره تلفن آماده شد.",
            )

        elif action == "email":
            parts = [x.strip() for x in text.split("|")]

            email = parts[0]
            subject = parts[1] if len(parts) > 1 else ""
            body = parts[2] if len(parts) > 2 else ""

            await send_qr(
                update,
                make_email(email, subject, body),
                "📧 QR ایمیل آماده شد.",
            )

        elif action == "wifi":
            parts = [x.strip() for x in text.split("|")]

            if len(parts) < 2:
                raise ValueError("فرمت باید SSID | PASSWORD باشد.")

            data = make_wifi(parts[0], parts[1])

            await send_qr(
                update,
                data,
                "📶 QR Wi-Fi آماده شد.",
            )

        elif action == "geo":
            parts = [x.strip() for x in text.split("|")]

            if len(parts) != 2:
                raise ValueError("فرمت باید latitude | longitude باشد.")

            data = make_geo(parts[0], parts[1])

            await send_qr(
                update,
                data,
                "📍 QR موقعیت آماده شد.",
            )

        elif action == "vcard":
            parts = [x.strip() for x in text.split("|")]

            name = parts[0]
            phone = parts[1] if len(parts) > 1 else ""
            email = parts[2] if len(parts) > 2 else ""
            organization = parts[3] if len(parts) > 3 else ""

            await send_qr(
                update,
                make_vcard(name, phone, email, organization),
                "👤 QR مخاطب آماده شد.",
            )

        elif action == "barcode":
            output = new_file(".png")
            make_barcode(text, output)

            await update.effective_chat.send_photo(
                photo=str(output),
                caption="🏷️ Barcode آماده شد.",
            )

            output.unlink(missing_ok=True)

        elif action == "isbn":
            isbn = text.replace("-", "").replace(" ", "")

            if len(isbn) not in (10, 13) or not isbn.isdigit():
                raise ValueError("ISBN باید ۱۰ یا ۱۳ رقم باشد.")

            await send_qr(
                update,
                f"isbn:{isbn}",
                "📚 QR ISBN آماده شد.",
            )

        context.user_data.pop("qr_action", None)
        context.user_data.pop("qr_step", None)

    except Exception as e:
        await update.effective_chat.send_message(
            f"❌ خطا:\n{str(e)}"
        )



async def handle_qr_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("active_lab") != "qr":
        return

    if context.user_data.get("qr_action") != "scan":
        return

    if not update.message:
        return

    if not await check_access(update, context):
        return

    try:
        telegram_file = None
        extension = ".jpg"

        # Normal Telegram photo
        if update.message.photo:
            photo = update.message.photo[-1]
            telegram_file = await photo.get_file()
            extension = ".jpg"

        # Image sent as Telegram document
        elif update.message.document:
            document = update.message.document

            mime = document.mime_type or ""

            if not mime.startswith("image/"):
                return

            telegram_file = await document.get_file()

            name = document.file_name or "image.jpg"

            if "." in name:
                extension = "." + name.rsplit(".", 1)[1].lower()

        else:
            return

        source = new_file(extension)
        await telegram_file.download_to_drive(str(source))

        result = image_to_qr_text(source)

        source.unlink(missing_ok=True)

        if result:
            await update.effective_chat.send_message(
                "📷 QR پیدا شد:\n\n"
                f"<code>{result}</code>",
                parse_mode="HTML",
            )
        else:
            await update.effective_chat.send_message(
                "❌ QR قابل شناسایی پیدا نشد.\n\n"
                "یک عکس واضح‌تر از QR ارسال کن."
            )

        context.user_data.pop("qr_action", None)
        context.user_data.pop("qr_step", None)

    except Exception as e:
        await update.effective_chat.send_message(
            f"❌ خطا در اسکن QR:\n{str(e)}"
        )

