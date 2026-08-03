from telegram import Bot
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)


async def send_message(chat_id, text):
    await bot.send_message(
        chat_id=chat_id,
        text=text
    )
async def create_unique_invite_link(chat_id):
    ...

async def send_welcome_message(chat_id, full_name):

    text = f"""
🎉 Welcome to ALHIKAM Learning Center

Hello {full_name},

✅ Your registration has been received successfully.

Please wait while we verify your payment and assign you to your faculty and subject channels.

Thank you for choosing ALHIKAM.
"""

    await send_message(chat_id, text)