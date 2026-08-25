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
# SEND TELEGRAM LINKS
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

BOT_TOKEN = os.getenv("BOT_TOKEN")

APP_URL = os.getenv(
    "APP_URL",
    "https://precious-trust-production-956b.up.railway.app"
).rstrip("/")


# ==========================================================
# SQLITE ROW HELPER
# ==========================================================
#
# sqlite3.Row ba shi da .get()
# Wannan helper zai yi aiki da:
#   - sqlite3.Row
#   - dict
#   - None
# ==========================================================

def row_get(row, key, default=""):

    if row is None:
        return default

    # sqlite3.Row
    try:

        if hasattr(row, "keys"):

            keys = row.keys()

            if key in keys:

                value = row[key]

                if value is None:
                    return default

                return value

    except Exception:
        pass

    # dictionary
    try:

        value = row.get(key, default)

        if value is None:
            return default

        return value

    except Exception:
        return default


# ==========================================================
# SAFE RESULT HELPER
# ==========================================================

def safe_result(result):

    if isinstance(result, dict):
        return result

    return {}


# ==========================================================
# START COMMAND
# ==========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    try:

        user = update.effective_user

        if not user:
            return


        # ==================================================
        # TELEGRAM INFORMATION
        # ==================================================

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


        # ==================================================
        # GET TX_REF FROM TELEGRAM DEEP LINK
        # ==================================================

        tx_ref = ""

        if context.args:

            tx_ref = (
                context.args[0]
                or ""
            ).strip()


        # ==================================================
        # LOG
        # ==================================================

        print(
            "=================================================="
        )

        print("TELEGRAM /START")

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


        # ==================================================
        # CASE 1
        # START WITH TX_REF
        #
        # Wannan shi ne:
        #
        # External payment page
        #       ↓
        # Registration
        #       ↓
        # Telegram deep link
        #       ↓
        # /start ALHIKAM_xxxxx
        #
        # Ba sai telegram_id ya kasance a payment URL ba.
        # TX_REF zai nemo student.
        # ==================================================

        if tx_ref:

            print(
                f"Looking for student by TX_REF: {tx_ref}"
            )


            student = None


            # ------------------------------------------------
            # FIND STUDENT
            # ------------------------------------------------

            try:

                student = get_student_by_tx_ref(
                    tx_ref
                )

            except Exception as e:

                print(
                    "TX_REF student lookup error:",
                    repr(e)
                )

                student = None


            # ------------------------------------------------
            # STUDENT NOT FOUND
            # ------------------------------------------------

            if not student:

                await update.message.reply_text(

                    "⚠️ We could not find your ALHIKAM "
                    "registration.\n\n"

                    "Please make sure you opened Telegram "
                    "using the button from your registration "
                    "success page.\n\n"

                    "If the problem continues, please contact "
                    "ALHIKAM support."

                )

                return


            print(
                "Student found successfully."
            )


            # ------------------------------------------------
            # CHECK REGISTRATION
            # ------------------------------------------------

            registration_completed = int(

                row_get(
                    student,
                    "registration_completed",
                    0
                )
                or 0

            )


            print(
                "Registration completed:",
                registration_completed
            )


            if registration_completed != 1:

                await update.message.reply_text(

                    "⚠️ Your ALHIKAM registration has not "
                    "been completed yet.\n\n"

                    "Please complete your registration first."

                )

                return


            # ------------------------------------------------
            # GET FACULTY / COURSE
            # ------------------------------------------------

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

            ).strip()


            print(
                f"Faculty/Course={faculty}"
            )


            # ------------------------------------------------
            # STUDENT NAME
            # ------------------------------------------------

            student_name = (

                row_get(
                    student,
                    "full_name",
                    ""
                )

                or

                telegram_name

                or

                "Student"

            ).strip()


            # ------------------------------------------------
            # CONNECT TELEGRAM ACCOUNT
            # ------------------------------------------------

            try:

                from database import (
                    connect_student_to_telegram
                )

                connect_student_to_telegram(

                    tx_ref,

                    telegram_id,

                    telegram_username,

                    telegram_name

                )

                print(
                    "Telegram account connected successfully."
                )

            except Exception as e:

                print(
                    "Could not connect Telegram account:",
                    repr(e)
                )


            # ------------------------------------------------
            # WELCOME MESSAGE
            # ------------------------------------------------

            await update.message.reply_text(

                f"🎉 Congratulations {student_name}!\n\n"

                "✅ Your ALHIKAM registration has been "
                "successfully connected to your Telegram "
                "account.\n\n"

                "📚 We are now preparing your class "
                "invitation links..."

            )


            # ------------------------------------------------
            # SEND SUBJECT / CLASS LINKS
            # ------------------------------------------------

            try:

                result = await send_student_links(

                    telegram_id,

                    faculty

                )


                result = safe_result(result)


                successful_links = result.get(
                    "successful_links",
                    []
                ) or []


                failed_links = result.get(
                    "failed_links",
                    []
                ) or []


                print(
                    "=================================================="
                )

                print(
                    "STUDENT LINKS RESULT"
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
                    f"SUCCESSFUL={len(successful_links)}"
                )

                print(
                    f"FAILED={len(failed_links)}"
                )

                print(
                    "=================================================="
                )


                # --------------------------------------------
                # LINKS SENT
                # --------------------------------------------

                if successful_links:

                    await update.message.reply_text(

                        "✅ Your ALHIKAM class invitation "
                        "links have been sent successfully.\n\n"

                        "📚 Please check the messages above "
                        "and join your Main Group, Faculty "
                        "and Subject classes."

                    )

                else:

                    await update.message.reply_text(

                        "⚠️ Your registration is successful, "
                        "but no class invitation link could "
                        "be sent right now.\n\n"

                        "Please contact ALHIKAM support."

                    )


            except Exception as e:

                print(
                    "Telegram links error:",
                    repr(e)
                )


                await update.message.reply_text(

                    "⚠️ Your registration is successful, "
                    "but I could not send your class links "
                    "right now.\n\n"

                    "Please contact ALHIKAM support."

                )


            return


        # ==================================================
        # CASE 2
        # NORMAL /START WITHOUT TX_REF
        # ==================================================

        print(
            "Normal /start without TX_REF"
        )


        # ==================================================
        # FIND EXISTING STUDENT BY TELEGRAM ID
        # ==================================================

        try:

            student = get_student_by_telegram_id(
                telegram_id
            )

        except Exception as e:

            print(
                "Telegram student lookup error:",
                repr(e)
            )

            student = None


        # ==================================================
        # EXISTING REGISTERED STUDENT
        # ==================================================

        registration_completed = 0


        if student:

            registration_completed = int(

                row_get(
                    student,
                    "registration_completed",
                    0
                )
                or 0

            )


        if (

            student

            and

            registration_completed == 1

        ):

            await update.message.reply_text(

                "🎓 Welcome back to ALHIKAM Learning Center\n\n"

                f"Hello {telegram_name},\n\n"

                "✅ Your registration is already completed.\n\n"

                "🔗 I will send your invitation links again."

            )


            # ------------------------------------------------
            # GET FACULTY
            # ------------------------------------------------

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

            ).strip()


            # ------------------------------------------------
            # SEND LINKS AGAIN
            # ------------------------------------------------

            try:

                result = await send_student_links(

                    telegram_id,

                    faculty

                )


                result = safe_result(result)


                successful_links = result.get(
                    "successful_links",
                    []
                ) or []


                print(
                    "LINKS RESENT | "
                    f"TELEGRAM_ID={telegram_id} | "
                    f"FACULTY={faculty} | "
                    f"SUCCESS={len(successful_links)}"
                )


            except Exception as e:

                print(
                    "Could not resend Telegram links:",
                    repr(e)
                )


                await update.message.reply_text(

                    "⚠️ I could not send your invitation "
                    "links right now.\n\n"

                    "Please contact ALHIKAM support."

                )


            return


        # ==================================================
        # NEW STUDENT
        # ==================================================

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


        # ==================================================
        # PAYMENT BUTTON
        # ==================================================

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


        # ==================================================
        # SEND PAYMENT MESSAGE
        # ==================================================

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


    # ======================================================
    # FINAL PROTECTION
    # ======================================================

    except Exception as e:

        print(
            "=================================================="
        )

        print(
            "UNHANDLED /START ERROR"
        )

        print(
            repr(e)
        )

        print(
            "=================================================="
        )


        try:

            if update.message:

                await update.message.reply_text(

                    "⚠️ Something went wrong while "
                    "processing your request.\n\n"

                    "Your payment/registration data has "
                    "not been deleted.\n\n"

                    "Please try /start again."

                )

        except Exception as reply_error:

            print(
                "Could not send error message:",
                repr(reply_error)
            )


# ==========================================================
# ERROR HANDLER
# ==========================================================

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE
):

    print(
        "=================================================="
    )

    print(
        "TELEGRAM BOT ERROR"
    )

    print(
        repr(context.error)
    )

    print(
        "=================================================="
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
# ERROR HANDLER REGISTRATION
# ==========================================================

application.add_error_handler(
    error_handler
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