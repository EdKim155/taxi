from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from bot.services.sheets_service import SheetsService

# Conversation states
PHONE_REQUEST = 1


class AuthHandler:
    def __init__(self, sheets_service: SheetsService):
        self.sheets = sheets_service
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        user = update.effective_user
        
        # Check if user is already authorized
        driver = self.sheets.get_driver_by_telegram_id(user.id)
        
        if driver:
            # Already authorized
            await update.message.reply_text(
                f"Здравствуйте, {driver.get('fio', 'водитель')}! 👋\n\n"
                "Вы уже авторизованы в системе.\n"
                "Используйте главное меню для работы с ботом.",
                reply_markup=self.get_main_menu_keyboard()
            )
            return ConversationHandler.END
        
        # Request phone authorization
        await update.message.reply_text(
            "👋 Добро пожаловать в систему управления путевыми листами!\n\n"
            "Для авторизации необходимо подтвердить ваш номер телефона.\n"
            "Нажмите кнопку ниже, чтобы поделиться номером.",
            reply_markup=self.get_phone_keyboard()
        )
        
        return PHONE_REQUEST
    
    async def handle_phone(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle phone number from user."""
        contact = update.message.contact
        
        if not contact:
            await update.message.reply_text(
                "❌ Не удалось получить номер телефона.\n"
                "Пожалуйста, используйте кнопку 'Поделиться номером'."
            )
            return PHONE_REQUEST
        
        phone = contact.phone_number
        if not phone.startswith('+'):
            phone = f'+{phone}'
        
        # Check if phone exists in drivers sheet
        driver = self.sheets.get_driver_by_phone(phone)
        
        if not driver:
            await update.message.reply_text(
                f"❌ Доступ запрещён.\n\n"
                f"Номер {phone} не найден в системе.\n"
                f"Обратитесь к администратору для добавления в базу водителей.",
                reply_markup=self.get_remove_keyboard()
            )
            return ConversationHandler.END
        
        # Check if driver is active
        if not driver.get('is_active', True):
            await update.message.reply_text(
                "❌ Ваш аккаунт деактивирован.\n"
                "Обратитесь к администратору.",
                reply_markup=self.get_remove_keyboard()
            )
            return ConversationHandler.END
        
        # Update telegram ID
        user = update.effective_user
        self.sheets.update_driver_telegram_id(phone, user.id)
        
        await update.message.reply_text(
            f"✅ Авторизация успешна!\n\n"
            f"Добро пожаловать, {driver.get('fio', 'водитель')}!\n\n"
            f"🚗 Ваш автомобиль: {driver.get('car_model', 'N/A')}\n"
            f"🔢 ГРЗ: {driver.get('car_plate', 'N/A')}\n"
            f"💰 Баланс: {driver.get('balance', 0):.2f} ₽\n\n"
            "Используйте главное меню для работы с системой.",
            reply_markup=self.get_main_menu_keyboard()
        )
        
        return ConversationHandler.END
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel authorization."""
        await update.message.reply_text(
            "❌ Авторизация отменена.\n"
            "Для повторной попытки используйте команду /start",
            reply_markup=self.get_remove_keyboard()
        )
        return ConversationHandler.END
    
    @staticmethod
    def get_phone_keyboard():
        """Get keyboard with phone request button."""
        keyboard = [[KeyboardButton("📱 Поделиться номером", request_contact=True)]]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    @staticmethod
    def get_main_menu_keyboard():
        """Get main menu keyboard."""
        keyboard = [
            ["💰 Мой баланс", "📋 Получить путевой лист"],
            ["❓ Помощь"]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    @staticmethod
    def get_remove_keyboard():
        """Get empty keyboard to remove previous one."""
        from telegram import ReplyKeyboardRemove
        return ReplyKeyboardRemove()
