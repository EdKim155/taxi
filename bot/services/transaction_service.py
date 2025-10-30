from datetime import datetime
from typing import Dict, Any
import pytz
from bot.services.sheets_service import SheetsService


class TransactionService:
    def __init__(self, sheets_service: SheetsService):
        self.sheets = sheets_service
    
    def generate_tx_id(self) -> str:
        """Generate unique transaction ID."""
        now = datetime.now()
        return f"TX-{now.strftime('%Y%m%d%H%M%S')}"
    
    def debit_for_waybill(
        self,
        driver_id: str,
        driver_data: Dict[str, Any],
        wb_number: str,
        amount: float
    ) -> tuple[bool, float, str]:
        """
        Debit amount from driver's balance for waybill.
        
        Returns:
            tuple: (success, new_balance, error_message)
        """
        current_balance = float(driver_data.get('balance', 0))
        
        # Check if sufficient balance
        if current_balance < amount:
            return False, current_balance, f"Недостаточно средств. Баланс: {current_balance:.2f} ₽, требуется: {amount:.2f} ₽"
        
        # Calculate new balance
        new_balance = current_balance - amount
        
        # Update balance in sheets
        success = self.sheets.update_driver_balance(driver_id, new_balance)
        if not success:
            return False, current_balance, "Ошибка обновления баланса"
        
        # Get timezone
        tz_name = driver_data.get('tz', 'Europe/Moscow')
        tz = pytz.timezone(tz_name)
        now = datetime.now(tz)
        
        # Create transaction record
        tx_data = {
            'tx_id': self.generate_tx_id(),
            'dt': now.strftime('%Y-%m-%d %H:%M:%S'),
            'driver_id': driver_id,
            'type': 'debit',
            'amount': amount,
            'reason': f'ПЛ №{wb_number}',
            'balance_after': new_balance
        }
        
        # Add transaction to sheets
        self.sheets.add_transaction(tx_data)
        
        return True, new_balance, ""
    
    def get_balance_summary(self, driver_id: str, driver_data: Dict[str, Any]) -> str:
        """Get formatted balance summary with recent transactions."""
        balance = float(driver_data.get('balance', 0))
        transactions = self.sheets.get_driver_transactions(driver_id, limit=3)
        
        summary = f"💰 <b>Текущий баланс:</b> {balance:.2f} ₽\n\n"
        
        if transactions:
            summary += "<b>Последние операции:</b>\n"
            for tx in reversed(transactions):
                tx_type = tx.get('type', '')
                amount = float(tx.get('amount', 0))
                dt = tx.get('dt', '')
                reason = tx.get('reason', '')
                
                if tx_type == 'debit':
                    emoji = "📤"
                    sign = "-"
                else:
                    emoji = "📥"
                    sign = "+"
                
                summary += f"{emoji} {sign}{amount:.2f} ₽ | {reason}\n"
                summary += f"   <i>{dt}</i>\n"
        else:
            summary += "<i>История операций пуста</i>\n"
        
        return summary
