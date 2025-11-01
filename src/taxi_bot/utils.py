from __future__ import annotations

import re


PHONE_CLEAN_RE = re.compile(r"[^+\d]")


def normalize_phone(phone: str) -> str:
    digits = PHONE_CLEAN_RE.sub("", phone or "")
    if digits.startswith("8") and len(digits) == 11:
        digits = "+7" + digits[1:]
    if not digits.startswith("+") and len(digits) == 11:
        digits = "+" + digits
    return digits


__all__ = ["normalize_phone"]
