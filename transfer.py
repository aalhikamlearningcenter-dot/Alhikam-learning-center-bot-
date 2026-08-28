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

FLW_SECRET_KEY = os.getenv(
    "FLW_SECRET_KEY"
)

FLUTTERWAVE_TRANSFER_URL = (
    "https://api.flutterwave.com/v3/transfers"
)


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

    # ------------------------------------------------------
    # CHECK SECRET KEY
    # ------------------------------------------------------

    if not FLW_SECRET_KEY:

        print(
            "FLUTTERWAVE TRANSFER ERROR: "
            "FLW_SECRET_KEY is missing."
        )

        return None


    # ------------------------------------------------------
    # VALIDATE AMOUNT
    # ------------------------------------------------------

    try:

        amount = float(
            amount
        )

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


    # ------------------------------------------------------
    # VALIDATE ACCOUNT NUMBER
    # ------------------------------------------------------

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


    # ------------------------------------------------------
    # VALIDATE BANK CODE
    # ------------------------------------------------------

    bank_code = str(
        bank_code or ""
    ).strip()


    if not bank_code:

        print(
            "FLUTTERWAVE TRANSFER ERROR: "
            "Bank code is missing."
        )

        return None


    # ------------------------------------------------------
    # GENERATE UNIQUE REFERENCE
    # ------------------------------------------------------

    reference = (
        "ALHIKAM-"
        + uuid.uuid4().hex[:16].upper()
    )


    # ------------------------------------------------------
    # REQUEST HEADERS
    # ------------------------------------------------------

    headers = {

        "Authorization":
            f"Bearer {FLW_SECRET_KEY}",

        "Content-Type":
            "application/json",

    }


    # ------------------------------------------------------
    # TRANSFER DATA
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
            account_name or "",

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


    # ------------------------------------------------------
    # SEND TRANSFER
    # ------------------------------------------------------

    try:

        response = requests.post(

            FLUTTERWAVE_TRANSFER_URL,

            headers=headers,

            json=payload,

            timeout=60,

        )


    except requests.RequestException as e:

        print(
            "FLUTTERWAVE TRANSFER REQUEST ERROR:",
            repr(e)
        )

        return None


    # ------------------------------------------------------
    # RESPONSE
    # ------------------------------------------------------

    print(
        "FLUTTERWAVE TRANSFER STATUS:",
        response.status_code
    )

    print(
        "FLUTTERWAVE TRANSFER RESPONSE:",
        response.text
    )


    try:

        result = response.json()

    except Exception:

        print(
            "FLUTTERWAVE TRANSFER ERROR: "
            "Invalid JSON response."
        )

        return None


    # ------------------------------------------------------
    # CHECK HTTP RESPONSE
    # ------------------------------------------------------

    if response.status_code not in {
        200,
        201
    }:

        print(
            "FLUTTERWAVE TRANSFER FAILED:"
            ,
            result
        )

        return None


    # ------------------------------------------------------
    # CHECK FLUTTERWAVE STATUS
    # ------------------------------------------------------

    if result.get("status") != "success":

        print(
            "FLUTTERWAVE TRANSFER NOT ACCEPTED:",
            result
        )

        return None


    # ------------------------------------------------------
    # GET TRANSFER DATA
    # ------------------------------------------------------

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
        result.get("message")
        or data.get("message")
        or ""
    )


    # ------------------------------------------------------
    # RETURN STANDARD RESULT
    # ------------------------------------------------------

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