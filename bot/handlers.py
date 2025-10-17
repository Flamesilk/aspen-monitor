from telegram import Update, BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, ForceReply, ReplyKeyboardMarkup
from telegram.constants import ChatAction
from telegram.ext import ContextTypes, Application, ConversationHandler, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from database import Database
from bot.scraper import AspenScraper
from bot.scheduler import fetch_and_notify_user
# Email service removed - Telegram only notifications
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

# Initialize database
db = Database()

# Conversation states
(REGISTER_USERNAME, REGISTER_PASSWORD,
 SET_CREDENTIALS_USERNAME, SET_CREDENTIALS_PASSWORD,
 SET_NOTIFICATION_TIME, SET_TIMEZONE,
 SETUP_TIMEZONE, SETUP_NOTIFICATION_TIME) = range(8)

# Common timezones for Aspen users
COMMON_TIMEZONES = {
    "🇺🇸 Eastern": "America/New_York",
    "🇺🇸 Central": "America/Chicago",
    "🇺🇸 Mountain": "America/Denver",
    "🇺🇸 Pacific": "America/Los_Angeles",
    "🇺🇸 Alaska": "America/Anchorage",
    "🇺🇸 Hawaii": "Pacific/Honolulu",
    "🇨🇦 Eastern": "America/Toronto",
    "🇨🇦 Central": "America/Winnipeg",
    "🇨🇦 Mountain": "America/Edmonton",
    "🇨🇦 Pacific": "America/Vancouver"
}

def generate_random_notification_time():
    """Generate a random time between 12:00 and 20:00 at 15-minute intervals"""
    import random

    # Random hour between 12 and 19 (12:00 to 19:45)
    hour = random.randint(12, 19)

    # Random minute: 0, 15, 30, or 45 (15-minute intervals)
    minute = random.choice([0, 15, 30, 45])

    # Format as HH:MM
    return f"{hour:02d}:{minute:02d}"

async def setup_commands(application: Application) -> None:
    """Setup bot commands in the menu."""
    commands = [
        BotCommand("start", "Start the bot"),
        BotCommand("register", "Register your Aspen account"),
        BotCommand("grades", "Fetch current grades and assignments"),
        BotCommand("settings", "Manage your account settings"),
        BotCommand("status", "Check your account status"),
        BotCommand("donate", "Support the developer"),
        BotCommand("help", "Get help and instructions"),
    ]
    await application.bot.set_my_commands(commands)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    chat_id = update.effective_chat.id
    user = db.get_user(chat_id)

    if user:
        await update.message.reply_text(
            f"👋 Welcome back, {update.effective_user.first_name}!\n\n"
            f"Your account is already set up. Use /grades to check your grades or /settings to manage your account."
        )
    else:
        await update.message.reply_text(
            f"👋 Hello {update.effective_user.first_name}! Welcome to Aspen Grade Monitor!\n\n"
            f"Your chat ID is: {chat_id}\n\n"
            "I'm here to help you keep track of your CPS grades and assignments from Aspen. 📚\n\n"
            "🔒 <b>Your data is secure:</b>\n"
            "• Credentials are encrypted and protected\n"
            "• Your privacy is our priority\n"
            "• You control your account completely\n\n"
            "<b>To get started:</b>\n"
            "🔐 /register - Set up your Aspen account\n"
            "📊 /grades - Fetch your current grades\n"
            "⚙️ /settings - Manage your account\n"
            "❓ /help - Get help and instructions\n\n"
            "<i>Ready to check your grades? Start with /register!</i>",
            parse_mode='HTML'
        )

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start registration process."""
    chat_id = update.effective_chat.id

    # Check if user already exists
    if db.get_user(chat_id):
        await update.message.reply_text(
            "You're already registered! Use /settings to update your information or /grades to check your grades."
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "🔐 <b>Registration Process</b>\n\n"
        "To get started, I'll need your Aspen credentials.\n\n"
        "🛡️ <b>Your privacy is protected:</b>\n"
        "• All data is encrypted and secure\n"
        "• Credentials are never shared\n"
        "• You control your account completely\n\n"
        "Please send your <b>Aspen username</b>:",
        parse_mode='HTML'
    )
    return REGISTER_USERNAME

async def register_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store username and ask for password."""
    username = update.message.text.strip()
    context.user_data['aspen_username'] = username

    # Check if this is an update or new registration
    is_update = context.user_data.get('updating') == 'credentials'

    if is_update:
        await update.message.reply_text(
            f"✅ New username saved: <code>{username}</code>\n\n"
            "Now please send your <b>new Aspen password</b>:\n\n"
            "🔒 <b>Your password is secure:</b>\n"
            "• Encrypted and stored safely\n"
            "• Never shared with anyone\n"
            "• Only used to fetch your grades\n"
            "• You can delete your account anytime",
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text(
            f"✅ Username saved: <code>{username}</code>\n\n"
            "Now please send your <b>Aspen password</b>:\n\n"
            "🔒 <b>Your password is secure:</b>\n"
            "• Encrypted and stored safely\n"
            "• Never shared with anyone\n"
            "• Only used to fetch your grades\n"
            "• You can delete your account anytime",
            parse_mode='HTML'
        )
    return REGISTER_PASSWORD

async def register_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store password and complete registration."""
    password = update.message.text.strip()
    context.user_data['aspen_password'] = password

    # Complete registration with Telegram notifications only
    success = db.add_user(
        telegram_id=update.effective_user.id,
        aspen_username=context.user_data['aspen_username'],
        aspen_password=context.user_data['aspen_password'],
        notification_method='telegram'
    )

    if success:
        # Check if this is an update or new registration
        is_update = context.user_data.get('updating') == 'credentials'

        if is_update:
            await update.message.reply_text(
                "✅ <b>Credentials Updated!</b>\n\n"
                "Your Aspen credentials have been updated successfully!\n\n"
                "You can now use:\n"
                "📊 /grades - Check your grades with new credentials\n"
                "⚙️ /settings - Manage your account\n\n"
                "Your daily grade updates will continue as usual!",
                parse_mode='HTML'
            )
        else:
            # Start setup flow for new users
            await start_setup_flow(update, context)
    else:
        action = "update" if context.user_data.get('updating') == 'credentials' else "registration"
        await update.message.reply_text(
            f"❌ {action.title()} failed. Please try again with /settings or /register."
        )

    return ConversationHandler.END

async def start_setup_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the post-registration setup flow for new users."""
    # Generate random notification time
    random_time = generate_random_notification_time()

    # Set default timezone and time
    db.update_user_timezone(update.effective_user.id, 'America/Chicago')
    db.update_user_notification_time(update.effective_user.id, random_time)

    await update.message.reply_text(
        f"🎉 <b>Registration Complete!</b>\n\n"
        f"Your account has been set up successfully!\n\n"
        f"<b>Default Settings Applied:</b>\n"
        f"🌍 Timezone: 🇺🇸 Central (Chicago)\n"
        f"⏰ Notification Time: {random_time}\n\n"
        f"<b>Would you like to customize these settings?</b>\n\n"
        f"Choose an option:",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🌍 Change Timezone", callback_data="setup_timezone")],
            [InlineKeyboardButton("⏰ Change Time", callback_data="setup_notification_time")],
            [InlineKeyboardButton("✅ Keep Defaults", callback_data="setup_complete")]
        ])
    )

async def setup_timezone_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle timezone selection during setup."""
    query = update.callback_query
    await query.answer()

    if query.data == "setup_timezone":
        # Create timezone selection keyboard
        keyboard = []
        for display_name, timezone in COMMON_TIMEZONES.items():
            keyboard.append([InlineKeyboardButton(display_name, callback_data=f"setup_timezone_{timezone}")])

        keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="setup_complete")])
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            "🌍 <b>Select Your Timezone</b>\n\n"
            "Choose your timezone for grade notifications:\n\n"
            "<i>This ensures notifications arrive at the correct local time.</i>",
            parse_mode='HTML',
            reply_markup=reply_markup
        )
        return SETUP_TIMEZONE

    elif query.data.startswith("setup_timezone_"):
        timezone = query.data.replace("setup_timezone_", "")

        # Update user's timezone
        success = db.update_user_timezone(query.from_user.id, timezone)

        if success:
            # Get display name for confirmation
            timezone_display = "Unknown"
            for display, tz in COMMON_TIMEZONES.items():
                if tz == timezone:
                    timezone_display = display
                    break

            await query.edit_message_text(
                f"✅ <b>Timezone Set!</b>\n\n"
                f"Your timezone has been set to <b>{timezone_display}</b>.\n\n"
                f"<b>Next, let's set your notification time:</b>",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⏰ Set Notification Time", callback_data="setup_notification_time")],
                    [InlineKeyboardButton("✅ Complete Setup", callback_data="setup_complete")]
                ])
            )
        else:
            await query.edit_message_text(
                "❌ Failed to update timezone. Please try again with /settings."
            )
        return ConversationHandler.END

    elif query.data == "setup_complete":
        await complete_setup(update, context)
        return ConversationHandler.END

    return ConversationHandler.END

async def setup_notification_time_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle notification time selection during setup."""
    query = update.callback_query
    await query.answer()

    if query.data == "setup_notification_time":
        await query.edit_message_text(
            "⏰ <b>Set Your Notification Time</b>\n\n"
            "When would you like to receive daily grade notifications?\n\n"
            "<b>Format examples:</b>\n"
            "• <code>15:00</code> (3:00 PM)\n"
            "• <code>08:30</code> (8:30 AM)\n"
            "• <code>22:00</code> (10:00 PM)\n\n"
            "Send the time in 24-hour format (HH:MM):",
            parse_mode='HTML'
        )
        return SETUP_NOTIFICATION_TIME

    elif query.data == "setup_complete":
        await complete_setup(update, context)
        return ConversationHandler.END

    return ConversationHandler.END

async def setup_notification_time_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle notification time input during setup."""
    time_input = update.message.text.strip()

    # Validate time format (HH:MM)
    import re
    time_pattern = r'^([01]?[0-9]|2[0-3]):([0-5][0-9])$'

    if not re.match(time_pattern, time_input):
        await update.message.reply_text(
            "❌ <b>Invalid time format!</b>\n\n"
            "Please use 24-hour format (HH:MM):\n"
            "• <code>15:00</code> (3:00 PM)\n"
            "• <code>08:30</code> (8:30 AM)\n"
            "• <code>22:00</code> (10:00 PM)\n\n"
            "Try again:",
            parse_mode='HTML'
        )
        return SETUP_NOTIFICATION_TIME

    # Update user's notification time
    success = db.update_user_notification_time(update.effective_user.id, time_input)

    if success:
        await update.message.reply_text(
            f"✅ <b>Notification Time Set!</b>\n\n"
            f"Your daily grade notifications will be sent at <code>{time_input}</code>.\n\n"
            f"<b>Setup Complete!</b> You can change these settings anytime in /settings.",
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text(
            "❌ Failed to update notification time. You can change this later in /settings."
        )

    return ConversationHandler.END

async def complete_setup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Complete the setup flow."""
    # Get current settings to show what was set
    settings = db.get_user_settings(update.effective_user.id)
    timezone_display = "🇺🇸 Central"  # Default
    notification_time = "15:00"  # Default

    if settings:
        notification_time = settings.get('notification_time', '15:00')
        current_timezone = settings.get('timezone', 'America/Chicago')
        for display, tz in COMMON_TIMEZONES.items():
            if tz == current_timezone:
                timezone_display = display
                break

    await update.message.reply_text(
        f"🎉 <b>Setup Complete!</b>\n\n"
        f"<b>Your Settings:</b>\n"
        f"🌍 Timezone: {timezone_display}\n"
        f"⏰ Notification Time: {notification_time}\n\n"
        f"<b>⏰ Important:</b>\n"
        f"Notifications may be delayed by 1-2 minutes to prevent server overload and ensure reliable service for all users.\n\n"
        f"<b>You can now use:</b>\n"
        f"📊 /grades - Check your grades\n"
        f"⚙️ /settings - Manage your account\n\n"
        f"I'll send you daily grade updates via Telegram!",
        parse_mode='HTML'
    )

async def set_notification_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle notification time setting."""
    time_input = update.message.text.strip()

    # Validate time format (HH:MM)
    import re
    time_pattern = r'^([01]?[0-9]|2[0-3]):([0-5][0-9])$'

    if not re.match(time_pattern, time_input):
        await update.message.reply_text(
            "❌ <b>Invalid time format!</b>\n\n"
            "Please use 24-hour format (HH:MM):\n"
            "• <code>15:00</code> (3:00 PM)\n"
            "• <code>08:30</code> (8:30 AM)\n"
            "• <code>22:00</code> (10:00 PM)\n\n"
            "Try again:",
            parse_mode='HTML'
        )
        return SET_NOTIFICATION_TIME

    # Update user's notification time
    success = db.update_user_notification_time(update.effective_user.id, time_input)

    if success:
        try:
            # Reschedule the user's job with new time
            await reschedule_user_job(update.effective_user.id, time_input, context)

            await update.message.reply_text(
                f"✅ <b>Notification Time Updated!</b>\n\n"
                f"Your daily grade notifications will now be sent at <code>{time_input}</code>.\n\n"
                "You can change this anytime in /settings.",
                parse_mode='HTML'
            )
            logger.info(f"Successfully updated notification time for user {update.effective_user.id} to {time_input}")
        except Exception as e:
            logger.error(f"Error rescheduling job for user {update.effective_user.id}: {str(e)}")
            await update.message.reply_text(
                f"⚠️ <b>Time Updated but Scheduling Failed</b>\n\n"
                f"Your notification time was saved as <code>{time_input}</code>, but there was an error scheduling the job.\n\n"
                "Please try /settings again or contact support if the issue persists.",
                parse_mode='HTML'
            )
    else:
        logger.error(f"Failed to update notification time in database for user {update.effective_user.id}")
        await update.message.reply_text(
            "❌ Failed to update notification time in database. Please try again with /settings."
        )

    return ConversationHandler.END

async def reschedule_user_job(telegram_id: int, notification_time: str, context: ContextTypes.DEFAULT_TYPE):
    """Reschedule a user's notification job with new time."""
    try:
        import pytz
        from datetime import time
        import random

        # Get user data
        user = db.get_user(telegram_id)
        if not user:
            logger.error(f"User {telegram_id} not found for rescheduling")
            return

        # Get user's timezone
        settings = db.get_user_settings(telegram_id)
        user_timezone = settings.get('timezone', 'America/Chicago') if settings else 'America/Chicago'
        tz = pytz.timezone(user_timezone)

        # Parse time (HH:MM format) and add random offset
        hour, minute = map(int, notification_time.split(':'))

        # Add random offset to prevent all users hitting at exact same time
        random_offset = random.choice([0, 15, 30, 45])  # 15-minute interval offset
        minute += random_offset
        if minute >= 60:
            hour += 1
            minute -= 60

        # Create time object without timezone (job queue handles timezone separately)
        job_time = time(hour=hour, minute=minute)

        # Remove existing job
        job_name = f"grade_check_user_{telegram_id}"
        try:
            context.job_queue.scheduler.remove_job(job_name)
            logger.info(f"Removed existing job for user {telegram_id}")
        except Exception as e:
            logger.info(f"No existing job to remove for user {telegram_id}: {e}")

        # Create new job with updated time
        context.job_queue.run_daily(
            fetch_and_notify_user,
            time=job_time,
            name=job_name,
            data=user
        )

        logger.info(f"Successfully rescheduled job for user {telegram_id} at {notification_time} {user_timezone}")

    except Exception as e:
        logger.error(f"Error rescheduling job for user {telegram_id}: {str(e)}", exc_info=True)

# Removed email notification functions - Telegram only

async def fetch_grades(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /grades command - fetches current grades and assignments"""
    chat_id = update.effective_chat.id
    user = db.get_user(chat_id)

    if not user:
        await update.message.reply_text(
            "❌ You're not registered yet!\n\n"
            "Please use /register to set up your Aspen account first."
        )
        return

    # Send initial message
    await context.bot.send_message(
        chat_id=chat_id,
        text="Fetching your grades... Please wait."
    )

    try:
        # Initialize scraper with user's credentials
        scraper = AspenScraper(user['aspen_username'], user['aspen_password'])
        messages = scraper.fetch_formatted_grades()

        # Send all messages
        for message in messages:
            await context.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode='HTML'
            )
    except Exception as e:
        logger.error(f"Error fetching grades for user {chat_id}: {e}")
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Failed to fetch grades. Please check your credentials and try again."
        )

async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user settings and management options."""
    chat_id = update.effective_chat.id
    user = db.get_user(chat_id)

    if not user:
        await update.message.reply_text(
            "❌ You're not registered yet!\n\n"
            "Please use /register to set up your Aspen account first."
        )
        return

    # Get user settings to show current notification time and timezone
    settings = db.get_user_settings(chat_id)
    current_time = settings.get('notification_time', '15:00') if settings else '15:00'
    current_timezone = settings.get('timezone', 'America/Chicago') if settings else 'America/Chicago'

    # Convert timezone to display name
    timezone_display = "Central"  # Default
    for display, tz in COMMON_TIMEZONES.items():
        if tz == current_timezone:
            timezone_display = display
            break

    # Create settings keyboard
    keyboard = [
        [InlineKeyboardButton("🔐 Update Credentials", callback_data="update_creds")],
        [InlineKeyboardButton(f"⏰ Notification Time ({current_time})", callback_data="set_notification_time")],
        [InlineKeyboardButton(f"🌍 Timezone ({timezone_display})", callback_data="set_timezone")],
        [InlineKeyboardButton("🗑️ Delete Account", callback_data="delete_account")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Format created timestamp with timezone info
    from datetime import datetime
    import pytz

    try:
        created_dt = datetime.fromisoformat(user['created_at'].replace('Z', '+00:00'))
        if created_dt.tzinfo is None:
            local_tz = pytz.timezone('America/Chicago')
            created_dt = local_tz.localize(created_dt).astimezone(pytz.UTC)
        else:
            created_dt = created_dt.astimezone(pytz.UTC)
        created_utc = created_dt.strftime('%Y-%m-%d %H:%M:%S UTC')
    except Exception:
        created_utc = f"{user['created_at']} (local time)"

    await update.message.reply_text(
        f"⚙️ <b>Account Settings</b>\n\n"
        f"👤 Username: <code>{user['aspen_username']}</code>\n"
        f"🔔 Notifications: <code>Telegram</code>\n"
        f"📅 Created: <code>{created_utc}</code>\n\n"
        f"⏰ <b>Note:</b> Notifications may be delayed by 1-2 minutes to ensure reliable service.\n\n"
        "Choose an option below:",
        parse_mode='HTML',
        reply_markup=reply_markup
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user account status."""
    chat_id = update.effective_chat.id
    user = db.get_user(chat_id)

    if not user:
        await update.message.reply_text(
            "❌ You're not registered yet!\n\n"
            "Please use /register to set up your Aspen account first."
        )
        return

    # Format timestamps with timezone info
    from datetime import datetime
    import pytz

    try:
        # Parse the stored timestamp and convert to UTC
        created_dt = datetime.fromisoformat(user['created_at'].replace('Z', '+00:00'))
        if created_dt.tzinfo is None:
            # If no timezone info, assume local time and convert to UTC
            local_tz = pytz.timezone('America/Chicago')  # Default timezone
            created_dt = local_tz.localize(created_dt).astimezone(pytz.UTC)
        else:
            created_dt = created_dt.astimezone(pytz.UTC)

        last_updated_dt = datetime.fromisoformat(user['last_updated'].replace('Z', '+00:00'))
        if last_updated_dt.tzinfo is None:
            local_tz = pytz.timezone('America/Chicago')
            last_updated_dt = local_tz.localize(last_updated_dt).astimezone(pytz.UTC)
        else:
            last_updated_dt = last_updated_dt.astimezone(pytz.UTC)

        # Format with UTC indicator
        created_utc = created_dt.strftime('%Y-%m-%d %H:%M:%S UTC')
        last_updated_utc = last_updated_dt.strftime('%Y-%m-%d %H:%M:%S UTC')

    except Exception as e:
        # Fallback to original format if parsing fails
        created_utc = f"{user['created_at']} (local time)"
        last_updated_utc = f"{user['last_updated']} (local time)"

    await update.message.reply_text(
        f"📊 <b>Account Status</b>\n\n"
        f"✅ Account: Active\n"
        f"👤 Username: <code>{user['aspen_username']}</code>\n"
        f"🔔 Notifications: <code>Telegram</code>\n"
        f"📅 Created: <code>{created_utc}</code>\n"
        f"🔄 Last Updated: <code>{last_updated_utc}</code>",
        parse_mode='HTML'
    )

async def donate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show donation information."""
    if config.DONATION_URL:
        await update.message.reply_text(
            "💝 <b>Support the Developer</b>\n\n"
            "If you find this bot helpful, consider supporting its development!\n\n"
            "Your support helps with:\n"
            "• Server hosting costs\n"
            "• Development time\n"
            "• New features and improvements\n"
            "• Bug fixes and maintenance\n\n"
            f"🙏 <a href='{config.DONATION_URL}'>Click here to donate</a>\n\n"
            "Thank you for your support! 💙",
            parse_mode='HTML',
            disable_web_page_preview=True
        )
    else:
        await update.message.reply_text(
            "💝 <b>Support the Developer</b>\n\n"
            "Thank you for using this bot! Your support is greatly appreciated. 💙",
            parse_mode='HTML'
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help information."""
    await update.message.reply_text(
        "❓ <b>Help & Instructions</b>\n\n"
        "<b>Available Commands:</b>\n"
        "🔐 /register - Set up your Aspen account\n"
        "📊 /grades - Check your current grades\n"
        "⚙️ /settings - Manage your account\n"
        "📊 /status - Check your account status\n"
        "💝 /donate - Support the developer\n"
        "❓ /help - Show this help message\n\n"
        "<b>Getting Started:</b>\n"
        "1. Use /register to set up your Aspen credentials\n"
        "2. Use /grades to check your grades anytime\n"
        "3. You'll receive daily grade updates via Telegram\n\n"
        "⏰ <b>Notification Timing:</b>\n"
        "• Notifications may be delayed by 1-2 minutes\n"
        "• This prevents server overload and ensures reliability\n"
        "• Delays are shown in notification messages\n\n"
        "🔒 <b>Security & Privacy:</b>\n"
        "• Your credentials are encrypted and secure\n"
        "• Data is never shared with third parties\n"
        "• You can delete your account anytime\n\n"
        "<b>Need Help?</b>\n"
        "If you have issues, make sure your Aspen credentials are correct and try /register again.",
        parse_mode='HTML'
    )

# Callback query handlers
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks."""
    query = update.callback_query
    await query.answer()

    if query.data == "update_creds":
        await query.edit_message_text(
            "🔐 <b>Update Credentials</b>\n\n"
            "Please send your new Aspen username:",
            parse_mode='HTML'
        )
        context.user_data['updating'] = 'credentials'
        return SET_CREDENTIALS_USERNAME

    # Removed email-related options - Telegram only

    elif query.data == "set_notification_time":
        await query.edit_message_text(
            "⏰ <b>Set Notification Time</b>\n\n"
            "Please send the time when you want to receive daily grade notifications.\n\n"
            "<b>Format examples:</b>\n"
            "• <code>15:00</code> (3:00 PM)\n"
            "• <code>08:30</code> (8:30 AM)\n"
            "• <code>22:00</code> (10:00 PM)\n\n"
            "Send the time in 24-hour format (HH:MM):",
            parse_mode='HTML'
        )
        return SET_NOTIFICATION_TIME

    elif query.data == "set_timezone":
        # Create timezone selection keyboard
        keyboard = []
        for display_name, timezone in COMMON_TIMEZONES.items():
            keyboard.append([InlineKeyboardButton(display_name, callback_data=f"timezone_{timezone}")])

        keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel_timezone")])
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            "🌍 <b>Select Your Timezone</b>\n\n"
            "Choose your timezone for grade notifications:\n\n"
            "<i>This ensures notifications arrive at the correct local time.</i>",
            parse_mode='HTML',
            reply_markup=reply_markup
        )
        return SET_TIMEZONE

    elif query.data.startswith("timezone_"):
        timezone = query.data.replace("timezone_", "")

        # Update user's timezone
        success = db.update_user_timezone(query.from_user.id, timezone)

        if success:
            # Get display name for confirmation
            timezone_display = "Unknown"
            for display, tz in COMMON_TIMEZONES.items():
                if tz == timezone:
                    timezone_display = display
                    break

            await query.edit_message_text(
                f"✅ <b>Timezone Updated!</b>\n\n"
                f"Your timezone has been set to <b>{timezone_display}</b>.\n\n"
                f"Grade notifications will now be sent according to your local time.\n\n"
                f"Use /settings to change this anytime.",
                parse_mode='HTML'
            )
        else:
            await query.edit_message_text(
                "❌ Failed to update timezone. Please try again with /settings."
            )
        return ConversationHandler.END

    elif query.data == "cancel_timezone":
        await query.edit_message_text(
            "❌ Timezone selection cancelled.\n\n"
            "Use /settings to try again."
        )
        return ConversationHandler.END

    # Setup flow handlers
    elif query.data in ["setup_timezone", "setup_notification_time", "setup_complete"]:
        if query.data == "setup_timezone":
            return await setup_timezone_selection(update, context)
        elif query.data == "setup_notification_time":
            return await setup_notification_time_selection(update, context)
        elif query.data == "setup_complete":
            await complete_setup(update, context)
            return ConversationHandler.END

    elif query.data == "delete_account":
        keyboard = [
            [InlineKeyboardButton("✅ Yes, Delete", callback_data="confirm_delete")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_delete")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            "🗑️ <b>Delete Account</b>\n\n"
            "⚠️ This will permanently delete your account and all data.\n"
            "Are you sure you want to continue?",
            parse_mode='HTML',
            reply_markup=reply_markup
        )

    elif query.data == "confirm_delete":
        success = db.delete_user(update.effective_user.id)
        if success:
            await query.edit_message_text(
                "🗑️ <b>Account Deleted</b>\n\n"
                "Your account has been permanently deleted.\n"
                "Use /register to create a new account.",
                parse_mode='HTML'
            )
        else:
            await query.edit_message_text(
                "❌ Failed to delete account. Please try again."
            )
        return ConversationHandler.END

    elif query.data == "cancel_delete":
        await query.edit_message_text(
            "✅ Account deletion cancelled.\n\n"
            "Your account remains active."
        )
        return ConversationHandler.END

    # Removed notification method handling - Telegram only

# Conversation handlers
registration_handler = ConversationHandler(
    entry_points=[CommandHandler("register", register)],
    states={
        REGISTER_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_username)],
        REGISTER_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_password)],
    },
    fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)]
)

settings_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(button_callback)],
    states={
        SET_CREDENTIALS_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_username)],
        SET_CREDENTIALS_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_password)],
        SET_NOTIFICATION_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_notification_time)],
        SET_TIMEZONE: [CallbackQueryHandler(button_callback)],
    },
    fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)]
)

setup_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(button_callback)],
    states={
        SETUP_TIMEZONE: [CallbackQueryHandler(button_callback)],
        SETUP_NOTIFICATION_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, setup_notification_time_input)],
    },
    fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)]
)
