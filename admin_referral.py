# ==========================================================
# ALHIKAM LEARNING CENTER V2
# admin_referral.py
#
# ADMIN PROMOTER CREATION
# ==========================================================

import secrets
import string

from flask import (
    request,
    render_template_string,
)

from database import (
    add_promoter,
    get_promoter_by_referral_code,
)

from config import APP_URL


# ==========================================================
# GENERATE UNIQUE REFERRAL CODE
# ==========================================================

def generate_referral_code():

    """
    Generate a unique referral code.

    Example:
    ALHIKAM-X7K92P
    """

    characters = (
        string.ascii_uppercase
        + string.digits
    )

    while True:

        random_part = "".join(
            secrets.choice(characters)
            for _ in range(6)
        )

        referral_code = (
            f"ALHIKAM-{random_part}"
        )

        existing = (
            get_promoter_by_referral_code(
                referral_code
            )
        )

        if not existing:

            return referral_code


# ==========================================================
# ADMIN LOGIN HTML
# ==========================================================

ADMIN_LOGIN_HTML = """

<!DOCTYPE html>

<html>

<head>

<meta name="viewport"
content="width=device-width, initial-scale=1">

<title>ALHIKAM Admin Login</title>

<style>

body{
    font-family:Arial,sans-serif;
    background:#f5f7f9;
    padding:20px;
    margin:0;
}

.container{
    max-width:450px;
    margin:60px auto;
}

.card{
    background:white;
    padding:25px;
    border-radius:15px;
    box-shadow:0 3px 12px rgba(0,0,0,.08);
}

h2{
    color:#087f5b;
    margin-top:0;
}

input{
    width:100%;
    padding:14px;
    box-sizing:border-box;
    border:1px solid #ccc;
    border-radius:8px;
    font-size:16px;
    margin-top:10px;
}

button{
    width:100%;
    padding:15px;
    margin-top:18px;
    background:#087f5b;
    color:white;
    border:none;
    border-radius:10px;
    font-size:17px;
    font-weight:bold;
}

.error{
    background:#ffe8e8;
    color:#a00000;
    padding:12px;
    border-radius:8px;
    margin-bottom:15px;
}

</style>

</head>

<body>

<div class="container">

<div class="card">

<h2>
🔐 ALHIKAM Admin
</h2>

<p>
Enter admin password to continue.
</p>

{% if error %}

<div class="error">
{{ error }}
</div>

{% endif %}

<form method="POST">

<input
type="password"
name="password"
placeholder="Admin Password"
required
>

<button type="submit">
🔓 LOGIN
</button>

</form>

</div>

</div>

</body>

</html>

"""


# ==========================================================
# CREATE PROMOTER HTML
# ==========================================================

ADMIN_REFERRAL_HTML = """

<!DOCTYPE html>

<html>

<head>

<meta name="viewport"
content="width=device-width, initial-scale=1">

<title>
ALHIKAM Admin - Create Promoter
</title>

<style>

body{
    font-family:Arial,sans-serif;
    background:#f5f7f9;
    padding:20px;
    margin:0;
}

.container{
    max-width:550px;
    margin:auto;
}

.card{
    background:white;
    padding:25px;
    border-radius:15px;
    box-shadow:0 3px 12px rgba(0,0,0,.08);
}

h2{
    margin-top:0;
    color:#087f5b;
}

label{
    display:block;
    margin-top:15px;
    margin-bottom:6px;
    font-weight:bold;
}

input{
    width:100%;
    padding:14px;
    box-sizing:border-box;
    border:1px solid #ccc;
    border-radius:8px;
    font-size:16px;
}

button{
    width:100%;
    padding:15px;
    margin-top:20px;
    background:#087f5b;
    color:white;
    border:none;
    border-radius:10px;
    font-size:17px;
    font-weight:bold;
}

.success{
    background:#e8f7ef;
    padding:18px;
    border-radius:10px;
    margin-top:20px;
}

.code{
    background:#eef8f4;
    padding:14px;
    border-radius:8px;
    font-size:20px;
    font-weight:bold;
    word-break:break-all;
}

.link{
    background:#f4f4f4;
    padding:14px;
    border-radius:8px;
    font-size:14px;
    word-break:break-all;
    margin-top:8px;
}

.small{
    color:#666;
    font-size:13px;
    line-height:1.5;
}

.error{
    background:#ffe8e8;
    color:#a00000;
    padding:15px;
    border-radius:8px;
    margin-bottom:15px;
}

.logout{
    display:block;
    text-align:center;
    margin-top:20px;
    color:#087f5b;
    text-decoration:none;
}

</style>

</head>

<body>

<div class="container">

<div class="card">

<h2>
🎯 Create Referral Promoter
</h2>

<p class="small">

Create a new promoter account.

The system will automatically generate
a unique referral code.

</p>


{% if error %}

<div class="error">

{{ error }}

</div>

{% endif %}


<form method="POST">


<label>
Full Name
</label>

<input
type="text"
name="full_name"
placeholder="Enter promoter full name"
value="{{ full_name }}"
required
>


<label>
Phone Number
</label>

<input
type="text"
name="phone"
placeholder="08012345678"
value="{{ phone }}"
>


<label>
Email
</label>

<input
type="email"
name="email"
placeholder="example@gmail.com"
value="{{ email }}"
>


<label>
Commission Rate (%)
</label>

<input
type="number"
name="commission_rate"
value="{{ commission_rate }}"
min="0"
max="100"
step="0.01"
required
>


<button type="submit">

➕ CREATE PROMOTER

</button>

</form>


{% if promoter %}

<div class="success">

<h3>
✅ Promoter Created Successfully
</h3>


<p>
<b>Promoter ID:</b>
{{ promoter_id }}
</p>


<p>
<b>Name:</b>
{{ promoter_name }}
</p>


<p>
<b>Commission:</b>
{{ promoter_rate }}%
</p>


<p>
<b>Referral Code:</b>
</p>

<div class="code">

{{ referral_code }}

</div>


<p>
<b>Referral Link:</b>
</p>

<div class="link">

{{ referral_link }}

</div>


<p>
<b>Dashboard Link:</b>
</p>

<div class="link">

{{ dashboard_link }}

</div>

</div>

{% endif %}


<a
class="logout"
href="/admin/referral"
>
← Back to Admin
</a>


</div>

</div>

</body>

</html>

"""


# ==========================================================
# ADMIN REFERRAL PAGE
# ==========================================================

def admin_referral_page():

    error = ""

    promoter = False

    promoter_id = ""

    promoter_name = ""

    promoter_rate = ""

    referral_code = ""

    referral_link = ""

    dashboard_link = ""

    full_name = ""

    phone = ""

    email = ""

    commission_rate = "20"


    # ======================================================
    # POST
    # ======================================================

    if request.method == "POST":

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


        commission_rate = (
            request.form.get(
                "commission_rate",
                "20"
            )
            or "20"
        ).strip()


        # --------------------------------------------------
        # Validate name
        # --------------------------------------------------

        if not full_name:

            error = (
                "Full name is required."
            )


        # --------------------------------------------------
        # Validate commission
        # --------------------------------------------------

        commission_value = 20

        if not error:

            try:

                commission_value = float(
                    commission_rate
                )

            except Exception:

                error = (
                    "Invalid commission rate."
                )


        if not error:

            if (
                commission_value < 0
                or commission_value > 100
            ):

                error = (
                    "Commission rate must be "
                    "between 0 and 100."
                )


        # ==================================================
        # CREATE PROMOTER
        # ==================================================

        if not error:

            try:

                referral_code = (
                    generate_referral_code()
                )


                promoter_id = add_promoter(

                    full_name=full_name,

                    phone=phone,

                    email=email,

                    referral_code=referral_code,

                    commission_rate=commission_value,

                )


                promoter = True

                promoter_name = full_name

                promoter_rate = commission_value


                referral_link = (
                    f"{APP_URL}/payment"
                    f"?ref={referral_code}"
                )


                dashboard_link = (
                    f"{APP_URL}/referral-dashboard"
                    f"?ref={referral_code}"
                )


            except Exception as e:

                print(
                    "ADMIN PROMOTER ERROR:",
                    repr(e)
                )

                error = (
                    "Unable to create promoter."
                )


    # ======================================================
    # RENDER
    # ======================================================

    return render_template_string(

        ADMIN_REFERRAL_HTML,

        error=error,

        promoter=promoter,

        promoter_id=promoter_id,

        promoter_name=promoter_name,

        promoter_rate=promoter_rate,

        referral_code=referral_code,

        referral_link=referral_link,

        dashboard_link=dashboard_link,

        full_name=full_name,

        phone=phone,

        email=email,

        commission_rate=commission_rate,

    )