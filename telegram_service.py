from telegram import Bot
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)


async def send_message(chat_id, text):
    await bot.send_message(
        chat_id=chat_id,
        text=text
    )