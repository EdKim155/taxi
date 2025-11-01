from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML

from taxi_bot.config import get_settings

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "templates"
WAYBILL_TEMPLATE = "waybill.html"


def _format_datetime(dt: datetime, fmt: str = "%d.%m.%Y %H:%M") -> str:
    return dt.strftime(fmt)


def _format_currency(value: float) -> str:
    return f"{value:,.2f}".replace(",", " ")


class PdfRenderer:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.env = Environment(
            loader=FileSystemLoader(str(TEMPLATES_DIR)),
            autoescape=select_autoescape(["html", "xml"]),
        )
        self.env.filters["datetime"] = _format_datetime
        self.env.filters["currency"] = _format_currency

    def render_waybill(self, context: Dict[str, Any]) -> Path:
        template = self.env.get_template(WAYBILL_TEMPLATE)
        html = template.render(**context)
        file_name = f"{context['wb_number'].replace('/', '-')}-{context['driver_id']}.pdf"
        target_path = self.settings.pdf_storage_dir / file_name
        HTML(string=html).write_pdf(target=str(target_path))
        logger.info("Generated PDF waybill at %s", target_path)
        return target_path

    def build_public_url(self, file_path: Path) -> str:
        if self.settings.public_base_url:
            relative_name = file_path.name
            return f"{self.settings.public_base_url.rstrip('/')}/{relative_name}"
        return str(file_path.resolve())


__all__ = ["PdfRenderer"]
