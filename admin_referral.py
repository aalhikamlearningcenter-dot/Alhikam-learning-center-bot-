# ============================================================
# ALHIKAM LEARNING CENTER
# ADMIN REFERRAL DASHBOARD
#
# Features:
# - Secure Admin Login
# - Admin Password Protection
# - CSRF Protection
# - Create Promoter
# - Main Payment Link
# - Individual Referral Link
# - Individual Referral Payment Link
# - Promoter Dashboard Link
# - Copy Buttons
# - Withdrawal Status Refresh
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


# ============================================================
# LOGGER
# ============================================================

logger = logging.getLogger(__name__)


# ============================================================
# ADMIN PASSWORD
# ============================================================

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")


# ============================================================
# SESSION KEYS
# ============================================================

ADMIN_SESSION_KEY = "alhikam_admin_logged_in"
ADMIN_CSRF_KEY = "alhikam_admin_csrf"


# ============================================================
# ADMIN LOGIN CHECK
# ============================================================

def admin_logged_in():

    return bool(
        session.get(
            ADMIN_SESSION_KEY
        )
    )


# ============================================================
# ADMIN REQUIRED
# ============================================================

def admin_required(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        if not admin_logged_in():

            return redirect(
                url_for(
                    "admin_referral_login",
                    next=request.path,
                )
            )

        return function(
            *args,
            **kwargs
        )

    return wrapper


# ============================================================
# CSRF
# ============================================================

def get_admin_csrf():

    token = session.get(
        ADMIN_CSRF_KEY
    )

    if not token:

        token = secrets.token_urlsafe(32)

        session[ADMIN_CSRF_KEY] = token

    return token


def check_admin_csrf():

    submitted = request.form.get(
        "csrf_token",
        ""
    )

    expected = session.get(
        ADMIN_CSRF_KEY,
        ""
    )

    if not submitted or not expected:

        return False

    return secrets.compare_digest(
        submitted,
        expected
    )


# ============================================================
# MASK ACCOUNT NUMBER
# ============================================================

def mask_account_number(account_number):

    value = str(
        account_number or ""
    )

    if len(value) <= 4:

        return "****"

    return (
        "*" * (len(value) - 4)
        + value[-4:]
    )


# ============================================================
# ADMIN LOGIN HTML
# ============================================================

ADMIN_LOGIN_HTML = """

<!DOCTYPE html>

<html>

<head>

<meta name="viewport"
      content="width=device-width, initial-scale=1">

<title>ALHIKAM Admin Login</title>

<style>

*{
    box-sizing:border-box;
}

body{

    font-family:Arial,sans-serif;

    background:#f4f7f6;

    margin:0;

    padding:20px;

}

.container{

    max-width:420px;

    margin:80px auto;

    background:white;

    padding:30px;

    border-radius:16px;

    box-shadow:0 4px 20px rgba(0,0,0,.10);

}

h1{

    text-align:center;

    color:#087f5b;

    margin-top:0;

}

.subtitle{

    text-align:center;

    color:#666;

    margin-bottom:25px;

}

input{

    width:100%;

    padding:14px;

    margin-top:10px;

    border:1px solid #ddd;

    border-radius:8px;

    font-size:16px;

}

button{

    width:100%;

    padding:14px;

    margin-top:18px;

    border:none;

    border-radius:8px;

    background:#087f5b;

    color:white;

    font-size:16px;

    font-weight:bold;

    cursor:pointer;

}

button:hover{

    opacity:.9;

}

.error{

    background:#ffe8e8;

    color:#b00020;

    padding:12px;

    border-radius:8px;

    margin-bottom:15px;

}

.security{

    margin-top:20px;

    text-align:center;

    font-size:13px;

    color:#777;

}

</style>

</head>

<body>

<div class="container">

<h1>
🔐 ALHIKAM ADMIN
</h1>

<div class="subtitle">
Secure Administrator Login
</div>

{% if error %}

<div class="error">
{{ error }}
</div>

{% endif %}

<form method="POST"
      action="{{ url_for('admin_referral_login') }}">

<input
    type="hidden"
    name="csrf_token"
    value="{{ csrf_token }}"
>

<input
    type="hidden"
    name="next"
    value="{{ next_url }}"
>

<label>
<strong>Admin Password</strong>
</label>

<input
    type="password"
    name="password"
    placeholder="Enter admin password"
    required
    autocomplete="current-password"
>

<button type="submit">
🔓 LOGIN
</button>

</form>

<div class="security">
🛡️ Authorized administrators only.
</div>

</div>

</body>

</html>

"""


# ============================================================
# ADMIN LOGIN
# ============================================================

def admin_login_page():

    if admin_logged_in():

        return redirect(
            url_for(
                "admin_referral"
            )
        )

    if request.method == "GET":

        return render_template_string(

            ADMIN_LOGIN_HTML,

            csrf_token=get_admin_csrf(),

            error="",

            next_url=request.args.get(
                "next",
                "",
            ),

        )

    if not ADMIN_PASSWORD:

        logger.error(
            "ADMIN_PASSWORD is not configured."
        )

        return (
            "Admin password is not configured.",
            500,
        )

    if not check_admin_csrf():

        return render_template_string(

            ADMIN_LOGIN_HTML,

            csrf_token=get_admin_csrf(),

            error=(
                "Invalid security token. "
                "Please refresh and try again."
            ),

            next_url=request.form.get(
                "next",
                "",
            ),

        ), 400

    password = request.form.get(
        "password",
        ""
    )

    if not secrets.compare_digest(
        password,
        ADMIN_PASSWORD,
    ):

        return render_template_string(

            ADMIN_LOGIN_HTML,

            csrf_token=get_admin_csrf(),

            error="❌ Incorrect admin password.",

            next_url=request.form.get(
                "next",
                "",
            ),

        ), 401

    session[
        ADMIN_SESSION_KEY
    ] = True

    session[
        ADMIN_CSRF_KEY
    ] = secrets.token_urlsafe(32)

    session.permanent = True

    next_url = request.form.get(
        "next",
        ""
    ).strip()

    if (
        next_url
        and next_url.startswith("/")
        and not next_url.startswith("//")
    ):

        return redirect(next_url)

    return redirect(
        url_for(
            "admin_referral"
        )
    )


# ============================================================
# ADMIN LOGOUT
# ============================================================

@admin_required
def admin_logout_page():

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


# ============================================================
# ADMIN DASHBOARD HTML
# ============================================================

ADMIN_DASHBOARD_HTML = """

<!DOCTYPE html>

<html>

<head>

<meta name="viewport"
      content="width=device-width, initial-scale=1">

<title>
ALHIKAM Learning Center Admin
</title>

<style>

*{
    box-sizing:border-box;
}

body{

    font-family:Arial,sans-serif;

    background:#f4f7f6;

    margin:0;

    padding:20px;

}

.container{

    max-width:1250px;

    margin:auto;

}

.header{

    background:white;

    padding:20px;

    border-radius:14px;

    margin-bottom:20px;

    display:flex;

    justify-content:space-between;

    align-items:center;

    gap:15px;

    flex-wrap:wrap;

    box-shadow:0 3px 15px rgba(0,0,0,.08);

}

.header h1{

    margin:0;

    color:#087f5b;

}

.header-subtitle{

    color:#666;

    margin-top:5px;

    font-size:13px;

}

.logout{

    margin:0;

}

.logout button{

    background:#c62828;

    width:auto;

}

.card{

    background:white;

    padding:20px;

    border-radius:14px;

    margin-bottom:20px;

    box-shadow:0 3px 15px rgba(0,0,0,.08);

}

.card h2{

    margin-top:0;

    color:#087f5b;

}

.link-card{

    border-left:5px solid #087f5b;

}

input,
select{

    width:100%;

    box-sizing:border-box;

    padding:12px;

    margin:7px 0 13px;

    border:1px solid #ddd;

    border-radius:8px;

    font-size:15px;

}

button{

    padding:11px 16px;

    border:none;

    border-radius:8px;

    background:#087f5b;

    color:white;

    font-weight:bold;

    cursor:pointer;

}

button:hover{

    opacity:.9;

}

.copy-btn{

    background:#1565c0;

    white-space:nowrap;

}

.link-box{

    display:flex;

    gap:8px;

    align-items:center;

    margin-top:8px;

}

.link-box input{

    flex:1;

    margin:0;

    background:#f7f7f7;

}

.small{

    font-size:13px;

    color:#666;

    line-height:1.5;

}

.code{

    font-weight:bold;

    color:#087f5b;

    word-break:break-all;

}

.table-wrap{

    overflow-x:auto;

}

table{

    width:100%;

    border-collapse:collapse;

    min-width:1150px;

}

th,
td{

    padding:11px;

    border-bottom:1px solid #eee;

    text-align:left;

    vertical-align:top;

}

th{

    background:#f1f7f5;

}

.money{

    font-weight:bold;

}

.status{

    font-weight:bold;

}

.referral-links{

    min-width:390px;

}

.link-section{

    margin-bottom:16px;

}

.link-section:last-child{

    margin-bottom:0;

}

.link-title{

    font-size:13px;

    font-weight:bold;

    margin-bottom:6px;

}

.success{

    background:#e8f5e9;

    color:#1b5e20;

    padding:12px;

    border-radius:8px;

    margin-bottom:15px;

}

.warning{

    background:#fff8e1;

    color:#795548;

    padding:12px;

    border-radius:8px;

    margin-bottom:15px;

}

.info{

    background:#e3f2fd;

    color:#0d47a1;

    padding:12px;

    border-radius:8px;

    margin-bottom:15px;

}

.form-grid{

    display:grid;

    grid-template-columns:1fr 1fr;

    gap:15px;

}

.form-group{

    min-width:0;

}

.form-full{

    grid-column:1 / -1;

}

.create-btn{

    margin-top:5px;

}

@media(max-width:700px){

    body{

        padding:10px;

    }

    .form-grid{

        grid-template-columns:1fr;

    }

    .form-full{

        grid-column:auto;

    }

    .link-box{

        flex-direction:column;

        align-items:stretch;

    }

    .link-box button{

        width:100%;

    }

    .logout button{

        width:100%;

    }

}

</style>

<script>

function copyLink(inputId, button) {

    const input =
        document.getElementById(inputId);

    if (!input) return;

    const text =
        input.value;

    if (
        navigator.clipboard &&
        window.isSecureContext
    ) {

        navigator.clipboard
            .writeText(text)
            .then(function(){

                showCopied(button);

            })
            .catch(function(){

                fallbackCopy(
                    input,
                    button
                );

            });

    } else {

        fallbackCopy(
            input,
            button
        );

    }

}


function showCopied(button) {

    const oldText =
        button.innerText;

    button.innerText =
        "✅ Copied!";

    setTimeout(function(){

        button.innerText =
            oldText;

    }, 1500);

}


function fallbackCopy(
    input,
    button
) {

    input.focus();

    input.select();

    input.setSelectionRange(
        0,
        99999
    );

    try {

        document.execCommand(
            "copy"
        );

        showCopied(button);

    } catch (e) {

        alert(
            "Please copy the link manually."
        );

    }

}

</script>

</head>

<body>

<div class="container">


<!-- ===================================================== -->
<!-- HEADER -->
<!-- ===================================================== -->

<div class="header">

<div>

<h1>
🎓 ALHIKAM Learning Center
</h1>

<div class="header-subtitle">
Admin Referral Dashboard
</div>

</div>

<form method="POST"
      class="logout"
      action="{{ url_for('admin_referral_logout') }}">

<input
    type="hidden"
    name="csrf_token"
    value="{{ csrf_token }}"
>

<button type="submit">
🚪 Logout
</button>

</form>

</div>


<!-- ===================================================== -->
<!-- MAIN PAYMENT LINK -->
<!-- ===================================================== -->

<div class="card link-card">

<h2>
💳 Main Payment Link
</h2>

<p class="small">
This is the general payment page for ALHIKAM Learning Center.
Use this when no promoter referral is required.
</p>

<div class="link-box">

<input
    id="main-payment-link"
    type="text"
    value="{{ payment_link }}"
    readonly
>

<button
    type="button"
    class="copy-btn"
    onclick="copyLink(
        'main-payment-link',
        this
    )"
>
📋 Copy Payment Link
</button>

</div>

</div>


<!-- ===================================================== -->
<!-- PROMOTER DASHBOARD LINK -->
<!-- ===================================================== -->

<div class="card link-card">

<h2>
📊 Promoter Dashboard
</h2>

<p class="small">
General promoter login/dashboard page.
A promoter can use their referral credentials to access their account.
</p>

<div class="link-box">

<input
    id="promoter-dashboard-link"
    type="text"
    value="{{ promoter_dashboard_link }}"
    readonly
>

<button
    type="button"
    class="copy-btn"
    onclick="copyLink(
        'promoter-dashboard-link',
        this
    )"
>
📋 Copy Dashboard Link
</button>

</div>

</div>


<!-- ===================================================== -->
<!-- CREATE PROMOTER -->
<!-- ===================================================== -->

<div class="card">

<h2>
👤 Create New Promoter
</h2>

<div class="info">
After creating a promoter, the system will generate a unique referral code for that promoter.
</div>

<form method="POST"
      action="{{ url_for('admin_create_promoter') }}">

<input
    type="hidden"
    name="csrf_token"
    value="{{ csrf_token }}"
>

<div class="form-grid">

<div class="form-group">

<label>
<strong>Full Name</strong>
</label>

<input
    type="text"
    name="full_name"
    placeholder="Promoter full name"
    required
>

</div>


<div class="form-group">

<label>
<strong>Phone</strong>
</label>

<input
    type="text"
    name="phone"
    placeholder="+234..."
    required
>

</div>


<div class="form-group">

<label>
<strong>Email</strong>
</label>

<input
    type="email"
    name="email"
    placeholder="Email address"
    required
>

</div>


<div class="form-group">

<label>
<strong>Commission Rate (%)</strong>
</label>

<input
    type="number"
    name="commission_rate"
    value="10"
    min="0"
    max="100"
    step="0.1"
    required
>

</div>


<div class="form-group form-full">

<label>
<strong>Promoter Password</strong>
</label>

<input
    type="password"
    name="password"
    placeholder="Set promoter dashboard password"
    minlength="6"
    required
>

</div>

</div>

<button
    type="submit"
    class="create-btn"
>
➕ Create Promoter
</button>

</form>

</div>


<!-- ===================================================== -->
<!-- PROMOTERS -->
<!-- ===================================================== -->

<div class="card">

<h2>
👥 Promoters
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

<th>Links</th>

</tr>

</thead>

<tbody>

{% for promoter in promoters %}

<tr>

<td>
{{ promoter["id"] }}
</td>

<td>
<strong>
{{ promoter["full_name"] }}
</strong>
</td>

<td>
{{ promoter["phone"] }}
</td>

<td>
{{ promoter["email"] }}
</td>

<td>

<div class="code">
{{ promoter["referral_code"] }}
</div>

</td>

<td>
{{ promoter["commission_rate"] }}%
</td>

<td class="money">
₦{{ "{:,.2f}".format(
    promoter["total_sales"] or 0
) }}
</td>

<td class="money">
₦{{ "{:,.2f}".format(
    promoter["available_balance"] or 0
) }}
</td>

<td class="money">
₦{{ "{:,.2f}".format(
    promoter["withdrawn"] or 0
) }}
</td>

<td class="referral-links">


<!-- ================================================= -->
<!-- PROMOTER REFERRAL LINK -->
<!-- ================================================= -->

{% set referral_link =
    base_url
    + "/referral/"
    + promoter["referral_code"]
%}

<div class="link-section">

<div class="link-title">
🔗 Promoter Referral Link
</div>

<div class="link-box">

<input
    id="referral-{{ promoter['id'] }}"
    type="text"
    value="{{ referral_link }}"
    readonly
>

<button
    type="button"
    class="copy-btn"
    onclick="copyLink(
        'referral-{{ promoter['id'] }}',
        this
    )"
>
📋 Copy
</button>

</div>

<p class="small">
Used for promoter login/referral access.
</p>

</div>


<!-- ================================================= -->
<!-- DIRECT REFERRAL PAYMENT LINK -->
<!-- ================================================= -->

{% set payment_referral_link =
    base_url
    + "/pay?ref="
    + promoter["referral_code"]
%}

<div class="link-section">

<div class="link-title">
💳 Direct Referral Payment Link
</div>

<div class="link-box">

<input
    id="payment-ref-{{ promoter['id'] }}"
    type="text"
    value="{{ payment_referral_link }}"
    readonly
>

<button
    type="button"
    class="copy-btn"
    onclick="copyLink(
        'payment-ref-{{ promoter['id'] }}',
        this
    )"
>
📋 Copy Payment Link
</button>

</div>

<p class="small">
Students can open this link directly to pay.
The promoter referral code is automatically included.
</p>

</div>


<!-- ================================================= -->
<!-- COPY REFERRAL CODE -->
<!-- ================================================= -->

<div class="link-section">

<div class="link-title">
🏷️ Referral Code
</div>

<div class="link-box">

<input
    id="code-{{ promoter['id'] }}"
    type="text"
    value="{{ promoter['referral_code'] }}"
    readonly
>

<button
    type="button"
    class="copy-btn"
    onclick="copyLink(
        'code-{{ promoter['id'] }}',
        this
    )"
>
📋 Copy Code
</button>

</div>

</div>


</td>

</tr>

{% else %}

<tr>

<td
    colspan="10"
    style="text-align:center;"
>

No promoters found.

</td>

</tr>

{% endfor %}

</tbody>

</table>

</div>

</div>


<!-- ===================================================== -->
<!-- WITHDRAWALS -->
<!-- ===================================================== -->

<div class="card">

<h2>
💰 Withdrawal Requests
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
{{ withdrawal["id"] }}
</td>

<td>
{{ withdrawal["promoter_name"] or withdrawal["promoter_id"] }}
</td>

<td class="money">
₦{{ "{:,.2f}".format(
    withdrawal["amount"] or 0
) }}
</td>

<td>
{{ withdrawal["bank_name"] or "" }}
</td>

<td>
{{ mask_account_number(
    withdrawal["account_number"]
) }}
</td>

<td class="status">
{{ withdrawal["status"] }}
</td>

<td>
{{ withdrawal["transfer_id"] or "" }}
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
    value="{{ withdrawal['id'] }}"
>

<button type="submit">
🔄 Refresh Status
</button>

</form>

</td>

</tr>

{% else %}

<tr>

<td
    colspan="8"
    style="text-align:center;"
>

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
# ADMIN DASHBOARD
# ============================================================

@admin_required
def admin_referral_page():

    promoters = get_all_promoters()

    withdrawals = get_all_withdrawals()

    base_url = request.url_root.rstrip("/")

    # General payment link
    payment_link = (
        f"{base_url}/pay"
    )

    # General promoter dashboard
    promoter_dashboard_link = (
        f"{base_url}/referral/dashboard"
    )

    return render_template_string(

        ADMIN_DASHBOARD_HTML,

        promoters=promoters,

        withdrawals=withdrawals,

        base_url=base_url,

        payment_link=payment_link,

        promoter_dashboard_link=
            promoter_dashboard_link,

        csrf_token=
            get_admin_csrf(),

        mask_account_number=
            mask_account_number,

    )


# ============================================================
# CREATE PROMOTER
# ============================================================

@admin_required
def create_promoter_page():

    if request.method != "POST":

        return redirect(
            url_for(
                "admin_referral"
            )
        )

    if not check_admin_csrf():

        return (
            "Invalid security token.",
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

    password = request.form.get(
        "password",
        ""
    )

    try:

        commission_rate = float(
            request.form.get(
                "commission_rate",
                "10"
            )
        )

    except Exception:

        commission_rate = 10.0

    if not full_name:

        return (
            "Full name is required.",
            400,
        )

    if not phone:

        return (
            "Phone number is required.",
            400,
        )

    if not email:

        return (
            "Email address is required.",
            400,
        )

    if len(password) < 6:

        return (
            "Promoter password must be at least 6 characters.",
            400,
        )

    if commission_rate < 0:

        return (
            "Commission rate cannot be negative.",
            400,
        )

    if commission_rate > 100:

        return (
            "Commission rate cannot exceed 100%.",
            400,
        )

    try:

        promoter = add_promoter(

            full_name=full_name,

            phone=phone,

            email=email,

            commission_rate=commission_rate,

        )

    except TypeError:

        try:

            promoter = add_promoter(

                full_name,

                phone,

                email,

                commission_rate,

            )

        except Exception as e:

            logger.exception(
                "Create promoter failed"
            )

            return (
                f"Unable to create promoter: {e}",
                500,
            )

    except Exception as e:

        logger.exception(
            "Create promoter failed"
        )

        return (
            f"Unable to create promoter: {e}",
            500,
        )

    if not promoter:

        return (
            "Promoter could not be created.",
            500,
        )

    try:

        if isinstance(
            promoter,
            dict
        ):

            promoter_id = promoter["id"]

        else:

            promoter_id = promoter

        set_promoter_password(

            promoter_id,

            password,

        )

    except Exception as e:

        logger.exception(
            "Setting promoter password failed"
        )

        return (
            "Promoter was created but password could not be saved.",
            500,
        )

    return redirect(
        url_for(
            "admin_referral"
        )
    )


# ============================================================
# REFRESH WITHDRAWAL STATUS
# ============================================================

@admin_required
def admin_withdrawal_status_page():

    if request.method != "POST":

        return redirect(
            url_for(
                "admin_referral"
            )
        )

    if not check_admin_csrf():

        return (
            "Invalid security token.",
            400,
        )

    withdrawal_id = (
        request.form.get(
            "withdrawal_id",
            ""
        )
        .strip()
    )

    if not withdrawal_id:

        return (
            "Withdrawal ID is required.",
            400,
        )

    try:

        withdrawal_id = int(
            withdrawal_id
        )

    except ValueError:

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

    transfer_id = str(
        withdrawal.get(
            "transfer_id"
        )
        or ""
    ).strip()

    if not transfer_id:

        return redirect(
            url_for(
                "admin_referral"
            )
        )

    try:

        result = (
            get_flutterwave_transfer_status(
                transfer_id
            )
        )

    except Exception:

        logger.exception(
            "Flutterwave transfer status check failed"
        )

        result = None

    if result:

        update_withdrawal_status(

            withdrawal_id=withdrawal_id,

            status=result.get(
                "status"
            ),

            message=result.get(
                "message"
            ),

        )

    return redirect(
        url_for(
            "admin_referral"
        )
    )