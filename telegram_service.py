# ==========================================================
# ALHIKAM LEARNING CENTER V2
# telegram_service.py
#
# PAYMENT
#   ↓
# REGISTRATION
#   ↓
# TELEGRAM /START
#   ↓
# FIND STUDENT
#   ↓
# DETECT FACULTY
#   ↓
# SEND ALL FACULTY LINKS
#   ↓
# WHATSAPP COMMUNITY
# ==========================================================


from datetime import datetime, timedelta, timezone

from telegram import Bot

from config import (
    BOT_TOKEN,

    # ------------------------------------------------------
    # MAIN
    # ------------------------------------------------------
    MAIN_GROUP_ID,
    ANNOUNCEMENT_CHANNEL_ID,

    # ------------------------------------------------------
    # FACULTIES
    # ------------------------------------------------------
    SCIENCE_FACULTY_ID,
    ARTS_FACULTY_ID,
    COMMERCIAL_FACULTY_ID,

    # ------------------------------------------------------
    # SCIENCE SUBJECTS
    # ------------------------------------------------------
    PHYSICS_ID,
    CHEMISTRY_ID,
    BIOLOGY_ID,
    MATHEMATICS_ID,
    AGRICULTURAL_SCIENCE_ID,
    GEOGRAPHY_ID,

    # ------------------------------------------------------
    # ARTS SUBJECTS
    # ------------------------------------------------------
    GOVERNMENT_ID,
    LITERATURE_ID,
    USE_OF_ENGLISH_ID,
    HISTORY_ID,
    HAUSA_ID,
    CRS_ID,
    ISLAMIC_STUDIES_ID,
    FINE_ARTS_ID,

    # ------------------------------------------------------
    # COMMERCIAL SUBJECTS
    # ------------------------------------------------------
    ACCOUNTING_ID,
    COMMERCE_ID,
    ECONOMICS_ID,

    # ------------------------------------------------------
    # WHATSAPP
    # ------------------------------------------------------
    WHATSAPP_COMMUNITY_LINK,

    # ------------------------------------------------------
    # INVITE SETTINGS
    # ------------------------------------------------------
    INVITE_LINK_EXPIRE_MINUTES,
    INVITE_LINK_MEMBER_LIMIT,
)


# ==========================================================
# BOT
# ==========================================================

if not BOT_TOKEN:

    raise RuntimeError(
        "BOT_TOKEN is not set."
    )


bot = Bot(
    token=BOT_TOKEN
)


# ==========================================================
# SEND MESSAGE
# ==========================================================

async def send_message(
    chat_id,
    text
):

    if not chat_id:

        raise ValueError(
            "Telegram chat ID is missing."
        )

    await bot.send_message(

        chat_id=chat_id,

        text=text,

        disable_web_page_preview=True

    )


# ==========================================================
# CREATE TELEGRAM INVITE LINK
# ==========================================================

async def create_invite(
    chat_id
):

    # ------------------------------------------------------
    # If Telegram ID is missing, skip it.
    # ------------------------------------------------------

    if not chat_id:

        raise ValueError(
            "Telegram chat ID is missing."
        )


    # ------------------------------------------------------
    # Expiration time
    # ------------------------------------------------------

    expire = (

        datetime.now(
            timezone.utc
        )

        +

        timedelta(
            minutes=INVITE_LINK_EXPIRE_MINUTES
        )

    )


    # ------------------------------------------------------
    # Create invite
    # ------------------------------------------------------

    invite = (

        await bot.create_chat_invite_link(

            chat_id=chat_id,

            expire_date=expire,

            member_limit=INVITE_LINK_MEMBER_LIMIT

        )

    )


    return invite.invite_link


# ==========================================================
# SAFE ADD TELEGRAM LINK
#
# Wannan helper yana hana wani missing Telegram ID
# ya sa bot ya crash.
# ==========================================================

async def add_telegram_link(
    links,
    title,
    chat_id
):

    # ------------------------------------------------------
    # Skip missing ID
    # ------------------------------------------------------

    if not chat_id:

        print(
            f"SKIPPED TELEGRAM LINK | "
            f"{title} | ID is missing"
        )

        return


    try:

        link = await create_invite(
            chat_id
        )

        links.append(
            (
                title,
                link
            )
        )

        print(
            f"TELEGRAM LINK CREATED | "
            f"{title} | {chat_id}"
        )


    except Exception as e:

        print(
            f"TELEGRAM LINK FAILED | "
            f"{title} | "
            f"ID={chat_id} | "
            f"ERROR={e}"
        )


# ==========================================================
# SEND WHATSAPP LINK
# ==========================================================

def add_whatsapp_link(
    links
):

    if not WHATSAPP_COMMUNITY_LINK:

        print(
            "WHATSAPP LINK SKIPPED | "
            "WHATSAPP_COMMUNITY_LINK is empty"
        )

        return


    links.append(

        (
            "💬 WhatsApp Community",
            WHATSAPP_COMMUNITY_LINK
        )

    )

    print(
        "WHATSAPP COMMUNITY LINK ADDED"
    )


# ==========================================================
# SEND STUDENT LINKS
# ==========================================================

async def send_student_links(
    chat_id,
    faculty
):

    links = []


    # ======================================================
    # NORMALIZE FACULTY
    # ======================================================

    faculty = (

        str(
            faculty
            or ""
        )

        .strip()

    )


    print(
        "=================================================="
    )

    print(
        "PREPARING STUDENT LINKS"
    )

    print(
        f"TELEGRAM_ID={chat_id}"
    )

    print(
        f"FACULTY={faculty}"
    )

    print(
        "=================================================="
    )


    # ======================================================
    # MAIN GROUP
    # ======================================================

    await add_telegram_link(

        links,

        "🏠 Main Group",

        MAIN_GROUP_ID

    )


    # ======================================================
    # ANNOUNCEMENT CHANNEL
    # ======================================================

    await add_telegram_link(

        links,

        "📢 Announcement Channel",

        ANNOUNCEMENT_CHANNEL_ID

    )


    # ======================================================
    # SCIENCE
    # ======================================================

    if faculty.lower() == "science":

        # --------------------------------------------------
        # Faculty
        # --------------------------------------------------

        await add_telegram_link(

            links,

            "🎓 Science Faculty",

            SCIENCE_FACULTY_ID

        )


        # --------------------------------------------------
        # Physics
        # --------------------------------------------------

        await add_telegram_link(

            links,

            "📘 Physics",

            PHYSICS_ID

        )


        # --------------------------------------------------
        # Chemistry
        # --------------------------------------------------

        await add_telegram_link(

            links,

            "🧪 Chemistry",

            CHEMISTRY_ID

        )


        # --------------------------------------------------
        # Biology
        # --------------------------------------------------

        await add_telegram_link(

            links,

            "🧬 Biology",

            BIOLOGY_ID

        )


        # --------------------------------------------------
        # Mathematics
        # --------------------------------------------------

        await add_telegram_link(

            links,

            "📐 Mathematics",

            MATHEMATICS_ID

        )


        # --------------------------------------------------
        # Agricultural Science
        # --------------------------------------------------

        await add_telegram_link(

            links,

            "🌾 Agricultural Science",

            AGRICULTURAL_SCIENCE_ID

        )


        # --------------------------------------------------
        # Geography
        # --------------------------------------------------

        await add_telegram_link(

            links,

            "🌍 Geography",

            GEOGRAPHY_ID

        )


    # ======================================================
    # ARTS
    # ======================================================

    elif faculty.lower() == "arts":

        # --------------------------------------------------
        # Arts Faculty
        # --------------------------------------------------

        await add_telegram_link(

            links,

            "🎨 Arts Faculty",

            ARTS_FACULTY_ID

        )


        # --------------------------------------------------
        # Government
        # --------------------------------------------------

        await add_telegram_link(

            links,

            "🌍 Government",

            GOVERNMENT_ID

        )


        # --------------------------------------------------
        # Literature
        # --------------------------------------------------

        await add_telegram_link(

            links,

            "📖 Literature in English",

            LITERATURE_ID

        )


        # --------------------------------------------------
        # Use of English
        # --------------------------------------------------

        await add_telegram_link(

            links,

            "📖 Use of English",

            USE_OF_ENGLISH_ID

        )


        # --------------------------------------------------
        # History
        # --------------------------------------------------

        await add_telegram_link(

            links,

            "🕰️ History",

            HISTORY_ID

        )


        # --------------------------------------------------
        # Hausa
        # --------------------------------------------------

        await add_telegram_link(

            links,

            "🗣️ Hausa",

            HAUSA_ID

        )


        # --------------------------------------------------
        # CRS
        # --------------------------------------------------

        await add_telegram_link(

            links,

            "✝️ CRS",

            CRS_ID

        )


        # --------------------------------------------------
        # Islamic Studies
        # --------------------------------------------------

        await add_telegram_link(

            links,

            "🕌 Islamic Studies (IRS)",

            ISLAMIC_STUDIES_ID

        )


        # --------------------------------------------------
        # Fine Arts
        # --------------------------------------------------

        await add_telegram_link(

            links,

            "🎭 Fine Arts",

            FINE_ARTS_ID

        )


        # --------------------------------------------------
        # Geography
        #
        # Same Geography channel used for Science/Arts.
        # --------------------------------------------------

        await add_telegram_link(

            links,

            "🌍 Geography",

            GEOGRAPHY_ID

        )


    # ======================================================
    # COMMERCIAL
    # ======================================================

    elif faculty.lower() == "commercial":

        # --------------------------------------------------
        # Commercial Faculty
        # --------------------------------------------------

        await add_telegram_link(

            links,

            "💼 Commercial Faculty",

            COMMERCIAL_FACULTY_ID

        )


        # --------------------------------------------------
        # Principles of Accounts
        # --------------------------------------------------

        await add_telegram_link(

            links,

            "📚 Principles of Accounts",

            ACCOUNTING_ID

        )


        # --------------------------------------------------
        # Commerce
        # --------------------------------------------------

        await add_telegram_link(

            links,

            "📊 Commerce",

            COMMERCE_ID

        )


        # --------------------------------------------------
        # Economics
        # --------------------------------------------------

        await add_telegram_link(

            links,

            "💼 Economics",

            ECONOMICS_ID

        )


    # ======================================================
    # INVALID FACULTY
    # ======================================================

    else:

        print(
            f"INVALID FACULTY: {faculty}"
        )

        raise ValueError(
            f"Invalid faculty: {faculty}"
        )


    # ======================================================
    # WHATSAPP COMMUNITY
    #
    # Everyone gets WhatsApp Community.
    # ======================================================

    add_whatsapp_link(
        links
    )


    # ======================================================
    # CHECK LINKS
    # ======================================================

    print(
        "=================================================="
    )

    print(
        "STUDENT LINKS PREPARED"
    )

    print(
        f"FACULTY={faculty}"
    )

    print(
        f"TOTAL LINKS={len(links)}"
    )

    for title, link in links:

        print(
            f"LINK: {title}"
        )

    print(
        "=================================================="
    )


    # ======================================================
    # NO LINKS
    # ======================================================

    if not links:

        raise RuntimeError(
            "No student links were created."
        )


    # ======================================================
    # BUILD MESSAGE
    # ======================================================

    text = (

        "🎉 ALHIKAM Registration Completed!\n\n"

        "Welcome to ALHIKAM Learning Center.\n\n"

        "✅ Your registration has been successfully "
        "connected to your Telegram account.\n\n"

        "📚 Please join all your classes using the "
        "links below:\n\n"

    )


    for title, link in links:

        text += (

            f"{title}\n"

            f"{link}\n\n"

        )


    # ======================================================
    # SEND MESSAGE TO STUDENT
    # ======================================================

    await send_message(

        chat_id,

        text

    )


    # ======================================================
    # RETURN RESULT
    #
    # This structure is compatible with bot.py
    # ======================================================

    successful_links = [

        {
            "title": title,
            "link": link
        }

        for title, link in links

    ]


    return {

        "successful_links":
            successful_links,

        "failed_links":
            [],

        "total_links":
            len(links)

    }


# ==========================================================
# WELCOME MESSAGE
# ==========================================================

async def send_welcome_message(
    chat_id,
    full_name
):

    text = (

        f"🎉 Welcome to ALHIKAM Learning Center\n\n"

        f"Hello {full_name},\n\n"

        "✅ Your payment has been verified successfully.\n\n"

        "Please complete your registration.\n\n"

        "Thank you."

    )


    await send_message(

        chat_id,

        text

    )