import os
import uuid
import hmac
import asyncio
import threading
import requests
import hashlib
import hmac
from urllib.parse import urlencode

from flask import (
    Flask,
    request,
    jsonify,
    render_template_string,
    redirect,
)

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
BOT_USERNAME = "Alhikamcenterbot"
APP_URL = "https://precious-trust-production-956b.up.railway.app"
BOT_TOKEN = os.getenv("BOT_TOKEN")
FLW_SECRET_KEY = os.getenv("FLW_SECRET_KEY")
FLUTTERWAVE_SECRET_HASH = os.getenv("FLUTTERWAVE_SECRET_HASH")

SHEET_URL = os.getenv(
    "SHEET_URL",
    "https://script.google.com/macros/s/AKfycbw6LRBGCzMIHcWGEIKXAYXo9bMHxsO_am4a4iSZ4kR58FFA-bj4TcUNy085uTaVRx2z0A/exec",
)

RAILWAY_URL = os.getenv(
    "RAILWAY_URL",
    "https://precious-trust-production-956b.up.railway.app",
).rstrip("/")

PORT = int(os.getenv("PORT", "8080"))

MAIN_GROUP_ID = -1004384506380
ANNOUNCEMENT_CHANNEL_ID = -1004315707986

SCIENCE_FACULTY_ID = -1004479887604
PHYSICS_ID = -1004467391688
CHEMISTRY_ID = -1003575115831
BIOLOGY_ID = -1004412247385
MATHEMATICS_ID = -1004480230539
AGRICULTURAL_SCIENCE_ID = -1004398599335
GEOGRAPHY_ID = -1003901130871

ARTS_FACULTY_ID = -1004314659728
GOVERNMENT_ID = -1003735736424
LITERATURE_ID = -1004317587777
HISTORY_ID = -1004494276405
HAUSA_ID = -1004436228793
CRS_ID = -1004469127265
ISLAMIC_STUDIES_ID = -1003823376901
FINE_ARTS_ID = -1003801904375

COMMERCIAL_FACULTY_ID = -1003967146846
ACCOUNTS_ID = -1004459228986
COMMERCE_ID = -1003930273330
ECONOMICS_ID = -1003632758498

USE_OF_ENGLISH_ID = -1003759215809

PAYMENT_REGISTRATION_ID = -1003935952561
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
# TEMPORARY PAYMENT STORAGE
# ============================================================

pending_payments = {}

processed_payments = set()

telegram_bot_app = None


# ============================================================
# FLASK
# ============================================================

web_app = Flask(__name__)
from flask import session, redirect, request

@app.route("/telegram-auth")
def telegram_auth():
    telegram_id = request.args.get("id")
    first_name = request.args.get("first_name", "")
    username = request.args.get("username", "")

    if not telegram_id:
        return "Telegram login failed.", 400

    session["telegram_id"] = telegram_id
    session["telegram_username"] = username
    session["telegram_name"] = first_name

    return redirect("/registration-success")

@web_app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "online",
        "bot": "ALHIKAM Learning Center Bot",
        "payment_page": f"{RAILWAY_URL}/pay",
        "webhook": f"{RAILWAY_URL}/webhook/flutterwave",
    })


@web_app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy"
    })


# ============================================================
# ONE PAYMENT PAGE
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
Choose your learning duration and continue to secure payment.
</div>

<form method="POST" action="/create-payment">

{% for key, plan in plans.items() %}

<div class="plan">

<label>

<input
type="radio"
name="plan"
value="{{ key }}"
required
>

<strong>{{ plan.name }}</strong>

<br>

<span class="amount">
₦{{ "{:,}".format(plan.amount) }}
</span>

</label>

</div>

{% endfor %}

<button type="submit">
💳 CONTINUE TO SECURE PAYMENT
</button>

</form>

<div class="note">
After successful payment, you will be taken directly to registration.
</div>

</div>

</body>
</html>
"""


@web_app.route("/pay", methods=["GET"])
def payment_page():

    return render_template_string(
        PAYMENT_PAGE_HTML,
        plans=PAYMENT_PLANS,
    )


# ============================================================
# CREATE FLUTTERWAVE PAYMENT
# ============================================================

@web_app.route("/create-payment", methods=["POST"])
def create_payment():

    if not FLW_SECRET_KEY:

        return (
            "Payment system is temporarily unavailable.",
            500,
        )

    plan_number = request.form.get("plan")

    plan = PAYMENT_PLANS.get(plan_number)

    if not plan:

        return (
            "Invalid payment plan.",
            400,
        )

    payment_token = uuid.uuid4().hex

    tx_ref = (
        f"ALHIKAM_{payment_token}"
    )

    pending_payments[payment_token] = {

        "tx_ref":
            tx_ref,

        "plan":
            plan_number,

        "plan_name":
            plan["name"],

        "amount":
            plan["amount"],

        "status":
            "pending",

    }

    payload = {

        "tx_ref":
            tx_ref,

        "amount":
            plan["amount"],

        "currency":
            "NGN",

        "redirect_url":
            f"{RAILWAY_URL}/payment-complete/{payment_token}",

        "customer": {

            "email":
                f"student_{payment_token}@alhikam.com",

            "name":
                "ALHIKAM Student",

        },

        "customizations": {

            "title":
                "ALHIKAM Learning Center",

            "description":
                f"{plan['name']} Training",

            "logo":
                "",

        },

    }

    headers = {

        "Authorization":
            f"Bearer {FLW_SECRET_KEY}",

        "Content-Type":
            "application/json",

    }

    try:

        response = requests.post(

            "https://api.flutterwave.com/v3/payments",

            json=payload,

            headers=headers,

            timeout=30,

        )

        result = response.json()

        print(
            "Flutterwave Checkout Response:",
            result,
        )

        if (

            response.status_code == 200

            and

            result.get("status") == "success"

        ):

            payment_link = (

                result
                .get("data", {})
                .get("link")

            )

            if payment_link:

                return redirect(
                    payment_link
                )

        return (

            "Unable to create payment link. Please try again.",

            500,

        )

    except Exception as e:

        print(
            "Flutterwave API Error:",
            e,
        )

        return (

            "Payment system error. Please try again later.",

            500,

        )


# ============================================================
# PAYMENT RETURN PAGE
# ============================================================

@web_app.route(
    "/payment-complete/<payment_token>",
    methods=["GET"]
)
def payment_complete(payment_token):

    payment = pending_payments.get(
        payment_token
    )

    if not payment:

        return """

        <h2>Payment Reference Not Found</h2>

        <p>
        Please contact ALHIKAM Learning Center.
        </p>

        """

    if payment.get("status") != "successful":

        return f"""

        <html>

        <head>

        <meta name="viewport"
        content="width=device-width, initial-scale=1">

        <style>

        body {{
            font-family: Arial;
            text-align: center;
            padding: 50px 20px;
        }}

        </style>

        </head>

        <body>

        <h2>⏳ Payment Verification</h2>

        <p>
        Your payment is being verified.
        </p>

        <p>
        Please wait a moment and refresh this page.
        </p>

        <a href="/payment-complete/{payment_token}">
        🔄 Refresh
        </a>

        </body>

        </html>

        """

    return redirect(
        f"/register/{payment_token}"
    )


# ============================================================
# REGISTRATION PAGE
# ============================================================

REGISTRATION_HTML = """

<!DOCTYPE html>

<html>

<head>

<meta name="viewport"
content="width=device-width, initial-scale=1">

<title>
ALHIKAM Student Registration
</title>

<style>

body {

font-family: Arial;

background: #f4f7f6;

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

input,
select {

width: 100%;

padding: 13px;

margin: 8px 0 15px;

border: 1px solid #ddd;

border-radius: 8px;

box-sizing: border-box;

}

button {

width: 100%;

padding: 15px;

background: #087f5b;

color: white;

border: none;

border-radius: 10px;

font-size: 17px;

font-weight: bold;

}

.info {

background: #eef8f4;

padding: 15px;

border-radius: 10px;

margin-bottom: 20px;

}

</style>

</head>

<body>

<div class="container">

<h1>
🎓 ALHIKAM Learning Center
</h1>

<div class="info">

<strong>Payment Confirmed ✅</strong>

<br><br>

Plan:
{{ plan_name }}

<br>

Amount:
₦{{ "{:,}".format(amount) }}

</div>

<form method="POST">

<label>
Full Name
</label>

<input
type="text"
name="full_name"
required
>

<label>
Phone Number
</label>

<input
type="tel"
name="phone"
required
>

<label>
Email Address
</label>

<input
type="email"
name="email"
required
>

<label>
Course
</label>

<select
name="course"
required
>

<option value="">
Select Course
</option>

<option>
JAMB Science
</option>

<option>
JAMB Arts
</option>

<option>
WAEC
</option>

<option>
NECO
</option>

<option>
CBT Training
</option>

</select>

<label>
Telegram Username

>

<button type="submit">

✅ COMPLETE REGISTRATION

</button>

</form>

</div>

</body>

</html>

"""


@web_app.route(
    "/register/<payment_token>",
    methods=["GET", "POST"]
)
def register_student(payment_token):

    payment = pending_payments.get(
        payment_token
    )

    if not payment:

        return (
            "Payment reference not found.",
            404,
        )

    if payment.get("status") != "successful":

        return (
            "Payment has not yet been verified.",
            400,
        )

    if payment.get("registration_completed"):

        return """

        <h2>
        Registration Already Completed
        </h2>

        <p>
        Your Telegram class access has already been processed.
        </p>

        """

    if request.method == "GET":

        return render_template_string(

            REGISTRATION_HTML,

            plan_name=
                payment["plan_name"],

            amount=
                payment["amount"],

        )

    full_name = (
        request.form.get(
            "full_name",
            ""
        ).strip()
    )

    phone = (
        request.form.get(
            "phone",
            ""
        ).strip()
    )

    email = (
        request.form.get(
            "email",
            ""
        ).strip()
    )

    course = (
        request.form.get(
            "course",
            ""
        ).strip()
    )

    

    if not full_name or not phone or not email or not course:

        return (

            "Please complete all required fields.",

            400,

        )

    registration_data = {

        

        "full_name":
            full_name,

        "phone":
            phone,

        "email":
            email,

        "course":
            course,

        "payment_plan":
            payment["plan_name"],

        "amount_paid":
            payment["amount"],

        "tx_ref":
            payment["tx_ref"],

    }

    saved = save_registration_to_google_sheets(

        registration_data

    )

    if not saved:

        return (

            "Registration could not be saved. "
            "Please try again.",

            500,

        )

    payment["registration_completed"] = True

    payment["registration"] = registration_data

    invite_link = create_unique_invite_link(

        payment_token

    )

    if not invite_link:

        return """

        <h2>
        Registration Successful
        </h2>

        <p>
        Your registration has been saved.
        </p>

        <p>
        Please contact ALHIKAM Learning Center
        to receive your class access.
        </p>

        """

    # Send Telegram message if Telegram ID was provided

    if telegram_id.isdigit():

        threading.Thread(

            target=
                send_registration_access,

            args=(

                int(telegram_id),

                full_name,

                payment["amount"],

                invite_link,

            ),

            daemon=True,

        ).start()

    return f"""

    <html>

    <head>

    <meta name="viewport"
    content="width=device-width, initial-scale=1">

    <style>

    body {{

        font-family: Arial;

        text-align: center;

        padding: 40px 20px;

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

    <h1>
    🎉 Registration Completed!
    </h1>

    <p>
    Welcome to ALHIKAM Learning Center,
    <strong>{full_name}</strong>.
    </p>

    <p>
    Your payment and registration have been confirmed.
    </p>

    <p>
    Click below to join your Telegram class.
    </p>

    <br>

    <a href="{invite_link}">
    🎓 JOIN ALHIKAM CLASS
    </a>

    </body>

    </html>

    """


# ============================================================
# GOOGLE SHEETS
# ============================================================

def save_registration_to_google_sheets(data):

    try:

        print(
            "Saving registration:",
            data,
        )

        response = requests.post(

            SHEET_URL,

            json=data,

            timeout=20,

        )

        print(
            "Google Sheets Status:",
            response.status_code,
        )

        print(
            "Google Sheets Response:",
            response.text,
        )

        return response.status_code == 200

    except Exception as e:

        print(
            "Google Sheets Error:",
            e,
        )

        return False


# ============================================================
# CREATE UNIQUE TELEGRAM INVITE LINK
# ============================================================

def create_unique_invite_link(payment_token):

    global telegram_bot_app

    if telegram_bot_app is None:

        print(
            "Telegram application not ready."
        )

        return None

    try:

        invite_link = asyncio.run(

            telegram_bot_app.bot.create_chat_invite_link(

                chat_id=
                    MAIN_GROUP_ID,

                member_limit=
                    1,

                name=
                    f"ALHIKAM-{payment_token[:10]}",

            )

        )

        return invite_link.invite_link

    except Exception as e:

        print(
            "Invite link creation error:",
            e,
        )

        return None


# ============================================================
# SEND TELEGRAM ACCESS
# ============================================================

def send_registration_access(

    telegram_id,

    full_name,

    amount,

    invite_link,

):

    try:

        asyncio.run(

            send_access_message(

                telegram_id,

                full_name,

                amount,

                invite_link,

            )

        )

    except Exception as e:

        print(
            "Telegram access error:",
            e,
        )


async def send_access_message(

    telegram_id,

    full_name,

    amount,

    invite_link,

):

    global telegram_bot_app

    if telegram_bot_app is None:

        return

    try:

        await telegram_bot_app.bot.send_message(

            chat_id=
                telegram_id,

            text=(

                "🎉 *REGISTRATION COMPLETED!*\n\n"

                f"👤 Name: {full_name}\n\n"

                "🎓 ALHIKAM Learning Center\n\n"

                f"💰 Amount Paid: ₦{amount:,}\n\n"

                "✅ Payment confirmed.\n"

                "✅ Registration completed.\n\n"

                "📚 Your class access is ready.\n\n"

                "👇 Click the button below to join your class.\n\n"

                "⚠️ This invite link is for you only."

            ),

            parse_mode=
                "Markdown",

            reply_markup=
                InlineKeyboardMarkup([

                    [

                        InlineKeyboardButton(

                            "🎓 JOIN ALHIKAM CLASS",

                            url=
                                invite_link,

                        )

                    ]

                ]),

        )

        print(

            "Access sent to Telegram:",
            telegram_id,

        )

    except TelegramError as e:

        print(

            "Telegram Error:",
            e,

        )


# ============================================================
# FLUTTERWAVE VERIFY
# ============================================================

def verify_flutterwave_transaction(transaction_id):

    if not FLW_SECRET_KEY:

        return None

    try:

        url = (

            "https://api.flutterwave.com/v3/transactions/"

            f"{transaction_id}/verify"

        )

        headers = {

            "Authorization":
                f"Bearer {FLW_SECRET_KEY}",

            "Content-Type":
                "application/json",

        }

        response = requests.get(

            url,

            headers=headers,

            timeout=30,

        )

        result = response.json()

        print(

            "Verification Response:",
            result,

        )

        if (

            response.status_code == 200

            and

            result.get("status") == "success"

        ):

            return result.get(

                "data",

                {}

            )

        return None

    except Exception as e:

        print(

            "Verification Error:",
            e,

        )

        return None


# ============================================================
# FLUTTERWAVE WEBHOOK
# ============================================================

@web_app.route(

    "/webhook/flutterwave",

    methods=["POST"]

)
def flutterwave_webhook():

    incoming_hash = request.headers.get(

        "verif-hash"

    )

    if not FLUTTERWAVE_SECRET_HASH:

        return jsonify({

            "status":
                "error",

            "message":
                "Webhook secret hash missing",

        }), 500

    if not incoming_hash:

        return jsonify({

            "status":
                "error",

            "message":
                "Missing verification hash",

        }), 401

    if not hmac.compare_digest(

        incoming_hash,

        FLUTTERWAVE_SECRET_HASH,

    ):

        return jsonify({

            "status":
                "error",

            "message":
                "Invalid verification hash",

        }), 401

    data = request.get_json(

        silent=True

    )

    if not data:

        return jsonify({

            "status":
                "error",

        }), 400

    payment_data = data.get(

        "data",

        {}

    )

    transaction_id = payment_data.get(

        "id"

    )

    tx_ref = payment_data.get(

        "tx_ref"

    )

    status = payment_data.get(

        "status"

    )

    if status != "successful":

        return jsonify({

            "status":
                "ignored"

        }), 200

    if not transaction_id:

        return jsonify({

            "status":
                "error",

        }), 400

    verified = verify_flutterwave_transaction(

        transaction_id

    )

    if not verified:

        return jsonify({

            "status":
                "error",

            "message":
                "Verification failed",

        }), 400

    verified_status = verified.get(

        "status"

    )

    verified_tx_ref = verified.get(

        "tx_ref"

    )

    verified_amount = verified.get(

        "amount"

    )

    verified_currency = verified.get(

        "currency"

    )

    if verified_status != "successful":

        return jsonify({

            "status":
                "ignored"

        }), 200

    if verified_currency != "NGN":

        return jsonify({

            "status":
                "error",

            "message":
                "Invalid currency",

        }), 400

    if verified_tx_ref != tx_ref:

        return jsonify({

            "status":
                "error",

            "message":
                "Transaction reference mismatch",

        }), 400

    if tx_ref.startswith("ALHIKAM_"):

        payment_token = tx_ref.replace(

            "ALHIKAM_",

            "",

            1

        )

    else:

        return jsonify({

            "status":
                "error",

        }), 400

    payment = pending_payments.get(

        payment_token

    )

    if not payment:

        print(

            "Payment token not found:",
            payment_token,

        )

        return jsonify({

            "status":
                "error",

        }), 404

    if payment_token in processed_payments:

        return jsonify({

            "status":
                "already_processed"

        }), 200

    if int(verified_amount) != int(

        payment["amount"]

    ):

        return jsonify({

            "status":
                "error",

            "message":
                "Amount mismatch",

        }), 400

    payment["status"] = "successful"

    payment["transaction_id"] = transaction_id

    payment["verified_amount"] = verified_amount

    processed_payments.add(

        payment_token

    )

    print(

        "PAYMENT SUCCESSFUL:",

        payment,

    )

    return jsonify({

        "status":
            "success"

    }), 200


# ============================================================
# RUN FLASK
# ============================================================

def run_web_server():

    print(

        "Starting Flask Web Server..."

    )

    web_app.run(

        host=
            "0.0.0.0",

        port=
            PORT,

        use_reloader=
            False,

    )


# ============================================================
# TELEGRAM MENUS
# ============================================================

MAIN_MENU = [

    [

        "📚 Courses",

        "📝 CBT Practice",

    ],

    [

        "👤 Student Registration",

        "💳 Pay School Fees",

    ],

    [

        "📞 Contact Us",

        "ℹ️ About Us",

    ],

]


COURSE_MENU = [

    [

        "🎯 JAMB Science",

        "🎨 JAMB Arts",

    ],

    [

        "📘 WAEC",

        "📕 NECO",

    ],

    [

        "💻 CBT Training",

    ],

    [

        "🔙 Back to Main Menu",

    ],

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

        "We provide educational support for:\n\n"

        "• JAMB\n"

        "• WAEC\n"

        "• NECO\n"

        "• CBT Training\n\n"

        "Please choose an option below.",

        parse_mode=
            "Markdown",

        reply_markup=
            keyboard,

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

        "❌ Registration cancelled.",

        reply_markup=
            ReplyKeyboardMarkup(

                MAIN_MENU,

                resize_keyboard=True,

            ),

    )


# ============================================================
# TELEGRAM MESSAGE HANDLER
# ============================================================

async def menu_handler(

    update: Update,

    context: ContextTypes.DEFAULT_TYPE,

):

    if not update.message:

        return

    text = update.message.text

    step = context.user_data.get(

        "step"

    )


    # ========================================================
    # REGISTRATION
    # ========================================================

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

            "📚 Please type your Course."

        )

        return


    if step == "course":

        context.user_data["course"] = text

        data = {

            "telegram_id":
                update.effective_user.id,

            "username":
                update.effective_user.username or "",

            "full_name":
                context.user_data.get(

                    "full_name",

                    "",

                ),

            "phone":
                context.user_data.get(

                    "phone",

                    "",

                ),

            "email":
                context.user_data.get(

                    "email",

                    "",

                ),

            "course":
                context.user_data.get(

                    "course",

                    "",

                ),

        }

        save_registration_to_google_sheets(

            data

        )

        full_name = data["full_name"]

        context.user_data.clear()

        await update.message.reply_text(

            "✅ *REGISTRATION COMPLETED*\n\n"

            f"👤 Name: {full_name}\n\n"

            "🎓 Thank you for registering with "

            "ALHIKAM Learning Center.",

            parse_mode=
                "Markdown",

        )

        return


    # ========================================================
    # STUDENT REGISTRATION
    # ========================================================

    if text == "👤 Student Registration":

        context.user_data.clear()

        context.user_data["step"] = "full_name"

        await update.message.reply_text(

            "👤 *STUDENT REGISTRATION*\n\n"

            "Please enter your Full Name.\n\n"

            "Type /cancel to cancel.",

            parse_mode=
                "Markdown",

        )

        return


    # ========================================================
    # COURSES
    # ========================================================

    if text == "📚 Courses":

        await update.message.reply_text(

            "📚 *ALHIKAM COURSES*\n\n"

            "Please select a course:",

            parse_mode=
                "Markdown",

            reply_markup=
                ReplyKeyboardMarkup(

                    COURSE_MENU,

                    resize_keyboard=True,

                ),

        )

        return


    if text == "🎯 JAMB Science":

        await update.message.reply_text(

            "🎯 *JAMB SCIENCE*\n\n"

            "• Mathematics\n"

            "• English Language\n"

            "• Physics\n"

            "• Chemistry\n"

            "• Biology\n"

            "• Agricultural Science",

            parse_mode=
                "Markdown",

        )

        return


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

            parse_mode=
                "Markdown",

        )

        return


    if text == "📘 WAEC":

        await update.message.reply_text(

            "📘 *WAEC PREPARATION*\n\n"

            "📚 Study materials\n"

            "📝 Practice questions\n"

            "💻 CBT training\n"

            "🎓 Examination guidance",

            parse_mode=
                "Markdown",

        )

        return


    if text == "📕 NECO":

        await update.message.reply_text(

            "📕 *NECO PREPARATION*\n\n"

            "📚 Study materials\n"

            "📝 Practice questions\n"

            "💻 CBT training\n"

            "🎓 Examination guidance",

            parse_mode=
                "Markdown",

        )

        return


    if text == "💻 CBT Training":

        await update.message.reply_text(

            "💻 *CBT TRAINING*\n\n"

            "📝 Practice Questions\n"

            "⏱️ Timed Tests\n"

            "📊 Results and Scores\n\n"

            "🚧 CBT system is under development.",

            parse_mode=
                "Markdown",

        )

        return


    if text == "🔙 Back to Main Menu":

        await update.message.reply_text(

            "🏠 *MAIN MENU*",

            parse_mode=
                "Markdown",

            reply_markup=
                ReplyKeyboardMarkup(

                    MAIN_MENU,

                    resize_keyboard=True,

                ),

        )

        return


    # ========================================================
    # CBT
    # ========================================================

    if text == "📝 CBT Practice":

        await update.message.reply_text(

            "📝 *CBT PRACTICE*\n\n"

            "JAMB • WAEC • NECO\n\n"

            "🚧 This feature is under development.",

            parse_mode=
                "Markdown",

        )

        return


    # ========================================================
    # PAYMENT
    # ========================================================

    if text == "💳 Pay School Fees":

        await update.message.reply_text(

            "💳 *ALHIKAM SCHOOL FEES PAYMENT*\n\n"

            "Click below to open the payment page.\n\n"

            "After successful payment, you will be taken "
            "directly to registration.",

            parse_mode=
                "Markdown",

            reply_markup=
                InlineKeyboardMarkup([

                    [

                        InlineKeyboardButton(

                            "💳 OPEN PAYMENT PAGE",

                            url=
                                PUBLIC_PAYMENT_PAGE,

                        )

                    ]

                ]),

        )

        return


    # ========================================================
    # CONTACT
    # ========================================================

    if text == "📞 Contact Us":

        await update.message.reply_text(

            "📞 *CONTACT US*\n\n"

            "🎓 ALHIKAM Learning Center\n\n"

            "JAMB • WAEC • NECO • CBT Training",

            parse_mode=
                "Markdown",

        )

        return


    # ========================================================
    # ABOUT
    # ========================================================

    if text == "ℹ️ About Us":

        await update.message.reply_text(

            "🎓 *ALHIKAM Learning Center*\n\n"

            "JAMB • WAEC • NECO • CBT Training\n\n"

            "We provide educational support "
            "and examination preparation for students.",

            parse_mode=
                "Markdown",

        )

        return


    await update.message.reply_text(

        "❓ Please choose an option from the menu."

    )


# ============================================================
# MAIN
# ============================================================

def main():

    global telegram_bot_app

    if not BOT_TOKEN:

        raise ValueError(

            "BOT_TOKEN is missing."

        )

    if not FLW_SECRET_KEY:

        raise ValueError(

            "FLW_SECRET_KEY is missing."

        )

    if not FLUTTERWAVE_SECRET_HASH:

        raise ValueError(

            "FLUTTERWAVE_SECRET_HASH is missing."

        )


    # ========================================================
    # START FLASK
    # ========================================================

    web_thread = threading.Thread(

        target=
            run_web_server,

        daemon=True,

    )

    web_thread.start()


    # ========================================================
    # TELEGRAM BOT
    # ========================================================

    telegram_bot_app = (

        Application

        .builder()

        .token(

            BOT_TOKEN

        )

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

            filters.TEXT

            &

            ~filters.COMMAND,

            menu_handler,

        )

    )


    print(

        "================================"

    )

    print(

        "ALHIKAM Learning Center Bot Running"

    )

    print(

        "Payment Page:",
        PUBLIC_PAYMENT_PAGE,

    )

    print(

        "Flutterwave Webhook:",
        f"{RAILWAY_URL}/webhook/flutterwave",

    )

    print(

        "Registration Flow: ENABLED"

    )

    print(

        "Google Sheets: ENABLED"

    )

    print(

        "Unique Telegram Invite: ENABLED"

    )

    print(

        "Main Group ID:",
        MAIN_GROUP_ID,

    )

    print(

        "================================"

    )


    telegram_bot_app.run_polling(

        drop_pending_updates=True,

        close_loop=False,

    )


# ============================================================
# START APPLICATION
# ============================================================

if __name__ == "__main__":

    main()