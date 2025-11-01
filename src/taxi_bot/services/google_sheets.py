from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Iterable, List
from uuid import uuid4

import gspread
from gspread.exceptions import WorksheetNotFound
from google.oauth2.service_account import Credentials

from taxi_bot.config import get_settings
from taxi_bot.exceptions import DriverNotFoundError
from taxi_bot.models import Driver

logger = logging.getLogger(__name__)

DRIVERS_SHEET = "drivers"
WAYBILLS_SHEET = "waybills"
TRANSACTIONS_SHEET = "transactions"
SETTINGS_SHEET = "settings"


@dataclass(slots=True)
class DriverRow:
    driver: Driver
    row_index: int


class GoogleSheetsClient:
    """Wrapper around Google Sheets providing typed access to business entities."""

    SCOPES = (
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    )

    def __init__(self) -> None:
        settings = get_settings()
        credentials = Credentials.from_service_account_file(
            str(settings.google_service_account_json), scopes=self.SCOPES
        )
        self._client = gspread.authorize(credentials)
        self._spreadsheet = self._client.open_by_key(settings.google_spreadsheet_id)

    # -- Generic helpers -------------------------------------------------

    def _worksheet(self, name: str) -> gspread.Worksheet:
        try:
            return self._spreadsheet.worksheet(name)
        except WorksheetNotFound as exc:  # pragma: no cover - configuration issue
            logger.error("Worksheet %s not found", name)
            raise exc

    @staticmethod
    def _bool(value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if value is None:
            return False
        return str(value).strip().lower() in {"1", "true", "yes", "y"}

    @staticmethod
    def _float(value: Any, default: float = 0.0) -> float:
        try:
            return float(str(value).replace(",", "."))
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _int(value: Any, default: int = 0) -> int:
        try:
            return int(float(str(value)))
        except (TypeError, ValueError):
            return default

    # -- Drivers ---------------------------------------------------------

    def list_drivers(self) -> Iterable[DriverRow]:
        ws = self._worksheet(DRIVERS_SHEET)
        records = ws.get_all_records()
        for idx, record in enumerate(records, start=2):  # account for header row
            yield DriverRow(driver=self._map_driver(record), row_index=idx)

    def _map_driver(self, record: Dict[str, Any]) -> Driver:
        return Driver(
            driver_id=str(record.get("driver_id")),
            fio=str(record.get("fio")),
            phone=str(record.get("phone")),
            car_id=str(record.get("car_id")),
            car_plate=str(record.get("car_plate")),
            car_model=str(record.get("car_model")),
            vin=str(record.get("vin")) if record.get("vin") else None,
            org_name=str(record.get("org_name")),
            med_worker=str(record.get("med_worker")),
            mech_worker=str(record.get("mech_worker")),
            last_odo=self._float(record.get("last_odo")),
            odo_delta=self._float(record.get("odo_delta")),
            balance=self._float(record.get("balance")),
            pl_price=self._float(record.get("pl_price"), get_settings().pl_price_default),
            tz=str(record.get("tz")) if record.get("tz") else get_settings().tz_default,
            is_active=self._bool(record.get("is_active", True)),
            tg_user_id=self._int(record.get("tg_user_id"), 0) or None,
        )

    def get_driver_by_phone(self, phone: str) -> DriverRow:
        for row in self.list_drivers():
            if row.driver.phone.replace(" ", "") == phone.replace(" ", ""):
                return row
        raise DriverNotFoundError(f"Driver with phone {phone} not found")

    def get_driver_by_tg_user_id(self, tg_user_id: int) -> DriverRow:
        for row in self.list_drivers():
            if row.driver.tg_user_id == tg_user_id:
                return row
        raise DriverNotFoundError(f"Driver with telegram id {tg_user_id} not found")

    def update_driver(self, row_index: int, updates: Dict[str, Any]) -> None:
        ws = self._worksheet(DRIVERS_SHEET)
        headers = ws.row_values(1)
        header_map = {header: idx for idx, header in enumerate(headers, start=1)}
        cells = []
        for key, value in updates.items():
            if key not in header_map:
                continue
            cell_label = gspread.utils.rowcol_to_a1(row_index, header_map[key])
            cells.append({"range": cell_label, "values": [[value]]})
        if cells:
            ws.batch_update(cells, value_input_option="USER_ENTERED")

    # -- Waybills --------------------------------------------------------

    def reserve_waybill_number(self, dt: datetime) -> tuple[str, str]:
        counter = self._int(self.get_setting("waybill_counter", default="0")) + 1
        pattern = self.get_setting("waybill_number_pattern", default="76-{year}{month}-{counter:04d}")
        formatted = pattern.format(
            counter=counter,
            year=dt.strftime("%Y"),
            month=dt.strftime("%m"),
            day=dt.strftime("%d"),
        )
        self.set_setting("waybill_counter", str(counter))
        wb_id = uuid4().hex
        return wb_id, formatted

    def append_waybill(self, record: Dict[str, Any]) -> None:
        self._append_record(WAYBILLS_SHEET, record)

    # -- Transactions ----------------------------------------------------

    def append_transaction(self, record: Dict[str, Any]) -> None:
        self._append_record(TRANSACTIONS_SHEET, record)

    def _append_record(self, sheet_name: str, record: Dict[str, Any]) -> None:
        ws = self._worksheet(sheet_name)
        headers = ws.row_values(1)
        row = [record.get(header, "") for header in headers]
        ws.append_row(row, value_input_option="USER_ENTERED")

    def list_recent_transactions(self, driver_id: str, limit: int = 3) -> List[Dict[str, Any]]:
        ws = self._worksheet(TRANSACTIONS_SHEET)
        records = ws.get_all_records()
        driver_records = [record for record in records if str(record.get("driver_id")) == driver_id]
        recent = driver_records[-limit:]
        return list(reversed(recent))

    # -- Settings --------------------------------------------------------

    def get_setting(self, key: str, default: str | None = None) -> str:
        ws = self._worksheet(SETTINGS_SHEET)
        values = ws.get_all_records(expected_headers=["key", "value"])
        for record in values:
            if record.get("key") == key:
                return str(record.get("value"))
        if default is None:
            raise KeyError(f"Setting {key} not found")
        return default

    def set_setting(self, key: str, value: str) -> None:
        ws = self._worksheet(SETTINGS_SHEET)
        values = ws.get_all_records(expected_headers=["key", "value"])
        for index, record in enumerate(values, start=2):
            if record.get("key") == key:
                cell_range = gspread.utils.rowcol_to_a1(index, 2)
                ws.update(cell_range, value, value_input_option="USER_ENTERED")
                return
        ws.append_row([key, value], value_input_option="USER_ENTERED")

    # -- Helpers ---------------------------------------------------------

    @staticmethod
    def format_datetime(dt: datetime) -> str:
        return dt.isoformat()


__all__ = ["GoogleSheetsClient", "DriverRow"]
