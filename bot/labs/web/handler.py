from telegram import (
    Update,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from telegram.ext import (
    ContextTypes,
    MessageHandler,
    filters,
)

from bot.services.access import check_access

from bot.labs.web.processor import (
    web_search,
    wikipedia_search,
    wikipedia_summary,
    article_reader,
    url_info,
    link_preview,
    get_weather,
    get_news,
    webpage_to_pdf,
    parse_url,
    dns_info,
)


ACTIONS = {
    "🔎 Web Search": "search",
    "📖 Wikipedia": "wiki",
    "📰 News": "news",
    "🌤️ Weather": "weather",
    "🔗 URL Info": "url_info",
    "👀 Link Preview": "preview",
    "📄 Webpage → PDF": "pdf",
    "🧩 URL Parser": "parser",
    "🌍 DNS Info": "dns",
    "📚 Article Reader": "article",
}


def web_menu():
    return ReplyKeyboardMarkup(
        [
            [
                KeyboardButton("🔎 Web Search"),
                KeyboardButton("📖 Wikipedia"),
            ],
            [
                KeyboardButton("📰 News"),
                KeyboardButton("🌤️ Weather"),
            ],
            [
                KeyboardButton("🔗 URL Info"),
                KeyboardButton("👀 Link Preview"),
            ],
            [
                KeyboardButton("📄 Webpage → PDF"),
                KeyboardButton("🧩 URL Parser"),
            ],
            [
                KeyboardButton("🌍 DNS Info"),
                KeyboardButton("📚 Article Reader"),
            ],
            [
                KeyboardButton("🏠 Home"),
            ],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )


LAB_BUTTONS = {
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
}


async def web_lab_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    context.user_data["active_lab"] = "web"

    for key in (
        "web_action",
    ):
        context.user_data.pop(key, None)

    await update.effective_chat.send_message(
        "🌐 Web Lab\n\n"
        "ابزارهای وب، جستجو، Wikipedia، آب‌وهوا، "
        "URL و تبدیل Webpage به PDF.\n\n"
        "👇 یک ابزار را انتخاب کنید:",
        reply_markup=web_menu(),
    )


async def delete_selection(update):
    try:
        await update.message.delete()
    except Exception:
        pass


async def handle_web_text(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()

    if text in LAB_BUTTONS:
        return

    if context.user_data.get("active_lab") != "web":
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

    if action:
        context.user_data["web_action"] = action
        await delete_selection(update)

        if action == "news":
            try:
                results = get_news()

                if not results:
                    raise ValueError(
                        "خبر جدیدی پیدا نشد."
                    )

                msg = "📰 آخرین اخبار\n\n"

                for i, item in enumerate(
                    results,
                    1,
                ):
                    msg += (
                        f"{i}. {item['title']}\n"
                        f"🔗 {item['url']}\n\n"
                    )

                await update.effective_chat.send_message(
                    msg[:4000]
                )

            except Exception as e:
                await update.effective_chat.send_message(
                    f"❌ خطا:\n{e}"
                )

            context.user_data.pop(
                "web_action",
                None,
            )
            return

        prompts = {
            "search": "🔎 عبارت موردنظر برای جستجو را ارسال کن:",
            "wiki": "📖 موضوع Wikipedia را ارسال کن:",
            "weather": "🌤️ نام شهر را ارسال کن:",
            "url_info": "🔗 لینک را ارسال کن:",
            "preview": "👀 لینک را ارسال کن:",
            "pdf": "📄 لینک صفحه را ارسال کن:",
            "parser": "🧩 URL را ارسال کن:",
            "dns": "🌍 دامنه را ارسال کن:",
            "article": "📚 لینک مقاله را ارسال کن:",
        }

        await update.effective_chat.send_message(
            prompts[action]
        )
        return

    action = context.user_data.get("web_action")

    if not action:
        return

    try:
        if action == "search":
            results = web_search(text)

            if not results:
                raise ValueError(
                    "نتیجه‌ای پیدا نشد."
                )

            msg = "🔎 نتایج جستجو\n\n"

            for i, item in enumerate(
                results,
                1,
            ):
                msg += (
                    f"{i}. {item['title']}\n"
                    f"🔗 {item['url']}\n"
                )

                if item["snippet"]:
                    msg += (
                        f"📝 {item['snippet']}\n"
                    )

                msg += "\n"

            await update.effective_chat.send_message(
                msg[:4000]
            )

        elif action == "wiki":
            results = wikipedia_search(text)

            if not results:
                raise ValueError(
                    "نتیجه‌ای در Wikipedia پیدا نشد."
                )

            msg = "📖 Wikipedia\n\n"

            for i, item in enumerate(
                results,
                1,
            ):
                msg += (
                    f"{i}. {item['title']}\n"
                    f"📝 {item['snippet']}\n"
                    f"🔗 {item['url']}\n\n"
                )

            await update.effective_chat.send_message(
                msg[:4000]
            )

        elif action == "weather":
            data = get_weather(text)

            msg = (
                f"🌤️ آب‌وهوای {data['city']}\n\n"
                f"🌡️ دما: {data['temp']}°C\n"
                f"🌡️ احساس دما: {data['feels']}°C\n"
                f"☁️ وضعیت: {data['description']}\n"
                f"💧 رطوبت: {data['humidity']}%\n"
                f"💨 باد: {data['wind']} km/h"
            )

            await update.effective_chat.send_message(
                msg
            )

        elif action == "url_info":
            data = url_info(text)

            msg = (
                "🔗 URL Information\n\n"
                f"🌐 Scheme: {data['scheme']}\n"
                f"🏠 Host: {data['host']}\n"
                f"📡 IP: {data['ip']}\n"
                f"🚪 Port: {data['port']}\n"
                f"📂 Path: {data['path']}\n"
                f"🔎 Query: {data['query'] or '-'}\n"
                f"⚓ Fragment: {data['fragment'] or '-'}"
            )

            await update.effective_chat.send_message(
                msg
            )

        elif action == "preview":
            data = link_preview(text)

            msg = (
                "👀 Link Preview\n\n"
                f"📌 {data['title'] or 'بدون عنوان'}\n\n"
                f"📝 {data['description'] or 'بدون توضیح'}\n\n"
                f"🌐 {data['url']}\n"
                f"📡 Status: {data['status']}\n"
                f"📦 Type: {data['content_type']}"
            )

            await update.effective_chat.send_message(
                msg[:4000]
            )

        elif action == "article":
            title, article = article_reader(text)

            if not article:
                raise ValueError(
                    "متن مقاله قابل استخراج نیست."
                )

            msg = (
                f"📚 {title}\n\n"
                f"{article}"
            )

            await update.effective_chat.send_message(
                msg[:4000]
            )

        elif action == "pdf":
            output = webpage_to_pdf(text)

            with output.open("rb") as f:
                await update.effective_chat.send_document(
                    document=f,
                    caption="📄 Webpage به PDF تبدیل شد.",
                )

            output.unlink(missing_ok=True)

        elif action == "parser":
            data = parse_url(text)

            params = data["parameters"]

            param_text = "\n".join(
                f"  • {k}: {', '.join(v)}"
                for k, v in params.items()
            )

            msg = (
                "🧩 URL Parser\n\n"
                f"Scheme: {data['scheme']}\n"
                f"Username: {data['username'] or '-'}\n"
                f"Hostname: {data['hostname']}\n"
                f"Port: {data['port'] or '-'}\n"
                f"Path: {data['path']}\n"
                f"Query: {data['query'] or '-'}\n"
                f"Fragment: {data['fragment'] or '-'}\n\n"
                f"Parameters:\n"
                f"{param_text or '  -'}"
            )

            await update.effective_chat.send_message(
                msg[:4000]
            )

        elif action == "dns":
            data = dns_info(text)

            ipv4 = "\n".join(
                f"• {ip}"
                for ip in data["ipv4"]
            )

            aliases = "\n".join(
                f"• {a}"
                for a in data["aliases"]
            )

            msg = (
                "🌍 DNS Information\n\n"
                f"🏠 Host: {data['host']}\n\n"
                f"IPv4:\n"
                f"{ipv4 or '• پیدا نشد'}\n\n"
                f"Aliases:\n"
                f"{aliases or '• ندارد'}"
            )

            await update.effective_chat.send_message(
                msg
            )

        context.user_data.pop(
            "web_action",
            None,
        )

    except Exception as e:
        await update.effective_chat.send_message(
            f"❌ خطا:\n{str(e)}"
        )


def register_web_handlers(app):
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_web_text,
        )
    )
