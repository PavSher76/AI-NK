#!/bin/bash

# Специализированный скрипт развертывания для QNAP NAS
# Оптимизирован для Docker 27.1.2-qnap4
set -e

echo "🏠 Развертывание AI-NK на QNAP NAS"
echo "=================================="
echo "🐳 Docker версия: 27.1.2-qnap4"
echo ""

# Проверка QNAP окружения
check_qnap_environment() {
    echo "🔍 Проверка QNAP окружения..."
    
    # Проверка Docker
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker не найден. Установите Container Station на QNAP."
        exit 1
    fi
    
    # Проверка версии Docker
    DOCKER_VERSION=$(docker --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
    echo "✅ Docker версия: $DOCKER_VERSION"
    
    # Проверка Docker Compose
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
        echo "✅ Docker Compose: standalone"
    elif docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
        echo "✅ Docker Compose: встроенный"
    else
        echo "❌ Docker Compose не найден"
        exit 1
    fi
    
    # Проверка доступного места
    echo "💾 Проверка дискового пространства..."
    AVAILABLE_SPACE=$(df -h . | awk 'NR==2 {print $4}' | sed 's/[^0-9]//g')
    if [ "$AVAILABLE_SPACE" -lt 20 ]; then
        echo "⚠️  Мало свободного места: ${AVAILABLE_SPACE}GB"
        echo "   Рекомендуется минимум 20GB для стабильной работы"
        read -p "Продолжить? [y/N] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        echo "✅ Достаточно места: ${AVAILABLE_SPACE}GB"
    fi
}

# Создание оптимизированной конфигурации для QNAP
create_qnap_config() {
    echo "⚙️  Создание конфигурации для QNAP..."
    
    # Создание .env файла
    cat > .env << 'EOF'
# QNAP Optimized Configuration
# ===========================

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
JWT_SECRET_KEY=ai-nk-qnap-$(date +%s)
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# QNAP Optimized Limits
MAX_FILE_SIZE=26214400
MAX_CHECKABLE_DOCUMENT_SIZE=26214400
MAX_NORMATIVE_DOCUMENT_SIZE=52428800

# Extended Timeouts for QNAP
LLM_REQUEST_TIMEOUT=300
PAGE_PROCESSING_TIMEOUT=900

# Logging
LOG_LEVEL=INFO
TZ=Europe/Moscow

# QNAP Specific
DOCKER_ENV=true
QNAP_OPTIMIZED=true
QNAP_NAS=true

# External Services
OLLAMA_BASE_URL=http://host.docker.internal:11434

# Monitoring (optional)
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
GRAFANA_ADMIN_PASSWORD=admin
EOF

    # Создание docker-compose.qnap.yml
    cat > docker-compose.qnap.yml << 'EOF'
version: '3.8'

services:
  # Основной сервис AI-NK (оптимизирован для QNAP)
  ai-nk:
    build:
      context: .
      dockerfile: Dockerfile.production
    container_name: ai-nk-qnap
    ports:
      - "80:80"
      - "443:443"
      - "8001:8001"
      - "8002:8002"
      - "8003:8003"
      - "8004:8004"
      - "8005:8005"
      - "8006:8006"
      - "8007:8007"
      - "8443:8443"
    volumes:
      - ai-nk-data:/app/data
      - ai-nk-logs:/app/logs
      - ai-nk-uploads:/app/uploads
      - ai-nk-reports:/app/reports
      - ai-nk-models:/app/models
    environment:
      - POSTGRES_HOST=norms-db
      - POSTGRES_PORT=5432
      - POSTGRES_DB=norms_db
      - POSTGRES_USER=norms_user
      - POSTGRES_PASSWORD=norms_password
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - REDIS_PASSWORD=redispass
      - QDRANT_HOST=qdrant
      - QDRANT_PORT=6333
      - QNAP_OPTIMIZED=true
      - TZ=Europe/Moscow
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2.0'
        reservations:
          memory: 2G
          cpus: '1.0'
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/health"]
      interval: 60s
      timeout: 30s
      retries: 3
      start_period: 120s
    networks:
      - ai-nk-network

  # PostgreSQL (оптимизирован для QNAP)
  norms-db:
    image: pgvector/pgvector:pg15
    container_name: ai-nk-norms-db-qnap
    environment:
      POSTGRES_DB: norms_db
      POSTGRES_USER: norms_user
      POSTGRES_PASSWORD: norms_password
      POSTGRES_INITDB_ARGS: "--encoding=UTF-8 --lc-collate=C --lc-ctype=C"
      TZ: Europe/Moscow
    ports:
      - "5432:5432"
    volumes:
      - norms_db_data:/var/lib/postgresql/data
      - ./sql:/docker-entrypoint-initdb.d:ro
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
        reservations:
          memory: 1G
          cpus: '0.5'
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U norms_user -d norms_db"]
      interval: 60s
      timeout: 30s
      retries: 3
    networks:
      - ai-nk-network

  # Qdrant (оптимизирован для QNAP)
  qdrant:
    image: qdrant/qdrant:latest
    container_name: ai-nk-qdrant-qnap
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_data:/qdrant/storage
    environment:
      - TZ=Europe/Moscow
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
        reservations:
          memory: 1G
          cpus: '0.5'
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:6333/health"]
      interval: 60s
      timeout: 30s
      retries: 3
    networks:
      - ai-nk-network

  # Redis (оптимизирован для QNAP)
  redis:
    image: redis:7-alpine
    container_name: ai-nk-redis-qnap
    command: redis-server --requirepass redispass --maxmemory 512mb --maxmemory-policy allkeys-lru
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    environment:
      - TZ=Europe/Moscow
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
        reservations:
          memory: 512M
          cpus: '0.25'
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 60s
      timeout: 30s
      retries: 3
    networks:
      - ai-nk-network

volumes:
  ai-nk-data:
    driver: local
  ai-nk-logs:
    driver: local
  ai-nk-uploads:
    driver: local
  ai-nk-reports:
    driver: local
  ai-nk-models:
    driver: local
  norms_db_data:
    driver: local
  qdrant_data:
    driver: local
  redis_data:
    driver: local

networks:
  ai-nk-network:
    driver: bridge
    name: ai-nk-qnap-network
EOF

    echo "✅ Конфигурация для QNAP создана"
}

# Оптимизация системы для QNAP
optimize_for_qnap() {
    echo "🔧 Оптимизация системы для QNAP..."
    
    # Очистка системы
    echo "🧹 Очистка Docker системы..."
    docker system prune -a -f 2>/dev/null || true
    
    # Настройка лимитов
    echo "⚙️  Настройка лимитов ресурсов..."
    
    # Создание директорий с правильными правами
    mkdir -p uploads temp logs data reports models
    chmod 755 uploads temp logs data reports models
    
    echo "✅ Оптимизация завершена"
}

# Развертывание на QNAP
deploy_to_qnap() {
    echo "🚀 Развертывание на QNAP..."
    
    # Остановка существующих контейнеров
    echo "🛑 Остановка существующих контейнеров..."
    $COMPOSE_CMD -f docker-compose.qnap.yml down 2>/dev/null || true
    
    # Сборка образа
    echo "📦 Сборка образа для QNAP..."
    docker build -f Dockerfile.production -t ai-nk:qnap . --no-cache
    
    if [ $? -ne 0 ]; then
        echo "❌ Ошибка сборки образа"
        exit 1
    fi
    
    # Запуск системы
    echo "🚀 Запуск системы на QNAP..."
    $COMPOSE_CMD -f docker-compose.qnap.yml up -d
    
    if [ $? -ne 0 ]; then
        echo "❌ Ошибка запуска системы"
        exit 1
    fi
    
    echo "✅ Развертывание завершено"
}

# Проверка состояния
check_status() {
    echo "🔍 Проверка состояния системы..."
    
    # Ожидание запуска
    echo "⏳ Ожидание запуска сервисов (QNAP может потребовать больше времени)..."
    sleep 90
    
    # Проверка сервисов
    services=("ai-nk-qnap" "ai-nk-norms-db-qnap" "ai-nk-qdrant-qnap" "ai-nk-redis-qnap")
    all_healthy=true
    
    for service in "${services[@]}"; do
        if docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "$service.*Up"; then
            echo "✅ $service запущен"
        else
            echo "❌ $service не запущен"
            all_healthy=false
        fi
    done
    
    # Проверка веб-интерфейса
    echo "🌐 Проверка веб-интерфейса..."
    if curl -f http://localhost/health >/dev/null 2>&1; then
        echo "✅ Веб-интерфейс доступен"
    else
        echo "⚠️  Веб-интерфейс пока недоступен"
    fi
    
    # Статистика ресурсов
    echo "📊 Использование ресурсов:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" 2>/dev/null || echo "   Статистика недоступна"
    
    return $all_healthy
}

# Основная функция
main() {
    check_qnap_environment
    create_qnap_config
    optimize_for_qnap
    deploy_to_qnap
    
    if check_status; then
        echo ""
        echo "🎉 AI-NK успешно развернут на QNAP!"
        echo "=================================="
        echo ""
        echo "🌐 Веб-интерфейс: http://localhost"
        echo "📊 API: https://localhost:8443"
        echo ""
        echo "📋 Управление:"
        echo "  Статус: $COMPOSE_CMD -f docker-compose.qnap.yml ps"
        echo "  Логи:   $COMPOSE_CMD -f docker-compose.qnap.yml logs -f"
        echo "  Стоп:   $COMPOSE_CMD -f docker-compose.qnap.yml down"
        echo ""
        echo "💡 Рекомендации для QNAP:"
        echo "  • Регулярно очищайте: docker system prune -a"
        echo "  • Мониторьте место: df -h"
        echo "  • Используйте SSD для лучшей производительности"
    else
        echo ""
        echo "⚠️  Некоторые сервисы имеют проблемы"
        echo "📋 Проверьте логи: $COMPOSE_CMD -f docker-compose.qnap.yml logs"
    fi
}

# Запуск
main "$@"
