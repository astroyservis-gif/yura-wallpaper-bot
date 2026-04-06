FROM python:3.11-slim

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем все файлы из текущей директории в рабочую директорию контейнера
COPY . /app

# Устанавливаем необходимые зависимости
RUN pip install --no-cache-dir aiogram python-dotenv requests

# Команда для запуска бота
CMD ["python", "bot.py"]
