# ==========================================================
# ALHIKAM LEARNING CENTER V2
# main.py
#
# PAYMENT
#   ↓
# REFERRAL
#   ↓
# FLUTTERWAVE PAYMENT
#   ↓
# PAYMENT VERIFICATION
#   ↓
# COMMISSION
#   ↓
# REGISTRATION
#   ↓
# TELEGRAM
#   ↓
# REFERRAL DASHBOARD
#   ↓
# WITHDRAWAL
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
    get_promoter_by_id,
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
    # REFERRAL
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
    # VALIDATE REFERRAL
    # ------------------------------------------------------

    promoter = None

    if referral_code:

        try:

            promoter = get_promoter_by_referral_code(
                referral_code
            )

        except Exception:

            logger.exception(
                "Referral lookup error."
            )

            promoter = None

        if not promoter:

            logger.warning(
                "Invalid referral code: %s",
                referral_code
            )

            referral_code = ""

    # ------------------------------------------------------
    # LOG
    # ------------------------------------------------------

    logger.info(
        "PAYMENT PAGE | TELEGRAM_ID=%s | NAME=%s | "
        "USERNAME=%s | REF=%s",
        telegram_id,
        telegram_name,
        telegram_username,
        referral_code
    )

    # ------------------------------------------------------
    # RENDER
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
    # PLAN
    # ------------------------------------------------------

    plan_id = (
        request.form.get(
            "plan",
            ""
        )
        or ""
    ).strip()

    # ------------------------------------------------------
    # REFERRAL
    # ------------------------------------------------------

    referral_code = (
        request.form.get(
            "referral_code",
            ""
        )
        or ""
    ).strip()

    # ------------------------------------------------------
    # TELEGRAM
    # ------------------------------------------------------

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

    logger.info(
        "CREATE PAYMENT | PLAN=%s | REF=%s | TELEGRAM=%s",
        plan_id,
        referral_code,
        telegram_id
    )

    # ======================================================
    # VALIDATE PLAN
    # ======================================================

    if plan_id not in PAYMENT_PLANS:

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

            promoter = get_promoter_by_referral_code(
                referral_code
            )

        except Exception:

            logger.exception(
                "Referral lookup error."
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

    try:

        payment = create_flutterwave_payment(

            plan_id=plan_id,

            app_url=APP_URL,

            referral_code=referral_code,

            telegram_id=telegram_id,

            telegram_name=telegram_name,

            telegram_username=telegram_username,

        )

    except Exception:

        logger.exception(
            "Flutterwave payment creation error."
        )

        return (
            "Unable to create payment.",
            500
        )

    if not payment:

        logger.error(
            "Flutterwave returned empty payment."
        )

        return (
            "Unable to create payment.",
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

    if not tx_ref:

        logger.error(
            "Flutterwave payment has no tx_ref."
        )

        return (
            "Payment reference could not be created.",
            500
        )

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

    payment_plan = (
        payment.get(
            "plan",
            plan_id
        )
        or plan_id
    ).strip()

    if amount <= 0:

        return (
            "Invalid payment amount.",
            500
        )

    # ======================================================
    # PROMOTER DATA
    # ======================================================

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
    # EXPECTED COMMISSION
    # ======================================================

    commission_amount = COMMISSION_BY_AMOUNT.get(
        int(round(amount)),
        0
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

            "registration_completed": 0,

        })

    except Exception:

        logger.exception(
            "Could not save pending payment."
        )

        return (
            "Could not initialize payment.",
            500
        )

    # ======================================================
    # MEMORY
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
        "PAYMENT CREATED | TX=%s | AMOUNT=%s | REF=%s",
        tx_ref,
        amount,
        referral_code
    )

    # ======================================================
    # REDIRECT
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

    transaction_id = (
        request.args.get(
            "transaction_id",
            ""
        )
        or ""
    ).strip()

    callback_tx_ref = (
        request.args.get(
            "tx_ref",
            ""
        )
        or ""
    ).strip()

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
        "PAYMENT CALLBACK | TRANSACTION=%s | TX=%s",
        transaction_id,
        callback_tx_ref
    )

    # ======================================================
    # TRANSACTION ID
    # ======================================================

    if not transaction_id:

        return (
            "Transaction ID is missing.",
            400
        )

    # ======================================================
    # VERIFY FLUTTERWAVE
    # ======================================================

    try:

        payment = verify_flutterwave_payment(
            transaction_id
        )

    except Exception:

        logger.exception(
            "Flutterwave verification error."
        )

        return (
            "Payment verification failed.",
            400
        )

    if not payment:

        return (
            "Payment verification failed.",
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

        return (
            "Payment was not successful.",
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

        return (
            "Transaction reference missing.",
            400
        )

    # ======================================================
    # GET ORIGINAL PAYMENT
    # ======================================================

    original_payment = get_payment_by_tx_ref(
        tx_ref
    )

    if not original_payment:

        logger.error(
            "Unknown TX_REF: %s",
            tx_ref
        )

        return (
            "Unknown payment reference.",
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

        return (
            "Invalid payment currency.",
            400
        )

    # ======================================================
    # VERIFIED AMOUNT
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
    # COMPARE AMOUNT
    # ======================================================

    expected_amount = float(
        original_payment["amount"]
        or 0
    )

    if abs(
        amount - expected_amount
    ) > 0.01:

        logger.error(
            "AMOUNT MISMATCH | TX=%s | "
            "EXPECTED=%s | RECEIVED=%s",
            tx_ref,
            expected_amount,
            amount
        )

        return (
            "Payment amount does not match.",
            400
        )

    # ======================================================
    # ORIGINAL PAYMENT DATA
    # ======================================================

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

    # ======================================================
    # TELEGRAM
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

    # ======================================================
    # VERIFY PROMOTER AGAIN
    # ======================================================

    promoter = None

    if referral_code:

        try:

            promoter = get_promoter_by_referral_code(
                referral_code
            )

        except Exception:

            logger.exception(
                "Promoter verification error."
            )

            promoter = None

        if not promoter:

            logger.warning(
                "Promoter no longer active: %s",
                referral_code
            )

            referral_code = ""

            promoter_id = None

            promoter_name = ""

            commission_amount = 0

    # ======================================================
    # UPDATE PAYMENT
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

            "registration_completed": 0,

        })

    except Exception:

        logger.exception(
            "Could not save successful payment."
        )

        return (
            "Payment verified but could not be saved.",
            500
        )

    # ======================================================
    # MEMORY
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
        and referral_code
    ):

        if not commission_exists(tx_ref):

            try:

                result = create_commission(

                    promoter_id=promoter_id,

                    student_id=None,

                    tx_ref=tx_ref,

                    payment_amount=amount,

                    commission_amount=commission_amount,

                )

                logger.info(
                    "COMMISSION CREATED | "
                    "PROMOTER=%s | TX=%s | COMMISSION=%s",
                    promoter_name,
                    tx_ref,
                    result["commission_amount"]
                )

            except Exception:

                logger.exception(
                    "Commission creation error."
                )

        else:

            logger.info(
                "Commission already exists | TX=%s",
                tx_ref
            )

    # ======================================================
    # REGISTRATION URL
    # ======================================================

    registration_url = (
        f"{APP_URL}/register?"
        + urlencode({
            "tx_ref": tx_ref
        })
    )

    logger.info(
        "PAYMENT SUCCESSFUL | TX=%s | "
        "AMOUNT=%s | REF=%s | TELEGRAM=%s",
        tx_ref,
        amount,
        referral_code,
        telegram_id
    )

    # ======================================================
    # REDIRECT
    # ======================================================

    return redirect(
        registration_url
    )


# ==========================================================
# REFERRAL DASHBOARD
# ==========================================================

@web_app.route(
    "/referral/dashboard",
    methods=["GET"]
)
def referral_dashboard_route():

    # ------------------------------------------------------
    # Accept promoter_id
    # ------------------------------------------------------

    promoter_id = (
        request.args.get(
            "promoter_id",
            ""
        )
        or ""
    ).strip()

    # ------------------------------------------------------
    # Also accept referral code
    # ------------------------------------------------------

    referral_code = (
        request.args.get(
            "ref",
            ""
        )
        or ""
    ).strip()

    if not promoter_id and referral_code:

        promoter = get_promoter_by_referral_code(
            referral_code
        )

        if not promoter:

            return (
                "Invalid referral code.",
                404
            )

        promoter_id = promoter["id"]

    # ------------------------------------------------------
    # Validate promoter ID
    # ------------------------------------------------------

    if not promoter_id:

        return (
            "Promoter ID or referral code is required.",
            400
        )

    try:

        promoter_id = int(
            promoter_id
        )

    except ValueError:

        return (
            "Invalid promoter ID.",
            400
        )

    # ------------------------------------------------------
    # Import here to avoid circular import
    # ------------------------------------------------------

    from referral_dashboard import (
        referral_dashboard
    )

    return referral_dashboard(
        promoter_id
    )


# ==========================================================
# REFERRAL DASHBOARD BY CODE
# ==========================================================

@web_app.route(
    "/referral/<referral_code>",
    methods=["GET"]
)
def referral_by_code(referral_code):

    referral_code = (
        referral_code
        or ""
    ).strip()

    if not referral_code:

        return (
            "Referral code is required.",
            400
        )

    try:

        promoter = get_promoter_by_referral_code(
            referral_code
        )

    except Exception:

        logger.exception(
            "Referral code lookup error."
        )

        return (
            "Unable to find referral account.",
            500
        )

    if not promoter:

        return (
            "Invalid referral code.",
            404
        )

    from referral_dashboard import (
        referral_dashboard
    )

    return referral_dashboard(
        promoter["id"]
    )


# ==========================================================
# REFERRAL DASHBOARD LOGIN BY CODE
# ==========================================================

@web_app.route(
    "/referral-dashboard",
    methods=["GET"]
)
def referral_dashboard_by_ref():

    referral_code = (
        request.args.get(
            "ref",
            ""
        )
        or ""
    ).strip()

    if not referral_code:

        return (
            """
            <h3>Referral Dashboard</h3>

            <p>
            Please provide your referral code.
            </p>

            <p>
            Example:
            /referral-dashboard?ref=ALHIKAM123
            </p>
            """,
            400
        )

    try:

        promoter = get_promoter_by_referral_code(
            referral_code
        )

    except Exception:

        logger.exception(
            "Referral dashboard lookup error."
        )

        return (
            "Unable to load referral account.",
            500
        )

    if not promoter:

        return (
            "Invalid referral code.",
            404
        )

    from referral_dashboard import (
        referral_dashboard
    )

    return referral_dashboard(
        promoter["id"]
    )


# ==========================================================
# WITHDRAWAL
# ==========================================================

@web_app.route(
    "/referral/withdraw",
    methods=["GET", "POST"]
)
def referral_withdraw():

    # ------------------------------------------------------
    # Get promoter ID
    # ------------------------------------------------------

    promoter_id = (
        request.args.get(
            "promoter_id",
            ""
        )
        or ""
    ).strip()

    # ------------------------------------------------------
    # Allow referral code too
    #
    # Example:
    # /referral/withdraw?ref=ALHIKAM123
    # ------------------------------------------------------

    referral_code = (
        request.args.get(
            "ref",
            ""
        )
        or ""
    ).strip()

    if not promoter_id and referral_code:

        promoter = get_promoter_by_referral_code(
            referral_code
        )

        if not promoter:

            return (
                "Invalid referral code.",
                404
            )

        promoter_id = promoter["id"]

    # ------------------------------------------------------
    # POST can contain promoter ID
    # ------------------------------------------------------

    if request.method == "POST":

        promoter_id = (
            request.form.get(
                "promoter_id",
                promoter_id
            )
            or ""
        ).strip()

        if not promoter_id:

            referral_code = (
                request.form.get(
                    "referral_code",
                    referral_code
                )
                or ""
            ).strip()

            if referral_code:

                promoter = get_promoter_by_referral_code(
                    referral_code
                )

                if promoter:

                    promoter_id = promoter["id"]

    # ------------------------------------------------------
    # Validate promoter
    # ------------------------------------------------------

    if not promoter_id:

        return (
            "Promoter ID or referral code is required.",
            400
        )

    try:

        promoter_id = int(
            promoter_id
        )

    except ValueError:

        return (
            "Invalid promoter ID.",
            400
        )

    # ------------------------------------------------------
    # Import withdrawal page
    # ------------------------------------------------------

    from referral_dashboard import (
        withdrawal_page
    )

    return withdrawal_page(
        promoter_id
    )


# ==========================================================
# HEALTH CHECK
# ==========================================================

@web_app.route(
    "/health",
    methods=["GET"]
)
def health():

    return jsonify({

        "status": "healthy",

        "app": "ALHIKAM V2",

    })


# ==========================================================
# START TELEGRAM BOT
# ==========================================================

def start_telegram_bot():

    logger.info(
        "STARTING TELEGRAM BOT..."
    )

    try:

        subprocess.Popen(
            [
                sys.executable,
                "bot.py"
            ]
        )

        logger.info(
            "TELEGRAM BOT STARTED."
        )

    except Exception:

        logger.exception(
            "Telegram bot could not start."
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

    logger.info(
        "ALHIKAM WEB SERVER STARTING ON PORT %s",
        PORT
    )

    web_app.run(
        host="0.0.0.0",
        port=PORT,
    )