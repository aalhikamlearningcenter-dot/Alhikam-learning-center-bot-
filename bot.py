# ==========================================================
# ALHIKAM LEARNING CENTER V2
# bot.py
#
# PAYMENT
#   ↓
# REGISTRATION
#   ↓
# START ALHIKAM BOT
#   ↓
# BOT RECEIVES TX_REF
#   ↓
# FIND STUDENT
#   ↓
# CHECK FACULTY
#   ↓
# SEND TELEGRAM LINKS
#   ↓
# SEND WHATSAPP COMMUNITY
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
    get_student_by_tx_ref,
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
# SQLITE ROW HELPER
# ==========================================================

def row_get(
    row,
    key,
    default=""
):

    if row is None:

        return default


    # ------------------------------------------------------
    # SQLITE ROW
    # ------------------------------------------------------

    try:

        if key in row.keys():

            value = row[key]

            if value is None:

                return default

            return value

    except Exception:

        pass


    # ------------------------------------------------------
    # DICT
    # ------------------------------------------------------

    try:

        return row.get(
            key,
            default
        )

    except Exception:

        return default


# ==========================================================
# GET FACULTY
# ==========================================================

def get_student_faculty(
    student
):

    faculty = (

        row_get(
            student,
            "faculty",
            ""
        )

        or

        row_get(
            student,
            "course",
            ""
        )

        or ""

    )


    return str(
        faculty
    ).strip()


# ==========================================================
# SEND LINKS
# ==========================================================

async def send_links_to_student(
    update,
    telegram_id,
    faculty,
    tx_ref=""
):

    try:

        result = await send_student_links(

            telegram_id,

            faculty

        )


        total_links = len(
            result
        )


        print(
            "=================================================="
        )

        print(
            "STUDENT LINKS SENT"
        )

        print(
            f"TX_REF={tx_ref}"
        )

        print(
            f"TELEGRAM_ID={telegram_id}"
        )

        print(
            f"FACULTY={faculty}"
        )

        print(
            f"TOTAL_LINKS_SENT={total_links}"
        )

        print(
            "=================================================="
        )


        if total_links > 0:

            await update.message.reply_text(

                "✅ Your ALHIKAM class links have "
                "been sent successfully.\n\n"

                "📚 Please check the message above.\n\n"

                "🏠 Join the Main Group.\n"
                "📢 Join the Announcement Channel.\n"
                "🎓 Join your Faculty.\n"
                "📚 Join all your subjects.\n"
                "💬 Join the WhatsApp Community.\n\n"

                "⚠️ Telegram invitation links are "
                "limited to one student and expire "
                "after 10 minutes."

            )


        else:

            await update.message.reply_text(

                "⚠️ Your registration is successful, "
                "but no invitation link was created.\n\n"

                "Please contact ALHIKAM support."

            )


        return True


    except Exception as e:

        print(
            "=================================================="
        )

        print(
            "TELEGRAM LINKS ERROR"
        )

        print(
            f"TX_REF={tx_ref}"
        )

        print(
            f"TELEGRAM_ID={telegram_id}"
        )

        print(
            f"FACULTY={faculty}"
        )

        print(
            f"ERROR={repr(e)}"
        )

        print(
            "=================================================="
        )


        await update.message.reply_text(

            "⚠️ Your registration is successful, "
            "but I could not send your class links "
            "right now.\n\n"

            "Please contact ALHIKAM support."

        )


        return False


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
    # TELEGRAM INFORMATION
    # ======================================================

    telegram_id = str(
        user.id
    ).strip()


    telegram_name = (
        user.first_name
        or ""
    ).strip()


    telegram_username = (
        user.username
        or ""
    ).strip()


    # ======================================================
    # TX_REF
    # ======================================================

    tx_ref = ""


    if context.args:

        tx_ref = (

            context.args[0]
            or ""

        ).strip()


    # ======================================================
    # LOG
    # ======================================================

    print(
        "=================================================="
    )

    print(
        "TELEGRAM /START"
    )

    print(
        f"ID={telegram_id}"
    )

    print(
        f"NAME={telegram_name}"
    )

    print(
        f"USERNAME={telegram_username}"
    )

    print(
        f"TX_REF={tx_ref}"
    )

    print(
        "=================================================="
    )


    # ======================================================
    # CASE 1
    # START WITH TX_REF
    # ======================================================

    if tx_ref:

        student = None


        try:

            student = (
                get_student_by_tx_ref(
                    tx_ref
                )
            )

        except Exception as e:

            print(
                "TX_REF lookup error:",
                repr(e)
            )


        if not student:

            await update.message.reply_text(

                "⚠️ We could not find your "
                "ALHIKAM registration.\n\n"

                "Please make sure you opened Telegram "
                "using the button from your registration "
                "success page.\n\n"

                "If the problem continues, please "
                "contact ALHIKAM support."

            )

            return


        # --------------------------------------------------
        # REGISTRATION CHECK
        # --------------------------------------------------

        registration_completed = int(

            row_get(
                student,
                "registration_completed",
                0
            )
            or 0

        )


        if registration_completed != 1:

            await update.message.reply_text(

                "⚠️ Your ALHIKAM registration has not "
                "been completed yet.\n\n"

                "Please complete your registration first."

            )

            return


        # --------------------------------------------------
        # FACULTY
        # --------------------------------------------------

        faculty = get_student_faculty(
            student
        )


        if not faculty:

            await update.message.reply_text(

                "⚠️ Your faculty information could "
                "not be found.\n\n"

                "Please contact ALHIKAM support."

            )

            return


        # --------------------------------------------------
        # STUDENT NAME
        # --------------------------------------------------

        student_name = (

            row_get(
                student,
                "full_name",
                ""
            )

            or telegram_name

            or "Student"

        ).strip()


        # --------------------------------------------------
        # WELCOME
        # --------------------------------------------------

        await update.message.reply_text(

            f"🎉 Congratulations {student_name}!\n\n"

            "✅ Your ALHIKAM registration has been "
            "successfully connected.\n\n"

            f"🎓 Faculty: {faculty}\n\n"

            "📚 I am preparing your class links..."

        )


        # --------------------------------------------------
        # SEND LINKS
        # --------------------------------------------------

        await send_links_to_student(

            update,

            telegram_id,

            faculty,

            tx_ref

        )


        return


    # ======================================================
    # CASE 2
    # NORMAL /START
    # ======================================================

    try:

        student = (
            get_student_by_telegram_id(
                telegram_id
            )
        )

    except Exception as e:

        print(
            "Telegram student lookup error:",
            repr(e)
        )

        student = None


    # ======================================================
    # EXISTING STUDENT
    # ======================================================

    if student:

        registration_completed = int(

            row_get(
                student,
                "registration_completed",
                0
            )
            or 0

        )


        if registration_completed == 1:

            faculty = get_student_faculty(
                student
            )


            await update.message.reply_text(

                "🎓 Welcome back to ALHIKAM "
                "Learning Center.\n\n"

                f"Hello {telegram_name},\n\n"

                "✅ Your registration is already "
                "completed.\n\n"

                "🔗 I will send your class links again."

            )


            await send_links_to_student(

                update,

                telegram_id,

                faculty

            )


            return


    # ======================================================
    # NEW STUDENT
    # ======================================================

    payment_params = {

        "telegram_id":
            telegram_id,

        "telegram_name":
            telegram_name,

        "telegram_username":
            telegram_username,

    }


    # ======================================================
    # PAYMENT URL
    # ======================================================

    payment_url = (

        f"{APP_URL}/payment?"

        +

        urlencode(
            payment_params
        )

    )


    # ======================================================
    # PAYMENT BUTTON
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
    # MESSAGE
    # ======================================================

    await update.message.reply_text(

        f"🎓 Welcome to ALHIKAM Learning Center\n\n"

        f"Hello {telegram_name},\n\n"

        "You are about to register as an "
        "ALHIKAM student.\n\n"

        "🔗 Your Telegram account can be connected "
        "automatically to your registration.\n\n"

        "💳 Tap the button below to choose your "
        "payment plan and continue registration.",

        reply_markup=reply_markup

    )


# ==========================================================
# BOT TOKEN CHECK
# ==========================================================

if not BOT_TOKEN:

    raise RuntimeError(
        "BOT_TOKEN is missing."
    )


# ==========================================================
# APPLICATION
# ==========================================================

application = (

    Application
    .builder()
    .token(
        BOT_TOKEN
    )
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