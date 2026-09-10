============================================================

ALHIKAM LEARNING CENTER V2

Flutterwave Payment

Secure Payment Verification

Telegram Login

Student Registration

Google Sheets

Unique Telegram Invite

Referral / Commission

Withdrawal

Admin Referral Dashboard

============================================================

import os
import uuid
import hmac
import hashlib
import asyncio
import threading
import requests
import logging
import secrets
import time

from datetime import datetime, timedelta, timezone
from markupsafe import escape
from decimal import Decimal, InvalidOperation

from flask import (
Flask,
request,
jsonify,
render_template_string,
redirect,
url_for,
session,
)

from telegram import (
Update,
ReplyKeyboardMarkup,
InlineKeyboardMarkup,
InlineKeyboardButton,
)

from telegram.ext import (
Application,
CommandHandler,
MessageHandler,
ContextTypes,
filters,
)

from telegram.error import TelegramError

============================================================

DATABASE

============================================================

from database import (
initialize_database,
get_promoter_by_id,
get_promoter_by_referral_code,
save_payment,
get_payment_by_tx_ref,
update_payment_status,
mark_payment_registration_completed,
payment_registration_completed,
commission_exists,
create_commission,
add_student,
create_or_get_student,
get_student_by_tx_ref,
get_withdrawal_by_transfer_id,
get_withdrawal_by_transfer_reference,
process_transfer_result,
)

============================================================

FLUTTERWAVE TRANSFER

============================================================

from transfer import (
get_flutterwave_transfer_status,
get_flutterwave_transfer_status_by_reference,
)

============================================================

REFERRAL DASHBOARD

============================================================

from referral_dashboard import (
promoter_login_page,
promoter_logout as promoter_logout_page,
referral_dashboard_by_code,
withdrawal_page,
withdrawal_status_page,
)

============================================================

ADMIN DASHBOARD

============================================================

try:
from admin_referral import (
admin_referral_page,
admin_login_page,
admin_logout_page,
create_promoter_page,
admin_withdrawal_status_page,
)

ADMIN_MODULE_AVAILABLE = True

except ImportError:

ADMIN_MODULE_AVAILABLE = False

============================================================

INITIALIZE DATABASE

============================================================

initialize_database()

logger = logging.getLogger(name)

============================================================

ENVIRONMENT VARIABLES

============================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")

FLW_SECRET_KEY = os.getenv("FLW_SECRET_KEY")

FLUTTERWAVE_SECRET_HASH = os.getenv(
"FLUTTERWAVE_SECRET_HASH"
)

SHEET_URL = os.getenv(
"SHEET_URL",
"https://script.google.com/macros/s/AKfycbw6LRBGCzMIHcWGEIKXAYXo9bMHxsO_am4a4iSZ4kR58FFA-bj4TcUNy085uTaVRx2z0A/exec",
)

RAILWAY_URL = os.getenv(
"RAILWAY_URL",
"https://precious-trust-production-956b.up.railway.app",
).rstrip("/")

PORT = int(
os.getenv(
"PORT",
"8080"
)
)

============================================================

BASIC CONFIGURATION

============================================================

MAIN_GROUP_ID = -1004384506380

PUBLIC_PAYMENT_PAGE = (
f"{RAILWAY_URL}/pay"
)

TELEGRAM_BOT_USERNAME = (
"Alhikamcenterbot"
)

============================================================

PAYMENT PLANS

============================================================

PAYMENT_PLANS = {

"1": {
"name": "1 Month",
"amount": 3600,
},

"2": {
"name": "2 Months",
"amount": 6800,
},

"3": {
"name": "3 Months",
"amount": 10000,
},

"4": {
"name": "4 Months",
"amount": 13600,
},

"5": {
"name": "5 Months",
"amount": 16500,
},

"6": {
"name": "6 Months",
"amount": 20000,
},

}

============================================================

MEMORY

============================================================

pending_payments = {}

processed_payments = set()

telegram_bot_app = None

============================================================

FLASK

============================================================

web_app = Flask(name)

============================================================

SECRET KEY

============================================================

SECRET_KEY = os.getenv(
"SECRET_KEY"
)

if (
not SECRET_KEY
or len(SECRET_KEY) < 32
):
raise RuntimeError(
"SECRET_KEY must be configured and at least 32 characters long."
)

web_app.secret_key = SECRET_KEY

web_app.config.update(

SESSION_COOKIE_HTTPONLY=True,

SESSION_COOKIE_SAMESITE="Lax",

SESSION_COOKIE_SECURE=(
RAILWAY_URL.startswith("https://")
),

PERMANENT_SESSION_LIFETIME=86400,

)

============================================================

HOME

============================================================

@web_app.route(
"/",
methods=["GET"]
)
def home():

return jsonify({

"status": "online",    

"bot":    
    "ALHIKAM Learning Center Bot",    

"payment_page":    
    PUBLIC_PAYMENT_PAGE,    

"webhook":    
    f"{RAILWAY_URL}/webhook/flutterwave",    

"telegram_login":    
    f"{RAILWAY_URL}/telegram-auth",

})

============================================================

HEALTH CHECK

============================================================

@web_app.route(
"/health",
methods=["GET"]
)
def health():

return jsonify({
"status": "healthy"
})

============================================================

PAYMENT PAGE HTML

============================================================

PAYMENT_PAGE_HTML = """

<!DOCTYPE html>  <html>  <head>  <meta  name="viewport"
content="width=device-width, initial-scale=1"

> 

<title>    
ALHIKAM Learning Center Payment    
</title>  <style>    body{
font-family:Arial,sans-serif;
background:#f4f7f6;
margin:0;
padding:20px;
}

.container{
max-width:520px;
margin:30px auto;
background:white;
padding:25px;
border-radius:16px;
box-shadow:0 4px 18px rgba(0,0,0,.10);
}

h1{
color:#087f5b;
text-align:center;
}

.subtitle{
text-align:center;
color:#555;
margin-bottom:25px;
}

.plan{
border:1px solid #ddd;
border-radius:12px;
padding:15px;
margin:10px 0;
}

.plan label{
display:block;
cursor:pointer;
}

.amount{
font-weight:bold;
font-size:18px;
color:#087f5b;
}

button{
width:100%;
padding:15px;
margin-top:20px;
border:none;
border-radius:10px;
background:#087f5b;
color:white;
font-size:17px;
font-weight:bold;
cursor:pointer;
}

.note{
text-align:center;
font-size:13px;
color:#777;
margin-top:18px;
}

</style>  </head>  <body>  <div class="container">  <h1>
🎓 ALHIKAM Learning Center

</h1>  <div class="subtitle">  Choose your learning duration  
and continue to secure payment.  </div>  <form    
method="POST"    
action="/create-payment"    
>  <input  
type="hidden"  
name="referral_code"  
value="{{ referral_code }}"  > 

{% for key, plan in plans.items() %}

<div class="plan">  <label>  <input  
type="radio"  
name="plan"  
value="{{ key }}"  
required  > 

<strong>    
{{ plan.name }}    
</strong>  <br>  <span class="amount">  ₦{{ "{:,}".format(plan.amount) }}  </span>  </label>  </div>  {% endfor %}

<button
type="submit"

> 

💳 CONTINUE TO SECURE PAYMENT

</button>  </form>  <div class="note">  After successful payment,
you will connect your Telegram account
and complete registration.

</div>  </div>  </body>  </html>  """  ============================================================

PAYMENT PAGE

============================================================

@web_app.route(
"/pay",
methods=["GET"]
)
def payment_page():

referral_code = (
request.args.get(
"ref",
""
)
or ""
).strip()

if (
referral_code
and not get_promoter_by_referral_code(
referral_code
)
):

referral_code = ""

return render_template_string(

PAYMENT_PAGE_HTML,    

plans=PAYMENT_PLANS,    

referral_code=referral_code,

)

============================================================

CREATE PAYMENT

============================================================

@web_app.route(
"/create-payment",
methods=["POST"]
)
def create_payment():

if not FLW_SECRET_KEY:

return (    
    "Payment system is temporarily unavailable.",    
    500    
)

plan_number = (
request.form.get(
"plan"
)
or ""
).strip()

plan = PAYMENT_PLANS.get(
plan_number
)

if not plan:

return (    
    "Invalid payment plan.",    
    400    
)

--------------------------------------------------------

REFERRAL CODE

--------------------------------------------------------

referral_code = (
request.form.get(
"referral_code",
""
)
or ""
).strip()

promoter = None

if referral_code:

promoter = (    
    get_promoter_by_referral_code(    
        referral_code    
    )    
)    


if not promoter:    

    referral_code = ""

--------------------------------------------------------

PAYMENT TOKEN

--------------------------------------------------------

payment_token = uuid.uuid4().hex

tx_ref = (
f"ALHIKAM_{payment_token}"
)

--------------------------------------------------------

PAYMENT RECORD

--------------------------------------------------------

payment = {

"tx_ref": tx_ref,    

"plan": plan_number,    

"plan_name":    
    plan["name"],    

"amount":    
    plan["amount"],    

"status":    
    "pending",    

"payment_status":    
    "Pending",    

"referral_code":    
    referral_code,    

"promoter_id":    
    promoter["id"]    
    if promoter    
    else None,    

"promoter_name":    
    promoter["full_name"]    
    if promoter    
    else "",    

"commission":    
    0,    

"registration_completed":    
    0,

}

pending_payments[
payment_token
] = payment.copy()

--------------------------------------------------------

SAVE INITIAL PAYMENT

--------------------------------------------------------

save_payment(payment)

========================================================

FLUTTERWAVE CHECKOUT

========================================================

payload = {

"tx_ref":    
    tx_ref,    

"amount":    
    plan["amount"],    

"currency":    
    "NGN",    

"redirect_url":    
    f"{RAILWAY_URL}/payment-complete/{payment_token}",    


"customer": {    

    "email":    
        f"student_{payment_token}@alhikam.com",    

    "name":    
        "ALHIKAM Student",    

},    


"customizations": {    

    "title":    
        "ALHIKAM Learning Center",    

    "description":    
        f"{plan['name']} Training",    

    "logo":    
        "",    

},    


# ----------------------------------------------------    
# PAYMENT SESSION CONFIGURATION    
# ----------------------------------------------------    

"configurations": {    

    "session_duration":    
        30,    

    "max_retry_attempt":    
        3,    

},

}

headers = {

"Authorization":    
    f"Bearer {FLW_SECRET_KEY}",    

"Content-Type":    
    "application/json",

}

try:

response = requests.post(    

    "https://api.flutterwave.com/v3/payments",    

    json=payload,    

    headers=headers,    

    timeout=30,    

)    


result = response.json()    


logger.info(    
    "Flutterwave checkout status=%s",    
    response.status_code    
)    


if (    

    response.status_code == 200    

    and result.get("status")    
    == "success"    

):    

    payment_link = (    
        result    
        .get("data", {})    
        .get("link")    
    )    


    if payment_link:    

        return redirect(    
            payment_link    
        )    


logger.error(    
    "Unable to create Flutterwave payment: %s",    
    result    
)    


return (    
    "Unable to create payment link. Please try again.",    
    500    
)

except requests.RequestException:

logger.exception(    
    "Flutterwave payment request failed"    
)    

return (    
    "Payment system error. Please try again later.",    
    500    
)

except Exception:

logger.exception(    
    "Flutterwave payment creation failed"    
)    

return (    
    "Payment system error. Please try again later.",    
    500    
)

============================================================

GET PAYMENT FROM TOKEN

============================================================

def _payment_from_token(payment_token):

if not payment_token:

return None

tx_ref = (
f"ALHIKAM_{payment_token}"
)

row = get_payment_by_tx_ref(
tx_ref
)

========================================================

DATABASE PAYMENT

========================================================

if row:

data = dict(row)    


data["plan_name"] = (    
    data.get("payment_plan")    
    or data.get("plan_name")    
    or ""    
)    


data["amount"] = float(    
    data.get("amount")    
    or 0    
)    


# ----------------------------------------------------    
# IMPORTANT FIX:    
#    
# database.py uses "status",    
# NOT "payment_status".    
# ----------------------------------------------------    

raw_status = (    
    data.get("status")    
    or data.get("payment_status")    
    or ""    
)    


data["status"] = (    
    str(raw_status)    
    .strip()    
    .lower()    
)    


if data["status"] in {    
    "success",    
    "successful",    
    "completed",    
}:    

    data["status"] = (    
        "successful"    
    )    


data["registration_completed"] = int(    
    data.get(    
        "registration_completed"    
    )    
    or 0    
)    


# ----------------------------------------------------    
# TELEGRAM AUTH    
#    
# telegram_name is NOT a database column.    
# Therefore do not read it from DB.    
# ----------------------------------------------------    

if data.get("telegram_id"):    

    data["telegram_auth"] = {    

        "telegram_id":    
            str(    
                data.get(    
                    "telegram_id"    
                )    
            ),    

        "telegram_username":    
            data.get(    
                "telegram_username"    
            )    
            or "",    

        "first_name":    
            "",    

        "last_name":    
            "",    

    }    


return data

========================================================

MEMORY PAYMENT

========================================================

return pending_payments.get(
payment_token
)

============================================================

COMMISSION CALCULATION

============================================================

def _commission_for_amount(amount):

try:

amount = int(    
    Decimal(    
        str(amount)    
    )    
)

except Exception:

return 0

return {

3600: 200,    

6800: 500,    

10000: 800,    

13600: 1200,    

16500: 1800,    

20000: 2500,

}.get(
amount,
0
)

============================================================

FIND FLUTTERWAVE TRANSACTION BY TX REF

============================================================

def find_flutterwave_transaction_by_tx_ref(
tx_ref
):

if not FLW_SECRET_KEY:

logger.error(    
    "FLW_SECRET_KEY is missing."    
)    

return None

tx_ref = str(
tx_ref or ""
).strip()

if not tx_ref:

return None

try:

today = (    
    datetime.now(    
        timezone.utc    
    ).date()    
)    


from_date = (    
    today - timedelta(    
        days=30    
    )    
).isoformat()    


to_date = (    
    today.isoformat()    
)    


response = requests.get(    

    "https://api.flutterwave.com/v3/transactions",    

    headers={    

        "Authorization":    
            f"Bearer {FLW_SECRET_KEY}",    

        "Content-Type":    
            "application/json",    

        "Accept":    
            "application/json",    

    },    

    params={    

        "from":    
            from_date,    

        "to":    
            to_date,    

        "page":    
            1,    

        "tx_ref":    
            tx_ref,    

        "currency":    
            "NGN",    

    },    

    timeout=30,    

)    


logger.info(    

    "Flutterwave tx_ref lookup status=%s tx_ref=%s",    

    response.status_code,    

    tx_ref,    

)    


if response.status_code != 200:    

    logger.error(    

        "Flutterwave tx_ref lookup failed status=%s body=%s",    

        response.status_code,    

        response.text[:1000],    

    )    

    return None    


result = response.json()    

data = result.get(    
    "data"    
)    


if not isinstance(    
    data,    
    list    
):    

    logger.warning(    
        "Unexpected Flutterwave transaction data: %s",    
        result    
    )    

    return None    


for transaction in data:    

    transaction_tx_ref = str(    

        transaction.get(    
            "tx_ref"    
        )    
        or ""    

    ).strip()    


    if (    
        transaction_tx_ref    
        == tx_ref    
    ):    

        return transaction    


return None

except Exception:

logger.exception(    
    "Error finding Flutterwave transaction."    
)    

return None

============================================================

VERIFY AND FINALIZE PAYMENT

============================================================

def _verify_and_finalize_payment(
payment_token,
transaction_id=None,
):

payment = _payment_from_token(
payment_token
)

if not payment:

return None

--------------------------------------------------------

ALREADY SUCCESSFUL

--------------------------------------------------------

current_status = str(
payment.get("status")
or ""
).strip().lower()

if current_status == "successful":

return payment

expected_tx_ref = str(
payment.get("tx_ref")
or ""
).strip()

if not expected_tx_ref:

logger.error(    
    "Payment has no tx_ref. token=%s",    
    payment_token    
)    

return payment

transaction_id = str(
transaction_id or ""
).strip()

========================================================

FIND TRANSACTION IF ID NOT PROVIDED

========================================================

if not transaction_id:

logger.info(    
    "Searching Flutterwave by tx_ref=%s",    
    expected_tx_ref    
)    


found_transaction = (    
    find_flutterwave_transaction_by_tx_ref(    
        expected_tx_ref    
    )    
)    


if found_transaction:    

    transaction_id = str(    
        found_transaction.get(    
            "id"    
        )    
        or ""