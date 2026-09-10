# ============================================================
# REGISTRATION HTML
# ============================================================

REGISTRATION_HTML = """
<!DOCTYPE html>
<html>

<head>

<meta name="viewport"
      content="width=device-width, initial-scale=1">

<title>
ALHIKAM Student Registration
</title>

<style>

body{
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
    margin-bottom:25px;
}

.info{
    background:#eef8f4;
    padding:15px;
    border-radius:10px;
    margin-bottom:20px;
    line-height:1.7;
}

.connected{
    background:#e8f5e9;
    padding:14px;
    border-radius:10px;
    margin-bottom:20px;
    line-height:1.7;
}

.referral{
    background:#f0f8f5;
    border:1px solid #cdeee1;
    padding:15px;
    border-radius:10px;
    margin-bottom:20px;
    line-height:1.7;
}

.referral-title{
    color:#087f5b;
    font-weight:bold;
    font-size:16px;
}

.referral-code{
    display:block;
    margin-top:8px;
    padding:10px;
    background:white;
    border-radius:8px;
    border:1px solid #cdeee1;
    font-weight:bold;
    color:#087f5b;
    word-break:break-all;
}

.no-referral{
    color:#666;
}

label{
    display:block;
    margin-top:8px;
    font-weight:bold;
}

input,
select{
    width:100%;
    padding:13px;
    margin:8px 0 15px;
    border:1px solid #ddd;
    border-radius:8px;
    box-sizing:border-box;
    font-size:16px;
}

.readonly{
    background:#f5f5f5;
    color:#555;
}

button{
    width:100%;
    padding:15px;
    background:#087f5b;
    color:white;
    border:none;
    border-radius:10px;
    font-size:17px;
    font-weight:bold;
    cursor:pointer;
}

.warning{
    background:#fff8e1;
    padding:12px;
    border-radius:10px;
    margin-bottom:20px;
    color:#6b5200;
}

</style>

</head>

<body>

<div class="container">

<h1>
🎓 ALHIKAM Learning Center
</h1>


<!-- ====================================================== -->
<!-- PAYMENT -->
<!-- ====================================================== -->

<div class="info">

<strong>
Payment Confirmed ✅
</strong>

<br><br>

Plan:
<strong>
{{ plan_name }}
</strong>

<br>

Amount:
<strong>
₦{{ "{:,.0f}".format(amount) }}
</strong>

<br>

Status:
<strong>
✅ Successful
</strong>

</div>


<!-- ====================================================== -->
<!-- TELEGRAM -->
<!-- ====================================================== -->

<div class="connected">

<strong>
📱 Telegram Connected ✅
</strong>

<br><br>

Username:
<strong>
@{{ telegram_username if telegram_username else "Telegram User" }}
</strong>

<br>

Your Telegram ID has been verified automatically.

</div>


<!-- ====================================================== -->
<!-- REFERRAL -->
<!-- ====================================================== -->

<div class="referral">

<div class="referral-title">
🔗 Referral Information
</div>

{% if referral_code %}

<br>

Referral Code:

<span class="referral-code">
{{ referral_code }}
</span>

<br>

Promoter:

<strong>
{{ promoter_name if promoter_name else "ALHIKAM Promoter" }}
</strong>

<br><br>

<small>
✅ This referral is automatically attached to your payment.
</small>

{% else %}

<br>

<span class="no-referral">
No referral code was used for this payment.
</span>

{% endif %}

</div>


<!-- ====================================================== -->
<!-- WARNING -->
<!-- ====================================================== -->

<div class="warning">

<strong>
⚠️ Important
</strong>

<br><br>

Please enter your correct information.
Your registration details will be used to create
your official ALHIKAM student record.

</div>


<!-- ====================================================== -->
<!-- REGISTRATION FORM -->
<!-- ====================================================== -->

<form method="POST">


<input
    type="hidden"
    name="csrf_token"
    value="{{ csrf_token }}"
>


<input
    type="hidden"
    name="referral_code"
    value="{{ referral_code }}"
>


<label>
Full Name
</label>

<input
    type="text"
    name="full_name"
    placeholder="Enter your full name"
    required
>


<label>
Phone Number
</label>

<input
    type="tel"
    name="phone"
    placeholder="08012345678"
    required
>


<label>
Email Address
</label>

<input
    type="email"
    name="email"
    placeholder="example@gmail.com"
    required
>


<label>
Course
</label>

<select
    name="course"
    required
>

<option value="">
Select Course
</option>

<option value="JAMB Science">
JAMB Science
</option>

<option value="JAMB Arts">
JAMB Arts
</option>

<option value="WAEC">
WAEC
</option>

<option value="NECO">
NECO
</option>

<option value="CBT Training">
CBT Training
</option>

</select>


<button type="submit">

✅ COMPLETE REGISTRATION

</button>

</form>

</div>

</body>

</html>
"""