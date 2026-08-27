# ==========================================================
# ALHIKAM LEARNING CENTER V2
# admin_referral.py
#
# ADMIN LOGIN
# ADMIN PROMOTER CREATION
# ADMIN PROMOTER LIST
# ADMIN WITHDRAWAL MANAGEMENT
# ==========================================================

import secrets
import string

from flask import (
    request,
    render_template_string,
    session,
    redirect,
)

from database import (
    get_connection,
    add_promoter,
    get_promoter_by_referral_code,
    update_withdrawal_status,
)

from config import APP_URL


# ==========================================================
# ADMIN SESSION
# ==========================================================

ADMIN_SESSION_KEY = "alhikam_admin_logged_in"


# ==========================================================
# GENERATE UNIQUE REFERRAL CODE
# ==========================================================

def generate_referral_code():

    characters = (
        string.ascii_uppercase
        + string.digits
    )

    while True:

        random_part = "".join(
            secrets.choice(characters)
            for _ in range(6)
        )

        referral_code = (
            f"ALHIKAM-{random_part}"
        )

        existing = get_promoter_by_referral_code(
            referral_code
        )

        if not existing:
            return referral_code


# ==========================================================
# ADMIN LOGIN HTML
# ==========================================================

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
    background:#f5f7f9;
    padding:20px;
    margin:0;
}

.container{
    max-width:450px;
    margin:60px auto;
}

.card{
    background:white;
    padding:25px;
    border-radius:15px;
    box-shadow:0 3px 12px rgba(0,0,0,.08);
}

h2{
    color:#087f5b;
    margin-top:0;
}

input{
    width:100%;
    padding:14px;
    box-sizing:border-box;
    border:1px solid #ccc;
    border-radius:8px;
    font-size:16px;
    margin-top:10px;
}

button{
    width:100%;
    padding:15px;
    margin-top:18px;
    background:#087f5b;
    color:white;
    border:none;
    border-radius:10px;
    font-size:17px;
    font-weight:bold;
}

.error{
    background:#ffe8e8;
    color:#a00000;
    padding:12px;
    border-radius:8px;
    margin-bottom:15px;
}

</style>

</head>

<body>

<div class="container">

<div class="card">

<h2>
🔐 ALHIKAM Admin
</h2>

<p>
Enter admin password to continue.
</p>

{% if error %}

<div class="error">
{{ error }}
</div>

{% endif %}

<form method="POST">

<input
type="password"
name="password"
placeholder="Admin Password"
required
>

<button type="submit">
🔓 LOGIN
</button>

</form>

</div>

</div>

</body>

</html>

"""


# ==========================================================
# ADMIN PANEL HTML
# ==========================================================

ADMIN_PANEL_HTML = """

<!DOCTYPE html>

<html>

<head>

<meta name="viewport"
content="width=device-width, initial-scale=1">

<title>ALHIKAM Admin Referral</title>

<style>

*{
    box-sizing:border-box;
}

body{
    font-family:Arial,sans-serif;
    background:#f5f7f9;
    padding:15px;
    margin:0;
}

.container{
    max-width:1000px;
    margin:auto;
}

.header{
    background:#087f5b;
    color:white;
    padding:22px;
    border-radius:15px;
    margin-bottom:15px;
}

.header h2{
    margin:0 0 8px 0;
}

.card{
    background:white;
    padding:20px;
    border-radius:15px;
    margin-bottom:15px;
    box-shadow:0 3px 10px rgba(0,0,0,.07);
}

input{
    width:100%;
    padding:13px;
    border:1px solid #ccc;
    border-radius:8px;
    font-size:16px;
}

label{
    display:block;
    font-weight:bold;
    margin-top:12px;
    margin-bottom:6px;
}

button{
    padding:12px 16px;
    background:#087f5b;
    color:white;
    border:none;
    border-radius:8px;
    font-weight:bold;
    cursor:pointer;
}

.logout{
    display:inline-block;
    background:#dc2626;
    color:white;
    text-decoration:none;
    padding:10px 15px;
    border-radius:8px;
    margin-top:10px;
}

.success{
    background:#e8f7ef;
    color:#075c43;
    padding:15px;
    border-radius:10px;
    margin-bottom:15px;
    word-break:break-word;
}

.error{
    background:#ffe8e8;
    color:#a00000;
    padding:15px;
    border-radius:10px;
    margin-bottom:15px;
}

.code{
    background:#eef8f4;
    padding:12px;
    border-radius:8px;
    word-break:break-all;
    font-weight:bold;
}

.link{
    background:#f4f4f4;
    padding:12px;
    border-radius:8px;
    word-break:break-all;
    font-size:13px;
    margin-top:5px;
}

.table-wrap{
    overflow-x:auto;
}

table{
    width:100%;
    border-collapse:collapse;
    min-width:750px;
}

th,
td{
    padding:11px;
    border-bottom:1px solid #eee;
    text-align:left;
    vertical-align:top;
}

th{
    background:#f7f7f7;
}

.status{
    font-weight:bold;
}

.pending{
    color:#d97706;
}

.processing{
    color:#2563eb;
}

.successful{
    color:#087f5b;
}

.failed,
.cancelled{
    color:#dc2626;
}

.small{
    color:#666;
    font-size:13px;
    line-height:1.5;
}

.stat-grid{
    display:grid;
    grid-template-columns:repeat(4, 1fr);
    gap:12px;
}

.stat{
    background:#f8faf9;
    padding:15px;
    border-radius:10px;
}

.stat-number{
    font-size:22px;
    font-weight:bold;
}

.withdraw-form{
    display:inline-block;
}

.withdraw-form select{
    padding:8px;
    border:1px solid #ccc;
    border-radius:7px;
}

.withdraw-form button{
    padding:8px 10px;
}

.create-button{
    margin-top:15px;
}

@media(max-width:700px){

    .stat-grid{
        grid-template-columns:1fr 1fr;
    }

}

</style>

</head>

<body>

<div class="container">


<!-- =====================================================
     HEADER
====================================================== -->

<div class="header">

<h2>
🎯 ALHIKAM Referral Admin
</h2>

<div>
Promoter & Withdrawal Management
</div>

<a
class="logout"
href="/admin/referral/logout"
>
🚪 Logout
</a>

</div>


<!-- =====================================================
     MESSAGES
====================================================== -->

{% if error %}

<div class="error">
{{ error }}
</div>

{% endif %}


{% if success %}

<div class="success">
{{ success }}
</div>

{% endif %}


<!-- =====================================================
     CREATE PROMOTER
====================================================== -->

<div class="card">

<h3>
➕ Create New Promoter
</h3>

<form method="POST"
action="/admin/referral/create-promoter">

<label>
Full Name
</label>

<input
type="text"
name="full_name"
placeholder="Promoter full name"
required
>

<label>
Phone Number
</label>

<input
type="text"
name="phone"
placeholder="08012345678"
>

<label>
Email
</label>

<input
type="email"
name="email"
placeholder="example@gmail.com"
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
required
>

<button
class="create-button"
type="submit"
>
➕ CREATE PROMOTER
</button>

</form>

</div>


<!-- =====================================================
     SUMMARY
====================================================== -->

<div class="card">

<h3>
📊 Summary
</h3>

<div class="stat-grid">

<div class="stat">

<div class="small">
Promoters
</div>

<div class="stat-number">
{{ promoters|length }}
</div>

</div>


<div class="stat">

<div class="small">
Withdrawal Requests
</div>

<div class="stat-number">
{{ withdrawals|length }}
</div>

</div>


<div class="stat">

<div class="small">
Pending Withdrawals
</div>

<div class="stat-number">
{{ pending_count }}
</div>

</div>


<div class="stat">

<div class="small">
Pending Amount
</div>

<div class="stat-number">
₦{{ pending_amount }}
</div>

</div>

</div>

</div>


<!-- =====================================================
     PROMOTERS
====================================================== -->

<div class="card">

<h3>
👥 Promoters
</h3>

{% if promoters %}

<div class="table-wrap">

<table>

<thead>

<tr>

<th>ID</th>
<th>Name</th>
<th>Referral Code</th>
<th>Sales</th>
<th>Earned</th>
<th>Balance</th>
<th>Withdrawn</th>
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

<b>
{{ promoter["full_name"] }}
</b>

<br>

<span class="small">
{{ promoter["phone"] or "" }}
</span>

</td>

<td>

<div class="code">
{{ promoter["referral_code"] }}
</div>

<br>

<a
href="/referral/dashboard?ref={{ promoter['referral_code'] }}"
target="_blank"
>
Open Dashboard
</a>

<br><br>

<a
href="/payment?ref={{ promoter['referral_code'] }}"
target="_blank"
>
Open Payment Link
</a>

</td>

<td>
{{ promoter["total_sales"] or 0 }}
</td>

<td>
₦{{ "{:,.0f}".format(promoter["total_earned"] or 0) }}
</td>

<td>
₦{{ "{:,.0f}".format(promoter["available_balance"] or 0) }}
</td>

<td>
₦{{ "{:,.0f}".format(promoter["withdrawn_amount"] or 0) }}
</td>

<td>
{{ promoter["status"]|capitalize }}
</td>

</tr>

{% endfor %}

</tbody>

</table>

</div>

{% else %}

<p class="small">
No promoters yet.
</p>

{% endif %}

</div>


<!-- =====================================================
     WITHDRAWALS
====================================================== -->

<div class="card">

<h3>
💸 Withdrawal Requests
</h3>

{% if withdrawals %}

<div class="table-wrap">

<table>

<thead>

<tr>

<th>ID</th>
<th>Promoter</th>
<th>Amount</th>
<th>Bank Details</th>
<th>Status</th>
<th>Action</th>
<th>Date</th>

</tr>

</thead>

<tbody>

{% for withdrawal in withdrawals %}

<tr>

<td>
#{{ withdrawal["id"] }}
</td>

<td>

<b>
{{ withdrawal["promoter_name"] }}
</b>

<br>

<span class="small">
{{ withdrawal["referral_code"] }}
</span>

</td>

<td>

<b>
₦{{ "{:,.0f}".format(withdrawal["amount"] or 0) }}
</b>

</td>

<td>

{{ withdrawal["bank_name"] }}

<br>

{{ withdrawal["account_name"] }}

<br>

<b>
{{ withdrawal["account_number"] }}
</b>

</td>

<td>

<span class="status {{ withdrawal['status']|lower }}">

{{ withdrawal["status"]|capitalize }}

</span>

</td>

<td>

{% if withdrawal["status"] not in
["successful", "failed", "cancelled"] %}

<form
class="withdraw-form"
method="POST"
action="/admin/referral/withdrawal-status"
>

<input
type="hidden"
name="withdrawal_id"
value="{{ withdrawal['id'] }}"
>

<select name="status">

<option value="processing">
Processing
</option>

<option value="successful">
Successful
</option>

<option value="failed">
Failed
</option>

<option value="cancelled">
Cancelled
</option>

</select>

<button type="submit">
UPDATE
</button>

</form>

{% else %}

<span class="small">
Final
</span>

{% endif %}

</td>

<td>
{{ withdrawal["created_at"] }}
</td>

</tr>

{% endfor %}

</tbody>

</table>

</div>

{% else %}

<p class="small">
No withdrawal request yet.
</p>

{% endif %}

</div>


</div>

</body>

</html>

"""


# ==========================================================
# ADMIN LOGIN CHECK
# ==========================================================

def admin_logged_in():

    return bool(
        session.get(
            ADMIN_SESSION_KEY,
            False
        )
    )


# ==========================================================
# LOGIN PAGE
# ==========================================================

def admin_login_page(error=""):

    return render_template_string(
        ADMIN_LOGIN_HTML,
        error=error
    )


# ==========================================================
# LOGIN
# ==========================================================

def admin_login(password, correct_password):

    if not password:
        return False

    if not correct_password:
        return False

    if password != correct_password:
        return False

    session[
        ADMIN_SESSION_KEY
    ] = True

    return True


# ==========================================================
# LOGOUT
# ==========================================================

def admin_logout():

    session.pop(
        ADMIN_SESSION_KEY,
        None
    )

    return redirect(
        "/admin/referral"
    )


# ==========================================================
# GET ALL PROMOTERS
# ==========================================================

def get_all_promoters():

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute("""
        SELECT *
        FROM promoters
        ORDER BY id DESC
        """)

        return cursor.fetchall()

    finally:

        conn.close()


# ==========================================================
# GET ALL WITHDRAWALS
# ==========================================================

def get_all_withdrawals():

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute("""
        SELECT

            withdrawals.*,

            promoters.full_name
                AS promoter_name,

            promoters.referral_code
                AS referral_code

        FROM withdrawals

        INNER JOIN promoters
            ON promoters.id =
               withdrawals.promoter_id

        ORDER BY withdrawals.id DESC
        """)

        return cursor.fetchall()

    finally:

        conn.close()


# ==========================================================
# CALCULATE WITHDRAWAL SUMMARY
# ==========================================================

def calculate_withdrawal_summary(withdrawals):

    pending_count = 0
    pending_amount = 0.0

    for withdrawal in withdrawals:

        status = str(
            withdrawal["status"] or ""
        ).lower().strip()

        if status in {
            "pending",
            "processing"
        }:

            pending_count += 1

            try:

                pending_amount += float(
                    withdrawal["amount"] or 0
                )

            except Exception:

                pass

    return (
        pending_count,
        pending_amount
    )


# ==========================================================
# ADMIN PANEL
# ==========================================================

def admin_referral_page(
    error="",
    success=""
):

    if not admin_logged_in():

        return admin_login_page()


    try:

        promoters = get_all_promoters()

    except Exception as e:

        print(
            "ADMIN PROMOTER LIST ERROR:",
            repr(e)
        )

        promoters = []

        if not error:

            error = (
                "Unable to load promoters."
            )


    try:

        withdrawals = get_all_withdrawals()

    except Exception as e:

        print(
            "ADMIN WITHDRAWAL LIST ERROR:",
            repr(e)
        )

        withdrawals = []

        if not error:

            error = (
                "Unable to load withdrawals."
            )


    (
        pending_count,
        pending_amount
    ) = calculate_withdrawal_summary(
        withdrawals
    )


    return render_template_string(

        ADMIN_PANEL_HTML,

        promoters=promoters,

        withdrawals=withdrawals,

        pending_count=pending_count,

        pending_amount=(
            f"{pending_amount:,.0f}"
        ),

        error=error,

        success=success

    )


# ==========================================================
# CREATE PROMOTER
# ==========================================================

def create_promoter_admin():

    if not admin_logged_in():

        return redirect(
            "/admin/referral"
        )


    full_name = (
        request.form.get(
            "full_name",
            ""
        )
        or ""
    ).strip()


    phone = (
        request.form.get(
            "phone",
            ""
        )
        or ""
    ).strip()


    email = (
        request.form.get(
            "email",
            ""
        )
        or ""
    ).strip()


    commission_rate_raw = (
        request.form.get(
            "commission_rate",
            "20"
        )
        or "20"
    ).strip()


    # ======================================================
    # VALIDATE NAME
    # ======================================================

    if not full_name:

        return admin_referral_page(
            error="Full name is required."
        )


    # ======================================================
    # VALIDATE COMMISSION
    # ======================================================

    try:

        commission_rate = float(
            commission_rate_raw
        )

    except Exception:

        return admin_referral_page(
            error=(
                "Invalid commission rate."
            )
        )


    if (
        commission_rate < 0
        or commission_rate > 100
    ):

        return admin_referral_page(
            error=(
                "Commission rate must be "
                "between 0 and 100."
            )
        )


    # ======================================================
    # CREATE PROMOTER
    # ======================================================

    try:

        referral_code = (
            generate_referral_code()
        )


        promoter_id = add_promoter(

            full_name=full_name,

            phone=phone,

            email=email,

            referral_code=referral_code,

            commission_rate=commission_rate

        )


        referral_link = (
            f"{APP_URL}/payment"
            f"?ref={referral_code}"
        )


        dashboard_link = (
            f"{APP_URL}/referral/dashboard"
            f"?ref={referral_code}"
        )


        success_message = (
            "✅ Promoter created successfully.\n\n"
            f"Promoter ID: {promoter_id}\n"
            f"Name: {full_name}\n"
            f"Commission: {commission_rate:g}%\n"
            f"Referral Code: {referral_code}\n"
            f"Payment Link: {referral_link}\n"
            f"Dashboard Link: {dashboard_link}"
        )


        return admin_referral_page(
            success=success_message
        )


    except Exception as e:

        print(
            "ADMIN CREATE PROMOTER ERROR:",
            repr(e)
        )

        return admin_referral_page(
            error=(
                "Unable to create promoter. "
                "Please check the Railway logs."
            )
        )


# ==========================================================
# UPDATE WITHDRAWAL
# ==========================================================

def admin_update_withdrawal():

    if not admin_logged_in():

        return redirect(
            "/admin/referral"
        )


    withdrawal_id_raw = (
        request.form.get(
            "withdrawal_id",
            ""
        )
        or ""
    ).strip()


    status = (
        request.form.get(
            "status",
            ""
        )
        or ""
    ).strip().lower()


    try:

        withdrawal_id = int(
            withdrawal_id_raw
        )

    except Exception:

        return redirect(
            "/admin/referral"
        )


    allowed_statuses = {

        "processing",
        "successful",
        "failed",
        "cancelled"

    }


    if status not in allowed_statuses:

        return redirect(
            "/admin/referral"
        )


    try:

        update_withdrawal_status(

            withdrawal_id,

            status

        )

    except Exception as e:

        print(
            "ADMIN WITHDRAWAL UPDATE ERROR:",
            repr(e)
        )


    return redirect(
        "/admin/referral"
    )