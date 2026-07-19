from telegram import Update, ReplyKeyboardMarkup

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

import os

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Registration States
FULL_NAME, PHONE, EMAIL, COURSE = range(4)

# Temporary storage
student_data = {}

menu = [
    ["📚 Courses", "📝 CBT Practice"],
    ["👤 Student Registration", "💳 Pay School Fees"],
    ["📞 Contact Us", "ℹ️ About Us"],
]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = ReplyKeyboardMarkup(menu, resize_keyboard=True)

    await update.message.reply_text(
        "🎓 *ALHIKAM Learning Center*\n\n"
        "Welcome to ALHIKAM Learning Center.\n"
        "Please choose an option below.",
        parse_mode="Markdown",
        reply_markup=keyboard,
    )

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👤 STUDENT REGISTRATION\n\n"
        "Please enter your Full Name:"
    )
    return FULL_NAME


async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "📚 Courses":
        await update.message.reply_text(
            "📚 Courses will be available soon."
        )

    elif text == "📝 CBT Practice":
        await update.message.reply_text(
            "📝 CBT Practice is under development."
        )

    elif text == "👤 Student Registration":
        await update.message.reply_text(
            "👤 Student Registration will be available soon."
        )

    elif text == "💳 Pay School Fees":
        await update.message.reply_text(
            "💳 Flutterwave payment will be added soon."
        )

    elif text == "📞 Contact Us":
        await update.message.reply_text(
            "📞 Email: support@alhikam.com"
        )

    elif text == "ℹ️ About Us":
        await update.message.reply_text(
            "🎓 ALHIKAM Learning Center\n\n"
            "JAMB • WAEC • NECO • CBT Training"
        )

    else:
        await update.message.reply_text(
            "Please choose an option from the menu."
        )


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler)
    )

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()