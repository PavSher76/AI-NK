#!/bin/bash

# Скрипт сборки и развертывания AI-NK системы
set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для вывода сообщений
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✅${NC} $1"
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ⚠️${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ❌${NC} $1"
}

# Проверка зависимостей
check_dependencies() {
    log "Проверка зависимостей..."
    
    if ! command -v docker &> /dev/null; then
        error "Docker не установлен!"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose не установлен!"
        exit 1
    fi
    
    success "Все зависимости установлены"
}

# Создание .env файла
create_env_file() {
    log "Создание файла конфигурации .env..."
    
    if [ ! -f .env ]; then
        cat > .env << 'EOF'
# Database Configuration
POSTGRES_HOST=norms-db
POSTGRES_PORT=5432
POSTGRES_DB=norms_db
POSTGRES_USER=norms_user
POSTGRES_PASSWORD=norms_password

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=redispass

# Qdrant Configuration
QDRANT_HOST=qdrant
QDRANT_PORT=6333

# Security
JWT_SECRET_KEY=your-secret-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# File Upload Limits
MAX_FILE_SIZE=104857600
MAX_CHECKABLE_DOCUMENT_SIZE=104857600
MAX_NORMATIVE_DOCUMENT_SIZE=209715200

# Timeouts
LLM_REQUEST_TIMEOUT=120
PAGE_PROCESSING_TIMEOUT=300

# Logging
LOG_LEVEL=INFO
TZ=Europe/Moscow

# Keycloak (опционально)
KEYCLOAK_ADMIN=admin
KEYCLOAK_ADMIN_PASSWORD=admin
KEYCLOAK_PORT=8081

# Monitoring (опционально)
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
GRAFANA_ADMIN_PASSWORD=admin
EOF
        success "Файл .env создан"
    else
        warning "Файл .env уже существует, пропускаем создание"
    fi
}

# Сборка образа
build_image() {
    log "Сборка Docker образа AI-NK..."
    
    # Очистка старых образов
    log "Очистка старых образов..."
    docker image prune -f || true
    
    # Сборка нового образа
    log "Сборка образа ai-nk:latest..."
    docker build -f Dockerfile.production -t ai-nk:latest .
    
    if [ $? -eq 0 ]; then
        success "Образ успешно собран"
    else
        error "Ошибка при сборке образа"
        exit 1
    fi
}

# Запуск системы
start_system() {
    log "Запуск AI-NK системы..."
    
    # Остановка существующих контейнеров
    log "Остановка существующих контейнеров..."
    docker-compose -f docker-compose.production.yml down || true
    
    # Запуск системы
    log "Запуск системы с docker-compose..."
    docker-compose -f docker-compose.production.yml up -d
    
    if [ $? -eq 0 ]; then
        success "Система успешно запущена"
    else
        error "Ошибка при запуске системы"
        exit 1
    fi
}

# Проверка состояния системы
check_system_health() {
    log "Проверка состояния системы..."
    
    # Ждем запуска основных сервисов
    log "Ожидание запуска сервисов..."
    sleep 30
    
    # Проверяем основные сервисы
    services=("ai-nk" "norms-db" "qdrant" "redis")
    
    for service in "${services[@]}"; do
        if docker-compose -f docker-compose.production.yml ps | grep -q "$service.*Up"; then
            success "Сервис $service запущен"
        else
            warning "Сервис $service не запущен или имеет проблемы"
        fi
    done
    
    # Проверяем доступность веб-интерфейса
    log "Проверка доступности веб-интерфейса..."
    if curl -f http://localhost/health >/dev/null 2>&1; then
        success "Веб-интерфейс доступен"
    else
        warning "Веб-интерфейс недоступен, возможно сервисы еще запускаются"
    fi
}

# Показать информацию о системе
show_system_info() {
    log "Информация о системе:"
    echo ""
    echo "🌐 Веб-интерфейс: http://localhost"
    echo "🔒 HTTPS: https://localhost"
    echo "📊 API Gateway: https://localhost:8443"
    echo "🗄️  База данных: localhost:5432"
    echo "🔍 Qdrant: http://localhost:6333"
    echo "🔴 Redis: localhost:6379"
    echo ""
    echo "📋 Микросервисы:"
    echo "   • Document Parser: http://localhost:8001"
    echo "   • Rule Engine: http://localhost:8002"
    echo "   • RAG Service: http://localhost:8003"
    echo "   • Calculation Service: http://localhost:8004"
    echo "   • VLLM Service: http://localhost:8005"
    echo "   • Outgoing Control: http://localhost:8006"
    echo "   • Spellchecker: http://localhost:8007"
    echo ""
    echo "🔧 Мониторинг (если включен):"
    echo "   • Prometheus: http://localhost:9090"
    echo "   • Grafana: http://localhost:3000"
    echo "   • Keycloak: http://localhost:8081"
    echo ""
    echo "📝 Логи:"
    echo "   docker-compose -f docker-compose.production.yml logs -f"
    echo ""
    echo "🛑 Остановка:"
    echo "   docker-compose -f docker-compose.production.yml down"
}

# Остановка системы
stop_system() {
    log "Остановка AI-NK системы..."
    docker-compose -f docker-compose.production.yml down
    success "Система остановлена"
}

# Очистка системы
cleanup_system() {
    log "Очистка AI-NK системы..."
    docker-compose -f docker-compose.production.yml down -v
    docker system prune -f
    success "Система очищена"
}

# Показать помощь
show_help() {
    echo "Использование: $0 [КОМАНДА]"
    echo ""
    echo "Команды:"
    echo "  build     - Собрать Docker образ"
    echo "  start     - Запустить систему"
    echo "  stop      - Остановить систему"
    echo "  restart   - Перезапустить систему"
    echo "  status    - Показать статус системы"
    echo "  logs      - Показать логи"
    echo "  cleanup   - Очистить систему"
    echo "  deploy    - Полное развертывание (build + start)"
    echo "  help      - Показать эту справку"
    echo ""
    echo "Примеры:"
    echo "  $0 deploy    # Полное развертывание"
    echo "  $0 start     # Только запуск"
    echo "  $0 logs      # Просмотр логов"
}

# Основная логика
main() {
    case "${1:-deploy}" in
        "build")
            check_dependencies
            create_env_file
            build_image
            ;;
        "start")
            check_dependencies
            create_env_file
            start_system
            check_system_health
            show_system_info
            ;;
        "stop")
            stop_system
            ;;
        "restart")
            stop_system
            sleep 5
            start_system
            check_system_health
            show_system_info
            ;;
        "status")
            docker-compose -f docker-compose.production.yml ps
            ;;
        "logs")
            docker-compose -f docker-compose.production.yml logs -f
            ;;
        "cleanup")
            cleanup_system
            ;;
        "deploy")
            check_dependencies
            create_env_file
            build_image
            start_system
            check_system_health
            show_system_info
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            error "Неизвестная команда: $1"
            show_help
            exit 1
            ;;
    esac
}

# Запуск
main "$@"
