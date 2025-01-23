import os
from decouple import config

ASPEN_USERNAME = config("ASPEN_USERNAME")
ASPEN_PASSWORD = config("ASPEN_PASSWORD")

ENV = os.getenv("ENV", None)
SERVERLESS = os.getenv("SERVERLESS", "False").lower() == "true"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_NAME = os.getenv("MONGODB_NAME", "habitbuilder")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
DONATION_URL = os.getenv("DONATION_URL", None)

# SMTP configuration
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")  # Default to Gmail SMTP
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))  # Default TLS port
SMTP_USERNAME = os.getenv("SMTP_FROM_EMAIL")  # Your email address
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")  # Your app password
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL")  # Can be same as SMTP_USERNAME
SMTP_TO_EMAIL = os.getenv("SMTP_TO_EMAIL")  # Where to receive feedback

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", None)
