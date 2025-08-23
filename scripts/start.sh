#!/bin/bash

set -e

echo "🚀 Запуск AI-NK системы..."

# Функция для логирования
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Функция для проверки здоровья сервиса
check_health() {
    local service=$1
    local url=$2
    local max_attempts=30
    local attempt=1
    
    log "🔍 Проверка здоровья $service..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s "$url" > /dev/null 2>&1; then
            log "✅ $service готов"
            return 0
        fi
        
        log "⏳ Попытка $attempt/$max_attempts для $service..."
        sleep 2
        ((attempt++))
    done
    
    log "❌ $service не готов после $max_attempts попыток"
    return 1
}

# Инициализация системы
log "📋 Инициализация AI-NK системы..."

# Запуск инициализации базы данных
if [ -f "/app/init.sh" ]; then
    log "🗄️ Инициализация базы данных..."
    /app/init.sh
fi

# Запуск PostgreSQL
log "🐘 Запуск PostgreSQL..."
pg_ctl -D /app/data/postgres -l /app/logs/postgres.log start || true

# Ожидание готовности PostgreSQL
check_health "PostgreSQL" "http://localhost:5432" || {
    log "❌ PostgreSQL не запустился"
    exit 1
}

# Запуск Redis
log "🔴 Запуск Redis..."
redis-server --daemonize yes --logfile /app/logs/redis.log

# Ожидание готовности Redis
check_health "Redis" "http://localhost:6379" || {
    log "❌ Redis не запустился"
    exit 1
}

# Запуск Qdrant
log "🔍 Запуск Qdrant..."
qdrant --storage-path /app/data/qdrant --log-level INFO > /app/logs/qdrant.log 2>&1 &

# Ожидание готовности Qdrant
check_health "Qdrant" "http://localhost:6333/health" || {
    log "❌ Qdrant не запустился"
    exit 1
}

# Запуск Python сервисов
log "🐍 Запуск Python сервисов..."

# Document Parser
log "📄 Запуск Document Parser..."
cd /app/document_parser
python -m uvicorn main:app --host 0.0.0.0 --port 8001 --timeout-keep-alive 600 --limit-max-requests 500 --limit-concurrency 5 --timeout-graceful-shutdown 60 > /app/logs/document-parser.log 2>&1 &

# RAG Service
log "🧠 Запуск RAG Service..."
cd /app/rag_service
python -m uvicorn main:app --host 0.0.0.0 --port 8002 > /app/logs/rag-service.log 2>&1 &

# Rule Engine
log "⚙️ Запуск Rule Engine..."
cd /app/rule_engine
python -m uvicorn main:app --host 0.0.0.0 --port 8003 > /app/logs/rule-engine.log 2>&1 &

# Gateway
log "🌐 Запуск Gateway..."
cd /app/gateway
python -m uvicorn app:app --host 0.0.0.0 --port 8004 > /app/logs/gateway.log 2>&1 &

# Ожидание готовности сервисов
log "⏳ Ожидание готовности сервисов..."

check_health "Document Parser" "http://localhost:8001/health" || {
    log "❌ Document Parser не готов"
    exit 1
}

check_health "RAG Service" "http://localhost:8002/health" || {
    log "❌ RAG Service не готов"
    exit 1
}

check_health "Rule Engine" "http://localhost:8003/health" || {
    log "❌ Rule Engine не готов"
    exit 1
}

check_health "Gateway" "http://localhost:8004/health" || {
    log "❌ Gateway не готов"
    exit 1
}

# Запуск Nginx
log "🌐 Запуск Nginx..."
nginx -g "daemon off;" &

# Ожидание готовности Nginx
check_health "Nginx" "http://localhost:80" || {
    log "❌ Nginx не готов"
    exit 1
}

log "🎉 AI-NK система успешно запущена!"
log "📊 Доступные сервисы:"
log "   - Frontend: http://localhost"
log "   - API Gateway: http://localhost/api"
log "   - Document Parser: http://localhost:8001"
log "   - RAG Service: http://localhost:8002"
log "   - Rule Engine: http://localhost:8003"

# Мониторинг процессов
log "📈 Запуск мониторинга процессов..."
while true; do
    sleep 30
    
    # Проверка основных процессов
    if ! pgrep -f "uvicorn.*main:app" > /dev/null; then
        log "❌ Один из Python сервисов остановился"
        exit 1
    fi
    
    if ! pgrep nginx > /dev/null; then
        log "❌ Nginx остановился"
        exit 1
    fi
    
    if ! pgrep postgres > /dev/null; then
        log "❌ PostgreSQL остановился"
        exit 1
    fi
    
    log "✅ Все сервисы работают нормально"
done
