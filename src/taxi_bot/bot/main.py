from __future__ import annotations

import asyncio
import logging
from typing import Optional

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart, Text
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile, Message, ReplyKeyboardRemove

from taxi_bot.config import get_settings
from taxi_bot.exceptions import (
    DriverNotFoundError,
    InactiveDriverError,
    InsufficientBalanceError,
    ValidationError,
    WaybillGenerationError,
)
from taxi_bot.services.google_sheets import DriverRow, GoogleSheetsClient
from taxi_bot.services.pdf import PdfRenderer
from taxi_bot.services.waybill_service import WaybillService
from taxi_bot.utils import normalize_phone

from .keyboards import main_menu, phone_request_keyboard
from .states import WaybillStates

logger = logging.getLogger(__name__)


def create_services() -> tuple[GoogleSheetsClient, WaybillService]:
    sheets = GoogleSheetsClient()
    pdf = PdfRenderer()
    waybill_service = WaybillService(sheets, pdf)
    return sheets, waybill_service


sheets_client, waybill_service = create_services()
settings = get_settings()

dp = Dispatcher()


async def send_welcome(message: Message, driver_row: DriverRow) -> None:
    driver = driver_row.driver
    greeting = (
        f"Здравствуйте, {driver.fio}!\n"
        f"Ваш текущий баланс: {driver.balance:.2f} ₽.\n"
        "Выберите действие из меню ниже."
    )
    await message.answer(greeting, reply_markup=main_menu())


def get_driver_by_tg_user(tg_user_id: int) -> DriverRow | None:
    try:
        return sheets_client.get_driver_by_tg_user_id(tg_user_id)
    except DriverNotFoundError:
        return None


@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    driver_row = get_driver_by_tg_user(message.from_user.id)
    if driver_row:
        await send_welcome(message, driver_row)
    else:
        await message.answer(
            "Пожалуйста, подтвердите номер телефона для доступа к боту.",
            reply_markup=phone_request_keyboard(),
        )


@dp.message(F.contact)
async def handle_contact(message: Message, state: FSMContext) -> None:
    contact = message.contact
    if contact is None or contact.user_id != message.from_user.id:
        await message.answer("Поделитесь, пожалуйста, своим номером телефона через кнопку.")
        return

    normalized = normalize_phone(contact.phone_number)
    try:
        driver_row = sheets_client.get_driver_by_phone(normalized)
    except DriverNotFoundError:
        await message.answer(
            "Ваш номер телефона не найден в справочнике. Обратитесь к администратору.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    sheets_client.update_driver(
        driver_row.row_index,
        {
            "tg_user_id": message.from_user.id,
        },
    )

    await state.clear()
    await send_welcome(message, driver_row)


async def ensure_authorized(message: Message) -> Optional[DriverRow]:
    driver_row = get_driver_by_tg_user(message.from_user.id)
    if driver_row:
        return driver_row
    await message.answer(
        "Вы не авторизованы. Нажмите /start и поделитесь номером телефона.",
        reply_markup=phone_request_keyboard(),
    )
    return None


@dp.message(Text("Помощь"))
@dp.message(Command("help"))
async def help_handler(message: Message) -> None:
    await message.answer(
        "По всем вопросам обращайтесь к администратору Михаилу: +7 999 123‑45‑67",
        reply_markup=main_menu(),
    )


@dp.message(Text("Мой баланс"))
async def balance_handler(message: Message) -> None:
    driver_row = await ensure_authorized(message)
    if not driver_row:
        return

    driver = driver_row.driver
    transactions = sheets_client.list_recent_transactions(driver.driver_id, limit=3)
    history_lines = [
        f"{tx.get('dt')} — {tx.get('type')} {tx.get('amount')} ₽ (остаток {tx.get('balance_after')} ₽)"
        for tx in transactions
    ]
    history_text = "\n".join(history_lines) if history_lines else "Нет операций."
    text = (
        f"Баланс: {driver.balance:.2f} ₽\n\n"
        f"Последние операции:\n{history_text}"
    )
    await message.answer(text, reply_markup=main_menu())


@dp.message(Text("Получить путевой лист"))
async def waybill_request(message: Message, state: FSMContext) -> None:
    driver_row = await ensure_authorized(message)
    if not driver_row:
        return

    driver = driver_row.driver
    price = driver.effective_price or settings.pl_price_default
    if driver.balance < price:
        await message.answer(
            (
                "Недостаточно средств для выпуска ПЛ. Стоимость — "
                f"{price:.2f} ₽. Пополните баланс у администратора."
            ),
            reply_markup=main_menu(),
        )
        return

    await message.answer(
        "Введите текущий пробег автомобиля (км).",
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.set_state(WaybillStates.waiting_for_odometer)


@dp.message(WaybillStates.waiting_for_odometer)
async def waybill_process(message: Message, state: FSMContext) -> None:
    driver_row = await ensure_authorized(message)
    if not driver_row:
        await state.clear()
        return

    text = (message.text or "").replace(",", ".")
    try:
        odo_value = float(text)
    except ValueError:
        await message.answer("Не удалось распознать число. Введите пробег ещё раз.")
        return

    try:
        waybill = waybill_service.issue_waybill(driver_row, odo_value)
    except ValidationError as exc:
        await message.answer(str(exc))
        return
    except InsufficientBalanceError as exc:
        await message.answer(str(exc), reply_markup=main_menu())
        await state.clear()
        return
    except InactiveDriverError as exc:
        await message.answer(str(exc), reply_markup=main_menu())
        await state.clear()
        return
    except WaybillGenerationError as exc:
        await message.answer(str(exc), reply_markup=main_menu())
        await state.clear()
        return

    try:
        document = FSInputFile(path=str(waybill.pdf_path))
        caption = (
            f"Путевой лист № {waybill.wb_number} сформирован.\n"
            f"Дата/время: {waybill.dt_fact.strftime('%d.%m.%Y %H:%M')}\n"
            f"Списано: {waybill.price:.2f} ₽\n"
            f"Остаток: {waybill.balance_after:.2f} ₽"
        )
        await message.answer_document(document=document, caption=caption, reply_markup=main_menu())
    except TelegramBadRequest:
        await message.answer(
            (
                "Путевой лист сформирован, но файл не удалось отправить. "
                "Ссылка на PDF: "
                f"{waybill.pdf_url}"
            ),
            reply_markup=main_menu(),
        )

    await state.clear()


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=settings.telegram_bot_token, parse_mode=ParseMode.HTML)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped")
