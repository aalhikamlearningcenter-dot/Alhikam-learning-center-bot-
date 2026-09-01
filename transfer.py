# ==========================================================
# ALHIKAM LEARNING CENTER V2
# transfer.py
#
# FLUTTERWAVE TRANSFER
# BANK ACCOUNT RESOLUTION
# TRANSFER STATUS
# ==========================================================

import os
import uuid
import requests


# ==========================================================
# CONFIG
# ==========================================================

FLW_SECRET_KEY = os.getenv("FLW_SECRET_KEY")

TRANSFER_URL = (
    "https://api.flutterwave.com/v3/transfers"
)

RESOLVE_ACCOUNT_URL = (
    "https://api.flutterwave.com/v3/accounts/resolve"
)


# ==========================================================
# HEADERS
# ==========================================================

def _headers():

    if not FLW_SECRET_KEY:
        return {
            "Content-Type": "application/json"
        }

    return {
        "Authorization": (
            f"Bearer {FLW_SECRET_KEY}"
        ),
        "Content-Type": "application/json",
    }


# ==========================================================
# RESOLVE BANK ACCOUNT
# ==========================================================

def resolve_bank_account(
    account_number,
    bank_code
):

    if not FLW_SECRET_KEY:

        print(
            "FLW ERROR: FLW_SECRET_KEY missing."
        )

        return None

    account_number = str(
        account_number or ""
    ).strip()

    bank_code = str(
        bank_code or ""
    ).strip()

    # ------------------------------------------------------
    # VALIDATE ACCOUNT NUMBER
    # ------------------------------------------------------

    if (
        len(account_number) != 10
        or not account_number.isdigit()
    ):

        print(
            "ACCOUNT RESOLVE: Invalid account number."
        )

        return None

    # ------------------------------------------------------
    # VALIDATE BANK CODE
    # ------------------------------------------------------

    if not bank_code:

        print(
            "ACCOUNT RESOLVE: Bank code missing."
        )

        return None

    payload = {

        "account_number":
            account_number,

        "account_bank":
            bank_code,

    }

    print(
        "ACCOUNT RESOLVE REQUEST:",
        {
            "bank_code": bank_code,
            "account":
                f"****{account_number[-4:]}",
        }
    )

    try:

        response = requests.post(

            RESOLVE_ACCOUNT_URL,

            headers=_headers(),

            json=payload,

            timeout=30,

        )

    except requests.RequestException as e:

        print(
            "ACCOUNT RESOLVE REQUEST ERROR:",
            repr(e)
        )

        return None

    print(
        "ACCOUNT RESOLVE HTTP:",
        response.status_code
    )

    try:

        result = response.json()

    except Exception:

        print(
            "ACCOUNT RESOLVE INVALID JSON."
        )

        return None

    print(
        "ACCOUNT RESOLVE RESPONSE:",
        result
    )

    # ------------------------------------------------------
    # HTTP CHECK
    # ------------------------------------------------------

    if response.status_code != 200:

        print(
            "ACCOUNT RESOLVE FAILED:",
            result
        )

        return None

    # ------------------------------------------------------
    # FLUTTERWAVE STATUS CHECK
    # ------------------------------------------------------

    if result.get("status") != "success":

        print(
            "ACCOUNT RESOLVE NOT SUCCESS:",
            result
        )

        return None

    data = (
        result.get("data")
        or {}
    )

    resolved_account_number = str(
        data.get(
            "account_number",
            account_number
        )
        or account_number
    ).strip()

    resolved_account_name = str(
        data.get(
            "account_name",
            ""
        )
        or ""
    ).strip()

    if not resolved_account_name:

        print(
            "ACCOUNT RESOLVE: Account name missing."
        )

        return None

    return {

        "account_number":
            resolved_account_number,

        "account_name":
            resolved_account_name,

        "bank_code":
            bank_code,

    }


# ==========================================================
# CREATE FLUTTERWAVE TRANSFER
# ==========================================================

def create_flutterwave_transfer(
    amount,
    account_number,
    bank_code,
    account_name=None,
    narration="ALHIKAM Referral Commission",
    callback_url=None,
):

    if not FLW_SECRET_KEY:

        print(
            "FLW TRANSFER ERROR: "
            "FLW_SECRET_KEY missing."
        )

        return None

    # ------------------------------------------------------
    # AMOUNT
    # ------------------------------------------------------

    try:

        amount = float(amount)

    except Exception:

        print(
            "FLW TRANSFER: Invalid amount."
        )

        return None

    if amount <= 0:

        print(
            "FLW TRANSFER: Amount must be greater than zero."
        )

        return None

    # ------------------------------------------------------
    # ACCOUNT DATA
    # ------------------------------------------------------

    account_number = str(
        account_number or ""
    ).strip()

    bank_code = str(
        bank_code or ""
    ).strip()

    account_name = str(
        account_name or ""
    ).strip()

    # ------------------------------------------------------
    # ACCOUNT NUMBER VALIDATION
    # ------------------------------------------------------

    if (
        len(account_number) != 10
        or not account_number.isdigit()
    ):

        print(
            "FLW TRANSFER: Invalid account number."
        )

        return None

    # ------------------------------------------------------
    # BANK CODE VALIDATION
    # ------------------------------------------------------

    if not bank_code:

        print(
            "FLW TRANSFER: Bank code missing."
        )

        return None

    # ------------------------------------------------------
    # RESOLVE ACCOUNT
    #
    # This confirms the account exists before transfer.
    # ------------------------------------------------------

    resolved = resolve_bank_account(

        account_number=account_number,

        bank_code=bank_code,

    )

    if not resolved:

        print(
            "FLW TRANSFER: "
            "Bank account could not be resolved."
        )

        return None

    resolved_account_name = (
        resolved.get(
            "account_name",
            ""
        )
        or ""
    ).strip()

    if not resolved_account_name:

        print(
            "FLW TRANSFER: "
            "Resolved account name is empty."
        )

        return None

    # ------------------------------------------------------
    # USE FLUTTERWAVE RESOLVED NAME
    #
    # This prevents a user from typing a fake name.
    # ------------------------------------------------------

    beneficiary_name = (
        resolved_account_name
    )

    # ------------------------------------------------------
    # UNIQUE REFERENCE
    # ------------------------------------------------------

    reference = (
        "ALHIKAM-"
        + uuid.uuid4().hex[:16].upper()
    )

    # ------------------------------------------------------
    # TRANSFER PAYLOAD
    # ------------------------------------------------------

    payload = {

        "account_bank":
            bank_code,

        "account_number":
            account_number,

        "amount":
            amount,

        "currency":
            "NGN",

        "debit_currency":
            "NGN",

        "beneficiary_name":
            beneficiary_name,

        "narration":
            narration,

        "reference":
            reference,

    }

    # ------------------------------------------------------
    # CALLBACK
    # ------------------------------------------------------

    if callback_url:

        payload[
            "callback_url"
        ] = callback_url

    print(
        "FLW TRANSFER REQUEST:",
        {
            "amount": amount,
            "bank_code": bank_code,
            "account":
                f"****{account_number[-4:]}",
            "beneficiary":
                beneficiary_name,
            "reference":
                reference,
        }
    )

    # ------------------------------------------------------
    # SEND TRANSFER
    # ------------------------------------------------------

    try:

        response = requests.post(

            TRANSFER_URL,

            headers=_headers(),

            json=payload,

            timeout=60,

        )

    except requests.RequestException as e:

        print(
            "FLW TRANSFER REQUEST ERROR:",
            repr(e)
        )

        return None

    print(
        "FLW TRANSFER HTTP:",
        response.status_code
    )

    print(
        "FLW TRANSFER RESPONSE:",
        response.text
    )

    # ------------------------------------------------------
    # JSON
    # ------------------------------------------------------

    try:

        result = response.json()

    except Exception:

        print(
            "FLW TRANSFER: Invalid JSON response."
        )

        return None

    # ------------------------------------------------------
    # HTTP STATUS
    # ------------------------------------------------------

    if response.status_code not in {
        200,
        201
    }:

        print(
            "FLW TRANSFER FAILED:",
            result
        )

        return None

    # ------------------------------------------------------
    # FLUTTERWAVE STATUS
    # ------------------------------------------------------

    if result.get("status") != "success":

        print(
            "FLW TRANSFER NOT ACCEPTED:",
            result
        )

        return None

    data = (
        result.get("data")
        or {}
    )

    transfer_id = data.get("id")

    transfer_reference = (
        data.get("reference")
        or reference
    )

    transfer_status = str(
        data.get(
            "status",
            "NEW"
        )
        or "NEW"
    ).upper().strip()

    transfer_message = (
        data.get(
            "complete_message"
        )
        or data.get(
            "message"
        )
        or result.get(
            "message"
        )
        or ""
    )

    return {

        "success":
            True,

        "transfer_id":
            transfer_id,

        "reference":
            transfer_reference,

        "status":
            transfer_status,

        "message":
            transfer_message,

        "account_name":
            beneficiary_name,

        "account_number":
            account_number,

        "bank_code":
            bank_code,

        "raw":
            result,

    }


# ==========================================================
# GET TRANSFER STATUS
# ==========================================================

def get_flutterwave_transfer_status(
    transfer_id
):

    if not FLW_SECRET_KEY:

        print(
            "FLW STATUS ERROR: "
            "FLW_SECRET_KEY missing."
        )

        return None

    if not transfer_id:

        print(
            "FLW STATUS ERROR: "
            "Transfer ID missing."
        )

        return None

    transfer_id = str(
        transfer_id
    ).strip()

    url = (
        f"{TRANSFER_URL}/{transfer_id}"
    )

    print(
        "FLW STATUS REQUEST:",
        transfer_id
    )

    try:

        response = requests.get(

            url,

            headers=_headers(),

            timeout=60,

        )

    except requests.RequestException as e:

        print(
            "FLW STATUS REQUEST ERROR:",
            repr(e)
        )

        return None

    print(
        "FLW STATUS HTTP:",
        response.status_code
    )

    try:

        result = response.json()

    except Exception:

        print(
            "FLW STATUS INVALID JSON."
        )

        return None

    print(
        "FLW STATUS RESPONSE:",
        result
    )

    if response.status_code != 200:

        return None

    if result.get("status") != "success":

        return None

    data = (
        result.get("data")
        or {}
    )

    final_transfer_id = (
        data.get("id")
        or transfer_id
    )

    transfer_reference = (
        data.get("reference")
        or ""
    )

    transfer_status = str(
        data.get(
            "status",
            ""
        )
        or ""
    ).upper().strip()

    transfer_message = (
        data.get(
            "complete_message"
        )
        or data.get(
            "message"
        )
        or result.get(
            "message"
        )
        or ""
    )

    return {

        "success":
            True,

        "transfer_id":
            final_transfer_id,

        "reference":
            transfer_reference,

        "status":
            transfer_status,

        "message":
            transfer_message,

        "raw":
            result,

    }