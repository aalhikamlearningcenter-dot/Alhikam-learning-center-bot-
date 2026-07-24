import os
import uuid
import hmac
import threading
import requests

from flask import Flask, request, jsonify

from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from telegram.error import TelegramError


# ============================================================
# SETTINGS
# ============================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")

FLW_SECRET_KEY = os.getenv("FLW_SECRET_KEY")

FLUTTERWAVE_SECRET_HASH = os.getenv(
    "FLUTTERWAVE_SECRET_HASH"
)

SHEET_URL = os.getenv(
    "SHEET_URL",
    "https://script.google.com/macros/s/AKfycby5lIhCjoD0NaPZ-HHQ9hapAKlstypQvxyWK22qHblJr4uGBrPn5FoGG1TP-EvIfteo9w/exec"
)

RAILWAY_URL = os.getenv(
    "RAILWAY_URL",
    "https://precious-trust-production-956b.up.railway.app"
)

PORT = int(
    os.getenv(
        "PORT",
        "8080"
    )
)


# ============================================================
# MAIN TELEGRAM GROUP
# ============================================================

MAIN_GROUP_ID = -1004384506380


# ============================================================
# PAYMENT PLANS
# ============================================================

PAYMENT_PLANS = {

    "1": {
        "name": "1 Month",
        "amount": 3600,
    },

    "2": {
        "name": "2 Months",
        "amount": 6800,
    },

    "3": {
        "name": "3 Months",
        "amount": 10000,
    },

    "4": {
        "name": "4 Months",
        "amount": 13200,
    },

    "5": {
        "name": "5 Months",
        "amount": 16500,
    },

    "6": {
        "name": "6 Months",
        "amount": 20000,
    },
}


# ============================================================
# FLASK WEB SERVER
# ============================================================

web_app = Flask(__name__)


@web_app.route("/", methods=["GET"])
def home():

    return jsonify({
        "status": "online",
        "bot": "ALHIKAM Learning Center Bot",
        "webhook": "/webhook/flutterwave"
    })


@web_app.route("/health", methods=["GET"])
def health():

    return jsonify({
        "status": "healthy"
    })


# ============================================================
# FLUTTERWAVE WEBHOOK
# ============================================================

@web_app.route(
    "/webhook/flutterwave",
    methods=["POST"]
)
def flutterwave_webhook():

    # --------------------------------------------------------
    # VERIFY SECRET HASH
    # --------------------------------------------------------

    incoming_hash = request.headers.get(
        "verif-hash"
    )

    if not FLUTTERWAVE_SECRET_HASH:

        print(
            "ERROR: FLUTTERWAVE_SECRET_HASH is missing."
        )

        return jsonify({
            "status": "error",
            "message": "Webhook secret hash not configured"
        }), 500


    if not incoming_hash:

        print(
            "Webhook rejected: Missing verif-hash."
        )

        return jsonify({
            "status": "error",
            "message": "Missing verification hash"
        }), 401


    if not hmac.compare_digest(
        incoming_hash,
        FLUTTERWAVE_SECRET_HASH
    ):

        print(
            "Webhook rejected: Invalid secret hash."
        )

        return jsonify({
            "status": "error",
            "message": "Invalid verification hash"
        }), 401


    # --------------------------------------------------------
    # GET JSON DATA
    # --------------------------------------------------------

    data = request.get_json(
        silent=True
    )


    if not data:

        print(
            "Webhook received without JSON data."
        )

        return jsonify({
            "status": "error",
            "message": "Invalid JSON"
        }), 400


    print(
        "================================"
    )

    print(
        "FLUTTERWAVE WEBHOOK RECEIVED"
    )

    print(
        "EVENT:",
        data.get("event")
    )

    print(
        "DATA:",
        data
    )

    print(
        "================================"
    )


    # --------------------------------------------------------
    # PAYMENT DATA
    # --------------------------------------------------------

    payment_data = data.get(
        "data",
        {}
    )


    status = payment_data.get(
        "status"
    )

    amount = payment_data.get(
        "amount"
    )

    currency = payment_data.get(
        "currency"
    )

    transaction_id = payment_data.get(
        "id"
    )

    tx_ref = payment_data.get(
        "tx_ref"
    )


    print(
        "Payment Status:",
        status
    )

    print(
        "Amount:",
        amount
    )

    print(
        "Currency:",
        currency
    )

    print(
        "Transaction ID:",
        transaction_id
    )

    print(
        "Transaction Reference:",
        tx_ref
    )


    # --------------------------------------------------------
    # ONLY SUCCESSFUL PAYMENTS
    # --------------------------------------------------------

    if status != "successful":

        print(
            "Payment is not successful."
        )

        return jsonify({
            "status": "ignored"
        }), 200


    # --------------------------------------------------------
    # GET TELEGRAM USER ID FROM TX REF
    # --------------------------------------------------------

    telegram_id = None


    if tx_ref:

        try:

            parts = tx_ref.split("_")

            # Expected:
            # ALHIKAM_TELEGRAMID_UUID

            if len(parts) >= 3:

                telegram_id = int(
                    parts[1]
                )

        except Exception as e:

            print(
                "Telegram ID extraction error:",
                e
            )


    if not telegram_id:

        print(
            "ERROR: Telegram ID not found in tx_ref."
        )

        return jsonify({
            "status": "error",
            "message": "Telegram ID not found"
        }), 400


    print(
        "Telegram User ID:",
        telegram_id
    )


    # --------------------------------------------------------
    # START ASYNC ACCESS PROCESS
    # --------------------------------------------------------

    threading.Thread(

        target=process_successful_payment,

        args=(
            telegram_id,
            payment_data
        ),

        daemon=True

    ).start()


    return jsonify({
        "status": "success"
    }), 200


# ============================================================
# PROCESS SUCCESSFUL PAYMENT
# ============================================================

def process_successful_payment(
    telegram_id,
    payment_data
):

    try:

        # Get payment plan
        amount = payment_data.get(
            "amount",
            "N/A"
        )

        tx_ref = payment_data.get(
            "tx_ref",
            "N/A"
        )


        # Run async Telegram access
        asyncio_run_payment_access(

            telegram_id,

            amount,

            tx_ref
        )


    except Exception as e:

        print(
            "Payment processing error:",
            e
        )


# ============================================================
# ASYNC RUNNER FOR PAYMENT ACCESS
# ============================================================

def asyncio_run_payment_access(
    telegram_id,
    amount,
    tx_ref
):

    import asyncio

    asyncio.run(

        send_payment_access(

            telegram_id,

            amount,

            tx_ref
        )
    )


# ============================================================
# SEND PAYMENT ACCESS
# ============================================================

async def send_payment_access(
    telegram_id,
    amount,
    tx_ref
):

    global telegram_bot_app


    if telegram_bot_app is None:

        print(
            "Telegram application is not ready."
        )

        return


    try:

        # ----------------------------------------------------
        # CREATE ONE-TIME INVITE LINK
        # ----------------------------------------------------

        invite_link = await telegram_bot_app.bot.create_chat_invite_link(

            chat_id=MAIN_GROUP_ID,

            member_limit=1,

            name=f"ALHIKAM-{telegram_id}"

        )


        join_url = invite_link.invite_link


        print(
            "Invite link created:",
            join_url
        )


        # ----------------------------------------------------
        # SEND MESSAGE TO STUDENT
        # ----------------------------------------------------

        await telegram_bot_app.bot.send_message(

            chat_id=telegram_id,

            text=(

                "🎉 *PAYMENT SUCCESSFUL!*\n\n"

                "🎓 ALHIKAM Learning Center\n\n"

                f"💰 Amount Paid: ₦{amount:,}\n\n"

                "✅ Your payment has been confirmed.\n\n"

                "📚 Your class access is now ready.\n\n"

                "👇 Click the button below to join your class:\n\n"

                "⚠️ This invitation link is for you only."

            ),

            parse_mode="Markdown",

            reply_markup=InlineKeyboardMarkup([

                [

                    InlineKeyboardButton(

                        "🎓 JOIN ALHIKAM CLASS",

                        url=join_url

                    )

                ]

            ])

        )


        print(
            "Access sent successfully to:",
            telegram_id
        )


    except TelegramError as e:

        print(
            "Telegram access error:",
            e
        )


    except Exception as e:

        print(
            "General access error:",
            e
        )


# ============================================================
# RUN WEB SERVER
# ============================================================

def run_web_server():

    print(
        "Starting Flask Web Server..."
    )

    web_app.run(

        host="0.0.0.0",

        port=PORT

    )


# ============================================================
# MENUS
# ============================================================

MAIN_MENU = [

    [
        "📚 Courses",
        "📝 CBT Practice"
    ],

    [
        "👤 Student Registration",
        "💳 Pay School Fees"
    ],

    [
        "📞 Contact Us",
        "ℹ️ About Us"
    ]

]


PAYMENT_MENU = [

    [
        "💳 1 Month",
        "💳 2 Months"
    ],

    [
        "💳 3 Months",
        "💳 4 Months"
    ],

    [
        "💳 5 Months",
        "💳 6 Months"
    ],

    [
        "🔙 Back to Main Menu"
    ]

]


COURSE_MENU = [

    [
        "🎯 JAMB Science",
        "🎨 JAMB Arts"
    ],

    [
        "📘 WAEC",
        "📕 NECO"
    ],

    [
        "💻 CBT Training"
    ],

    [
        "🔙 Back to Main Menu"
    ]

]


# ============================================================
# START
# ============================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data.clear()


    keyboard = ReplyKeyboardMarkup(

        MAIN_MENU,

        resize_keyboard=True

    )


    await update.message.reply_text(

        "🎓 *ALHIKAM Learning Center*\n\n"

        "Welcome to ALHIKAM Learning Center.\n\n"

        "We provide educational support for:\n"

        "• JAMB\n"

        "• WAEC\n"

        "• NECO\n"

        "• CBT Training\n\n"

        "Please choose an option below.",

        parse_mode="Markdown",

        reply_markup=keyboard

    )


# ============================================================
# CANCEL
# ============================================================

async def cancel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data.clear()


    keyboard = ReplyKeyboardMarkup(

        MAIN_MENU,

        resize_keyboard=True

    )


    await update.message.reply_text(

        "❌ Registration cancelled.\n\n"

        "Please choose an option below.",

        reply_markup=keyboard

    )


# ============================================================
# CREATE FLUTTERWAVE CHECKOUT
# ============================================================

async def create_flutterwave_checkout(

    update,

    context,

    plan_number

):

    user = update.effective_user


    plan = PAYMENT_PLANS.get(

        plan_number

    )


    if not plan:

        await update.message.reply_text(

            "❌ Invalid payment plan."

        )

        return


    if not FLW_SECRET_KEY:

        await update.message.reply_text(

            "❌ Payment system is temporarily unavailable.\n\n"

            "Please contact ALHIKAM Learning Center."

        )

        print(
            "ERROR: FLW_SECRET_KEY missing."
        )

        return


    telegram_id = user.id


    unique_ref = (

        f"ALHIKAM_"

        f"{telegram_id}_"

        f"{uuid.uuid4().hex}"

    )


    checkout_url = (

        "https://api.flutterwave.com/v3/payments"

    )


    payload = {

        "tx_ref":
            unique_ref,

        "amount":
            plan["amount"],

        "currency":
            "NGN",

        "redirect_url":
            f"{RAILWAY_URL}/payment-success",

        "customer": {

            "email":
                f"telegram{telegram_id}@alhikam.com",

            "name":
                user.full_name or "ALHIKAM Student",

        },

        "customizations": {

            "title":
                "ALHIKAM Learning Center",

            "description":
                f"{plan['name']} Training",

            "logo":
                ""

        }

    }


    headers = {

        "Authorization":
            f"Bearer {FLW_SECRET_KEY}",

        "Content-Type":
            "application/json"

    }


    try:

        response = requests.post(

            checkout_url,

            json=payload,

            headers=headers,

            timeout=30

        )


        result = response.json()


        print(
            "Flutterwave Checkout Response:",
            result
        )


        if (

            response.status_code == 200

            and result.get("status") == "success"

        ):

            payment_link = (

                result

                .get("data", {})

                .get("link")

            )


            if payment_link:

                await update.message.reply_text(

                    f"💳 *{plan['name'].upper()} PAYMENT*\n\n"

                    f"💰 Amount: ₦{plan['amount']:,}\n\n"

                    "Click the button below to pay securely:\n\n"

                    "After successful payment, "

                    "your Telegram class access will be "

                    "sent automatically.",

                    parse_mode="Markdown",

                    reply_markup=InlineKeyboardMarkup([

                        [

                            InlineKeyboardButton(

                                "💳 PAY NOW",

                                url=payment_link

                            )

                        ]

                    ])

                )

                return


        print(
            "Flutterwave payment link creation failed."
        )


        await update.message.reply_text(

            "❌ We could not create your payment link.\n\n"

            "Please try again."

        )


    except Exception as e:

        print(

            "Flutterwave API Error:",

            e

        )


        await update.message.reply_text(

            "❌ Payment system error.\n\n"

            "Please try again later."

        )


# ============================================================
# SAVE REGISTRATION
# ============================================================

async def save_registration(

    update,

    context

):

    data = {

        "telegram_id":
            update.effective_user.id,

        "username":
            update.effective_user.username or "",

        "full_name":
            context.user_data.get(
                "full_name",
                ""
            ),

        "phone":
            context.user_data.get(
                "phone",
                ""
            ),

        "email":
            context.user_data.get(
                "email",
                ""
            ),

        "course":
            context.user_data.get(
                "course",
                ""
            )

    }


    try:

        response = requests.post(

            SHEET_URL,

            json=data,

            timeout=15

        )


        print(

            "Google Sheet Response:",

            response.text

        )


    except Exception as e:

        print(

            "Google Sheet Error:",

            e

        )


# ============================================================
# MAIN MESSAGE HANDLER
# ============================================================

async def menu_handler(

    update: Update,

    context: ContextTypes.DEFAULT_TYPE

):

    if not update.message:

        return


    text = update.message.text


    # --------------------------------------------------------
    # REGISTRATION STEPS
    # --------------------------------------------------------

    step = context.user_data.get(

        "step"

    )


    if step == "full_name":

        context.user_data[
            "full_name"
        ] = text


        context.user_data[
            "step"
        ] = "phone"


        await update.message.reply_text(

            "📱 Please enter your Phone Number:"

        )


        return


    if step == "phone":

        context.user_data[
            "phone"
        ] = text


        context.user_data[
            "step"
        ] = "email"


        await update.message.reply_text(

            "📧 Please enter your Email Address:"

        )


        return


    if step == "email":

        context.user_data[
            "email"
        ] = text


        context.user_data[
            "step"
        ] = "course"


        await update.message.reply_text(

            "📚 Please type your Course.\n\n"

            "Example:\n"

            "JAMB Science\n"

            "JAMB Arts\n"

            "WAEC\n"

            "NECO"

        )


        return


    if step == "course":

        context.user_data[
            "course"
        ] = text


        await save_registration(

            update,

            context

        )


        full_name = context.user_data.get(

            "full_name",

            ""

        )


        context.user_data.clear()


        await update.message.reply_text(

            "✅ *REGISTRATION COMPLETED*\n\n"

            f"👤 Name: {full_name}\n\n"

            "🎓 Thank you for registering with "

            "ALHIKAM Learning Center.",

            parse_mode="Markdown"

        )


        return


    # --------------------------------------------------------
    # STUDENT REGISTRATION
    # --------------------------------------------------------

    if text == "👤 Student Registration":

        context.user_data.clear()


        context.user_data[
            "step"
        ] = "full_name"


        await update.message.reply_text(

            "👤 *STUDENT REGISTRATION*\n\n"

            "Please enter your Full Name.\n\n"

            "Type /cancel to cancel.",

            parse_mode="Markdown"

        )


        return


    # --------------------------------------------------------
    # COURSES
    # --------------------------------------------------------

    if text == "📚 Courses":

        await update.message.reply_text(

            "📚 *ALHIKAM COURSES*\n\n"

            "Please select a course:",

            parse_mode="Markdown",

            reply_markup=ReplyKeyboardMarkup(

                COURSE_MENU,

                resize_keyboard=True

            )

        )


        return


    # --------------------------------------------------------
    # JAMB SCIENCE
    # --------------------------------------------------------

    if text == "🎯 JAMB Science":

        await update.message.reply_text(

            "🎯 *JAMB SCIENCE*\n\n"

            "• Mathematics\n"

            "• English Language\n"

            "• Physics\n"

            "• Chemistry\n"

            "• Biology\n"

            "• Agricultural Science",

            parse_mode="Markdown"

        )


        return


    # --------------------------------------------------------
    # JAMB ARTS
    # --------------------------------------------------------

    if text == "🎨 JAMB Arts":

        await update.message.reply_text(

            "🎨 *JAMB ARTS*\n\n"

            "• Use of English\n"

            "• Literature in English\n"

            "• Government\n"

            "• Economics\n"

            "• History\n"

            "• Hausa\n"

            "• Islamic Studies\n"

            "• CRS\n"

            "• Fine Arts",

            parse_mode="Markdown"

        )


        return


    # --------------------------------------------------------
    # WAEC
    # --------------------------------------------------------

    if text == "📘 WAEC":

        await update.message.reply_text(

            "📘 *WAEC PREPARATION*\n\n"

            "📚 Study materials\n"

            "📝 Practice questions\n"

            "💻 CBT training\n"

            "🎓 Examination guidance",

            parse_mode="Markdown"

        )


        return


    # --------------------------------------------------------
    # NECO
    # --------------------------------------------------------

    if text == "📕 NECO":

        await update.message.reply_text(

            "📕 *NECO PREPARATION*\n\n"

            "📚 Study materials\n"

            "📝 Practice questions\n"

            "💻 CBT training\n"

            "🎓 Examination guidance",

            parse_mode="Markdown"

        )


        return


    # --------------------------------------------------------
    # CBT
    # --------------------------------------------------------

    if text == "💻 CBT Training":

        await update.message.reply_text(

            "💻 *CBT TRAINING*\n\n"

            "📝 Practice Questions\n"

            "⏱️ Timed Tests\n"

            "📊 Results and Scores\n\n"

            "🚧 CBT system is under development.",

            parse_mode="Markdown"

        )


        return


    # --------------------------------------------------------
    # BACK
    # --------------------------------------------------------

    if text == "🔙 Back to Main Menu":

        await update.message.reply_text(

            "🏠 *MAIN MENU*",

            parse_mode="Markdown",

            reply_markup=ReplyKeyboardMarkup(

                MAIN_MENU,

                resize_keyboard=True

            )

        )


        return


    # --------------------------------------------------------
    # CBT PRACTICE
    # --------------------------------------------------------

    if text == "📝 CBT Practice":

        await update.message.reply_text(

            "📝 *CBT PRACTICE*\n\n"

            "JAMB • WAEC • NECO\n\n"

            "🚧 This feature is under development.",

            parse_mode="Markdown"

        )


        return


    # --------------------------------------------------------
    # PAYMENT MENU
    # --------------------------------------------------------

    if text == "💳 Pay School Fees":

        await update.message.reply_text(

            "💳 *ALHIKAM SCHOOL FEES PAYMENT*\n\n"

            "Select your preferred duration:",

            parse_mode="Markdown",

            reply_markup=ReplyKeyboardMarkup(

                PAYMENT_MENU,

                resize_keyboard=True

            )

        )


        return


    # --------------------------------------------------------
    # PAYMENT OPTIONS
    # --------------------------------------------------------

    if text.startswith("💳 ") and "Month" in text:

        month_number = (

            text

            .replace("💳 ", "")

            .split()[0]

        )


        await create_flutterwave_checkout(

            update,

            context,

            month_number

        )


        return


    # --------------------------------------------------------
    # CONTACT
    # --------------------------------------------------------

    if text == "📞 Contact Us":

        await update.message.reply_text(

            "📞 *CONTACT US*\n\n"

            "🎓 ALHIKAM Learning Center\n\n"

            "JAMB • WAEC • NECO • CBT Training",

            parse_mode="Markdown"

        )


        return


    # --------------------------------------------------------
    # ABOUT
    # --------------------------------------------------------

    if text == "ℹ️ About Us":

        await update.message.reply_text(

            "🎓 *ALHIKAM Learning Center*\n\n"

            "JAMB • WAEC • NECO • CBT Training\n\n"

            "We provide educational support "

            "and examination preparation for students.",

            parse_mode="Markdown"

        )


        return


    # --------------------------------------------------------
    # UNKNOWN
    # --------------------------------------------------------

    await update.message.reply_text(

        "❓ Please choose an option from the menu."

    )


# ============================================================
# GLOBAL TELEGRAM APPLICATION
# ============================================================

telegram_bot_app = None


# ============================================================
# MAIN
# ============================================================

def main():

    global telegram_bot_app


    # --------------------------------------------------------
    # CHECK VARIABLES
    # --------------------------------------------------------

    if not BOT_TOKEN:

        raise ValueError(

            "BOT_TOKEN is missing."

        )


    if not FLW_SECRET_KEY:

        raise ValueError(

            "FLW_SECRET_KEY is missing."

        )


    if not FLUTTERWAVE_SECRET_HASH:

        print(

            "WARNING: FLUTTERWAVE_SECRET_HASH is missing."

        )


    # --------------------------------------------------------
    # START WEB SERVER
    # --------------------------------------------------------

    web_thread = threading.Thread(

        target=run_web_server,

        daemon=True

    )


    web_thread.start()


    # --------------------------------------------------------
    # CREATE TELEGRAM APPLICATION
    # --------------------------------------------------------

    telegram_bot_app = (

        Application

        .builder()

        .token(BOT_TOKEN)

        .build()

    )


    # --------------------------------------------------------
    # COMMANDS
    # --------------------------------------------------------

    telegram_bot_app.add_handler(

        CommandHandler(

            "start",

            start

        )

    )


    telegram_bot_app.add_handler(

        CommandHandler(

            "cancel",

            cancel

        )

    )


    # --------------------------------------------------------
    # TEXT HANDLER
    # --------------------------------------------------------

    telegram_bot_app.add_handler(

        MessageHandler(

            filters.TEXT & ~filters.COMMAND,

            menu_handler

        )

    )


    # --------------------------------------------------------
    # LOGS
    # --------------------------------------------------------

    print(

        "================================"

    )


    print(

        "ALHIKAM Learning Center Bot "
        "is running..."

    )


    print(

        "Dynamic Flutterwave Checkout: ENABLED"

    )


    print(

        "Flutterwave Webhook:"

    )


    print(

        RAILWAY_URL +

        "/webhook/flutterwave"

    )


    print(

        "Main Group ID:",

        MAIN_GROUP_ID

    )


    print(

        "================================"

    )


    # --------------------------------------------------------
    # START BOT
    # --------------------------------------------------------

    telegram_bot_app.run_polling(

        drop_pending_updates=True

    )


# ============================================================
# START APPLICATION
# ============================================================

if __name__ == "__main__":

    main()