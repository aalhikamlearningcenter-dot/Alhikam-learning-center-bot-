# ==========================================================
# ALHIKAM LEARNING CENTER V2
# referral_dashboard.py
#
# REFERRAL DASHBOARD
# WITHDRAWAL
# FLUTTERWAVE TRANSFER
# WITHDRAWAL STATUS
#
# MINIMUM WITHDRAWAL = ₦200
# ==========================================================

import logging
import math

from flask import (
    request,
    redirect,
    render_template_string,
)

from database import (
    get_promoter_by_referral_code,
    create_withdrawal,
    get_promoter_withdrawals,
    get_withdrawal_by_id,
    update_withdrawal_transfer,
    process_transfer_result,
)

from transfer import (
    resolve_bank_account,
    create_flutterwave_transfer,
    get_flutterwave_transfer_status,
)


# ==========================================================
# LOGGING
# ==========================================================

logger = logging.getLogger("ALHIKAM")


# ==========================================================
# SETTINGS
# ==========================================================

MINIMUM_WITHDRAWAL = 200


# ==========================================================
# BANKS
# ==========================================================

BANKS = {

    "044": "Access Bank",
    "023": "Citibank Nigeria",
    "050": "Ecobank Nigeria",
    "011": "First Bank Nigeria",
    "214": "FCMB",
    "070": "Fidelity Bank",
    "058": "GTBank",
    "030": "Heritage Bank",
    "301": "Jaiz Bank",
    "082": "Keystone Bank",
    "221": "Stanbic IBTC",
    "068": "Standard Chartered Bank",
    "232": "Sterling Bank",
    "100": "SunTrust Bank",
    "032": "Union Bank",
    "033": "UBA",
    "215": "Unity Bank",
    "035": "Wema Bank",
    "057": "Zenith Bank",

    # Digital banks / wallets
    "090267": "Kuda Bank",
    "999991": "PalmPay",
    "999992": "OPay",

}


# ==========================================================
# HELPER
# ==========================================================

def row_value(row, key, default=None):

    if row is None:
        return default

    try:

        keys = row.keys()

        if key in keys:

            value = row[key]

            if value is None:
                return default

            return value

    except Exception:
        pass

    return default


# ==========================================================
# MONEY FORMAT
# ==========================================================

def money(value):

    try:

        value = float(value or 0)

        return f"₦{value:,.2f}"

    except Exception:

        return "₦0.00"


# ==========================================================
# REFERRAL DASHBOARD
# ==========================================================

def referral_dashboard_by_code(
    referral_code
):

    referral_code = (
        referral_code or ""
    ).strip()

    if not referral_code:

        return (
            "Referral code is required.",
            400
        )


    # ======================================================
    # GET PROMOTER
    # ======================================================

    try:

        promoter = (
            get_promoter_by_referral_code(
                referral_code
            )
        )

    except Exception:

        logger.exception(
            "Could not load promoter dashboard."
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


    # ======================================================
    # STATUS
    # ======================================================

    promoter_status = str(
        row_value(
            promoter,
            "status",
            ""
        )
        or ""
    ).lower().strip()


    if promoter_status != "active":

        return (
            "This referral account is not active.",
            403
        )


    # ======================================================
    # PROMOTER DATA
    # ======================================================

    promoter_id = row_value(
        promoter,
        "id",
        0
    )

    full_name = str(
        row_value(
            promoter,
            "full_name",
            ""
        )
        or ""
    )


    total_sales = row_value(
        promoter,
        "total_sales",
        0
    )

    total_earned = row_value(
        promoter,
        "total_earned",
        0
    )

    available_balance = row_value(
        promoter,
        "available_balance",
        0
    )

    withdrawn_amount = row_value(
        promoter,
        "withdrawn_amount",
        0
    )


    # ======================================================
    # WITHDRAWAL HISTORY
    # ======================================================

    try:

        withdrawals = (
            get_promoter_withdrawals(
                promoter_id
            )
        )

    except Exception:

        logger.exception(
            "Could not load withdrawal history."
        )

        withdrawals = []


    # ======================================================
    # REFERRAL LINK
    # ======================================================

    try:

        from config import APP_URL

        referral_link = (
            f"{APP_URL}/referral/"
            f"{referral_code}"
        )

    except Exception:

        referral_link = (
            f"/referral/{referral_code}"
        )


    # ======================================================
    # HTML
    # ======================================================

    html = """

<!DOCTYPE html>

<html>

<head>

<meta name="viewport"
      content="width=device-width, initial-scale=1">

<title>Alhikam Referral Dashboard</title>

<style>

body {

    margin: 0;

    padding: 0;

    font-family: Arial, sans-serif;

    background: #f4f7fb;

    color: #172033;

}

.container {

    max-width: 900px;

    margin: auto;

    padding: 20px;

}

.header {

    background: #111827;

    color: white;

    padding: 22px;

    border-radius: 18px;

    margin-bottom: 18px;

}

.header h1 {

    margin: 0 0 8px 0;

    font-size: 25px;

}

.header p {

    margin: 5px 0;

    opacity: .9;

}

.cards {

    display: grid;

    grid-template-columns:
        repeat(auto-fit, minmax(190px, 1fr));

    gap: 14px;

    margin-bottom: 18px;

}

.card {

    background: white;

    padding: 18px;

    border-radius: 16px;

    box-shadow:
        0 5px 18px rgba(0,0,0,.06);

}

.card-title {

    font-size: 13px;

    color: #6b7280;

    margin-bottom: 8px;

}

.card-value {

    font-size: 23px;

    font-weight: bold;

}

.section {

    background: white;

    padding: 18px;

    border-radius: 16px;

    margin-bottom: 18px;

    box-shadow:
        0 5px 18px rgba(0,0,0,.06);

}

.section h2 {

    margin-top: 0;

}

.referral-box {

    background: #f3f4f6;

    padding: 13px;

    border-radius: 10px;

    word-break: break-all;

    margin: 10px 0;

}

.button {

    display: inline-block;

    padding: 13px 18px;

    border-radius: 10px;

    background: #111827;

    color: white;

    text-decoration: none;

    font-weight: bold;

}

.button:hover {

    opacity: .9;

}

.withdraw {

    background: #047857;

}

table {

    width: 100%;

    border-collapse: collapse;

}

th, td {

    padding: 11px 7px;

    border-bottom: 1px solid #eee;

    text-align: left;

    font-size: 13px;

}

.status {

    font-weight: bold;

}

@media(max-width:600px) {

    .container {

        padding: 12px;

    }

    table {

        font-size: 12px;

    }

}

</style>

</head>


<body>


<div class="container">


<div class="header">

<h1>Alhikam Learning Center</h1>

<p>
Referral Dashboard
</p>

<p>
Welcome, {{ full_name }}
</p>

<p>
Referral Code:
<strong>{{ referral_code }}</strong>
</p>

</div>


<div class="cards">


<div class="card">

<div class="card-title">
Total Sales
</div>

<div class="card-value">
{{ total_sales }}
</div>

</div>


<div class="card">

<div class="card-title">
Total Earned
</div>

<div class="card-value">
{{ total_earned }}
</div>

</div>


<div class="card">

<div class="card-title">
Available Balance
</div>

<div class="card-value">
{{ available_balance }}
</div>

</div>


<div class="card">

<div class="card-title">
Withdrawn
</div>

<div class="card-value">
{{ withdrawn_amount }}
</div>

</div>


</div>


<div class="section">

<h2>Your Referral Link</h2>

<div class="referral-box">
{{ referral_link }}
</div>

<a
href="/referral/withdraw?ref={{ referral_code }}"
class="button withdraw">

Withdraw Commission

</a>

</div>


<div class="section">

<h2>Withdrawal History</h2>


{% if withdrawals %}

<table>

<thead>

<tr>

<th>ID</th>

<th>Amount</th>

<th>Bank</th>

<th>Status</th>

<th>Date</th>

</tr>

</thead>


<tbody>


{% for item in withdrawals %}

<tr>

<td>
#{{ item["id"] }}
</td>

<td>
{{ money(item["amount"]) }}
</td>

<td>
{{ item["bank_name"] }}
</td>

<td class="status">

{% set s = (item["status"] or "")|lower %}

{% if s == "successful" %}

Successful

{% elif s == "failed" %}

Failed

{% elif s == "cancelled" %}

Cancelled

{% elif s == "processing" %}

Processing

{% else %}

Pending

{% endif %}

</td>

<td>
{{ item["created_at"] or "" }}
</td>

</tr>

{% endfor %}


</tbody>

</table>


{% else %}

<p>
No withdrawal history yet.
</p>

{% endif %}


</div>


</div>


</body>

</html>

"""


    return render_template_string(

        html,

        full_name=full_name,

        referral_code=referral_code,

        referral_link=referral_link,

        total_sales=int(
            total_sales or 0
        ),

        total_earned=money(
            total_earned
        ),

        available_balance=money(
            available_balance
        ),

        withdrawn_amount=money(
            withdrawn_amount
        ),

        withdrawals=withdrawals,

        money=money,

    )


# ==========================================================
# WITHDRAWAL PAGE
# ==========================================================

def withdrawal_page(
    referral_code
):

    referral_code = (
        referral_code or ""
    ).strip()


    if not referral_code:

        return (
            "Referral code is required.",
            400
        )


    # ======================================================
    # GET PROMOTER
    # ======================================================

    try:

        promoter = (
            get_promoter_by_referral_code(
                referral_code
            )
        )

    except Exception:

        logger.exception(
            "Withdrawal promoter lookup failed."
        )

        return (
            "Unable to load promoter.",
            500
        )


    if not promoter:

        return (
            "Invalid referral code.",
            404
        )


    promoter_id = row_value(
        promoter,
        "id",
        0
    )

    full_name = str(
        row_value(
            promoter,
            "full_name",
            ""
        )
        or ""
    )

    available_balance = float(
        row_value(
            promoter,
            "available_balance",
            0
        )
        or 0
    )


    # ======================================================
    # PROCESS POST
    # ======================================================

    if request.method == "POST":

        # --------------------------------------------------
        # AMOUNT
        # --------------------------------------------------

        raw_amount = (
            request.form.get(
                "amount",
                ""
            )
            or ""
        ).strip()


        try:

            amount = float(
                raw_amount
            )

        except Exception:

            return render_template_string(

                WITHDRAWAL_HTML,

                referral_code=referral_code,

                full_name=full_name,

                available_balance=available_balance,

                banks=BANKS,

                error="Enter a valid withdrawal amount."

            )


        if not math.isfinite(amount):

            return render_template_string(

                WITHDRAWAL_HTML,

                referral_code=referral_code,

                full_name=full_name,

                available_balance=available_balance,

                banks=BANKS,

                error="Invalid withdrawal amount."

            )


        # --------------------------------------------------
        # MINIMUM
        # --------------------------------------------------

        if amount < MINIMUM_WITHDRAWAL:

            return render_template_string(

                WITHDRAWAL_HTML,

                referral_code=referral_code,

                full_name=full_name,

                available_balance=available_balance,

                banks=BANKS,

                error=(
                    f"Minimum withdrawal is "
                    f"₦{MINIMUM_WITHDRAWAL:,.0f}."
                )

            )


        # --------------------------------------------------
        # BALANCE
        # --------------------------------------------------

        if amount > available_balance:

            return render_template_string(

                WITHDRAWAL_HTML,

                referral_code=referral_code,

                full_name=full_name,

                available_balance=available_balance,

                banks=BANKS,

                error="Insufficient available balance."

            )


        # --------------------------------------------------
        # BANK
        # --------------------------------------------------

        bank_code = (
            request.form.get(
                "bank_code",
                ""
            )
            or ""
        ).strip()


        bank_name = BANKS.get(
            bank_code,
            ""
        )


        if not bank_code or not bank_name:

            return render_template_string(

                WITHDRAWAL_HTML,

                referral_code=referral_code,

                full_name=full_name,

                available_balance=available_balance,

                banks=BANKS,

                error="Please select a valid bank."

            )


        # --------------------------------------------------
        # ACCOUNT NUMBER
        # --------------------------------------------------

        account_number = (
            request.form.get(
                "account_number",
                ""
            )
            or ""
        ).strip()


        if (
            len(account_number) != 10
            or not account_number.isdigit()
        ):

            return render_template_string(

                WITHDRAWAL_HTML,

                referral_code=referral_code,

                full_name=full_name,

                available_balance=available_balance,

                banks=BANKS,

                error=(
                    "Account number must contain "
                    "exactly 10 digits."
                )

            )


        # ==================================================
        # RESOLVE BANK ACCOUNT
        # ==================================================

        try:

            resolved = resolve_bank_account(

                account_number=account_number,

                bank_code=bank_code,

            )

        except Exception:

            logger.exception(
                "Bank account resolve error."
            )

            resolved = None


        if not resolved:

            return render_template_string(

                WITHDRAWAL_HTML,

                referral_code=referral_code,

                full_name=full_name,

                available_balance=available_balance,

                banks=BANKS,

                error=(
                    "Unable to verify bank account. "
                    "Please check the bank and account number."
                )

            )


        resolved_account_name = str(

            resolved.get(
                "account_name",
                ""
            )

            or ""

        ).strip()


        resolved_account_number = str(

            resolved.get(
                "account_number",
                account_number
            )

            or account_number

        ).strip()


        resolved_bank_code = str(

            resolved.get(
                "bank_code",
                bank_code
            )

            or bank_code

        ).strip()


        if not resolved_account_name:

            return render_template_string(

                WITHDRAWAL_HTML,

                referral_code=referral_code,

                full_name=full_name,

                available_balance=available_balance,

                banks=BANKS,

                error="Bank account name could not be verified."

            )


        # ==================================================
        # CREATE LOCAL WITHDRAWAL
        #
        # This reserves the promoter balance.
        # ==================================================

        try:

            withdrawal_id = create_withdrawal(

                promoter_id=promoter_id,

                amount=amount,

                bank_name=bank_name,

                account_name=resolved_account_name,

                account_number=resolved_account_number,

                bank_code=resolved_bank_code,

            )

        except Exception as e:

            logger.exception(
                "Could not create withdrawal."
            )

            return render_template_string(

                WITHDRAWAL_HTML,

                referral_code=referral_code,

                full_name=full_name,

                available_balance=available_balance,

                banks=BANKS,

                error=str(e)

            )


        logger.info(

            "WITHDRAWAL CREATED | "
            "ID=%s | PROMOTER=%s | AMOUNT=%s",

            withdrawal_id,

            promoter_id,

            amount

        )


        # ==================================================
        # CREATE FLUTTERWAVE TRANSFER
        # ==================================================

        try:

            transfer = create_flutterwave_transfer(

                amount=amount,

                account_number=resolved_account_number,

                bank_code=resolved_bank_code,

                account_name=resolved_account_name,

                narration=(
                    "ALHIKAM Referral Commission"
                ),

            )

        except Exception as e:

            logger.exception(
                "Flutterwave transfer exception."
            )

            # ----------------------------------------------
            # IMPORTANT:
            # Transfer creation failed.
            # Refund reserved balance.
            # ----------------------------------------------

            try:

                process_transfer_result(

                    withdrawal_id=withdrawal_id,

                    transfer_status="FAILED",

                    transfer_message=str(e),

                )

            except Exception:

                logger.exception(
                    "Could not refund failed withdrawal."
                )


            return render_template_string(

                WITHDRAWAL_RESULT_HTML,

                referral_code=referral_code,

                withdrawal_id=withdrawal_id,

                amount=money(amount),

                status="FAILED",

                message=(
                    "Flutterwave could not create the transfer. "
                    "Your reserved balance has been returned."
                ),

            )


        # ==================================================
        # CHECK TRANSFER RESPONSE
        # ==================================================

        if not transfer or not transfer.get(
            "success",
            False
        ):

            message = str(

                transfer.get(
                    "message",
                    "Flutterwave transfer could not be created."
                )

                if transfer

                else
                "Flutterwave transfer could not be created."

            )


            try:

                process_transfer_result(

                    withdrawal_id=withdrawal_id,

                    transfer_status="FAILED",

                    transfer_message=message,

                )

            except Exception:

                logger.exception(
                    "Could not refund failed transfer."
                )


            return render_template_string(

                WITHDRAWAL_RESULT_HTML,

                referral_code=referral_code,

                withdrawal_id=withdrawal_id,

                amount=money(amount),

                status="FAILED",

                message=message,

            )


        # ==================================================
        # TRANSFER DATA
        # ==================================================

        transfer_id = transfer.get(
            "transfer_id"
        )

        transfer_reference = transfer.get(
            "reference"
        )

        transfer_status = str(

            transfer.get(
                "status",
                "NEW"
            )

            or "NEW"

        ).upper().strip()


        transfer_message = transfer.get(
            "message"
        )


        # ==================================================
        # SAVE TRANSFER DATA
        # ==================================================

        try:

            update_withdrawal_transfer(

                withdrawal_id=withdrawal_id,

                transfer_reference=transfer_reference,

                transfer_id=transfer_id,

                transfer_status=transfer_status,

                transfer_message=transfer_message,

            )

        except Exception:

            logger.exception(
                "Could not save transfer information."
            )


        # ==================================================
        # PROCESS RESULT
        # ==================================================

        try:

            process_transfer_result(

                withdrawal_id=withdrawal_id,

                transfer_status=transfer_status,

                transfer_id=transfer_id,

                transfer_reference=transfer_reference,

                transfer_message=transfer_message,

            )

        except Exception as e:

            logger.exception(
                "Could not process transfer result."
            )

            return render_template_string(

                WITHDRAWAL_RESULT_HTML,

                referral_code=referral_code,

                withdrawal_id=withdrawal_id,

                amount=money(amount),

                status="PROCESSING",

                message=(
                    "Transfer was created but its final "
                    "status is still being processed."
                ),

            )


        # ==================================================
        # SUCCESS
        # ==================================================

        if transfer_status in {

            "SUCCESSFUL",
            "SUCCESS",
            "COMPLETED"

        }:

            final_status = "SUCCESSFUL"

            final_message = (
                "Withdrawal was successfully sent "
                "to the bank account."
            )


        # ==================================================
        # FAILED
        # ==================================================

        elif transfer_status in {

            "FAILED",
            "CANCELLED",
            "CANCELED"

        }:

            final_status = "FAILED"

            final_message = (

                transfer_message

                or
                "Flutterwave transfer failed. "
                "Your balance has been restored."

            )


        # ==================================================
        # NEW / PENDING / PROCESSING
        # ==================================================

        else:

            final_status = "PROCESSING"

            final_message = (

                "Withdrawal request has been created. "
                "Flutterwave is processing the transfer. "
                "Your balance remains reserved until the "
                "final transfer status is known."

            )


        # ==================================================
        # RESULT
        # ==================================================

        return render_template_string(

            WITHDRAWAL_RESULT_HTML,

            referral_code=referral_code,

            withdrawal_id=withdrawal_id,

            amount=money(amount),

            status=final_status,

            message=final_message,

        )


    # ======================================================
    # GET
    # ======================================================

    return render_template_string(

        WITHDRAWAL_HTML,

        referral_code=referral_code,

        full_name=full_name,

        available_balance=available_balance,

        banks=BANKS,

        error="",

    )


# ==========================================================
# WITHDRAWAL STATUS PAGE
# ==========================================================

def withdrawal_status_page(
    withdrawal_id,
    referral_code
):

    referral_code = (
        referral_code or ""
    ).strip()


    if not referral_code:

        return (
            "Referral code is required.",
            400
        )


    # ======================================================
    # PROMOTER
    # ======================================================

    try:

        promoter = (
            get_promoter_by_referral_code(
                referral_code
            )
        )

    except Exception:

        logger.exception(
            "Could not verify promoter."
        )

        return (
            "Unable to verify referral account.",
            500
        )


    if not promoter:

        return (
            "Invalid referral code.",
            404
        )


    promoter_id = row_value(
        promoter,
        "id",
        0
    )


    # ======================================================
    # WITHDRAWAL
    # ======================================================

    try:

        withdrawal = (
            get_withdrawal_by_id(
                withdrawal_id
            )
        )

    except Exception:

        logger.exception(
            "Could not load withdrawal."
        )

        return (
            "Unable to load withdrawal.",
            500
        )


    if not withdrawal:

        return (
            "Withdrawal not found.",
            404
        )


    # ======================================================
    # SECURITY:
    # MAKE SURE THIS WITHDRAWAL BELONGS
    # TO THIS PROMOTER.
    # ======================================================

    if int(
        withdrawal["promoter_id"]
    ) != int(promoter_id):

        return (
            "You are not authorized to view this withdrawal.",
            403
        )


    # ======================================================
    # AUTO REFRESH FLUTTERWAVE STATUS
    # ======================================================

    current_status = str(

        withdrawal["status"]

        or ""

    ).lower().strip()


    transfer_id = withdrawal["transfer_id"]


    if (
        current_status == "processing"
        and transfer_id
    ):

        try:

            result = get_flutterwave_transfer_status(

                transfer_id

            )

        except Exception:

            logger.exception(
                "Could not refresh Flutterwave transfer."
            )

            result = None


        if result and result.get(
            "success",
            False
        ):

            transfer_status = str(

                result.get(
                    "status",
                    ""
                )

                or ""

            ).upper().strip()


            transfer_reference = result.get(
                "reference"
            )

            transfer_message = result.get(
                "message"
            )


            try:

                process_transfer_result(

                    withdrawal_id=withdrawal_id,

                    transfer_status=transfer_status,

                    transfer_id=transfer_id,

                    transfer_reference=transfer_reference,

                    transfer_message=transfer_message,

                )

            except Exception:

                logger.exception(
                    "Could not update withdrawal from "
                    "Flutterwave status."
                )


            withdrawal = (
                get_withdrawal_by_id(
                    withdrawal_id
                )
            )


    # ======================================================
    # FINAL DATA
    # ======================================================

    status = str(

        withdrawal["status"]

        or "pending"

    ).lower().strip()


    transfer_status = str(

        withdrawal["transfer_status"]

        or ""

    ).upper().strip()


    message = (

        withdrawal["transfer_message"]

        or ""

    )


    if status == "successful":

        title = "Withdrawal Successful"

        message = (
            message
            or
            "The money has been successfully sent "
            "to the bank account."
        )


    elif status in {
        "failed",
        "cancelled"
    }:

        title = "Withdrawal Failed"

        message = (
            message
            or
            "The transfer failed and your balance "
            "has been restored."
        )


    elif status == "processing":

        title = "Withdrawal Processing"

        message = (
            message
            or
            "Flutterwave is still processing your transfer."
        )


    else:

        title = "Withdrawal Pending"

        message = (
            message
            or
            "Your withdrawal request is pending."
        )


    # ======================================================
    # HTML
    # ======================================================

    return render_template_string(

        WITHDRAWAL_STATUS_HTML,

        title=title,

        referral_code=referral_code,

        withdrawal_id=withdrawal_id,

        amount=money(
            withdrawal["amount"]
        ),

        bank_name=withdrawal["bank_name"],

        account_name=withdrawal["account_name"],

        account_number=withdrawal["account_number"],

        status=status.upper(),

        transfer_status=transfer_status,

        transfer_id=withdrawal["transfer_id"] or "",

        transfer_reference=(
            withdrawal["transfer_reference"]
            or ""
        ),

        message=message,

    )


# ==========================================================
# WITHDRAWAL FORM HTML
# ==========================================================

WITHDRAWAL_HTML = """

<!DOCTYPE html>

<html>

<head>

<meta name="viewport"
      content="width=device-width, initial-scale=1">

<title>Withdraw Commission</title>

<style>

body {

    margin: 0;

    padding: 20px;

    background: #f4f7fb;

    font-family: Arial, sans-serif;

}

.container {

    max-width: 600px;

    margin: auto;

}

.box {

    background: white;

    padding: 22px;

    border-radius: 18px;

    box-shadow:
        0 5px 20px rgba(0,0,0,.07);

}

h1 {

    margin-top: 0;

}

.balance {

    background: #ecfdf5;

    padding: 15px;

    border-radius: 12px;

    margin-bottom: 18px;

}

.error {

    background: #fef2f2;

    color: #991b1b;

    padding: 13px;

    border-radius: 10px;

    margin-bottom: 15px;

}

label {

    display: block;

    font-weight: bold;

    margin-top: 15px;

    margin-bottom: 7px;

}

input,
select {

    width: 100%;

    box-sizing: border-box;

    padding: 13px;

    border: 1px solid #d1d5db;

    border-radius: 10px;

    font-size: 16px;

}

button {

    width: 100%;

    margin-top: 20px;

    padding: 14px;

    border: 0;

    border-radius: 10px;

    background: #047857;

    color: white;

    font-size: 16px;

    font-weight: bold;

}

.back {

    display: inline-block;

    margin-top: 15px;

    text-decoration: none;

    color: #111827;

}

.small {

    color: #6b7280;

    font-size: 13px;

    margin-top: 5px;

}

</style>

</head>


<body>


<div class="container">


<div class="box">


<h1>
Withdraw Commission
</h1>


<p>
Welcome, <strong>{{ full_name }}</strong>
</p>


<div class="balance">

Available Balance:

<strong>
₦{{ "{:,.2f}".format(available_balance) }}
</strong>

<br>

<span class="small">
Minimum withdrawal: ₦200
</span>

</div>


{% if error %}

<div class="error">
{{ error }}
</div>

{% endif %}


<form method="POST">


<input
type="hidden"
name="referral_code"
value="{{ referral_code }}"
>


<label>
Withdrawal Amount
</label>

<input
type="number"
name="amount"
min="200"
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

{% for code, name in banks.items() %}

<option value="{{ code }}">
{{ name }}
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
placeholder="10 digit account number"
required
>


<button type="submit">
Submit Withdrawal
</button>


</form>


<a
class="back"
href="/referral/dashboard?ref={{ referral_code }}"
>
← Back to Dashboard
</a>


</div>

</div>


</body>

</html>

"""


# ==========================================================
# WITHDRAWAL RESULT HTML
# ==========================================================

WITHDRAWAL_RESULT_HTML = """

<!DOCTYPE html>

<html>

<head>

<meta name="viewport"
      content="width=device-width, initial-scale=1">

<title>Withdrawal Result</title>

<style>

body {

    margin: 0;

    padding: 20px;

    background: #f4f7fb;

    font-family: Arial, sans-serif;

}

.box {

    max-width: 600px;

    margin: 40px auto;

    background: white;

    padding: 25px;

    border-radius: 18px;

    text-align: center;

    box-shadow:
        0 5px 20px rgba(0,0,0,.07);

}

.status {

    font-size: 25px;

    font-weight: bold;

    margin: 15px 0;

}

.message {

    line-height: 1.6;

    color: #4b5563;

}

a {

    display: inline-block;

    margin-top: 20px;

    padding: 13px 18px;

    background: #111827;

    color: white;

    text-decoration: none;

    border-radius: 10px;

}

</style>

</head>


<body>


<div class="box">


<h1>
Alhikam Learning Center
</h1>


<div class="status">
{{ status }}
</div>


<p>
Withdrawal ID:
<strong>
#{{ withdrawal_id }}
</strong>
</p>


<p>
Amount:
<strong>
{{ amount }}
</strong>
</p>


<p class="message">
{{ message }}
</p>


<a
href="/referral/withdraw/status/{{ withdrawal_id }}?ref={{ referral_code }}"
>
Check Withdrawal Status
</a>


<br>


<a
href="/referral/dashboard?ref={{ referral_code }}"
>
Back to Dashboard
</a>


</div>


</body>

</html>

"""


# ==========================================================
# WITHDRAWAL STATUS HTML
# ==========================================================

WITHDRAWAL_STATUS_HTML = """

<!DOCTYPE html>

<html>

<head>

<meta name="viewport"
      content="width=device-width, initial-scale=1">

<title>{{ title }}</title>

<style>

body {

    margin: 0;

    padding: 20px;

    background: #f4f7fb;

    font-family: Arial, sans-serif;

}

.box {

    max-width: 650px;

    margin: 30px auto;

    background: white;

    padding: 24px;

    border-radius: 18px;

    box-shadow:
        0 5px 20px rgba(0,0,0,.07);

}

.row {

    display: flex;

    justify-content: space-between;

    gap: 15px;

    padding: 12px 0;

    border-bottom: 1px solid #eee;

}

.label {

    color: #6b7280;

}

.value {

    font-weight: bold;

    text-align: right;

    word-break: break-word;

}

.message {

    margin-top: 20px;

    padding: 15px;

    background: #f3f4f6;

    border-radius: 10px;

    line-height: 1.6;

}

.button {

    display: inline-block;

    margin-top: 20px;

    padding: 13px 18px;

    background: #111827;

    color: white;

    text-decoration: none;

    border-radius: 10px;

}

</style>

</head>


<body>


<div class="box">


<h1>
{{ title }}
</h1>


<div class="row">

<span class="label">
Withdrawal ID
</span>

<span class="value">
#{{ withdrawal_id }}
</span>

</div>


<div class="row">

<span class="label">
Amount
</span>

<span class="value">
{{ amount }}
</span>

</div>


<div class="row">

<span class="label">
Bank
</span>

<span class="value">
{{ bank_name }}
</span>

</div>


<div class="row">

<span class="label">
Account Name
</span>

<span class="value">
{{ account_name }}
</span>

</div>


<div class="row">

<span class="label">
Account Number
</span>

<span class="value">
{{ account_number }}
</span>

</div>


<div class="row">

<span class="label">
Withdrawal Status
</span>

<span class="value">
{{ status }}
</span>

</div>


<div class="row">

<span class="label">
Flutterwave Status
</span>

<span class="value">
{{ transfer_status }}
</span>

</div>


{% if transfer_id %}

<div class="row">

<span class="label">
Transfer ID
</span>

<span class="value">
{{ transfer_id }}
</span>

</div>

{% endif %}


{% if transfer_reference %}

<div class="row">

<span class="label">
Transfer Reference
</span>

<span class="value">
{{ transfer_reference }}
</span>

</div>

{% endif %}


<div class="message">
{{ message }}
</div>


<a
class="button"
href="/referral/withdraw/status/{{ withdrawal_id }}?ref={{ referral_code }}"
>
Refresh Status
</a>


<a
class="button"
href="/referral/dashboard?ref={{ referral_code }}"
>
Dashboard
</a>


</div>


</body>

</html>

"""