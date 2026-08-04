from telegram import Bot
import os
from datetime import datetime, timedelta

from config import *

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)


async def send_message(chat_id, text):
    await bot.send_message(
        chat_id=int(chat_id),
        text=text,
        disable_web_page_preview=True,
    )


async def create_invite(chat_id):

    expire_time = datetime.utcnow() + timedelta(minutes=10)

    invite = await bot.create_chat_invite_link(
        chat_id=chat_id,
        expire_date=expire_time,
        member_limit=1,
    )

    return invite.invite_link


async def send_welcome_message(chat_id, full_name):

    text = f"""
🎉 Welcome to ALHIKAM Learning Center

Hello {full_name},

Your registration has been received successfully.
"""

    await send_message(chat_id, text)


async def send_student_links(chat_id, faculty):

    text = "✅ Registration Completed Successfully\n\n"

    # Main Group
    main = await create_invite(MAIN_GROUP_ID)
    text += f"🏠 Main Group\n{main}\n\n"

    # Faculty
    if faculty == "Science":

        faculty_link = await create_invite(SCIENCE_FACULTY_ID)
        physics = await create_invite(PHYSICS_ID)
        chemistry = await create_invite(CHEMISTRY_ID)
        biology = await create_invite(BIOLOGY_ID)
        mathematics = await create_invite(MATHEMATICS_ID)
        agriculture = await create_invite(AGRICULTURAL_SCIENCE_ID)
        geography = await create_invite(GEOGRAPHY_ID)

        text += f"""🎓 Science Faculty
{faculty_link}

📘 Physics
{physics}

🧪 Chemistry
{chemistry}

🧬 Biology
{biology}

📐 Mathematics
{mathematics}

🌾 Agricultural Science
{agriculture}

🌍 Geography
{geography}
"""

    elif faculty == "Arts":

        faculty_link = await create_invite(ARTS_FACULTY_ID)

        text += f"""🎓 Arts Faculty
{faculty_link}
"""

    elif faculty == "Commercial":

        faculty_link = await create_invite(COMMERCIAL_FACULTY_ID)

        text += f"""🎓 Commercial Faculty
{faculty_link}
"""

    await send_message(chat_id, text)