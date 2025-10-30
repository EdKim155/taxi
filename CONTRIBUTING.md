# Руководство для разработчиков

Спасибо за интерес к улучшению Taxi Waybill Bot! Это руководство поможет вам внести свой вклад в проект.

## Начало работы

### Требования для разработки

- Python 3.10 или выше
- Git
- Текстовый редактор или IDE (рекомендуется VS Code или PyCharm)
- Базовые знания Python, async/await, Telegram Bot API
- Аккаунт Google Cloud для тестирования Google Sheets API

### Настройка окружения разработки

1. **Клонирование репозитория**

```bash
git clone <repository-url>
cd taxi-waybill-bot
```

2. **Создание виртуального окружения**

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows
```

3. **Установка зависимостей**

```bash
pip install -r requirements.txt
```

4. **Настройка конфигурации**

```bash
cp .env.example .env
# Заполните .env своими тестовыми данными
```

5. **Создание тестовой Google таблицы**

Следуйте инструкциям в `GOOGLE_SHEETS_TEMPLATE.md`

6. **Запуск бота**

```bash
python main.py
```

## Структура проекта

```
taxi-waybill-bot/
├── bot/
│   ├── handlers/          # Обработчики Telegram команд
│   │   ├── auth_handler.py    # Авторизация
│   │   └── main_handler.py    # Основная логика
│   ├── services/          # Бизнес-логика
│   │   ├── sheets_service.py      # Google Sheets API
│   │   ├── pdf_service.py         # Генерация PDF
│   │   ├── transaction_service.py # Работа с балансами
│   │   └── waybill_service.py     # Логика путевых листов
│   ├── templates/         # Шаблоны для генерации
│   │   └── waybill.html       # Шаблон путевого листа
│   └── static/            # Статические файлы
│       ├── css/
│       └── fonts/
├── generated_waybills/    # Сгенерированные PDF
├── config.py              # Конфигурация
├── main.py                # Точка входа
└── requirements.txt       # Зависимости
```

## Стиль кода

### Python

Проект следует [PEP 8](https://peps.python.org/pep-0008/) стандарту.

**Основные правила:**

- Отступы: 4 пробела (не табы)
- Максимальная длина строки: 100 символов
- Использование type hints для функций
- Docstrings для классов и публичных методов
- Использование async/await для I/O операций

**Пример:**

```python
async def process_waybill(
    driver_data: Dict[str, Any],
    odometer: float
) -> Tuple[bool, str]:
    """
    Process waybill creation for driver.
    
    Args:
        driver_data: Driver information from sheets
        odometer: Current odometer reading
    
    Returns:
        Tuple of (success, message)
    """
    # Implementation
    pass
```

### Форматирование

Рекомендуется использовать:
- **black** для автоформатирования
- **isort** для сортировки импортов
- **flake8** для проверки стиля

```bash
pip install black isort flake8
black bot/ main.py config.py
isort bot/ main.py config.py
flake8 bot/ main.py config.py
```

## Внесение изменений

### Рабочий процесс Git

1. **Создайте новую ветку**

```bash
git checkout -b feature/your-feature-name
# или
git checkout -b fix/bug-description
```

2. **Внесите изменения**

Пишите код, следуя стилю проекта

3. **Коммит изменений**

```bash
git add .
git commit -m "Краткое описание изменений"
```

**Формат commit message:**

```
<type>: <subject>

<body>

<footer>
```

**Типы:**
- `feat`: новая функциональность
- `fix`: исправление бага
- `docs`: изменения в документации
- `style`: форматирование, отступы
- `refactor`: рефакторинг кода
- `test`: добавление тестов
- `chore`: обновление зависимостей, конфигурации

**Пример:**

```
feat: добавить уведомления администратору о низком балансе

Реализована функция отправки уведомлений администратору,
когда баланс водителя опускается ниже установленного порога.

Closes #123
```

4. **Push в репозиторий**

```bash
git push origin feature/your-feature-name
```

5. **Создайте Pull Request**

Опишите изменения, укажите связанные задачи

## Добавление новых функций

### Пример: Добавление новой команды бота

1. **Создайте обработчик в `bot/handlers/`**

```python
# bot/handlers/stats_handler.py

from telegram import Update
from telegram.ext import ContextTypes

class StatsHandler:
    async def show_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show driver statistics."""
        # Implementation
        pass
```

2. **Зарегистрируйте обработчик в `main.py`**

```python
from bot.handlers.stats_handler import StatsHandler

stats_handler = StatsHandler()

application.add_handler(
    MessageHandler(filters.Regex('^📊 Статистика$'), stats_handler.show_stats)
)
```

3. **Добавьте кнопку в клавиатуру**

```python
keyboard = [
    ["💰 Мой баланс", "📋 Получить путевой лист"],
    ["📊 Статистика", "❓ Помощь"]
]
```

### Пример: Добавление поля в путевой лист

1. **Обновите структуру Google Sheets**

Добавьте колонку в лист `drivers`, например `driver_license`

2. **Обновите PDF шаблон**

```html
<!-- bot/templates/waybill.html -->
<div class="info-row">
    <div class="info-label">Водительское удостоверение:</div>
    <div class="info-value">{{ driver_license }}</div>
</div>
```

3. **Передайте данные в шаблон**

```python
# bot/services/pdf_service.py

context = {
    # ... existing fields
    'driver_license': driver_data.get('driver_license', 'N/A'),
}
```

## Тестирование

### Ручное тестирование

1. Запустите бота локально
2. Проверьте новую функциональность через Telegram
3. Проверьте логи на ошибки

### Автоматическое тестирование (TODO)

В будущем планируется добавить:
- Unit тесты (pytest)
- Integration тесты
- CI/CD pipeline

## Документация

При добавлении новых функций обязательно обновите:

- **README.md** - если изменилась установка или использование
- **DEPLOYMENT.md** - если изменились требования к развертыванию
- **FAQ.md** - если нужно добавить новые вопросы
- **CHANGELOG.md** - опишите изменения
- **Docstrings** - в коде

## Отладка

### Логирование

Используйте стандартный модуль logging:

```python
import logging

logger = logging.getLogger(__name__)

logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
```

### Уровни логирования

Установите в `.env`:

```
LOG_LEVEL=DEBUG  # для разработки
LOG_LEVEL=INFO   # для production
```

### Просмотр логов

```bash
# Файловые логи
tail -f bot.log

# Systemd
sudo journalctl -u taxi-waybill-bot -f

# Docker
docker-compose logs -f
```

## Работа с Google Sheets

### Тестирование без реальных данных

Создайте отдельную тестовую таблицу с тестовыми водителями:

```
driver_id: TEST001
fio: Тестовый Водитель
phone: +79999999999
balance: 10000
```

### Избегайте частых обращений к API

Google Sheets API имеет лимиты:
- 100 запросов в 100 секунд на пользователя
- 500 запросов в 100 секунд на проект

**Решения:**
- Кэшируйте данные где возможно
- Используйте batch operations
- Не делайте запросы в циклах

## Оптимизация PDF

### Размер файла

- Используйте векторную графику где возможно
- Оптимизируйте изображения
- Избегайте сложных градиентов

### Скорость генерации

- Минимизируйте CSS
- Используйте простые селекторы
- Избегайте вложенных таблиц

## Безопасность

### Проверка входных данных

Всегда валидируйте данные от пользователя:

```python
def validate_odometer(value: str) -> float:
    try:
        odo = float(value)
        if odo <= 0:
            raise ValueError("Odometer must be positive")
        return odo
    except ValueError:
        raise ValueError("Invalid odometer value")
```

### Защита от SQL-инъекций

Google Sheets API защищен от инъекций, но при расширении на SQL БД:
- Используйте параметризованные запросы
- Никогда не конкатенируйте SQL строки с пользовательским вводом

### Секретные данные

- Никогда не коммитьте `.env`, `service_account.json`
- Используйте `.gitignore`
- В production используйте environment variables или secrets management

## Расширения и плагины

### Архитектура для расширений

Проект построен с учетом расширяемости:

```python
# bot/services/payment_service.py

class PaymentService:
    """Base class for payment integrations."""
    
    async def process_payment(self, amount: float, driver_id: str) -> bool:
        raise NotImplementedError

class YookassaPaymentService(PaymentService):
    """YooKassa payment integration."""
    
    async def process_payment(self, amount: float, driver_id: str) -> bool:
        # Implementation
        pass
```

### Добавление нового storage backend

```python
# bot/services/storage/base.py

class StorageService:
    async def get_driver(self, driver_id: str):
        raise NotImplementedError
    
    async def save_waybill(self, waybill_data: dict):
        raise NotImplementedError

# bot/services/storage/sheets.py
class SheetsStorage(StorageService):
    # Current implementation

# bot/services/storage/postgres.py
class PostgresStorage(StorageService):
    # New implementation for PostgreSQL
```

## Полезные ресурсы

### Документация

- [python-telegram-bot](https://docs.python-telegram-bot.org/)
- [Google Sheets API](https://developers.google.com/sheets/api)
- [WeasyPrint](https://doc.courtbouillon.org/weasyprint/)
- [Jinja2](https://jinja.palletsprojects.com/)

### Инструменты

- [BotFather](https://t.me/BotFather) - создание и управление ботами
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Google Cloud Console](https://console.cloud.google.com/)

## Вопросы и поддержка

Если у вас есть вопросы:

1. Проверьте документацию
2. Поищите в существующих issues
3. Создайте новый issue с подробным описанием
4. Или свяжитесь с мейнтейнером проекта

## Лицензия

Внося изменения в проект, вы соглашаетесь с лицензией MIT.

---

**Спасибо за ваш вклад в проект!** 🙏
