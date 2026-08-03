from telegram import Bot
import os
from datetime import datetime, timedelta

from config import (
    MAIN_GROUP_ID,
    SCIENCE_FACULTY_ID,
    ARTS_FACULTY_ID,
    COMMERCIAL_FACULTY_ID,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)


async def send_message(chat_id, text):
    await bot.send_message(
        chat_id=chat_id,
        text=text
    )


async def create_unique_invite_link():

    expire_time = datetime.utcnow() + timedelta(minutes=10)

    invite = await bot.create_chat_invite_link(
        chat_id=MAIN_GROUP_ID,
        expire_date=expire_time,
        member_limit=1,
    )

    return invite.invite_link


async def create_faculty_invite_link(faculty):

    if faculty == "Science":
        chat_id = SCIENCE_FACULTY_ID

    elif faculty == "Arts":
        chat_id = ARTS_FACULTY_ID

    elif faculty == "Commercial":
        chat_id = COMMERCIAL_FACULTY_ID

    else:
        return None

    expire_time = datetime.utcnow() + timedelta(minutes=10)

    invite = await bot.create_chat_invite_link(
        chat_id=chat_id,
        expire_date=expire_time,
        member_limit=1,
    )

    return invite.invite_link


async def send_welcome_message(chat_id, full_name):

async def send_student_links(chat_id, faculty):

    main_link = await create_unique_invite_link()

    faculty_link = await create_faculty_invite_link(faculty)

    text = f"""
🎉 Registration Completed Successfully

Welcome to ALHIKAM Learning Center.

Please join your official groups below.

👥 Main Group
{main_link}

🎓 Faculty Group
{faculty_link}
"""

    await send_message(chat_id, text)

    text = f"""
🎉 Welcome to ALHIKAM Learning Center

Hello {full_name},

✅ Your registration has been received successfully.

Please wait while we verify your payment and assign you to your faculty and subject channels.

Thank you for choosing ALHIKAM.
"""

    await send_message(chat_id, text)