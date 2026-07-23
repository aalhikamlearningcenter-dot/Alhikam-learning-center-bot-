from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from telegram.error import TelegramError

from flask import Flask, request, jsonify
from threading import Thread

import os
import requests
import hmac


# ============================================================
# SETTINGS
# ============================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")

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


@web_app.route(
    "/webhook/flutterwave",
    methods=["POST"]
)
def flutterwave_webhook():

    # Get Flutterwave Secret Hash
    flutterwave_hash = request.headers.get(
        "verif-hash"
    )

    # Check Secret Hash
    if not FLUTTERWAVE_SECRET_HASH:

        print(
            "ERROR: FLUTTERWAVE_SECRET_HASH is missing"
        )

        return jsonify({
            "status": "error",
            "message": "Secret hash not configured"
        }), 500


    if not flutterwave_hash:

        print(
            "Webhook rejected: No verif-hash"
        )

        return jsonify({
            "status": "error",
            "message": "Missing verification hash"
        }), 401


    if not hmac.compare_digest(
        flutterwave_hash,
        FLUTTERWAVE_SECRET_HASH
    ):

        print(
            "Webhook rejected: Invalid Secret Hash"
        )

        return jsonify({
            "status": "error",
            "message": "Invalid verification hash"
        }), 401


    # Get webhook data
    data = request.get_json(
        silent=True
    )


    if not data:

        print(
            "Webhook received without JSON data"
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
    # SUCCESSFUL PAYMENT
    # --------------------------------------------------------

    if status == "successful":

        print(
            "PAYMENT SUCCESSFUL"
        )

        # Payment access automation
        # will be connected to Telegram
        # after user/payment mapping is finalized.

    else:

        print(
            "Payment is not successful"
        )


    return jsonify({
        "status": "success"
    }), 200


# ============================================================
# RUN WEB SERVER
# ============================================================

def run_web_server():

    port = int(
        os.getenv(
            "PORT",
            8080
        )
    )

    web_app.run(
        host="0.0.0.0",
        port=port
    )


# ============================================================
# CHANNEL IDS
# ============================================================

CHANNEL_IDS = {

    "bot_access": -1003800935640,

    "announcements": -1004315707986,

    "payment_registration": -1003935952561,

    "science_faculty": -1004479887604,

    "arts_faculty": -1004314659728,

    "commercial_faculty": -1003967146846,

    "physics": -1004467391688,

    "chemistry": -1003575115831,

    "biology": -1004412247385,

    "mathematics": -1004480230539,

    "agricultural_science": -1004398599335,

    "geography": -1003901130871,

    "use_of_english": -1003759215809,

    "literature": -1004317587777,

    "principles_of_accounts": -1004459228986,

    "commerce": -1003930273330,

    "economics": -1003632758498,

    "fine_arts": -1003801904375,

    "history": -1004494276405,

    "hausa": -1004436228793,

    "crs": -1004469127265,

    "islamic_studies": -1003823376901,

    "government": -1003735736424,
}


# ============================================================
# PAYMENT LINKS
# ============================================================

PAYMENT_LINKS = {

    "1": {
        "name": "1 Month",
        "amount": 3600,
        "link": "https://flutterwave.com/pay/xzxojtyp2igm",
    },

    "2": {
        "name": "2 Months",
        "amount": 6800,
        "link": "https://flutterwave.com/pay/7dmjszf7keh7",
    },

    "3": {
        "name": "3 Months",
        "amount": 10000,
        "link": "https://flutterwave.com/pay/ghclijb4q33v",
    },

    "4": {
        "name": "4 Months",
        "amount": 13200,
        "link": "https://flutterwave.com/pay/hplaya85sxfh",
    },

    "5": {
        "name": "5 Months",
        "amount": 16500,
        "link": "https://flutterwave.com/pay/gwkniyevqmdm",
    },

    "6": {
        "name": "6 Months",
        "amount": 20000,
        "link": "https://flutterwave.com/pay/ubrjptqujfem",
    },
}


# ============================================================
# MAIN MENU
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
    ],
]


# ============================================================
# COURSE MENU
# ============================================================

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
    ],
]


# ============================================================
# PAYMENT MENU
# ============================================================

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
    ],
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

        "We provide educational support for "
        "JAMB, WAEC, NECO and CBT Training.\n\n"

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

        "Please choose an option from the main menu.",

        reply_markup=keyboard
    )


# ============================================================
# SAVE REGISTRATION
# ============================================================

async def save_registration(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
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
            ),
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
# GIVE CHANNEL ACCESS
# ============================================================

async def give_channel_access(

    bot,

    user_id,

    channel_id

):

    try:

        invite_link = (

            await bot.create_chat_invite_link(

                chat_id=channel_id,

                member_limit=1
            )
        )


        return invite_link.invite_link


    except TelegramError as e:

        print(

            "Telegram Channel Error:",

            e
        )


        return None


# ============================================================
# STUDENT REGISTRATION
# ============================================================

async def menu_handler(

    update: Update,

    context: ContextTypes.DEFAULT_TYPE

):

    if not update.message:

        return


    text = update.message.text


    step = context.user_data.get(
        "step"
    )


    # --------------------------------------------------------
    # FULL NAME
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # PHONE
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # EMAIL
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # COURSE
    # --------------------------------------------------------

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


        phone = context.user_data.get(

            "phone",

            ""
        )


        email = context.user_data.get(

            "email",

            ""
        )


        course = context.user_data.get(

            "course",

            ""
        )


        context.user_data.clear()


        keyboard = ReplyKeyboardMarkup(

            MAIN_MENU,

            resize_keyboard=True
        )


        await update.message.reply_text(

            "✅ *REGISTRATION COMPLETED*\n\n"

            f"👤 Name: {full_name}\n"

            f"📱 Phone: {phone}\n"

            f"📧 Email: {email}\n"

            f"📚 Course: {course}\n\n"

            "🎓 Thank you for registering with "

            "ALHIKAM Learning Center.",

            parse_mode="Markdown",

            reply_markup=keyboard
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

            "Type /cancel to cancel registration.",

            parse_mode="Markdown"
        )


        return


    # --------------------------------------------------------
    # COURSES
    # --------------------------------------------------------

    if text == "📚 Courses":

        keyboard = ReplyKeyboardMarkup(

            COURSE_MENU,

            resize_keyboard=True
        )


        await update.message.reply_text(

            "📚 *ALHIKAM COURSES*\n\n"

            "Please select a course below:",

            parse_mode="Markdown",

            reply_markup=keyboard
        )


        return


    # --------------------------------------------------------
    # JAMB SCIENCE
    # --------------------------------------------------------

    if text == "🎯 JAMB Science":

        await update.message.reply_text(

            "🎯 *JAMB SCIENCE*\n\n"

            "📚 Subjects include:\n"

            "• Mathematics\n"

            "• English Language\n"

            "• Physics\n"

            "• Chemistry\n"

            "• Biology\n"

            "• Agricultural Science\n\n"

            "📝 CBT practice and study materials "
            "are available through ALHIKAM Learning Center.",

            parse_mode="Markdown"
        )


        return


    # --------------------------------------------------------
    # JAMB ARTS
    # --------------------------------------------------------

    if text == "🎨 JAMB Arts":

        await update.message.reply_text(

            "🎨 *JAMB ARTS*\n\n"

            "📚 Subjects include:\n"

            "• Use of English\n"

            "• Literature in English\n"

            "• Government\n"

            "• Economics\n"

            "• History\n"

            "• Hausa\n"

            "• Islamic Studies\n"

            "• CRS\n"

            "• Fine Arts\n\n"

            "📝 CBT practice and study materials "
            "are available through ALHIKAM Learning Center.",

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

            "🎓 Examination guidance\n\n"

            "More WAEC learning resources will be available soon.",

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

            "🎓 Examination guidance\n\n"

            "More NECO learning resources will be available soon.",

            parse_mode="Markdown"
        )


        return


    # --------------------------------------------------------
    # CBT TRAINING
    # --------------------------------------------------------

    if text == "💻 CBT Training":

        await update.message.reply_text(

            "💻 *CBT TRAINING*\n\n"

            "📝 Practice questions\n"

            "⏱️ Timed examinations\n"

            "📊 Results and performance\n"

            "🎯 JAMB • WAEC • NECO preparation\n\n"

            "🚧 CBT Training system is currently under development.",

            parse_mode="Markdown"
        )


        return


    # --------------------------------------------------------
    # BACK
    # --------------------------------------------------------

    if text == "🔙 Back to Main Menu":

        keyboard = ReplyKeyboardMarkup(

            MAIN_MENU,

            resize_keyboard=True
        )


        await update.message.reply_text(

            "🏠 *MAIN MENU*\n\n"

            "Please choose an option below.",

            parse_mode="Markdown",

            reply_markup=keyboard
        )


        return


    # --------------------------------------------------------
    # CBT PRACTICE
    # --------------------------------------------------------

    if text == "📝 CBT Practice":

        await update.message.reply_text(

            "📝 *CBT PRACTICE*\n\n"

            "CBT Practice will include:\n\n"

            "• JAMB Practice\n"

            "• WAEC Practice\n"

            "• NECO Practice\n"

            "• Timed Tests\n"

            "• Results and Scores\n\n"

            "🚧 This feature is under development.",

            parse_mode="Markdown"
        )


        return


    # --------------------------------------------------------
    # PAY SCHOOL FEES
    # --------------------------------------------------------

    if text == "💳 Pay School Fees":

        keyboard = ReplyKeyboardMarkup(

            PAYMENT_MENU,

            resize_keyboard=True
        )


        await update.message.reply_text(

            "💳 *ALHIKAM SCHOOL FEES PAYMENT*\n\n"

            "Please select your training duration:\n\n"

            "💳 1 Month — ₦3,600\n"

            "💳 2 Months — ₦6,800\n"

            "💳 3 Months — ₦10,000\n"

            "💳 4 Months — ₦13,200\n"

            "💳 5 Months — ₦16,500\n"

            "💳 6 Months — ₦20,000\n\n"

            "Select your preferred option below.",

            parse_mode="Markdown",

            reply_markup=keyboard
        )


        return


    # --------------------------------------------------------
    # PAYMENT OPTIONS
    # --------------------------------------------------------

    if text.startswith("💳 "):

        month = text.replace(

            "💳 ",

            ""
        )


        month_number = month.split()[0]


        payment = PAYMENT_LINKS.get(

            month_number
        )


        if payment:

            await update.message.reply_text(

                f"💳 *{payment['name'].upper()}*\n\n"

                f"💰 Price: ₦{payment['amount']:,}\n\n"

                "Click the payment link below:\n\n"

                f"{payment['link']}\n\n"

                "⚠️ After successful payment, "
                "your payment will be processed.",

                parse_mode="Markdown"
            )


            return


    # --------------------------------------------------------
    # CONTACT
    # --------------------------------------------------------

    if text == "📞 Contact Us":

        await update.message.reply_text(

            "📞 *CONTACT US*\n\n"

            "📧 Email: support@alhikam.com\n\n"

            "🎓 ALHIKAM Learning Center\n"

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

            "We provide quality educational support "
            "and examination preparation for students.\n\n"

            "📚 Courses\n"

            "📝 CBT Practice\n"

            "👤 Student Registration\n"

            "💳 School Fees Payment\n\n"

            "Our goal is to help students prepare "
            "successfully for their examinations.",

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
# MAIN
# ============================================================

def main():

    if not BOT_TOKEN:

        raise ValueError(

            "BOT_TOKEN is missing. "
            "Please add BOT_TOKEN in Railway Variables."
        )


    if not FLUTTERWAVE_SECRET_HASH:

        print(

            "WARNING: FLUTTERWAVE_SECRET_HASH is missing."
        )


    # Start Flask server
    Thread(

        target=run_web_server,

        daemon=True

    ).start()


    # Telegram Application
    app = (

        Application

        .builder()

        .token(BOT_TOKEN)

        .build()
    )


    # Commands
    app.add_handler(

        CommandHandler(

            "start",

            start
        )
    )


    app.add_handler(

        CommandHandler(

            "cancel",

            cancel
        )
    )


    # Text messages
    app.add_handler(

        MessageHandler(

            filters.TEXT & ~filters.COMMAND,

            menu_handler
        )
    )


    print(

        "================================"
    )


    print(

        "ALHIKAM Learning Center Bot "
        "is running..."
    )


    print(

        "Flutterwave Webhook:"
    )


    print(

        RAILWAY_URL +
        "/webhook/flutterwave"
    )


    print(

        "================================"
    )


    # Run Telegram Bot
    app.run_polling(

        drop_pending_updates=True
    )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    main()