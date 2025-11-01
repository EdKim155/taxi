class TaxiBotError(Exception):
    """Base error for the Taxi bot application."""


class DriverNotFoundError(TaxiBotError):
    """Raised when a driver cannot be located in Google Sheets."""


class InsufficientBalanceError(TaxiBotError):
    """Raised when a driver has insufficient funds for a waybill."""


class InactiveDriverError(TaxiBotError):
    """Raised when a driver is marked as inactive."""


class ValidationError(TaxiBotError):
    """Raised when user-provided data fails validation."""


class WaybillGenerationError(TaxiBotError):
    """Raised when generating a waybill fails."""


__all__ = [
    "TaxiBotError",
    "DriverNotFoundError",
    "InsufficientBalanceError",
    "InactiveDriverError",
    "ValidationError",
    "WaybillGenerationError",
]
