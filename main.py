# ============================================================
# ALHIKAM Learning Center
# Part 1 - Imports, Settings, Flask & Telegram Setup
# ============================================================

import os
import time
import uuid
import hmac
import json
import asyncio
import hashlib
import logging
import threading
import requests

from flask import (
    Flask,
    request,
    jsonify,
    redirect,
    render_template_string,
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
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ============================================================
# ENVIRONMENT VARIABLES
# ============================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")

FLW_SECRET_KEY = os.getenv("FLW_SECRET_KEY")

FLUTTERWAVE_SECRET_HASH = os.getenv(
    "FLUTTERWAVE_SECRET_HASH"
)

SHEET_URL = os.getenv("SHEET_URL")

PORT = int(
    os.getenv("PORT", "8080")
)

RAILWAY_URL = os.getenv(
    "RAILWAY_URL",
    ""
).rstrip("/")

TELEGRAM_BOT_USERNAME = os.getenv(
    "TELEGRAM_BOT_USERNAME",
    "Alhikamcenterbot"
)

# ============================================================
# PAYMENT PLANS
# ============================================================

PAYMENT_PLANS = {

    "1": {
        "name": "1 Month",
        "amount": 3600
    },

    "2": {
        "name": "2 Months",
        "amount": 6800
    },

    "3": {
        "name": "3 Months",
        "amount": 10000
    },

    "4": {
        "name": "4 Months",
        "amount": 13200
    },

    "5": {
        "name": "5 Months",
        "amount": 16500
    },

    "6": {
        "name": "6 Months",
        "amount": 20000
    }

}

# ============================================================
# TEMP STORAGE
# ============================================================

pending_payments = {}

processed_payments = set()

telegram_bot_app = None

# ============================================================
# FLASK APP
# ============================================================

web_app = Flask(__name__)

# ============================================================
# HOME
# ============================================================

@web_app.route("/")

def home():

    return jsonify({

        "status": "online",

        "bot": "ALHIKAM Learning Center",

        "telegram": TELEGRAM_BOT_USERNAME,

        "payment": f"{RAILWAY_URL}/pay",

        "health": f"{RAILWAY_URL}/health"

    })

# ============================================================
# HEALTH CHECK
# ============================================================

@web_app.route("/health")

def health():

    return jsonify({

        "status": "healthy"

    })

# ============================================================
# RUN FLASK
# ============================================================

def run_web_server():

    logging.info("Starting Flask...")

    web_app.run(

        host="0.0.0.0",

        port=PORT,

        use_reloader=False

    )

# ============================================================
# TELEGRAM /START
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

async def start(

    update: Update,

    context: ContextTypes.DEFAULT_TYPE

):

    keyboard = ReplyKeyboardMarkup(

        MAIN_MENU,

        resize_keyboard=True

    )

    await update.message.reply_text(

        "🎓 Welcome to ALHIKAM Learning Center\n\n"

        "Please choose an option below.",

        reply_markup=keyboard

    )
# ============================================================
# PART 2 - FLUTTERWAVE PAYMENT
# ============================================================

PAYMENT_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>ALHIKAM Payment</title>
<meta name="viewport" content="width=device-width, initial-scale=1">

<style>

body{

font-family:Arial;

max-width:500px;

margin:auto;

padding:20px;

}

select,button{

width:100%;

padding:15px;

margin-top:15px;

}

button{

background:green;

color:white;

border:none;

font-size:16px;

}

</style>

</head>

<body>

<h2>ALHIKAM Learning Center</h2>

<form method="POST" action="/create-payment">

<select name="plan" required>

<option value="">Choose Payment Plan</option>

<option value="1">1 Month - ₦3,600</option>

<option value="2">2 Months - ₦6,800</option>

<option value="3">3 Months - ₦10,000</option>

<option value="4">4 Months - ₦13,200</option>

<option value="5">5 Months - ₦16,500</option>

<option value="6">6 Months - ₦20,000</option>

</select>

<button>

Continue Payment

</button>

</form>

</body>

</html>
"""

# ============================================================
# PAYMENT PAGE
# ============================================================

@web_app.route("/pay")

def pay():

    return render_template_string(

        PAYMENT_HTML

    )

# ============================================================
# CREATE PAYMENT
# ============================================================

@web_app.route(

"/create-payment",

methods=["POST"]

)

def create_payment():

    try:

        plan_id = request.form.get("plan")

        if plan_id not in PAYMENT_PLANS:

            return "Invalid payment plan.",400

        plan = PAYMENT_PLANS[plan_id]

        payment_token = uuid.uuid4().hex

        tx_ref = f"ALHIKAM_{payment_token}"

        pending_payments[payment_token] = {

            "status":"pending",

            "plan":plan

        }

        payload = {

            "tx_ref":tx_ref,

            "amount":plan["amount"],

            "currency":"NGN",

            "redirect_url":

            f"{RAILWAY_URL}/payment-success",

            "customer":{

                "email":

                f"{payment_token}@student.com",

                "name":"ALHIKAM Student"

            },

            "customizations":{

                "title":

                "ALHIKAM Learning Center"

            }

        }

        headers={

            "Authorization":

            f"Bearer {FLW_SECRET_KEY}"

        }

        response=requests.post(

            "https://api.flutterwave.com/v3/payments",

            json=payload,

            headers=headers,

            timeout=30

        )

        result=response.json()

        if result.get("status")=="success":

            return redirect(

                result["data"]["link"]

            )

        logging.error(result)

        return "Unable to create payment.",500

    except Exception as e:

        logging.exception(e)

        return "Internal Server Error",500

# ============================================================
# PAYMENT SUCCESS
# ============================================================

@web_app.route("/payment-success")

def payment_success():

    tx_ref=request.args.get("tx_ref","")

    transaction_id=request.args.get("transaction_id","")

    return f"""

<h2>Payment Submitted</h2>

<p>

Transaction Reference:

<br>

<b>{tx_ref}</b>

</p>

<p>

Transaction ID:

<br>

<b>{transaction_id}</b>

</p>

<p>

Please wait while your payment is verified.

</p>

"""
# ============================================================
# PART 3 - FLUTTERWAVE WEBHOOK
# ============================================================

def verify_flutterwave_transaction(transaction_id):

    try:

        headers = {
            "Authorization": f"Bearer {FLW_SECRET_KEY}"
        }

        response = requests.get(
            f"https://api.flutterwave.com/v3/transactions/{transaction_id}/verify",
            headers=headers,
            timeout=30
        )

        if response.status_code != 200:
            logging.error("Verification request failed.")
            return None

        result = response.json()

        if result.get("status") != "success":
            return None

        return result.get("data")

    except Exception as e:
        logging.exception(e)
        return None


# ============================================================
# WEBHOOK
# ============================================================

@web_app.route(
    "/webhook/flutterwave",
    methods=["POST"]
)
def flutterwave_webhook():

    try:

        incoming_hash = request.headers.get("verif-hash")

        if incoming_hash != FLUTTERWAVE_SECRET_HASH:
            return "Unauthorized", 401

        payload = request.get_json()

        if not payload:
            return "Invalid Payload", 400

        data = payload.get("data", {})

        transaction_id = data.get("id")
        tx_ref = data.get("tx_ref")

        if not transaction_id or not tx_ref:
            return "Missing Transaction", 400

        verified = verify_flutterwave_transaction(
            transaction_id
        )

        if not verified:
            return "Verification Failed", 400

        if verified["status"] != "successful":
            return "Payment Not Successful", 200

        if verified["currency"] != "NGN":
            return "Invalid Currency", 400

        payment_token = tx_ref.replace(
            "ALHIKAM_",
            ""
        )

        if payment_token not in pending_payments:
            return "Payment Record Not Found", 404

        if payment_token in processed_payments:
            return "Already Processed", 200

        processed_payments.add(payment_token)

        pending_payments[payment_token]["status"] = "successful"

        pending_payments[payment_token]["amount"] = verified["amount"]

        pending_payments[payment_token]["transaction_id"] = transaction_id

        pending_payments[payment_token]["tx_ref"] = tx_ref

        logging.info(
            f"Payment Verified: {tx_ref}"
        )

        return "OK", 200

    except Exception as e:

        logging.exception(e)

        return "Internal Server Error", 500


# ============================================================
# PAYMENT STATUS
# ============================================================

@web_app.route("/payment-status/<payment_token>")
def payment_status(payment_token):

    payment = pending_payments.get(payment_token)

    if not payment:

        return jsonify({

            "status": "not_found"

        }),404

    return jsonify(payment)
# ============================================================
# PART 4 - TELEGRAM LOGIN
# ============================================================

TELEGRAM_LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Connect Telegram</title>

<script async
src="https://telegram.org/js/telegram-widget.js?22"
data-telegram-login="{{ bot_username }}"
data-size="large"
data-userpic="false"
data-request-access="write"
data-onauth="onTelegramAuth(user)">
</script>

<script>

function onTelegramAuth(user){

    const form=document.createElement("form");

    form.method="POST";

    form.action="/telegram-auth";

    const fields={

        payment_token:"{{ payment_token }}",

        id:user.id,

        first_name:user.first_name||"",

        last_name:user.last_name||"",

        username:user.username||"",

        photo_url:user.photo_url||"",

        auth_date:user.auth_date,

        hash:user.hash

    };

    for(const key in fields){

        const input=document.createElement("input");

        input.type="hidden";

        input.name=key;

        input.value=fields[key];

        form.appendChild(input);

    }

    document.body.appendChild(form);

    form.submit();

}

</script>

</head>

<body>

<h2>Connect Your Telegram Account</h2>

<p>

Click the Telegram button below.

</p>

</body>

</html>
"""

# ============================================================
# REGISTER
# ============================================================

@web_app.route("/register/<payment_token>")
def register(payment_token):

    payment=pending_payments.get(payment_token)

    if not payment:
        return "Payment Not Found",404

    if payment["status"]!="successful":
        return "Payment not verified.",400

    return render_template_string(

        TELEGRAM_LOGIN_HTML,

        payment_token=payment_token,

        bot_username=TELEGRAM_BOT_USERNAME

    )

# ============================================================
# VERIFY TELEGRAM LOGIN
# ============================================================

def verify_telegram_login(data):

    received_hash=data.pop("hash")

    data_check=[]

    for k,v in sorted(data.items()):

        if v!="":

            data_check.append(f"{k}={v}")

    data_check_string="\n".join(data_check)

    secret_key=hashlib.sha256(

        BOT_TOKEN.encode()

    ).digest()

    calculated_hash=hmac.new(

        secret_key,

        data_check_string.encode(),

        hashlib.sha256

    ).hexdigest()

    return hmac.compare_digest(

        calculated_hash,

        received_hash

    )

# ============================================================
# TELEGRAM AUTH
# ============================================================

@web_app.route(

"/telegram-auth",

methods=["POST"]

)

def telegram_auth():

    form=dict(request.form)

    payment_token=form.get("payment_token")

    payment=pending_payments.get(payment_token)

    if not payment:

        return "Payment Not Found",404

    if not verify_telegram_login(form.copy()):

        return "Telegram Verification Failed",401

    payment["telegram"]={

        "telegram_id":form["id"],

        "username":form.get("username",""),

        "first_name":form.get("first_name",""),

        "last_name":form.get("last_name","")

    }

    logging.info(

        f"Telegram Linked: {form['id']}"

    )

    return redirect(

        f"/registration-form/{payment_token}"

    )
# ============================================================
# PART 5 - STUDENT REGISTRATION
# ============================================================

REGISTRATION_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Student Registration</title>
<meta name="viewport" content="width=device-width, initial-scale=1">

<style>

body{

font-family:Arial;

max-width:500px;

margin:auto;

padding:20px;

}

input,select{

width:100%;

padding:12px;

margin:10px 0;

}

button{

width:100%;

padding:15px;

background:green;

color:white;

border:none;

font-size:16px;

}

</style>

</head>

<body>

<h2>ALHIKAM Registration</h2>

<form method="POST">

<input
type="text"
name="full_name"
placeholder="Full Name"
required>

<input
type="tel"
name="phone"
placeholder="Phone Number"
required>

<input
type="email"
name="email"
placeholder="Email Address"
required>

<select
name="course"
required>

<option value="">Choose Course</option>

<option>JAMB Science</option>

<option>JAMB Arts</option>

<option>WAEC</option>

<option>NECO</option>

<option>CBT Training</option>

</select>

<button>

Complete Registration

</button>

</form>

</body>

</html>

"""

# ============================================================
# REGISTRATION FORM
# ============================================================

@web_app.route(

"/registration-form/<payment_token>",

methods=["GET","POST"]

)

def registration_form(payment_token):

    payment = pending_payments.get(payment_token)

    if not payment:

        return "Payment Not Found",404

    if request.method=="GET":

        return render_template_string(

            REGISTRATION_HTML

        )

    full_name=request.form.get("full_name")

    phone=request.form.get("phone")

    email=request.form.get("email")

    course=request.form.get("course")

    payment["registration"]={

        "full_name":full_name,

        "phone":phone,

        "email":email,

        "course":course

    }

    logging.info(

        f"Registration Completed: {full_name}"

    )

    return redirect(

        f"/registration-success/{payment_token}"

    )

# ============================================================
# SUCCESS PAGE
# ============================================================

@web_app.route(

"/registration-success/<payment_token>"

)

def registration_success(payment_token):

    payment=pending_payments.get(payment_token)

    if not payment:

        return "Not Found",404

    student=payment["registration"]

    return f"""

<h2>

Registration Completed

</h2>

<p>

Welcome

<b>

{student["full_name"]}

</b>

</p>

<p>

Your registration has been received successfully.

</p>

<p>

The system will now prepare your course access.

</p>

"""
# ============================================================
# PART 6 - GOOGLE SHEETS
# ============================================================

SHEET_URL = os.getenv("SHEET_URL")

# ============================================================
# SAVE TO GOOGLE SHEETS
# ============================================================

def save_to_google_sheets(student_data):

    if not SHEET_URL:

        logging.error("SHEET_URL not configured")

        return False

    try:

        response = requests.post(

            SHEET_URL,

            json=student_data,

            timeout=30

        )

        if response.status_code == 200:

            logging.info("Student saved successfully")

            return True

        logging.error(response.text)

        return False

    except Exception as e:

        logging.exception(e)

        return False


# ============================================================
# UPDATE REGISTRATION FORM
# ============================================================

# A cikin registration_form()
# bayan payment["registration"] = {...}

registration_data = {

    "telegram_id":

        payment["telegram"]["telegram_id"],

    "telegram_username":

        payment["telegram"]["username"],

    "full_name":

        full_name,

    "phone":

        phone,

    "email":

        email,

    "course":

        course,

    "amount_paid":

        payment["amount"],

    "transaction_id":

        payment["transaction_id"],

    "tx_ref":

        payment["tx_ref"]

}

saved = save_to_google_sheets(

    registration_data

)

if not saved:

    return """

<h2>

Registration Failed

</h2>

<p>

Unable to save your details.

Please try again later.

</p>

""",500

payment["registration"] = registration_data

logging.info(

    f"Google Sheets Saved: {full_name}"

)

return redirect(

    f"/registration-success/{payment_token}"

)
function doPost(e){

  const sheet = SpreadsheetApp
      .getActiveSpreadsheet()
      .getSheetByName("Students");

  const data = JSON.parse(e.postData.contents);

  sheet.appendRow([

    new Date(),

    data.telegram_id,

    data.telegram_username,

    data.full_name,

    data.phone,

    data.email,

    data.course,

    data.amount_paid,

    data.transaction_id,

    data.tx_ref

  ]);

  return ContentService
      .createTextOutput("OK");

}

# ============================================================
# PART 7 - TELEGRAM INVITE LINKS
# ============================================================

# Environment Variables
MAIN_GROUP_ID = int(os.getenv("MAIN_GROUP_ID"))
ANNOUNCEMENT_CHANNEL_ID = int(os.getenv("ANNOUNCEMENT_CHANNEL_ID"))
SCIENCE_FACULTY_ID = int(os.getenv("SCIENCE_FACULTY_ID"))
ARTS_FACULTY_ID = int(os.getenv("ARTS_FACULTY_ID"))

SCIENCE_SUBJECTS = {
    "Mathematics": int(os.getenv("SCIENCE_MATH_ID")),
    "English": int(os.getenv("SCIENCE_ENGLISH_ID")),
    "Biology": int(os.getenv("SCIENCE_BIOLOGY_ID")),
    "Chemistry": int(os.getenv("SCIENCE_CHEMISTRY_ID")),
    "Physics": int(os.getenv("SCIENCE_PHYSICS_ID")),
}

ARTS_SUBJECTS = {
    "English": int(os.getenv("ARTS_ENGLISH_ID")),
    "Literature": int(os.getenv("ARTS_LITERATURE_ID")),
    "Government": int(os.getenv("ARTS_GOVERNMENT_ID")),
    "Economics": int(os.getenv("ARTS_ECONOMICS_ID")),
    "CRS": int(os.getenv("ARTS_CRS_ID")),
}

FACULTY_ACCESS = {
    "JAMB Science": {
        "faculty": SCIENCE_FACULTY_ID,
        "subjects": SCIENCE_SUBJECTS
    },
    "JAMB Arts": {
        "faculty": ARTS_FACULTY_ID,
        "subjects": ARTS_SUBJECTS
    },
    "WAEC": {
        "faculty": SCIENCE_FACULTY_ID,
        "subjects": SCIENCE_SUBJECTS
    },
    "NECO": {
        "faculty": SCIENCE_FACULTY_ID,
        "subjects": SCIENCE_SUBJECTS
    },
}

# ============================================================
# CREATE INVITE LINKS
# ============================================================

async def create_course_invites(course):

    bot = telegram_bot_app.bot

    links = []

    invite = await bot.create_chat_invite_link(
        MAIN_GROUP_ID,
        member_limit=1
    )

    links.append(("🎓 Main Group", invite.invite_link))

    invite = await bot.create_chat_invite_link(
        ANNOUNCEMENT_CHANNEL_ID,
        member_limit=1
    )

    links.append(("📢 Announcement", invite.invite_link))

    faculty = FACULTY_ACCESS.get(course)

    if faculty:

        invite = await bot.create_chat_invite_link(
            faculty["faculty"],
            member_limit=1
        )

        links.append(("🏫 Faculty", invite.invite_link))

        for subject, chat_id in faculty["subjects"].items():

            invite = await bot.create_chat_invite_link(
                chat_id,
                member_limit=1
            )

            links.append(
                (f"📚 {subject}", invite.invite_link)
            )

    return links

# ============================================================
# SEND INVITES
# ============================================================

async def send_access_message(payment):

    telegram_id = int(
        payment["telegram"]["telegram_id"]
    )

    student = payment["registration"]

    links = await create_course_invites(
        student["course"]
    )

    keyboard = []

    for title, url in links:

        keyboard.append([
            InlineKeyboardButton(
                text=title,
                url=url
            )
        ])

    await telegram_bot_app.bot.send_message(

        chat_id=telegram_id,

        text=f"""
🎉 Registration Successful

👤 {student['full_name']}

📚 {student['course']}

💰 ₦{payment['amount']:,}

Click the buttons below to join all your official classes.
""",

        reply_markup=InlineKeyboardMarkup(
            keyboard
        )

    )

# ============================================================
# AFTER REGISTRATION
# ============================================================

# Bayan an gama Google Sheets:

threading.Thread(

    target=lambda: asyncio.run(

        send_access_message(payment)

    ),

    daemon=True

).start()

# ============================================================
# PART 8 - MAIN APPLICATION STARTUP
# ============================================================

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Unknown command. Type /start."
    )

# ============================================================
# START TELEGRAM BOT
# ============================================================

async def on_startup(application):

    logging.info("================================")
    logging.info("ALHIKAM BOT STARTED")
    logging.info("Telegram Bot Online")
    logging.info("================================")

# ============================================================
# BUILD APPLICATION
# ============================================================

def build_bot():

    global telegram_bot_app

    telegram_bot_app = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    telegram_bot_app.post_init = on_startup

    telegram_bot_app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    telegram_bot_app.add_handler(

        MessageHandler(

            filters.COMMAND,

            unknown

        )

    )

    return telegram_bot_app

# ============================================================
# RUN EVERYTHING
# ============================================================

def main():

    if not BOT_TOKEN:

        raise RuntimeError(
            "BOT_TOKEN not configured."
        )

    flask_thread = threading.Thread(

        target=run_web_server,

        daemon=True

    )

    flask_thread.start()

    logging.info(
        "Flask Started"
    )

    application = build_bot()

    application.run_polling(

        drop_pending_updates=True,

        close_loop=False

    )

# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    try:

        main()

    except KeyboardInterrupt:

        logging.info(
            "Bot stopped by user."
        )

    except Exception as e:

        logging.exception(e)