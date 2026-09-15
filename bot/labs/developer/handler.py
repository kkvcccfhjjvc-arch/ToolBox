from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, MessageHandler, filters

from bot.services.access import check_access
from .processor import (
    json_format,
    json_minify,
    json_validate,
    json_to_yaml,
    yaml_to_json,
    json_to_csv,
    csv_to_json,
    regex_test,
    text_diff,
    base64_encode,
    base64_decode,
    url_encode,
    url_decode,
    html_encode,
    html_decode,
    number_convert,
    unix_to_datetime,
    datetime_to_unix,
    color_convert,
    generate_uuid,
    jwt_decode,
    cron_explain,
)


ACTIONS = {
    "🧹 JSON Format": "json_format",
    "📦 JSON Minify": "json_minify",
    "✅ JSON Validate": "json_validate",
    "🔄 JSON → YAML": "json_yaml",
    "🔄 YAML → JSON": "yaml_json",
    "📊 JSON → CSV": "json_csv",
    "📊 CSV → JSON": "csv_json",
    "🔍 Regex Tester": "regex",
    "↔️ Text Diff": "diff",
    "🔐 Base64 Encode": "b64_encode",
    "🔓 Base64 Decode": "b64_decode",
    "🔗 URL Encode": "url_encode",
    "🔗 URL Decode": "url_decode",
    "🏷️ HTML Encode": "html_encode",
    "🏷️ HTML Decode": "html_decode",
    "🔢 Number Convert": "number",
    "⏱️ Unix Timestamp": "timestamp",
    "🎨 Color Converter": "color",
    "🆔 UUID Generator": "uuid",
    "🔑 JWT Inspector": "jwt",
    "⏰ Cron Builder": "cron",
}


def developer_menu():
    return ReplyKeyboardMarkup(
        [
            [
                KeyboardButton("🧹 JSON Format"),
                KeyboardButton("📦 JSON Minify"),
            ],
            [
                KeyboardButton("✅ JSON Validate"),
                KeyboardButton("🔄 JSON → YAML"),
            ],
            [
                KeyboardButton("🔄 YAML → JSON"),
                KeyboardButton("📊 JSON → CSV"),
            ],
            [
                KeyboardButton("📊 CSV → JSON"),
                KeyboardButton("🔍 Regex Tester"),
            ],
            [
                KeyboardButton("↔️ Text Diff"),
                KeyboardButton("🔐 Base64 Encode"),
            ],
            [
                KeyboardButton("🔓 Base64 Decode"),
                KeyboardButton("🔗 URL Encode"),
            ],
            [
                KeyboardButton("🔗 URL Decode"),
                KeyboardButton("🏷️ HTML Encode"),
            ],
            [
                KeyboardButton("🏷️ HTML Decode"),
                KeyboardButton("🔢 Number Convert"),
            ],
            [
                KeyboardButton("⏱️ Unix Timestamp"),
                KeyboardButton("🎨 Color Converter"),
            ],
            [
                KeyboardButton("🆔 UUID Generator"),
                KeyboardButton("🔑 JWT Inspector"),
            ],
            [
                KeyboardButton("⏰ Cron Builder"),
            ],
            [
                KeyboardButton("🏠 Home"),
            ],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )


async def developer_lab_menu(update, context):
    context.user_data.clear()
    context.user_data["active_lab"] = "developer"

    await update.effective_chat.send_message(
        "🛠️ Developer & Data Lab\n\n"
        "ابزار موردنظر را انتخاب کنید:",
        reply_markup=developer_menu(),
    )


async def handle_developer_text(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not update.message or not update.message.text:
        return

    if context.user_data.get("active_lab") != "developer":
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

        context.user_data["developer_action"] = action

        try:
            await update.message.delete()
        except Exception:
            pass

        prompts = {
            "json_format": "🧹 JSON را ارسال کنید:",
            "json_minify": "📦 JSON را ارسال کنید:",
            "json_validate": "✅ JSON را ارسال کنید:",
            "json_yaml": "🔄 JSON را ارسال کنید:",
            "yaml_json": "🔄 YAML را ارسال کنید:",
            "json_csv": "📊 JSON را ارسال کنید:",
            "csv_json": "📊 CSV را ارسال کنید:",
            "regex": (
                "🔍 ابتدا Regex را ارسال کنید:\n"
                "مثال: ^[A-Za-z]+$"
            ),
            "diff": (
                "↔️ متن اول را ارسال کنید:"
            ),
            "b64_encode": "🔐 متن را ارسال کنید:",
            "b64_decode": "🔓 Base64 را ارسال کنید:",
            "url_encode": "🔗 متن را ارسال کنید:",
            "url_decode": "🔗 URL Encoded را ارسال کنید:",
            "html_encode": "🏷️ متن HTML را ارسال کنید:",
            "html_decode": "🏷️ HTML Encoded را ارسال کنید:",
            "number": (
                "🔢 مقدار را ارسال کنید.\n"
                "مثال: 255"
            ),
            "timestamp": (
                "⏱️ Unix Timestamp یا تاریخ ISO را ارسال کنید:"
            ),
            "color": (
                "🎨 رنگ را به شکل HEX ارسال کنید.\n"
                "مثال: #00FF88"
            ),
            "uuid": "",
            "jwt": "🔑 JWT را ارسال کنید:",
            "cron": (
                "⏰ عبارت Cron را ارسال کنید.\n"
                "مثال: */5 * * * *"
            ),
        }

        if action == "uuid":
            await update.effective_chat.send_message(
                f"🆔 UUID جدید:\n\n"
                f"`{generate_uuid()}`",
                parse_mode="Markdown",
                reply_markup=developer_menu(),
            )
            context.user_data.pop(
                "developer_action",
                None,
            )
            return

        await update.effective_chat.send_message(
            prompts.get(
                action,
                "📥 مقدار موردنظر را ارسال کنید:",
            ),
            reply_markup=developer_menu(),
        )
        return

    action = context.user_data.get(
        "developer_action"
    )

    if not action:
        return

    try:
        if action == "json_format":
            result = json_format(text)

        elif action == "json_minify":
            result = json_minify(text)

        elif action == "json_validate":
            json_validate(text)
            result = "✅ JSON معتبر است."

        elif action == "json_yaml":
            result = json_to_yaml(text)

        elif action == "yaml_json":
            result = yaml_to_json(text)

        elif action == "json_csv":
            result = json_to_csv(text)

        elif action == "csv_json":
            result = csv_to_json(text)

        elif action == "regex":
            context.user_data["regex_pattern"] = text
            context.user_data["developer_action"] = "regex_text"

            await update.effective_chat.send_message(
                "📝 حالا متن موردنظر برای تست Regex را ارسال کنید."
            )
            return

        elif action == "regex_text":
            pattern = context.user_data.get(
                "regex_pattern",
                "",
            )

            matches = regex_test(
                pattern,
                text,
            )

            if not matches:
                result = "❌ هیچ Matchای پیدا نشد."
            else:
                lines = []

                for i, match in enumerate(
                    matches,
                    1,
                ):
                    lines.append(
                        f"#{i} `{match['match']}` "
                        f"({match['start']}-{match['end']})"
                    )

                result = (
                    f"🔍 تعداد Match: {len(matches)}\n\n"
                    + "\n".join(lines)
                )

        elif action == "diff":
            context.user_data["diff_first"] = text
            context.user_data["developer_action"] = "diff_second"

            await update.effective_chat.send_message(
                "📝 متن دوم را ارسال کنید."
            )
            return

        elif action == "diff_second":
            result = text_diff(
                context.user_data.get(
                    "diff_first",
                    "",
                ),
                text,
            )

            if not result:
                result = "✅ دو متن یکسان هستند."

        elif action == "b64_encode":
            result = base64_encode(text)

        elif action == "b64_decode":
            result = base64_decode(text)

        elif action == "url_encode":
            result = url_encode(text)

        elif action == "url_decode":
            result = url_decode(text)

        elif action == "html_encode":
            result = html_encode(text)

        elif action == "html_decode":
            result = html_decode(text)

        elif action == "number":
            # قالب: binary decimal 1010
            parts = text.split()

            if len(parts) != 3:
                result = (
                    "فرمت:\n"
                    "`source target value`\n\n"
                    "مثال:\n"
                    "`binary decimal 1010`"
                )
            else:
                result = number_convert(
                    parts[2],
                    parts[0].lower(),
                    parts[1].lower(),
                )

        elif action == "timestamp":
            if re.fullmatch(r"-?\d+", text):
                result = unix_to_datetime(text)
            else:
                result = datetime_to_unix(text)

        elif action == "color":
            data = color_convert(text)

            result = (
                f"🎨 HEX: {data['hex']}\n"
                f"🔴 RGB: {data['rgb']}\n"
                f"🔢 Decimal: {data['decimal']}"
            )

        elif action == "jwt":
            data = jwt_decode(text)

            result = (
                "🔑 JWT Header:\n"
                f"{json_format(json.dumps(data['header']))}\n\n"
                "📦 JWT Payload:\n"
                f"{json_format(json.dumps(data['payload']))}\n\n"
                "⚠️ Signature فقط نمایش داده شد؛ "
                "هیچ بررسی امضایی انجام نشده است."
            )

        elif action == "cron":
            result = cron_explain(text)

        else:
            result = "❌ عملیات نامعتبر است."

        if len(result) > 3800:
            result = result[:3800] + "\n\n…"

        await update.effective_chat.send_message(
            f"🛠️ نتیجه:\n\n{result}",
            reply_markup=developer_menu(),
        )

        context.user_data.pop(
            "developer_action",
            None,
        )

    except Exception as e:
        await update.effective_chat.send_message(
            f"❌ خطا:\n{str(e)[:1000]}",
            reply_markup=developer_menu(),
        )


def register_developer_handlers(app):
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_developer_text,
        ),
        group=9,
    )
