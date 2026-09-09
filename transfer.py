# ==========================================================
# ALHIKAM LEARNING CENTER V2
# transfer.py
#
# FLUTTERWAVE TRANSFER / WITHDRAWAL
# SECURE VERSION
#
# IMPORTANT:
# - Never trust browser-supplied transfer status.
# - Always verify status from Flutterwave API.
# - Never refund automatically after timeout.
# - Use one stable transfer reference per withdrawal.
# ==========================================================

import os
import logging
import re

import requests

from config import APP_URL


logger = logging.getLogger(__name__)


# ==========================================================
# FLUTTERWAVE CONFIG
# ==========================================================

FLW_SECRET_KEY = os.getenv("FLW_SECRET_KEY")

FLW_TRANSFER_URL = (
    "https://api.flutterwave.com/v3/transfers"
)

FLW_ACCOUNT_RESOLVE_URL = (
    "https://api.flutterwave.com/v3/accounts/resolve"
)

FLW_BANKS_URL = (
    "https://api.flutterwave.com/v3/banks"
)

FLW_TIMEOUT = (10, 60)


# ==========================================================
# TRANSFER STATUS GROUPS
# ==========================================================

TRANSFER_FINAL_SUCCESS = {
    "SUCCESS",
    "SUCCESSFUL",
    "COMPLETED",
}

TRANSFER_FINAL_FAILED = {
    "FAILED",
    "CANCELLED",
    "CANCELED",
    "REJECTED",
}

TRANSFER_PROCESSING = {
    "NEW",
    "PENDING",
    "PROCESSING",
    "QUEUED",
}


# ==========================================================
# HEADERS
# ==========================================================

def _headers():

    if not FLW_SECRET_KEY:
        raise RuntimeError(
            "FLW_SECRET_KEY is not configured."
        )

    return {
        "Authorization": f"Bearer {FLW_SECRET_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


# ==========================================================
# ACCOUNT NUMBER VALIDATION
# ==========================================================

def _validate_account_number(account_number):

    account_number = str(
        account_number or ""
    ).strip()

    if not re.fullmatch(r"\d{10}", account_number):

        raise ValueError(
            "Account number must contain exactly 10 digits."
        )

    return account_number


# ==========================================================
# BANK CODE VALIDATION
# ==========================================================

def _validate_bank_code(bank_code):

    bank_code = str(
        bank_code or ""
    ).strip()

    if not bank_code:
        raise ValueError(
            "Bank code is required."
        )

    if len(bank_code) > 20:
        raise ValueError(
            "Invalid bank code."
        )

    return bank_code


# ==========================================================
# MASK ACCOUNT
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
# SAFE PROVIDER MESSAGE
# ==========================================================

def _safe_message(response=None, data=None):

    try:

        if isinstance(data, dict):

            message = data.get("message")

            if message:
                return str(message)[:300]

        if response is not None:

            return (
                f"Flutterwave HTTP status "
                f"{response.status_code}"
            )

    except Exception:
        pass

    return "Flutterwave transfer request could not be completed."


# ==========================================================
# JSON RESPONSE
# ==========================================================

def _json(response):

    try:
        return response.json()

    except ValueError:

        logger.error(
            "Flutterwave returned invalid JSON."
        )

        return None


# ==========================================================
# EXTRACT DATA
# ==========================================================

def _extract_result(data):

    if not isinstance(data, dict):
        return {}

    result = data.get("data")

    if isinstance(result, dict):
        return result

    return {}


# ==========================================================
# RESOLVE BANK ACCOUNT
# ==========================================================

def resolve_bank_account(
    account_number,
    bank_code,
):

    account_number = _validate_account_number(
        account_number
    )

    bank_code = _validate_bank_code(
        bank_code
    )

    payload = {
        "account_number": account_number,
        "account_bank": bank_code,
    }

    try:

        response = requests.post(
            FLW_ACCOUNT_RESOLVE_URL,
            headers=_headers(),
            json=payload,
            timeout=FLW_TIMEOUT,
        )

    except requests.Timeout:

        logger.warning(
            "Bank account resolve timed out: %s",
            _mask_account(account_number),
        )

        raise RuntimeError(
            "Bank account verification timed out. "
            "Please try again."
        )

    except requests.RequestException:

        logger.exception(
            "Bank account resolve request failed."
        )

        raise RuntimeError(
            "Unable to verify bank account right now."
        )

    data = _json(response)

    if response.status_code != 200:

        logger.error(
            "Account resolve failed. HTTP=%s",
            response.status_code,
        )

        raise ValueError(
            "Unable to verify the bank account."
        )

    if not isinstance(data, dict):

        raise RuntimeError(
            "Invalid response from Flutterwave."
        )

    provider_status = str(
        data.get("status", "")
    ).lower()

    if provider_status != "success":

        raise ValueError(
            _safe_message(
                response=response,
                data=data,
            )
        )

    result = _extract_result(data)

    resolved_name = str(
        result.get("account_name") or ""
    ).strip()

    resolved_number = str(
        result.get("account_number")
        or account_number
    ).strip()

    resolved_bank = str(
        result.get("account_bank")
        or bank_code
    ).strip()

    if not resolved_name:

        raise ValueError(
            "Flutterwave could not verify the account name."
        )

    if resolved_number != account_number:

        raise ValueError(
            "Verified account number does not match."
        )

    return {
        "success": True,
        "account_name": resolved_name,
        "account_number": resolved_number,
        "bank_code": resolved_bank,
        "message": str(
            data.get("message")
            or "Account verified successfully."
        )[:300],
    }


# ==========================================================
# CREATE FLUTTERWAVE TRANSFER
# ==========================================================

def create_flutterwave_transfer(
    amount,
    account_number,
    bank_code,
    account_name=None,
    narration="Alhikam Learning Center withdrawal",
    callback_url=None,
    reference=None,
):

    # ------------------------------------------------------
    # AMOUNT
    # ------------------------------------------------------

    try:

        amount = float(amount)

    except (TypeError, ValueError):

        raise ValueError(
            "Invalid transfer amount."
        )

    if amount <= 0:

        raise ValueError(
            "Transfer amount must be greater than zero."
        )

    # ------------------------------------------------------
    # BANK DETAILS
    # ------------------------------------------------------

    account_number = _validate_account_number(
        account_number
    )

    bank_code = _validate_bank_code(
        bank_code
    )

    # ------------------------------------------------------
    # STABLE REFERENCE REQUIRED
    # ------------------------------------------------------

    reference = str(
        reference or ""
    ).strip()

    if not reference:

        raise ValueError(
            "A stable transfer reference is required."
        )

    if len(reference) > 100:

        raise ValueError(
            "Transfer reference is too long."
        )

    # ------------------------------------------------------
    # VERIFY ACCOUNT FIRST
    # ------------------------------------------------------

    resolved = resolve_bank_account(
        account_number=account_number,
        bank_code=bank_code,
    )

    verified_account_name = resolved[
        "account_name"
    ]

    # NEVER TRUST USER-SUPPLIED ACCOUNT NAME
    account_name = verified_account_name

    # ------------------------------------------------------
    # NARRATION
    # ------------------------------------------------------

    narration = str(
        narration or
        "Alhikam Learning Center withdrawal"
    ).strip()

    narration = narration[:200]

    # ------------------------------------------------------
    # PAYLOAD
    # ------------------------------------------------------

    payload = {
        "account_bank": bank_code,
        "account_number": account_number,
        "amount": amount,
        "currency": "NGN",
        "debit_currency": "NGN",
        "beneficiary_name": account_name,
        "narration": narration,
        "reference": reference,
    }

    # ------------------------------------------------------
    # CALLBACK
    # ------------------------------------------------------

    callback_url = str(
        callback_url or ""
    ).strip()

    if callback_url.startswith(
        ("http://", "https://")
    ):

        payload["callback_url"] = callback_url

    # ------------------------------------------------------
    # CREATE TRANSFER
    # ------------------------------------------------------

    try:

        response = requests.post(
            FLW_TRANSFER_URL,
            headers=_headers(),
            json=payload,
            timeout=FLW_TIMEOUT,
        )

    except requests.Timeout:

        # IMPORTANT:
        # The transfer may have been created even though
        # our request timed out.
        #
        # NEVER REFUND HERE.
        logger.warning(
            "Flutterwave transfer timeout. "
            "Reference=%s",
            reference,
        )

        return {
            "success": False,
            "uncertain": True,
            "status": "PROCESSING",
            "transfer_id": None,
            "reference": reference,
            "message": (
                "Transfer request timed out. "
                "Status must be verified from Flutterwave."
            ),
        }

    except requests.RequestException:

        # Same principle:
        # do not assume transfer failed.
        logger.exception(
            "Flutterwave transfer request error. "
            "Reference=%s",
            reference,
        )

        return {
            "success": False,
            "uncertain": True,
            "status": "PROCESSING",
            "transfer_id": None,
            "reference": reference,
            "message": (
                "Transfer status could not be confirmed. "
                "Please verify the transfer status."
            ),
        }

    # ------------------------------------------------------
    # PARSE RESPONSE
    # ------------------------------------------------------

    data = _json(response)

    if not isinstance(data, dict):

        return {
            "success": False,
            "uncertain": True,
            "status": "PROCESSING",
            "transfer_id": None,
            "reference": reference,
            "message": (
                "Invalid response from Flutterwave. "
                "Transfer status must be verified."
            ),
        }

    result = _extract_result(data)

    provider_status = str(
        data.get("status", "")
    ).lower()

    transfer_status = str(
        result.get("status") or ""
    ).upper()

    transfer_id = result.get("id")

    provider_reference = str(
        result.get("reference")
        or reference
    ).strip()

    message = str(
        result.get("message")
        or data.get("message")
        or ""
    )[:300]

    # ------------------------------------------------------
    # REFERENCE SAFETY
    # ------------------------------------------------------

    if provider_reference != reference:

        logger.error(
            "Flutterwave reference mismatch. "
            "Expected=%s Received=%s",
            reference,
            provider_reference,
        )

        return {
            "success": False,
            "uncertain": True,
            "status": "PROCESSING",
            "transfer_id": transfer_id,
            "reference": reference,
            "message": (
                "Transfer reference mismatch. "
                "Status must be verified."
            ),
        }

    # ------------------------------------------------------
    # FINAL SUCCESS
    # ------------------------------------------------------

    if transfer_status in TRANSFER_FINAL_SUCCESS:

        return {
            "success": True,
            "uncertain": False,
            "status": transfer_status,
            "transfer_id": transfer_id,
            "reference": reference,
            "message": message
            or "Transfer successful.",
            "account_name": verified_account_name,
        }

    # ------------------------------------------------------
    # FINAL FAILED
    # ------------------------------------------------------

    if transfer_status in TRANSFER_FINAL_FAILED:

        return {
            "success": False,
            "uncertain": False,
            "status": transfer_status,
            "transfer_id": transfer_id,
            "reference": reference,
            "message": message
            or "Transfer failed.",
            "account_name": verified_account_name,
        }

    # ------------------------------------------------------
    # PROCESSING
    # ------------------------------------------------------

    if transfer_status in TRANSFER_PROCESSING:

        return {
            "success": False,
            "uncertain": True,
            "status": transfer_status,
            "transfer_id": transfer_id,
            "reference": reference,
            "message": message
            or "Transfer is being processed.",
            "account_name": verified_account_name,
        }

    # ------------------------------------------------------
    # PROVIDER ACCEPTED REQUEST BUT STATUS UNKNOWN
    # ------------------------------------------------------

    if provider_status == "success":

        return {
            "success": False,
            "uncertain": True,
            "status": transfer_status
            or "PROCESSING",
            "transfer_id": transfer_id,
            "reference": reference,
            "message": message
            or (
                "Transfer request accepted. "
                "Final status is being verified."
            ),
            "account_name": verified_account_name,
        }

    # ------------------------------------------------------
    # UNKNOWN RESPONSE
    # ------------------------------------------------------

    logger.error(
        "Unknown Flutterwave transfer response: "
        "reference=%s status=%s",
        reference,
        transfer_status,
    )

    return {
        "success": False,
        "uncertain": True,
        "status": transfer_status
        or "PROCESSING",
        "transfer_id": transfer_id,
        "reference": reference,
        "message": (
            "Transfer result is uncertain. "
            "Status must be verified."
        ),
        "account_name": verified_account_name,
    }


# ==========================================================
# GET TRANSFER STATUS BY ID
# ==========================================================

def get_flutterwave_transfer_status(
    transfer_id
):

    transfer_id = str(
        transfer_id or ""
    ).strip()

    if not transfer_id:
        raise ValueError(
            "Transfer ID is required."
        )

    url = (
        f"{FLW_TRANSFER_URL}/"
        f"{transfer_id}"
    )

    try:

        response = requests.get(
            url,
            headers=_headers(),
            timeout=FLW_TIMEOUT,
        )

    except requests.Timeout:

        logger.warning(
            "Transfer status timeout. ID=%s",
            transfer_id,
        )

        return {
            "success": False,
            "uncertain": True,
            "status": "PROCESSING",
            "transfer_id": transfer_id,
            "reference": None,
            "message": (
                "Transfer status check timed out."
            ),
        }

    except requests.RequestException:

        logger.exception(
            "Transfer status request failed. ID=%s",
            transfer_id,
        )

        return {
            "success": False,
            "uncertain": True,
            "status": "PROCESSING",
            "transfer_id": transfer_id,
            "reference": None,
            "message": (
                "Unable to confirm transfer status."
            ),
        }

    data = _json(response)

    if not isinstance(data, dict):

        return {
            "success": False,
            "uncertain": True,
            "status": "PROCESSING",
            "transfer_id": transfer_id,
            "reference": None,
            "message": (
                "Invalid Flutterwave response."
            ),
        }

    if response.status_code != 200:

        logger.error(
            "Transfer status HTTP failure. "
            "ID=%s HTTP=%s",
            transfer_id,
            response.status_code,
        )

        return {
            "success": False,
            "uncertain": True,
            "status": "PROCESSING",
            "transfer_id": transfer_id,
            "reference": None,
            "message": (
                "Transfer status could not be confirmed."
            ),
        }

    result = _extract_result(data)

    transfer_status = str(
        result.get("status") or ""
    ).upper()

    reference = str(
        result.get("reference") or ""
    ).strip()

    actual_transfer_id = result.get(
        "id",
        transfer_id
    )

    message = str(
        result.get("message")
        or data.get("message")
        or ""
    )[:300]

    if transfer_status in TRANSFER_FINAL_SUCCESS:

        return {
            "success": True,
            "uncertain": False,
            "status": transfer_status,
            "transfer_id": actual_transfer_id,
            "reference": reference,
            "message": message
            or "Transfer successful.",
        }

    if transfer_status in TRANSFER_FINAL_FAILED:

        return {
            "success": False,
            "uncertain": False,
            "status": transfer_status,
            "transfer_id": actual_transfer_id,
            "reference": reference,
            "message": message
            or "Transfer failed.",
        }

    return {
        "success": False,
        "uncertain": True,
        "status": transfer_status
        or "PROCESSING",
        "transfer_id": actual_transfer_id,
        "reference": reference,
        "message": message
        or "Transfer is still being processed.",
    }


# ==========================================================
# GET TRANSFER STATUS BY REFERENCE
# ==========================================================

def get_flutterwave_transfer_status_by_reference(
    reference
):

    reference = str(
        reference or ""
    ).strip()

    if not reference:
        raise ValueError(
            "Transfer reference is required."
        )

    try:

        response = requests.get(
            FLW_TRANSFER_URL,
            headers=_headers(),
            params={
                "reference": reference
            },
            timeout=FLW_TIMEOUT,
        )

    except requests.Timeout:

        logger.warning(
            "Transfer reference lookup timeout. "
            "Reference=%s",
            reference,
        )

        return {
            "success": False,
            "uncertain": True,
            "status": "PROCESSING",
            "transfer_id": None,
            "reference": reference,
            "message": (
                "Transfer status check timed out."
            ),
        }

    except requests.RequestException:

        logger.exception(
            "Transfer reference lookup failed. "
            "Reference=%s",
            reference,
        )

        return {
            "success": False,
            "uncertain": True,
            "status": "PROCESSING",
            "transfer_id": None,
            "reference": reference,
            "message": (
                "Unable to confirm transfer status."
            ),
        }

    data = _json(response)

    if not isinstance(data, dict):

        return {
            "success": False,
            "uncertain": True,
            "status": "PROCESSING",
            "transfer_id": None,
            "reference": reference,
            "message": (
                "Invalid Flutterwave response."
            ),
        }

    if response.status_code != 200:

        logger.error(
            "Transfer reference lookup HTTP failure. "
            "Reference=%s HTTP=%s",
            reference,
            response.status_code,
        )

        return {
            "success": False,
            "uncertain": True,
            "status": "PROCESSING",
            "transfer_id": None,
            "reference": reference,
            "message": (
                "Transfer status could not be confirmed."
            ),
        }

    result = data.get("data")

    if not isinstance(result, list):

        return {
            "success": False,
            "uncertain": True,
            "status": "PROCESSING",
            "transfer_id": None,
            "reference": reference,
            "message": (
                "Transfer status could not be confirmed."
            ),
        }

    # ------------------------------------------------------
    # FIND EXACT REFERENCE
    # ------------------------------------------------------

    transfer = None

    for item in result:

        if not isinstance(item, dict):
            continue

        item_reference = str(
            item.get("reference") or ""
        ).strip()

        if item_reference == reference:

            transfer = item
            break

    # ------------------------------------------------------
    # NOT FOUND
    # ------------------------------------------------------

    if not transfer:

        # IMPORTANT:
        # "Not found" does NOT mean failed.
        # Keep withdrawal processing.
        return {
            "success": False,
            "uncertain": True,
            "status": "PROCESSING",
            "transfer_id": None,
            "reference": reference,
            "message": (
                "Transfer was not found yet. "
                "Keep checking the status."
            ),
        }

    transfer_status = str(
        transfer.get("status") or ""
    ).upper()

    transfer_id = transfer.get("id")

    message = str(
        transfer.get("message")
        or ""
    )[:300]

    if transfer_status in TRANSFER_FINAL_SUCCESS:

        return {
            "success": True,
            "uncertain": False,
            "status": transfer_status,
            "transfer_id": transfer_id,
            "reference": reference,
            "message": message
            or "Transfer successful.",
        }

    if transfer_status in TRANSFER_FINAL_FAILED:

        return {
            "success": False,
            "uncertain": False,
            "status": transfer_status,
            "transfer_id": transfer_id,
            "reference": reference,
            "message": message
            or "Transfer failed.",
        }

    return {
        "success": False,
        "uncertain": True,
        "status": transfer_status
        or "PROCESSING",
        "transfer_id": transfer_id,
        "reference": reference,
        "message": message
        or "Transfer is still being processed.",
    }


# ==========================================================
# GET FLUTTERWAVE BANKS
# ==========================================================

def get_flutterwave_banks(country="NG"):

    country = str(
        country or "NG"
    ).strip().upper()

    if not re.fullmatch(
        r"[A-Z]{2}",
        country
    ):

        raise ValueError(
            "Invalid country code."
        )

    url = (
        f"{FLW_BANKS_URL}/"
        f"{country}"
    )

    try:

        response = requests.get(
            url,
            headers=_headers(),
            timeout=FLW_TIMEOUT,
        )

    except requests.Timeout:

        logger.warning(
            "Bank list request timed out."
        )

        return []

    except requests.RequestException:

        logger.exception(
            "Bank list request failed."
        )

        return []

    data = _json(response)

    if (
        response.status_code != 200
        or not isinstance(data, dict)
    ):

        return []

    if str(
        data.get("status", "")
    ).lower() != "success":

        return []

    banks = data.get("data")

    if not isinstance(banks, list):
        return []

    clean_banks = []

    for bank in banks:

        if not isinstance(bank, dict):
            continue

        code = str(
            bank.get("code") or ""
        ).strip()

        name = str(
            bank.get("name") or ""
        ).strip()

        if not code or not name:
            continue

        clean_banks.append({
            "code": code,
            "name": name,
        })

    return clean_banks