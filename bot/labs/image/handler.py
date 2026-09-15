from pathlib import Path
import os
import shutil

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, MessageHandler, filters

from bot.services.access import check_access

from .processor import (
    new_file,
    crop,
    draw,
    blur,
    pixelate,
    watermark,
    stamp,
    timestamp,
    stitch,
    split,
    exif_view,
    exif_remove,
    palette,
    ascii_art,
    document_scan,
    contact_sheet,
)

IMAGE_MENU = [
    [KeyboardButton("📝 OCR"), KeyboardButton("✂️ Crop")],
    [KeyboardButton("✏️ Draw"), KeyboardButton("🌫️ Blur")],
    [KeyboardButton("🟪 Pixelate"), KeyboardButton("💧 Watermark")],
    [KeyboardButton("🏷️ Stamp"), KeyboardButton("🕒 Timestamp")],
    [KeyboardButton("🔗 Stitch"), KeyboardButton("✂️ Split")],
    [KeyboardButton("📋 EXIF View"), KeyboardButton("🧹 EXIF Remove")],
    [KeyboardButton("🎨 Palette"), KeyboardButton("🔤 ASCII")],
    [KeyboardButton("📄 Document Scan"), KeyboardButton("🖼️ Contact Sheet")],
    [KeyboardButton("🏠 Home")],
]

HOME = ReplyKeyboardMarkup(
    [
        [KeyboardButton("🔤 Font & Text"), KeyboardButton("🎛️ Audio Lab")],
        [KeyboardButton("🖼️ Image Lab"), KeyboardButton("📄 PDF Lab")],
        [KeyboardButton("📦 File Lab"), KeyboardButton("🎬 Video Lab")],
        [KeyboardButton("🔲 QR & Barcode"), KeyboardButton("🌐 Web Lab")],
        [KeyboardButton("🛠️ Developer Lab"), KeyboardButton("🧮 Utility Lab")],
    ],
    resize_keyboard=True,
    is_persistent=True,
)

MENU = ReplyKeyboardMarkup(
    IMAGE_MENU,
    resize_keyboard=True,
    is_persistent=True,
)

ACTIONS = {
    "📝 OCR": "ocr",
    "✂️ Crop": "crop",
    "✏️ Draw": "draw",
    "🌫️ Blur": "blur",
    "🟪 Pixelate": "pixelate",
    "💧 Watermark": "watermark",
    "🏷️ Stamp": "stamp",
    "🕒 Timestamp": "timestamp",
    "🔗 Stitch": "stitch",
    "✂️ Split": "split",
    "📋 EXIF View": "exif_view",
    "🧹 EXIF Remove": "exif_remove",
    "🎨 Palette": "palette",
    "🔤 ASCII": "ascii",
    "📄 Document Scan": "document_scan",
    "🖼️ Contact Sheet": "contact_sheet",
}

async def delete_message(update):
    try:
        await update.message.delete()
    except Exception:
        pass

async def image_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update, context):
        return

    await delete_message(update)

    context.user_data.pop("image_action", None)

    await update.effective_chat.send_message(
        "🖼️ Image Lab\n\n"
        "یکی از ابزارهای زیر را انتخاب کن:",
        reply_markup=MENU,
    )

async def image_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("active_lab") != "image":
        return

    if not update.message or not update.message.text:
        return

    text = update.message.text

    if text not in ACTIONS and text != "🏠 Home":
        return

    if not await check_access(update, context):
        return

    await delete_message(update)

    if text == "🏠 Home":
        context.user_data.pop("image_action", None)

        await update.effective_chat.send_message(
            "🧰 TOOL BOX\n\n"
            "👇 یک بخش را انتخاب کنید:",
            reply_markup=HOME,
        )
        return

    action = ACTIONS[text]
    context.user_data["image_action"] = action

    if action == "ocr":
        msg = "📝 OCR\n\nعکس را بفرست تا متن داخل آن استخراج شود."
    elif action == "stitch":
        msg = "🔗 Stitch\n\nعکس‌ها را یکی‌یکی بفرست.\nدر پایان /done را بزن."
    elif action == "contact_sheet":
        msg = "🖼️ Contact Sheet\n\nچند عکس بفرست.\nدر پایان /done را بزن."
    elif action == "crop":
        msg = "✂️ Crop\n\nفعلاً عکس را بفرست؛ برش پیش‌فرض انجام می‌شود."
    elif action == "watermark":
        msg = "💧 Watermark\n\nعکس را بفرست."
    elif action == "stamp":
        msg = "🏷️ Stamp\n\nعکس را بفرست."
    else:
        msg = f"{text}\n\n📷 عکس را بفرست."

    await update.effective_chat.send_message(
        msg,
        reply_markup=MENU,
    )

async def download_photo(update, context):
    message = update.message

    if message.photo:
        photo = message.photo[-1]
        tg_file = await context.bot.get_file(photo.file_id)

        path = new_file(".jpg")
        await tg_file.download_to_drive(path)

        return path

    if message.document:
        mime = message.document.mime_type or ""

        if not mime.startswith("image/"):
            return None

        if message.document.file_size and message.document.file_size > 50 * 1024 * 1024:
            raise RuntimeError("حداکثر حجم فایل 50MB است.")

        tg_file = await context.bot.get_file(message.document.file_id)

        ext = Path(message.document.file_name or ".jpg").suffix or ".jpg"
        path = new_file(ext)

        await tg_file.download_to_drive(path)

        return path

    return None

async def ocr_image(path):
    try:
        import pytesseract
        from PIL import (
            Image,
            ImageOps,
            ImageEnhance,
            ImageFilter,
        )

        original = Image.open(path).convert("RGB")

        candidates = []

        # -------------------------------------------------
        # 1. تصویر اصلی
        # -------------------------------------------------
        images = [original]

        # -------------------------------------------------
        # 2. بزرگ‌نمایی
        # -------------------------------------------------
        for scale in (2, 3):
            img = original.resize(
                (
                    original.width * scale,
                    original.height * scale
                ),
                Image.Resampling.LANCZOS
            )
            images.append(img)

        # -------------------------------------------------
        # 3. preprocessing
        # -------------------------------------------------
        processed = []

        for img in images:
            gray = ImageOps.grayscale(img)

            # افزایش کنتراست
            contrast = ImageEnhance.Contrast(gray).enhance(2.0)

            # شارپ کردن
            sharp = ImageEnhance.Sharpness(contrast).enhance(2.0)

            # حذف نویز جزئی
            sharp = sharp.filter(ImageFilter.MedianFilter(size=3))

            processed.append(sharp)

            # threshold معمولی
            for threshold_value in (140, 170, 200):
                bw = sharp.point(
                    lambda p, t=threshold_value:
                    255 if p > t else 0
                )
                processed.append(bw)

        # -------------------------------------------------
        # OCR
        # -------------------------------------------------
        languages = []

        try:
            available = pytesseract.get_languages(config="")
        except Exception:
            available = ["eng"]

        if "fas" in available and "eng" in available:
            languages.append("fas+eng")

        if "fas" in available:
            languages.append("fas")

        if "eng" in available:
            languages.append("eng")

        if not languages:
            languages = ["eng"]

        # جلوگیری از تکرار
        languages = list(dict.fromkeys(languages))

        for img in processed:
            for lang in languages:

                for psm in (3, 6, 11, 12):

                    try:
                        text = pytesseract.image_to_string(
                            img,
                            lang=lang,
                            config=f"--oem 3 --psm {psm}"
                        ).strip()

                        if not text:
                            continue

                        # حذف خروجی‌های خیلی ضعیف
                        useful = sum(
                            1
                            for c in text
                            if c.isalnum()
                            or "\u0600" <= c <= "\u06ff"
                        )

                        if useful >= 3:
                            candidates.append(text)

                    except Exception:
                        continue

        if not candidates:
            return ""

        # -------------------------------------------------
        # انتخاب بهترین خروجی
        # -------------------------------------------------
        def score(text):
            chars = [
                c for c in text
                if c.isalnum() or "\u0600" <= c <= "\u06ff"
            ]

            words = [
                x for x in text.split()
                if len(x) >= 2
            ]

            # تعداد حروف + کلمات
            value = len(chars) + (len(words) * 4)

            # خروجی‌های پر از کاراکتر عجیب امتیاز کمتر
            weird = sum(
                1
                for c in text
                if c in "`~^|{}[]<>"
            )

            value -= weird * 3

            return value

        candidates.sort(key=score, reverse=True)

        best = candidates[0]

        # -------------------------------------------------
        # تمیز کردن خروجی
        # -------------------------------------------------
        lines = []

        for line in best.splitlines():
            line = line.strip()

            if not line:
                continue

            # خطوط خیلی کوتاه و بی‌معنی
            if len(line) <= 1:
                continue

            lines.append(line)

        return "\n".join(lines)

    except Exception as e:
        raise RuntimeError(f"OCR error: {e}")

async def send_photo_result(update, path, caption=None):
    if not os.path.exists(path):
        raise RuntimeError("فایل خروجی ساخته نشد.")

    with open(path, "rb") as f:
        await update.effective_chat.send_document(
            document=f,
            caption=caption
        )

async def process_image(update, context, path):
    action = context.user_data.get("image_action")

    if not action:
        return

    output = None

    if action == "ocr":
        text = await ocr_image(path)

        if not text:
            text = "❌ متنی پیدا نشد."

        await update.effective_chat.send_message(
            "📝 OCR Result\n\n" + text
        )
        return

    if action == "crop":
        output = new_file(".jpg")
        crop(path, output)

    elif action == "draw":
        output = new_file(".jpg")
        draw(path, output)

    elif action == "blur":
        output = new_file(".jpg")
        blur(path, output)

    elif action == "pixelate":
        output = new_file(".jpg")
        pixelate(path, output)

    elif action == "watermark":
        output = new_file(".png")
        watermark(path, output)

    elif action == "stamp":
        output = new_file(".png")
        stamp(path, output)

    elif action == "timestamp":
        output = new_file(".png")
        timestamp(path, output)

    elif action == "exif_view":
        text = exif_view(path)

        await update.effective_chat.send_message(text)
        return

    elif action == "exif_remove":
        output = new_file(".jpg")
        exif_remove(path, output)

    elif action == "palette":
        output = new_file(".jpg")
        palette(path, output)

    elif action == "ascii":
        output = new_file(".txt")
        ascii_art(path, output)

    elif action == "document_scan":
        output = new_file(".jpg")
        document_scan(path, output)

    elif action == "split":
        out_dir = Path("temp/image") / os.urandom(4).hex()
        out_dir.mkdir(parents=True, exist_ok=True)

        outputs = split(path, str(out_dir))

        for item in outputs:
            await send_photo_result(
                update,
                item,
                "✂️ Image Split"
            )

        return

    elif action in ("stitch", "contact_sheet"):
        await update.effective_chat.send_message(
            "این ابزار برای چند عکس است.\n"
            "فعلاً برای پردازش تکی، ابزار دیگری انتخاب کن."
        )
        return

    if output:
        await send_photo_result(
            update,
            output,
            f"✅ {action} انجام شد."
        )

async def image_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("active_lab") != "image":
        return

    if not context.user_data.get("image_action"):
        return

    if not await check_access(update, context):
        return

    try:
        path = await download_photo(update, context)

        if not path:
            return

        await process_image(update, context, path)

    except Exception as e:
        await update.effective_chat.send_message(
            f"❌ خطا در پردازش تصویر:\n{e}"
        )

def register_image_handlers(app):
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            image_text,
            block=False,
        ),
        group=1,
    )

    app.add_handler(
        MessageHandler(
            filters.PHOTO | filters.Document.IMAGE,
            image_media,
            block=False,
        ),
        group=1,
    )
