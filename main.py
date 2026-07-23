from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")


async def get_channel_id(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.channel_post:

        chat = update.channel_post.chat

        print("================================")
        print("CHANNEL NAME:", chat.title)
        print("CHANNEL ID:", chat.id)
        print("================================")

        # Ba da amsa a log kawai


def main():

    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is missing")

    app = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )

    app.add_handler(
        MessageHandler(
            filters.ALL,
            get_channel_id
        )
    )

    print("Chat ID Finder is running...")

    app.run_polling()


if __name__ == "__main__":
    main()