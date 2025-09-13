#!/bin/bash

# Скрипт запуска всех сервисов AI-NK
set -e

echo "🚀 Запуск AI-NK системы..."

# Функция для ожидания готовности сервиса
wait_for_service() {
    local host=$1
    local port=$2
    local service_name=$3
    local max_attempts=30
    local attempt=1

    echo "⏳ Ожидание готовности $service_name на $host:$port..."
    
    while [ $attempt -le $max_attempts ]; do
        if nc -z $host $port 2>/dev/null; then
            echo "✅ $service_name готов!"
            return 0
        fi
        echo "   Попытка $attempt/$max_attempts..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo "❌ $service_name не готов после $max_attempts попыток"
    return 1
}

# Функция запуска сервиса в фоне
start_service() {
    local service_name=$1
    local command=$2
    local port=$3
    
    echo "🔄 Запуск $service_name..."
    cd /app/$service_name
    nohup $command > /var/log/ai-nk/${service_name}.log 2>&1 &
    echo $! > /var/run/ai-nk/${service_name}.pid
    
    # Ждем готовности сервиса
    if [ -n "$port" ]; then
        wait_for_service localhost $port $service_name
    fi
}

# Создаем необходимые директории
mkdir -p /var/log/ai-nk /var/run/ai-nk /app/uploads /app/temp /app/logs /app/data /app/reports

# Устанавливаем права доступа
chmod 755 /var/log/ai-nk /var/run/ai-nk

# Инициализация базы данных (если нужно)
if [ ! -f /app/data/.initialized ]; then
    echo "🔧 Инициализация базы данных..."
    /app/init.sh
    touch /app/data/.initialized
fi

# Запуск Nginx
echo "🌐 Запуск Nginx..."
nginx -g "daemon off;" &
echo $! > /var/run/ai-nk/nginx.pid

# Запуск микросервисов
echo "🔧 Запуск микросервисов..."

# 1. Document Parser Service
start_service "document_parser" "python -m uvicorn main:app --host 0.0.0.0 --port 8001" "8001"

# 2. RAG Service
start_service "rag_service" "python -m uvicorn main:app --host 0.0.0.0 --port 8003" "8003"

# 3. Rule Engine Service
start_service "rule_engine" "python -m uvicorn main:app --host 0.0.0.0 --port 8002" "8002"

# 4. Calculation Service
start_service "calculation_service" "python -m uvicorn main:app --host 0.0.0.0 --port 8004" "8004"

# 5. VLLM Service
start_service "vllm_service" "python -m uvicorn main:app --host 0.0.0.0 --port 8005" "8005"

# 6. Outgoing Control Service
start_service "outgoing_control_service" "python -m uvicorn main:app --host 0.0.0.0 --port 8006" "8006"

# 7. Spellchecker Service
start_service "spellchecker_service" "python -m uvicorn main:app --host 0.0.0.0 --port 8007" "8007"

# 8. Gateway Service (последний, так как зависит от других)
start_service "gateway" "python -m uvicorn main:app --host 0.0.0.0 --port 8443" "8443"

echo "✅ Все сервисы запущены!"

# Функция для graceful shutdown
cleanup() {
    echo "🛑 Остановка сервисов..."
    
    # Останавливаем все сервисы
    for pidfile in /var/run/ai-nk/*.pid; do
        if [ -f "$pidfile" ]; then
            pid=$(cat "$pidfile")
            if kill -0 "$pid" 2>/dev/null; then
                echo "Остановка процесса $pid..."
                kill -TERM "$pid"
            fi
        fi
    done
    
    # Ждем завершения процессов
    sleep 5
    
    # Принудительно завершаем оставшиеся процессы
    for pidfile in /var/run/ai-nk/*.pid; do
        if [ -f "$pidfile" ]; then
            pid=$(cat "$pidfile")
            if kill -0 "$pid" 2>/dev/null; then
                echo "Принудительная остановка процесса $pid..."
                kill -KILL "$pid"
            fi
        fi
    done
    
    echo "✅ Все сервисы остановлены"
    exit 0
}

# Устанавливаем обработчик сигналов
trap cleanup SIGTERM SIGINT

# Мониторинг процессов
echo "📊 Мониторинг сервисов..."
while true; do
    sleep 30
    
    # Проверяем состояние каждого сервиса
    for pidfile in /var/run/ai-nk/*.pid; do
        if [ -f "$pidfile" ]; then
            pid=$(cat "$pidfile")
            if ! kill -0 "$pid" 2>/dev/null; then
                service_name=$(basename "$pidfile" .pid)
                echo "⚠️  Сервис $service_name остановлен, перезапуск..."
                # Здесь можно добавить логику перезапуска
            fi
        fi
    done
done