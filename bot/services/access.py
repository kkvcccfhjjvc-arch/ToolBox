from bot.services.membership import is_member, join_keyboard

async def check_access(update, context):
    user = update.effective_user

    if not user:
        return False

    if await is_member(context.bot, user.id):
        return True

    text = (
        "🔒 برای استفاده از Tool Box ابتدا باید عضو کانال شوید.\n\n"
        "بعد از عضویت روی «عضو شدم» بزنید."
    )

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(
            text,
            reply_markup=join_keyboard()
        )
    else:
        await update.effective_message.reply_text(
            text,
            reply_markup=join_keyboard()
        )

    return False
