#!/bin/bash

# Быстрое развертывание AI-NK на новом хосте
set -e

echo "🚀 Быстрое развертывание AI-NK системы"
echo "======================================"

# Проверка Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен. Установите Docker и повторите попытку."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose не установлен. Установите Docker Compose и повторите попытку."
    exit 1
fi

echo "✅ Docker и Docker Compose установлены"

# Создание .env файла
if [ ! -f .env ]; then
    echo "📝 Создание конфигурационного файла .env..."
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
    echo "✅ Файл .env создан"
else
    echo "ℹ️  Файл .env уже существует"
fi

# Установка прав доступа
echo "🔧 Настройка прав доступа..."
chmod +x build-and-deploy.sh scripts/start.sh scripts/init.sh 2>/dev/null || true

# Сборка и запуск
echo "🏗️  Сборка и запуск системы..."
echo "Это может занять несколько минут..."

# Остановка существующих контейнеров
docker-compose -f docker-compose.production.yml down 2>/dev/null || true

# Сборка образа
echo "📦 Сборка Docker образа..."
docker build -f Dockerfile.production -t ai-nk:latest .

if [ $? -ne 0 ]; then
    echo "❌ Ошибка при сборке образа"
    exit 1
fi

# Запуск системы
echo "🚀 Запуск системы..."
docker-compose -f docker-compose.production.yml up -d

if [ $? -ne 0 ]; then
    echo "❌ Ошибка при запуске системы"
    exit 1
fi

# Ожидание запуска
echo "⏳ Ожидание запуска сервисов..."
sleep 30

# Проверка состояния
echo "🔍 Проверка состояния системы..."

# Проверка основных сервисов
services=("ai-nk" "norms-db" "qdrant" "redis")
all_healthy=true

for service in "${services[@]}"; do
    if docker-compose -f docker-compose.production.yml ps | grep -q "$service.*Up"; then
        echo "✅ Сервис $service запущен"
    else
        echo "❌ Сервис $service не запущен"
        all_healthy=false
    fi
done

# Проверка веб-интерфейса
echo "🌐 Проверка веб-интерфейса..."
if curl -f http://localhost/health >/dev/null 2>&1; then
    echo "✅ Веб-интерфейс доступен"
else
    echo "⚠️  Веб-интерфейс пока недоступен (возможно, сервисы еще запускаются)"
fi

echo ""
echo "🎉 Развертывание завершено!"
echo "=========================="
echo ""
echo "🌐 Веб-интерфейс: http://localhost"
echo "🔒 HTTPS: https://localhost"
echo "📊 API: https://localhost:8443"
echo ""
echo "📋 Управление системой:"
echo "  Статус:     docker-compose -f docker-compose.production.yml ps"
echo "  Логи:       docker-compose -f docker-compose.production.yml logs -f"
echo "  Остановка:  docker-compose -f docker-compose.production.yml down"
echo "  Перезапуск: ./build-and-deploy.sh restart"
echo ""
echo "📖 Подробная документация: DEPLOYMENT_GUIDE.md"
echo ""

if [ "$all_healthy" = true ]; then
    echo "✅ Все сервисы работают корректно!"
    echo "🚀 Система готова к использованию!"
else
    echo "⚠️  Некоторые сервисы могут иметь проблемы"
    echo "📋 Проверьте логи: docker-compose -f docker-compose.production.yml logs"
fi
