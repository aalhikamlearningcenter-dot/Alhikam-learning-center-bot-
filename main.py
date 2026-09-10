# ============================================================
# ALHIKAM LEARNING CENTER V2
# ============================================================
#
# Main Flask Application
#
# Flutterwave Payment
# Secure Payment Verification
# Telegram Login
# Student Registration
# Google Sheets
# Referral / Commission
# Promoter Dashboard
# Withdrawal
# Admin Referral Dashboard
#
# ============================================================

import os
import sys
import time
import threading
import subprocess
import logging

from flask import (
    Flask,
    request,
    redirect,
    url_for,
    render_template_string,
    jsonify,
    session,
)

# ============================================================
# PROJECT IMPORTS
# ============================================================

from config import (
    APP_URL,
    BOT_TOKEN,
    PAYMENT_PLANS,
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
    get_payment_by_tx_ref,
    save_payment,
    update_payment_status,
    get_promoter_by_referral_code,
    create_commission,
    commission_exists,
)

from referral_dashboard import (
    referral_dashboard_by_code,
    promoter_login_page,
    promoter_logout_page,
    withdrawal_page,
    withdrawal_status_page,
)

from admin_referral import (
    admin_logged_in,
    admin_login_page,
    admin_logout_page,
    admin_referral_page,
    create_promoter_page,
    admin_withdrawal_status_page,
)


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

logger = logging.getLogger(__name__)


# ============================================================
# FLASK APP
# ============================================================

web_app = Flask(__name__)

web_app.secret_key = os.getenv(
    "FLASK_SECRET_KEY",
    os.getenv(
        "SECRET_KEY",
        "ALHIKAM_LEARNING_CENTER_CHANGE_THIS_SECRET_KEY",
    ),
)


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

try:
    initialize_database()
    logger.info("Database initialized successfully.")
except Exception as e:
    logger.exception("Database initialization failed: %s", e)


# ============================================================
# PAYMENT SESSIONS
# ============================================================
#
# This is only a temporary cache.
# The database remains the main source of truth.
#
# ============================================================

PAYMENT_SESSIONS = {}


# ============================================================
# COMMISSION MAP
# ============================================================

COMMISSION_BY_AMOUNT = {
    3600: 200,
    6800: 500,
    10000: 800,
    13600: 1200,
    16500: 1800,
    20000: 2500,
}


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def row_to_dict(row):
    """
    Safely convert sqlite3.Row / dict / object to dict.
    """

    if row is None:
        return None

    if isinstance(row, dict):
        return dict(row)

    try:
        return dict(row)
    except Exception:
        pass

    result = {}

    try:
        for key in row.keys():
            result[key] = row[key]
    except Exception:
        pass

    return result


def get_value(data, key, default=None):
    """
    Safely get a value from dict/sqlite Row.
    """

    if data is None:
        return default

    try:
        value = data[key]
        return default if value is None else value
    except Exception:
        pass

    try:
        value = data.get(key, default)
        return default if value is None else value
    except Exception:
        return default


def normalize_amount(value):
    """
    Convert payment amount safely to integer.
    """

    try:
        return int(round(float(value)))
    except Exception:
        return 0


def get_plan_amount(plan):
    """
    Return the configured amount for a payment plan.
    """

    plan = str(plan)

    if plan not in PAYMENT_PLANS:
        return None

    try:
        return normalize_amount(PAYMENT_PLANS[plan][1])
    except Exception:
        return None


def calculate_commission(amount):
    """
    Calculate promoter commission based on verified amount.
    """

    amount = normalize_amount(amount)

    return COMMISSION_BY_AMOUNT.get(amount, 0)


def safe_redirect(endpoint, **kwargs):
    """
    Redirect safely to a Flask endpoint.
    """

    try:
        return redirect(url_for(endpoint, **kwargs))
    except Exception as e:
        logger.exception(
            "Redirect failed for endpoint %s: %s",
            endpoint,
            e,
        )

        return redirect("/")


# ============================================================
# HOME
# ============================================================

@web_app.route("/", methods=["GET"])
def home():
    return redirect(url_for("payment_page"))


# ============================================================
# PAYMENT PAGE
# ============================================================

@web_app.route("/payment", methods=["GET"])
def payment_page():
    """
    Main payment page.

    Supports:
        /payment
        /payment?ref=ABC123
        /payment?telegram_id=...
    """

    referral_code = (
        request.args.get("ref")
        or request.args.get("referral_code")
        or ""
    ).strip()

    telegram_id = (
        request.args.get("telegram_id")
        or ""
    ).strip()

    telegram_name = (
        request.args.get("telegram_name")
        or ""
    ).strip()

    telegram_username = (
        request.args.get("telegram_username")
        or ""
    ).strip()

    # --------------------------------------------------------
    # Validate referral if supplied
    # --------------------------------------------------------

    if referral_code:

        promoter = get_promoter_by_referral_code(
            referral_code
        )

        if promoter is None:
            referral_code = ""

    # --------------------------------------------------------
    # Render payment page
    # --------------------------------------------------------

    try:
        return render_template_string(
            PAYMENT_HTML,
            referral_code=referral_code,
            telegram_id=telegram_id,
            telegram_name=telegram_name,
            telegram_username=telegram_username,
        )

    except TypeError:
        # Compatibility fallback if PAYMENT_HTML does not
        # expect template variables.
        return render_template_string(
            PAYMENT_HTML
        )


# ============================================================
# /pay
# ============================================================
#
# Admin/referral dashboard creates links like:
#
# https://your-app/pay
# https://your-app/pay?ref=ABC123
#
# Keep /payment as the main route and /pay as an alias.
#
# ============================================================

@web_app.route("/pay", methods=["GET"])
def pay():
    return payment_page()


# ============================================================
# CREATE PAYMENT
# ============================================================

@web_app.route("/create-payment", methods=["POST"])
def create_payment():
    """
    Create Flutterwave payment.

    Important:
    We store the payment in our database BEFORE redirecting
    the student to Flutterwave.
    """

    try:

        # ----------------------------------------------------
        # Get submitted data
        # ----------------------------------------------------

        telegram_id = (
            request.form.get("telegram_id")
            or ""
        ).strip()

        telegram_name = (
            request.form.get("telegram_name")
            or ""
        ).strip()

        telegram_username = (
            request.form.get("telegram_username")
            or ""
        ).strip()

        payment_plan = (
            request.form.get("payment_plan")
            or request.form.get("plan")
            or ""
        ).strip()

        referral_code = (
            request.form.get("referral_code")
            or request.form.get("ref")
            or ""
        ).strip()

        # ----------------------------------------------------
        # Validate plan
        # ----------------------------------------------------

        if payment_plan not in PAYMENT_PLANS:
            return (
                "Invalid payment plan.",
                400,
            )

        plan_amount = get_plan_amount(payment_plan)

        if not plan_amount:
            return (
                "Invalid payment amount.",
                400,
            )

        # ----------------------------------------------------
        # Validate referral
        # ----------------------------------------------------

        promoter_id = None

        if referral_code:

            promoter = get_promoter_by_referral_code(
                referral_code
            )

            if promoter is None:
                return (
                    "Invalid or inactive referral code.",
                    400,
                )

            promoter_dict = row_to_dict(promoter)

            promoter_id = get_value(
                promoter_dict,
                "id",
            )

        # ----------------------------------------------------
        # Create Flutterwave payment
        # ----------------------------------------------------

        payment = create_flutterwave_payment(
            payment_plan=payment_plan,
            telegram_id=telegram_id,
            telegram_name=telegram_name,
            telegram_username=telegram_username,
            referral_code=referral_code,
        )

        if not payment:
            return (
                "Unable to create payment. Please try again.",
                500,
            )

        # ----------------------------------------------------
        # Extract payment information
        # ----------------------------------------------------

        tx_ref = str(
            payment.get("tx_ref")
            or ""
        ).strip()

        amount = normalize_amount(
            payment.get("amount")
        )

        payment_link = (
            payment.get("payment_link")
            or ""
        )

        if not tx_ref or not payment_link:
            logger.error(
                "Flutterwave payment response missing tx_ref/payment_link."
            )

            return (
                "Payment initialization failed.",
                500,
            )

        # ----------------------------------------------------
        # Verify amount against our own plan
        # ----------------------------------------------------

        if amount != plan_amount:

            logger.error(
                "Amount mismatch while creating payment. "
                "Plan=%s Expected=%s Received=%s",
                payment_plan,
                plan_amount,
                amount,
            )

            return (
                "Payment amount validation failed.",
                400,
            )

        # ----------------------------------------------------
        # Save pending payment
        # ----------------------------------------------------

        payment_data = {
            "tx_ref": tx_ref,
            "transaction_id": None,
            "payment_plan": payment_plan,
            "amount": amount,
            "status": "pending",
            "referral_code": referral_code,
            "promoter_id": promoter_id,
            "commission": calculate_commission(amount),
            "telegram_username": telegram_username,
            "telegram_id": telegram_id,
            "registration_completed": 0,
        }

        save_payment(payment_data)

        # ----------------------------------------------------
        # Temporary session cache
        # ----------------------------------------------------

        PAYMENT_SESSIONS[tx_ref] = {
            **payment_data,
            "payment_status": "pending",
        }

        logger.info(
            "Payment created: tx_ref=%s amount=%s plan=%s",
            tx_ref,
            amount,
            payment_plan,
        )

        # ----------------------------------------------------
        # Redirect to Flutterwave checkout
        # ----------------------------------------------------

        return redirect(payment_link)

    except Exception as e:

        logger.exception(
            "CREATE PAYMENT ERROR: %s",
            e,
        )

        return (
            "Unable to start payment. Please try again.",
            500,
        )


# ============================================================
# FLUTTERWAVE PAYMENT CALLBACK
# ============================================================

@web_app.route("/payment-callback", methods=["GET"])
def payment_callback():
    """
    Flutterwave redirects here after payment.

    SECURITY:
    We do NOT trust:
        - amount from URL
        - referral from URL
        - Telegram data from URL

    The original payment record in SQLite is the authority.
    """

    try:

        # ----------------------------------------------------
        # Get Flutterwave transaction ID
        # ----------------------------------------------------

        transaction_id = (
            request.args.get("transaction_id")
            or ""
        ).strip()

        callback_tx_ref = (
            request.args.get("tx_ref")
            or ""
        ).strip()

        # Telegram values are only fallback display/context.
        callback_telegram_id = (
            request.args.get("telegram_id")
            or ""
        ).strip()

        callback_telegram_name = (
            request.args.get("telegram_name")
            or ""
        ).strip()

        callback_telegram_username = (
            request.args.get("telegram_username")
            or ""
        ).strip()

        # ----------------------------------------------------
        # Transaction ID is required
        # ----------------------------------------------------

        if not transaction_id:
            return (
                "Payment verification failed: "
                "missing transaction ID.",
                400,
            )

        # ----------------------------------------------------
        # Verify with Flutterwave
        # ----------------------------------------------------

        verified = verify_flutterwave_payment(
            transaction_id
        )

        if not verified:

            return (
                "Payment verification failed. "
                "Please contact Alhikam Learning Center.",
                400,
            )

        # ----------------------------------------------------
        # Convert response safely
        # ----------------------------------------------------

        verified_dict = row_to_dict(verified) or {}

        verified_status = str(
            get_value(
                verified_dict,
                "status",
                "",
            )
        ).strip().lower()

        # Flutterwave normally returns successful
        if verified_status != "successful":

            logger.warning(
                "Flutterwave payment not successful: %s",
                verified_status,
            )

            return (
                "Payment was not successful.",
                400,
            )

        # ----------------------------------------------------
        # Verified transaction data
        # ----------------------------------------------------

        verified_tx_ref = str(
            get_value(
                verified_dict,
                "tx_ref",
                "",
            )
        ).strip()

        verified_amount = normalize_amount(
            get_value(
                verified_dict,
                "amount",
                0,
            )
        )

        verified_currency = str(
            get_value(
                verified_dict,
                "currency",
                "",
            )
        ).strip().upper()

        # ----------------------------------------------------
        # tx_ref must exist
        # ----------------------------------------------------

        if not verified_tx_ref:

            return (
                "Payment verification failed: "
                "missing transaction reference.",
                400,
            )

        # ----------------------------------------------------
        # If Flutterwave gives tx_ref in callback,
        # it must match verified tx_ref.
        # ----------------------------------------------------

        if callback_tx_ref:

            if callback_tx_ref != verified_tx_ref:

                logger.warning(
                    "Callback tx_ref mismatch: callback=%s verified=%s",
                    callback_tx_ref,
                    verified_tx_ref,
                )

                return (
                    "Payment verification failed: "
                    "transaction reference mismatch.",
                    400,
                )

        tx_ref = verified_tx_ref

        # ----------------------------------------------------
        # Load ORIGINAL payment from database
        # ----------------------------------------------------

        original_payment = get_payment_by_tx_ref(
            tx_ref
        )

        if original_payment is None:

            logger.warning(
                "No original payment found for tx_ref=%s",
                tx_ref,
            )

            return (
                "Payment record not found.",
                404,
            )

        payment = row_to_dict(
            original_payment
        ) or {}

        # ----------------------------------------------------
        # Original amount
        # ----------------------------------------------------

        original_amount = normalize_amount(
            get_value(
                payment,
                "amount",
                0,
            )
        )

        # ----------------------------------------------------
        # Currency validation
        # ----------------------------------------------------

        if verified_currency != "NGN":

            logger.warning(
                "Wrong payment currency: %s",
                verified_currency,
            )

            update_payment_status(
                tx_ref=tx_ref,
                status="failed",
            )

            return (
                "Invalid payment currency.",
                400,
            )

        # ----------------------------------------------------
        # Amount validation
        # ----------------------------------------------------

        if verified_amount != original_amount:

            logger.warning(
                "Payment amount mismatch: tx_ref=%s "
                "original=%s verified=%s",
                tx_ref,
                original_amount,
                verified_amount,
            )

            update_payment_status(
                tx_ref=tx_ref,
                status="failed",
            )

            return (
                "Payment amount does not match the selected plan.",
                400,
            )

        # ----------------------------------------------------
        # Validate configured plan amount too
        # ----------------------------------------------------

        payment_plan = str(
            get_value(
                payment,
                "payment_plan",
                "",
            )
        ).strip()

        expected_plan_amount = get_plan_amount(
            payment_plan
        )

        if expected_plan_amount is None:

            logger.error(
                "Unknown payment plan in DB: %s",
                payment_plan,
            )

            return (
                "Payment plan validation failed.",
                400,
            )

        if original_amount != expected_plan_amount:

            logger.error(
                "Database payment plan amount mismatch: "
                "plan=%s expected=%s db=%s",
                payment_plan,
                expected_plan_amount,
                original_amount,
            )

            return (
                "Payment plan amount validation failed.",
                400,
            )

        # ----------------------------------------------------
        # Get referral information ONLY from original DB
        # ----------------------------------------------------

        referral_code = str(
            get_value(
                payment,
                "referral_code",
                "",
            )
            or ""
        ).strip()

        promoter_id = get_value(
            payment,
            "promoter_id",
            None,
        )

        # ----------------------------------------------------
        # Revalidate promoter
        # ----------------------------------------------------

        if referral_code:

            promoter = get_promoter_by_referral_code(
                referral_code
            )

            if promoter is None:

                logger.warning(
                    "Referral promoter no longer active: %s",
                    referral_code,
                )

                promoter_id = None
                referral_code = ""

            else:

                promoter_dict = row_to_dict(
                    promoter
                ) or {}

                promoter_id = get_value(
                    promoter_dict,
                    "id",
                    promoter_id,
                )

        else:
            promoter_id = None

        # ----------------------------------------------------
        # Calculate commission
        # ----------------------------------------------------

        commission_amount = 0
        commission_rate = 0

        if promoter_id:

            commission_amount = calculate_commission(
                original_amount
            )

            # The current system uses the fixed amount map.
            # Store the effective rate as informational data.
            if original_amount > 0:
                commission_rate = (
                    commission_amount / original_amount
                ) * 100

        # ----------------------------------------------------
        # Save SUCCESSFUL payment
        # ----------------------------------------------------

        save_payment({
            "tx_ref": tx_ref,
            "transaction_id": transaction_id,
            "payment_plan": payment_plan,
            "amount": original_amount,
            "status": "successful",
            "referral_code": referral_code,
            "promoter_id": promoter_id,
            "commission": commission_amount,
            "telegram_username": get_value(
                payment,
                "telegram_username",
                callback_telegram_username,
            ),
            "telegram_id": get_value(
                payment,
                "telegram_id",
                callback_telegram_id,
            ),
            "registration_completed": get_value(
                payment,
                "registration_completed",
                0,
            ),
        })

        # ----------------------------------------------------
        # Update status explicitly
        # ----------------------------------------------------

        update_payment_status(
            tx_ref=tx_ref,
            status="successful",
            transaction_id=transaction_id,
        )

        # ----------------------------------------------------
        # Temporary cache
        # ----------------------------------------------------

        PAYMENT_SESSIONS[tx_ref] = {
            **payment,
            "tx_ref": tx_ref,
            "transaction_id": transaction_id,
            "amount": original_amount,
            "payment_status": "successful",
            "status": "successful",
            "referral_code": referral_code,
            "promoter_id": promoter_id,
            "commission": commission_amount,
            "telegram_id": get_value(
                payment,
                "telegram_id",
                callback_telegram_id,
            ),
            "telegram_username": get_value(
                payment,
                "telegram_username",
                callback_telegram_username,
            ),
            "telegram_name": callback_telegram_name,
        }

        # ----------------------------------------------------
        # Create commission ONCE
        # ----------------------------------------------------
        #
        # We keep the existing architecture:
        # commission is created after VERIFIED payment.
        #
        # commission_exists protects against duplicate callbacks.
        #
        # ----------------------------------------------------

        if promoter_id and commission_amount > 0:

            try:

                already_exists = commission_exists(
                    tx_ref
                )

                if not already_exists:

                    create_commission(
                        tx_ref=tx_ref,
                        promoter_id=promoter_id,
                        student_id=None,
                        payment_amount=original_amount,
                        commission_rate=commission_rate,
                        commission_amount=commission_amount,
                    )

                    logger.info(
                        "Commission created: tx_ref=%s promoter=%s amount=%s",
                        tx_ref,
                        promoter_id,
                        commission_amount,
                    )

                else:

                    logger.info(
                        "Commission already exists: tx_ref=%s",
                        tx_ref,
                    )

            except Exception as commission_error:

                # Do NOT mark the payment as failed just because
                # commission creation has a separate problem.
                logger.exception(
                    "Commission creation error for %s: %s",
                    tx_ref,
                    commission_error,
                )

        # ----------------------------------------------------
        # Payment successful -> registration
        # ----------------------------------------------------

        return redirect(
            url_for(
                "register",
                tx_ref=tx_ref,
            )
        )

    except Exception as e:

        logger.exception(
            "PAYMENT CALLBACK ERROR: %s",
            e,
        )

        return (
            "An error occurred while verifying your payment. "
            "Please contact Alhikam Learning Center.",
            500,
        )


# ============================================================
# REGISTRATION
# ============================================================

@web_app.route("/register", methods=["GET", "POST"])
def register():
    """
    Student registration after successful payment.

    registration.py expects a dictionary-like payment object
    and uses payment_status, while database.py uses status.
    We provide both for compatibility.
    """

    try:

        # ----------------------------------------------------
        # tx_ref can come from:
        #   GET ?tx_ref=
        #   POST form
        # ----------------------------------------------------

        tx_ref = (
            request.args.get("tx_ref")
            or request.form.get("tx_ref")
            or ""
        ).strip()

        if not tx_ref:

            return (
                "Missing payment reference.",
                400,
            )

        # ----------------------------------------------------
        # Always use database payment
        # ----------------------------------------------------

        db_payment = get_payment_by_tx_ref(
            tx_ref
        )

        if db_payment is None:

            return (
                "Payment record not found.",
                404,
            )

        payment = row_to_dict(
            db_payment
        ) or {}

        # ----------------------------------------------------
        # Compatibility fields
        # ----------------------------------------------------

        payment["tx_ref"] = tx_ref

        payment["status"] = str(
            payment.get(
                "status",
                "",
            )
            or ""
        ).lower()

        payment["payment_status"] = (
            "Successful"
            if payment["status"] == "successful"
            else payment["status"]
        )

        # ----------------------------------------------------
        # Registration must only happen after success
        # ----------------------------------------------------

        if payment["status"] != "successful":

            return (
                "This payment has not been successfully verified.",
                403,
            )

        # ----------------------------------------------------
        # Make sure the temporary session has the latest DB data
        # ----------------------------------------------------

        PAYMENT_SESSIONS[tx_ref] = payment

        # ----------------------------------------------------
        # registration.py expects:
        #
        # payment_sessions[tx_ref]
        #
        # ----------------------------------------------------

        return registration_page(
            payment_sessions={
                tx_ref: payment
            }
        )

    except Exception as e:

        logger.exception(
            "REGISTRATION ERROR: %s",
            e,
        )

        return (
            "Unable to open registration page. "
            "Please contact Alhikam Learning Center.",
            500,
        )


# ============================================================
# PROMOTER LOGIN
# ============================================================

@web_app.route(
    "/referral/login",
    methods=["GET", "POST"],
)
def promoter_login():
    return promoter_login_page()


# ============================================================
# PROMOTER LOGOUT
# ============================================================

@web_app.route(
    "/referral/logout",
    methods=["GET", "POST"],
)
def promoter_logout():
    return promoter_logout_page()


# ============================================================
# PROMOTER DASHBOARD
# ============================================================

@web_app.route(
    "/referral/dashboard",
    methods=["GET"],
)
def referral_dashboard():
    """
    Session-based promoter dashboard.

    referral_dashboard.py handles promoter authentication.
    """

    return referral_dashboard_by_code(
        None
    )


# ============================================================
# PROMOTER REFERRAL DASHBOARD LINK
# ============================================================

@web_app.route(
    "/referral/<referral_code>",
    methods=["GET"],
)
def referral_by_code(referral_code):
    """
    Promoter-specific dashboard/referral URL.

    Example:
        /referral/ALC123
    """

    referral_code = (
        referral_code or ""
    ).strip()

    if not referral_code:

        return redirect(
            url_for("promoter_login")
        )

    promoter = get_promoter_by_referral_code(
        referral_code
    )

    if promoter is None:

        return (
            "Invalid or inactive referral code.",
            404,
        )

    return referral_dashboard_by_code(
        referral_code
    )


# ============================================================
# LEGACY PROMOTER DASHBOARD URL
# ============================================================

@web_app.route(
    "/referral-dashboard",
    methods=["GET"],
)
def referral_dashboard_legacy():

    return referral_dashboard_by_code(
        None
    )


# ============================================================
# PROMOTER WITHDRAWAL
# ============================================================

@web_app.route(
    "/referral/withdraw",
    methods=["POST"],
)
def referral_withdraw():

    # withdrawal_page() already checks:
    # - promoter login
    # - CSRF
    # - balance
    # - withdrawal code
    # - bank
    # - transfer
    # etc.

    return withdrawal_page()


# ============================================================
# PROMOTER WITHDRAWAL STATUS
# ============================================================

@web_app.route(
    "/referral/withdraw/status/<int:withdrawal_id>",
    methods=["GET", "POST"],
)
def promoter_withdrawal_status(
    withdrawal_id
):

    return withdrawal_status_page(
        withdrawal_id
    )


# ============================================================
# ADMIN REFERRAL LOGIN
# ============================================================
#
# IMPORTANT:
# admin_referral.py expects endpoint:
#
#     admin_referral_login
#
# and after successful login it redirects to:
#
#     admin_referral
#
# ============================================================

@web_app.route(
    "/admin/referral/login",
    methods=["GET", "POST"],
)
def admin_referral_login():

    return admin_login_page()


# ============================================================
# ADMIN REFERRAL DASHBOARD
# ============================================================

@web_app.route(
    "/admin/referral",
    methods=["GET"],
)
def admin_referral():

    try:

        if not admin_logged_in():

            return redirect(
                url_for(
                    "admin_referral_login"
                )
            )

        return admin_referral_page()

    except Exception as e:

        logger.exception(
            "ADMIN REFERRAL DASHBOARD ERROR: %s",
            e,
        )

        return (
            "Admin referral dashboard error.",
            500,
        )


# ============================================================
# ADMIN LOGOUT
# ============================================================

@web_app.route(
    "/admin/referral/logout",
    methods=["GET", "POST"],
)
def admin_referral_logout():

    return admin_logout_page()


# ============================================================
# ADMIN CREATE PROMOTER
# ============================================================

@web_app.route(
    "/admin/referral/create-promoter",
    methods=["POST"],
)
def admin_create_promoter():

    return create_promoter_page()


# ============================================================
# ADMIN WITHDRAWAL STATUS
# ============================================================

@web_app.route(
    "/admin/referral/withdrawal-status/<int:withdrawal_id>",
    methods=["GET", "POST"],
)
def admin_withdrawal_status(
    withdrawal_id
):

    return admin_withdrawal_status_page(
        withdrawal_id
    )


# ============================================================
# HEALTH CHECK
# ============================================================

@web_app.route(
    "/health",
    methods=["GET"],
)
def health():

    return jsonify({
        "status": "ok",
        "service": "ALHIKAM LEARNING CENTER V2",
    })


# ============================================================
# CHECK IP
# ============================================================

@web_app.route(
    "/check-ip",
    methods=["GET"],
)
def check_ip():

    forwarded_for = (
        request.headers.get(
            "X-Forwarded-For"
        )
        or ""
    )

    real_ip = (
        request.headers.get(
            "X-Real-IP"
        )
        or ""
    )

    remote_addr = (
        request.remote_addr
        or ""
    )

    return jsonify({
        "remote_addr": remote_addr,
        "real_ip": real_ip,
        "x_forwarded_for": forwarded_for,
    })


# ============================================================
# BOT STARTER
# ============================================================

def start_telegram_bot():
    """
    Start bot.py as a background process.

    The bot remains separate from Flask.
    """

    if not BOT_TOKEN:

        logger.warning(
            "BOT_TOKEN is not configured. Telegram bot will not start."
        )

        return

    try:

        bot_file = os.path.join(
            os.path.dirname(
                os.path.abspath(__file__)
            ),
            "bot.py",
        )

        if not os.path.exists(bot_file):

            logger.warning(
                "bot.py was not found: %s",
                bot_file,
            )

            return

        logger.info(
            "Starting Telegram bot..."
        )

        subprocess.Popen(
            [
                sys.executable,
                bot_file,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
        )

        logger.info(
            "Telegram bot process started."
        )

    except Exception as e:

        logger.exception(
            "Unable to start Telegram bot: %s",
            e,
        )


# ============================================================
# BOT THREAD
# ============================================================

def launch_bot_once():

    try:

        # Small delay allows Flask/Railway service
        # to finish starting.
        time.sleep(3)

        start_telegram_bot()

    except Exception as e:

        logger.exception(
            "Bot launcher error: %s",
            e,
        )


# ============================================================
# START APPLICATION
# ============================================================

if __name__ == "__main__":

    logger.info(
        "Starting ALHIKAM LEARNING CENTER V2..."
    )

    # --------------------------------------------------------
    # Start Telegram bot in background
    # --------------------------------------------------------

    bot_thread = threading.Thread(
        target=launch_bot_once,
        daemon=True,
    )

    bot_thread.start()

    # --------------------------------------------------------
    # Railway provides PORT automatically
    # --------------------------------------------------------

    port = int(
        os.getenv(
            "PORT",
            "5000",
        )
    )

    host = "0.0.0.0"

    logger.info(
        "Flask server starting on %s:%s",
        host,
        port,
    )

    web_app.run(
        host=host,
        port=port,
        debug=False,
        use_reloader=False,
    )