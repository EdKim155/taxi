import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Google Sheets
GOOGLE_SHEET_ID = os.getenv('GOOGLE_SHEET_ID')
GOOGLE_SERVICE_ACCOUNT_FILE = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE', 'service_account.json')

# Application
TIMEZONE = os.getenv('TIMEZONE', 'Europe/Moscow')
ADMIN_PHONE = os.getenv('ADMIN_PHONE', '')
ADMIN_TELEGRAM_ID = os.getenv('ADMIN_TELEGRAM_ID', '')

# Logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Paths
WAYBILLS_DIR = 'generated_waybills'
TEMPLATES_DIR = 'bot/templates'
STATIC_DIR = 'bot/static'
