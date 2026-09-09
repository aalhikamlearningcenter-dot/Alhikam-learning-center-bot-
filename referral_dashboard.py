# ==========================================================
# ALHIKAM LEARNING CENTER V2
# referral_dashboard.py
#
# SECURE PROMOTER / REFERRAL DASHBOARD
# PAYMENT
# COMMISSION
# WITHDRAWAL
# FLUTTERWAVE TRANSFER
# ==========================================================

import os
import hmac
import secrets
import logging

from decimal import Decimal, InvalidOperation

from flask import (
    request,
    redirect,
    render_template_string,
    session,
    url_for,
    abort,
)

from database import (
    MINIMUM_WITHDRAWAL,
    get_promoter_by_referral_code,
    get_promoter_by_id,
    create_withdrawal,
    get_promoter_withdrawals,
    get_withdrawal_by_id,
    update_withdrawal_transfer,
    process_transfer_result,
    verify_promoter_password,
)

from transfer import (
    resolve_bank_account,
    create_flutterwave_transfer,
    get_flutterwave_transfer_status,
    get_flutterwave_transfer_status_by_reference,
    get_flutterwave_banks,
)


logger = logging.getLogger(__name__)


# ==========================================================
# CONFIG
# ==========================================================

APP_URL = os.getenv(
    "APP_URL",
    "http://127.0.0.1:5000"
).rstrip("/")


PROMOTER_SESSION_ID = (
    "alhikam_promoter_id"
)

PROMOTER_CSRF_SESSION = (
    "alhikam_promoter_csrf"
)


# ==========================================================
# SQLITE ROW HELPER
# ==========================================================

def _row_get(row, key, default=None):

    if row is None:
        return default

    try:
        return row[key]

    except (
        KeyError,
        IndexError,
        TypeError,
    ):
        return default


# ==========================================================
# ACCOUNT MASK
# ==========================================================

def _mask_account(account_number):

    account_number = str(
        account_number or ""
    )

    if len(account_number) <= 4:
        return "****"

    return (
        "*" * (len(account_number) - 4)
        + account_number[-4:]
    )


# ==========================================================
# MONEY FORMAT
# ==========================================================

def _safe_money(value):

    try:

        amount = Decimal(
            str(value or "0")
        )

        return (
            f"₦{amount:,.2f}"
        )

    except (
        InvalidOperation,
        ValueError,
        TypeError,
    ):

        return "₦0.00"


# ==========================================================
# CSRF
# ==========================================================

def _csrf_token():

    token = session.get(
        PROMOTER_CSRF_SESSION
    )

    if not token:

        token = secrets.token_urlsafe(32)

        session[
            PROMOTER_CSRF_SESSION
        ] = token

    return token


def _check_csrf():

    sent = str(
        request.form.get(
            "csrf_token",
            ""
        )
    )

    expected = session.get(
        PROMOTER_CSRF_SESSION
    )

    if (
        not sent
        or not expected
        or not hmac.compare_digest(
            sent,
            expected
        )
    ):

        abort(400)


# ==========================================================
# CURRENT PROMOTER
# ==========================================================

def _current_promoter():

    promoter_id = session.get(
        PROMOTER_SESSION_ID
    )

    if promoter_id is None:
        return None

    try:
        promoter_id = int(
            promoter_id
        )

    except (
        ValueError,
        TypeError,
    ):

        session.pop(
            PROMOTER_SESSION_ID,
            None
        )

        session.pop(
            PROMOTER_CSRF_SESSION,
            None
        )

        return None

    promoter = get_promoter_by_id(
        promoter_id
    )

    if not promoter:

        session.pop(
            PROMOTER_SESSION_ID,
            None
        )

        session.pop(
            PROMOTER_CSRF_SESSION,
            None
        )

        return None

    if str(
        _row_get(
            promoter,
            "status",
            ""
        )
    ).lower() != "active":

        session.pop(
            PROMOTER_SESSION_ID,
            None
        )

        session.pop(
            PROMOTER_CSRF_SESSION,
            None
        )

        return None

    return promoter


# ==========================================================
# LOGIN PAGE
# ==========================================================

def promoter_login_page():

    existing = _current_promoter()

    if existing:

        return redirect(
            url_for(
                "referral_dashboard"
            )
        )

    csrf = _csrf_token()

    referral_prefill = str(
        request.args.get(
            "ref",
            ""
        )
    ).strip()

    error = None

    if request.method == "POST":

        try:

            _check_csrf()

            referral_code = str(
                request.form.get(
                    "referral_code",
                    ""
                )
            ).strip()

            password = str(
                request.form.get(
                    "password",
                    ""
                )
            )

            if not referral_code:

                raise ValueError(
                    "Referral code is required."
                )

            if not password:

                raise ValueError(
                    "Password is required."
                )

            promoter = (
                get_promoter_by_referral_code(
                    referral_code
                )
            )

            if not promoter:

                raise ValueError(
                    "Invalid referral code or password."
                )

            promoter_id = _row_get(
                promoter,
                "id"
            )

            if not verify_promoter_password(
                promoter_id,
                password
            ):

                raise ValueError(
                    "Invalid referral code or password."
                )

            # ------------------------------------------
            # ROTATE PROMOTER SESSION
            # ------------------------------------------

            session.pop(
                PROMOTER_SESSION_ID,
                None
            )

            session.pop(
                PROMOTER_CSRF_SESSION,
                None
            )

            session[
                PROMOTER_SESSION_ID
            ] = int(promoter_id)

            session[
                PROMOTER_CSRF_SESSION
            ] = secrets.token_urlsafe(32)

            session.permanent = True

            return redirect(
                url_for(
                    "referral_dashboard"
                )
            )

        except Exception as exc:

            if isinstance(
                exc,
                ValueError
            ):

                error = str(exc)

            else:

                logger.exception(
                    "Promoter login error."
                )

                error = (
                    "Unable to login right now."
                )

    return render_template_string(
        """
<!doctype html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport"
          content="width=device-width,initial-scale=1">

    <title>Promoter Login - Alhikam</title>

    <style>
        body {
            font-family: Arial, sans-serif;
            background: #f5f7fb;
            margin: 0;
            padding: 30px 15px;
        }

        .box {
            max-width: 430px;
            margin: 40px auto;
            background: white;
            padding: 25px;
            border-radius: 14px;
            box-shadow: 0 8px 30px rgba(0,0,0,.08);
        }

        h1 {
            text-align: center;
            margin-bottom: 25px;
        }

        label {
            display: block;
            margin-top: 15px;
            font-weight: bold;
        }

        input {
            width: 100%;
            box-sizing: border-box;
            padding: 13px;
            margin-top: 7px;
            border: 1px solid #ddd;
            border-radius: 8px;
        }

        button {
            width: 100%;
            padding: 14px;
            margin-top: 22px;
            border: 0;
            border-radius: 8px;
            background: #111827;
            color: white;
            font-weight: bold;
        }

        .error {
            background: #fee2e2;
            color: #991b1b;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 15px;
        }
    </style>
</head>

<body>

<div class="box">

    <h1>Alhikam Promoter Login</h1>

    {% if error %}
        <div class="error">
            {{ error }}
        </div>
    {% endif %}

    <form method="POST">

        <input
            type="hidden"
            name="csrf_token"
            value="{{ csrf }}"
        >

        <label>
            Referral Code
        </label>

        <input
            type="text"
            name="referral_code"
            value="{{ referral_prefill }}"
            required
            autocomplete="username"
        >

        <label>
            Password
        </label>

        <input
            type="password"
            name="password"
            required
            autocomplete="current-password"
        >

        <button type="submit">
            Login
        </button>

    </form>

</div>

</body>
</html>
        """,
        csrf=csrf,
        referral_prefill=referral_prefill,
        error=error,
    )


# ==========================================================
# LOGOUT
# ==========================================================

def promoter_logout():

    promoter = _current_promoter()

    if not promoter:
        return redirect(
            url_for(
                "promoter_login"
            )
        )

    if request.method != "POST":
        abort(405)

    _check_csrf()

    # IMPORTANT:
    # Do NOT use session.clear()
    # because the main application may have
    # other session information.

    session.pop(
        PROMOTER_SESSION_ID,
        None
    )

    session.pop(
        PROMOTER_CSRF_SESSION,
        None
    )

    return redirect(
        url_for(
            "promoter_login"
        )
    )


# ==========================================================
# DASHBOARD
# ==========================================================

def referral_dashboard_by_code(
    referral_code=None
):

    promoter = _current_promoter()

    if not promoter:

        return redirect(
            url_for(
                "promoter_login",
                ref=referral_code
                if referral_code
                else ""
            )
        )

    promoter_id = _row_get(
        promoter,
        "id"
    )

    actual_referral_code = _row_get(
        promoter,
        "referral_code",
        ""
    )

    withdrawals = (
        get_promoter_withdrawals(
            promoter_id
        )
    )

    withdrawal_rows = []

    for withdrawal in withdrawals:

        withdrawal_rows.append({
            "id": _row_get(
                withdrawal,
                "id"
            ),

            "amount": _safe_money(
                _row_get(
                    withdrawal,
                    "amount",
                    0
                )
            ),

            "bank_name": _row_get(
                withdrawal,
                "bank_name",
                ""
            ),

            "account_number":
                _mask_account(
                    _row_get(
                        withdrawal,
                        "account_number",
                        ""
                    )
                ),

            "status": _row_get(
                withdrawal,
                "status",
                "pending"
            ),

            "transfer_status":
                _row_get(
                    withdrawal,
                    "transfer_status",
                    ""
                ),

            "created_at":
                _row_get(
                    withdrawal,
                    "created_at",
                    ""
                ),
        })

    referral_link = (
        f"{APP_URL}/payment?ref="
        f"{actual_referral_code}"
    )

    return render_template_string(
        """
<!doctype html>
<html>
<head>

<meta charset="utf-8">

<meta name="viewport"
      content="width=device-width,initial-scale=1">

<title>Promoter Dashboard</title>

<style>

body {
    font-family: Arial, sans-serif;
    background: #f5f7fb;
    margin: 0;
    padding: 15px;
}

.container {
    max-width: 900px;
    margin: auto;
}

.card {
    background: white;
    padding: 20px;
    margin-bottom: 15px;
    border-radius: 14px;
    box-shadow: 0 5px 20px rgba(0,0,0,.06);
}

.balance {
    font-size: 30px;
    font-weight: bold;
}

.link {
    word-break: break-all;
    background: #f3f4f6;
    padding: 12px;
    border-radius: 8px;
}

a, button {
    display: inline-block;
    padding: 11px 15px;
    border-radius: 8px;
    text-decoration: none;
    border: 0;
    cursor: pointer;
}

.withdraw {
    background: #111827;
    color: white;
}

.logout {
    background: #fee2e2;
    color: #991b1b;
}

table {
    width: 100%;
    border-collapse: collapse;
}

th, td {
    padding: 10px;
    border-bottom: 1px solid #eee;
    text-align: left;
}

.status {
    font-weight: bold;
}

</style>

</head>

<body>

<div class="container">

<div class="card">

<h2>
    Welcome, {{ promoter_name }}
</h2>

<p>
    Referral Code:
    <strong>{{ referral_code }}</strong>
</p>

<p class="balance">
    {{ available_balance }}
</p>

<p>
    Available Balance
</p>

<a class="withdraw"
   href="{{ url_for('referral_withdraw') }}">
    Withdraw Money
</a>

<form method="POST"
      action="{{ url_for('promoter_logout') }}"
      style="margin-top:10px;">

    <input
        type="hidden"
        name="csrf_token"
        value="{{ csrf }}"
    >

    <button class="logout"
            type="submit">
        Logout
    </button>

</form>

</div>


<div class="card">

<h3>Your Referral Link</h3>

<div class="link">
    {{ referral_link }}
</div>

</div>


<div class="card">

<h3>Withdrawal History</h3>

{% if withdrawals %}

<table>

<tr>
    <th>ID</th>
    <th>Amount</th>
    <th>Bank</th>
    <th>Account</th>
    <th>Status</th>
    <th></th>
</tr>

{% for item in withdrawals %}

<tr>

<td>
    #{{ item.id }}
</td>

<td>
    {{ item.amount }}
</td>

<td>
    {{ item.bank_name }}
</td>

<td>
    {{ item.account_number }}
</td>

<td class="status">
    {{ item.status }}
</td>

<td>
    <a href="{{ url_for(
        'withdrawal_status',
        withdrawal_id=item.id
    ) }}">
        View
    </a>
</td>

</tr>

{% endfor %}

</table>

{% else %}

<p>
    No withdrawals yet.
</p>

{% endif %}

</div>

</div>

</body>
</html>
        """,

        promoter_name=_row_get(
            promoter,
            "full_name",
            "Promoter"
        ),

        referral_code=actual_referral_code,

        available_balance=_safe_money(
            _row_get(
                promoter,
                "available_balance",
                0
            )
        ),

        referral_link=referral_link,

        withdrawals=withdrawal_rows,

        csrf=_csrf_token(),
    )


# ==========================================================
# WITHDRAWAL PAGE
# ==========================================================

def withdrawal_page(
    referral_code=None
):

    promoter = _current_promoter()

    if not promoter:

        return redirect(
            url_for(
                "promoter_login",
                ref=referral_code
                if referral_code
                else ""
            )
        )

    promoter_id = _row_get(
        promoter,
        "id"
    )

    csrf = _csrf_token()

    error = None

    # ------------------------------------------------------
    # BANKS
    # ------------------------------------------------------

    banks = get_flutterwave_banks("NG")

    # Fallback only if API bank list is unavailable.
    #
    # IMPORTANT:
    # This is only a fallback, not the primary source.

    if not banks:

        banks = [
            {
                "code": "044",
                "name": "Access Bank"
            },
            {
                "code": "050",
                "name": "Ecobank Nigeria"
            },
            {
                "code": "011",
                "name": "First Bank of Nigeria"
            },
            {
                "code": "214",
                "name": "First City Monument Bank"
            },
            {
                "code": "070",
                "name": "Fidelity Bank"
            },
            {
                "code": "058",
                "name": "Guaranty Trust Bank"
            },
            {
                "code": "082",
                "name": "Keystone Bank"
            },
            {
                "code": "076",
                "name": "Polaris Bank"
            },
            {
                "code": "221",
                "name": "Stanbic IBTC Bank"
            },
            {
                "code": "068",
                "name": "Standard Chartered Bank"
            },
            {
                "code": "232",
                "name": "Sterling Bank"
            },
            {
                "code": "100",
                "name": "Suntrust Bank"
            },
            {
                "code": "032",
                "name": "Union Bank of Nigeria"
            },
            {
                "code": "033",
                "name": "United Bank for Africa"
            },
            {
                "code": "215",
                "name": "Unity Bank"
            },
            {
                "code": "035",
                "name": "Wema Bank"
            },
            {
                "code": "057",
                "name": "Zenith Bank"
            },
        ]

    # ------------------------------------------------------
    # POST
    # ------------------------------------------------------

    if request.method == "POST":

        try:

            _check_csrf()

            amount_raw = str(
                request.form.get(
                    "amount",
                    ""
                )
            ).strip()

            bank_code = str(
                request.form.get(
                    "bank_code",
                    ""
                )
            ).strip()

            account_number = str(
                request.form.get(
                    "account_number",
                    ""
                )
            ).strip()

            if not amount_raw:

                raise ValueError(
                    "Enter withdrawal amount."
                )

            try:

                amount = Decimal(
                    amount_raw
                )

            except InvalidOperation:

                raise ValueError(
                    "Invalid withdrawal amount."
                )

            if not amount.is_finite():

                raise ValueError(
                    "Invalid withdrawal amount."
                )

            amount = amount.quantize(
                Decimal("0.01")
            )

            if amount < MINIMUM_WITHDRAWAL:

                raise ValueError(
                    f"Minimum withdrawal is "
                    f"₦{MINIMUM_WITHDRAWAL:,.2f}"
                )

            if not bank_code:

                raise ValueError(
                    "Please select your bank."
                )

            if (
                not account_number.isdigit()
                or len(account_number) != 10
            ):

                raise ValueError(
                    "Account number must contain 10 digits."
                )

            # ------------------------------------------
            # SERVER-SIDE ACCOUNT RESOLVE
            # ------------------------------------------

            resolved = resolve_bank_account(
                account_number=account_number,
                bank_code=bank_code,
            )

            verified_name = str(
                resolved.get(
                    "account_name",
                    ""
                )
            ).strip()

            if not verified_name:

                raise ValueError(
                    "Bank account could not be verified."
                )

            # ------------------------------------------
            # CREATE LOCAL WITHDRAWAL
            # ------------------------------------------

            withdrawal_id = create_withdrawal(
                promoter_id=promoter_id,
                amount=amount,
                bank_name=str(
                    next(
                        (
                            b["name"]
                            for b in banks
                            if str(
                                b["code"]
                            ) == bank_code
                        ),
                        bank_code
                    )
                ),
                bank_code=bank_code,
                account_name=verified_name,
                account_number=account_number,
            )

            # ------------------------------------------
            # STABLE REFERENCE
            # ------------------------------------------

            stable_reference = (
                f"ALHIKAM-WD-{withdrawal_id}"
            )

            # ------------------------------------------
            # SAVE REFERENCE BEFORE PROVIDER CALL
            # ------------------------------------------

            update_withdrawal_transfer(
                withdrawal_id=withdrawal_id,
                transfer_reference=stable_reference,
                transfer_status="PROCESSING",
                transfer_message=(
                    "Withdrawal request created."
                ),
            )

            # ------------------------------------------
            # FLUTTERWAVE TRANSFER
            # ------------------------------------------

            result = create_flutterwave_transfer(

                amount=amount,

                account_number=account_number,

                bank_code=bank_code,

                account_name=verified_name,

                narration=(
                    "Alhikam Learning Center "
                    "promoter withdrawal"
                ),

                callback_url=(
                    f"{APP_URL}"
                    "/flutterwave/transfer-callback"
                ),

                reference=stable_reference,
            )

            transfer_id = result.get(
                "transfer_id"
            )

            returned_reference = result.get(
                "reference"
            )

            provider_status = str(
                result.get(
                    "status",
                    "PROCESSING"
                )
            ).upper()

            message = str(
                result.get(
                    "message",
                    ""
                )
            )[:300]

            # ------------------------------------------
            # REFERENCE MUST MATCH
            # ------------------------------------------

            if (
                returned_reference
                and returned_reference
                != stable_reference
            ):

                logger.error(
                    "Transfer reference mismatch. "
                    "Withdrawal=%s",
                    withdrawal_id,
                )

                update_withdrawal_transfer(
                    withdrawal_id=withdrawal_id,
                    transfer_id=transfer_id,
                    transfer_reference=stable_reference,
                    transfer_status="PROCESSING",
                    transfer_message=(
                        "Reference mismatch. "
                        "Manual verification required."
                    ),
                )

                return redirect(
                    url_for(
                        "withdrawal_status",
                        withdrawal_id=withdrawal_id
                    )
                )

            # ------------------------------------------
            # SAVE PROVIDER DATA
            # ------------------------------------------

            update_withdrawal_transfer(
                withdrawal_id=withdrawal_id,
                transfer_id=transfer_id,
                transfer_reference=stable_reference,
                transfer_status=provider_status,
                transfer_message=message,
            )

            # ------------------------------------------
            # FINAL STATUS
            # ------------------------------------------

            if transfer_id:

                verified = (
                    get_flutterwave_transfer_status(
                        transfer_id
                    )
                )

                verified_reference = str(
                    verified.get(
                        "reference"
                    ) or ""
                ).strip()

                if (
                    verified_reference
                    and verified_reference
                    != stable_reference
                ):

                    logger.error(
                        "Verified transfer reference "
                        "does not match local reference."
                    )

                else:

                    process_transfer_result(
                        withdrawal_id=withdrawal_id,

                        flutterwave_status=verified.get(
                            "status"
                        ),

                        transfer_id=verified.get(
                            "transfer_id"
                        ) or transfer_id,

                        transfer_reference=(
                            verified.get(
                                "reference"
                            )
                            or stable_reference
                        ),

                        message=verified.get(
                            "message"
                        ),
                    )

            else:

                # IMPORTANT:
                # No transfer ID does NOT mean failed.
                # Keep it processing.

                update_withdrawal_transfer(
                    withdrawal_id=withdrawal_id,
                    transfer_reference=stable_reference,
                    transfer_status="PROCESSING",
                    transfer_message=(
                        "Transfer is being verified."
                    ),
                )

            return redirect(
                url_for(
                    "withdrawal_status",
                    withdrawal_id=withdrawal_id
                )
            )

        except ValueError as exc:

            error = str(exc)

        except Exception:

            logger.exception(
                "Withdrawal processing error."
            )

            error = (
                "Withdrawal could not be completed "
                "right now. Please check the status "
                "before trying again."
            )

    return render_template_string(
        """
<!doctype html>
<html>

<head>

<meta charset="utf-8">

<meta name="viewport"
      content="width=device-width,initial-scale=1">

<title>Withdraw - Alhikam</title>

<style>

body {
    font-family: Arial, sans-serif;
    background: #f5f7fb;
    padding: 20px;
}

.box {
    max-width: 500px;
    margin: auto;
    background: white;
    padding: 25px;
    border-radius: 14px;
}

input, select {
    width: 100%;
    box-sizing: border-box;
    padding: 13px;
    margin: 7px 0 15px;
    border: 1px solid #ddd;
    border-radius: 8px;
}

button {
    width: 100%;
    padding: 14px;
    border: 0;
    border-radius: 8px;
    background: #111827;
    color: white;
    font-weight: bold;
}

.error {
    background: #fee2e2;
    color: #991b1b;
    padding: 12px;
    border-radius: 8px;
    margin-bottom: 15px;
}

.info {
    background: #eff6ff;
    padding: 12px;
    border-radius: 8px;
    margin-bottom: 15px;
}

</style>

</head>

<body>

<div class="box">

<h2>
    Withdraw Earnings
</h2>

<div class="info">

Available Balance:
<strong>
    {{ balance }}
</strong>

<br><br>

Minimum Withdrawal:
<strong>
    {{ minimum }}
</strong>

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
    value="{{ csrf }}"
>

<label>
    Amount
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

{% for bank in banks %}

<option value="{{ bank.code }}">
    {{ bank.name }}
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

<button type="submit">
    Withdraw
</button>

</form>

<br>

<a href="{{ url_for('referral_dashboard') }}">
    ← Back to Dashboard
</a>

</div>

</body>

</html>
        """,

        csrf=csrf,

        balance=_safe_money(
            _row_get(
                promoter,
                "available_balance",
                0
            )
        ),

        minimum=_safe_money(
            MINIMUM_WITHDRAWAL
        ),

        banks=banks,

        error=error,
    )


# ==========================================================
# WITHDRAWAL STATUS
# ==========================================================

def withdrawal_status_page(
    withdrawal_id,
    referral_code=None
):

    promoter = _current_promoter()

    if not promoter:

        return redirect(
            url_for(
                "promoter_login",
                ref=referral_code
                if referral_code
                else ""
            )
        )

    try:

        withdrawal_id = int(
            withdrawal_id
        )

    except (
        ValueError,
        TypeError,
    ):

        abort(404)

    withdrawal = get_withdrawal_by_id(
        withdrawal_id
    )

    if not withdrawal:

        abort(404)

    promoter_id = _row_get(
        promoter,
        "id"
    )

    # ======================================================
    # OWNERSHIP CHECK
    # ======================================================

    if int(
        _row_get(
            withdrawal,
            "promoter_id",
            -1
        )
    ) != int(promoter_id):

        abort(403)

    status = str(
        _row_get(
            withdrawal,
            "status",
            ""
        )
    ).lower()

    transfer_id = _row_get(
        withdrawal,
        "transfer_id"
    )

    transfer_reference = _row_get(
        withdrawal,
        "transfer_reference"
    )

    # ======================================================
    # VERIFY PROCESSING TRANSFER
    # ======================================================

    if (
        status == "processing"
        and (
            transfer_id
            or transfer_reference
        )
    ):

        try:

            if transfer_id:

                verified = (
                    get_flutterwave_transfer_status(
                        transfer_id
                    )
                )

            else:

                verified = (
                    get_flutterwave_transfer_status_by_reference(
                        transfer_reference
                    )
                )

            verified_reference = str(
                verified.get(
                    "reference"
                ) or ""
            ).strip()

            # ----------------------------------------------
            # NEVER ACCEPT WRONG REFERENCE
            # ----------------------------------------------

            if (
                verified_reference
                and verified_reference
                != str(
                    transfer_reference
                    or ""
                ).strip()
            ):

                logger.error(
                    "Transfer reference mismatch "
                    "during status verification. "
                    "Withdrawal=%s",
                    withdrawal_id,
                )

            else:

                process_transfer_result(

                    withdrawal_id=withdrawal_id,

                    flutterwave_status=verified.get(
                        "status"
                    ),

                    transfer_id=verified.get(
                        "transfer_id"
                    ) or transfer_id,

                    transfer_reference=(
                        verified_reference
                        or transfer_reference
                    ),

                    message=verified.get(
                        "message"
                    ),
                )

                withdrawal = (
                    get_withdrawal_by_id(
                        withdrawal_id
                    )
                )

        except Exception:

            logger.exception(
                "Withdrawal status verification failed. "
                "Withdrawal=%s",
                withdrawal_id,
            )

            # IMPORTANT:
            # Do not refund because verification failed.

    # ======================================================
    # DISPLAY
    # ======================================================

    display_status = str(
        _row_get(
            withdrawal,
            "status",
            "pending"
        )
    ).upper()

    amount = _safe_money(
        _row_get(
            withdrawal,
            "amount",
            0
        )
    )

    bank_name = _row_get(
        withdrawal,
        "bank_name",
        ""
    )

    account_number = _mask_account(
        _row_get(
            withdrawal,
            "account_number",
            ""
        )
    )

    account_name = _row_get(
        withdrawal,
        "account_name",
        ""
    )

    transfer_status = _row_get(
        withdrawal,
        "transfer_status",
        ""
    )

    transfer_message = _row_get(
        withdrawal,
        "transfer_message",
        ""
    )

    return render_template_string(
        """
<!doctype html>
<html>

<head>

<meta charset="utf-8">

<meta name="viewport"
      content="width=device-width,initial-scale=1">

<title>Withdrawal Status</title>

<style>

body {
    font-family: Arial, sans-serif;
    background: #f5f7fb;
    padding: 20px;
}

.box {
    max-width: 550px;
    margin: auto;
    background: white;
    padding: 25px;
    border-radius: 14px;
    box-shadow: 0 5px 20px rgba(0,0,0,.06);
}

.row {
    padding: 12px 0;
    border-bottom: 1px solid #eee;
}

.status {
    font-size: 22px;
    font-weight: bold;
}

.successful {
    color: #166534;
}

.processing,
.pending {
    color: #92400e;
}

.failed,
.cancelled {
    color: #991b1b;
}

button, a {
    display: inline-block;
    margin-top: 20px;
    padding: 12px 16px;
    border-radius: 8px;
    text-decoration: none;
}

a {
    background: #111827;
    color: white;
}

</style>

</head>

<body>

<div class="box">

<h2>
    Withdrawal #{{ withdrawal_id }}
</h2>

<div class="row">
    Amount:
    <strong>{{ amount }}</strong>
</div>

<div class="row">
    Bank:
    <strong>{{ bank_name }}</strong>
</div>

<div class="row">
    Account Name:
    <strong>{{ account_name }}</strong>
</div>

<div class="row">
    Account Number:
    <strong>{{ account_number }}</strong>
</div>

<div class="row">
    Status:
    <div class="status {{ status|lower }}">
        {{ status }}
    </div>
</div>

{% if transfer_status %}

<div class="row">
    Transfer Status:
    <strong>
        {{ transfer_status }}
    </strong>
</div>

{% endif %}

{% if transfer_message %}

<div class="row">
    Message:
    {{ transfer_message }}
</div>

{% endif %}

<a href="{{ url_for('referral_dashboard') }}">
    ← Back to Dashboard
</a>

{% if status in ["PROCESSING", "PENDING"] %}

<a href="{{ url_for(
    'withdrawal_status',
    withdrawal_id=withdrawal_id
) }}">
    Check Status Again
</a>

{% endif %}

</div>

</body>

</html>
        """,

        withdrawal_id=withdrawal_id,

        amount=amount,

        bank_name=bank_name,

        account_name=account_name,

        account_number=account_number,

        status=display_status,

        transfer_status=transfer_status,

        transfer_message=transfer_message,
    )