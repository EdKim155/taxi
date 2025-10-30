from datetime import datetime, timedelta
from typing import Dict, Any, Tuple
import pytz
from bot.services.sheets_service import SheetsService
from bot.services.pdf_service import PDFService
from bot.services.transaction_service import TransactionService


class WaybillService:
    def __init__(self, sheets_service: SheetsService):
        self.sheets = sheets_service
        self.pdf_service = PDFService()
        self.tx_service = TransactionService(sheets_service)
    
    def validate_odometer(
        self,
        odo_input: float,
        last_odo: float,
        require_confirmation: bool = True
    ) -> Tuple[bool, str]:
        """
        Validate odometer reading.
        
        Returns:
            tuple: (is_valid, message)
        """
        if odo_input <= 0:
            return False, "Показания одометра должны быть больше 0"
        
        if odo_input < last_odo and require_confirmation:
            return False, f"⚠️ Внимание! Введённый пробег ({odo_input} км) меньше предыдущего ({last_odo} км).\n\nВы уверены, что хотите продолжить?"
        
        return True, ""
    
    def create_waybill(
        self,
        driver_data: Dict[str, Any],
        odo_input: float,
        force: bool = False
    ) -> Tuple[bool, str, str]:
        """
        Create waybill for driver.
        
        Returns:
            tuple: (success, message, pdf_filepath)
        """
        try:
            driver_id = driver_data.get('driver_id', '')
            
            # Get settings
            settings = self.sheets.get_settings()
            
            # Validate odometer
            last_odo = float(driver_data.get('last_odo', 0))
            is_valid, validation_msg = self.validate_odometer(odo_input, last_odo, not force)
            
            if not is_valid and not force:
                return False, validation_msg, ""
            
            # Get price
            pl_price = float(driver_data.get('pl_price', settings.get('pl_price_default', 20)))
            
            # Check and debit balance
            success, new_balance, error_msg = self.tx_service.debit_for_waybill(
                driver_id,
                driver_data,
                "pending",
                pl_price
            )
            
            if not success:
                return False, error_msg, ""
            
            # Get timezone
            tz_name = driver_data.get('tz', settings.get('tz_default', 'Europe/Moscow'))
            tz = pytz.timezone(tz_name)
            
            # Calculate times
            dt_fact = datetime.now(tz)
            time_shift = settings.get('time_shift_minutes', 60)
            dt_print = dt_fact - timedelta(minutes=time_shift)
            
            # Generate waybill number
            wb_number = self.sheets.get_next_waybill_number()
            
            # Calculate effective odometer
            odo_delta = float(driver_data.get('odo_delta', 0))
            if settings.get('apply_odo_delta', True):
                odo_effective = max(0, odo_input - odo_delta)
            else:
                odo_effective = odo_input
            
            # Prepare waybill data
            waybill_data = {
                'wb_number': wb_number,
                'odo_input': odo_input,
                'odo_effective': odo_effective
            }
            
            # Generate PDF
            pdf_filename, pdf_filepath = self.pdf_service.generate_waybill_pdf(
                waybill_data,
                driver_data,
                settings
            )
            
            # Save waybill record to sheets
            wb_record = {
                'wb_id': f"WB-{dt_fact.strftime('%Y%m%d%H%M%S')}",
                'wb_number': wb_number,
                'dt_fact': dt_fact.strftime('%Y-%m-%d %H:%M:%S'),
                'dt_print': dt_print.strftime('%Y-%m-%d %H:%M:%S'),
                'driver_id': driver_id,
                'car_plate': driver_data.get('car_plate', ''),
                'odo_input': odo_input,
                'odo_effective': odo_effective,
                'price': pl_price,
                'balance_after': new_balance,
                'pdf_url': pdf_filename,
                'status': 'ok',
                'error': ''
            }
            
            self.sheets.add_waybill(wb_record)
            
            # Update last odometer
            update_with = settings.get('update_last_odo_with', 'input')
            odo_to_save = odo_input if update_with == 'input' else odo_effective
            self.sheets.update_driver_last_odo(driver_id, odo_to_save)
            
            # Prepare success message
            message = f"""
✅ <b>Путевой лист успешно сформирован!</b>

📋 <b>Номер ПЛ:</b> {wb_number}
📅 <b>Дата/время:</b> {dt_print.strftime('%d.%m.%Y %H:%M')}
🚗 <b>ГРЗ:</b> {driver_data.get('car_plate', 'N/A')}
📏 <b>Пробег:</b> {odo_effective} км

💳 <b>Списано:</b> {pl_price:.2f} ₽
💰 <b>Остаток баланса:</b> {new_balance:.2f} ₽
"""
            
            if odo_delta != 0:
                message += f"\n<i>Применена коррекция: -{odo_delta} км</i>"
            
            return True, message, pdf_filepath
            
        except Exception as e:
            # Log error and save to sheets
            error_msg = f"Ошибка генерации ПЛ: {str(e)}"
            
            # Try to save error record
            try:
                tz_name = driver_data.get('tz', 'Europe/Moscow')
                tz = pytz.timezone(tz_name)
                dt_fact = datetime.now(tz)
                
                wb_record = {
                    'wb_id': f"WB-{dt_fact.strftime('%Y%m%d%H%M%S')}",
                    'wb_number': 'ERROR',
                    'dt_fact': dt_fact.strftime('%Y-%m-%d %H:%M:%S'),
                    'dt_print': '',
                    'driver_id': driver_data.get('driver_id', ''),
                    'car_plate': driver_data.get('car_plate', ''),
                    'odo_input': odo_input,
                    'odo_effective': 0,
                    'price': 0,
                    'balance_after': driver_data.get('balance', 0),
                    'pdf_url': '',
                    'status': 'error',
                    'error': error_msg
                }
                
                self.sheets.add_waybill(wb_record)
            except:
                pass
            
            return False, f"❌ {error_msg}", ""
