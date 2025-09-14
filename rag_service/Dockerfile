FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Копирование зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование модуля utils
COPY utils /app/utils

# Копирование кода
COPY . .

# Создание директорий
RUN mkdir -p /app/models /app/data

# Установка переменных окружения для оптимизации
ENV PYTHONUNBUFFERED=1
ENV TRANSFORMERS_CACHE=/app/models
ENV HF_HOME=/app/models

# Запуск сервиса с оптимизированными настройками
CMD ["uvicorn", "ollama_main:app", "--host", "0.0.0.0", "--port", "8003", "--workers", "1"]
