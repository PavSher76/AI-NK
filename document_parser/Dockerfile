FROM python:3.11-slim

WORKDIR /app

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

# Установка Python пакетов через pip
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода
COPY . .

# Копирование конфигурации проекта
COPY config.py /app/config.py

# Создание директорий
RUN mkdir -p /app/uploads /app/temp /app/report_format

# Копирование шаблона отчета
COPY report_format/ОТЧЕТ_file_name.docx /app/report_format/

EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001", "--timeout-keep-alive", "600", "--limit-max-requests", "500", "--limit-concurrency", "5", "--timeout-graceful-shutdown", "60"]
