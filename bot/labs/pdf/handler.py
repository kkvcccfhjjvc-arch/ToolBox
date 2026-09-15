from pathlib import Path
import os
import shutil

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, MessageHandler, CommandHandler, filters

from bot.services.access import check_access

from .processor import (
    new_file,
    pdf_info,
    images_to_pdf,
    merge_pdfs,
    split_pdf,
    extract_pages,
    rotate_pdf,
    crop_pdf,
    extract_text,
    extract_images,
    encrypt_pdf,
    decrypt_pdf,
    add_watermark,
    metadata,
    compress_pdf,
    pdf_to_images,
)


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
    [
        [KeyboardButton("🖼️ Images → PDF"), KeyboardButton("📝 PDF → Text")],
        [KeyboardButton("🔗 Merge PDF"), KeyboardButton("✂️ Split PDF")],
        [KeyboardButton("🗜️ Compress PDF"), KeyboardButton("🔍 OCR PDF")],
        [KeyboardButton("🔐 Encrypt PDF"), KeyboardButton("🔓 Decrypt PDF")],
        [KeyboardButton("💧 Watermark"), KeyboardButton("🔄 Rotate")],
        [KeyboardButton("✂️ Crop PDF"), KeyboardButton("🖼️ Extract Images")],
        [KeyboardButton("📄 PDF → Images"), KeyboardButton("ℹ️ Metadata")],
        [KeyboardButton("🏠 Home")],
    ],
    resize_keyboard=True,
    is_persistent=True,
)


ACTIONS = {
    "🖼️ Images → PDF": "images_pdf",
    "📝 PDF → Text": "pdf_text",
    "🔗 Merge PDF": "merge",
    "✂️ Split PDF": "split",
    "🗜️ Compress PDF": "compress",
    "🔍 OCR PDF": "ocr",
    "🔐 Encrypt PDF": "encrypt",
    "🔓 Decrypt PDF": "decrypt",
    "💧 Watermark": "watermark",
    "🔄 Rotate": "rotate",
    "✂️ Crop PDF": "crop",
    "🖼️ Extract Images": "extract_images",
    "📄 PDF → Images": "pdf_images",
    "ℹ️ Metadata": "metadata",
}


async def delete_message(update):
    try:
        await update.message.delete()
    except Exception:
        pass


async def pdf_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update, context):
        return

    await delete_message(update)

    context.user_data.pop("pdf_action", None)
    context.user_data.pop("pdf_files", None)

    await update.effective_chat.send_message(
        "📄 PDF Lab\n\n"
        "یکی از ابزارها را انتخاب کن:",
        reply_markup=MENU,
    )


async def pdf_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text

    if text not in ACTIONS and text != "🏠 Home":
        return

    if not await check_access(update, context):
        return

    await delete_message(update)

    if text == "🏠 Home":
        context.user_data.pop("pdf_action", None)

        await update.effective_chat.send_message(
            "🧰 TOOL BOX\n\n👇 یک بخش را انتخاب کنید:",
            reply_markup=HOME,
        )
        return

    action = ACTIONS[text]

    context.user_data["pdf_action"] = action
    context.user_data["pdf_files"] = []

    messages = {
        "images_pdf":
            "🖼️ Images → PDF\n\n"
            "عکس‌ها را ارسال کن.\n"
            "در پایان /done را بزن.",

        "pdf_text":
            "📝 PDF → Text\n\n"
            "فایل PDF را ارسال کن.",

        "merge":
            "🔗 Merge PDF\n\n"
            "چند فایل PDF ارسال کن.\n"
            "در پایان /done را بزن.",

        "split":
            "✂️ Split PDF\n\n"
            "فایل PDF را ارسال کن.",

        "compress":
            "🗜️ Compress PDF\n\n"
            "فایل PDF را ارسال کن.",

        "ocr":
            "🔍 OCR PDF\n\n"
            "فایل PDF را ارسال کن.",

        "encrypt":
            "🔐 Encrypt PDF\n\n"
            "فایل PDF را ارسال کن.\n"
            "بعد رمز عبور را بفرست.",

        "decrypt":
            "🔓 Decrypt PDF\n\n"
            "فایل PDF را ارسال کن.\n"
            "بعد رمز عبور را بفرست.",

        "watermark":
            "💧 Watermark\n\n"
            "فایل PDF را ارسال کن.",

        "rotate":
            "🔄 Rotate\n\n"
            "فایل PDF را ارسال کن.\n"
            "چرخش پیش‌فرض 90 درجه است.",

        "crop":
            "✂️ Crop PDF\n\n"
            "فایل PDF را ارسال کن.",

        "extract_images":
            "🖼️ Extract Images\n\n"
            "فایل PDF را ارسال کن.",

        "pdf_images":
            "📄 PDF → Images\n\n"
            "فایل PDF را ارسال کن.",

        "metadata":
            "ℹ️ Metadata\n\n"
            "فایل PDF را ارسال کن.",
    }

    await update.effective_chat.send_message(
        messages[action],
        reply_markup=MENU,
    )


async def download_document(update, context):
    doc = update.message.document

    if not doc:
        return None

    if doc.file_size and doc.file_size > 50 * 1024 * 1024:
        raise RuntimeError("حداکثر حجم فایل 50MB است.")

    tg_file = await context.bot.get_file(doc.file_id)

    name = doc.file_name or "file.pdf"
    ext = Path(name).suffix or ".pdf"

    path = new_file(ext)

    await tg_file.download_to_drive(path)

    return path


async def send_file(update, path, caption=None):
    if not path or not os.path.exists(path):
        raise RuntimeError("فایل خروجی ساخته نشد.")

    with open(path, "rb") as f:
        await update.effective_chat.send_document(
            document=f,
            caption=caption,
        )


async def process_pdf(update, context, path):
    action = context.user_data.get("pdf_action")

    if not action:
        return

    if action == "images_pdf":
        files = context.user_data.setdefault("pdf_files", [])
        files.append(path)

        await update.effective_chat.send_message(
            f"✅ عکس دریافت شد ({len(files)})\n"
            "عکس بعدی را بفرست یا /done را بزن."
        )
        return

    if action == "merge":
        files = context.user_data.setdefault("pdf_files", [])
        files.append(path)

        await update.effective_chat.send_message(
            f"✅ PDF دریافت شد ({len(files)})\n"
            "PDF بعدی را بفرست یا /done را بزن."
        )
        return

    output = None

    if action == "pdf_text":
        output = new_file(".txt")
        output, text = extract_text(path, output)

        if not text.strip():
            text = "❌ متنی داخل PDF پیدا نشد."

        await update.effective_chat.send_message(
            "📝 PDF Text\n\n" + text[:3900]
        )
        return

    elif action == "split":
        out_dir = Path("temp/pdf") / os.urandom(4).hex()
        outputs = split_pdf(path, out_dir)

        for item in outputs[:20]:
            await send_file(update, item, "✂️ PDF Page")

        return

    elif action == "compress":
        output = new_file(".pdf")
        compress_pdf(path, output)

    elif action == "ocr":
        output = new_file(".txt")
        output, text = extract_text(path, output)

        if not text.strip():
            await update.effective_chat.send_message(
                "❌ متن قابل استخراج نبود.\n"
                "برای PDF اسکن‌شده باید OCR تصویری اضافه شود."
            )
            return

        await update.effective_chat.send_message(
            "🔍 OCR PDF\n\n" + text[:3900]
        )
        return

    elif action == "encrypt":
        context.user_data["pdf_pending_file"] = path
        context.user_data["pdf_waiting_password"] = True

        await update.effective_chat.send_message(
            "🔐 حالا رمز عبور PDF را ارسال کن."
        )
        return

    elif action == "decrypt":
        context.user_data["pdf_pending_file"] = path
        context.user_data["pdf_waiting_password"] = True

        await update.effective_chat.send_message(
            "🔓 رمز عبور PDF را ارسال کن."
        )
        return

    elif action == "watermark":
        output = new_file(".pdf")
        add_watermark(path, output)

    elif action == "rotate":
        output = new_file(".pdf")
        rotate_pdf(path, output, 90)

    elif action == "crop":
        output = new_file(".pdf")
        crop_pdf(path, output)

    elif action == "extract_images":
        out_dir = Path("temp/pdf") / os.urandom(4).hex()
        outputs = extract_images(path, out_dir)

        if not outputs:
            await update.effective_chat.send_message(
                "❌ تصویری داخل PDF پیدا نشد."
            )
            return

        for item in outputs[:20]:
            await send_file(update, item, "🖼️ Extracted Image")

        return

    elif action == "pdf_images":
        out_dir = Path("temp/pdf") / os.urandom(4).hex()
        outputs = pdf_to_images(path, out_dir)

        for item in outputs[:20]:
            await send_file(update, item, "📄 PDF Page")

        return

    elif action == "metadata":
        await update.effective_chat.send_message(
            metadata(path)
        )
        return

    if output:
        await send_file(
            update,
            output,
            f"✅ {action} انجام شد."
        )


async def pdf_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    action = context.user_data.get("pdf_action")

    if not action:
        return

    if not await check_access(update, context):
        return

    try:
        path = await download_document(update, context)

        if not path:
            return

        await process_pdf(update, context, path)

    except Exception as e:
        await update.effective_chat.send_message(
            f"❌ خطا در PDF:\n{e}"
        )


async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    action = context.user_data.get("pdf_action")
    files = context.user_data.get("pdf_files", [])

    if action not in ("merge", "images_pdf"):
        return

    if len(files) < 1:
        await update.message.reply_text("❌ هنوز فایلی دریافت نشده.")
        return

    try:
        output = new_file(".pdf")

        if action == "merge":
            merge_pdfs(files, output)
        else:
            images_to_pdf(files, output)

        await send_file(
            update,
            output,
            "✅ عملیات با موفقیت انجام شد."
        )

        context.user_data["pdf_files"] = []

    except Exception as e:
        await update.message.reply_text(
            f"❌ خطا:\n{e}"
        )


async def password_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("pdf_waiting_password"):
        return

    if not update.message or not update.message.text:
        return

    password = update.message.text.strip()
    path = context.user_data.get("pdf_pending_file")
    action = context.user_data.get("pdf_action")

    if not path:
        return

    try:
        output = new_file(".pdf")

        if action == "encrypt":
            encrypt_pdf(path, output, password)
        elif action == "decrypt":
            decrypt_pdf(path, output, password)
        else:
            return

        await send_file(
            update,
            output,
            "✅ PDF آماده شد."
        )

    except Exception as e:
        await update.effective_chat.send_message(
            f"❌ خطا:\n{e}"
        )

    finally:
        context.user_data.pop("pdf_waiting_password", None)
        context.user_data.pop("pdf_pending_file", None)


def register_pdf_handlers(app):
    app.add_handler(
        CommandHandler("done", done),
        group=2,
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            password_handler,
            block=False,
        ),
        group=2,
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            pdf_text,
            block=False,
        ),
        group=2,
    )

    app.add_handler(
        MessageHandler(
            filters.Document.PDF,
            pdf_media,
            block=False,
        ),
        group=2,
    )

    app.add_handler(
        MessageHandler(
            filters.PHOTO,
            pdf_media,
            block=False,
        ),
        group=2,
    )
