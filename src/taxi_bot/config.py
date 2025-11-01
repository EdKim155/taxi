from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import BaseSettings, Field, validator


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    telegram_bot_token: str = Field(..., env="TELEGRAM_BOT_TOKEN")
    google_service_account_json: Path = Field(..., env="GOOGLE_SERVICE_ACCOUNT_JSON")
    google_spreadsheet_id: str = Field(..., env="GOOGLE_SPREADSHEET_ID")

    pdf_storage_dir: Path = Field(Path("storage/waybills"), env="PDF_STORAGE_DIR")
    public_base_url: str | None = Field(None, env="PUBLIC_BASE_URL")

    admin_phone_numbers: List[str] = Field(default_factory=list, env="ADMIN_PHONE_NUMBERS")

    pl_price_default: float = 20.0
    tz_default: str = "Europe/Moscow"
    time_shift_minutes: int = 60
    apply_odo_delta: bool = True
    update_last_odo_with: str = Field("input", regex="^(input|effective)$")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @validator("admin_phone_numbers", pre=True)
    def _split_admin_phones(cls, value: str | List[str]) -> List[str]:
        if isinstance(value, list):
            return value
        if not value:
            return []
        return [phone.strip() for phone in value.split(",") if phone.strip()]

    @validator("pdf_storage_dir", pre=True)
    def _expand_path(cls, value: str | Path) -> Path:
        return Path(value).expanduser().resolve()


@lru_cache()
def get_settings() -> Settings:
    settings = Settings()
    settings.pdf_storage_dir.mkdir(parents=True, exist_ok=True)
    return settings


__all__ = ["Settings", "get_settings"]
