# ============================================================
# ALHIKAM LEARNING CENTER V2
# main.py
#
# FLOW:
# Flutterwave Payment
# -> Server Verification
# -> Telegram Login
# -> Registration
# -> Google Sheets
# -> Unique Telegram Invite
# -> Referral Commission
#
# PAYMENT VERIFICATION FIX:
# - Uses transaction_id from Flutterwave redirect
# - Direct transaction verification
# - tx_ref verification
# - amount verification
# - currency verification
# - webhook verification
# - retry without infinite verification loop
# - detailed logging
# ============================================================

import os
import uuid
import hmac
import hashlib
import json
import asyncio
import threading
import requests
import logging

from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation

from flask import (
    Flask,
    request,
    jsonify,
    render_template_string,
    redirect,
    url_for,
    session,
)

from markupsafe import escape

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from telegram.error import TelegramError

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ============================================================
# DATABASE
# ============================================================

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

# ============================================================
# TRANSFER
# ============================================================

from transfer import (
    get_flutterwave_transfer_status,
    get_flutterwave_transfer_status_by_reference,
)

# ============================================================
# REFERRAL DASHBOARD
# ============================================================

from referral_dashboard import (
    promoter_login_page,
    promoter_logout as promoter_logout_page,
    referral_dashboard_by_code,
    withdrawal_page,
    withdrawal_status_page,
)

# ============================================================
# OPTIONAL ADMIN MODULE
# ============================================================

ADMIN_MODULE_AVAILABLE = False

try:
    from admin_referral import (
        admin_referral_page,
        admin_login_page,
        admin_logout_page,
        create_promoter_page,
        admin_withdrawal_status_page,
    )

    ADMIN_MODULE_AVAILABLE = True

except ImportError:
    pass


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

initialize_database()


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger("ALHIKAM")


# ============================================================
# ENVIRONMENT VARIABLES
# ============================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")

FLW_SECRET_KEY = os.getenv("FLW_SECRET_KEY")

FLUTTERWAVE_SECRET_HASH = os.getenv(
    "FLUTTERWAVE_SECRET_HASH"
)

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

TELEGRAM_BOT_USERNAME = "Alhikamcenterbot"


# ============================================================
# PAYMENT PLANS
# ============================================================

PAYMENT_PLANS = {
    "1": {
        "name": "1 Month",
        "amount": 3600,
        "commission": 200,
    },
    "2": {
        "name": "2 Months",
        "amount": 6800,
        "commission": 500,
    },
    "3": {
        "name": "3 Months",
        "amount": 10000,
        "commission": 800,
    },
    "4": {
        "name": "4 Months",
        "amount": 13600,
        "commission": 1200,
    },
    "5": {
        "name": "5 Months",
        "amount": 16500,
        "commission": 1800,
    },
    "6": {
        "name": "6 Months",
        "amount": 20000,
        "commission": 2500,
    },
}


# ============================================================
# MEMORY CACHE
# ============================================================

pending_payments = {}

processed_payments = set()

telegram_bot_app = None

telegram_loop = None


# ============================================================
# FLASK
# ============================================================

web_app = Flask(__name__)

SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY or len(SECRET_KEY) < 32:
    raise RuntimeError(
        "SECRET_KEY must exist and contain at least 32 characters."
    )

web_app.secret_key = SECRET_KEY

web_app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=RAILWAY_URL.startswith("https://"),
    PERMANENT_SESSION_LIFETIME=86400,
)


# ============================================================
# BASIC ROUTES
# ============================================================

@web_app.route("/")
def home():

    return jsonify({
        "status": "online",
        "service": "ALHIKAM Learning Center V2",
        "bot": f"@{TELEGRAM_BOT_USERNAME}",
        "payment_page": f"{RAILWAY_URL}/pay",
        "webhook": f"{RAILWAY_URL}/webhook/flutterwave",
        "telegram_login": f"{RAILWAY_URL}/pay",
    })


@web_app.route("/health")
def health():

    return jsonify({
        "status": "healthy",
        "service": "ALHIKAM Learning Center",
    })


# ============================================================
# HTML HELPERS
# ============================================================

def html_page(title, body):

    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport"
content="width=device-width, initial-scale=1.0">

<title>{escape(title)}</title>

<style>

body {{
    margin: 0;
    padding: 20px;
    background: #f4f7fb;
    font-family: Arial, sans-serif;
}}

.card {{
    max-width: 650px;
    margin: 40px auto;
    background: white;
    padding: 28px;
    border-radius: 16px;
    box-shadow: 0 8px 30px rgba(0,0,0,.08);
}}

h1, h2 {{
    color: #123;
}}

button, .button {{
    display: inline-block;
    border: none;
    padding: 13px 20px;
    border-radius: 10px;
    background: #087f5b;
    color: white;
    text-decoration: none;
    cursor: pointer;
    font-weight: bold;
}}

input, select {{
    width: 100%;
    padding: 12px;
    margin: 8px 0 16px;
    border: 1px solid #ccc;
    border-radius: 8px;
    box-sizing: border-box;
}}

.plan {{
    border: 1px solid #ddd;
    padding: 15px;
    border-radius: 12px;
    margin-bottom: 12px;
}}

.error {{
    color: #b00020;
    background: #ffe8ec;
    padding: 12px;
    border-radius: 8px;
}}

.success {{
    color: #075b3a;
    background: #e4fff3;
    padding: 12px;
    border-radius: 8px;
}}

.warning {{
    color: #704800;
    background: #fff4d6;
    padding: 12px;
    border-radius: 8px;
}}

.small {{
    color: #666;
    font-size: 13px;
}}

</style>
</head>

<body>

<div class="card">

{body}

</div>

</body>
</html>
"""


# ============================================================
# PAYMENT PAGE
# ============================================================

@web_app.route("/pay", methods=["GET"])
def payment_page():

    referral_code = (
        request.args.get("referral_code", "").strip()
        or request.args.get("ref", "").strip()
    )

    promoter = None

    if referral_code:

        try:
            promoter = get_promoter_by_referral_code(
                referral_code
            )
        except Exception:
            logger.exception(
                "Unable to check referral code."
            )

    plans_html = ""

    for key, plan in PAYMENT_PLANS.items():

        plans_html += f"""
        <div class="plan">

        <label>

        <input
            type="radio"
            name="plan"
            value="{key}"
            required
        >

        <strong>
        {escape(plan["name"])}
        </strong>

        — ₦{plan["amount"]:,}

        </label>

        </div>
        """

    referral_message = ""

    if referral_code:

        if promoter:

            referral_message = f"""
            <div class="success">
            Referral code accepted:
            <strong>{escape(referral_code)}</strong>
            </div>
            """

        else:

            referral_message = """
            <div class="warning">
            Referral code was not found.
            You can continue without referral.
            </div>
            """

    body = f"""

    <h1>Alhikam Learning Center</h1>

    <h2>JAMB Online Tutorial</h2>

    <p>
    Select your preferred subscription plan.
    </p>

    {referral_message}

    <form method="POST"
          action="/create-payment">

        <input
            type="hidden"
            name="referral_code"
            value="{escape(referral_code)}"
        >

        {plans_html}

        <button type="submit">
        Continue to Payment
        </button>

    </form>

    """

    return html_page(
        "Alhikam Learning Center Payment",
        body,
    )


# ============================================================
# CREATE FLUTTERWAVE PAYMENT
# ============================================================

@web_app.route("/create-payment", methods=["POST"])
def create_payment():

    if not FLW_SECRET_KEY:

        return html_page(
            "Payment Error",
            """
            <h2>Payment configuration error</h2>

            <div class="error">
            Flutterwave secret key is missing.
            </div>
            """,
        ), 500

    plan_key = request.form.get("plan", "").strip()

    referral_code = (
        request.form.get("referral_code", "").strip()
    )

    if plan_key not in PAYMENT_PLANS:

        return html_page(
            "Invalid Plan",
            """
            <h2>Invalid payment plan</h2>

            <a class="button" href="/pay">
            Go Back
            </a>
            """,
        ), 400

    plan = PAYMENT_PLANS[plan_key]

    promoter = None
    promoter_id = None

    if referral_code:

        try:

            promoter = get_promoter_by_referral_code(
                referral_code
            )

        except Exception:

            logger.exception(
                "Referral lookup failed."
            )

    if promoter:

        try:
            promoter_id = promoter["id"]
        except Exception:

            try:
                promoter_id = promoter.get("id")
            except Exception:
                promoter_id = None

    payment_token = uuid.uuid4().hex

    tx_ref = f"ALHIKAM_{payment_token}"

    payment = {
        "payment_token": payment_token,
        "tx_ref": tx_ref,
        "plan": plan_key,
        "plan_name": plan["name"],
        "payment_plan": plan["name"],
        "amount": plan["amount"],
        "currency": "NGN",
        "status": "pending",
        "payment_status": "Pending",
        "referral_code": referral_code,
        "promoter_id": promoter_id,
        "commission": 0,
        "registration_completed": 0,
        "created_at": datetime.now(
            timezone.utc
        ).isoformat(),
    }

    try:

        save_payment(payment)

    except Exception as e:

        logger.exception(
            "Could not save payment."
        )

        return html_page(
            "Payment Error",
            f"""
            <h2>Unable to create payment</h2>

            <div class="error">
            {escape(str(e))}
            </div>
            """,
        ), 500

    pending_payments[payment_token] = payment

    callback_url = (
        f"{RAILWAY_URL}/payment-complete/"
        f"{payment_token}"
    )

    payload = {

        "tx_ref": tx_ref,

        "amount": plan["amount"],

        "currency": "NGN",

        "redirect_url": callback_url,

        "payment_options": "card,banktransfer,ussd",

        "customer": {

            "email":
                f"student_{payment_token}@alhikam.com",

            "name":
                "ALHIKAM Student",

        },

        "customizations": {

            "title":
                "Alhikam Learning Center",

            "description":
                f"{plan['name']} JAMB Online Tutorial",

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
            headers=headers,
            json=payload,
            timeout=30,
        )

    except Exception as e:

        logger.exception(
            "Flutterwave payment request failed."
        )

        return html_page(
            "Payment Error",
            f"""
            <h2>Flutterwave connection failed</h2>

            <div class="error">
            {escape(str(e))}
            </div>

            <a class="button" href="/pay">
            Try Again
            </a>
            """,
        ), 502

    logger.info(
        "Flutterwave create payment response: %s",
        response.text[:2000],
    )

    try:
        result = response.json()
    except Exception:
        result = {}

    if (
        response.status_code == 200
        and result.get("status") == "success"
        and result.get("data", {}).get("link")
    ):

        return redirect(
            result["data"]["link"]
        )

    error_message = (
        result.get("message")
        or "Flutterwave could not create the payment."
    )

    return html_page(
        "Payment Error",
        f"""
        <h2>Unable to start payment</h2>

        <div class="error">
        {escape(str(error_message))}
        </div>

        <a class="button" href="/pay">
        Try Again
        </a>
        """,
    ), 502


# ============================================================
# PAYMENT LOOKUP
# ============================================================

def _payment_from_token(payment_token):

    tx_ref = f"ALHIKAM_{payment_token}"

    try:

        row = get_payment_by_tx_ref(tx_ref)

    except Exception:

        logger.exception(
            "Database payment lookup failed."
        )

        row = None

    if row:

        try:

            payment = dict(row)

        except Exception:

            payment = row

        payment["payment_token"] = payment_token

        payment["tx_ref"] = (
            payment.get("tx_ref")
            or tx_ref
        )

        payment["plan_name"] = (
            payment.get("payment_plan")
            or payment.get("plan_name")
            or ""
        )

        try:

            payment["amount"] = float(
                payment.get("amount", 0)
            )

        except Exception:

            payment["amount"] = 0

        status = str(
            payment.get("payment_status")
            or payment.get("status")
            or "pending"
        ).lower()

        if status in (
            "successful",
            "success",
            "completed",
        ):

            payment["status"] = "successful"

        elif status in (
            "failed",
            "cancelled",
            "canceled",
        ):

            payment["status"] = "failed"

        else:

            payment["status"] = "pending"

        try:

            payment["registration_completed"] = int(
                payment.get(
                    "registration_completed",
                    0,
                ) or 0
            )

        except Exception:

            payment["registration_completed"] = 0

        telegram_id = payment.get("telegram_id")

        if telegram_id:

            payment["telegram_auth"] = {

                "id": telegram_id,

                "first_name":
                    payment.get("telegram_first_name", ""),

                "last_name":
                    payment.get("telegram_last_name", ""),

                "username":
                    payment.get("telegram_username", ""),

                "photo_url":
                    payment.get("telegram_photo_url", ""),

                "auth_date":
                    payment.get("telegram_auth_date", ""),

                "hash":
                    payment.get("telegram_hash", ""),
            }

        return payment

    return pending_payments.get(
        payment_token
    )


# ============================================================
# COMMISSION
# ============================================================

def _commission_for_amount(amount):

    try:

        amount = Decimal(
            str(amount)
        )

    except Exception:

        return 0

    for plan in PAYMENT_PLANS.values():

        if Decimal(
            str(plan["amount"])
        ) == amount:

            return plan["commission"]

    return 0


# ============================================================
# FLUTTERWAVE DIRECT TRANSACTION VERIFICATION
# ============================================================

def verify_flutterwave_transaction(
    transaction_id
):

    if not FLW_SECRET_KEY:

        logger.error(
            "FLW_SECRET_KEY is missing."
        )

        return None

    if not transaction_id:

        logger.error(
            "No transaction ID supplied."
        )

        return None

    url = (
        "https://api.flutterwave.com/v3/"
        f"transactions/{transaction_id}/verify"
    )

    headers = {

        "Authorization":
            f"Bearer {FLW_SECRET_KEY}",

        "Content-Type":
            "application/json",

    }

    try:

        response = requests.get(
            url,
            headers=headers,
            timeout=30,
        )

    except Exception:

        logger.exception(
            "Flutterwave verification request failed."
        )

        return None

    logger.info(
        "Flutterwave VERIFY %s -> HTTP %s",
        transaction_id,
        response.status_code,
    )

    logger.info(
        "Flutterwave VERIFY response: %s",
        response.text[:3000],
    )

    try:

        result = response.json()

    except Exception:

        logger.error(
            "Flutterwave returned invalid JSON."
        )

        return None

    if response.status_code != 200:

        return None

    if result.get("status") != "success":

        return None

    data = result.get("data")

    if not isinstance(data, dict):

        return None

    return data


# ============================================================
# FIND TRANSACTION BY TX REF
#
# This is only a FALLBACK.
#
# Primary method is direct verification using
# transaction_id from Flutterwave redirect/webhook.
# ============================================================

def find_flutterwave_transaction_by_tx_ref(
    tx_ref
):

    if not FLW_SECRET_KEY:

        return None

    if not tx_ref:

        return None

    headers = {

        "Authorization":
            f"Bearer {FLW_SECRET_KEY}",

        "Content-Type":
            "application/json",

    }

    today = datetime.now(
        timezone.utc
    ).date()

    from_date = today - timedelta(days=30)

    for page in range(1, 11):

        params = {

            "from":
                from_date.isoformat(),

            "to":
                today.isoformat(),

            "page":
                page,

            "limit":
                100,

        }

        try:

            response = requests.get(
                "https://api.flutterwave.com/v3/transactions",
                headers=headers,
                params=params,
                timeout=30,
            )

        except Exception:

            logger.exception(
                "Transaction list request failed."
            )

            return None

        logger.info(
            "Flutterwave transaction search page=%s HTTP=%s",
            page,
            response.status_code,
        )

        if response.status_code != 200:

            return None

        try:

            result = response.json()

        except Exception:

            return None

        if result.get("status") != "success":

            return None

        data = result.get("data", [])

        if not isinstance(data, list):

            return None

        for transaction in data:

            if not isinstance(
                transaction,
                dict,
            ):

                continue

            transaction_tx_ref = str(
                transaction.get("tx_ref", "")
            ).strip()

            if hmac.compare_digest(
                transaction_tx_ref,
                tx_ref,
            ):

                logger.info(
                    "Transaction found by tx_ref: %s",
                    tx_ref,
                )

                return transaction

        if len(data) < 100:

            break

    logger.warning(
        "Transaction not found for tx_ref=%s",
        tx_ref,
    )

    return None


# ============================================================
# PAYMENT FINALIZATION
# ============================================================

def _verify_and_finalize_payment(
    payment_token,
    transaction_id=None,
):

    payment = _payment_from_token(
        payment_token
    )

    if not payment:

        logger.error(
            "Payment not found: %s",
            payment_token,
        )

        return None

    tx_ref = payment.get(
        "tx_ref"
    ) or f"ALHIKAM_{payment_token}"

    # --------------------------------------------------------
    # Already successful
    # --------------------------------------------------------

    if payment.get("status") == "successful":

        return payment

    # --------------------------------------------------------
    # Get transaction ID
    # --------------------------------------------------------

    if transaction_id:

        transaction_id = str(
            transaction_id
        ).strip()

    if not transaction_id:

        logger.info(
            "No transaction_id received. "
            "Trying tx_ref fallback."
        )

        transaction = (
            find_flutterwave_transaction_by_tx_ref(
                tx_ref
            )
        )

        if transaction:

            transaction_id = (
                transaction.get("id")
            )

    if not transaction_id:

        logger.warning(
            "No Flutterwave transaction found for %s",
            tx_ref,
        )

        return payment

    # --------------------------------------------------------
    # Direct verification
    # --------------------------------------------------------

    verified = verify_flutterwave_transaction(
        transaction_id
    )

    if not verified:

        logger.warning(
            "Transaction verification failed: %s",
            transaction_id,
        )

        return payment

    # --------------------------------------------------------
    # Transaction status
    # --------------------------------------------------------

    transaction_status = str(
        verified.get("status", "")
    ).lower().strip()

    if transaction_status != "successful":

        logger.warning(
            "Transaction is not successful. status=%s",
            transaction_status,
        )

        return payment

    # --------------------------------------------------------
    # TX REF
    # --------------------------------------------------------

    verified_tx_ref = str(
        verified.get("tx_ref", "")
    ).strip()

    if not hmac.compare_digest(
        verified_tx_ref,
        tx_ref,
    ):

        logger.error(
            "TX REF mismatch. expected=%s received=%s",
            tx_ref,
            verified_tx_ref,
        )

        return payment

    # --------------------------------------------------------
    # CURRENCY
    # --------------------------------------------------------

    currency = str(
        verified.get("currency", "")
    ).upper().strip()

    if currency != "NGN":

        logger.error(
            "Currency mismatch: %s",
            currency,
        )

        return payment

    # --------------------------------------------------------
    # AMOUNT
    # --------------------------------------------------------

    try:

        expected_amount = Decimal(
            str(payment.get("amount"))
        )

        verified_amount = Decimal(
            str(verified.get("amount"))
        )

    except (
        InvalidOperation,
        TypeError,
        ValueError,
    ):

        logger.error(
            "Invalid payment amount."
        )

        return payment

    if verified_amount != expected_amount:

        logger.error(
            "Amount mismatch. expected=%s received=%s",
            expected_amount,
            verified_amount,
        )

        return payment

    # --------------------------------------------------------
    # SECURITY PREFIX
    # --------------------------------------------------------

    if not verified_tx_ref.startswith(
        "ALHIKAM_"
    ):

        logger.error(
            "Invalid ALHIKAM tx_ref."
        )

        return payment

    # --------------------------------------------------------
    # REFERRAL VALIDATION
    # --------------------------------------------------------

    referral_code = str(
        payment.get(
            "referral_code",
            "",
        ) or ""
    ).strip()

    promoter_id = payment.get(
        "promoter_id"
    )

    promoter = None

    if promoter_id:

        try:

            promoter = get_promoter_by_id(
                promoter_id
            )

        except Exception:

            logger.exception(
                "Promoter lookup failed."
            )

    if referral_code:

        if not promoter:

            logger.error(
                "Referral promoter not found."
            )

            return payment

        try:

            promoter_active = bool(
                promoter.get(
                    "active",
                    promoter.get(
                        "is_active",
                        0,
                    ),
                )
            )

        except Exception:

            promoter_active = False

        if not promoter_active:

            logger.error(
                "Promoter is inactive."
            )

            return payment

        try:

            promoter_code = str(
                promoter.get(
                    "referral_code",
                    "",
                ) or ""
            ).strip()

        except Exception:

            promoter_code = ""

        if promoter_code != referral_code:

            logger.error(
                "Referral code mismatch."
            )

            return payment

    # --------------------------------------------------------
    # COMMISSION
    # --------------------------------------------------------

    commission_amount = (
        _commission_for_amount(
            verified_amount
        )
    )

    # --------------------------------------------------------
    # UPDATE PAYMENT
    # --------------------------------------------------------

    try:

        update_payment_status(
            tx_ref,
            "Successful",
            transaction_id=transaction_id,
        )

    except Exception:

        logger.exception(
            "Could not update payment status."
        )

    payment.update({

        "status":
            "successful",

        "payment_status":
            "Successful",

        "transaction_id":
            transaction_id,

        "verified_amount":
            float(verified_amount),

        "verified_currency":
            currency,

        "verified_tx_ref":
            verified_tx_ref,

        "commission":
            commission_amount,

        "verified_at":
            datetime.now(
                timezone.utc
            ).isoformat(),
    })

    # --------------------------------------------------------
    # SAVE PAYMENT DETAILS
    # --------------------------------------------------------

    try:

        save_payment(payment)

    except Exception:

        logger.exception(
            "Could not save finalized payment."
        )

    pending_payments[
        payment_token
    ] = payment

    # --------------------------------------------------------
    # COMMISSION
    # --------------------------------------------------------

    if (
        promoter_id
        and commission_amount > 0
    ):

        try:

            exists = commission_exists(
                tx_ref
            )

        except Exception:

            logger.exception(
                "Commission existence check failed."
            )

            exists = True

        if not exists:

            try:

                create_commission(
                    promoter_id=promoter_id,
                    tx_ref=tx_ref,
                    amount=commission_amount,
                )

                logger.info(
                    "Commission created for %s: ₦%s",
                    tx_ref,
                    commission_amount,
                )

            except TypeError:

                try:

                    create_commission(
                        promoter_id,
                        tx_ref,
                        commission_amount,
                    )

                except Exception:

                    logger.exception(
                        "Commission creation failed."
                    )

            except Exception:

                logger.exception(
                    "Commission creation failed."
                )

    logger.info(
        "PAYMENT SUCCESSFULLY VERIFIED: %s",
        tx_ref,
    )

    return _payment_from_token(
        payment_token
    )


# ============================================================
# PAYMENT COMPLETE
# ============================================================

@web_app.route(
    "/payment-complete/<payment_token>",
    methods=["GET"],
)
def payment_complete(payment_token):

    payment = _payment_from_token(
        payment_token
    )

    if not payment:

        return html_page(
            "Payment Not Found",
            """
            <h2>Payment not found</h2>

            <div class="error">
            We could not find this payment.
            Please contact Alhikam Learning Center.
            </div>
            """,
        ), 404

    # --------------------------------------------------------
    # Flutterwave redirect values
    # --------------------------------------------------------

    transaction_id = (
        request.args.get("transaction_id")
        or request.args.get("transactionId")
        or request.args.get("id")
        or ""
    ).strip()

    returned_status = (
        request.args.get("status", "")
        .strip()
        .lower()
    )

    returned_tx_ref = (
        request.args.get("tx_ref", "")
        .strip()
    )

    expected_tx_ref = payment.get(
        "tx_ref"
    ) or f"ALHIKAM_{payment_token}"

    logger.info(
        "PAYMENT CALLBACK token=%s transaction_id=%s status=%s tx_ref=%s",
        payment_token,
        transaction_id,
        returned_status,
        returned_tx_ref,
    )

    # --------------------------------------------------------
    # Prevent tx_ref tampering
    # --------------------------------------------------------

    if (
        returned_tx_ref
        and returned_tx_ref != expected_tx_ref
    ):

        logger.error(
            "Callback TX REF mismatch."
        )

        return html_page(
            "Payment Error",
            """
            <h2>Payment verification error</h2>

            <div class="error">
            The payment reference does not match
            this payment session.
            </div>
            """,
        ), 400

    # --------------------------------------------------------
    # If already successful
    # --------------------------------------------------------

    if payment.get("status") == "successful":

        return redirect(
            url_for(
                "registration_page",
                payment_token=payment_token,
            )
        )

    # --------------------------------------------------------
    # Explicit failed/cancelled
    # --------------------------------------------------------

    if returned_status in (
        "cancelled",
        "canceled",
        "failed",
    ):

        try:

            update_payment_status(
                expected_tx_ref,
                "Failed",
            )

        except Exception:

            logger.exception(
                "Could not mark payment failed."
            )

        return html_page(
            "Payment Failed",
            """
            <h2>Payment was not completed</h2>

            <div class="error">
            Your Flutterwave payment was cancelled
            or failed.
            </div>

            <br>

            <a class="button" href="/pay">
            Try Payment Again
            </a>
            """,
        )

    # --------------------------------------------------------
    # VERIFY NOW
    # --------------------------------------------------------

    verified_payment = (
        _verify_and_finalize_payment(
            payment_token,
            transaction_id=transaction_id,
        )
    )

    if (
        verified_payment
        and verified_payment.get("status")
        == "successful"
    ):

        return redirect(
            url_for(
                "registration_page",
                payment_token=payment_token,
            )
        )

    # --------------------------------------------------------
    # PAYMENT STILL NOT VERIFIED
    #
    # IMPORTANT:
    # Do NOT redirect/reload the same page forever.
    # Give the user a manual retry.
    # --------------------------------------------------------

    retry_url = (
        f"/payment-complete/"
        f"{payment_token}?retry=1"
    )

    status_url = (
        f"/payment-status/"
        f"{payment_token}"
    )

    body = f"""

    <h2>⏳ Payment Verification</h2>

    <div class="warning">

    Your payment has been received by the
    payment page, but Flutterwave has not yet
    returned a confirmed successful transaction.

    </div>

    <p>
    We are checking your payment securely.
    </p>

    <p class="small">
    Payment Reference:
    <strong>{escape(expected_tx_ref)}</strong>
    </p>

    <p class="small">
    Transaction ID:
    <strong>
    {escape(transaction_id or "Not received yet")}
    </strong>
    </p>

    <br>

    <a class="button" href="{escape(retry_url)}">
    🔄 Check Payment Again
    </a>

    <br><br>

    <a href="{escape(status_url)}">
    View Payment Status
    </a>

    <p class="small">
    Do not make another payment unless you have
    confirmed that the first payment failed.
    </p>

    """

    return html_page(
        "Payment Verification",
        body,
    )


# ============================================================
# PAYMENT STATUS API
# ============================================================

@web_app.route(
    "/payment-status/<payment_token>",
    methods=["GET"],
)
def payment_status(payment_token):

    payment = _payment_from_token(
        payment_token
    )

    if not payment:

        return jsonify({
            "success": False,
            "message": "Payment not found.",
        }), 404

    # Try one verification when status is pending.

    if payment.get("status") != "successful":

        transaction_id = (
            payment.get("transaction_id")
            or request.args.get(
                "transaction_id",
                "",
            )
            or request.args.get(
                "id",
                "",
            )
        )

        payment = (
            _verify_and_finalize_payment(
                payment_token,
                transaction_id=transaction_id,
            )
            or payment
        )

    if payment.get("status") == "successful":

        return jsonify({

            "success": True,

            "status":
                "successful",

            "tx_ref":
                payment.get("tx_ref"),

            "transaction_id":
                payment.get(
                    "transaction_id"
                ),

            "next":
                f"/register/{payment_token}",
        })

    return jsonify({

        "success": False,

        "status":
            payment.get(
                "status",
                "pending",
            ),

        "tx_ref":
            payment.get("tx_ref"),

        "transaction_id":
            payment.get(
                "transaction_id"
            ),

        "message":
            "Payment has not been verified yet.",
    })


# ============================================================
# TELEGRAM LOGIN VERIFICATION
# ============================================================

def verify_telegram_login(data):

    if not BOT_TOKEN:

        return False

    try:

        received_hash = str(
            data.get("hash", "")
        ).strip()

        auth_date = int(
            data.get("auth_date")
        )

        telegram_id = str(
            data.get("id")
        )

    except Exception:

        return False

    if not received_hash:

        return False

    if not telegram_id:

        return False

    now = int(
        datetime.now(
            timezone.utc
        ).timestamp()
    )

    if now - auth_date > 3600:

        logger.warning(
            "Telegram login expired."
        )

        return False

    if auth_date > now + 60:

        return False

    check_items = []

    for key in sorted(data.keys()):

        if key == "hash":

            continue

        value = data.get(key)

        if value is None:

            continue

        check_items.append(
            f"{key}={value}"
        )

    data_check_string = "\n".join(
        check_items
    )

    secret_key = hashlib.sha256(
        BOT_TOKEN.encode()
    ).digest()

    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(
        calculated_hash,
        received_hash,
    )


# ============================================================
# TELEGRAM AUTH
# ============================================================

@web_app.route(
    "/telegram-auth",
    methods=["POST"],
)
def telegram_auth():

    data = request.get_json(
        silent=True
    ) or {}

    payment_token = str(
        data.get(
            "payment_token",
            "",
        )
    ).strip()

    if not payment_token:

        return jsonify({
            "success": False,
            "message": "Payment token missing.",
        }), 400

    payment = _payment_from_token(
        payment_token
    )

    if not payment:

        return jsonify({
            "success": False,
            "message": "Payment not found.",
        }), 404

    # --------------------------------------------------------
    # Verify payment again
    # --------------------------------------------------------

    if payment.get("status") != "successful":

        transaction_id = (
            data.get("transaction_id")
            or payment.get("transaction_id")
        )

        payment = (
            _verify_and_finalize_payment(
                payment_token,
                transaction_id=transaction_id,
            )
            or payment
        )

    if payment.get("status") != "successful":

        return jsonify({
            "success": False,
            "message":
                "Payment has not been successfully verified.",
        }), 400

    telegram_data = {

        "id":
            data.get("id"),

        "first_name":
            data.get("first_name", ""),

        "last_name":
            data.get("last_name", ""),

        "username":
            data.get("username", ""),

        "photo_url":
            data.get("photo_url", ""),

        "auth_date":
            data.get("auth_date"),

        "hash":
            data.get("hash"),
    }

    if not verify_telegram_login(
        telegram_data
    ):

        logger.warning(
            "Invalid Telegram login for payment %s",
            payment_token,
        )

        return jsonify({
            "success": False,
            "message":
                "Telegram login verification failed.",
        }), 403

    # --------------------------------------------------------
    # Save Telegram details
    # --------------------------------------------------------

    payment["telegram_auth"] = telegram_data

    payment["telegram_id"] = telegram_data["id"]

    payment["telegram_first_name"] = (
        telegram_data["first_name"]
    )

    payment["telegram_last_name"] = (
        telegram_data["last_name"]
    )

    payment["telegram_username"] = (
        telegram_data["username"]
    )

    payment["telegram_photo_url"] = (
        telegram_data["photo_url"]
    )

    payment["telegram_auth_date"] = (
        telegram_data["auth_date"]
    )

    payment["telegram_hash"] = (
        telegram_data["hash"]
    )

    try:

        save_payment(payment)

    except Exception:

        logger.exception(
            "Could not save Telegram payment data."
        )

    pending_payments[
        payment_token
    ] = payment

    return jsonify({

        "success": True,

        "message":
            "Telegram account verified.",

        "redirect":
            f"/register/{payment_token}",
    })


# ============================================================
# REGISTRATION PAGE
# ============================================================

@web_app.route(
    "/register/<payment_token>",
    methods=["GET", "POST"],
)
def registration_page(payment_token):

    payment = _payment_from_token(
        payment_token
    )

    if not payment:

        return html_page(
            "Registration Error",
            """
            <h2>Payment not found</h2>
            """,
        ), 404

    # --------------------------------------------------------
    # Verify payment
    # --------------------------------------------------------

    if payment.get("status") != "successful":

        payment = (
            _verify_and_finalize_payment(
                payment_token,
                payment.get(
                    "transaction_id"
                ),
            )
            or payment
        )

    if payment.get("status") != "successful":

        return html_page(
            "Payment Not Verified",
            """
            <h2>Payment not verified</h2>

            <div class="error">
            Please verify your payment before
            registration.
            </div>
            """,
        ), 400

    # --------------------------------------------------------
    # Telegram login required
    # --------------------------------------------------------

    telegram_auth = (
        payment.get("telegram_auth")
    )

    if not telegram_auth:

        telegram_login_html = f"""

        <h2>Telegram Login Required</h2>

        <p>
        Please login with Telegram to continue
        your Alhikam registration.
        </p>

        <script async
        src="https://telegram.org/js/telegram-widget.js?22"
        data-telegram-login="{escape(TELEGRAM_BOT_USERNAME)}"
        data-size="large"
        data-request-access="write"
        data-userpic="false"
        data-onauth="onTelegramAuth(user)">
        </script>

        <script>

        async function onTelegramAuth(user) {{

            const payload = {{

                payment_token:
                    "{escape(payment_token)}",

                id:
                    user.id,

                first_name:
                    user.first_name || "",

                last_name:
                    user.last_name || "",

                username:
                    user.username || "",

                photo_url:
                    user.photo_url || "",

                auth_date:
                    user.auth_date,

                hash:
                    user.hash

            }};

            const response = await fetch(
                "/telegram-auth",
                {{

                    method: "POST",

                    headers: {{
                        "Content-Type":
                            "application/json"
                    }},

                    body:
                        JSON.stringify(payload)

                }}
            );

            const result =
                await response.json();

            if (result.success) {{

                window.location.href =
                    result.redirect;

            }} else {{

                alert(
                    result.message ||
                    "Telegram verification failed."
                );

            }}

        }}

        </script>

        """

        return html_page(
            "Telegram Login",
            telegram_login_html,
        )

    # --------------------------------------------------------
    # Already completed
    # --------------------------------------------------------

    if (
        payment.get(
            "registration_completed"
        )
        == 1
    ):

        return html_page(
            "Registration Completed",
            """
            <h2>✅ Registration Already Completed</h2>

            <div class="success">
            Your registration has already been completed.
            Please check your Telegram for your class
            access.
            </div>

            <br>

            <a class="button"
               href="https://t.me/Alhikamcenterbot">
            Open Alhikam Bot
            </a>
            """,
        )

    # --------------------------------------------------------
    # CSRF
    # --------------------------------------------------------

    csrf_token = session.get(
        f"csrf_{payment_token}"
    )

    if not csrf_token:

        csrf_token = uuid.uuid4().hex

        session[
            f"csrf_{payment_token}"
        ] = csrf_token

        session.permanent = True

    # --------------------------------------------------------
    # POST
    # --------------------------------------------------------

    if request.method == "POST":

        submitted_csrf = (
            request.form.get(
                "csrf_token",
                "",
            )
        )

        if not hmac.compare_digest(
            str(submitted_csrf),
            str(csrf_token),
        ):

            return html_page(
                "Security Error",
                """
                <h2>Security verification failed</h2>

                <a class="button"
                   href="javascript:history.back()">
                Go Back
                </a>
                """,
            ), 403

        full_name = (
            request.form.get(
                "full_name",
                "",
            ).strip()
        )

        phone = (
            request.form.get(
                "phone",
                "",
            ).strip()
        )

        email = (
            request.form.get(
                "email",
                "",
            ).strip()
        )

        course = (
            request.form.get(
                "course",
                "",
            ).strip()
        )

        if not full_name:

            return html_page(
                "Registration Error",
                """
                <h2>Full name is required.</h2>
                """,
            ), 400

        if not phone:

            return html_page(
                "Registration Error",
                """
                <h2>Phone number is required.</h2>
                """,
            ), 400

        if not email:

            return html_page(
                "Registration Error",
                """
                <h2>Email is required.</h2>
                """,
            ), 400

        if not course:

            return html_page(
                "Registration Error",
                """
                <h2>Please select your course.</h2>
                """,
            ), 400

        registration_data = {

            "full_name":
                full_name,

            "phone":
                phone,

            "email":
                email,

            "course":
                course,

            "payment_token":
                payment_token,

            "tx_ref":
                payment.get("tx_ref"),

            "amount":
                payment.get("amount"),

            "payment_plan":
                payment.get("plan_name"),

            "telegram_id":
                telegram_auth.get("id"),

            "telegram_username":
                telegram_auth.get("username"),

            "referral_code":
                payment.get("referral_code", ""),

            "registered_at":
                datetime.now(
                    timezone.utc
                ).isoformat(),
        }

        # ----------------------------------------------------
        # Google Sheets
        # ----------------------------------------------------

        try:

            sheet_saved = (
                save_registration_to_google_sheets(
                    registration_data
                )
            )

        except Exception:

            logger.exception(
                "Google Sheets registration failed."
            )

            sheet_saved = False

        if not sheet_saved:

            return html_page(
                "Registration Error",
                """
                <h2>Registration could not be saved</h2>

                <div class="error">
                We could not save your registration.
                Please try again.
                </div>

                <br>

                <a class="button"
                   href="javascript:history.back()">
                Try Again
                </a>
                """,
            ), 502

        # ----------------------------------------------------
        # Telegram invite
        # ----------------------------------------------------

        invite_link = (
            create_unique_invite_link(
                payment_token
            )
        )

        if not invite_link:

            return html_page(
                "Registration Saved",
                """
                <h2>Registration Saved</h2>

                <div class="warning">
                Your registration was saved, but the
                Telegram class invite could not be
                created yet.

                Please contact Alhikam Learning Center
                support.
                </div>
                """,
            ), 503

        # ----------------------------------------------------
        # Create student
        # ----------------------------------------------------

        student_data = {

            "full_name":
                full_name,

            "phone":
                phone,

            "email":
                email,

            "course":
                course,

            "payment_token":
                payment_token,

            "tx_ref":
                payment.get("tx_ref"),

            "telegram_id":
                telegram_auth.get("id"),

            "telegram_username":
                telegram_auth.get("username"),

            "amount":
                payment.get("amount"),

            "payment_plan":
                payment.get("plan_name"),

            "referral_code":
                payment.get("referral_code", ""),

            "invite_link":
                invite_link,
        }

        try:

            result = create_or_get_student(
                student_data
            )

        except TypeError:

            try:

                result = create_or_get_student(
                    payment_token,
                    student_data,
                )

            except Exception:

                logger.exception(
                    "Student creation failed."
                )

                result = None

        except Exception:

            logger.exception(
                "Student creation failed."
            )

            result = None

        # ----------------------------------------------------
        # Mark registration complete
        # ----------------------------------------------------

        try:

            mark_payment_registration_completed(
                payment.get("tx_ref")
            )

        except TypeError:

            try:

                mark_payment_registration_completed(
                    payment_token
                )

            except Exception:

                logger.exception(
                    "Could not mark registration complete."
                )

        except Exception:

            logger.exception(
                "Could not mark registration complete."
            )

        payment[
            "registration_completed"
        ] = 1

        payment[
            "invite_link"
        ] = invite_link

        try:

            save_payment(payment)

        except Exception:

            logger.exception(
                "Could not save registration state."
            )

        pending_payments[
            payment_token
        ] = payment

        # ----------------------------------------------------
        # Send access
        # ----------------------------------------------------

        threading.Thread(
            target=send_registration_access,
            args=(
                telegram_auth.get("id"),
                full_name,
                invite_link,
            ),
            daemon=True,
        ).start()

        return html_page(
            "Registration Successful",
            f"""

            <h2>🎉 Registration Successful!</h2>

            <div class="success">

            Welcome to Alhikam Learning Center,
            <strong>{escape(full_name)}</strong>.

            </div>

            <p>
            Your Telegram class access has been prepared.
            </p>

            <p>
            Check your Telegram messages from
            <strong>@{escape(TELEGRAM_BOT_USERNAME)}</strong>.
            </p>

            <br>

            <a class="button"
               href="{escape(invite_link)}">
            🚀 Join Your Class
            </a>

            """,
        )

    # --------------------------------------------------------
    # GET FORM
    # --------------------------------------------------------

    body = f"""

    <h2>Student Registration</h2>

    <p>
    Payment verified successfully.
    Please complete your registration.
    </p>

    <form method="POST">

        <input
            type="hidden"
            name="csrf_token"
            value="{escape(csrf_token)}"
        >

        <label>
        Full Name
        </label>

        <input
            type="text"
            name="full_name"
            placeholder="Enter your full name"
            required
        >

        <label>
        Phone Number
        </label>

        <input
            type="tel"
            name="phone"
            placeholder="08012345678"
            required
        >

        <label>
        Email Address
        </label>

        <input
            type="email"
            name="email"
            placeholder="you@example.com"
            required
        >

        <label>
        Course
        </label>

        <select name="course" required>

            <option value="">
            Select Course
            </option>

            <option>
            JAMB Online Tutorial
            </option>

            <option>
            WAEC
            </option>

            <option>
            NECO
            </option>

            <option>
            Arabic
            </option>

            <option>
            English Language
            </option>

            <option>
            French Language
            </option>

            <option>
            Science
            </option>

            <option>
            Arts
            </option>

        </select>

        <button type="submit">
        Complete Registration
        </button>

    </form>

    """

    return html_page(
        "Student Registration",
        body,
    )


# ============================================================
# GOOGLE SHEETS
# ============================================================

def save_registration_to_google_sheets(
    registration_data
):

    if not SHEET_URL:

        logger.error(
            "SHEET_URL is missing."
        )

        return False

    try:

        response = requests.post(
            SHEET_URL,
            json=registration_data,
            timeout=30,
        )

    except Exception:

        logger.exception(
            "Google Sheets request failed."
        )

        return False

    logger.info(
        "Google Sheets response HTTP=%s body=%s",
        response.status_code,
        response.text[:1000],
    )

    return response.status_code == 200


# ============================================================
# TELEGRAM LOOP
# ============================================================

def run_telegram_coroutine(
    coroutine,
    timeout=40,
):

    global telegram_loop

    if (
        telegram_loop
        and telegram_loop.is_running()
    ):

        try:

            future = (
                asyncio.run_coroutine_threadsafe(
                    coroutine,
                    telegram_loop,
                )
            )

            return future.result(
                timeout=timeout
            )

        except Exception:

            logger.exception(
                "Telegram coroutine failed."
            )

            return None

    try:

        return asyncio.run(
            coroutine
        )

    except Exception:

        logger.exception(
            "Fallback Telegram coroutine failed."
        )

        return None


# ============================================================
# UNIQUE TELEGRAM INVITE
# ============================================================

def create_unique_invite_link(
    payment_token
):

    if not telegram_bot_app:

        logger.error(
            "Telegram application not available."
        )

        return None

    async def create_link():

        try:

            invite = (
                await telegram_bot_app.bot
                .create_chat_invite_link(

                    chat_id=MAIN_GROUP_ID,

                    member_limit=1,

                    name=
                        f"ALHIKAM-{payment_token[:10]}",
                )
            )

            return invite.invite_link

        except TelegramError:

            logger.exception(
                "Telegram could not create invite link."
            )

            return None

        except Exception:

            logger.exception(
                "Unexpected Telegram invite error."
            )

            return None

    return run_telegram_coroutine(
        create_link()
    )


# ============================================================
# SEND REGISTRATION ACCESS
# ============================================================

def send_registration_access(
    telegram_id,
    full_name,
    invite_link,
):

    async def send_access():

        try:

            await telegram_bot_app.bot.send_message(

                chat_id=telegram_id,

                text=(
                    f"🎉 Welcome {full_name}!\n\n"
                    "Your Alhikam Learning Center "
                    "registration is complete.\n\n"
                    "Click the button below to join "
                    "your class."
                ),

                reply_markup=InlineKeyboardMarkup([

                    [

                        InlineKeyboardButton(
                            "🚀 Join Your Class",
                            url=invite_link,
                        )

                    ]

                ]),
            )

            return True

        except TelegramError:

            logger.exception(
                "Telegram message failed."
            )

            return False

        except Exception:

            logger.exception(
                "Unexpected Telegram message error."
            )

            return False

    run_telegram_coroutine(
        send_access()
    )


# ============================================================
# FLUTTERWAVE WEBHOOK
# ============================================================

@web_app.route(
    "/webhook/flutterwave",
    methods=["POST"],
)
def flutterwave_webhook():

    # --------------------------------------------------------
    # Verify secret hash
    # --------------------------------------------------------

    if not FLUTTERWAVE_SECRET_HASH:

        logger.error(
            "FLUTTERWAVE_SECRET_HASH missing."
        )

        return jsonify({
            "success": False,
            "message": "Webhook not configured.",
        }), 500

    incoming_hash = (
        request.headers.get(
            "verif-hash",
            ""
        ).strip()
    )

    if not incoming_hash:

        incoming_hash = (
            request.headers.get(
                "Verif-Hash",
                ""
            ).strip()
        )

    if not hmac.compare_digest(
        incoming_hash,
        FLUTTERWAVE_SECRET_HASH,
    ):

        logger.warning(
            "Invalid Flutterwave webhook hash."
        )

        return jsonify({
            "success": False,
            "message": "Invalid signature.",
        }), 401

    payload = (
        request.get_json(
            silent=True
        )
        or {}
    )

    logger.info(
        "Flutterwave webhook received: %s",
        json.dumps(
            payload,
            default=str,
        )[:3000],
    )

    data = payload.get(
        "data",
        payload,
    )

    if not isinstance(data, dict):

        return jsonify({
            "success": True,
        })

    transaction_id = data.get(
        "id"
    )

    tx_ref = str(
        data.get(
            "tx_ref",
            ""
        )
    ).strip()

    if not tx_ref.startswith(
        "ALHIKAM_"
    ):

        logger.warning(
            "Webhook ignored: invalid tx_ref."
        )

        return jsonify({
            "success": True,
        })

    payment = get_payment_by_tx_ref(
        tx_ref
    )

    if not payment:

        logger.warning(
            "Webhook payment not found: %s",
            tx_ref,
        )

        return jsonify({
            "success": True,
        })

    payment_token = (
        tx_ref.replace(
            "ALHIKAM_",
            "",
            1,
        )
    )

    verified = (
        _verify_and_finalize_payment(
            payment_token,
            transaction_id=transaction_id,
        )
    )

    if (
        verified
        and verified.get("status")
        == "successful"
    ):

        logger.info(
            "Webhook successfully finalized %s",
            tx_ref,
        )

    else:

        logger.warning(
            "Webhook could not finalize %s",
            tx_ref,
        )

    return jsonify({
        "success": True,
    }), 200


# ============================================================
# FLUTTERWAVE TRANSFER CALLBACK
# ============================================================

@web_app.route(
    "/flutterwave/transfer-callback",
    methods=["GET", "POST"],
)
def flutterwave_transfer_callback():

    try:

        payload = (
            request.get_json(
                silent=True
            )
            or {}
        )

        data = payload.get(
            "data",
            payload,
        )

        transfer_id = (
            data.get("id")
            or request.args.get("id")
            or request.args.get("transfer_id")
        )

        transfer_reference = (
            data.get("reference")
            or request.args.get("reference")
            or request.args.get("transfer_reference")
        )

        withdrawal = None

        if transfer_id:

            try:

                withdrawal = (
                    get_withdrawal_by_transfer_id(
                        transfer_id
                    )
                )

            except Exception:

                logger.exception(
                    "Transfer ID lookup failed."
                )

        if (
            not withdrawal
            and transfer_reference
        ):

            try:

                withdrawal = (
                    get_withdrawal_by_transfer_reference(
                        transfer_reference
                    )
                )

            except Exception:

                logger.exception(
                    "Transfer reference lookup failed."
                )

        if not withdrawal:

            return jsonify({
                "success": True,
                "message":
                    "Transfer received.",
            }), 200

        status_data = None

        if transfer_id:

            status_data = (
                get_flutterwave_transfer_status(
                    transfer_id
                )
            )

        if (
            not status_data
            and transfer_reference
        ):

            status_data = (
                get_flutterwave_transfer_status_by_reference(
                    transfer_reference
                )
            )

        if status_data:

            try:

                process_transfer_result(
                    withdrawal,
                    status_data,
                )

            except TypeError:

                try:

                    process_transfer_result(
                        withdrawal.get("id"),
                        status_data,
                    )

                except Exception:

                    logger.exception(
                        "Could not process transfer result."
                    )

            except Exception:

                logger.exception(
                    "Could not process transfer result."
                )

        return jsonify({
            "success": True,
        }), 200

    except Exception:

        logger.exception(
            "Transfer callback error."
        )

        return jsonify({
            "success": True,
        }), 202


# ============================================================
# REFERRAL ROUTES
# ============================================================

@web_app.route(
    "/referral/login",
    methods=["GET", "POST"],
)
def referral_login():

    return promoter_login_page()


@web_app.route(
    "/referral/logout"
)
def referral_logout():

    return promoter_logout_page()


@web_app.route(
    "/referral/<referral_code>"
)
def referral_dashboard(
    referral_code
):

    return referral_dashboard_by_code(
        referral_code
    )


@web_app.route(
    "/referral-dashboard"
)
def old_referral_dashboard():

    referral_code = (
        request.args.get(
            "referral_code",
            ""
        ).strip()
    )

    if referral_code:

        return redirect(
            url_for(
                "referral_dashboard",
                referral_code=referral_code,
            )
        )

    return promoter_login_page()


@web_app.route(
    "/withdrawal",
    methods=["GET", "POST"],
)
def withdrawal():

    return withdrawal_page()


@web_app.route(
    "/withdrawal-status/<transfer_id>"
)
def withdrawal_status(
    transfer_id
):

    return withdrawal_status_page(
        transfer_id
    )


# ============================================================
# ADMIN ROUTES
# ============================================================

if ADMIN_MODULE_AVAILABLE:

    @web_app.route(
        "/admin/referral"
    )
    def admin_referral():

        return admin_referral_page()


    @web_app.route(
        "/admin/login",
        methods=["GET", "POST"],
    )
    def admin_login():

        return admin_login_page()


    @web_app.route(
        "/admin/logout"
    )
    def admin_logout():

        return admin_logout_page()


    @web_app.route(
        "/admin/promoter/create",
        methods=["GET", "POST"],
    )
    def admin_create_promoter():

        return create_promoter_page()


    @web_app.route(
        "/admin/withdrawals"
    )
    def admin_withdrawals():

        return admin_withdrawal_status_page()


# ============================================================
# TELEGRAM BOT MENUS
# ============================================================

MAIN_MENU = ReplyKeyboardMarkup(

    [

        [
            "📚 Courses",
            "📝 CBT Practice",
        ],

        [
            "🧾 Student Registration",
            "💳 Pay School Fees",
        ],

        [
            "📞 Contact Us",
            "ℹ️ About Us",
        ],

    ],

    resize_keyboard=True,
)


# ============================================================
# TELEGRAM /START
# ============================================================

async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    context.user_data.clear()

    await update.message.reply_text(

        "🎓 Welcome to Alhikam Learning Center!\n\n"

        "We provide online learning and examination "
        "preparation services including JAMB, WAEC "
        "and NECO.\n\n"

        "Please select an option below.",

        reply_markup=MAIN_MENU,
    )


# ============================================================
# CANCEL
# ============================================================

async def cancel_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    context.user_data.clear()

    await update.message.reply_text(

        "❌ Operation cancelled.\n\n"
        "Choose another option.",

        reply_markup=MAIN_MENU,
    )


# ============================================================
# TELEGRAM MESSAGE HANDLER
# ============================================================

async def message_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not update.message:

        return

    text = (
        update.message.text or ""
    ).strip()

    user = update.effective_user

    # --------------------------------------------------------
    # Courses
    # --------------------------------------------------------

    if text == "📚 Courses":

        await update.message.reply_text(

            "📚 ALHIKAM COURSES\n\n"

            "• JAMB Online Tutorial\n"
            "• WAEC Preparation\n"
            "• NECO Preparation\n"
            "• English Language\n"
            "• Arabic Language\n"
            "• French Language\n"
            "• Science Lessons\n"
            "• Arts Lessons\n\n"

            "Use 💳 Pay School Fees to subscribe.",

            reply_markup=MAIN_MENU,
        )

        return

    # --------------------------------------------------------
    # CBT
    # --------------------------------------------------------

    if text == "📝 CBT Practice":

        await update.message.reply_text(

            "📝 CBT PRACTICE\n\n"

            "Our CBT practice system is being prepared.\n\n"
            "You will be able to practise questions "
            "and monitor your performance.",

            reply_markup=MAIN_MENU,
        )

        return

    # --------------------------------------------------------
    # Payment
    # --------------------------------------------------------

    if text == "💳 Pay School Fees":

        await update.message.reply_text(

            "💳 ALHIKAM PAYMENT\n\n"
            "Click below to select your plan:",

            reply_markup=InlineKeyboardMarkup([

                [

                    InlineKeyboardButton(
                        "💳 Make Payment",
                        url=f"{RAILWAY_URL}/pay",
                    )

                ]

            ]),
        )

        return

    # --------------------------------------------------------
    # Registration
    # --------------------------------------------------------

    if text == "🧾 Student Registration":

        context.user_data[
            "registration_step"
        ] = "full_name"

        await update.message.reply_text(

            "🧾 STUDENT REGISTRATION\n\n"
            "Please enter your full name:",

            reply_markup=ReplyKeyboardMarkup(
                [["❌ Cancel"]],
                resize_keyboard=True,
            ),
        )

        return

    # --------------------------------------------------------
    # Contact
    # --------------------------------------------------------

    if text == "📞 Contact Us":

        await update.message.reply_text(

            "📞 ALHIKAM LEARNING CENTER\n\n"

            "For support and enquiries:\n\n"

            "📧 aalhikamlearningcenter@gmail.com\n\n"

            "Telegram:\n"
            f"@{TELEGRAM_BOT_USERNAME}",

            reply_markup=MAIN_MENU,
        )

        return

    # --------------------------------------------------------
    # About
    # --------------------------------------------------------

    if text == "ℹ️ About Us":

        await update.message.reply_text(

            "ℹ️ ABOUT ALHIKAM LEARNING CENTER\n\n"

            "Alhikam Learning Center is an online "
            "education platform focused on helping "
            "students prepare for JAMB, WAEC, NECO "
            "and other learning programmes.",

            reply_markup=MAIN_MENU,
        )

        return

    # --------------------------------------------------------
    # Cancel
    # --------------------------------------------------------

    if text == "❌ Cancel":

        context.user_data.clear()

        await update.message.reply_text(

            "❌ Registration cancelled.",

            reply_markup=MAIN_MENU,
        )

        return

    # --------------------------------------------------------
    # Registration state
    # --------------------------------------------------------

    step = context.user_data.get(
        "registration_step"
    )

    if not step:

        await update.message.reply_text(

            "Please select an option from the menu.",

            reply_markup=MAIN_MENU,
        )

        return

    if step == "full_name":

        context.user_data[
            "full_name"
        ] = text

        context.user_data[
            "registration_step"
        ] = "phone"

        await update.message.reply_text(
            "📱 Enter your phone number:"
        )

        return

    if step == "phone":

        context.user_data[
            "phone"
        ] = text

        context.user_data[
            "registration_step"
        ] = "email"

        await update.message.reply_text(
            "📧 Enter your email address:"
        )

        return

    if step == "email":

        context.user_data[
            "email"
        ] = text

        context.user_data[
            "registration_step"
        ] = "course"

        await update.message.reply_text(

            "📚 Enter your course:\n\n"
            "Example: JAMB Online Tutorial"
        )

        return

    if step == "course":

        context.user_data[
            "course"
        ] = text

        registration_data = {

            "full_name":
                context.user_data.get(
                    "full_name"
                ),

            "phone":
                context.user_data.get(
                    "phone"
                ),

            "email":
                context.user_data.get(
                    "email"
                ),

            "course":
                context.user_data.get(
                    "course"
                ),

            "telegram_id":
                user.id,

            "telegram_username":
                user.username or "",

            "registered_at":
                datetime.now(
                    timezone.utc
                ).isoformat(),
        }

        try:

            saved = (
                save_registration_to_google_sheets(
                    registration_data
                )
            )

        except Exception:

            logger.exception(
                "Bot registration failed."
            )

            saved = False

        if saved:

            await update.message.reply_text(

                "✅ Registration submitted successfully!\n\n"
                "Thank you for registering with "
                "Alhikam Learning Center.",

                reply_markup=MAIN_MENU,
            )

        else:

            await update.message.reply_text(

                "❌ We could not save your registration "
                "right now. Please try again later.",

                reply_markup=MAIN_MENU,
            )

        context.user_data.clear()

        return


# ============================================================
# START FLASK SERVER
# ============================================================

def run_flask():

    logger.info(
        "Starting Flask on port %s",
        PORT,
    )

    web_app.run(
        host="0.0.0.0",
        port=PORT,
        threaded=True,
        use_reloader=False,
    )


# ============================================================
# TELEGRAM POST INIT
# ============================================================

async def telegram_post_init(
    application: Application,
):

    global telegram_loop

    telegram_loop = (
        asyncio.get_running_loop()
    )

    logger.info(
        "Telegram event loop initialized."
    )


# ============================================================
# MAIN
# ============================================================

def main():

    global telegram_bot_app

    # --------------------------------------------------------
    # Required variables
    # --------------------------------------------------------

    missing = []

    if not BOT_TOKEN:
        missing.append("BOT_TOKEN")

    if not FLW_SECRET_KEY:
        missing.append("FLW_SECRET_KEY")

    if not FLUTTERWAVE_SECRET_HASH:
        missing.append(
            "FLUTTERWAVE_SECRET_HASH"
        )

    if not missing:

        logger.info(
            "All required environment variables are available."
        )

    else:

        raise RuntimeError(
            "Missing Railway environment variables: "
            + ", ".join(missing)
        )

    # --------------------------------------------------------
    # Flask thread
    # --------------------------------------------------------

    flask_thread = threading.Thread(
        target=run_flask,
        daemon=True,
    )

    flask_thread.start()

    # --------------------------------------------------------
    # Telegram application
    # --------------------------------------------------------

    telegram_bot_app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(telegram_post_init)
        .build()
    )

    telegram_bot_app.add_handler(
        CommandHandler(
            "start",
            start_command,
        )
    )

    telegram_bot_app.add_handler(
        CommandHandler(
            "cancel",
            cancel_command,
        )
    )

    telegram_bot_app.add_handler(
        MessageHandler(
            filters.TEXT
            & ~filters.COMMAND,
            message_handler,
        )
    )

    logger.info(
        "================================================"
    )

    logger.info(
        "ALHIKAM LEARNING CENTER V2 STARTED"
    )

    logger.info(
        "Payment page: %s/pay",
        RAILWAY_URL,
    )

    logger.info(
        "Webhook: %s/webhook/flutterwave",
        RAILWAY_URL,
    )

    logger.info(
        "Bot: @%s",
        TELEGRAM_BOT_USERNAME,
    )

    logger.info(
        "================================================"
    )

    telegram_bot_app.run_polling(
        drop_pending_updates=True,
        close_loop=False,
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()