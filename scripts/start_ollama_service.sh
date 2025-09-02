#!/bin/bash

# Скрипт для запуска Ollama Integration Service
# Использование: ./start_vllm_ollama.sh [port]

set -e

# Параметры по умолчанию
PORT=${1:-8005}
OLLAMA_SERVICE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/ollama_service"

echo "🚀 [OLLAMA_INTEGRATION] Starting Ollama Integration Service..."
echo "📍 [OLLAMA_INTEGRATION] Port: $PORT"
echo "📁 [OLLAMA_INTEGRATION] Service directory: $OLLAMA_SERVICE_DIR"

# Проверяем, что мы в правильной директории
if [ ! -f "$OLLAMA_SERVICE_DIR/main.py" ]; then
    echo "❌ [OLLAMA_INTEGRATION] main.py not found in $OLLAMA_SERVICE_DIR"
    exit 1
fi

# Проверяем доступность Ollama
echo "🔍 [OLLAMA_INTEGRATION] Checking Ollama availability..."
if ! curl -s "http://localhost:11434/api/tags" > /dev/null; then
    echo "❌ [OLLAMA_INTEGRATION] Ollama is not running. Please start Ollama first."
    echo "💡 [OLLAMA_INTEGRATION] Run: ollama serve"
    exit 1
fi

# Проверяем наличие моделей
echo "🔍 [VLLM_OLLAMA] Checking available models..."
BGE_M3_AVAILABLE=$(curl -s "http://localhost:11434/api/tags" | jq -r '.models[] | select(.name | contains("bge-m3")) | .name' 2>/dev/null || echo "")
GPT_OSS_AVAILABLE=$(curl -s "http://localhost:11434/api/tags" | jq -r '.models[] | select(.name | contains("gpt-oss")) | .name' 2>/dev/null || echo "")

if [ -z "$BGE_M3_AVAILABLE" ]; then
    echo "⚠️ [VLLM_OLLAMA] BGE-M3 model not found in Ollama."
    echo "💡 [VLLM_OLLAMA] Please pull the model: ollama pull bge-m3"
fi

if [ -z "$GPT_OSS_AVAILABLE" ]; then
    echo "⚠️ [VLLM_OLLAMA] GPT-OSS model not found in Ollama."
    echo "💡 [VLLM_OLLAMA] Please pull the model: ollama pull gpt-oss:20b"
fi

if [ -n "$BGE_M3_AVAILABLE" ]; then
    echo "✅ [VLLM_OLLAMA] BGE-M3 model available: $BGE_M3_AVAILABLE"
fi

if [ -n "$GPT_OSS_AVAILABLE" ]; then
    echo "✅ [VLLM_OLLAMA] GPT-OSS model available: $GPT_OSS_AVAILABLE"
fi

# Переходим в директорию сервиса
cd "$VLLM_SERVICE_DIR"

# Проверяем, запущен ли уже сервис
if pgrep -f "main.py" > /dev/null; then
    echo "⚠️ [VLLM_OLLAMA] VLLM + Ollama Service is already running. Stopping existing process..."
    pkill -f "main.py"
    sleep 2
fi

# Устанавливаем переменные окружения
export PYTHONPATH="$VLLM_SERVICE_DIR:$PYTHONPATH"

# Запускаем сервис
echo "🤖 [VLLM_OLLAMA] Starting VLLM + Ollama Integration Service..."
python main.py &

SERVICE_PID=$!
echo "✅ [VLLM_OLLAMA] Service started with PID: $SERVICE_PID"

# Ждем запуска сервиса
echo "⏳ [VLLM_OLLAMA] Waiting for service to start..."
sleep 5

# Проверяем статус
if curl -s "http://localhost:$PORT/health" > /dev/null; then
    echo "✅ [VLLM_OLLAMA] Service is running successfully on port $PORT"
    echo "🔗 [VLLM_OLLAMA] Service endpoint: http://localhost:$PORT"
    echo "💬 [CHAT] Chat endpoint: http://localhost:$PORT/chat"
    echo "🏥 [HEALTH] Health check: http://localhost:$PORT/health"
    echo "📊 [STATS] Statistics: http://localhost:$PORT/stats"
    echo "🤖 [MODELS] Models list: http://localhost:$PORT/models"
    
    # Показываем статус здоровья
    echo "🏥 [HEALTH] Service health status:"
    curl -s "http://localhost:$PORT/health" | jq '.' 2>/dev/null || curl -s "http://localhost:$PORT/health"
    
    echo ""
    echo "💡 [VLLM_OLLAMA] To stop the service, run: pkill -f 'main.py'"
    echo "💡 [VLLM_OLLAMA] Or use Ctrl+C to stop this script"
    
    # Сохраняем PID в файл для последующего управления
    echo $SERVICE_PID > /tmp/vllm_ollama.pid
    
    # Ждем завершения
    wait $SERVICE_PID
else
    echo "❌ [VLLM_OLLAMA] Failed to start service"
    kill $SERVICE_PID 2>/dev/null || true
    exit 1
fi
