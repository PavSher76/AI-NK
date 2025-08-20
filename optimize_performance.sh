#!/bin/bash

# =============================================================================
# AI-NK Performance Optimization для MacBook Pro
# =============================================================================

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Получение информации о системе
get_system_info() {
    print_info "Анализ системы для оптимизации..."
    
    # Архитектура
    ARCH=$(uname -m)
    if [[ "$ARCH" == "arm64" ]]; then
        SYSTEM_TYPE="Apple Silicon"
        OPTIMIZATION_LEVEL="high"
    elif [[ "$ARCH" == "x86_64" ]]; then
        SYSTEM_TYPE="Intel Mac"
        OPTIMIZATION_LEVEL="medium"
    else
        SYSTEM_TYPE="Unknown"
        OPTIMIZATION_LEVEL="low"
    fi
    
    # Память
    TOTAL_MEM=$(sysctl -n hw.memsize | awk '{print $0/1024/1024/1024}')
    TOTAL_MEM_GB=${TOTAL_MEM%.*}
    
    # CPU
    CPU_CORES=$(sysctl -n hw.ncpu)
    CPU_LOGICAL=$(sysctl -n hw.logicalcpu)
    
    # GPU (для Apple Silicon)
    if [[ "$ARCH" == "arm64" ]]; then
        GPU_CORES=$(system_profiler SPDisplaysDataType | grep "Cores" | head -1 | awk '{print $2}')
    else
        GPU_CORES="N/A"
    fi
    
    print_success "Система: $SYSTEM_TYPE"
    print_success "Память: ${TOTAL_MEM_GB}GB"
    print_success "CPU ядер: $CPU_CORES физических, $CPU_LOGICAL логических"
    if [[ "$GPU_CORES" != "N/A" ]]; then
        print_success "GPU ядер: $GPU_CORES"
    fi
}

# Оптимизация Docker
optimize_docker() {
    print_info "Оптимизация Docker для MacBook Pro..."
    
    # Создание или обновление .docker/daemon.json
    mkdir -p ~/.docker
    
    cat > ~/.docker/daemon.json << EOF
{
  "experimental": true,
  "features": {
    "buildkit": true
  },
  "builder": {
    "gc": {
      "enabled": true,
      "defaultKeepStorage": "20GB"
    }
  },
  "max-concurrent-downloads": 10,
  "max-concurrent-uploads": 5,
  "storage-driver": "overlay2",
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
EOF
    
    print_success "Docker оптимизирован"
}

# Оптимизация переменных окружения
optimize_env() {
    print_info "Оптимизация переменных окружения..."
    
    # Загрузка текущих настроек
    if [[ -f "env.macbook" ]]; then
        source env.macbook
    fi
    
    # Определение оптимальных настроек на основе системы
    if [[ "$TOTAL_MEM_GB" -ge 32 ]]; then
        OLLAMA_MEMORY_LIMIT="16G"
        OLLAMA_MEMORY_RESERVATION="12G"
        OLLAMA_GPU_LAYERS="40"
        OLLAMA_BATCH_SIZE="1024"
        OLLAMA_CPU_THREADS="12"
    elif [[ "$TOTAL_MEM_GB" -ge 24 ]]; then
        OLLAMA_MEMORY_LIMIT="14G"
        OLLAMA_MEMORY_RESERVATION="10G"
        OLLAMA_GPU_LAYERS="38"
        OLLAMA_BATCH_SIZE="768"
        OLLAMA_CPU_THREADS="10"
    elif [[ "$TOTAL_MEM_GB" -ge 16 ]]; then
        OLLAMA_MEMORY_LIMIT="12G"
        OLLAMA_MEMORY_RESERVATION="8G"
        OLLAMA_GPU_LAYERS="35"
        OLLAMA_BATCH_SIZE="512"
        OLLAMA_CPU_THREADS="8"
    else
        OLLAMA_MEMORY_LIMIT="8G"
        OLLAMA_MEMORY_RESERVATION="6G"
        OLLAMA_GPU_LAYERS="30"
        OLLAMA_BATCH_SIZE="256"
        OLLAMA_CPU_THREADS="6"
    fi
    
    # Создание оптимизированного файла env
    cat > env.macbook.optimized << EOF
# =============================================================================
# AI-NK Оптимизированная конфигурация для MacBook Pro
# Автоматически настроено для ${SYSTEM_TYPE} с ${TOTAL_MEM_GB}GB RAM
# =============================================================================

# Основные настройки портов
KEYCLOAK_PORT=8081
GATEWAY_PORT=8443
FRONTEND_PORT=443
OLLAMA_PORT=11434
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
POSTGRES_PORT=5432
QDANT_PORT=6333

# Настройки базы данных
POSTGRES_DB=norms_db
POSTGRES_USER=norms_user
POSTGRES_PASSWORD=norms_password

# Настройки Redis
REDIS_PASSWORD=redispass

# Настройки Keycloak
KEYCLOAK_ADMIN=admin
KEYCLOAK_ADMIN_PASSWORD=admin

# Настройки Grafana
GRAFANA_ADMIN_PASSWORD=admin

# =============================================================================
# ОПТИМИЗАЦИЯ ДЛЯ ВАШЕЙ СИСТЕМЫ
# =============================================================================

# Настройки для Ollama (Llama3) - оптимизировано для ${TOTAL_MEM_GB}GB RAM
OLLAMA_MODEL=llama3.1:8b
OLLAMA_GPU_LAYERS=${OLLAMA_GPU_LAYERS}
OLLAMA_CPU_THREADS=${OLLAMA_CPU_THREADS}
OLLAMA_BATCH_SIZE=${OLLAMA_BATCH_SIZE}

# Настройки памяти для контейнеров
OLLAMA_MEMORY_LIMIT=${OLLAMA_MEMORY_LIMIT}
OLLAMA_MEMORY_RESERVATION=${OLLAMA_MEMORY_RESERVATION}

VLLM_MEMORY_LIMIT=2G
VLLM_MEMORY_RESERVATION=1G

GATEWAY_MEMORY_LIMIT=1G
GATEWAY_MEMORY_RESERVATION=512M

POSTGRES_MEMORY_LIMIT=2G
POSTGRES_MEMORY_RESERVATION=1G

QDANT_MEMORY_LIMIT=2G
QDANT_MEMORY_RESERVATION=1G

DOCUMENT_PARSER_MEMORY_LIMIT=2G
DOCUMENT_PARSER_MEMORY_RESERVATION=1G

RULE_ENGINE_MEMORY_LIMIT=2G
RULE_ENGINE_MEMORY_RESERVATION=1G

RAG_SERVICE_MEMORY_LIMIT=1G
RAG_SERVICE_MEMORY_RESERVATION=512M

# Настройки производительности
DOCKER_COMPOSE_PARALLEL=4
DOCKER_BUILDKIT=1

# Настройки для разработки
NODE_ENV=development
PYTHONUNBUFFERED=1

# Настройки логирования
LOG_LEVEL=INFO

# Дополнительные оптимизации для ${SYSTEM_TYPE}
EOF
    
    # Копирование оптимизированного файла
    cp env.macbook.optimized env.macbook
    rm env.macbook.optimized
    
    print_success "Переменные окружения оптимизированы для вашей системы"
}

# Оптимизация Docker Compose
optimize_docker_compose() {
    print_info "Оптимизация Docker Compose конфигурации..."
    
    # Создание оптимизированной версии docker-compose
    if [[ -f "docker-compose.macbook.yaml" ]]; then
        # Добавление оптимизаций для Apple Silicon
        if [[ "$ARCH" == "arm64" ]]; then
            sed -i '' 's/platform: linux\/arm64/platform: linux\/arm64\n    environment:\n      - OLLAMA_HOST=0.0.0.0\n      - OLLAMA_ORIGINS=*\n      - OLLAMA_MODEL=${OLLAMA_MODEL:-llama3.1:8b}/' docker-compose.macbook.yaml
        fi
        
        print_success "Docker Compose оптимизирован"
    else
        print_warning "Файл docker-compose.macbook.yaml не найден"
    fi
}

# Оптимизация системы
optimize_system() {
    print_info "Оптимизация системы..."
    
    # Увеличение лимитов файловых дескрипторов
    if [[ -f ~/.zshrc ]]; then
        echo 'ulimit -n 65536' >> ~/.zshrc
        print_success "Лимит файловых дескрипторов увеличен"
    fi
    
    # Настройка swap (если необходимо)
    if [[ "$TOTAL_MEM_GB" -lt 16 ]]; then
        print_warning "Рекомендуется увеличить swap для систем с менее чем 16GB RAM"
        print_info "Выполните: sudo sysctl vm.swapusage"
    fi
    
    print_success "Система оптимизирована"
}

# Тестирование производительности
test_performance() {
    print_info "Тестирование производительности..."
    
    # Проверка доступности Ollama
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        print_success "Ollama доступен"
        
        # Тест производительности
        print_info "Выполнение теста производительности..."
        
        # Простой тест генерации
        START_TIME=$(date +%s)
        curl -s -X POST http://localhost:11434/api/generate \
            -H "Content-Type: application/json" \
            -d '{
                "model": "llama3.1:8b",
                "prompt": "Hello, how are you?",
                "stream": false,
                "options": {
                    "num_predict": 50,
                    "temperature": 0.7
                }
            }' > /dev/null
        
        END_TIME=$(date +%s)
        RESPONSE_TIME=$((END_TIME - START_TIME))
        
        print_success "Время ответа: ${RESPONSE_TIME} секунд"
        
        if [[ "$RESPONSE_TIME" -le 5 ]]; then
            print_success "Производительность отличная!"
        elif [[ "$RESPONSE_TIME" -le 10 ]]; then
            print_warning "Производительность хорошая"
        else
            print_warning "Производительность может быть улучшена"
        fi
    else
        print_warning "Ollama недоступен. Запустите сервисы: ./setup_macbook.sh"
    fi
}

# Рекомендации по оптимизации
show_recommendations() {
    print_info "Рекомендации по оптимизации для вашей системы:"
    echo
    
    if [[ "$TOTAL_MEM_GB" -lt 16 ]]; then
        print_warning "⚠️  Система с ${TOTAL_MEM_GB}GB RAM:"
        echo "   - Используйте модель llama3.1:8b"
        echo "   - Закройте другие приложения при работе"
        echo "   - Рассмотрите возможность увеличения RAM"
    elif [[ "$TOTAL_MEM_GB" -lt 32 ]]; then
        print_info "✅ Система с ${TOTAL_MEM_GB}GB RAM:"
        echo "   - Оптимальная конфигурация для llama3.1:8b"
        echo "   - Можете попробовать llama3.1:70b"
    else
        print_success "🚀 Система с ${TOTAL_MEM_GB}GB RAM:"
        echo "   - Отличная производительность"
        echo "   - Можете использовать llama3.1:70b"
        echo "   - Увеличьте OLLAMA_GPU_LAYERS до 40"
    fi
    
    echo
    print_info "Дополнительные рекомендации:"
    echo "   - Используйте SSD для лучшей производительности"
    echo "   - Поддерживайте macOS в актуальном состоянии"
    echo "   - Мониторьте температуру системы"
    echo "   - Используйте Activity Monitor для отслеживания ресурсов"
}

# Основная функция
main() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}  AI-NK Performance Optimizer  ${NC}"
    echo -e "${BLUE}================================${NC}"
    echo
    
    get_system_info
    optimize_docker
    optimize_env
    optimize_docker_compose
    optimize_system
    test_performance
    show_recommendations
    
    echo
    print_success "Оптимизация завершена!"
    print_info "Для применения изменений перезапустите сервисы:"
    echo "   ./setup_macbook.sh restart"
}

# Обработка аргументов
case "${1:-}" in
    "test")
        test_performance
        ;;
    "recommendations")
        get_system_info
        show_recommendations
        ;;
    "env")
        get_system_info
        optimize_env
        ;;
    *)
        main
        ;;
esac
