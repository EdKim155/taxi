# 🚖 Taxi Waybill Bot

Telegram-бот для автоматического формирования электронных путевых листов для таксопарка с системой учёта балансов и транзакций.

## 📋 Возможности

- ✅ **Авторизация по номеру телефона** - доступ только для зарегистрированных водителей
- 📄 **Генерация PDF путевых листов** - красивые путевые листы с QR-кодами
- 💰 **Учёт балансов** - автоматическое списание средств за каждый ПЛ
- 📊 **История операций** - полный журнал всех транзакций
- ⚙️ **Гибкие настройки** - коррекция одометра, часовой пояс, цена ПЛ
- 🔄 **Интеграция с Google Sheets** - все данные в удобных таблицах

## 🛠 Технологии

- **Python 3.10+**
- **python-telegram-bot** - Telegram Bot API
- **Google Sheets API** - хранение данных
- **WeasyPrint + Jinja2** - генерация PDF
- **pytz** - работа с часовыми поясами
- **qrcode** - генерация QR-кодов

## 📦 Установка

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd taxi
```

### 2. Создание виртуального окружения

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows
```

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 4. Создание Telegram бота

1. Откройте [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте команду `/newbot`
3. Следуйте инструкциям для создания бота
4. Сохраните полученный токен (например: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 5. Настройка Google Sheets API

#### 5.1. Создание проекта в Google Cloud Console

1. Перейдите в [Google Cloud Console](https://console.cloud.google.com/)
2. Создайте новый проект или выберите существующий
3. Включите **Google Sheets API**:
   - В меню слева выберите "APIs & Services" → "Library"
   - Найдите "Google Sheets API" и нажмите "Enable"
4. Включите **Google Drive API** (аналогично)

#### 5.2. Создание сервисного аккаунта

1. Перейдите в "APIs & Services" → "Credentials"
2. Нажмите "Create Credentials" → "Service Account"
3. Заполните данные:
   - Service account name: `taxi-waybill-bot`
   - Description: `Service account for taxi waybill bot`
4. Нажмите "Create and Continue"
5. Grant this service account access to project: выберите роль "Editor"
6. Нажмите "Done"

#### 5.3. Создание ключа

1. Найдите созданный сервисный аккаунт в списке
2. Нажмите на него и перейдите на вкладку "Keys"
3. Нажмите "Add Key" → "Create new key"
4. Выберите формат **JSON**
5. Файл автоматически скачается
6. Переименуйте его в `service_account.json` и поместите в корень проекта

#### 5.4. Создание Google таблицы

1. Откройте [Google Sheets](https://sheets.google.com/)
2. Создайте новую таблицу
3. Назовите её, например, "Taxi Waybills Database"
4. Скопируйте ID таблицы из URL (между `/d/` и `/edit`):
   ```
   https://docs.google.com/spreadsheets/d/ЭТОТ_ID_КОПИРУЙТЕ/edit
   ```

5. Откройте JSON-файл сервисного аккаунта и найдите email (формат: `название@проект.iam.gserviceaccount.com`)
6. Расшарьте таблицу на этот email с правами **Редактор**

#### 5.5. Создание структуры таблицы

Создайте 4 листа (вкладки) в таблице с указанными заголовками:

**Лист 1: `drivers`**
```
driver_id | fio | phone | tg_user_id | car_id | car_plate | car_model | vin | org_name | med_worker | mech_worker | last_odo | odo_delta | balance | pl_price | tz | is_active
```

**Лист 2: `waybills`**
```
wb_id | wb_number | dt_fact | dt_print | driver_id | car_plate | odo_input | odo_effective | price | balance_after | pdf_url | status | error
```

**Лист 3: `transactions`**
```
tx_id | dt | driver_id | type | amount | reason | balance_after
```

**Лист 4: `settings`**
```
parameter | value
```

Для листа `settings` добавьте следующие строки:
```
pl_price_default     | 20
tz_default           | Europe/Moscow
time_shift_minutes   | 60
apply_odo_delta      | true
update_last_odo_with | input
```

#### 5.6. Пример данных для водителя

Добавьте тестового водителя в лист `drivers`:

```
driver_id: DRV001
fio: Иванов Иван Иванович
phone: +79991234567
tg_user_id: (оставить пустым, заполнится при авторизации)
car_id: CAR001
car_plate: А123БВ777
car_model: Toyota Camry
vin: 1HGBH41JXMN109186
org_name: ИП Михайлов М.М.
med_worker: Петрова А.С.
mech_worker: Сидоров П.И.
last_odo: 100000
odo_delta: 0
balance: 1000
pl_price: 20
tz: Europe/Moscow
is_active: TRUE
```

### 6. Настройка переменных окружения

Создайте файл `.env` в корне проекта:

```bash
cp .env.example .env
```

Отредактируйте `.env`:

```env
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=ваш_токен_бота

# Google Sheets Configuration
GOOGLE_SHEET_ID=id_вашей_таблицы
GOOGLE_SERVICE_ACCOUNT_FILE=service_account.json

# Application Settings
TIMEZONE=Europe/Moscow
ADMIN_PHONE=+79991234567

# Optional: Admin notification
ADMIN_TELEGRAM_ID=123456789

# Logging
LOG_LEVEL=INFO
```

### 7. Запуск бота

```bash
python main.py
```

Бот запустится и будет готов к работе!

## 🚀 Использование

### Для водителя

1. **Авторизация**:
   - Отправьте `/start` боту
   - Нажмите кнопку "📱 Поделиться номером"
   - Если ваш номер есть в базе, вы будете авторизованы

2. **Проверка баланса**:
   - Нажмите "💰 Мой баланс"
   - Увидите текущий баланс и последние 3 операции

3. **Получение путевого листа**:
   - Нажмите "📋 Получить путевой лист"
   - Введите текущие показания одометра
   - Получите PDF-файл путевого листа

### Для администратора

#### Добавление нового водителя

1. Откройте Google таблицу
2. Перейдите на лист `drivers`
3. Добавьте новую строку с данными водителя
4. Обязательные поля:
   - `driver_id` - уникальный ID
   - `fio` - полное ФИО
   - `phone` - телефон в формате +7XXXXXXXXXX
   - `car_plate`, `car_model` - данные автомобиля
   - `balance` - начальный баланс
   - `is_active` - TRUE

#### Пополнение баланса

**Вариант 1: Прямое редактирование**
1. Найдите водителя в листе `drivers`
2. Увеличьте значение в колонке `balance`

**Вариант 2: Через транзакции**
1. Откройте лист `transactions`
2. Добавьте новую строку:
   ```
   tx_id: TX-20240101120000
   dt: 2024-01-01 12:00:00
   driver_id: DRV001
   type: topup
   amount: 500
   reason: Пополнение администратором
   balance_after: 1500
   ```
3. Обновите баланс в листе `drivers`

#### Просмотр логов

Все сформированные путевые листы записываются в лист `waybills`.

Все финансовые операции - в лист `transactions`.

## 🎨 Шаблон путевого листа

Путевой лист генерируется из HTML-шаблона с использованием CSS стилей. Шаблон находится в `bot/templates/waybill.html`.

### Особенности шаблона:

- 🎨 Современный дизайн с цветовым кодированием секций
- 📱 Адаптивная верстка для печати на A4
- 🔐 QR-код для проверки подлинности
- 📊 Информативные блоки с иконками
- ✅ Автоматические отметки медика, механика, диспетчера

### Настройка шаблона

Вы можете изменить внешний вид, отредактировав:
- HTML-структуру в `bot/templates/waybill.html`
- CSS-стили в теге `<style>` внутри шаблона

## 📁 Структура проекта

```
taxi/
├── bot/
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── auth_handler.py      # Авторизация водителей
│   │   └── main_handler.py      # Основная логика
│   ├── services/
│   │   ├── __init__.py
│   │   ├── sheets_service.py    # Работа с Google Sheets
│   │   ├── pdf_service.py       # Генерация PDF
│   │   ├── transaction_service.py # Работа с балансами
│   │   └── waybill_service.py   # Логика путевых листов
│   ├── templates/
│   │   └── waybill.html         # Шаблон PDF
│   └── static/
│       └── css/
├── generated_waybills/          # Сгенерированные PDF
├── config.py                    # Конфигурация
├── main.py                      # Точка входа
├── requirements.txt             # Зависимости
├── .env.example                 # Пример переменных окружения
├── .gitignore
└── README.md
```

## 🔧 Настройки

### Изменение цены путевого листа

**Глобально (для всех):**
В Google Sheets, лист `settings`, параметр `pl_price_default`

**Индивидуально (для конкретного водителя):**
В Google Sheets, лист `drivers`, колонка `pl_price` для нужного водителя

### Коррекция одометра

Если одометр автомобиля показывает неверные значения, можно настроить коррекцию:

В листе `drivers`, колонка `odo_delta` - значение, которое будет вычитаться из введённого пробега.

Например, если одометр "врёт" на +27 км, установите `odo_delta = 27`.

### Часовой пояс

**Глобально:**
Лист `settings`, параметр `tz_default`

**Индивидуально:**
Лист `drivers`, колонка `tz` для конкретного водителя

Поддерживаемые значения: все из библиотеки `pytz` (например: `Europe/Moscow`, `Asia/Yekaterinburg`)

### Сдвиг времени в ПЛ

По умолчанию время в путевом листе устанавливается на 1 час раньше фактического времени запроса.

Настраивается в листе `settings`, параметр `time_shift_minutes` (в минутах).

## 🐧 Развертывание на сервере

### Systemd service (рекомендуется)

1. Создайте файл `/etc/systemd/system/taxi-waybill-bot.service`:

```ini
[Unit]
Description=Taxi Waybill Telegram Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/taxi
Environment="PATH=/path/to/taxi/venv/bin"
ExecStart=/path/to/taxi/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

2. Активируйте и запустите сервис:

```bash
sudo systemctl daemon-reload
sudo systemctl enable taxi-waybill-bot
sudo systemctl start taxi-waybill-bot
```

3. Проверьте статус:

```bash
sudo systemctl status taxi-waybill-bot
```

4. Просмотр логов:

```bash
sudo journalctl -u taxi-waybill-bot -f
```

### Docker (опционально)

Создайте `Dockerfile`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for WeasyPrint
RUN apt-get update && apt-get install -y \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

Создайте `docker-compose.yml`:

```yaml
version: '3.8'

services:
  bot:
    build: .
    restart: unless-stopped
    volumes:
      - ./generated_waybills:/app/generated_waybills
      - ./bot.log:/app/bot.log
    env_file:
      - .env
```

Запуск:

```bash
docker-compose up -d
```

## 🔍 Мониторинг и отладка

### Логи

Бот записывает логи в файл `bot.log` и в stdout.

Уровень логирования настраивается в `.env` через параметр `LOG_LEVEL` (DEBUG, INFO, WARNING, ERROR).

### Проверка работы Google Sheets

```python
python -c "from bot.services.sheets_service import SheetsService; s = SheetsService(); print(s.get_settings())"
```

### Тестирование генерации PDF

```python
python -c "from bot.services.pdf_service import PDFService; p = PDFService(); print('PDF service OK')"
```

## ❓ Частые вопросы

**Q: Бот не отвечает на сообщения**
A: Проверьте, что бот запущен, токен верный, и есть интернет-соединение.

**Q: Ошибка при подключении к Google Sheets**
A: Убедитесь, что файл `service_account.json` существует, таблица расшарена на email сервисного аккаунта, и включены Google Sheets API и Drive API.

**Q: PDF генерируется с ошибками**
A: Установите системные зависимости для WeasyPrint (см. раздел "Развертывание на сервере").

**Q: Как изменить внешний вид путевого листа?**
A: Отредактируйте HTML/CSS в файле `bot/templates/waybill.html`.

**Q: Можно ли добавить фото водителя в ПЛ?**
A: Да, добавьте колонку `photo_url` в лист `drivers` и измените шаблон для отображения изображения.

## 📝 Лицензия

MIT License

## 👨‍💻 Автор

Разработано для таксопарка с ❤️

## 🤝 Поддержка

При возникновении вопросов или проблем:
1. Проверьте раздел "Частые вопросы"
2. Изучите логи (`bot.log`)
3. Проверьте настройки в `.env` и Google Sheets

---

**Важно:** Храните файл `service_account.json` и `.env` в безопасности! Не коммитьте их в публичные репозитории.
