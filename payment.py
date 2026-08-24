GA payment.py

# ==========================================================
# ALHIKAM LEARNING CENTER V2
# payment.py
# FLUTTERWAVE PAYMENT
# ==========================================================

import uuid
import requests
from urllib.parse import urlencode

from config import (
    APP_URL,
    FLW_SECRET_KEY,
    PAYMENT_PLANS,
)


FLUTTERWAVE_PAYMENT_URL = (
    "https://api.flutterwave.com/v3/payments"
)

FLUTTERWAVE_VERIFY_URL = (
    "https://api.flutterwave.com/v3/transactions/{}/verify"
)


# ==========================================================
# PAYMENT HTML
# ==========================================================

PAYMENT_HTML = """

<!DOCTYPE html>

<html>

<head>

<meta name="viewport"
      content="width=device-width, initial-scale=1">

<title>ALHIKAM Payment</title>

<style>

body{
    font-family:Arial,sans-serif;
    background:#f5f5f5;
    padding:20px;
}

.container{
    max-width:550px;
    margin:auto;
    background:white;
    padding:25px;
    border-radius:15px;
    box-shadow:0 4px 12px rgba(0,0,0,.1);
}

h2{
    text-align:center;
    color:#087f5b;
}

.info{
    background:#fff8e1;
    padding:14px;
    border-radius:10px;
    margin-bottom:20px;
}

.referral{
    background:#f0f8f5;
    padding:14px;
    border-radius:10px;
    margin-bottom:20px;
}

.plan{
    border:1px solid #ddd;
    padding:15px;
    margin-bottom:12px;
    border-radius:10px;
}

.plan label{
    display:block;
    cursor:pointer;
}

.plan input{
    width:auto;
    margin-right:8px;
}

.referral input{
    width:100%;
    padding:14px;
    margin-top:8px;
    box-sizing:border-box;
    border:1px solid #ccc;
    border-radius:8px;
}

button{
    width:100%;
    padding:15px;
    background:#087f5b;
    color:white;
    border:none;
    border-radius:10px;
    font-size:18px;
    font-weight:bold;
    cursor:pointer;
}

button:hover{
    opacity:.9;
}

.telegram{
    background:#e8f4ff;
    padding:14px;
    border-radius:10px;
    margin-bottom:20px;
}

</style>

</head>

<body>

<div class="container">

<h2>
🎓 ALHIKAM Learning Center
</h2>


<div class="telegram">

<b>📱 Telegram Connected</b>

<br><br>

Your Telegram account will be connected
to your ALHIKAM registration automatically.

</div>


<div class="info">

<b>Choose your subscription plan.</b>

<br><br>

After successful payment, you will be
redirected automatically to registration.

</div>


<form method="POST"
      action="/create-payment">


<!-- TELEGRAM DATA -->

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


<!-- REFERRAL -->

<div class="referral">

<label>
<b>🔗 Referral Code</b>
</label>

<input
type="text"
name="referral_code"
value="{{ referral_code }}"
placeholder="Enter referral code if you have one"
>

{% if referral_code %}

<br>

<div>

✅ Referral code detected:

<b>
{{ referral_code }}
</b>

</div>

{% endif %}

</div>


<!-- PLAN 1 -->

<div class="plan">

<label>

<input
type="radio"
name="plan"
value="1"
required
>

<b>1 Month</b>

— ₦3,600

</label>

</div>


<!-- PLAN 2 -->

<div class="plan">

<label>

<input
type="radio"
name="plan"
value="2"
>

<b>2 Months</b>

— ₦6,800

</label>

</div>


<!-- PLAN 3 -->

<div class="plan">

<label>

<input
type="radio"
name="plan"
value="3"
>

<b>3 Months</b>

— ₦10,000

</label>

</div>


<!-- PLAN 4 -->

<div class="plan">

<label>

<input
type="radio"
name="plan"
value="4"
>

<b>4 Months</b>

— ₦13,600

</label>

</div>


<!-- PLAN 5 -->

<div class="plan">

<label>

<input
type="radio"
name="plan"
value="5"
>

<b>5 Months</b>

— ₦16,500

</label>

</div>


<!-- PLAN 6 -->

<div class="plan">

<label>

<input
type="radio"
name="plan"
value="6"
>

<b>6 Months</b>

— ₦20,000

</label>

</div>


<button type="submit">

💳 Continue to Payment

</button>

</form>

</div>

</body>

</html>

"""


# ==========================================================
# GENERATE TRANSACTION REFERENCE
# ==========================================================

def generate_tx_ref():

    return (
        "ALHIKAM_"
        + uuid.uuid4().hex
    )


# ==========================================================
# CREATE FLUTTERWAVE PAYMENT
# ==========================================================

def create_flutterwave_payment(
    plan_id,
    app_url=None,
    referral_code="",
    telegram_id="",
    telegram_name="",
    telegram_username="",
):

    if not FLW_SECRET_KEY:

        print(
            "ERROR: FLW_SECRET_KEY is not configured."
        )

        return None


    # ------------------------------------------------------
    # Validate plan
    # ------------------------------------------------------

    if plan_id not in PAYMENT_PLANS:

        print(
            "ERROR: Invalid payment plan:",
            plan_id
        )

        return None


    payment_plan, amount = PAYMENT_PLANS[
        plan_id
    ]


    # ------------------------------------------------------
    # Generate TX reference
    # ------------------------------------------------------

    tx_ref = generate_tx_ref()


    # ------------------------------------------------------
    # APP URL
    # ------------------------------------------------------

    base_url = (
        app_url
        or APP_URL
    ).rstrip("/")


    # ------------------------------------------------------
    # Callback URL
    #
    # Telegram data is included so it can be recovered
    # after Flutterwave redirects the student.
    # ------------------------------------------------------

    callback_params = {

        "telegram_id":
            telegram_id or "",

        "telegram_name":
            telegram_name or "",

        "telegram_username":
            telegram_username or "",

    }


    callback_url = (

        f"{base_url}/payment-callback?"

        + urlencode(
            callback_params
        )

    )


    # ------------------------------------------------------
    # PAYMENT PAYLOAD
    # ------------------------------------------------------

    payload = {

        "tx_ref":
            tx_ref,

        "amount":
            amount,

        "currency":
            "NGN",

        "redirect_url":
            callback_url,

        "customer": {

            "email":
                "student@alhikam.ng",

            "name":
                telegram_name
                or "ALHIKAM Student",

        },

        "customizations": {

            "title":
                "ALHIKAM Learning Center",

            "description":
                payment_plan,

        },

        "meta": {

            "payment_plan":
                payment_plan,

            "referral_code":
                referral_code
                or "",

            "telegram_id":
                telegram_id
                or "",

            "telegram_name":
                telegram_name
                or "",

            "telegram_username":
                telegram_username
                or "",

        },

    }


    headers = {

        "Authorization":
            f"Bearer {FLW_SECRET_KEY}",

        "Content-Type":
            "application/json",

    }


    # ------------------------------------------------------
    # SEND REQUEST
    # ------------------------------------------------------

    try:

        response = requests.post(

            FLUTTERWAVE_PAYMENT_URL,

            json=payload,

            headers=headers,

            timeout=30,

        )


        print(
            "Flutterwave create response:",
            response.text
        )


        if response.status_code != 200:

            print(
                "Flutterwave HTTP error:",
                response.status_code
            )

            return None


        data = response.json()


        if data.get(
            "status"
        ) != "success":

            print(
                "Flutterwave returned failure:",
                data
            )

            return None


        payment_link = (

            data.get(
                "data",
                {}
            ).get(
                "link"
            )

        )


        if not payment_link:

            print(
                "ERROR: Flutterwave payment link missing."
            )

            return None


        return {

            "tx_ref":
                tx_ref,

            "amount":
                amount,

            "plan":
                payment_plan,

            "payment_link":
                payment_link,

        }


    except requests.RequestException as e:

        print(
            "Flutterwave request error:",
            e
        )

        return None


    except Exception as e:

        print(
            "Flutterwave payment error:",
            e
        )

        return None


# ==========================================================
# VERIFY FLUTTERWAVE PAYMENT
# ==========================================================

def verify_flutterwave_payment(
    transaction_id
):

    if not FLW_SECRET_KEY:

        print(
            "ERROR: FLW_SECRET_KEY is not configured."
        )

        return None


    if not transaction_id:

        print(
            "ERROR: Transaction ID is missing."
        )

        return None


    url = (
        FLUTTERWAVE_VERIFY_URL.format(
            transaction_id
        )
    )


    headers = {

        "Authorization":
            f"Bearer {FLW_SECRET_KEY}",

        "Content-Type":
            "application/json",

    }


    try:

        response = requests.get(

            url,

            headers=headers,

            timeout=30,

        )


        print(
            "Flutterwave verify response:",
            response.text
        )


        if response.status_code != 200:

            print(
                "Flutterwave verification HTTP error:",
                response.status_code
            )

            return None


        result = response.json()


        if result.get(
            "status"
        ) != "success":

            print(
                "Flutterwave verification failed:",
                result
            )

            return None


        payment_data = result.get(
            "data"
        )


        if not payment_data:

            print(
                "ERROR: Flutterwave verification data missing."
            )

            return None


        return payment_data


    except requests.RequestException as e:

        print(
            "Flutterwave verification request error:",
            e
        )

        return None


    except Exception as e:

        print(
            "Flutterwave verification error:",
            e
        )

        return None