# ==========================================================
# ALHIKAM LEARNING CENTER V2
# registration.py
# STUDENT REGISTRATION + GOOGLE SHEET + TELEGRAM
# ==========================================================

from flask import (
    request,
    render_template_string,
)

import asyncio

from telegram_service import (
    send_student_links
)

from sheets import (
    save_to_google_sheet
)

from database import (
    add_student,
    get_promoter_by_referral_code,
    get_payment_by_tx_ref,
    get_student_by_tx_ref,
)

from config import (
    WHATSAPP_COMMUNITY_LINK,
)


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

<title>
ALHIKAM Registration
</title>

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
    cursor:pointer;
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
    font-size:14px;
}

.info{
    background:#fff8e1;
    padding:12px;
    border-radius:10px;
    margin-bottom:20px;
    font-size:14px;
}

</style>

</head>

<body>

<div class="container">

<h2>
🎓 ALHIKAM Registration
</h2>

<div class="payment">

<b>Payment:</b>

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

Please enter your correct information.

This information will be used to create
your ALHIKAM student record.

</div>


<form method="POST">

<input
type="hidden"
name="tx_ref"
value="{{ tx_ref }}"
>

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


<label>
Full Name
</label>

<input
type="text"
name="full_name"
required
>


<label>
Phone Number
</label>

<input
type="tel"
name="phone"
required
>


<label>
Email Address
</label>

<input
type="email"
name="email"
required
>


<label>
Faculty
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

Complete Registration

</button>

</form>

</div>

</body>

</html>

"""


# ==========================================================
# ERROR PAGE
# ==========================================================

def error_page(
    title,
    message,
    status_code=400
):

    return f"""

    <!DOCTYPE html>

    <html>

    <body
    style="
    font-family:Arial;
    text-align:center;
    padding:40px;
    background:#f5f5f5;
    "
    >

    <div
    style="
    max-width:550px;
    margin:auto;
    background:white;
    padding:30px;
    border-radius:15px;
    box-shadow:0 4px 12px rgba(0,0,0,.1);
    "
    >

    <h2>
    {title}
    </h2>

    <p>
    {message}
    </p>

    </div>

    </body>

    </html>

    """, status_code


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

    tx_ref = request.args.get(
        "tx_ref",
        ""
    ).strip()


    if not tx_ref:

        return error_page(

            "❌ Payment Reference Missing",

            "We could not identify your payment.",

            400

        )


    # ======================================================
    # DATABASE FIRST
    #
    # Payment database is the main source.
    # ======================================================

    payment = None


    try:

        payment = get_payment_by_tx_ref(
            tx_ref
        )

    except Exception as e:

        print(
            "Payment database lookup error:",
            e
        )


    # ======================================================
    # MEMORY FALLBACK
    # ======================================================

    if not payment:

        payment = payment_sessions.get(
            tx_ref
        )


    # ======================================================
    # PAYMENT NOT FOUND
    # ======================================================

    if not payment:

        return error_page(

            "❌ Payment Not Found",

            "We could not find your payment record. "
            "Please contact ALHIKAM support.",

            404

        )


    # ======================================================
    # PAYMENT STATUS
    # ======================================================

    payment_status = (
        payment["payment_status"]
        if "payment_status" in payment.keys()
        else payment.get(
            "payment_status",
            ""
        )
    )


    if payment_status != "Successful":

        return error_page(

            "❌ Payment Not Completed",

            "Your payment has not been verified yet.",

            400

        )


    # ======================================================
    # PAYMENT DATA
    # ======================================================

    payment_plan = payment[
        "payment_plan"
    ]


    amount = float(
        payment[
            "amount"
        ]
    )


    referral_code = (
        payment[
            "referral_code"
        ]
        or ""
    )


    promoter_name = (
        payment[
            "promoter_name"
        ]
        or ""
    )


    promoter_id = payment[
        "promoter_id"
    ]


    commission = float(
        payment[
            "commission"
        ]
        or 0
    )


    # ======================================================
    # CHECK IF ALREADY REGISTERED
    # ======================================================

    existing_student = None


    try:

        existing_student = (
            get_student_by_tx_ref(
                tx_ref
            )
        )

    except Exception as e:

        print(
            "Student lookup error:",
            e
        )


    if existing_student:

        return f"""

        <!DOCTYPE html>

        <html>

        <body
        style="
        font-family:Arial;
        text-align:center;
        padding:40px;
        background:#f5f5f5;
        "
        >

        <div
        style="
        max-width:550px;
        margin:auto;
        background:white;
        padding:30px;
        border-radius:15px;
        "
        >

        <h2>
        ✅ Registration Already Completed
        </h2>

        <p>
        This payment has already been used
        to complete a registration.
        </p>

        <p>
        Student:
        <b>
        {existing_student["full_name"]}
        </b>
        </p>

        </div>

        </body>

        </html>

        """


    # ======================================================
    # GET
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

            telegram_id=request.args.get(
                "telegram_id",
                ""
            ),

            telegram_name=request.args.get(
                "telegram_name",
                ""
            ),

            telegram_username=request.args.get(
                "telegram_username",
                ""
            ),

        )


    # ======================================================
    # POST DATA
    # ======================================================

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


    telegram_id = request.form.get(
        "telegram_id",
        ""
    ).strip()


    telegram_name = request.form.get(
        "telegram_name",
        ""
    ).strip()


    telegram_username = request.form.get(
        "telegram_username",
        ""
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


    if not faculty:

        return (
            "Please select your faculty.",
            400
        )


    if faculty not in (
        "Science",
        "Arts",
        "Commercial"
    ):

        return (
            "Invalid faculty.",
            400
        )


    # ======================================================
    # VERIFY PROMOTER
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


        if not promoter:

            referral_code = ""

            promoter_id = None

            promoter_name = ""

            commission = 0


    # ======================================================
    # DATABASE DATA
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
            "Database Error:",
            e
        )

        return (
            "Registration could not be completed.",
            500
        )


    # ======================================================
    # GOOGLE SHEET
    # ======================================================

    student_data = {

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
            commission,

        "tx_ref":
            tx_ref,

    }


    try:

        result = save_to_google_sheet(
            student_data
        )

        print(
            "Google Sheet result:",
            result
        )

    except Exception as e:

        print(
            "Google Sheets Error:",
            e
        )


    # ======================================================
    # TELEGRAM
    # ======================================================

    telegram_message = """

    <p>
    🎓 Your Telegram invitation links have been sent.
    </p>

    """


    if telegram_id:

        try:

            asyncio.run(

                send_student_links(

                    telegram_id,

                    faculty

                )

            )

        except Exception as e:

            print(
                "Telegram Error:",
                e
            )

            telegram_message = """

            <p
            style="color:#b45309;"
            >

            ⚠️ Registration succeeded, but
            Telegram links could not be sent.

            Please contact ALHIKAM support.

            </p>

            """

    else:

        telegram_message = """

        <p
        style="color:#b45309;"
        >

        ⚠️ Telegram ID was not provided.

        Please contact ALHIKAM support
        to receive your Telegram links.

        </p>

        """


    # ======================================================
    # PROMOTER MESSAGE
    # ======================================================

    promoter_message = ""


    if promoter:

        promoter_message = f"""

        <div
        style="
        background:#f0f8f5;
        padding:15px;
        border-radius:10px;
        margin-top:20px;
        "
        >

        🔗 Referred by:

        <b>
        {promoter_name}
        </b>

        </div>

        """


    # ======================================================
    # WHATSAPP
    # ======================================================

    whatsapp_button = ""


    if WHATSAPP_COMMUNITY_LINK:

        whatsapp_button = f"""

        <a

        href="{WHATSAPP_COMMUNITY_LINK}"

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
        "

        >

        💬 Join WhatsApp Community

        </a>

        """


    # ======================================================
    # SUCCESS PAGE
    # ======================================================

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

    </head>

    <body

    style="
    font-family:Arial;
    text-align:center;
    padding:40px;
    background:#f5f5f5;
    "
    >

    <div

    style="
    max-width:550px;
    margin:auto;
    background:white;
    padding:30px;
    border-radius:15px;
    box-shadow:0 4px 12px rgba(0,0,0,.1);
    "
    >

    <h2>
    ✅ Registration Successful
    </h2>

    <p>

    Thank you

    <b>
    {full_name}
    </b>

    </p>

    <p>
    Your ALHIKAM registration has been
    completed successfully.
    </p>

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

    {promoter_message}

    {telegram_message}

    {whatsapp_button}

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