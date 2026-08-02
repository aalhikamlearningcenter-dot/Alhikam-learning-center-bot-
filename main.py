# ============================================================
# ALHIKAM LEARNING CENTER V2
# MAIN.PY (PART 1)
# ============================================================

import os
import threading
import logging
from payment import (
    PAYMENT_HTML,
    create_flutterwave_payment,
)
import os
import uuid
import requests
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
@web_app.route("/create-payment", methods=["POST"])
def create_payment():

    plan_id = request.form.get("plan")

    payment = create_flutterwave_payment(
        plan_id,
        os.getenv("RAILWAY_URL")
    )

    if payment is None:
        return "Unable to create payment.", 500

    return redirect(payment["payment_link"])

# ============================================================
# REGISTRATION
# ============================================================

@web_app.route("/register", methods=["GET", "POST"])
def register():
    return registration_page()

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