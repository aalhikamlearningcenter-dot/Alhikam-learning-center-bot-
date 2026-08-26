# ==========================================================
# ALHIKAM LEARNING CENTER V2
# referral_dashboard.py
#
# REFERRAL DASHBOARD
# REFERRAL WITHDRAWAL
# ==========================================================

from flask import (
    request,
    render_template_string,
)

from database import (
    get_promoter_by_id,
    create_withdrawal,
    get_promoter_withdrawals,
)


# ==========================================================
# APP URL
# ==========================================================

APP_URL = (
    "https://precious-trust-production-956b.up.railway.app"
)


# ==========================================================
# DASHBOARD HTML
# ==========================================================

REFERRAL_DASHBOARD_HTML = """

<!DOCTYPE html>

<html>

<head>

<meta name="viewport"
content="width=device-width, initial-scale=1">

<title>ALHIKAM Referral Dashboard</title>

<style>

body{
    font-family:Arial,sans-serif;
    background:#f5f7f9;
    padding:20px;
    margin:0;
}

.container{
    max-width:600px;
    margin:auto;
}

.header{
    background:#087f5b;
    color:white;
    padding:25px;
    border-radius:15px;
    margin-bottom:20px;
}

.header h2{
    margin:0 0 8px 0;
}

.card{
    background:white;
    padding:20px;
    border-radius:15px;
    margin-bottom:15px;
    box-shadow:0 3px 10px rgba(0,0,0,.08);
}

.label{
    color:#666;
    font-size:14px;
    margin-bottom:6px;
}

.value{
    font-size:24px;
    font-weight:bold;
}

.code{
    background:#eef8f4;
    padding:15px;
    border-radius:10px;
    font-weight:bold;
    font-size:20px;
    word-break:break-all;
}

.link{
    background:#f4f4f4;
    padding:15px;
    border-radius:10px;
    word-break:break-all;
    font-size:14px;
}

.grid{
    display:grid;
    grid-template-columns:1fr 1fr;
    gap:12px;
}

.stat{
    background:white;
    padding:18px;
    border-radius:12px;
    box-shadow:0 2px 8px rgba(0,0,0,.06);
}

.withdraw{
    display:block;
    width:100%;
    padding:16px;
    background:#087f5b;
    color:white;
    text-decoration:none;
    text-align:center;
    border-radius:10px;
    font-size:18px;
    font-weight:bold;
    box-sizing:border-box;
}

.withdraw-disabled{
    display:block;
    width:100%;
    padding:16px;
    background:#999;
    color:white;
    text-align:center;
    border-radius:10px;
    font-size:17px;
    font-weight:bold;
    box-sizing:border-box;
}

.copy{
    margin-top:10px;
    width:100%;
    padding:12px;
    border:none;
    background:#229ED9;
    color:white;
    border-radius:8px;
    font-size:15px;
}

.small{
    color:#666;
    font-size:13px;
    line-height:1.5;
}

.withdraw-item{
    border:1px solid #eee;
    padding:14px;
    border-radius:10px;
    margin-top:10px;
}

.pending{
    color:#d97706;
    font-weight:bold;
}

.successful{
    color:#087f5b;
    font-weight:bold;
}

.failed{
    color:#dc2626;
    font-weight:bold;
}

.cancelled{
    color:#dc2626;
    font-weight:bold;
}

.processing{
    color:#2563eb;
    font-weight:bold;
}

</style>

</head>

<body>

<div class="container">


<div class="header">

<h2>
🎯 ALHIKAM Referral Dashboard
</h2>

<div>
Welcome,
<b>{{ promoter_name }}</b>
</div>

</div>


<!-- =====================================================
     REFERRAL CODE
====================================================== -->

<div class="card">

<div class="label">
🔑 Your Referral Code
</div>

<div class="code">
{{ referral_code }}
</div>

<button
class="copy"
onclick="copyText('{{ referral_code }}')"
>
📋 Copy Referral Code
</button>

</div>


<!-- =====================================================
     REFERRAL LINK
====================================================== -->

<div class="card">

<div class="label">
🔗 Your Referral Link
</div>

<div class="link">
{{ referral_link }}
</div>

<button
class="copy"
onclick="copyText('{{ referral_link }}')"
>
📋 Copy Referral Link
</button>

</div>


<!-- =====================================================
     STATISTICS
====================================================== -->

<div class="grid">


<div class="stat">

<div class="label">
👥 Total Sales
</div>

<div class="value">
{{ total_sales }}
</div>

</div>


<div class="stat">

<div class="label">
💰 Total Earned
</div>

<div class="value">
₦{{ total_earned }}
</div>

</div>


<div class="stat">

<div class="label">
💵 Available Balance
</div>

<div class="value">
₦{{ available_balance }}
</div>

</div>


<div class="stat">

<div class="label">
💸 Withdrawn
</div>

<div class="value">
₦{{ withdrawn_amount }}
</div>

</div>


</div>


<!-- =====================================================
     WITHDRAWAL
====================================================== -->

<div class="card">

<h3>
💳 Withdrawal
</h3>

<p class="small">

Minimum withdrawal:
<b>₦5,000</b>

<br><br>

Available balance:
<b>₦{{ available_balance }}</b>

</p>


{% if available_balance_number >= 5000 %}

<a
class="withdraw"
href="/referral/withdraw?promoter_id={{ promoter_id }}"
>
💸 WITHDRAW MONEY
</a>

{% else %}

<div class="withdraw-disabled">
🔒 Minimum ₦5,000 Required
</div>

{% endif %}

</div>


<!-- =====================================================
     WITHDRAWAL HISTORY
====================================================== -->

<div class="card">

<h3>
📋 Withdrawal History
</h3>


{% if withdrawals %}

{% for withdrawal in withdrawals %}

<div class="withdraw-item">

<div>
<b>
Request #{{ withdrawal["id"] }}
</b>
</div>

<br>

<div>
Amount:
<b>
₦{{ "{:,.0f}".format(
    float(withdrawal["amount"] or 0)
) }}
</b>
</div>

<br>

<div>
Bank:
{{ withdrawal["bank_name"] }}
</div>

<div>
Account:
{{ withdrawal["account_number"] }}
</div>

<br>

<div>

Status:

<span class="{{ withdrawal['status'] }}">

{{ withdrawal["status"]|capitalize }}

</span>

</div>

<br>

<div class="small">

{{ withdrawal["created_at"] }}

</div>

</div>

{% endfor %}

{% else %}

<p class="small">
No withdrawal request yet.
</p>

{% endif %}

</div>


<!-- =====================================================
     REFERRAL INFORMATION
====================================================== -->

<div class="card">

<h3>
📌 Referral Information
</h3>

<p class="small">

Share your referral link with students.

When a student registers and successfully
pays through your referral link, your commission
will automatically be added to your balance.

</p>

</div>


</div>


<script>

function copyText(text){

    if(
        navigator.clipboard &&
        navigator.clipboard.writeText
    ){

        navigator.clipboard.writeText(text)
        .then(function(){

            alert("Copied successfully!");

        })
        .catch(function(){

            alert("Unable to copy.");

        });

    }else{

        alert("Copy is not supported on this browser.");

    }

}

</script>

</body>

</html>

"""


# ==========================================================
# REFERRAL DASHBOARD
# ==========================================================
#
# main.py zai kira:
#
# referral_dashboard(promoter_id)
#
# ==========================================================

def referral_dashboard(promoter_id):

    # ------------------------------------------------------
    # Validate promoter ID
    # ------------------------------------------------------

    if not promoter_id:

        return (
            "Promoter ID is required.",
            400
        )

    try:

        promoter_id = int(
            promoter_id
        )

    except (TypeError, ValueError):

        return (
            "Invalid promoter ID.",
            400
        )

    # ------------------------------------------------------
    # Get promoter
    # ------------------------------------------------------

    try:

        promoter = get_promoter_by_id(
            promoter_id
        )

    except Exception:

        return (
            "Unable to load referral account.",
            500
        )

    # ------------------------------------------------------
    # Check promoter
    # ------------------------------------------------------

    if not promoter:

        return (
            "Promoter account not found.",
            404
        )

    # ------------------------------------------------------
    # Check active status
    # ------------------------------------------------------

    if promoter["status"] != "active":

        return (
            "This referral account is not active.",
            403
        )

    # ------------------------------------------------------
    # Get withdrawal history
    # ------------------------------------------------------

    try:

        withdrawals = (
            get_promoter_withdrawals(
                promoter_id
            )
        )

    except Exception:

        withdrawals = []

    # ------------------------------------------------------
    # Balance
    # ------------------------------------------------------

    available_balance_number = float(
        promoter["available_balance"] or 0
    )

    # ------------------------------------------------------
    # Referral link
    # ------------------------------------------------------

    referral_link = (
        f"{APP_URL}/payment"
        f"?ref={promoter['referral_code']}"
    )

    # ------------------------------------------------------
    # Render dashboard
    # ------------------------------------------------------

    return render_template_string(

        REFERRAL_DASHBOARD_HTML,

        promoter_id=promoter["id"],

        promoter_name=promoter["full_name"],

        referral_code=promoter["referral_code"],

        referral_link=referral_link,

        total_sales=int(
            promoter["total_sales"] or 0
        ),

        total_earned=f"{float(
            promoter['total_earned'] or 0
        ):,.0f}",

        available_balance=f"{available_balance_number:,.0f}",

        available_balance_number=(
            available_balance_number
        ),

        withdrawn_amount=f"{float(
            promoter['withdrawn_amount'] or 0
        ):,.0f}",

        withdrawals=withdrawals

    )


# ==========================================================
# DASHBOARD BY REFERRAL CODE
# ==========================================================
#
# Wannan function tana taimakawa idan wani code ya kira
# dashboard directly.
#
# ==========================================================

def referral_dashboard_by_code(
    referral_code
):

    from database import (
        get_promoter_by_referral_code
    )

    referral_code = (
        referral_code or ""
    ).strip()

    if not referral_code:

        return (
            "Referral code is required.",
            400
        )

    promoter = (
        get_promoter_by_referral_code(
            referral_code
        )
    )

    if not promoter:

        return (
            "Invalid referral code.",
            404
        )

    return referral_dashboard(
        promoter["id"]
    )


# ==========================================================
# WITHDRAWAL HTML
# ==========================================================

WITHDRAWAL_HTML = """

<!DOCTYPE html>

<html>

<head>

<meta name="viewport"
content="width=device-width, initial-scale=1">

<title>ALHIKAM Withdrawal</title>

<style>

body{
    font-family:Arial,sans-serif;
    background:#f5f7f9;
    padding:20px;
    margin:0;
}

.container{
    max-width:550px;
    margin:auto;
    background:white;
    padding:25px;
    border-radius:15px;
}

input,
select{
    width:100%;
    padding:14px;
    margin-top:8px;
    margin-bottom:18px;
    box-sizing:border-box;
    border:1px solid #ccc;
    border-radius:8px;
    font-size:16px;
}

button{
    width:100%;
    padding:15px;
    background:#087f5b;
    color:white;
    border:none;
    border-radius:10px;
    font-size:18px;
    font-weight:bold;
}

.balance{
    background:#e8f7ef;
    padding:15px;
    border-radius:10px;
    margin-bottom:20px;
}

.error{
    background:#fee2e2;
    color:#991b1b;
    padding:15px;
    border-radius:10px;
    margin-bottom:20px;
}

</style>

</head>

<body>

<div class="container">

<h2>
💸 Withdraw Referral Commission
</h2>

<div class="balance">

Available Balance:

<br>

<b>
₦{{ balance }}
</b>

</div>


<form method="POST">

<input
type="hidden"
name="promoter_id"
value="{{ promoter_id }}"
>


<label>
<b>Amount</b>
</label>

<input
type="number"
name="amount"
min="5000"
max="{{ balance_number }}"
step="1"
placeholder="Enter withdrawal amount"
required
>


<label>
<b>Bank</b>
</label>

<select
name="bank_name"
required
>

<option value="">
Select Bank
</option>

<option>Opay</option>
<option>Palmpay</option>
<option>Moniepoint</option>
<option>Access Bank</option>
<option>GTBank</option>
<option>UBA</option>
<option>Zenith Bank</option>
<option>First Bank</option>
<option>Union Bank</option>
<option>Jaiz Bank</option>
<option>Kuda</option>

</select>


<label>
<b>Account Name</b>
</label>

<input
type="text"
name="account_name"
autocomplete="name"
required
>


<label>
<b>Account Number</b>
</label>

<input
type="text"
name="account_number"
maxlength="10"
inputmode="numeric"
pattern="[0-9]{10}"
required
>


<button type="submit">
💸 REQUEST WITHDRAWAL
</button>

</form>

</div>

</body>

</html>

"""


# ==========================================================
# WITHDRAWAL PAGE
# ==========================================================
#
# main.py zai kira:
#
# withdrawal_page(promoter_id)
#
# ==========================================================

def withdrawal_page(promoter_id):

    # ------------------------------------------------------
    # Validate promoter ID
    # ------------------------------------------------------

    if not promoter_id:

        return (
            "Promoter ID is required.",
            400
        )

    try:

        promoter_id = int(
            promoter_id
        )

    except (TypeError, ValueError):

        return (
            "Invalid promoter ID.",
            400
        )

    # ------------------------------------------------------
    # Get promoter
    # ------------------------------------------------------

    promoter = get_promoter_by_id(
        promoter_id
    )

    if not promoter:

        return (
            "Promoter account not found.",
            404
        )

    # ------------------------------------------------------
    # Check active
    # ------------------------------------------------------

    if promoter["status"] != "active":

        return (
            "This referral account is not active.",
            403
        )

    # ------------------------------------------------------
    # Current balance
    # ------------------------------------------------------

    balance = float(
        promoter["available_balance"] or 0
    )

    # ======================================================
    # GET
    # ======================================================

    if request.method == "GET":

        return render_template_string(

            WITHDRAWAL_HTML,

            promoter_id=promoter_id,

            balance=f"{balance:,.0f}",

            balance_number=balance

        )

    # ======================================================
    # POST
    # ======================================================

    # ------------------------------------------------------
    # Amount
    # ------------------------------------------------------

    try:

        amount = float(
            request.form.get(
                "amount",
                0
            )
        )

    except Exception:

        amount = 0

    # ------------------------------------------------------
    # Bank
    # ------------------------------------------------------

    bank_name = (
        request.form.get(
            "bank_name",
            ""
        )
        or ""
    ).strip()

    # ------------------------------------------------------
    # Account name
    # ------------------------------------------------------

    account_name = (
        request.form.get(
            "account_name",
            ""
        )
        or ""
    ).strip()

    # ------------------------------------------------------
    # Account number
    # ------------------------------------------------------

    account_number = (
        request.form.get(
            "account_number",
            ""
        )
        or ""
    ).strip()

    # ------------------------------------------------------
    # Basic validation
    # ------------------------------------------------------

    if amount < 5000:

        return (
            "Minimum withdrawal is ₦5,000.",
            400
        )

    if amount > balance:

        return (
            "Insufficient available balance.",
            400
        )

    if not bank_name:

        return (
            "Bank name is required.",
            400
        )

    if not account_name:

        return (
            "Account name is required.",
            400
        )

    if len(account_number) != 10:

        return (
            "Account number must contain 10 digits.",
            400
        )

    if not account_number.isdigit():

        return (
            "Account number must contain digits only.",
            400
        )

    # ======================================================
    # CREATE WITHDRAWAL
    # ======================================================

    try:

        withdrawal_id = create_withdrawal(

            promoter_id=promoter_id,

            amount=amount,

            bank_name=bank_name,

            account_name=account_name,

            account_number=account_number

        )

    except ValueError as e:

        return (

            f"""
            <div style="
                font-family:Arial;
                text-align:center;
                padding:40px;
            ">

            <h2>
            ❌ Withdrawal Failed
            </h2>

            <p>
            {str(e)}
            </p>

            <br>

            <a href="/referral/dashboard?promoter_id={promoter_id}">
            ← Back to Dashboard
            </a>

            </div>
            """,

            400

        )

    except Exception as e:

        print(
            "Withdrawal error:",
            repr(e)
        )

        return (

            """
            <div style="
                font-family:Arial;
                text-align:center;
                padding:40px;
            ">

            <h2>
            ❌ Withdrawal Request Failed
            </h2>

            <p>
            Please try again later.
            </p>

            </div>
            """,

            500

        )

    # ======================================================
    # SUCCESS
    # ======================================================

    return """

    <div style="
        font-family:Arial;
        text-align:center;
        padding:40px;
    ">

    <h2>
    ✅ Withdrawal Request Received
    </h2>

    <p>
    Your withdrawal request has been recorded successfully.
    </p>

    <p>
    Amount:
    <b>₦{0:,.0f}</b>
    </p>

    <p>
    Request ID:
    <b>#{1}</b>
    </p>

    <p>
    Status:
    <b>Pending</b>
    </p>

    <p style="
        color:#666;
        font-size:14px;
    ">
    Your balance has already been reserved for this
    withdrawal request.
    </p>

    <br>

    <a href="/referral/dashboard?promoter_id={2}">
    ← Back to Dashboard
    </a>

    </div>

    """.format(

        amount,

        withdrawal_id,

        promoter_id

    )