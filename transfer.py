# ==========================================================
# ALHIKAM LEARNING CENTER V2
# transfer.py
#
# FLUTTERWAVE TRANSFER
# REFERRAL WITHDRAWAL
# ==========================================================

import os
import uuid
import requests


# ==========================================================
# CONFIG
# ==========================================================

FLW_SECRET_KEY = os.getenv("FLW_SECRET_KEY")

FLUTTERWAVE_TRANSFER_URL = (
    "https://api.flutterwave.com/v3/transfers"
)


# ==========================================================
# COMMON HEADERS
# ==========================================================

def _headers():

    return {
        "Authorization": f"Bearer {FLW_SECRET_KEY}",
        "Content-Type": "application/json",
    }


# ==========================================================
# CREATE FLUTTERWAVE TRANSFER
# ==========================================================

def create_flutterwave_transfer(
    amount,
    account_number,
    bank_code,
    account_name=None,
    narration="ALHIKAM Referral Commission"
):

    if not FLW_SECRET_KEY:

        print(
            "FLUTTERWAVE TRANSFER ERROR: "
            "FLW_SECRET_KEY is missing."
        )

        return None


    # ======================================================
    # AMOUNT
    # ======================================================

    try:

        amount = float(amount)

    except Exception:

        print(
            "FLUTTERWAVE TRANSFER ERROR: "
            "Invalid amount."
        )

        return None


    if amount <= 0:

        print(
            "FLUTTERWAVE TRANSFER ERROR: "
            "Amount must be greater than zero."
        )

        return None


    # ======================================================
    # ACCOUNT NUMBER
    # ======================================================

    account_number = str(
        account_number or ""
    ).strip()


    if (
        len(account_number) != 10
        or not account_number.isdigit()
    ):

        print(
            "FLUTTERWAVE TRANSFER ERROR: "
            "Invalid account number."
        )

        return None


    # ======================================================
    # BANK CODE
    # ======================================================

    bank_code = str(
        bank_code or ""
    ).strip()


    if not bank_code:

        print(
            "FLUTTERWAVE TRANSFER ERROR: "
            "Bank code is missing."
        )

        return None


    # ======================================================
    # ACCOUNT NAME
    # ======================================================

    account_name = str(
        account_name or ""
    ).strip()


    # ======================================================
    # UNIQUE REFERENCE
    # ======================================================

    reference = (
        "ALHIKAM-"
        + uuid.uuid4().hex[:16].upper()
    )


    # ======================================================
    # PAYLOAD
    # ======================================================

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
            account_name,

        "narration":
            narration,

        "reference":
            reference,
    }


    print(
        "FLUTTERWAVE TRANSFER REQUEST:",
        {
            "amount": amount,
            "bank_code": bank_code,
            "account_number":
                f"****{account_number[-4:]}",
            "reference": reference,
        }
    )


    # ======================================================
    # SEND REQUEST
    # ======================================================

    try:

        response = requests.post(

            FLUTTERWAVE_TRANSFER_URL,

            headers=_headers(),

            json=payload,

            timeout=60,

        )

    except requests.RequestException as e:

        print(
            "FLUTTERWAVE TRANSFER REQUEST ERROR:",
            repr(e)
        )

        return None


    print(
        "FLUTTERWAVE TRANSFER HTTP STATUS:",
        response.status_code
    )

    print(
        "FLUTTERWAVE TRANSFER RESPONSE:",
        response.text
    )


    # ======================================================
    # JSON
    # ======================================================

    try:

        result = response.json()

    except Exception:

        print(
            "FLUTTERWAVE TRANSFER ERROR: "
            "Invalid JSON response."
        )

        return None


    # ======================================================
    # HTTP CHECK
    # ======================================================

    if response.status_code not in {
        200,
        201
    }:

        print(
            "FLUTTERWAVE TRANSFER FAILED:",
            result
        )

        return None


    # ======================================================
    # API CHECK
    # ======================================================

    if result.get("status") != "success":

        print(
            "FLUTTERWAVE TRANSFER NOT ACCEPTED:",
            result
        )

        return None


    # ======================================================
    # DATA
    # ======================================================

    data = result.get(
        "data"
    ) or {}


    transfer_id = data.get(
        "id"
    )


    transfer_reference = (
        data.get("reference")
        or reference
    )


    transfer_status = (
        data.get("status")
        or "NEW"
    )


    transfer_message = (
        data.get("complete_message")
        or data.get("message")
        or result.get("message")
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
            "FLUTTERWAVE STATUS ERROR: "
            "FLW_SECRET_KEY is missing."
        )

        return None


    if not transfer_id:

        print(
            "FLUTTERWAVE STATUS ERROR: "
            "Transfer ID is missing."
        )

        return None


    url = (
        f"{FLUTTERWAVE_TRANSFER_URL}/"
        f"{transfer_id}"
    )


    try:

        response = requests.get(

            url,

            headers=_headers(),

            timeout=60,

        )

    except requests.RequestException as e:

        print(
            "FLUTTERWAVE STATUS REQUEST ERROR:",
            repr(e)
        )

        return None


    print(
        "FLUTTERWAVE STATUS HTTP:",
        response.status_code
    )

    print(
        "FLUTTERWAVE STATUS RESPONSE:",
        response.text
    )


    try:

        result = response.json()

    except Exception:

        print(
            "FLUTTERWAVE STATUS ERROR: "
            "Invalid JSON."
        )

        return None


    if response.status_code != 200:

        print(
            "FLUTTERWAVE STATUS FAILED:",
            result
        )

        return None


    if result.get("status") != "success":

        print(
            "FLUTTERWAVE STATUS NOT SUCCESS:",
            result
        )

        return None


    data = result.get(
        "data"
    ) or {}


    status = str(
        data.get("status")
        or ""
    ).upper().strip()


    return {

        "success":
            True,

        "transfer_id":
            data.get("id"),

        "reference":
            data.get("reference"),

        "status":
            status,

        "message":
            (
                data.get("complete_message")
                or data.get("message")
                or result.get("message")
                or ""
            ),

        "raw":
            result,
    }