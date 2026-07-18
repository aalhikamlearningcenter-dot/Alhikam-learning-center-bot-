from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")

menu = [
    ["📚 Darussa", "📝 CBT Practice"],
    ["💳 Biya Kudin Karatu", "👤 Rajista"],
    ["📞 Tuntuɓe Mu"]
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = ReplyKeyboardMarkup(menu, resize_keyboard=True)

    await update.message.reply_text(
        "🎓 *ALHIKAM Learning Center*\n\n"
        "Barka da zuwa!\n\n"
        "Zaɓi abin da kake so daga menu na ƙasa.",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "📚 Darussa":
        await update.message.reply_text("📚elif text == "👤 Student Registration":
    await update.message.reply_text(
        "👤 STUDENT REGISTRATION\n\n"
        "Please send your Full Name."
    )

    elif text == "📝 CBT Practice":
        await update.message.reply_text("📝 CBT Practice yana kan ginawa.")

    elif text == "💳 Biya Kudin Karatu":
        await update.message.reply_text("💳 Za a haɗa Flutterwave payment nan.")

    elif text == "👤 Rajista":
        await update.message.reply_text("👤 Rajista zai fara nan ba da jimawa ba.")

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