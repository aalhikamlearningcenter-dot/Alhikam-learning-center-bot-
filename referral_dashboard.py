# ==========================================================
# ALHIKAM LEARNING CENTER V2
# referral_dashboard.py
#
# REFERRAL DASHBOARD
# BANK ACCOUNT RESOLUTION
# WITHDRAWAL
# FLUTTERWAVE TRANSFER
# WITHDRAWAL STATUS
# ==========================================================

from flask import request, render_template_string

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
# BANK LIST
#
# These are common Nigerian bank codes.
# ==========================================================

BANKS = [
    ("044", "Access Bank"),
    ("023", "Citibank Nigeria"),
    ("050", "Ecobank Nigeria"),
    ("011", "First Bank of Nigeria"),
    ("214", "First City Monument Bank"),
    ("070", "Fidelity Bank"),
    ("011", "FirstBank"),
    ("058", "Guaranty Trust Bank"),
    ("030", "Heritage Bank"),
    ("301", "Jaiz Bank"),
    ("082", "Keystone Bank"),
    ("090267", "Kuda Bank"),
    ("221", "Stanbic IBTC Bank"),
    ("068", "Standard Chartered Bank"),
    ("232", "Sterling Bank"),
    ("100", "SunTrust Bank"),
    ("032", "Union Bank"),
    ("033", "United Bank for Africa"),
    ("215", "Unity Bank"),
    ("035", "Wema Bank"),
    ("057", "Zenith Bank"),
    ("999991", "PalmPay"),
    ("999992", "OPay"),
]


# ==========================================================
# DASHBOARD HTML
# ==========================================================

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<title>Alhikam Referral Dashboard</title>

<style>

body {
    margin: 0;
    font-family: Arial, sans-serif;
    background: #f5f7fb;
    color: #111827;
}

.container {
    max-width: 900px;
    margin: auto;
    padding: 20px;
}

.card {
    background: white;
    border-radius: 15px;
    padding: 20px;
    margin-bottom: 18px;
    box-shadow: 0 5px 20px rgba(0,0,0,.06);
}

h1 {
    margin-top: 0;
}

.balance {
    font-size: 32px;
    font-weight: bold;
}

.stats {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
}

.stat {
    background: #f8fafc;
    padding: 15px;
    border-radius: 12px;
}

.stat strong {
    display: block;
    font-size: 22px;
    margin-top: 5px;
}

button {
    border: 0;
    padding: 13px 18px;
    border-radius: 9px;
    background: #111827;
    color: white;
    cursor: pointer;
    font-size: 15px;
}

input,
select {
    width: 100%;
    box-sizing: border-box;
    padding: 12px;
    border: 1px solid #d1d5db;
    border-radius: 8px;
    margin-top: 6px;
    margin-bottom: 15px;
}

label {
    font-weight: bold;
    font-size: 14px;
}

table {
    width: 100%;
    border-collapse: collapse;
}

th,
td {
    text-align: left;
    padding: 10px;
    border-bottom: 1px solid #e5e7eb;
    font-size: 14px;
}

.status {
    font-weight: bold;
}

.successful {
    color: green;
}

.failed,
.cancelled {
    color: red;
}

.pending,
.processing {
    color: #b45309;
}

.link-box {
    background: #f3f4f6;
    padding: 12px;
    border-radius: 8px;
    word-break: break-all;
}

.error {
    background: #fee2e2;
    color: #991b1b;
    padding: 12px;
    border-radius: 8px;
    margin-bottom: 15px;
}

.success {
    background: #dcfce7;
    color: #166534;
    padding: 12px;
    border-radius: 8px;
    margin-bottom: 15px;
}

@media(max-width: 650px) {

    .stats {
        grid-template-columns: 1fr;
    }

    table {
        font-size: 12px;
    }

}

</style>

</head>

<body>

<div class="container">

<div class="card">

<h1>Alhikam Referral Dashboard</h1>

<p>
Welcome,
<strong>{{ promoter["full_name"] }}</strong>
</p>

<p>Referral Code:</p>

<div class="link-box">
{{ promoter["referral_code"] }}
</div>

<br>

<p>Referral Link:</p>

<div class="link-box">
{{ referral_link }}
</div>

</div>


<div class="card">

<p>Available Balance</p>

<div class="balance">
₦{{ "%.2f"|format(promoter["available_balance"] or 0) }}
</div>

</div>


<div class="stats">

<div class="stat">

Total Sales

<strong>
{{ promoter["total_sales"] or 0 }}
</strong>

</div>

<div class="stat">

Total Earned

<strong>
₦{{ "%.2f"|format(promoter["total_earned"] or 0) }}
</strong>

</div>

<div class="stat">

Withdrawn

<strong>
₦{{ "%.2f"|format(promoter["withdrawn_amount"] or 0) }}
</strong>

</div>

</div>


<div class="card">

<h2>Withdraw Earnings</h2>

<a href="/referral/withdraw?ref={{ promoter['referral_code'] }}">
<button>
Withdraw Now
</button>
</a>

</div>


<div class="card">

<h2>Withdrawal History</h2>

{% if withdrawals %}

<table>

<thead>

<tr>

<th>Amount</th>
<th>Bank</th>
<th>Status</th>
<th>Date</th>

</tr>

</thead>

<tbody>

{% for w in withdrawals %}

<tr>

<td>
₦{{ "%.2f"|format(w["amount"] or 0) }}
</td>

<td>
{{ w["bank_name"] }}
</td>

<td class="status {{ w['status'] }}">

{{ w["status"]|upper }}

{% if w["transfer_status"] %}
<br>
<small>
{{ w["transfer_status"] }}
</small>
{% endif %}

</td>

<td>
{{ w["created_at"] }}
</td>

</tr>

{% endfor %}

</tbody>

</table>

{% else %}

<p>No withdrawals yet.</p>

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

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<title>Withdraw - Alhikam</title>

<style>

body {
    margin: 0;
    font-family: Arial, sans-serif;
    background: #f5f7fb;
}

.container {
    max-width: 600px;
    margin: auto;
    padding: 20px;
}

.card {
    background: white;
    padding: 22px;
    border-radius: 15px;
    box-shadow: 0 5px 20px rgba(0,0,0,.07);
}

input,
select {
    width: 100%;
    box-sizing: border-box;
    padding: 13px;
    margin-top: 7px;
    margin-bottom: 16px;
    border: 1px solid #d1d5db;
    border-radius: 8px;
}

button {
    width: 100%;
    padding: 14px;
    background: #111827;
    color: white;
    border: 0;
    border-radius: 9px;
    font-size: 16px;
}

.message {
    padding: 12px;
    border-radius: 8px;
    margin-bottom: 15px;
}

.error {
    background: #fee2e2;
    color: #991b1b;
}

.success {
    background: #dcfce7;
    color: #166534;
}

.balance {
    font-size: 27px;
    font-weight: bold;
}

.account-name {
    background: #ecfdf5;
    color: #065f46;
    padding: 12px;
    border-radius: 8px;
    margin-bottom: 15px;
}

</style>

</head>

<body>

<div class="container">

<div class="card">

<h2>Withdraw Referral Earnings</h2>

<p>
Available Balance
</p>

<div class="balance">
₦{{ "%.2f"|format(promoter["available_balance"] or 0) }}
</div>

<p>
Minimum withdrawal: <strong>₦200</strong>
</p>

{% if message %}

<div class="message {{ message_type }}">
{{ message }}
</div>

{% endif %}


<form method="POST">

<input
    type="hidden"
    name="referral_code"
    value="{{ promoter['referral_code'] }}"
>


<label>Withdrawal Amount</label>

<input
    type="number"
    name="amount"
    min="200"
    step="0.01"
    placeholder="Enter amount"
    required
>


<label>Bank</label>

<select
    name="bank_code"
    required
>

<option value="">
Select Bank
</option>

{% for code, name in banks %}

<option value="{{ code }}">
{{ name }}
</option>

{% endfor %}

</select>


<label>Account Number</label>

<input
    type="text"
    name="account_number"
    maxlength="10"
    inputmode="numeric"
    placeholder="10-digit account number"
    required
>


<label>Account Name</label>

<input
    type="text"
    name="account_name"
    placeholder="Account name"
    required
>


<button type="submit">
Submit Withdrawal
</button>

</form>

</div>

</div>

</body>
</html>
"""


# ==========================================================
# REFERRAL DASHBOARD
# ==========================================================

def referral_dashboard_by_code(
    referral_code
):

    promoter = get_promoter_by_referral_code(
        referral_code
    )

    if not promoter:
        return (
            "Invalid referral code.",
            404
        )

    withdrawals = get_promoter_withdrawals(
        promoter["id"]
    )

    referral_link = (
        request.host_url.rstrip("/")
        + "/referral/"
        + promoter["referral_code"]
    )

    return render_template_string(

        DASHBOARD_HTML,

        promoter=promoter,

        withdrawals=withdrawals,

        referral_link=referral_link,
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

    promoter = get_promoter_by_referral_code(
        referral_code
    )

    if not promoter:

        return (
            "Invalid referral code.",
            404
        )

    message = ""
    message_type = ""

    if request.method == "POST":

        try:

            amount = float(
                request.form.get(
                    "amount",
                    0
                )
                or 0
            )

            bank_code = (
                request.form.get(
                    "bank_code",
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

            submitted_account_name = (
                request.form.get(
                    "account_name",
                    ""
                )
                or ""
            ).strip()

            # --------------------------------------------------
            # VALIDATE ACCOUNT NUMBER
            # --------------------------------------------------

            if (
                len(account_number) != 10
                or not account_number.isdigit()
            ):

                raise ValueError(
                    "Account number must contain exactly 10 digits."
                )

            # --------------------------------------------------
            # FIND BANK NAME
            # --------------------------------------------------

            bank_name = ""

            for code, name in BANKS:

                if code == bank_code:

                    bank_name = name
                    break

            if not bank_name:

                raise ValueError(
                    "Please select a valid bank."
                )

            # --------------------------------------------------
            # RESOLVE ACCOUNT
            # --------------------------------------------------

            resolved = resolve_bank_account(
                account_number=account_number,
                bank_code=bank_code
            )

            if not resolved:

                raise ValueError(
                    "Unable to verify bank account. "
                    "Please check the bank and account number."
                )

            resolved_account_name = (
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

            # --------------------------------------------------
            # USE VERIFIED ACCOUNT NAME
            # --------------------------------------------------

            account_name = resolved_account_name

            # --------------------------------------------------
            # CREATE WITHDRAWAL
            #
            # Balance is reserved here.
            # --------------------------------------------------

            withdrawal_id = create_withdrawal(

                promoter_id=promoter["id"],

                amount=amount,

                bank_name=bank_name,

                account_name=account_name,

                account_number=account_number,

                bank_code=bank_code,
            )

            # --------------------------------------------------
            # CREATE FLUTTERWAVE TRANSFER
            # --------------------------------------------------

            transfer = create_flutterwave_transfer(

                amount=amount,

                account_number=account_number,

                bank_code=bank_code,

                account_name=account_name,

                narration="ALHIKAM Referral Commission",
            )

            # --------------------------------------------------
            # FLUTTERWAVE REQUEST FAILED
            # --------------------------------------------------

            if not transfer:

                process_transfer_result(

                    withdrawal_id=withdrawal_id,

                    transfer_status="FAILED",

                    transfer_message=(
                        "Flutterwave transfer request failed."
                    )
                )

                raise ValueError(
                    "Flutterwave could not process the transfer. "
                    "Your balance has been restored."
                )

            # --------------------------------------------------
            # SAVE TRANSFER DETAILS
            # --------------------------------------------------

            update_withdrawal_transfer(

                withdrawal_id=withdrawal_id,

                transfer_reference=(
                    transfer.get(
                        "reference"
                    )
                ),

                transfer_id=(
                    transfer.get(
                        "transfer_id"
                    )
                ),

                transfer_status=(
                    transfer.get(
                        "status"
                    )
                ),

                transfer_message=(
                    transfer.get(
                        "message"
                    )
                ),
            )

            # --------------------------------------------------
            # PROCESS TRANSFER STATUS
            # --------------------------------------------------

            process_transfer_result(

                withdrawal_id=withdrawal_id,

                transfer_status=(
                    transfer.get(
                        "status",
                        "NEW"
                    )
                ),

                transfer_id=(
                    transfer.get(
                        "transfer_id"
                    )
                ),

                transfer_reference=(
                    transfer.get(
                        "reference"
                    )
                ),

                transfer_message=(
                    transfer.get(
                        "message"
                    )
                ),
            )

            # --------------------------------------------------
            # GET FINAL WITHDRAWAL
            # --------------------------------------------------

            final_withdrawal = get_withdrawal_by_id(
                withdrawal_id
            )

            final_status = str(
                final_withdrawal["status"]
                if final_withdrawal
                else "processing"
            ).lower()

            # --------------------------------------------------
            # SUCCESS MESSAGE
            # --------------------------------------------------

            if final_status == "successful":

                message = (
                    f"Withdrawal of ₦{amount:,.2f} "
                    "was successful."
                )

                message_type = "success"

            elif final_status in {
                "failed",
                "cancelled"
            }:

                message = (
                    "Withdrawal failed. "
                    "Your balance has been restored."
                )

                message_type = "error"

            else:

                message = (
                    f"Withdrawal of ₦{amount:,.2f} "
                    "has been submitted and is processing."
                )

                message_type = "success"

            promoter = get_promoter_by_referral_code(
                referral_code
            )

        except Exception as e:

            message = str(e)

            message_type = "error"

            promoter = get_promoter_by_referral_code(
                referral_code
            )

    return render_template_string(

        WITHDRAWAL_HTML,

        promoter=promoter,

        banks=BANKS,

        message=message,

        message_type=message_type,
    )


# ==========================================================
# CHECK TRANSFER STATUS
#
# This function can be called by an admin route,
# webhook, scheduled job, or background worker.
# ==========================================================

def refresh_withdrawal_status(
    withdrawal_id
):

    withdrawal = get_withdrawal_by_id(
        withdrawal_id
    )

    if not withdrawal:

        raise ValueError(
            "Withdrawal not found."
        )

    transfer_id = (
        withdrawal["transfer_id"]
    )

    if not transfer_id:

        raise ValueError(
            "Transfer ID is missing."
        )

    result = get_flutterwave_transfer_status(
        transfer_id
    )

    if not result:

        raise ValueError(
            "Unable to get Flutterwave transfer status."
        )

    process_transfer_result(

        withdrawal_id=withdrawal_id,

        transfer_status=(
            result.get(
                "status",
                ""
            )
        ),

        transfer_id=(
            result.get(
                "transfer_id"
            )
        ),

        transfer_reference=(
            result.get(
                "reference"
            )
        ),

        transfer_message=(
            result.get(
                "message"
            )
        ),
    )

    return get_withdrawal_by_id(
        withdrawal_id
    )