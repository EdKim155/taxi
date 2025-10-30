from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from bot.services.sheets_service import SheetsService
from bot.services.transaction_service import TransactionService
from bot.services.waybill_service import WaybillService

# Conversation states
ODOMETER_INPUT, CONFIRM_LOW_ODO = range(2)


class MainHandler:
    def __init__(self, sheets_service: SheetsService):
        self.sheets = sheets_service
        self.tx_service = TransactionService(sheets_service)
        self.wb_service = WaybillService(sheets_service)
    
    def check_auth(self, user_id: int):
        """Check if user is authorized."""
        driver = self.sheets.get_driver_by_telegram_id(user_id)
        return driver
    
    async def balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user balance and transaction history."""
        user = update.effective_user
        driver = self.check_auth(user.id)
        
        if not driver:
            await update.message.reply_text(
                "❌ Вы не авторизованы. Используйте /start для авторизации."
            )
            return
        
        driver_id = driver.get('driver_id', '')
        summary = self.tx_service.get_balance_summary(driver_id, driver)
        
        # Add topup instruction
        topup_text = (
            "\n💳 <b>Как пополнить баланс:</b>\n"
            "1. Переведите нужную сумму на реквизиты таксопарка\n"
            "2. Сообщите администратору о пополнении\n"
            "3. Администратор зачислит средства на ваш баланс\n\n"
            "📞 Контакты для связи: /help"
        )
        
        await update.message.reply_text(
            summary + topup_text,
            parse_mode='HTML'
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show help information."""
        help_text = """
❓ <b>СПРАВКА ПО БОТУ</b>

<b>Доступные команды:</b>
• 💰 <b>Мой баланс</b> - проверить баланс и историю операций
• 📋 <b>Получить путевой лист</b> - сформировать новый ПЛ
• ❓ <b>Помощь</b> - эта справка

<b>Как получить путевой лист:</b>
1. Нажмите "Получить путевой лист"
2. Введите текущие показания одометра (км)
3. Получите PDF путевого листа

<b>Стоимость:</b>
Каждый путевой лист стоит 20 ₽ (сумма автоматически списывается с вашего баланса)

<b>Пополнение баланса:</b>
Для пополнения баланса обратитесь к администратору или диспетчеру.

<b>Контакты:</b>
📞 Диспетчер: [указать контакт]
👨‍💼 Администратор: [указать контакт]

<b>Техническая поддержка:</b>
При возникновении технических проблем обратитесь к администратору системы.
"""
        
        await update.message.reply_text(help_text, parse_mode='HTML')
    
    async def start_waybill(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start waybill creation process."""
        user = update.effective_user
        driver = self.check_auth(user.id)
        
        if not driver:
            await update.message.reply_text(
                "❌ Вы не авторизованы. Используйте /start для авторизации."
            )
            return ConversationHandler.END
        
        # Check balance
        settings = self.sheets.get_settings()
        pl_price = float(driver.get('pl_price', settings.get('pl_price_default', 20)))
        balance = float(driver.get('balance', 0))
        
        if balance < pl_price:
            await update.message.reply_text(
                f"❌ <b>Недостаточно средств на балансе!</b>\n\n"
                f"💰 Ваш баланс: {balance:.2f} ₽\n"
                f"💳 Требуется: {pl_price:.2f} ₽\n"
                f"📉 Недостаёт: {pl_price - balance:.2f} ₽\n\n"
                f"Пополните баланс для продолжения.\n"
                f"Инструкции: 💰 Мой баланс",
                parse_mode='HTML',
                reply_markup=self.get_main_menu_keyboard()
            )
            return ConversationHandler.END
        
        # Request odometer
        last_odo = driver.get('last_odo', 0)
        
        await update.message.reply_text(
            f"📏 <b>Введите текущие показания одометра</b>\n\n"
            f"Последний зафиксированный пробег: <b>{last_odo}</b> км\n\n"
            f"Введите число (например: 150000):",
            parse_mode='HTML',
            reply_markup=ReplyKeyboardRemove()
        )
        
        # Store driver data in context
        context.user_data['driver'] = driver
        
        return ODOMETER_INPUT
    
    async def handle_odometer(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle odometer input."""
        text = update.message.text.strip()
        
        # Try to parse as number
        try:
            odo_input = float(text)
        except ValueError:
            await update.message.reply_text(
                "❌ Неверный формат. Введите число (например: 150000):"
            )
            return ODOMETER_INPUT
        
        if odo_input <= 0:
            await update.message.reply_text(
                "❌ Показания одометра должны быть больше 0. Попробуйте снова:"
            )
            return ODOMETER_INPUT
        
        driver = context.user_data.get('driver')
        last_odo = float(driver.get('last_odo', 0))
        
        # Check if odometer is lower than last
        if odo_input < last_odo:
            context.user_data['odo_input'] = odo_input
            
            keyboard = [["✅ Да, продолжить", "❌ Отмена"]]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
            
            await update.message.reply_text(
                f"⚠️ <b>Внимание!</b>\n\n"
                f"Введённый пробег (<b>{odo_input}</b> км) меньше предыдущего (<b>{last_odo}</b> км).\n\n"
                f"Вы уверены, что хотите продолжить?",
                parse_mode='HTML',
                reply_markup=reply_markup
            )
            
            return CONFIRM_LOW_ODO
        
        # Create waybill
        await self.create_and_send_waybill(update, context, driver, odo_input)
        
        return ConversationHandler.END
    
    async def handle_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle low odometer confirmation."""
        text = update.message.text.strip()
        
        if text == "❌ Отмена":
            await update.message.reply_text(
                "❌ Создание путевого листа отменено.",
                reply_markup=self.get_main_menu_keyboard()
            )
            return ConversationHandler.END
        
        if text != "✅ Да, продолжить":
            await update.message.reply_text(
                "Пожалуйста, используйте кнопки ниже."
            )
            return CONFIRM_LOW_ODO
        
        # Get stored data
        driver = context.user_data.get('driver')
        odo_input = context.user_data.get('odo_input')
        
        # Create waybill with force flag
        await self.create_and_send_waybill(update, context, driver, odo_input, force=True)
        
        return ConversationHandler.END
    
    async def create_and_send_waybill(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        driver: dict,
        odo_input: float,
        force: bool = False
    ):
        """Create waybill and send to user."""
        # Show processing message
        processing_msg = await update.message.reply_text(
            "⏳ Формирую путевой лист...",
            reply_markup=self.get_main_menu_keyboard()
        )
        
        try:
            # Create waybill
            success, message, pdf_path = self.wb_service.create_waybill(
                driver,
                odo_input,
                force=force
            )
            
            # Delete processing message
            await processing_msg.delete()
            
            if not success:
                await update.message.reply_text(
                    message,
                    parse_mode='HTML',
                    reply_markup=self.get_main_menu_keyboard()
                )
                return
            
            # Send PDF
            with open(pdf_path, 'rb') as pdf_file:
                await update.message.reply_document(
                    document=pdf_file,
                    caption=message,
                    parse_mode='HTML',
                    reply_markup=self.get_main_menu_keyboard()
                )
        
        except Exception as e:
            await processing_msg.delete()
            await update.message.reply_text(
                f"❌ Произошла ошибка при создании путевого листа:\n{str(e)}\n\n"
                f"Пожалуйста, попробуйте позже или обратитесь к администратору.",
                reply_markup=self.get_main_menu_keyboard()
            )
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel waybill creation."""
        await update.message.reply_text(
            "❌ Создание путевого листа отменено.",
            reply_markup=self.get_main_menu_keyboard()
        )
        return ConversationHandler.END
    
    @staticmethod
    def get_main_menu_keyboard():
        """Get main menu keyboard."""
        keyboard = [
            ["💰 Мой баланс", "📋 Получить путевой лист"],
            ["❓ Помощь"]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
