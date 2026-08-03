from flask import request, render_template_string
import asyncio

from telegram_service import create_unique_invite_link
from sheets import save_to_google_sheet
from database import add_student

REGISTRATION_HTML = """
<!DOCTYPE html>
<html>
<head>

<meta name="viewport" content="width=device-width, initial-scale=1">

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

input,select{
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

</style>

</head>

<body>

<div class="container">

<h2>🎓 ALHIKAM Registration</h2>

<form method="POST">

<label>Full Name</label>
<input type="text" name="full_name" required>

<label>Phone Number</label>
<input type="tel" name="phone" required>

<label>Email Address</label>
<input type="email" name="email" required>

<input type="hidden" name="telegram_id" value="{{ telegram_id }}">
<input type="hidden" name="telegram_name" value="{{ telegram_name }}">
<input type="hidden" name="telegram_username" value="{{ telegram_username }}">

<label>Faculty</label>

<select name="faculty" required>

<option value="">Select Faculty</option>
<option value="Science">Science</option>
<option value="Arts">Arts</option>
<option value="Commercial">Commercial</option>

</select>

<button type="submit">
Complete Registration
</button>

</form>

</div>

</body>
</html>
"""


def registration_page():

    if request.method == "GET":

        return render_template_string(
            REGISTRATION_HTML,
            telegram_id=request.args.get("telegram_id", ""),
            telegram_name=request.args.get("telegram_name", ""),
            telegram_username=request.args.get("telegram_username", ""),
        )

    full_name = request.form.get("full_name")
    phone = request.form.get("phone")
    email = request.form.get("email")
    faculty = request.form.get("faculty")

    telegram_id = request.form.get("telegram_id")
    telegram_name = request.form.get("telegram_name")
    telegram_username = request.form.get("telegram_username")

    student_data = {
        "full_name": full_name,
        "phone": phone,
        "email": email,
        "course": faculty,
    }

    database_data = {
        "payment_token": "",
        "tx_ref": "",
        "full_name": full_name,
        "phone": phone,
        "email": email,
        "course": faculty,
        "telegram_id": telegram_id,
        "telegram_username": telegram_username,
        "telegram_name": telegram_name,
        "payment_plan": "",
        "amount_paid": 0,
        "payment_status": "Pending",
        "registration_completed": 1,
    }

    try:
        add_student(database_data)
    except Exception as e:
        print("Database Error:", e)

    try:
        save_to_google_sheet(student_data)
    except Exception as e:
        print("Google Sheets Error:", e)

    invite_link = None

    try:
        invite_link = asyncio.run(create_unique_invite_link())
    except Exception as e:
        print("Invite Link Error:", e)

    if invite_link:

        return f"""
<!DOCTYPE html>
<html>

<head>
<title>Registration Successful</title>
</head>

<body style="font-family:Arial;text-align:center;padding:40px;">

<h2>✅ Registration Successful</h2>

<p>Welcome <b>{full_name}</b></p>

<p>Faculty: <b>{faculty}</b></p>

<br>

<a href="{invite_link}"
style="
background:#087f5b;
color:white;
padding:15px 25px;
text-decoration:none;
border-radius:8px;
font-size:18px;
">

👉 Join ALHIKAM Main Group

</a>

</body>

</html>
"""

    return f"""
<!DOCTYPE html>
<html>

<head>
<title>Registration Successful</title>
</head>

<body style="font-family:Arial;text-align:center;padding:40px;">

<h2>✅ Registration Successful</h2>

<p>Welcome <b>{full_name}</b></p>

<p>Faculty: <b>{faculty}</b></p>

<p>Registration completed successfully.</p>

</body>

</html>
"""