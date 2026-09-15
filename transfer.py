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
# - Never expose full bank account numbers in logs.
# - If Flutterwave says a reference already exists,
#   verify the existing transfer instead of creating a duplicate.
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

# Wallet balance endpoint
FLW_BALANCES_URL = (
    "https://api.flutterwave.com/v3/balances"
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

            message = (
                data.get("complete_message")
                or data.get("response_message")
                or data.get("message")
            )

            if message:
                return str(message)[:300]

        if response is not None:

            return (
                f"Flutterwave HTTP status "
                f"{response.status_code}"
            )

    except Exception:
        pass

    return (
        "Flutterwave transfer request "
        "could not be completed."
    )


# ==========================================================
# TRANSFER MESSAGE EXTRACTOR
# ==========================================================

def _transfer_message(data=None, result=None):

    """
    Extract the most useful Flutterwave transfer message.

    Priority:

        result.complete_message
        result.response_message
        result.message
        data.complete_message
        data.response_message
        data.message
    """

    try:

        if isinstance(result, dict):

            message = (
                result.get("complete_message")
                or result.get("response_message")
                or result.get("message")
            )

            if message:
                return str(message)[:300]

        if isinstance(data, dict):

            message = (
                data.get("complete_message")
                or data.get("response_message")
                or data.get("message")
            )

            if message:
                return str(message)[:300]

    except Exception:

        logger.exception(
            "Unable to extract Flutterwave transfer message."
        )

    return ""


# ==========================================================
# JSON RESPONSE
# ==========================================================

def _json(response):

    try:

        return response.json()

    except (ValueError, requests.exceptions.JSONDecodeError):

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
# FLUTTERWAVE NGN WALLET DIAGNOSTIC
# ==========================================================

def get_flutterwave_ngn_balance():

    """
    Diagnostic function only.

    Checks the NGN wallet balance visible to the
    Flutterwave API key configured in the application.

    This function DOES NOT create a transfer.

    It also NEVER logs or returns the secret key.
    """

    try:

        response = requests.get(
            FLW_BALANCES_URL,
            headers=_headers(),
            timeout=FLW_TIMEOUT,
        )

    except requests.Timeout:

        logger.warning(
            "Flutterwave wallet balance request timed out."
        )

        return {
            "success": False,
            "message": (
                "Flutterwave wallet balance "
                "request timed out."
            ),
        }

    except requests.RequestException:

        logger.exception(
            "Flutterwave wallet balance request failed."
        )

        return {
            "success": False,
            "message": (
                "Unable to fetch Flutterwave "
                "wallet balance."
            ),
        }

    data = _json(response)

    if response.status_code != 200:

        logger.error(
            "Flutterwave wallet balance failed. HTTP=%s",
            response.status_code,
        )

        return {
            "success": False,
            "message": _safe_message(
                response=response,
                data=data,
            ),
        }

    if not isinstance(data, dict):

        return {
            "success": False,
            "message": (
                "Invalid Flutterwave wallet response."
            ),
        }

    provider_status = str(
        data.get("status", "")
    ).lower()

    if provider_status != "success":

        return {
            "success": False,
            "message": _safe_message(
                response=response,
                data=data,
            ),
        }

    wallets = data.get("data")

    if not isinstance(wallets, list):

        return {
            "success": False,
            "message": (
                "Flutterwave returned an invalid "
                "wallet list."
            ),
        }

    ngn_wallet = None

    for wallet in wallets:

        if not isinstance(wallet, dict):
            continue

        currency = str(
            wallet.get("currency") or ""
        ).strip().upper()

        if currency == "NGN":

            ngn_wallet = wallet
            break

    if not ngn_wallet:

        logger.warning(
            "Flutterwave API did not return an NGN wallet."
        )

        return {
            "success": False,
            "message": "NGN wallet was not found.",
        }

    available_balance = ngn_wallet.get(
        "available_balance"
    )

    ledger_balance = ngn_wallet.get(
        "ledger_balance"
    )

    logger.info(
        "Flutterwave API NGN wallet: "
        "available_balance=%s ledger_balance=%s",
        available_balance,
        ledger_balance,
    )

    return {
        "success": True,
        "currency": "NGN",
        "available_balance": available_balance,
        "ledger_balance": ledger_balance,
    }


# ==========================================================
# SAFE TRANSFER RESPONSE LOG
# ==========================================================

def _log_transfer_response(
    response,
    data,
    reference,
):

    """
    Log useful transfer information without logging
    account numbers, authorization headers, or full payloads.
    """

    try:

        result = _extract_result(data)

        logger.info(
            "Flutterwave transfer response: "
            "HTTP=%s reference=%s provider_status=%s "
            "transfer_status=%s transfer_id=%s message=%s",
            response.status_code
            if response is not None
            else None,
            reference,
            (
                data.get("status")
                if isinstance(data, dict)
                else None
            ),
            (
                result.get("status")
                if isinstance(result, dict)
                else None
            ),
            (
                result.get("id")
                if isinstance(result, dict)
                else None
            ),
            _transfer_message(
                data=data,
                result=result,
            ),
        )

    except Exception:

        logger.exception(
            "Unable to log Flutterwave transfer response."
        )


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
            _safe_message(
                response=response,
                data=data,
            )
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

        # IMPORTANT:
        # Do not assume transfer failed.

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

    # Log safe details BEFORE processing the response.

    _log_transfer_response(
        response=response,
        data=data,
        reference=reference,
    )

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

    # ------------------------------------------------------
    # REAL PROVIDER MESSAGE
    # ------------------------------------------------------

    message = _transfer_message(
        data=data,
        result=result,
    )

    # ------------------------------------------------------
    # DUPLICATE REFERENCE
    # ------------------------------------------------------

    duplicate_reference = (
        "already exists"
        in message.lower()
        or
        "payout with this ref already exists"
        in message.lower()
    )

    if (
        response.status_code in (400, 409)
        and duplicate_reference
    ):

        logger.warning(
            "Flutterwave says transfer reference already "
            "exists. Verifying existing transfer. "
            "Reference=%s",
            reference,
        )

        existing = (
            get_flutterwave_transfer_status_by_reference(
                reference
            )
        )

        # Make sure the lookup still belongs to the
        # exact reference we requested.

        existing_reference = str(
            existing.get("reference") or ""
        ).strip()

        if existing_reference == reference:

            logger.info(
                "Existing Flutterwave transfer found "
                "for reference=%s status=%s "
                "transfer_id=%s",
                reference,
                existing.get("status"),
                existing.get("transfer_id"),
            )

            return existing

        # If Flutterwave cannot confirm the exact
        # existing transfer, DO NOT create another one.

        return {
            "success": False,
            "uncertain": True,
            "status": "PROCESSING",
            "transfer_id": None,
            "reference": reference,
            "message": (
                "A transfer with this reference already "
                "exists, but its status could not be "
                "confirmed. Please check again."
            ),
            "account_name": verified_account_name,
        }

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
            "message": (
                message
                or "Transfer successful."
            ),
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
            "message": (
                message
                or "Transfer failed."
            ),
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
            "message": (
                message
                or "Transfer is being processed."
            ),
            "account_name": verified_account_name,
        }

    # ------------------------------------------------------
    # PROVIDER ACCEPTED REQUEST BUT STATUS UNKNOWN
    # ------------------------------------------------------

    if provider_status == "success":

        return {
            "success": False,
            "uncertain": True,
            "status": (
                transfer_status
                or "PROCESSING"
            ),
            "transfer_id": transfer_id,
            "reference": reference,
            "message": (
                message
                or
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
        "reference=%s status=%s message=%s",
        reference,
        transfer_status,
        message,
    )

    return {
        "success": False,
        "uncertain": True,
        "status": (
            transfer_status
            or "PROCESSING"
        ),
        "transfer_id": transfer_id,
        "reference": reference,
        "message": (
            message
            or
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

    # Safe status logging.

    logger.info(
        "Flutterwave transfer status response: "
        "ID=%s provider_status=%s transfer_status=%s "
        "reference=%s message=%s",
        transfer_id,
        data.get("status"),
        result.get("status"),
        result.get("reference"),
        _transfer_message(
            data=data,
            result=result,
        ),
    )

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

    message = _transfer_message(
        data=data,
        result=result,
    )

    if transfer_status in TRANSFER_FINAL_SUCCESS:

        return {
            "success": True,
            "uncertain": False,
            "status": transfer_status,
            "transfer_id": actual_transfer_id,
            "reference": reference,
            "message": (
                message
                or "Transfer successful."
            ),
        }

    if transfer_status in TRANSFER_FINAL_FAILED:

        return {
            "success": False,
            "uncertain": False,
            "status": transfer_status,
            "transfer_id": actual_transfer_id,
            "reference": reference,
            "message": (
                message
                or "Transfer failed."
            ),
        }

    return {
        "success": False,
        "uncertain": True,
        "status": (
            transfer_status
            or "PROCESSING"
        ),
        "transfer_id": actual_transfer_id,
        "reference": reference,
        "message": (
            message
            or "Transfer is still being processed."
        ),
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

    message = _transfer_message(
        data=data,
        result=transfer,
    )

    logger.info(
        "Flutterwave transfer reference response: "
        "reference=%s provider_status=%s "
        "transfer_status=%s transfer_id=%s message=%s",
        reference,
        data.get("status"),
        transfer_status,
        transfer_id,
        message,
    )

    if transfer_status in TRANSFER_FINAL_SUCCESS:

        return {
            "success": True,
            "uncertain": False,
            "status": transfer_status,
            "transfer_id": transfer_id,
            "reference": reference,
            "message": (
                message
                or "Transfer successful."
            ),
        }

    if transfer_status in TRANSFER_FINAL_FAILED:

        return {
            "success": False,
            "uncertain": False,
            "status": transfer_status,
            "transfer_id": transfer_id,
            "reference": reference,
            "message": (
                message
                or "Transfer failed."
            ),
        }

    return {
        "success": False,
        "uncertain": True,
        "status": (
            transfer_status
            or "PROCESSING"
        ),
        "transfer_id": transfer_id,
        "reference": reference,
        "message": (
            message
            or "Transfer is still being processed."
        ),
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