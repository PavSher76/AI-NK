#!/bin/bash

# Быстрое развертывание AI-NK на новом хосте
# Совместимо с Docker 27.1.2-qnap4 (QNAP NAS)
set -e

echo "🚀 Быстрое развертывание AI-NK системы"
echo "======================================"
echo "🐳 Целевая платформа: QNAP NAS (Docker 27.1.2-qnap4)"
echo ""

# Проверка Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен. Установите Docker и повторите попытку."
    exit 1
fi

# Проверка версии Docker
DOCKER_VERSION=$(docker --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
echo "🔍 Обнаружена версия Docker: $DOCKER_VERSION"

# Проверка Docker Compose (может быть встроен в Docker)
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
    echo "✅ Docker Compose найден (standalone)"
elif docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
    echo "✅ Docker Compose найден (встроенный в Docker)"
else
    echo "❌ Docker Compose не найден. Установите Docker Compose или обновите Docker."
    exit 1
fi

echo "✅ Docker и Docker Compose готовы к работе"

# Создание .env файла с оптимизацией для QNAP
if [ ! -f .env ]; then
    echo "📝 Создание конфигурационного файла .env для QNAP..."
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
JWT_SECRET_KEY=ai-nk-secret-key-$(date +%s)
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# File Upload Limits (оптимизировано для QNAP)
MAX_FILE_SIZE=52428800
MAX_CHECKABLE_DOCUMENT_SIZE=52428800
MAX_NORMATIVE_DOCUMENT_SIZE=104857600

# Timeouts (увеличены для QNAP)
LLM_REQUEST_TIMEOUT=180
PAGE_PROCESSING_TIMEOUT=600

# Logging
LOG_LEVEL=INFO
TZ=Europe/Moscow

# QNAP специфичные настройки
DOCKER_ENV=true
QNAP_OPTIMIZED=true

# Keycloak (опционально)
KEYCLOAK_ADMIN=admin
KEYCLOAK_ADMIN_PASSWORD=admin
KEYCLOAK_PORT=8081

# Monitoring (опционально)
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
GRAFANA_ADMIN_PASSWORD=admin

# Внешние сервисы (для QNAP)
OLLAMA_BASE_URL=http://host.docker.internal:11434
EOF
    echo "✅ Файл .env создан с оптимизацией для QNAP"
else
    echo "ℹ️  Файл .env уже существует"
fi

# Установка прав доступа
echo "🔧 Настройка прав доступа..."
chmod +x build-and-deploy.sh scripts/start.sh scripts/init.sh 2>/dev/null || true

# Проверка доступного места на диске (важно для QNAP)
echo "💾 Проверка доступного места на диске..."
AVAILABLE_SPACE=$(df -h . | awk 'NR==2 {print $4}' | sed 's/[^0-9]//g')
if [ "$AVAILABLE_SPACE" -lt 10 ]; then
    echo "⚠️  Внимание: Мало свободного места на диске (< 10GB)"
    echo "   Рекомендуется освободить место перед развертыванием"
    read -p "Продолжить? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Развертывание отменено"
        exit 1
    fi
fi

# Сборка и запуск
echo "🏗️  Сборка и запуск системы для QNAP..."
echo "Это может занять несколько минут на QNAP..."

# Остановка существующих контейнеров
echo "🛑 Остановка существующих контейнеров..."
$COMPOSE_CMD -f docker-compose.production.yml down 2>/dev/null || true

# Очистка неиспользуемых образов (важно для QNAP)
echo "🧹 Очистка неиспользуемых Docker ресурсов..."
docker system prune -f 2>/dev/null || true

# Сборка образа с оптимизацией для QNAP
echo "📦 Сборка Docker образа для QNAP..."
echo "   Используется многоэтапная сборка для экономии места"
docker build -f Dockerfile.production -t ai-nk:latest . --no-cache

if [ $? -ne 0 ]; then
    echo "❌ Ошибка при сборке образа"
    echo "💡 Попробуйте освободить место на диске и повторить"
    exit 1
fi

# Запуск системы
echo "🚀 Запуск системы на QNAP..."
$COMPOSE_CMD -f docker-compose.production.yml up -d

if [ $? -ne 0 ]; then
    echo "❌ Ошибка при запуске системы"
    echo "💡 Проверьте логи: $COMPOSE_CMD -f docker-compose.production.yml logs"
    exit 1
fi

# Ожидание запуска (увеличено для QNAP)
echo "⏳ Ожидание запуска сервисов на QNAP..."
echo "   QNAP может потребовать больше времени для запуска"
sleep 60

# Проверка состояния
echo "🔍 Проверка состояния системы..."

# Проверка основных сервисов
services=("ai-nk" "norms-db" "qdrant" "redis")
all_healthy=true

for service in "${services[@]}"; do
    if $COMPOSE_CMD -f docker-compose.production.yml ps | grep -q "$service.*Up"; then
        echo "✅ Сервис $service запущен"
    else
        echo "❌ Сервис $service не запущен"
        all_healthy=false
    fi
done

# Дополнительная проверка для QNAP
echo "🔍 Дополнительная диагностика для QNAP..."

# Проверка использования ресурсов
echo "📊 Использование ресурсов:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" 2>/dev/null || echo "   Статистика недоступна"

# Проверка веб-интерфейса
echo "🌐 Проверка веб-интерфейса..."
if curl -f http://localhost/health >/dev/null 2>&1; then
    echo "✅ Веб-интерфейс доступен"
elif curl -f http://127.0.0.1/health >/dev/null 2>&1; then
    echo "✅ Веб-интерфейс доступен (127.0.0.1)"
else
    echo "⚠️  Веб-интерфейс пока недоступен (возможно, сервисы еще запускаются)"
    echo "💡 Попробуйте через несколько минут или проверьте логи"
fi

echo ""
echo "🎉 Развертывание на QNAP завершено!"
echo "=================================="
echo ""
echo "🌐 Веб-интерфейс: http://localhost"
echo "🔒 HTTPS: https://localhost"
echo "📊 API: https://localhost:8443"
echo ""
echo "📋 Управление системой на QNAP:"
echo "  Статус:     $COMPOSE_CMD -f docker-compose.production.yml ps"
echo "  Логи:       $COMPOSE_CMD -f docker-compose.production.yml logs -f"
echo "  Остановка:  $COMPOSE_CMD -f docker-compose.production.yml down"
echo "  Перезапуск: ./build-and-deploy.sh restart"
echo ""
echo "🔧 QNAP специфичные команды:"
echo "  Мониторинг: docker stats"
echo "  Очистка:    docker system prune -a"
echo "  Образы:     docker images"
echo ""
echo "📖 Подробная документация: DEPLOYMENT_GUIDE.md"
echo ""

if [ "$all_healthy" = true ]; then
    echo "✅ Все сервисы работают корректно на QNAP!"
    echo "🚀 Система готова к использованию!"
    echo ""
    echo "💡 Рекомендации для QNAP:"
    echo "   • Регулярно очищайте неиспользуемые образы"
    echo "   • Мониторьте использование дискового пространства"
    echo "   • Используйте SSD для лучшей производительности"
else
    echo "⚠️  Некоторые сервисы могут иметь проблемы"
    echo "📋 Проверьте логи: $COMPOSE_CMD -f docker-compose.production.yml logs"
    echo ""
    echo "🔧 Устранение неполадок на QNAP:"
    echo "   • Проверьте доступное место на диске"
    echo "   • Убедитесь, что порты не заняты другими сервисами"
    echo "   • Проверьте права доступа к папкам"
fi
