#!/bin/bash

# Скрипт запуска оптимизированного Ollama
# Использование: ./start_ollama_optimized.sh

set -e

echo "🚀 [OLLAMA_STARTUP] Запускаем оптимизированный Ollama..."

# Загружаем конфигурацию
if [ -f "ollama_startup_config.env" ]; then
    source ollama_startup_config.env
    echo "✅ Конфигурация загружена"
else
    echo "⚠️ Конфигурационный файл не найден, используем настройки по умолчанию"
fi

# Проверяем, не запущен ли уже Ollama
if pgrep -f "ollama serve" > /dev/null; then
    echo "⚠️ Ollama уже запущен. Останавливаем..."
    pkill -f "ollama serve"
    sleep 3
fi

# Запускаем Ollama с оптимизированными настройками
echo "🤖 Запускаем Ollama с оптимизированными настройками..."

# Экспортируем переменные окружения
export OLLAMA_HOST=${OLLAMA_HOST:-0.0.0.0}
export OLLAMA_ORIGINS=${OLLAMA_ORIGINS:-*}
export OLLAMA_NUM_CTX=${OLLAMA_NUM_CTX:-32768}
export OLLAMA_NUM_BATCH=${OLLAMA_NUM_BATCH:-2048}
export OLLAMA_NUM_THREAD=${OLLAMA_NUM_THREAD:-8}
# export OLLAMA_FLASH_ATTN=${OLLAMA_FLASH_ATTN:-1}  # Flash Attention включен по умолчанию

# Запускаем Ollama в фоновом режиме
nohup ollama serve > ollama.log 2>&1 &
OLLAMA_PID=$!

echo "✅ Ollama запущен с PID: $OLLAMA_PID"
echo "📝 Логи: ollama.log"

# Ждем запуска
echo "⏳ Ждем запуска Ollama..."
sleep 5

# Проверяем статус
if curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "✅ Ollama успешно запущен и доступен"
    echo "🔗 API: http://localhost:11434"
    echo "📊 Модели: http://localhost:11434/api/tags"
    echo "🤖 Оптимизированная модель: gpt-oss-optimized"
    
    # Показываем доступные модели
    echo ""
    echo "📋 Доступные модели:"
    curl -s http://localhost:11434/api/tags | jq -r '.models[] | "  - \(.name) (\(.details.parameter_size))"'
    
    # Сохраняем PID
    echo $OLLAMA_PID > ollama.pid
    echo "💾 PID сохранен в ollama.pid"
    
    echo ""
    echo "🛑 Для остановки: kill $OLLAMA_PID или pkill -f 'ollama serve'"
else
    echo "❌ Ошибка запуска Ollama"
    kill $OLLAMA_PID 2>/dev/null || true
    exit 1
fi
