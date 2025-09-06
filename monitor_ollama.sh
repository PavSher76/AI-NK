#!/bin/bash

# Скрипт мониторинга Ollama
# Использование: ./monitor_ollama.sh

echo "📊 [OLLAMA_MONITOR] Мониторинг Ollama..."

while true; do
    clear
    echo "📊 [OLLAMA_MONITOR] $(date)"
    echo "=================================="
    
    # Проверка статуса
    if curl -s http://localhost:11434/api/tags > /dev/null; then
        echo "✅ Ollama: ONLINE"
        
        # Информация о моделях
        echo ""
        echo "🤖 Доступные модели:"
        curl -s http://localhost:11434/api/tags | jq -r '.models[] | "  - \(.name) (\(.details.parameter_size))"'
        
        # Тест производительности
        echo ""
        echo "⚡ Тест производительности:"
        start_time=$(date +%s%N)
        response=$(curl -s http://localhost:11434/api/generate \
            -d '{"model": "gpt-oss-optimized", "prompt": "Тест", "stream": false}' \
            | jq -r '.eval_duration // .total_duration // 0')
        end_time=$(date +%s%N)
        
        if [ "$response" != "0" ] && [ "$response" != "null" ]; then
            echo "  - Время генерации: $((response / 1000000))ms"
        else
            echo "  - Время генерации: $(((end_time - start_time) / 1000000))ms"
        fi
        
    else
        echo "❌ Ollama: OFFLINE"
    fi
    
    echo ""
    echo "🔄 Обновление через 30 секунд... (Ctrl+C для выхода)"
    sleep 30
done
