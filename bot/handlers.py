from telegram import Update, BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, ForceReply, ReplyKeyboardMarkup
from telegram.constants import ChatAction
from telegram.ext import ContextTypes, Application, ConversationHandler, CommandHandler, MessageHandler, filters, CallbackQueryHandler
# from database.mongodb import MongoService
from bot.scraper import AspenScraper
# from bot.email_service import send_feedback_email
import logging

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def setup_commands(application: Application) -> None:
    """Setup bot commands in the menu."""
    commands = [
        BotCommand("start", "Start the bot"),
        BotCommand("grades", "Fetch current grades and assignments"),
    ]
    await application.bot.set_my_commands(commands)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    await update.message.reply_text(
        f"👋 Hello {update.effective_user.first_name}! Welcome to your Aspen Grade Monitor!\n\n"
        "I'm here to help you keep track of your grades and assignments. "
        "Think of me as your personal academic assistant who can fetch your latest grades anytime! 📚\n\n"
        "<b>Here's what I can do for you:</b>\n\n"
        "📊 /grades - Fetch your current grades and recent assignments\n"
        "• See all your class grades\n"
        "• View recent assignments and scores\n"
        "• Check teacher information\n\n"
        "<i>Ready to check your grades? Just use the /grades command! 📝</i>",
        parse_mode='HTML'
    )


async def fetch_grades(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /grades command - fetches current grades and assignments"""
    chat_id = update.effective_chat.id

    # Send initial message
    await context.bot.send_message(
        chat_id=chat_id,
        text="Fetching your grades... Please wait."
    )

    # Initialize scraper and login
    scraper = AspenScraper()
    if not scraper.login():
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Failed to login to Aspen. Please check credentials."
        )
        return

    # Get class list
    class_list = scraper.get_class_list()
    if not class_list:
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Failed to fetch classes."
        )
        return

    # Format and send grades
    message = "📚 Current Grades:\n\n"
    for class_info in class_list:
        course_name = class_info.get('courseName', '')
        grade = class_info.get('sectionTermAverage', 'No grade')
        teacher = class_info.get('teacherName', '')

        message += f"📘 {course_name}\n"
        message += f"Grade: {grade}\n"
        message += f"Teacher: {teacher}\n"

        # Only get assignments if there's a grade
        if class_info.get('percentageValue'):
            schedule_oid = class_info.get('studentScheduleOid')
            if schedule_oid:
                assignments = scraper.get_grade_details(schedule_oid)
                if assignments:
                    message += "\nRecent Assignments:\n"
                    # Show only the 3 most recent assignments
                    for assignment in assignments[:3]:
                        name = assignment.get('name', '')
                        category = assignment.get('category', '')

                        # Get score
                        score_elements = assignment.get('scoreElements', [])
                        score = "Not graded"
                        if score_elements:
                            score_info = score_elements[0]
                            score = f"{score_info.get('score', 'No score')}"

                        message += f"• {name} ({category}): {score}\n"

        message += "\n"

        # Send message if it's getting too long
        if len(message) > 3000:
            await context.bot.send_message(
                chat_id=chat_id,
                text=message
            )
            message = ""  # Reset message

    # Send any remaining message
    if message:
        await context.bot.send_message(
            chat_id=chat_id,
            text=message
        )
