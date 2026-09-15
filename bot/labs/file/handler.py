from pathlib import Path
import os
import shutil
import zipfile

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, MessageHandler, filters

from bot.services.access import check_access
from .processor import (
    file_info,
    md5,
    sha256,
    create_zip,
    extract_zip,
    inspect_zip,
    rename_file,
    analyze_file,
)


MENU_BUTTONS = [
    ["📄 File Info", "🔐 MD5"],
    ["🔒 SHA-256", "🧪 File Analyzer"],
    ["📦 Create ZIP", "📂 Extract ZIP"],
    ["📋 ZIP Contents", "✏️ Rename File"],
    ["🏠 Home"],
]

MENU_SET = {item for row in MENU_BUTTONS for item in row}


def file_menu():
    return ReplyKeyboardMarkup(
        [[KeyboardButton(x) for x in row] for row in MENU_BUTTONS],
        resize_keyboard=True,
        is_persistent=True,
    )


async def delete_message(update):
    try:
        await update.message.delete()
    except Exception:
        pass


async def file_lab_menu(update, context):
    if not await check_access(update, context):
        return

    context.user_data.pop("file_action", None)

    await delete_message(update)

    await update.effective_chat.send_message(
        "📦 File Lab\n\n"
        "ابزار موردنظرت رو انتخاب کن 👇",
        reply_markup=file_menu(),
    )


async def handle_file_lab(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()

    if text == "📦 File Lab":
        await file_lab_menu(update, context)
        return

    if text not in MENU_SET:
        return

    if text == "🏠 Home":
        from bot.menu import main_menu

        context.user_data.pop("file_action", None)

        await delete_message(update)

        await update.effective_chat.send_message(
            "🧰 TOOL BOX\n\n"
            "👇 یک بخش را انتخاب کنید:",
            reply_markup=main_menu(),
        )
        return

    if not await check_access(update, context):
        return

    context.user_data["file_action"] = text

    await delete_message(update)

    prompts = {
        "📄 File Info": "📄 فایل موردنظر رو ارسال کن:",
        "🔐 MD5": "🔐 فایل رو ارسال کن تا MD5 محاسبه بشه:",
        "🔒 SHA-256": "🔒 فایل رو ارسال کن تا SHA-256 محاسبه بشه:",
        "🧪 File Analyzer": "🧪 فایل رو ارسال کن:",
        "📦 Create ZIP": "📦 فایل‌هایی که می‌خوای داخل ZIP قرار بگیرن رو یکی‌یکی ارسال کن.\n\nوقتی تمام شد بنویس: DONE",
        "📂 Extract ZIP": "📂 فایل ZIP رو ارسال کن:",
        "📋 ZIP Contents": "📋 فایل ZIP رو ارسال کن:",
        "✏️ Rename File": "✏️ اول فایل رو ارسال کن، سپس نام جدید رو بفرست.",
    }

    await update.effective_chat.send_message(
        prompts.get(text, "📄 فایل رو ارسال کن:")
    )


async def receive_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    action = context.user_data.get("file_action")

    if not action:
        return

    if not await check_access(update, context):
        return

    message = update.message

    # ZIP creation
    if action == "📦 Create ZIP":
        if message.text and message.text.strip().upper() == "DONE":
            files = context.user_data.get("zip_files", [])

            if not files:
                await message.reply_text("❌ هنوز فایلی ارسال نکردی.")
                return

            output = Path("temp") / f"toolbox_{update.effective_user.id}.zip"
            output.parent.mkdir(parents=True, exist_ok=True)

            try:
                create_zip(files, output)

                with open(output, "rb") as f:
                    await message.reply_document(
                        document=f,
                        caption="📦 ZIP ساخته شد."
                    )

            except Exception as e:
                await message.reply_text(f"❌ خطا:\n{e}")

            finally:
                context.user_data.pop("zip_files", None)
                context.user_data.pop("file_action", None)

            return

        path = await download_message_file(message)

        if path:
            context.user_data.setdefault("zip_files", []).append(path)

            await delete_message(update)

            await update.effective_chat.send_message(
                "✅ فایل اضافه شد.\n"
                "فایل بعدی رو ارسال کن یا بنویس DONE."
            )

        return

    # Other operations need a file
    path = await download_message_file(message)

    if not path:
        # Rename second step
        if action == "✏️ Rename File" and message.text:
            old = context.user_data.get("rename_file")

            if old:
                try:
                    new_path = rename_file(old, message.text.strip())

                    with open(new_path, "rb") as f:
                        await update.effective_chat.send_document(
                            document=f,
                            caption=f"✏️ نام فایل تغییر کرد:\n{Path(new_path).name}"
                        )

                    context.user_data.pop("rename_file", None)
                    context.user_data.pop("file_action", None)

                except Exception as e:
                    await message.reply_text(f"❌ خطا:\n{e}")

            return

        await message.reply_text("❌ لطفاً فایل را ارسال کن.")
        return

    try:
        if action == "📄 File Info":
            info = file_info(path)

            await message.reply_text(
                "📄 File Info\n\n"
                f"Name: {info['name']}\n"
                f"Size: {info['size_text']}\n"
                f"Extension: {info['extension']}\n"
                f"MIME: {info['mime']}"
            )

        elif action == "🔐 MD5":
            await message.reply_text(
                f"🔐 MD5\n\n`{md5(path)}`",
                parse_mode="Markdown"
            )

        elif action == "🔒 SHA-256":
            await message.reply_text(
                f"🔒 SHA-256\n\n`{sha256(path)}`",
                parse_mode="Markdown"
            )

        elif action == "🧪 File Analyzer":
            info = analyze_file(path)

            await message.reply_text(
                "🧪 File Analyzer\n\n"
                f"📄 Name: {info['name']}\n"
                f"📦 Size: {info['size']}\n"
                f"🔤 Extension: {info['extension']}\n"
                f"🧬 MIME: {info['mime']}\n\n"
                f"🔐 MD5:\n{info['md5']}\n\n"
                f"🔒 SHA-256:\n{info['sha256']}"
            )

        elif action == "📂 Extract ZIP":
            output_dir = Path("temp") / f"extract_{update.effective_user.id}"

            extract_zip(path, output_dir)

            archive = shutil.make_archive(
                str(output_dir),
                "zip",
                output_dir
            )

            with open(archive, "rb") as f:
                await message.reply_document(
                    document=f,
                    caption="📂 فایل ZIP استخراج شد."
                )

        elif action == "📋 ZIP Contents":
            files = inspect_zip(path)

            if not files:
                result = "📋 ZIP خالی است."
            else:
                result = "📋 ZIP Contents\n\n" + "\n".join(
                    f"{i + 1}. {name}"
                    for i, name in enumerate(files[:300])
                )

                if len(files) > 300:
                    result += f"\n\n... و {len(files) - 300} فایل دیگر"

            await message.reply_text(result)

        elif action == "✏️ Rename File":
            context.user_data["rename_file"] = path

            await message.reply_text(
                "✏️ فایل دریافت شد.\n\n"
                "نام جدید فایل را ارسال کن:"
            )
            return

        context.user_data.pop("file_action", None)

    except Exception as e:
        print("FILE LAB ERROR:", repr(e))
        await message.reply_text(
            f"❌ خطا در پردازش:\n{e}"
        )


async def download_message_file(message):
    file_obj = None
    filename = None

    if message.document:
        file_obj = await message.document.get_file()
        filename = message.document.file_name or "file"

    elif message.audio:
        file_obj = await message.audio.get_file()
        filename = message.audio.file_name or "audio"

    elif message.video:
        file_obj = await message.video.get_file()
        filename = message.video.file_name or "video.mp4"

    elif message.voice:
        file_obj = await message.voice.get_file()
        filename = "voice.ogg"

    elif message.photo:
        file_obj = await message.photo[-1].get_file()
        filename = "photo.jpg"

    if not file_obj:
        return None

    user_id = message.from_user.id

    safe_name = Path(filename).name
    output = Path("temp") / f"{user_id}_{safe_name}"
    output.parent.mkdir(parents=True, exist_ok=True)

    await file_obj.download_to_drive(str(output))

    return str(output)


def register_file_handlers(app):
    app.add_handler(
        MessageHandler(
            filters.ALL,
            receive_file,
        ),
        group=5,
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_file_lab,
        ),
        group=5,
    )
