#!/bin/bash

# Скрипт оптимизации Ollama с GPT-OSS для нормоконтроля
# Автор: AI Assistant
# Дата: $(date)

set -e

echo "🚀 [OLLAMA_OPTIMIZATION] Начинаем оптимизацию Ollama с GPT-OSS..."

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для логирования
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Проверка доступности Ollama
check_ollama() {
    log "Проверяем доступность Ollama..."
    
    if ! curl -s http://localhost:11434/api/tags > /dev/null; then
        error "Ollama не запущен. Запустите Ollama: ollama serve"
        exit 1
    fi
    
    success "Ollama доступен"
}

# Проверка наличия GPT-OSS модели
check_gpt_oss() {
    log "Проверяем наличие GPT-OSS модели..."
    
    if ! curl -s http://localhost:11434/api/tags | jq -e '.models[] | select(.name | contains("gpt-oss"))' > /dev/null; then
        error "GPT-OSS модель не найдена. Установите модель: ollama pull gpt-oss:latest"
        exit 1
    fi
    
    success "GPT-OSS модель найдена"
}

# Создание оптимизированной модели
create_optimized_model() {
    log "Создаем оптимизированную модель GPT-OSS..."
    
    if [ ! -f "Modelfile.gpt-oss-optimized" ]; then
        error "Файл Modelfile.gpt-oss-optimized не найден"
        exit 1
    fi
    
    # Создаем оптимизированную модель
    ollama create gpt-oss-optimized -f Modelfile.gpt-oss-optimized
    
    if [ $? -eq 0 ]; then
        success "Оптимизированная модель gpt-oss-optimized создана"
    else
        error "Ошибка создания оптимизированной модели"
        exit 1
    fi
}

# Тестирование оптимизированной модели
test_optimized_model() {
    log "Тестируем оптимизированную модель..."
    
    # Тестовый запрос
    test_prompt="Проанализируй требования к проектированию оснований зданий согласно СП 22.13330.2016"
    
    response=$(curl -s http://localhost:11434/api/generate \
        -d "{\"model\": \"gpt-oss-optimized\", \"prompt\": \"$test_prompt\", \"stream\": false}" \
        | jq -r '.response')
    
    if [ "$response" != "null" ] && [ -n "$response" ]; then
        success "Оптимизированная модель работает корректно"
        echo "Пример ответа: ${response:0:200}..."
    else
        error "Ошибка тестирования оптимизированной модели"
        exit 1
    fi
}

# Создание конфигурационного файла для запуска
create_startup_config() {
    log "Создаем конфигурационный файл для запуска..."
    
    cat > ollama_startup_config.env << EOF
# Конфигурация Ollama для оптимизированной работы
# Создано: $(date)

# Основные настройки
OLLAMA_HOST=0.0.0.0
OLLAMA_ORIGINS=*

# Оптимизация производительности
OLLAMA_NUM_CTX=32768
OLLAMA_NUM_BATCH=2048
OLLAMA_NUM_THREAD=8
# OLLAMA_FLASH_ATTN=1  # Flash Attention включен по умолчанию

# Настройки модели
OLLAMA_TEMPERATURE=0.1
OLLAMA_TOP_P=0.9
OLLAMA_TOP_K=40
OLLAMA_REPEAT_PENALTY=1.1
OLLAMA_REPEAT_LAST_N=64

# Оптимизация памяти
OLLAMA_GPU_LAYERS=10
OLLAMA_CPU_THREADS=8

# Логирование
OLLAMA_DEBUG=0
OLLAMA_VERBOSE=0
EOF
    
    success "Конфигурационный файл создан: ollama_startup_config.env"
}

# Создание скрипта запуска
create_startup_script() {
    log "Создаем скрипт запуска Ollama..."
    
    cat > start_ollama_optimized.sh << 'EOF'
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
EOF
    
    chmod +x start_ollama_optimized.sh
    success "Скрипт запуска создан: start_ollama_optimized.sh"
}

# Создание скрипта остановки
create_stop_script() {
    log "Создаем скрипт остановки Ollama..."
    
    cat > stop_ollama.sh << 'EOF'
#!/bin/bash

# Скрипт остановки Ollama
# Использование: ./stop_ollama.sh

echo "🛑 [OLLAMA_STOP] Останавливаем Ollama..."

# Останавливаем по PID файлу
if [ -f "ollama.pid" ]; then
    PID=$(cat ollama.pid)
    if kill -0 $PID 2>/dev/null; then
        kill $PID
        echo "✅ Ollama остановлен (PID: $PID)"
        rm -f ollama.pid
    else
        echo "⚠️ Процесс с PID $PID не найден"
        rm -f ollama.pid
    fi
fi

# Дополнительная проверка и остановка
if pgrep -f "ollama serve" > /dev/null; then
    echo "🔄 Останавливаем все процессы Ollama..."
    pkill -f "ollama serve"
    sleep 2
    echo "✅ Все процессы Ollama остановлены"
else
    echo "ℹ️ Ollama не запущен"
fi

echo "✅ Остановка завершена"
EOF
    
    chmod +x stop_ollama.sh
    success "Скрипт остановки создан: stop_ollama.sh"
}

# Создание скрипта мониторинга
create_monitoring_script() {
    log "Создаем скрипт мониторинга..."
    
    cat > monitor_ollama.sh << 'EOF'
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
EOF
    
    chmod +x monitor_ollama.sh
    success "Скрипт мониторинга создан: monitor_ollama.sh"
}

# Основная функция
main() {
    echo "🚀 [OLLAMA_OPTIMIZATION] Начинаем оптимизацию Ollama с GPT-OSS..."
    echo "================================================================"
    
    # Проверки
    check_ollama
    check_gpt_oss
    
    # Оптимизация
    create_optimized_model
    test_optimized_model
    
    # Создание файлов
    create_startup_config
    create_startup_script
    create_stop_script
    create_monitoring_script
    
    echo ""
    echo "🎉 [OLLAMA_OPTIMIZATION] Оптимизация завершена успешно!"
    echo "================================================================"
    echo ""
    echo "📋 Созданные файлы:"
    echo "  - Modelfile.gpt-oss-optimized (конфигурация модели)"
    echo "  - ollama_startup_config.env (переменные окружения)"
    echo "  - start_ollama_optimized.sh (скрипт запуска)"
    echo "  - stop_ollama.sh (скрипт остановки)"
    echo "  - monitor_ollama.sh (скрипт мониторинга)"
    echo ""
    echo "🚀 Для запуска оптимизированного Ollama:"
    echo "  ./start_ollama_optimized.sh"
    echo ""
    echo "📊 Для мониторинга:"
    echo "  ./monitor_ollama.sh"
    echo ""
    echo "🛑 Для остановки:"
    echo "  ./stop_ollama.sh"
    echo ""
    echo "✅ Готово к использованию!"
}

# Запуск основной функции
main "$@"
