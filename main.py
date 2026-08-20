# ==========================================================
# ALHIKAM LEARNING CENTER V2
# main.py
# ==========================================================

import os
import logging
import threading
import subprocess

from flask import (
    Flask,
    request,
    redirect,
    jsonify,
    render_template_string,
)

from payment import (
    PAYMENT_HTML,
    create_flutterwave_payment,
    verify_flutterwave_payment,
)

from registration import (
    registration_page,
)

from database import (
    initialize_database,
    get_promoter_by_referral_code,
    save_payment,
    get_payment_by_tx_ref,
    create_commission,
    commission_exists,
)

from config import (
    APP_URL,
    PAYMENT_PLANS,
)


# ==========================================================
# APP
# ==========================================================

web_app = Flask(__name__)

web_app.secret_key = os.getenv(
    "SECRET_KEY",
    "alhikam-secret-key"
)


# ==========================================================
# DATABASE
# ==========================================================

initialize_database()


# ==========================================================
# LOGGING
# ==========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

logger = logging.getLogger(
    "ALHIKAM"
)


# ==========================================================
# COMMISSION
# ==========================================================

COMMISSION_BY_AMOUNT = {

    3600: 200,

    6800: 500,

    10000: 800,

    13600: 1200,

    16500: 1800,

    20000: 2500,

}


# ==========================================================
# PAYMENT PAGE
# ==========================================================

@web_app.route(
    "/payment",
    methods=["GET"]
)
def payment_page():

    referral_code = request.args.get(
        "ref",
        ""
    ).strip()

    telegram_id = request.args.get(
        "telegram_id",
        ""
    ).strip()

    telegram_name = request.args.get(
        "telegram_name",
        ""
    ).strip()

    telegram_username = request.args.get(
        "telegram_username",
        ""
    ).strip()

    # ------------------------------------------------------
    # Verify referral
    # ------------------------------------------------------

    if referral_code:

        try:

            promoter = (
                get_promoter_by_referral_code(
                    referral_code
                )
            )

        except Exception as e:

            logger.error(
                "Referral lookup error: %s",
                e
            )

            promoter = None

        if not promoter:

            referral_code = ""

    return render_template_string(

        PAYMENT_HTML,

        referral_code=referral_code,

        telegram_id=telegram_id,

        telegram_name=telegram_name,

        telegram_username=telegram_username,

    )


# ==========================================================
# HOME
# ==========================================================

@web_app.route("/")
def home():

    return redirect(
        "/payment"
    )


# ==========================================================
# CREATE PAYMENT
# ==========================================================

@web_app.route(
    "/create-payment",
    methods=["POST"]
)
def create_payment():

    plan_id = request.form.get(
        "plan",
        ""
    ).strip()

    referral_code = request.form.get(
        "referral_code",
        ""
    ).strip()

    telegram_id = request.form.get(
        "telegram_id",
        ""
    ).strip()

    telegram_name = request.form.get(
        "telegram_name",
        ""
    ).strip()

    telegram_username = request.form.get(
        "telegram_username",
        ""
    ).strip()

    # ------------------------------------------------------
    # Plan
    # ------------------------------------------------------

    if plan_id not in PAYMENT_PLANS:

        return (
            "Invalid payment plan.",
            400
        )

    # ------------------------------------------------------
    # Referral
    # ------------------------------------------------------

    promoter = None

    if referral_code:

        try:

            promoter = (
                get_promoter_by_referral_code(
                    referral_code
                )
            )

        except Exception as e:

            logger.error(
                "Referral error: %s",
                e
            )

            promoter = None

        if not promoter:

            referral_code = ""

    # ------------------------------------------------------
    # Flutterwave
    # ------------------------------------------------------

    payment = create_flutterwave_payment(

        plan_id,

        APP_URL,

        referral_code=referral_code,

        telegram_id=telegram_id,

        telegram_name=telegram_name,

        telegram_username=telegram_username,

    )

    if not payment:

        return (
            "Unable to create payment. "
            "Please check Railway logs.",
            500
        )

    tx_ref = payment["tx_ref"]

    amount = float(
        payment["amount"]
    )

    payment_plan = payment["plan"]

    # ------------------------------------------------------
    # Commission
    # ------------------------------------------------------

    commission_amount = (
        COMMISSION_BY_AMOUNT.get(
            int(amount),
            0
        )
    )

    promoter_id = (
        promoter["id"]
        if promoter
        else None
    )

    promoter_name = (
        promoter["full_name"]
        if promoter
        else ""
    )

    # ------------------------------------------------------
    # SAVE PENDING PAYMENT
    # ------------------------------------------------------

    try:

        save_payment({

            "tx_ref":
                tx_ref,

            "transaction_id":
                "",

            "payment_plan":
                payment_plan,

            "amount":
                amount,

            "payment_status":
                "Pending",

            "referral_code":
                referral_code,

            "promoter_id":
                promoter_id,

            "promoter_name":
                promoter_name,

            "commission":
                commission_amount,

            "telegram_id":
                telegram_id,

            "telegram_username":
                telegram_username,

            "telegram_name":
                telegram_name,

        })

    except Exception as e:

        logger.error(
            "Payment save error: %s",
            e
        )

        return (
            "Could not initialize payment.",
            500
        )

    logger.info(

        "PAYMENT CREATED | "
        "TX=%s | "
        "PLAN=%s | "
        "AMOUNT=%s | "
        "REF=%s",

        tx_ref,

        payment_plan,

        amount,

        referral_code

    )

    return redirect(
        payment["payment_link"]
    )


# ==========================================================
# REGISTRATION
# ==========================================================

@web_app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    return registration_page()


# ==========================================================
# PAYMENT CALLBACK
# ==========================================================

@web_app.route(
    "/payment-callback"
)
def payment_callback():

    transaction_id = request.args.get(
        "transaction_id",
        ""
    ).strip()

    if not transaction_id:

        return (
            "Missing transaction_id.",
            400
        )

    # ------------------------------------------------------
    # Verify with Flutterwave
    # ------------------------------------------------------

    payment = verify_flutterwave_payment(
        transaction_id
    )

    if not payment:

        return (
            "Payment verification failed.",
            400
        )

    if payment.get("status") != "successful":

        return (
            "Payment was not successful.",
            400
        )

    tx_ref = (
        payment.get(
            "tx_ref",
            ""
        )
        or ""
    ).strip()

    amount = float(
        payment.get(
            "amount",
            0
        )
        or 0
    )

    currency = payment.get(
        "currency",
        ""
    )

    # ------------------------------------------------------
    # Security
    # ------------------------------------------------------

    if not tx_ref:

        return (
            "Transaction reference missing.",
            400
        )

    if currency != "NGN":

        return (
            "Invalid payment currency.",
            400
        )

    # ------------------------------------------------------
    # Original payment
    # ------------------------------------------------------

    original_payment = (
        get_payment_by_tx_ref(
            tx_ref
        )
    )

    if not original_payment:

        logger.error(
            "Unknown transaction reference: %s",
            tx_ref
        )

        return (
            "Unknown payment reference.",
            400
        )

    expected_amount = float(
        original_payment["amount"]
    )

    if amount != expected_amount:

        logger.error(

            "AMOUNT MISMATCH | "
            "TX=%s | "
            "EXPECTED=%s | "
            "RECEIVED=%s",

            tx_ref,

            expected_amount,

            amount

        )

        return (
            "Payment amount does not match.",
            400
        )

    payment_plan = (
        original_payment["payment_plan"]
        or ""
    )

    referral_code = (
        original_payment["referral_code"]
        or ""
    ).strip()

    promoter_id = (
        original_payment["promoter_id"]
    )

    promoter_name = (
        original_payment["promoter_name"]
        or ""
    )

    commission_amount = float(
        original_payment["commission"]
        or 0
    )

    telegram_id = (
        original_payment["telegram_id"]
        or ""
    )

    telegram_username = (
        original_payment["telegram_username"]
        or ""
    )

    telegram_name = (
        original_payment["telegram_name"]
        or ""
    )

    # ------------------------------------------------------
    # Verify promoter
    # ------------------------------------------------------

    if referral_code:

        promoter = (
            get_promoter_by_referral_code(
                referral_code
            )
        )

        if not promoter:

            referral_code = ""

            promoter_id = None

            promoter_name = ""

            commission_amount = 0

    # ------------------------------------------------------
    # Save successful payment
    # ------------------------------------------------------

    try:

        save_payment({

            "tx_ref":
                tx_ref,

            "transaction_id":
                transaction_id,

            "payment_plan":
                payment_plan,

            "amount":
                amount,

            "payment_status":
                "Successful",

            "referral_code":
                referral_code,

            "promoter_id":
                promoter_id,

            "promoter_name":
                promoter_name,

            "commission":
                commission_amount,

            "telegram_id":
                telegram_id,

            "telegram_username":
                telegram_username,

            "telegram_name":
                telegram_name,

        })

    except Exception as e:

        logger.error(
            "Successful payment save error: %s",
            e
        )

        return (
            "Payment verified but could not be saved.",
            500
        )

    # ------------------------------------------------------
    # Commission
    # ------------------------------------------------------

    if (
        promoter_id
        and
        commission_amount > 0
        and
        not commission_exists(tx_ref)
    ):

        try:

            create_commission(

                promoter_id=promoter_id,

                student_id=None,

                tx_ref=tx_ref,

                payment_amount=amount,

                commission_amount=
                    commission_amount

            )

        except Exception as e:

            logger.error(
                "Commission error: %s",
                e
            )

    # ------------------------------------------------------
    # Registration URL
    # ------------------------------------------------------

    registration_url = (
        f"{APP_URL}/register"
        f"?tx_ref={tx_ref}"
    )

    return redirect(
        registration_url
    )


# ==========================================================
# HEALTH
# ==========================================================

@web_app.route(
    "/health"
)
def health():

    return jsonify({

        "status":
            "healthy",

        "app":
            "ALHIKAM V2"

    })


# ==========================================================
# START TELEGRAM BOT
# ==========================================================

def start_telegram_bot():

    print(
        "STARTING TELEGRAM BOT..."
    )

    try:

        subprocess.Popen(
            [
                "python",
                "bot.py"
            ]
        )

        print(
            "TELEGRAM BOT STARTED."
        )

    except Exception as e:

        logger.error(
            "Telegram bot error: %s",
            e
        )


# ==========================================================
# SERVER
# ==========================================================

if __name__ == "__main__":

    threading.Thread(

        target=start_telegram_bot,

        daemon=True

    ).start()

    PORT = int(
        os.getenv(
            "PORT",
            "8080"
        )
    )

    web_app.run(

        host="0.0.0.0",

        port=PORT

    )