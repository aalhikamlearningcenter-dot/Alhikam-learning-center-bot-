import os
from database import get_student_by_telegram_id
from telegram_service import send_student_links
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")

APP_URL = os.getenv("RAILWAY_URL")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

student = get_student_by_telegram_id(user.id)

if student and student["registration_completed"] == 1:

    await send_student_links(
        user.id,
        student["course"]
    )

    return

    register_link = (
        f"{APP_URL}/register"
        f"?telegram_id={user.id}"
        f"&telegram_name={user.first_name}"
        f"&telegram_username={user.username or ''}"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "📝 Continue Registration",
                url=register_link
            )
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"""🎓 Welcome to ALHIKAM Learning Center

Hello {user.first_name},

✅ Your payment has been verified.

Tap the button below to continue your registration.
""",
        reply_markup=reply_markup
    )


    text = f"""
🎓 Welcome to ALHIKAM Learning Center

Hello {user.first_name}.

✅ Your Telegram account has been identified successfully.

Click the button below to continue your registration.

{register_link}
"""

    await update.message.reply_text(text)


application = (
    Application.builder()
    .token(BOT_TOKEN)
    .build()
)

application.add_handler(
    CommandHandler("start", start)
)


if __name__ == "__main__":
    application.run_polling()