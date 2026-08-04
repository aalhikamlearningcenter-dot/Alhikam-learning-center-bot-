import os
import uuid
import requests
from flask import request, redirect

PAYMENT_PLANS = {
    "1": {"name": "1 Month", "amount": 3600},
    "2": {"name": "2 Months", "amount": 6800},
    "3": {"name": "3 Months", "amount": 10000},
    "4": {"name": "4 Months", "amount": 13200},
    "5": {"name": "5 Months", "amount": 16500},
    "6": {"name": "6 Months", "amount": 20000},
}

FLW_PUBLIC_KEY = os.getenv("FLW_PUBLIC_KEY")
FLW_SECRET_KEY = os.getenv("FLW_SECRET_KEY")

pending_payments = {}

PAYMENT_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
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
text-align:center;
color:#087f5b;
}

select{
width:100%;
padding:15px;
margin-top:15px;
border-radius:10px;
}

button{
width:100%;
padding:15px;
margin-top:20px;
background:#087f5b;
color:white;
border:none;
border-radius:10px;
font-size:18px;
font-weight:bold;
cursor:pointer;
}

</style>

</head>

<body>

<div class="container">

<h2>🎓 ALHIKAM Learning Center</h2>

<form action="/create-payment" method="POST">

<select name="plan" required>

<option value="">Select Subscription</option>

<option value="1">1 Month — ₦3,600</option>

<option value="2">2 Months — ₦6,800</option>

<option value="3">3 Months — ₦10,000</option>

<option value="4">4 Months — ₦13,200</option>

<option value="5">5 Months — ₦16,500</option>

<option value="6">6 Months — ₦20,000</option>

</select>

<button type="submit">

Continue To Payment

</button>

</form>

</div>

</body>

</html>
"""
def create_flutterwave_payment(plan_id, app_url):

    if plan_id not in PAYMENT_PLANS:
        return None

    plan = PAYMENT_PLANS[plan_id]

    tx_ref = f"ALHIKAM_{uuid.uuid4().hex}"

    payload = {
        "tx_ref": tx_ref,
        "amount": plan["amount"],
        "currency": "NGN",
        "redirect_url": f"{app_url}/payment-callback",
        "customer": {
            "email": f"{tx_ref}@alhikam.com",
            "name": "ALHIKAM Student",
        },
        "customizations": {
            "title": "ALHIKAM Learning Center",
            "description": plan["name"],
        },
    }

    headers = {
        "Authorization": f"Bearer {FLW_SECRET_KEY}",
        "Content-Type": "application/json",
    }

    response = requests.post(
        "https://api.flutterwave.com/v3/payments",
        json=payload,
        headers=headers,
        timeout=30,
    )

    if response.status_code != 200:
        return None

    data = response.json()

    if data.get("status") != "success":
    return None

pending_payments[tx_ref] = {
    "plan_id": plan_id,
    "plan": plan,
    "status": "pending",
}

return {
    "tx_ref": tx_ref,
    "payment_link": data["data"]["link"],
}

    return {
        "tx_ref": tx_ref,
        "payment_link": data["data"]["link"],
    }

def verify_flutterwave_payment(transaction_id):

    headers = {
        "Authorization": f"Bearer {FLW_SECRET_KEY}",
    }

    response = requests.get(
        f"https://api.flutterwave.com/v3/transactions/{transaction_id}/verify",
        headers=headers,
        timeout=30,
    )

    if response.status_code != 200:
        return None

    result = response.json()

    if result.get("status") != "success":
        return None

    return result["data"]