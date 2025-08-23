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
        error "Docker не установлен"
        exit 1
    fi
    
    success "Docker найден"
}

# Очистка старых образов
cleanup_old_images() {
    log "🧹 Очистка старых образов..."
    
    # Удаление старых образов AI-NK
    docker images | grep "ai-nk" | awk '{print $3}' | xargs -r docker rmi -f
    
    # Очистка неиспользуемых образов
    docker image prune -f
    
    success "Очистка завершена"
}

# Сборка образа
build_image() {
    local tag=${1:-"latest"}
    local version=${2:-"1.0.0"}
    
    log "🔨 Сборка Docker образа AI-NK v$version..."
    
    # Сборка с тегами
    docker build \
        --tag "ai-nk:$tag" \
        --tag "ai-nk:$version" \
        --tag "ai-nk:latest" \
        --build-arg VERSION=$version \
        --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
        .
    
    if [ $? -eq 0 ]; then
        success "Образ успешно собран"
        success "Теги: ai-nk:$tag, ai-nk:$version, ai-nk:latest"
    else
        error "Ошибка при сборке образа"
        exit 1
    fi
}

# Тестирование образа
test_image() {
    log "🧪 Тестирование образа..."
    
    # Создание временного контейнера для тестирования
    local container_id=$(docker run -d --name ai-nk-test \
        -p 8080:80 \
        -p 8081:8001 \
        -p 8082:8002 \
        -p 8083:8003 \
        -p 8084:8004 \
        ai-nk:latest)
    
    if [ -z "$container_id" ]; then
        error "Не удалось запустить тестовый контейнер"
        exit 1
    fi
    
    log "⏳ Ожидание запуска тестового контейнера..."
    sleep 30
    
    # Проверка здоровья контейнера
    if docker ps | grep -q "ai-nk-test"; then
        success "Тестовый контейнер запущен"
        
        # Проверка доступности сервисов
        local services=("http://localhost:8080" "http://localhost:8084/health")
        local all_healthy=true
        
        for service in "${services[@]}"; do
            if curl -f -s "$service" > /dev/null 2>&1; then
                log "✅ $service доступен"
            else
                log "❌ $service недоступен"
                all_healthy=false
            fi
        done
        
        if [ "$all_healthy" = true ]; then
            success "Все сервисы работают корректно"
        else
            warning "Некоторые сервисы недоступны"
        fi
    else
        error "Тестовый контейнер не запустился"
    fi
    
    # Остановка и удаление тестового контейнера
    log "🛑 Остановка тестового контейнера..."
    docker stop ai-nk-test 2>/dev/null || true
    docker rm ai-nk-test 2>/dev/null || true
}

# Сохранение образа
save_image() {
    local filename=${1:-"ai-nk-image.tar.gz"}
    
    log "💾 Сохранение образа в файл $filename..."
    
    docker save ai-nk:latest | gzip > "$filename"
    
    if [ $? -eq 0 ]; then
        local size=$(du -h "$filename" | cut -f1)
        success "Образ сохранен: $filename ($size)"
    else
        error "Ошибка при сохранении образа"
        exit 1
    fi
}

# Создание README для образа
create_image_readme() {
    local version=${1:-"1.0.0"}
    
    log "📝 Создание README для образа..."
    
    cat > IMAGE_README.md << EOF
# 🐳 AI-NK Docker Image

## 📋 Описание

Готовый Docker образ системы AI-NK для автоматизированной проверки нормативной документации.

**Версия:** $version  
**Размер:** $(docker images ai-nk:latest --format "table {{.Size}}" | tail -n 1)  
**Создан:** $(date)

## 🚀 Быстрый запуск

### Требования
- Docker 20.10+
- 4GB RAM (минимум)
- 10GB свободного места

### Запуск

\`\`\`bash
# Загрузка образа (если скачан как файл)
docker load < ai-nk-image.tar.gz

# Запуск системы
docker run -d \\
  --name ai-nk \\
  -p 80:80 \\
  -p 8001:8001 \\
  -p 8002:8002 \\
  -p 8003:8003 \\
  -p 8004:8004 \\
  -v ai-nk-data:/app/data \\
  -v ai-nk-logs:/app/logs \\
  -v ai-nk-uploads:/app/uploads \\
  ai-nk:latest
\`\`\`

### Проверка работы

\`\`\`bash
# Проверка статуса
docker ps | grep ai-nk

# Проверка здоровья
curl http://localhost/health

# Просмотр логов
docker logs ai-nk
\`\`\`

## 🌐 Доступные сервисы

| Сервис | URL | Описание |
|--------|-----|----------|
| Frontend | http://localhost | Веб-интерфейс |
| API Gateway | http://localhost/api | API системы |
| Document Parser | http://localhost:8001 | Парсинг документов |
| RAG Service | http://localhost:8002 | Векторный поиск |
| Rule Engine | http://localhost:8003 | Проверка норм |

## 📊 Мониторинг

\`\`\`bash
# Логи системы
docker logs ai-nk

# Логи приложения
docker exec ai-nk tail -f /app/logs/*.log

# Статистика контейнера
docker stats ai-nk
\`\`\`

## 🛠️ Управление

\`\`\`bash
# Остановка
docker stop ai-nk

# Перезапуск
docker restart ai-nk

# Удаление
docker rm -f ai-nk
\`\`\`

## 📁 Данные

Образ использует следующие тома:
- \`ai-nk-data\` - База данных PostgreSQL
- \`ai-nk-logs\` - Логи системы
- \`ai-nk-uploads\` - Загруженные документы

## 🔧 Конфигурация

Переменные окружения:
- \`MAX_NORMATIVE_DOCUMENT_SIZE\` - Максимальный размер нормативного документа (по умолчанию: 100MB)
- \`MAX_CHECKABLE_DOCUMENT_SIZE\` - Максимальный размер проверяемого документа (по умолчанию: 100MB)
- \`POSTGRES_PASSWORD\` - Пароль PostgreSQL (по умолчанию: norms_password)

## 🚨 Устранение неполадок

### Проблемы с портами
\`\`\`bash
# Проверка занятых портов
lsof -i :80
lsof -i :8001

# Изменение портов
docker run -p 8080:80 -p 8081:8001 ... ai-nk:latest
\`\`\`

### Проблемы с памятью
\`\`\`bash
# Ограничение памяти
docker run --memory=4g --memory-swap=6g ... ai-nk:latest
\`\`\`

### Сброс данных
\`\`\`bash
# Удаление томов
docker volume rm ai-nk-data ai-nk-logs ai-nk-uploads
\`\`\`

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи: \`docker logs ai-nk\`
2. Убедитесь в достаточности ресурсов
3. Проверьте доступность портов
4. Обратитесь к документации

---

**AI-NK System** - Автоматизированная проверка нормативной документации 🤖
EOF

    success "README создан: IMAGE_README.md"
}

# Главное меню
main_menu() {
    echo
    echo "🔨 AI-NK Image Builder"
    echo "======================"
    echo "1. Полная сборка и тестирование"
    echo "2. Только сборка образа"
    echo "3. Только тестирование"
    echo "4. Сохранить образ в файл"
    echo "5. Очистить старые образы"
    echo "6. Создать README"
    echo "0. Выход"
    echo
    read -p "Выберите действие (0-6): " -n 1 -r
    echo
    
    case $REPLY in
        1)
            check_dependencies
            cleanup_old_images
            build_image
            test_image
            create_image_readme
            ;;
        2)
            check_dependencies
            build_image
            ;;
        3)
            test_image
            ;;
        4)
            read -p "Имя файла (по умолчанию: ai-nk-image.tar.gz): " filename
            save_image "${filename:-ai-nk-image.tar.gz}"
            ;;
        5)
            cleanup_old_images
            ;;
        6)
            read -p "Версия (по умолчанию: 1.0.0): " version
            create_image_readme "${version:-1.0.0}"
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
    --build)
        check_dependencies
        build_image
        ;;
    --test)
        test_image
        ;;
    --save)
        save_image "${2:-ai-nk-image.tar.gz}"
        ;;
    --cleanup)
        cleanup_old_images
        ;;
    --full)
        check_dependencies
        cleanup_old_images
        build_image
        test_image
        create_image_readme
        ;;
    --menu)
        main_menu
        ;;
    *)
        echo "Использование: $0 [опция]"
        echo
        echo "Опции:"
        echo "  --build     Сборка образа"
        echo "  --test      Тестирование образа"
        echo "  --save      Сохранение образа в файл"
        echo "  --cleanup   Очистка старых образов"
        echo "  --full      Полная сборка и тестирование"
        echo "  --menu      Интерактивное меню"
        echo
        echo "Примеры:"
        echo "  $0 --full                    # Полная сборка"
        echo "  $0 --save my-image.tar.gz    # Сохранение с именем"
        echo "  $0 --menu                    # Интерактивное меню"
        ;;
esac
