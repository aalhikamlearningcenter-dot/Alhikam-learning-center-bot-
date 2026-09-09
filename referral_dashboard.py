# ============================================================
# ALHIKAM LEARNING CENTER V2
# PROMOTER REFERRAL DASHBOARD
#
# FEATURES:
# - Promoter Login
# - Referral Dashboard
# - Referral Link
# - Direct Payment Link
# - Secure Withdrawal
# - Withdrawal Code Verification
# - CSRF Protection
# - Bank Account Resolve
# - Flutterwave Transfer
# - Transfer Status Verification
# - Withdrawal History
# - MAIN.PY COMPATIBILITY ALIASES
# ============================================================

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
    flash,
)

from database import (
    MINIMUM_WITHDRAWAL,
    get_promoter_by_id,
    get_promoter_by_referral_code,
    create_withdrawal,
    get_promoter_withdrawals,
    get_withdrawal_by_id,
    update_withdrawal_transfer,
    process_transfer_result,
    verify_promoter_password,
    verify_promoter_withdrawal_code,
)

from transfer import (
    resolve_bank_account,
    create_flutterwave_transfer,
    get_flutterwave_transfer_status,
    get_flutterwave_transfer_status_by_reference,
    get_flutterwave_banks,
)


# ============================================================
# LOGGER
# ============================================================

logger = logging.getLogger(__name__)


# ============================================================
# APP URL
# ============================================================

APP_URL = os.getenv(
    "RAILWAY_URL",
    "https://precious-trust-production-956b.up.railway.app",
).rstrip("/")


# ============================================================
# SESSION KEYS
# ============================================================

PROMOTER_SESSION_KEY = "alhikam_promoter_id"
PROMOTER_CSRF_KEY = "alhikam_promoter_csrf"


# ============================================================
# HELPER
# ============================================================

def _row_get(row, key, default=None):
    if row is None:
        return default

    try:
        return row[key]
    except Exception:
        pass

    try:
        return row.get(key, default)
    except Exception:
        return default


# ============================================================
# MONEY
# ============================================================

def _safe_money(value):
    try:
        return float(value or 0)
    except Exception:
        return 0.0


# ============================================================
# MASK ACCOUNT
# ============================================================

def _mask_account(account_number):
    value = str(account_number or "")

    if len(value) <= 4:
        return "****"

    return (
        "*" * (len(value) - 4)
        + value[-4:]
    )


# ============================================================
# PROMOTER CSRF
# ============================================================

def _csrf_token():
    token = session.get(PROMOTER_CSRF_KEY)

    if not token:
        token = secrets.token_urlsafe(32)
        session[PROMOTER_CSRF_KEY] = token

    return token


def _check_csrf():
    submitted = request.form.get(
        "csrf_token",
        "",
    )

    expected = session.get(
        PROMOTER_CSRF_KEY,
        "",
    )

    if not submitted or not expected:
        return False

    try:
        return secrets.compare_digest(
            submitted,
            expected,
        )
    except Exception:
        return False


# ============================================================
# CURRENT PROMOTER
# ============================================================

def _current_promoter():
    promoter_id = session.get(
        PROMOTER_SESSION_KEY
    )

    if not promoter_id:
        return None

    try:
        promoter_id = int(promoter_id)
    except Exception:
        return None

    try:
        return get_promoter_by_id(
            promoter_id
        )
    except Exception:
        logger.exception(
            "Unable to load current promoter"
        )
        return None


# ============================================================
# PROMOTER LOGIN REQUIRED
# ============================================================

def promoter_required(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        promoter = _current_promoter()

        if not promoter:
            return redirect(
                url_for(
                    "promoter_login"
                )
            )

        return function(
            *args,
            **kwargs
        )

    return wrapper


# ============================================================
# LOGIN HTML
# ============================================================

PROMOTER_LOGIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport"
          content="width=device-width, initial-scale=1.0">

    <title>ALHIKAM Promoter Login</title>

    <style>
        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            padding: 20px;
            font-family: Arial, sans-serif;
            background: #f3f6f9;
            color: #17202a;
        }

        .container {
            max-width: 480px;
            margin: 50px auto;
        }

        .card {
            background: white;
            padding: 30px;
            border-radius: 18px;
            box-shadow: 0 8px 30px rgba(0,0,0,0.08);
        }

        h1 {
            margin-bottom: 5px;
            color: #0b6b3a;
        }

        .subtitle {
            color: #666;
            margin-bottom: 25px;
        }

        label {
            display: block;
            margin-top: 16px;
            margin-bottom: 7px;
            font-weight: bold;
        }

        input {
            width: 100%;
            padding: 13px;
            border: 1px solid #ccd3d8;
            border-radius: 10px;
            font-size: 15px;
        }

        button {
            width: 100%;
            margin-top: 22px;
            padding: 14px;
            border: none;
            border-radius: 10px;
            background: #0b6b3a;
            color: white;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
        }

        .error {
            background: #ffe8e8;
            color: #a00000;
            padding: 12px;
            border-radius: 10px;
            margin-bottom: 15px;
        }

        .info {
            margin-top: 18px;
            color: #666;
            font-size: 14px;
        }
    </style>
</head>

<body>

<div class="container">

    <div class="card">

        <h1>🎓 ALHIKAM</h1>

        <div class="subtitle">
            Promoter Dashboard Login
        </div>

        {% if error %}
            <div class="error">
                {{ error }}
            </div>
        {% endif %}

        <p>
            Enter your referral code and promoter password.
        </p>

        <form method="POST">

            <input
                type="hidden"
                name="csrf_token"
                value="{{ csrf_token }}"
            >

            <input
                type="hidden"
                name="ref"
                value="{{ referral_code }}"
            >

            <label>
                Referral Code
            </label>

            <input
                type="text"
                name="referral_code"
                value="{{ referral_code }}"
                placeholder="Enter referral code"
                required
                autocomplete="username"
            >

            <label>
                Password
            </label>

            <input
                type="password"
                name="password"
                placeholder="Enter promoter password"
                required
                autocomplete="current-password"
            >

            <button type="submit">
                🔐 Login
            </button>

        </form>

        <div class="info">
            Alhikam Learning Center Promoter System
        </div>

    </div>

</div>

</body>
</html>
"""


# ============================================================
# PROMOTER LOGIN
# ============================================================

def promoter_login_page():

    if _current_promoter():
        return redirect(
            url_for(
                "referral_dashboard"
            )
        )

    referral_code = (
        request.args.get(
            "ref",
            "",
        )
        or request.form.get(
            "referral_code",
            "",
        )
    ).strip().upper()

    if request.method == "GET":

        return render_template_string(
            PROMOTER_LOGIN_HTML,
            csrf_token=_csrf_token(),
            referral_code=referral_code,
            error="",
        )

    if not _check_csrf():

        return render_template_string(
            PROMOTER_LOGIN_HTML,
            csrf_token=_csrf_token(),
            referral_code=referral_code,
            error=(
                "Invalid security token. "
                "Please refresh and try again."
            ),
        ), 400

    password = request.form.get(
        "password",
        "",
    )

    if not referral_code:

        return render_template_string(
            PROMOTER_LOGIN_HTML,
            csrf_token=_csrf_token(),
            referral_code="",
            error="Referral code is required.",
        ), 400

    try:
        promoter = get_promoter_by_referral_code(
            referral_code
        )
    except Exception:
        logger.exception(
            "Unable to find promoter"
        )
        promoter = None

    if not promoter:

        return render_template_string(
            PROMOTER_LOGIN_HTML,
            csrf_token=_csrf_token(),
            referral_code=referral_code,
            error=(
                "❌ Invalid referral code or password."
            ),
        ), 401

    promoter_id = _row_get(
        promoter,
        "id",
    )

    try:
        valid_password = verify_promoter_password(
            promoter_id,
            password,
        )
    except Exception:
        logger.exception(
            "Promoter password verification failed"
        )
        valid_password = False

    if not valid_password:

        return render_template_string(
            PROMOTER_LOGIN_HTML,
            csrf_token=_csrf_token(),
            referral_code=referral_code,
            error=(
                "❌ Invalid referral code or password."
            ),
        ), 401

    # --------------------------------------------------------
    # LOGIN SUCCESS
    # --------------------------------------------------------

    session[
        PROMOTER_SESSION_KEY
    ] = promoter_id

    session[
        PROMOTER_CSRF_KEY
    ] = secrets.token_urlsafe(32)

    session.permanent = True

    return redirect(
        url_for(
            "referral_dashboard"
        )
    )


# ============================================================
# PROMOTER LOGOUT
# ============================================================

def promoter_logout_page():

    session.pop(
        PROMOTER_SESSION_KEY,
        None,
    )

    session.pop(
        PROMOTER_CSRF_KEY,
        None,
    )

    return redirect(
        url_for(
            "promoter_login"
        )
    )


# ============================================================
# COMPATIBILITY ALIAS
# ============================================================

promoter_logout = promoter_logout_page


# ============================================================
# DASHBOARD HTML
# ============================================================

REFERRAL_DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">

<head>

    <meta charset="UTF-8">

    <meta name="viewport"
          content="width=device-width, initial-scale=1.0">

    <title>ALHIKAM Promoter Dashboard</title>

    <style>

        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            padding: 18px;
            font-family: Arial, sans-serif;
            background: #f3f6f9;
            color: #17202a;
        }

        .container {
            max-width: 1000px;
            margin: auto;
        }

        .header {
            background: #0b6b3a;
            color: white;
            padding: 22px;
            border-radius: 16px;
            margin-bottom: 18px;
        }

        .header h1 {
            margin: 0 0 6px 0;
        }

        .logout {
            background: #8b0000;
            margin-top: 15px;
        }

        .card {
            background: white;
            padding: 22px;
            border-radius: 16px;
            margin-bottom: 18px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.06);
        }

        .stats {
            display: grid;
            grid-template-columns:
                repeat(auto-fit, minmax(180px, 1fr));
            gap: 14px;
        }

        .stat {
            background: #f7faf8;
            padding: 18px;
            border-radius: 13px;
        }

        .stat-title {
            color: #666;
            font-size: 14px;
        }

        .stat-value {
            margin-top: 7px;
            font-size: 21px;
            font-weight: bold;
            color: #0b6b3a;
        }

        input,
        select {
            width: 100%;
            padding: 12px;
            border: 1px solid #ccd3d8;
            border-radius: 9px;
            margin-top: 6px;
            margin-bottom: 13px;
            font-size: 15px;
        }

        label {
            font-weight: bold;
        }

        button {
            border: none;
            border-radius: 9px;
            padding: 12px 16px;
            cursor: pointer;
            font-weight: bold;
        }

        .copy {
            background: #e8f1ff;
            color: #174a91;
        }

        .withdraw {
            width: 100%;
            background: #0b6b3a;
            color: white;
            font-size: 16px;
            margin-top: 8px;
        }

        .warning {
            background: #fff5d9;
            border-radius: 10px;
            padding: 13px;
            margin-bottom: 16px;
        }

        .message {
            padding: 12px;
            border-radius: 9px;
            margin-bottom: 8px;
            background: #eef7ef;
        }

        .error {
            background: #ffe8e8;
            color: #a00000;
        }

        .table-wrap {
            overflow-x: auto;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            min-width: 750px;
        }

        th,
        td {
            padding: 11px;
            border-bottom: 1px solid #eee;
            text-align: left;
        }

        th {
            background: #f5f7f8;
        }

        .status-link {
            color: #0b6b3a;
            font-weight: bold;
            text-decoration: none;
        }

        .small {
            color: #666;
            font-size: 14px;
        }

    </style>

</head>

<body>

<div class="container">

    <div class="header">

        <h1>🎓 ALHIKAM Learning Center</h1>

        <div>
            Promoter Dashboard
        </div>

        <form
            method="POST"
            action="{{ url_for('promoter_logout') }}"
        >

            <input
                type="hidden"
                name="csrf_token"
                value="{{ csrf_token }}"
            >

            <button
                type="submit"
                class="logout"
            >
                🚪 Logout
            </button>

        </form>

    </div>


    {% with messages = get_flashed_messages(
        with_categories=true
    ) %}

        {% for category, message in messages %}

            <div
                class="message
                {% if category == 'error' %}
                    error
                {% endif %}"
            >
                {{ message }}
            </div>

        {% endfor %}

    {% endwith %}


    <!-- ================================================== -->
    <!-- PERFORMANCE -->
    <!-- ================================================== -->

    <div class="card">

        <h2>📊 My Performance</h2>

        <div class="stats">

            <div class="stat">

                <div class="stat-title">
                    Total Sales
                </div>

                <div class="stat-value">
                    ₦{{ "{:,.2f}".format(
                        promoter["total_sales"] or 0
                    ) }}
                </div>

            </div>


            <div class="stat">

                <div class="stat-title">
                    Total Earned
                </div>

                <div class="stat-value">
                    ₦{{ "{:,.2f}".format(
                        promoter["total_earned"] or 0
                    ) }}
                </div>

            </div>


            <div class="stat">

                <div class="stat-title">
                    Available Balance
                </div>

                <div class="stat-value">
                    ₦{{ "{:,.2f}".format(
                        promoter["available_balance"] or 0
                    ) }}
                </div>

            </div>


            <div class="stat">

                <div class="stat-title">
                    Withdrawn
                </div>

                <div class="stat-value">
                    ₦{{ "{:,.2f}".format(
                        promoter["withdrawn_amount"] or 0
                    ) }}
                </div>

            </div>

        </div>

    </div>


    <!-- ================================================== -->
    <!-- REFERRAL LINK -->
    <!-- ================================================== -->

    <div class="card">

        <h2>🔗 My Referral Link</h2>

        <p>
            Share this link with students.
        </p>

        <p class="small">
            Payments made through your referral link
            will be connected to your referral account.
        </p>

        {% set referral_link =
            app_url
            + "/referral/"
            + promoter["referral_code"]
        %}

        <input
            id="referral-link"
            type="text"
            value="{{ referral_link }}"
            readonly
        >

        <button
            type="button"
            class="copy"
            onclick="copyText('referral-link', this)"
        >
            📋 Copy
        </button>

        <p>
            <strong>Referral Code:</strong>
            {{ promoter["referral_code"] }}
        </p>

    </div>


    <!-- ================================================== -->
    <!-- DIRECT PAYMENT LINK -->
    <!-- ================================================== -->

    <div class="card">

        <h2>💳 Direct Payment Link</h2>

        <p>
            Students can use this link directly
            to open the payment page.
        </p>

        <p class="small">
            Your referral code is automatically attached.
        </p>

        {% set payment_link =
            app_url
            + "/pay?ref="
            + promoter["referral_code"]
        %}

        <input
            id="payment-link"
            type="text"
            value="{{ payment_link }}"
            readonly
        >

        <button
            type="button"
            class="copy"
            onclick="copyText('payment-link', this)"
        >
            📋 Copy
        </button>

    </div>


    <!-- ================================================== -->
    <!-- WITHDRAWAL -->
    <!-- ================================================== -->

    <div class="card">

        <h2>💰 Withdraw Commission</h2>

        <div class="warning">

            <strong>
                Withdrawal Security
            </strong>

            <br><br>

            Your Withdrawal Code is required
            before any withdrawal can be processed.

            <br><br>

            <strong>
                Never share your Withdrawal Code
                with another person.
            </strong>

        </div>

        <p>
            Minimum withdrawal:
            <strong>
                ₦{{ "{:,.2f}".format(
                    minimum_withdrawal
                ) }}
            </strong>
        </p>


        <!-- IMPORTANT:
             main.py registers the withdrawal endpoint
             as referral_withdraw.
        -->

        <form
            method="POST"
            action="{{ url_for('referral_withdraw') }}"
        >

            <input
                type="hidden"
                name="csrf_token"
                value="{{ csrf_token }}"
            >


            <label>
                Withdrawal Amount
            </label>

            <input
                type="number"
                name="amount"
                min="{{ minimum_withdrawal }}"
                step="0.01"
                placeholder="Enter amount"
                required
            >


            <label>
                Bank
            </label>

            <select
                name="bank_code"
                required
            >

                <option value="">
                    Select Bank
                </option>

                {% for bank in banks %}

                    <option
                        value="{{ bank['code'] }}"
                    >
                        {{ bank['name'] }}
                    </option>

                {% endfor %}

            </select>


            <label>
                Account Number
            </label>

            <input
                type="text"
                name="account_number"
                inputmode="numeric"
                maxlength="10"
                minlength="10"
                placeholder="10-digit account number"
                required
            >


            <label>
                Withdrawal Code
            </label>

            <input
                type="password"
                name="withdrawal_code"
                placeholder="Enter your withdrawal code"
                minlength="6"
                autocomplete="off"
                required
            >


            <button
                type="submit"
                class="withdraw"
            >
                💸 Request Withdrawal
            </button>

        </form>

    </div>


    <!-- ================================================== -->
    <!-- WITHDRAWAL HISTORY -->
    <!-- ================================================== -->

    <div class="card">

        <h2>📜 Withdrawal History</h2>

        <div class="table-wrap">

            <table>

                <thead>

                    <tr>

                        <th>ID</th>
                        <th>Amount</th>
                        <th>Bank</th>
                        <th>Account</th>
                        <th>Status</th>
                        <th>Transfer Status</th>
                        <th>Created</th>
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
                            ₦{{ "{:,.2f}".format(
                                withdrawal["amount"] or 0
                            ) }}
                        </td>

                        <td>
                            {{ withdrawal["bank_name"] or "" }}
                        </td>

                        <td>
                            {{ mask_account(
                                withdrawal["account_number"]
                            ) }}
                        </td>

                        <td>
                            {{ withdrawal["status"] or "" }}
                        </td>

                        <td>
                            {{ withdrawal["transfer_status"] or "" }}
                        </td>

                        <td>
                            {{ withdrawal["created_at"] or "" }}
                        </td>

                        <td>

                            <a
                                class="status-link"
                                href="{{ url_for(
                                    'promoter_withdrawal_status',
                                    withdrawal_id=withdrawal['id']
                                ) }}"
                            >
                                View
                            </a>

                        </td>

                    </tr>

                    {% else %}

                    <tr>

                        <td colspan="8">
                            No withdrawal requests yet.
                        </td>

                    </tr>

                    {% endfor %}

                </tbody>

            </table>

        </div>

    </div>

</div>


<script>

function copyText(id, button) {

    const input = document.getElementById(id);

    if (!input) {
        return;
    }

    navigator.clipboard.writeText(
        input.value
    ).then(function() {

        const oldText = button.innerText;

        button.innerText = "✅ Copied";

        setTimeout(function() {
            button.innerText = oldText;
        }, 1500);

    }).catch(function() {

        input.select();
        document.execCommand("copy");

        const oldText = button.innerText;

        button.innerText = "✅ Copied";

        setTimeout(function() {
            button.innerText = oldText;
        }, 1500);

    });
}

</script>

</body>
</html>
"""


# ============================================================
# DASHBOARD
# ============================================================

def referral_dashboard_by_code(referral_code=None):

    promoter = _current_promoter()

    if not promoter:

        if referral_code:

            return redirect(
                url_for(
                    "promoter_login",
                    ref=referral_code,
                )
            )

        return redirect(
            url_for(
                "promoter_login"
            )
        )

    withdrawals = get_promoter_withdrawals(
        promoter["id"]
    )

    try:

        banks = (
            get_flutterwave_banks()
            or []
        )

    except Exception:

        logger.exception(
            "Unable to get Flutterwave banks"
        )

        banks = []

    return render_template_string(
        REFERRAL_DASHBOARD_HTML,
        promoter=promoter,
        withdrawals=withdrawals,
        banks=banks,
        minimum_withdrawal=MINIMUM_WITHDRAWAL,
        app_url=APP_URL,
        csrf_token=_csrf_token(),
        mask_account=_mask_account,
    )


# ============================================================
# WITHDRAWAL STATUS HTML
# ============================================================

WITHDRAWAL_STATUS_HTML = """
<!DOCTYPE html>
<html lang="en">

<head>

    <meta charset="UTF-8">

    <meta name="viewport"
          content="width=device-width, initial-scale=1.0">

    <title>ALHIKAM Withdrawal Status</title>

    <style>

        body {
            margin: 0;
            padding: 20px;
            font-family: Arial, sans-serif;
            background: #f3f6f9;
            color: #17202a;
        }

        .container {
            max-width: 600px;
            margin: 40px auto;
        }

        .card {
            background: white;
            padding: 25px;
            border-radius: 16px;
            box-shadow: 0 8px 25px rgba(0,0,0,0.08);
        }

        .row {
            padding: 12px 0;
            border-bottom: 1px solid #eee;
        }

        .label {
            font-weight: bold;
            color: #555;
        }

        button {
            width: 100%;
            margin-top: 20px;
            padding: 13px;
            border: none;
            border-radius: 9px;
            background: #0b6b3a;
            color: white;
            font-weight: bold;
            cursor: pointer;
        }

        a {
            display: block;
            margin-top: 18px;
            text-align: center;
            color: #0b6b3a;
            font-weight: bold;
            text-decoration: none;
        }

    </style>

</head>

<body>

<div class="container">

    <div class="card">

        <h1>
            💰 Withdrawal Status
        </h1>


        <div class="row">

            <div class="label">
                Withdrawal ID
            </div>

            {{ withdrawal["id"] }}

        </div>


        <div class="row">

            <div class="label">
                Amount
            </div>

            ₦{{ "{:,.2f}".format(
                withdrawal["amount"] or 0
            ) }}

        </div>


        <div class="row">

            <div class="label">
                Bank
            </div>

            {{ withdrawal["bank_name"] or "" }}

        </div>


        <div class="row">

            <div class="label">
                Account
            </div>

            {{ mask_account(
                withdrawal["account_number"]
            ) }}

        </div>


        <div class="row">

            <div class="label">
                Status
            </div>

            {{ withdrawal["status"] or "" }}

        </div>


        <div class="row">

            <div class="label">
                Transfer Status
            </div>

            {{ withdrawal["transfer_status"] or "" }}

        </div>


        <div class="row">

            <div class="label">
                Transfer Reference
            </div>

            {{ withdrawal["transfer_reference"] or "" }}

        </div>


        {% if withdrawal["transfer_message"] %}

        <div class="row">

            <div class="label">
                Message
            </div>

            {{ withdrawal["transfer_message"] }}

        </div>

        {% endif %}


        {% if can_refresh %}

        <form
            method="POST"
            action="{{ url_for(
                'promoter_withdrawal_status',
                withdrawal_id=withdrawal['id']
            ) }}"
        >

            <input
                type="hidden"
                name="csrf_token"
                value="{{ csrf_token }}"
            >

            <button type="submit">
                🔄 Refresh Status
            </button>

        </form>

        {% endif %}


        <a
            href="{{ url_for('referral_dashboard') }}"
        >
            ← Back to Dashboard
        </a>

    </div>

</div>

</body>
</html>
"""


# ============================================================
# WITHDRAWAL PAGE
# ============================================================

@promoter_required
def withdrawal_page():

    promoter = _current_promoter()

    if not promoter:

        return redirect(
            url_for(
                "promoter_login"
            )
        )

    if request.method != "POST":

        return redirect(
            url_for(
                "referral_dashboard"
            )
        )


    # ========================================================
    # CSRF
    # ========================================================

    if not _check_csrf():

        flash(
            "Invalid security token. Please try again.",
            "error",
        )

        return redirect(
            url_for(
                "referral_dashboard"
            )
        )


    # ========================================================
    # AMOUNT
    # ========================================================

    amount_raw = request.form.get(
        "amount",
        "",
    ).strip()

    try:

        amount = float(
            amount_raw
        )

    except Exception:

        flash(
            "Invalid withdrawal amount.",
            "error",
        )

        return redirect(
            url_for(
                "referral_dashboard"
            )
        )


    if amount <= 0:

        flash(
            "Withdrawal amount must be greater than zero.",
            "error",
        )

        return redirect(
            url_for(
                "referral_dashboard"
            )
        )


    if amount < MINIMUM_WITHDRAWAL:

        flash(
            (
                f"Minimum withdrawal is "
                f"₦{MINIMUM_WITHDRAWAL:,.2f}."
            ),
            "error",
        )

        return redirect(
            url_for(
                "referral_dashboard"
            )
        )


    # ========================================================
    # AVAILABLE BALANCE
    # ========================================================

    available_balance = _safe_money(
        _row_get(
            promoter,
            "available_balance",
            0,
        )
    )


    if amount > available_balance:

        flash(
            (
                "Insufficient available balance. "
                f"Your available balance is "
                f"₦{available_balance:,.2f}."
            ),
            "error",
        )

        return redirect(
            url_for(
                "referral_dashboard"
            )
        )


    # ========================================================
    # WITHDRAWAL CODE
    # ========================================================

    withdrawal_code = request.form.get(
        "withdrawal_code",
        "",
    ).strip()


    if not withdrawal_code:

        flash(
            "Withdrawal Code is required.",
            "error",
        )

        return redirect(
            url_for(
                "referral_dashboard"
            )
        )


    # ========================================================
    # VERIFY WITHDRAWAL CODE
    #
    # BEFORE bank resolve
    # BEFORE withdrawal creation
    # BEFORE balance reservation
    # ========================================================

    try:

        code_valid = verify_promoter_withdrawal_code(
            promoter["id"],
            withdrawal_code,
        )

    except Exception:

        logger.exception(
            "Withdrawal code verification failed"
        )

        code_valid = False


    if not code_valid:

        flash(
            "❌ Incorrect Withdrawal Code.",
            "error",
        )

        return redirect(
            url_for(
                "referral_dashboard"
            )
        )


    # ========================================================
    # BANK CODE
    # ========================================================

    bank_code = request.form.get(
        "bank_code",
        "",
    ).strip()


    if not bank_code:

        flash(
            "Please select your bank.",
            "error",
        )

        return redirect(
            url_for(
                "referral_dashboard"
            )
        )


    # ========================================================
    # ACCOUNT NUMBER
    # ========================================================

    account_number = (
        request.form.get(
            "account_number",
            "",
        )
        .strip()
        .replace(" ", "")
    )


    if (
        not account_number.isdigit()
        or len(account_number) != 10
    ):

        flash(
            "Account number must contain exactly 10 digits.",
            "error",
        )

        return redirect(
            url_for(
                "referral_dashboard"
            )
        )


    # ========================================================
    # GET BANK NAME
    # ========================================================

    bank_name = bank_code

    try:

        banks = (
            get_flutterwave_banks()
            or []
        )

        for bank in banks:

            code = str(
                bank.get(
                    "code",
                    "",
                )
            ).strip()

            if code == bank_code:

                bank_name = (
                    bank.get("name")
                    or bank_code
                )

                break

    except Exception:

        logger.exception(
            "Unable to identify bank name"
        )


    # ========================================================
    # RESOLVE BANK ACCOUNT
    # ========================================================

    try:

        resolved = resolve_bank_account(
            account_number=account_number,
            bank_code=bank_code,
        )

    except TypeError:

        try:

            resolved = resolve_bank_account(
                bank_code,
                account_number,
            )

        except Exception:

            logger.exception(
                "Bank account resolve failed"
            )

            flash(
                (
                    "Unable to verify bank account. "
                    "Please check your bank and account number."
                ),
                "error",
            )

            return redirect(
                url_for(
                    "referral_dashboard"
                )
            )

    except Exception:

        logger.exception(
            "Bank account resolve failed"
        )

        flash(
            (
                "Unable to verify bank account. "
                "Please check your bank and account number."
            ),
            "error",
        )

        return redirect(
            url_for(
                "referral_dashboard"
            )
        )


    if not resolved:

        flash(
            "Bank account could not be verified.",
            "error",
        )

        return redirect(
            url_for(
                "referral_dashboard"
            )
        )


    # ========================================================
    # ACCOUNT NAME
    # ========================================================

    account_name = ""


    if isinstance(
        resolved,
        dict,
    ):

        account_name = (
            resolved.get(
                "account_name"
            )
            or resolved.get(
                "accountName"
            )
            or ""
        )


        if not account_name:

            data = resolved.get(
                "data"
            )

            if isinstance(
                data,
                dict,
            ):

                account_name = (
                    data.get(
                        "account_name"
                    )
                    or data.get(
                        "accountName"
                    )
                    or ""
                )

    else:

        account_name = str(
            resolved
        )


    if not account_name:

        flash(
            "Bank account name could not be verified.",
            "error",
        )

        return redirect(
            url_for(
                "referral_dashboard"
            )
        )


    # ========================================================
    # CREATE WITHDRAWAL
    # ========================================================

    try:

        withdrawal_id = create_withdrawal(
            promoter_id=promoter["id"],
            amount=amount,
            bank_name=bank_name,
            bank_code=bank_code,
            account_name=account_name,
            account_number=account_number,
        )

    except Exception:

        logger.exception(
            "Create withdrawal failed"
        )

        flash(
            "Unable to create withdrawal. Please try again.",
            "error",
        )

        return redirect(
            url_for(
                "referral_dashboard"
            )
        )


    if not withdrawal_id:

        flash(
            "Withdrawal request could not be created.",
            "error",
        )

        return redirect(
            url_for(
                "referral_dashboard"
            )
        )


    # ========================================================
    # STABLE TRANSFER REFERENCE
    # ========================================================

    transfer_reference = (
        f"ALHIKAM-WD-{withdrawal_id}"
    )


    try:

        update_withdrawal_transfer(
            withdrawal_id=withdrawal_id,
            transfer_reference=transfer_reference,
        )

    except TypeError:

        try:

            update_withdrawal_transfer(
                withdrawal_id,
                transfer_reference,
                None,
                "PENDING",
            )

        except Exception:

            logger.exception(
                "Unable to save transfer reference"
            )

    except Exception:

        logger.exception(
            "Unable to save transfer reference"
        )


    # ========================================================
    # CREATE FLUTTERWAVE TRANSFER
    # ========================================================

    try:

        transfer_result = create_flutterwave_transfer(
            amount=amount,
            bank_code=bank_code,
            account_number=account_number,
            account_name=account_name,
            reference=transfer_reference,
        )

    except TypeError:

        try:

            transfer_result = create_flutterwave_transfer(
                amount,
                bank_code,
                account_number,
                account_name,
                transfer_reference,
            )

        except Exception as e:

            logger.exception(
                "Flutterwave transfer failed"
            )

            transfer_result = {
                "status": "failed",
                "message": str(e),
            }

    except Exception as e:

        logger.exception(
            "Flutterwave transfer failed"
        )

        transfer_result = {
            "status": "failed",
            "message": str(e),
        }


    # ========================================================
    # PROCESS TRANSFER RESULT
    # ========================================================

    try:

        process_transfer_result(
            withdrawal_id=withdrawal_id,
            result=transfer_result,
        )

    except TypeError:

        try:

            process_transfer_result(
                withdrawal_id,
                transfer_result,
            )

        except Exception:

            logger.exception(
                "Processing transfer result failed"
            )

    except Exception:

        logger.exception(
            "Processing transfer result failed"
        )


    # ========================================================
    # REDIRECT TO STATUS
    # ========================================================

    return redirect(
        url_for(
            "promoter_withdrawal_status",
            withdrawal_id=withdrawal_id,
        )
    )


# ============================================================
# WITHDRAWAL STATUS PAGE
# ============================================================

@promoter_required
def withdrawal_status_page(withdrawal_id):

    promoter = _current_promoter()

    if not promoter:

        return redirect(
            url_for(
                "promoter_login"
            )
        )


    try:

        withdrawal_id = int(
            withdrawal_id
        )

    except Exception:

        return (
            "Invalid withdrawal ID.",
            400,
        )


    withdrawal = get_withdrawal_by_id(
        withdrawal_id
    )


    if not withdrawal:

        return (
            "Withdrawal not found.",
            404,
        )


    # ========================================================
    # OWNERSHIP CHECK
    # ========================================================

    withdrawal_promoter_id = _row_get(
        withdrawal,
        "promoter_id",
    )


    if str(
        withdrawal_promoter_id
    ) != str(
        promoter["id"]
    ):

        return (
            "Unauthorized.",
            403,
        )


    # ========================================================
    # AUTO REFRESH PROCESSING TRANSFER
    # ========================================================

    current_status = str(
        _row_get(
            withdrawal,
            "status",
            "",
        )
        or ""
    ).upper()


    transfer_status = str(
        _row_get(
            withdrawal,
            "transfer_status",
            "",
        )
        or ""
    ).upper()


    transfer_id = str(
        _row_get(
            withdrawal,
            "transfer_id",
            "",
        )
        or ""
    ).strip()


    transfer_reference = str(
        _row_get(
            withdrawal,
            "transfer_reference",
            "",
        )
        or ""
    ).strip()


    processing_statuses = {
        "PENDING",
        "PROCESSING",
        "NEW",
        "QUEUED",
    }


    if (
        current_status in processing_statuses
        or transfer_status in processing_statuses
    ):

        result = None


        # ----------------------------------------------------
        # FIRST: TRANSFER ID
        # ----------------------------------------------------

        if transfer_id:

            try:

                result = (
                    get_flutterwave_transfer_status(
                        transfer_id
                    )
                )

            except Exception:

                logger.exception(
                    "Transfer ID status refresh failed"
                )


        # ----------------------------------------------------
        # SECOND: TRANSFER REFERENCE
        # ----------------------------------------------------

        if (
            not result
            and transfer_reference
        ):

            try:

                result = (
                    get_flutterwave_transfer_status_by_reference(
                        transfer_reference
                    )
                )

            except Exception:

                logger.exception(
                    "Transfer reference status refresh failed"
                )


        # ----------------------------------------------------
        # PROCESS RESULT
        # ----------------------------------------------------

        if result:

            try:

                process_transfer_result(
                    withdrawal_id=withdrawal_id,
                    result=result,
                )

            except TypeError:

                try:

                    process_transfer_result(
                        withdrawal_id,
                        result,
                    )

                except Exception:

                    logger.exception(
                        "Unable to process refreshed transfer result"
                    )

            except Exception:

                logger.exception(
                    "Unable to process refreshed transfer result"
                )


            # ------------------------------------------------
            # RELOAD LATEST WITHDRAWAL
            # ------------------------------------------------

            withdrawal = get_withdrawal_by_id(
                withdrawal_id
            )


    # ========================================================
    # CAN REFRESH?
    # ========================================================

    latest_status = str(
        _row_get(
            withdrawal,
            "status",
            "",
        )
        or ""
    ).upper()


    latest_transfer_status = str(
        _row_get(
            withdrawal,
            "transfer_status",
            "",
        )
        or ""
    ).upper()


    can_refresh = (
        latest_status in processing_statuses
        or latest_transfer_status in processing_statuses
    )


    return render_template_string(
        WITHDRAWAL_STATUS_HTML,
        withdrawal=withdrawal,
        csrf_token=_csrf_token(),
        can_refresh=can_refresh,
        mask_account=_mask_account,
    )


# ============================================================
# COMPATIBILITY ALIASES
# ============================================================

promoter_login = promoter_login_page

promoter_logout = promoter_logout_page

withdrawal_status = withdrawal_status_page