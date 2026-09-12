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
# Student Details
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
    admin_student_details_page,
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

    logger.info(
        "Database initialized successfully."
    )

except Exception as e:

    logger.exception(
        "Database initialization failed: %s",
        e,
    )

# ============================================================
# PAYMENT SESSIONS
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
    Safely convert sqlite3.Row / dict to dict.
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


def get_value(
    data,
    key,
    default=None,
):
    """
    Safely get a value from dict/sqlite Row.
    """

    if data is None:
        return default

    try:

        value = data[key]

        if value is None:
            return default

        return value

    except Exception:
        pass

    try:

        value = data.get(
            key,
            default,
        )

        if value is None:
            return default

        return value

    except Exception:
        return default


def normalize_amount(value):
    """
    Convert payment amount safely to integer.
    """

    try:

        return int(
            round(
                float(value)
            )
        )

    except Exception:

        return 0


def get_plan_amount(plan):
    """
    Return configured amount for payment plan.
    """

    plan = str(plan)

    if plan not in PAYMENT_PLANS:
        return None

    try:

        return normalize_amount(
            PAYMENT_PLANS[plan][1]
        )

    except Exception:

        return None


def calculate_commission(amount):
    """
    Calculate promoter commission
    from verified payment amount.
    """

    amount = normalize_amount(
        amount
    )

    return COMMISSION_BY_AMOUNT.get(
        amount,
        0,
    )


# ============================================================
# HOME
# ============================================================

@web_app.route(
    "/",
    methods=["GET"],
)
def home():

    return redirect(
        url_for(
            "payment_page"
        )
    )


# ============================================================
# PAYMENT PAGE
# ============================================================

@web_app.route(
    "/payment",
    methods=["GET"],
)
def payment_page():

    referral_code = (
        request.args.get("ref")
        or request.args.get(
            "referral_code"
        )
        or ""
    ).strip()

    telegram_id = (
        request.args.get(
            "telegram_id"
        )
        or ""
    ).strip()

    telegram_name = (
        request.args.get(
            "telegram_name"
        )
        or ""
    ).strip()

    telegram_username = (
        request.args.get(
            "telegram_username"
        )
        or ""
    ).strip()

    if referral_code:

        promoter = (
            get_promoter_by_referral_code(
                referral_code
            )
        )

        if promoter is None:

            referral_code = ""

    return render_template_string(
        PAYMENT_HTML,
        referral_code=referral_code,
        telegram_id=telegram_id,
        telegram_name=telegram_name,
        telegram_username=telegram_username,
    )


# ============================================================
# /pay ALIAS
# ============================================================

@web_app.route(
    "/pay",
    methods=["GET"],
)
def pay():

    return payment_page()


# ============================================================
# CREATE PAYMENT
# ============================================================

@web_app.route(
    "/create-payment",
    methods=["POST"],
)
def create_payment():

    try:

        telegram_id = (
            request.form.get(
                "telegram_id"
            )
            or ""
        ).strip()

        telegram_name = (
            request.form.get(
                "telegram_name"
            )
            or ""
        ).strip()

        telegram_username = (
            request.form.get(
                "telegram_username"
            )
            or ""
        ).strip()

        payment_plan = (
            request.form.get(
                "plan"
            )
            or request.form.get(
                "payment_plan"
            )
            or ""
        ).strip()

        referral_code = (
            request.form.get(
                "referral_code"
            )
            or request.form.get(
                "ref"
            )
            or ""
        ).strip()

        logger.info(
            "CREATE PAYMENT REQUEST: "
            "plan=%s referral=%s telegram_id=%s",
            payment_plan,
            referral_code,
            telegram_id,
        )

        if payment_plan not in PAYMENT_PLANS:

            logger.warning(
                "Invalid payment plan received: %s",
                payment_plan,
            )

            return (
                "Invalid payment plan.",
                400,
            )

        plan_amount = get_plan_amount(
            payment_plan
        )

        if not plan_amount:

            logger.error(
                "Could not determine amount for plan=%s",
                payment_plan,
            )

            return (
                "Invalid payment amount.",
                400,
            )

        # ----------------------------------------------------
        # FIND PROMOTER
        # ----------------------------------------------------

        promoter_id = None

        if referral_code:

            promoter = (
                get_promoter_by_referral_code(
                    referral_code
                )
            )

            if promoter is None:

                return (
                    "Invalid or inactive referral code.",
                    400,
                )

            promoter_dict = (
                row_to_dict(
                    promoter
                )
                or {}
            )

            promoter_id = get_value(
                promoter_dict,
                "id",
                None,
            )

        # ----------------------------------------------------
        # CREATE FLUTTERWAVE PAYMENT
        # ----------------------------------------------------

        payment = create_flutterwave_payment(
            plan_id=payment_plan,
            app_url=APP_URL,
            referral_code=referral_code,
            telegram_id=telegram_id,
            telegram_name=telegram_name,
            telegram_username=telegram_username,
        )

        if not payment:

            logger.error(
                "Flutterwave payment creation returned None."
            )

            return (
                "Unable to create payment. "
                "Please try again.",
                500,
            )

        tx_ref = str(
            payment.get(
                "tx_ref"
            )
            or ""
        ).strip()

        amount = normalize_amount(
            payment.get(
                "amount"
            )
        )

        payment_link = str(
            payment.get(
                "payment_link"
            )
            or ""
        ).strip()

        payment_plan_name = str(
            payment.get(
                "plan"
            )
            or PAYMENT_PLANS[
                payment_plan
            ][0]
        ).strip()

        if not tx_ref:

            return (
                "Payment initialization failed: "
                "missing transaction reference.",
                500,
            )

        if not payment_link:

            return (
                "Payment initialization failed: "
                "payment link missing.",
                500,
            )

        if amount != plan_amount:

            logger.error(
                "Payment amount mismatch during creation: "
                "plan=%s expected=%s received=%s",
                payment_plan,
                plan_amount,
                amount,
            )

            return (
                "Payment amount validation failed.",
                400,
            )

        # ----------------------------------------------------
        # CALCULATE COMMISSION
        # ----------------------------------------------------

        commission_amount = calculate_commission(
            amount
        )

        payment_data = {
            "tx_ref": tx_ref,
            "transaction_id": None,
            "payment_plan": payment_plan,
            "amount": amount,
            "status": "pending",
            "referral_code": referral_code,
            "promoter_id": promoter_id,
            "commission": commission_amount,
            "telegram_username": telegram_username,
            "telegram_id": telegram_id,
            "registration_completed": 0,
        }

        save_payment(
            payment_data
        )

        PAYMENT_SESSIONS[
            tx_ref
        ] = {
            **payment_data,
            "payment_status": "pending",
            "plan": payment_plan_name,
        }

        logger.info(
            "Flutterwave payment created successfully: "
            "tx_ref=%s amount=%s plan=%s",
            tx_ref,
            amount,
            payment_plan,
        )

        return redirect(
            payment_link
        )

    except Exception as e:

        logger.exception(
            "CREATE PAYMENT ERROR: %s",
            e,
        )

        return (
            "Unable to start payment. "
            "Please try again.",
            500,
        )


# ============================================================
# FLUTTERWAVE CALLBACK
# ============================================================

@web_app.route(
    "/payment-callback",
    methods=["GET"],
)
def payment_callback():

    try:

        transaction_id = (
            request.args.get(
                "transaction_id"
            )
            or ""
        ).strip()

        callback_tx_ref = (
            request.args.get(
                "tx_ref"
            )
            or ""
        ).strip()

        callback_telegram_id = (
            request.args.get(
                "telegram_id"
            )
            or ""
        ).strip()

        callback_telegram_name = (
            request.args.get(
                "telegram_name"
            )
            or ""
        ).strip()

        callback_telegram_username = (
            request.args.get(
                "telegram_username"
            )
            or ""
        ).strip()

        # ----------------------------------------------------
        # TRANSACTION ID
        # ----------------------------------------------------

        if not transaction_id:

            return (
                "Payment verification failed: "
                "missing transaction ID.",
                400,
            )

        # ----------------------------------------------------
        # VERIFY FLUTTERWAVE PAYMENT
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

        verified_dict = (
            row_to_dict(
                verified
            )
            or {}
        )

        verified_status = str(
            get_value(
                verified_dict,
                "status",
                "",
            )
        ).strip().lower()

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
        # VERIFIED TX REF
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

        if not verified_tx_ref:

            return (
                "Payment verification failed: "
                "missing transaction reference.",
                400,
            )

        # ----------------------------------------------------
        # CALLBACK TX REF CHECK
        # ----------------------------------------------------

        if callback_tx_ref:

            if callback_tx_ref != verified_tx_ref:

                logger.warning(
                    "Callback tx_ref mismatch: "
                    "callback=%s verified=%s",
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
        # GET ORIGINAL PAYMENT
        # ----------------------------------------------------

        original_payment = (
            get_payment_by_tx_ref(
                tx_ref
            )
        )

        if original_payment is None:

            logger.warning(
                "Original payment not found: %s",
                tx_ref,
            )

            return (
                "Payment record not found.",
                404,
            )

        payment = (
            row_to_dict(
                original_payment
            )
            or {}
        )

        original_amount = normalize_amount(
            get_value(
                payment,
                "amount",
                0,
            )
        )

        # ----------------------------------------------------
        # CURRENCY VALIDATION
        # ----------------------------------------------------

        if verified_currency != "NGN":

            update_payment_status(
                tx_ref=tx_ref,
                status="failed",
            )

            return (
                "Invalid payment currency.",
                400,
            )

        # ----------------------------------------------------
        # AMOUNT VALIDATION
        # ----------------------------------------------------

        if verified_amount != original_amount:

            logger.warning(
                "Payment amount mismatch: "
                "tx_ref=%s original=%s verified=%s",
                tx_ref,
                original_amount,
                verified_amount,
            )

            update_payment_status(
                tx_ref=tx_ref,
                status="failed",
            )

            return (
                "Payment amount does not match "
                "the selected plan.",
                400,
            )

        # ----------------------------------------------------
        # PAYMENT PLAN VALIDATION
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
                "Unknown payment plan: %s",
                payment_plan,
            )

            return (
                "Payment plan validation failed.",
                400,
            )

        if original_amount != expected_plan_amount:

            logger.error(
                "Plan amount mismatch: "
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
        # REFERRAL / PROMOTER
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

        if referral_code:

            promoter = (
                get_promoter_by_referral_code(
                    referral_code
                )
            )

            if promoter is None:

                logger.warning(
                    "Promoter inactive: %s",
                    referral_code,
                )

                referral_code = ""
                promoter_id = None

            else:

                promoter_dict = (
                    row_to_dict(
                        promoter
                    )
                    or {}
                )

                promoter_id = get_value(
                    promoter_dict,
                    "id",
                    promoter_id,
                )

        else:

            promoter_id = None

        # ----------------------------------------------------
        # CALCULATE COMMISSION
        # ----------------------------------------------------

        commission_amount = 0
        commission_rate = 0

        if promoter_id:

            commission_amount = calculate_commission(
                original_amount
            )

            if original_amount > 0:

                commission_rate = (
                    commission_amount
                    / original_amount
                ) * 100

        # ----------------------------------------------------
        # SAVE SUCCESSFUL PAYMENT
        # ----------------------------------------------------

        save_payment(
            {
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
            }
        )

        # ----------------------------------------------------
        # UPDATE PAYMENT STATUS
        # ----------------------------------------------------

        update_payment_status(
            tx_ref=tx_ref,
            status="successful",
            transaction_id=transaction_id,
        )

        # ----------------------------------------------------
        # UPDATE PAYMENT SESSION
        # ----------------------------------------------------

        PAYMENT_SESSIONS[
            tx_ref
        ] = {
            **payment,
            "tx_ref": tx_ref,
            "transaction_id": transaction_id,
            "amount": original_amount,
            "status": "successful",
            "payment_status": "successful",
            "payment_plan": payment_plan,
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

        # ====================================================
        # CREATE PROMOTER COMMISSION
        # ====================================================

        if (
            promoter_id
            and commission_amount > 0
        ):

            try:

                # ------------------------------------------------
                # CHECK DUPLICATE COMMISSION
                # ------------------------------------------------

                already_exists = commission_exists(
                    promoter_id,
                    tx_ref,
                )

                if not already_exists:

                    # ------------------------------------------------
                    # CREATE COMMISSION
                    # ------------------------------------------------

                    commission_id = create_commission(
                        promoter_id,
                        tx_ref,
                        commission_amount,
                    )

                    if commission_id:

                        logger.info(
                            "=================================================="
                        )

                        logger.info(
                            "COMMISSION CREATED SUCCESSFULLY"
                        )

                        logger.info(
                            "TX REF: %s",
                            tx_ref,
                        )

                        logger.info(
                            "PROMOTER ID: %s",
                            promoter_id,
                        )

                        logger.info(
                            "PAYMENT AMOUNT: ₦%s",
                            original_amount,
                        )

                        logger.info(
                            "COMMISSION AMOUNT: ₦%s",
                            commission_amount,
                        )

                        logger.info(
                            "COMMISSION ID: %s",
                            commission_id,
                        )

                        logger.info(
                            "=================================================="
                        )

                    else:

                        logger.warning(
                            "Commission was not created: "
                            "tx_ref=%s promoter=%s",
                            tx_ref,
                            promoter_id,
                        )

                else:

                    logger.info(
                        "Commission already exists. "
                        "No duplicate commission created. "
                        "tx_ref=%s promoter=%s",
                        tx_ref,
                        promoter_id,
                    )

            except Exception as commission_error:

                logger.exception(
                    "COMMISSION CREATION ERROR: %s",
                    commission_error,
                )

        else:

            logger.info(
                "No commission created. "
                "promoter_id=%s commission_amount=%s",
                promoter_id,
                commission_amount,
            )

        # ----------------------------------------------------
        # GO TO REGISTRATION
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
            "An error occurred while verifying "
            "your payment. Please contact "
            "Alhikam Learning Center.",
            500,
        )


# ============================================================
# REGISTRATION
# ============================================================

@web_app.route(
    "/register",
    methods=["GET", "POST"],
)
def register():

    try:

        tx_ref = (
            request.args.get(
                "tx_ref"
            )
            or request.form.get(
                "tx_ref"
            )
            or ""
        ).strip()

        if not tx_ref:

            return (
                "Missing payment reference.",
                400,
            )

        db_payment = (
            get_payment_by_tx_ref(
                tx_ref
            )
        )

        if db_payment is None:

            return (
                "Payment record not found.",
                404,
            )

        payment = (
            row_to_dict(
                db_payment
            )
            or {}
        )

        payment["tx_ref"] = tx_ref

        # ====================================================
        # PAYMENT STATUS CHECK
        # ====================================================

        payment_status = str(
            payment.get(
                "payment_status",
                "",
            )
            or payment.get(
                "status",
                "",
            )
            or ""
        ).strip().lower()

        payment["payment_status"] = (
            payment_status
        )

        # Keep compatibility with older code
        payment["status"] = (
            payment_status
        )

        if payment_status != "successful":

            logger.warning(
                "Registration blocked: "
                "payment not successful "
                "tx_ref=%s status=%s",
                tx_ref,
                payment_status,
            )

            return (
                "This payment has not been "
                "successfully verified.",
                403,
            )

        # ====================================================
        # PAYMENT SESSION
        # ====================================================

        PAYMENT_SESSIONS[
            tx_ref
        ] = payment

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

    return referral_dashboard_by_code(
        None
    )


# ============================================================
# PROMOTER REFERRAL LINK
# ============================================================

@web_app.route(
    "/referral/<referral_code>",
    methods=["GET"],
)
def referral_by_code(
    referral_code
):

    referral_code = (
        referral_code or ""
    ).strip()

    if not referral_code:

        return redirect(
            url_for(
                "promoter_login"
            )
        )

    promoter = (
        get_promoter_by_referral_code(
            referral_code
        )
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
# LEGACY PROMOTER DASHBOARD
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
# ADMIN LOGIN
# ============================================================

@web_app.route(
    "/admin/referral/login",
    methods=["GET", "POST"],
)
def admin_referral_login():

    return admin_login_page()


# ============================================================
# ADMIN DASHBOARD
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
# ADMIN STUDENT DETAILS
# ============================================================
#
# Opens the full student details page from the
# Admin Referral Dashboard.
#
# Example:
#
# /admin/referral/student/12
#
# ============================================================

@web_app.route(
    "/admin/referral/student/<int:student_id>",
    methods=["GET"],
)
def admin_student_details(
    student_id
):

    try:

        if not admin_logged_in():

            return redirect(
                url_for(
                    "admin_referral_login"
                )
            )

        return admin_student_details_page(
            student_id
        )

    except Exception as e:

        logger.exception(
            "ADMIN STUDENT DETAILS ERROR: %s",
            e,
        )

        return (
            "Unable to open student details.",
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
#
# IMPORTANT:
# admin_referral.py sends withdrawal_id
# inside POST form data.
#
# Therefore this route MUST NOT require
# withdrawal_id in the URL.
#
# ============================================================

@web_app.route(
    "/admin/referral/withdrawal-status",
    methods=["POST"],
)
def admin_withdrawal_status():

    return admin_withdrawal_status_page()


# ============================================================
# HEALTH CHECK
# ============================================================

@web_app.route(
    "/health",
    methods=["GET"],
)
def health():

    return jsonify(
        {
            "status": "ok",
            "service": "ALHIKAM LEARNING CENTER V2",
        }
    )


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

    return jsonify(
        {
            "remote_addr": remote_addr,
            "real_ip": real_ip,
            "x_forwarded_for": forwarded_for,
        }
    )


# ============================================================
# TELEGRAM BOT STARTER
# ============================================================

def start_telegram_bot():

    if not BOT_TOKEN:

        logger.error(
            "=================================================="
        )

        logger.error(
            "❌ BOT_TOKEN IS MISSING"
        )

        logger.error(
            "Telegram bot cannot start."
        )

        logger.error(
            "=================================================="
        )

        return

    try:

        base_dir = os.path.dirname(
            os.path.abspath(
                __file__
            )
        )

        bot_file = os.path.join(
            base_dir,
            "bot.py",
        )

        if not os.path.isfile(
            bot_file
        ):

            logger.error(
                "❌ bot.py was not found: %s",
                bot_file,
            )

            return

        logger.info(
            "=================================================="
        )

        logger.info(
            "STARTING ALHIKAM TELEGRAM BOT"
        )

        logger.info(
            "BOT FILE: %s",
            bot_file,
        )

        logger.info(
            "=================================================="
        )

        # ------------------------------------------------
        # DO NOT HIDE BOT OUTPUT
        # ------------------------------------------------

        process = subprocess.Popen(
            [
                sys.executable,
                "-u",
                bot_file,
            ],
            stdout=sys.stdout,
            stderr=sys.stderr,
            cwd=base_dir,
        )

        logger.info(
            "Telegram bot process started. PID=%s",
            process.pid,
        )

        # ------------------------------------------------
        # MONITOR BOT PROCESS
        # ------------------------------------------------

        def monitor_bot():

            try:

                exit_code = process.wait()

                logger.error(
                    "=================================================="
                )

                logger.error(
                    "❌ TELEGRAM BOT PROCESS STOPPED"
                )

                logger.error(
                    "BOT EXIT CODE: %s",
                    exit_code,
                )

                logger.error(
                    "=================================================="
                )

            except Exception as monitor_error:

                logger.exception(
                    "Telegram bot monitor error: %s",
                    monitor_error,
                )

        monitor_thread = threading.Thread(
            target=monitor_bot,
            name="telegram-bot-monitor",
            daemon=True,
        )

        monitor_thread.start()

    except Exception as e:

        logger.exception(
            "❌ Unable to start Telegram bot: %s",
            e,
        )


# ============================================================
# BOT LAUNCHER
# ============================================================

def launch_bot_once():

    try:

        logger.info(
            "Telegram bot launcher waiting 3 seconds..."
        )

        time.sleep(3)

        start_telegram_bot()

    except Exception as e:

        logger.exception(
            "❌ Bot launcher error: %s",
            e,
        )


# ============================================================
# START APPLICATION
# ============================================================

if __name__ == "__main__":

    logger.info(
        "=================================================="
    )

    logger.info(
        "Starting ALHIKAM LEARNING CENTER V2..."
    )

    logger.info(
        "=================================================="
    )

    bot_thread = threading.Thread(
        target=launch_bot_once,
        name="telegram-bot-launcher",
        daemon=True,
    )

    bot_thread.start()

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