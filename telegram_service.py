# ==========================================================
# ALHIKAM LEARNING CENTER V2
# telegram_service.py
#
# TELEGRAM + WHATSAPP COMMUNITY
# SECURE STUDENT INVITATION SYSTEM
# ==========================================================

from datetime import datetime, timedelta, timezone

from telegram import Bot

from config import (
    BOT_TOKEN,

    MAIN_GROUP_ID,
    ANNOUNCEMENT_CHANNEL_ID,

    SCIENCE_FACULTY_ID,
    ARTS_FACULTY_ID,
    COMMERCIAL_FACULTY_ID,

    PHYSICS_ID,
    CHEMISTRY_ID,
    BIOLOGY_ID,
    MATHEMATICS_ID,
    AGRICULTURAL_SCIENCE_ID,
    GEOGRAPHY_ID,

    PRINCIPLES_OF_ACCOUNTS_ID,
    COMMERCE_ID,
    ECONOMICS_ID,
    FINE_ARTS_ID,
    HISTORY_ID,
    HAUSA_ID,
    CRS_ID,
    ISLAMIC_STUDIES_ID,
    GOVERNMENT_ID,
    LITERATURE_ID,
    USE_OF_ENGLISH_ID,

    WHATSAPP_COMMUNITY_LINK,

    INVITE_LINK_EXPIRE_MINUTES,
    INVITE_LINK_MEMBER_LIMIT,
)


# ==========================================================
# BOT TOKEN CHECK
# ==========================================================

if not BOT_TOKEN:

    raise RuntimeError(
        "BOT_TOKEN is not set."
    )


# ==========================================================
# TELEGRAM BOT
# ==========================================================

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
            "Telegram student chat ID is missing."
        )


    await bot.send_message(

        chat_id=chat_id,

        text=text,

        disable_web_page_preview=True

    )


# ==========================================================
# CREATE ONE INVITATION LINK
# ==========================================================

async def create_invite(
    chat_id,
    chat_name="Telegram Group"
):

    if not chat_id:

        raise ValueError(
            f"{chat_name}: Telegram chat ID is missing."
        )


    # ------------------------------------------------------
    # EXPIRATION TIME
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


    try:

        invite = await bot.create_chat_invite_link(

            chat_id=chat_id,

            expire_date=expire,

            member_limit=INVITE_LINK_MEMBER_LIMIT

        )


        invite_link = (
            invite.invite_link
            or ""
        ).strip()


        if not invite_link:

            raise ValueError(
                f"{chat_name}: Telegram returned an empty invite link."
            )


        print(
            f"✅ INVITE CREATED: {chat_name}"
        )

        print(
            f"   CHAT_ID={chat_id}"
        )

        print(
            f"   LINK={invite_link}"
        )


        return invite_link


    except Exception as e:

        print(
            "=================================================="
        )

        print(
            "❌ INVITE CREATION FAILED"
        )

        print(
            f"CHAT_NAME={chat_name}"
        )

        print(
            f"CHAT_ID={chat_id}"
        )

        print(
            f"ERROR={repr(e)}"
        )

        print(
            "=================================================="
        )

        # --------------------------------------------------
        # IMPORTANT:
        # Do NOT stop the entire process.
        # --------------------------------------------------

        return None


# ==========================================================
# ADD INVITE SAFELY
# ==========================================================

async def add_invite(
    links,
    title,
    chat_id
):

    link = await create_invite(

        chat_id,

        title

    )


    if link:

        links.append(

            (
                title,
                link
            )

        )

        return True


    return False


# ==========================================================
# SEND STUDENT LINKS
# ==========================================================

async def send_student_links(
    chat_id,
    faculty
):

    print(
        "=================================================="
    )

    print(
        "STARTING STUDENT LINK DELIVERY"
    )

    print(
        f"STUDENT_TELEGRAM_ID={chat_id}"
    )

    print(
        f"FACULTY={faculty}"
    )

    print(
        "=================================================="
    )


    # ======================================================
    # VALIDATE STUDENT TELEGRAM ID
    # ======================================================

    if not chat_id:

        raise ValueError(
            "Student Telegram ID is missing."
        )


    chat_id = str(
        chat_id
    ).strip()


    # ======================================================
    # NORMALIZE FACULTY
    # ======================================================

    faculty = (
        faculty
        or ""
    ).strip()


    faculty_lower = faculty.lower()


    if faculty_lower == "science":

        faculty_name = "Science"


    elif faculty_lower == "arts":

        faculty_name = "Arts"


    elif faculty_lower == "commercial":

        faculty_name = "Commercial"


    else:

        raise ValueError(
            f"Invalid faculty: {faculty}"
        )


    # ======================================================
    # LINKS
    # ======================================================

    links = []


    # ======================================================
    # MAIN GROUP
    # ======================================================

    await add_invite(

        links,

        "🏠 Main Group",

        MAIN_GROUP_ID

    )


    # ======================================================
    # ANNOUNCEMENT CHANNEL
    # ======================================================

    await add_invite(

        links,

        "📢 Announcement Channel",

        ANNOUNCEMENT_CHANNEL_ID

    )


    # ======================================================
    # WHATSAPP COMMUNITY
    # ======================================================

    if WHATSAPP_COMMUNITY_LINK:

        links.append(

            (
                "💬 WhatsApp Community",
                WHATSAPP_COMMUNITY_LINK
            )

        )

        print(
            "✅ WhatsApp Community link added."
        )


    # ======================================================
    # SCIENCE
    # ======================================================

    if faculty_name == "Science":

        await add_invite(

            links,

            "🎓 Science Faculty",

            SCIENCE_FACULTY_ID

        )


        await add_invite(

            links,

            "📘 Physics",

            PHYSICS_ID

        )


        await add_invite(

            links,

            "🧪 Chemistry",

            CHEMISTRY_ID

        )


        await add_invite(

            links,

            "🧬 Biology",

            BIOLOGY_ID

        )


        await add_invite(

            links,

            "📐 Mathematics",

            MATHEMATICS_ID

        )


        await add_invite(

            links,

            "🌾 Agricultural Science",

            AGRICULTURAL_SCIENCE_ID

        )


        await add_invite(

            links,

            "🌍 Geography",

            GEOGRAPHY_ID

        )


    # ======================================================
    # ARTS
    # ======================================================

    elif faculty_name == "Arts":

        await add_invite(

            links,

            "🎓 Arts Faculty",

            ARTS_FACULTY_ID

        )


        await add_invite(

            links,

            "🎭 Fine Arts",

            FINE_ARTS_ID

        )


        await add_invite(

            links,

            "🕰️ History",

            HISTORY_ID

        )


        await add_invite(

            links,

            "🗣️ Hausa",

            HAUSA_ID

        )


        await add_invite(

            links,

            "✝️ CRS",

            CRS_ID

        )


        await add_invite(

            links,

            "🕌 Islamic Studies (IRS)",

            ISLAMIC_STUDIES_ID

        )


        await add_invite(

            links,

            "🌍 Government",

            GOVERNMENT_ID

        )


        await add_invite(

            links,

            "📖 Literature in English",

            LITERATURE_ID

        )


        await add_invite(

            links,

            "📖 Use of English",

            USE_OF_ENGLISH_ID

        )


    # ======================================================
    # COMMERCIAL
    # ======================================================

    elif faculty_name == "Commercial":

        await add_invite(

            links,

            "💼 Commercial Faculty",

            COMMERCIAL_FACULTY_ID

        )


        await add_invite(

            links,

            "📚 Principles of Accounts",

            PRINCIPLES_OF_ACCOUNTS_ID

        )


        await add_invite(

            links,

            "📊 Commerce",

            COMMERCE_ID

        )


        await add_invite(

            links,

            "💼 Economics",

            ECONOMICS_ID

        )


        await add_invite(

            links,

            "🎭 Fine Arts",

            FINE_ARTS_ID

        )


        await add_invite(

            links,

            "🕰️ History",

            HISTORY_ID

        )


        await add_invite(

            links,

            "🗣️ Hausa",

            HAUSA_ID

        )


        await add_invite(

            links,

            "✝️ CRS",

            CRS_ID

        )


        await add_invite(

            links,

            "🕌 Islamic Studies (IRS)",

            ISLAMIC_STUDIES_ID

        )


        await add_invite(

            links,

            "🌍 Government",

            GOVERNMENT_ID

        )


        await add_invite(

            links,

            "📖 Literature in English",

            LITERATURE_ID

        )


        await add_invite(

            links,

            "📖 Use of English",

            USE_OF_ENGLISH_ID

        )


    # ======================================================
    # NO LINK CHECK
    # ======================================================

    if not links:

        print(
            "❌ NO LINKS WERE CREATED."
        )

        raise RuntimeError(
            "No Telegram or WhatsApp links could be created."
        )


    # ======================================================
    # BUILD MESSAGE
    # ======================================================

    text = (

        "🎉 ALHIKAM Registration Completed!\n\n"

        "Welcome to ALHIKAM Learning Center.\n\n"

        f"🎓 Faculty: {faculty_name}\n\n"

        "Your class invitation links are ready.\n\n"

        "👇 Click each link below to join your "
        "classes and community:\n\n"

    )


    # ======================================================
    # ADD LINKS
    # ======================================================

    for title, link in links:

        text += (

            f"{title}\n"
            f"{link}\n\n"

        )


    # ======================================================
    # IMPORTANT MESSAGE
    # ======================================================

    text += (

        "⚠️ Important:\n"

        "Telegram invitation links are limited to "
        f"{INVITE_LINK_MEMBER_LIMIT} student "

        "and expire after "

        f"{INVITE_LINK_EXPIRE_MINUTES} minutes.\n\n"

        "💬 Please make sure you join the WhatsApp "
        "Community as well.\n\n"

        "🎓 Welcome to ALHIKAM Learning Center!"

    )


    # ======================================================
    # SEND TO STUDENT
    # ======================================================

    print(
        "=================================================="
    )

    print(
        "SENDING LINKS TO STUDENT"
    )

    print(
        f"TELEGRAM_ID={chat_id}"
    )

    print(
        f"TOTAL_LINKS={len(links)}"
    )

    print(
        "=================================================="
    )


    await send_message(

        chat_id,

        text

    )


    # ======================================================
    # SUCCESS LOG
    # ======================================================

    print(
        "=================================================="
    )

    print(
        "✅ STUDENT LINKS DELIVERED"
    )

    print(
        f"TELEGRAM_ID={chat_id}"
    )

    print(
        f"FACULTY={faculty_name}"
    )

    print(
        f"TOTAL_LINKS={len(links)}"
    )

    print(
        "=================================================="
    )


    return links


# ==========================================================
# WELCOME MESSAGE
# ==========================================================

async def send_welcome_message(
    chat_id,
    full_name
):

    text = (

        "🎉 Welcome to ALHIKAM Learning Center\n\n"

        f"Hello {full_name},\n\n"

        "✅ Your payment has been verified successfully.\n\n"

        "Please complete your registration.\n\n"

        "Thank you."

    )


    await send_message(

        chat_id,

        text

    )