# ==========================================================
# ALHIKAM LEARNING CENTER V2
# registration.py
# PAYMENT -> REGISTRATION -> REFERRAL -> GOOGLE SHEETS -> TELEGRAM
# ==========================================================

from flask import request, render_template_string
import asyncio
from urllib.parse import quote

from telegram_service import send_student_links
from sheets import save_to_google_sheet

from database import (
    add_student,
    get_promoter_by_referral_code,
    get_payment_by_tx_ref,
    mark_payment_registration_completed,
)


# ==========================================================
# CONFIG
# ==========================================================

BOT_USERNAME = "Alhikamcenterbot"


# ==========================================================
# REGISTRATION HTML
# ==========================================================

REGISTRATION_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport"
          content="width=device-width, initial-scale=1.0">

    <title>ALHIKAM Registration</title>

    <style>
        body {
            font-family: Arial, sans-serif;
            background: #f4f7f9;
            margin: 0;
            padding: 20px;
        }

        .container {
            max-width: 600px;
            margin: auto;
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        }

        h1 {
            text-align: center;
            color: #087f5b;
        }

        .payment-box {
            background: #f0fdf4;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
        }

        .referral-box {
            background: #fff7ed;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
        }

        label {
            display: block;
            margin-top: 15px;
            margin-bottom: 6px;
            font-weight: bold;
        }

        input,
        select {
            width: 100%;
            box-sizing: border-box;
            padding: 12px;
            border: 1px solid #ccc;
            border-radius: 8px;
            font-size: 15px;
        }

        button {
            width: 100%;
            margin-top: 25px;
            padding: 14px;
            border: none;
            border-radius: 8px;
            background: #087f5b;
            color: white;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
        }

        .telegram {
            background: #e8f4ff;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
        }

        .warning {
            color: #b45309;
            font-weight: bold;
        }

        .success {
            color: #087f5b;
            font-weight: bold;
        }
    </style>
</head>

<body>

<div class="container">

    <h1>🎓 ALHIKAM Registration</h1>

    <div class="payment-box">

        <h3>💳 Payment Information</h3>

        <p>
            <strong>Plan:</strong>
            {{ payment_plan }}
        </p>

        <p>
            <strong>Amount:</strong>
            ₦{{ amount }}
        </p>

        <p>
            <strong>Status:</strong>
            <span class="success">
                ✅ {{ payment_status }}
            </span>
        </p>

        <p>
            <strong>Transaction:</strong>
            {{ tx_ref }}
        </p>

    </div>


    {% if referral_code %}

    <div class="referral-box">

        <h3>🔗 Referral Information</h3>

        <p>
            <strong>Referral Code:</strong>
            {{ referral_code }}
        </p>

        <p>
            <strong>Promoter:</strong>
            {{ promoter_name }}
        </p>

        {% if commission > 0 %}

        <p>
            <strong>Promoter Commission:</strong>
            ₦{{ commission }}

        </p>

        {% endif %}

    </div>

    {% endif %}


    <div class="telegram">

        {% if telegram_id %}

            <p class="success">
                📱 Telegram Connected
            </p>

            <p>
                Your Telegram account has already been
                connected to this registration.
            </p>

        {% else %}

            <p class="warning">
                ⚠️ Telegram is not connected yet.
            </p>

            <p>
                After completing registration,
                use the Telegram button on the success page
                to connect your account.
            </p>

        {% endif %}

    </div>


    <h3>📝 Complete Your Registration</h3>

    <p>
        Please enter your correct information.
        This information will be used to create your
        ALHIKAM student record.
    </p>


    <form method="POST">

        <input
            type="hidden"
            name="tx_ref"
            value="{{ tx_ref }}"
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

        <label>Full Name</label>

        <input
            type="text"
            name="full_name"
            placeholder="Enter your full name"
            required
        >


        <label>Phone Number</label>

        <input
            type="tel"
            name="phone"
            placeholder="08012345678"
            required
        >


        <label>Email Address</label>

        <input
            type="email"
            name="email"
            placeholder="example@gmail.com"
            required
        >


        <label>Faculty</label>

        <select name="faculty" required>

            <option value="">
                Select Faculty
            </option>

            <option value="Science">
                Science
            </option>

            <option value="Arts">
                Arts
            </option>

            <option value="Commercial">
                Commercial
            </option>

        </select>


        <button type="submit">
            ✅ Complete Registration
        </button>

    </form>

</div>

</body>
</html>
"""


# ==========================================================
# ERROR PAGE
# ==========================================================

def error_page(title, message, status_code=400):

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport"
              content="width=device-width, initial-scale=1.0">

        <title>{title}</title>

        <style>
            body {{
                font-family: Arial, sans-serif;
                background: #f4f7f9;
                padding: 30px;
                text-align: center;
            }}

            .box {{
                max-width: 600px;
                margin: auto;
                background: white;
                padding: 30px;
                border-radius: 15px;
                box-shadow: 0 4px 15px
                    rgba(0,0,0,0.08);
            }}

            h2 {{
                color: #b45309;
            }}
        </style>
    </head>

    <body>

        <div class="box">

            <h2>{title}</h2>

            <p>{message}</p>

        </div>

    </body>
    </html>
    """

    return html, status_code


# ==========================================================
# SUCCESS PAGE
# ==========================================================

def success_page(
    full_name,
    payment_plan,
    amount,
    tx_ref,
    telegram_message,
    referral_code="",
    promoter_name="",
    commission=0,
):

    bot_url = (
        f"https://t.me/"
        f"{BOT_USERNAME}"
        f"?start="
        f"{quote(tx_ref, safe='')}"
    )

    referral_html = ""

    if referral_code:

        referral_html = f"""
        <div class="referral-box">

            <h3>🔗 Referral Information</h3>

            <p>
                <strong>Referral Code:</strong>
                {referral_code}
            </p>

            <p>
                <strong>Promoter:</strong>
                {promoter_name}
            </p>

            <p>
                <strong>Commission:</strong>
                ₦{commission:,.0f}
            </p>

        </div>
        """

    return f"""
    <!DOCTYPE html>

    <html>

    <head>

        <meta charset="UTF-8">

        <meta name="viewport"
              content="width=device-width, initial-scale=1.0">

        <title>Registration Successful</title>

        <style>

            body {{
                font-family: Arial, sans-serif;
                background: #f4f7f9;
                padding: 20px;
            }}

            .container {{
                max-width: 600px;
                margin: auto;
                background: white;
                padding: 30px;
                border-radius: 15px;
                text-align: center;
                box-shadow:
                    0 4px 15px rgba(0,0,0,0.08);
            }}

            h1 {{
                color: #087f5b;
            }}

            .info {{
                background: #f0fdf4;
                padding: 15px;
                border-radius: 10px;
                text-align: left;
                margin: 20px 0;
            }}

            .referral-box {{
                background: #fff7ed;
                padding: 15px;
                border-radius: 10px;
                text-align: left;
                margin: 20px 0;
            }}

            .telegram-button {{
                display: block;
                background: #229ED9;
                color: white;
                text-decoration: none;
                padding: 15px;
                border-radius: 10px;
                font-weight: bold;
                margin-top: 20px;
            }}

            .tx {{
                font-size: 12px;
                color: #666;
                margin-top: 20px;
                word-break: break-all;
            }}

        </style>

    </head>

    <body>

        <div class="container">

            <h1>
                🎉 Registration Successful
            </h1>

            <p>
                Thank you
                <strong>{full_name}</strong>
            </p>

            <p>
                Your ALHIKAM registration has been
                completed successfully.
            </p>


            <div class="info">

                <p>
                    🎓 <strong>Plan:</strong>
                    {payment_plan}
                </p>

                <p>
                    💰 <strong>Amount Paid:</strong>
                    ₦{amount:,.0f}
                </p>

            </div>


            {referral_html}


            {telegram_message}


            <a
                href="{bot_url}"
                class="telegram-button"
            >
                🤖 START ALHIKAM BOT
            </a>


            <p>
                Tap the button above to open Telegram
                and receive your ALHIKAM class invitation
                links.
            </p>


            <p class="tx">
                Transaction Reference:
                {tx_ref}
            </p>

        </div>

    </body>

    </html>
    """


# ==========================================================
# REGISTRATION PAGE
# ==========================================================

def registration_page(payment_sessions=None):

    if payment_sessions is None:
        payment_sessions = {}


    # ======================================================
    # GET TX REF
    # ======================================================

    tx_ref = (
        request.args.get(
            "tx_ref",
            ""
        )
        or ""
    ).strip()

    if not tx_ref:

        return error_page(
            "⚠️ Payment Reference Missing",
            "Payment reference is missing.",
            400
        )


    # ======================================================
    # GET PAYMENT
    # ======================================================

    payment = None

    if payment_sessions:

        payment = payment_sessions.get(
            tx_ref
        )


    if not payment:

        try:

            payment = get_payment_by_tx_ref(
                tx_ref
            )

        except Exception as e:

            print(
                "Payment lookup error:",
                e
            )

            payment = None


    if not payment:

        return error_page(
            "⚠️ Payment Session Not Found",
            "We could not find this payment reference. "
            "Please contact ALHIKAM support.",
            404
        )


    # ======================================================
    # PAYMENT DATA
    # ======================================================

    payment_plan = (
        payment["payment_plan"]
        or ""
    )

    amount = float(
        payment["amount"]
        or 0
    )

    payment_status = (
        payment["payment_status"]
        or "Pending"
    ).strip()


    # ======================================================
    # ONLY SUCCESSFUL PAYMENT
    # ======================================================

    if payment_status.lower() != "successful":

        return error_page(
            "⚠️ Payment Not Confirmed",
            "This payment has not been confirmed yet.",
            400
        )


    # ======================================================
    # TELEGRAM INFORMATION
    # ======================================================

    telegram_id = (
        payment["telegram_id"]
        or request.args.get(
            "telegram_id",
            ""
        )
        or ""
    )

    telegram_name = (
        payment["telegram_name"]
        or request.args.get(
            "telegram_name",
            ""
        )
        or ""
    )

    telegram_username = (
        payment["telegram_username"]
        or request.args.get(
            "telegram_username",
            ""
        )
        or ""
    )

    telegram_id = str(
        telegram_id
    ).strip()

    telegram_name = str(
        telegram_name
    ).strip()

    telegram_username = str(
        telegram_username
    ).strip()


    # ======================================================
    # REFERRAL INFORMATION
    # ======================================================

    referral_code = (
        payment["referral_code"]
        or ""
    ).strip()

    promoter_id = payment["promoter_id"]

    promoter_name = (
        payment["promoter_name"]
        or ""
    ).strip()

    commission = float(
        payment["commission"]
        or 0
    )


    # ======================================================
    # VERIFY REFERRAL AGAIN
    # ======================================================

    promoter = None

    if referral_code:

        try:

            promoter = (
                get_promoter_by_referral_code(
                    referral_code
                )
            )

        except Exception as e:

            print(
                "Promoter lookup error:",
                e
            )

            promoter = None


        # --------------------------------------------------
        # INVALID REFERRAL
        # --------------------------------------------------

        if not promoter:

            referral_code = ""
            promoter_id = None
            promoter_name = ""
            commission = 0

        else:

            promoter_id = promoter["id"]

            promoter_name = (
                promoter["full_name"]
                or ""
            )

    else:

        promoter_id = None
        promoter_name = ""
        commission = 0


    # ======================================================
    # GET PAGE
    # ======================================================

    if request.method == "GET":

        return render_template_string(
            REGISTRATION_HTML,

            tx_ref=tx_ref,

            payment_plan=payment_plan,

            amount=f"{amount:,.0f}",

            payment_status=payment_status,

            referral_code=referral_code,

            promoter_name=promoter_name,

            commission=f"{commission:,.0f}",

            telegram_id=telegram_id,

            telegram_name=telegram_name,

            telegram_username=telegram_username,
        )


    # ======================================================
    # POST DATA
    # ======================================================

    full_name = (
        request.form.get(
            "full_name",
            ""
        )
        or ""
    ).strip()

    phone = (
        request.form.get(
            "phone",
            ""
        )
        or ""
    ).strip()

    email = (
        request.form.get(
            "email",
            ""
        )
        or ""
    ).strip()

    faculty = (
        request.form.get(
            "faculty",
            ""
        )
        or ""
    ).strip()


    # ======================================================
    # VALIDATION
    # ======================================================

    if not full_name:

        return error_page(
            "⚠️ Missing Information",
            "Full name is required.",
            400
        )


    if not phone:

        return error_page(
            "⚠️ Missing Information",
            "Phone number is required.",
            400
        )


    if not email:

        return error_page(
            "⚠️ Missing Information",
            "Email address is required.",
            400
        )


    if faculty not in (
        "Science",
        "Arts",
        "Commercial"
    ):

        return error_page(
            "⚠️ Invalid Faculty",
            "Please select a valid faculty.",
            400
        )


    # ======================================================
    # GET TELEGRAM DATA FROM FORM
    # ======================================================

    telegram_id = (
        request.form.get(
            "telegram_id",
            telegram_id
        )
        or ""
    ).strip()

    telegram_name = (
        request.form.get(
            "telegram_name",
            telegram_name
        )
        or ""
    ).strip()

    telegram_username = (
        request.form.get(
            "telegram_username",
            telegram_username
        )
        or ""
    ).strip()


    # ======================================================
    # PREVENT DUPLICATE REGISTRATION
    #
    # IMPORTANT:
    # payments and students are separate tables.
    # Therefore we check students using tx_ref.
    # ======================================================

    existing_student = None

    try:

        from database import (
            get_student_by_tx_ref
        )

        existing_student = (
            get_student_by_tx_ref(
                tx_ref
            )
        )

    except Exception as e:

        print(
            "Existing student lookup error:",
            e
        )


    if existing_student:

        return success_page(

            existing_student["full_name"],

            payment_plan,

            amount,

            tx_ref,

            """
            <p style="
                color:#087f5b;
                font-weight:bold;
            ">
                ✅ This payment has already been
                registered successfully.
            </p>
            """,

            referral_code=(
                existing_student["referral_code"]
                or referral_code
            ),

            promoter_name=promoter_name,

            commission=commission,
        )


    # ======================================================
    # STUDENT DATA
    # ======================================================

    database_data = {

        "payment_token":
            tx_ref,

        "tx_ref":
            tx_ref,

        "full_name":
            full_name,

        "phone":
            phone,

        "email":
            email,

        "course":
            faculty,

        "telegram_id":
            telegram_id,

        "telegram_username":
            telegram_username,

        "telegram_name":
            telegram_name,

        "payment_plan":
            payment_plan,

        "amount_paid":
            amount,

        "payment_status":
            "Successful",

        "registration_completed":
            1,

        "referral_code":
            referral_code,

        "promoter_id":
            promoter_id,
    }


    # ======================================================
    # SAVE STUDENT
    # ======================================================

    try:

        student_id = add_student(
            database_data
        )

        print(
            "Student saved:",
            student_id
        )

    except Exception as e:

        print(
            "Student database error:",
            e
        )

        return error_page(
            "❌ Registration Failed",
            "Registration could not be completed. "
            "Please try again or contact ALHIKAM support.",
            500
        )


    # ======================================================
    # MARK PAYMENT AS REGISTERED
    # ======================================================

    try:

        mark_payment_registration_completed(
            tx_ref
        )

    except Exception as e:

        print(
            "Payment registration update error:",
            e
        )


    # ======================================================
    # GOOGLE SHEETS
    # ======================================================

    student_data = {

        "telegram_id":
            telegram_id,

        "username":
            telegram_username,

        "telegram_name":
            telegram_name,

        "full_name":
            full_name,

        "phone":
            phone,

        "email":
            email,

        "course":
            faculty,

        "referral_code":
            referral_code,

        "promoter_name":
            promoter_name,

        "promoter_id":
            promoter_id,

        "payment_plan":
            payment_plan,

        "amount_paid":
            amount,

        "payment_status":
            "Successful",

        "commission":
            commission,

        "tx_ref":
            tx_ref,

        "student_id":
            student_id,
    }


    try:

        sheet_result = save_to_google_sheet(
            student_data
        )

        print(
            "Google Sheet result:",
            sheet_result
        )

    except Exception as e:

        print(
            "Google Sheets error:",
            e
        )


    # ======================================================
    # TELEGRAM LINKS
    #
    # If Telegram ID is already available,
    # send links automatically.
    #
    # If not, the student uses the bot button.
    # ======================================================

    telegram_error = None

    if telegram_id:

        try:

            asyncio.run(
                send_student_links(
                    telegram_id,
                    faculty
                )
            )

        except Exception as e:

            telegram_error = e

            print(
                "Telegram link error:",
                e
            )


    # ======================================================
    # TELEGRAM MESSAGE
    # ======================================================

    if telegram_id and not telegram_error:

        telegram_message = """
        <p style="
            color:#087f5b;
            font-weight:bold;
        ">
            🎉 Your Telegram invitation links
            have been sent successfully.
        </p>
        """

    elif telegram_id and telegram_error:

        telegram_message = """
        <p style="
            color:#b45309;
            font-weight:bold;
        ">
            ⚠️ Registration was successful,
            but Telegram invitation links
            could not be sent automatically.

            <br><br>

            You can use the Telegram button below
            to continue.
        </p>
        """

    else:

        telegram_message = """
        <p style="
            color:#b45309;
            font-weight:bold;
        ">
            📱 Telegram is not connected yet.

            <br><br>

            Tap the
            <b>START ALHIKAM BOT</b>
            button below to connect your Telegram
            and receive your invitation links.
        </p>
        """


    # ======================================================
    # SUCCESS
    # ======================================================

    return success_page(

        full_name,

        payment_plan,

        amount,

        tx_ref,

        telegram_message,

        referral_code=referral_code,

        promoter_name=promoter_name,

        commission=commission,
    )