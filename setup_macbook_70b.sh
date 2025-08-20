#!/bin/bash

# =============================================================================
# AI-NK Setup Script для MacBook Pro с Llama3.1:70b
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

# Проверка системы для 70b модели
check_system_70b() {
    print_info "Проверка системы для Llama3.1:70b..."
    
    # Проверка macOS
    if [[ "$OSTYPE" != "darwin"* ]]; then
        print_error "Этот скрипт предназначен только для macOS"
        exit 1
    fi
    
    # Проверка архитектуры
    ARCH=$(uname -m)
    if [[ "$ARCH" == "arm64" ]]; then
        print_success "Обнаружен Apple Silicon (ARM64) - отлично для 70b!"
        export DOCKER_DEFAULT_PLATFORM=linux/arm64
    elif [[ "$ARCH" == "x86_64" ]]; then
        print_warning "Обнаружен Intel Mac (x86_64) - 70b может работать медленно"
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
    TOTAL_MEM_GB=${TOTAL_MEM%.*}
    
    print_info "Общая память: ${TOTAL_MEM_GB}GB"
    
    if (( $(echo "$TOTAL_MEM_GB < 32" | bc -l) )); then
        print_error "Для Llama3.1:70b требуется минимум 32GB RAM!"
        print_error "Текущая память: ${TOTAL_MEM_GB}GB"
        print_info "Рекомендуется: 64GB+ для комфортной работы"
        exit 1
    elif (( $(echo "$TOTAL_MEM_GB < 64" | bc -l) )); then
        print_warning "Для оптимальной работы 70b рекомендуется 64GB+ RAM"
        print_info "Текущая память: ${TOTAL_MEM_GB}GB - будет работать, но медленно"
    else
        print_success "Отличная конфигурация для 70b! Память: ${TOTAL_MEM_GB}GB"
    fi
    
    # Проверка свободного места на диске
    FREE_SPACE=$(df -h . | awk 'NR==2 {print $4}' | sed 's/G//')
    if (( $(echo "$FREE_SPACE < 50" | bc -l) )); then
        print_warning "Мало свободного места на диске: ${FREE_SPACE}GB"
        print_info "Модель 70b занимает ~40GB, рекомендуется минимум 50GB свободного места"
    else
        print_success "Достаточно места на диске: ${FREE_SPACE}GB"
    fi
    
    print_success "Система готова к работе с Llama3.1:70b"
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

# Загрузка переменных окружения для 70b
load_env_70b() {
    print_info "Загрузка переменных окружения для 70b..."
    
    if [[ -f "env.macbook.70b" ]]; then
        export $(cat env.macbook.70b | grep -v '^#' | xargs)
        print_success "Переменные окружения загружены из env.macbook.70b"
    else
        print_error "Файл env.macbook.70b не найден!"
        exit 1
    fi
}

# Сборка и запуск сервисов для 70b
build_and_run_70b() {
    print_info "Сборка и запуск сервисов для 70b..."
    
    # Остановка существующих контейнеров
    docker-compose -f docker-compose.macbook.70b.yaml down 2>/dev/null || true
    
    # Очистка неиспользуемых ресурсов
    docker system prune -f
    
    # Сборка образов с оптимизацией для 70b
    print_info "Сборка Docker образов для 70b..."
    DOCKER_BUILDKIT=1 docker-compose -f docker-compose.macbook.70b.yaml build --parallel --no-cache
    
    # Запуск сервисов
    print_info "Запуск сервисов для 70b..."
    docker-compose -f docker-compose.macbook.70b.yaml up -d
    
    print_success "Сервисы для 70b запущены"
}

# Установка модели Llama3.1:70b
install_llama3_70b() {
    print_info "Установка модели Llama3.1:70b..."
    
    # Ждем запуска Ollama
    print_info "Ожидание запуска Ollama..."
    sleep 60  # Увеличенное время ожидания для 70b
    
    # Проверка доступности Ollama
    for i in {1..15}; do
        if curl -s http://localhost:11434/api/tags > /dev/null; then
            print_success "Ollama доступен"
            break
        else
            print_info "Ожидание Ollama... (попытка $i/15)"
            sleep 15
        fi
    done
    
    # Проверка, установлена ли уже модель
    if curl -s http://localhost:11434/api/tags | grep -q "llama3.1:70b"; then
        print_success "Модель llama3.1:70b уже установлена"
    else
        # Установка модели
        print_info "Загрузка модели llama3.1:70b (это может занять 30-60 минут)..."
        print_warning "Размер модели: ~40GB"
        print_info "Убедитесь, что у вас стабильное интернет-соединение"
        
        curl -X POST http://localhost:11434/api/pull -d '{"name": "llama3.1:70b"}'
        
        print_success "Модель llama3.1:70b установлена"
    fi
}

# Проверка статуса сервисов для 70b
check_services_70b() {
    print_info "Проверка статуса сервисов для 70b..."
    
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

# Тестирование производительности 70b
test_performance_70b() {
    print_info "Тестирование производительности 70b модели..."
    
    # Проверка доступности Ollama
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        print_success "Ollama доступен"
        
        # Тест производительности
        print_info "Выполнение теста производительности 70b..."
        
        # Простой тест генерации
        START_TIME=$(date +%s)
        curl -s -X POST http://localhost:11434/api/generate \
            -H "Content-Type: application/json" \
            -d '{
                "model": "llama3.1:70b",
                "prompt": "Hello, how are you?",
                "stream": false,
                "options": {
                    "num_predict": 50,
                    "temperature": 0.7
                }
            }' > /dev/null
        
        END_TIME=$(date +%s)
        RESPONSE_TIME=$((END_TIME - START_TIME))
        
        print_success "Время ответа 70b: ${RESPONSE_TIME} секунд"
        
        if [[ "$RESPONSE_TIME" -le 10 ]]; then
            print_success "Производительность 70b отличная!"
        elif [[ "$RESPONSE_TIME" -le 20 ]]; then
            print_warning "Производительность 70b хорошая"
        else
            print_warning "Производительность 70b может быть улучшена"
        fi
    else
        print_warning "Ollama недоступен. Запустите сервисы: ./setup_macbook_70b.sh"
    fi
}

# Отображение информации о доступе для 70b
show_access_info_70b() {
    print_info "Информация о доступе к сервисам (70b):"
    echo
    echo -e "${GREEN}Frontend:${NC} https://localhost"
    echo -e "${GREEN}Keycloak:${NC} https://localhost:8081 (admin/admin)"
    echo -e "${GREEN}Grafana:${NC} http://localhost:3000 (admin/admin)"
    echo -e "${GREEN}Prometheus:${NC} http://localhost:9090"
    echo -e "${GREEN}Ollama:${NC} http://localhost:11434"
    echo -e "${GREEN}API Gateway:${NC} https://localhost:8443"
    echo
    print_info "Модель: llama3.1:70b"
    print_info "Для остановки сервисов выполните:"
    echo "docker-compose -f docker-compose.macbook.70b.yaml down"
    echo
    print_info "Для просмотра логов выполните:"
    echo "docker-compose -f docker-compose.macbook.70b.yaml logs -f"
}

# Основная функция
main() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}  AI-NK Setup для MacBook Pro  ${NC}"
    echo -e "${BLUE}      с Llama3.1:70b          ${NC}"
    echo -e "${BLUE}================================${NC}"
    echo
    
    check_system_70b
    create_directories
    setup_ssl
    load_env_70b
    build_and_run_70b
    install_llama3_70b
    check_services_70b
    test_performance_70b
    show_access_info_70b
    
    print_success "Установка Llama3.1:70b завершена успешно!"
}

# Обработка аргументов командной строки
case "${1:-}" in
    "stop")
        print_info "Остановка сервисов 70b..."
        docker-compose -f docker-compose.macbook.70b.yaml down
        print_success "Сервисы 70b остановлены"
        ;;
    "restart")
        print_info "Перезапуск сервисов 70b..."
        docker-compose -f docker-compose.macbook.70b.yaml restart
        print_success "Сервисы 70b перезапущены"
        ;;
    "logs")
        print_info "Просмотр логов 70b..."
        docker-compose -f docker-compose.macbook.70b.yaml logs -f
        ;;
    "status")
        check_services_70b
        ;;
    "test")
        test_performance_70b
        ;;
    "clean")
        print_info "Очистка всех данных 70b..."
        docker-compose -f docker-compose.macbook.70b.yaml down -v
        docker system prune -af
        print_success "Данные 70b очищены"
        ;;
    *)
        main
        ;;
esac
