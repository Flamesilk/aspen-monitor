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

        scraper = AspenScraper()
        if not scraper.login():
            logger.error("Failed to login to Aspen during scheduled check")
            return

        class_list = scraper.get_class_list()
        if not class_list:
            logger.error("Failed to fetch classes during scheduled check")
            return

        # TODO: Compare with previous grades and only notify if there are changes
        message = f"📚 Scheduled Grade Check ({current_time.strftime('%I:%M %p %Z')})\n\n"

        for class_info in class_list:
            course_name = class_info.get('courseName', '')
            grade = class_info.get('sectionTermAverage', 'No grade')
            teacher = class_info.get('teacherName', '')

            message += f"📘 {course_name}\n"
            message += f"Grade: {grade}\n"
            message += f"Teacher: {teacher}\n\n"

        # Send the message to all authorized users
        for chat_id in config.AUTHORIZED_CHAT_IDS:
            try:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=message
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
    job_time = time(hour=14, minute=3, tzinfo=tz)
    app.job_queue.run_daily(
        fetch_and_notify,
        time=job_time,
        name='daily_grade_check'
    )

    logger.info(f"Scheduled daily grade check for {job_time.strftime('%I:%M %p')} {tz.zone}")
