# ============================================================
#
# ALHIKAM LEARNING CENTER
# ADMIN REFERRAL DASHBOARD
#
# ============================================================
#
# FEATURES
#
# - Secure Admin Login
# - Admin Password Protection
# - CSRF Protection
# - Create Promoter
# - One-time display of promoter password
# - Automatic unique withdrawal code
# - One-time display of withdrawal code
# - Main Payment Link
# - Individual Referral Link
# - Individual Referral Payment Link
# - Promoter Dashboard Link
# - Copy Buttons
# - Withdrawal Status Refresh
#
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
    update_withdrawal_transfer,
    set_promoter_password,
)

from transfer import (
    get_flutterwave_transfer_status,
    get_flutterwave_transfer_status_by_reference,
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

# One-time promoter creation result
ADMIN_CREATED_PROMOTER_KEY = "alhikam_created_promoter"


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
# FORMAT WITHDRAWAL STATUS
# ============================================================

def format_withdrawal_status(status):

    if status is None:

        return "⚠️ Verification Required"

    # --------------------------------------------------------
    # If status is already a dictionary
    # --------------------------------------------------------

    if isinstance(status, dict):

        status = (
            status.get("status")
            or "unknown"
        )

    status = str(
        status
    ).strip()

    if not status:

        return "⚠️ Verification Required"

    normalized = status.lower()

    # --------------------------------------------------------
    # SUCCESS
    # --------------------------------------------------------

    if normalized in (
        "success",
        "successful",
        "completed",
        "complete",
    ):

        return "✅ Successful"

    # --------------------------------------------------------
    # FAILED
    # --------------------------------------------------------

    if normalized in (
        "failed",
        "failure",
        "rejected",
        "error",
    ):

        return "❌ Failed"

    # --------------------------------------------------------
    # CANCELLED
    # --------------------------------------------------------

    if normalized in (
        "cancelled",
        "canceled",
    ):

        return "🚫 Cancelled"

    # --------------------------------------------------------
    # PROCESSING
    # --------------------------------------------------------

    if normalized in (
        "processing",
        "pending",
        "new",
        "queued",
        "in_progress",
        "in-progress",
    ):

        return "⏳ Processing"

    # --------------------------------------------------------
    # OLD RAW DICTIONARY STRING
    # --------------------------------------------------------

    if (
        "'status': 'processing'" in normalized
        or '"status": "processing"' in normalized
        or "'status':'processing'" in normalized
        or '"status":"processing"' in normalized
    ):

        return "⏳ Processing"

    if (
        "'status': 'pending'" in normalized
        or '"status": "pending"' in normalized
        or "'status':'pending'" in normalized
        or '"status":"pending"' in normalized
    ):

        return "⏳ Processing"

    if (
        "'status': 'successful'" in normalized
        or '"status": "successful"' in normalized
        or "'status':'successful'" in normalized
        or '"status":"successful"' in normalized
    ):

        return "✅ Successful"

    if (
        "'status': 'failed'" in normalized
        or '"status": "failed"' in normalized
        or "'status':'failed'" in normalized
        or '"status":"failed"' in normalized
    ):

        return "❌ Failed"

    if (
        "'status': 'cancelled'" in normalized
        or '"status": "cancelled"' in normalized
        or "'status':'cancelled'" in normalized
        or '"status":"cancelled"' in normalized
    ):

        return "🚫 Cancelled"

    # --------------------------------------------------------
    # UNKNOWN
    # --------------------------------------------------------

    return "⚠️ Verification Required"


# ============================================================
# ADMIN LOGIN HTML
# ============================================================

ADMIN_LOGIN_HTML = """

<!DOCTYPE html>

<html>

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<title>ALHIKAM Admin Login</title>

<style>

body {
    margin: 0;
    padding: 20px;
    background: #f4f7fb;
    font-family: Arial, sans-serif;
}

.login-box {
    max-width: 420px;
    margin: 70px auto;
    background: white;
    padding: 30px;
    border-radius: 16px;
    box-shadow: 0 10px 35px rgba(0,0,0,0.10);
}

h1 {
    margin-top: 0;
}

.subtitle {
    color: #666;
    margin-bottom: 25px;
}

.error {
    background: #ffe7e7;
    color: #a00000;
    padding: 12px;
    border-radius: 8px;
    margin-bottom: 15px;
}

input {
    width: 100%;
    box-sizing: border-box;
    padding: 13px;
    margin: 8px 0 18px;
    border: 1px solid #ccc;
    border-radius: 8px;
}

button {
    width: 100%;
    padding: 13px;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    background: #111827;
    color: white;
    font-weight: bold;
}

.notice {
    margin-top: 20px;
    color: #666;
    font-size: 13px;
}

</style>

</head>

<body>

<div class="login-box">

<h1>🔐 ALHIKAM ADMIN</h1>

<div class="subtitle">
Secure Administrator Login
</div>

{% if error %}

<div class="error">
{{ error }}
</div>

{% endif %}

<form method="POST">

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

<div class="notice">
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

        return redirect(
            next_url
        )

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

    session.pop(
        ADMIN_CREATED_PROMOTER_KEY,
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

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<title>ALHIKAM Learning Center Admin</title>

<style>

body {
    margin: 0;
    padding: 20px;
    background: #f4f7fb;
    font-family: Arial, sans-serif;
    color: #172033;
}

.container {
    max-width: 1250px;
    margin: auto;
}

.header {
    background: #111827;
    color: white;
    padding: 22px;
    border-radius: 14px;
    margin-bottom: 20px;
}

.header h1 {
    margin: 0 0 6px;
}

.card {
    background: white;
    padding: 22px;
    margin-bottom: 20px;
    border-radius: 14px;
    box-shadow: 0 5px 20px rgba(0,0,0,0.06);
}

input,
select {
    width: 100%;
    box-sizing: border-box;
    padding: 11px;
    margin: 7px 0 14px;
    border: 1px solid #d1d5db;
    border-radius: 8px;
}

button {
    border: none;
    border-radius: 8px;
    padding: 10px 14px;
    cursor: pointer;
    font-weight: bold;
}

.copy-btn {
    background: #e5e7eb;
}

.create-btn {
    background: #111827;
    color: white;
}

.logout-btn {
    background: #dc2626;
    color: white;
}

.refresh-btn {
    background: #2563eb;
    color: white;
}

.table-wrap {
    overflow-x: auto;
}

table {
    width: 100%;
    border-collapse: collapse;
    min-width: 950px;
}

th,
td {
    padding: 12px;
    border-bottom: 1px solid #e5e7eb;
    text-align: left;
    vertical-align: top;
}

th {
    background: #f8fafc;
}

.success-box {
    background: #ecfdf5;
    border: 1px solid #86efac;
    padding: 18px;
    border-radius: 10px;
}

.warning-box {
    background: #fff7ed;
    border: 1px solid #fdba74;
    padding: 14px;
    border-radius: 10px;
}

.link-box {
    margin: 15px 0;
}

.small {
    font-size: 13px;
    color: #6b7280;
}

.code-value {
    font-weight: bold;
    word-break: break-all;
}

</style>

<script>

function copyLink(id, button) {

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

</head>

<body>

<div class="container">

<div class="header">

<h1>
🎓 ALHIKAM Learning Center
</h1>

<div>
Admin Referral Dashboard
</div>

<br>

<form
    method="POST"
    action="{{ url_for('admin_logout') }}"
>

<input
    type="hidden"
    name="csrf_token"
    value="{{ csrf_token }}"
>

<button
    type="submit"
    class="logout-btn"
>
🚪 Logout
</button>

</form>

</div>


{% if created_promoter %}

<div class="card">

<div class="success-box">

<h2>
✅ Promoter Created Successfully
</h2>

<p>
<strong>Important:</strong>
These credentials are shown for this creation only.
The database stores the password and withdrawal code
securely as hashes.
</p>

<hr>

<p>
👤 <strong>PROMOTER</strong><br>
<span class="code-value">
{{ created_promoter["full_name"] }}
</span>
</p>

<p>
🏷️ <strong>REFERRAL CODE</strong><br>
<span class="code-value">
{{ created_promoter["referral_code"] }}
</span>
</p>

<p>
🔑 <strong>PROMOTER PASSWORD</strong><br>
<span class="code-value">
{{ created_promoter["password"] }}
</span>
</p>

<p>
💰 <strong>WITHDRAWAL CODE</strong><br>
<span class="code-value">
{{ created_promoter["withdrawal_code"] }}
</span>
</p>

<p>
⚠️ Save these credentials securely.
The password and withdrawal code will not be stored
in plaintext.
</p>

</div>

</div>

{% endif %}


<div class="card">

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


<div class="card">

<h2>
📊 Promoter Dashboard
</h2>

<p class="small">
General promoter login/dashboard page.
Promoters can use their referral code and password
to access their account.
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


<div class="card">

<h2>
👤 Create New Promoter
</h2>

<p class="small">
After creating a promoter, the system automatically
generates a unique referral code and withdrawal code.
The password and withdrawal code are shown once.
</p>

<form
    method="POST"
    action="{{ url_for('create_promoter') }}"
>

<input
    type="hidden"
    name="csrf_token"
    value="{{ csrf_token }}"
>

<label>
<strong>Full Name</strong>
</label>

<input
    type="text"
    name="full_name"
    placeholder="Promoter full name"
    required
>

<label>
<strong>Phone</strong>
</label>

<input
    type="text"
    name="phone"
    placeholder="+234..."
    required
>

<label>
<strong>Email</strong>
</label>

<input
    type="email"
    name="email"
    placeholder="Email address"
    required
>

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

<button
    type="submit"
    class="create-btn"
>
➕ Create Promoter
</button>

</form>

</div>


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
{{ promoter["referral_code"] }}
</td>

<td>
{{ promoter["commission_rate"] }}%
</td>

<td>
₦{{ "{:,.2f}".format(
    promoter["total_sales"] or 0
) }}
</td>

<td>
₦{{ "{:,.2f}".format(
    promoter["available_balance"] or 0
) }}
</td>

<td>
₦{{ "{:,.2f}".format(
    promoter["withdrawn"] or 0
) }}
</td>

<td>

{% set referral_link =
    base_url
    + "/referral/"
    + promoter["referral_code"]
%}

<div class="link-box">

<strong>
🔗 Promoter Referral Link
</strong>

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

<p class="small">
Used for promoter login/referral access.
</p>

</div>


{% set payment_referral_link =
    base_url
    + "/pay?ref="
    + promoter["referral_code"]
%}

<div class="link-box">

<strong>
💳 Direct Referral Payment Link
</strong>

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

<p class="small">
Students can open this link directly to pay.
The promoter referral code is automatically included.
</p>

</div>


<div class="link-box">

<strong>
🏷️ Referral Code
</strong>

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

</td>

</tr>

{% else %}

<tr>

<td colspan="10">

No promoters found.

</td>

</tr>

{% endfor %}

</tbody>

</table>

</div>

</div>


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

<td>
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

<td>

{{ format_withdrawal_status(
    withdrawal["status"]
) }}

</td>

<td>

{{ withdrawal["transfer_id"] or "" }}

</td>

<td>

<form
    method="POST"
    action="{{ url_for(
        'admin_withdrawal_status'
    ) }}"
>

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

<button
    type="submit"
    class="refresh-btn"
>
🔄 Refresh Status
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

    # Get one-time creation result

    created_promoter = session.pop(
        ADMIN_CREATED_PROMOTER_KEY,
        None
    )

    return render_template_string(

        ADMIN_DASHBOARD_HTML,

        promoters=promoters,

        withdrawals=withdrawals,

        base_url=base_url,

        payment_link=payment_link,

        promoter_dashboard_link=
            promoter_dashboard_link,

        created_promoter=
            created_promoter,

        csrf_token=
            get_admin_csrf(),

        mask_account_number=
            mask_account_number,

        format_withdrawal_status=
            format_withdrawal_status,
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
        ).strip()
    )

    phone = (
        request.form.get(
            "phone",
            ""
        ).strip()
    )

    email = (
        request.form.get(
            "email",
            ""
        )
        .strip()
        .lower()
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

    # ========================================================
    # VALIDATION
    # ========================================================

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

    # ========================================================
    # CREATE PROMOTER
    # ========================================================

    try:

        promoter = add_promoter(
            full_name=full_name,
            phone=phone,
            email=email,
            commission_rate=commission_rate,
        )

    except TypeError:

        # Compatibility with older positional version

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

    # ========================================================
    # DATABASE RETURN COMPATIBILITY
    # ========================================================

    try:

        if isinstance(
            promoter,
            dict
        ):

            promoter_id = promoter["id"]

            referral_code = (
                promoter.get(
                    "referral_code"
                )
                or ""
            )

            withdrawal_code = (
                promoter.get(
                    "withdrawal_code"
                )
                or ""
            )

        else:

            # Older database compatibility

            promoter_id = promoter

            referral_code = ""

            withdrawal_code = ""

        # ====================================================
        # SET PROMOTER PASSWORD
        # ====================================================

        set_promoter_password(
            promoter_id,
            password,
        )

    except Exception as e:

        logger.exception(
            "Setting promoter password failed"
        )

        return (
            "Promoter was created but password "
            "could not be saved.",
            500,
        )

    # ========================================================
    # ONE-TIME PROMOTER CREATION RESULT
    # ========================================================

    session[
        ADMIN_CREATED_PROMOTER_KEY
    ] = {

        "id":
            promoter_id,

        "full_name":
            full_name,

        "referral_code":
            referral_code,

        "password":
            password,

        "withdrawal_code":
            withdrawal_code,
    }

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

    # ========================================================
    # POST ONLY
    # ========================================================

    if request.method != "POST":

        return redirect(
            url_for(
                "admin_referral"
            )
        )

    # ========================================================
    # CSRF
    # ========================================================

    if not check_admin_csrf():

        return (
            "Invalid security token.",
            400,
        )

    # ========================================================
    # GET WITHDRAWAL ID
    # ========================================================

    withdrawal_id = (
        request.form.get(
            "withdrawal_id",
            ""
        ).strip()
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

    # ========================================================
    # GET WITHDRAWAL
    # ========================================================

    withdrawal = get_withdrawal_by_id(
        withdrawal_id
    )

    if not withdrawal:

        return (
            "Withdrawal not found.",
            404,
        )

    # ========================================================
    # GET TRANSFER ID
    #
    # sqlite3.Row MUST be accessed using ["column"]
    # ========================================================

    try:

        transfer_id = (
            withdrawal["transfer_id"]
            or ""
        )

    except Exception:

        transfer_id = ""

    transfer_id = str(
        transfer_id
    ).strip()

    # ========================================================
    # GET TRANSFER REFERENCE
    #
    # IMPORTANT:
    #
    # Database column is:
    #
    # transfer_reference
    #
    # NOT:
    #
    # reference
    # ========================================================

    try:

        transfer_reference = (
            withdrawal["transfer_reference"]
            or ""
        )

    except Exception:

        transfer_reference = ""

    transfer_reference = str(
        transfer_reference
    ).strip()

    result = None

    # ========================================================
    # OPTION 1:
    # CHECK BY TRANSFER ID
    # ========================================================

    if transfer_id:

        try:

            result = (
                get_flutterwave_transfer_status(
                    transfer_id
                )
            )

        except Exception:

            logger.exception(
                "Flutterwave transfer status "
                "check by transfer ID failed."
            )

            result = None

    # ========================================================
    # OPTION 2:
    # CHECK BY TRANSFER REFERENCE
    # ========================================================

    elif transfer_reference:

        try:

            result = (
                get_flutterwave_transfer_status_by_reference(
                    transfer_reference
                )
            )

        except Exception:

            logger.exception(
                "Flutterwave transfer status "
                "check by reference failed."
            )

            result = None

    # ========================================================
    # NOTHING TO CHECK
    # ========================================================

    else:

        logger.warning(
            "Withdrawal %s has no transfer ID "
            "and no transfer reference.",
            withdrawal_id,
        )

        return redirect(
            url_for(
                "admin_referral"
            )
        )

    # ========================================================
    # NO FLUTTERWAVE RESULT
    # ========================================================

    if not result:

        logger.warning(
            "No Flutterwave status result "
            "for withdrawal %s.",
            withdrawal_id,
        )

        return redirect(
            url_for(
                "admin_referral"
            )
        )

    # ========================================================
    # NORMALIZE FLUTTERWAVE RESULT
    # ========================================================

    if isinstance(
        result,
        dict
    ):

        raw_status = (
            result.get(
                "status"
            )
            or "processing"
        )

        status = str(
            raw_status
        ).strip().lower()

        message = str(
            result.get(
                "message"
            )
            or ""
        ).strip()

        new_transfer_id = str(
            result.get(
                "transfer_id"
            )
            or ""
        ).strip()

        new_reference = str(
            result.get(
                "reference"
            )
            or transfer_reference
            or ""
        ).strip()

    else:

        status = "processing"

        message = (
            "Transfer status could not "
            "be confirmed."
        )

        new_transfer_id = ""

        new_reference = (
            transfer_reference
        )

    # ========================================================
    # NORMALIZE STATUS
    # ========================================================

    if status in (
        "success",
        "successful",
        "completed",
        "complete",
    ):

        final_status = "successful"

    elif status in (
        "failed",
        "failure",
        "rejected",
        "error",
    ):

        final_status = "failed"

    elif status in (
        "cancelled",
        "canceled",
    ):

        final_status = "cancelled"

    elif status in (
        "pending",
        "processing",
        "new",
        "queued",
        "in_progress",
        "in-progress",
    ):

        final_status = "processing"

    else:

        # Unknown status must NOT be treated as failed.

        final_status = "processing"

        if not message:

            message = (
                "Transfer status is still "
                "being verified."
            )

    # ========================================================
    # SAVE TRANSFER ID / REFERENCE
    # ========================================================

    try:

        update_withdrawal_transfer(
            withdrawal_id=withdrawal_id,

            transfer_id=(
                new_transfer_id
                if new_transfer_id
                else None
            ),

            transfer_reference=(
                new_reference
                if new_reference
                else None
            ),

            status=final_status,

            message=(
                message
                if message
                else None
            ),
        )

    except TypeError:

        # Compatibility with older positional version

        try:

            update_withdrawal_transfer(
                withdrawal_id,
                (
                    new_transfer_id
                    if new_transfer_id
                    else None
                ),
                (
                    new_reference
                    if new_reference
                    else None
                ),
                final_status,
                (
                    message
                    if message
                    else None
                ),
            )

        except Exception:

            logger.exception(
                "Could not update withdrawal "
                "transfer information."
            )

    except Exception:

        logger.exception(
            "Could not update withdrawal "
            "transfer information."
        )

    # ========================================================
    # PROCESS FINAL STATUS
    #
    # PROCESSING:
    #   Do NOT change promoter balance.
    #
    # SUCCESSFUL:
    #   update_withdrawal_status() increments withdrawn.
    #
    # FAILED/CANCELLED:
    #   update_withdrawal_status() restores
    #   promoter available balance.
    #
    # The database function also checks the previous
    # status, so refreshing the same successful/failed
    # withdrawal again will not double-process it.
    # ========================================================

    if final_status in (
        "successful",
        "failed",
        "cancelled",
    ):

        try:

            update_withdrawal_status(
                withdrawal_id=withdrawal_id,

                status=final_status,

                message=(
                    message
                    if message
                    else None
                ),
            )

        except TypeError:

            try:

                update_withdrawal_status(
                    withdrawal_id,
                    final_status,
                    (
                        message
                        if message
                        else None
                    ),
                )

            except Exception:

                logger.exception(
                    "Could not update final "
                    "withdrawal status."
                )

        except Exception:

            logger.exception(
                "Could not update final "
                "withdrawal status."
            )

    # ========================================================
    # LOG RESULT
    # ========================================================

    logger.info(
        "Withdrawal status refreshed: "
        "withdrawal=%s status=%s "
        "transfer_id=%s reference=%s",
        withdrawal_id,

        final_status,

        (
            new_transfer_id
            or transfer_id
            or "none"
        ),

        (
            new_reference
            or transfer_reference
            or "none"
        ),
    )

    # ========================================================
    # RETURN DASHBOARD
    # ========================================================

    return redirect(
        url_for(
            "admin_referral"
        )
    )