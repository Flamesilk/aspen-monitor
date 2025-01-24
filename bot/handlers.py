from telegram import Update, BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, ForceReply, ReplyKeyboardMarkup
from telegram.constants import ChatAction
from telegram.ext import ContextTypes, Application, ConversationHandler, CommandHandler, MessageHandler, filters, CallbackQueryHandler
# from database.mongodb import MongoService
from bot.scraper import AspenScraper
# from bot.email_service import send_feedback_email
import logging
import time
from functools import wraps
import config

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
    chat_id = update.effective_chat.id
    await update.message.reply_text(
        f"👋 Hello {update.effective_user.first_name}! Welcome to your Aspen Grade Monitor!\n\n"
        f"Your chat ID is: {chat_id}\n\n"
        "I'm here to help you keep track of your CPS grades and assignments from Aspen. 📚\n\n"
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
    is_authorized = chat_id in config.AUTHORIZED_CHAT_IDS

    if not is_authorized:
        await update.message.reply_text(
            "⛔️ Sorry, you are not authorized to use this bot.\n\n"
            "This bot is for private use only."
        )
        return

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

    # Get student name from the scraper
    student_name = getattr(scraper, 'student_name', None)
    print(student_name)

    def format_score(score_text, percentage=None):
        """Helper function to format score with emoji indicators"""
        try:
            if percentage is not None:
                score = float(percentage)
                if score >= 90:
                    return f'✅ {score_text}'  # Green checkmark for good scores
                else:
                    return f'⚠️ {score_text}'  # Warning symbol for scores below 90
        except (ValueError, TypeError):
            pass
        return score_text

    # Format and send grades
    message = "📚 Current Grades"
    if student_name:
        message += f" for {student_name}"
    message += ":\n\n"

    has_content = False

    for class_info in class_list:
        course_name = class_info.get('courseName', '')
        grade = class_info.get('sectionTermAverage', '')
        percentage = class_info.get('percentageValue')
        teacher = class_info.get('teacherName', '')

        # Skip if no grade and no assignments
        if not grade and not class_info.get('percentageValue'):
            continue

        has_content = True
        message += f"📘 {course_name}\n"
        message += f"Grade: {format_score(grade or 'No grade', percentage)}\n"
        message += f"Teacher: {teacher}\n"

        # Get assignments if available
        if class_info.get('percentageValue'):
            schedule_oid = class_info.get('studentScheduleOid')
            if schedule_oid:
                assignments = scraper.get_grade_details(schedule_oid)
                if assignments:
                    # Sort assignments by date (most recent first)
                    sorted_assignments = sorted(
                        assignments,
                        key=lambda x: x.get('dueDate', 0),
                        reverse=True
                    )

                    message += "\nRecent Assignments:\n"
                    # Show only the 3 most recent assignments
                    for assignment in sorted_assignments[:3]:
                        name = assignment.get('name', '')
                        category = assignment.get('category', '')
                        due_date = assignment.get('dueDate')

                        # Format date
                        date_str = ''
                        if due_date:
                            date_str = time.strftime('%Y-%m-%d', time.localtime(due_date/1000))

                        # Get score
                        score_elements = assignment.get('scoreElements', [])
                        score = "Not graded"
                        score_percentage = None
                        if score_elements:
                            score_info = score_elements[0]
                            if score_info.get('score') is not None:
                                score = f"{score_info.get('score')}"
                                score_percentage = score_info.get('scorePercent')

                        message += f"• {name}\n"
                        message += f"  📅 Due: {date_str}\n"
                        message += f"  📝 {category}: {format_score(score, score_percentage)}\n"

        message += "\n"

        # Send message if it's getting too long
        if len(message) > 3000:
            await context.bot.send_message(
                chat_id=chat_id,
                text=message
            )
            message = ""  # Reset message
            has_content = False

    # Send any remaining message
    if message and has_content:
        await context.bot.send_message(
            chat_id=chat_id,
            text=message
        )
    elif not has_content:
        await context.bot.send_message(
            chat_id=chat_id,
            text="No grades or assignments found for the current term."
        )
