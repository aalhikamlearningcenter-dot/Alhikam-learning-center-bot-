# ============================================================
# ALHIKAM LEARNING CENTER V2
# Flutterwave Payment + Secure Verification
# Telegram Login + Student Registration
# Google Sheets + Unique Telegram Invite
# Referral / Commission + Withdrawal
# Admin Referral Dashboard + Telegram Bot
# ============================================================

import os
import uuid
import hmac
import hashlib
import asyncio
import threading
import requests
import logging
import secrets
import time
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from html import escape

from flask import (
    Flask, request, jsonify, render_template_string,
    redirect, url_for, session
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

from database import (
    initialize_database,
    get_promoter_by_id,
    get_promoter_by_referral_code,
    save_payment,
    get_payment_by_tx_ref,
    update_payment_status,
    mark_payment_registration_completed,
    payment_registration_completed,
    commission_exists,
    create_commission,
    add_student,
    create_or_get_student,
    get_student_by_tx_ref,
    get_withdrawal_by_transfer_id,
    get_withdrawal_by_transfer_reference,
    process_transfer_result,
)

from transfer import (
    get_flutterwave_transfer_status,
    get_flutterwave_transfer_status_by_reference,
)

from referral_dashboard import (
    promoter_login_page,
    promoter_logout as promoter_logout_page,
    referral_dashboard_by_code,
    withdrawal_page,
    withdrawal_status_page,
)

try:
    from admin_referral import (
        admin_referral_page,
        admin_login_page,
        admin_logout_page,
        create_promoter_page,
        admin_withdrawal_status_page,
    )
    ADMIN_MODULE_AVAILABLE = True
except Exception:
    ADMIN_MODULE_AVAILABLE = False


# ============================================================
# INITIALIZATION
# ============================================================

initialize_database()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("alhikam")

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
FLW_SECRET_KEY = os.getenv("FLW_SECRET_KEY", "").strip()
FLUTTERWAVE_SECRET_HASH = os.getenv("FLUTTERWAVE_SECRET_HASH", "").strip()

SHEET_URL = os.getenv(
    "SHEET_URL",
    "https://script.google.com/macros/s/AKfycbw6LRBGCzMIHcWGEIKXAYXo9bMHxsO_am4a4iSZ4kR58FFA-bj4TcUNy085uTaVRx2z0A/exec",
).strip()

RAILWAY_URL = os.getenv(
    "RAILWAY_URL",
    "https://precious-trust-production-956b.up.railway.app",
).rstrip("/")

PORT = int(os.getenv("PORT", "8080"))

MAIN_GROUP_ID = -1004384506380
PUBLIC_PAYMENT_PAGE = f"{RAILWAY_URL}/pay"
TELEGRAM_BOT_USERNAME = "Alhikamcenterbot"

PLANS = {
    1: {"months": 1, "name": "1 Month", "amount": 3600},
    2: {"months": 2, "name": "2 Months", "amount": 6800},
    3: {"months": 3, "name": "3 Months", "amount": 10000},
    4: {"months": 4, "name": "4 Months", "amount": 13600},
    5: {"months": 5, "name": "5 Months", "amount": 16500},
    6: {"months": 6, "name": "6 Months", "amount": 20000},
}

COMMISSION_AMOUNTS = {
    3600: 200,
    6800: 500,
    10000: 800,
    13600: 1200,
    16500: 1800,
    20000: 2500,
}

pending_payments = {}
processed_payments = set()
telegram_bot_app = None


# ============================================================
# FLASK
# ============================================================

app = Flask(__name__)
app.secret_key = os.getenv(
    "FLASK_SECRET_KEY",
    secrets.token_hex(32),
)

if len(app.secret_key) < 32:
    app.secret_key = secrets.token_hex(32)

app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)


# ============================================================
# HELPERS
# ============================================================

def utc_now():
    return datetime.now(timezone.utc)


def money_equal(a, b):
    try:
        return Decimal(str(a)).quantize(Decimal("0.01")) == Decimal(
            str(b)
        ).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError, TypeError):
        return False


def normalize_status(value):
    value = str(value or "").strip().lower()
    if value in {
        "success",
        "successful",
        "completed",
        "complete",
        "paid",
    }:
        return "successful"
    if value in {"failed", "cancelled", "canceled", "error"}:
        return "failed"
    if value in {"pending", "processing", "initiated"}:
        return "pending"
    return value


def get_payment_amount(payment):
    try:
        return float(
            payment.get("amount")
            or payment.get("amount_paid")
            or 0
        )
    except (ValueError, TypeError):
        return 0.0


def get_payment_tx_ref(payment):
    return (
        payment.get("tx_ref")
        or payment.get("transaction_ref")
        or ""
    ).strip()


def get_payment_status(payment):
    return normalize_status(
        payment.get("status")
        or payment.get("payment_status")
        or ""
    )


def payment_is_successful(payment):
    return get_payment_status(payment) == "successful"


def _payment_from_token(payment_token):
    tx_ref = f"ALHIKAM_{payment_token}"

    try:
        data = get_payment_by_tx_ref(tx_ref)
    except Exception as exc:
        logger.exception("Database payment lookup failed: %s", exc)
        data = None

    if data:
        data = dict(data)

        # IMPORTANT:
        # Some database versions use status while older versions
        # use payment_status. Accept both.
        raw_status = data.get("status") or data.get("payment_status") or ""
        data["status"] = normalize_status(raw_status)

        data["payment_status"] = (
            "Successful"
            if data["status"] == "successful"
            else "Failed"
            if data["status"] == "failed"
            else "Pending"
        )

        data["amount"] = get_payment_amount(data)
        data["registration_completed"] = int(
            data.get("registration_completed") or 0
        )

        if data.get("telegram_id"):
            data["telegram_auth"] = {
                "id": data.get("telegram_id"),
                "username": data.get("telegram_username")
                or data.get("username"),
                "first_name": data.get("telegram_first_name")
                or data.get("first_name"),
                "last_name": data.get("telegram_last_name")
                or data.get("last_name"),
            }

        return data

    return pending_payments.get(payment_token)


def save_payment_compat(payment):
    """
    Save using both status fields so this main.py remains compatible
    with database.py versions that use either field.
    """
    payment = dict(payment)
    normalized = normalize_status(
        payment.get("status")
        or payment.get("payment_status")
        or "pending"
    )

    payment["status"] = normalized
    payment["payment_status"] = (
        "Successful"
        if normalized == "successful"
        else "Failed"
        if normalized == "failed"
        else "Pending"
    )

    try:
        save_payment(payment)
    except TypeError:
        # Compatibility fallback for database functions that accept
        # named fields differently.
        logger.exception("save_payment() rejected payment dictionary")
        raise

    token = payment.get("payment_token")
    if token:
        pending_payments[token] = payment

    return payment


# ============================================================
# FLUTTERWAVE
# ============================================================

def verify_flutterwave_transaction(transaction_id):
    """
    Verify a transaction directly with Flutterwave.
    Never trust the browser redirect alone.
    """
    if not FLW_SECRET_KEY or not transaction_id:
        logger.error("Missing FLW_SECRET_KEY or transaction_id")
        return None

    url = (
        "https://api.flutterwave.com/v3/transactions/"
        f"{transaction_id}/verify"
    )

    headers = {
        "Authorization": f"Bearer {FLW_SECRET_KEY}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=30,
        )
        logger.info(
            "Flutterwave verify transaction=%s HTTP=%s",
            transaction_id,
            response.status_code,
        )

        result = response.json()

        if (
            response.status_code == 200
            and result.get("status") == "success"
            and isinstance(result.get("data"), dict)
        ):
            return result["data"]

        logger.warning("Flutterwave verification response: %s", result)
        return None

    except Exception as exc:
        logger.exception(
            "Flutterwave transaction verification failed: %s",
            exc,
        )
        return None


def find_flutterwave_transaction_by_tx_ref(tx_ref):
    """
    Fallback lookup when Flutterwave redirect does not contain
    transaction_id yet.
    """
    if not FLW_SECRET_KEY or not tx_ref:
        return None

    url = "https://api.flutterwave.com/v3/transactions"

    headers = {
        "Authorization": f"Bearer {FLW_SECRET_KEY}",
        "Content-Type": "application/json",
    }

    params = {
        "from": (utc_now() - timedelta(days=30)).strftime("%Y-%m-%d"),
        "to": utc_now().strftime("%Y-%m-%d"),
        "page": 1,
        "tx_ref": tx_ref,
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=30,
        )

        if response.status_code != 200:
            logger.warning(
                "Flutterwave transaction search HTTP=%s",
                response.status_code,
            )
            return None

        result = response.json()
        data = result.get("data") or []

        if not isinstance(data, list):
            return None

        for transaction in data:
            if str(transaction.get("tx_ref", "")).strip() == tx_ref:
                if str(transaction.get("currency", "")).upper() == "NGN":
                    return transaction

        return None

    except Exception as exc:
        logger.exception(
            "Flutterwave tx_ref search failed: %s",
            exc,
        )
        return None


def _verify_and_finalize_payment(payment_token, transaction_id=None):
    """
    Securely verifies and finalizes a payment.

    Required checks:
    - Flutterwave API verification
    - successful status
    - exact tx_ref
    - NGN
    - exact amount
    - ALHIKAM_ prefix
    - promoter validity
    - commission only once
    """
    payment = _payment_from_token(payment_token)

    if not payment:
        return None, "payment_not_found"

    if payment_is_successful(payment):
        return payment, "already_successful"

    expected_tx_ref = f"ALHIKAM_{payment_token}"

    if not transaction_id:
        found = find_flutterwave_transaction_by_tx_ref(expected_tx_ref)

        if not found:
            return payment, "transaction_not_found"

        transaction_id = (
            found.get("id")
            or found.get("transaction_id")
        )

    verified = verify_flutterwave_transaction(transaction_id)

    if not verified:
        return payment, "verification_failed"

    verified_status = normalize_status(
        verified.get("status")
    )

    verified_tx_ref = str(
        verified.get("tx_ref") or ""
    ).strip()

    verified_currency = str(
        verified.get("currency") or ""
    ).upper().strip()

    verified_amount = verified.get("amount")

    if verified_status != "successful":
        return payment, "transaction_not_successful"

    if verified_tx_ref != expected_tx_ref:
        logger.warning(
            "TX_REF mismatch expected=%s actual=%s",
            expected_tx_ref,
            verified_tx_ref,
        )
        return payment, "tx_ref_mismatch"

    if verified_currency != "NGN":
        return payment, "currency_mismatch"

    expected_amount = get_payment_amount(payment)

    if not money_equal(verified_amount, expected_amount):
        logger.warning(
            "Amount mismatch expected=%s actual=%s",
            expected_amount,
            verified_amount,
        )
        return payment, "amount_mismatch"

    if not verified_tx_ref.startswith("ALHIKAM_"):
        return payment, "invalid_tx_ref"

    # --------------------------------------------------------
    # PROMOTER / REFERRAL VALIDATION
    # --------------------------------------------------------
    promoter_id = payment.get("promoter_id")
    referral_code = payment.get("referral_code")

    promoter = None

    try:
        if promoter_id:
            promoter = get_promoter_by_id(promoter_id)
        elif referral_code:
            promoter = get_promoter_by_referral_code(
                referral_code
            )
    except Exception as exc:
        logger.warning(
            "Promoter lookup failed: %s",
            exc,
        )

    if promoter_id or referral_code:
        if not promoter:
            return payment, "invalid_promoter"

        active = promoter.get("active", promoter.get("is_active", 1))
        if str(active).lower() in {"0", "false", "inactive"}:
            return payment, "inactive_promoter"

    # --------------------------------------------------------
    # SAVE SUCCESSFUL PAYMENT
    # --------------------------------------------------------
    try:
        update_payment_status(
            verified_tx_ref,
            "successful",
            transaction_id=transaction_id,
        )
    except TypeError:
        # Compatibility with older database.py
        update_payment_status(
            verified_tx_ref,
            "successful",
        )

    payment["status"] = "successful"
    payment["payment_status"] = "Successful"
    payment["transaction_id"] = transaction_id
    payment["flutterwave_transaction_id"] = transaction_id
    payment["verified_amount"] = verified_amount
    payment["currency"] = "NGN"
    payment["verified_at"] = utc_now().isoformat()

    try:
        save_payment(payment)
    except Exception as exc:
        logger.exception(
            "Could not save verified payment: %s",
            exc,
        )
        # The Flutterwave verification itself succeeded. Keep the
        # in-memory record so the user can continue during this
        # request while the database error is visible in logs.

    pending_payments[payment_token] = payment

    # --------------------------------------------------------
    # COMMISSION - ONLY ONCE
    # --------------------------------------------------------
    commission_amount = COMMISSION_AMOUNTS.get(
        int(round(expected_amount))
    )

    if promoter and commission_amount:
        try:
            promoter_identifier = (
                promoter.get("id")
                or promoter.get("promoter_id")
                or promoter_id
            )

            if not commission_exists(transaction_id):
                create_commission(
                    promoter_id=promoter_identifier,
                    tx_ref=verified_tx_ref,
                    amount=commission_amount,
                    rate=commission_amount,
                )
        except TypeError:
            # Some existing database.py versions use a positional
            # signature. Do not break the payment if commission
            # storage has a different compatible signature.
            try:
                if not commission_exists(transaction_id):
                    create_commission(
                        promoter_identifier,
                        verified_tx_ref,
                        commission_amount,
                    )
            except Exception:
                logger.exception(
                    "Commission creation failed"
                )
        except Exception:
            logger.exception(
                "Commission creation failed"
            )

    return _payment_from_token(payment_token), "successful"


# ============================================================
# TELEGRAM LOGIN SECURITY
# ============================================================

def verify_telegram_login(data):
    """
    Validate Telegram Login Widget data using BOT_TOKEN.
    """
    if not BOT_TOKEN:
        return False

    received_hash = str(data.get("hash") or "").strip()

    if not received_hash:
        return False

    auth_date = data.get("auth_date")

    try:
        auth_timestamp = int(auth_date)
    except (ValueError, TypeError):
        return False

    now = int(time.time())

    if abs(now - auth_timestamp) > 3600:
        return False

    fields = []

    for key in sorted(data.keys()):
        if key in {"hash", "payment_token"}:
            continue

        value = data.get(key)

        if value is None:
            continue

        fields.append(f"{key}={value}")

    data_check_string = "\n".join(fields)

    secret_key = hashlib.sha256(
        BOT_TOKEN.encode("utf-8")
    ).digest()

    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(
        calculated_hash,
        received_hash,
    )


# ============================================================
# TELEGRAM INVITE
# ============================================================

async def create_unique_invite_link(payment_token):
    if not telegram_bot_app:
        raise RuntimeError(
            "Telegram bot application is not initialized"
        )

    invite = await telegram_bot_app.bot.create_chat_invite_link(
        chat_id=MAIN_GROUP_ID,
        member_limit=1,
        name=f"ALHIKAM-{payment_token[:10]}",
    )

    return invite.invite_link


async def send_access_message(
    telegram_id,
    full_name,
    invite_link,
):
    text = (
        f"🎓 *Welcome to Alhikam Learning Center, "
        f"{escape(full_name)}!*\n\n"
        "Your registration has been completed successfully. "
        "Your private class access is ready.\n\n"
        "👇 Click the button below to join the class."
    )

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🎓 JOIN ALHIKAM CLASS",
                    url=invite_link,
                )
            ]
        ]
    )

    await telegram_bot_app.bot.send_message(
        chat_id=telegram_id,
        text=text,
        reply_markup=keyboard,
        parse_mode="Markdown",
    )


def send_registration_access(
    telegram_id,
    full_name,
    invite_link,
):
    try:
        asyncio.run(
            send_access_message(
                telegram_id,
                full_name,
                invite_link,
            )
        )
    except Exception as exc:
        logger.exception(
            "Failed to send Telegram access message: %s",
            exc,
        )


# ============================================================
# PAGES
# ============================================================

HOME_HTML = """
<!doctype html>
<html>
<head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Alhikam Learning Center</title>
<style>
body{font-family:Arial,sans-serif;background:#f5f7fb;margin:0;padding:25px}
.box{max-width:650px;margin:30px auto;background:white;padding:30px;border-radius:18px;box-shadow:0 5px 25px #0001}
.btn{display:block;text-decoration:none;text-align:center;padding:15px;margin:12px 0;background:#146c43;color:white;border-radius:10px;font-weight:bold}
</style>
</head>
<body>
<div class="box">
<h1>🎓 Alhikam Learning Center</h1>
<p>JAMB Online Tutorial • WAEC • NECO • CBT Training</p>
<a class="btn" href="{{ payment_page }}">💳 Pay for Classes</a>
<a class="btn" href="https://t.me/Alhikamcenterbot">🤖 Open Telegram Bot</a>
</div>
</body>
</html>
"""


PAYMENT_PAGE_HTML = """
<!doctype html>
<html>
<head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Alhikam Payment</title>
<style>
body{font-family:Arial,sans-serif;background:#f4f7f9;padding:20px}
.box{max-width:650px;margin:auto;background:white;padding:25px;border-radius:18px;box-shadow:0 4px 20px #0001}
.plan{border:1px solid #ddd;border-radius:12px;padding:15px;margin:10px 0}
button{width:100%;padding:15px;border:0;border-radius:10px;background:#146c43;color:white;font-size:16px;font-weight:bold}
select,input{width:100%;box-sizing:border-box;padding:13px;margin:8px 0 18px;border:1px solid #ccc;border-radius:9px}
</style>
</head>
<body>
<div class="box">
<h1>💳 Alhikam Learning Center</h1>
<p>Select your class duration and continue to secure payment.</p>

<form method="post" action="{{ url_for('create_payment') }}">
<label>Class Plan</label>
<select name="plan" required>
{% for key, plan in plans.items() %}
<option value="{{ key }}">
{{ plan.name }} — ₦{{ "{:,.0f}".format(plan.amount) }}
</option>
{% endfor %}
</select>

<label>Full Name</label>
<input name="customer_name" required>

<label>Email</label>
<input name="customer_email" type="email" required>

<button type="submit">💳 Continue to Flutterwave</button>
</form>
</div>
</body>
</html>
"""


PAYMENT_WAITING_HTML = """
<!doctype html>
<html>
<head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Payment Verification</title>
<style>
body{font-family:Arial,sans-serif;background:#f4f7f9;padding:20px}
.box{max-width:600px;margin:70px auto;background:white;padding:30px;text-align:center;border-radius:18px;box-shadow:0 4px 20px #0001}
.spinner{font-size:45px}
</style>
</head>
<body>
<div class="box">
<div class="spinner">⏳</div>
<h2>Payment Verification</h2>
<p id="message">
Your payment is being verified securely with Flutterwave.
</p>
<p>Please wait a moment.</p>
<p id="attempt">Checking payment status...</p>
</div>

<script>
const token = "{{ payment_token }}";
let checks = 0;

async function checkPayment() {
    checks++;
    document.getElementById("attempt").textContent =
        "Checking payment status... (" + checks + ")";

    try {
        const response = await fetch(
            "/payment-status/" + encodeURIComponent(token),
            {
                cache: "no-store",
                headers: {"Accept": "application/json"}
            }
        );

        const data = await response.json();

        if (data.status === "successful") {
            document.getElementById("message").textContent =
                "✅ Payment confirmed. Opening registration...";
            window.location.href = data.redirect;
            return;
        }

        if (data.status === "failed") {
            document.getElementById("message").textContent =
                "❌ Payment was not successful.";
            document.getElementById("attempt").innerHTML =
                '<a href="/pay">Try again</a>';
            return;
        }

        setTimeout(checkPayment, 3000);
    } catch (error) {
        setTimeout(checkPayment, 4000);
    }
}

checkPayment();
</script>
</body>
</html>
"""


TELEGRAM_LOGIN_HTML = """
<!doctype html>
<html>
<head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Telegram Login</title>
<style>
body{font-family:Arial,sans-serif;background:#f4f7f9;padding:20px}
.box{max-width:600px;margin:60px auto;background:white;padding:30px;text-align:center;border-radius:18px;box-shadow:0 4px 20px #0001}
</style>
</head>
<body>
<div class="box">
<h2>🔐 Telegram Login</h2>
<p>Payment confirmed.</p>
<p>Login with Telegram to continue to your student registration form.</p>

<div id="telegram-login"></div>

<script async
src="https://telegram.org/js/telegram-widget.js?22"
data-telegram-login="{{ bot_username }}"
data-size="large"
data-userpic="false"
data-request-access="write">
</script>

<script>
function onTelegramAuth(user) {
    user.payment_token = "{{ payment_token }}";

    const form = document.createElement("form");
    form.method = "POST";
    form.action = "{{ auth_url }}";

    for (const key in user) {
        const input = document.createElement("input");
        input.type = "hidden";
        input.name = key;
        input.value = user[key];
        form.appendChild(input);
    }

    document.body.appendChild(form);
    form.submit();
}
</script>

<p style="margin-top:20px">
After Telegram login, you will complete your registration first.
Your class Join button will only be sent after registration is completed.
</p>
</div>
</body>
</html>
"""


REGISTRATION_FORM_HTML = """
<!doctype html>
<html>
<head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Student Registration</title>
<style>
body{font-family:Arial,sans-serif;background:#f4f7f9;padding:20px}
.box{max-width:650px;margin:auto;background:white;padding:25px;border-radius:18px;box-shadow:0 4px 20px #0001}
input,select{width:100%;box-sizing:border-box;padding:13px;margin:7px 0 16px;border:1px solid #ccc;border-radius:9px}
button{width:100%;padding:15px;border:0;border-radius:10px;background:#146c43;color:white;font-weight:bold;font-size:16px}
.info{background:#eef8f1;padding:15px;border-radius:10px;margin-bottom:20px}
</style>
</head>
<body>
<div class="box">
<h2>📝 Student Registration</h2>

<div class="info">
<strong>Payment confirmed.</strong><br>
Complete your student registration below.<br>
<strong>Your Telegram class Join link will be sent only after this registration is completed.</strong>
</div>

<form method="post">
<input type="hidden" name="csrf_token" value="{{ csrf_token }}">

<label>Full Name</label>
<input name="full_name" required value="{{ auth.get('first_name','') }} {{ auth.get('last_name','') }}">

<label>Phone Number</label>
<input name="phone" required>

<label>Email</label>
<input name="email" type="email" required>

<label>Course</label>
<select name="course" required>
<option value="">Select Course</option>
<option>JAMB Science</option>
<option>JAMB Arts</option>
<option>WAEC</option>
<option>NECO</option>
<option>CBT Training</option>
</select>

<button type="submit">✅ Complete Registration</button>
</form>
</div>
</body>
</html>
"""


# ============================================================
# BASIC ROUTES
# ============================================================

@app.route("/")
def home():
    return render_template_string(
        HOME_HTML,
        payment_page=PUBLIC_PAYMENT_PAGE,
    )


@app.route("/health")
def health():
    return jsonify(
        {
            "status": "ok",
            "service": "Alhikam Learning Center V2",
            "time": utc_now().isoformat(),
        }
    )


@app.route("/pay")
def payment_page():
    return render_template_string(
        PAYMENT_PAGE_HTML,
        plans=PLANS,
    )


# ============================================================
# CREATE PAYMENT
# ============================================================

@app.route("/create-payment", methods=["POST"])
def create_payment():
    plan_key = request.form.get("plan", "").strip()
    customer_name = request.form.get("customer_name", "").strip()
    customer_email = request.form.get("customer_email", "").strip()

    try:
        plan = PLANS[int(plan_key)]
    except (ValueError, KeyError):
        return "Invalid plan", 400

    if not customer_name or not customer_email:
        return "Name and email are required", 400

    payment_token = uuid.uuid4().hex
    tx_ref = f"ALHIKAM_{payment_token}"

    payment = {
        "payment_token": payment_token,
        "tx_ref": tx_ref,
        "plan_name": plan["name"],
        "payment_plan": plan["name"],
        "amount": plan["amount"],
        "amount_paid": plan["amount"],
        "currency": "NGN",
        "customer_name": customer_name,
        "customer_email": customer_email,
        "status": "pending",
        "payment_status": "Pending",
        "registration_completed": 0,
        "created_at": utc_now().isoformat(),
    }

    pending_payments[payment_token] = payment

    try:
        save_payment(payment)
    except Exception as exc:
        logger.exception(
            "Could not save initial payment: %s",
            exc,
        )
        return "Unable to create payment record", 500

    if not FLW_SECRET_KEY:
        return "Flutterwave secret key is not configured", 500

    payload = {
        "tx_ref": tx_ref,
        "amount": plan["amount"],
        "currency": "NGN",
        "redirect_url": (
            f"{RAILWAY_URL}/payment-complete/"
            f"{payment_token}"
        ),
        "customer": {
            "email": customer_email,
            "name": customer_name,
        },
        "customizations": {
            "title": "ALHIKAM Learning Center",
            "description": f"{plan['name']} JAMB Online Tutorial",
        },
        "configurations": {
            "session_duration": 30,
            "max_retry_attempt": 3,
        },
    }

    try:
        response = requests.post(
            "https://api.flutterwave.com/v3/payments",
            headers={
                "Authorization": f"Bearer {FLW_SECRET_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=30,
        )

        result = response.json()

        if (
            response.status_code not in (200, 201)
            or result.get("status") != "success"
        ):
            logger.error(
                "Flutterwave payment creation failed: %s",
                result,
            )
            return "Flutterwave could not create the payment", 502

        link = (
            result.get("data", {}).get("link")
            or result.get("data", {}).get("payment_link")
        )

        if not link:
            return "Flutterwave payment link was not returned", 502

        return redirect(link)

    except Exception as exc:
        logger.exception(
            "Payment creation error: %s",
            exc,
        )
        return "Payment service error", 502


# ============================================================
# PAYMENT COMPLETE / VERIFICATION
# ============================================================

@app.route("/payment-complete/<payment_token>")
def payment_complete(payment_token):
    payment = _payment_from_token(payment_token)

    if not payment:
        return "Payment record not found", 404

    query_transaction_id = (
        request.args.get("transaction_id")
        or request.args.get("id")
    )

    query_status = normalize_status(
        request.args.get("status")
    )

    query_tx_ref = (
        request.args.get("tx_ref")
        or ""
    ).strip()

    expected_tx_ref = f"ALHIKAM_{payment_token}"

    if query_tx_ref and query_tx_ref != expected_tx_ref:
        return "Invalid transaction reference", 400

    # Direct transaction ID from Flutterwave redirect is preferred.
    if not payment_is_successful(payment):
        for attempt in range(3):
            verified_payment, result = (
                _verify_and_finalize_payment(
                    payment_token,
                    query_transaction_id,
                )
            )

            if verified_payment:
                payment = verified_payment

            if payment and payment_is_successful(payment):
                break

            if attempt < 2:
                time.sleep(2)

    if payment and payment_is_successful(payment):
        return redirect(
            url_for(
                "register_student",
                payment_token=payment_token,
            )
        )

    if query_status == "failed":
        return """
        <div style="font-family:Arial;text-align:center;padding:40px">
        <h2>❌ Payment Failed</h2>
        <p>Your payment was not completed successfully.</p>
        <a href="/pay">Try Again</a>
        </div>
        """, 400

    # Do not keep the user trapped on this page.
    # JavaScript polls /payment-status and redirects automatically.
    return render_template_string(
        PAYMENT_WAITING_HTML,
        payment_token=payment_token,
    )


@app.route("/payment-status/<payment_token>")
def payment_status(payment_token):
    """
    Browser polling endpoint.
    It attempts verification again when Flutterwave has not yet
    returned the transaction to the application.
    """
    payment = _payment_from_token(payment_token)

    if not payment:
        return jsonify(
            {"status": "not_found"}
        ), 404

    if payment_is_successful(payment):
        return jsonify(
            {
                "status": "successful",
                "redirect": url_for(
                    "register_student",
                    payment_token=payment_token,
                ),
            }
        )

    transaction_id = (
        request.args.get("transaction_id")
        or request.args.get("id")
    )

    verified_payment, result = (
        _verify_and_finalize_payment(
            payment_token,
            transaction_id,
        )
    )

    if verified_payment:
        payment = verified_payment

    if payment and payment_is_successful(payment):
        return jsonify(
            {
                "status": "successful",
                "redirect": url_for(
                    "register_student",
                    payment_token=payment_token,
                ),
            }
        )

    if result in {
        "verification_failed",
        "transaction_not_successful",
        "tx_ref_mismatch",
        "currency_mismatch",
        "amount_mismatch",
        "invalid_tx_ref",
        "invalid_promoter",
        "inactive_promoter",
    }:
        # Keep as pending for transient verification failures,
        # except for explicit failed transaction.
        if result == "transaction_not_successful":
            return jsonify({"status": "failed"})

    return jsonify(
        {
            "status": "pending",
            "message": "Payment is still being verified.",
        }
    )


# ============================================================
# TELEGRAM LOGIN
# ============================================================

@app.route("/register/<payment_token>")
def register_student(payment_token):
    payment = _payment_from_token(payment_token)

    if not payment:
        return "Payment record not found", 404

    if not payment_is_successful(payment):
        return redirect(
            url_for(
                "payment_complete",
                payment_token=payment_token,
            )
        )

    if int(payment.get("registration_completed") or 0) == 1:
        return """
        <div style="font-family:Arial;text-align:center;padding:40px">
        <h2>✅ Registration Already Completed</h2>
        <p>Your class access has already been processed.</p>
        </div>
        """

    telegram_auth = payment.get("telegram_auth")

    if telegram_auth:
        return redirect(
            url_for(
                "registration_form",
                payment_token=payment_token,
            )
        )

    return render_template_string(
        TELEGRAM_LOGIN_HTML,
        bot_username=TELEGRAM_BOT_USERNAME,
        payment_token=payment_token,
        auth_url=url_for(
            "telegram_auth",
            _external=True,
        ),
    )


@app.route("/telegram-auth", methods=["POST", "GET"])
def telegram_auth():
    data = request.form.to_dict() or request.args.to_dict()

    payment_token = (
        data.get("payment_token")
        or request.args.get("payment_token")
        or request.form.get("payment_token")
    )

    if not payment_token:
        return "Payment token missing", 400

    payment = _payment_from_token(payment_token)

    if not payment or not payment_is_successful(payment):
        return "Payment has not been verified", 403

    telegram_data = dict(data)
    telegram_data.pop("payment_token", None)

    if not verify_telegram_login(telegram_data):
        return "Invalid Telegram login", 403

    telegram_id = telegram_data.get("id")

    if not telegram_id:
        return "Telegram ID missing", 400

    payment["telegram_id"] = int(telegram_id)
    payment["telegram_username"] = telegram_data.get("username", "")
    payment["telegram_first_name"] = telegram_data.get(
        "first_name",
        "",
    )
    payment["telegram_last_name"] = telegram_data.get(
        "last_name",
        "",
    )
    payment["telegram_auth"] = telegram_data

    save_payment_compat(payment)

    return redirect(
        url_for(
            "registration_form",
            payment_token=payment_token,
        )
    )


# ============================================================
# STUDENT REGISTRATION
# ============================================================

@app.route(
    "/registration-form/<payment_token>",
    methods=["GET", "POST"],
)
def registration_form(payment_token):
    payment = _payment_from_token(payment_token)

    if not payment:
        return "Payment record not found", 404

    if not payment_is_successful(payment):
        return "Payment has not been verified", 403

    if int(payment.get("registration_completed") or 0) == 1:
        return """
        <div style="font-family:Arial;text-align:center;padding:40px">
        <h2>✅ Registration Completed</h2>
        <p>Your registration has already been completed.</p>
        <p>Please check your Telegram for your class access.</p>
        </div>
        """

    telegram_auth = payment.get("telegram_auth")

    if not telegram_auth:
        return redirect(
            url_for(
                "register_student",
                payment_token=payment_token,
            )
        )

    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)

    if request.method == "GET":
        return render_template_string(
            REGISTRATION_FORM_HTML,
            csrf_token=session["csrf_token"],
            auth=telegram_auth,
        )

    # --------------------------------------------------------
    # CSRF
    # --------------------------------------------------------
    if request.form.get("csrf_token") != session.get("csrf_token"):
        return "Invalid form request", 403

    full_name = request.form.get("full_name", "").strip()
    phone = request.form.get("phone", "").strip()
    email = request.form.get("email", "").strip()
    course = request.form.get("course", "").strip()

    if not full_name or not phone or not email or not course:
        return "All registration fields are required", 400

    telegram_id = int(
        payment.get("telegram_id")
        or telegram_auth.get("id")
    )

    username = (
        payment.get("telegram_username")
        or telegram_auth.get("username")
        or ""
    )

    registration_data = {
        "telegram_id": telegram_id,
        "telegram_username": username,
        "full_name": full_name,
        "phone": phone,
        "email": email,
        "course": course,
        "payment_plan": (
            payment.get("payment_plan")
            or payment.get("plan_name")
        ),
        "amount_paid": get_payment_amount(payment),
        "tx_ref": get_payment_tx_ref(payment),
    }

    # ========================================================
    # IMPORTANT ORDER:
    # 1. Registration data is saved first.
    # 2. Registration is marked completed.
    # 3. ONLY THEN is the private Telegram invite created.
    # 4. ONLY THEN is the Join button sent.
    # ========================================================

    # --------------------------------------------------------
    # DATABASE STUDENT REGISTRATION
    # --------------------------------------------------------
    try:
        student = create_or_get_student(
            telegram_id=telegram_id,
            tx_ref=registration_data["tx_ref"],
            full_name=full_name,
            phone=phone,
            email=email,
            course=course,
            username=username,
        )
    except TypeError:
        try:
            student = create_or_get_student(
                telegram_id,
                registration_data["tx_ref"],
                full_name,
                phone,
                email,
                course,
                username,
            )
        except Exception:
            logger.exception(
                "Student registration failed"
            )
            return "Unable to save registration", 500
    except Exception:
        logger.exception(
            "Student registration failed"
        )
        return "Unable to save registration", 500

    # --------------------------------------------------------
    # GOOGLE SHEETS
    # --------------------------------------------------------
    try:
        save_registration_to_google_sheets(
            registration_data
        )
    except Exception:
        logger.exception(
            "Google Sheets registration save failed"
        )
        return (
            "Registration could not be completed because "
            "the registration sheet could not be updated. "
            "Please try again.",
            500,
        )

    # --------------------------------------------------------
    # MARK REGISTRATION COMPLETED BEFORE ACCESS
    # --------------------------------------------------------
    try:
        mark_payment_registration_completed(
            registration_data["tx_ref"]
        )
    except TypeError:
        try:
            mark_payment_registration_completed(
                payment_token
            )
        except Exception:
            logger.exception(
                "Could not mark registration completed"
            )
            return "Registration status could not be updated", 500
    except Exception:
        logger.exception(
            "Could not mark registration completed"
        )
        return "Registration status could not be updated", 500

    payment["registration_completed"] = 1
    payment["status"] = "successful"
    payment["payment_status"] = "Successful"

    try:
        save_payment(payment)
    except Exception:
        logger.exception(
            "Could not save final registration payment state"
        )

    # --------------------------------------------------------
    # NOW CREATE UNIQUE TELEGRAM INVITE
    # --------------------------------------------------------
    try:
        invite_link = asyncio.run(
            create_unique_invite_link(
                payment_token
            )
        )
    except Exception:
        logger.exception(
            "Registration completed but Telegram invite "
            "creation failed"
        )

        return """
        <div style="font-family:Arial;text-align:center;padding:40px">
        <h2>✅ Registration Completed</h2>
        <p>Your student registration has been saved successfully.</p>
        <p>Your Telegram class access is being prepared.</p>
        <p>Please contact Alhikam Learning Center if the Join button
        does not arrive in your Telegram.</p>
        </div>
        """

    # --------------------------------------------------------
    # SEND JOIN BUTTON ONLY AFTER REGISTRATION
    # --------------------------------------------------------
    threading.Thread(
        target=send_registration_access,
        args=(
            telegram_id,
            full_name,
            invite_link,
        ),
        daemon=True,
    ).start()

    session.pop("csrf_token", None)

    return """
    <div style="font-family:Arial;text-align:center;padding:40px">
    <h2>🎉 Registration Completed Successfully!</h2>
    <p>Your student registration has been saved.</p>
    <p>✅ Your private Telegram class Join button has been sent to your Telegram account.</p>
    <p>Please open Telegram and click <strong>JOIN ALHIKAM CLASS</strong>.</p>
    </div>
    """


# ============================================================
# GOOGLE SHEETS
# ============================================================

def save_registration_to_google_sheets(data):
    if not SHEET_URL:
        raise RuntimeError("SHEET_URL is not configured")

    response = requests.post(
        SHEET_URL,
        json=data,
        timeout=30,
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"Google Sheets HTTP {response.status_code}"
        )

    return True


# ============================================================
# FLUTTERWAVE WEBHOOK
# ============================================================

@app.route("/webhook/flutterwave", methods=["POST"])
def flutterwave_webhook():
    if FLUTTERWAVE_SECRET_HASH:
        received_hash = (
            request.headers.get("verif-hash")
            or request.headers.get("Verif-Hash")
            or ""
        )

        if not hmac.compare_digest(
            received_hash,
            FLUTTERWAVE_SECRET_HASH,
        ):
            return "Invalid webhook signature", 401

    payload = request.get_json(
        silent=True
    ) or {}

    data = payload.get("data") or {}

    transaction_id = (
        data.get("id")
        or data.get("transaction_id")
    )

    tx_ref = str(
        data.get("tx_ref") or ""
    ).strip()

    if not transaction_id or not tx_ref:
        return jsonify(
            {"status": "ignored"}
        )

    if not tx_ref.startswith("ALHIKAM_"):
        return jsonify(
            {"status": "ignored"}
        )

    payment_token = tx_ref[len("ALHIKAM_"):]

    payment = _payment_from_token(payment_token)

    if not payment:
        return jsonify(
            {"status": "accepted"}
        )

    verified_payment, result = (
        _verify_and_finalize_payment(
            payment_token,
            transaction_id,
        )
    )

    if verified_payment and payment_is_successful(
        verified_payment
    ):
        return jsonify(
            {"status": "success"}
        )

    return jsonify(
        {
            "status": "accepted",
            "verification": result,
        }
    )


# ============================================================
# TRANSFER CALLBACK
# ============================================================

@app.route(
    "/flutterwave/transfer-callback",
    methods=["POST", "GET"],
)
def flutterwave_transfer_callback():
    payload = request.get_json(
        silent=True
    ) or {}

    data = payload.get("data") or payload

    transfer_id = (
        data.get("id")
        or data.get("transfer_id")
        or request.args.get("id")
    )

    reference = (
        data.get("reference")
        or data.get("tx_ref")
        or request.args.get("reference")
    )

    if not transfer_id and not reference:
        return jsonify(
            {"status": "ignored"}
        )

    withdrawal = None

    try:
        if transfer_id:
            withdrawal = get_withdrawal_by_transfer_id(
                transfer_id
            )

        if not withdrawal and reference:
            withdrawal = get_withdrawal_by_transfer_reference(
                reference
            )
    except Exception:
        logger.exception(
            "Withdrawal lookup failed"
        )

    if not withdrawal:
        return jsonify(
            {"status": "withdrawal_not_found"}
        ), 404

    try:
        withdrawal_reference = (
            withdrawal.get("transfer_reference")
            or withdrawal.get("reference")
        )

        if (
            reference
            and withdrawal_reference
            and str(reference) != str(withdrawal_reference)
        ):
            return jsonify(
                {"status": "reference_mismatch"}
            ), 400
    except Exception:
        pass

    status = None

    try:
        if transfer_id:
            status = get_flutterwave_transfer_status(
                transfer_id
            )
        elif reference:
            status = get_flutterwave_transfer_status_by_reference(
                reference
            )
    except Exception:
        logger.exception(
            "Flutterwave transfer status lookup failed"
        )

    if status is None:
        return jsonify(
            {"status": "pending"}
        )

    try:
        process_transfer_result(
            withdrawal,
            status,
        )
    except TypeError:
        try:
            process_transfer_result(
                withdrawal.get("id"),
                status,
            )
        except Exception:
            logger.exception(
                "Could not process transfer result"
            )
    except Exception:
        logger.exception(
            "Could not process transfer result"
        )

    return jsonify(
        {
            "status": "processed",
            "transfer_status": status,
        }
    )


# ============================================================
# REFERRAL DASHBOARD
# ============================================================

@app.route(
    "/referral/login",
    methods=["GET", "POST"],
)
def referral_login():
    return promoter_login_page()


@app.route("/referral/logout")
def referral_logout():
    return promoter_logout_page()


@app.route("/referral/dashboard")
def referral_dashboard():
    return referral_dashboard_by_code()


@app.route("/referral/<referral_code>")
def referral_by_code(referral_code):
    return referral_dashboard_by_code(
        referral_code
    )


@app.route("/referral-dashboard")
def referral_dashboard_alias():
    return referral_dashboard_by_code()


# ============================================================
# WITHDRAWAL
# ============================================================

@app.route(
    "/referral/withdraw",
    methods=["GET", "POST"],
)
def referral_withdraw():
    return withdrawal_page()


@app.route(
    "/referral/withdraw/status/<int:withdrawal_id>"
)
def referral_withdraw_status(withdrawal_id):
    return withdrawal_status_page(
        withdrawal_id
    )


# ============================================================
# ADMIN
# ============================================================

if ADMIN_MODULE_AVAILABLE:

    @app.route("/admin/referral")
    def admin_referral():
        return admin_referral_page()

    @app.route(
        "/admin/referral/login",
        methods=["GET", "POST"],
    )
    def admin_referral_login():
        return admin_login_page()

    @app.route("/admin/referral/logout")
    def admin_referral_logout():
        return admin_logout_page()

    @app.route(
        "/admin/referral/create-promoter",
        methods=["GET", "POST"],
    )
    def admin_create_promoter():
        return create_promoter_page()

    @app.route(
        "/admin/referral/withdrawal-status"
    )
    def admin_withdrawal_status():
        return admin_withdrawal_status_page()


# ============================================================
# TELEGRAM BOT MENUS
# ============================================================

MAIN_MENU = [
    ["📚 Courses", "📝 CBT Practice"],
    ["👤 Student Registration", "💳 Pay School Fees"],
    ["📞 Contact Us", "ℹ️ About Us"],
]

COURSE_MENU = [
    ["JAMB Science", "JAMB Arts"],
    ["WAEC", "NECO"],
    ["CBT Training"],
    ["⬅️ Back"],
]


async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    keyboard = ReplyKeyboardMarkup(
        MAIN_MENU,
        resize_keyboard=True,
    )

    await update.message.reply_text(
        "🎓 Welcome to Alhikam Learning Center!\n\n"
        "Choose an option below:",
        reply_markup=keyboard,
    )


async def cancel_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    context.user_data.clear()

    keyboard = ReplyKeyboardMarkup(
        MAIN_MENU,
        resize_keyboard=True,
    )

    await update.message.reply_text(
        "❌ Current process cancelled.",
        reply_markup=keyboard,
    )


async def menu_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not update.message:
        return

    text = (
        update.message.text
        or ""
    ).strip()

    if text == "📚 Courses":
        await update.message.reply_text(
            "📚 Select a course:",
            reply_markup=ReplyKeyboardMarkup(
                COURSE_MENU,
                resize_keyboard=True,
            ),
        )
        return

    if text in {
        "JAMB Science",
        "JAMB Arts",
        "WAEC",
        "NECO",
        "CBT Training",
    }:
        await update.message.reply_text(
            f"📚 {text}\n\n"
            "For registration, payment and class access, "
            "use the official Alhikam Learning Center payment page.",
            reply_markup=ReplyKeyboardMarkup(
                MAIN_MENU,
                resize_keyboard=True,
            ),
        )
        return

    if text == "⬅️ Back":
        await update.message.reply_text(
            "Main menu:",
            reply_markup=ReplyKeyboardMarkup(
                MAIN_MENU,
                resize_keyboard=True,
            ),
        )
        return

    if text == "📝 CBT Practice":
        await update.message.reply_text(
            "📝 CBT Practice\n\n"
            "CBT practice and examination features are "
            "available through Alhikam Learning Center.",
        )
        return

    if text == "👤 Student Registration":
        await update.message.reply_text(
            "👤 Student Registration\n\n"
            "Paid students should complete payment first. "
            "After payment verification, Telegram login and "
            "registration will be provided.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "📝 START REGISTRATION",
                            url=PUBLIC_PAYMENT_PAGE,
                        )
                    ]
                ]
            ),
        )
        return

    if text == "💳 Pay School Fees":
        await update.message.reply_text(
            "💳 Secure Payment\n\n"
            "Use the official Alhikam Learning Center "
            "payment page:",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "💳 PAY NOW",
                            url=PUBLIC_PAYMENT_PAGE,
                        )
                    ]
                ]
            ),
        )
        return

    if text == "📞 Contact Us":
        await update.message.reply_text(
            "📞 Contact Alhikam Learning Center\n\n"
            "Email: aalhikamlearningcenter@gmail.com"
        )
        return

    if text == "ℹ️ About Us":
        await update.message.reply_text(
            "ℹ️ About Alhikam Learning Center\n\n"
            "JAMB • WAEC • NECO • CBT Training\n"
            "English • Arabic • French • Science • Arts\n\n"
            "Learning for everyone."
        )
        return


# ============================================================
# FLASK SERVER THREAD
# ============================================================

def run_flask():
    app.run(
        host="0.0.0.0",
        port=PORT,
        debug=False,
        use_reloader=False,
    )


# ============================================================
# MAIN
# ============================================================

def main():
    global telegram_bot_app

    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN environment variable is missing"
        )

    flask_thread = threading.Thread(
        target=run_flask,
        daemon=True,
    )
    flask_thread.start()

    telegram_bot_app = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    telegram_bot_app.add_handler(
        CommandHandler("start", start_command)
    )

    telegram_bot_app.add_handler(
        CommandHandler("cancel", cancel_command)
    )

    telegram_bot_app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            menu_handler,
        )
    )

    logger.info(
        "Alhikam Learning Center V2 starting..."
    )

    telegram_bot_app.run_polling(
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
