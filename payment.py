# ==========================================================
# ALHIKAM LEARNING CENTER V2
# payment.py
# FLUTTERWAVE PAYMENT
# ==========================================================

import os
import uuid
import requests


# ==========================================================
# PAYMENT PLANS
# ==========================================================

PAYMENT_PLANS = {

    "1": {
        "name": "1 Month",
        "amount": 3600
    },

    "2": {
        "name": "2 Months",
        "amount": 6800
    },

    "3": {
        "name": "3 Months",
        "amount": 10000
    },

    "4": {
        "name": "4 Months",
        "amount": 13600
    },

    "5": {
        "name": "5 Months",
        "amount": 16500
    },

    "6": {
        "name": "6 Months",
        "amount": 20000
    },

}


# ==========================================================
# SECRET KEY
# ==========================================================

FLW_SECRET_KEY = os.getenv("FLW_SECRET_KEY")


# ==========================================================
# PAYMENT PAGE
# ==========================================================

PAYMENT_HTML = """

<!DOCTYPE html>

<html>

<head>

<meta name="viewport"
content="width=device-width, initial-scale=1">

<title>ALHIKAM Learning Center</title>

<style>

body{
    font-family:Arial,sans-serif;
    background:#f4f7f6;
    padding:20px;
}

.container{
    max-width:500px;
    margin:auto;
    background:white;
    padding:25px;
    border-radius:15px;
    box-shadow:0 4px 12px rgba(0,0,0,.1);
}

h2{
    color:#087f5b;
    text-align:center;
}

select{
    width:100%;
    padding:15px;
    margin-top:15px;
    border-radius:10px;
    border:1px solid #ccc;
    box-sizing:border-box;
}

button{
    width:100%;
    padding:15px;
    margin-top:15px;
    border-radius:10px;
    border:none;
    background:#087f5b;
    color:white;
    font-size:18px;
    font-weight:bold;
}

.referral{
    background:#f0f8f5;
    padding:12px;
    border-radius:10px;
    margin-top:15px;
    font-size:14px;
}

</style>

</head>

<body>

<div class="container">

<h2>
🎓 ALHIKAM Learning Center
</h2>

{% if referral_code %}

<div class="referral">

🔗 Referral Code:

<b>{{ referral_code }}</b>

<br><br>

✅ Referral has been recorded.

</div>

{% endif %}

<form action="/create-payment"
method="POST">

<input
type="hidden"
name="referral_code"
value="{{ referral_code }}"
>

<input
type="hidden"
name="telegram_id"
value="{{ telegram_id }}"
>

<input
type="hidden"
name="telegram_name"
value="{{ telegram_name }}"
>

<input
type="hidden"
name="telegram_username"
value="{{ telegram_username }}"
>

<select name="plan" required>

<option value="">
Select Subscription
</option>

<option value="1">
1 Month — ₦3,600
</option>

<option value="2">
2 Months — ₦6,800
</option>

<option value="3">
3 Months — ₦10,000
</option>

<option value="4">
4 Months — ₦13,600
</option>

<option value="5">
5 Months — ₦16,500
</option>

<option value="6">
6 Months — ₦20,000
</option>

</select>

<button type="submit">
Continue To Payment
</button>

</form>

</div>

</body>

</html>

"""


# ==========================================================
# CREATE PAYMENT
# ==========================================================

def create_flutterwave_payment(
    plan_id,
    app_url,
    referral_code="",
    telegram_id="",
    telegram_name="",
    telegram_username=""
):

    if plan_id not in PAYMENT_PLANS:
        return None

    if not FLW_SECRET_KEY:
        print("ERROR: FLW_SECRET_KEY is not set.")
        return None

    if not app_url:
        print("ERROR: APP_URL is not set.")
        return None

    plan = PAYMENT_PLANS[plan_id]

    tx_ref = (
        "ALHIKAM_" +
        uuid.uuid4().hex
    )

    referral_code = (
        referral_code or ""
    ).strip()

    payload = {

        "tx_ref": tx_ref,

        "amount": plan["amount"],

        "currency": "NGN",

        "redirect_url":
            f"{app_url}/payment-callback",

        "customer": {

            "email":
                f"{tx_ref.lower()}@alhikam.com",

            "name":
                "ALHIKAM Student"

        },

        "customizations": {

            "title":
                "ALHIKAM Learning Center",

            "description":
                plan["name"]

        },

        "meta": {

            "referral_code":
                referral_code,

            "payment_plan":
                plan["name"],

            "plan_id":
                plan_id,

            "telegram_id":
                str(telegram_id or ""),

            "telegram_name":
                telegram_name or "",

            "telegram_username":
                telegram_username or ""

        }

    }

    headers = {

        "Authorization":
            f"Bearer {FLW_SECRET_KEY}",

        "Content-Type":
            "application/json"

    }

    try:

        response = requests.post(

            "https://api.flutterwave.com/v3/payments",

            json=payload,

            headers=headers,

            timeout=30

        )

    except Exception as e:

        print(
            "Flutterwave request error:",
            e
        )

        return None

    if response.status_code not in (200, 201):

        print(
            "Flutterwave HTTP Error:",
            response.status_code
        )

        print(response.text)

        return None

    try:

        result = response.json()

    except Exception as e:

        print(
            "Flutterwave JSON Error:",
            e
        )

        return None

    if result.get("status") != "success":

        print(
            "Flutterwave Payment Error:",
            result
        )

        return None

    payment_link = (
        result
        .get("data", {})
        .get("link")
    )

    if not payment_link:

        print(
            "Flutterwave did not return payment link."
        )

        return None

    return {

        "tx_ref":
            tx_ref,

        "payment_link":
            payment_link,

        "plan":
            plan["name"],

        "amount":
            plan["amount"],

        "referral_code":
            referral_code,

        "telegram_id":
            str(telegram_id or ""),

        "telegram_name":
            telegram_name or "",

        "telegram_username":
            telegram_username or ""

    }


# ==========================================================
# VERIFY PAYMENT
# ==========================================================

def verify_flutterwave_payment(
    transaction_id
):

    if not FLW_SECRET_KEY:

        print(
            "ERROR: FLW_SECRET_KEY is not set."
        )

        return None

    if not transaction_id:
        return None

    headers = {

        "Authorization":
            f"Bearer {FLW_SECRET_KEY}",

        "Content-Type":
            "application/json"

    }

    url = (
        "https://api.flutterwave.com/v3/"
        f"transactions/{transaction_id}/verify"
    )

    try:

        response = requests.get(

            url,

            headers=headers,

            timeout=30

        )

    except Exception as e:

        print(
            "Flutterwave verification error:",
            e
        )

        return None

    if response.status_code != 200:

        print(
            "Verification HTTP Error:",
            response.status_code
        )

        print(response.text)

        return None

    try:

        result = response.json()

    except Exception as e:

        print(
            "Verification JSON Error:",
            e
        )

        return None

    if result.get("status") != "success":

        print(
            "Verification failed:",
            result
        )

        return None

    data = result.get("data")

    if not data:
        return None

    if data.get("currency") != "NGN":

        print(
            "Invalid payment currency."
        )

        return None

    if data.get("status") != "successful":

        print(
            "Payment is not successful."
        )

        return None

    return data