#!/bin/bash

# AI-НК - Скрипт установки системы нормоконтроля
# Версия: 1.0.0
# Автор: AI-НК Team

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для вывода сообщений
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

# Проверка системных требований
check_requirements() {
    log_info "Проверка системных требований..."
    
    # Проверка операционной системы
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
    else
        log_error "Неподдерживаемая операционная система: $OSTYPE"
        exit 1
    fi
    
    log_success "Операционная система: $OS"
    
    # Проверка Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker не установлен. Пожалуйста, установите Docker."
        exit 1
    fi
    
    # Проверка Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose не установлен. Пожалуйста, установите Docker Compose."
        exit 1
    fi
    
    # Проверка версии Docker
    DOCKER_VERSION=$(docker --version | cut -d ' ' -f3 | cut -d ',' -f1)
    log_success "Docker версия: $DOCKER_VERSION"
    
    # Проверка версии Docker Compose
    COMPOSE_VERSION=$(docker-compose --version | cut -d ' ' -f3 | cut -d ',' -f1)
    log_success "Docker Compose версия: $COMPOSE_VERSION"
    
    # Проверка доступности портов
    check_ports() {
        local ports=("80" "443" "8080" "8081" "8082" "8083" "8084" "8085" "8086" "8087" "8088" "8089" "5432" "6379" "6333")
        for port in "${ports[@]}"; do
            if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
                log_warning "Порт $port уже используется. Возможны конфликты."
            fi
        done
    }
    
    check_ports
    log_success "Проверка системных требований завершена"
}

# Установка зависимостей
install_dependencies() {
    log_info "Установка системных зависимостей..."
    
    if [[ "$OS" == "linux" ]]; then
        # Обновление пакетов
        sudo apt-get update
        
        # Установка необходимых пакетов
        sudo apt-get install -y \
            curl \
            wget \
            git \
            unzip \
            jq \
            lsof \
            postgresql-client \
            redis-tools
    elif [[ "$OS" == "macos" ]]; then
        # Проверка Homebrew
        if ! command -v brew &> /dev/null; then
            log_info "Установка Homebrew..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        fi
        
        # Установка необходимых пакетов
        brew install \
            curl \
            wget \
            git \
            unzip \
            jq \
            lsof \
            postgresql \
            redis
    fi
    
    log_success "Зависимости установлены"
}

# Создание структуры проекта
create_project_structure() {
    log_info "Создание структуры проекта..."
    
    # Создание основных директорий
    mkdir -p ai-nk/{data,logs,ssl,uploads,backups}
    mkdir -p ai-nk/data/{postgres,redis,qdrant}
    mkdir -p ai-nk/logs/{gateway,calculation-service,rag-service,chat-service,frontend,keycloak}
    mkdir -p ai-nk/ssl/{certs,keys}
    mkdir -p ai-nk/uploads/{documents,reports}
    mkdir -p ai-nk/backups/{database,configs}
    
    # Установка прав доступа
    chmod 755 ai-nk
    chmod 755 ai-nk/data
    chmod 755 ai-nk/logs
    chmod 700 ai-nk/ssl
    chmod 755 ai-nk/uploads
    chmod 755 ai-nk/backups
    
    log_success "Структура проекта создана"
}

# Копирование файлов проекта
copy_project_files() {
    log_info "Копирование файлов проекта..."
    
    # Копирование основных файлов
    cp -r ../calculation_service ai-nk/
    cp -r ../rag_service ai-nk/
    cp -r ../chat_service ai-nk/
    cp -r ../gateway ai-nk/
    cp -r ../frontend ai-nk/
    cp -r ../keycloak ai-nk/
    cp -r ../document_parser ai-nk/
    cp -r ../vllm_service ai-nk/
    cp -r ../rule_engine ai-nk/
    
    # Копирование конфигурационных файлов
    cp ../docker-compose.yaml ai-nk/
    cp ../docker-compose.prod.yaml ai-nk/
    cp ../nginx.conf ai-nk/
    cp ../config.py ai-nk/
    
    # Копирование скриптов
    cp -r ../scripts ai-nk/
    cp -r ../sql ai-nk/
    cp -r ../configs ai-nk/
    
    # Копирование документации
    cp ../README.md ai-nk/
    cp ../LICENSE ai-nk/
    cp ../CHANGELOG.md ai-nk/
    cp ../DEPLOYMENT.md ai-nk/
    cp ../INSTALLATION_GUIDE.md ai-nk/
    
    log_success "Файлы проекта скопированы"
}

# Создание переменных окружения
create_environment_files() {
    log_info "Создание файлов переменных окружения..."
    
    # Основной файл окружения
    cat > ai-nk/.env << EOF
# AI-НК Environment Configuration
# Версия: 1.0.0

# Основные настройки
PROJECT_NAME=AI-НК
PROJECT_VERSION=1.0.0
ENVIRONMENT=production
DEBUG=false

# Настройки базы данных
POSTGRES_DB=norms_db
POSTGRES_USER=norms_user
POSTGRES_PASSWORD=$(openssl rand -base64 32)
POSTGRES_HOST=norms-db
POSTGRES_PORT=5432

# Настройки Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=$(openssl rand -base64 32)

# Настройки Qdrant
QDRANT_HOST=qdrant
QDRANT_PORT=6333
QDRANT_API_KEY=$(openssl rand -base64 32)

# Настройки Keycloak
KEYCLOAK_ADMIN_USER=admin
KEYCLOAK_ADMIN_PASSWORD=$(openssl rand -base64 32)
KEYCLOAK_DB_PASSWORD=$(openssl rand -base64 32)

# Настройки JWT
JWT_SECRET_KEY=$(openssl rand -base64 64)
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Настройки API Gateway
GATEWAY_HOST=localhost
GATEWAY_PORT=80
GATEWAY_SSL_PORT=443

# Настройки сервисов
CALCULATION_SERVICE_PORT=8002
RAG_SERVICE_PORT=8003
CHAT_SERVICE_PORT=8004
DOCUMENT_PARSER_PORT=8005
VLLM_SERVICE_PORT=8006
FRONTEND_PORT=3000

# Настройки SSL
SSL_CERT_PATH=/app/ssl/certs/cert.pem
SSL_KEY_PATH=/app/ssl/keys/key.pem

# Настройки логирования
LOG_LEVEL=INFO
LOG_FORMAT=json

# Настройки мониторинга
PROMETHEUS_PORT=9090
GRAFANA_PORT=3001

# Настройки резервного копирования
BACKUP_RETENTION_DAYS=30
BACKUP_SCHEDULE="0 2 * * *"

# Настройки безопасности
CORS_ORIGINS=["https://localhost", "https://127.0.0.1"]
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# Настройки файлов
MAX_FILE_SIZE=100MB
ALLOWED_FILE_TYPES=["pdf", "doc", "docx", "txt", "rtf"]

# Настройки AI моделей
DEFAULT_MODEL=gpt-3.5-turbo
MODEL_TEMPERATURE=0.7
MAX_TOKENS=4000

# Настройки уведомлений
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=
EMAIL_PASSWORD=
EMAIL_USE_TLS=true

# Настройки интеграций
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
OLLAMA_HOST=http://ollama:11434
EOF

    # Файл окружения для разработки
    cat > ai-nk/.env.development << EOF
# AI-НК Development Environment
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
LOG_FORMAT=text

# Разработка - используем локальные пароли
POSTGRES_PASSWORD=dev_password
REDIS_PASSWORD=dev_password
QDRANT_API_KEY=dev_key
KEYCLOAK_ADMIN_PASSWORD=admin
KEYCLOAK_DB_PASSWORD=keycloak_password
JWT_SECRET_KEY=dev_secret_key_32_chars_long

# Отключение SSL для разработки
SSL_ENABLED=false
EOF

    log_success "Файлы переменных окружения созданы"
}

# Генерация SSL сертификатов
generate_ssl_certificates() {
    log_info "Генерация SSL сертификатов..."
    
    cd ai-nk/ssl
    
    # Создание самоподписанного сертификата
    openssl req -x509 -newkey rsa:4096 -keyout keys/key.pem -out certs/cert.pem \
        -days 365 -nodes -subj "/C=RU/ST=Moscow/L=Moscow/O=AI-НК/OU=IT/CN=localhost"
    
    # Создание дополнительных сертификатов для поддоменов
    openssl req -x509 -newkey rsa:4096 -keyout keys/api.key.pem -out certs/api.cert.pem \
        -days 365 -nodes -subj "/C=RU/ST=Moscow/L=Moscow/O=AI-НК/OU=IT/CN=api.localhost"
    
    # Установка прав доступа
    chmod 600 keys/*.pem
    chmod 644 certs/*.pem
    
    cd ../..
    
    log_success "SSL сертификаты сгенерированы"
}

# Создание скриптов управления
create_management_scripts() {
    log_info "Создание скриптов управления..."
    
    # Скрипт запуска
    cat > ai-nk/start.sh << 'EOF'
#!/bin/bash
# AI-НК - Скрипт запуска системы

set -e

echo "🚀 Запуск AI-НК системы..."

# Проверка Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose не установлен"
    exit 1
fi

# Выбор конфигурации
if [ "$1" = "dev" ]; then
    COMPOSE_FILE="docker-compose.yaml"
    ENV_FILE=".env.development"
    echo "🔧 Режим разработки"
else
    COMPOSE_FILE="docker-compose.prod.yaml"
    ENV_FILE=".env"
    echo "🏭 Продакшн режим"
fi

# Запуск сервисов
echo "📦 Запуск контейнеров..."
docker-compose -f $COMPOSE_FILE --env-file $ENV_FILE up -d

# Ожидание готовности сервисов
echo "⏳ Ожидание готовности сервисов..."
sleep 30

# Проверка статуса
echo "🔍 Проверка статуса сервисов..."
docker-compose -f $COMPOSE_FILE --env-file $ENV_FILE ps

echo "✅ AI-НК система запущена!"
echo "🌐 Веб-интерфейс: https://localhost"
echo "📊 API Gateway: https://localhost/api"
echo "🔐 Keycloak: https://localhost/auth"
EOF

    # Скрипт остановки
    cat > ai-nk/stop.sh << 'EOF'
#!/bin/bash
# AI-НК - Скрипт остановки системы

set -e

echo "🛑 Остановка AI-НК системы..."

# Выбор конфигурации
if [ "$1" = "dev" ]; then
    COMPOSE_FILE="docker-compose.yaml"
    ENV_FILE=".env.development"
else
    COMPOSE_FILE="docker-compose.prod.yaml"
    ENV_FILE=".env"
fi

# Остановка сервисов
docker-compose -f $COMPOSE_FILE --env-file $ENV_FILE down

echo "✅ AI-НК система остановлена!"
EOF

    # Скрипт перезапуска
    cat > ai-nk/restart.sh << 'EOF'
#!/bin/bash
# AI-НК - Скрипт перезапуска системы

set -e

echo "🔄 Перезапуск AI-НК системы..."

# Остановка
./stop.sh $1

# Запуск
./start.sh $1
EOF

    # Скрипт обновления
    cat > ai-nk/update.sh << 'EOF'
#!/bin/bash
# AI-НК - Скрипт обновления системы

set -e

echo "🔄 Обновление AI-НК системы..."

# Создание резервной копии
echo "💾 Создание резервной копии..."
./backup.sh

# Остановка сервисов
echo "🛑 Остановка сервисов..."
./stop.sh

# Обновление образов
echo "📦 Обновление Docker образов..."
docker-compose -f docker-compose.prod.yaml pull

# Запуск сервисов
echo "🚀 Запуск обновленных сервисов..."
./start.sh

echo "✅ AI-НК система обновлена!"
EOF

    # Скрипт резервного копирования
    cat > ai-nk/backup.sh << 'EOF'
#!/bin/bash
# AI-НК - Скрипт резервного копирования

set -e

BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

echo "💾 Создание резервной копии в $BACKUP_DIR..."

# Резервное копирование базы данных
echo "🗄️ Резервное копирование базы данных..."
docker-compose exec -T norms-db pg_dump -U norms_user norms_db > $BACKUP_DIR/database.sql

# Резервное копирование конфигураций
echo "⚙️ Резервное копирование конфигураций..."
cp -r configs $BACKUP_DIR/
cp .env $BACKUP_DIR/
cp docker-compose*.yaml $BACKUP_DIR/

# Резервное копирование загруженных файлов
echo "📁 Резервное копирование файлов..."
cp -r uploads $BACKUP_DIR/

# Создание архива
echo "📦 Создание архива..."
cd backups
tar -czf $(basename $BACKUP_DIR).tar.gz $(basename $BACKUP_DIR)
rm -rf $(basename $BACKUP_DIR)
cd ..

echo "✅ Резервная копия создана: backups/$(basename $BACKUP_DIR).tar.gz"
EOF

    # Скрипт восстановления
    cat > ai-nk/restore.sh << 'EOF'
#!/bin/bash
# AI-НК - Скрипт восстановления из резервной копии

set -e

if [ -z "$1" ]; then
    echo "❌ Укажите путь к резервной копии"
    echo "Использование: ./restore.sh <путь_к_архиву>"
    exit 1
fi

BACKUP_FILE=$1

if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Файл резервной копии не найден: $BACKUP_FILE"
    exit 1
fi

echo "🔄 Восстановление из резервной копии: $BACKUP_FILE"

# Остановка сервисов
echo "🛑 Остановка сервисов..."
./stop.sh

# Извлечение архива
echo "📦 Извлечение архива..."
cd backups
tar -xzf $BACKUP_FILE
BACKUP_DIR=$(basename $BACKUP_FILE .tar.gz)
cd ..

# Восстановление базы данных
echo "🗄️ Восстановление базы данных..."
docker-compose up -d norms-db
sleep 10
docker-compose exec -T norms-db psql -U norms_user -d norms_db < backups/$BACKUP_DIR/database.sql

# Восстановление конфигураций
echo "⚙️ Восстановление конфигураций..."
cp -r backups/$BACKUP_DIR/configs/* configs/
cp backups/$BACKUP_DIR/.env .env

# Восстановление файлов
echo "📁 Восстановление файлов..."
cp -r backups/$BACKUP_DIR/uploads/* uploads/

# Запуск сервисов
echo "🚀 Запуск сервисов..."
./start.sh

echo "✅ Восстановление завершено!"
EOF

    # Скрипт мониторинга
    cat > ai-nk/monitor.sh << 'EOF'
#!/bin/bash
# AI-НК - Скрипт мониторинга системы

set -e

echo "📊 Мониторинг AI-НК системы..."

# Проверка статуса контейнеров
echo "🐳 Статус контейнеров:"
docker-compose ps

echo ""
echo "💾 Использование диска:"
df -h

echo ""
echo "🧠 Использование памяти:"
free -h

echo ""
echo "🌐 Сетевые соединения:"
netstat -tulpn | grep -E ':(80|443|8080|8081|8082|8083|8084|8085|8086|8087|8088|8089|5432|6379|6333)'

echo ""
echo "📋 Логи сервисов:"
echo "Gateway:"
docker-compose logs --tail=5 gateway

echo ""
echo "Calculation Service:"
docker-compose logs --tail=5 calculation-service

echo ""
echo "RAG Service:"
docker-compose logs --tail=5 rag-service

echo ""
echo "Frontend:"
docker-compose logs --tail=5 frontend
EOF

    # Скрипт очистки
    cat > ai-nk/cleanup.sh << 'EOF'
#!/bin/bash
# AI-НК - Скрипт очистки системы

set -e

echo "🧹 Очистка AI-НК системы..."

# Остановка сервисов
echo "🛑 Остановка сервисов..."
./stop.sh

# Удаление контейнеров
echo "🗑️ Удаление контейнеров..."
docker-compose down --volumes --remove-orphans

# Очистка неиспользуемых образов
echo "📦 Очистка неиспользуемых образов..."
docker image prune -f

# Очистка неиспользуемых томов
echo "💾 Очистка неиспользуемых томов..."
docker volume prune -f

# Очистка логов
echo "📋 Очистка логов..."
find logs -name "*.log" -mtime +7 -delete

echo "✅ Очистка завершена!"
EOF

    # Установка прав выполнения
    chmod +x ai-nk/*.sh
    
    log_success "Скрипты управления созданы"
}

# Создание документации
create_documentation() {
    log_info "Создание документации..."
    
    # README для развертывания
    cat > ai-nk/README-DEPLOYMENT.md << 'EOF'
# AI-НК - Руководство по развертыванию

## Обзор

AI-НК - это система нормоконтроля с использованием искусственного интеллекта для анализа строительной документации.

## Системные требования

- **ОС**: Linux (Ubuntu 20.04+) или macOS (10.15+)
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **RAM**: минимум 8GB, рекомендуется 16GB+
- **Диск**: минимум 50GB свободного места
- **CPU**: минимум 4 ядра, рекомендуется 8+

## Быстрый старт

1. **Установка**:
   ```bash
   ./install.sh
   ```

2. **Запуск**:
   ```bash
   ./start.sh
   ```

3. **Доступ к системе**:
   - Веб-интерфейс: https://localhost
   - API: https://localhost/api
   - Keycloak: https://localhost/auth

## Управление системой

### Основные команды

- `./start.sh` - запуск системы
- `./stop.sh` - остановка системы
- `./restart.sh` - перезапуск системы
- `./update.sh` - обновление системы
- `./backup.sh` - создание резервной копии
- `./restore.sh <архив>` - восстановление из резервной копии
- `./monitor.sh` - мониторинг системы
- `./cleanup.sh` - очистка системы

### Режимы работы

- **Продакшн**: `./start.sh` (по умолчанию)
- **Разработка**: `./start.sh dev`

## Конфигурация

### Переменные окружения

Основные настройки находятся в файле `.env`:

- `POSTGRES_PASSWORD` - пароль базы данных
- `REDIS_PASSWORD` - пароль Redis
- `JWT_SECRET_KEY` - секретный ключ JWT
- `KEYCLOAK_ADMIN_PASSWORD` - пароль администратора Keycloak

### SSL сертификаты

Система использует самоподписанные сертификаты для HTTPS.
Для продакшн использования замените сертификаты в папке `ssl/`.

## Мониторинг

### Логи

Логи сервисов находятся в папке `logs/`:
- `logs/gateway/` - логи API Gateway
- `logs/calculation-service/` - логи сервиса расчетов
- `logs/rag-service/` - логи RAG сервиса
- `logs/chat-service/` - логи чат сервиса
- `logs/frontend/` - логи фронтенда

### Мониторинг в реальном времени

```bash
# Просмотр логов всех сервисов
docker-compose logs -f

# Просмотр логов конкретного сервиса
docker-compose logs -f gateway
```

## Резервное копирование

### Автоматическое резервное копирование

Система автоматически создает резервные копии каждый день в 2:00.

### Ручное резервное копирование

```bash
./backup.sh
```

### Восстановление

```bash
./restore.sh backups/20240101_120000.tar.gz
```

## Безопасность

### Рекомендации

1. Измените все пароли по умолчанию
2. Используйте надежные SSL сертификаты
3. Настройте файрвол
4. Регулярно обновляйте систему
5. Мониторьте логи на предмет подозрительной активности

### Настройка файрвола

```bash
# Разрешить только необходимые порты
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

## Устранение неполадок

### Проблемы с запуском

1. Проверьте системные требования
2. Убедитесь, что порты свободны
3. Проверьте логи: `./monitor.sh`

### Проблемы с производительностью

1. Увеличьте объем RAM
2. Настройте параметры Docker
3. Оптимизируйте конфигурацию базы данных

### Проблемы с SSL

1. Проверьте сертификаты в папке `ssl/`
2. Убедитесь в правильности прав доступа
3. Перегенерируйте сертификаты при необходимости

## Поддержка

- Документация: [ссылка на документацию]
- Поддержка: [email поддержки]
- Баг-трекер: [ссылка на баг-трекер]

## Лицензия

Проект распространяется под лицензией MIT. См. файл LICENSE.
EOF

    # Руководство по настройке
    cat > ai-nk/SETUP-GUIDE.md << 'EOF'
# AI-НК - Руководство по настройке

## Первоначальная настройка

### 1. Настройка базы данных

После первого запуска выполните миграции:

```bash
# Подключение к базе данных
docker-compose exec norms-db psql -U norms_user -d norms_db

# Выполнение миграций
\i /app/sql/init.sql
\i /app/sql/migrations.sql
```

### 2. Настройка Keycloak

1. Откройте https://localhost/auth
2. Войдите как администратор (admin / пароль из .env)
3. Создайте realm для AI-НК
4. Настройте клиентов и роли

### 3. Настройка пользователей

```bash
# Создание администратора
curl -X POST https://localhost/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@example.com",
    "password": "secure_password",
    "role": "admin"
  }'
```

## Настройка сервисов

### API Gateway

Основные настройки в `gateway/app.py`:
- CORS настройки
- Rate limiting
- Аутентификация

### Сервис расчетов

Настройки в `calculation_service/config.py`:
- Параметры базы данных
- Настройки логирования
- Конфигурация моделей

### RAG сервис

Настройки в `rag_service/config.py`:
- Параметры векторной базы
- Настройки эмбеддингов
- Конфигурация поиска

## Настройка мониторинга

### Prometheus

1. Откройте http://localhost:9090
2. Настройте алерты
3. Добавьте дашборды

### Grafana

1. Откройте http://localhost:3001
2. Войдите (admin / admin)
3. Импортируйте дашборды из `configs/grafana/`

## Настройка резервного копирования

### Автоматическое резервное копирование

Добавьте в crontab:

```bash
# Ежедневное резервное копирование в 2:00
0 2 * * * /path/to/ai-nk/backup.sh
```

### Настройка уведомлений

В файле `.env` настройте параметры email:

```env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
```

## Производительность

### Оптимизация Docker

В файле `/etc/docker/daemon.json`:

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "storage-driver": "overlay2",
  "storage-opts": [
    "overlay2.override_kernel_check=true"
  ]
}
```

### Оптимизация базы данных

В файле `configs/postgresql/postgresql.conf`:

```conf
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
```

## Безопасность

### Настройка SSL

1. Получите сертификаты от CA
2. Замените файлы в `ssl/certs/` и `ssl/keys/`
3. Обновите настройки в `.env`

### Настройка файрвола

```bash
# UFW
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable

# iptables
iptables -A INPUT -p tcp --dport 22 -j ACCEPT
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT
iptables -A INPUT -j DROP
```

### Настройка аутентификации

1. Настройте OAuth2 провайдеров в Keycloak
2. Настройте двухфакторную аутентификацию
3. Настройте политики паролей

## Масштабирование

### Горизонтальное масштабирование

1. Настройте load balancer
2. Используйте внешнюю базу данных
3. Настройте Redis Cluster

### Вертикальное масштабирование

1. Увеличьте ресурсы контейнеров
2. Оптимизируйте конфигурацию
3. Настройте кэширование
EOF

    log_success "Документация создана"
}

# Создание systemd сервисов
create_systemd_services() {
    log_info "Создание systemd сервисов..."
    
    # Сервис для AI-НК
    cat > ai-nk/ai-nk.service << EOF
[Unit]
Description=AI-НК System
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$(pwd)/ai-nk
ExecStart=$(pwd)/ai-nk/start.sh
ExecStop=$(pwd)/ai-nk/stop.sh
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

    # Сервис для резервного копирования
    cat > ai-nk/ai-nk-backup.service << EOF
[Unit]
Description=AI-НК Backup Service
Requires=ai-nk.service
After=ai-nk.service

[Service]
Type=oneshot
WorkingDirectory=$(pwd)/ai-nk
ExecStart=$(pwd)/ai-nk/backup.sh
EOF

    # Таймер для резервного копирования
    cat > ai-nk/ai-nk-backup.timer << EOF
[Unit]
Description=AI-НК Backup Timer
Requires=ai-nk-backup.service

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
EOF

    log_success "Systemd сервисы созданы"
}

# Основная функция установки
main() {
    echo "🚀 AI-НК - Установка системы нормоконтроля"
    echo "=========================================="
    echo ""
    
    # Проверка прав администратора
    if [[ $EUID -eq 0 ]]; then
        log_warning "Запуск от имени root не рекомендуется"
        read -p "Продолжить? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    # Выполнение этапов установки
    check_requirements
    install_dependencies
    create_project_structure
    copy_project_files
    create_environment_files
    generate_ssl_certificates
    create_management_scripts
    create_documentation
    create_systemd_services
    
    echo ""
    echo "✅ Установка завершена!"
    echo ""
    echo "📋 Следующие шаги:"
    echo "1. Перейдите в папку проекта: cd ai-nk"
    echo "2. Запустите систему: ./start.sh"
    echo "3. Откройте браузер: https://localhost"
    echo ""
    echo "📚 Документация:"
    echo "- README-DEPLOYMENT.md - руководство по развертыванию"
    echo "- SETUP-GUIDE.md - руководство по настройке"
    echo ""
    echo "🔧 Управление:"
    echo "- ./start.sh - запуск"
    echo "- ./stop.sh - остановка"
    echo "- ./monitor.sh - мониторинг"
    echo "- ./backup.sh - резервное копирование"
    echo ""
    echo "🎉 Готово к работе!"
}

# Запуск установки
main "$@"
