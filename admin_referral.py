# ============================================================
# ALHIKAM LEARNING CENTER V2
# admin_referral.py
#
# SECURE ADMIN REFERRAL DASHBOARD
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

from transfer import get_flutterwave_transfer_status


# ============================================================
# LOGGER
# ============================================================

logger = logging.getLogger(__name__)


# ============================================================
# ADMIN CONFIG
# ============================================================

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

ADMIN_SESSION_KEY = "alhikam_admin_logged_in"
ADMIN_CSRF_KEY = "alhikam_admin_csrf"


# ============================================================
# ADMIN AUTH
# ============================================================

def admin_logged_in():
    return session.get(ADMIN_SESSION_KEY) is True


def admin_required(view_func):

    @wraps(view_func)
    def wrapped(*args, **kwargs):

        if not admin_logged_in():
            return redirect(url_for("admin_referral_login"))

        return view_func(*args, **kwargs)

    return wrapped


# ============================================================
# CSRF
# ============================================================

def get_admin_csrf_token():

    token = session.get(ADMIN_CSRF_KEY)

    if not token:
        token = secrets.token_urlsafe(32)
        session[ADMIN_CSRF_KEY] = token

    return token


def validate_admin_csrf():

    token = request.form.get("csrf_token", "")

    session_token = session.get(ADMIN_CSRF_KEY, "")

    if (
        not token
        or not session_token
        or not secrets.compare_digest(token, session_token)
    ):
        abort(403)

    return True


# ============================================================
# ACCOUNT NUMBER MASKING
# ============================================================

def mask_account_number(account_number):

    if not account_number:
        return ""

    account_number = str(account_number)

    if len(account_number) <= 4:
        return "*" * len(account_number)

    return (
        "*" * (len(account_number) - 4)
        + account_number[-4:]
    )


# ============================================================
# LOGIN PAGE
# ============================================================

ADMIN_LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<title>Alhikam Admin Login</title>

<style>

body {
    margin: 0;
    padding: 0;
    font-family: Arial, sans-serif;
    background: #f3f4f6;
}

.container {
    max-width: 420px;
    margin: 80px auto;
    padding: 20px;
}

.card {
    background: white;
    padding: 30px;
    border-radius: 15px;
    box-shadow: 0 8px 30px rgba(0,0,0,.08);
}

h1 {
    text-align: center;
    margin-bottom: 10px;
}

.subtitle {
    text-align: center;
    color: #666;
    margin-bottom: 25px;
}

input {
    width: 100%;
    box-sizing: border-box;
    padding: 13px;
    margin-bottom: 15px;
    border: 1px solid #ddd;
    border-radius: 8px;
    font-size: 16px;
}

button {
    width: 100%;
    padding: 13px;
    border: none;
    border-radius: 8px;
    background: #111827;
    color: white;
    font-size: 16px;
    cursor: pointer;
}

button:hover {
    opacity: .9;
}

.error {
    background: #fee2e2;
    color: #991b1b;
    padding: 12px;
    border-radius: 8px;
    margin-bottom: 15px;
}

</style>

</head>

<body>

<div class="container">

<div class="card">

<h1>Alhikam Admin</h1>

<div class="subtitle">
Referral Dashboard Login
</div>

{% if error %}

<div class="error">
{{ error }}
</div>

{% endif %}

<form method="POST"
      action="{{ url_for('admin_referral_login') }}">

<input
    type="password"
    name="password"
    placeholder="Admin password"
    required
    autocomplete="current-password"
>

<input
    type="hidden"
    name="csrf_token"
    value="{{ csrf_token }}"
>

<button type="submit">
Login
</button>

</form>

</div>

</div>

</body>
</html>
"""


def admin_login_page():

    if admin_logged_in():
        return redirect(url_for("admin_referral"))

    error = None

    if request.method == "POST":

        token = request.form.get("csrf_token", "")

        session_token = session.get(ADMIN_CSRF_KEY, "")

        if (
            not token
            or not session_token
            or not secrets.compare_digest(
                token,
                session_token,
            )
        ):
            abort(403)

        password = request.form.get(
            "password",
            "",
        )

        if (
            ADMIN_PASSWORD
            and secrets.compare_digest(
                password,
                ADMIN_PASSWORD,
            )
        ):

            session[ADMIN_SESSION_KEY] = True

            session[ADMIN_CSRF_KEY] = secrets.token_urlsafe(32)

            return redirect(
                url_for("admin_referral")
            )

        error = "Invalid admin password."

    return render_template_string(
        ADMIN_LOGIN_HTML,
        error=error,
        csrf_token=get_admin_csrf_token(),
    )


# ============================================================
# LOGOUT
# ============================================================

def admin_logout_page():

    if request.method != "POST":
        abort(405)

    validate_admin_csrf()

    session.pop(
        ADMIN_SESSION_KEY,
        None,
    )

    session.pop(
        ADMIN_CSRF_KEY,
        None,
    )

    return redirect(
        url_for("admin_referral_login")
    )


# ============================================================
# DASHBOARD HTML
# ============================================================

ADMIN_DASHBOARD_HTML = """
<!DOCTYPE html>
<html>

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<title>Alhikam Referral Admin</title>

<style>

body {
    margin: 0;
    font-family: Arial, sans-serif;
    background: #f5f7fb;
    color: #111827;
}

.header {
    background: #111827;
    color: white;
    padding: 18px;
}

.header-inner {
    max-width: 1200px;
    margin: auto;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 15px;
}

.header h1 {
    margin: 0;
    font-size: 21px;
}

.logout button {
    background: #dc2626;
    color: white;
    border: none;
    padding: 10px 15px;
    border-radius: 7px;
    cursor: pointer;
}

.container {
    max-width: 1200px;
    margin: 25px auto;
    padding: 0 15px;
}

.card {
    background: white;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: 0 4px 18px rgba(0,0,0,.06);
}

.card h2 {
    margin-top: 0;
}

.form-grid {
    display: grid;
    grid-template-columns:
        repeat(auto-fit, minmax(180px, 1fr));
    gap: 12px;
}

input,
select {
    width: 100%;
    box-sizing: border-box;
    padding: 11px;
    border: 1px solid #ddd;
    border-radius: 7px;
}

.btn {
    border: none;
    padding: 11px 15px;
    border-radius: 7px;
    cursor: pointer;
    background: #111827;
    color: white;
}

.btn-green {
    background: #16a34a;
}

.btn-blue {
    background: #2563eb;
}

.btn-red {
    background: #dc2626;
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
    background: #f9fafb;
}

.badge {
    display: inline-block;
    padding: 5px 9px;
    border-radius: 999px;
    font-size: 12px;
}

.pending {
    background: #fef3c7;
    color: #92400e;
}

.processing {
    background: #dbeafe;
    color: #1e40af;
}

.success {
    background: #dcfce7;
    color: #166534;
}

.failed {
    background: #fee2e2;
    color: #991b1b;
}

.message {
    padding: 12px;
    border-radius: 8px;
    margin-bottom: 15px;
    background: #ecfdf5;
    color: #065f46;
}

</style>

</head>

<body>

<div class="header">

<div class="header-inner">

<h1>
Alhikam Learning Center — Admin
</h1>

<form method="POST"
      class="logout"
      action="{{ url_for('admin_referral_logout') }}">

<input
    type="hidden"
    name="csrf_token"
    value="{{ csrf_token }}"
>

<button type="submit">
Logout
</button>

</form>

</div>

</div>


<div class="container">


{% if message %}

<div class="message">
{{ message }}
</div>

{% endif %}


<!-- ======================================================
     CREATE PROMOTER
     ====================================================== -->

<div class="card">

<h2>
Create Promoter
</h2>

<form method="POST"
      action="{{ url_for('admin_create_promoter') }}">

<input
    type="hidden"
    name="csrf_token"
    value="{{ csrf_token }}"
>

<div class="form-grid">

<div>
<input
    type="text"
    name="full_name"
    placeholder="Full name"
    required
>
</div>

<div>
<input
    type="text"
    name="phone"
    placeholder="Phone number"
    required
>
</div>

<div>
<input
    type="email"
    name="email"
    placeholder="Email"
>
</div>

<div>
<input
    type="number"
    name="commission_rate"
    placeholder="Commission rate %"
    min="0"
    max="100"
    step="0.01"
    value="10"
    required
>
</div>

<div>
<input
    type="password"
    name="password"
    placeholder="Promoter password"
    minlength="6"
    required
>
</div>

<div>
<button
    type="submit"
    class="btn btn-green"
>
Create Promoter
</button>
</div>

</div>

</form>

</div>


<!-- ======================================================
     PROMOTERS
     ====================================================== -->

<div class="card">

<h2>
Promoters
</h2>

<div class="table-wrap">

<table>

<thead>

<tr>

<th>ID</th>
<th>Name</th>
<th>Phone</th>
<th>Email</th>
<th>Referral Code</th>
<th>Commission Rate</th>
<th>Total Sales</th>
<th>Available Balance</th>
<th>Withdrawn</th>

</tr>

</thead>

<tbody>

{% for promoter in promoters %}

<tr>

<td>
{{ promoter.id }}
</td>

<td>
{{ promoter.full_name }}
</td>

<td>
{{ promoter.phone }}
</td>

<td>
{{ promoter.email or "-" }}
</td>

<td>
{{ promoter.referral_code }}
</td>

<td>
{{ promoter.commission_rate }}%
</td>

<td>
₦{{ "{:,.2f}".format(promoter.total_sales or 0) }}
</td>

<td>
₦{{ "{:,.2f}".format(promoter.available_balance or 0) }}
</td>

<td>
₦{{ "{:,.2f}".format(promoter.withdrawn_amount or 0) }}
</td>

</tr>

{% else %}

<tr>

<td colspan="9">
No promoters found.
</td>

</tr>

{% endfor %}

</tbody>

</table>

</div>

</div>


<!-- ======================================================
     WITHDRAWALS
     ====================================================== -->

<div class="card">

<h2>
Withdrawal Requests
</h2>

<div class="table-wrap">

<table>

<thead>

<tr>

<th>ID</th>
<th>Promoter</th>
<th>Amount</th>
<th>Bank</th>
<th>Account</th>
<th>Status</th>
<th>Transfer ID</th>
<th>Action</th>

</tr>

</thead>

<tbody>

{% for withdrawal in withdrawals %}

<tr>

<td>
{{ withdrawal.id }}
</td>

<td>
{{ withdrawal.promoter_name or withdrawal.promoter_id }}
</td>

<td>
₦{{ "{:,.2f}".format(withdrawal.amount or 0) }}
</td>

<td>
{{ withdrawal.bank_name or "-" }}
</td>

<td>
{{ mask_account_number(withdrawal.account_number) }}
</td>

<td>

{% set status = (withdrawal.status or "pending")|lower %}

<span class="badge {{ status }}">

{{ withdrawal.status }}

</span>

</td>

<td>
{{ withdrawal.transfer_id or "-" }}
</td>

<td>

<form method="POST"
      action="{{ url_for('admin_withdrawal_status') }}">

<input
    type="hidden"
    name="csrf_token"
    value="{{ csrf_token }}"
>

<input
    type="hidden"
    name="withdrawal_id"
    value="{{ withdrawal.id }}"
>

<select name="status">

<option value="processing">
Processing
</option>

<option value="success">
Success
</option>

<option value="failed">
Failed
</option>

</select>

<br><br>

<button
    type="submit"
    class="btn btn-blue"
>
Update
</button>

</form>

</td>

</tr>

{% else %}

<tr>

<td colspan="8">
No withdrawal requests found.
</td>

</tr>

{% endfor %}

</tbody>

</table>

</div>

</div>


</div>

</body>

</html>
"""


# ============================================================
# ADMIN REFERRAL DASHBOARD
# ============================================================

@admin_required
def admin_referral_page():

    try:

        promoters = get_all_promoters()

        withdrawals = get_all_withdrawals()

        message = session.pop(
            "admin_message",
            None,
        )

        return render_template_string(
            ADMIN_DASHBOARD_HTML,
            promoters=promoters,
            withdrawals=withdrawals,
            csrf_token=get_admin_csrf_token(),
            mask_account_number=mask_account_number,
            message=message,
        )

    except Exception:

        logger.exception(
            "Error loading admin referral dashboard"
        )

        raise


# ============================================================
# CREATE PROMOTER
# ============================================================

@admin_required
def create_promoter_page():

    if request.method != "POST":
        abort(405)

    validate_admin_csrf()

    full_name = request.form.get(
        "full_name",
        "",
    ).strip()

    phone = request.form.get(
        "phone",
        "",
    ).strip()

    email = request.form.get(
        "email",
        "",
    ).strip()

    commission_rate_raw = request.form.get(
        "commission_rate",
        "10",
    ).strip()

    password = request.form.get(
        "password",
        "",
    )

    if not full_name:
        abort(400)

    if not phone:
        abort(400)

    if not password or len(password) < 6:
        abort(400)

    try:

        commission_rate = float(
            commission_rate_raw
        )

    except ValueError:

        abort(400)

    if commission_rate < 0 or commission_rate > 100:
        abort(400)

    try:

        promoter_id = add_promoter(
            full_name=full_name,
            phone=phone,
            email=email,
            commission_rate=commission_rate,
        )

        set_promoter_password(
            promoter_id,
            password,
        )

        session["admin_message"] = (
            "Promoter created successfully."
        )

        return redirect(
            url_for("admin_referral")
        )

    except Exception:

        logger.exception(
            "Failed to create promoter"
        )

        raise


# ============================================================
# REFRESH WITHDRAWAL STATUS
# ============================================================

def refresh_withdrawal_status(withdrawal_id):

    withdrawal = get_withdrawal_by_id(
        withdrawal_id
    )

    if not withdrawal:
        return None

    transfer_id = withdrawal.get(
        "transfer_id"
    )

    if not transfer_id:
        return withdrawal

    try:

        result = get_flutterwave_transfer_status(
            transfer_id
        )

        if not result:
            return withdrawal

        status = (
            result.get("status")
            or result.get("data", {}).get("status")
        )

        if not status:
            return withdrawal

        status = str(status).lower()

        if status in (
            "successful",
            "success",
            "completed",
        ):

            update_withdrawal_status(
                withdrawal_id,
                "success",
            )

        elif status in (
            "failed",
            "cancelled",
            "canceled",
        ):

            update_withdrawal_status(
                withdrawal_id,
                "failed",
            )

        elif status in (
            "pending",
            "processing",
        ):

            update_withdrawal_status(
                withdrawal_id,
                "processing",
            )

    except Exception:

        logger.exception(
            "Failed to refresh withdrawal status: %s",
            withdrawal_id,
        )

    return get_withdrawal_by_id(
        withdrawal_id
    )


# ============================================================
# ADMIN WITHDRAWAL STATUS
# ============================================================

@admin_required
def admin_withdrawal_status_page():

    if request.method != "POST":
        abort(405)

    validate_admin_csrf()

    withdrawal_id = request.form.get(
        "withdrawal_id",
        "",
    ).strip()

    new_status = request.form.get(
        "status",
        "",
    ).strip().lower()

    if not withdrawal_id:
        abort(400)

    allowed_statuses = {
        "processing",
        "success",
        "failed",
    }

    if new_status not in allowed_statuses:
        abort(400)

    withdrawal = get_withdrawal_by_id(
        withdrawal_id
    )

    if not withdrawal:
        abort(404)

    try:

        # ----------------------------------------------------
        # Manual processing status
        # ----------------------------------------------------

        if new_status == "processing":

            update_withdrawal_status(
                withdrawal_id,
                "processing",
            )

            session["admin_message"] = (
                "Withdrawal marked as processing."
            )

            return redirect(
                url_for("admin_referral")
            )

        # ----------------------------------------------------
        # SUCCESS / FAILED
        # ----------------------------------------------------

        transfer_id = withdrawal.get(
            "transfer_id"
        )

        if not transfer_id:

            session["admin_message"] = (
                "No Flutterwave transfer ID was found."
            )

            return redirect(
                url_for("admin_referral")
            )

        result = get_flutterwave_transfer_status(
            transfer_id
        )

        if not result:

            session["admin_message"] = (
                "Unable to verify Flutterwave transfer."
            )

            return redirect(
                url_for("admin_referral")
            )

        flutterwave_status = (
            result.get("status")
            or result.get("data", {}).get("status")
        )

        if not flutterwave_status:

            session["admin_message"] = (
                "Flutterwave did not return a transfer status."
            )

            return redirect(
                url_for("admin_referral")
            )

        flutterwave_status = str(
            flutterwave_status
        ).lower()

        # ----------------------------------------------------
        # SUCCESS
        # ----------------------------------------------------

        if new_status == "success":

            if flutterwave_status not in (
                "successful",
                "success",
                "completed",
            ):

                session["admin_message"] = (
                    "Cannot mark withdrawal as successful "
                    "because Flutterwave has not confirmed it."
                )

                return redirect(
                    url_for("admin_referral")
                )

            update_withdrawal_status(
                withdrawal_id,
                "success",
            )

            session["admin_message"] = (
                "Withdrawal successfully confirmed."
            )

        # ----------------------------------------------------
        # FAILED
        # ----------------------------------------------------

        elif new_status == "failed":

            if flutterwave_status not in (
                "failed",
                "cancelled",
                "canceled",
            ):

                session["admin_message"] = (
                    "Cannot mark withdrawal as failed "
                    "because Flutterwave has not confirmed failure."
                )

                return redirect(
                    url_for("admin_referral")
                )

            update_withdrawal_status(
                withdrawal_id,
                "failed",
            )

            session["admin_message"] = (
                "Withdrawal marked as failed."
            )

        return redirect(
            url_for("admin_referral")
        )

    except Exception:

        logger.exception(
            "Failed to update withdrawal status"
        )

        raise