# Руководство по развертыванию

Подробная инструкция по развертыванию Taxi Waybill Bot на production сервере.

## Требования к серверу

### Минимальные требования:
- **OS**: Ubuntu 20.04 LTS или выше / Debian 11+
- **RAM**: 512 MB (рекомендуется 1 GB)
- **CPU**: 1 core (рекомендуется 2 cores)
- **Disk**: 5 GB свободного места
- **Network**: стабильное интернет-соединение

### Программное обеспечение:
- Python 3.10 или выше
- pip
- git
- systemd (для сервиса) или Docker

## Вариант 1: Развертывание через systemd

### Шаг 1: Подготовка сервера

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка необходимых пакетов
sudo apt install -y python3 python3-pip python3-venv git

# Установка системных зависимостей для WeasyPrint
sudo apt install -y \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    libcairo2 \
    libpangoft2-1.0-0
```

### Шаг 2: Создание пользователя

```bash
# Создание системного пользователя для бота
sudo useradd -r -m -d /opt/taxi-waybill-bot -s /bin/bash taxi

# Переключение на пользователя
sudo -u taxi -i
```

### Шаг 3: Клонирование репозитория

```bash
cd /opt/taxi-waybill-bot
git clone <repository-url> .

# Или загрузка архива
# scp taxi-bot.tar.gz user@server:/tmp/
# sudo -u taxi tar -xzf /tmp/taxi-bot.tar.gz -C /opt/taxi-waybill-bot
```

### Шаг 4: Создание виртуального окружения

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Шаг 5: Настройка конфигурации

```bash
# Копирование примера .env
cp .env.example .env

# Редактирование .env
nano .env
```

Заполните все необходимые параметры:
- `TELEGRAM_BOT_TOKEN` - токен от BotFather
- `GOOGLE_SHEET_ID` - ID Google таблицы
- и другие параметры

### Шаг 6: Загрузка service account ключа

```bash
# Загрузите файл service_account.json на сервер
scp service_account.json user@server:/tmp/
sudo mv /tmp/service_account.json /opt/taxi-waybill-bot/
sudo chown taxi:taxi /opt/taxi-waybill-bot/service_account.json
sudo chmod 600 /opt/taxi-waybill-bot/service_account.json
```

### Шаг 7: Создание директорий для логов

```bash
sudo mkdir -p /var/log/taxi-waybill-bot
sudo chown taxi:taxi /var/log/taxi-waybill-bot
```

### Шаг 8: Тестовый запуск

```bash
# От имени пользователя taxi
sudo -u taxi -i
cd /opt/taxi-waybill-bot
source venv/bin/activate
python main.py
```

Если бот запустился без ошибок, нажмите Ctrl+C для остановки.

### Шаг 9: Установка systemd сервиса

```bash
# Копирование unit файла
sudo cp taxi-waybill-bot.service /etc/systemd/system/

# Перечитывание конфигурации systemd
sudo systemctl daemon-reload

# Включение автозапуска
sudo systemctl enable taxi-waybill-bot

# Запуск сервиса
sudo systemctl start taxi-waybill-bot

# Проверка статуса
sudo systemctl status taxi-waybill-bot
```

### Шаг 10: Проверка логов

```bash
# Просмотр логов systemd
sudo journalctl -u taxi-waybill-bot -f

# Просмотр логов приложения
sudo tail -f /var/log/taxi-waybill-bot/output.log
sudo tail -f /var/log/taxi-waybill-bot/error.log
```

## Вариант 2: Развертывание через Docker

### Шаг 1: Установка Docker

```bash
# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Установка Docker Compose
sudo apt install -y docker-compose

# Добавление текущего пользователя в группу docker
sudo usermod -aG docker $USER
newgrp docker
```

### Шаг 2: Подготовка проекта

```bash
# Клонирование репозитория
git clone <repository-url> taxi-waybill-bot
cd taxi-waybill-bot

# Копирование .env
cp .env.example .env
nano .env

# Загрузка service_account.json
# Поместите файл в корень проекта
```

### Шаг 3: Сборка и запуск

```bash
# Сборка образа
docker-compose build

# Запуск контейнера
docker-compose up -d

# Просмотр логов
docker-compose logs -f
```

### Шаг 4: Управление контейнером

```bash
# Остановка
docker-compose stop

# Запуск
docker-compose start

# Перезапуск
docker-compose restart

# Остановка и удаление
docker-compose down

# Пересборка и запуск
docker-compose up -d --build
```

### Шаг 5: Просмотр логов Docker

```bash
# Все логи
docker-compose logs

# Последние 100 строк с follow
docker-compose logs --tail=100 -f

# Логи конкретного сервиса
docker logs taxi-waybill-bot
```

## Обновление бота

### Для systemd:

```bash
# Остановка сервиса
sudo systemctl stop taxi-waybill-bot

# Переключение на пользователя taxi
sudo -u taxi -i
cd /opt/taxi-waybill-bot

# Обновление кода
git pull origin main
# или загрузка новой версии

# Активация виртуального окружения
source venv/bin/activate

# Обновление зависимостей (если изменились)
pip install -r requirements.txt

# Выход из пользователя taxi
exit

# Запуск сервиса
sudo systemctl start taxi-waybill-bot

# Проверка статуса
sudo systemctl status taxi-waybill-bot
```

### Для Docker:

```bash
cd /path/to/taxi-waybill-bot

# Остановка контейнера
docker-compose down

# Обновление кода
git pull origin main

# Пересборка и запуск
docker-compose up -d --build
```

## Настройка firewall

```bash
# UFW (Ubuntu)
sudo ufw allow 22/tcp
sudo ufw enable
sudo ufw status

# Примечание: бот не требует открытых портов,
# так как использует исходящие соединения к Telegram API
```

## Резервное копирование

### Автоматическое резервное копирование Google Sheets

Создайте скрипт `/opt/taxi-waybill-bot/backup.sh`:

```bash
#!/bin/bash

BACKUP_DIR="/opt/taxi-waybill-bot/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

# Экспорт через API (требует настройки)
# или ручное копирование таблицы через Google Takeout

# Очистка старых бэкапов (старше 30 дней)
find "$BACKUP_DIR" -name "*.csv" -mtime +30 -delete

echo "Backup completed: $DATE"
```

Добавьте в crontab:

```bash
sudo crontab -e

# Ежедневное резервное копирование в 3:00
0 3 * * * /opt/taxi-waybill-bot/backup.sh
```

### Резервное копирование сгенерированных PDF

```bash
#!/bin/bash

BACKUP_DIR="/backup/waybills"
SOURCE_DIR="/opt/taxi-waybill-bot/generated_waybills"
DATE=$(date +%Y%m%d)

mkdir -p "$BACKUP_DIR"

# Копирование файлов
rsync -av "$SOURCE_DIR/" "$BACKUP_DIR/$DATE/"

# Архивирование
tar -czf "$BACKUP_DIR/waybills_$DATE.tar.gz" "$BACKUP_DIR/$DATE/"
rm -rf "$BACKUP_DIR/$DATE"

# Очистка старых архивов (старше 90 дней)
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +90 -delete
```

## Мониторинг

### Проверка работоспособности

Создайте скрипт мониторинга `/opt/taxi-waybill-bot/health_check.sh`:

```bash
#!/bin/bash

# Проверка процесса
if pgrep -f "python.*main.py" > /dev/null; then
    echo "✓ Bot process is running"
else
    echo "✗ Bot process is NOT running"
    sudo systemctl restart taxi-waybill-bot
    echo "Service restarted"
fi

# Проверка логов на ошибки
ERROR_COUNT=$(grep -c "ERROR" /var/log/taxi-waybill-bot/error.log 2>/dev/null || echo 0)
if [ "$ERROR_COUNT" -gt 0 ]; then
    echo "⚠ Found $ERROR_COUNT errors in logs"
fi

# Проверка места на диске
DISK_USAGE=$(df -h /opt/taxi-waybill-bot | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 80 ]; then
    echo "⚠ Disk usage is high: ${DISK_USAGE}%"
fi
```

Добавьте в crontab для периодической проверки:

```bash
*/5 * * * * /opt/taxi-waybill-bot/health_check.sh >> /var/log/taxi-waybill-bot/health.log 2>&1
```

### Интеграция с мониторингом

Для продвинутого мониторинга можно использовать:
- **Prometheus + Grafana** - метрики и дашборды
- **Sentry** - отслеживание ошибок
- **Uptime Robot** - проверка доступности
- **Telegram Notifications** - уведомления о критических событиях

## Безопасность

### 1. Защита конфиденциальных файлов

```bash
# Правильные права доступа
chmod 600 /opt/taxi-waybill-bot/.env
chmod 600 /opt/taxi-waybill-bot/service_account.json
chown taxi:taxi /opt/taxi-waybill-bot/.env
chown taxi:taxi /opt/taxi-waybill-bot/service_account.json
```

### 2. Ограничение SSH доступа

```bash
# Отключение root login
sudo nano /etc/ssh/sshd_config
# PermitRootLogin no

# Использование SSH ключей вместо паролей
# PasswordAuthentication no

sudo systemctl restart sshd
```

### 3. Настройка fail2ban

```bash
sudo apt install -y fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### 4. Автоматические обновления безопасности

```bash
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

## Решение проблем

### Бот не запускается

```bash
# Проверка логов
sudo journalctl -u taxi-waybill-bot -n 50 --no-pager

# Проверка конфигурации
sudo -u taxi -i
cd /opt/taxi-waybill-bot
source venv/bin/activate
python -c "import config; print('Config OK')"
```

### Ошибка подключения к Google Sheets

```bash
# Проверка service account
python -c "from bot.services.sheets_service import SheetsService; s = SheetsService(); print(s.get_settings())"
```

### Ошибка генерации PDF

```bash
# Проверка WeasyPrint
python -c "from bot.services.pdf_service import PDFService; p = PDFService(); print('PDF OK')"

# Установка недостающих системных библиотек
sudo apt install -y libpango-1.0-0 libcairo2 libpangoft2-1.0-0
```

### Высокое использование памяти

```bash
# Просмотр использования ресурсов
top
# или
htop

# Перезапуск сервиса
sudo systemctl restart taxi-waybill-bot
```

## Масштабирование

### Горизонтальное масштабирование

Если нагрузка возрастет, можно:

1. **Разделить на микросервисы**:
   - Bot handler (обработка сообщений)
   - PDF Generator (генерация документов)
   - Queue system (Redis/RabbitMQ для очередей)

2. **Использовать load balancer**:
   - Несколько инстансов бота за балансировщиком

3. **Кэширование**:
   - Redis для кэширования данных из Google Sheets
   - Уменьшение количества запросов к API

### Вертикальное масштабирование

- Увеличение RAM и CPU на сервере
- Использование SSD для быстрого доступа к файлам
- Оптимизация кода и запросов

## Чек-лист после развертывания

- [ ] Бот запущен и отвечает на команды
- [ ] Авторизация по телефону работает
- [ ] Генерация PDF путевых листов работает
- [ ] Списание средств происходит корректно
- [ ] Данные записываются в Google Sheets
- [ ] Логи пишутся и доступны для просмотра
- [ ] Systemd сервис настроен на автозапуск
- [ ] Резервное копирование настроено
- [ ] Мониторинг работает
- [ ] Документация доступна администраторам
- [ ] Контакты техподдержки указаны в боте

## Контакты поддержки

При возникновении проблем с развертыванием:

1. Проверьте документацию в README.md
2. Изучите логи приложения
3. Проверьте FAQ в README
4. Обратитесь к разработчику

---

**Успешного развертывания!** 🚀
