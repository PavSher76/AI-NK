#!/bin/bash

# =============================================================================
# AI-NK Setup Script для MacBook Pro с Llama3
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

# Проверка системы
check_system() {
    print_info "Проверка системы..."
    
    # Проверка macOS
    if [[ "$OSTYPE" != "darwin"* ]]; then
        print_error "Этот скрипт предназначен только для macOS"
        exit 1
    fi
    
    # Проверка архитектуры
    ARCH=$(uname -m)
    if [[ "$ARCH" == "arm64" ]]; then
        print_success "Обнаружен Apple Silicon (ARM64)"
        export DOCKER_DEFAULT_PLATFORM=linux/arm64
    elif [[ "$ARCH" == "x86_64" ]]; then
        print_success "Обнаружен Intel Mac (x86_64)"
        export DOCKER_DEFAULT_PLATFORM=linux/amd64
    else
        print_warning "Неизвестная архитектура: $ARCH"
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
    print_info "Общая память: ${TOTAL_MEM%.*}GB"
    
    if (( $(echo "$TOTAL_MEM < 16" | bc -l) )); then
        print_warning "Рекомендуется минимум 16GB RAM для работы с Llama3"
    fi
    
    print_success "Система готова к работе"
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

# Загрузка переменных окружения
load_env() {
    print_info "Загрузка переменных окружения..."
    
    if [[ -f "env.macbook" ]]; then
        export $(cat env.macbook | grep -v '^#' | xargs)
        print_success "Переменные окружения загружены из env.macbook"
    else
        print_warning "Файл env.macbook не найден. Использование значений по умолчанию"
    fi
}

# Сборка и запуск сервисов
build_and_run() {
    print_info "Сборка и запуск сервисов..."
    
    # Остановка существующих контейнеров
    docker-compose -f docker-compose.macbook.yaml down 2>/dev/null || true
    
    # Очистка неиспользуемых ресурсов
    docker system prune -f
    
    # Сборка образов
    print_info "Сборка Docker образов..."
    docker-compose -f docker-compose.macbook.yaml build --parallel
    
    # Запуск сервисов
    print_info "Запуск сервисов..."
    docker-compose -f docker-compose.macbook.yaml up -d
    
    print_success "Сервисы запущены"
}

# Установка модели Llama3
install_llama3() {
    print_info "Установка модели Llama3..."
    
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
    
    # Установка модели
    print_info "Загрузка модели ${OLLAMA_MODEL:-llama3.1:8b}..."
    curl -X POST http://localhost:11434/api/pull -d "{\"name\": \"${OLLAMA_MODEL:-llama3.1:8b}\"}"
    
    print_success "Модель Llama3 установлена"
}

# Проверка статуса сервисов
check_services() {
    print_info "Проверка статуса сервисов..."
    
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

# Отображение информации о доступе
show_access_info() {
    print_info "Информация о доступе к сервисам:"
    echo
    echo -e "${GREEN}Frontend:${NC} https://localhost"
    echo -e "${GREEN}Keycloak:${NC} https://localhost:8081 (admin/admin)"
    echo -e "${GREEN}Grafana:${NC} http://localhost:3000 (admin/admin)"
    echo -e "${GREEN}Prometheus:${NC} http://localhost:9090"
    echo -e "${GREEN}Ollama:${NC} http://localhost:11434"
    echo -e "${GREEN}API Gateway:${NC} https://localhost:8443"
    echo
    print_info "Для остановки сервисов выполните:"
    echo "docker-compose -f docker-compose.macbook.yaml down"
    echo
    print_info "Для просмотра логов выполните:"
    echo "docker-compose -f docker-compose.macbook.yaml logs -f"
}

# Основная функция
main() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}  AI-NK Setup для MacBook Pro  ${NC}"
    echo -e "${BLUE}================================${NC}"
    echo
    
    check_system
    create_directories
    setup_ssl
    load_env
    build_and_run
    install_llama3
    check_services
    show_access_info
    
    print_success "Установка завершена успешно!"
}

# Обработка аргументов командной строки
case "${1:-}" in
    "stop")
        print_info "Остановка сервисов..."
        docker-compose -f docker-compose.macbook.yaml down
        print_success "Сервисы остановлены"
        ;;
    "restart")
        print_info "Перезапуск сервисов..."
        docker-compose -f docker-compose.macbook.yaml restart
        print_success "Сервисы перезапущены"
        ;;
    "logs")
        print_info "Просмотр логов..."
        docker-compose -f docker-compose.macbook.yaml logs -f
        ;;
    "status")
        check_services
        ;;
    "clean")
        print_info "Очистка всех данных..."
        docker-compose -f docker-compose.macbook.yaml down -v
        docker system prune -af
        print_success "Данные очищены"
        ;;
    *)
        main
        ;;
esac
