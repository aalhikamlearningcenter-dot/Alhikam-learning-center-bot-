
# ALHIKAM Learning Center Bot
# Updated flow:
# Flutterwave Payment -> Verified Payment -> Telegram Login -> Registration
# -> Google Sheets -> Unique Telegram Invite -> Bot sends invite directly

import os
import time
import uuid
import hmac
import hashlib
import json
import asyncio
import threading
import requests
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

from flask import Flask, request, jsonify, render_template_string, redirect
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
    "https://script.google.com/macros/s/AKfycbw6LRBGCzMIHcWGEIKXAYXo9bMHxsO_am4a4iSZ4kR58FFA-bj4TcUNy085uTaVRx2z0A/exec",
)

RAILWAY_URL = os.getenv(
    "RAILWAY_URL",
    "https://precious-trust-production-956b.up.railway.app",
).rstrip("/")

PORT = int(os.getenv("PORT", "8080"))

# ============================================================
# TELEGRAM GROUPS & CHANNELS
# ============================================================

# Main gateway group (student must join this first)
MAIN_GROUP_ID = -1004384506380

# Announcement channel
ANNOUNCEMENT_CHANNEL_ID = -1004315707986

# Faculty groups
SCIENCE_FACULTY_ID = -1004479887604
ARTS_FACULTY_ID = -1004314659728
COMMERCIAL_FACULTY_ID = -1003967146846

# Science subjects
SCIENCE_SUBJECTS = {
    "Physics": -1004467391688,
    "Chemistry": -1003575115831,
    "Biology": -1004412247385,
    "Mathematics": -1004480230539,
    "Agricultural Science": -1004398599335,
    "Geography": -1003901130871,
}

# Arts subjects
ARTS_SUBJECTS = {
    "History": -1004494276405,
    "Hausa": -1004436228793,
    "CRS": -1004469127265,
    "Islamic Studies": -1003823376901,
    "Government": -1003735736424,
    "Literature in English": -1004317587777,
    "Use of English": -1003759215809,
    "Fine Arts": -1003801904375,
}

# Commercial subjects
COMMERCIAL_SUBJECTS = {
    "Principles of Accounts": -1004459228986,
    "Commerce": -1003930273330,
    "Economics": -1003632758498,
    "Use of English": -1003759215809,
}

# Payment & registration support
PAYMENT_REGISTRATION_ID = -1003935952561

# Public payment page
PUBLIC_PAYMENT_PAGE = f"{RAILWAY_URL}/pay"

# Telegram Login Widget bot username
TELEGRAM_BOT_USERNAME = "Alhikamcenterbot"

# ============================================================
# FACULTY ACCESS MAPPING
# ============================================================

FACULTY_ACCESS = {
    "JAMB Science": {
        "faculty": SCIENCE_FACULTY_ID,
        "subjects": SCIENCE_SUBJECTS,
    },

    "JAMB Arts": {
        "faculty": ARTS_FACULTY_ID,
        "subjects": ARTS_SUBJECTS,
    },

    "WAEC": {
        "faculty": SCIENCE_FACULTY_ID,
        "subjects": SCIENCE_SUBJECTS,
    },

    "NECO": {
        "faculty": SCIENCE_FACULTY_ID,
        "subjects": SCIENCE_SUBJECTS,
    },

    "CBT Training": {
        "faculty": SCIENCE_FACULTY_ID,
        "subjects": {
            "Mathematics": -1004480230539,
            "Use of English": -1003759215809,
        },
    },
}



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
# TEMPORARY STORAGE
# NOTE: Railway restarts clear this memory. For production,
# move pending payments to a persistent database.
# ============================================================

pending_payments = {}
processed_payments = set()
telegram_bot_app = None


# ============================================================
# FLASK
# ============================================================

web_app = Flask(__name__)


@web_app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "online",
        "bot": "ALHIKAM Learning Center Bot",
        "payment_page": PUBLIC_PAYMENT_PAGE,
        "webhook": f"{RAILWAY_URL}/webhook/flutterwave",
        "telegram_login": f"{RAILWAY_URL}/telegram-auth",
    })


@web_app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"})


# ============================================================
# PAYMENT PAGE
# ============================================================

PAYMENT_PAGE_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ALHIKAM Learning Center Payment</title>
<style>
body{font-family:Arial,sans-serif;background:#f4f7f6;margin:0;padding:20px}
.container{max-width:520px;margin:30px auto;background:white;padding:25px;border-radius:16px;box-shadow:0 4px 18px rgba(0,0,0,.10)}
h1{color:#087f5b;text-align:center}
.subtitle{text-align:center;color:#555;margin-bottom:25px}
.plan{border:1px solid #ddd;border-radius:12px;padding:15px;margin:10px 0}
.plan label{display:block;cursor:pointer}
.amount{font-weight:bold;font-size:18px;color:#087f5b}
button{width:100%;padding:15px;margin-top:20px;border:none;border-radius:10px;background:#087f5b;color:white;font-size:17px;font-weight:bold;cursor:pointer}
.note{text-align:center;font-size:13px;color:#777;margin-top:18px}
</style>
</head>
<body>
<div class="container">
<h1>🎓 ALHIKAM Learning Center</h1>
<div class="subtitle">Choose your learning duration and continue to secure payment.</div>

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

<button type="submit">💳 CONTINUE TO SECURE PAYMENT</button>
</form>

<div class="note">
After successful payment, you will connect your Telegram account and complete registration.
</div>
</div>
</body>
</html>
"""


@web_app.route("/pay", methods=["GET"])
def payment_page():
    return render_template_string(PAYMENT_PAGE_HTML, plans=PAYMENT_PLANS)


# ============================================================
# CREATE FLUTTERWAVE PAYMENT
# ============================================================

@web_app.route("/create-payment", methods=["POST"])
def create_payment():
    if not FLW_SECRET_KEY:
        return "Payment system is temporarily unavailable.", 500

    plan_number = request.form.get("plan")
    plan = PAYMENT_PLANS.get(plan_number)

    if not plan:
        return "Invalid payment plan.", 400

    payment_token = uuid.uuid4().hex
    tx_ref = f"ALHIKAM_{payment_token}"

    pending_payments[payment_token] = {
        "tx_ref": tx_ref,
        "plan": plan_number,
        "plan_name": plan["name"],
        "amount": plan["amount"],
        "status": "pending",
    }

    payload = {
        "tx_ref": tx_ref,
        "amount": plan["amount"],
        "currency": "NGN",
        "redirect_url": f"{RAILWAY_URL}/payment-complete/{payment_token}",
        "customer": {
            "email": f"student_{payment_token}@alhikam.com",
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

        if response.status_code == 200 and result.get("status") == "success":
            payment_link = result.get("data", {}).get("link")

            if payment_link:
                return redirect(payment_link)

        return "Unable to create payment link. Please try again.", 500

    except Exception as e:
        print("Flutterwave API Error:", e)
        return "Payment system error. Please try again later.", 500


# ============================================================
# PAYMENT RETURN PAGE
# ============================================================

@web_app.route("/payment-complete/<payment_token>", methods=["GET"])
def payment_complete(payment_token):
    payment = pending_payments.get(payment_token)

    if not payment:
        return """
        <h2>Payment Reference Not Found</h2>
        <p>Please contact ALHIKAM Learning Center.</p>
        """, 404

    if payment.get("status") != "successful":
        return f"""
        <html>
        <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
        body{{font-family:Arial;text-align:center;padding:50px 20px}}
        </style>
        </head>
        <body>
        <h2>⏳ Payment Verification</h2>
        <p>Your payment is being verified.</p>
        <p>Please wait a moment and refresh this page.</p>
        <a href="/payment-complete/{payment_token}">🔄 Refresh</a>
        </body>
        </html>
        """

    return redirect(f"/register/{payment_token}")


# ============================================================
# TELEGRAM LOGIN PAGE
# ============================================================

TELEGRAM_LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Connect Telegram</title>

<style>
body{
    font-family:Arial,sans-serif;
    background:#f4f7f6;
    padding:20px;
}
.container{
    max-width:520px;
    margin:30px auto;
    background:white;
    padding:25px;
    border-radius:16px;
    box-shadow:0 4px 18px rgba(0,0,0,.10);
    text-align:center;
}
h1{color:#087f5b}
.info{
    background:#eef8f4;
    padding:15px;
    border-radius:10px;
    margin:20px 0;
    text-align:left;
}
</style>

<script async src="https://telegram.org/js/telegram-widget.js?22"
        data-telegram-login="{{ bot_username }}"
        data-size="large"
        data-userpic="false"
        data-request-access="write"
        data-onauth="onTelegramAuth(user)">
</script>

<script>
function onTelegramAuth(user) {
    const form = document.createElement("form");
    form.method = "POST";
    form.action = "/telegram-auth";

    const data = {
        payment_token: "{{ payment_token }}",
        id: user.id,
        first_name: user.first_name || "",
        last_name: user.last_name || "",
        username: user.username || "",
        photo_url: user.photo_url || "",
        auth_date: user.auth_date,
        hash: user.hash
    };

    for (const key in data) {
        const input = document.createElement("input");
        input.type = "hidden";
        input.name = key;
        input.value = data[key];
        form.appendChild(input);
    }

    document.body.appendChild(form);
    form.submit();
}
</script>

</head>

<body>
<div class="container">

<h1>🔗 Connect Your Telegram</h1>

<div class="info">
<strong>Payment Confirmed ✅</strong><br><br>
Plan: {{ plan_name }}<br>
Amount: ₦{{ "{:,}".format(amount) }}
</div>

<p>
To continue registration, connect the Telegram account you will use to receive your ALHIKAM class invite.
</p>

<p>
<strong>⚠️ Do not enter your Telegram ID manually.</strong>
</p>

<p>
Click the Telegram button below to connect your account.
</p>

</div>
</body>
</html>
"""


@web_app.route("/register/<payment_token>", methods=["GET"])
def register_student(payment_token):
    payment = pending_payments.get(payment_token)

    if not payment:
        return "Payment reference not found.", 404

    if payment.get("status") != "successful":
        return "Payment has not yet been verified.", 400

    if payment.get("registration_completed"):
        return """
        <h2>Registration Already Completed</h2>
        <p>Your Telegram class access has already been processed.</p>
        """

    if payment.get("telegram_auth"):
        return redirect(f"/registration-form/{payment_token}")

    return render_template_string(
        TELEGRAM_LOGIN_HTML,
        bot_username=TELEGRAM_BOT_USERNAME,
        payment_token=payment_token,
        plan_name=payment["plan_name"],
        amount=payment["amount"],
    )


# ============================================================
# TELEGRAM LOGIN VERIFICATION
# ============================================================

def verify_telegram_login(data):
    if not BOT_TOKEN:
        return False

    received_hash = data.get("hash", "")
    auth_date = str(data.get("auth_date", ""))
    telegram_id = str(data.get("id", ""))

    if not received_hash or not auth_date or not telegram_id:
        return False

    # Prevent very old authentication data
    try:
        if abs(int(__import__("time").time()) - int(auth_date)) > 86400:
            return False
    except Exception:
        return False

    check_data = {
        "id": telegram_id,
        "first_name": data.get("first_name", ""),
        "last_name": data.get("last_name", ""),
        "username": data.get("username", ""),
        "photo_url": data.get("photo_url", ""),
        "auth_date": auth_date,
    }

    # Telegram requires only fields actually received.
    pairs = []
    for key, value in check_data.items():
        if value not in (None, ""):
            pairs.append(f"{key}={value}")

    data_check_string = "\n".join(sorted(pairs))

    secret_key = hashlib.sha256(BOT_TOKEN.encode()).digest()

    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(
        calculated_hash,
        received_hash,
    )


@web_app.route("/telegram-auth", methods=["POST"])
def telegram_auth():
    payment_token = request.form.get("payment_token", "")
    payment = pending_payments.get(payment_token)

    if not payment:
        return "Payment reference not found.", 404

    if payment.get("status") != "successful":
        return "Payment has not been verified.", 400

    data = {
        "id": request.form.get("id", ""),
        "first_name": request.form.get("first_name", ""),
        "last_name": request.form.get("last_name", ""),
        "username": request.form.get("username", ""),
        "photo_url": request.form.get("photo_url", ""),
        "auth_date": request.form.get("auth_date", ""),
        "hash": request.form.get("hash", ""),
    }

    if not verify_telegram_login(data):
        return """
        <h2>Telegram Verification Failed ❌</h2>
        <p>Please go back and connect Telegram again.</p>
        """, 401

    payment["telegram_auth"] = {
        "telegram_id": data["id"],
        "telegram_username": data["username"],
        "first_name": data["first_name"],
        "last_name": data["last_name"],
    }

    return redirect(
        f"/registration-form/{payment_token}"
    )


# ============================================================
# REGISTRATION FORM
# ============================================================

REGISTRATION_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ALHIKAM Student Registration</title>

<style>
body{font-family:Arial;background:#f4f7f6;padding:20px}
.container{max-width:520px;margin:30px auto;background:white;padding:25px;border-radius:16px;box-shadow:0 4px 18px rgba(0,0,0,.10)}
h1{color:#087f5b;text-align:center}
input,select{width:100%;padding:13px;margin:8px 0 15px;border:1px solid #ddd;border-radius:8px;box-sizing:border-box}
button{width:100%;padding:15px;background:#087f5b;color:white;border:none;border-radius:10px;font-size:17px;font-weight:bold}
.info{background:#eef8f4;padding:15px;border-radius:10px;margin-bottom:20px}
.connected{background:#e8f5e9;padding:12px;border-radius:8px;margin-bottom:20px}
</style>
</head>

<body>
<div class="container">

<h1>🎓 ALHIKAM Learning Center</h1>

<div class="info">
<strong>Payment Confirmed ✅</strong><br><br>
Plan: {{ plan_name }}<br>
Amount: ₦{{ "{:,}".format(amount) }}
</div>

<div class="connected">
<strong>Telegram Connected ✅</strong><br>
Username: @{{ telegram_username if telegram_username else "Telegram User" }}
<br>
Your Telegram ID has been verified automatically.
</div>

<form method="POST">

<label>Full Name</label>
<input type="text" name="full_name" required>

<label>Phone Number</label>
<input type="tel" name="phone" required>

<label>Email Address</label>
<input type="email" name="email" required>

<label>Course</label>
<select name="course" required>
<option value="">Select Course</option>
<option>JAMB Science</option>
<option>JAMB Arts</option>
<option>WAEC</option>
<option>NECO</option>
<option>CBT Training</option>
</select>

<button type="submit">✅ COMPLETE REGISTRATION</button>

</form>
</div>
</body>
</html>
"""


@web_app.route(
    "/registration-form/<payment_token>",
    methods=["GET", "POST"],
)
def registration_form(payment_token):
    payment = pending_payments.get(payment_token)

    if not payment:
        return "Payment reference not found.", 404

    if payment.get("status") != "successful":
        return "Payment has not yet been verified.", 400

    telegram_auth = payment.get("telegram_auth")

    if not telegram_auth:
        return redirect(f"/register/{payment_token}")

    if payment.get("registration_completed"):
        return """
        <h2>Registration Already Completed</h2>
        <p>Your Telegram class access has already been processed.</p>
        """

    if request.method == "GET":
        return render_template_string(
            REGISTRATION_HTML,
            plan_name=payment["plan_name"],
            amount=payment["amount"],
            telegram_username=telegram_auth.get(
                "telegram_username",
                "",
            ),
        )

    full_name = request.form.get(
        "full_name",
        "",
    ).strip()

    phone = request.form.get(
        "phone",
        "",
    ).strip()

    email = request.form.get(
        "email",
        "",
    ).strip()

    course = request.form.get(
        "course",
        "",
    ).strip()

    if not full_name or not phone or not email or not course:
        return "Please complete all required fields.", 400

    registration_data = {
        "telegram_id": telegram_auth["telegram_id"],
        "telegram_username": telegram_auth["telegram_username"],
        "full_name": full_name,
        "phone": phone,
        "email": email,
        "course": course,
        "payment_plan": payment["plan_name"],
        "amount_paid": payment["amount"],
        "tx_ref": payment["tx_ref"],
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

    invite_link = create_unique_invite_link(
        payment_token
    )

    if not invite_link:
        return """
        <h2>Registration Saved ✅</h2>
        <p>
        Your registration was saved, but your Telegram invite
        could not be created automatically.
        Please contact ALHIKAM Learning Center.
        </p>
        """, 500

    payment["registration_completed"] = True
    payment["registration"] = registration_data
    payment["invite_link"] = invite_link

    telegram_id = int(
        telegram_auth["telegram_id"]
    )
    threading.Thread(
        target=send_registration_access,
        args=(
            telegram_id,
            full_name,
            payment["amount"],
            course,
        ),
        daemon=True,
    ).start()

    return f"""
    <html>
    <head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
    body{{font-family:Arial;text-align:center;padding:40px 20px}}
    </style>
    </head>
    <body>
    <h1>🎉 Registration Completed!</h1>
    <p>
    Welcome to ALHIKAM Learning Center,
    <strong>{full_name}</strong>.
    </p>
    <p>
    Your payment and registration have been confirmed.
    </p>
    <p>
    ✅ Your unique Telegram class invite has been sent to your connected Telegram account.
    </p>
    <p>
    Please open Telegram and check the message from
    <strong>@Alhikamcenterbot</strong>.
    </p>
    </body>
    </html>
    """


# ============================================================
# GOOGLE SHEETS
# ============================================================

def save_registration_to_google_sheets(data):
    try:
        print("Saving registration:", data)

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
        print("Google Sheets Error:", e)
        return False


# ============================================================
# CREATE UNIQUE TELEGRAM INVITE LINK
# ============================================================

def create_unique_invite_link(payment_token):
    global telegram_bot_app

    if telegram_bot_app is None:
        print("Telegram application not ready.")
        return None

    try:
        async def create_link():
            return await telegram_bot_app.bot.create_chat_invite_link(
                chat_id=MAIN_GROUP_ID,
                member_limit=1,
                name=f"ALHIKAM-{payment_token[:10]}",
            )

        invite_link = asyncio.run(create_link())
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
async def create_course_invites(course):
    global telegram_bot_app

    links = []

    # Main Group
    main = await telegram_bot_app.bot.create_chat_invite_link(
        chat_id=MAIN_GROUP_ID,
        member_limit=1,
    )
    links.append(("🎓 Main Class", main.invite_link))

    # Announcement
    ann = await telegram_bot_app.bot.create_chat_invite_link(
        chat_id=ANNOUNCEMENT_CHANNEL_ID,
        member_limit=1,
    )
    links.append(("📢 Announcement Channel", ann.invite_link))

    # Payment Support
    support = await telegram_bot_app.bot.create_chat_invite_link(
        chat_id=PAYMENT_REGISTRATION_ID,
        member_limit=1,
    )
    links.append(("🆘 Payment Support", support.invite_link))

    # Faculty
    faculty = FACULTY_ACCESS.get(course)

    if faculty:
        faculty_link = await telegram_bot_app.bot.create_chat_invite_link(
            chat_id=faculty["faculty"],
            member_limit=1,
        )

        links.append(("🏫 Faculty Group", faculty_link.invite_link))

        for subject_name, subject_id in faculty["subjects"].items():

            subject_link = await telegram_bot_app.bot.create_chat_invite_link(
                chat_id=subject_id,
                member_limit=1,
            )

            links.append(
                (
                    f"📚 {subject_name}",
                    subject_link.invite_link,
                )
            )

    return links
def send_registration_access(
    telegram_id,
    full_name,
    amount,
    course,
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
        payment_group = await telegram_bot_app.bot.create_chat_invite_link(
            chat_id=PAYMENT_REGISTRATION_ID,
            member_limit=1,
            name=f"Support-{telegram_id}",
        )

        announcement = await telegram_bot_app.bot.create_chat_invite_link(
            chat_id=ANNOUNCEMENT_CHANNEL_ID,
            member_limit=1,
            name=f"Announcement-{telegram_id}",
        )

        await telegram_bot_app.bot.send_message(
            chat_id=telegram_id,
            parse_mode="Markdown",
            text=(
                f"🎉 *Welcome {full_name}!*\n\n"
                "✅ Payment Confirmed\n"
                "✅ Registration Completed\n\n"
                f"💰 Amount Paid: ₦{amount:,}\n\n"
                "Click the buttons below one by one."
            ),
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🎓 Main Class",
                        url=invite_link,
                    )
                ],
                [
                    InlineKeyboardButton(
                        "📢 Announcement Channel",
                        url=announcement.invite_link,
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🆘 Payment Support",
                        url=payment_group.invite_link,
                    )
                ],
            ]),
        )

        print("Telegram access sent successfully.")

    except Exception as e:
        print("Telegram Error:", e)

    global telegram_bot_app

    if telegram_bot_app is None:
        return

    try:
        await telegram_bot_app.bot.send_message(
            chat_id=telegram_id,
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
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🎓 JOIN ALHIKAM CLASS",
                        url=invite_link,
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
  async def send_access_message(
    telegram_id,
    full_name,
    amount,
    course,
):
    global telegram_bot_app

    if telegram_bot_app is None:
        return

    try:
        links = await create_course_invites(course)

        keyboard = []

        for title, url in links:
            keyboard.append([
                InlineKeyboardButton(
                    title,
                    url=url,
                )
            ])

        await telegram_bot_app.bot.send_message(
            chat_id=telegram_id,
            parse_mode="Markdown",
            text=(
                f"🎉 *Welcome {full_name}!*\n\n"
                "✅ Payment Confirmed\n"
                "✅ Registration Completed\n\n"
                f"💰 Amount Paid: ₦{amount:,}\n\n"
                f"📚 Course: {course}\n\n"
                "Below are your private class invite links.\n"
                "Click each button and join all the groups and channel."
            ),
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

        print(
            f"All invite links sent to {telegram_id}"
        )

    except Exception as e:
        print(
            "Telegram send error:",
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
            "Authorization": f"Bearer {FLW_SECRET_KEY}",
            "Content-Type": "application/json",
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
            and result.get("status") == "success"
        ):
            return result.get(
                "data",
                {},
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
    methods=["POST"],
)
def flutterwave_webhook():
    incoming_hash = request.headers.get("verif-hash")

    if not FLUTTERWAVE_SECRET_HASH:
        return jsonify({
            "status": "error",
            "message": "Webhook secret hash missing",
        }), 500

    if not incoming_hash:
        return jsonify({
            "status": "error",
            "message": "Missing verification hash",
        }), 401

    if not hmac.compare_digest(
        incoming_hash,
        FLUTTERWAVE_SECRET_HASH,
    ):
        return jsonify({
            "status": "error",
            "message": "Invalid verification hash",
        }), 401

    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "status": "error",
        }), 400

    payment_data = data.get("data", {})

    transaction_id = payment_data.get("id")
    tx_ref = payment_data.get("tx_ref")
    status = payment_data.get("status")

    if status != "successful":
        return jsonify({
            "status": "ignored",
        }), 200

    if not transaction_id:
        return jsonify({
            "status": "error",
        }), 400

    verified = verify_flutterwave_transaction(
        transaction_id
    )

    if not verified:
        return jsonify({
            "status": "error",
            "message": "Verification failed",
        }), 400

    verified_status = verified.get("status")
    verified_tx_ref = verified.get("tx_ref")
    verified_amount = verified.get("amount")
    verified_currency = verified.get("currency")

    if verified_status != "successful":
        return jsonify({
            "status": "ignored",
        }), 200

    if verified_currency != "NGN":
        return jsonify({
            "status": "error",
            "message": "Invalid currency",
        }), 400

    if verified_tx_ref != tx_ref:
        return jsonify({
            "status": "error",
            "message": "Transaction reference mismatch",
        }), 400

    if tx_ref.startswith("ALHIKAM_"):
        payment_token = tx_ref.replace(
            "ALHIKAM_",
            "",
            1,
        )
    else:
        return jsonify({
            "status": "error",
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
            "status": "error",
        }), 404

    if payment_token in processed_payments:
        return jsonify({
            "status": "already_processed",
        }), 200

    if int(float(verified_amount)) != int(
        payment["amount"]
    ):
        return jsonify({
            "status": "error",
            "message": "Amount mismatch",
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
        "status": "success",
    }), 200


# ============================================================
# WEB SERVER
# ============================================================

def run_web_server():
    print("Starting Flask Web Server...")

    web_app.run(
        host="0.0.0.0",
        port=PORT,
        use_reloader=False,
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
        "❌ Registration cancelled.",
        reply_markup=ReplyKeyboardMarkup(
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
    step = context.user_data.get("step")

    # ========================================================
    # BOT REGISTRATION
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
            "telegram_id": update.effective_user.id,
            "username": update.effective_user.username or "",
            "full_name": context.user_data.get(
                "full_name",
                "",
            ),
            "phone": context.user_data.get(
                "phone",
                "",
            ),
            "email": context.user_data.get(
                "email",
                "",
            ),
            "course": context.user_data.get(
                "course",
                "",
            ),
        }

        save_registration_to_google_sheets(data)

        full_name = data["full_name"]
        context.user_data.clear()

        await update.message.reply_text(
            "✅ *REGISTRATION COMPLETED*\n\n"
            f"👤 Name: {full_name}\n\n"
            "🎓 Thank you for registering with "
            "ALHIKAM Learning Center.",
            parse_mode="Markdown",
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
            parse_mode="Markdown",
        )
        return

    # ========================================================
    # COURSES
    # ========================================================

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

    # ========================================================
    # CBT
    # ========================================================

    if text == "📝 CBT Practice":
        await update.message.reply_text(
            "📝 *CBT PRACTICE*\n\n"
            "JAMB • WAEC • NECO\n\n"
            "🚧 This feature is under development.",
            parse_mode="Markdown",
        )
        return

    # ========================================================
    # PAYMENT
    # ========================================================

    if text == "💳 Pay School Fees":
        await update.message.reply_text(
            "💳 *ALHIKAM SCHOOL FEES PAYMENT*\n\n"
            "Click below to open the payment page.\n\n"
            "After successful payment, you will connect "
            "your Telegram account and complete registration.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "💳 OPEN PAYMENT PAGE",
                        url=PUBLIC_PAYMENT_PAGE,
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
            parse_mode="Markdown",
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
            parse_mode="Markdown",
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
        raise ValueError("BOT_TOKEN is missing.")

    if not FLW_SECRET_KEY:
        raise ValueError("FLW_SECRET_KEY is missing.")

    if not FLUTTERWAVE_SECRET_HASH:
        raise ValueError(
            "FLUTTERWAVE_SECRET_HASH is missing."
        )

    # Start Flask
    web_thread = threading.Thread(
        target=run_web_server,
        daemon=True,
    )
    web_thread.start()

    # Telegram bot
    telegram_bot_app = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )

    telegram_bot_app.add_handler(
        CommandHandler("start", start)
    )

    telegram_bot_app.add_handler(
        CommandHandler("cancel", cancel)
    )

    telegram_bot_app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            menu_handler,
        )
    )

    print("================================")
    print("ALHIKAM Learning Center Bot Running")
    print("Payment Page:", PUBLIC_PAYMENT_PAGE)
    print(
        "Flutterwave Webhook:",
        f"{RAILWAY_URL}/webhook/flutterwave",
    )
    print(
        "Telegram Login Domain:",
        RAILWAY_URL,
    )
    print("Registration Flow: ENABLED")
    print("Google Sheets: ENABLED")
    print("Unique Telegram Invite: ENABLED")
    print("Automatic Telegram ID: ENABLED")
    print("Main Group ID:", MAIN_GROUP_ID)
    print("================================")

    telegram_bot_app.run_polling(
        drop_pending_updates=True,
        close_loop=False,
    )


if __name__ == "__main__":
    main()

  