# ==========================================================
# ALHIKAM LEARNING CENTER V2
# referral_dashboard.py
#
# REFERRAL DASHBOARD
# REFERRAL WITHDRAWAL
# ==========================================================

from flask import request, render_template_string

from database import (
    get_promoter_by_id,
    get_promoter_by_referral_code,
    create_withdrawal,
    get_promoter_withdrawals,
)

try:
    from config import APP_URL
except Exception:
    APP_URL = "https://precious-trust-production-956b.up.railway.app"


# ==========================================================
# SETTINGS
# ==========================================================

MIN_WITHDRAWAL = 5000


# ==========================================================
# HELPERS
# ==========================================================

def _clean_referral_code(referral_code):

    return str(
        referral_code or ""
    ).strip()


def _get_promoter_from_code(referral_code):

    referral_code = _clean_referral_code(
        referral_code
    )

    if not referral_code:
        return None

    return get_promoter_by_referral_code(
        referral_code
    )


def _money(value):

    try:
        return f"{float(value or 0):,.0f}"

    except Exception:
        return "0"


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
    max-width:600px;
    margin:auto;
}

.header{
    background:#087f5b;
    color:white;
    padding:25px 20px;
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
    box-shadow:0 3px 10px rgba(0,0,0,.08);
}

.label{
    color:#666;
    font-size:14px;
    margin-bottom:7px;
}

.value{
    font-size:23px;
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
    line-height:1.5;
}

.grid{
    display:grid;
    grid-template-columns:1fr 1fr;
    gap:12px;
    margin-bottom:15px;
}

.stat{
    background:white;
    padding:18px;
    border-radius:12px;
    box-shadow:0 2px 8px rgba(0,0,0,.06);
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
    cursor:pointer;
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
}

.withdraw-disabled{
    display:block;
    width:100%;
    padding:16px;
    background:#999;
    color:white;
    text-align:center;
    border-radius:10px;
    font-size:16px;
    font-weight:bold;
}

.small{
    color:#666;
    font-size:13px;
    line-height:1.6;
}

.withdraw-item{
    border:1px solid #eee;
    padding:14px;
    border-radius:10px;
    margin-top:10px;
    line-height:1.5;
}

.pending{
    color:#d97706;
    font-weight:bold;
}

.successful{
    color:#087f5b;
    font-weight:bold;
}

.failed,
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
onclick='copyText({{ referral_code|tojson }})'
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
onclick='copyText({{ referral_link|tojson }})'
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
<b>₦{{ min_withdrawal }}</b>

<br><br>

Available balance:
<b>₦{{ available_balance }}</b>

</p>


{% if available_balance_number >= min_withdrawal_number %}

<a
class="withdraw"
href="/referral/withdraw?ref={{ referral_code|urlencode }}"
>
💸 WITHDRAW MONEY
</a>

{% else %}

<div class="withdraw-disabled">
🔒 Minimum ₦{{ min_withdrawal }} Required
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
Account Name:
{{ withdrawal["account_name"] }}
</div>

<div>
Account:
{{ withdrawal["account_number"] }}
</div>

<br>

<div>

Status:

<span class="{{ withdrawal['status']|lower }}">

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
     INFORMATION
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

            fallbackCopy(text);

        });

    }else{

        fallbackCopy(text);

    }

}


function fallbackCopy(text){

    var textarea =
        document.createElement("textarea");

    textarea.value = text;

    textarea.style.position = "fixed";
    textarea.style.left = "-9999px";

    document.body.appendChild(textarea);

    textarea.focus();
    textarea.select();

    try{

        document.execCommand("copy");

        alert("Copied successfully!");

    }catch(error){

        alert("Unable to copy.");

    }

    document.body.removeChild(textarea);

}

</script>

</body>

</html>

"""


# ==========================================================
# REFERRAL DASHBOARD BY PROMOTER ID
# ==========================================================

def referral_dashboard(promoter_id):

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


    # ======================================================
    # GET PROMOTER
    # ======================================================

    try:

        promoter = get_promoter_by_id(
            promoter_id
        )

    except Exception as e:

        print(
            "Referral dashboard error:",
            repr(e)
        )

        return (
            "Unable to load referral account.",
            500
        )


    if not promoter:

        return (
            "Promoter account not found.",
            404
        )


    # ======================================================
    # ACTIVE CHECK
    # ======================================================

    if str(
        promoter["status"]
    ).lower() != "active":

        return (
            "This referral account is not active.",
            403
        )


    # ======================================================
    # WITHDRAWALS
    # ======================================================

    try:

        withdrawals = get_promoter_withdrawals(
            promoter_id
        )

    except Exception as e:

        print(
            "Withdrawal history error:",
            repr(e)
        )

        withdrawals = []


    # ======================================================
    # BALANCE
    # ======================================================

    try:

        available_balance_number = float(
            promoter["available_balance"] or 0
        )

    except Exception:

        available_balance_number = 0


    try:

        total_earned_number = float(
            promoter["total_earned"] or 0
        )

    except Exception:

        total_earned_number = 0


    try:

        withdrawn_amount_number = float(
            promoter["withdrawn_amount"] or 0
        )

    except Exception:

        withdrawn_amount_number = 0


    try:

        total_sales = int(
            promoter["total_sales"] or 0
        )

    except Exception:

        total_sales = 0


    # ======================================================
    # REFERRAL CODE
    # ======================================================

    referral_code = str(
        promoter["referral_code"] or ""
    ).strip()


    if not referral_code:

        return (
            "Referral code is missing.",
            500
        )


    # ======================================================
    # REFERRAL LINK
    # ======================================================

    base_url = (
        APP_URL or ""
    ).rstrip("/")


    referral_link = (
        f"{base_url}/payment"
        f"?ref={referral_code}"
    )


    # ======================================================
    # RENDER
    # ======================================================

    return render_template_string(

        REFERRAL_DASHBOARD_HTML,

        promoter_id=promoter["id"],

        promoter_name=(
            promoter["full_name"]
            or "Promoter"
        ),

        referral_code=referral_code,

        referral_link=referral_link,

        total_sales=total_sales,

        total_earned=(
            f"{total_earned_number:,.0f}"
        ),

        available_balance=(
            f"{available_balance_number:,.0f}"
        ),

        available_balance_number=(
            available_balance_number
        ),

        withdrawn_amount=(
            f"{withdrawn_amount_number:,.0f}"
        ),

        withdrawals=withdrawals,

        min_withdrawal=(
            f"{MIN_WITHDRAWAL:,.0f}"
        ),

        min_withdrawal_number=(
            MIN_WITHDRAWAL
        )

    )


# ==========================================================
# REFERRAL DASHBOARD BY CODE
# ==========================================================

def referral_dashboard_by_code(
    referral_code
):

    referral_code = _clean_referral_code(
        referral_code
    )

    if not referral_code:

        return (
            "Referral code is required.",
            400
        )


    try:

        promoter = _get_promoter_from_code(
            referral_code
        )

    except Exception as e:

        print(
            "Referral code lookup error:",
            repr(e)
        )

        return (
            "Unable to load referral account.",
            500
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
    max-width:550px;
    margin:auto;
    background:white;
    padding:25px;
    border-radius:15px;
    box-shadow:0 3px 12px rgba(0,0,0,.08);
}

input,
select{
    width:100%;
    padding:14px;
    margin-top:8px;
    margin-bottom:18px;
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
    cursor:pointer;
}

button:active{
    opacity:.8;
}

.balance{
    background:#e8f7ef;
    padding:15px;
    border-radius:10px;
    margin-bottom:20px;
}

.note{
    color:#666;
    font-size:13px;
    line-height:1.5;
}

.back{
    display:block;
    margin-top:18px;
    text-align:center;
    color:#087f5b;
    text-decoration:none;
}

.warning{
    background:#fff8e1;
    padding:12px;
    border-radius:8px;
    color:#7a5b00;
    font-size:13px;
    line-height:1.5;
    margin-bottom:18px;
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


<div class="warning">

⚠️ Please make sure the bank account name
and account number are correct before submitting
your withdrawal request.

</div>


<p class="note">

Minimum withdrawal:
<b>₦{{ min_withdrawal }}</b>

</p>


<form method="POST">

<input
type="hidden"
name="referral_code"
value="{{ referral_code }}"
>


<label>
<b>Amount</b>
</label>

<input
type="number"
name="amount"
min="{{ min_withdrawal_number }}"
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

<option>Access Bank</option>
<option>Citibank Nigeria</option>
<option>Ecobank</option>
<option>Fidelity Bank</option>
<option>First Bank</option>
<option>FCMB</option>
<option>Globus Bank</option>
<option>GTBank</option>
<option>Heritage Bank</option>
<option>Jaiz Bank</option>
<option>Keystone Bank</option>
<option>Kuda</option>
<option>Moniepoint</option>
<option>Opay</option>
<option>Palmpay</option>
<option>Polaris Bank</option>
<option>Premium Trust Bank</option>
<option>Stanbic IBTC</option>
<option>Standard Chartered</option>
<option>Sterling Bank</option>
<option>SunTrust Bank</option>
<option>UBA</option>
<option>Union Bank</option>
<option>Unity Bank</option>
<option>Wema Bank</option>
<option>Zenith Bank</option>

</select>


<label>
<b>Account Name</b>
</label>

<input
type="text"
name="account_name"
autocomplete="name"
maxlength="100"
placeholder="Enter account name"
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
placeholder="10 digit account number"
required
>


<button type="submit">
💸 REQUEST WITHDRAWAL
</button>

</form>


<a
class="back"
href="/referral/dashboard?ref={{ referral_code|urlencode }}"
>
← Back to Referral Dashboard
</a>


</div>

</body>

</html>

"""


# ==========================================================
# WITHDRAWAL PAGE
# ==========================================================

def withdrawal_page(
    referral_code
):

    referral_code = _clean_referral_code(
        referral_code
    )


    if not referral_code:

        return (
            "Referral code is required.",
            400
        )


    # ======================================================
    # GET PROMOTER
    # ======================================================

    try:

        promoter = _get_promoter_from_code(
            referral_code
        )

    except Exception as e:

        print(
            "Promoter lookup error:",
            repr(e)
        )

        return (
            "Unable to load promoter.",
            500
        )


    if not promoter:

        return (
            "Invalid promoter/referral code.",
            404
        )


    # ======================================================
    # ACTIVE CHECK
    # ======================================================

    if str(
        promoter["status"]
    ).lower() != "active":

        return (
            "This referral account is not active.",
            403
        )


    # ======================================================
    # BALANCE
    # ======================================================

    try:

        balance = float(
            promoter["available_balance"] or 0
        )

    except Exception:

        balance = 0


    # ======================================================
    # GET
    # ======================================================

    if request.method == "GET":

        return render_template_string(

            WITHDRAWAL_HTML,

            promoter_id=promoter["id"],

            referral_code=referral_code,

            balance=f"{balance:,.0f}",

            balance_number=balance,

            min_withdrawal=(
                f"{MIN_WITHDRAWAL:,.0f}"
            ),

            min_withdrawal_number=(
                MIN_WITHDRAWAL
            )

        )


    # ======================================================
    # POST
    # ======================================================

    amount_raw = (
        request.form.get(
            "amount",
            ""
        )
        or ""
    ).strip()


    try:

        amount = float(
            amount_raw
        )

    except Exception:

        amount = 0


    # ======================================================
    # FORM DATA
    # ======================================================

    bank_name = (
        request.form.get(
            "bank_name",
            ""
        )
        or ""
    ).strip()


    account_name = (
        request.form.get(
            "account_name",
            ""
        )
        or ""
    ).strip()


    account_number = (
        request.form.get(
            "account_number",
            ""
        )
        or ""
    ).strip()


    # ======================================================
    # VALIDATION
    # ======================================================

    if amount < MIN_WITHDRAWAL:

        return (
            f"Minimum withdrawal is ₦{MIN_WITHDRAWAL:,.0f}.",
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
            "Account number must contain exactly 10 digits.",
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

            promoter_id=promoter["id"],

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

            <a href="/referral/dashboard?ref={referral_code}">
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

            f"""
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

            <br>

            <a href="/referral/dashboard?ref={referral_code}">
            ← Back to Dashboard
            </a>

            </div>
            """,

            500

        )


    # ======================================================
    # SUCCESS
    # ======================================================

    return f"""

    <div style="
        font-family:Arial;
        text-align:center;
        padding:40px;
        font-family:Arial,sans-serif;
    ">

    <h2>
    ✅ Withdrawal Request Received
    </h2>

    <p>
    Your withdrawal request has been recorded successfully.
    </p>

    <p>
    Amount:
    <b>₦{amount:,.0f}</b>
    </p>

    <p>
    Request ID:
    <b>#{withdrawal_id}</b>
    </p>

    <p>
    Status:
    <b style="color:#d97706;">
    Pending
    </b>
    </p>

    <p style="
        color:#666;
        font-size:14px;
    ">
    Your balance has already been reserved for this
    withdrawal request.
    </p>

    <br>

    <a href="/referral/dashboard?ref={referral_code}">
    ← Back to Dashboard
    </a>

    </div>

    """