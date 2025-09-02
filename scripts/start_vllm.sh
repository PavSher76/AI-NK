#!/bin/bash

# Скрипт запуска VLLM + Ollama Integration Service
# Автор: AI Assistant
# Дата: $(date)

set -e

echo "🚀 [VLLM] Запуск VLLM + Ollama Integration Service..."

# Проверяем, что мы в корневой директории проекта
if [ ! -f "docker-compose.yaml" ]; then
    echo "❌ [VLLM] Ошибка: запустите скрипт из корневой директории проекта"
    exit 1
fi

# Проверяем, что Ollama запущен
echo "🔍 [VLLM] Проверка статуса Ollama..."
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "❌ [VLLM] Ошибка: Ollama не запущен на порту 11434"
    echo "💡 [VLLM] Запустите Ollama: ollama serve"
    exit 1
fi

echo "✅ [VLLM] Ollama доступен"

# Проверяем доступные модели
echo "🔍 [VLLM] Проверка доступных моделей..."
MODELS=$(curl -s http://localhost:11434/api/tags | jq -r '.models[].name' 2>/dev/null || echo "")

if [ -z "$MODELS" ]; then
    echo "⚠️ [VLLM] Предупреждение: не удалось получить список моделей"
else
    echo "📋 [VLLM] Доступные модели:"
    echo "$MODELS" | while read -r model; do
        echo "  - $model"
    done
fi

# Останавливаем локальный VLLM сервис, если он запущен
echo "🛑 [VLLM] Остановка локального VLLM сервиса..."
pkill -f "python main.py" 2>/dev/null || true

# Собираем и запускаем VLLM контейнер
echo "🔨 [VLLM] Сборка VLLM Docker образа..."
docker-compose build vllm

echo "🚀 [VLLM] Запуск VLLM контейнера..."
docker-compose up -d vllm

# Ждем запуска сервиса
echo "⏳ [VLLM] Ожидание запуска VLLM сервиса..."
sleep 10

# Проверяем статус
echo "🔍 [VLLM] Проверка статуса VLLM сервиса..."
if curl -s http://localhost:8005/health > /dev/null; then
    echo "✅ [VLLM] VLLM сервис успешно запущен на порту 8005"
    
    # Показываем информацию о сервисе
    echo "📊 [VLLM] Информация о сервисе:"
    curl -s http://localhost:8005/ | jq '.' 2>/dev/null || curl -s http://localhost:8005/
    
    echo ""
    echo "🔗 [VLLM] Доступные эндпоинты:"
    echo "  - Health: http://localhost:8005/health"
    echo "  - Models: http://localhost:8005/models"
    echo "  - Chat: http://localhost:8005/chat"
    echo "  - Stats: http://localhost:8005/stats"
    
else
    echo "❌ [VLLM] Ошибка: VLLM сервис не отвечает"
    echo "📋 [VLLM] Логи контейнера:"
    docker-compose logs vllm --tail=20
    exit 1
fi

echo ""
echo "🎉 [VLLM] VLLM + Ollama Integration Service успешно запущен!"
echo "💡 [VLLM] Для остановки: docker-compose stop vllm"
echo "💡 [VLLM] Для просмотра логов: docker-compose logs -f vllm"
