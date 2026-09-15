import os
import asyncio
from pathlib import Path

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, MessageHandler, CommandHandler, filters

from bot.services.access import check_access
from .processor import (
    images_to_pdf,
    pdf_to_text,
    merge_pdfs,
    split_pdf,
    compress_pdf,
    ocr_pdf,
    encrypt_pdf,
    decrypt_pdf,
    watermark_pdf,
    rotate_pdf,
    crop_pdf,
    extract_images,
    pdf_to_images,
    get_metadata,
)


TEMP_DIR = Path("temp/pdf")
TEMP_DIR.mkdir(parents=True, exist_ok=True)


def pdf_menu_keyboard():
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("🖼️ Images → PDF"), KeyboardButton("📝 PDF → Text")],
            [KeyboardButton("🔗 Merge PDF"), KeyboardButton("✂️ Split PDF")],
            [KeyboardButton("🗜 Compress PDF"), KeyboardButton("🔍 OCR PDF")],
            [KeyboardButton("🔐 Encrypt PDF"), KeyboardButton("🔓 Decrypt PDF")],
            [KeyboardButton("💧 Watermark PDF"), KeyboardButton("🔄 Rotate PDF")],
            [KeyboardButton("✂️ Crop PDF"), KeyboardButton("🖼 Extract Images")],
            [KeyboardButton("📸 PDF → Images"), KeyboardButton("ℹ️ PDF Metadata")],
            [KeyboardButton("🏠 Home")],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )


PDF_ACTIONS = {
    "🖼️ Images → PDF": "images_to_pdf",
    "📝 PDF → Text": "pdf_to_text",
    "🔗 Merge PDF": "merge",
    "✂️ Split PDF": "split",
    "🗜 Compress PDF": "compress",
    "🔍 OCR PDF": "ocr",
    "🔐 Encrypt PDF": "encrypt",
    "🔓 Decrypt PDF": "decrypt",
    "💧 Watermark PDF": "watermark",
    "🔄 Rotate PDF": "rotate",
    "✂️ Crop PDF": "crop",
    "🖼 Extract Images": "extract_images",
    "📸 PDF → Images": "pdf_to_images",
    "ℹ️ PDF Metadata": "metadata",
}


async def delete_message(update):
    try:
        if update.message:
            await update.message.delete()
    except Exception:
        pass


async def image_to_pdf_start(update, context):
    context.user_data.clear()
    context.user_data["pdf_action"] = "images_to_pdf"
    context.user_data["pdf_files"] = []

    await update.message.reply_text(
        "🖼️ Images → PDF\n\n"
        "عکس‌ها را یکی‌یکی ارسال کن.\n"
        "بعد از ارسال همه عکس‌ها، /done را بزن."
    )


async def pdf_action_start(update, context):
    if not update.message:
        return

    text = update.message.text

    if text == "🏠 Home":
        context.user_data.clear()

        from bot.menu import main_menu
        await update.message.reply_text(
            "🏠 منوی اصلی:",
            reply_markup=main_menu()
        )
        return

    action = PDF_ACTIONS.get(text)

    if not action:
        return

    await delete_message(update)

    if action == "images_to_pdf":
        context.user_data.clear()
        context.user_data["pdf_action"] = "images_to_pdf"
        context.user_data["pdf_files"] = []

        await update.effective_chat.send_message(
            "🖼️ Images → PDF\n\n"
            "عکس‌ها را ارسال کن.\n"
            "برای پایان /done را بزن."
        )
        return

    context.user_data.clear()
    context.user_data["pdf_action"] = action

    messages = {
        "pdf_to_text": "📝 PDF → Text\n\nیک فایل PDF ارسال کن.",
        "merge": "🔗 Merge PDF\n\nPDFها را یکی‌یکی ارسال کن و در پایان /done بزن.",
        "split": "✂️ Split PDF\n\nیک فایل PDF ارسال کن.",
        "compress": "🗜 Compress PDF\n\nیک فایل PDF ارسال کن.",
        "ocr": "🔍 OCR PDF\n\nیک فایل PDF ارسال کن.",
        "encrypt": "🔐 Encrypt PDF\n\nیک فایل PDF ارسال کن.",
        "decrypt": "🔓 Decrypt PDF\n\nیک فایل PDF ارسال کن.",
        "watermark": "💧 Watermark PDF\n\nیک فایل PDF ارسال کن.",
        "rotate": "🔄 Rotate PDF\n\nیک فایل PDF ارسال کن.",
        "crop": "✂️ Crop PDF\n\nیک فایل PDF ارسال کن.",
        "extract_images": "🖼 Extract Images\n\nیک فایل PDF ارسال کن.",
        "pdf_to_images": "📸 PDF → Images\n\nیک فایل PDF ارسال کن.",
        "metadata": "ℹ️ PDF Metadata\n\nیک فایل PDF ارسال کن.",
    }

    await update.effective_chat.send_message(
        messages.get(action, "یک فایل PDF ارسال کن.")
    )


async def pdf_document_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.document:
        return

    action = context.user_data.get("pdf_action")

    if not action:
        return

    if not await check_access(update, context):
        return

    document = update.message.document

    if document.file_size and document.file_size > 45 * 1024 * 1024:
        await update.message.reply_text("❌ حجم فایل بیشتر از 45MB است.")
        return

    filename = document.file_name or "input.pdf"
    ext = Path(filename).suffix.lower()

    if action != "images_to_pdf" and ext != ".pdf":
        await update.message.reply_text("❌ لطفاً فایل PDF ارسال کن.")
        return

    await update.message.reply_text("⏳ در حال پردازش...")

    try:
        tg_file = await context.bot.get_file(document.file_id)

        input_path = TEMP_DIR / f"{update.effective_user.id}_input{ext or '.pdf'}"

        data = await tg_file.download_as_bytearray()

        with open(input_path, "wb") as f:
            f.write(data)

        if action == "merge":
            files = context.user_data.setdefault("pdf_files", [])
            files.append(str(input_path))

            await update.message.reply_text(
                f"✅ PDF شماره {len(files)} اضافه شد.\n\n"
                "PDF بعدی را بفرست یا /done را بزن."
            )
            return

        output = TEMP_DIR / f"{update.effective_user.id}_output"

        if action == "pdf_to_text":
            output = output.with_suffix(".txt")
            result = pdf_to_text(str(input_path), str(output))

            await update.message.reply_document(
                document=open(result, "rb"),
                caption="✅ متن PDF آماده شد."
            )

        elif action == "compress":
            output = output.with_suffix(".pdf")
            result = compress_pdf(str(input_path), str(output))

            await update.message.reply_document(
                document=open(result, "rb"),
                caption="✅ PDF فشرده شد."
            )

        elif action == "ocr":
            output = output.with_suffix(".pdf")
            result = ocr_pdf(str(input_path), str(output))

            await update.message.reply_document(
                document=open(result, "rb"),
                caption="✅ OCR انجام شد."
            )

        elif action == "split":
            results = split_pdf(str(input_path), str(TEMP_DIR))

            for file in results:
                await update.message.reply_document(
                    document=open(file, "rb")
                )

        elif action == "metadata":
            result = get_metadata(str(input_path))

            text = "ℹ️ PDF Metadata\n\n"
            for key, value in result.items():
                text += f"• {key}: {value}\n"

            await update.message.reply_text(text)

        elif action == "pdf_to_images":
            results = pdf_to_images(str(input_path), str(TEMP_DIR))

            for file in results:
                await update.message.reply_document(
                    document=open(file, "rb")
                )

        elif action == "extract_images":
            results = extract_images(str(input_path), str(TEMP_DIR))

            if not results:
                await update.message.reply_text(
                    "⚠️ تصویری داخل PDF پیدا نشد."
                )
            else:
                for file in results:
                    await update.message.reply_document(
                        document=open(file, "rb")
                    )

        else:
            await update.message.reply_text(
                "⚠️ این قابلیت فعلاً نیاز به اطلاعات بیشتری دارد."
            )

        context.user_data.clear()

    except Exception as e:
        print("PDF ERROR:", repr(e))
        await update.message.reply_text(
            f"❌ پردازش PDF انجام نشد.\n\n`{e}`"
        )
        context.user_data.clear()


async def done_command(update, context):
    action = context.user_data.get("pdf_action")

    if action != "merge":
        if action == "images_to_pdf":
            await update.message.reply_text(
                "⚠️ برای Images → PDF فعلاً باید حداقل یک عکس ارسال شده باشد."
            )
        return

    files = context.user_data.get("pdf_files", [])

    if len(files) < 2:
        await update.message.reply_text(
            "❌ برای Merge حداقل ۲ فایل PDF لازم است."
        )
        return

    try:
        await update.message.reply_text("⏳ در حال ادغام PDFها...")

        output = TEMP_DIR / f"{update.effective_user.id}_merged.pdf"

        result = merge_pdfs(files, str(output))

        await update.message.reply_document(
            document=open(result, "rb"),
            caption="✅ PDFها با موفقیت ادغام شدند."
        )

    except Exception as e:
        print("PDF MERGE ERROR:", repr(e))
        await update.message.reply_text(
            f"❌ Merge انجام نشد.\n\n`{e}`"
        )

    finally:
        context.user_data.clear()


async def pdf_menu(update, context):
    if not await check_access(update, context):
        return

    await delete_message(update)

    await update.effective_chat.send_message(
        "📄 PDF Lab\n\n"
        "یکی از ابزارهای زیر را انتخاب کن:",
        reply_markup=pdf_menu_keyboard()
    )


def register_pdf_handlers(app):

    # PDF menu buttons
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            pdf_action_start
        ),
        group=3
    )

    # PDF files
    app.add_handler(
        MessageHandler(
            filters.Document.PDF,
            pdf_document_handler
        ),
        group=2
    )

    # Done
    app.add_handler(
        CommandHandler("done", done_command),
        group=2
    )
