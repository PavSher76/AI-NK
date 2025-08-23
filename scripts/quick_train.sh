#!/bin/bash

# 🎓 Быстрый запуск обучения системы AI-NK
# Автор: AI Assistant
# Версия: 1.0.0

set -e  # Остановка при ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции для вывода
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_header() {
    echo -e "${BLUE}"
    echo "🎓 Система обучения AI-NK"
    echo "================================"
    echo -e "${NC}"
}

# Проверка зависимостей
check_dependencies() {
    print_info "Проверка зависимостей..."
    
    # Проверка Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 не установлен"
        exit 1
    fi
    
    # Проверка Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker не установлен"
        exit 1
    fi
    
    # Проверка Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose не установлен"
        exit 1
    fi
    
    print_success "Все зависимости установлены"
}

# Проверка состояния системы
check_system_status() {
    print_info "Проверка состояния системы AI-NK..."
    
    # Проверка контейнеров
    if ! docker-compose ps | grep -q "Up"; then
        print_warning "Система не запущена. Запускаем..."
        docker-compose up -d
        sleep 30  # Ждем запуска
    fi
    
    # Проверка доступности API
    if curl -k -s "https://localhost/api/health" > /dev/null; then
        print_success "Система работает"
    else
        print_error "Система недоступна"
        exit 1
    fi
}

# Создание структуры папок
create_folder_structure() {
    print_info "Создание структуры папок для обучения..."
    
    mkdir -p TestDocs/for_check/{Правильные,С_ошибками,Пограничные}
    mkdir -p TestDocs/Norms/{ГОСТ,СП,СНиП,Ведомственные}
    mkdir -p scripts/results
    
    print_success "Структура папок создана"
}

# Установка зависимостей Python
install_python_deps() {
    print_info "Установка зависимостей Python..."
    
    # Проверка существования виртуального окружения
    if [ ! -d "training_env" ]; then
        print_info "Создание виртуального окружения..."
        python3 -m venv training_env
    fi
    
    # Активация виртуального окружения и установка зависимостей
    source training_env/bin/activate && pip install requests psycopg2-binary > /dev/null 2>&1 || {
        print_warning "Не удалось установить зависимости"
        print_info "Попробуйте установить вручную: source training_env/bin/activate && pip install requests psycopg2-binary"
    }
    
    print_success "Зависимости Python установлены в виртуальном окружении"
}

# Запуск обучения
run_training() {
    print_info "Запуск процесса обучения..."
    
    cd scripts
    
    if [ -f "train_system.py" ]; then
        # Активация виртуального окружения и запуск скрипта
        source ../training_env/bin/activate && python3 train_system.py
    else
        print_error "Скрипт обучения не найден: scripts/train_system.py"
        exit 1
    fi
    
    cd ..
}

# Анализ результатов
analyze_results() {
    print_info "Анализ результатов обучения..."
    
    if [ -f "scripts/training_results.json" ]; then
        echo "📊 Результаты обучения:"
        echo "========================"
        
        # Извлекаем основные метрики
        f1_score=$(source training_env/bin/activate && python3 -c "
import json
with open('scripts/training_results.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    metrics = data.get('overall_metrics', {})
    print(f\"F1-Score: {metrics.get('f1_score', 0):.3f}\")
    print(f\"Precision: {metrics.get('precision', 0):.3f}\")
    print(f\"Recall: {metrics.get('recall', 0):.3f}\")
    print(f\"Тестов: {metrics.get('successful_tests', 0)}/{metrics.get('total_tests', 0)}\")
")
        echo "$f1_score"
        
        # Рекомендации
        f1_value=$(source training_env/bin/activate && python3 -c "
import json
with open('scripts/training_results.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    metrics = data.get('overall_metrics', {})
    print(metrics.get('f1_score', 0))
")
        
        if (( $(echo "$f1_value >= 0.9" | bc -l) )); then
            print_success "Отличные результаты! Система готова к продакшену."
        elif (( $(echo "$f1_value >= 0.8" | bc -l) )); then
            print_warning "Хорошие результаты. Рекомендуется дополнительная настройка."
        elif (( $(echo "$f1_value >= 0.7" | bc -l) )); then
            print_warning "Средние результаты. Требуется значительная доработка промптов."
        else
            print_error "Низкие результаты. Необходима серьезная переработка системы."
        fi
        
    else
        print_warning "Файл результатов не найден"
    fi
}

# Показ справки
show_help() {
    echo "Использование: $0 [опции]"
    echo ""
    echo "Опции:"
    echo "  -h, --help     Показать эту справку"
    echo "  -s, --setup    Только настройка окружения"
    echo "  -t, --train    Только запуск обучения"
    echo "  -a, --analyze  Только анализ результатов"
    echo ""
    echo "Примеры:"
    echo "  $0              # Полный процесс обучения"
    echo "  $0 --setup      # Только настройка"
    echo "  $0 --train      # Только обучение"
}

# Основная функция
main() {
    print_header
    
    # Парсинг аргументов
    case "${1:-}" in
        -h|--help)
            show_help
            exit 0
            ;;
        -s|--setup)
            print_info "Режим: только настройка"
            check_dependencies
            check_system_status
            create_folder_structure
            install_python_deps
            print_success "Настройка завершена"
            exit 0
            ;;
        -t|--train)
            print_info "Режим: только обучение"
            run_training
            exit 0
            ;;
        -a|--analyze)
            print_info "Режим: только анализ"
            analyze_results
            exit 0
            ;;
        "")
            # Полный процесс
            ;;
        *)
            print_error "Неизвестная опция: $1"
            show_help
            exit 1
            ;;
    esac
    
    # Полный процесс обучения
    print_info "Запуск полного процесса обучения..."
    
    check_dependencies
    check_system_status
    create_folder_structure
    install_python_deps
    run_training
    analyze_results
    
    print_success "Обучение завершено!"
    echo ""
    echo "📁 Результаты сохранены в:"
    echo "  - scripts/training_results.json"
    echo "  - scripts/training.log"
    echo ""
    echo "📚 Дополнительная информация:"
    echo "  - TRAINING_GUIDE.md - подробная инструкция"
    echo "  - https://localhost - веб-интерфейс системы"
}

# Запуск основной функции
main "$@"
