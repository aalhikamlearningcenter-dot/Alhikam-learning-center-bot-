# ==========================================================
# ALHIKAM LEARNING CENTER V2
# referral_dashboard.py
#
# REFERRAL DASHBOARD
# BANK ACCOUNT RESOLUTION
# WITHDRAWAL
# FLUTTERWAVE TRANSFER
# WITHDRAWAL STATUS
#
# MINIMUM WITHDRAWAL = ₦200
# ==========================================================

from flask import (
    request,
    render_template_string,
    redirect,
    url_for,
    flash
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
# CONFIG
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

    "090267": "Kuda Bank",

    "999991": "PalmPay",

    "999992": "OPay",

}


# ==========================================================
# MONEY FORMAT
# ==========================================================

def format_money(amount):

    try:

        return f"₦{float(amount):,.2f}"

    except Exception:

        return "₦0.00"


# ==========================================================
# NORMALIZE STATUS
# ==========================================================

def normalize_status(status):

    if not status:

        return ""

    return str(
        status
    ).strip().upper()


# ==========================================================
# REFERRAL DASHBOARD
# ==========================================================

def referral_dashboard(
    referral_code
):

    promoter = get_promoter_by_referral_code(
        referral_code
    )

    if not promoter:

        return (
            "Promoter not found.",
            404
        )

    withdrawals = get_promoter_withdrawals(
        promoter["id"]
    )

    return render_template_string(

        DASHBOARD_HTML,

        promoter=promoter,

        withdrawals=withdrawals,

        referral_code=referral_code,

        format_money=format_money,

    )


# ==========================================================
# WITHDRAWAL PAGE
# ==========================================================

def withdrawal_page(
    referral_code
):

    promoter = get_promoter_by_referral_code(
        referral_code
    )

    if not promoter:

        return (
            "Promoter not found.",
            404
        )


    # ======================================================
    # POST = CREATE WITHDRAWAL
    # ======================================================

    if request.method == "POST":

        withdrawal_id = None

        try:

            # ------------------------------------------------
            # FORM DATA
            # ------------------------------------------------

            amount_raw = (
                request.form.get(
                    "amount",
                    ""
                )
                .strip()
            )

            bank_code = (
                request.form.get(
                    "bank_code",
                    ""
                )
                .strip()
            )

            account_number = (
                request.form.get(
                    "account_number",
                    ""
                )
                .strip()
            )


            # ------------------------------------------------
            # AMOUNT
            # ------------------------------------------------

            if not amount_raw:

                raise ValueError(
                    "Please enter withdrawal amount."
                )

            try:

                amount = float(
                    amount_raw
                )

            except Exception:

                raise ValueError(
                    "Invalid withdrawal amount."
                )


            if amount < MINIMUM_WITHDRAWAL:

                raise ValueError(
                    "Minimum withdrawal is ₦200."
                )


            # ------------------------------------------------
            # BANK
            # ------------------------------------------------

            if not bank_code:

                raise ValueError(
                    "Please select your bank."
                )


            bank_name = BANKS.get(
                bank_code
            )


            if not bank_name:

                raise ValueError(
                    "Invalid bank selected."
                )


            # ------------------------------------------------
            # ACCOUNT NUMBER
            # ------------------------------------------------

            if not account_number.isdigit():

                raise ValueError(
                    "Account number must contain numbers only."
                )


            if len(account_number) != 10:

                raise ValueError(
                    "Account number must be exactly 10 digits."
                )


            # ------------------------------------------------
            # VERIFY BANK ACCOUNT
            # ------------------------------------------------

            resolved = resolve_bank_account(

                account_number=account_number,

                bank_code=bank_code,

            )


            if not resolved:

                raise ValueError(

                    "Unable to verify bank account. "
                    "Please check your bank and account number."

                )


            resolved_account_name = str(

                resolved.get(
                    "account_name",
                    ""
                )

                or ""

            ).strip()


            if not resolved_account_name:

                raise ValueError(
                    "Bank account name could not be verified."
                )


            # =================================================
            # CREATE WITHDRAWAL
            #
            # DATABASE RESERVES THE BALANCE HERE
            # =================================================

            withdrawal_id = create_withdrawal(

                promoter_id=promoter["id"],

                amount=amount,

                bank_name=bank_name,

                account_name=resolved_account_name,

                account_number=account_number,

                bank_code=bank_code,

            )


            # =================================================
            # CREATE FLUTTERWAVE TRANSFER
            #
            # IMPORTANT:
            # These parameter names MUST match transfer.py
            # =================================================

            transfer_result = create_flutterwave_transfer(

                amount=amount,

                account_number=account_number,

                bank_code=bank_code,

                account_name=resolved_account_name,

                narration=(
                    "ALHIKAM Referral Commission"
                ),

            )


            # =================================================
            # FLUTTERWAVE REQUEST FAILED
            # =================================================

            if not transfer_result:

                process_transfer_result(

                    withdrawal_id=withdrawal_id,

                    transfer_status="FAILED",

                    transfer_id=None,

                    transfer_reference=None,

                    transfer_message=(
                        "Flutterwave transfer request failed."
                    ),

                )

                raise ValueError(

                    "Flutterwave could not process "
                    "the transfer. Your balance "
                    "has been restored."

                )


            # =================================================
            # TRANSFER DATA
            # =================================================

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

            transfer_status = normalize_status(

                transfer_result.get(
                    "status"
                )

            )

            transfer_message = (

                transfer_result.get(
                    "message"
                )

                or ""

            )


            # =================================================
            # SAVE TRANSFER INFORMATION
            # =================================================

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


            # =================================================
            # SUCCESSFUL
            # =================================================

            if transfer_status in {

                "SUCCESSFUL",

                "SUCCESS",

                "COMPLETED",

            }:

                process_transfer_result(

                    withdrawal_id=withdrawal_id,

                    transfer_status="SUCCESSFUL",

                    transfer_id=transfer_id,

                    transfer_reference=(
                        transfer_reference
                    ),

                    transfer_message=(
                        transfer_message
                        or
                        "Transfer completed successfully."
                    ),

                )

                flash(

                    "Withdrawal successful. "

                    + format_money(amount)

                    + " has been sent to "

                    + resolved_account_name
                    + ".",

                    "success"

                )


            # =================================================
            # FAILED
            # =================================================

            elif transfer_status in {

                "FAILED",

                "CANCELLED",

                "CANCELED",

            }:

                process_transfer_result(

                    withdrawal_id=withdrawal_id,

                    transfer_status=(
                        transfer_status
                    ),

                    transfer_id=transfer_id,

                    transfer_reference=(
                        transfer_reference
                    ),

                    transfer_message=(
                        transfer_message
                        or
                        "Flutterwave transfer failed."
                    ),

                )

                raise ValueError(

                    "Transfer failed. "
                    "Your balance has been restored."

                )


            # =================================================
            # NEW / PENDING / PROCESSING
            # =================================================

            else:

                process_transfer_result(

                    withdrawal_id=withdrawal_id,

                    transfer_status=(
                        transfer_status
                        or "NEW"
                    ),

                    transfer_id=transfer_id,

                    transfer_reference=(
                        transfer_reference
                    ),

                    transfer_message=(
                        transfer_message
                        or
                        "Transfer is being processed."
                    ),

                )

                flash(

                    "Withdrawal request received. "
                    "Your payment is currently processing.",

                    "info"

                )


            return redirect(

                url_for(

                    "withdrawal_page",

                    referral_code=referral_code

                )

            )


        except Exception as e:

            # ------------------------------------------------
            # IMPORTANT:
            #
            # If create_withdrawal() succeeded and something
            # failed afterwards, refund the reserved balance.
            #
            # But ONLY if withdrawal still exists and is not
            # already finalized.
            # ------------------------------------------------

            if withdrawal_id:

                try:

                    current = get_withdrawal_by_id(
                        withdrawal_id
                    )

                    if current:

                        current_status = str(

                            current["status"]

                            or ""

                        ).lower().strip()


                        if current_status == "pending":

                            process_transfer_result(

                                withdrawal_id=withdrawal_id,

                                transfer_status="FAILED",

                                transfer_id=(
                                    current["transfer_id"]
                                ),

                                transfer_reference=(
                                    current[
                                        "transfer_reference"
                                    ]
                                ),

                                transfer_message=str(e),

                            )

                except Exception as refund_error:

                    print(
                        "WITHDRAWAL REFUND ERROR:",
                        repr(refund_error)
                    )


            flash(
                str(e),
                "error"
            )


            return redirect(

                url_for(

                    "withdrawal_page",

                    referral_code=referral_code

                )

            )


    # ======================================================
    # GET
    # ======================================================

    withdrawals = get_promoter_withdrawals(

        promoter["id"]

    )


    return render_template_string(

        WITHDRAWAL_HTML,

        promoter=promoter,

        withdrawals=withdrawals,

        referral_code=referral_code,

        banks=BANKS,

        minimum_withdrawal=MINIMUM_WITHDRAWAL,

        format_money=format_money,

    )


# ==========================================================
# REFRESH WITHDRAWAL STATUS
# ==========================================================

def refresh_withdrawal_status(
    withdrawal_id
):

    withdrawal = get_withdrawal_by_id(
        withdrawal_id
    )


    if not withdrawal:

        return {

            "success": False,

            "message":
                "Withdrawal not found."

        }


    # ------------------------------------------------------
    # ONLY PROCESSING WITHDRAWALS
    # ------------------------------------------------------

    current_status = str(

        withdrawal["status"]

        or ""

    ).lower().strip()


    if current_status in {

        "successful",

        "failed",

        "cancelled",

    }:

        return {

            "success": True,

            "status":
                current_status,

            "withdrawal":
                withdrawal,

        }


    # ------------------------------------------------------
    # TRANSFER ID
    # ------------------------------------------------------

    transfer_id = (
        withdrawal["transfer_id"]
    )


    if not transfer_id:

        return {

            "success": False,

            "message":
                "Flutterwave transfer ID not found."

        }


    # ======================================================
    # GET CURRENT STATUS FROM FLUTTERWAVE
    # ======================================================

    result = get_flutterwave_transfer_status(

        transfer_id

    )


    if not result:

        return {

            "success": False,

            "message":
                "Unable to retrieve Flutterwave transfer status."

        }


    transfer_status = normalize_status(

        result.get(
            "status"
        )

    )


    transfer_reference = (

        result.get(
            "reference"
        )

        or withdrawal["transfer_reference"]

    )


    transfer_message = (

        result.get(
            "message"
        )

        or ""

    )


    # ======================================================
    # SUCCESSFUL
    # ======================================================

    if transfer_status in {

        "SUCCESSFUL",

        "SUCCESS",

        "COMPLETED",

    }:

        process_transfer_result(

            withdrawal_id=withdrawal_id,

            transfer_status="SUCCESSFUL",

            transfer_id=transfer_id,

            transfer_reference=(
                transfer_reference
            ),

            transfer_message=(
                transfer_message
                or
                "Transfer completed successfully."
            ),

        )


    # ======================================================
    # FAILED
    # ======================================================

    elif transfer_status in {

        "FAILED",

        "CANCELLED",

        "CANCELED",

    }:

        process_transfer_result(

            withdrawal_id=withdrawal_id,

            transfer_status=(
                transfer_status
            ),

            transfer_id=transfer_id,

            transfer_reference=(
                transfer_reference
            ),

            transfer_message=(
                transfer_message
                or
                "Transfer failed."
            ),

        )


    # ======================================================
    # STILL PROCESSING
    # ======================================================

    else:

        process_transfer_result(

            withdrawal_id=withdrawal_id,

            transfer_status=(
                transfer_status
                or "NEW"
            ),

            transfer_id=transfer_id,

            transfer_reference=(
                transfer_reference
            ),

            transfer_message=(
                transfer_message
                or
                "Transfer is still processing."
            ),

        )


    updated = get_withdrawal_by_id(
        withdrawal_id
    )


    return {

        "success": True,

        "status":
            updated["status"],

        "flutterwave_status":
            transfer_status,

        "withdrawal":
            updated,

    }


# ==========================================================
# WITHDRAWAL STATUS
# ==========================================================

def withdrawal_status(
    withdrawal_id
):

    withdrawal = get_withdrawal_by_id(
        withdrawal_id
    )


    if not withdrawal:

        return (
            "Withdrawal not found.",
            404
        )


    # ------------------------------------------------------
    # AUTO REFRESH PROCESSING TRANSFER
    # ------------------------------------------------------

    if (

        str(
            withdrawal["status"]
            or ""
        ).lower().strip()

        == "processing"

        and

        withdrawal["transfer_id"]

    ):

        refresh_withdrawal_status(
            withdrawal_id
        )

        withdrawal = get_withdrawal_by_id(
            withdrawal_id
        )


    return render_template_string(

        STATUS_HTML,

        withdrawal=withdrawal,

        format_money=format_money,

    )


# ==========================================================
# DASHBOARD HTML
# ==========================================================

DASHBOARD_HTML = """

<!DOCTYPE html>

<html>

<head>

<meta name="viewport"
      content="width=device-width, initial-scale=1">

<title>Alhikam Referral Dashboard</title>

<style>

body {

    font-family: Arial, sans-serif;

    background: #f4f6f8;

    margin: 0;

    padding: 20px;

}

.container {

    max-width: 700px;

    margin: auto;

}

.card {

    background: white;

    padding: 20px;

    margin-bottom: 15px;

    border-radius: 14px;

    box-shadow:
        0 2px 10px rgba(0,0,0,0.06);

}

.balance {

    font-size: 30px;

    font-weight: bold;

}

.button {

    display: inline-block;

    padding: 12px 18px;

    background: #111;

    color: white;

    text-decoration: none;

    border-radius: 8px;

}

.row {

    display: flex;

    justify-content: space-between;

    padding: 10px 0;

    border-bottom: 1px solid #eee;

}

.small {

    color: #666;

    font-size: 14px;

}

</style>

</head>

<body>

<div class="container">

<div class="card">

<h2>
Alhikam Learning Center
</h2>

<p>
Referral Dashboard
</p>

<p>
Available Balance
</p>

<div class="balance">

{{ format_money(
    promoter["available_balance"]
    or 0
) }}

</div>

<br>

<a
    class="button"
    href="{{ url_for(
        'withdrawal_page',
        referral_code=referral_code
    ) }}"
>
Withdraw
</a>

</div>


<div class="card">

<div class="row">

<span>Total Sales</span>

<strong>
{{ promoter["total_sales"] or 0 }}
</strong>

</div>


<div class="row">

<span>Total Earned</span>

<strong>

{{ format_money(
    promoter["total_earned"]
    or 0
) }}

</strong>

</div>


<div class="row">

<span>Withdrawn</span>

<strong>

{{ format_money(
    promoter["withdrawn_amount"]
    or 0
) }}

</strong>

</div>

</div>


<div class="card">

<h3>
Withdrawal History
</h3>

{% if withdrawals %}

{% for withdrawal in withdrawals %}

<div
style="
padding:12px 0;
border-bottom:1px solid #eee;
"
>

<strong>

{{ format_money(
    withdrawal["amount"]
    or 0
) }}

</strong>

<br>

<span>

{{ withdrawal["bank_name"] }}

</span>

<br>

<span class="small">

Account:
{{ withdrawal["account_number"] }}

</span>

<br>

<span class="small">

Status:
{{ withdrawal["status"] }}

</span>

<br>

{% if withdrawal["id"] %}

<a
href="{{ url_for(
    'withdrawal_status',
    withdrawal_id=withdrawal['id']
) }}"
>
View Status
</a>

{% endif %}

</div>

{% endfor %}

{% else %}

<p class="small">

No withdrawal history yet.

</p>

{% endif %}

</div>

</div>

</body>

</html>

"""


# ==========================================================
# WITHDRAWAL HTML
# ==========================================================

WITHDRAWAL_HTML = """

<!DOCTYPE html>

<html>

<head>

<meta name="viewport"
      content="width=device-width, initial-scale=1">

<title>Withdraw Referral Earnings</title>

<style>

body {

    font-family: Arial, sans-serif;

    background: #f4f6f8;

    margin: 0;

    padding: 20px;

}

.container {

    max-width: 600px;

    margin: auto;

}

.card {

    background: white;

    padding: 20px;

    margin-bottom: 15px;

    border-radius: 14px;

    box-shadow:
        0 2px 10px rgba(0,0,0,0.06);

}

.balance {

    font-size: 28px;

    font-weight: bold;

}

label {

    display: block;

    margin-top: 15px;

    margin-bottom: 6px;

    font-weight: bold;

}

input,
select {

    width: 100%;

    box-sizing: border-box;

    padding: 13px;

    border: 1px solid #ddd;

    border-radius: 8px;

    font-size: 16px;

}

button {

    width: 100%;

    padding: 14px;

    margin-top: 20px;

    border: none;

    border-radius: 8px;

    font-size: 17px;

    font-weight: bold;

    cursor: pointer;

    background: #111;

    color: white;

}

.alert {

    padding: 12px;

    border-radius: 8px;

    margin-bottom: 10px;

}

.error {

    background: #ffe5e5;

    color: #a00000;

}

.success {

    background: #e5ffe9;

    color: #08752b;

}

.info {

    background: #e5f2ff;

    color: #07558c;

}

.small {

    color: #666;

    font-size: 14px;

}

.history {

    padding: 12px 0;

    border-bottom: 1px solid #eee;

}

</style>

</head>

<body>

<div class="container">


<div class="card">

<h2>
Withdraw Referral Earnings
</h2>

<p class="small">

Minimum withdrawal:
<strong>₦200</strong>

</p>

<p>
Available Balance
</p>

<div class="balance">

{{ format_money(
    promoter["available_balance"]
    or 0
) }}

</div>

</div>


{% with messages =
    get_flashed_messages(
        with_categories=true
    )
%}

{% if messages %}

{% for category, message in messages %}

<div class="alert {{ category }}">

{{ message }}

</div>

{% endfor %}

{% endif %}

{% endwith %}


<div class="card">

<form method="POST">


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

maxlength="10"

minlength="10"

inputmode="numeric"

placeholder="10 digit account number"

required

>


<p class="small">

The account name will be verified
automatically with Flutterwave.

</p>


<button type="submit">

Withdraw Money

</button>

</form>

</div>


<div class="card">

<h3>
Withdrawal History
</h3>


{% if withdrawals %}

{% for withdrawal in withdrawals %}

<div class="history">

<strong>

{{ format_money(
    withdrawal["amount"]
    or 0
) }}

</strong>

<br>

<span>

{{ withdrawal["bank_name"] }}

</span>

<br>

<span class="small">

{{ withdrawal["account_name"] }}

</span>

<br>

<span class="small">

Account:
{{ withdrawal["account_number"] }}

</span>

<br>

<span class="small">

Status:
<strong>
{{ withdrawal["status"] }}
</strong>

</span>

{% if withdrawal["id"] %}

<br>

<a
href="{{ url_for(
    'withdrawal_status',
    withdrawal_id=withdrawal['id']
) }}"
>

Check Status

</a>

{% endif %}

</div>

{% endfor %}

{% else %}

<p class="small">

No withdrawal history yet.

</p>

{% endif %}

</div>


</div>

</body>

</html>

"""


# ==========================================================
# STATUS HTML
# ==========================================================

STATUS_HTML = """

<!DOCTYPE html>

<html>

<head>

<meta name="viewport"
      content="width=device-width, initial-scale=1">

<title>Withdrawal Status</title>

<style>

body {

    font-family: Arial, sans-serif;

    background: #f4f6f8;

    padding: 20px;

}

.card {

    max-width: 600px;

    margin: auto;

    background: white;

    padding: 20px;

    border-radius: 14px;

    box-shadow:
        0 2px 10px rgba(0,0,0,0.06);

}

.amount {

    font-size: 30px;

    font-weight: bold;

}

.status {

    padding: 10px;

    border-radius: 8px;

    background: #f1f1f1;

}

</style>

</head>

<body>

<div class="card">

<h2>
Withdrawal Status
</h2>

<p class="amount">

{{ format_money(
    withdrawal["amount"]
    or 0
) }}

</p>


<p class="status">

<strong>
Status:
</strong>

{{ withdrawal["status"] }}

</p>


<p>

<strong>
Bank:
</strong>

{{ withdrawal["bank_name"] }}

</p>


<p>

<strong>
Account:
</strong>

{{ withdrawal["account_number"] }}

</p>


<p>

<strong>
Account Name:
</strong>

{{ withdrawal["account_name"] }}

</p>


{% if withdrawal["transfer_reference"] %}

<p>

<strong>
Transfer Reference:
</strong>

{{ withdrawal["transfer_reference"] }}

</p>

{% endif %}


{% if withdrawal["transfer_id"] %}

<p>

<strong>
Transfer ID:
</strong>

{{ withdrawal["transfer_id"] }}

</p>

{% endif %}


{% if withdrawal["transfer_status"] %}

<p>

<strong>
Flutterwave Status:
</strong>

{{ withdrawal["transfer_status"] }}

</p>

{% endif %}


{% if withdrawal["transfer_message"] %}

<p>

<strong>
Message:
</strong>

{{ withdrawal["transfer_message"] }}

</p>

{% endif %}


</div>

</body>

</html>

"""