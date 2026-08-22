# ==========================================================
# ALHIKAM LEARNING CENTER V2
# registration.py
# PAYMENT -> REGISTRATION -> TELEGRAM BOT
# ==========================================================

from flask import (
    request,
    render_template_string,
)

import asyncio
from urllib.parse import quote

from telegram_service import (
    send_student_links,
)

from sheets import (
    save_to_google_sheet,
)

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

<meta
name="viewport"
content="width=device-width, initial-scale=1"
>

<title>ALHIKAM Registration</title>

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

input,
select{
    width:100%;
    padding:14px;
    margin-top:8px;
    margin-bottom:18px;
    border-radius:8px;
    border:1px solid #ccc;
    box-sizing:border-box;
    font-size:16px;
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

.payment{
    background:#e8f7ef;
    padding:15px;
    border-radius:10px;
    margin-bottom:20px;
}

.telegram{
    background:#e8f4ff;
    padding:12px;
    border-radius:10px;
    margin-bottom:20px;
}

.referral{
    background:#f0f8f5;
    padding:12px;
    border-radius:10px;
    margin-bottom:20px;
}

.info{
    background:#fff8e1;
    padding:12px;
    border-radius:10px;
    margin-bottom:20px;
}

</style>

</head>

<body>

<div class="container">

<h2>
🎓 ALHIKAM Registration
</h2>

<div class="payment">

<b>Payment Information</b>

<br><br>

Plan:
<b>{{ payment_plan }}</b>

<br>

Amount:
<b>₦{{ amount }}</b>

<br>

Status:
<b>✅ {{ payment_status }}</b>

<br>

Transaction:
<br>

<small>
{{ tx_ref }}
</small>

</div>


<div class="telegram">

{% if telegram_id %}

<b>📱 Telegram Connected</b>

<br><br>

Your Telegram account has been connected.

{% else %}

⚠️ Telegram has not been connected yet.

<br><br>

After completing registration,
tap the Telegram button on the success page
to connect with ALHIKAM Bot.

{% endif %}

</div>


<div class="referral">

{% if referral_code %}

🔗 Referral Code:

<b>
{{ referral_code }}
</b>

<br><br>

Promoter:

<b>
{{ promoter_name }}
</b>

{% else %}

No referral code detected.

{% endif %}

</div>


<div class="info">

<b>Complete your registration.</b>

<br><br>

Please enter your correct information.
This information will be used to create your
ALHIKAM student record.

</div>


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


<label>
<b>Full Name</b>
</label>

<input
type="text"
name="full_name"
placeholder="Enter your full name"
required
>


<label>
<b>Phone Number</b>
</label>

<input
type="tel"
name="phone"
placeholder="08012345678"
required
>


<label>
<b>Email Address</b>
</label>

<input
type="email"
name="email"
placeholder="example@gmail.com"
required
>


<label>
<b>Faculty</b>
</label>

<select
name="faculty"
required
>

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
# SUCCESS HTML
# ==========================================================

def success_page(
    full_name,
    payment_plan,
    amount,
    tx_ref,
    telegram_message
):

    # ------------------------------------------------------
    # CREATE TELEGRAM DEEP LINK
    # ------------------------------------------------------

    bot_url = (
        f"https://t.me/"
        f"{BOT_USERNAME}"
        f"?start="
        f"{quote(tx_ref, safe='')}"
    )


    return f"""

<!DOCTYPE html>

<html>

<head>

<meta
name="viewport"
content="width=device-width, initial-scale=1"
>

<title>
Registration Successful
</title>

<style>

body{{
    font-family:Arial,sans-serif;
    background:#f5f5f5;
    padding:30px 15px;
    text-align:center;
}}

.container{{
    max-width:550px;
    margin:auto;
    background:white;
    padding:30px;
    border-radius:15px;
    box-shadow:0 4px 12px rgba(0,0,0,.1);
}}

h2{{
    color:#087f5b;
}}

.success{{
    background:#e8f7ef;
    padding:15px;
    border-radius:10px;
}}

.telegram-button{{
    display:block;
    width:100%;
    box-sizing:border-box;
    padding:16px;
    margin-top:25px;
    background:#229ED9;
    color:white;
    text-decoration:none;
    border-radius:10px;
    font-size:18px;
    font-weight:bold;
}}

.telegram-info{{
    margin-top:12px;
    color:#555;
    font-size:14px;
}}

</style>

</head>

<body>

<div class="container">

<h2>
🎉 Registration Successful
</h2>

<div class="success">

<p>
Thank you
<b>{full_name}</b>
</p>

<p>
Your ALHIKAM registration has been completed.
</p>

</div>


<p>

🎓 Plan:

<b>
{payment_plan}
</b>

</p>


<p>

💰 Amount Paid:

<b>
₦{amount:,.0f}
</b>

</p>


{telegram_message}


<!-- ================================================== -->
<!-- TELEGRAM BOT BUTTON -->
<!-- ================================================== -->

<a
href="{bot_url}"
class="telegram-button"
>

🤖 START ALHIKAM BOT

</a>


<p class="telegram-info">

Tap the button above to open Telegram
and receive your ALHIKAM invitation links.

</p>


<p
style="
margin-top:25px;
color:#666;
"
>

Transaction Reference:

<br>

<small>
{tx_ref}
</small>

</p>

</div>

</body>

</html>

"""


# ==========================================================
# REGISTRATION PAGE
# ==========================================================

def registration_page(
    payment_sessions=None
):

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

        return (
            "Payment reference missing.",
            400
        )


    # ======================================================
    # GET PAYMENT
    # ======================================================

    payment = None


    if payment_sessions:

        payment = (
            payment_sessions.get(
                tx_ref
            )
        )


    if not payment:

        try:

            payment = (
                get_payment_by_tx_ref(
                    tx_ref
                )
            )

        except Exception as e:

            print(
                "Payment lookup error:",
                e
            )

            payment = None


    if not payment:

        return (
            """

            <div style="
                font-family:Arial;
                text-align:center;
                padding:40px;
            ">

            <h2>
            ⚠️ Payment Session Not Found
            </h2>

            <p>
            We could not find this payment reference.
            </p>

            <p>
            Please contact ALHIKAM support.
            </p>

            </div>

            """,
            404
        )


    # ======================================================
    # PAYMENT DATA
    # ======================================================

    payment_plan = (
        payment.get(
            "payment_plan",
            ""
        )
        or ""
    )


    amount = float(
        payment.get(
            "amount",
            0
        )
        or 0
    )


    payment_status = (
        payment.get(
            "payment_status",
            "Successful"
        )
        or "Successful"
    )


    # ======================================================
    # ONLY SUCCESSFUL PAYMENT
    # ======================================================

    if payment_status.lower() != "successful":

        return (
            """

            <div style="
                font-family:Arial;
                text-align:center;
                padding:40px;
            ">

            <h2>
            ⚠️ Payment Not Confirmed
            </h2>

            <p>
            This payment has not been confirmed yet.
            </p>

            </div>

            """,
            400
        )


    # ======================================================
    # TELEGRAM INFORMATION
    # ======================================================

    telegram_id = (
        payment.get(
            "telegram_id",
            ""
        )
        or request.args.get(
            "telegram_id",
            ""
        )
        or ""
    )


    telegram_name = (
        payment.get(
            "telegram_name",
            ""
        )
        or request.args.get(
            "telegram_name",
            ""
        )
        or ""
    )


    telegram_username = (
        payment.get(
            "telegram_username",
            ""
        )
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
    # REFERRAL
    # ======================================================

    referral_code = (
        payment.get(
            "referral_code",
            ""
        )
        or ""
    ).strip()


    promoter_name = (
        payment.get(
            "promoter_name",
            ""
        )
        or ""
    )


    # ======================================================
    # GET PROMOTER AGAIN
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


        if promoter:

            promoter_name = (
                promoter["full_name"]
            )

        else:

            referral_code = ""
            promoter_name = ""


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

        return (
            "Full name is required.",
            400
        )


    if not phone:

        return (
            "Phone number is required.",
            400
        )


    if not email:

        return (
            "Email address is required.",
            400
        )


    if faculty not in (
        "Science",
        "Arts",
        "Commercial"
    ):

        return (
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

            """

        )


    # ======================================================
    # PROMOTER ID
    # ======================================================

    promoter_id = (
        promoter["id"]
        if promoter
        else None
    )


    # ======================================================
    # COMMISSION
    # ======================================================

    commission = float(
        payment.get(
            "commission",
            0
        )
        or 0
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

        return (
            "Registration could not be completed. "
            "Please try again or contact support.",
            500
        )


    # ======================================================
    # MARK PAYMENT REGISTERED
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

    }


    try:

        sheet_result = (
            save_to_google_sheet(
                student_data
            )
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

        telegram_message

    )