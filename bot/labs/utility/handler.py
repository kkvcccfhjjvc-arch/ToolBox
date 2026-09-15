import asyncio
import time

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
    calculate,
    convert_unit,
    convert_temperature,
    generate_password,
    random_number,
    random_choice,
    number_convert,
    timezone_now,
    timezone_convert,
    format_seconds,
)


ACTIONS = {
    "🧮 Calculator": "calculator",
    "📏 Unit Converter": "unit",
    "🔐 Password Generator": "password",
    "⏱️ Timer": "timer",
    "⏱️ Stopwatch": "stopwatch",
    "🔔 Reminder": "reminder",
    "📝 Todo List": "todo",
    "🎲 Random": "random",
    "🔢 Number Converter": "number",
    "🌍 Timezone": "timezone",
}


def utility_menu():
    return ReplyKeyboardMarkup(
        [
            [
                KeyboardButton("🧮 Calculator"),
                KeyboardButton("📏 Unit Converter"),
            ],
            [
                KeyboardButton("🔐 Password Generator"),
                KeyboardButton("⏱️ Timer"),
            ],
            [
                KeyboardButton("⏱️ Stopwatch"),
                KeyboardButton("🔔 Reminder"),
            ],
            [
                KeyboardButton("📝 Todo List"),
                KeyboardButton("🎲 Random"),
            ],
            [
                KeyboardButton("🔢 Number Converter"),
                KeyboardButton("🌍 Timezone"),
            ],
            [
                KeyboardButton("🏠 Home"),
            ],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )


async def utility_lab_menu(update, context):
    context.user_data.clear()
    context.user_data["active_lab"] = "utility"

    await update.effective_chat.send_message(
        "🧮 Utility Lab\n\n"
        "ابزار موردنظر را انتخاب کنید:",
        reply_markup=utility_menu(),
    )


async def timer_task(chat_id, seconds, context, label):
    await asyncio.sleep(seconds)

    await context.bot.send_message(
        chat_id=chat_id,
        text=(
            "⏰ Timer تمام شد!\n\n"
            f"⏱️ مدت: {label}"
        ),
    )


async def reminder_task(
    chat_id,
    seconds,
    context,
    message,
):
    await asyncio.sleep(seconds)

    await context.bot.send_message(
        chat_id=chat_id,
        text=(
            "🔔 Reminder\n\n"
            f"{message}"
        ),
    )


async def handle_utility_text(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not update.message or not update.message.text:
        return

    if context.user_data.get("active_lab") != "utility":
        return

    if not await check_access(update, context):
        return

    text = update.message.text.strip()

    if text == "🏠 Home":
        context.user_data.clear()

        try:
            await update.message.delete()
        except Exception:
            pass

        from bot.menu import main_menu

        await update.effective_chat.send_message(
            "🧰 TOOL BOX\n\n"
            "👇 یک بخش را انتخاب کنید:",
            reply_markup=main_menu(),
        )
        return

    if text in ACTIONS:
        action = ACTIONS[text]

        context.user_data["utility_action"] = action

        try:
            await update.message.delete()
        except Exception:
            pass

        prompts = {
            "calculator": (
                "🧮 عبارت ریاضی را ارسال کنید.\n\n"
                "مثال:\n"
                "`25 * 4 + 10 / 2`"
            ),
            "unit": (
                "📏 فرمت:\n"
                "`value from_unit to_unit`\n\n"
                "مثال:\n"
                "`10 km mile`\n\n"
                "دما:\n"
                "`25 C F`"
            ),
            "password": (
                "🔐 طول رمز را ارسال کنید.\n"
                "مثال: `20`\n\n"
                "بین 4 تا 128"
            ),
            "timer": (
                "⏱️ زمان را برحسب ثانیه ارسال کنید.\n"
                "مثال: `60`"
            ),
            "stopwatch": (
                "⏱️ برای شروع کرنومتر، `start` را بفرستید.\n"
                "برای توقف: `stop`"
            ),
            "reminder": (
                "🔔 فرمت:\n"
                "`seconds | message`\n\n"
                "مثال:\n"
                "`60 | وقت درس خواندن`"
            ),
            "todo": (
                "📝 دستورها:\n"
                "`add متن`\n"
                "`list`\n"
                "`done شماره`\n"
                "`clear`"
            ),
            "random": (
                "🎲 فرمت:\n"
                "`number min max`\n"
                "یا\n"
                "`choice گزینه1 | گزینه2 | گزینه3`"
            ),
            "number": (
                "🔢 فرمت:\n"
                "`source target value`\n\n"
                "مثال:\n"
                "`binary decimal 1010`"
            ),
            "timezone": (
                "🌍 فرمت:\n"
                "`now Asia/Tehran`\n\n"
                "یا:\n"
                "`convert Asia/Tehran Europe/Berlin`"
            ),
        }

        await update.effective_chat.send_message(
            prompts[action],
            reply_markup=utility_menu(),
        )
        return

    action = context.user_data.get(
        "utility_action"
    )

    if not action:
        return

    try:
        if action == "calculator":
            result = calculate(text)

            await update.effective_chat.send_message(
                f"🧮 نتیجه:\n\n`{result}`",
                parse_mode="Markdown",
                reply_markup=utility_menu(),
            )

        elif action == "unit":
            parts = text.split()

            if len(parts) != 3:
                raise ValueError(
                    "فرمت صحیح:\n"
                    "10 km mile"
                )

            value, source, target = parts

            if source.upper() in ("C", "F", "K"):
                result = convert_temperature(
                    value,
                    source,
                    target,
                )
            else:
                result = convert_unit(
                    value,
                    source,
                    target,
                )

            await update.effective_chat.send_message(
                f"📏 نتیجه:\n\n"
                f"`{result} {target}`",
                parse_mode="Markdown",
                reply_markup=utility_menu(),
            )

        elif action == "password":
            result = generate_password(
                int(text)
            )

            await update.effective_chat.send_message(
                f"🔐 رمز تولیدشده:\n\n"
                f"`{result}`",
                parse_mode="Markdown",
                reply_markup=utility_menu(),
            )

        elif action == "timer":
            seconds = int(text)

            if seconds <= 0 or seconds > 86400:
                raise ValueError(
                    "زمان باید بین 1 تا 86400 ثانیه باشد."
                )

            label = format_seconds(seconds)

            asyncio.create_task(
                timer_task(
                    update.effective_chat.id,
                    seconds,
                    context,
                    label,
                )
            )

            await update.effective_chat.send_message(
                f"⏱️ Timer شروع شد.\n\n"
                f"مدت: {label}",
                reply_markup=utility_menu(),
            )

        elif action == "stopwatch":
            if text.lower() == "start":
                context.user_data[
                    "stopwatch_start"
                ] = time.monotonic()

                await update.effective_chat.send_message(
                    "⏱️ Stopwatch شروع شد.",
                    reply_markup=utility_menu(),
                )

            elif text.lower() == "stop":
                started = context.user_data.get(
                    "stopwatch_start"
                )

                if not started:
                    raise ValueError(
                        "Stopwatch هنوز شروع نشده است."
                    )

                elapsed = int(
                    time.monotonic() - started
                )

                context.user_data.pop(
                    "stopwatch_start",
                    None,
                )

                await update.effective_chat.send_message(
                    "⏱️ Stopwatch متوقف شد.\n\n"
                    f"زمان: {format_seconds(elapsed)}",
                    reply_markup=utility_menu(),
                )

            else:
                raise ValueError(
                    "فقط `start` یا `stop` ارسال کنید."
                )

        elif action == "reminder":
            if "|" not in text:
                raise ValueError(
                    "فرمت:\n"
                    "60 | متن یادآوری"
                )

            seconds_text, message = text.split(
                "|",
                1,
            )

            seconds = int(
                seconds_text.strip()
            )

            message = message.strip()

            if seconds <= 0 or seconds > 604800:
                raise ValueError(
                    "زمان باید بین 1 ثانیه تا 7 روز باشد."
                )

            if not message:
                raise ValueError(
                    "متن یادآوری خالی است."
                )

            asyncio.create_task(
                reminder_task(
                    update.effective_chat.id,
                    seconds,
                    context,
                    message,
                )
            )

            await update.effective_chat.send_message(
                "🔔 Reminder ثبت شد.",
                reply_markup=utility_menu(),
            )

        elif action == "todo":
            todos = context.user_data.setdefault(
                "todos",
                [],
            )

            parts = text.split(
                " ",
                1,
            )

            command = parts[0].lower()

            if command == "add":
                if len(parts) < 2:
                    raise ValueError(
                        "متن Todo را وارد کنید."
                    )

                todos.append(parts[1].strip())

                result = (
                    f"✅ اضافه شد.\n"
                    f"شماره: {len(todos)}"
                )

            elif command == "list":
                if not todos:
                    result = "📝 لیست خالی است."

                else:
                    result = "\n".join(
                        f"{i}. {item}"
                        for i, item in enumerate(
                            todos,
                            1,
                        )
                    )

            elif command == "done":
                if len(parts) < 2:
                    raise ValueError(
                        "شماره Todo را وارد کنید."
                    )

                index = int(parts[1]) - 1

                if index < 0 or index >= len(todos):
                    raise ValueError(
                        "شماره نامعتبر است."
                    )

                item = todos.pop(index)

                result = f"✅ انجام شد:\n{item}"

            elif command == "clear":
                todos.clear()
                result = "🧹 لیست پاک شد."

            else:
                raise ValueError(
                    "دستور نامعتبر است."
                )

            await update.effective_chat.send_message(
                f"📝 Todo:\n\n{result}",
                reply_markup=utility_menu(),
            )

        elif action == "random":
            parts = text.split(
                " ",
                2,
            )

            if len(parts) >= 3 and parts[0].lower() == "number":
                minimum = int(parts[1])
                maximum = int(parts[2])

                if minimum > maximum:
                    raise ValueError(
                        "حداقل نباید بزرگ‌تر از حداکثر باشد."
                    )

                result = random_number(
                    minimum,
                    maximum,
                )

            elif text.lower().startswith("choice "):
                values = text[7:].split("|")

                result = random_choice(values)

            else:
                raise ValueError(
                    "فرمت نامعتبر است."
                )

            await update.effective_chat.send_message(
                f"🎲 نتیجه:\n\n`{result}`",
                parse_mode="Markdown",
                reply_markup=utility_menu(),
            )

        elif action == "number":
            parts = text.split()

            if len(parts) != 3:
                raise ValueError(
                    "مثال:\n"
                    "binary decimal 1010"
                )

            result = number_convert(
                parts[2],
                parts[0],
                parts[1],
            )

            await update.effective_chat.send_message(
                f"🔢 نتیجه:\n\n`{result}`",
                parse_mode="Markdown",
                reply_markup=utility_menu(),
            )

        elif action == "timezone":
            parts = text.split()

            if len(parts) == 2 and parts[0].lower() == "now":
                result = timezone_now(parts[1])

            elif (
                len(parts) == 3
                and parts[0].lower() == "convert"
            ):
                result = timezone_convert(
                    parts[1],
                    parts[2],
                )

            else:
                raise ValueError(
                    "مثال:\n"
                    "now Asia/Tehran\n\n"
                    "یا:\n"
                    "convert Asia/Tehran Europe/Berlin"
                )

            await update.effective_chat.send_message(
                f"🌍 نتیجه:\n\n`{result}`",
                parse_mode="Markdown",
                reply_markup=utility_menu(),
            )

        else:
            return

    except Exception as e:
        await update.effective_chat.send_message(
            f"❌ خطا:\n{str(e)[:1000]}",
            reply_markup=utility_menu(),
        )


def register_utility_handlers(app):
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_utility_text,
        ),
        group=10,
    )
