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
    "https://precious-trust-production-956b.up.railway.app"
).rstrip("/")


# ============================================================
# SESSION KEYS
# ============================================================

PROMOTER_SESSION_KEY = (
    "alhikam_promoter_id"
)

PROMOTER_CSRF_KEY = (
    "alhikam_promoter_csrf"
)


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
# PROMOTER CSRF
# ============================================================

def _csrf_token():

    token = session.get(
        PROMOTER_CSRF_KEY
    )

    if not token:

        token = secrets.token_urlsafe(32)

        session[
            PROMOTER_CSRF_KEY
        ] = token

    return token


def _check_csrf():

    submitted = request.form.get(
        "csrf_token",
        ""
    )

    expected = session.get(
        PROMOTER_CSRF_KEY,
        ""
    )

    if not submitted or not expected:
        return False

    return secrets.compare_digest(
        submitted,
        expected
    )


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

<html>

<head>

<meta name="viewport"
      content="width=device-width, initial-scale=1">

<title>
ALHIKAM Promoter Login
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

    max-width:430px;

    margin:70px auto;

    background:white;

    padding:28px;

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

label{

    display:block;

    margin-top:14px;

    font-weight:bold;

}

input{

    width:100%;

    padding:14px;

    margin-top:7px;

    border:1px solid #ddd;

    border-radius:8px;

    font-size:16px;

}

button{

    width:100%;

    padding:14px;

    margin-top:20px;

    border:none;

    border-radius:8px;

    background:#087f5b;

    color:white;

    font-size:16px;

    font-weight:bold;

    cursor:pointer;

}

.error{

    background:#ffebee;

    color:#b71c1c;

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

    font-size:13px;

    line-height:1.5;

}

</style>

</head>

<body>

<div class="container">

<h1>
🎓 ALHIKAM
</h1>

<div class="subtitle">
Promoter Dashboard Login
</div>

{% if error %}

<div class="error">
{{ error }}
</div>

{% endif %}

<div class="info">
Enter your referral code and promoter password.
</div>

<form method="POST"
      action="{{ url_for('promoter_login') }}">

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
            ""
        )
        or request.form.get(
            "referral_code",
            ""
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
        ""
    )

    if not referral_code:

        return render_template_string(

            PROMOTER_LOGIN_HTML,

            csrf_token=_csrf_token(),

            referral_code="",

            error="Referral code is required.",

        ), 400

    promoter = (
        get_promoter_by_referral_code(
            referral_code
        )
    )

    if not promoter:

        return render_template_string(

            PROMOTER_LOGIN_HTML,

            csrf_token=_csrf_token(),

            referral_code=referral_code,

            error="❌ Invalid referral code or password.",

        ), 401

    promoter_id = _row_get(
        promoter,
        "id"
    )

    try:

        valid_password = (
            verify_promoter_password(
                promoter_id,
                password
            )
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

            error="❌ Invalid referral code or password.",

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
        None
    )

    session.pop(
        PROMOTER_CSRF_KEY,
        None
    )

    return redirect(
        url_for(
            "promoter_login"
        )
    )


# ============================================================
# DASHBOARD HTML
# ============================================================

REFERRAL_DASHBOARD_HTML = """

<!DOCTYPE html>

<html>

<head>

<meta name="viewport"
      content="width=device-width, initial-scale=1">

<title>
ALHIKAM Promoter Dashboard
</title>

<style>

*{
    box-sizing:border-box;
}

body{

    font-family:Arial,sans-serif;

    background:#f4f7f6;

    margin:0;

    padding:15px;

}

.container{

    max-width:1000px;

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

    gap:10px;

    flex-wrap:wrap;

    box-shadow:0 3px 15px rgba(0,0,0,.08);

}

.header h1{

    margin:0;

    color:#087f5b;

}

.small{

    color:#666;

    font-size:13px;

    line-height:1.5;

}

.card{

    background:white;

    padding:20px;

    border-radius:14px;

    margin-bottom:20px;

    box-shadow:0 3px 15px rgba(0,0,0,.08);

}

.card h2{

    color:#087f5b;

    margin-top:0;

}

.stats{

    display:grid;

    grid-template-columns:
        repeat(4,1fr);

    gap:12px;

}

.stat{

    background:#f1f7f5;

    padding:16px;

    border-radius:10px;

}

.stat-title{

    font-size:13px;

    color:#666;

}

.stat-value{

    margin-top:7px;

    font-size:20px;

    font-weight:bold;

    color:#087f5b;

}

.link-box{

    display:flex;

    gap:8px;

}

.link-box input{

    flex:1;

}

input,
select{

    width:100%;

    padding:13px;

    border:1px solid #ddd;

    border-radius:8px;

    font-size:15px;

    margin-top:7px;

    margin-bottom:12px;

}

button{

    padding:12px 16px;

    border:none;

    border-radius:8px;

    background:#087f5b;

    color:white;

    font-weight:bold;

    cursor:pointer;

}

.logout{

    background:#c62828;

}

.copy{

    background:#1565c0;

}

.withdraw{

    background:#087f5b;

    width:100%;

    margin-top:8px;

}

.error{

    background:#ffebee;

    color:#b71c1c;

    padding:12px;

    border-radius:8px;

    margin-bottom:15px;

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

table{

    width:100%;

    border-collapse:collapse;

    min-width:800px;

}

th,
td{

    padding:11px;

    border-bottom:1px solid #eee;

    text-align:left;

}

th{

    background:#f1f7f5;

}

.table-wrap{

    overflow-x:auto;

}

.status{

    font-weight:bold;

}

@media(max-width:700px){

    .stats{

        grid-template-columns:1fr 1fr;

    }

    .link-box{

        flex-direction:column;

    }

}

</style>

<script>

function copyText(
    inputId,
    button
){

    const input =
        document.getElementById(inputId);

    if(!input) return;

    const text =
        input.value;

    if(
        navigator.clipboard &&
        window.isSecureContext
    ){

        navigator.clipboard
            .writeText(text)
            .then(function(){

                const old =
                    button.innerText;

                button.innerText =
                    "✅ Copied!";

                setTimeout(function(){

                    button.innerText =
                        old;

                },1500);

            });

    }else{

        input.focus();

        input.select();

        input.setSelectionRange(
            0,
            99999
        );

        document.execCommand(
            "copy"
        );

        const old =
            button.innerText;

        button.innerText =
            "✅ Copied!";

        setTimeout(function(){

            button.innerText =
                old;

        },1500);

    }

}

</script>

</head>

<body>

<div class="container">


<!-- HEADER -->

<div class="header">

<div>

<h1>
🎓 ALHIKAM Learning Center
</h1>

<div class="small">
Promoter Dashboard
</div>

</div>

<form method="POST"
      action="{{ url_for('promoter_logout') }}">

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


{% with messages =
    get_flashed_messages(
        with_categories=true
    )
%}

{% for category, message in messages %}

<div class="{{ category }}">
{{ message }}
</div>

{% endfor %}

{% endwith %}


<!-- STATS -->

<div class="card">

<h2>
📊 My Performance
</h2>

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
    promoter["withdrawn_amount"]
    or promoter["withdrawn"]
    or 0
) }}
</div>

</div>

</div>

</div>


<!-- REFERRAL INFORMATION -->

<div class="card">

<h2>
🔗 My Referral Link
</h2>

<p class="small">
Share this link with students. Payments made through your referral link will be connected to your referral account.
</p>

{% set referral_link =
    app_url
    + "/referral/"
    + promoter["referral_code"]
%}

<div class="link-box">

<input
    id="referral-link"
    type="text"
    value="{{ referral_link }}"
    readonly
>

<button
    type="button"
    class="copy"
    onclick="copyText(
        'referral-link',
        this
    )"
>
📋 Copy
</button>

</div>

<br>

<strong>
Referral Code:
</strong>

<span>
{{ promoter["referral_code"] }}
</span>

</div>


<!-- DIRECT PAYMENT LINK -->

<div class="card">

<h2>
💳 Direct Payment Link
</h2>

<p class="small">
Students can use this link directly to open the payment page. Your referral code is automatically attached.
</p>

{% set payment_link =
    app_url
    + "/pay?ref="
    + promoter["referral_code"]
%}

<div class="link-box">

<input
    id="payment-link"
    type="text"
    value="{{ payment_link }}"
    readonly
>

<button
    type="button"
    class="copy"
    onclick="copyText(
        'payment-link',
        this
    )"
>
📋 Copy
</button>

</div>

</div>


<!-- WITHDRAW -->

<div class="card">

<h2>
💰 Withdraw Commission
</h2>

<div class="warning">

<strong>
Withdrawal Security
</strong>

<br><br>

Your Withdrawal Code is required before any withdrawal can be processed.

<br>

Never share your Withdrawal Code with another person.

</div>

<p class="small">

Minimum withdrawal:
<strong>
₦{{ "{:,.2f}".format(minimum_withdrawal) }}
</strong>

</p>

<form method="POST"
      action="{{ url_for('promoter_withdrawal') }}">

<input
    type="hidden"
    name="csrf_token"
    value="{{ csrf_token }}"
>


<label>
<strong>
Withdrawal Amount
</strong>
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
<strong>
Bank
</strong>
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
<strong>
Account Number
</strong>
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
<strong>
Withdrawal Code
</strong>
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


<!-- WITHDRAWAL HISTORY -->

<div class="card">

<h2>
📜 Withdrawal History
</h2>

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

<td class="status">
{{ withdrawal["status"] or "" }}
</td>

<td class="status">
{{ withdrawal["transfer_status"] or "" }}
</td>

<td>
{{ withdrawal["created_at"] or "" }}
</td>

<td>

<a href="{{ url_for(
    'promoter_withdrawal_status',
    withdrawal_id=withdrawal['id']
) }}">
View
</a>

</td>

</tr>

{% else %}

<tr>

<td
    colspan="8"
    style="text-align:center;"
>

No withdrawal requests yet.

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
# DASHBOARD
# ============================================================

def referral_dashboard_by_code(
    referral_code=None
):

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

    withdrawals = (
        get_promoter_withdrawals(
            promoter["id"]
        )
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

        minimum_withdrawal=
            MINIMUM_WITHDRAWAL,

        app_url=APP_URL,

        csrf_token=
            _csrf_token(),

        mask_account=
            _mask_account,

    )


# ============================================================
# WITHDRAWAL HTML
# ============================================================

WITHDRAWAL_STATUS_HTML = """

<!DOCTYPE html>

<html>

<head>

<meta name="viewport"
      content="width=device-width, initial-scale=1">

<title>
ALHIKAM Withdrawal Status
</title>

<style>

body{

    font-family:Arial,sans-serif;

    background:#f4f7f6;

    padding:20px;

    margin:0;

}

.container{

    max-width:600px;

    margin:50px auto;

}

.card{

    background:white;

    padding:25px;

    border-radius:15px;

    box-shadow:0 4px 20px rgba(0,0,0,.10);

}

h1{

    color:#087f5b;

}

.item{

    padding:12px 0;

    border-bottom:1px solid #eee;

}

.status{

    font-size:20px;

    font-weight:bold;

    color:#087f5b;

}

button{

    width:100%;

    padding:13px;

    margin-top:15px;

    border:none;

    border-radius:8px;

    background:#087f5b;

    color:white;

    font-weight:bold;

}

a{

    display:block;

    margin-top:15px;

    text-align:center;

    color:#087f5b;

}

</style>

</head>

<body>

<div class="container">

<div class="card">

<h1>
💰 Withdrawal Status
</h1>

<div class="item">

<strong>
Withdrawal ID
</strong>

<br>

{{ withdrawal["id"] }}

</div>


<div class="item">

<strong>
Amount
</strong>

<br>

₦{{ "{:,.2f}".format(
    withdrawal["amount"] or 0
) }}

</div>


<div class="item">

<strong>
Bank
</strong>

<br>

{{ withdrawal["bank_name"] or "" }}

</div>


<div class="item">

<strong>
Account
</strong>

<br>

{{ mask_account(
    withdrawal["account_number"]
) }}

</div>


<div class="item">

<strong>
Status
</strong>

<br>

<div class="status">
{{ withdrawal["status"] or "" }}
</div>

</div>


<div class="item">

<strong>
Transfer Status
</strong>

<br>

{{ withdrawal["transfer_status"] or "" }}

</div>


<div class="item">

<strong>
Transfer Reference
</strong>

<br>

{{ withdrawal["transfer_reference"] or "" }}

</div>


{% if withdrawal["transfer_message"] %}

<div class="item">

<strong>
Message
</strong>

<br>

{{ withdrawal["transfer_message"] }}

</div>

{% endif %}


{% if can_refresh %}

<form method="POST"
      action="{{ url_for(
          'promoter_withdrawal_status',
          withdrawal_id=withdrawal['id']
      ) }}">

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


<a href="{{ url_for(
    'referral_dashboard'
) }}">
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

    # --------------------------------------------------------
    # CSRF
    # --------------------------------------------------------

    if not _check_csrf():

        flash(
            "Invalid security token. Please try again.",
            "error"
        )

        return redirect(
            url_for(
                "referral_dashboard"
            )
        )

    # --------------------------------------------------------
    # AMOUNT
    # --------------------------------------------------------

    amount_raw = (
        request.form.get(
            "amount",
            ""
        )
        .strip()
    )

    try:

        amount = float(
            amount_raw
        )

    except Exception:

        flash(
            "Invalid withdrawal amount.",
            "error"
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
            "error"
        )

        return redirect(
            url_for(
                "referral_dashboard"
            )
        )

    # --------------------------------------------------------
    # AVAILABLE BALANCE
    # --------------------------------------------------------

    available_balance = _safe_money(
        _row_get(
            promoter,
            "available_balance",
            0
        )
    )

    if amount > available_balance:

        flash(
            (
                "Insufficient available balance. "
                f"Your available balance is "
                f"₦{available_balance:,.2f}."
            ),
            "error"
        )

        return redirect(
            url_for(
                "referral_dashboard"
            )
        )

    # --------------------------------------------------------
    # WITHDRAWAL CODE
    # --------------------------------------------------------

    withdrawal_code = (
        request.form.get(
            "withdrawal_code",
            ""
        )
        .strip()
    )

    if not withdrawal_code:

        flash(
            "Withdrawal Code is required.",
            "error"
        )

        return redirect(
            url_for(
                "referral_dashboard"
            )
        )

    # --------------------------------------------------------
    # VERIFY WITHDRAWAL CODE
    #
    # IMPORTANT:
    # This happens BEFORE bank resolution and BEFORE money
    # is reserved.
    # --------------------------------------------------------

    try:

        code_valid = (
            verify_promoter_withdrawal_code(
                promoter["id"],
                withdrawal_code
            )
        )

    except Exception:

        logger.exception(
            "Withdrawal code verification failed"
        )

        code_valid = False

    if not code_valid:

        flash(
            "❌ Incorrect Withdrawal Code.",
            "error"
        )

        return redirect(
            url_for(
                "referral_dashboard"
            )
        )

    # --------------------------------------------------------
    # BANK CODE
    # --------------------------------------------------------

    bank_code = (
        request.form.get(
            "bank_code",
            ""
        )
        .strip()
    )

    if not bank_code:

        flash(
            "Please select your bank.",
            "error"
        )

        return redirect(
            url_for(
                "referral_dashboard"
            )
        )

    # --------------------------------------------------------
    # ACCOUNT NUMBER
    # --------------------------------------------------------

    account_number = (
        request.form.get(
            "account_number",
            ""
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
            "error"
        )

        return redirect(
            url_for(
                "referral_dashboard"
            )
        )

    # --------------------------------------------------------
    # GET BANK NAME
    # --------------------------------------------------------

    bank_name = bank_code

    try:

        banks = (
            get_flutterwave_banks()
            or []
        )

        for bank in banks:

            code = str(
                bank.get("code", "")
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

    # --------------------------------------------------------
    # RESOLVE BANK ACCOUNT
    # --------------------------------------------------------

    try:

        resolved = resolve_bank_account(

            account_number=
                account_number,

            bank_code=
                bank_code,

        )

    except TypeError:

        # Compatibility with possible positional version
        try:

            resolved = resolve_bank_account(
                bank_code,
                account_number
            )

        except Exception as e:

            logger.exception(
                "Bank account resolve failed"
            )

            flash(
                f"Unable to verify bank account: {e}",
                "error"
            )

            return redirect(
                url_for(
                    "referral_dashboard"
                )
            )

    except Exception as e:

        logger.exception(
            "Bank account resolve failed"
        )

        flash(
            "Unable to verify bank account. Please check your bank and account number.",
            "error"
        )

        return redirect(
            url_for(
                "referral_dashboard"
            )
        )

    if not resolved:

        flash(
            "Bank account could not be verified.",
            "error"
        )

        return redirect(
            url_for(
                "referral_dashboard"
            )
        )

    # --------------------------------------------------------
    # ACCOUNT NAME
    # --------------------------------------------------------

    if isinstance(
        resolved,
        dict
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
                dict
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
            "error"
        )

        return redirect(
            url_for(
                "referral_dashboard"
            )
        )

    # --------------------------------------------------------
    # CREATE WITHDRAWAL
    #
    # Database reserves the balance atomically.
    # --------------------------------------------------------

    try:

        withdrawal_id = create_withdrawal(

            promoter_id=
                promoter["id"],

            amount=
                amount,

            bank_name=
                bank_name,

            bank_code=
                bank_code,

            account_name=
                account_name,

            account_number=
                account_number,

        )

    except Exception as e:

        logger.exception(
            "Create withdrawal failed"
        )

        flash(
            f"Unable to create withdrawal: {e}",
            "error"
        )

        return redirect(
            url_for(
                "referral_dashboard"
            )
        )

    if not withdrawal_id:

        flash(
            "Withdrawal request could not be created.",
            "error"
        )

        return redirect(
            url_for(
                "referral_dashboard"
            )
        )

    # --------------------------------------------------------
    # STABLE TRANSFER REFERENCE
    # --------------------------------------------------------

    transfer_reference = (
        f"ALHIKAM-WD-{withdrawal_id}"
    )

    try:

        update_withdrawal_transfer(

            withdrawal_id=
                withdrawal_id,

            transfer_reference=
                transfer_reference,

        )

    except TypeError:

        # Compatibility with alternative function signature
        try:

            update_withdrawal_transfer(
                withdrawal_id,
                transfer_reference,
                None,
                "PENDING"
            )

        except Exception:

            logger.exception(
                "Unable to save transfer reference"
            )

    except Exception:

        logger.exception(
            "Unable to save transfer reference"
        )

    # --------------------------------------------------------
    # CREATE FLUTTERWAVE TRANSFER
    # --------------------------------------------------------

    try:

        transfer_result = (
            create_flutterwave_transfer(

                amount=amount,

                bank_code=bank_code,

                account_number=
                    account_number,

                account_name=
                    account_name,

                reference=
                    transfer_reference,

            )
        )

    except TypeError:

        # Compatibility fallback
        try:

            transfer_result = (
                create_flutterwave_transfer(

                    amount,

                    bank_code,

                    account_number,

                    account_name,

                    transfer_reference,

                )
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

    # --------------------------------------------------------
    # PROCESS TRANSFER RESULT
    # --------------------------------------------------------

    try:

        process_transfer_result(

            withdrawal_id=
                withdrawal_id,

            result=
                transfer_result,

        )

    except TypeError:

        # Compatibility with older signature
        try:

            process_transfer_result(
                withdrawal_id,
                transfer_result
            )

        except Exception:

            logger.exception(
                "Processing transfer result failed"
            )

    except Exception:

        logger.exception(
            "Processing transfer result failed"
        )

    # --------------------------------------------------------
    # REDIRECT TO STATUS
    # --------------------------------------------------------

    return redirect(
        url_for(
            "promoter_withdrawal_status",
            withdrawal_id=
                withdrawal_id,
        )
    )


# ============================================================
# WITHDRAWAL STATUS PAGE
# ============================================================

@promoter_required
def withdrawal_status_page(
    withdrawal_id
):

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

    withdrawal = (
        get_withdrawal_by_id(
            withdrawal_id
        )
    )

    if not withdrawal:

        return (
            "Withdrawal not found.",
            404,
        )

    # --------------------------------------------------------
    # OWNERSHIP CHECK
    # --------------------------------------------------------

    withdrawal_promoter_id = _row_get(
        withdrawal,
        "promoter_id"
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

    # --------------------------------------------------------
    # AUTO REFRESH PROCESSING TRANSFER
    # --------------------------------------------------------

    current_status = str(
        _row_get(
            withdrawal,
            "status",
            ""
        )
        or ""
    ).upper()

    transfer_status = str(
        _row_get(
            withdrawal,
            "transfer_status",
            ""
        )
        or ""
    ).upper()

    transfer_id = str(
        _row_get(
            withdrawal,
            "transfer_id",
            ""
        )
        or ""
    ).strip()

    transfer_reference = str(
        _row_get(
            withdrawal,
            "transfer_reference",
            ""
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

                    withdrawal_id=
                        withdrawal_id,

                    result=
                        result,

                )

            except TypeError:

                try:

                    process_transfer_result(
                        withdrawal_id,
                        result
                    )

                except Exception:

                    logger.exception(
                        "Unable to process refreshed transfer result"
                    )

            except Exception:

                logger.exception(
                    "Unable to process refreshed transfer result"
                )

            # Reload latest withdrawal
            withdrawal = (
                get_withdrawal_by_id(
                    withdrawal_id
                )
            )

    # --------------------------------------------------------
    # CAN REFRESH?
    # --------------------------------------------------------

    latest_status = str(
        _row_get(
            withdrawal,
            "status",
            ""
        )
        or ""
    ).upper()

    latest_transfer_status = str(
        _row_get(
            withdrawal,
            "transfer_status",
            ""
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

        csrf_token=
            _csrf_token(),

        can_refresh=
            can_refresh,

        mask_account=
            _mask_account,

    )