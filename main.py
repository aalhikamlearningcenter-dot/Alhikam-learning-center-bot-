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


# ==================================================
# SETTINGS
# ==================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")

SHEET_URL = "https://script.google.com/macros/s/AKfycby5lIhCjoD0NaPZ-HHQ9hapAKlstypQvxyWK22qHblJr4uGBrPn5FoGG1TP-EvIfteo9w/exec"


# ==================================================
# MAIN MENU
# ==================================================

MAIN_MENU = [
    ["📚 Courses", "📝 CBT Practice"],
    ["👤 Student Registration", "💳 Pay School Fees"],
    ["📞 Contact Us", "ℹ️ About Us"],
]


# ==================================================
# COURSE MENU
# ==================================================

COURSE_MENU = [
    ["🎯 JAMB Science", "🎨 JAMB Arts"],
    ["📘 WAEC", "📕 NECO"],
    ["💻 CBT Training"],
    ["🔙 Back to Main Menu"],
]


# ==================================================
# START COMMAND
# ==================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    # Clear previous registration step
    context.user_data.clear()

    keyboard = ReplyKeyboardMarkup(
        MAIN_MENU,
        resize_keyboard=True
    )

    await update.message.reply_text(
        "🎓 *ALHIKAM Learning Center*\n\n"
        "Welcome to ALHIKAM Learning Center.\n\n"
        "We provide educational support for "
        "JAMB, WAEC, NECO and CBT Training.\n\n"
        "Please choose an option below.",
        parse_mode="Markdown",
        reply_markup=keyboard
    )


# ==================================================
# CANCEL COMMAND
# ==================================================

async def cancel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    context.user_data.clear()

    keyboard = ReplyKeyboardMarkup(
        MAIN_MENU,
        resize_keyboard=True
    )

    await update.message.reply_text(
        "❌ Registration cancelled.\n\n"
        "Please choose an option from the main menu.",
        reply_markup=keyboard
    )


# ==================================================
# MAIN MESSAGE HANDLER
# ==================================================

async def menu_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    text = update.message.text


    # ==================================================
    # REGISTRATION STEP CHECK
    # ==================================================

    step = context.user_data.get("step")


    # ==================================================
    # FULL NAME
    # ==================================================

    if step == "full_name":

        context.user_data["full_name"] = text
        context.user_data["step"] = "phone"

        await update.message.reply_text(
            "📱 Please enter your Phone Number:"
        )

        return


    # ==================================================
    # PHONE
    # ==================================================

    if step == "phone":

        context.user_data["phone"] = text
        context.user_data["step"] = "email"

        await update.message.reply_text(
            "📧 Please enter your Email Address:"
        )

        return


    # ==================================================
    # EMAIL
    # ==================================================

    if step == "email":

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


    # ==================================================
    # COURSE DURING REGISTRATION
    # ==================================================

    if step == "course":

        context.user_data["course"] = text

        data = {
            "full_name": context.user_data.get("full_name", ""),
            "phone": context.user_data.get("phone", ""),
            "email": context.user_data.get("email", ""),
            "course": context.user_data.get("course", ""),
        }


        # ==================================================
        # SEND DATA TO GOOGLE SHEET
        # ==================================================

        try:

            response = requests.post(
                SHEET_URL,
                json=data,
                timeout=15
            )

            print(
                "Google Sheet Response:",
                response.text
            )

        except Exception as e:

            print(
                "Google Sheet Error:",
                e
            )


        # Save details before clearing
        full_name = context.user_data.get(
            "full_name",
            ""
        )

        phone = context.user_data.get(
            "phone",
            ""
        )

        email = context.user_data.get(
            "email",
            ""
        )

        course = context.user_data.get(
            "course",
            ""
        )


        # Clear registration
        context.user_data.clear()


        keyboard = ReplyKeyboardMarkup(
            MAIN_MENU,
            resize_keyboard=True
        )


        await update.message.reply_text(
            "✅ *REGISTRATION COMPLETED*\n\n"
            f"👤 Name: {full_name}\n"
            f"📱 Phone: {phone}\n"
            f"📧 Email: {email}\n"
            f"📚 Course: {course}\n\n"
            "🎓 Thank you for registering with "
            "ALHIKAM Learning Center.",
            parse_mode="Markdown",
            reply_markup=keyboard
        )

        return


    # ==================================================
    # STUDENT REGISTRATION
    # ==================================================

    if text == "👤 Student Registration":

        context.user_data.clear()

        context.user_data["step"] = "full_name"

        await update.message.reply_text(
            "👤 *STUDENT REGISTRATION*\n\n"
            "Please enter your Full Name.\n\n"
            "Type /cancel to cancel registration.",
            parse_mode="Markdown"
        )

        return


    # ==================================================
    # COURSES
    # ==================================================

    if text == "📚 Courses":

        keyboard = ReplyKeyboardMarkup(
            COURSE_MENU,
            resize_keyboard=True
        )

        await update.message.reply_text(
            "📚 *ALHIKAM COURSES*\n\n"
            "Please select a course below "
            "to learn more:",
            parse_mode="Markdown",
            reply_markup=keyboard
        )

        return


    # ==================================================
    # JAMB SCIENCE
    # ==================================================

    if text == "🎯 JAMB Science":

        await update.message.reply_text(
            "🎯 *JAMB SCIENCE*\n\n"
            "ALHIKAM Learning Center provides "
            "JAMB Science preparation and support.\n\n"
            "📚 Subjects include:\n"
            "• Mathematics\n"
            "• English Language\n"
            "• Physics\n"
            "• Chemistry\n"
            "• Biology\n\n"
            "📝 CBT practice and study materials "
            "will be available soon.",
            parse_mode="Markdown"
        )

        return


    # ==================================================
    # JAMB ARTS
    # ==================================================

    if text == "🎨 JAMB Arts":

        await update.message.reply_text(
            "🎨 *JAMB ARTS*\n\n"
            "ALHIKAM Learning Center provides "
            "JAMB Arts preparation and support.\n\n"
            "📚 Subjects include:\n"
            "• English Language\n"
            "• Literature in English\n"
            "• Government\n"
            "• Economics\n"
            "• CRS / IRS\n\n"
            "📝 CBT practice and study materials "
            "will be available soon.",
            parse_mode="Markdown"
        )

        return


    # ==================================================
    # WAEC
    # ==================================================

    if text == "📘 WAEC":

        await update.message.reply_text(
            "📘 *WAEC PREPARATION*\n\n"
            "Prepare for your WAEC examination "
            "with ALHIKAM Learning Center.\n\n"
            "📚 Study materials\n"
            "📝 Practice questions\n"
            "💻 CBT training\n"
            "🎓 Examination guidance\n\n"
            "More WAEC learning resources "
            "will be available soon.",
            parse_mode="Markdown"
        )

        return


    # ==================================================
    # NECO
    # ==================================================

    if text == "📕 NECO":

        await update.message.reply_text(
            "📕 *NECO PREPARATION*\n\n"
            "ALHIKAM Learning Center provides "
            "support for NECO examination preparation.\n\n"
            "📚 Study materials\n"
            "📝 Practice questions\n"
            "💻 CBT training\n"
            "🎓 Examination guidance\n\n"
            "More NECO learning resources "
            "will be available soon.",
            parse_mode="Markdown"
        )

        return


    # ==================================================
    # CBT TRAINING
    # ==================================================

    if text == "💻 CBT Training":

        await update.message.reply_text(
            "💻 *CBT TRAINING*\n\n"
            "Improve your examination skills "
            "with Computer-Based Test training.\n\n"
            "📝 Practice questions\n"
            "⏱️ Timed examinations\n"
            "📊 Results and performance\n"
            "🎯 JAMB • WAEC • NECO preparation\n\n"
            "🚧 CBT Training system is currently "
            "under development.\n\n"
            "It will be available soon.",
            parse_mode="Markdown"
        )

        return


    # ==================================================
    # BACK TO MAIN MENU
    # ==================================================

    if text == "🔙 Back to Main Menu":

        keyboard = ReplyKeyboardMarkup(
            MAIN_MENU,
            resize_keyboard=True
        )

        await update.message.reply_text(
            "🏠 *MAIN MENU*\n\n"
            "Please choose an option below.",
            parse_mode="Markdown",
            reply_markup=keyboard
        )

        return


    # ==================================================
    # CBT PRACTICE
    # ==================================================

    if text == "📝 CBT Practice":

        await update.message.reply_text(
            "📝 *CBT PRACTICE*\n\n"
            "CBT Practice is currently under development.\n\n"
            "It will include:\n"
            "• JAMB Practice\n"
            "• WAEC Practice\n"
            "• NECO Practice\n"
            "• Timed Tests\n"
            "• Results and Scores\n\n"
            "🚧 This feature will be available soon.",
            parse_mode="Markdown"
        )

        return


     # ==================================================
# PAY SCHOOL FEES
# ==================================================

if text == "💳 Pay School Fees":

    payment_menu = ReplyKeyboardMarkup(
        [
            ["💳 1 Month", "💳 2 Months"],
            ["💳 3 Months", "💳 4 Months"],
            ["💳 5 Months", "💳 6 Months"],
            ["🔙 Back to Main Menu"],
        ],
        resize_keyboard=True
    )

    await update.message.reply_text(
        "💳 *ALHIKAM SCHOOL FEES PAYMENT*\n\n"
        "Please select the training duration you want to pay for:\n\n"
        "💳 1 Month\n"
        "💳 2 Months\n"
        "💳 3 Months\n"
        "💳 4 Months\n"
        "💳 5 Months\n"
        "💳 6 Months\n\n"
        "Select your preferred option below.",
        parse_mode="Markdown",
        reply_markup=payment_menu
    )

    return


# ==================================================
# 1 MONTH PAYMENT
# ==================================================

if text == "💳 1 Month":

    await update.message.reply_text(
        "💳 *1 MONTH JAMB TRAINING*\n\n"
        "Click the link below to complete your payment:\n\n"
        "https://flutterwave.com/pay/xzxojtyp2igm",
        parse_mode="Markdown"
    )

    return


# ==================================================
# 2 MONTHS PAYMENT
# ==================================================

if text == "💳 2 Months":

    await update.message.reply_text(
        "💳 *2 MONTHS JAMB TRAINING*\n\n"
        "Click the link below to complete your payment:\n\n"
        "https://flutterwave.com/pay/7dmjszf7keh7",
        parse_mode="Markdown"
    )

    return


# ==================================================
# 3 MONTHS PAYMENT
# ==================================================

if text == "💳 3 Months":

    await update.message.reply_text(
        "💳 *3 MONTHS JAMB TRAINING*\n\n"
        "Click the link below to complete your payment:\n\n"
        "https://flutterwave.com/pay/ghclijb4q33v",
        parse_mode="Markdown"
    )

    return


# ==================================================
# 4 MONTHS PAYMENT
# ==================================================

if text == "💳 4 Months":

    await update.message.reply_text(
        "💳 *4 MONTHS JAMB TRAINING*\n\n"
        "Click the link below to complete your payment:\n\n"
        "https://flutterwave.com/pay/hplaya85sxfh",
        parse_mode="Markdown"
    )

    return


# ==================================================
# 5 MONTHS PAYMENT
# ==================================================

if text == "💳 5 Months":

    await update.message.reply_text(
        "💳 *5 MONTHS JAMB TRAINING*\n\n"
        "Click the link below to complete your payment:\n\n"
        "https://flutterwave.com/pay/gwkniyevqmdm",
        parse_mode="Markdown"
    )

    return


# ==================================================
# 6 MONTHS PAYMENT
# ==================================================

if text == "💳 6 Months":

    await update.message.reply_text(
        "💳 *6 MONTHS JAMB TRAINING*\n\n"
        "Click the link below to complete your payment:\n\n"
        "https://flutterwave.com/pay/ubrjptqujfem",
        parse_mode="Markdown"
    )

    return


    # ==================================================
    # CONTACT US
    # ==================================================

    if text == "📞 Contact Us":

        await update.message.reply_text(
            "📞 *CONTACT US*\n\n"
            "📧 Email: support@alhikam.com\n\n"
            "🎓 ALHIKAM Learning Center\n"
            "JAMB • WAEC • NECO • CBT Training",
            parse_mode="Markdown"
        )

        return


    # ==================================================
    # ABOUT US
    # ==================================================

    if text == "ℹ️ About Us":

        await update.message.reply_text(
            "🎓 *ALHIKAM Learning Center*\n\n"
            "JAMB • WAEC • NECO • CBT Training\n\n"
            "We provide quality educational support "
            "and examination preparation for students.\n\n"
            "📚 Courses\n"
            "📝 CBT Practice\n"
            "👤 Student Registration\n"
            "💳 School Fees Payment\n\n"
            "Our goal is to help students prepare "
            "successfully for their examinations.",
            parse_mode="Markdown"
        )

        return


    # ==================================================
    # UNKNOWN MESSAGE
    # ==================================================

    await update.message.reply_text(
        "❓ Please choose an option from the menu."
    )


# ==================================================
# MAIN
# ==================================================

def main():

    # Check BOT_TOKEN
    if not BOT_TOKEN:

        raise ValueError(
            "BOT_TOKEN is missing. "
            "Please add BOT_TOKEN in Railway Variables."
        )


    # Create application
    app = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )


    # ==================================================
    # COMMAND HANDLERS
    # ==================================================

    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )


    app.add_handler(
        CommandHandler(
            "cancel",
            cancel
        )
    )


    # ==================================================
    # TEXT MESSAGE HANDLER
    # ==================================================

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            menu_handler
        )
    )


    print("Bot is running...")


    # ==================================================
    # POLLING
    # ==================================================

    app.run_polling(
        drop_pending_updates=True
    )


# ==================================================
# START APPLICATION
# ==================================================

if __name__ == "__main__":

    main()