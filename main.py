#!/usr/bin/env python3
import logging
import sys
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters
)

import config
from bot.services.sheets_service import SheetsService
from bot.handlers.auth_handler import AuthHandler, PHONE_REQUEST
from bot.handlers.main_handler import MainHandler, ODOMETER_INPUT, CONFIRM_LOW_ODO

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, config.LOG_LEVEL, logging.INFO),
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def main():
    """Start the bot."""
    # Validate configuration
    if not config.TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is not set!")
        sys.exit(1)
    
    if not config.GOOGLE_SHEET_ID:
        logger.error("GOOGLE_SHEET_ID is not set!")
        sys.exit(1)
    
    logger.info("Starting Taxi Waybill Bot...")
    
    # Initialize services
    try:
        sheets_service = SheetsService()
        logger.info("Google Sheets service initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Google Sheets service: {e}")
        sys.exit(1)
    
    # Initialize handlers
    auth_handler = AuthHandler(sheets_service)
    main_handler = MainHandler(sheets_service)
    
    # Create application
    application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
    
    # Authorization conversation handler
    auth_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', auth_handler.start)],
        states={
            PHONE_REQUEST: [
                MessageHandler(filters.CONTACT, auth_handler.handle_phone),
            ],
        },
        fallbacks=[CommandHandler('cancel', auth_handler.cancel)],
    )
    
    # Waybill creation conversation handler
    waybill_conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(
                filters.Regex('^📋 Получить путевой лист$'),
                main_handler.start_waybill
            )
        ],
        states={
            ODOMETER_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, main_handler.handle_odometer)
            ],
            CONFIRM_LOW_ODO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, main_handler.handle_confirmation)
            ],
        },
        fallbacks=[
            CommandHandler('cancel', main_handler.cancel),
            MessageHandler(filters.Regex('^❌ Отмена$'), main_handler.cancel)
        ],
    )
    
    # Add handlers
    application.add_handler(auth_conv_handler)
    application.add_handler(waybill_conv_handler)
    
    # Main menu handlers
    application.add_handler(
        MessageHandler(filters.Regex('^💰 Мой баланс$'), main_handler.balance)
    )
    application.add_handler(
        MessageHandler(filters.Regex('^❓ Помощь$'), main_handler.help_command)
    )
    application.add_handler(CommandHandler('help', main_handler.help_command))
    
    # Start the bot
    logger.info("Bot is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
