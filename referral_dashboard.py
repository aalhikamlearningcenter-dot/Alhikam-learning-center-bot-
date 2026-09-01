# ==========================================================
# ALHIKAM LEARNING CENTER V2
# referral_dashboard.py
#
# REFERRAL DASHBOARD
# AUTOMATIC WITHDRAWAL
# FLUTTERWAVE TRANSFER
#
# MINIMUM WITHDRAWAL = ₦200
# ==========================================================

import os
import requests

from flask import (
    request,
    render_template_string,
)

from database import (
    get_promoter_by_id,
    get_promoter_by_referral_code,
    create_withdrawal,
    mark_withdrawal_successful,
    refund_withdrawal,
    update_withdrawal_transfer,
)

from transfer import (
    create_flutterwave_transfer,
)


# ==========================================================
# CONFIG
# ==========================================================

APP_URL = os.getenv(
    "APP_URL",
    "https://precious-trust-production-956b.up.railway.app"
).rstrip("/")

FLW_SECRET_KEY = os.getenv(
    "FLW_SECRET_KEY"
)

FLUTTERWAVE_BANKS_URL = (
    "https://api.flutterwave.com/v3/banks/NG"
)


# ==========================================================
# MINIMUM WITHDRAWAL
# ==========================================================

MINIMUM_WITHDRAWAL = 200


# ==========================================================
# GET NIGERIAN BANKS
# ==========================================================

def get_nigerian_banks():

    if not FLW_SECRET_KEY:

        print(
            "ERROR: FLW_SECRET_KEY is missing."
        )

        return []

    headers = {
        "Authorization":
            f"Bearer {FLW_SECRET_KEY}",

        "Content-Type":
            "application/json",
    }

    try:

        response = requests.get(
            FLUTTERWAVE_BANKS_URL,
            headers=headers,
            timeout=30,
        )

        print(
            "Flutterwave banks HTTP status:",
            response.status_code
        )

        if response.status_code != 200:

            print(
                "Flutterwave banks error:",
                response.text
            )

            return []

        result = response.json()

        if result.get("status") != "success":

            print(
                "Flutterwave banks API error:",
                result
            )

            return []

        return result.get("data") or []

    except Exception as e:

        print(
            "Bank lookup error:",
            repr(e)
        )

        return []


# ==========================================================
# REFERRAL DASHBOARD HTML
# ==========================================================

REFERRAL_DASHBOARD_HTML = """

<!DOCTYPE html>

<html>

<head>

<meta
    name="viewport"
    content="width=device-width, initial-scale=1"
>

<title>ALHIKAM Referral Dashboard</title>

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

    box-shadow:
        0 3px 10px
        rgba(0,0,0,.08);
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

    box-shadow:
        0 2px 8px
        rgba(0,0,0,.06);
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

    border:none;

    cursor:pointer;
}

.withdraw-disabled{

    background:#999;

    cursor:not-allowed;
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

<div class="card">

<div class="label">
    🔑 Your Referral Code
</div>

<div class="code">
    {{ referral_code }}
</div>

<button
    class="copy"
    onclick="copyText({{ referral_code|tojson }})"
>
    📋 Copy Referral Code
</button>

</div>

<div class="card">

<div class="label">
    🔗 Your Referral Link
</div>

<div class="link">
    {{ referral_link }}
</div>

<button
    class="copy"
    onclick="copyText({{ referral_link|tojson }})"
>
    📋 Copy Referral Link
</button>

</div>

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

<div class="card">

<h3>
    💳 Withdrawal
</h3>

{% if available_balance_number >= minimum_withdrawal %}

<p class="small">

You can withdraw any amount from
<b>₦{{ minimum_withdrawal }}</b>
up to your available balance.

<br><br>

Your withdrawal will be sent automatically through Flutterwave.

</p>

<!-- IMPORTANT:
     Send referral_code to main.py.
-->

<a
    class="withdraw"
    href="/referral/withdraw?ref={{ referral_code|urlencode }}"
>
    💸 WITHDRAW MONEY
</a>

{% else %}

<p class="small">

Minimum withdrawal is
<b>₦{{ minimum_withdrawal }}</b>.

<br><br>

Your current balance is not enough
to request a withdrawal.

</p>

<button
    class="withdraw withdraw-disabled"
    disabled
>
    🔒 ₦{{ minimum_withdrawal }}
    MINIMUM REQUIRED
</button>

{% endif %}

</div>

<div class="card">

<h3>
    📌 Referral Information
</h3>

<p class="small">

Share your referral link with students.

<br><br>

When a student registers and successfully
pays through your referral link,
your commission is automatically added
to your available balance.

<br><br>

You can withdraw from
<b>₦{{ minimum_withdrawal }}</b>
and above.

</p>

</div>

</div>

<script>

function copyText(text){

    if(
        navigator.clipboard &&
        window.isSecureContext
    ){

        navigator.clipboard
        .writeText(text)

        .then(function(){

            alert(
                "Copied successfully!"
            );

        })

        .catch(function(){

            fallbackCopy(text);

        });

    }else{

        fallbackCopy(text);

    }

}

function fallbackCopy(text){

    const textarea =
        document.createElement("textarea");

    textarea.value = text;

    textarea.style.position = "fixed";

    textarea.style.left = "-9999px";

    document.body.appendChild(textarea);

    textarea.focus();

    textarea.select();

    try{

        document.execCommand("copy");

        alert(
            "Copied successfully!"
        );

    }catch(error){

        alert(
            "Copy failed. Please copy manually."
        );

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

    try:

        promoter = get_promoter_by_id(
            promoter_id
        )

    except Exception as e:

        print(
            "Promoter lookup error:",
            repr(e)
        )

        return (
            "Unable to load referral dashboard.",
            500
        )

    if not promoter:

        return (
            "Promoter account not found.",
            404
        )

    referral_code = str(
        promoter["referral_code"]
        or ""
    ).strip()

    if not referral_code:

        return (
            "Promoter referral code is missing.",
            500
        )

    referral_link = (
        f"{APP_URL}/payment"
        f"?ref={referral_code}"
    )

    total_sales = int(
        promoter["total_sales"]
        or 0
    )

    total_earned = float(
        promoter["total_earned"]
        or 0
    )

    available_balance = float(
        promoter["available_balance"]
        or 0
    )

    withdrawn_amount = float(
        promoter["withdrawn_amount"]
        or 0
    )

    return render_template_string(

        REFERRAL_DASHBOARD_HTML,

        promoter_id=promoter["id"],

        promoter_name=(
            promoter["full_name"]
            or ""
        ),

        referral_code=referral_code,

        referral_link=referral_link,

        total_sales=total_sales,

        total_earned=(
            f"{total_earned:,.0f}"
        ),

        available_balance=(
            f"{available_balance:,.0f}"
        ),

        available_balance_number=(
            available_balance
        ),

        withdrawn_amount=(
            f"{withdrawn_amount:,.0f}"
        ),

        minimum_withdrawal=(
            MINIMUM_WITHDRAWAL
        ),

    )


# ==========================================================
# REFERRAL DASHBOARD BY CODE
#
# main.py imports this function.
# ==========================================================

def referral_dashboard_by_code(
    referral_code=None
):

    referral_code = (
        referral_code
        or request.args.get("ref", "")
        or request.args.get(
            "referral_code",
            ""
        )
    ).strip()

    if not referral_code:

        return (
            "Referral code is required.",
            400
        )

    try:

        promoter = get_promoter_by_referral_code(
            referral_code
        )

    except Exception as e:

        print(
            "Referral code lookup error:",
            repr(e)
        )

        return (
            "Unable to load referral dashboard.",
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

<meta
    name="viewport"
    content="width=device-width, initial-scale=1"
>

<title>ALHIKAM Withdrawal</title>

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

.note{

    background:#fff8e1;

    padding:12px;

    border-radius:8px;

    margin-bottom:18px;

    font-size:13px;

    line-height:1.5;
}

.back{

    display:block;

    margin-top:20px;

    text-decoration:none;

    color:#087f5b;

    font-weight:bold;
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

<div class="note">

<b>
    Minimum withdrawal:
    ₦{{ minimum_withdrawal }}
</b>

<br><br>

You can withdraw any amount from
₦{{ minimum_withdrawal }}
up to your available balance.

<br><br>

The money will be sent automatically
through Flutterwave.

</div>

<form method="POST">

<!-- Keep referral code with the POST request -->
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
    min="{{ minimum_withdrawal }}"
    max="{{ balance_number }}"
    step="1"
    placeholder="Enter withdrawal amount"
    required
>

<label>
    <b>Bank</b>
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
    <b>Account Name</b>
</label>

<input
    type="text"
    name="account_name"
    placeholder="Account name"
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
    ← Back to Dashboard
</a>

</div>

</body>

</html>

"""


# ==========================================================
# WITHDRAWAL PAGE
#
# IMPORTANT:
# main.py calls:
#
#     withdrawal_page(
#         referral_code=referral_code
#     )
#
# So this function MUST accept referral_code.
# ==========================================================

def withdrawal_page(
    referral_code=None
):

    # ------------------------------------------------------
    # GET REFERRAL CODE
    # ------------------------------------------------------

    referral_code = (
        referral_code
        or request.args.get("ref", "")
        or request.args.get(
            "referral_code",
            ""
        )
        or request.form.get(
            "referral_code",
            ""
        )
    ).strip()

    if not referral_code:

        return (
            "Referral code is required.",
            400
        )

    # ------------------------------------------------------
    # FIND PROMOTER
    # ------------------------------------------------------

    try:

        promoter = get_promoter_by_referral_code(
            referral_code
        )

    except Exception as e:

        print(
            "Withdrawal promoter lookup error:",
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

    promoter_id = promoter["id"]

    if str(
        promoter["status"]
    ).lower() != "active":

        return (
            "This referral account is not active.",
            403
        )

    balance = float(
        promoter["available_balance"]
        or 0
    )

    # ======================================================
    # GET
    # ======================================================

    if request.method == "GET":

        if balance < MINIMUM_WITHDRAWAL:

            return (

                f"""
                <div
                    style="
                    font-family:Arial;
                    text-align:center;
                    padding:40px
                    "
                >

                    <h2>
                        🔒 Withdrawal Unavailable
                    </h2>

                    <p>
                        Minimum withdrawal is
                        <b>₦{MINIMUM_WITHDRAWAL}</b>.
                    </p>

                    <p>
                        Your available balance is
                        <b>₦{balance:,.0f}</b>.
                    </p>

                    <br>

                    <a
                        href="/referral/dashboard?ref={referral_code}"
                    >
                        ← Back to Dashboard
                    </a>

                </div>
                """

            )

        banks = get_nigerian_banks()

        if not banks:

            return (
                "Unable to load Nigerian banks. "
                "Please try again later.",
                503
            )

        return render_template_string(

            WITHDRAWAL_HTML,

            balance=f"{balance:,.0f}",

            balance_number=balance,

            promoter_id=promoter_id,

            referral_code=referral_code,

            banks=banks,

            minimum_withdrawal=(
                MINIMUM_WITHDRAWAL
            ),

        )

    # ======================================================
    # POST
    # ======================================================

    try:

        amount = float(
            request.form.get(
                "amount",
                0
            )
            or 0
        )

    except Exception:

        amount = 0

    bank_code = (
        request.form.get(
            "bank_code",
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
    # VALIDATE AMOUNT
    # ======================================================

    if amount < MINIMUM_WITHDRAWAL:

        return (
            f"Minimum withdrawal is "
            f"₦{MINIMUM_WITHDRAWAL}.",
            400
        )

    if amount > balance:

        return (
            "Insufficient available balance.",
            400
        )

    # ======================================================
    # VALIDATE ACCOUNT NAME
    # ======================================================

    if not account_name:

        return (
            "Account name is required.",
            400
        )

    # ======================================================
    # VALIDATE ACCOUNT NUMBER
    # ======================================================

    if (
        len(account_number) != 10
        or not account_number.isdigit()
    ):

        return (
            "Account number must contain exactly 10 digits.",
            400
        )

    # ======================================================
    # VALIDATE BANK
    # ======================================================

    if not bank_code:

        return (
            "Please select a valid bank.",
            400
        )

    # ======================================================
    # GET BANK NAME
    # ======================================================

    banks = get_nigerian_banks()

    bank_name = None

    for bank in banks:

        if (
            str(
                bank.get("code", "")
            ).strip()
            == bank_code
        ):

            bank_name = (
                bank.get(
                    "name",
                    bank_code
                )
            )

            break

    if not bank_name:

        return (
            "Invalid bank selected.",
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

            bank_code=bank_code,

            account_name=account_name,

            account_number=account_number,

        )

    except ValueError as e:

        return (
            str(e),
            400
        )

    except Exception as e:

        print(
            "Withdrawal creation error:",
            repr(e)
        )

        return (
            "Unable to create withdrawal.",
            500
        )

    # ======================================================
# FLUTTERWAVE TRANSFER
# ======================================================

try:

    transfer_result = (
        create_flutterwave_transfer(

            amount=amount,

            account_number=account_number,

            bank_code=bank_code,

            account_name=account_name,

            narration=(
                "ALHIKAM Referral Commission"
            ),

        )
    )

except Exception as e:

    print(
        "Flutterwave transfer error:",
        repr(e)
    )

    transfer_result = None


# ======================================================
# TRANSFER REQUEST FAILED
# ======================================================

if not transfer_result:

    try:

        refund_withdrawal(

            withdrawal_id=withdrawal_id,

            transfer_status="failed",

            transfer_message=(
                "Flutterwave transfer request failed."
            ),

        )

    except Exception as e:

        print(
            "Withdrawal refund error:",
            repr(e)
        )

    return (

        f"""
        <div
            style="
            font-family:Arial;
            text-align:center;
            padding:40px
            "
        >

            <h2>
                ❌ Transfer Failed
            </h2>

            <p>
                We could not process your withdrawal.
            </p>

            <p>
                Your balance has been restored.
            </p>

            <br>

            <a
                href="/referral/dashboard?ref={referral_code}"
            >
                ← Back to Dashboard
            </a>

        </div>
        """

    )


# ======================================================
# TRANSFER INFORMATION
# ======================================================

transfer_id = (
    transfer_result.get(
        "transfer_id"
    )
)

transfer_reference = (
    transfer_result.get(
        "reference"
    )
)

transfer_status = str(
    transfer_result.get(
        "status",
        "NEW"
    )
    or "NEW"
).upper().strip()

transfer_message = (
    transfer_result.get(
        "message"
    )
)


# ======================================================
# SAVE TRANSFER INFORMATION
# ======================================================

try:

    update_withdrawal_transfer(

        withdrawal_id=withdrawal_id,

        transfer_reference=(
            transfer_reference
        ),

        transfer_id=(
            transfer_id
        ),

        transfer_status=(
            transfer_status
        ),

        transfer_message=(
            transfer_message
        ),

    )

except Exception as e:

    print(
        "Transfer information update error:",
        repr(e)
    )


# ======================================================
# FINAL STATUS CHECK
# ======================================================

final_status = transfer_status


if transfer_id:

    try:

        status_result = (
            get_flutterwave_transfer_status(
                transfer_id
            )
        )

    except Exception as e:

        print(
            "Flutterwave status check error:",
            repr(e)
        )

        status_result = None

    if status_result:

        final_status = str(
            status_result.get(
                "status",
                transfer_status
            )
            or transfer_status
        ).upper().strip()

        transfer_message = (
            status_result.get(
                "message"
            )
            or transfer_message
        )

        transfer_reference = (
            status_result.get(
                "reference"
            )
            or transfer_reference
        )

        update_withdrawal_transfer(

            withdrawal_id=withdrawal_id,

            transfer_reference=(
                transfer_reference
            ),

            transfer_id=(
                transfer_id
            ),

            transfer_status=(
                final_status
            ),

            transfer_message=(
                transfer_message
            ),

        )


# ======================================================
# SUCCESS
# ======================================================

if final_status in {
    "SUCCESSFUL",
    "COMPLETED",
    "SUCCESS"
}:

    try:

        mark_withdrawal_successful(

            withdrawal_id=withdrawal_id,

            transfer_id=transfer_id,

            transfer_reference=(
                transfer_reference
            ),

            transfer_message=(
                transfer_message
            ),

        )

    except Exception as e:

        print(
            "Withdrawal success update error:",
            repr(e)
        )

        return (
            "Transfer was successful, "
            "but withdrawal record could not be updated. "
            "Please contact admin.",
            500
        )

    result_title = "✅ Withdrawal Successful"

    result_message = (
        "Your referral commission has "
        "been sent successfully."
    )


# ======================================================
# CONFIRMED FAILED
# ======================================================

elif final_status in {
    "FAILED",
    "CANCELLED"
}:

    try:

        refund_withdrawal(

            withdrawal_id=withdrawal_id,

            transfer_status=(
                final_status.lower()
            ),

            transfer_message=(
                transfer_message
            ),

        )

    except Exception as e:

        print(
            "Withdrawal refund error:",
            repr(e)
        )

        return (
            "Transfer failed, but automatic refund "
            "could not be completed. Please contact admin.",
            500
        )

    result_title = "❌ Transfer Failed"

    result_message = (
        "The transfer failed and your balance "
        "has been restored."
    )


# ======================================================
# PENDING / PROCESSING / NEW
# ======================================================

else:

    # IMPORTANT:
    # DO NOT REFUND.
    #
    # The money remains reserved until the
    # transfer is confirmed successful or failed.

    result_title = "⏳ Withdrawal Processing"

    result_message = (
        "Your withdrawal has been submitted "
        "to Flutterwave and is still processing. "
        "Your balance has been reserved."
    )


# ======================================================
# RESULT PAGE
# ======================================================

return (

    f"""
    <div
        style="
        font-family:Arial;
        text-align:center;
        padding:40px
        "
    >

        <h2>
            {result_title}
        </h2>

        <p>
            {result_message}
        </p>

        <p>
            Amount:
            <b>
                ₦{amount:,.0f}
            </b>
        </p>

        <p>
            Account:
            <b>
                ****{account_number[-4:]}
            </b>
        </p>

        <p>
            Reference:
            <b>
                {transfer_reference or "N/A"}
            </b>
        </p>

        <p>
            Status:
            <b>
                {final_status or "PROCESSING"}
            </b>
        </p>

        <br>

        <a
            href="/referral/dashboard?ref={referral_code}"
        >
            ← Back to Dashboard
        </a>

    </div>
    """

)