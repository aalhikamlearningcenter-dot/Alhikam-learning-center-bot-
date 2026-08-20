# ==========================================================
# ALHIKAM LEARNING CENTER V2
# config.py
# ==========================================================

import os


# ==========================================================
# APP
# ==========================================================

APP_NAME = "ALHIKAM Learning Center"

APP_URL = os.getenv(
    "APP_URL",
    "https://precious-trust-production-956b.up.railway.app"
).rstrip("/")

BOT_USERNAME = "Alhikamcenterbot"


# ==========================================================
# TELEGRAM
# ==========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")


# ==========================================================
# FLUTTERWAVE
# ==========================================================

FLW_PUBLIC_KEY = os.getenv("FLW_PUBLIC_KEY")

FLW_SECRET_KEY = os.getenv("FLW_SECRET_KEY")

FLW_ENCRYPTION_KEY = os.getenv("FLW_ENCRYPTION_KEY")


# ==========================================================
# GOOGLE SHEETS
# ==========================================================

GOOGLE_SCRIPT_URL = os.getenv("GOOGLE_SCRIPT_URL")


# ==========================================================
# DATABASE
# ==========================================================

DATABASE_NAME = os.getenv(
    "DATABASE_NAME",
    "alhikam.db"
)


# ==========================================================
# WHATSAPP
# ==========================================================

WHATSAPP_COMMUNITY_LINK = os.getenv(
    "WHATSAPP_COMMUNITY_LINK",
    ""
)


# ==========================================================
# REFERRAL
# ==========================================================

DEFAULT_COMMISSION_RATE = 20

MINIMUM_WITHDRAWAL = 5000


# ==========================================================
# TELEGRAM GROUPS
# ==========================================================

MAIN_GROUP_ID = -1004384506380

ANNOUNCEMENT_CHANNEL_ID = -1004315707986


# ==========================================================
# FACULTIES
# ==========================================================

SCIENCE_FACULTY_ID = -1004479887604

ARTS_FACULTY_ID = -1004314659728

COMMERCIAL_FACULTY_ID = -1003967146846


# ==========================================================
# SCIENCE SUBJECTS
# ==========================================================

PHYSICS_ID = -1004467391688

CHEMISTRY_ID = -1003575115831

BIOLOGY_ID = -1004412247385

MATHEMATICS_ID = -1004480230539

AGRICULTURAL_SCIENCE_ID = -1004398599335

GEOGRAPHY_ID = -1003901130871


# ==========================================================
# ARTS SUBJECTS
# ==========================================================

LITERATURE_ID = None

GOVERNMENT_ID = None

ISLAMIC_STUDIES_ID = None

HISTORY_ID = None

CIVIC_EDUCATION_ID = None


# ==========================================================
# COMMERCIAL SUBJECTS
# ==========================================================

ACCOUNTING_ID = None

COMMERCE_ID = None

ECONOMICS_ID = None

OFFICE_PRACTICE_ID = None

MARKETING_ID = None


# ==========================================================
# INVITE LINKS
# ==========================================================

INVITE_LINK_EXPIRE_MINUTES = 10

INVITE_LINK_MEMBER_LIMIT = 1


# ==========================================================
# PAYMENT PLANS
# ==========================================================

PAYMENT_PLANS = {

    "1": ("1 Month", 3600),

    "2": ("2 Months", 6800),

    "3": ("3 Months", 10000),

    "4": ("4 Months", 13600),

    "5": ("5 Months", 16500),

    "6": ("6 Months", 20000),

}