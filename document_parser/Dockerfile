FROM python:3.11-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    libmagic1 \
    postgresql-client \
    tesseract-ocr \
    tesseract-ocr-rus \
    tesseract-ocr-eng \
    poppler-utils \
    libglib2.0-0 \
    libgomp1 \
    gcc \
    python3-dev \
    fonts-dejavu \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Установка рабочей директории
WORKDIR /app

# Копирование файлов зависимостей
COPY requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода
COPY . .

# Копирование конфигурации
# config.py теперь находится в core/config.py

# Создание необходимых директорий
RUN mkdir -p /app/uploads /app/temp /app/report_format /app/models

# Копирование шаблонов отчетов
COPY report_format/ОТЧЕТ_file_name.docx /app/report_format/

# Создание __init__.py файлов для пакетов
RUN touch /app/__init__.py

# Установка переменных окружения
ENV PYTHONPATH=/app
ENV TRANSFORMERS_CACHE=/app/models
ENV HF_HOME=/app/models

# Открытие порта
EXPOSE 8001

# Команда запуска
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8001"]
