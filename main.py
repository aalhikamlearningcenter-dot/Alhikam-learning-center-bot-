from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")# Registration States
FULL_NAME = 1
PHONE = 2

# Temporary storage
student_data = {}

menu = [
    ["📚 Courses", "📝 CBT Practice"],
    ["👤 Student Registration", "💳 Pay School Fees"],
    ["📞 Contact Us", "ℹ️ About Us"]

]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = ReplyKeyboardMarkup(menu, resize_keyboard=True)

    await update.message.reply_text(
    "🎓 *ALHIKAM Learning Center*\n\n"
    "Welcome to ALHIKAM Learning Center!\n\n"
    "Please choose an option from the menu below.",
    parse_mode="Markdown",
    reply_markup=keyboard

    )

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "📚 Darussa":
        await update.message.reply_text("📚 Courses will be available soon.")

    elif text == "📝 CBT Practice":
        await update.message.reply_text("📝 CBT Practice is under development.")

    elif text == "💳 Biya Kudin Karatu":
        await update.message.reply_text("💳 Flutterwave payment will be added soon.")

    elif text == "👤 Rajista":
        await update.message.reply_text(
            "👤 STUDENT REGISTRATION\n\n"
            "Please send your Full Name."
        )

    elif text == "📞 Tuntuɓe Mu":
        await update.message.reply_text("📞 Email: support@alhikam.com")

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()