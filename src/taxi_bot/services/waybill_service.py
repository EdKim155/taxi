from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Dict, Tuple
from zoneinfo import ZoneInfo

from taxi_bot.config import get_settings
from taxi_bot.exceptions import (
    InactiveDriverError,
    InsufficientBalanceError,
    ValidationError,
    WaybillGenerationError,
)
from taxi_bot.models import Driver, Waybill
from taxi_bot.services.google_sheets import DriverRow, GoogleSheetsClient
from taxi_bot.services.pdf import PdfRenderer

logger = logging.getLogger(__name__)


class WaybillService:
    def __init__(self, sheets: GoogleSheetsClient, pdf_renderer: PdfRenderer) -> None:
        self.sheets = sheets
        self.pdf = pdf_renderer
        self.settings = get_settings()

    # ------------------------------------------------------------------
    def validate_odometer(self, driver: Driver, odo_input: float) -> None:
        if odo_input <= 0:
            raise ValidationError("Пробег должен быть положительным числом.")
        if odo_input + 1e-6 < driver.last_odo:
            logger.warning(
                "Driver %s entered odometer %.2f less than last recorded %.2f",
                driver.driver_id,
                odo_input,
                driver.last_odo,
            )

    def _compute_effective_odometer(self, driver: Driver, odo_input: float) -> float:
        if self.settings.apply_odo_delta:
            return max(0.0, odo_input - driver.odo_delta)
        return odo_input

    def _compute_balance(self, driver: Driver) -> Tuple[float, float]:
        price = driver.effective_price or self.settings.pl_price_default
        balance_after = driver.balance - price
        if balance_after < 0:
            raise InsufficientBalanceError("Недостаточно средств для формирования ПЛ.")
        return price, balance_after

    def _get_timezone(self, driver: Driver) -> ZoneInfo:
        try:
            return ZoneInfo(driver.tz or self.settings.tz_default)
        except Exception:  # pragma: no cover - depends on system tz database
            return ZoneInfo(self.settings.tz_default)

    # ------------------------------------------------------------------
    def issue_waybill(self, driver_row: DriverRow, odo_input: float) -> Waybill:
        driver = driver_row.driver
        if not driver.is_active:
            raise InactiveDriverError("Профиль водителя не активен. Обратитесь к администратору.")

        self.validate_odometer(driver, odo_input)
        price, balance_after = self._compute_balance(driver)

        tz = self._get_timezone(driver)
        dt_fact = datetime.now(tz=tz)
        dt_print = dt_fact - timedelta(minutes=self.settings.time_shift_minutes)

        odo_effective = self._compute_effective_odometer(driver, odo_input)

        wb_id, wb_number = self.sheets.reserve_waybill_number(dt_fact)

        context = self._build_pdf_context(
            driver=driver,
            wb_number=wb_number,
            dt_print=dt_print,
            odo_effective=odo_effective,
        )

        try:
            pdf_path = self.pdf.render_waybill(context)
        except Exception as exc:  # pragma: no cover - depends on weasyprint stack
            logger.exception("Failed to render PDF for waybill %s", wb_number)
            self._log_waybill_error(
                wb_id=wb_id,
                wb_number=wb_number,
                driver=driver,
                dt_fact=dt_fact,
                dt_print=dt_print,
                odo_input=odo_input,
                odo_effective=odo_effective,
                price=price,
                balance_after=driver.balance,
                error=str(exc),
            )
            raise WaybillGenerationError("Не удалось сформировать PDF. Попробуйте позже.") from exc

        pdf_url = self.pdf.build_public_url(pdf_path)

        waybill = Waybill(
            wb_id=wb_id,
            wb_number=wb_number,
            dt_fact=dt_fact,
            dt_print=dt_print,
            driver_id=driver.driver_id,
            car_plate=driver.car_plate,
            odo_input=odo_input,
            odo_effective=odo_effective,
            price=price,
            balance_after=balance_after,
            pdf_path=pdf_path,
            pdf_url=pdf_url,
            status="ok",
        )

        self._persist_waybill(driver_row, waybill)

        return waybill

    # ------------------------------------------------------------------
    def _persist_waybill(self, driver_row: DriverRow, waybill: Waybill) -> None:
        driver = driver_row.driver
        price = waybill.price
        balance_after = waybill.balance_after

        # Update driver balance and odometer
        update_last_odo = (
            waybill.odo_input if self.settings.update_last_odo_with == "input" else waybill.odo_effective
        )
        self.sheets.update_driver(
            driver_row.row_index,
            {
                "balance": balance_after,
                "last_odo": update_last_odo,
            },
        )
        driver.balance = balance_after
        driver.last_odo = update_last_odo

        dt_fact_iso = GoogleSheetsClient.format_datetime(waybill.dt_fact)
        dt_print_iso = GoogleSheetsClient.format_datetime(waybill.dt_print)

        # Append transaction
        tx_record = {
            "tx_id": uuid_hex(),
            "dt": dt_fact_iso,
            "driver_id": driver.driver_id,
            "type": "debit",
            "amount": price,
            "reason": f"ПЛ {waybill.wb_number}",
            "balance_after": balance_after,
        }
        self.sheets.append_transaction(tx_record)

        # Append waybill log
        wb_record = {
            "wb_id": waybill.wb_id,
            "wb_number": waybill.wb_number,
            "dt_fact": dt_fact_iso,
            "dt_print": dt_print_iso,
            "driver_id": driver.driver_id,
            "car_plate": driver.car_plate,
            "odo_input": waybill.odo_input,
            "odo_effective": waybill.odo_effective,
            "price": price,
            "balance_after": balance_after,
            "pdf_url": waybill.pdf_url,
            "status": waybill.status,
            "error": "",
        }
        self.sheets.append_waybill(wb_record)

        logger.info(
            "Waybill %s stored. Balance after debit: %.2f", waybill.wb_number, balance_after
        )

    # ------------------------------------------------------------------
    def _log_waybill_error(
        self,
        wb_id: str,
        wb_number: str,
        driver: Driver,
        dt_fact: datetime,
        dt_print: datetime,
        odo_input: float,
        odo_effective: float,
        price: float,
        balance_after: float,
        error: str,
    ) -> None:
        dt_fact_iso = GoogleSheetsClient.format_datetime(dt_fact)
        dt_print_iso = GoogleSheetsClient.format_datetime(dt_print)
        record = {
            "wb_id": wb_id,
            "wb_number": wb_number,
            "dt_fact": dt_fact_iso,
            "dt_print": dt_print_iso,
            "driver_id": driver.driver_id,
            "car_plate": driver.car_plate,
            "odo_input": odo_input,
            "odo_effective": odo_effective,
            "price": price,
            "balance_after": balance_after,
            "pdf_url": "",
            "status": "error",
            "error": error,
        }
        self.sheets.append_waybill(record)

    def _build_pdf_context(
        self,
        driver: Driver,
        wb_number: str,
        dt_print: datetime,
        odo_effective: float,
    ) -> Dict[str, object]:
        return {
            "wb_number": wb_number,
            "dt_print": dt_print,
            "driver_id": driver.driver_id,
            "driver_name": driver.fio,
            "driver_phone": driver.phone,
            "car_plate": driver.car_plate,
            "car_model": driver.car_model,
            "vin": driver.vin,
            "org_name": driver.org_name,
            "med_worker": driver.med_worker,
            "mech_worker": driver.mech_worker,
            "odo_effective": odo_effective,
        }


def uuid_hex() -> str:
    from uuid import uuid4

    return uuid4().hex


__all__ = ["WaybillService"]
