from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class WaybillStates(StatesGroup):
    waiting_for_odometer = State()


__all__ = ["WaybillStates"]
