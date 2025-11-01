from __future__ import annotations

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def main_menu() -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="Получить путевой лист")],
        [KeyboardButton(text="Мой баланс")],
        [KeyboardButton(text="Помощь")],
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def phone_request_keyboard() -> ReplyKeyboardMarkup:
    buttons = [[KeyboardButton(text="Поделиться номером", request_contact=True)]]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, one_time_keyboard=True)


__all__ = ["main_menu", "phone_request_keyboard"]
