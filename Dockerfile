# Многоэтапная сборка для AI-NK проекта
FROM node:18-alpine AS frontend-builder

# Устанавливаем зависимости для сборки
RUN apk add --no-cache python3 make g++

# Копируем frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install --omit=dev

# Копируем исходный код frontend
COPY frontend/src ./src
COPY frontend/public ./public

# Собираем frontend
RUN npm run build

# Этап для Python сервисов
FROM python:3.11-slim AS python-builder

# Устанавливаем системные зависимости
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

# Копируем requirements для всех сервисов
WORKDIR /app
COPY document_parser/requirements.txt ./document_parser/
COPY rag_service/requirements.txt ./rag_service/
COPY rule_engine/requirements.txt ./rule_engine/
COPY gateway/requirements.txt ./gateway/

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r document_parser/requirements.txt && \
    pip install --no-cache-dir -r rag_service/requirements.txt && \
    pip install --no-cache-dir -r rule_engine/requirements.txt && \
    pip install --no-cache-dir -r gateway/requirements.txt

# Финальный этап
FROM python:3.11-slim AS ai-nk

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    libmagic1 \
    postgresql-client \
    tesseract-ocr \
    tesseract-ocr-rus \
    tesseract-ocr-eng \
    poppler-utils \
    libglib2.0-0 \
    libgomp1 \
    nginx \
    curl \
    fonts-dejavu \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Создаем пользователя для безопасности
RUN useradd -m -u 1000 ai-nk && \
    mkdir -p /app /var/log/ai-nk /var/run/ai-nk && \
    chown -R ai-nk:ai-nk /app /var/log/ai-nk /var/run/ai-nk

# Копируем Python зависимости из builder
COPY --from=python-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=python-builder /usr/local/bin /usr/local/bin

# Копируем собранный frontend
COPY --from=frontend-builder /app/frontend/build /app/frontend/build

# Копируем исходный код сервисов
WORKDIR /app
COPY document_parser/ ./document_parser/
COPY rag_service/ ./rag_service/
COPY rule_engine/ ./rule_engine/
COPY gateway/ ./gateway/
COPY config.py ./

# Копируем конфигурационные файлы
COPY nginx.conf /etc/nginx/nginx.conf
COPY docker-compose.yaml ./
COPY sql/ ./sql/
COPY report_format/ ./report_format/

# Создаем необходимые директории
RUN mkdir -p /app/uploads /app/temp /app/logs /app/data && \
    chown -R ai-nk:ai-nk /app

# Копируем скрипты запуска
COPY scripts/start.sh /app/start.sh
COPY scripts/init.sh /app/init.sh
RUN chmod +x /app/start.sh /app/init.sh

# Устанавливаем переменные окружения
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Переключаемся на пользователя ai-nk
USER ai-nk

# Открываем порты
EXPOSE 80 443 8001 8002 8003 8004 8005 5432 6379 6333 9090 3000

# Точка входа
ENTRYPOINT ["/app/start.sh"]
