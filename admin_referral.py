# ==========================================================
# ALHIKAM LEARNING CENTER V2
# admin_referral.py
#
# SECURE ADMIN REFERRAL MANAGEMENT
# ==========================================================

import os
import secrets
import logging
from functools import wraps

from flask import (
    request,
    redirect,
    url_for,
    render_template_string,
    session,
    abort,
)

from database import (
    get_all_promoters,
    get_all_withdrawals,
    add_promoter,
    get_withdrawal_by_id,
    update_withdrawal_status,
    set_promoter_password,
)

from transfer import (
    get_flutterwave_transfer_status,
)


# ==========================================================
# LOGGING
# ==========================================================

logger = logging.getLogger(__name__)


# ==========================================================
# CONFIG
# ==========================================================

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

ADMIN_SESSION_KEY = "alhikam_admin_logged_in"
ADMIN_CSRF_KEY = "alhikam_admin_csrf"


# ==========================================================
# ADMIN PASSWORD CONFIG CHECK
# ==========================================================

if not ADMIN_PASSWORD:
    logger.warning(
        "ADMIN_PASSWORD is not configured."
    )


# ==========================================================
# ADMIN SESSION CHECK
# ==========================================================

def admin_logged_in():
    return session.get(
        ADMIN_SESSION_KEY
    ) is True


def admin_required(view):

    @wraps(view)
    def wrapped(*args, **kwargs):

        if not admin_logged_in():

            return redirect(
                url_for(
                    "admin_referral_login"
                )
            )

        return view(
            *args,
            **kwargs
        )

    return wrapped


# ==========================================================
# CSRF
# ==========================================================

def get_admin_csrf():

    token = session.get(
        ADMIN_CSRF_KEY
    )

    if not token:

        token = secrets.token_urlsafe(
            32
        )

        session[
            ADMIN_CSRF_KEY
        ] = token

    return token


def verify_admin_csrf():

    token = request.form.get(
        "csrf_token",
        ""
    )

    expected = session.get(
        ADMIN_CSRF_KEY
    )

    if not expected or not token:
        abort(403)

    if not secrets.compare_digest(
        str(token),
        str(expected)
    ):
        abort(403)


# ==========================================================
# MASK ACCOUNT NUMBER
# ==========================================================

def mask_account_number(
    account_number
):

    account_number = str(
        account_number or ""
    ).strip()

    if not account_number:
        return "**********"

    if len(account_number) <= 4:
        return "*" * len(
            account_number
        )

    return (
        "*" * (
            len(account_number) - 4
        )
        + account_number[-4:]
    )


# ==========================================================
# ADMIN LOGIN
# ==========================================================

def admin_login_page():

    if request.method == "POST":

        password = request.form.get(
            "password",
            ""
        ).strip()

        if (
            ADMIN_PASSWORD
            and secrets.compare_digest(
                password,
                ADMIN_PASSWORD
            )
        ):

            session.pop(
                ADMIN_SESSION_KEY,
                None
            )

            session.pop(
                ADMIN_CSRF_KEY,
                None
            )

            session[
                ADMIN_SESSION_KEY
            ] = True

            session[
                ADMIN_CSRF_KEY
            ] = secrets.token_urlsafe(
                32
            )

            session.permanent = True

            return redirect(
                url_for(
                    "admin_referral"
                )
            )

        return render_template_string(
            ADMIN_LOGIN_HTML,
            error="Invalid admin password."
        )

    return render_template_string(
        ADMIN_LOGIN_HTML,
        error=None
    )


# ==========================================================
# ADMIN LOGOUT
# ==========================================================

@admin_required
def admin_logout_page():

    verify_admin_csrf()

    session.pop(
        ADMIN_SESSION_KEY,
        None
    )

    session.pop(
        ADMIN_CSRF_KEY,
        None
    )

    return redirect(
        url_for(
            "admin_referral_login"
        )
    )


# ==========================================================
# ADMIN DASHBOARD
# ==========================================================

@admin_required
def admin_referral_page():

    promoters = get_all_promoters()

    withdrawals = get_all_withdrawals()

    csrf_token = get_admin_csrf()

    safe_withdrawals = []

    for withdrawal in withdrawals:

        item = dict(
            withdrawal
        )

        item[
            "masked_account_number"
        ] = mask_account_number(
            withdrawal.get(
                "account_number"
            )
        )

        safe_withdrawals.append(
            item
        )

    return render_template_string(
        ADMIN_DASHBOARD_HTML,
        promoters=promoters,
        withdrawals=safe_withdrawals,
        csrf_token=csrf_token,
    )


# ==========================================================
# CREATE PROMOTER
# ==========================================================

@admin_required
def create_promoter_page():

    verify_admin_csrf()

    full_name = request.form.get(
        "full_name",
        ""
    ).strip()

    phone = request.form.get(
        "phone",
        ""
    ).strip()

    email = request.form.get(
        "email",
        ""
    ).strip()

    commission_rate_raw = request.form.get(
        "commission_rate",
        "20"
    ).strip()

    password = request.form.get(
        "password",
        ""
    )

    # ------------------------------------------------------
    # VALIDATE NAME
    # ------------------------------------------------------

    if not full_name:

        return redirect(
            url_for(
                "admin_referral",
                error="Full name is required."
            )
        )

    if len(full_name) > 100:

        return redirect(
            url_for(
                "admin_referral",
                error="Full name is too long."
            )
        )

    # ------------------------------------------------------
    # VALIDATE PASSWORD
    # ------------------------------------------------------

    if len(password) < 8:

        return redirect(
            url_for(
                "admin_referral",
                error=(
                    "Promoter password must be "
                    "at least 8 characters."
                )
            )
        )

    if len(password) > 200:

        return redirect(
            url_for(
                "admin_referral",
                error="Password is too long."
            )
        )

    # ------------------------------------------------------
    # VALIDATE COMMISSION
    # ------------------------------------------------------

    try:

        commission_rate = float(
            commission_rate_raw
        )

    except (
        TypeError,
        ValueError
    ):

        return redirect(
            url_for(
                "admin_referral",
                error=(
                    "Invalid commission rate."
                )
            )
        )

    if (
        commission_rate < 0
        or commission_rate > 100
    ):

        return redirect(
            url_for(
                "admin_referral",
                error=(
                    "Commission rate must "
                    "be between 0 and 100."
                )
            )
        )

    # ------------------------------------------------------
    # CREATE PROMOTER
    # ------------------------------------------------------

    try:

        promoter_id = add_promoter(
            full_name=full_name,
            phone=phone,
            email=email,
            commission_rate=commission_rate,
        )

        set_promoter_password(
            promoter_id,
            password
        )

        logger.info(
            "Promoter created successfully: id=%s",
            promoter_id
        )

        return redirect(
            url_for(
                "admin_referral",
                success=(
                    "Promoter created successfully."
                )
            )
        )

    except Exception:

        logger.exception(
            "Failed to create promoter"
        )

        return redirect(
            url_for(
                "admin_referral",
                error=(
                    "Unable to create promoter."
                )
            )
        )


# ==========================================================
# REFRESH FLUTTERWAVE WITHDRAWAL STATUS
# ==========================================================

def refresh_withdrawal_status(
    withdrawal_id
):

    withdrawal = get_withdrawal_by_id(
        withdrawal_id
    )

    if not withdrawal:

        return (
            False,
            "Withdrawal not found."
        )

    transfer_id = withdrawal.get(
        "transfer_id"
    )

    if not transfer_id:

        return (
            False,
            "This withdrawal does not "
            "have a Flutterwave transfer ID."
        )

    try:

        result = (
            get_flutterwave_transfer_status(
                transfer_id
            )
        )

    except Exception:

        logger.exception(
            "Flutterwave status check failed "
            "for withdrawal %s",
            withdrawal_id
        )

        return (
            False,
            "Unable to verify transfer status."
        )

    if not result:

        return (
            False,
            "Flutterwave returned no status."
        )

    status = str(
        result.get(
            "status",
            ""
        )
    ).upper().strip()

    message = str(
        result.get(
            "message",
            ""
        )
    ).strip()

    # ------------------------------------------------------
    # SUCCESS
    # ------------------------------------------------------

    if status in (
        "SUCCESSFUL",
        "SUCCESS",
        "COMPLETED",
    ):

        try:

            update_withdrawal_status(
                withdrawal_id,
                "successful",
                transfer_id=transfer_id,
                transfer_status=status,
                transfer_message=message,
            )

            return (
                True,
                "Withdrawal confirmed successful."
            )

        except Exception:

            logger.exception(
                "Failed to mark withdrawal %s "
                "successful",
                withdrawal_id
            )

            return (
                False,
                "Database update failed."
            )

    # ------------------------------------------------------
    # FAILED
    # ------------------------------------------------------

    if status in (
        "FAILED",
        "CANCELLED",
        "REVERSED",
    ):

        try:

            update_withdrawal_status(
                withdrawal_id,
                "failed",
                transfer_id=transfer_id,
                transfer_status=status,
                transfer_message=message,
            )

            return (
                True,
                "Withdrawal failed and balance "
                "was returned according to "
                "the withdrawal state."
            )

        except Exception:

            logger.exception(
                "Failed to process failed withdrawal %s",
                withdrawal_id
            )

            return (
                False,
                "Database update failed."
            )

    # ------------------------------------------------------
    # PROCESSING
    # ------------------------------------------------------

    try:

        update_withdrawal_status(
            withdrawal_id,
            "processing",
            transfer_id=transfer_id,
            transfer_status=status,
            transfer_message=message,
        )

    except Exception:

        logger.exception(
            "Failed to update processing withdrawal %s",
            withdrawal_id
        )

        return (
            False,
            "Database update failed."
        )

    return (
        True,
        f"Transfer is still processing ({status})."
    )


# ==========================================================
# ADMIN WITHDRAWAL STATUS
# ==========================================================

@admin_required
def admin_withdrawal_status_page():

    verify_admin_csrf()

    withdrawal_id_raw = request.form.get(
        "withdrawal_id",
        ""
    ).strip()

    new_status = request.form.get(
        "status",
        ""
    ).strip().lower()

    try:

        withdrawal_id = int(
            withdrawal_id_raw
        )

    except (
        TypeError,
        ValueError
    ):

        return redirect(
            url_for(
                "admin_referral",
                error=(
                    "Invalid withdrawal ID."
                )
            )
        )

    withdrawal = get_withdrawal_by_id(
        withdrawal_id
    )

    if not withdrawal:

        return redirect(
            url_for(
                "admin_referral",
                error=(
                    "Withdrawal not found."
                )
            )
        )

    # ------------------------------------------------------
    # SUCCESS
    # ------------------------------------------------------

    if new_status in (
        "successful",
        "success",
    ):

        ok, message = (
            refresh_withdrawal_status(
                withdrawal_id
            )
        )

        return redirect(
            url_for(
                "admin_referral",
                success=(
                    message if ok else None
                ),
                error=(
                    None if ok else message
                ),
            )
        )

    # ------------------------------------------------------
    # FAILED
    # ------------------------------------------------------

    if new_status == "failed":

        ok, message = (
            refresh_withdrawal_status(
                withdrawal_id
            )
        )

        return redirect(
            url_for(
                "admin_referral",
                success=(
                    message if ok else None
                ),
                error=(
                    None if ok else message
                ),
            )
        )

    # ------------------------------------------------------
    # PROCESSING
    # ------------------------------------------------------

    if new_status == "processing":

        try:

            update_withdrawal_status(
                withdrawal_id,
                "processing"
            )

            return redirect(
                url_for(
                    "admin_referral",
                    success=(
                        "Withdrawal marked as processing."
                    )
                )
            )

        except Exception:

            logger.exception(
                "Failed to mark withdrawal "
                "%s as processing",
                withdrawal_id
            )

            return redirect(
                url_for(
                    "admin_referral",
                    error=(
                        "Unable to update withdrawal."
                    )
                )
            )

    # ------------------------------------------------------
    # CANCELLED
    # ------------------------------------------------------

    if new_status == "cancelled":

        return redirect(
            url_for(
                "admin_referral",
                error=(
                    "Manual cancellation is disabled. "
                    "Verify the Flutterwave transfer status "
                    "before changing the withdrawal."
                )
            )
        )

    return redirect(
        url_for(
            "admin_referral",
            error="Invalid withdrawal status."
        )
    )


# ==========================================================
# HTML: ADMIN LOGIN
# ==========================================================

ADMIN_LOGIN_HTML = """
<!doctype html>

<html>

<head>

    <meta charset="utf-8">

    <meta name="viewport"
          content="width=device-width, initial-scale=1">

    <title>Alhikam Admin Login</title>

    <style>

        body {
            font-family: Arial, sans-serif;
            background: #f4f6f8;
            margin: 0;
            padding: 30px;
        }

        .box {
            max-width: 420px;
            margin: 80px auto;
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 5px 25px rgba(0,0,0,.08);
        }

        input {
            width: 100%;
            box-sizing: border-box;
            padding: 12px;
            margin: 8px 0 15px;
            border: 1px solid #ddd;
            border-radius: 8px;
        }

        button {
            width: 100%;
            padding: 12px;
            border: 0;
            border-radius: 8px;
            cursor: pointer;
        }

        .error {
            background: #ffe5e5;
            padding: 10px;
            border-radius: 8px;
            margin-bottom: 15px;
        }

    </style>

</head>

<body>

<div class="box">

    <h2>Alhikam Learning Center</h2>

    <h3>Admin Login</h3>

    {% if error %}

        <div class="error">
            {{ error }}
        </div>

    {% endif %}

    <form method="POST"
          action="{{ url_for('admin_referral_login') }}">

        <label>
            Admin Password
        </label>

        <input
            type="password"
            name="password"
            required
            autocomplete="current-password"
        >

        <button type="submit">
            Login
        </button>

    </form>

</div>

</body>

</html>
"""


# ==========================================================
# HTML: ADMIN DASHBOARD
# ==========================================================

ADMIN_DASHBOARD_HTML = """
<!doctype html>

<html>

<head>

    <meta charset="utf-8">

    <meta name="viewport"
          content="width=device-width, initial-scale=1">

    <title>Alhikam Referral Admin</title>

    <style>

        body {
            font-family: Arial, sans-serif;
            margin: 0;
            background: #f5f7fa;
            color: #222;
        }

        header {
            background: #111827;
            color: white;
            padding: 18px;
        }

        main {
            max-width: 1200px;
            margin: auto;
            padding: 20px;
        }

        .card {
            background: white;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 12px;
            box-shadow: 0 3px 15px rgba(0,0,0,.06);
        }

        input,
        select {
            width: 100%;
            box-sizing: border-box;
            padding: 10px;
            margin: 6px 0 12px;
            border: 1px solid #ddd;
            border-radius: 7px;
        }

        button {
            padding: 10px 15px;
            border: 0;
            border-radius: 7px;
            cursor: pointer;
        }

        table {
            width: 100%;
            border-collapse: collapse;
        }

        th,
        td {
            padding: 10px;
            border-bottom: 1px solid #eee;
            text-align: left;
        }

        .success {
            background: #e8f8ed;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 15px;
        }

        .error {
            background: #ffe7e7;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 15px;
        }

        .logout {
            background: white;
            color: #111827;
        }

        @media(max-width:700px) {

            table {
                display: block;
                overflow-x: auto;
                white-space: nowrap;
            }

        }

    </style>

</head>

<body>

<header>

    <div style="
        max-width:1200px;
        margin:auto;
        display:flex;
        justify-content:space-between;
        align-items:center;
        gap:10px;
    ">

        <strong>
            ALHIKAM LEARNING CENTER
        </strong>

        <!-- FIXED: correct Flask endpoint -->

        <form method="POST"
              action="{{ url_for('admin_referral_logout') }}">

            <input
                type="hidden"
                name="csrf_token"
                value="{{ csrf_token }}"
            >

            <button
                class="logout"
                type="submit"
            >
                Logout
            </button>

        </form>

    </div>

</header>

<main>

    {% if request.args.get('success') %}

        <div class="success">
            {{ request.args.get('success') }}
        </div>

    {% endif %}

    {% if request.args.get('error') %}

        <div class="error">
            {{ request.args.get('error') }}
        </div>

    {% endif %}


    <!-- ================================================== -->
    <!-- CREATE PROMOTER -->
    <!-- ================================================== -->

    <div class="card">

        <h2>Create Promoter</h2>

        <form method="POST"
              action="{{ url_for('create_promoter') }}">

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
                maxlength="100"
            >

            <label>
                Phone
            </label>

            <input
                type="text"
                name="phone"
            >

            <label>
                Email
            </label>

            <input
                type="email"
                name="email"
            >

            <label>
                Commission Rate (%)
            </label>

            <input
                type="number"
                name="commission_rate"
                value="20"
                min="0"
                max="100"
                step="0.01"
            >

            <label>
                Promoter Password
            </label>

            <input
                type="password"
                name="password"
                minlength="8"
                required
                autocomplete="new-password"
            >

            <button type="submit">
                Create Promoter
            </button>

        </form>

    </div>


    <!-- ================================================== -->
    <!-- PROMOTERS -->
    <!-- ================================================== -->

    <div class="card">

        <h2>
            Promoters
        </h2>

        <div style="overflow-x:auto;">

            <table>

                <thead>

                    <tr>

                        <th>ID</th>
                        <th>Name</th>
                        <th>Phone</th>
                        <th>Referral Code</th>
                        <th>Sales</th>
                        <th>Earned</th>
                        <th>Available</th>
                        <th>Status</th>

                    </tr>

                </thead>

                <tbody>

                {% for promoter in promoters %}

                    <tr>

                        <td>
                            {{ promoter["id"] }}
                        </td>

                        <td>
                            {{ promoter["full_name"] }}
                        </td>

                        <td>
                            {{ promoter["phone"] or "" }}
                        </td>

                        <td>
                            {{ promoter["referral_code"] }}
                        </td>

                        <td>
                            {{ promoter["total_sales"] }}
                        </td>

                        <td>
                            ₦{{ "%.2f"|format(
                                promoter["total_earned"] or 0
                            ) }}
                        </td>

                        <td>
                            ₦{{ "%.2f"|format(
                                promoter["available_balance"] or 0
                            ) }}
                        </td>

                        <td>
                            {{ promoter["status"] }}
                        </td>

                    </tr>

                {% else %}

                    <tr>

                        <td colspan="8">
                            No promoters found.
                        </td>

                    </tr>

                {% endfor %}

                </tbody>

            </table>

        </div>

    </div>


    <!-- ================================================== -->
    <!-- WITHDRAWALS -->
    <!-- ================================================== -->

    <div class="card">

        <h2>
            Withdrawals
        </h2>

        <div style="overflow-x:auto;">

            <table>

                <thead>

                    <tr>

                        <th>ID</th>
                        <th>Promoter</th>
                        <th>Amount</th>
                        <th>Bank</th>
                        <th>Account</th>
                        <th>Status</th>
                        <th>Transfer</th>
                        <th>Action</th>

                    </tr>

                </thead>

                <tbody>

                {% for withdrawal in withdrawals %}

                    <tr>

                        <td>
                            {{ withdrawal["id"] }}
                        </td>

                        <td>
                            {{ withdrawal["promoter_id"] }}
                        </td>

                        <td>
                            ₦{{ "%.2f"|format(
                                withdrawal["amount"] or 0
                            ) }}
                        </td>

                        <td>
                            {{ withdrawal["bank_name"] or "" }}
                        </td>

                        <td>
                            {{ withdrawal[
                                "masked_account_number"
                            ] }}
                        </td>

                        <td>
                            {{ withdrawal["status"] }}
                        </td>

                        <td>
                            {{ withdrawal[
                                "transfer_status"
                            ] or "" }}
                        </td>

                        <td>

                            <form method="POST"
                                  action="{{ url_for(
                                      'admin_withdrawal_status'
                                  ) }}">

                                <input
                                    type="hidden"
                                    name="csrf_token"
                                    value="{{ csrf_token }}"
                                >

                                <input
                                    type="hidden"
                                    name="withdrawal_id"
                                    value="{{ withdrawal['id'] }}"
                                >

                                <select name="status">

                                    <option value="processing">
                                        Check Processing
                                    </option>

                                    <option value="successful">
                                        Verify Success
                                    </option>

                                    <option value="failed">
                                        Verify Failed
                                    </option>

                                </select>

                                <button type="submit">
                                    Update
                                </button>

                            </form>

                        </td>

                    </tr>

                {% else %}

                    <tr>

                        <td colspan="8">
                            No withdrawals found.
                        </td>

                    </tr>

                {% endfor %}

                </tbody>

            </table>

        </div>

    </div>

</main>

</body>

</html>
"""