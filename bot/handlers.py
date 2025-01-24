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

    # Initialize scraper and fetch formatted grades
    scraper = AspenScraper()
    messages = scraper.fetch_formatted_grades()

    # Send all messages
    for message in messages:
        await context.bot.send_message(
            chat_id=chat_id,
            text=message
        )
