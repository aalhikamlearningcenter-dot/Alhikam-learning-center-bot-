# ============================================================
# ALHIKAM LEARNING CENTER V2
# MAIN.PY (PART 1)
# ============================================================

import os
import threading
import logging
from payment import PAYMENT_HTML
import os
import uuid
import requests
payment_bp = Blueprint(
    "payment",
    __name__
)
from flask import (
    Flask,
    request,
    redirect,
    jsonify,
    render_template_string,
    session,
)

from database import (
    initialize_database,
)

from config import *

# ============================================================
# FLASK APP
# ============================================================

web_app = Flask(__name__)

web_app.secret_key = os.getenv(
    "SECRET_KEY",
    "alhikam-secret-key"
)

# ============================================================
# DATABASE
# ============================================================

initialize_database()

# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

logger = logging.getLogger("ALHIKAM")

# ============================================================
# HOME PAGE
# ============================================================

@web_app.route("/")
def home():
    return redirect("/payment")


# ============================================================
# PAYMENT PAGE
# ============================================================

@web_app.route("/payment", methods=["GET"])
def payment_page():
    return render_template_string(PAYMENT_HTML)
@payment_bp.route("/create-payment", methods=["POST"])
def create_payment():

    plan_id = request.form.get("plan")

    if plan_id not in PAYMENT_PLANS:
        return "Invalid payment plan", 400

    plan = PAYMENT_PLANS[plan_id]

    payment_token = uuid.uuid4().hex

    tx_ref = f"ALHIKAM_{payment_token}"

    pending_payments[payment_token] = {
        "payment_token": payment_token,
        "tx_ref": tx_ref,
        "plan": plan,
        "status": "pending",
    }

    payload = {
        "tx_ref": tx_ref,
        "amount": plan["amount"],
        "currency": "NGN",
        "redirect_url": os.getenv("APP_URL") + "/payment-callback",
        "customer": {
            "email": f"{payment_token}@alhikam.com",
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

    result = response.json()

    if (
        response.status_code == 200
        and result.get("status") == "success"
    ):
        return redirect(result["data"]["link"])

    return "Unable to create payment link", 500
# ============================================================
# FLUTTERWAVE CONFIGURATION
# ============================================================

FLW_PUBLIC_KEY = os.getenv("FLW_PUBLIC_KEY")
FLW_SECRET_KEY = os.getenv("FLW_SECRET_KEY")

PAYMENT_PLANS = {
    "1": {"name": "1 Month", "amount": 3600},
    "2": {"name": "2 Months", "amount": 6800},
    "3": {"name": "3 Months", "amount": 10000},
    "4": {"name": "4 Months", "amount": 13200},
    "5": {"name": "5 Months", "amount": 16500},
    "6": {"name": "6 Months", "amount": 20000},
}

pending_payments = {}

# ============================================================
# HEALTH CHECK
# ============================================================

@web_app.route("/health")
def health():

    return jsonify({
        "status": "healthy",
        "app": "ALHIKAM V2"
    })

# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    PORT = int(
        os.getenv(
            "PORT",
            8080
        )
    )

    web_app.run(
        host="0.0.0.0",
        port=PORT
    )