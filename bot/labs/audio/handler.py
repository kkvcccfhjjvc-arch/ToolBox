import os
import uuid
from pathlib import Path

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from telegram.ext import (
    ContextTypes,
    MessageHandler,
    filters,
)

from bot.services.access import check_access
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


BASE = Path("temp/audio")
BASE.mkdir(parents=True, exist_ok=True)


def audio_menu():
    return ReplyKeyboardMarkup(
        [
            [
                KeyboardButton("🎙️ Voice"),
                KeyboardButton("🔄 Convert"),
            ],
            [
                KeyboardButton("✂️ Cut"),
                KeyboardButton("🔗 Merge"),
            ],
            [
                KeyboardButton("⏩ Speed"),
                KeyboardButton("🔊 Volume"),
            ],
            [
                KeyboardButton("🎵 Pitch"),
                KeyboardButton("🔇 Silence"),
            ],
            [
                KeyboardButton("↩️ Reverse"),
                KeyboardButton("📦 Compress"),
            ],
            [
                KeyboardButton("〰️ Waveform"),
                KeyboardButton("📊 Spectrogram"),
            ],
            [
                KeyboardButton("🎬 Extract Audio"),
                KeyboardButton("ℹ️ File Info"),
            ],
            [
                KeyboardButton("🏷️ Metadata"),
            ],
            [
                KeyboardButton("🏠 منوی اصلی"),
        ],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )


def format_menu():
    return ReplyKeyboardMarkup(
        [
            [
                KeyboardButton("MP3"),
                KeyboardButton("WAV"),
            ],
            [
                KeyboardButton("OGG"),
                KeyboardButton("FLAC"),
            ],
            [
                KeyboardButton("M4A"),
            ],
            [
                KeyboardButton("🔙 Audio Lab"),
            ],
        ],
        resize_keyboard=True,
    )


def speed_menu():
    return ReplyKeyboardMarkup(
        [
            [
                KeyboardButton("0.5x"),
                KeyboardButton("0.75x"),
            ],
            [
                KeyboardButton("1.25x"),
                KeyboardButton("1.5x"),
            ],
            [
                KeyboardButton("2x"),
            ],
            [
                KeyboardButton("🔙 Audio Lab"),
            ],
        ],
        resize_keyboard=True,
    )


def volume_menu():
    return ReplyKeyboardMarkup(
        [
            [
                KeyboardButton("50%"),
                KeyboardButton("75%"),
            ],
            [
                KeyboardButton("100%"),
                KeyboardButton("125%"),
            ],
            [
                KeyboardButton("150%"),
                KeyboardButton("200%"),
            ],
            [
                KeyboardButton("🔙 Audio Lab"),
            ],
        ],
        resize_keyboard=True,
    )


def pitch_menu():
    return ReplyKeyboardMarkup(
        [
            [
                KeyboardButton("-2"),
                KeyboardButton("-1"),
            ],
            [
                KeyboardButton("0"),
                KeyboardButton("+1"),
            ],
            [
                KeyboardButton("+2"),
            ],
            [
                KeyboardButton("🔙 Audio Lab"),
            ],
        ],
        resize_keyboard=True,
    )


def cut_menu():
    return ReplyKeyboardMarkup(
        [
            [
                KeyboardButton("5 ثانیه"),
                KeyboardButton("10 ثانیه"),
            ],
            [
                KeyboardButton("30 ثانیه"),
                KeyboardButton("60 ثانیه"),
            ],
            [
                KeyboardButton("🔙 Audio Lab"),
            ],
        ],
        resize_keyboard=True,
    )


def back_menu():
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("🔙 Audio Lab")],
            [KeyboardButton("🏠 منوی اصلی")],
        ],
        resize_keyboard=True,
    )


async def delete_selection(update):
    try:
        if update.message:
            await update.message.delete()
    except Exception:
        pass


async def send_audio_menu(update, text=None):
    if text is None:
        text = (
            "🎛️ Audio Lab\n\n"
            "👇 ابزار صوتی را انتخاب کنید:"
        )

    await update.message.reply_text(
        text,
        reply_markup=audio_menu(),
    )


def new_session():
    folder = BASE / uuid.uuid4().hex
    folder.mkdir(parents=True, exist_ok=True)
    return folder


async def download_media(update, context):
    message = update.message

    media = None
    filename = "input"

    if message.audio:
        media = message.audio
        filename = message.audio.file_name or "audio"

    elif message.voice:
        media = message.voice
        filename = "voice.ogg"

    elif message.video:
        media = message.video
        filename = message.video.file_name or "video.mp4"

    elif message.document:
        media = message.document
        filename = message.document.file_name or "file"

    if not media:
        return None

    if getattr(media, "file_size", 0) > 50 * 1024 * 1024:
        await message.reply_text(
            "❌ حجم فایل نباید بیشتر از 50MB باشد.",
            reply_markup=audio_menu(),
        )
        return None

    folder = context.user_data.get("audio_folder")

    if not folder:
        folder = new_session()
        context.user_data["audio_folder"] = str(folder)

    folder = Path(folder)

    ext = Path(filename).suffix or ".bin"
    path = folder / f"input_{uuid.uuid4().hex}{ext}"

    tg_file = await media.get_file()
    await tg_file.download_to_drive(str(path))

    return path


async def send_result(update, path, caption="✅ انجام شد"):
    path = Path(path)

    if not path.exists():
        await update.message.reply_text(
            "❌ فایل خروجی ساخته نشد.",
            reply_markup=audio_menu(),
        )
        return

    with open(path, "rb") as f:
        await update.message.reply_document(
            document=f,
            caption=caption,
            reply_markup=audio_menu(),
        )


async def process_audio(update, context):
    if not await check_access(update, context):
        return

    action = context.user_data.get("audio_action")

    if not action:
        return

    path = await download_media(update, context)

    if not path:
        return

    folder = Path(context.user_data["audio_folder"])

    try:
        if action == "voice":
            output = folder / "voice.ogg"
            await convert(path, output)
            await update.message.reply_voice(
                voice=open(output, "rb"),
                caption="🎙️ آماده شد",
                reply_markup=audio_menu(),
            )

        elif action == "convert":
            context.user_data["audio_input"] = str(path)
            await update.message.reply_text(
                "🔄 فرمت خروجی را انتخاب کنید:",
                reply_markup=format_menu(),
            )
            return

        elif action == "speed":
            context.user_data["audio_input"] = str(path)
            await update.message.reply_text(
                "⏩ سرعت را انتخاب کنید:",
                reply_markup=speed_menu(),
            )
            return

        elif action == "volume":
            context.user_data["audio_input"] = str(path)
            await update.message.reply_text(
                "🔊 میزان صدا را انتخاب کنید:",
                reply_markup=volume_menu(),
            )
            return

        elif action == "pitch":
            context.user_data["audio_input"] = str(path)
            await update.message.reply_text(
                "🎵 تغییر Pitch را انتخاب کنید:",
                reply_markup=pitch_menu(),
            )
            return

        elif action == "cut":
            context.user_data["audio_input"] = str(path)
            await update.message.reply_text(
                "✂️ مقدار برش را انتخاب کنید:",
                reply_markup=cut_menu(),
            )
            return

        elif action == "reverse":
            output = folder / "reverse.mp3"
            await reverse(path, output)
            await send_result(update, output, "↩️ Reverse انجام شد")

        elif action == "silence":
            output = folder / "silence_removed.mp3"
            await silence_remove(path, output)
            await send_result(update, output, "🔇 سکوت حذف شد")

        elif action == "compress":
            output = folder / "compressed.mp3"
            await compress(path, output)
            await send_result(update, output, "📦 فشرده‌سازی انجام شد")

        elif action == "waveform":
            output = folder / "waveform.png"
            await waveform(path, output)

            with open(output, "rb") as f:
                await update.message.reply_photo(
                    photo=f,
                    caption="〰️ Waveform",
                    reply_markup=audio_menu(),
                )

        elif action == "spectrogram":
            output = folder / "spectrogram.png"
            await spectrogram(path, output)

            with open(output, "rb") as f:
                await update.message.reply_photo(
                    photo=f,
                    caption="📊 Spectrogram",
                    reply_markup=audio_menu(),
                )

        elif action == "extract":
            output = folder / "audio.mp3"
            await extract_audio(path, output)
            await send_result(update, output, "🎬 Audio استخراج شد")

        elif action == "info":
            info = await ffprobe(path)

            await update.message.reply_text(
                "ℹ️ File Info\n\n"
                f"{info}",
                reply_markup=audio_menu(),
            )

        elif action == "metadata":
            info = await ffprobe(path)

            await update.message.reply_text(
                "🏷️ Metadata\n\n"
                f"{info}",
                reply_markup=audio_menu(),
            )

        context.user_data.pop("audio_action", None)

    except Exception as e:
        context.user_data.pop("audio_action", None)

        await update.message.reply_text(
            f"❌ خطا در پردازش فایل:\n{e}",
            reply_markup=audio_menu(),
        )


async def audio_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update, context):
        return

    text = update.message.text

    await delete_selection(update)

    # ---------- MAIN AUDIO ----------
    if text == "🎛️ Audio Lab":
        context.user_data.pop("audio_action", None)
        context.user_data.pop("audio_input", None)

        await send_audio_menu(update)
        return

    if text == "🏠 منوی اصلی":
        from bot.menu import main_menu

        context.user_data.pop("audio_action", None)
        context.user_data.pop("audio_input", None)

        await update.message.reply_text(
            "🏠 منوی اصلی\n\n👇 یک بخش را انتخاب کنید:",
            reply_markup=main_menu(),
        )
        return

    if text == "🔙 Audio Lab":
        context.user_data.pop("audio_action", None)
        context.user_data.pop("audio_input", None)

        await send_audio_menu(update)
        return

    # ---------- ACTIONS ----------
    actions = {
        "🎙️ Voice": "voice",
        "🔄 Convert": "convert",
        "✂️ Cut": "cut",
        "⏩ Speed": "speed",
        "🔊 Volume": "volume",
        "🎵 Pitch": "pitch",
        "🔇 Silence": "silence",
        "↩️ Reverse": "reverse",
        "📦 Compress": "compress",
        "〰️ Waveform": "waveform",
        "📊 Spectrogram": "spectrogram",
        "🎬 Extract Audio": "extract",
        "ℹ️ File Info": "info",
        "🏷️ Metadata": "metadata",
    }

    if text in actions:
        context.user_data["audio_action"] = actions[text]

        if text == "🎬 Extract Audio":
            msg = "🎬 یک ویدیو ارسال کنید:"
        elif text == "ℹ️ File Info":
            msg = "ℹ️ فایل صوتی یا ویدیو را ارسال کنید:"
        elif text == "🏷️ Metadata":
            msg = "🏷️ فایل صوتی را ارسال کنید:"
        else:
            msg = f"{text}\n\n📎 فایل موردنظر را ارسال کنید:"

        await update.message.reply_text(
            msg,
            reply_markup=back_menu(),
        )
        return

    # ---------- FORMAT ----------
    formats = {
        "MP3": "mp3",
        "WAV": "wav",
        "OGG": "ogg",
        "FLAC": "flac",
        "M4A": "m4a",
    }

    if text in formats and context.user_data.get("audio_input"):
        input_file = Path(context.user_data["audio_input"])
        output = input_file.parent / f"converted.{formats[text]}"

        try:
            await convert(input_file, output)
            context.user_data.pop("audio_input", None)
            context.user_data.pop("audio_action", None)

            await send_result(update, output, f"🔄 تبدیل به {text} انجام شد")
        except Exception as e:
            await update.message.reply_text(
                f"❌ خطا:\n{e}",
                reply_markup=audio_menu(),
            )
        return

    # ---------- SPEED ----------
    if text in ["0.5x", "0.75x", "1.25x", "1.5x", "2x"]:
        input_file = context.user_data.get("audio_input")

        if input_file:
            factor = float(text.replace("x", ""))
            input_file = Path(input_file)
            output = input_file.parent / "speed.mp3"

            try:
                await speed(input_file, output, factor)

                context.user_data.pop("audio_input", None)
                context.user_data.pop("audio_action", None)

                await send_result(
                    update,
                    output,
                    f"⏩ سرعت {text} اعمال شد",
                )
            except Exception as e:
                await update.message.reply_text(
                    f"❌ خطا:\n{e}",
                    reply_markup=audio_menu(),
                )
            return

    # ---------- VOLUME ----------
    if text in ["50%", "75%", "100%", "125%", "150%", "200%"]:
        input_file = context.user_data.get("audio_input")

        if input_file:
            percent = int(text.replace("%", ""))
            input_file = Path(input_file)
            output = input_file.parent / "volume.mp3"

            try:
                await change_volume(input_file, output, percent / 100)

                context.user_data.pop("audio_input", None)
                context.user_data.pop("audio_action", None)

                await send_result(
                    update,
                    output,
                    f"🔊 Volume روی {text} تنظیم شد",
                )
            except Exception as e:
                await update.message.reply_text(
                    f"❌ خطا:\n{e}",
                    reply_markup=audio_menu(),
                )
            return

    # ---------- PITCH ----------
    if text in ["-2", "-1", "0", "+1", "+2"]:
        input_file = context.user_data.get("audio_input")

        if input_file:
            semitones = int(text)
            input_file = Path(input_file)
            output = input_file.parent / "pitch.mp3"

            try:
                await pitch(input_file, output, semitones)

                context.user_data.pop("audio_input", None)
                context.user_data.pop("audio_action", None)

                await send_result(
                    update,
                    output,
                    f"🎵 Pitch {text} اعمال شد",
                )
            except Exception as e:
                await update.message.reply_text(
                    f"❌ خطا:\n{e}",
                    reply_markup=audio_menu(),
                )
            return

    # ---------- CUT ----------
    if text in ["5 ثانیه", "10 ثانیه", "30 ثانیه", "60 ثانیه"]:
        input_file = context.user_data.get("audio_input")

        if input_file:
            seconds = int(text.split()[0])
            input_file = Path(input_file)
            output = input_file.parent / "cut.mp3"

            try:
                await cut(input_file, output, 0, seconds)

                context.user_data.pop("audio_input", None)
                context.user_data.pop("audio_action", None)

                await send_result(
                    update,
                    output,
                    f"✂️ {seconds} ثانیه اول جدا شد",
                )
            except Exception as e:
                await update.message.reply_text(
                    f"❌ خطا:\n{e}",
                    reply_markup=audio_menu(),
                )
            return


async def audio_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("audio_action"):
        await process_audio(update, context)


def register_audio_handlers(application):
    # اول متن‌های Audio
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            audio_text,
        ),
        group=0,
    )

    # بعد فایل‌های صوتی / ویدیویی
    application.add_handler(
        MessageHandler(
            filters.AUDIO
            | filters.VOICE
            | filters.VIDEO
            | filters.Document.ALL,
            audio_media,
        ),
        group=0,
    )
