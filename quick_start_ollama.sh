#!/bin/bash

# Быстрый старт Ollama с оптимизацией
# Использование: ./quick_start_ollama.sh

set -e

echo "🚀 [QUICK_START] Быстрый старт Ollama с оптимизацией..."
echo "======================================================"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Проверка доступности Ollama
check_ollama() {
    log "Проверяем Ollama..."
    
    if ! curl -s http://localhost:11434/api/tags > /dev/null; then
        error "Ollama не запущен. Запускаем..."
        
        # Пытаемся запустить Ollama
        if command -v ollama > /dev/null; then
            nohup ollama serve > /dev/null 2>&1 &
            sleep 5
            
            if curl -s http://localhost:11434/api/tags > /dev/null; then
                success "Ollama запущен"
            else
                error "Не удалось запустить Ollama. Запустите вручную: ollama serve"
                exit 1
            fi
        else
            error "Ollama не установлен. Установите Ollama: https://ollama.ai"
            exit 1
        fi
    else
        success "Ollama уже запущен"
    fi
}

# Проверка моделей
check_models() {
    log "Проверяем модели..."
    
    # Проверяем GPT-OSS
    if curl -s http://localhost:11434/api/tags | jq -e '.models[] | select(.name | contains("gpt-oss"))' > /dev/null; then
        success "GPT-OSS модель найдена"
    else
        error "GPT-OSS модель не найдена. Установите: ollama pull gpt-oss:latest"
        exit 1
    fi
    
    # Проверяем BGE-M3
    if curl -s http://localhost:11434/api/tags | jq -e '.models[] | select(.name | contains("bge-m3"))' > /dev/null; then
        success "BGE-M3 модель найдена"
    else
        error "BGE-M3 модель не найдена. Установите: ollama pull bge-m3"
        exit 1
    fi
}

# Создание оптимизированной модели (если не существует)
create_optimized_model() {
    log "Проверяем оптимизированную модель..."
    
    if curl -s http://localhost:11434/api/tags | jq -e '.models[] | select(.name == "gpt-oss-optimized")' > /dev/null; then
        success "Оптимизированная модель уже существует"
    else
        log "Создаем оптимизированную модель..."
        
        if [ -f "Modelfile.gpt-oss-optimized" ]; then
            ollama create gpt-oss-optimized -f Modelfile.gpt-oss-optimized
            success "Оптимизированная модель создана"
        else
            error "Файл Modelfile.gpt-oss-optimized не найден. Запустите: ./ollama_optimization_config.sh"
            exit 1
        fi
    fi
}

# Тест системы
test_system() {
    log "Тестируем систему..."
    
    # Тест базовой модели
    echo "🔍 Тест базовой модели:"
    response=$(curl -s http://localhost:11434/api/generate \
        -d '{"model": "gpt-oss:latest", "prompt": "Привет! Как дела?", "stream": false}' \
        | jq -r '.response')
    
    if [ "$response" != "null" ] && [ -n "$response" ]; then
        success "Базовая модель работает: ${response:0:50}..."
    else
        error "Ошибка тестирования базовой модели"
        exit 1
    fi
    
    # Тест оптимизированной модели
    if curl -s http://localhost:11434/api/tags | jq -e '.models[] | select(.name == "gpt-oss-optimized")' > /dev/null; then
        echo "🔍 Тест оптимизированной модели:"
        response=$(curl -s http://localhost:11434/api/generate \
            -d '{"model": "gpt-oss-optimized", "prompt": "Привет! Как дела?", "stream": false}' \
            | jq -r '.response')
        
        if [ "$response" != "null" ] && [ -n "$response" ]; then
            success "Оптимизированная модель работает: ${response:0:50}..."
        else
            error "Ошибка тестирования оптимизированной модели"
        fi
    fi
}

# Показать статус
show_status() {
    echo ""
    echo "📊 [STATUS] Статус системы:"
    echo "=========================="
    
    # Информация о моделях
    echo "🤖 Доступные модели:"
    curl -s http://localhost:11434/api/tags | jq -r '.models[] | "  - \(.name) (\(.details.parameter_size))"'
    
    echo ""
    echo "🔗 API endpoints:"
    echo "  - Ollama API: http://localhost:11434"
    echo "  - Модели: http://localhost:11434/api/tags"
    echo "  - Генерация: http://localhost:11434/api/generate"
    
    echo ""
    echo "📋 Полезные команды:"
    echo "  - Тест производительности: ./test_ollama_performance.sh"
    echo "  - Мониторинг: ./monitor_ollama.sh"
    echo "  - Остановка: ./stop_ollama.sh"
    echo "  - Полная оптимизация: ./ollama_optimization_config.sh"
}

# Основная функция
main() {
    echo "🚀 [QUICK_START] Быстрый старт Ollama с оптимизацией..."
    echo "======================================================"
    
    # Проверки и настройка
    check_ollama
    check_models
    create_optimized_model
    
    # Тестирование
    test_system
    
    # Показать статус
    show_status
    
    echo ""
    echo "🎉 [QUICK_START] Система готова к работе!"
    echo "======================================================"
    echo ""
    echo "✅ Ollama запущен и оптимизирован"
    echo "✅ Модели GPT-OSS и BGE-M3 доступны"
    echo "✅ Оптимизированная модель создана"
    echo "✅ Система протестирована"
    echo ""
    echo "🚀 Готово к использованию!"
}

# Запуск
main "$@"
