# ============================================================
# ALHIKAM LEARNING CENTER BOT
# ============================================================
#
# Flow:
# Flutterwave Payment
# -> Verified Payment
# -> Telegram Login
# -> Registration
# -> Google Sheets
# -> Unique Telegram Invite
# -> Bot sends invite directly
#
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

from markupsafe import escape
from decimal import Decimal

from flask import (
    Flask,
    request,
    jsonify,
    render_template_string,
    redirect,
    url_for,
    session,
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
# ALHIKAM DATABASE + SECURE REFERRAL SYSTEM
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


# ============================================================
# OPTIONAL ADMIN REFERRAL MODULE
# ============================================================

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

    ADMIN_MODULE_AVAILABLE = False


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

initialize_database()

logger = logging.getLogger(__name__)


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
    "https://script.google.com/macros/s/AKfycbw6LRBGCzMIHcWGEIKXAYXo9bMHxsO_am4a4iSZ4kR58FFA-bj4TcUNy085uTaVRx2z0A/exec",
)


RAILWAY_URL = os.getenv(
    "RAILWAY_URL",
    "https://precious-trust-production-956b.up.railway.app",
).rstrip("/")


PORT = int(
    os.getenv(
        "PORT",
        "8080",
    )
)


MAIN_GROUP_ID = -1004384506380


PUBLIC_PAYMENT_PAGE = (
    f"{RAILWAY_URL}/pay"
)


# Telegram Login Widget bot username
TELEGRAM_BOT_USERNAME = "Alhikamcenterbot"


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
        "amount": 13600,
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
# TEMPORARY STORAGE
#
# NOTE:
# Railway restarts clear this memory.
# Database remains the source of truth.
# ============================================================

pending_payments = {}

processed_payments = set()

telegram_bot_app = None


# ============================================================
# FLASK
# ============================================================

web_app = Flask(__name__)


SECRET_KEY = os.getenv("SECRET_KEY")


if not SECRET_KEY or len(SECRET_KEY) < 32:

    raise RuntimeError(
        "SECRET_KEY must be configured and at least 32 characters long."
    )


web_app.secret_key = SECRET_KEY


web_app.config.update(

    SESSION_COOKIE_HTTPONLY=True,

    SESSION_COOKIE_SAMESITE="Lax",

    SESSION_COOKIE_SECURE=RAILWAY_URL.startswith(
        "https://"
    ),

    PERMANENT_SESSION_LIFETIME=86400,

)


# ============================================================
# HOME
# ============================================================

@web_app.route(
    "/",
    methods=["GET"],
)
def home():

    return jsonify(

        {

            "status": "online",

            "bot":
                "ALHIKAM Learning Center Bot",

            "payment_page":
                PUBLIC_PAYMENT_PAGE,

            "webhook":
                f"{RAILWAY_URL}/webhook/flutterwave",

            "telegram_login":
                f"{RAILWAY_URL}/telegram-login",

        }

    )


# ============================================================
# HEALTH
# ============================================================

@web_app.route(
    "/health",
    methods=["GET"],
)
def health():

    return jsonify(
        {
            "status": "healthy"
        }
    )


# ============================================================
# PAYMENT PAGE
# ============================================================

PAYMENT_PAGE_HTML = """

<!DOCTYPE html>

<html>

<head>

<meta name="viewport"
      content="width=device-width, initial-scale=1">

<title>
ALHIKAM Learning Center Payment
</title>

<style>

body{

    font-family:Arial,sans-serif;

    background:#f4f7f6;

    margin:0;

    padding:20px

}

.container{

    max-width:520px;

    margin:30px auto;

    background:white;

    padding:25px;

    border-radius:16px;

    box-shadow:0 4px 18px rgba(0,0,0,.10)

}

h1{

    color:#087f5b;

    text-align:center

}

.subtitle{

    text-align:center;

    color:#555;

    margin-bottom:25px

}

.plan{

    border:1px solid #ddd;

    border-radius:12px;

    padding:15px;

    margin:10px 0

}

.plan label{

    display:block;

    cursor:pointer

}

.amount{

    font-weight:bold;

    font-size:18px;

    color:#087f5b

}

button{

    width:100%;

    padding:15px;

    margin-top:20px;

    border:none;

    border-radius:10px;

    background:#087f5b;

    color:white;

    font-size:17px;

    font-weight:bold;

    cursor:pointer

}

.note{

    text-align:center;

    font-size:13px;

    color:#777;

    margin-top:18px

}

</style>

</head>

<body>

<div class="container">

<h1>
🎓 ALHIKAM Learning Center
</h1>

<div class="subtitle">

Choose your learning duration and continue to secure payment.

</div>

<form method="POST"
      action="/create-payment">

<input type="hidden"
       name="referral_code"
       value="{{ referral_code }}">

{% for key, plan in plans.items() %}

<div class="plan">

<label>

<input type="radio"
       name="plan"
       value="{{ key }}"
       required>

<strong>
{{ plan.name }}
</strong>

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

After successful payment, you will connect your Telegram account and complete registration.

</div>

</div>

</body>

</html>

"""


@web_app.route(
    "/pay",
    methods=["GET"],
)
def payment_page():

    referral_code = (

        request.args.get(
            "ref",
            "",
        )
        or ""

    ).strip()


    if (

        referral_code

        and not get_promoter_by_referral_code(
            referral_code
        )

    ):

        referral_code = ""


    return render_template_string(

        PAYMENT_PAGE_HTML,

        plans=PAYMENT_PLANS,

        referral_code=referral_code,

    )


# ============================================================
# CREATE FLUTTERWAVE PAYMENT
# ============================================================

@web_app.route(
    "/create-payment",
    methods=["POST"],
)
def create_payment():

    if not FLW_SECRET_KEY:

        return (
            "Payment system is temporarily unavailable.",
            500,
        )


    plan_number = (

        request.form.get(
            "plan"
        )
        or ""

    ).strip()


    plan = PAYMENT_PLANS.get(
        plan_number
    )


    if not plan:

        return (
            "Invalid payment plan.",
            400,
        )


    referral_code = (

        request.form.get(
            "referral_code"
        )
        or ""

    ).strip()


    promoter = None


    if referral_code:

        promoter = (
            get_promoter_by_referral_code(
                referral_code
            )
        )

        if not promoter:

            referral_code = ""


    payment_token = uuid.uuid4().hex


    tx_ref = (
        f"ALHIKAM_{payment_token}"
    )


    payment = {

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

        "payment_status":
            "Pending",

        "referral_code":
            referral_code,

        "promoter_id":
            (
                promoter["id"]
                if promoter
                else None
            ),

        "promoter_name":
            (
                promoter["full_name"]
                if promoter
                else ""
            ),

        "commission":
            0,

        "registration_completed":
            0,

    }


    pending_payments[
        payment_token
    ] = payment.copy()


    save_payment(
        payment
    )


    payload = {

        "tx_ref":
            tx_ref,

        "amount":
            plan["amount"],

        "currency":
            "NGN",

        "redirect_url":
            (
                f"{RAILWAY_URL}/payment-complete/"
                f"{payment_token}"
            ),

        "customer": {

            "email":
                (
                    f"student_{payment_token}"
                    "@alhikam.com"
                ),

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


        logger.info(

            "Flutterwave checkout status=%s",

            response.status_code,

        )


        if (

            response.status_code == 200

            and result.get(
                "status"
            ) == "success"

        ):

            payment_link = (

                result.get(
                    "data",
                    {}
                ).get(
                    "link"
                )

            )


            if payment_link:

                return redirect(
                    payment_link
                )


        return (
            "Unable to create payment link. Please try again.",
            500,
        )


    except requests.RequestException:

        logger.exception(
            "Flutterwave payment request failed"
        )

        return (
            "Payment system error. Please try again later.",
            500,
        )


    except Exception:

        logger.exception(
            "Flutterwave payment creation failed"
        )

        return (
            "Payment system error. Please try again later.",
            500,
        )


# ============================================================
# PAYMENT HELPERS
# ============================================================

def _payment_from_token(
    payment_token
):

    if not payment_token:

        return None


    tx_ref = (
        f"ALHIKAM_{payment_token}"
    )


    row = get_payment_by_tx_ref(
        tx_ref
    )


    if row:

        data = dict(row)


        data["plan_name"] = (

            data.get(
                "payment_plan"
            )

            or data.get(
                "plan_name"
            )

            or ""

        )


        data["amount"] = float(

            data.get(
                "amount"
            )
            or 0

        )


        data["status"] = str(

            data.get(
                "payment_status"
            )
            or ""

        ).lower()


        if data["status"] in {

            "successful",

            "success",

            "completed",

        }:

            data["status"] = "successful"


        data[
            "registration_completed"
        ] = int(

            data.get(
                "registration_completed"
            )
            or 0

        )


        if data.get(
            "telegram_id"
        ):

            data[
                "telegram_auth"
            ] = {

                "telegram_id":
                    str(
                        data.get(
                            "telegram_id"
                        )
                    ),

                "telegram_username":
                    data.get(
                        "telegram_username"
                    )
                    or "",

                "first_name":
                    (
                        data.get(
                            "telegram_name"
                        )
                        or ""
                    ).split(
                        " "
                    )[0],

                "last_name":
                    " ".join(

                        (
                            data.get(
                                "telegram_name"
                            )
                            or ""
                        ).split(
                            " "
                        )[1:]

                    ),

            }


        return data


    return pending_payments.get(
        payment_token
    )


# ============================================================
# COMMISSION CALCULATOR
# ============================================================

def _commission_for_amount(
    amount
):

    try:

        amount = int(

            Decimal(
                str(amount)
            )

        )

    except Exception:

        return 0


    return {

        3600:
            200,

        6800:
            500,

        10000:
            800,

        13600:
            1200,

        16500:
            1800,

        20000:
            2500,

    }.get(
        amount,
        0
    )


# ============================================================
# PAYMENT RETURN PAGE
# DIRECT FLUTTERWAVE VERIFICATION
# ============================================================

def _verify_and_finalize_payment(
    payment_token,
    transaction_id=None,
):

    payment = _payment_from_token(
        payment_token
    )

    if not payment:
        return None

    # --------------------------------------------------------
    # ALREADY SUCCESSFUL
    # --------------------------------------------------------
    if str(
        payment.get("status") or ""
    ).lower() == "successful":

        return payment

    transaction_id = str(
        transaction_id or ""
    ).strip()

    if not transaction_id:

        logger.warning(
            "No Flutterwave transaction ID received "
            "for payment token=%s",
            payment_token,
        )

        return payment

    # --------------------------------------------------------
    # VERIFY DIRECTLY WITH FLUTTERWAVE
    # --------------------------------------------------------
    verified = verify_flutterwave_transaction(
        transaction_id
    )

    if not verified:

        logger.warning(
            "Flutterwave verification unavailable "
            "tx_ref=%s transaction_id=%s",
            payment.get("tx_ref"),
            transaction_id,
        )

        return payment

    # --------------------------------------------------------
    # VERIFIED DATA
    # --------------------------------------------------------
    verified_status = str(
        verified.get("status") or ""
    ).strip().lower()

    verified_tx_ref = str(
        verified.get("tx_ref") or ""
    ).strip()

    verified_currency = str(
        verified.get("currency") or ""
    ).strip().upper()

    expected_tx_ref = str(
        payment.get("tx_ref") or ""
    ).strip()

    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------
    if verified_status != "successful":

        logger.warning(
            "Payment is not successful "
            "tx_ref=%s status=%s",
            verified_tx_ref,
            verified_status,
        )

        return payment

    # --------------------------------------------------------
    # TX REF
    # --------------------------------------------------------
    if (
        not expected_tx_ref
        or verified_tx_ref != expected_tx_ref
    ):

        logger.error(
            "Payment tx_ref mismatch "
            "expected=%s received=%s",
            expected_tx_ref,
            verified_tx_ref,
        )

        return payment

    # --------------------------------------------------------
    # CURRENCY
    # --------------------------------------------------------
    if verified_currency != "NGN":

        logger.error(
            "Payment currency mismatch "
            "tx_ref=%s currency=%s",
            verified_tx_ref,
            verified_currency,
        )

        return payment

    # --------------------------------------------------------
    # AMOUNT
    # --------------------------------------------------------
    try:

        verified_amount = Decimal(
            str(
                verified.get("amount")
            )
        )

        expected_amount = Decimal(
            str(
                payment.get("amount")
            )
        )

    except Exception:

        logger.exception(
            "Unable to validate payment amount "
            "tx_ref=%s",
            verified_tx_ref,
        )

        return payment

    if verified_amount != expected_amount:

        logger.error(
            "Payment amount mismatch "
            "tx_ref=%s expected=%s received=%s",
            verified_tx_ref,
            expected_amount,
            verified_amount,
        )

        return payment

    # --------------------------------------------------------
    # PAYMENT MUST BELONG TO ALHIKAM
    # --------------------------------------------------------
    if not verified_tx_ref.startswith(
        "ALHIKAM_"
    ):

        logger.error(
            "Invalid ALHIKAM transaction reference: %s",
            verified_tx_ref,
        )

        return payment

    # --------------------------------------------------------
    # PROMOTER
    # --------------------------------------------------------
    promoter_id = payment.get(
        "promoter_id"
    )

    referral_code = str(
        payment.get("referral_code") or ""
    ).strip().upper()

    promoter = None

    if promoter_id:

        try:

            promoter = get_promoter_by_id(
                promoter_id
            )

        except Exception:

            logger.exception(
                "Could not load promoter id=%s",
                promoter_id,
            )

            promoter = None

    # --------------------------------------------------------
    # VALIDATE PROMOTER
    # --------------------------------------------------------
    if promoter:

        promoter_status = str(
            promoter.get("status") or ""
        ).strip().lower()

        promoter_referral_code = str(
            promoter.get("referral_code") or ""
        ).strip().upper()

        if promoter_status != "active":

            promoter = None

        elif (
            referral_code
            and promoter_referral_code != referral_code
        ):

            logger.error(
                "Promoter referral mismatch "
                "payment=%s promoter=%s",
                referral_code,
                promoter_referral_code,
            )

            promoter = None

    # --------------------------------------------------------
    # COMMISSION
    # --------------------------------------------------------
    commission_amount = 0

    if promoter:

        commission_amount = (
            _commission_for_amount(
                verified_amount
            )
        )

    # --------------------------------------------------------
    # UPDATE PAYMENT STATUS
    # --------------------------------------------------------
    try:

        update_payment_status(

            verified_tx_ref,

            "Successful",

            transaction_id=transaction_id,

        )

    except Exception:

        logger.exception(
            "Failed to update payment status "
            "tx_ref=%s",
            verified_tx_ref,
        )

        return payment

    # --------------------------------------------------------
    # SAVE VERIFIED PAYMENT
    # --------------------------------------------------------
    try:

        save_payment(

            {

                "tx_ref":
                    verified_tx_ref,

                "transaction_id":
                    transaction_id,

                "payment_plan":
                    (
                        payment.get(
                            "plan_name"
                        )

                        or payment.get(
                            "payment_plan",
                            "",
                        )
                    ),

                "amount":
                    float(
                        verified_amount
                    ),

                "payment_status":
                    "Successful",

                "referral_code":
                    (
                        referral_code
                        if promoter
                        else ""
                    ),

                "promoter_id":
                    (
                        promoter["id"]
                        if promoter
                        else None
                    ),

                "promoter_name":
                    (
                        promoter["full_name"]
                        if promoter
                        else ""
                    ),

                "commission":
                    commission_amount,

                "telegram_id":
                    payment.get(
                        "telegram_id",
                        "",
                    ),

                "telegram_username":
                    payment.get(
                        "telegram_username",
                        "",
                    ),

                "telegram_name":
                    payment.get(
                        "telegram_name",
                        "",
                    ),

                "registration_completed":
                    payment.get(
                        "registration_completed",
                        0,
                    ),

            }

        )

    except Exception:

        logger.exception(
            "Failed to save verified payment "
            "tx_ref=%s",
            verified_tx_ref,
        )

        return payment

    # --------------------------------------------------------
    # UPDATE MEMORY
    # --------------------------------------------------------
    pending_payments[
        payment_token
    ] = {

        **pending_payments.get(
            payment_token,
            {},
        ),

        **payment,

        "status":
            "successful",

        "payment_status":
            "Successful",

        "transaction_id":
            transaction_id,

        "promoter_id":
            (
                promoter["id"]
                if promoter
                else None
            ),

        "promoter_name":
            (
                promoter["full_name"]
                if promoter
                else ""
            ),

        "commission":
            commission_amount,

    }

    # --------------------------------------------------------
    # CREATE COMMISSION ONLY ONCE
    # --------------------------------------------------------
    if (

        promoter

        and commission_amount > 0

        and not commission_exists(
            verified_tx_ref
        )

    ):

        try:

            create_commission(

                promoter_id=
                    promoter["id"],

                student_id=
                    None,

                tx_ref=
                    verified_tx_ref,

                payment_amount=
                    verified_amount,

                commission_amount=
                    commission_amount,

            )

            logger.info(

                "Commission created "
                "tx_ref=%s promoter=%s amount=%s",

                verified_tx_ref,

                promoter["id"],

                commission_amount,

            )

        except Exception:

            logger.exception(

                "Commission creation failed "
                "tx_ref=%s",

                verified_tx_ref,

            )

    # --------------------------------------------------------
    # SUCCESS LOG
    # --------------------------------------------------------
    logger.info(

        "DIRECT FLUTTERWAVE PAYMENT VERIFIED "
        "tx_ref=%s transaction_id=%s",

        verified_tx_ref,

        transaction_id,

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
def payment_complete(
    payment_token
):

    payment = _payment_from_token(
        payment_token
    )

    # --------------------------------------------------------
    # PAYMENT NOT FOUND
    # --------------------------------------------------------
    if not payment:

        return (

            """

            <!DOCTYPE html>

            <html>

            <head>

            <meta name="viewport"
                  content="width=device-width, initial-scale=1">

            <title>
            Payment Not Found
            </title>

            </head>

            <body style="
                font-family:Arial;
                text-align:center;
                padding:50px 20px;
            ">

            <h2>
            ❌ Payment Reference Not Found
            </h2>

            <p>
            We could not find this payment reference.
            </p>

            <p>
            Please contact ALHIKAM Learning Center
            support if money was deducted.
            </p>

            </body>

            </html>

            """,

            404,

        )

    # --------------------------------------------------------
    # GET FLUTTERWAVE RETURN DATA
    # --------------------------------------------------------
    transaction_id = (

        request.args.get(
            "transaction_id"
        )

        or request.args.get(
            "id"
        )

        or ""

    ).strip()

    flutterwave_status = str(

        request.args.get(
            "status"
        )

        or ""

    ).strip().lower()

    returned_tx_ref = str(

        request.args.get(
            "tx_ref"
        )

        or ""

    ).strip()

    expected_tx_ref = str(

        payment.get(
            "tx_ref"
        )

        or ""

    ).strip()

    # --------------------------------------------------------
    # VERIFY RETURNED TX REF
    # --------------------------------------------------------
    if (

        returned_tx_ref

        and returned_tx_ref != expected_tx_ref

    ):

        logger.error(

            "Flutterwave redirect tx_ref mismatch "
            "expected=%s received=%s",

            expected_tx_ref,

            returned_tx_ref,

        )

        return (

            """

            <!DOCTYPE html>

            <html>

            <head>

            <meta name="viewport"
                  content="width=device-width, initial-scale=1">

            <title>
            Payment Verification Error
            </title>

            </head>

            <body style="
                font-family:Arial;
                text-align:center;
                padding:50px 20px;
            ">

            <h2>
            ❌ Payment Verification Error
            </h2>

            <p>
            The payment reference could not be verified.
            </p>

            <p>
            Please contact ALHIKAM Learning Center.
            </p>

            </body>

            </html>

            """,

            400,

        )

    # --------------------------------------------------------
    # DIRECT SERVER-SIDE VERIFICATION
    # --------------------------------------------------------
    if (

        str(
            payment.get("status") or ""
        ).lower()
        != "successful"

        and transaction_id

    ):

        payment = _verify_and_finalize_payment(

            payment_token,

            transaction_id,

        )

    # --------------------------------------------------------
    # SUCCESS
    # --------------------------------------------------------
    if (

        payment

        and str(
            payment.get("status") or ""
        ).lower()
        == "successful"

    ):

        logger.info(

            "Payment verified successfully. "
            "Redirecting to Telegram login. "
            "token=%s",

            payment_token,

        )

        return redirect(

            f"/telegram-login/"
            f"{payment_token}"

        )

    # --------------------------------------------------------
    # FAILED / CANCELLED
    # --------------------------------------------------------
    if flutterwave_status in {

        "cancelled",

        "canceled",

        "failed",

    }:

        return (

            """

            <!DOCTYPE html>

            <html>

            <head>

            <meta name="viewport"
                  content="width=device-width, initial-scale=1">

            <title>
            Payment Not Completed
            </title>

            </head>

            <body style="
                font-family:Arial;
                text-align:center;
                padding:50px 20px;
            ">

            <h2>
            ❌ Payment Not Completed
            </h2>

            <p>
            Your payment was cancelled or failed.
            </p>

            <p>
            If money was deducted, please wait for
            Flutterwave to process the transaction.
            </p>

            <br>

            <a href="/pay">
            🔄 Try Payment Again
            </a>

            </body>

            </html>

            """

        )

    # --------------------------------------------------------
    # STILL VERIFYING
    # --------------------------------------------------------
    return f"""

    <!DOCTYPE html>

    <html>

    <head>

    <meta name="viewport"
          content="width=device-width, initial-scale=1">

    <title>
    Payment Verification
    </title>

    <meta
        http-equiv="refresh"
        content="5"
    >

    <style>

    body{{

        font-family:Arial,sans-serif;

        background:#f4f7f6;

        margin:0;

        padding:30px 20px;

        text-align:center;

    }}

    .container{{

        max-width:520px;

        margin:30px auto;

        background:white;

        padding:30px;

        border-radius:16px;

        box-shadow:
            0 4px 18px rgba(0,0,0,.10);

    }}

    h2{{

        color:#087f5b;

    }}

    .loader{{

        font-size:42px;

        margin:15px;

    }}

    .refresh{{

        display:inline-block;

        margin-top:15px;

        padding:12px 20px;

        background:#087f5b;

        color:white;

        text-decoration:none;

        border-radius:8px;

    }}

    </style>

    </head>

    <body>

    <div class="container">

    <div class="loader">
    ⏳
    </div>

    <h2>
    Payment Verification
    </h2>

    <p>
    Your payment is being verified securely
    with Flutterwave.
    </p>

    <p>
    Please wait a moment.
    </p>

    <p>
    This page will automatically refresh.
    </p>

    <a
        class="refresh"
        href="/payment-complete/{payment_token}"
    >
    🔄 Refresh Now
    </a>

    </div>

    </body>

    </html>

    """


# ============================================================
# TELEGRAM LOGIN PAGE
# ============================================================

TELEGRAM_LOGIN_HTML = """

<!DOCTYPE html>

<html>

<head>

<meta name="viewport"
      content="width=device-width, initial-scale=1">

<title>
Connect Telegram
</title>

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

h1{

    color:#087f5b

}

.info{

    background:#eef8f4;

    padding:15px;

    border-radius:10px;

    margin:20px 0;

    text-align:left;

}

</style>


<script async
        src="https://telegram.org/js/telegram-widget.js?22"
        data-telegram-login="{{ bot_username }}"
        data-size="large"
        data-userpic="false"
        data-request-access="write"
        data-onauth="onTelegramAuth(user)">
</script>


<script>

function onTelegramAuth(user) {

    const form =
        document.createElement("form");

    form.method = "POST";

    form.action = "/telegram-auth";


    const data = {

        payment_token:
            "{{ payment_token }}",

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

    };


    for (
        const key in data
    ) {

        const input =
            document.createElement(
                "input"
            );

        input.type = "hidden";

        input.name = key;

        input.value = data[key];

        form.appendChild(
            input
        );

    }


    document.body.appendChild(
        form
    );


    form.submit();

}

</script>

</head>


<body>

<div class="container">

<h1>
🔗 Connect Your Telegram
</h1>


<div class="info">

<strong>
Payment Confirmed ✅
</strong>

<br><br>

Plan:
{{ plan_name }}

<br>

Amount:
₦{{ "{:,}".format(amount) }}

</div>


<p>

To continue registration, connect the Telegram account you will use to receive your ALHIKAM class invite.

</p>


<p>

<strong>
⚠️ Do not enter your Telegram ID manually.
</strong>

</p>


<p>

Click the Telegram button below to connect your account.

</p>

</div>

</body>

</html>

"""


# ============================================================
# TELEGRAM LOGIN ROUTE
# ============================================================

@web_app.route(
    "/telegram-login/<payment_token>",
    methods=["GET"],
)
def telegram_login_page(
    payment_token
):

    payment = _payment_from_token(
        payment_token
    )


    if not payment:

        return (
            "Payment reference not found.",
            404,
        )


    if payment.get(
        "status"
    ) != "successful":

        return (
            "Payment has not been verified.",
            400,
        )


    return render_template_string(

        TELEGRAM_LOGIN_HTML,

        bot_username=
            TELEGRAM_BOT_USERNAME,

        payment_token=
            payment_token,

        plan_name=
            payment.get(
                "plan_name",
                ""
            ),

        amount=
            payment.get(
                "amount",
                0
            ),

    )


# ============================================================
# TELEGRAM LOGIN VERIFICATION
# ============================================================

def verify_telegram_login(
    data
):

    if not BOT_TOKEN:

        return False


    received_hash = data.get(
        "hash",
        ""
    )


    auth_date = str(

        data.get(
            "auth_date",
            ""
        )

    )


    telegram_id = str(

        data.get(
            "id",
            ""
        )

    )


    if (

        not received_hash

        or not auth_date

        or not telegram_id

    ):

        return False


    try:

        if (

            abs(

                int(time.time())

                - int(auth_date)

            )

            > 3600

        ):

            return False

    except Exception:

        return False


    check_data = {

        "id":
            telegram_id,

        "first_name":
            data.get(
                "first_name",
                ""
            ),

        "last_name":
            data.get(
                "last_name",
                ""
            ),

        "username":
            data.get(
                "username",
                ""
            ),

        "photo_url":
            data.get(
                "photo_url",
                ""
            ),

        "auth_date":
            auth_date,

    }


    pairs = []


    for key, value in check_data.items():

        if value not in (
            None,
            "",
        ):

            pairs.append(
                f"{key}={value}"
            )


    data_check_string = "\n".join(
        sorted(pairs)
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
# TELEGRAM AUTH ROUTE
# ============================================================

@web_app.route(
    "/telegram-auth",
    methods=["POST"],
)
def telegram_auth():

    payment_token = (

        request.form.get(
            "payment_token",
            ""
        )

    ).strip()


    payment = _payment_from_token(
        payment_token
    )


    if not payment:

        return (
            "Payment reference not found.",
            404,
        )


    if payment.get(
        "status"
    ) != "successful":

        return (
            "Payment has not been verified.",
            400,
        )


    data = {

        "id":
            request.form.get(
                "id",
                ""
            ),

        "first_name":
            request.form.get(
                "first_name",
                ""
            ),

        "last_name":
            request.form.get(
                "last_name",
                ""
            ),

        "username":
            request.form.get(
                "username",
                ""
            ),

        "photo_url":
            request.form.get(
                "photo_url",
                ""
            ),

        "auth_date":
            request.form.get(
                "auth_date",
                ""
            ),

        "hash":
            request.form.get(
                "hash",
                ""
            ),

    }


    if not verify_telegram_login(
        data
    ):

        return (
            """
            <h2>
            Telegram Verification Failed ❌
            </h2>

            <p>
            Please go back and connect Telegram again.
            </p>
            """,
            401,
        )


    payment["telegram_auth"] = {

        "telegram_id":
            data["id"],

        "telegram_username":
            data["username"],

        "first_name":
            data["first_name"],

        "last_name":
            data["last_name"],

    }


    save_payment(

        {

            "tx_ref":
                payment["tx_ref"],

            "transaction_id":
                payment.get(
                    "transaction_id",
                    ""
                ),

            "payment_plan":
                payment.get(
                    "plan_name",
                    ""
                ),

            "amount":
                payment.get(
                    "amount",
                    0
                ),

            "payment_status":
                "Successful",

            "referral_code":
                payment.get(
                    "referral_code",
                    ""
                ),

            "promoter_id":
                payment.get(
                    "promoter_id"
                ),

            "promoter_name":
                payment.get(
                    "promoter_name",
                    ""
                ),

            "commission":
                payment.get(
                    "commission",
                    0
                ),

            "telegram_id":
                data["id"],

            "telegram_username":
                data["username"],

            "telegram_name":
                (
                    f"{data['first_name']} "
                    f"{data['last_name']}"
                ).strip(),

            "registration_completed":
                payment.get(
                    "registration_completed",
                    0
                ),

        }

    )


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

<meta name="viewport"
      content="width=device-width, initial-scale=1">

<title>
ALHIKAM Student Registration
</title>

<style>

body{

    font-family:Arial;

    background:#f4f7f6;

    padding:20px

}

.container{

    max-width:520px;

    margin:30px auto;

    background:white;

    padding:25px;

    border-radius:16px;

    box-shadow:0 4px 18px rgba(0,0,0,.10)

}

h1{

    color:#087f5b;

    text-align:center

}

input,select{

    width:100%;

    padding:13px;

    margin:8px 0 15px;

    border:1px solid #ddd;

    border-radius:8px;

    box-sizing:border-box

}

button{

    width:100%;

    padding:15px;

    background:#087f5b;

    color:white;

    border:none;

    border-radius:10px;

    font-size:17px;

    font-weight:bold

}

.info{

    background:#eef8f4;

    padding:15px;

    border-radius:10px;

    margin-bottom:20px

}

.connected{

    background:#e8f5e9;

    padding:12px;

    border-radius:8px;

    margin-bottom:20px

}

</style>

</head>


<body>

<div class="container">

<h1>
🎓 ALHIKAM Learning Center
</h1>


<div class="info">

<strong>
Payment Confirmed ✅
</strong>

<br><br>

Plan:
{{ plan_name }}

<br>

Amount:
₦{{ "{:,}".format(amount) }}

</div>


<div class="connected">

<strong>
Telegram Connected ✅
</strong>

<br>

Username:
@{{ telegram_username if telegram_username else "Telegram User" }}

<br>

Your Telegram ID has been verified automatically.

</div>


<form method="POST">

<input
    type="hidden"
    name="csrf_token"
    value="{{ csrf_token }}"
>


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


<button type="submit">

✅ COMPLETE REGISTRATION

</button>

</form>

</div>

</body>

</html>

"""


# ============================================================
# REGISTRATION CSRF
# ============================================================

def registration_csrf(
    payment_token
):

    key = (
        f"reg_csrf_{payment_token}"
    )


    token = session.get(
        key
    )


    if not token:

        token = secrets.token_urlsafe(
            32
        )

        session[key] = token


    return token


# ============================================================
# REGISTRATION FORM ROUTE
# ============================================================

@web_app.route(
    "/registration-form/<payment_token>",
    methods=["GET", "POST"],
)
def registration_form(
    payment_token
):

    payment = _payment_from_token(
        payment_token
    )


    if not payment:

        return (
            "Payment reference not found.",
            404,
        )


    if payment.get(
        "status"
    ) != "successful":

        return (
            "Payment has not yet been verified.",
            400,
        )


    telegram_auth = payment.get(
        "telegram_auth"
    )


    if not telegram_auth:

        return redirect(
            f"/telegram-login/{payment_token}"
        )


    if payment.get(
        "registration_completed"
    ):

        return (

            "<h2>"
            "Registration Already Completed"
            "</h2>"

            "<p>"
            "Your Telegram class access has already been processed."
            "</p>"

        )


    if request.method == "GET":

        return render_template_string(

            REGISTRATION_HTML,

            plan_name=
                payment["plan_name"],

            amount=
                payment["amount"],

            telegram_username=
                telegram_auth.get(
                    "telegram_username",
                    "",
                ),

            csrf_token=
                registration_csrf(
                    payment_token
                ),

        )


    token = request.form.get(
        "csrf_token",
        ""
    )


    expected = session.get(
        f"reg_csrf_{payment_token}",
        "",
    )


    if (

        not token

        or not expected

        or not secrets.compare_digest(
            token,
            expected,
        )

    ):

        return (

            "Invalid registration request. "
            "Please refresh and try again.",

            400,

        )


    full_name = (

        request.form.get(
            "full_name",
            ""
        )

        .strip()

    )


    phone = (

        request.form.get(
            "phone",
            ""
        )

        .strip()

    )


    email = (

        request.form.get(
            "email",
            ""
        )

        .strip()

    )


    course = (

        request.form.get(
            "course",
            ""
        )

        .strip()

    )


    if (

        not full_name

        or not phone

        or not email

        or not course

    ):

        return (

            "Please complete all required fields.",

            400,

        )


    registration_data = {

        "telegram_id":
            telegram_auth[
                "telegram_id"
            ],

        "telegram_username":
            telegram_auth.get(
                "telegram_username",
                "",
            ),

        "full_name":
            full_name,

        "phone":
            phone,

        "email":
            email,

        "course":
            course,

        "payment_plan":
            payment[
                "plan_name"
            ],

        "amount_paid":
            payment[
                "amount"
            ],

        "tx_ref":
            payment[
                "tx_ref"
            ],

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

        return (

            """

            <h2>
            Registration Saved ✅
            </h2>

            <p>
            Your registration was saved, but your Telegram invite
            could not be created automatically.
            </p>

            <p>
            Please contact ALHIKAM Learning Center.
            </p>

            """,

            500,

        )


    student_id, created_now = create_or_get_student(

        {

            "payment_token":
                payment_token,

            "tx_ref":
                payment["tx_ref"],

            "full_name":
                full_name,

            "phone":
                phone,

            "email":
                email,

            "course":
                course,

            "telegram_id":
                telegram_auth[
                    "telegram_id"
                ],

            "telegram_username":
                telegram_auth.get(
                    "telegram_username",
                    "",
                ),

            "telegram_name":
                (
                    f"{telegram_auth.get('first_name', '')} "
                    f"{telegram_auth.get('last_name', '')}"
                ).strip(),

            "payment_plan":
                payment.get(
                    "plan_name",
                    "",
                ),

            "amount_paid":
                payment.get(
                    "amount",
                    0,
                ),

            "payment_status":
                "Successful",

            "registration_completed":
                1,

            "referral_code":
                payment.get(
                    "referral_code",
                    "",
                ),

            "promoter_id":
                payment.get(
                    "promoter_id"
                ),

        }

    )


    if not created_now:

        mark_payment_registration_completed(
            payment["tx_ref"]
        )

        return (

            "<h2>"
            "Registration Already Completed"
            "</h2>"

            "<p>"
            "Your registration has already been processed."
            "</p>"

        )


    payment[
        "registration_completed"
    ] = True


    payment[
        "registration"
    ] = registration_data


    payment[
        "invite_link"
    ] = invite_link


    mark_payment_registration_completed(
        payment["tx_ref"]
    )


    save_payment(

        {

            "tx_ref":
                payment["tx_ref"],

            "transaction_id":
                payment.get(
                    "transaction_id",
                    "",
                ),

            "payment_plan":
                payment.get(
                    "plan_name",
                    "",
                ),

            "amount":
                payment.get(
                    "amount",
                    0,
                ),

            "payment_status":
                "Successful",

            "referral_code":
                payment.get(
                    "referral_code",
                    "",
                ),

            "promoter_id":
                payment.get(
                    "promoter_id"
                ),

            "promoter_name":
                payment.get(
                    "promoter_name",
                    "",
                ),

            "commission":
                _commission_for_amount(
                    payment.get(
                        "amount",
                        0
                    )
                ),

            "telegram_id":
                telegram_auth[
                    "telegram_id"
                ],

            "telegram_username":
                telegram_auth.get(
                    "telegram_username",
                    "",
                ),

            "telegram_name":
                (
                    f"{telegram_auth.get('first_name', '')} "
                    f"{telegram_auth.get('last_name', '')}"
                ).strip(),

            "registration_completed":
                1,

        }

    )


    telegram_id = int(

        telegram_auth[
            "telegram_id"
        ]

    )


    threading.Thread(

        target=send_registration_access,

        args=(

            telegram_id,

            full_name,

            payment["amount"],

            invite_link,

        ),

        daemon=True,

    ).start()


    safe_full_name = escape(
        full_name
    )


    return f"""

    <html>

    <head>

    <meta name="viewport"
          content="width=device-width, initial-scale=1">

    <style>

    body{{

        font-family:Arial;

        text-align:center;

        padding:40px 20px

    }}

    </style>

    </head>

    <body>

    <h1>
    🎉 Registration Completed!
    </h1>

    <p>

    Welcome to ALHIKAM Learning Center,
    <strong>{safe_full_name}</strong>.

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

def save_registration_to_google_sheets(
    data
):

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


        return (
            response.status_code == 200
        )


    except Exception as e:

        print(
            "Google Sheets Error:",
            e,
        )

        return False


# ============================================================
# CREATE UNIQUE TELEGRAM INVITE LINK
# ============================================================

def create_unique_invite_link(
    payment_token
):

    global telegram_bot_app


    if telegram_bot_app is None:

        print(
            "Telegram application not ready."
        )

        return None


    try:

        async def create_link():

            return await (

                telegram_bot_app.bot
                .create_chat_invite_link(

                    chat_id=MAIN_GROUP_ID,

                    member_limit=1,

                    name=(
                        f"ALHIKAM-{payment_token[:10]}"
                    ),

                )

            )


        invite_link = asyncio.run(
            create_link()
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


# ============================================================
# SEND ACCESS MESSAGE
# ============================================================

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

            reply_markup=InlineKeyboardMarkup(

                [

                    [

                        InlineKeyboardButton(

                            "🎓 JOIN ALHIKAM CLASS",

                            url=invite_link,

                        )

                    ]

                ]

            ),

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

def verify_flutterwave_transaction(
    transaction_id
):

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

            and result.get(
                "status"
            ) == "success"

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

    incoming_hash = request.headers.get(
        "verif-hash"
    )


    if not FLUTTERWAVE_SECRET_HASH:

        return jsonify(

            {

                "status":
                    "error",

                "message":
                    "Webhook secret hash missing",

            }

        ), 500


    if (

        not incoming_hash

        or not hmac.compare_digest(

            str(incoming_hash),

            str(
                FLUTTERWAVE_SECRET_HASH
            ),

        )

    ):

        return jsonify(

            {

                "status":
                    "error",

                "message":
                    "Invalid verification hash",

            }

        ), 401


    data = request.get_json(
        silent=True
    ) or {}


    payment_data = (

        data.get(
            "data"
        )
        or {}

    )


    transaction_id = (

        payment_data.get(
            "id"
        )

    )


    callback_tx_ref = str(

        payment_data.get(
            "tx_ref"
        )
        or ""

    ).strip()


    if (

        not transaction_id

        or not callback_tx_ref

    ):

        return jsonify(

            {

                "status":
                    "error",

                "message":
                    "Missing transaction data",

            }

        ), 400


    verified = verify_flutterwave_transaction(

        transaction_id

    )


    if not verified:

        return jsonify(

            {

                "status":
                    "accepted",

                "message":
                    "Verification unavailable; retry later",

            }

        ), 202


    verified_status = str(

        verified.get(
            "status"
        )
        or ""

    ).lower()


    verified_tx_ref = str(

        verified.get(
            "tx_ref"
        )
        or ""

    ).strip()


    verified_currency = str(

        verified.get(
            "currency"
        )
        or ""

    ).upper()


    if verified_status != "successful":

        return jsonify(
            {
                "status":
                    "ignored"
            }
        ), 200


    if (

        verified_currency != "NGN"

        or verified_tx_ref != callback_tx_ref

    ):

        return jsonify(

            {

                "status":
                    "error",

                "message":
                    "Transaction verification mismatch",

            }

        ), 400


    if not verified_tx_ref.startswith(
        "ALHIKAM_"
    ):

        return jsonify(

            {

                "status":
                    "error",

                "message":
                    "Invalid transaction reference",

            }

        ), 400


    payment_token = verified_tx_ref[
        len("ALHIKAM_"):
    ]


    payment = _payment_from_token(
        payment_token
    )


    if not payment:

        return jsonify(

            {

                "status":
                    "accepted",

                "message":
                    "Payment record not found yet",

            }

        ), 202


    try:

        verified_amount = Decimal(

            str(
                verified.get(
                    "amount"
                )
            )

        )


        expected_amount = Decimal(

            str(
                payment.get(
                    "amount"
                )
            )

        )


    except Exception:

        return jsonify(

            {

                "status":
                    "error",

                "message":
                    "Invalid amount",

            }

        ), 400


    if verified_amount != expected_amount:

        logger.error(

            "Payment amount mismatch tx_ref=%s",

            verified_tx_ref,

        )


        return jsonify(

            {

                "status":
                    "error",

                "message":
                    "Amount mismatch",

            }

        ), 400


    # ========================================================
    # PRESERVE PROMOTER
    # ========================================================

    promoter_id = payment.get(
        "promoter_id"
    )


    referral_code = (

        payment.get(
            "referral_code"
        )
        or ""

    )


    promoter = (

        get_promoter_by_id(
            promoter_id
        )

        if promoter_id

        else None

    )


    if promoter:

        if str(

            promoter[
                "status"
            ]

        ).lower() != "active":

            promoter = None


        elif (

            referral_code

            and str(

                promoter[
                    "referral_code"
                ]

            ).strip()
            != referral_code

        ):

            promoter = None


    # ========================================================
    # COMMISSION
    # ========================================================

    commission_amount = (

        _commission_for_amount(
            verified_amount
        )

        if promoter

        else 0

    )


    # ========================================================
    # UPDATE PAYMENT
    # ========================================================

    update_payment_status(

        verified_tx_ref,

        "Successful",

        transaction_id=transaction_id,

    )


    save_payment(

        {

            "tx_ref":
                verified_tx_ref,

            "transaction_id":
                transaction_id,

            "payment_plan":

                (

                    payment.get(
                        "plan_name"
                    )

                    or payment.get(
                        "payment_plan",
                        "",
                    )

                ),

            "amount":
                float(
                    verified_amount
                ),

            "payment_status":
                "Successful",

            "referral_code":

                (

                    referral_code
                    if promoter
                    else ""

                ),

            "promoter_id":

                (

                    promoter["id"]
                    if promoter
                    else None

                ),

            "promoter_name":

                (

                    promoter["full_name"]
                    if promoter
                    else ""

                ),

            "commission":
                commission_amount,

            "telegram_id":
                payment.get(
                    "telegram_id",
                    "",
                ),

            "telegram_username":
                payment.get(
                    "telegram_username",
                    "",
                ),

            "telegram_name":
                payment.get(
                    "telegram_name",
                    "",
                ),

            "registration_completed":
                payment.get(
                    "registration_completed",
                    0,
                ),

        }

    )


    pending_payments[
        payment_token
    ] = {

        **pending_payments.get(
            payment_token,
            {},
        ),

        **payment,

        "status":
            "successful",

        "payment_status":
            "Successful",

        "transaction_id":
            transaction_id,

        "promoter_id":

            (

                promoter["id"]
                if promoter
                else None

            ),

        "promoter_name":

            (

                promoter["full_name"]
                if promoter
                else ""

            ),

        "commission":
            commission_amount,

    }


    # ========================================================
    # CREDIT COMMISSION ONLY AFTER VERIFICATION
    # ========================================================

    if (

        promoter

        and commission_amount > 0

        and not commission_exists(
            verified_tx_ref
        )

    ):

        create_commission(

            promoter_id=
                promoter["id"],

            student_id=None,

            tx_ref=
                verified_tx_ref,

            payment_amount=
                verified_amount,

            commission_amount=
                commission_amount,

        )


    logger.info(

        "PAYMENT SUCCESSFUL tx_ref=%s",

        verified_tx_ref,

    )


    return jsonify(

        {
            "status":
                "success"
        }

    ), 200


# ============================================================
# FLUTTERWAVE TRANSFER CALLBACK
# ============================================================

@web_app.route(

    "/flutterwave/transfer-callback",

    methods=["GET", "POST"],

)
def flutterwave_transfer_callback():

    try:

        data = request.get_json(
            silent=True
        ) or {}


        transfer_id = (

            data.get(
                "id"
            )

            or data.get(
                "transfer_id"
            )

            or request.form.get(
                "id"
            )

            or request.form.get(
                "transfer_id"
            )

            or request.args.get(
                "id"
            )

            or request.args.get(
                "transfer_id"
            )

        )


        callback_reference = (

            data.get(
                "reference"
            )

            or data.get(
                "transfer_reference"
            )

            or request.form.get(
                "reference"
            )

            or request.form.get(
                "transfer_reference"
            )

            or request.args.get(
                "reference"
            )

            or request.args.get(
                "transfer_reference"
            )

        )


        transfer_id = str(
            transfer_id or ""
        ).strip()


        callback_reference = str(
            callback_reference or ""
        ).strip()


        withdrawal = None


        if transfer_id:

            withdrawal = (

                get_withdrawal_by_transfer_id(
                    transfer_id
                )

            )


        if (

            not withdrawal

            and callback_reference

        ):

            withdrawal = (

                get_withdrawal_by_transfer_reference(
                    callback_reference
                )

            )


        if not withdrawal:

            return jsonify(

                {
                    "status":
                        "accepted"
                }

            ), 202


        local_reference = str(

            withdrawal[
                "transfer_reference"
            ]

            or ""

        ).strip()


        if (

            callback_reference

            and local_reference

            and callback_reference
                != local_reference

        ):

            logger.error(

                "Transfer callback reference mismatch withdrawal=%s",

                withdrawal["id"],

            )


            return jsonify(

                {
                    "status":
                        "accepted"
                }

            ), 202


        if transfer_id:

            verified = (

                get_flutterwave_transfer_status(
                    transfer_id
                )

            )

        else:

            verified = (

                get_flutterwave_transfer_status_by_reference(
                    local_reference
                )

            )


        if not verified:

            return jsonify(

                {
                    "status":
                        "accepted"
                }

            ), 202


        verified_reference = str(

            verified.get(
                "reference"
            )

            or ""

        ).strip()


        if (

            local_reference

            and verified_reference

            and verified_reference
                != local_reference

        ):

            logger.error(

                "Verified transfer reference mismatch withdrawal=%s",

                withdrawal["id"],

            )


            return jsonify(

                {
                    "status":
                        "accepted"
                }

            ), 202


        process_transfer_result(

            withdrawal_id=
                withdrawal["id"],

            flutterwave_status=
                verified.get(
                    "status"
                ),

            transfer_id=

                verified.get(
                    "transfer_id"
                )
                or transfer_id,

            transfer_reference=(

                verified_reference
                or local_reference

            ),

            message=
                verified.get(
                    "message"
                ),

        )


        return jsonify(

            {
                "status":
                    "accepted"
            }

        ), 200


    except Exception:

        logger.exception(
            "Flutterwave transfer callback failed"
        )


        return jsonify(

            {
                "status":
                    "accepted"
            }

        ), 202


# ============================================================
# SECURE REFERRAL ROUTES
# ============================================================

@web_app.route(

    "/referral/login",

    methods=["GET", "POST"],

)
def promoter_login():

    return promoter_login_page()


@web_app.route(

    "/referral/logout",

    methods=["POST"],

)
def promoter_logout():

    return promoter_logout_page()


@web_app.route(

    "/referral/dashboard",

    methods=["GET"],

)
def referral_dashboard():

    return referral_dashboard_by_code(
        None
    )


@web_app.route(

    "/referral/<referral_code>",

    methods=["GET"],

)
def referral_entry(
    referral_code
):

    return redirect(

        url_for(

            "promoter_login",

            ref=referral_code,

        )

    )


@web_app.route(

    "/referral-dashboard",

    methods=["GET"],

)
def old_referral_dashboard():

    return redirect(

        url_for(

            "promoter_login",

            ref=request.args.get(
                "ref",
                "",
            ),

        )

    )


@web_app.route(

    "/referral/withdraw",

    methods=["GET", "POST"],

)
def referral_withdraw():

    return withdrawal_page(

        request.args.get(
            "ref"
        )
        or None

    )


@web_app.route(

    "/referral/withdraw/status/<int:withdrawal_id>",

    methods=["GET"],

)
def withdrawal_status(
    withdrawal_id
):

    return withdrawal_status_page(

        withdrawal_id,

        request.args.get(
            "ref"
        )
        or None,

    )


# ============================================================
# ADMIN REFERRAL ROUTES
# ============================================================

if ADMIN_MODULE_AVAILABLE:

    @web_app.route(

        "/admin/referral",

        methods=["GET"],

    )
    def admin_referral():

        return admin_referral_page()


    @web_app.route(

        "/admin/referral/login",

        methods=["GET", "POST"],

    )
    def admin_referral_login():

        return admin_login_page()


    @web_app.route(

        "/admin/referral/logout",

        methods=["POST"],

    )
    def admin_referral_logout():

        return admin_logout_page()


    @web_app.route(

        "/admin/referral/create-promoter",

        methods=["POST"],

    )
    def admin_create_promoter():

        return create_promoter_page()


    @web_app.route(

        "/admin/referral/withdrawal-status",

        methods=["POST"],

    )
    def admin_withdrawal_status():

        return admin_withdrawal_status_page()


# ============================================================
# WEB SERVER
# ============================================================

def run_web_server():

    print(
        "Starting Flask Web Server..."
    )


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


    step = context.user_data.get(
        "step"
    )


    # ========================================================
    # BOT REGISTRATION
    # ========================================================

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

            "📚 Please type your Course."

        )

        return


    if step == "course":

        context.user_data[
            "course"
        ] = text


        data = {

            "telegram_id":
                update.effective_user.id,

            "username":
                (
                    update.effective_user.username
                    or ""
                ),

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


        full_name = data[
            "full_name"
        ]


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


        context.user_data[
            "step"
        ] = "full_name"


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

            reply_markup=InlineKeyboardMarkup(

                [

                    [

                        InlineKeyboardButton(

                            "💳 OPEN PAYMENT PAGE",

                            url=PUBLIC_PAYMENT_PAGE,

                        )

                    ]

                ]

            ),

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


    # ========================================================
    # ENVIRONMENT CHECK
    # ========================================================

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

        target=run_web_server,

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
            & ~filters.COMMAND,

            menu_handler,

        )

    )


    # ========================================================
    # STARTUP LOG
    # ========================================================

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

        "Telegram Login Domain:",

        RAILWAY_URL,

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
        "Automatic Telegram ID: ENABLED"
    )


    print(

        "Main Group ID:",

        MAIN_GROUP_ID,

    )


    print(
        "================================"
    )


    # ========================================================
    # START BOT
    # ========================================================

    telegram_bot_app.run_polling(

        drop_pending_updates=True,

        close_loop=False,

    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()