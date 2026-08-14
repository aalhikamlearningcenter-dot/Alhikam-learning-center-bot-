# ==========================================================
# ALHIKAM LEARNING CENTER V2
# bot.py
# TELEGRAM BOT
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

from database import get_student_by_telegram_id
from telegram_service import send_student_links
from config import BOT_TOKEN, APP_URL


# ==========================================================
# START COMMAND
# ==========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    if not user:
        return

    # ======================================================
    # CHECK EXISTING STUDENT
    # ======================================================

    student = get_student_by_telegram_id(
        user.id
    )

    # ======================================================
    # ALREADY REGISTERED
    # ======================================================

    if (
        student
        and student["registration_completed"] == 1
    ):

        await update.message.reply_text(
            "🎓 Welcome back to ALHIKAM Learning Center.\n\n"
            "Your registration is already completed.\n"
            "I am generating your class links..."
        )

        try:

            await send_student_links(
                user.id,
                student["course"]
            )

        except Exception as e:

            print(
                "Send student links error:",
                e
            )

            await update.message.reply_text(
                "⚠️ We could not generate your links right now.\n"
                "Please try again later."
            )

        return

    # ======================================================
    # REGISTRATION LINK
    # ======================================================

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

    reply_markup = InlineKeyboardMarkup(
        keyboard
    )

    await update.message.reply_text(

        f"""
🎓 Welcome to ALHIKAM Learning Center

Hello {user.first_name} 👋

✅ Your payment has been verified.

Please tap the button below to complete your registration.
""",

        reply_markup=reply_markup

    )


# ==========================================================
# APPLICATION
# ==========================================================

application = (

    Application
    .builder()
    .token(BOT_TOKEN)
    .build()

)


# ==========================================================
# HANDLER
# ==========================================================

application.add_handler(

    CommandHandler(
        "start",
        start
    )

)


# ==========================================================
# RUN BOT
# ==========================================================

if __name__ == "__main__":

    print(
        "ALHIKAM BOT STARTED..."
    )

    application.run_polling(
        drop_pending_updates=True
    )