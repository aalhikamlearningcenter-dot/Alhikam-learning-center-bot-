# ==========================================================
# ALHIKAM LEARNING CENTER V2
# bot.py
# ==========================================================

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

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

from config import (
    BOT_TOKEN,
    APP_URL,
)


# ==========================================================
# START
# ==========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.effective_user:
        return

    user = update.effective_user

    student = get_student_by_telegram_id(
        user.id
    )

    # ------------------------------------------------------
    # ALREADY REGISTERED
    # ------------------------------------------------------

    if (
        student
        and
        student["registration_completed"] == 1
        and
        student["payment_status"] == "Successful"
    ):

        try:

            await send_student_links(

                user.id,

                student["course"]

            )

        except Exception as e:

            print(
                "Could not send Telegram links:",
                e
            )

            await update.message.reply_text(
                "⚠️ We could not generate your class links right now. Please try /start again."
            )

        return

    # ------------------------------------------------------
    # REGISTRATION LINK
    # ------------------------------------------------------

    register_link = (

        f"{APP_URL}/register"

        f"?telegram_id={user.id}"

        f"&telegram_name={user.first_name}"

        f"&telegram_username="
        f"{user.username or ''}"

    )

    keyboard = [

        [

            InlineKeyboardButton(

                "📝 Continue Registration",

                url=register_link

            )

        ]

    ]

    reply_markup = InlineKeyboardMarkup(
        keyboard
    )

    await update.message.reply_text(

        f"""
🎓 Welcome to ALHIKAM Learning Center

Hello {user.first_name},

Please tap the button below to continue your registration.

If you have already paid, your payment will be connected to your registration.
""",

        reply_markup=reply_markup

    )


# ==========================================================
# APPLICATION
# ==========================================================

if not BOT_TOKEN:

    raise RuntimeError(
        "BOT_TOKEN is not set."
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