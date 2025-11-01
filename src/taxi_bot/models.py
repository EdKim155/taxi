from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass(slots=True)
class Driver:
    driver_id: str
    fio: str
    phone: str
    car_id: str
    car_plate: str
    car_model: str
    vin: str | None
    org_name: str
    med_worker: str
    mech_worker: str
    last_odo: float
    odo_delta: float
    balance: float
    pl_price: float
    tz: str
    is_active: bool
    tg_user_id: Optional[int] = None

    @property
    def effective_price(self) -> float:
        return self.pl_price if self.pl_price > 0 else 0.0


@dataclass(slots=True)
class Waybill:
    wb_id: str
    wb_number: str
    dt_fact: datetime
    dt_print: datetime
    driver_id: str
    car_plate: str
    odo_input: float
    odo_effective: float
    price: float
    balance_after: float
    pdf_path: Path
    pdf_url: str
    status: str
    error: str | None = None


@dataclass(slots=True)
class Transaction:
    tx_id: str
    dt: datetime
    driver_id: str
    type: str
    amount: float
    reason: str
    balance_after: float


__all__ = ["Driver", "Waybill", "Transaction"]
