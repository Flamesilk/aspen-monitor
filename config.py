import os
from decouple import config, Csv

ASPEN_USERNAME = config("ASPEN_USERNAME")
ASPEN_PASSWORD = config("ASPEN_PASSWORD")

ENV = config("ENV", None)
SERVERLESS = config("SERVERLESS", "False").lower() == "true"
TELEGRAM_TOKEN = config("TELEGRAM_BOT_TOKEN")
# MONGODB_URI = config("MONGODB_URI", "mongodb://localhost:27017")
# MONGODB_NAME = config("MONGODB_NAME", "habitbuilder")
WEBHOOK_URL = config('WEBHOOK_URL', default='')
DONATION_URL = config("DONATION_URL", None)

# SMTP configuration
# SMTP_SERVER = config("SMTP_SERVER", "smtp.gmail.com")  # Default to Gmail SMTP
# SMTP_PORT = int(config("SMTP_PORT", "587"))  # Default TLS port
# SMTP_USERNAME = config("SMTP_FROM_EMAIL")  # Your email address
# SMTP_PASSWORD = config("SMTP_PASSWORD")  # Your app password
# SMTP_FROM_EMAIL = config("SMTP_FROM_EMAIL")  # Can be same as SMTP_USERNAME
# SMTP_TO_EMAIL = config("SMTP_TO_EMAIL")  # Where to receive feedback

# GEMINI_API_KEY = config("GEMINI_API_KEY", None)

PORT = config('PORT', default=8000, cast=int)

TIMEZONE = config('TIMEZONE', default='America/Chicago')

# Get authorized chat IDs as a list of integers
AUTHORIZED_CHAT_IDS = [
    int(chat_id)
    for chat_id in config('AUTHORIZED_CHAT_IDS', default='', cast=Csv())
]
