# ==========================================================
# ALHIKAM LEARNING CENTER V2
# registration.py
# ==========================================================

from flask import (
    request,
    render_template_string,
)

import asyncio

from telegram_service import (
    send_student_links,
)

from sheets import (
    save_to_google_sheet,
)

from database import (
    add_student,
    get_payment_by_tx_ref,
    get_promoter_by_referral_code,
)

from config import (
    WHATSAPP_COMMUNITY_LINK,
)


# ==========================================================
# HTML
# ==========================================================

REGISTRATION_HTML = """

<!DOCTYPE html>

<html>

<head>

<meta name="viewport"
content="width=device-width, initial-scale=1">

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
    margin-top:10px;
    margin-bottom:18px;
    border-radius:8px;
    border:1px solid #ccc;
    box-sizing:border-box;
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
}

.payment{
    background:#e8f7ef;
    padding:15px;
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

<b>Payment</b>

<br><br>

Plan:
<b>{{ payment_plan }}</b>

<br>

Amount:
<b>₦{{ amount }}</b>

<br>

Status:
<b>✅ {{ payment_status }}</b>

</div>


{% if referral_code %}

<div class="referral">

🔗 Referral Code:

<b>{{ referral_code }}</b>

<br><br>

Promoter:

<b>{{ promoter_name }}</b>

</div>

{% endif %}


<div class="info">

Please enter your correct information.

Your information will be used to create your ALHIKAM student record.

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


<label>Full Name</label>

<input
type="text"
name="full_name"
required
>


<label>Phone Number</label>

<input
type="tel"
name="phone"
required
>


<label>Email Address</label>

<input
type="email"
name="email"
required
>


<label>Faculty</label>

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

Complete Registration

</button>

</form>

</div>

</body>

</html>

"""


# ==========================================================
# PAGE
# ==========================================================

def registration_page():

    tx_ref = request.args.get(
        "tx_ref",
        ""
    ).strip()

    telegram_id = request.args.get(
        "telegram_id",
        ""
    ).strip()

    telegram_name = request.args.get(
        "telegram_name",
        ""
    ).strip()

    telegram_username = request.args.get(
        "telegram_username",
        ""
    ).strip()

    if not tx_ref:

        return (
            "❌ Payment reference is missing.",
            400
        )

    payment = get_payment_by_tx_ref(
        tx_ref
    )

    if not payment:

        return (
            "❌ Payment record was not found.",
            404
        )

    if payment["payment_status"] != "Successful":

        return (
            "❌ Payment has not been verified yet.",
            400
        )

    payment_plan = payment["payment_plan"]

    amount = float(
        payment["amount"] or 0
    )

    payment_status = payment["payment_status"]

    referral_code = (
        payment["referral_code"]
        or ""
    )

    promoter_id = payment["promoter_id"]

    promoter_name = (
        payment["promoter_name"]
        or ""
    )

    # ------------------------------------------------------
    # Get Telegram information saved during payment
    # ------------------------------------------------------

    if not telegram_id:

        telegram_id = (
            payment["telegram_id"]
            or ""
        )

    if not telegram_username:

        telegram_username = (
            payment["telegram_username"]
            or ""
        )

    if not telegram_name:

        telegram_name = (
            payment["telegram_name"]
            or ""
        )

    # ------------------------------------------------------
    # GET
    # ------------------------------------------------------

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

    # ------------------------------------------------------
    # POST
    # ------------------------------------------------------

    full_name = request.form.get(
        "full_name",
        ""
    ).strip()

    phone = request.form.get(
        "phone",
        ""
    ).strip()

    email = request.form.get(
        "email",
        ""
    ).strip()

    faculty = request.form.get(
        "faculty",
        ""
    ).strip()

    if not full_name:
        return "Full name is required.", 400

    if not phone:
        return "Phone number is required.", 400

    if not email:
        return "Email address is required.", 400

    if faculty not in (
        "Science",
        "Arts",
        "Commercial"
    ):

        return (
            "Invalid faculty.",
            400
        )

    # ------------------------------------------------------
    # Verify promoter
    # ------------------------------------------------------

    promoter = None

    if referral_code:

        promoter = (
            get_promoter_by_referral_code(
                referral_code
            )
        )

        if not promoter:

            referral_code = ""

            promoter_id = None

            promoter_name = ""

    # ------------------------------------------------------
    # Student
    # ------------------------------------------------------

    student_data = {

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

    try:

        student_id = add_student(
            student_data
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
            "Registration could not be completed.",
            500
        )

    # ------------------------------------------------------
    # Google Sheet
    # ------------------------------------------------------

    sheet_data = {

        "telegram_id":
            telegram_id,

        "username":
            telegram_username,

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
            payment["commission"],

        "tx_ref":
            tx_ref,

    }

    try:

        save_to_google_sheet(
            sheet_data
        )

    except Exception as e:

        print(
            "Google Sheet error:",
            e
        )

    # ------------------------------------------------------
    # Telegram links
    # ------------------------------------------------------

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
                "Telegram invite error:",
                e
            )

    # ------------------------------------------------------
    # WhatsApp
    # ------------------------------------------------------

    whatsapp_button = ""

    if WHATSAPP_COMMUNITY_LINK:

        whatsapp_button = f"""

        <a href="{WHATSAPP_COMMUNITY_LINK}"
        target="_blank"
        style="
        display:inline-block;
        background:#25D366;
        color:white;
        padding:15px 25px;
        border-radius:10px;
        text-decoration:none;
        font-weight:bold;
        margin-top:15px;
        ">

        💬 Join WhatsApp Community

        </a>

        """

    # ------------------------------------------------------
    # Telegram status
    # ------------------------------------------------------

    if telegram_id and not telegram_error:

        telegram_message = """

        <p>
        🎉 Your Telegram class links have been sent.
        </p>

        """

    elif telegram_error:

        telegram_message = """

        <p style="color:#b45309;">

        ⚠️ Registration is successful, but Telegram links
        could not be sent automatically.

        Please contact ALHIKAM support.

        </p>

        """

    else:

        telegram_message = """

        <p style="color:#b45309;">

        ⚠️ Telegram ID was not provided.

        Please contact ALHIKAM support.

        </p>

        """

    # ------------------------------------------------------
    # SUCCESS
    # ------------------------------------------------------

    return f"""

    <!DOCTYPE html>

    <html>

    <head>

    <meta name="viewport"
    content="width=device-width, initial-scale=1">

    <title>
    Registration Successful
    </title>

    </head>

    <body style="
    font-family:Arial;
    text-align:center;
    padding:40px;
    background:#f5f5f5;
    ">

    <div style="
    max-width:550px;
    margin:auto;
    background:white;
    padding:30px;
    border-radius:15px;
    box-shadow:0 4px 12px rgba(0,0,0,.1);
    ">

    <h2>
    ✅ Registration Successful
    </h2>

    <p>
    Thank you <b>{full_name}</b>
    </p>

    <p>
    Your ALHIKAM registration has been completed.
    </p>

    <p>
    🎓 Plan:
    <b>{payment_plan}</b>
    </p>

    <p>
    💰 Amount Paid:
    <b>₦{amount:,.0f}</b>
    </p>

    {telegram_message}

    {whatsapp_button}

    <p style="
    margin-top:25px;
    color:#666;
    ">

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