from flask import render_template_string

PAYMENT_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ALHIKAM Payment</title>

<style>

body{
font-family:Arial;
background:#f4f7f6;
padding:20px;
}

.container{
max-width:500px;
margin:auto;
background:white;
padding:25px;
border-radius:15px;
box-shadow:0 4px 12px rgba(0,0,0,.1);
}

select,button{
width:100%;
padding:15px;
margin-top:15px;
border-radius:10px;
}

button{
background:#087f5b;
color:white;
border:none;
font-size:18px;
font-weight:bold;
}

</style>

</head>

<body>

<div class="container">

<h2>🎓 ALHIKAM Learning Center</h2>

<form method="POST">

<select name="plan" required>

<option value="">Select Payment Plan</option>

<option value="1">₦2,000 - Monthly</option>

<option value="2">₦5,000 - Termly</option>

<option value="3">₦10,000 - Annual</option>

</select>

<button type="submit">

Continue To Payment

</button>

</form>

</div>

</body>

</html>
"""