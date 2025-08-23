#!/bin/bash

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для логирования
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ОШИБКА]${NC} $1"
}

success() {
    echo -e "${GREEN}[УСПЕХ]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[ПРЕДУПРЕЖДЕНИЕ]${NC} $1"
}

# Проверка зависимостей
check_dependencies() {
    log "🔍 Проверка зависимостей..."
    
    if ! command -v docker &> /dev/null; then
        error "Docker не установлен. Установите Docker и попробуйте снова."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose не установлен. Установите Docker Compose и попробуйте снова."
        exit 1
    fi
    
    success "Все зависимости установлены"
}

# Проверка портов
check_ports() {
    log "🔍 Проверка доступности портов..."
    
    local ports=(80 443 8001 8002 8003 8004)
    local occupied_ports=()
    
    for port in "${ports[@]}"; do
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            occupied_ports+=($port)
        fi
    done
    
    if [ ${#occupied_ports[@]} -ne 0 ]; then
        warning "Следующие порты уже заняты: ${occupied_ports[*]}"
        read -p "Продолжить развертывание? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log "Развертывание отменено"
            exit 0
        fi
    fi
    
    success "Порты свободны"
}

# Сборка образа
build_image() {
    log "🔨 Сборка Docker образа..."
    
    if docker build -t ai-nk:latest .; then
        success "Образ успешно собран"
    else
        error "Ошибка при сборке образа"
        exit 1
    fi
}

# Запуск системы
start_system() {
    log "🚀 Запуск AI-NK системы..."
    
    if docker-compose -f docker-compose.prod.yaml up -d; then
        success "Система запущена"
    else
        error "Ошибка при запуске системы"
        exit 1
    fi
}

# Проверка здоровья системы
check_health() {
    log "🏥 Проверка здоровья системы..."
    
    local max_attempts=60
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s "http://localhost/health" > /dev/null 2>&1; then
            success "Система готова к работе!"
            return 0
        fi
        
        log "⏳ Попытка $attempt/$max_attempts..."
        sleep 5
        ((attempt++))
    done
    
    error "Система не готова после $max_attempts попыток"
    return 1
}

# Показать информацию о системе
show_info() {
    log "📊 Информация о системе:"
    echo
    echo "🌐 Доступные сервисы:"
    echo "   - Frontend: http://localhost"
    echo "   - API Gateway: http://localhost/api"
    echo "   - Document Parser: http://localhost:8001"
    echo "   - RAG Service: http://localhost:8002"
    echo "   - Rule Engine: http://localhost:8003"
    echo
    echo "📁 Логи системы:"
    echo "   - Основные логи: docker logs ai-nk-system"
    echo "   - Логи приложения: docker exec ai-nk-system tail -f /app/logs/*.log"
    echo
    echo "🛠️ Управление системой:"
    echo "   - Остановка: docker-compose -f docker-compose.prod.yaml down"
    echo "   - Перезапуск: docker-compose -f docker-compose.prod.yaml restart"
    echo "   - Обновление: ./deploy.sh --update"
    echo
}

# Обновление системы
update_system() {
    log "🔄 Обновление системы..."
    
    # Остановка текущей системы
    docker-compose -f docker-compose.prod.yaml down
    
    # Удаление старого образа
    docker rmi ai-nk:latest 2>/dev/null || true
    
    # Сборка нового образа
    build_image
    
    # Запуск обновленной системы
    start_system
    
    # Проверка здоровья
    check_health
    
    success "Система успешно обновлена"
}

# Остановка системы
stop_system() {
    log "🛑 Остановка системы..."
    
    if docker-compose -f docker-compose.prod.yaml down; then
        success "Система остановлена"
    else
        error "Ошибка при остановке системы"
        exit 1
    fi
}

# Очистка системы
clean_system() {
    log "🧹 Очистка системы..."
    
    # Остановка системы
    docker-compose -f docker-compose.prod.yaml down
    
    # Удаление образов
    docker rmi ai-nk:latest 2>/dev/null || true
    
    # Удаление томов
    read -p "Удалить все данные системы? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker volume rm ai-nk_ai-nk-data ai-nk_ai-nk-logs ai-nk_ai-nk-uploads 2>/dev/null || true
        success "Все данные удалены"
    fi
    
    success "Система очищена"
}

# Главное меню
main_menu() {
    echo
    echo "🤖 AI-NK Система развертывания"
    echo "================================"
    echo "1. Полное развертывание"
    echo "2. Только сборка образа"
    echo "3. Только запуск системы"
    echo "4. Проверить здоровье"
    echo "5. Обновить систему"
    echo "6. Остановить систему"
    echo "7. Очистить систему"
    echo "8. Показать информацию"
    echo "0. Выход"
    echo
    read -p "Выберите действие (0-8): " -n 1 -r
    echo
    
    case $REPLY in
        1)
            check_dependencies
            check_ports
            build_image
            start_system
            check_health
            show_info
            ;;
        2)
            build_image
            ;;
        3)
            start_system
            check_health
            ;;
        4)
            check_health
            ;;
        5)
            update_system
            ;;
        6)
            stop_system
            ;;
        7)
            clean_system
            ;;
        8)
            show_info
            ;;
        0)
            log "До свидания!"
            exit 0
            ;;
        *)
            error "Неверный выбор"
            main_menu
            ;;
    esac
}

# Обработка аргументов командной строки
case "${1:-}" in
    --deploy)
        check_dependencies
        check_ports
        build_image
        start_system
        check_health
        show_info
        ;;
    --build)
        build_image
        ;;
    --start)
        start_system
        check_health
        ;;
    --stop)
        stop_system
        ;;
    --update)
        update_system
        ;;
    --clean)
        clean_system
        ;;
    --health)
        check_health
        ;;
    --info)
        show_info
        ;;
    --menu)
        main_menu
        ;;
    *)
        echo "Использование: $0 [опция]"
        echo
        echo "Опции:"
        echo "  --deploy    Полное развертывание"
        echo "  --build     Только сборка образа"
        echo "  --start     Только запуск системы"
        echo "  --stop      Остановка системы"
        echo "  --update    Обновление системы"
        echo "  --clean     Очистка системы"
        echo "  --health    Проверка здоровья"
        echo "  --info      Показать информацию"
        echo "  --menu      Интерактивное меню"
        echo
        echo "Примеры:"
        echo "  $0 --deploy    # Полное развертывание"
        echo "  $0 --menu      # Интерактивное меню"
        ;;
esac
