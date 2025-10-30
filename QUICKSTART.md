# Быстрый старт

Минимальная инструкция для запуска Taxi Waybill Bot за 15 минут.

## Шаг 1: Создать Telegram бота (2 мин)

1. Откройте [@BotFather](https://t.me/BotFather)
2. Отправьте `/newbot`
3. Следуйте инструкциям
4. Сохраните токен

## Шаг 2: Настроить Google Sheets (5 мин)

### 2.1 Создать проект и Service Account

1. Перейдите на [console.cloud.google.com](https://console.cloud.google.com)
2. Создайте новый проект
3. Включите **Google Sheets API** и **Google Drive API**
4. Создайте Service Account:
   - APIs & Services → Credentials → Create Credentials → Service Account
   - Скачайте JSON ключ
   - Переименуйте в `service_account.json`

### 2.2 Создать таблицу

1. Откройте [sheets.google.com](https://sheets.google.com)
2. Создайте новую таблицу
3. Создайте 4 листа: `drivers`, `waybills`, `transactions`, `settings`
4. Скопируйте ID таблицы из URL
5. Расшарьте таблицу на email из `service_account.json` (права: Редактор)

### 2.3 Заполнить структуру

**Лист `drivers`:** (первая строка - заголовки)
```
driver_id | fio | phone | tg_user_id | car_id | car_plate | car_model | vin | org_name | med_worker | mech_worker | last_odo | odo_delta | balance | pl_price | tz | is_active
```

**Лист `waybills`:**
```
wb_id | wb_number | dt_fact | dt_print | driver_id | car_plate | odo_input | odo_effective | price | balance_after | pdf_url | status | error
```

**Лист `transactions`:**
```
tx_id | dt | driver_id | type | amount | reason | balance_after
```

**Лист `settings`:** (добавьте эти строки после заголовков)
```
parameter          | value
pl_price_default   | 20
tz_default         | Europe/Moscow
time_shift_minutes | 60
apply_odo_delta    | true
update_last_odo_with | input
```

### 2.4 Добавить тестового водителя

В лист `drivers` добавьте строку:
```
DRV001 | Иванов Иван | +79991234567 |  | CAR001 | А123БВ777 | Toyota Camry |  | ИП Тестов | Петрова А. | Сидоров П. | 100000 | 0 | 1000 | 20 | Europe/Moscow | TRUE
```

## Шаг 3: Установить бот (5 мин)

### Вариант A: Локально (для теста)

```bash
# Клонировать или скачать проект
cd taxi-waybill-bot

# Создать виртуальное окружение
python3 -m venv venv
source venv/bin/activate

# Установить зависимости
pip install -r requirements.txt

# Настроить конфигурацию
cp .env.example .env
nano .env  # Заполните TELEGRAM_BOT_TOKEN и GOOGLE_SHEET_ID

# Скопировать service_account.json в корень проекта

# Запустить
python main.py
```

### Вариант B: На сервере (production)

```bash
# На сервере Ubuntu/Debian
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git

# Установить системные зависимости для WeasyPrint
sudo apt install -y libpango-1.0-0 libcairo2 libgdk-pixbuf2.0-0

# Создать пользователя
sudo useradd -r -m -d /opt/taxi-waybill-bot -s /bin/bash taxi

# Клонировать проект
sudo -u taxi git clone <url> /opt/taxi-waybill-bot
cd /opt/taxi-waybill-bot

# Создать venv и установить зависимости
sudo -u taxi python3 -m venv venv
sudo -u taxi venv/bin/pip install -r requirements.txt

# Настроить конфигурацию
sudo -u taxi cp .env.example .env
sudo -u taxi nano .env

# Загрузить service_account.json
sudo cp /path/to/service_account.json /opt/taxi-waybill-bot/
sudo chown taxi:taxi /opt/taxi-waybill-bot/service_account.json

# Установить systemd service
sudo cp taxi-waybill-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable taxi-waybill-bot
sudo systemctl start taxi-waybill-bot

# Проверить статус
sudo systemctl status taxi-waybill-bot
```

## Шаг 4: Проверить работу (3 мин)

1. Откройте бота в Telegram
2. Отправьте `/start`
3. Нажмите "Поделиться номером" (используйте +79991234567 или свой, если добавили в таблицу)
4. Проверьте авторизацию
5. Нажмите "💰 Мой баланс" - должно показать 1000 ₽
6. Нажмите "📋 Получить путевой лист"
7. Введите пробег: `100500`
8. Получите PDF файл!

## Готово! 🎉

Бот работает. Теперь вы можете:

- Добавлять водителей в Google таблицу
- Настраивать параметры в листе `settings`
- Изменять шаблон ПЛ в `bot/templates/waybill.html`
- Пополнять балансы водителей

## Частые проблемы

### Бот не отвечает
```bash
# Проверить логи
tail -f bot.log
# или
sudo journalctl -u taxi-waybill-bot -f
```

### Ошибка подключения к Google Sheets
- Убедитесь, что таблица расшарена на email из service_account.json
- Проверьте, что включены Google Sheets API и Drive API
- Проверьте правильность GOOGLE_SHEET_ID в .env

### Ошибка генерации PDF
```bash
# Установить системные библиотеки
sudo apt install -y libpango-1.0-0 libcairo2 libgdk-pixbuf2.0-0
```

### Номер телефона не принимается
- Проверьте формат в таблице: +79991234567 (с +7)
- Убедитесь, что is_active = TRUE

## Полная документация

- **README.md** - детальная инструкция
- **DEPLOYMENT.md** - развертывание на production
- **FAQ.md** - часто задаваемые вопросы
- **GOOGLE_SHEETS_TEMPLATE.md** - структура таблицы

## Поддержка

Если что-то не работает:
1. Проверьте раздел "Частые проблемы" выше
2. Изучите логи
3. Прочитайте FAQ.md
4. Обратитесь к администратору
