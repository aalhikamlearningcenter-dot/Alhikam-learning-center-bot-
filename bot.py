# ==========================================================
# ALHIKAM LEARNING CENTER V2
# bot.py
# ==========================================================

import os
from urllib.parse import urlencode

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


# ==========================================================
# CONFIG
# ==========================================================

BOT_TOKEN = os.getenv(
    "BOT_TOKEN"
)

APP_URL = os.getenv(
    "APP_URL",
    "https://precious-trust-production-956b.up.railway.app"
).rstrip("/")


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


    # ======================================================
    # TELEGRAM INFORMATION
    # ======================================================

    telegram_id = str(
        user.id
    )

    telegram_name = (
        user.first_name
        or ""
    ).strip()

    telegram_username = (
        user.username
        or ""
    ).strip()


    # ======================================================
    # LOG
    # ======================================================

    print(
        "TELEGRAM /START | "
        f"ID={telegram_id} | "
        f"NAME={telegram_name} | "
        f"USERNAME={telegram_username}"
    )


    # ======================================================
    # CHECK EXISTING STUDENT
    # ======================================================

    try:

        student = (
            get_student_by_telegram_id(
                user.id
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


        # --------------------------------------------------
        # SEND LINKS AGAIN
        # --------------------------------------------------

        try:

            faculty = (
                student.get(
                    "faculty",
                    ""
                )
                or student.get(
                    "course",
                    ""
                )
                or ""
            )


            await send_student_links(

                telegram_id,

                faculty

            )


        except Exception as e:

            print(
                "Could not resend Telegram links:",
                e
            )


            await update.message.reply_text(

                "⚠️ I could not create your invitation "
                "links right now.\n\n"
                "Please contact ALHIKAM support."
            )


        return


    # ======================================================
    # PAYMENT URL
    # ======================================================

    payment_params = {

        "telegram_id":
            telegram_id,

        "telegram_name":
            telegram_name,

        "telegram_username":
            telegram_username,

    }


    payment_url = (

        f"{APP_URL}/payment?"
        + urlencode(
            payment_params
        )

    )


    # ======================================================
    # BUTTON
    # ======================================================

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


    # ======================================================
    # SEND PAYMENT MESSAGE
    # ======================================================

    await update.message.reply_text(

        f"🎓 Welcome to ALHIKAM Learning Center\n\n"

        f"Hello {telegram_name},\n\n"

        "You are about to register as an "
        "ALHIKAM student.\n\n"

        "🔗 Your Telegram account will automatically "
        "be connected to your registration.\n\n"

        "💳 Tap the button below to choose your "
        "payment plan and continue registration.",

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


# ==========================================================
# COMMAND HANDLER
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
        "=================================================="
    )

    print(
        "ALHIKAM TELEGRAM BOT STARTING..."
    )

    print(
        "=================================================="
    )


    application.run_polling(

        drop_pending_updates=True

    )