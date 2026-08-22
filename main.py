# ==========================================================
# ALHIKAM LEARNING CENTER V2
# main.py
# PAYMENT + REGISTRATION + REFERRAL + TELEGRAM
# ==========================================================

import os
import logging
import threading
import subprocess
import sys

from urllib.parse import urlencode

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

from registration import registration_page

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
# FLASK APP
# ==========================================================

web_app = Flask(__name__)

web_app.secret_key = os.getenv(
    "SECRET_KEY",
    "alhikam-secret-key"
)


# ==========================================================
# LOGGING
# ==========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

logger = logging.getLogger("ALHIKAM")


# ==========================================================
# DATABASE
# ==========================================================

initialize_database()


# ==========================================================
# COMMISSION RULES
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
# PAYMENT MEMORY
# ==========================================================

PAYMENT_SESSIONS = {}


# ==========================================================
# HOME
# ==========================================================

@web_app.route("/")
def home():

    return redirect("/payment")


# ==========================================================
# PAYMENT PAGE
# ==========================================================

@web_app.route(
    "/payment",
    methods=["GET"]
)
def payment_page():

    # ------------------------------------------------------
    # Telegram information
    # ------------------------------------------------------

    telegram_id = (
        request.args.get(
            "telegram_id",
            ""
        )
        or ""
    ).strip()

    telegram_name = (
        request.args.get(
            "telegram_name",
            ""
        )
        or ""
    ).strip()

    telegram_username = (
        request.args.get(
            "telegram_username",
            ""
        )
        or ""
    ).strip()


    # ------------------------------------------------------
    # LOG TELEGRAM DATA
    # ------------------------------------------------------

    logger.info(
        "PAYMENT PAGE | TELEGRAM_ID=%s | NAME=%s | USERNAME=%s",
        telegram_id,
        telegram_name,
        telegram_username
    )


    # ------------------------------------------------------
    # Referral
    # ------------------------------------------------------

    referral_code = (
        request.args.get(
            "ref",
            ""
        )
        or ""
    ).strip()


    if not referral_code:

        referral_code = (
            request.args.get(
                "referral_code",
                ""
            )
            or ""
        ).strip()


    # ------------------------------------------------------
    # Validate referral
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

            logger.warning(
                "Invalid referral code on payment page: %s",
                referral_code
            )

            referral_code = ""


    # ------------------------------------------------------
    # Render payment page
    # ------------------------------------------------------

    return render_template_string(

        PAYMENT_HTML,

        telegram_id=telegram_id,

        telegram_name=telegram_name,

        telegram_username=telegram_username,

        referral_code=referral_code,

    )


# ==========================================================
# CREATE PAYMENT
# ==========================================================

@web_app.route(
    "/create-payment",
    methods=["POST"]
)
def create_payment():

    # ------------------------------------------------------
    # Get form data
    # ------------------------------------------------------

    plan_id = (
        request.form.get(
            "plan",
            ""
        )
        or ""
    ).strip()


    referral_code = (
        request.form.get(
            "referral_code",
            ""
        )
        or ""
    ).strip()


    telegram_id = (
        request.form.get(
            "telegram_id",
            ""
        )
        or ""
    ).strip()


    telegram_name = (
        request.form.get(
            "telegram_name",
            ""
        )
        or ""
    ).strip()


    telegram_username = (
        request.form.get(
            "telegram_username",
            ""
        )
        or ""
    ).strip()


    # ------------------------------------------------------
    # Log payment request
    # ------------------------------------------------------

    logger.info(
        "CREATE PAYMENT | PLAN=%s | TELEGRAM_ID=%s | NAME=%s | USERNAME=%s | REF=%s",
        plan_id,
        telegram_id,
        telegram_name,
        telegram_username,
        referral_code
    )


    # ======================================================
    # VALIDATE PLAN
    # ======================================================

    if plan_id not in PAYMENT_PLANS:

        logger.warning(
            "Invalid payment plan: %s",
            plan_id
        )

        return (
            "Invalid payment plan.",
            400
        )


    # ======================================================
    # VALIDATE REFERRAL
    # ======================================================

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
                "Referral lookup error: %s",
                e
            )

            promoter = None


        if not promoter:

            logger.warning(
                "Invalid referral code: %s",
                referral_code
            )

            referral_code = ""


    # ======================================================
    # CREATE FLUTTERWAVE PAYMENT
    # ======================================================

    payment = create_flutterwave_payment(

        plan_id=plan_id,

        app_url=APP_URL,

        referral_code=referral_code,

        telegram_id=telegram_id,

        telegram_name=telegram_name,

        telegram_username=telegram_username,

    )


    if not payment:

        logger.error(
            "Flutterwave payment creation failed."
        )

        return (
            """
            <h3>
            Unable to create payment.
            </h3>

            <p>
            Please try again.
            </p>
            """,
            500
        )


    # ======================================================
    # PAYMENT DATA
    # ======================================================

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


    payment_plan = (
        payment.get(
            "plan",
            ""
        )
        or ""
    )


    # ======================================================
    # COMMISSION
    # ======================================================

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


    # ======================================================
    # SAVE PENDING PAYMENT
    # ======================================================

    try:

        save_payment({

            "tx_ref": tx_ref,

            "transaction_id": "",

            "payment_plan": payment_plan,

            "amount": amount,

            "payment_status": "Pending",

            "referral_code": referral_code,

            "promoter_id": promoter_id,

            "promoter_name": promoter_name,

            "commission": commission_amount,

            "telegram_id": telegram_id,

            "telegram_username": telegram_username,

            "telegram_name": telegram_name,

        })

    except Exception as e:

        logger.exception(
            "Could not save pending payment."
        )

        return (
            "Could not initialize payment.",
            500
        )


    # ======================================================
    # MEMORY CACHE
    # ======================================================

    PAYMENT_SESSIONS[tx_ref] = {

        "tx_ref": tx_ref,

        "transaction_id": "",

        "amount": amount,

        "payment_plan": payment_plan,

        "payment_status": "Pending",

        "referral_code": referral_code,

        "promoter_id": promoter_id,

        "promoter_name": promoter_name,

        "commission": commission_amount,

        "telegram_id": telegram_id,

        "telegram_username": telegram_username,

        "telegram_name": telegram_name,

        "registration_completed": 0,

    }


    logger.info(
        "PAYMENT CREATED | TX=%s | PLAN=%s | AMOUNT=%s | REF=%s | TELEGRAM=%s",
        tx_ref,
        payment_plan,
        amount,
        referral_code,
        telegram_id
    )


    # ======================================================
    # REDIRECT TO FLUTTERWAVE
    # ======================================================

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

    return registration_page(
        payment_sessions=PAYMENT_SESSIONS
    )


# ==========================================================
# PAYMENT CALLBACK
# ==========================================================

@web_app.route(
    "/payment-callback",
    methods=["GET"]
)
def payment_callback():

    # ------------------------------------------------------
    # Flutterwave transaction ID
    # ------------------------------------------------------

    transaction_id = (
        request.args.get(
            "transaction_id",
            ""
        )
        or ""
    ).strip()


    # ------------------------------------------------------
    # tx_ref backup
    # ------------------------------------------------------

    callback_tx_ref = (
        request.args.get(
            "tx_ref",
            ""
        )
        or ""
    ).strip()


    # ------------------------------------------------------
    # Telegram backup
    # ------------------------------------------------------

    callback_telegram_id = (
        request.args.get(
            "telegram_id",
            ""
        )
        or ""
    ).strip()


    callback_telegram_name = (
        request.args.get(
            "telegram_name",
            ""
        )
        or ""
    ).strip()


    callback_telegram_username = (
        request.args.get(
            "telegram_username",
            ""
        )
        or ""
    ).strip()


    logger.info(
        "PAYMENT CALLBACK | TRANSACTION_ID=%s | TX_REF=%s | TELEGRAM_ID=%s",
        transaction_id,
        callback_tx_ref,
        callback_telegram_id
    )


    # ======================================================
    # TRANSACTION ID REQUIRED
    # ======================================================

    if not transaction_id:

        logger.error(
            "Payment callback missing transaction_id."
        )

        return (
            """
            <h3>
            Payment verification could not start.
            </h3>

            <p>
            Transaction ID is missing.
            </p>
            """,
            400
        )


    # ======================================================
    # VERIFY WITH FLUTTERWAVE
    # ======================================================

    payment = verify_flutterwave_payment(
        transaction_id
    )


    if not payment:

        logger.error(
            "Flutterwave verification failed."
        )

        return (
            """
            <h3>
            Payment verification failed.
            </h3>

            <p>
            Please contact ALHIKAM support.
            </p>
            """,
            400
        )


    # ======================================================
    # PAYMENT STATUS
    # ======================================================

    payment_status = (
        payment.get(
            "status",
            ""
        )
        or ""
    ).lower().strip()


    if payment_status != "successful":

        logger.warning(
            "Payment not successful: %s",
            payment_status
        )

        return (
            """
            <h3>
            Payment was not successful.
            </h3>

            <p>
            Please try again.
            </p>
            """,
            400
        )


    # ======================================================
    # VERIFIED TX REF
    # ======================================================

    tx_ref = (
        payment.get(
            "tx_ref",
            ""
        )
        or ""
    ).strip()


    if not tx_ref:

        tx_ref = callback_tx_ref


    if not tx_ref:

        logger.error(
            "Verified payment has no tx_ref."
        )

        return (
            "Transaction reference missing.",
            400
        )


    # ======================================================
    # CURRENCY
    # ======================================================

    currency = (
        payment.get(
            "currency",
            ""
        )
        or ""
    ).upper().strip()


    if currency != "NGN":

        logger.error(
            "Invalid currency: %s",
            currency
        )

        return (
            "Invalid payment currency.",
            400
        )


    # ======================================================
    # AMOUNT
    # ======================================================

    try:

        amount = float(
            payment.get(
                "amount",
                0
            )
            or 0
        )

    except Exception:

        amount = 0


    if amount <= 0:

        return (
            "Invalid payment amount.",
            400
        )


    # ======================================================
    # GET ORIGINAL PAYMENT
    # ======================================================

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
            """
            <h3>
            Unknown payment reference.
            </h3>

            <p>
            Please contact ALHIKAM support.
            </p>
            """,
            400
        )


    # ======================================================
    # CHECK ORIGINAL AMOUNT
    # ======================================================

    expected_amount = float(
        original_payment["amount"]
        or 0
    )


    if abs(
        amount - expected_amount
    ) > 0.01:

        logger.error(
            "AMOUNT MISMATCH | TX=%s | EXPECTED=%s | RECEIVED=%s",
            tx_ref,
            expected_amount,
            amount
        )

        return (
            "Payment amount does not match.",
            400
        )


    # ======================================================
    # ORIGINAL PAYMENT PLAN
    # ======================================================

    payment_plan = (
        original_payment["payment_plan"]
        or ""
    )


    # ======================================================
    # ORIGINAL REFERRAL
    # ======================================================

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


    # ======================================================
    # TELEGRAM DATA
    #
    # Priority:
    # 1. Original payment database
    # 2. Callback values
    # ======================================================

    telegram_id = (
        original_payment["telegram_id"]
        or callback_telegram_id
        or ""
    )


    telegram_name = (
        original_payment["telegram_name"]
        or callback_telegram_name
        or ""
    )


    telegram_username = (
        original_payment["telegram_username"]
        or callback_telegram_username
        or ""
    )


    telegram_id = str(
        telegram_id
    ).strip()


    telegram_name = str(
        telegram_name
    ).strip()


    telegram_username = str(
        telegram_username
    ).strip()


    logger.info(
        "VERIFIED PAYMENT TELEGRAM | ID=%s | NAME=%s | USERNAME=%s",
        telegram_id,
        telegram_name,
        telegram_username
    )


    # ======================================================
    # VERIFY PROMOTER AGAIN
    # ======================================================

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
                "Promoter verification error: %s",
                e
            )

            promoter = None


        if not promoter:

            logger.warning(
                "Referral promoter no longer valid: %s",
                referral_code
            )

            referral_code = ""

            promoter_id = None

            promoter_name = ""

            commission_amount = 0


    # ======================================================
    # SAVE SUCCESSFUL PAYMENT
    # ======================================================

    try:

        save_payment({

            "tx_ref": tx_ref,

            "transaction_id": transaction_id,

            "payment_plan": payment_plan,

            "amount": amount,

            "payment_status": "Successful",

            "referral_code": referral_code,

            "promoter_id": promoter_id,

            "promoter_name": promoter_name,

            "commission": commission_amount,

            "telegram_id": telegram_id,

            "telegram_username": telegram_username,

            "telegram_name": telegram_name,

        })

    except Exception as e:

        logger.exception(
            "Payment update error."
        )

        return (
            """
            <h3>
            Payment verified but could not be saved.
            </h3>

            <p>
            Please contact ALHIKAM support.
            </p>
            """,
            500
        )


    # ======================================================
    # UPDATE MEMORY
    # ======================================================

    PAYMENT_SESSIONS[tx_ref] = {

        "tx_ref": tx_ref,

        "transaction_id": transaction_id,

        "amount": amount,

        "payment_plan": payment_plan,

        "payment_status": "Successful",

        "referral_code": referral_code,

        "promoter_id": promoter_id,

        "promoter_name": promoter_name,

        "commission": commission_amount,

        "telegram_id": telegram_id,

        "telegram_username": telegram_username,

        "telegram_name": telegram_name,

        "registration_completed": 0,

    }


    # ======================================================
    # CREATE COMMISSION
    # ======================================================

    if (
        promoter_id
        and commission_amount > 0
    ):

        if not commission_exists(
            tx_ref
        ):

            try:

                result = create_commission(

                    promoter_id=promoter_id,

                    student_id=None,

                    tx_ref=tx_ref,

                    payment_amount=amount,

                    commission_amount=commission_amount,

                )


                logger.info(
                    "COMMISSION CREATED | PROMOTER=%s | AMOUNT=%s | COMMISSION=%s",
                    promoter_name,
                    amount,
                    result["commission_amount"]
                )


            except Exception:

                logger.exception(
                    "Commission creation error."
                )

        else:

            logger.info(
                "Commission already exists for TX=%s",
                tx_ref
            )


    # ======================================================
    # REGISTRATION URL
    # ======================================================

    registration_params = urlencode({
        "tx_ref": tx_ref,
    })


    registration_url = (
        f"{APP_URL}/register?{registration_params}"
    )


    logger.info(
        "PAYMENT SUCCESSFUL | TX=%s | AMOUNT=%s | TELEGRAM=%s | REF=%s",
        tx_ref,
        amount,
        telegram_id,
        referral_code
    )


    # ======================================================
    # REDIRECT TO REGISTRATION
    # ======================================================

    return redirect(
        registration_url
    )


# ==========================================================
# HEALTH CHECK
# ==========================================================

@web_app.route("/health")
def health():

    return jsonify({

        "status": "healthy",

        "app": "ALHIKAM V2",

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
                sys.executable,
                "bot.py"
            ]
        )

        print(
            "TELEGRAM BOT STARTED."
        )

    except Exception:

        logger.exception(
            "Telegram bot error."
        )


# ==========================================================
# START SERVER
# ==========================================================

if __name__ == "__main__":

    # ------------------------------------------------------
    # Start Telegram bot
    # ------------------------------------------------------

    threading.Thread(
        target=start_telegram_bot,
        daemon=True
    ).start()


    # ------------------------------------------------------
    # Railway PORT
    # ------------------------------------------------------

    PORT = int(
        os.getenv(
            "PORT",
            "8080"
        )
    )


    print(
        f"ALHIKAM WEB SERVER STARTING ON PORT {PORT}"
    )


    web_app.run(
        host="0.0.0.0",
        port=PORT,
    )