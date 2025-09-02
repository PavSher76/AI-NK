#!/bin/bash

# Скрипт для запуска интегрированного RAG сервиса
# Использование: ./start_integrated_rag.sh [port]

set -e

# Параметры по умолчанию
PORT=${1:-8003}
RAG_SERVICE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/rag_service"

echo "🚀 [INTEGRATED_RAG] Starting Integrated RAG Service..."
echo "📍 [INTEGRATED_RAG] Port: $PORT"
echo "📁 [INTEGRATED_RAG] Service directory: $RAG_SERVICE_DIR"

# Проверяем, что мы в правильной директории
if [ ! -f "$RAG_SERVICE_DIR/integrated_main.py" ]; then
    echo "❌ [INTEGRATED_RAG] integrated_main.py not found in $RAG_SERVICE_DIR"
    exit 1
fi

# Проверяем доступность Ollama
echo "🔍 [INTEGRATED_RAG] Checking Ollama availability..."
if ! curl -s "http://localhost:11434/api/tags" > /dev/null; then
    echo "❌ [INTEGRATED_RAG] Ollama is not running. Please start Ollama first."
    echo "💡 [INTEGRATED_RAG] Run: ollama serve"
    exit 1
fi

# Проверяем наличие модели BGE-M3
BGE_M3_AVAILABLE=$(curl -s "http://localhost:11434/api/tags" | jq -r '.models[] | select(.name | contains("bge-m3")) | .name' 2>/dev/null || echo "")
if [ -z "$BGE_M3_AVAILABLE" ]; then
    echo "❌ [INTEGRATED_RAG] BGE-M3 model not found in Ollama."
    echo "💡 [INTEGRATED_RAG] Please pull the model: ollama pull bge-m3"
    exit 1
fi
echo "✅ [INTEGRATED_RAG] BGE-M3 model available: $BGE_M3_AVAILABLE"

# Проверяем доступность vLLM
echo "🔍 [INTEGRATED_RAG] Checking vLLM availability..."
if ! curl -s "http://localhost:8000/v1/models" > /dev/null; then
    echo "❌ [INTEGRATED_RAG] vLLM is not running. Please start vLLM first."
    echo "💡 [INTEGRATED_RAG] Run: ./scripts/start_vllm.sh"
    exit 1
fi

# Проверяем наличие модели GPT-OSS
GPT_OSS_AVAILABLE=$(curl -s "http://localhost:8000/v1/models" | jq -r '.data[] | select(.id | contains("gpt-oss")) | .id' 2>/dev/null || echo "")
if [ -z "$GPT_OSS_AVAILABLE" ]; then
    echo "❌ [INTEGRATED_RAG] GPT-OSS model not found in vLLM."
    echo "💡 [INTEGRATED_RAG] Please ensure GPT-OSS model is loaded in vLLM"
    exit 1
fi
echo "✅ [INTEGRATED_RAG] GPT-OSS model available: $GPT_OSS_AVAILABLE"

# Проверяем доступность Qdrant
echo "🔍 [INTEGRATED_RAG] Checking Qdrant availability..."
if ! curl -s "http://localhost:6333/collections" > /dev/null; then
    echo "❌ [INTEGRATED_RAG] Qdrant is not running. Please start Qdrant first."
    echo "💡 [INTEGRATED_RAG] Run: docker-compose up qdrant -d"
    exit 1
fi
echo "✅ [INTEGRATED_RAG] Qdrant is available"

# Проверяем доступность PostgreSQL
echo "🔍 [INTEGRATED_RAG] Checking PostgreSQL availability..."
if ! pg_isready -h localhost -p 5432 -U norms_user > /dev/null 2>&1; then
    echo "❌ [INTEGRATED_RAG] PostgreSQL is not accessible. Please start PostgreSQL first."
    echo "💡 [INTEGRATED_RAG] Run: docker-compose up norms-db -d"
    exit 1
fi
echo "✅ [INTEGRATED_RAG] PostgreSQL is accessible"

# Переходим в директорию RAG сервиса
cd "$RAG_SERVICE_DIR"

# Проверяем, запущен ли уже RAG сервис
if pgrep -f "integrated_main.py" > /dev/null; then
    echo "⚠️ [INTEGRATED_RAG] Integrated RAG Service is already running. Stopping existing process..."
    pkill -f "integrated_main.py"
    sleep 2
fi

# Устанавливаем переменные окружения
export PYTHONPATH="$RAG_SERVICE_DIR:$PYTHONPATH"

# Запускаем интегрированный RAG сервис
echo "🤖 [INTEGRATED_RAG] Starting Integrated RAG Service..."
python integrated_main.py &

RAG_PID=$!
echo "✅ [INTEGRATED_RAG] Integrated RAG Service started with PID: $RAG_PID"

# Ждем запуска сервиса
echo "⏳ [INTEGRATED_RAG] Waiting for service to start..."
sleep 5

# Проверяем статус
if curl -s "http://localhost:$PORT/health" > /dev/null; then
    echo "✅ [INTEGRATED_RAG] Integrated RAG Service is running successfully on port $PORT"
    echo "🔗 [INTEGRATED_RAG] Service endpoint: http://localhost:$PORT"
    echo "💬 [INTD_CONSULTATION] NTD Consultation: http://localhost:$PORT/ntd-consultation/chat"
    echo "🔍 [SEARCH] Search endpoint: http://localhost:$PORT/search"
    echo "📊 [HEALTH] Health check: http://localhost:$PORT/health"
    echo "📈 [METRICS] Metrics: http://localhost:$PORT/metrics"
    
    # Показываем статус здоровья
    echo "🏥 [HEALTH] Service health status:"
    curl -s "http://localhost:$PORT/health" | jq '.' 2>/dev/null || curl -s "http://localhost:$PORT/health"
    
    echo ""
    echo "💡 [INTEGRATED_RAG] To stop the service, run: pkill -f 'integrated_main.py'"
    echo "💡 [INTEGRATED_RAG] Or use Ctrl+C to stop this script"
    
    # Сохраняем PID в файл для последующего управления
    echo $RAG_PID > /tmp/integrated_rag.pid
    
    # Ждем завершения
    wait $RAG_PID
else
    echo "❌ [INTEGRATED_RAG] Failed to start Integrated RAG Service"
    kill $RAG_PID 2>/dev/null || true
    exit 1
fi
