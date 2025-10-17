from telegram.ext import Application, ContextTypes
from bot.scraper import AspenScraper
# Email service removed - Telegram only notifications
from database import Database
import logging
from datetime import time, datetime
import pytz
import asyncio
import random
import config

logger = logging.getLogger(__name__)

# Initialize database
db = Database()

# Rate limiting and request spacing
REQUEST_DELAY_MIN = 30  # Minimum 30 seconds between requests
REQUEST_DELAY_MAX = 120  # Maximum 2 minutes between requests
MAX_CONCURRENT_REQUESTS = 3  # Maximum concurrent requests to Aspen

# Global request queue and semaphore
request_semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
last_request_time = 0

async def fetch_and_notify_user(context: ContextTypes.DEFAULT_TYPE):
    """Fetch grades and notify a specific user with rate limiting"""
    async with request_semaphore:
        try:
            user_data = context.job.data
            user_id = user_data['telegram_id']
            username = user_data['aspen_username']
            password = user_data['aspen_password']

            # Check if it's a weekend (Saturday = 5, Sunday = 6)
            current_time = datetime.now()
            if current_time.weekday() >= 5:  # Saturday or Sunday
                logger.info(f"Skipping notification for user {user_id} - weekend detected (day {current_time.weekday()})")
                return

            logger.info(f"Processing scheduled grade check for user {user_id} ({username})")

            # Add random delay to prevent simultaneous requests
            delay = random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX)
            logger.info(f"Waiting {delay:.1f} seconds before request to avoid rate limiting")
            await asyncio.sleep(delay)

            # Initialize scraper with user's credentials
            scraper = AspenScraper(username, password)

            # Calculate actual notification time vs scheduled time
            current_time = datetime.now()
            scheduled_time = context.job.scheduled_time if hasattr(context.job, 'scheduled_time') else current_time

            # Add delay information to title
            delay_minutes = int((current_time - scheduled_time).total_seconds() / 60) if current_time > scheduled_time else 0

            # Format current time with date and local timezone
            formatted_time = current_time.strftime('%A, %B %d, %Y at %I:%M %p %Z')

            messages = scraper.fetch_formatted_grades(
                title=f"📚 Daily Grade Update ({formatted_time})"
            )

            # Send notifications via Telegram
            for message in messages:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode='HTML'
                )

            # Send delay explanation if there was a delay
            if delay_minutes > 0:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"⏰ <b>Delay Notice</b>\n\n"
                         f"Your notification was delayed by {delay_minutes} minutes due to rate limiting protection.\n\n"
                         f"This ensures reliable service for all users by preventing server overload.",
                    parse_mode='HTML'
                )

            logger.info(f"Sent scheduled update to user {user_id}")

        except Exception as e:
            logger.error(f"Error in scheduled grade fetch for user {user_data.get('telegram_id', 'unknown')}: {str(e)}", exc_info=True)

def setup_scheduler(app: Application):
    """Setup the job queue with individual user grade checking jobs"""
    # Get timezone
    tz = pytz.timezone(config.TIMEZONE)

    # Get all active users and their notification times
    users = db.get_all_active_users()
    logger.info(f"Setting up scheduled jobs for {len(users)} users")

    for user in users:
        try:
            # Get user settings
            settings = db.get_user_settings(user['telegram_id'])
            notification_time = settings.get('notification_time', '15:00') if settings else '15:00'
            user_timezone = settings.get('timezone', 'America/Chicago') if settings else 'America/Chicago'

            # Use user's timezone instead of global timezone
            user_tz = pytz.timezone(user_timezone)

            # Parse time (HH:MM format) and add random offset
            hour, minute = map(int, notification_time.split(':'))

            # Add random offset to prevent all users hitting at exact same time
            # Use 15-minute intervals for better distribution
            random_offset = random.choice([0, 15, 30, 45])  # 15-minute interval offset
            minute += random_offset
            if minute >= 60:
                hour += 1
                minute -= 60

            job_time = time(hour=hour, minute=minute, tzinfo=user_tz)

            # Create individual job for this user
            job_name = f"grade_check_user_{user['telegram_id']}"
            app.job_queue.run_daily(
                fetch_and_notify_user,
                time=job_time,
                name=job_name,
                data=user  # Pass user data to the job
            )

            logger.info(f"Scheduled grade check for user {user['telegram_id']} at {notification_time} {user_timezone}")

        except Exception as e:
            logger.error(f"Error setting up job for user {user['telegram_id']}: {str(e)}")
            continue

    logger.info(f"Completed scheduling {len(users)} individual grade check jobs")
