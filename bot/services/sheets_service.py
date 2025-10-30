import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from typing import Optional, Dict, List, Any
import config


class SheetsService:
    def __init__(self):
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            config.GOOGLE_SERVICE_ACCOUNT_FILE,
            scope
        )
        self.client = gspread.authorize(creds)
        self.spreadsheet = self.client.open_by_key(config.GOOGLE_SHEET_ID)
        
        # Cache worksheets
        self.drivers_sheet = self.spreadsheet.worksheet('drivers')
        self.waybills_sheet = self.spreadsheet.worksheet('waybills')
        self.transactions_sheet = self.spreadsheet.worksheet('transactions')
        self.settings_sheet = self.spreadsheet.worksheet('settings')
    
    def get_settings(self) -> Dict[str, Any]:
        """Get system settings from settings sheet."""
        records = self.settings_sheet.get_all_records()
        settings = {}
        for record in records:
            settings[record.get('parameter', '')] = record.get('value', '')
        
        # Set defaults if not found
        return {
            'pl_price_default': float(settings.get('pl_price_default', 20)),
            'tz_default': settings.get('tz_default', 'Europe/Moscow'),
            'time_shift_minutes': int(settings.get('time_shift_minutes', 60)),
            'apply_odo_delta': str(settings.get('apply_odo_delta', 'true')).lower() == 'true',
            'update_last_odo_with': settings.get('update_last_odo_with', 'input')
        }
    
    def get_driver_by_phone(self, phone: str) -> Optional[Dict[str, Any]]:
        """Get driver by phone number."""
        records = self.drivers_sheet.get_all_records()
        for idx, record in enumerate(records, start=2):
            if record.get('phone', '').strip() == phone.strip():
                record['_row'] = idx
                return record
        return None
    
    def get_driver_by_telegram_id(self, tg_user_id: int) -> Optional[Dict[str, Any]]:
        """Get driver by Telegram user ID."""
        records = self.drivers_sheet.get_all_records()
        for idx, record in enumerate(records, start=2):
            if str(record.get('tg_user_id', '')).strip() == str(tg_user_id).strip():
                record['_row'] = idx
                return record
        return None
    
    def update_driver_telegram_id(self, phone: str, tg_user_id: int) -> bool:
        """Update driver's Telegram ID after first authorization."""
        driver = self.get_driver_by_phone(phone)
        if driver:
            row = driver['_row']
            # Find column index for tg_user_id
            headers = self.drivers_sheet.row_values(1)
            col_idx = headers.index('tg_user_id') + 1
            self.drivers_sheet.update_cell(row, col_idx, tg_user_id)
            return True
        return False
    
    def update_driver_balance(self, driver_id: str, new_balance: float) -> bool:
        """Update driver's balance."""
        records = self.drivers_sheet.get_all_records()
        for idx, record in enumerate(records, start=2):
            if record.get('driver_id', '').strip() == driver_id.strip():
                headers = self.drivers_sheet.row_values(1)
                col_idx = headers.index('balance') + 1
                self.drivers_sheet.update_cell(idx, col_idx, new_balance)
                return True
        return False
    
    def update_driver_last_odo(self, driver_id: str, odo: float) -> bool:
        """Update driver's last odometer reading."""
        records = self.drivers_sheet.get_all_records()
        for idx, record in enumerate(records, start=2):
            if record.get('driver_id', '').strip() == driver_id.strip():
                headers = self.drivers_sheet.row_values(1)
                col_idx = headers.index('last_odo') + 1
                self.drivers_sheet.update_cell(idx, col_idx, odo)
                return True
        return False
    
    def get_next_waybill_number(self) -> str:
        """Generate next waybill number."""
        records = self.waybills_sheet.get_all_records()
        count = len(records) + 1
        now = datetime.now()
        return f"76-{now.strftime('%Y%m')}-{count:04d}"
    
    def add_waybill(self, waybill_data: Dict[str, Any]) -> bool:
        """Add new waybill record."""
        headers = self.waybills_sheet.row_values(1)
        row = []
        for header in headers:
            row.append(waybill_data.get(header, ''))
        self.waybills_sheet.append_row(row)
        return True
    
    def add_transaction(self, tx_data: Dict[str, Any]) -> bool:
        """Add new transaction record."""
        headers = self.transactions_sheet.row_values(1)
        row = []
        for header in headers:
            row.append(tx_data.get(header, ''))
        self.transactions_sheet.append_row(row)
        return True
    
    def get_driver_transactions(self, driver_id: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Get last N transactions for driver."""
        records = self.transactions_sheet.get_all_records()
        driver_txs = [tx for tx in records if tx.get('driver_id') == driver_id]
        return driver_txs[-limit:] if driver_txs else []
