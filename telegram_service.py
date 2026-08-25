# ==========================================================
# ALHIKAM LEARNING CENTER V2
# telegram_service.py
#
# TELEGRAM + WHATSAPP COMMUNITY
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

    await bot.send_message(

        chat_id=chat_id,

        text=text,

        disable_web_page_preview=True

    )


# ==========================================================
# CREATE INVITE LINK
# ==========================================================

async def create_invite(
    chat_id
):

    if not chat_id:

        raise ValueError(
            "Telegram chat ID is missing."
        )


    expire = (

        datetime.now(
            timezone.utc
        )

        +

        timedelta(
            minutes=INVITE_LINK_EXPIRE_MINUTES
        )

    )


    invite = await bot.create_chat_invite_link(

        chat_id=chat_id,

        expire_date=expire,

        member_limit=INVITE_LINK_MEMBER_LIMIT

    )


    return invite.invite_link


# ==========================================================
# SEND STUDENT LINKS
# ==========================================================

async def send_student_links(
    chat_id,
    faculty
):

    faculty = (
        faculty
        or ""
    ).strip()


    # ------------------------------------------------------
    # NORMALIZE FACULTY
    # ------------------------------------------------------

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

    links.append(

        (
            "🏠 Main Group",
            await create_invite(
                MAIN_GROUP_ID
            )
        )

    )


    # ======================================================
    # ANNOUNCEMENT
    # ======================================================

    links.append(

        (
            "📢 Announcement Channel",
            await create_invite(
                ANNOUNCEMENT_CHANNEL_ID
            )
        )

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


    # ======================================================
    # SCIENCE
    # ======================================================

    if faculty_name == "Science":

        links.append(

            (
                "🎓 Science Faculty",
                await create_invite(
                    SCIENCE_FACULTY_ID
                )
            )

        )


        links.append(

            (
                "📘 Physics",
                await create_invite(
                    PHYSICS_ID
                )
            )

        )


        links.append(

            (
                "🧪 Chemistry",
                await create_invite(
                    CHEMISTRY_ID
                )
            )

        )


        links.append(

            (
                "🧬 Biology",
                await create_invite(
                    BIOLOGY_ID
                )
            )

        )


        links.append(

            (
                "📐 Mathematics",
                await create_invite(
                    MATHEMATICS_ID
                )
            )

        )


        links.append(

            (
                "🌾 Agricultural Science",
                await create_invite(
                    AGRICULTURAL_SCIENCE_ID
                )
            )

        )


        links.append(

            (
                "🌍 Geography",
                await create_invite(
                    GEOGRAPHY_ID
                )
            )

        )


    # ======================================================
    # ARTS
    # ======================================================

    elif faculty_name == "Arts":

        links.append(

            (
                "🎓 Arts Faculty",
                await create_invite(
                    ARTS_FACULTY_ID
                )
            )

        )


        links.append(

            (
                "🎭 Fine Arts",
                await create_invite(
                    FINE_ARTS_ID
                )
            )

        )


        links.append(

            (
                "🕰️ History",
                await create_invite(
                    HISTORY_ID
                )
            )

        )


        links.append(

            (
                "🗣️ Hausa",
                await create_invite(
                    HAUSA_ID
                )
            )

        )


        links.append(

            (
                "✝️ CRS",
                await create_invite(
                    CRS_ID
                )
            )

        )


        links.append(

            (
                "🕌 Islamic Studies (IRS)",
                await create_invite(
                    ISLAMIC_STUDIES_ID
                )
            )

        )


        links.append(

            (
                "🌍 Government",
                await create_invite(
                    GOVERNMENT_ID
                )
            )

        )


        links.append(

            (
                "📖 Literature in English",
                await create_invite(
                    LITERATURE_ID
                )
            )

        )


        links.append(

            (
                "📖 Use of English",
                await create_invite(
                    USE_OF_ENGLISH_ID
                )
            )

        )


    # ======================================================
    # COMMERCIAL
    # ======================================================

    elif faculty_name == "Commercial":

        links.append(

            (
                "💼 Commercial Faculty",
                await create_invite(
                    COMMERCIAL_FACULTY_ID
                )
            )

        )


        links.append(

            (
                "📚 Principles of Accounts",
                await create_invite(
                    PRINCIPLES_OF_ACCOUNTS_ID
                )
            )

        )


        links.append(

            (
                "📊 Commerce",
                await create_invite(
                    COMMERCE_ID
                )
            )

        )


        links.append(

            (
                "💼 Economics",
                await create_invite(
                    ECONOMICS_ID
                )
            )

        )


        links.append(

            (
                "🎭 Fine Arts",
                await create_invite(
                    FINE_ARTS_ID
                )
            )

        )


        links.append(

            (
                "🕰️ History",
                await create_invite(
                    HISTORY_ID
                )
            )

        )


        links.append(

            (
                "🗣️ Hausa",
                await create_invite(
                    HAUSA_ID
                )
            )

        )


        links.append(

            (
                "✝️ CRS",
                await create_invite(
                    CRS_ID
                )
            )

        )


        links.append(

            (
                "🕌 Islamic Studies (IRS)",
                await create_invite(
                    ISLAMIC_STUDIES_ID
                )
            )

        )


        links.append(

            (
                "🌍 Government",
                await create_invite(
                    GOVERNMENT_ID
                )
            )

        )


        links.append(

            (
                "📖 Literature in English",
                await create_invite(
                    LITERATURE_ID
                )
            )

        )


        links.append(

            (
                "📖 Use of English",
                await create_invite(
                    USE_OF_ENGLISH_ID
                )
            )

        )


    # ======================================================
    # MESSAGE
    # ======================================================

    text = (

        "🎉 ALHIKAM Registration Completed!\n\n"

        "Welcome to ALHIKAM Learning Center.\n\n"

        f"🎓 Faculty: {faculty_name}\n\n"

        "Click each link below to join your "
        "classes and community:\n\n"

    )


    for title, link in links:

        text += (

            f"{title}\n"
            f"{link}\n\n"

        )


    text += (

        "⚠️ Important:\n"
        "Telegram invitation links are limited to "
        "one student and expire after "
        f"{INVITE_LINK_EXPIRE_MINUTES} minutes.\n\n"

        "💬 Please make sure you join the WhatsApp "
        "Community as well."

    )


    # ======================================================
    # SEND
    # ======================================================

    await send_message(

        chat_id,

        text

    )


    return links


# ==========================================================
# WELCOME
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