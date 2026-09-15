from pathlib import Path
import os

from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, MessageHandler, filters

from bot.services.access import check_access
from bot.labs.video.processor import (
    new_file,
    video_info,
    thumbnail,
    screenshot,
    sample_video,
    trim,
    watermark,
    process_subtitle_extract,
)


ACTIONS = {
    "ℹ️ Video Info": "info",
    "🖼️ Thumbnail": "thumbnail",
    "📸 Screenshot": "screenshot",
    "🎞️ Sample Video": "sample",
    "✂️ Trim": "trim",
    "🏷️ Watermark": "watermark",
    "💬 Subtitle Extract": "subtitle",
}


def video_menu():
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("ℹ️ Video Info"), KeyboardButton("🖼️ Thumbnail")],
            [KeyboardButton("📸 Screenshot"), KeyboardButton("🎞️ Sample Video")],
            [KeyboardButton("✂️ Trim"), KeyboardButton("🏷️ Watermark")],
            [KeyboardButton("💬 Subtitle Extract")],
            [KeyboardButton("🏠 Home")],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )


async def video_lab_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["active_lab"] = "video"
    context.user_data.pop("video_action", None)
    context.user_data.pop("video_path", None)

    await update.effective_chat.send_message(
        "🎬 Video Lab\n\n👇 یک ابزار را انتخاب کنید:",
        reply_markup=video_menu(),
    )


async def delete_selection(update):
    try:
        await update.message.delete()
    except Exception:
        pass


async def handle_video_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()

    # Top-level lab buttons belong to central router.
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

    if context.user_data.get("active_lab") != "video":
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
    if not action:
        return

    context.user_data["video_action"] = action
    await delete_selection(update)

    prompts = {
        "info": "ℹ️ ویدیو را ارسال کن:",
        "thumbnail": "🖼️ ویدیو را ارسال کن تا Thumbnail ساخته شود:",
        "screenshot": "📸 ویدیو را ارسال کن:",
        "sample": "🎞️ ویدیو را ارسال کن تا یک نمونه ۱۰ ثانیه‌ای ساخته شود:",
        "trim": (
            "✂️ ویدیو را ارسال کن.\n\n"
            "بعداً زمان شروع و مدت را به این شکل بفرست:\n"
            "`00:00:10 00:00:20`"
        ),
        "watermark": (
            "🏷️ ویدیو را ارسال کن.\n\n"
            "بعد از آن متن Watermark را بفرست."
        ),
        "subtitle": "💬 ویدیو را ارسال کن تا Subtitle آن استخراج شود:",
    }

    await update.effective_chat.send_message(prompts[action])


async def handle_video_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("active_lab") != "video":
        return

    if not context.user_data.get("video_action"):
        return

    if not update.message:
        return

    if not await check_access(update, context):
        return

    message = update.message

    if not message.video and not message.document:
        return

    if message.video:
        file_obj = await message.video.get_file()
        filename = message.video.file_name or "video.mp4"
    else:
        filename = message.document.file_name or "video.mp4"

        if not filename.lower().endswith(
            (".mp4", ".mkv", ".mov", ".avi", ".webm", ".m4v", ".3gp")
        ):
            return

        file_obj = await message.document.get_file()

    source = new_file(Path(filename).suffix or ".mp4")
    await file_obj.download_to_drive(str(source))

    context.user_data["video_path"] = str(source)

    action = context.user_data.get("video_action")

    try:
        if action == "info":
            info = await video_info(str(source))

            await update.effective_chat.send_message(
                "ℹ️ Video Info\n\n"
                f"<pre>{info}</pre>",
                parse_mode="HTML",
            )

        elif action == "thumbnail":
            output = new_file(".jpg")
            await thumbnail(str(source), str(output))

            await update.effective_chat.send_photo(
                photo=str(output),
                caption="🖼️ Thumbnail آماده شد.",
            )

        elif action == "screenshot":
            output = new_file(".jpg")
            await screenshot(str(source), str(output))

            await update.effective_chat.send_photo(
                photo=str(output),
                caption="📸 Screenshot آماده شد.",
            )

        elif action == "sample":
            output = new_file(".mp4")
            await sample_video(str(source), str(output))

            await update.effective_chat.send_video(
                video=str(output),
                caption="🎞️ Sample Video آماده شد.",
            )

        elif action == "trim":
            context.user_data["video_waiting_trim"] = True

            await update.effective_chat.send_message(
                "✂️ حالا زمان را بفرست:\n\n"
                "`شروع مدت`\n\n"
                "مثال:\n"
                "`00:00:10 00:00:20`",
                parse_mode="Markdown",
            )

        elif action == "watermark":
            context.user_data["video_waiting_watermark"] = True

            await update.effective_chat.send_message(
                "🏷️ حالا متن Watermark را بفرست:"
            )

        elif action == "subtitle":
            output = new_file(".srt")

            success = await process_subtitle_extract(
                str(source),
                str(output),
            )

            if not success or not output.exists() or output.stat().st_size == 0:
                await update.effective_chat.send_message(
                    "❌ این ویدیو Subtitle قابل استخراج ندارد."
                )
            else:
                await update.effective_chat.send_document(
                    document=str(output),
                    caption="💬 Subtitle استخراج شد.",
                )

    except Exception as e:
        await update.effective_chat.send_message(
            f"❌ خطا در پردازش ویدیو:\n{str(e)[-1500:]}"
        )

    finally:
        if action not in {"trim", "watermark"}:
            try:
                source.unlink(missing_ok=True)
            except Exception:
                pass


async def handle_video_followup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("active_lab") != "video":
        return

    if not update.message or not update.message.text:
        return

    if not await check_access(update, context):
        return

    text = update.message.text.strip()
    source = context.user_data.get("video_path")

    if not source:
        return

    if context.user_data.get("video_waiting_trim"):
        parts = text.split()

        if len(parts) != 2:
            await update.effective_chat.send_message(
                "❌ فرمت اشتباه است.\nمثال:\n`00:00:10 00:00:20`",
                parse_mode="Markdown",
            )
            return

        start, duration = parts

        try:
            output = new_file(".mp4")
            await trim(source, str(output), start, duration)

            await update.effective_chat.send_video(
                video=str(output),
                caption="✂️ ویدیو برش خورد.",
            )

            context.user_data.pop("video_waiting_trim", None)
            Path(source).unlink(missing_ok=True)
            context.user_data.pop("video_path", None)

        except Exception as e:
            await update.effective_chat.send_message(
                f"❌ خطا:\n{str(e)[-1200:]}"
            )

        return

    if context.user_data.get("video_waiting_watermark"):
        try:
            output = new_file(".mp4")
            await watermark(source, str(output), text)

            await update.effective_chat.send_video(
                video=str(output),
                caption="🏷️ Watermark اضافه شد.",
            )

            context.user_data.pop("video_waiting_watermark", None)
            Path(source).unlink(missing_ok=True)
            context.user_data.pop("video_path", None)

        except Exception as e:
            await update.effective_chat.send_message(
                f"❌ خطا:\n{str(e)[-1200:]}"
            )

        return


def register_video_handlers(application):
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_video_text,
        ),
        group=6,
    )

    application.add_handler(
        MessageHandler(
            filters.VIDEO | filters.Document.VIDEO,
            handle_video_media,
        ),
        group=6,
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_video_followup,
        ),
        group=6,
    )
