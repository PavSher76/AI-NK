FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    default-jre-headless \
    wget \
    unzip \
    curl \
    libhunspell-dev \
    hunspell \
    hunspell-ru \
    hunspell-en-us \
    && rm -rf /var/lib/apt/lists/*

# Установка LanguageTool
RUN wget -O /tmp/languagetool.zip https://languagetool.org/download/LanguageTool-6.1.zip && \
    cd /tmp && \
    unzip languagetool.zip && \
    mv LanguageTool-6.1 /opt/languagetool && \
    rm /tmp/languagetool.zip && \
    chmod +x /opt/languagetool/languagetool-commandline.jar

# Копирование файлов
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Создание директорий
RUN mkdir -p /app/logs /app/cache

# Настройка переменных окружения для LanguageTool
ENV LANGUAGETOOL_HOME=/opt/languagetool

# Открытие порта
EXPOSE 8007

# Создание скрипта запуска
RUN echo '#!/bin/bash\n\
# Запуск LanguageTool в фоновом режиме\n\
java -cp /opt/languagetool/languagetool-server.jar org.languagetool.server.HTTPServer --port 8081 --public &\n\
# Ждем запуска LanguageTool\n\
sleep 10\n\
# Запуск основного сервиса\n\
uvicorn main:app --host 0.0.0.0 --port 8007' > /app/start.sh && chmod +x /app/start.sh

# Запуск сервиса
CMD ["/app/start.sh"]
