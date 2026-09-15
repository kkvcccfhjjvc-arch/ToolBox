from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import CHANNEL

async def is_member(bot, user_id):
    try:
        member = await bot.get_chat_member(CHANNEL, user_id)

        return member.status in (
            "member",
            "administrator",
            "creator"
        )

    except Exception:
        return False

def join_keyboard():
    channel = CHANNEL.replace("@", "")

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "📢 عضویت در کانال",
                url=f"https://t.me/{channel}"
            )
        ],
        [
            InlineKeyboardButton(
                "✅ عضو شدم",
                callback_data="check_membership"
            )
        ]
    ])
