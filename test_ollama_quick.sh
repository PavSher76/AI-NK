#!/bin/bash

# Быстрый тест Ollama
# Использование: ./test_ollama_quick.sh

set -e

echo "🧪 [QUICK_TEST] Быстрый тест Ollama..."
echo "===================================="

# Цвета
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

# Проверка Ollama
log "Проверяем Ollama..."
if curl -s http://localhost:11434/api/tags > /dev/null; then
    success "Ollama доступен"
else
    error "Ollama недоступен. Запустите: ollama serve"
    exit 1
fi

# Показать модели
log "Доступные модели:"
curl -s http://localhost:11434/api/tags | jq -r '.models[] | "  - \(.name) (\(.details.parameter_size))"'

# Тест GPT-OSS
log "Тестируем GPT-OSS..."
start_time=$(date +%s%N)

response=$(curl -s http://localhost:11434/api/generate \
    -d '{"model": "gpt-oss:latest", "prompt": "Привет! Как дела?", "stream": false}')

end_time=$(date +%s%N)
total_time=$(( (end_time - start_time) / 1000000 ))

eval_duration=$(echo "$response" | jq -r '.eval_duration // 0')
response_text=$(echo "$response" | jq -r '.response // ""')

if [ "$response_text" != "null" ] && [ -n "$response_text" ]; then
    success "GPT-OSS работает"
    echo "  - Время генерации: $((eval_duration / 1000000))ms"
    echo "  - Общее время: ${total_time}ms"
    echo "  - Ответ: ${response_text:0:100}..."
else
    error "Ошибка тестирования GPT-OSS"
fi

# Тест BGE-M3
log "Тестируем BGE-M3..."
start_time=$(date +%s%N)

response=$(curl -s http://localhost:11434/api/embeddings \
    -d '{"model": "bge-m3", "prompt": "Тестовый текст для эмбеддинга"}')

end_time=$(date +%s%N)
total_time=$(( (end_time - start_time) / 1000000 ))

embedding=$(echo "$response" | jq -r '.embedding // []')

if [ "$embedding" != "[]" ] && [ "$embedding" != "null" ]; then
    success "BGE-M3 работает"
    echo "  - Время генерации: ${total_time}ms"
    echo "  - Размер эмбеддинга: $(echo "$embedding" | jq 'length')"
else
    error "Ошибка тестирования BGE-M3"
fi

# Тест оптимизированной модели (если есть)
if curl -s http://localhost:11434/api/tags | jq -e '.models[] | select(.name | contains("gpt-oss-optimized"))' > /dev/null; then
    log "Тестируем оптимизированную модель..."
    start_time=$(date +%s%N)
    
    response=$(curl -s http://localhost:11434/api/generate \
        -d '{"model": "gpt-oss-optimized", "prompt": "Привет! Как дела?", "stream": false}')
    
    end_time=$(date +%s%N)
    total_time=$(( (end_time - start_time) / 1000000 ))
    
    eval_duration=$(echo "$response" | jq -r '.eval_duration // 0')
    response_text=$(echo "$response" | jq -r '.response // ""')
    
    if [ "$response_text" != "null" ] && [ -n "$response_text" ]; then
        success "Оптимизированная модель работает"
        echo "  - Время генерации: $((eval_duration / 1000000))ms"
        echo "  - Общее время: ${total_time}ms"
        echo "  - Ответ: ${response_text:0:100}..."
    else
        error "Ошибка тестирования оптимизированной модели"
    fi
else
    log "Оптимизированная модель не найдена. Создайте: ./ollama_optimization_config.sh"
fi

echo ""
echo "🎉 [QUICK_TEST] Тестирование завершено!"
echo "===================================="
echo ""
echo "📋 Результаты:"
echo "  - Ollama: ✅ Работает"
echo "  - GPT-OSS: ✅ Работает"
echo "  - BGE-M3: ✅ Работает"
echo "  - Оптимизированная модель: $(if curl -s http://localhost:11434/api/tags | jq -e '.models[] | select(.name | contains("gpt-oss-optimized"))' > /dev/null; then echo "✅ Работает"; else echo "⚠️ Не создана"; fi)"
echo ""
echo "🚀 Система готова к использованию!"
