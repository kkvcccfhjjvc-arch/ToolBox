from pathlib import Path
import shutil

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

MENU_SET = {x for row in MENU_BUTTONS for x in row}


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
    context.user_data.pop("zip_files", None)
    context.user_data.pop("rename_file", None)

    await delete_message(update)

    await update.effective_chat.send_message(
        "📦 File Lab\n\n"
        "ابزار موردنظرت رو انتخاب کن 👇",
        reply_markup=file_menu(),
    )


async def download_file(message):
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

    safe_name = Path(filename).name
    user_id = message.from_user.id

    output = Path("temp") / f"{user_id}_{safe_name}"
    output.parent.mkdir(parents=True, exist_ok=True)

    await file_obj.download_to_drive(str(output))

    return str(output)


async def handle_file_lab(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    message = update.message
    text = message.text.strip() if message.text else ""

    # ورود به File Lab
    if text == "📦 File Lab":
        await file_lab_menu(update, context)
        return

    # Home
    if text == "🏠 Home":
        from bot.menu import main_menu

        context.user_data.pop("file_action", None)
        context.user_data.pop("zip_files", None)
        context.user_data.pop("rename_file", None)

        await delete_message(update)

        await update.effective_chat.send_message(
            "🧰 TOOL BOX\n\n"
            "👇 یک بخش را انتخاب کنید:",
            reply_markup=main_menu(),
        )
        return

    # انتخاب ابزار
    if text in MENU_SET:
        if not await check_access(update, context):
            return

        context.user_data["file_action"] = text
        context.user_data.pop("rename_file", None)

        await delete_message(update)

        prompts = {
            "📄 File Info": "📄 فایل موردنظر رو ارسال کن:",
            "🔐 MD5": "🔐 فایل رو ارسال کن:",
            "🔒 SHA-256": "🔒 فایل رو ارسال کن:",
            "🧪 File Analyzer": "🧪 فایل رو ارسال کن:",
            "📦 Create ZIP":
                "📦 فایل‌ها رو یکی‌یکی ارسال کن.\n\n"
                "وقتی تمام شد بنویس: DONE",
            "📂 Extract ZIP": "📂 فایل ZIP رو ارسال کن:",
            "📋 ZIP Contents": "📋 فایل ZIP رو ارسال کن:",
            "✏️ Rename File":
                "✏️ فایل رو ارسال کن.\n\n"
                "بعدش نام جدید رو بفرست.",
        }

        await update.effective_chat.send_message(
            prompts[text]
        )
        return

    # اگر هیچ عملیات فعالی نداریم
    action = context.user_data.get("file_action")

    if not action:
        return

    if not await check_access(update, context):
        return

    # -------------------------
    # CREATE ZIP
    # -------------------------
    if action == "📦 Create ZIP":

        if text.upper() == "DONE":
            files = context.user_data.get("zip_files", [])

            if not files:
                await message.reply_text(
                    "❌ هنوز فایلی ارسال نکردی."
                )
                return

            output = Path("temp") / (
                f"toolbox_{update.effective_user.id}.zip"
            )

            try:
                create_zip(files, output)

                with open(output, "rb") as f:
                    await message.reply_document(
                        document=f,
                        caption="📦 ZIP با موفقیت ساخته شد."
                    )

            except Exception as e:
                await message.reply_text(
                    f"❌ خطا:\n{e}"
                )

            context.user_data.pop("file_action", None)
            context.user_data.pop("zip_files", None)
            return

        path = await download_file(message)

        if not path:
            await message.reply_text(
                "❌ لطفاً یک فایل ارسال کن."
            )
            return

        context.user_data.setdefault(
            "zip_files", []
        ).append(path)

        await delete_message(update)

        await update.effective_chat.send_message(
            "✅ فایل اضافه شد.\n\n"
            "فایل بعدی رو بفرست یا بنویس DONE."
        )
        return

    # -------------------------
    # RENAME - STEP 2
    # -------------------------
    if action == "✏️ Rename File":

        old_file = context.user_data.get("rename_file")

        if old_file and text:
            try:
                new_path = rename_file(
                    old_file,
                    text
                )

                with open(new_path, "rb") as f:
                    await message.reply_document(
                        document=f,
                        caption=(
                            "✏️ نام فایل تغییر کرد.\n\n"
                            f"📄 {Path(new_path).name}"
                        )
                    )

                context.user_data.pop(
                    "rename_file",
                    None
                )
                context.user_data.pop(
                    "file_action",
                    None
                )

            except Exception as e:
                await message.reply_text(
                    f"❌ خطا:\n{e}"
                )

            return

    # -------------------------
    # FILE OPERATIONS
    # -------------------------
    path = await download_file(message)

    if not path:
        await message.reply_text(
            "❌ لطفاً فایل را ارسال کن."
        )
        return

    try:

        if action == "📄 File Info":

            info = file_info(path)

            await message.reply_text(
                "📄 File Info\n\n"
                f"📌 Name: {info['name']}\n"
                f"📦 Size: {info['size_text']}\n"
                f"🔤 Extension: {info['extension']}\n"
                f"🧬 MIME: {info['mime']}"
            )

        elif action == "🔐 MD5":

            await message.reply_text(
                "🔐 MD5\n\n"
                f"`{md5(path)}`",
                parse_mode="Markdown"
            )

        elif action == "🔒 SHA-256":

            await message.reply_text(
                "🔒 SHA-256\n\n"
                f"`{sha256(path)}`",
                parse_mode="Markdown"
            )

        elif action == "🧪 File Analyzer":

            info = analyze_file(path)

            await message.reply_text(
                "🧪 File Analyzer\n\n"
                f"📌 Name: {info['name']}\n"
                f"📦 Size: {info['size']}\n"
                f"🔤 Extension: {info['extension']}\n"
                f"🧬 MIME: {info['mime']}\n\n"
                f"🔐 MD5:\n{info['md5']}\n\n"
                f"🔒 SHA-256:\n{info['sha256']}"
            )

        elif action == "📂 Extract ZIP":

            output_dir = (
                Path("temp")
                / f"extract_{update.effective_user.id}"
            )

            extract_zip(
                path,
                output_dir
            )

            archive = shutil.make_archive(
                str(output_dir),
                "zip",
                output_dir
            )

            with open(archive, "rb") as f:
                await message.reply_document(
                    document=f,
                    caption="📂 ZIP استخراج شد."
                )

        elif action == "📋 ZIP Contents":

            files = inspect_zip(path)

            if not files:
                result = "📋 ZIP خالی است."
            else:
                result = (
                    "📋 ZIP Contents\n\n"
                    + "\n".join(
                        f"{i + 1}. {name}"
                        for i, name in enumerate(files[:300])
                    )
                )

                if len(files) > 300:
                    result += (
                        f"\n\n... و "
                        f"{len(files) - 300} فایل دیگر"
                    )

            await message.reply_text(result)

        elif action == "✏️ Rename File":

            context.user_data["rename_file"] = path

            await message.reply_text(
                "✅ فایل دریافت شد.\n\n"
                "حالا نام جدید فایل را ارسال کن.\n"
                "مثال:\n"
                "new_file.pdf"
            )

            return

        context.user_data.pop("file_action", None)

    except Exception as e:

        print(
            "FILE LAB ERROR:",
            repr(e)
        )

        await message.reply_text(
            f"❌ خطا در پردازش:\n{e}"
        )


def register_file_handlers(app):

    app.add_handler(
        MessageHandler(
            filters.ALL,
            handle_file_lab,
        ),
        group=5,
    )
