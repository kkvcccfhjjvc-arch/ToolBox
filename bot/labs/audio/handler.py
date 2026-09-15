import os
import uuid

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, MessageHandler, ContextTypes, filters

from .processor import (
    convert,
    cut,
    merge,
    speed,
    change_volume,
    pitch,
    silence_remove,
    reverse,
    waveform,
    spectrogram,
    compress,
    extract_audio,
    ffprobe,
)

TMP = os.path.expanduser("~/ToolBox/temp")
os.makedirs(TMP, exist_ok=True)

MAX_SIZE = 50 * 1024 * 1024


def audio_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎙️ Voice", callback_data="audio_voice"),
            InlineKeyboardButton("🔄 Convert", callback_data="audio_convert"),
        ],
        [
            InlineKeyboardButton("✂️ Cut", callback_data="audio_cut"),
            InlineKeyboardButton("🔗 Merge", callback_data="audio_merge"),
        ],
        [
            InlineKeyboardButton("⏩ Speed", callback_data="audio_speed"),
            InlineKeyboardButton("🔊 Volume", callback_data="audio_volume"),
        ],
        [
            InlineKeyboardButton("🎵 Pitch", callback_data="audio_pitch"),
            InlineKeyboardButton("🔇 Silence", callback_data="audio_silence"),
        ],
        [
            InlineKeyboardButton("↩️ Reverse", callback_data="audio_reverse"),
            InlineKeyboardButton("📦 Compress", callback_data="audio_compress"),
        ],
        [
            InlineKeyboardButton("〰️ Waveform", callback_data="audio_waveform"),
            InlineKeyboardButton("📊 Spectrogram", callback_data="audio_spectrogram"),
        ],
        [
            InlineKeyboardButton("🎬 Extract Audio", callback_data="audio_extract"),
            InlineKeyboardButton("ℹ️ File Info", callback_data="audio_info"),
        ],
        [
            InlineKeyboardButton("🏷️ Metadata", callback_data="audio_metadata"),
        ],
        [
            InlineKeyboardButton("🔙 منوی اصلی", callback_data="back_main"),
        ],
    ])


def back_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Audio Lab", callback_data="lab_audio")],
        [InlineKeyboardButton("🏠 منوی اصلی", callback_data="back_main")],
    ])


def format_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("MP3", callback_data="audio_format_mp3"),
            InlineKeyboardButton("WAV", callback_data="audio_format_wav"),
        ],
        [
            InlineKeyboardButton("OGG", callback_data="audio_format_ogg"),
            InlineKeyboardButton("FLAC", callback_data="audio_format_flac"),
        ],
        [
            InlineKeyboardButton("M4A", callback_data="audio_format_m4a"),
        ],
        [
            InlineKeyboardButton("🔙 Audio Lab", callback_data="lab_audio"),
        ],
    ])


def speed_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("0.5x", callback_data="audio_speed_value_0.5"),
            InlineKeyboardButton("0.75x", callback_data="audio_speed_value_0.75"),
        ],
        [
            InlineKeyboardButton("1.25x", callback_data="audio_speed_value_1.25"),
            InlineKeyboardButton("1.5x", callback_data="audio_speed_value_1.5"),
        ],
        [
            InlineKeyboardButton("2x", callback_data="audio_speed_value_2"),
        ],
        [
            InlineKeyboardButton("🔙 Audio Lab", callback_data="lab_audio"),
        ],
    ])


def volume_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("50%", callback_data="audio_volume_value_0.5"),
            InlineKeyboardButton("75%", callback_data="audio_volume_value_0.75"),
        ],
        [
            InlineKeyboardButton("100%", callback_data="audio_volume_value_1"),
            InlineKeyboardButton("125%", callback_data="audio_volume_value_1.25"),
        ],
        [
            InlineKeyboardButton("150%", callback_data="audio_volume_value_1.5"),
            InlineKeyboardButton("200%", callback_data="audio_volume_value_2"),
        ],
        [
            InlineKeyboardButton("🔙 Audio Lab", callback_data="lab_audio"),
        ],
    ])


def pitch_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("-2", callback_data="audio_pitch_value_-2"),
            InlineKeyboardButton("-1", callback_data="audio_pitch_value_-1"),
        ],
        [
            InlineKeyboardButton("0", callback_data="audio_pitch_value_0"),
            InlineKeyboardButton("+1", callback_data="audio_pitch_value_1"),
        ],
        [
            InlineKeyboardButton("+2", callback_data="audio_pitch_value_2"),
        ],
        [
            InlineKeyboardButton("🔙 Audio Lab", callback_data="lab_audio"),
        ],
    ])


async def download_media(message):
    media = (
        message.audio
        or message.voice
        or message.video
        or message.document
    )

    if not media:
        return None

    size = getattr(media, "file_size", 0) or 0

    if size > MAX_SIZE:
        await message.reply_text("❌ حجم فایل بیشتر از 50MB است.")
        return None

    tg_file = await media.get_file()

    filename = getattr(media, "file_name", None)
    ext = ".bin"

    if filename and "." in filename:
        ext = "." + filename.rsplit(".", 1)[1].lower()

    path = os.path.join(
        TMP,
        f"{uuid.uuid4().hex}{ext}"
    )

    await tg_file.download_to_drive(path)

    return path


async def send_result(chat, path, caption=None, voice=False):
    try:
        if voice:
            with open(path, "rb") as f:
                await chat.send_voice(voice=f, caption=caption)

        elif path.endswith(".png"):
            with open(path, "rb") as f:
                await chat.send_photo(photo=f, caption=caption)

        else:
            with open(path, "rb") as f:
                await chat.send_document(
                    document=f,
                    caption=caption
                )
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


async def audio_callback(update, context):
    q = update.callback_query
    await q.answer()

    data = q.data

    if data == "lab_audio":
        context.user_data.clear()

        await q.edit_message_text(
            "🎛️ Audio Lab\n\n"
            "ابزار موردنظر را انتخاب کنید:",
            reply_markup=audio_menu()
        )
        return

    if data == "audio_convert":
        await q.edit_message_text(
            "🔄 فرمت خروجی را انتخاب کنید:",
            reply_markup=format_menu()
        )
        return

    if data.startswith("audio_format_"):
        fmt = data.replace("audio_format_", "")

        context.user_data["audio_operation"] = "convert"
        context.user_data["audio_format"] = "." + fmt

        await q.edit_message_text(
            f"🔄 تبدیل به {fmt.upper()}\n\n"
            "📤 فایل را ارسال کنید.",
            reply_markup=back_buttons()
        )
        return

    if data == "audio_speed":
        await q.edit_message_text(
            "⏩ سرعت را انتخاب کنید:",
            reply_markup=speed_menu()
        )
        return

    if data.startswith("audio_speed_value_"):
        value = float(data.replace("audio_speed_value_", ""))

        context.user_data["audio_operation"] = "speed"
        context.user_data["audio_value"] = value

        await q.edit_message_text(
            f"⏩ سرعت: {value}x\n\n"
            "📤 فایل صوتی را ارسال کنید.",
            reply_markup=back_buttons()
        )
        return

    if data == "audio_volume":
        await q.edit_message_text(
            "🔊 میزان صدا را انتخاب کنید:",
            reply_markup=volume_menu()
        )
        return

    if data.startswith("audio_volume_value_"):
        value = float(data.replace("audio_volume_value_", ""))

        context.user_data["audio_operation"] = "volume"
        context.user_data["audio_value"] = value

        await q.edit_message_text(
            f"🔊 Volume: {int(value * 100)}%\n\n"
            "📤 فایل صوتی را ارسال کنید.",
            reply_markup=back_buttons()
        )
        return

    if data == "audio_pitch":
        await q.edit_message_text(
            "🎵 Pitch را انتخاب کنید:",
            reply_markup=pitch_menu()
        )
        return

    if data.startswith("audio_pitch_value_"):
        value = float(data.replace("audio_pitch_value_", ""))

        context.user_data["audio_operation"] = "pitch"
        context.user_data["audio_value"] = value

        await q.edit_message_text(
            f"🎵 Pitch: {value:+g}\n\n"
            "📤 فایل صوتی را ارسال کنید.",
            reply_markup=back_buttons()
        )
        return

    actions = {
        "audio_voice": ("voice", "🎙️ فایل صوتی را ارسال کنید."),
        "audio_cut": ("cut", "✂️ فایل صوتی را ارسال کنید."),
        "audio_merge": ("merge", "🔗 فایل‌های صوتی را ارسال کنید."),
        "audio_silence": ("silence", "🔇 فایل صوتی را ارسال کنید."),
        "audio_reverse": ("reverse", "↩️ فایل صوتی را ارسال کنید."),
        "audio_compress": ("compress", "📦 فایل صوتی را ارسال کنید."),
        "audio_waveform": ("waveform", "〰️ فایل صوتی را ارسال کنید."),
        "audio_spectrogram": ("spectrogram", "📊 فایل صوتی را ارسال کنید."),
        "audio_extract": ("extract", "🎬 فایل ویدئویی را ارسال کنید."),
        "audio_info": ("info", "ℹ️ فایل را ارسال کنید."),
        "audio_metadata": ("metadata", "🏷️ فایل صوتی را ارسال کنید."),
    }

    if data in actions:
        operation, text = actions[data]

        context.user_data["audio_operation"] = operation

        if operation == "merge":
            context.user_data["audio_merge_files"] = []

        await q.edit_message_text(
            text,
            reply_markup=back_buttons()
        )


async def audio_media_handler(update, context):
    operation = context.user_data.get("audio_operation")

    if not operation:
        return

    message = update.message

    if operation == "merge":
        path = await download_media(message)

        if not path:
            return

        files = context.user_data.setdefault(
            "audio_merge_files", []
        )

        files.append(path)

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "✅ پایان و ادغام",
                    callback_data="audio_merge_done"
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 Audio Lab",
                    callback_data="lab_audio"
                )
            ],
        ])

        await message.reply_text(
            f"✅ فایل {len(files)} دریافت شد.\n"
            "فایل بعدی را بفرستید یا پایان را بزنید.",
            reply_markup=keyboard
        )

        return

    path = await download_media(message)

    if not path:
        return

    try:
        status = await message.reply_text("⏳ در حال پردازش...")

        if operation == "voice":
            output = await convert(path, ".ogg")
            await status.delete()
            await send_result(
                message.chat,
                output,
                "🎙️ Telegram Voice آماده شد.",
                True
            )

        elif operation == "convert":
            output = await convert(
                path,
                context.user_data["audio_format"]
            )

            await status.delete()

            await send_result(
                message.chat,
                output,
                "🔄 تبدیل فرمت انجام شد."
            )

        elif operation == "speed":
            output = await speed(
                path,
                context.user_data["audio_value"]
            )

            await status.delete()

            await send_result(
                message.chat,
                output,
                "⏩ سرعت تغییر کرد."
            )

        elif operation == "volume":
            output = await change_volume(
                path,
                context.user_data["audio_value"]
            )

            await status.delete()

            await send_result(
                message.chat,
                output,
                "🔊 Volume تغییر کرد."
            )

        elif operation == "pitch":
            output = await pitch(
                path,
                context.user_data["audio_value"]
            )

            await status.delete()

            await send_result(
                message.chat,
                output,
                "🎵 Pitch تغییر کرد."
            )

        elif operation == "silence":
            output = await silence_remove(path)
            await status.delete()
            await send_result(
                message.chat,
                output,
                "🔇 سکوت‌ها حذف شدند."
            )

        elif operation == "reverse":
            output = await reverse(path)
            await status.delete()
            await send_result(
                message.chat,
                output,
                "↩️ Reverse انجام شد."
            )

        elif operation == "compress":
            output = await compress(path)
            await status.delete()
            await send_result(
                message.chat,
                output,
                "📦 فشرده‌سازی انجام شد."
            )

        elif operation == "waveform":
            output = await waveform(path)
            await status.delete()
            await send_result(
                message.chat,
                output,
                "〰️ Waveform"
            )

        elif operation == "spectrogram":
            output = await spectrogram(path)
            await status.delete()
            await send_result(
                message.chat,
                output,
                "📊 Spectrogram"
            )

        elif operation == "extract":
            output = await extract_audio(path)
            await status.delete()
            await send_result(
                message.chat,
                output,
                "🎬 صدا استخراج شد."
            )

        elif operation in ("info", "metadata"):
            info = await ffprobe(path)
            fmt = info.get("format", {})
            streams = info.get("streams", [])

            if operation == "metadata":
                tags = fmt.get("tags", {})

                text = "🏷️ Metadata\n\n"

                if tags:
                    for key, value in tags.items():
                        text += f"• {key}: {value}\n"
                else:
                    text += "Metadataای پیدا نشد."

            else:
                audio = next(
                    (
                        s for s in streams
                        if s.get("codec_type") == "audio"
                    ),
                    None
                )

                duration = float(
                    fmt.get("duration", 0) or 0
                )

                minutes = int(duration // 60)
                seconds = int(duration % 60)

                size = int(fmt.get("size", 0) or 0)

                text = (
                    "ℹ️ اطلاعات فایل\n\n"
                    f"📦 Format: {fmt.get('format_name', '-')}\n"
                    f"💾 Size: {size / 1024 / 1024:.2f} MB\n"
                    f"⏱ Duration: {minutes}:{seconds:02d}\n"
                )

                if audio:
                    text += (
                        f"🎵 Codec: {audio.get('codec_name', '-')}\n"
                        f"🔊 Sample Rate: {audio.get('sample_rate', '-')}\n"
                        f"🎚 Channels: {audio.get('channels', '-')}\n"
                    )

            await status.edit_text(
                text,
                reply_markup=back_buttons()
            )

            return

    except Exception as e:
        await status.edit_text(
            f"❌ خطا در پردازش:\n{str(e)[-1200:]}",
            reply_markup=back_buttons()
        )

    finally:
        try:
            os.remove(path)
        except OSError:
            pass

        context.user_data.pop("audio_operation", None)


async def merge_done(update, context):
    q = update.callback_query
    await q.answer()

    files = context.user_data.get("audio_merge_files", [])

    if len(files) < 2:
        await q.edit_message_text(
            "❌ حداقل دو فایل لازم است.",
            reply_markup=back_buttons()
        )
        return

    try:
        await q.edit_message_text("⏳ در حال ادغام...")

        output = await merge(files)

        await send_result(
            q.message.chat,
            output,
            "🔗 فایل‌ها با موفقیت ادغام شدند."
        )

    except Exception as e:
        await q.edit_message_text(
            f"❌ خطا:\n{str(e)[-1200:]}",
            reply_markup=back_buttons()
        )

    finally:
        for path in files:
            try:
                os.remove(path)
            except OSError:
                pass

        context.user_data.clear()


def register_audio_handlers(application):
    application.add_handler(
        CallbackQueryHandler(
            audio_callback,
            pattern=r"^(lab_audio|audio_)"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            merge_done,
            pattern=r"^audio_merge_done$"
        )
    )

    application.add_handler(
        MessageHandler(
            filters.AUDIO |
            filters.VOICE |
            filters.VIDEO |
            filters.Document.ALL,
            audio_media_handler
        )
    )
