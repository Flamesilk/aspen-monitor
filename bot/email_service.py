import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import config
import logging

logger = logging.getLogger(__name__)

def send_feedback_email(feedback_type: str, feedback_text: str, user_info: dict) -> bool:
    """
    Send feedback email using SMTP.

    Args:
        feedback_type: Type of feedback (bug, feature, success, question)
        feedback_text: The actual feedback message
        user_info: Dictionary containing user information

    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        # Format the email content
        username = user_info.get('username', 'No username')
        user_id = user_info.get('id', 'No ID')
        first_name = user_info.get('first_name', 'No name')

        subject = f"HabitBuilder Feedback: {feedback_type.title()} from @{username}"

        content = f"""
New {feedback_type} feedback received from HabitBuilder user:

User Information:
----------------
Username: @{username}
User ID: {user_id}
Name: {first_name}

Feedback:
---------
{feedback_text}
"""
        # Create message
        msg = MIMEMultipart()
        msg['From'] = config.SMTP_FROM_EMAIL
        msg['To'] = config.SMTP_TO_EMAIL
        msg['Subject'] = subject
        msg.attach(MIMEText(content, 'plain'))

        # Create SMTP connection
        with smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT) as server:
            server.starttls()  # Enable TLS
            server.login(config.SMTP_USERNAME, config.SMTP_PASSWORD)
            server.send_message(msg)

        logger.info(f"Feedback email sent successfully to {config.SMTP_TO_EMAIL}")
        return True

    except Exception as e:
        logger.error(f"Error sending feedback email: {str(e)}")
        return False
