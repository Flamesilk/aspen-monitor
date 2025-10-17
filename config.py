import os
from decouple import config, Csv

ENV = config("ENV", None)
SERVERLESS = config("SERVERLESS", "False").lower() == "true"
TELEGRAM_TOKEN = config("TELEGRAM_BOT_TOKEN")
# MONGODB_URI = config("MONGODB_URI", "mongodb://localhost:27017")
# MONGODB_NAME = config("MONGODB_NAME", "habitbuilder")
WEBHOOK_URL = config('WEBHOOK_URL', default='')
DONATION_URL = config("DONATION_URL", None)

# Email configuration removed - Telegram only notifications

# GEMINI_API_KEY = config("GEMINI_API_KEY", None)

PORT = config('PORT', default=8000, cast=int)

TIMEZONE = config('TIMEZONE', default='America/Chicago')

# Get authorized chat IDs as a list of integers
AUTHORIZED_CHAT_IDS = [
    int(chat_id)
    for chat_id in config('AUTHORIZED_CHAT_IDS', default='', cast=Csv())
]

# Admin user IDs (comma-separated list)
ADMIN_USER_IDS = [
    int(chat_id)
    for chat_id in config('ADMIN_USER_IDS', default='', cast=Csv())
]
