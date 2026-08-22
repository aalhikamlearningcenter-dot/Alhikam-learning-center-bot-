# ==========================================================
# ALHIKAM LEARNING CENTER V2
# bot.py
# ==========================================================

import os
import asyncio
from urllib.parse import urlencode

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup

from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

from database import (
    get_student_by_telegram_id,
)

from telegram_service import (
    send_student_links,
)


# ==========================================================
# CONFIG
# ==========================================================

BOT_TOKEN = os.getenv(
    "BOT_TOKEN"
)

APP_URL = os.getenv(
    "APP_URL",
    "https://precious-trust-production-956b.up.railway.app"
)


# ==========================================================
# START
# ==========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    if not user:
        return

    telegram_id = str(
        user.id
    )

    telegram_name = (
        user.first_name
        or ""
    )

    telegram_username = (
        user.username
        or ""
    )

    # ======================================================
    # CHECK EXISTING STUDENT
    # ======================================================

    try:

        student = (
            get_student_by_telegram_id(
                telegram_id
            )
        )

    except Exception as e:

        print(
            "Student lookup error:",
            e
        )

        student = None

    # ======================================================
    # ALREADY REGISTERED
    # ======================================================

    if (
        student
        and int(
            student.get(
                "registration_completed",
                0
            ) or 0
        ) == 1
    ):

        await update.message.reply_text(

            f"🎓 Welcome back to ALHIKAM Learning Center\n\n"
            f"Hello {telegram_name},\n\n"
            "✅ Your registration is already completed.\n\n"
            "🔗 I will send your invitation links again now."
        )

        try:

            await send_student_links(
                telegram_id,
                student.get(
                    "course",
                    ""
                )
            )

        except Exception as e:

            print(
                "Could not resend Telegram links:",
                e
            )

            await update.message.reply_text(
                "⚠️ I could not create your links right now. "
                "Please contact ALHIKAM support."
            )

        return

    # ======================================================
    # PAYMENT URL
    # ======================================================

    payment_params = urlencode({
    "telegram_id": telegram_id,
    "telegram_name": telegram_name,
    "telegram_username": telegram_username,
})

payment_url = (
    f"{APP_URL}/payment?{payment_params}"
)

    

    keyboard = [

        [

            InlineKeyboardButton(
                "💳 Start Registration",
                url=payment_url
            )

        ]

    ]

    reply_markup = InlineKeyboardMarkup(
        keyboard
    )

    await update.message.reply_text(

        f"🎓 Welcome to ALHIKAM Learning Center\n\n"
        f"Hello {telegram_name},\n\n"
        "You are about to register as an ALHIKAM student.\n\n"
        "Your Telegram account will automatically be "
        "connected to your registration.\n\n"
        "Tap the button below to continue.",

        reply_markup=reply_markup
    )


# ==========================================================
# APPLICATION
# ==========================================================

if not BOT_TOKEN:

    raise RuntimeError(
        "BOT_TOKEN is missing."
    )


application = (
    Application
    .builder()
    .token(BOT_TOKEN)
    .build()
)


application.add_handler(
    CommandHandler(
        "start",
        start
    )
)


# ==========================================================
# RUN
# ==========================================================

if __name__ == "__main__":

    print(
        "ALHIKAM BOT STARTED..."
    )

    application.run_polling(
        drop_pending_updates=True
    )