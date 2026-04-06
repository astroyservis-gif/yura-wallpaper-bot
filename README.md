# Time Hour Bot

Telegram-бот для учета рабочего времени и заработка.

Бот:
- фиксирует время начала и окончания работы;
- запрашивает сумму за выход и тип обоев;
- считает стоимость часа;
- отправляет запись в Google Apps Script (например, в Google Sheets).

## Возможности

- Команда `/start` и кнопки `🚀 Старт` / `🏁 Финиш`
- Хранение активной сессии в SQLite (`work_log.db`)
- Проверка корректности введенной суммы
- Отправка данных в Google Script в формате JSON
- Поддержка запуска локально и через Docker

## Стек

- Python 3.11+
- aiogram
- python-dotenv
- requests
- SQLite

## Быстрый старт (локально)

1. Установите зависимости:

```bash
pip install aiogram python-dotenv requests
```

2. Создайте файл `.env` в корне проекта:

```env
API_TOKEN=your_telegram_bot_token
GOOGLE_SCRIPT_URL=https://script.google.com/macros/s/XXXXXXXX/exec
```

3. Запустите бота:

```bash
python bot.py
```

## Запуск через Docker

1. Убедитесь, что рядом есть файл `.env`.
2. Выполните:

```bash
docker compose up -d --build
```

3. Логи:

```bash
docker compose logs -f
```

4. Остановка:

```bash
docker compose down
```

## Как пользоваться ботом

1. Отправьте `/start`
2. Нажмите `🚀 Старт` в начале работы
3. Нажмите `🏁 Финиш` в конце работы
4. Введите сумму (например, `1500`, `1500.5` или `1 500`)
5. Выберите тип обоев (`Флизелин` или `Бумага`)
6. Бот отправит данные в Google Script и покажет расчет стоимости часа

## Формат отправляемых данных

Бот отправляет POST-запрос (JSON) на `GOOGLE_SCRIPT_URL`:

```json
{
  "date": "YYYY-MM-DD",
  "start": "HH:MM",
  "finish": "HH:MM",
  "hours": 6.5,
  "money": 1500.0,
  "hourly": 231.0,
  "type": "флизелин"
}
```

## Структура проекта

- `bot.py` — основная логика бота
- `work_log.db` — база SQLite с активными сессиями
- `Dockerfile` — контейнеризация приложения
- `docker-compose.yml` — запуск контейнера через Compose

## Возможные ошибки

- `API_TOKEN не задан в .env` — отсутствует токен бота
- `GOOGLE_SCRIPT_URL не задан в .env` — отсутствует URL скрипта
- `❌ Ошибка при записи в таблицу.` — Google Script вернул не `200`
- `❌ Ошибка связи: ...` — проблема сети или недоступен endpoint
