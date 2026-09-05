# ==========================================================
# ALHIKAM LEARNING CENTER V2
# referral_dashboard.py
#
# REFERRAL DASHBOARD
# WITHDRAWAL
# FLUTTERWAVE TRANSFER
# TRANSFER STATUS
# MINIMUM WITHDRAWAL = ₦200
# ==========================================================

import logging

from flask import (
    request,
    redirect,
    render_template_string,
    flash,
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
# LOGGER
# ==========================================================

logger = logging.getLogger("ALHIKAM")


# ==========================================================
# SETTINGS
# ==========================================================

MINIMUM_WITHDRAWAL = 200


# ==========================================================
# BANK LIST
# ==========================================================

BANKS = {
    "044": "Access Bank",
    "023": "Citibank Nigeria",
    "050": "Ecobank Nigeria",
    "011": "First Bank of Nigeria",
    "214": "FCMB",
    "070": "Fidelity Bank",
    "058": "GTBank",
    "030": "Heritage Bank",
    "301": "Jaiz Bank",
    "082": "Keystone Bank",
    "221": "Stanbic IBTC Bank",
    "068": "Standard Chartered Bank",
    "232": "Sterling Bank",
    "100": "SunTrust Bank",
    "032": "Union Bank",
    "033": "UBA",
    "215": "Unity Bank",
    "035": "Wema Bank",
    "057": "Zenith Bank",

    # Fintech / other supported codes
    "090267": "Kuda Bank",
    "999991": "PalmPay",
    "999992": "OPay",
}


# ==========================================================
# HELPERS
# ==========================================================

def money(value):
    try:
        return f"₦{float(value):,.2f}"
    except Exception:
        return "₦0.00"


def get_referral_code():
    """
    Get referral code from GET or POST.
    """

    return (
        request.args.get("ref", "")
        or request.args.get("referral_code", "")
        or request.form.get("referral_code", "")
        or ""
    ).strip()


def get_promoter(referral_code):
    if not referral_code:
        return None

    try:
        return get_promoter_by_referral_code(
            referral_code
        )
    except Exception:
        logger.exception(
            "Could not load promoter: %s",
            referral_code
        )
        return None


# ==========================================================
# REFERRAL DASHBOARD
# ==========================================================

def referral_dashboard_by_code(referral_code):
    """
    Main referral dashboard.

    IMPORTANT:
    This function is imported directly by main.py.
    """

    referral_code = (
        referral_code or ""
    ).strip()

    if not referral_code:
        return (
            "Referral code is required.",
            400
        )

    promoter = get_promoter(
        referral_code
    )

    if not promoter:
        return (
            "Invalid referral code.",
            404
        )

    if str(
        promoter["status"]
    ).lower() != "active":

        return (
            "This referral account is not active.",
            403
        )

    # ------------------------------------------------------
    # PROMOTER DATA
    # ------------------------------------------------------

    full_name = (
        promoter["full_name"]
        or "Promoter"
    )

    code = (
        promoter["referral_code"]
        or referral_code
    )

    available_balance = float(
        promoter["available_balance"]
        or 0
    )

    withdrawn_amount = float(
        promoter["withdrawn_amount"]
        or 0
    )

    total_earned = (
        available_balance
        + withdrawn_amount
    )

    # ------------------------------------------------------
    # GET WITHDRAWALS
    # ------------------------------------------------------

    try:
        withdrawals = get_promoter_withdrawals(
            promoter["id"]
        )
    except Exception:
        logger.exception(
            "Could not load promoter withdrawals."
        )
        withdrawals = []

    # ------------------------------------------------------
    # REFERRAL LINK
    # ------------------------------------------------------

    referral_link = (
        request.host_url.rstrip("/")
        + "/referral/"
        + str(code)
    )

    # ------------------------------------------------------
    # DASHBOARD HTML
    # ------------------------------------------------------

    html = """
<!DOCTYPE html>
<html lang="en">
<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<title>Alhikam Referral Dashboard</title>

<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    padding: 20px;
    font-family: Arial, sans-serif;
    background: #f4f6f8;
    color: #222;
}

.container {
    max-width: 900px;
    margin: auto;
}

.header {
    background: #111827;
    color: white;
    padding: 24px;
    border-radius: 18px;
    margin-bottom: 20px;
}

.header h1 {
    margin: 0 0 8px 0;
    font-size: 25px;
}

.header p {
    margin: 0;
    opacity: 0.85;
}

.cards {
    display: grid;
    grid-template-columns:
        repeat(auto-fit, minmax(200px, 1fr));
    gap: 15px;
    margin-bottom: 20px;
}

.card {
    background: white;
    border-radius: 16px;
    padding: 20px;
    box-shadow:
        0 3px 12px rgba(0,0,0,0.06);
}

.card-title {
    color: #6b7280;
    font-size: 14px;
    margin-bottom: 8px;
}

.card-value {
    font-size: 25px;
    font-weight: bold;
}

.section {
    background: white;
    padding: 20px;
    border-radius: 16px;
    margin-bottom: 20px;
    box-shadow:
        0 3px 12px rgba(0,0,0,0.06);
}

.section h2 {
    margin-top: 0;
}

.referral-box {
    background: #f3f4f6;
    padding: 15px;
    border-radius: 12px;
    word-break: break-all;
}

.code {
    font-weight: bold;
    font-size: 20px;
}

.buttons {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    margin-top: 15px;
}

.btn {
    display: inline-block;
    text-decoration: none;
    border: none;
    padding: 13px 18px;
    border-radius: 10px;
    cursor: pointer;
    font-weight: bold;
}

.withdraw {
    background: #111827;
    color: white;
}

.refresh {
    background: #e5e7eb;
    color: #111827;
}

table {
    width: 100%;
    border-collapse: collapse;
}

th,
td {
    padding: 12px 8px;
    border-bottom: 1px solid #eee;
    text-align: left;
}

.status {
    font-weight: bold;
    text-transform: capitalize;
}

.successful {
    color: #15803d;
}

.processing {
    color: #b45309;
}

.pending {
    color: #b45309;
}

.failed,
.cancelled,
.canceled {
    color: #dc2626;
}

@media(max-width:600px) {

    body {
        padding: 10px;
    }

    .card-value {
        font-size: 21px;
    }

    th,
    td {
        font-size: 12px;
    }

}

</style>

</head>

<body>

<div class="container">

    <div class="header">

        <h1>
            Alhikam Learning Center
        </h1>

        <p>
            Referral Promoter Dashboard
        </p>

        <p style="margin-top:8px;">
            Welcome, {{ full_name }}
        </p>

    </div>


    <!-- ================================================== -->
    <!-- BALANCE CARDS -->
    <!-- ================================================== -->

    <div class="cards">

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
                Total Earned
            </div>

            <div class="card-value">
                {{ total_earned }}
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


    <!-- ================================================== -->
    <!-- REFERRAL LINK -->
    <!-- ================================================== -->

    <div class="section">

        <h2>
            Your Referral Link
        </h2>

        <div class="referral-box">

            <div class="card-title">
                Referral Code
            </div>

            <div class="code">
                {{ code }}
            </div>

            <br>

            <div class="card-title">
                Referral Link
            </div>

            <div>
                {{ referral_link }}
            </div>

        </div>

        <div class="buttons">

            <a
                class="btn withdraw"
                href="/referral/withdraw?ref={{ code }}"
            >
                Withdraw Commission
            </a>

            <a
                class="btn refresh"
                href="/referral/dashboard?ref={{ code }}"
            >
                Refresh
            </a>

        </div>

    </div>


    <!-- ================================================== -->
    <!-- WITHDRAWAL HISTORY -->
    <!-- ================================================== -->

    <div class="section">

        <h2>
            Withdrawal History
        </h2>

        {% if withdrawals %}

        <div style="overflow-x:auto;">

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

            {% for withdrawal in withdrawals %}

                <tr>

                    <td>
                        ₦{{ "{:,.2f}".format(
                            withdrawal["amount"] or 0
                        ) }}
                    </td>

                    <td>
                        {{ withdrawal["bank_name"] or "-" }}
                    </td>

                    <td>

                        {% set status =
                            (withdrawal["status"] or "pending")
                            |lower
                        %}

                        <span class="status {{ status }}">
                            {{ status }}
                        </span>

                    </td>

                    <td>
                        {{ withdrawal["created_at"] or "-" }}
                    </td>

                </tr>

            {% endfor %}

            </tbody>

        </table>

        </div>

        {% else %}

        <p>
            No withdrawals yet.
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
        code=code,
        referral_link=referral_link,
        available_balance=money(
            available_balance
        ),
        total_earned=money(
            total_earned
        ),
        withdrawn_amount=money(
            withdrawn_amount
        ),
        withdrawals=withdrawals,
    )


# ==========================================================
# WITHDRAWAL PAGE
# ==========================================================

def withdrawal_page(referral_code=None):
    """
    Handles both GET and POST withdrawal requests.

    main.py calls:
        withdrawal_page(referral_code=referral_code)
    """

    referral_code = (
        referral_code
        or get_referral_code()
    ).strip()

    if not referral_code:

        return (
            "Referral code is required.",
            400
        )

    # ------------------------------------------------------
    # FIND PROMOTER
    # ------------------------------------------------------

    promoter = get_promoter(
        referral_code
    )

    if not promoter:

        return (
            "Invalid referral code.",
            404
        )

    if str(
        promoter["status"]
    ).lower() != "active":

        return (
            "This referral account is not active.",
            403
        )

    # ------------------------------------------------------
    # POST = PROCESS WITHDRAWAL
    # ------------------------------------------------------

    if request.method == "POST":

        amount_raw = (
            request.form.get(
                "amount",
                ""
            )
            or ""
        ).strip()

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

        # --------------------------------------------------
        # AMOUNT
        # --------------------------------------------------

        try:

            amount = float(
                amount_raw
            )

        except Exception:

            amount = 0

        if amount < MINIMUM_WITHDRAWAL:

            return render_withdrawal_page(
                promoter=promoter,
                referral_code=referral_code,
                error=(
                    "Minimum withdrawal is "
                    "₦200."
                ),
            )

        # --------------------------------------------------
        # BANK
        # --------------------------------------------------

        if not bank_code:

            return render_withdrawal_page(
                promoter=promoter,
                referral_code=referral_code,
                error="Please select your bank.",
            )

        bank_name = BANKS.get(
            bank_code
        )

        if not bank_name:

            return render_withdrawal_page(
                promoter=promoter,
                referral_code=referral_code,
                error="Invalid bank selected.",
            )

        # --------------------------------------------------
        # ACCOUNT NUMBER
        # --------------------------------------------------

        account_number = (
            account_number
            .replace(" ", "")
            .replace("-", "")
        )

        if (
            len(account_number) != 10
            or not account_number.isdigit()
        ):

            return render_withdrawal_page(
                promoter=promoter,
                referral_code=referral_code,
                error=(
                    "Account number must "
                    "contain exactly 10 digits."
                ),
            )

        # --------------------------------------------------
        # CHECK AVAILABLE BALANCE
        # --------------------------------------------------

        try:

            available_balance = float(
                promoter["available_balance"]
                or 0
            )

        except Exception:

            available_balance = 0

        if amount > available_balance:

            return render_withdrawal_page(
                promoter=promoter,
                referral_code=referral_code,
                error=(
                    "Insufficient available balance. "
                    f"Your balance is "
                    f"{money(available_balance)}."
                ),
            )

        # --------------------------------------------------
        # RESOLVE BANK ACCOUNT
        # --------------------------------------------------

        try:

            resolved = resolve_bank_account(
                account_number=account_number,
                bank_code=bank_code,
            )

        except Exception:

            logger.exception(
                "Bank account resolve error."
            )

            return render_withdrawal_page(
                promoter=promoter,
                referral_code=referral_code,
                error=(
                    "Unable to verify bank account "
                    "right now. Please try again."
                ),
            )

        if not resolved:

            return render_withdrawal_page(
                promoter=promoter,
                referral_code=referral_code,
                error=(
                    "Bank account could not be verified."
                ),
            )

        resolved_account_name = (
            resolved.get(
                "account_name",
                ""
            )
            or ""
        ).strip()

        if not resolved_account_name:

            return render_withdrawal_page(
                promoter=promoter,
                referral_code=referral_code,
                error=(
                    "Could not retrieve account name."
                ),
            )

        # --------------------------------------------------
        # CREATE WITHDRAWAL
        #
        # This reserves/deducts the amount from
        # available_balance.
        # --------------------------------------------------

        withdrawal_id = None

        try:

            withdrawal_id = create_withdrawal(

                promoter_id=promoter["id"],

                amount=amount,

                bank_name=bank_name,

                account_name=resolved_account_name,

                account_number=account_number,

                bank_code=bank_code,

            )

        except ValueError as e:

            logger.warning(
                "Withdrawal validation error: %s",
                e
            )

            return render_withdrawal_page(
                promoter=promoter,
                referral_code=referral_code,
                error=str(e),
            )

        except Exception:

            logger.exception(
                "Could not create withdrawal."
            )

            return render_withdrawal_page(
                promoter=promoter,
                referral_code=referral_code,
                error=(
                    "Could not create withdrawal. "
                    "Please try again."
                ),
            )

        # --------------------------------------------------
        # CREATE FLUTTERWAVE TRANSFER
        # --------------------------------------------------

        try:

            transfer = create_flutterwave_transfer(

                amount=amount,

                account_number=account_number,

                bank_code=bank_code,

                account_name=resolved_account_name,

                narration=(
                    "ALHIKAM Referral Commission"
                ),

            )

        except Exception as e:

            logger.exception(
                "Flutterwave transfer creation error."
            )

            # Refund reserved balance
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

            return render_withdrawal_page(
                promoter=promoter,
                referral_code=referral_code,
                error=(
                    "Transfer could not be started. "
                    "Your balance has been returned."
                ),
            )

        # --------------------------------------------------
        # TRANSFER RESPONSE CHECK
        # --------------------------------------------------

        if not transfer:

            try:

                process_transfer_result(

                    withdrawal_id=withdrawal_id,

                    transfer_status="FAILED",

                    transfer_message=(
                        "Flutterwave returned no response."
                    ),

                )

            except Exception:

                logger.exception(
                    "Could not refund empty transfer."
                )

            return render_withdrawal_page(
                promoter=promoter,
                referral_code=referral_code,
                error=(
                    "Transfer could not be started. "
                    "Your balance has been returned."
                ),
            )

        if not transfer.get("success"):

            message = (
                transfer.get(
                    "message",
                    ""
                )
                or "Transfer failed."
            )

            try:

                process_transfer_result(

                    withdrawal_id=withdrawal_id,

                    transfer_status="FAILED",

                    transfer_id=transfer.get(
                        "transfer_id"
                    ),

                    transfer_reference=transfer.get(
                        "reference"
                    ),

                    transfer_message=message,

                )

            except Exception:

                logger.exception(
                    "Could not refund unsuccessful transfer."
                )

            return render_withdrawal_page(
                promoter=promoter,
                referral_code=referral_code,
                error=(
                    f"{message} "
                    "Your balance has been returned."
                ),
            )

        # --------------------------------------------------
        # SAVE TRANSFER INFORMATION
        # --------------------------------------------------

        transfer_id = (
            transfer.get(
                "transfer_id"
            )
        )

        transfer_reference = (
            transfer.get(
                "reference"
            )
            or ""
        )

        transfer_status = (
            transfer.get(
                "status",
                "NEW"
            )
            or "NEW"
        ).upper().strip()

        transfer_message = (
            transfer.get(
                "message",
                ""
            )
            or ""
        )

        try:

            update_withdrawal_transfer(

                withdrawal_id=withdrawal_id,

                transfer_reference=(
                    transfer_reference
                ),

                transfer_id=transfer_id,

                transfer_status=(
                    transfer_status
                ),

                transfer_message=(
                    transfer_message
                ),

            )

        except Exception:

            logger.exception(
                "Could not save transfer information."
            )

        # --------------------------------------------------
        # PROCESS TRANSFER RESULT
        # --------------------------------------------------

        try:

            process_transfer_result(

                withdrawal_id=withdrawal_id,

                transfer_status=transfer_status,

                transfer_id=transfer_id,

                transfer_reference=(
                    transfer_reference
                ),

                transfer_message=(
                    transfer_message
                ),

            )

        except Exception:

            logger.exception(
                "Could not process transfer result."
            )

            # Do NOT automatically refund here because
            # Flutterwave transfer may already exist.
            # It must be checked before any refund.

        # --------------------------------------------------
        # FINAL MESSAGE
        # --------------------------------------------------

        normalized_status = (
            transfer_status
            .upper()
            .strip()
        )

        if normalized_status in (
            "SUCCESSFUL",
            "SUCCESS",
            "COMPLETED",
        ):

            return redirect(
                "/referral/withdraw/status/"
                + str(withdrawal_id)
                + "?ref="
                + referral_code
            )

        if normalized_status in (
            "FAILED",
            "CANCELLED",
            "CANCELED",
        ):

            return redirect(
                "/referral/withdraw/status/"
                + str(withdrawal_id)
                + "?ref="
                + referral_code
            )

        # NEW / PENDING / PROCESSING
        return redirect(
            "/referral/withdraw/status/"
            + str(withdrawal_id)
            + "?ref="
            + referral_code
        )

    # ------------------------------------------------------
    # GET
    # ------------------------------------------------------

    return render_withdrawal_page(
        promoter=promoter,
        referral_code=referral_code,
    )


# ==========================================================
# WITHDRAWAL HTML
# ==========================================================

def render_withdrawal_page(
    promoter,
    referral_code,
    error=None,
):

    try:

        available_balance = float(
            promoter["available_balance"]
            or 0
        )

    except Exception:

        available_balance = 0

    html = """
<!DOCTYPE html>
<html lang="en">

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<title>Withdraw - Alhikam Learning Center</title>

<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    padding: 20px;
    font-family: Arial, sans-serif;
    background: #f4f6f8;
}

.container {
    max-width: 600px;
    margin: auto;
}

.card {
    background: white;
    padding: 24px;
    border-radius: 18px;
    box-shadow:
        0 4px 15px rgba(0,0,0,0.08);
}

h1 {
    margin-top: 0;
}

.balance {
    background: #111827;
    color: white;
    padding: 18px;
    border-radius: 14px;
    margin-bottom: 20px;
}

.balance-label {
    opacity: .8;
    font-size: 14px;
}

.balance-value {
    font-size: 28px;
    font-weight: bold;
    margin-top: 5px;
}

label {
    display: block;
    margin-top: 15px;
    margin-bottom: 7px;
    font-weight: bold;
}

input,
select {
    width: 100%;
    padding: 14px;
    border: 1px solid #d1d5db;
    border-radius: 10px;
    font-size: 16px;
    background: white;
}

button {
    width: 100%;
    margin-top: 20px;
    padding: 15px;
    border: none;
    border-radius: 10px;
    background: #111827;
    color: white;
    font-size: 16px;
    font-weight: bold;
    cursor: pointer;
}

.error {
    background: #fee2e2;
    color: #991b1b;
    padding: 14px;
    border-radius: 10px;
    margin-bottom: 15px;
}

.info {
    background: #f3f4f6;
    padding: 14px;
    border-radius: 10px;
    margin-top: 15px;
    font-size: 14px;
}

.back {
    display: inline-block;
    margin-top: 15px;
    text-decoration: none;
    color: #111827;
    font-weight: bold;
}

</style>

</head>

<body>

<div class="container">

<div class="card">

<h1>
    Withdraw Commission
</h1>

<p>
    Alhikam Learning Center
</p>

<div class="balance">

    <div class="balance-label">
        Available Balance
    </div>

    <div class="balance-value">
        ₦{{ "{:,.2f}".format(
            available_balance
        ) }}
    </div>

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
        placeholder="Minimum ₦200"
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
            Select your bank
        </option>

        {% for bank_code, bank_name in banks.items() %}

        <option value="{{ bank_code }}">
            {{ bank_name }}
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
        placeholder="10-digit account number"
        required
    >


    <div class="info">

        <strong>Important:</strong>

        Your bank account will be verified before
        the withdrawal is processed.

        <br><br>

        Minimum withdrawal:
        <strong>₦200</strong>

    </div>


    <button type="submit">
        Withdraw Money
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

    return render_template_string(

        html,

        promoter=promoter,

        referral_code=referral_code,

        available_balance=available_balance,

        banks=BANKS,

        error=error,

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
        return None

    transfer_id = (
        withdrawal["transfer_id"]
        or ""
    )

    if not transfer_id:
        return withdrawal

    current_status = (
        withdrawal["transfer_status"]
        or withdrawal["status"]
        or ""
    ).upper().strip()

    # Already final
    if current_status in (
        "SUCCESSFUL",
        "SUCCESS",
        "COMPLETED",
        "FAILED",
        "CANCELLED",
        "CANCELED",
    ):

        return withdrawal

    # ------------------------------------------------------
    # ASK FLUTTERWAVE FOR CURRENT STATUS
    # ------------------------------------------------------

    try:

        result = get_flutterwave_transfer_status(
            transfer_id
        )

    except Exception:

        logger.exception(
            "Could not retrieve transfer status."
        )

        return withdrawal

    if not result:

        return withdrawal

    if not result.get("success"):

        return withdrawal

    status = (
        result.get(
            "status",
            ""
        )
        or ""
    ).upper().strip()

    reference = (
        result.get(
            "reference",
            ""
        )
        or withdrawal["transfer_reference"]
        or ""
    )

    message = (
        result.get(
            "message",
            ""
        )
        or ""
    )

    # ------------------------------------------------------
    # UPDATE DATABASE
    # ------------------------------------------------------

    try:

        process_transfer_result(

            withdrawal_id=withdrawal_id,

            transfer_status=status,

            transfer_id=(
                result.get(
                    "transfer_id"
                )
                or transfer_id
            ),

            transfer_reference=reference,

            transfer_message=message,

        )

    except Exception:

        logger.exception(
            "Could not update transfer result."
        )

    return get_withdrawal_by_id(
        withdrawal_id
    )


# ==========================================================
# WITHDRAWAL STATUS PAGE
# ==========================================================

def withdrawal_status_page(
    withdrawal_id,
    referral_code
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
    # AUTO REFRESH FLUTTERWAVE STATUS
    # ------------------------------------------------------

    status = (
        withdrawal["status"]
        or "pending"
    ).lower().strip()

    if status in (
        "pending",
        "processing",
    ) and withdrawal["transfer_id"]:

        withdrawal = refresh_withdrawal_status(
            withdrawal_id
        )

    status = (
        withdrawal["status"]
        or "pending"
    ).lower().strip()

    amount = float(
        withdrawal["amount"]
        or 0
    )

    bank_name = (
        withdrawal["bank_name"]
        or "-"
    )

    account_name = (
        withdrawal["account_name"]
        or "-"
    )

    account_number = (
        withdrawal["account_number"]
        or "-"
    )

    transfer_reference = (
        withdrawal["transfer_reference"]
        or "-"
    )

    transfer_status = (
        withdrawal["transfer_status"]
        or "-"
    )

    transfer_message = (
        withdrawal["transfer_message"]
        or ""
    )

    # ------------------------------------------------------
    # STATUS MESSAGE
    # ------------------------------------------------------

    if status == "successful":

        message = (
            "Your withdrawal was successful. "
            "The money has been sent to your bank account."
        )

    elif status == "failed":

        message = (
            "Your withdrawal failed. "
            "The reserved balance has been returned."
        )

    elif status in (
        "cancelled",
        "canceled",
    ):

        message = (
            "Your withdrawal was cancelled. "
            "The reserved balance has been returned."
        )

    else:

        message = (
            "Your withdrawal is being processed. "
            "Flutterwave has received the transfer request."
        )

    # ------------------------------------------------------
    # STATUS HTML
    # ------------------------------------------------------

    html = """
<!DOCTYPE html>
<html lang="en">

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<title>Withdrawal Status</title>

<style>

body {
    margin: 0;
    padding: 20px;
    font-family: Arial, sans-serif;
    background: #f4f6f8;
}

.container {
    max-width: 600px;
    margin: auto;
}

.card {
    background: white;
    padding: 25px;
    border-radius: 18px;
    box-shadow:
        0 4px 15px rgba(0,0,0,.08);
}

.status-box {
    padding: 20px;
    border-radius: 14px;
    margin-bottom: 20px;
    background: #f3f4f6;
}

.status {
    font-size: 25px;
    font-weight: bold;
    text-transform: capitalize;
}

.successful {
    color: #15803d;
}

.processing,
.pending {
    color: #b45309;
}

.failed,
.cancelled,
.canceled {
    color: #dc2626;
}

.row {
    padding: 12px 0;
    border-bottom: 1px solid #eee;
}

.label {
    color: #6b7280;
    font-size: 13px;
}

.value {
    font-weight: bold;
    margin-top: 4px;
    word-break: break-word;
}

.btn {
    display: inline-block;
    margin-top: 20px;
    padding: 13px 18px;
    background: #111827;
    color: white;
    text-decoration: none;
    border-radius: 10px;
    font-weight: bold;
}

</style>

</head>

<body>

<div class="container">

<div class="card">

<h1>
    Withdrawal Status
</h1>


<div class="status-box">

    <div class="status {{ status }}">
        {{ status }}
    </div>

    <p>
        {{ message }}
    </p>

</div>


<div class="row">

    <div class="label">
        Amount
    </div>

    <div class="value">
        ₦{{ "{:,.2f}".format(amount) }}
    </div>

</div>


<div class="row">

    <div class="label">
        Bank
    </div>

    <div class="value">
        {{ bank_name }}
    </div>

</div>


<div class="row">

    <div class="label">
        Account Name
    </div>

    <div class="value">
        {{ account_name }}
    </div>

</div>


<div class="row">

    <div class="label">
        Account Number
    </div>

    <div class="value">
        {{ account_number }}
    </div>

</div>


<div class="row">

    <div class="label">
        Transfer Status
    </div>

    <div class="value">
        {{ transfer_status }}
    </div>

</div>


<div class="row">

    <div class="label">
        Transfer Reference
    </div>

    <div class="value">
        {{ transfer_reference }}
    </div>

</div>


{% if transfer_message %}

<div class="row">

    <div class="label">
        Transfer Message
    </div>

    <div class="value">
        {{ transfer_message }}
    </div>

</div>

{% endif %}


<a
    class="btn"
    href="/referral/dashboard?ref={{ referral_code }}"
>
    Back to Dashboard
</a>


{% if status in ["pending", "processing"] %}

<a
    class="btn"
    href="/referral/withdraw/status/{{ withdrawal_id }}?ref={{ referral_code }}"
>
    Check Status Again
</a>

{% endif %}


</div>

</div>

</body>

</html>
"""

    return render_template_string(

        html,

        withdrawal_id=withdrawal_id,

        referral_code=referral_code,

        amount=amount,

        bank_name=bank_name,

        account_name=account_name,

        account_number=account_number,

        status=status,

        transfer_status=transfer_status,

        transfer_reference=transfer_reference,

        transfer_message=transfer_message,

        message=message,

    )