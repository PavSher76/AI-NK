#!/bin/bash

# AI-НК - Быстрое развертывание
# Для тестирования и разработки

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Проверка Docker
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker не установлен"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose не установлен"
        exit 1
    fi
}

# Создание минимальной конфигурации
create_minimal_config() {
    log_info "Создание минимальной конфигурации..."
    
    # Создание .env файла
    cat > .env << EOF
# AI-НК - Минимальная конфигурация для быстрого развертывания
PROJECT_NAME=AI-НК
ENVIRONMENT=development
DEBUG=true

# База данных
POSTGRES_DB=norms_db
POSTGRES_USER=norms_user
POSTGRES_PASSWORD=dev_password
POSTGRES_HOST=norms-db
POSTGRES_PORT=5432

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=dev_password

# Qdrant
QDRANT_HOST=qdrant
QDRANT_PORT=6333

# Keycloak
KEYCLOAK_ADMIN_USER=admin
KEYCLOAK_ADMIN_PASSWORD=admin
KEYCLOAK_DB_PASSWORD=keycloak_password

# JWT
JWT_SECRET_KEY=dev_secret_key_32_chars_long_for_development
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Сервисы
GATEWAY_HOST=localhost
GATEWAY_PORT=80
CALCULATION_SERVICE_PORT=8002
RAG_SERVICE_PORT=8003
CHAT_SERVICE_PORT=8004
DOCUMENT_PARSER_PORT=8005
VLLM_SERVICE_PORT=8006
FRONTEND_PORT=3000

# SSL (отключено для разработки)
SSL_ENABLED=false

# Логирование
LOG_LEVEL=DEBUG
LOG_FORMAT=text

# CORS
CORS_ORIGINS=["http://localhost:3000", "https://localhost"]

# Файлы
MAX_FILE_SIZE=100MB
ALLOWED_FILE_TYPES=["pdf", "doc", "docx", "txt", "rtf"]

# AI модели
DEFAULT_MODEL=gpt-3.5-turbo
MODEL_TEMPERATURE=0.7
MAX_TOKENS=4000
EOF

    log_success "Конфигурация создана"
}

# Создание docker-compose для быстрого развертывания
create_quick_compose() {
    log_info "Создание docker-compose для быстрого развертывания..."
    
    cat > docker-compose.quick.yaml << 'EOF'
version: '3.8'

services:
  # База данных PostgreSQL
  norms-db:
    image: postgres:15-alpine
    container_name: ai-nk-norms-db
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - norms_db_data:/var/lib/postgresql/data
      - ./sql:/docker-entrypoint-initdb.d
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis
  redis:
    image: redis:7-alpine
    container_name: ai-nk-redis
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Qdrant
  qdrant:
    image: qdrant/qdrant:latest
    container_name: ai-nk-qdrant
    volumes:
      - qdrant_data:/qdrant/storage
    ports:
      - "6333:6333"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:6333/health"]
      interval: 10s
      timeout: 5s
      retries: 5

  # API Gateway
  gateway:
    build:
      context: ./gateway
      dockerfile: Dockerfile
    container_name: ai-nk-gateway
    environment:
      - POSTGRES_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@norms-db:5432/${POSTGRES_DB}
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - CORS_ORIGINS=${CORS_ORIGINS}
    ports:
      - "80:80"
    depends_on:
      norms-db:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Сервис расчетов
  calculation-service:
    build:
      context: ./calculation_service
      dockerfile: Dockerfile
    container_name: ai-nk-calculation-service
    environment:
      - POSTGRES_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@norms-db:5432/${POSTGRES_DB}
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379
      - QDRANT_URL=http://qdrant:6333
    ports:
      - "8002:8002"
    depends_on:
      norms-db:
        condition: service_healthy
      redis:
        condition: service_healthy
      qdrant:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8002/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # RAG сервис
  rag-service:
    build:
      context: ./rag_service
      dockerfile: Dockerfile
    container_name: ai-nk-rag-service
    environment:
      - POSTGRES_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@norms-db:5432/${POSTGRES_DB}
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379
      - QDRANT_URL=http://qdrant:6333
    ports:
      - "8003:8003"
    depends_on:
      norms-db:
        condition: service_healthy
      redis:
        condition: service_healthy
      qdrant:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8003/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Чат сервис
  chat-service:
    build:
      context: ./chat_service
      dockerfile: Dockerfile
    container_name: ai-nk-chat-service
    environment:
      - POSTGRES_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@norms-db:5432/${POSTGRES_DB}
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379
      - OPENAI_API_KEY=${OPENAI_API_KEY:-}
    ports:
      - "8004:8004"
    depends_on:
      norms-db:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8004/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Парсер документов
  document-parser:
    build:
      context: ./document_parser
      dockerfile: Dockerfile
    container_name: ai-nk-document-parser
    environment:
      - POSTGRES_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@norms-db:5432/${POSTGRES_DB}
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379
    ports:
      - "8005:8005"
    depends_on:
      norms-db:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8005/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # VLLM сервис
  vllm-service:
    build:
      context: ./vllm_service
      dockerfile: Dockerfile
    container_name: ai-nk-vllm-service
    environment:
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379
      - MODEL_NAME=${MODEL_NAME:-gpt-3.5-turbo}
    ports:
      - "8006:8006"
    depends_on:
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8006/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Фронтенд
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: ai-nk-frontend
    ports:
      - "3000:80"
    depends_on:
      - gateway
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  norms_db_data:
  redis_data:
  qdrant_data:

networks:
  default:
    name: ai-nk-network
EOF

    log_success "Docker Compose файл создан"
}

# Создание скриптов управления
create_quick_scripts() {
    log_info "Создание скриптов управления..."
    
    # Скрипт запуска
    cat > start-quick.sh << 'EOF'
#!/bin/bash
set -e

echo "🚀 Быстрый запуск AI-НК..."

# Проверка .env файла
if [ ! -f .env ]; then
    echo "❌ Файл .env не найден. Запустите ./quick-deploy.sh сначала."
    exit 1
fi

# Запуск сервисов
echo "📦 Запуск контейнеров..."
docker-compose -f docker-compose.quick.yaml up -d

# Ожидание готовности
echo "⏳ Ожидание готовности сервисов..."
sleep 30

# Проверка статуса
echo "🔍 Проверка статуса..."
docker-compose -f docker-compose.quick.yaml ps

echo ""
echo "✅ AI-НК запущен!"
echo "🌐 Веб-интерфейс: http://localhost:3000"
echo "🔗 API: http://localhost/api"
echo ""
echo "📋 Полезные команды:"
echo "- Просмотр логов: docker-compose -f docker-compose.quick.yaml logs -f"
echo "- Остановка: docker-compose -f docker-compose.quick.yaml down"
echo "- Перезапуск: docker-compose -f docker-compose.quick.yaml restart"
EOF

    # Скрипт остановки
    cat > stop-quick.sh << 'EOF'
#!/bin/bash
set -e

echo "🛑 Остановка AI-НК..."

docker-compose -f docker-compose.quick.yaml down

echo "✅ AI-НК остановлен!"
EOF

    # Скрипт очистки
    cat > clean-quick.sh << 'EOF'
#!/bin/bash
set -e

echo "🧹 Очистка AI-НК..."

# Остановка сервисов
docker-compose -f docker-compose.quick.yaml down

# Удаление контейнеров и томов
docker-compose -f docker-compose.quick.yaml down --volumes --remove-orphans

# Очистка неиспользуемых образов
docker image prune -f

echo "✅ Очистка завершена!"
EOF

    # Установка прав выполнения
    chmod +x start-quick.sh stop-quick.sh clean-quick.sh
    
    log_success "Скрипты управления созданы"
}

# Создание README для быстрого развертывания
create_quick_readme() {
    log_info "Создание README для быстрого развертывания..."
    
    cat > README-QUICK.md << 'EOF'
# AI-НК - Быстрое развертывание

## Описание

Этот скрипт предназначен для быстрого развертывания AI-НК системы для тестирования и разработки.

## Требования

- Docker 20.10+
- Docker Compose 2.0+
- 4GB+ RAM
- 10GB+ свободного места

## Быстрый старт

1. **Клонирование и подготовка**:
   ```bash
   git clone <repository-url>
   cd ai-nk-deployment
   ./scripts/quick-deploy.sh
   ```

2. **Запуск системы**:
   ```bash
   cd ai-nk
   ./start-quick.sh
   ```

3. **Доступ к системе**:
   - Веб-интерфейс: http://localhost:3000
   - API: http://localhost/api

## Управление

- `./start-quick.sh` - запуск системы
- `./stop-quick.sh` - остановка системы
- `./clean-quick.sh` - полная очистка

## Мониторинг

```bash
# Просмотр логов всех сервисов
docker-compose -f docker-compose.quick.yaml logs -f

# Просмотр логов конкретного сервиса
docker-compose -f docker-compose.quick.yaml logs -f gateway

# Статус контейнеров
docker-compose -f docker-compose.quick.yaml ps
```

## Конфигурация

Основные настройки в файле `.env`:

- `POSTGRES_PASSWORD` - пароль базы данных (по умолчанию: dev_password)
- `REDIS_PASSWORD` - пароль Redis (по умолчанию: dev_password)
- `JWT_SECRET_KEY` - секретный ключ JWT
- `OPENAI_API_KEY` - ключ OpenAI API (опционально)

## Устранение неполадок

### Проблемы с портами

Если порты заняты, измените их в `docker-compose.quick.yaml`:

```yaml
ports:
  - "3001:80"  # Изменить 3000 на 3001
```

### Проблемы с памятью

Увеличьте лимиты Docker или добавьте swap:

```bash
# Добавление swap (Linux)
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Проблемы с базой данных

```bash
# Сброс базы данных
docker-compose -f docker-compose.quick.yaml down
docker volume rm ai-nk-deployment_norms_db_data
docker-compose -f docker-compose.quick.yaml up -d
```

## Разработка

### Логи в реальном времени

```bash
# Все сервисы
docker-compose -f docker-compose.quick.yaml logs -f

# Конкретный сервис
docker-compose -f docker-compose.quick.yaml logs -f calculation-service
```

### Пересборка сервиса

```bash
# Пересборка и перезапуск конкретного сервиса
docker-compose -f docker-compose.quick.yaml up -d --build calculation-service
```

### Подключение к контейнеру

```bash
# Подключение к контейнеру
docker-compose -f docker-compose.quick.yaml exec calculation-service bash
```

## Безопасность

⚠️ **Внимание**: Эта конфигурация предназначена только для разработки и тестирования!

Для продакшн использования:
1. Измените все пароли по умолчанию
2. Настройте SSL сертификаты
3. Используйте внешнюю базу данных
4. Настройте файрвол
5. Включите мониторинг

## Поддержка

При возникновении проблем:
1. Проверьте логи: `docker-compose -f docker-compose.quick.yaml logs`
2. Проверьте статус: `docker-compose -f docker-compose.quick.yaml ps`
3. Перезапустите: `./stop-quick.sh && ./start-quick.sh`
EOF

    log_success "README создан"
}

# Основная функция
main() {
    echo "🚀 AI-НК - Быстрое развертывание"
    echo "================================="
    echo ""
    
    check_docker
    create_minimal_config
    create_quick_compose
    create_quick_scripts
    create_quick_readme
    
    echo ""
    echo "✅ Быстрое развертывание завершено!"
    echo ""
    echo "📋 Следующие шаги:"
    echo "1. Перейдите в папку проекта: cd ai-nk"
    echo "2. Запустите систему: ./start-quick.sh"
    echo "3. Откройте браузер: http://localhost:3000"
    echo ""
    echo "📚 Документация: README-QUICK.md"
    echo ""
    echo "🎉 Готово к работе!"
}

# Запуск
main "$@"
