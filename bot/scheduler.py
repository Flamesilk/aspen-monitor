from telegram.ext import Application, ContextTypes
from bot.scraper import AspenScraper
import logging
from datetime import time, datetime
import pytz
import config

logger = logging.getLogger(__name__)

async def fetch_and_notify(context: ContextTypes.DEFAULT_TYPE):
    """Fetch grades and notify all authorized users if there are changes"""
    try:
        # Log the current time in the configured timezone
        current_time = datetime.now(pytz.timezone(config.TIMEZONE))
        logger.info(f"Starting scheduled grade check at {current_time}")

        # Initialize scraper and fetch formatted grades
        scraper = AspenScraper()
        messages = scraper.fetch_formatted_grades(
            title=f"📚 Scheduled Grade Check ({current_time.strftime('%I:%M %p %Z')})"
        )

        # Send all messages to each authorized user
        for chat_id in config.AUTHORIZED_CHAT_IDS:
            try:
                for message in messages:
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=message,
                        parse_mode='HTML'
                    )
                logger.info(f"Sent scheduled update to chat_id: {chat_id}")
            except Exception as e:
                logger.error(f"Failed to send update to chat_id {chat_id}: {str(e)}")

    except Exception as e:
        logger.error(f"Error in scheduled grade fetch: {str(e)}", exc_info=True)

def setup_scheduler(app: Application):
    """Setup the job queue with the grade checking job"""
    # Get timezone
    tz = pytz.timezone(config.TIMEZONE)

    # Schedule the job to run every day at 8 AM in the configured timezone
    job_time = time(hour=15, minute=00, tzinfo=tz)
    app.job_queue.run_daily(
        fetch_and_notify,
        time=job_time,
        name='daily_grade_check'
    )

    logger.info(f"Scheduled daily grade check for {job_time.strftime('%I:%M %p')} {tz.zone}")
