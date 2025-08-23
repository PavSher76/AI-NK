#!/bin/bash

set -e

echo "🗄️ Инициализация базы данных AI-NK..."

# Функция для логирования
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Проверяем, была ли уже инициализация
if [ -f "/app/data/.initialized" ]; then
    log "✅ База данных уже инициализирована"
    exit 0
fi

# Создаем директории для данных
log "📁 Создание директорий для данных..."
mkdir -p /app/data/postgres /app/data/redis /app/data/qdrant /app/logs

# Инициализация PostgreSQL
log "🐘 Инициализация PostgreSQL..."
initdb -D /app/data/postgres -U postgres --pwprompt <<< "ai-nk-password
ai-nk-password"

# Запуск PostgreSQL для инициализации
log "🚀 Запуск PostgreSQL для инициализации..."
pg_ctl -D /app/data/postgres -l /app/logs/postgres-init.log start

# Ожидание готовности PostgreSQL
log "⏳ Ожидание готовности PostgreSQL..."
for i in {1..30}; do
    if pg_isready -h localhost -p 5432 -U postgres > /dev/null 2>&1; then
        log "✅ PostgreSQL готов"
        break
    fi
    log "⏳ Попытка $i/30..."
    sleep 2
done

# Создание базы данных и пользователей
log "👤 Создание пользователей и баз данных..."
psql -h localhost -U postgres -c "CREATE USER norms_user WITH PASSWORD 'norms_password';"
psql -h localhost -U postgres -c "CREATE DATABASE norms_db OWNER norms_user;"
psql -h localhost -U postgres -c "CREATE DATABASE checkable_db OWNER norms_user;"
psql -h localhost -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE norms_db TO norms_user;"
psql -h localhost -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE checkable_db TO norms_user;"

# Подключение к базе norms_db и создание расширений
log "🔧 Настройка расширений PostgreSQL..."
psql -h localhost -U postgres -d norms_db -c "CREATE EXTENSION IF NOT EXISTS vector;"
psql -h localhost -U postgres -U postgres -d checkable_db -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Выполнение SQL скриптов
log "📜 Выполнение SQL скриптов..."

# Создание таблиц для нормативных документов
psql -h localhost -U postgres -d norms_db -f /app/sql/create_tables.sql

# Создание таблиц для проверяемых документов
psql -h localhost -U postgres -d checkable_db -f /app/sql/create_checkable_tables.sql

# Настройка логирования
log "📝 Настройка логирования PostgreSQL..."
psql -h localhost -U postgres -d norms_db -f /app/sql/configure_logging.sql

# Инициализация настроек
log "⚙️ Инициализация системных настроек..."
psql -h localhost -U postgres -d norms_db -f /app/sql/init_settings.sql

# Остановка PostgreSQL
log "🛑 Остановка PostgreSQL..."
pg_ctl -D /app/data/postgres stop

# Создание маркера инициализации
log "✅ Создание маркера инициализации..."
echo "$(date)" > /app/data/.initialized

log "🎉 Инициализация базы данных завершена успешно!"
