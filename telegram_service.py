# ==========================================================
# ALHIKAM LEARNING CENTER V2
# telegram_service.py
# TELEGRAM INVITE LINKS
# ==========================================================

from datetime import datetime, timedelta

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

    INVITE_LINK_EXPIRE_MINUTES,
    INVITE_LINK_MEMBER_LIMIT,
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

    expire = (

        datetime.utcnow()
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
    # ANNOUNCEMENT CHANNEL
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
    # SCIENCE
    # ======================================================

    if faculty == "Science":

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

    elif faculty == "Arts":

        links.append(

            (
                "🎓 Arts Faculty",

                await create_invite(
                    ARTS_FACULTY_ID
                )

            )

        )


    # ======================================================
    # COMMERCIAL
    # ======================================================

    elif faculty == "Commercial":

        links.append(

            (
                "🎓 Commercial Faculty",

                await create_invite(
                    COMMERCIAL_FACULTY_ID
                )

            )

        )


    # ======================================================
    # BUILD MESSAGE
    # ======================================================

    text = (

        "🎉 Registration Completed Successfully!\n\n"

        "Welcome to ALHIKAM Learning Center.\n\n"

        "🔗 Click the links below to join your classes:\n\n"

    )


    for title, link in links:

        text += (

            f"{title}\n"
            f"{link}\n\n"

        )


    # ======================================================
    # SEND LINKS
    # ======================================================

    await send_message(
        chat_id,
        text
    )


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