#!/bin/bash

# =============================================================================
# AI-NK Setup Script для MacBook Pro M3 Pro (18GB RAM)
# =============================================================================

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции для вывода
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

# Проверка системы для M3 Pro
check_system_m3pro() {
    print_info "Проверка системы для MacBook Pro M3 Pro..."
    
    # Проверка macOS
    if [[ "$OSTYPE" != "darwin"* ]]; then
        print_error "Этот скрипт предназначен только для macOS"
        exit 1
    fi
    
    # Проверка архитектуры
    ARCH=$(uname -m)
    if [[ "$ARCH" == "arm64" ]]; then
        print_success "Обнаружен Apple Silicon (ARM64) - отлично для M3 Pro!"
        export DOCKER_DEFAULT_PLATFORM=linux/arm64
    else
        print_error "Ожидается ARM64 архитектура для M3 Pro"
        exit 1
    fi
    
    # Проверка Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker не установлен. Установите Docker Desktop для Mac"
        exit 1
    fi
    
    # Проверка Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose не установлен"
        exit 1
    fi
    
    # Проверка доступной памяти
    TOTAL_MEM=$(sysctl -n hw.memsize | awk '{print $0/1024/1024/1024}')
    TOTAL_MEM_GB=${TOTAL_MEM%.*}
    
    print_info "Общая память: ${TOTAL_MEM_GB}GB"
    
    if [[ "$TOTAL_MEM_GB" -lt 16 ]]; then
        print_error "Для M3 Pro требуется минимум 16GB RAM!"
        print_error "Текущая память: ${TOTAL_MEM_GB}GB"
        exit 1
    elif [[ "$TOTAL_MEM_GB" -eq 18 ]]; then
        print_success "Отличная конфигурация для M3 Pro! Память: ${TOTAL_MEM_GB}GB"
        print_info "Рекомендуется использовать llama3.1:8b для оптимальной производительности"
    else
        print_warning "Неожиданный объем памяти для M3 Pro: ${TOTAL_MEM_GB}GB"
        print_info "Скрипт адаптируется под вашу конфигурацию"
    fi
    
    # Проверка свободного места на диске
    FREE_SPACE=$(df -h . | awk 'NR==2 {print $4}' | sed 's/G//')
    if (( $(echo "$FREE_SPACE < 20" | bc -l) )); then
        print_warning "Мало свободного места на диске: ${FREE_SPACE}GB"
        print_info "Рекомендуется минимум 20GB свободного места"
    else
        print_success "Достаточно места на диске: ${FREE_SPACE}GB"
    fi
    
    print_success "Система готова к работе с M3 Pro"
}

# Создание необходимых директорий
create_directories() {
    print_info "Создание необходимых директорий..."
    
    mkdir -p uploads
    mkdir -p temp
    mkdir -p logs
    mkdir -p backups
    mkdir -p ssl
    
    print_success "Директории созданы"
}

# Настройка SSL сертификатов
setup_ssl() {
    print_info "Настройка SSL сертификатов..."
    
    if [[ ! -f "ssl/frontend.crt" ]] || [[ ! -f "ssl/frontend.key" ]]; then
        print_warning "SSL сертификаты не найдены. Создание самоподписанных сертификатов..."
        
        # Создание самоподписанного сертификата
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout ssl/frontend.key \
            -out ssl/frontend.crt \
            -subj "/C=RU/ST=Moscow/L=Moscow/O=AI-NK/CN=localhost"
        
        # Создание Keycloak keystore
        openssl pkcs12 -export \
            -in ssl/frontend.crt \
            -inkey ssl/frontend.key \
            -out ssl/keycloak.p12 \
            -name keycloak \
            -passout pass:keycloak
        
        keytool -importkeystore \
            -srckeystore ssl/keycloak.p12 \
            -srcstoretype PKCS12 \
            -srcstorepass keycloak \
            -destkeystore ssl/keycloak.keystore \
            -deststoretype JKS \
            -deststorepass keycloak
        
        rm ssl/keycloak.p12
        
        print_success "SSL сертификаты созданы"
    else
        print_success "SSL сертификаты уже существуют"
    fi
}

# Загрузка переменных окружения для M3 Pro
load_env_m3pro() {
    print_info "Загрузка переменных окружения для M3 Pro..."
    
    if [[ -f "env.macbook.m3pro" ]]; then
        export $(cat env.macbook.m3pro | grep -v '^#' | xargs)
        print_success "Переменные окружения загружены из env.macbook.m3pro"
    else
        print_error "Файл env.macbook.m3pro не найден!"
        exit 1
    fi
}

# Сборка и запуск сервисов для M3 Pro
build_and_run_m3pro() {
    print_info "Сборка и запуск сервисов для M3 Pro..."
    
    # Остановка существующих контейнеров
    docker-compose -f docker-compose.macbook.m3pro.yaml down 2>/dev/null || true
    
    # Очистка неиспользуемых ресурсов
    docker system prune -f
    
    # Сборка образов с оптимизацией для M3 Pro
    print_info "Сборка Docker образов для M3 Pro..."
    DOCKER_BUILDKIT=1 docker-compose -f docker-compose.macbook.m3pro.yaml build --parallel
    
    # Запуск сервисов
    print_info "Запуск сервисов для M3 Pro..."
    docker-compose -f docker-compose.macbook.m3pro.yaml up -d
    
    print_success "Сервисы для M3 Pro запущены"
}

# Установка модели для M3 Pro
install_model_m3pro() {
    print_info "Установка модели для M3 Pro..."
    
    # Ждем запуска Ollama
    print_info "Ожидание запуска Ollama..."
    sleep 30
    
    # Проверка доступности Ollama
    for i in {1..10}; do
        if curl -s http://localhost:11434/api/tags > /dev/null; then
            print_success "Ollama доступен"
            break
        else
            print_info "Ожидание Ollama... (попытка $i/10)"
            sleep 10
        fi
    done
    
    # Проверка, установлена ли уже модель
    if curl -s http://localhost:11434/api/tags | grep -q "llama3.1:8b"; then
        print_success "Модель llama3.1:8b уже установлена"
    else
        # Установка модели
        print_info "Загрузка модели llama3.1:8b (оптимально для M3 Pro с 18GB RAM)..."
        print_info "Размер модели: ~4.7GB"
        
        curl -X POST http://localhost:11434/api/pull -d '{"name": "llama3.1:8b"}'
        
        print_success "Модель llama3.1:8b установлена"
    fi
}

# Проверка статуса сервисов для M3 Pro
check_services_m3pro() {
    print_info "Проверка статуса сервисов для M3 Pro..."
    
    services=(
        "redis:6379"
        "keycloak:8081"
        "ollama:11434"
        "vllm:8000"
        "gateway:8443"
        "frontend:443"
        "prometheus:9090"
        "grafana:3000"
        "norms-db:5432"
        "qdrant:6333"
        "document-parser:8001"
        "rule-engine:8002"
        "rag-service:8003"
    )
    
    for service in "${services[@]}"; do
        name=$(echo $service | cut -d: -f1)
        port=$(echo $service | cut -d: -f2)
        
        if curl -s http://localhost:$port > /dev/null 2>&1 || \
           curl -s https://localhost:$port > /dev/null 2>&1 || \
           curl -s -k https://localhost:$port > /dev/null 2>&1; then
            print_success "$name доступен на порту $port"
        else
            print_warning "$name недоступен на порту $port"
        fi
    done
}

# Тестирование производительности M3 Pro
test_performance_m3pro() {
    print_info "Тестирование производительности M3 Pro..."
    
    # Проверка доступности Ollama
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        print_success "Ollama доступен"
        
        # Тест производительности
        print_info "Выполнение теста производительности M3 Pro..."
        
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
        
        print_success "Время ответа M3 Pro: ${RESPONSE_TIME} секунд"
        
        if [[ "$RESPONSE_TIME" -le 3 ]]; then
            print_success "Производительность M3 Pro отличная!"
        elif [[ "$RESPONSE_TIME" -le 5 ]]; then
            print_warning "Производительность M3 Pro хорошая"
        else
            print_warning "Производительность M3 Pro может быть улучшена"
        fi
    else
        print_warning "Ollama недоступен. Запустите сервисы: ./setup_macbook_m3pro.sh"
    fi
}

# Отображение информации о доступе для M3 Pro
show_access_info_m3pro() {
    print_info "Информация о доступе к сервисам (M3 Pro):"
    echo
    echo -e "${GREEN}Frontend:${NC} https://localhost"
    echo -e "${GREEN}Keycloak:${NC} https://localhost:8081 (admin/admin)"
    echo -e "${GREEN}Grafana:${NC} http://localhost:3000 (admin/admin)"
    echo -e "${GREEN}Prometheus:${NC} http://localhost:9090"
    echo -e "${GREEN}Ollama:${NC} http://localhost:11434"
    echo -e "${GREEN}API Gateway:${NC} https://localhost:8443"
    echo
    print_info "Модель: llama3.1:8b (оптимально для M3 Pro с 18GB RAM)"
    print_info "Для остановки сервисов выполните:"
    echo "docker-compose -f docker-compose.macbook.m3pro.yaml down"
    echo
    print_info "Для просмотра логов выполните:"
    echo "docker-compose -f docker-compose.macbook.m3pro.yaml logs -f"
}

# Основная функция
main() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}  AI-NK Setup для MacBook Pro  ${NC}"
    echo -e "${BLUE}         M3 Pro (18GB)         ${NC}"
    echo -e "${BLUE}================================${NC}"
    echo
    
    check_system_m3pro
    create_directories
    setup_ssl
    load_env_m3pro
    build_and_run_m3pro
    install_model_m3pro
    check_services_m3pro
    test_performance_m3pro
    show_access_info_m3pro
    
    print_success "Установка для M3 Pro завершена успешно!"
}

# Обработка аргументов командной строки
case "${1:-}" in
    "stop")
        print_info "Остановка сервисов M3 Pro..."
        docker-compose -f docker-compose.macbook.m3pro.yaml down
        print_success "Сервисы M3 Pro остановлены"
        ;;
    "restart")
        print_info "Перезапуск сервисов M3 Pro..."
        docker-compose -f docker-compose.macbook.m3pro.yaml restart
        print_success "Сервисы M3 Pro перезапущены"
        ;;
    "logs")
        print_info "Просмотр логов M3 Pro..."
        docker-compose -f docker-compose.macbook.m3pro.yaml logs -f
        ;;
    "status")
        check_services_m3pro
        ;;
    "test")
        test_performance_m3pro
        ;;
    "clean")
        print_info "Очистка всех данных M3 Pro..."
        docker-compose -f docker-compose.macbook.m3pro.yaml down -v
        docker system prune -af
        print_success "Данные M3 Pro очищены"
        ;;
    *)
        main
        ;;
esac
