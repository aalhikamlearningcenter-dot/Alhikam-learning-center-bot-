import os
import uuid
import hmac
import asyncio
import threading
import requests

from flask import Flask, request, jsonify, render_template_string

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
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
FLUTTERWAVE_SECRET_HASH = os.getenv("FLUTTERWAVE_SECRET_HASH")

SHEET_URL = os.getenv(
    "SHEET_URL",
    "https://script.google.com/macros/s/AKfycby5lIhCjoD0NaPZ-HHQ9hapAKlstypQvxyWK22qHblJr4uGBrPn5FoGG1TP-EvIfteo9w/exec",
)

RAILWAY_URL = os.getenv(
    "RAILWAY_URL",
    "https://precious-trust-production-956b.up.railway.app",
).rstrip("/")

PORT = int(os.getenv("PORT", "8080"))

MAIN_GROUP_ID = -1004384506380

# One public payment page.
# The Telegram bot sends users to this page with their Telegram ID.
PUBLIC_PAYMENT_PAGE = f"{RAILWAY_URL}/pay"


# ============================================================
# PAYMENT PLANS
# ============================================================

PAYMENT_PLANS = {
    "1": {"name": "1 Month", "amount": 3600},
    "2": {"name": "2 Months", "amount": 6800},
    "3": {"name": "3 Months", "amount": 10000},
    "4": {"name": "4 Months", "amount": 13200},
    "5": {"name": "5 Months", "amount": 16500},
    "6": {"name": "6 Months", "amount": 20000},
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
        "payment_page": "/pay/<telegram_id>",
        "webhook": "/webhook/flutterwave",
    })


@web_app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"})


# ============================================================
# SINGLE PAYMENT PAGE
# ============================================================

PAYMENT_PAGE_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ALHIKAM Learning Center Payment</title>
<style>
body {
    font-family: Arial, sans-serif;
    background: #f4f7f6;
    margin: 0;
    padding: 20px;
}
.container {
    max-width: 520px;
    margin: 30px auto;
    background: white;
    padding: 25px;
    border-radius: 16px;
    box-shadow: 0 4px 18px rgba(0,0,0,.10);
}
h1 {
    color: #087f5b;
    text-align: center;
}
.subtitle {
    text-align: center;
    color: #555;
    margin-bottom: 25px;
}
.plan {
    border: 1px solid #ddd;
    border-radius: 12px;
    padding: 15px;
    margin: 10px 0;
}
.plan label {
    display: block;
    cursor: pointer;
}
.amount {
    font-weight: bold;
    font-size: 18px;
    color: #087f5b;
}
button {
    width: 100%;
    padding: 15px;
    margin-top: 20px;
    border: none;
    border-radius: 10px;
    background: #087f5b;
    color: white;
    font-size: 17px;
    font-weight: bold;
    cursor: pointer;
}
button:hover {
    background: #066b4d;
}
.note {
    text-align: center;
    font-size: 13px;
    color: #777;
    margin-top: 18px;
}
</style>
</head>
<body>
<div class="container">
    <h1>🎓 ALHIKAM Learning Center</h1>
    <div class="subtitle">
        Select your preferred learning duration and pay securely.
    </div>

    <form method="POST" action="/create-payment">

        {% for key, plan in plans.items() %}
        <div class="plan">
            <label>
                <input type="radio" name="plan" value="{{ key }}" required>
                <strong>{{ plan.name }}</strong><br>
                <span class="amount">₦{{ "{:,}".format(plan.amount) }}</span>
            </label>
        </div>
        {% endfor %}

        <input type="hidden" name="telegram_id" value="{{ telegram_id }}">

        <button type="submit">
            💳 CONTINUE TO SECURE PAYMENT
        </button>
    </form>

    <div class="note">
        After successful payment, your Telegram class access will be sent automatically.
    </div>
</div>
</body>
</html>
"""


@web_app.route("/pay", methods=["GET"])
def payment_page_without_id():
    return """
    <h2>ALHIKAM Learning Center</h2>
    <p>Please open the payment link from the ALHIKAM Telegram bot.</p>
    """


@web_app.route("/pay/<int:telegram_id>", methods=["GET"])
def payment_page(telegram_id):
    return render_template_string(
        PAYMENT_PAGE_HTML,
        plans=PAYMENT_PLANS,
        telegram_id=telegram_id,
    )


# ============================================================
# CREATE FLUTTERWAVE PAYMENT FROM SINGLE PAGE
# ============================================================

@web_app.route("/create-payment", methods=["POST"])
def create_payment():
    if not FLW_SECRET_KEY:
        return "Payment system is temporarily unavailable.", 500

    telegram_id = request.form.get("telegram_id")
    plan_number = request.form.get("plan")

    if not telegram_id or not telegram_id.isdigit():
        return "Invalid Telegram account.", 400

    plan = PAYMENT_PLANS.get(plan_number)

    if not plan:
        return "Invalid payment plan.", 400

    unique_ref = (
        f"ALHIKAM_{telegram_id}_{plan_number}_{uuid.uuid4().hex}"
    )

    payload = {
        "tx_ref": unique_ref,
        "amount": plan["amount"],
        "currency": "NGN",
        "redirect_url": f"{RAILWAY_URL}/payment-success",
        "customer": {
            "email": f"telegram{telegram_id}@alhikam.com",
            "name": "ALHIKAM Student",
        },
        "customizations": {
            "title": "ALHIKAM Learning Center",
            "description": f"{plan['name']} Training",
            "logo": "",
        },
    }

    headers = {
        "Authorization": f"Bearer {FLW_SECRET_KEY}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            "https://api.flutterwave.com/v3/payments",
            json=payload,
            headers=headers,
            timeout=30,
        )

        result = response.json()

        print("Flutterwave Checkout Response:", result)

        if (
            response.status_code == 200
            and result.get("status") == "success"
        ):
            payment_link = (
                result.get("data", {}).get("link")
            )

            if payment_link:
                return f"""
                <html>
                <head>
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <style>
                body {{
                    font-family: Arial;
                    text-align: center;
                    padding: 50px 20px;
                }}
                a {{
                    display: inline-block;
                    padding: 15px 25px;
                    background: #087f5b;
                    color: white;
                    text-decoration: none;
                    border-radius: 10px;
                    font-weight: bold;
                }}
                </style>
                </head>
                <body>
                <h2>🎓 ALHIKAM Learning Center</h2>
                <p>Payment plan: <strong>{plan["name"]}</strong></p>
                <p>Amount: <strong>₦{plan["amount"]:,}</strong></p>
                <p>Click below to continue your secure payment.</p>
                <br>
                <a href="{payment_link}">💳 PAY NOW</a>
                </body>
                </html>
                """

        print("Flutterwave payment link creation failed.")
        return "Unable to create payment link. Please try again.", 500

    except Exception as e:
        print("Flutterwave API Error:", e)
        return "Payment system error. Please try again later.", 500


# ============================================================
# PAYMENT SUCCESS PAGE
# ============================================================

@web_app.route("/payment-success", methods=["GET"])
def payment_success():
    return """
    <html>
    <head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
    body {
        font-family: Arial;
        text-align: center;
        padding: 50px 20px;
    }
    h1 { color: #087f5b; }
    </style>
    </head>
    <body>
        <h1>✅ Payment Received</h1>
        <p>Your payment is being verified.</p>
        <p>Please check your Telegram account for your class access link.</p>
    </body>
    </html>
    """


# ============================================================
# FLUTTERWAVE WEBHOOK
# ============================================================

@web_app.route("/webhook/flutterwave", methods=["POST"])
def flutterwave_webhook():

    incoming_hash = request.headers.get("verif-hash")

    if not FLUTTERWAVE_SECRET_HASH:
        print("ERROR: FLUTTERWAVE_SECRET_HASH is missing.")
        return jsonify({
            "status": "error",
            "message": "Webhook secret hash not configured",
        }), 500

    if not incoming_hash:
        print("Webhook rejected: Missing verif-hash.")
        return jsonify({
            "status": "error",
            "message": "Missing verification hash",
        }), 401

    if not hmac.compare_digest(
        incoming_hash,
        FLUTTERWAVE_SECRET_HASH,
    ):
        print("Webhook rejected: Invalid secret hash.")
        return jsonify({
            "status": "error",
            "message": "Invalid verification hash",
        }), 401

    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "status": "error",
            "message": "Invalid JSON",
        }), 400

    print("================================")
    print("FLUTTERWAVE WEBHOOK RECEIVED")
    print("EVENT:", data.get("event"))
    print("DATA:", data)
    print("================================")

    payment_data = data.get("data", {})

    status = payment_data.get("status")
    amount = payment_data.get("amount")
    currency = payment_data.get("currency")
    transaction_id = payment_data.get("id")
    tx_ref = payment_data.get("tx_ref")

    print("Payment Status:", status)
    print("Amount:", amount)
    print("Currency:", currency)
    print("Transaction ID:", transaction_id)
    print("Transaction Reference:", tx_ref)

    if status != "successful":
        return jsonify({"status": "ignored"}), 200

    telegram_id = None

    if tx_ref:
        try:
            parts = tx_ref.split("_")

            # ALHIKAM_TELEGRAMID_PLAN_UUID
            if len(parts) >= 3:
                telegram_id = int(parts[1])

        except Exception as e:
            print("Telegram ID extraction error:", e)

    if not telegram_id:
        print("ERROR: Telegram ID not found in tx_ref.")
        return jsonify({
            "status": "error",
            "message": "Telegram ID not found",
        }), 400

    print("Telegram User ID:", telegram_id)

    threading.Thread(
        target=process_successful_payment,
        args=(telegram_id, payment_data),
        daemon=True,
    ).start()

    return jsonify({"status": "success"}), 200


# ============================================================
# PROCESS SUCCESSFUL PAYMENT
# ============================================================

def process_successful_payment(
    telegram_id,
    payment_data,
):
    try:
        amount = payment_data.get("amount", "N/A")
        tx_ref = payment_data.get("tx_ref", "N/A")

        asyncio_run_payment_access(
            telegram_id,
            amount,
            tx_ref,
        )

    except Exception as e:
        print("Payment processing error:", e)


def asyncio_run_payment_access(
    telegram_id,
    amount,
    tx_ref,
):
    asyncio.run(
        send_payment_access(
            telegram_id,
            amount,
            tx_ref,
        )
    )


# ============================================================
# SEND TELEGRAM ACCESS
# ============================================================

async def send_payment_access(
    telegram_id,
    amount,
    tx_ref,
):

    global telegram_bot_app

    if telegram_bot_app is None:
        print("Telegram application is not ready.")
        return

    try:

        invite_link = await telegram_bot_app.bot.create_chat_invite_link(
            chat_id=MAIN_GROUP_ID,
            member_limit=1,
            name=f"ALHIKAM-{telegram_id}",
        )

        join_url = invite_link.invite_link

        await telegram_bot_app.bot.send_message(
            chat_id=telegram_id,
            text=(
                "🎉 *PAYMENT SUCCESSFUL!*\n\n"
                "🎓 ALHIKAM Learning Center\n\n"
                f"💰 Amount Paid: ₦{amount:,}\n\n"
                "✅ Your payment has been confirmed.\n\n"
                "📚 Your class access is now ready.\n\n"
                "👇 Click the button below to join your class.\n\n"
                "⚠️ This invitation link is for you only."
            ),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🎓 JOIN ALHIKAM CLASS",
                        url=join_url,
                    )
                ]
            ]),
        )

        print(
            "Access sent successfully to:",
            telegram_id,
        )

    except TelegramError as e:
        print("Telegram access error:", e)

    except Exception as e:
        print("General access error:", e)


# ============================================================
# RUN WEB SERVER
# ============================================================

def run_web_server():
    print("Starting Flask Web Server...")

    web_app.run(
        host="0.0.0.0",
        port=PORT,
        use_reloader=False,
    )


# ============================================================
# MENUS
# ============================================================

MAIN_MENU = [
    ["📚 Courses", "📝 CBT Practice"],
    ["👤 Student Registration", "💳 Pay School Fees"],
    ["📞 Contact Us", "ℹ️ About Us"],
]

COURSE_MENU = [
    ["🎯 JAMB Science", "🎨 JAMB Arts"],
    ["📘 WAEC", "📕 NECO"],
    ["💻 CBT Training"],
    ["🔙 Back to Main Menu"],
]


# ============================================================
# START
# ============================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    context.user_data.clear()

    keyboard = ReplyKeyboardMarkup(
        MAIN_MENU,
        resize_keyboard=True,
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
        reply_markup=keyboard,
    )


# ============================================================
# CANCEL
# ============================================================

async def cancel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    context.user_data.clear()

    await update.message.reply_text(
        "❌ Registration cancelled.\n\n"
        "Please choose an option below.",
        reply_markup=ReplyKeyboardMarkup(
            MAIN_MENU,
            resize_keyboard=True,
        ),
    )


# ============================================================
# SAVE REGISTRATION
# ============================================================

async def save_registration(
    update,
    context,
):

    data = {
        "telegram_id": update.effective_user.id,
        "username": update.effective_user.username or "",
        "full_name": context.user_data.get("full_name", ""),
        "phone": context.user_data.get("phone", ""),
        "email": context.user_data.get("email", ""),
        "course": context.user_data.get("course", ""),
    }

    try:

        response = requests.post(
            SHEET_URL,
            json=data,
            timeout=15,
        )

        print(
            "Google Sheet Response:",
            response.text,
        )

    except Exception as e:

        print(
            "Google Sheet Error:",
            e,
        )


# ============================================================
# MAIN MESSAGE HANDLER
# ============================================================

async def menu_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not update.message:
        return

    text = update.message.text

    # --------------------------------------------------------
    # REGISTRATION STEPS
    # --------------------------------------------------------

    step = context.user_data.get("step")

    if step == "full_name":

        context.user_data["full_name"] = text
        context.user_data["step"] = "phone"

        await update.message.reply_text(
            "📱 Please enter your Phone Number:"
        )

        return

    if step == "phone":

        context.user_data["phone"] = text
        context.user_data["step"] = "email"

        await update.message.reply_text(
            "📧 Please enter your Email Address:"
        )

        return

    if step == "email":

        context.user_data["email"] = text
        context.user_data["step"] = "course"

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

        context.user_data["course"] = text

        await save_registration(
            update,
            context,
        )

        full_name = context.user_data.get(
            "full_name",
            "",
        )

        context.user_data.clear()

        await update.message.reply_text(
            "✅ *REGISTRATION COMPLETED*\n\n"
            f"👤 Name: {full_name}\n\n"
            "🎓 Thank you for registering with "
            "ALHIKAM Learning Center.",
            parse_mode="Markdown",
        )

        return

    # --------------------------------------------------------
    # STUDENT REGISTRATION
    # --------------------------------------------------------

    if text == "👤 Student Registration":

        context.user_data.clear()
        context.user_data["step"] = "full_name"

        await update.message.reply_text(
            "👤 *STUDENT REGISTRATION*\n\n"
            "Please enter your Full Name.\n\n"
            "Type /cancel to cancel.",
            parse_mode="Markdown",
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
                resize_keyboard=True,
            ),
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
            parse_mode="Markdown",
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
            parse_mode="Markdown",
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
            parse_mode="Markdown",
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
            parse_mode="Markdown",
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
            parse_mode="Markdown",
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
                resize_keyboard=True,
            ),
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
            parse_mode="Markdown",
        )

        return

    # --------------------------------------------------------
    # PAYMENT - ONE LINK
    # --------------------------------------------------------

    if text == "💳 Pay School Fees":

        telegram_id = update.effective_user.id

        payment_url = (
            f"{PUBLIC_PAYMENT_PAGE}/{telegram_id}"
        )

        await update.message.reply_text(
            "💳 *ALHIKAM SCHOOL FEES PAYMENT*\n\n"
            "Click the button below to open the payment page.\n\n"
            "You will see all available durations and "
            "choose the one you want to pay for.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "💳 OPEN PAYMENT PAGE",
                        url=payment_url,
                    )
                ]
            ]),
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
            parse_mode="Markdown",
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
            parse_mode="Markdown",
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

    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is missing.")

    if not FLW_SECRET_KEY:
        raise ValueError("FLW_SECRET_KEY is missing.")

    if not FLUTTERWAVE_SECRET_HASH:
        print(
            "WARNING: FLUTTERWAVE_SECRET_HASH is missing."
        )

    # Start Flask only once.
    web_thread = threading.Thread(
        target=run_web_server,
        daemon=True,
    )

    web_thread.start()

    telegram_bot_app = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )

    telegram_bot_app.add_handler(
        CommandHandler(
            "start",
            start,
        )
    )

    telegram_bot_app.add_handler(
        CommandHandler(
            "cancel",
            cancel,
        )
    )

    telegram_bot_app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            menu_handler,
        )
    )

    print("================================")
    print(
        "ALHIKAM Learning Center Bot "
        "is running..."
    )
    print("Single Payment Page: ENABLED")
    print(
        "Payment Page:",
        PUBLIC_PAYMENT_PAGE,
    )
    print(
        "Dynamic Flutterwave Checkout: ENABLED"
    )
    print("Flutterwave Webhook:")
    print(
        RAILWAY_URL +
        "/webhook/flutterwave"
    )
    print(
        "Main Group ID:",
        MAIN_GROUP_ID,
    )
    print("================================")

    # IMPORTANT:
    # Railway must run only ONE replica/instance of this service.
    telegram_bot_app.run_polling(
        drop_pending_updates=True,
        close_loop=False,
    )


if __name__ == "__main__":
    main()
