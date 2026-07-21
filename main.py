from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

import os
import requests

# ==============================
# BOT SETTINGS
# ==============================

BOT_TOKEN = os.getenv("BOT_TOKEN")

SHEET_URL = "YOUR_GOOGLE_APPS_SCRIPT_URL"

# ==============================
# MENU
# ==============================

menu = [
    ["📚 Courses", "📝 CBT Practice"],
    ["👤 Student Registration", "💳 Pay School Fees"],
    ["📞 Contact Us", "ℹ️ About Us"],
]


# ==============================
# START COMMAND
# ==============================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = ReplyKeyboardMarkup(
        menu,
        resize_keyboard=True
    )

    await update.message.reply_text(
        "🎓 *ALHIKAM Learning Center*\n\n"
        "Welcome to ALHIKAM Learning Center.\n\n"
        "Please choose an option below.",
        parse_mode="Markdown",
        reply_markup=keyboard,
    )


# ==============================
# MENU HANDLER
# ==============================

async def menu_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = update.message.text

    # ==============================
    # STUDENT REGISTRATION
    # ==============================

    if text == "👤 Student Registration":

        context.user_data["step"] = "full_name"

        await update.message.reply_text(
            "👤 *STUDENT REGISTRATION*\n\n"
            "Please enter your Full Name:",
            parse_mode="Markdown"
        )

        return


    # ==============================
    # FULL NAME
    # ==============================

    if context.user_data.get("step") == "full_name":

        context.user_data["full_name"] = text
        context.user_data["step"] = "phone"

        await update.message.reply_text(
            "📱 Please enter your Phone Number:"
        )

        return


    # ==============================
    # PHONE
    # ==============================

    if context.user_data.get("step") == "phone":

        context.user_data["phone"] = text
        context.user_data["step"] = "email"

        await update.message.reply_text(
            "📧 Please enter your Email Address:"
        )

        return


    # ==============================
    # EMAIL
    # ==============================

    if context.user_data.get("step") == "email":

        context.user_data["email"] = text
        context.user_data["step"] = "course"

        await update.message.reply_text(
            "📚 Please type your Course.\n\n"
            "Example:\n"
            "JAMB Science\n"
            "JAMB Arts\n"
            "WAEC\n"
            "NECO"
        )

        return


    # ==============================
    # COURSE
    # ==============================

    if context.user_data.get("step") == "course":

        context.user_data["course"] = text
        context.user_data["step"] = None

        # Registration data
        data = {
            "full_name": context.user_data["full_name"],
            "phone": context.user_data["phone"],
            "email": context.user_data["email"],
            "course": context.user_data["course"],
        }

        # Send data to Google Sheet
        try:

            requests.post(
                SHEET_URL,
                json=data,
                timeout=15
            )

        except Exception as e:

            print(
                "Google Sheet Error:",
                e
            )


        # Registration completed
        await update.message.reply_text(
            "✅ *REGISTRATION COMPLETED*\n\n"
            f"👤 Name: {context.user_data['full_name']}\n"
            f"📱 Phone: {context.user_data['phone']}\n"
            f"📧 Email: {context.user_data['email']}\n"
            f"📚 Course: {context.user_data['course']}",
            parse_mode="Markdown"
        )

        return# ==============================
# COURSES
# ==============================

    if text == "📚 Courses":

        await update.message.reply_text(
            "📚 *ALHIKAM COURSES*\n\n"
            "1️⃣ JAMB Science\n"
            "2️⃣ JAMB Arts\n"
            "3️⃣ WAEC\n"
            "4️⃣ NECO\n"
            "5️⃣ CBT Training\n\n"
            "More courses will be available soon.",
            parse_mode="Markdown"
        )

        return


# ==============================
# CBT PRACTICE
# ==============================

    if text == "📝 CBT Practice":

        await update.message.reply_text(
            "📝 *CBT PRACTICE*\n\n"
            "CBT Practice is currently under development.\n\n"
            "It will be available soon.",
            parse_mode="Markdown"
        )

        return


# ==============================
# PAY SCHOOL FEES
# ==============================

    if text == "💳 Pay School Fees":

        await update.message.reply_text(
            "💳 *SCHOOL FEES PAYMENT*\n\n"
            "Flutterwave payment system will be available soon.",
            parse_mode="Markdown"
        )

        return


# ==============================
# CONTACT US
# ==============================

    if text == "📞 Contact Us":

        await update.message.reply_text(
            "📞 *CONTACT US*\n\n"
            "Email: support@alhikam.com\n\n"
            "ALHIKAM Learning Center",
            parse_mode="Markdown"
        )

        return


# ==============================
# ABOUT US
# ==============================

    if text == "ℹ️ About Us":

        await update.message.reply_text(
            "🎓 *ALHIKAM Learning Center*\n\n"
            "JAMB • WAEC • NECO • CBT Training\n\n"
            "We provide quality educational support "
            "and examination preparation for students.",
            parse_mode="Markdown"
        )

        return


# ==============================
# UNKNOWN MESSAGE
# ==============================

    await update.message.reply_text(
        "Please choose an option from the menu."
    )# ==============================
# RAILWAY WEBHOOK
# ==============================

PORT = int(os.getenv("PORT", "8080"))

WEBHOOK_URL = os.getenv("WEBHOOK_URL")


# ==============================
# MAIN
# ==============================

def main():

    app = Application.builder().token(BOT_TOKEN).build()

    # Start command
    app.add_handler(
        CommandHandler("start", start)
    )

    # All text messages
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            menu_handler
        )
    )

    print("Bot is running...")

    # Run bot with Railway Webhook
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=BOT_TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}",
    )


# ==============================
# START APPLICATION
# ==============================

if __name__ == "__main__":
    main()