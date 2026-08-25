# ==========================================================
# ALHIKAM LEARNING CENTER V2
# telegram_service.py
#
# TELEGRAM LINKS
#   ↓
# MAIN GROUP
#   ↓
# ANNOUNCEMENT CHANNEL
#   ↓
# FACULTY
#   ↓
# SUBJECTS
#   ↓
# WHATSAPP COMMUNITY
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

    INVITE_LINK_EXPIRE_MINUTES,
    INVITE_LINK_MEMBER_LIMIT,
)


# ==========================================================
# WHATSAPP COMMUNITY
# ==========================================================

WHATSAPP_COMMUNITY_LINK = (
    "https://chat.whatsapp.com/GvypYrvjtTECNh2MsONyKa"
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
# CREATE TELEGRAM INVITE LINK
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

    links = []


    # ======================================================
    # MAIN GROUP
    # ======================================================

    try:

        main_link = await create_invite(
            MAIN_GROUP_ID
        )

        links.append(
            (
                "🏠 Main Group",
                main_link
            )
        )

        print(
            "MAIN GROUP LINK CREATED"
        )

    except Exception as e:

        print(
            "MAIN GROUP LINK ERROR:",
            repr(e)
        )


    # ======================================================
    # ANNOUNCEMENT CHANNEL
    # ======================================================

    try:

        announcement_link = await create_invite(
            ANNOUNCEMENT_CHANNEL_ID
        )

        links.append(
            (
                "📢 Announcement Channel",
                announcement_link
            )
        )

        print(
            "ANNOUNCEMENT LINK CREATED"
        )

    except Exception as e:

        print(
            "ANNOUNCEMENT LINK ERROR:",
            repr(e)
        )


    # ======================================================
    # SCIENCE
    # ======================================================

    if faculty == "Science":

        # --------------------------------------------------
        # SCIENCE FACULTY
        # --------------------------------------------------

        try:

            science_link = await create_invite(
                SCIENCE_FACULTY_ID
            )

            links.append(
                (
                    "🎓 Science Faculty",
                    science_link
                )
            )

            print(
                "SCIENCE FACULTY LINK CREATED"
            )

        except Exception as e:

            print(
                "SCIENCE FACULTY LINK ERROR:",
                repr(e)
            )


        # --------------------------------------------------
        # PHYSICS
        # --------------------------------------------------

        try:

            physics_link = await create_invite(
                PHYSICS_ID
            )

            links.append(
                (
                    "📘 Physics",
                    physics_link
                )
            )

            print(
                "PHYSICS LINK CREATED"
            )

        except Exception as e:

            print(
                "PHYSICS LINK ERROR:",
                repr(e)
            )


        # --------------------------------------------------
        # CHEMISTRY
        # --------------------------------------------------

        try:

            chemistry_link = await create_invite(
                CHEMISTRY_ID
            )

            links.append(
                (
                    "🧪 Chemistry",
                    chemistry_link
                )
            )

            print(
                "CHEMISTRY LINK CREATED"
            )

        except Exception as e:

            print(
                "CHEMISTRY LINK ERROR:",
                repr(e)
            )


        # --------------------------------------------------
        # BIOLOGY
        # --------------------------------------------------

        try:

            biology_link = await create_invite(
                BIOLOGY_ID
            )

            links.append(
                (
                    "🧬 Biology",
                    biology_link
                )
            )

            print(
                "BIOLOGY LINK CREATED"
            )

        except Exception as e:

            print(
                "BIOLOGY LINK ERROR:",
                repr(e)
            )


        # --------------------------------------------------
        # MATHEMATICS
        # --------------------------------------------------

        try:

            mathematics_link = await create_invite(
                MATHEMATICS_ID
            )

            links.append(
                (
                    "📐 Mathematics",
                    mathematics_link
                )
            )

            print(
                "MATHEMATICS LINK CREATED"
            )

        except Exception as e:

            print(
                "MATHEMATICS LINK ERROR:",
                repr(e)
            )


        # --------------------------------------------------
        # AGRICULTURAL SCIENCE
        # --------------------------------------------------

        try:

            agricultural_link = await create_invite(
                AGRICULTURAL_SCIENCE_ID
            )

            links.append(
                (
                    "🌾 Agricultural Science",
                    agricultural_link
                )
            )

            print(
                "AGRICULTURAL SCIENCE LINK CREATED"
            )

        except Exception as e:

            print(
                "AGRICULTURAL SCIENCE LINK ERROR:",
                repr(e)
            )


        # --------------------------------------------------
        # GEOGRAPHY
        # --------------------------------------------------

        try:

            geography_link = await create_invite(
                GEOGRAPHY_ID
            )

            links.append(
                (
                    "🌍 Geography",
                    geography_link
                )
            )

            print(
                "GEOGRAPHY LINK CREATED"
            )

        except Exception as e:

            print(
                "GEOGRAPHY LINK ERROR:",
                repr(e)
            )


    # ======================================================
    # ARTS
    # ======================================================

    elif faculty == "Arts":

        try:

            arts_link = await create_invite(
                ARTS_FACULTY_ID
            )

            links.append(
                (
                    "🎓 Arts Faculty",
                    arts_link
                )
            )

            print(
                "ARTS FACULTY LINK CREATED"
            )

        except Exception as e:

            print(
                "ARTS FACULTY LINK ERROR:",
                repr(e)
            )


    # ======================================================
    # COMMERCIAL
    # ======================================================

    elif faculty == "Commercial":

        try:

            commercial_link = await create_invite(
                COMMERCIAL_FACULTY_ID
            )

            links.append(
                (
                    "🎓 Commercial Faculty",
                    commercial_link
                )
            )

            print(
                "COMMERCIAL FACULTY LINK CREATED"
            )

        except Exception as e:

            print(
                "COMMERCIAL FACULTY LINK ERROR:",
                repr(e)
            )


    # ======================================================
    # INVALID FACULTY
    # ======================================================

    else:

        print(
            f"WARNING: Invalid faculty received: {faculty}"
        )


    # ======================================================
    # WHATSAPP COMMUNITY
    #
    # Wannan ba Telegram invite ba ne.
    # Direct WhatsApp Community link ne.
    # ======================================================

    links.append(
        (
            "💬 WhatsApp Community",
            WHATSAPP_COMMUNITY_LINK
        )
    )


    print(
        "WHATSAPP COMMUNITY LINK ADDED"
    )


    # ======================================================
    # CHECK IF TELEGRAM LINKS EXIST
    # ======================================================

    telegram_link_count = len(
        links
    ) - 1


    if telegram_link_count <= 0:

        raise RuntimeError(
            "No Telegram invitation links were created."
        )


    # ======================================================
    # MESSAGE
    # ======================================================

    text = (

        "🎉 ALHIKAM Registration Completed!\n\n"

        "Welcome to ALHIKAM Learning Center. ❤️\n\n"

        "✅ Your registration has been successfully "
        "connected to your Telegram account.\n\n"

        "📚 Please click each link below to join "
        "your classes and community:\n\n"

    )


    for title, link in links:

        text += (

            f"{title}\n"
            f"{link}\n\n"

        )


    text += (

        "⚠️ Important:\n"
        "Please join all the groups/channels that "
        "apply to your faculty.\n\n"

        "💬 Also join our WhatsApp Community to "
        "receive important updates and announcements.\n\n"

        "🎓 Welcome once again to ALHIKAM Learning Center!"

    )


    # ======================================================
    # SEND ALL LINKS TO STUDENT
    # ======================================================

    await send_message(

        chat_id,

        text

    )


    # ======================================================
    # FINAL LOG
    # ======================================================

    print(
        "=================================================="
    )

    print(
        "STUDENT LINKS RESULT"
    )

    print(
        f"TELEGRAM_ID={chat_id}"
    )

    print(
        f"FACULTY={faculty}"
    )

    print(
        f"TOTAL_LINKS_SENT={len(links)}"
    )

    print(
        f"TELEGRAM_LINKS={telegram_link_count}"
    )

    print(
        "WHATSAPP_COMMUNITY=YES"
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