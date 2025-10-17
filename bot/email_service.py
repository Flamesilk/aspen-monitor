import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import config
import logging
from typing import List

logger = logging.getLogger(__name__)

def send_grade_notification(user_email: str, user_name: str, grade_messages: List[str]) -> bool:
    """
    Send grade notification email to user.

    Args:
        user_email: User's email address
        user_name: User's name
        grade_messages: List of formatted grade messages

    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        subject = f"📚 Daily Grade Update - {user_name}"

        # Combine all grade messages into HTML content
        html_content = f"""
        <html>
        <body>
            <h2>📚 Daily Grade Update</h2>
            <p>Hello {user_name},</p>
            <p>Here are your current grades and assignments from Aspen:</p>
            <hr>
        """

        for message in grade_messages:
            # Convert Telegram HTML to email HTML
            email_message = message.replace('<b>', '<strong>').replace('</b>', '</strong>')
            email_message = email_message.replace('<i>', '<em>').replace('</i>', '</em>')
            email_message = email_message.replace('<code>', '<code>').replace('</code>', '</code>')
            html_content += f"<div style='margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px;'>{email_message}</div>"

        html_content += """
            <hr>
            <p><em>This is an automated message from your Aspen Grade Monitor.</em></p>
            <p>To stop receiving these emails, use /settings in your Telegram bot.</p>
        </body>
        </html>
        """

        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = config.SMTP_FROM_EMAIL
        msg['To'] = user_email
        msg['Subject'] = subject

        # Add HTML content
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)

        # Create SMTP connection
        with smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT) as server:
            server.starttls()  # Enable TLS
            server.login(config.SMTP_USERNAME, config.SMTP_PASSWORD)
            server.send_message(msg)

        logger.info(f"Grade notification sent successfully to {user_email}")
        return True

    except Exception as e:
        logger.error(f"Error sending grade notification to {user_email}: {str(e)}")
        return False

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
