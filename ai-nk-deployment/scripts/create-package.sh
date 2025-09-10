#!/bin/bash

# AI-НК - Создание пакета для развертывания
# Создает готовый к развертыванию архив проекта

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

# Переменные
PACKAGE_NAME="ai-nk-$(date +%Y%m%d_%H%M%S)"
PACKAGE_DIR="ai-nk-deployment/packages/$PACKAGE_NAME"
SOURCE_DIR=".."

# Создание директории пакета
create_package_structure() {
    log_info "Создание структуры пакета..."
    
    mkdir -p "$PACKAGE_DIR"
    mkdir -p "$PACKAGE_DIR/ai-nk"
    mkdir -p "$PACKAGE_DIR/scripts"
    mkdir -p "$PACKAGE_DIR/docs"
    mkdir -p "$PACKAGE_DIR/configs"
    
    log_success "Структура пакета создана"
}

# Копирование исходного кода
copy_source_code() {
    log_info "Копирование исходного кода..."
    
    # Основные сервисы
    cp -r "$SOURCE_DIR/calculation_service" "$PACKAGE_DIR/ai-nk/"
    cp -r "$SOURCE_DIR/rag_service" "$PACKAGE_DIR/ai-nk/"
    cp -r "$SOURCE_DIR/chat_service" "$PACKAGE_DIR/ai-nk/"
    cp -r "$SOURCE_DIR/gateway" "$PACKAGE_DIR/ai-nk/"
    cp -r "$SOURCE_DIR/frontend" "$PACKAGE_DIR/ai-nk/"
    cp -r "$SOURCE_DIR/keycloak" "$PACKAGE_DIR/ai-nk/"
    cp -r "$SOURCE_DIR/document_parser" "$PACKAGE_DIR/ai-nk/"
    cp -r "$SOURCE_DIR/vllm_service" "$PACKAGE_DIR/ai-nk/"
    cp -r "$SOURCE_DIR/rule_engine" "$PACKAGE_DIR/ai-nk/"
    
    # Конфигурационные файлы
    cp "$SOURCE_DIR/docker-compose.yaml" "$PACKAGE_DIR/ai-nk/"
    cp "$SOURCE_DIR/docker-compose.prod.yaml" "$PACKAGE_DIR/ai-nk/"
    cp "$SOURCE_DIR/nginx.conf" "$PACKAGE_DIR/ai-nk/"
    cp "$SOURCE_DIR/config.py" "$PACKAGE_DIR/ai-nk/"
    
    # SQL скрипты
    cp -r "$SOURCE_DIR/sql" "$PACKAGE_DIR/ai-nk/"
    
    # Конфигурации
    cp -r "$SOURCE_DIR/configs" "$PACKAGE_DIR/ai-nk/"
    
    log_success "Исходный код скопирован"
}

# Копирование скриптов установки
copy_installation_scripts() {
    log_info "Копирование скриптов установки..."
    
    cp scripts/install.sh "$PACKAGE_DIR/scripts/"
    cp scripts/quick-deploy.sh "$PACKAGE_DIR/scripts/"
    
    # Создание скрипта установки пакета
    cat > "$PACKAGE_DIR/install.sh" << 'EOF'
#!/bin/bash

# AI-НК - Установка из пакета
set -e

echo "🚀 AI-НК - Установка из пакета"
echo "==============================="

# Проверка прав
if [[ $EUID -eq 0 ]]; then
    echo "⚠️  Запуск от имени root не рекомендуется"
    read -p "Продолжить? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Запуск основного скрипта установки
echo "📦 Запуск установки..."
chmod +x scripts/install.sh
./scripts/install.sh

echo "✅ Установка завершена!"
EOF

    chmod +x "$PACKAGE_DIR/install.sh"
    
    log_success "Скрипты установки скопированы"
}

# Создание документации
create_documentation() {
    log_info "Создание документации..."
    
    # Основной README
    cat > "$PACKAGE_DIR/README.md" << 'EOF'
# AI-НК - Система нормоконтроля

## Описание

AI-НК - это система нормоконтроля с использованием искусственного интеллекта для анализа строительной документации.

## Возможности

- 📄 Анализ строительной документации
- 🔍 Проверка соответствия нормативным требованиям
- 🧮 Инженерные расчеты
- 💬 Чат-бот для консультаций
- 📊 Отчеты и рекомендации
- 🔐 Безопасная аутентификация

## Быстрый старт

1. **Установка**:
   ```bash
   ./install.sh
   ```

2. **Запуск**:
   ```bash
   cd ai-nk
   ./start.sh
   ```

3. **Доступ**:
   - Веб-интерфейс: https://localhost
   - API: https://localhost/api

## Документация

- `docs/INSTALLATION.md` - руководство по установке
- `docs/CONFIGURATION.md` - руководство по настройке
- `docs/API.md` - документация API
- `docs/DEVELOPMENT.md` - руководство разработчика

## Поддержка

- Email: support@ai-nk.ru
- Документация: https://docs.ai-nk.ru
- Баг-трекер: https://github.com/ai-nk/issues

## Лицензия

MIT License. См. файл LICENSE.
EOF

    # Руководство по установке
    cat > "$PACKAGE_DIR/docs/INSTALLATION.md" << 'EOF'
# Руководство по установке AI-НК

## Системные требования

### Минимальные требования
- **ОС**: Linux (Ubuntu 20.04+) или macOS (10.15+)
- **RAM**: 8GB
- **Диск**: 50GB свободного места
- **CPU**: 4 ядра

### Рекомендуемые требования
- **ОС**: Linux (Ubuntu 22.04+) или macOS (12+)
- **RAM**: 16GB+
- **Диск**: 100GB+ SSD
- **CPU**: 8+ ядер

### Программное обеспечение
- Docker 20.10+
- Docker Compose 2.0+
- Git (для клонирования)

## Установка

### Автоматическая установка

1. **Запуск установщика**:
   ```bash
   ./install.sh
   ```

2. **Следование инструкциям**:
   - Установщик проверит системные требования
   - Установит необходимые зависимости
   - Создаст структуру проекта
   - Настроит конфигурацию

### Ручная установка

1. **Клонирование репозитория**:
   ```bash
   git clone <repository-url>
   cd ai-nk
   ```

2. **Установка зависимостей**:
   ```bash
   # Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install -y docker.io docker-compose git curl wget

   # macOS
   brew install docker docker-compose git curl wget
   ```

3. **Настройка Docker**:
   ```bash
   sudo systemctl start docker
   sudo systemctl enable docker
   sudo usermod -aG docker $USER
   ```

4. **Создание конфигурации**:
   ```bash
   cp .env.example .env
   # Отредактируйте .env файл
   ```

5. **Запуск сервисов**:
   ```bash
   docker-compose up -d
   ```

## Проверка установки

1. **Проверка статуса**:
   ```bash
   docker-compose ps
   ```

2. **Проверка логов**:
   ```bash
   docker-compose logs
   ```

3. **Проверка веб-интерфейса**:
   - Откройте https://localhost
   - Должен загрузиться интерфейс AI-НК

## Настройка после установки

1. **Создание администратора**:
   ```bash
   curl -X POST https://localhost/api/auth/register \
     -H "Content-Type: application/json" \
     -d '{
       "username": "admin",
       "email": "admin@example.com",
       "password": "secure_password",
       "role": "admin"
     }'
   ```

2. **Настройка Keycloak**:
   - Откройте https://localhost/auth
   - Войдите как администратор
   - Создайте realm и пользователей

3. **Настройка мониторинга**:
   - Prometheus: http://localhost:9090
   - Grafana: http://localhost:3001

## Устранение неполадок

### Проблемы с Docker

```bash
# Перезапуск Docker
sudo systemctl restart docker

# Очистка Docker
docker system prune -a
```

### Проблемы с портами

```bash
# Проверка занятых портов
netstat -tulpn | grep -E ':(80|443|5432|6379)'

# Освобождение портов
sudo fuser -k 80/tcp
```

### Проблемы с базой данных

```bash
# Сброс базы данных
docker-compose down
docker volume rm ai-nk_norms_db_data
docker-compose up -d
```

## Обновление

1. **Создание резервной копии**:
   ```bash
   ./backup.sh
   ```

2. **Обновление кода**:
   ```bash
   git pull origin main
   ```

3. **Обновление сервисов**:
   ```bash
   ./update.sh
   ```

## Удаление

1. **Остановка сервисов**:
   ```bash
   ./stop.sh
   ```

2. **Удаление контейнеров**:
   ```bash
   docker-compose down --volumes
   ```

3. **Удаление данных**:
   ```bash
   rm -rf ai-nk/
   ```
EOF

    # Руководство по настройке
    cat > "$PACKAGE_DIR/docs/CONFIGURATION.md" << 'EOF'
# Руководство по настройке AI-НК

## Основные настройки

### Переменные окружения

Основные настройки находятся в файле `.env`:

```env
# Основные настройки
PROJECT_NAME=AI-НК
ENVIRONMENT=production
DEBUG=false

# База данных
POSTGRES_DB=norms_db
POSTGRES_USER=norms_user
POSTGRES_PASSWORD=secure_password
POSTGRES_HOST=norms-db
POSTGRES_PORT=5432

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=secure_password

# JWT
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
CORS_ORIGINS=["https://localhost", "https://yourdomain.com"]
```

### Настройка базы данных

1. **Подключение к базе данных**:
   ```bash
   docker-compose exec norms-db psql -U norms_user -d norms_db
   ```

2. **Выполнение миграций**:
   ```sql
   \i /app/sql/init.sql
   \i /app/sql/migrations.sql
   ```

3. **Создание индексов**:
   ```sql
   CREATE INDEX idx_documents_title ON documents(title);
   CREATE INDEX idx_documents_type ON documents(type);
   ```

### Настройка аутентификации

1. **Keycloak**:
   - Откройте https://localhost/auth
   - Создайте realm
   - Настройте клиентов
   - Создайте роли и пользователей

2. **JWT настройки**:
   ```env
   JWT_SECRET_KEY=your-very-secure-secret-key
   JWT_ALGORITHM=HS256
   JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
   JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
   ```

### Настройка SSL

1. **Получение сертификатов**:
   ```bash
   # Let's Encrypt
   certbot certonly --standalone -d yourdomain.com
   
   # Копирование сертификатов
   cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ssl/certs/cert.pem
   cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ssl/keys/key.pem
   ```

2. **Обновление конфигурации**:
   ```env
   SSL_ENABLED=true
   SSL_CERT_PATH=/app/ssl/certs/cert.pem
   SSL_KEY_PATH=/app/ssl/keys/key.pem
   ```

### Настройка мониторинга

1. **Prometheus**:
   - Откройте http://localhost:9090
   - Настройте алерты
   - Добавьте targets

2. **Grafana**:
   - Откройте http://localhost:3001
   - Войдите (admin/admin)
   - Импортируйте дашборды

### Настройка резервного копирования

1. **Автоматическое резервное копирование**:
   ```bash
   # Добавление в crontab
   crontab -e
   
   # Ежедневное резервное копирование в 2:00
   0 2 * * * /path/to/ai-nk/backup.sh
   ```

2. **Настройка уведомлений**:
   ```env
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_USER=your-email@gmail.com
   EMAIL_PASSWORD=your-app-password
   ```

## Производительность

### Оптимизация Docker

1. **Настройка daemon.json**:
   ```json
   {
     "log-driver": "json-file",
     "log-opts": {
       "max-size": "10m",
       "max-file": "3"
     },
     "storage-driver": "overlay2"
   }
   ```

2. **Ограничение ресурсов**:
   ```yaml
   services:
     calculation-service:
       deploy:
         resources:
           limits:
             memory: 2G
             cpus: '1.0'
   ```

### Оптимизация базы данных

1. **Настройка PostgreSQL**:
   ```conf
   shared_buffers = 256MB
   effective_cache_size = 1GB
   maintenance_work_mem = 64MB
   checkpoint_completion_target = 0.9
   wal_buffers = 16MB
   ```

2. **Создание индексов**:
   ```sql
   CREATE INDEX CONCURRENTLY idx_documents_created_at ON documents(created_at);
   CREATE INDEX CONCURRENTLY idx_documents_user_id ON documents(user_id);
   ```

## Безопасность

### Настройка файрвола

1. **UFW (Ubuntu)**:
   ```bash
   ufw default deny incoming
   ufw default allow outgoing
   ufw allow ssh
   ufw allow 80/tcp
   ufw allow 443/tcp
   ufw enable
   ```

2. **iptables**:
   ```bash
   iptables -A INPUT -p tcp --dport 22 -j ACCEPT
   iptables -A INPUT -p tcp --dport 80 -j ACCEPT
   iptables -A INPUT -p tcp --dport 443 -j ACCEPT
   iptables -A INPUT -j DROP
   ```

### Настройка аутентификации

1. **Двухфакторная аутентификация**:
   - Настройте в Keycloak
   - Используйте TOTP или SMS

2. **Политики паролей**:
   - Минимальная длина: 12 символов
   - Обязательные символы: буквы, цифры, спецсимволы
   - Запрет повторного использования

## Масштабирование

### Горизонтальное масштабирование

1. **Load Balancer**:
   ```yaml
   services:
     nginx:
       image: nginx:alpine
       ports:
         - "80:80"
       volumes:
         - ./nginx.conf:/etc/nginx/nginx.conf
   ```

2. **Внешняя база данных**:
   ```env
   POSTGRES_HOST=your-db-host.com
   POSTGRES_PORT=5432
   POSTGRES_SSL=true
   ```

### Вертикальное масштабирование

1. **Увеличение ресурсов**:
   ```yaml
   services:
     calculation-service:
       deploy:
         resources:
           limits:
             memory: 4G
             cpus: '2.0'
   ```

2. **Оптимизация кода**:
   - Использование кэширования
   - Асинхронная обработка
   - Пакетная обработка
EOF

    log_success "Документация создана"
}

# Создание конфигурационных шаблонов
create_config_templates() {
    log_info "Создание конфигурационных шаблонов..."
    
    # Шаблон .env
    cat > "$PACKAGE_DIR/configs/.env.template" << 'EOF'
# AI-НК - Шаблон конфигурации
# Скопируйте этот файл в .env и настройте под ваши нужды

# Основные настройки
PROJECT_NAME=AI-НК
PROJECT_VERSION=1.0.0
ENVIRONMENT=production
DEBUG=false

# База данных
POSTGRES_DB=norms_db
POSTGRES_USER=norms_user
POSTGRES_PASSWORD=CHANGE_ME
POSTGRES_HOST=norms-db
POSTGRES_PORT=5432

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=CHANGE_ME

# Qdrant
QDRANT_HOST=qdrant
QDRANT_PORT=6333
QDRANT_API_KEY=CHANGE_ME

# Keycloak
KEYCLOAK_ADMIN_USER=admin
KEYCLOAK_ADMIN_PASSWORD=CHANGE_ME
KEYCLOAK_DB_PASSWORD=CHANGE_ME

# JWT
JWT_SECRET_KEY=CHANGE_ME
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# API Gateway
GATEWAY_HOST=localhost
GATEWAY_PORT=80
GATEWAY_SSL_PORT=443

# Сервисы
CALCULATION_SERVICE_PORT=8002
RAG_SERVICE_PORT=8003
CHAT_SERVICE_PORT=8004
DOCUMENT_PARSER_PORT=8005
VLLM_SERVICE_PORT=8006
FRONTEND_PORT=3000

# SSL
SSL_ENABLED=true
SSL_CERT_PATH=/app/ssl/certs/cert.pem
SSL_KEY_PATH=/app/ssl/keys/key.pem

# Логирование
LOG_LEVEL=INFO
LOG_FORMAT=json

# Мониторинг
PROMETHEUS_PORT=9090
GRAFANA_PORT=3001

# Резервное копирование
BACKUP_RETENTION_DAYS=30
BACKUP_SCHEDULE="0 2 * * *"

# Безопасность
CORS_ORIGINS=["https://localhost", "https://yourdomain.com"]
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# Файлы
MAX_FILE_SIZE=100MB
ALLOWED_FILE_TYPES=["pdf", "doc", "docx", "txt", "rtf"]

# AI модели
DEFAULT_MODEL=gpt-3.5-turbo
MODEL_TEMPERATURE=0.7
MAX_TOKENS=4000

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=
EMAIL_PASSWORD=
EMAIL_USE_TLS=true

# Интеграции
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
OLLAMA_HOST=http://ollama:11434
EOF

    # Шаблон nginx.conf
    cat > "$PACKAGE_DIR/configs/nginx.conf.template" << 'EOF'
# AI-НК - Шаблон конфигурации Nginx

events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    # Логирование
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log;

    # Основные настройки
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    # Gzip сжатие
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;

    # Ограничения
    client_max_body_size 100M;
    client_body_timeout 60s;
    client_header_timeout 60s;

    # Upstream серверы
    upstream gateway {
        server gateway:80;
    }

    upstream frontend {
        server frontend:80;
    }

    # HTTP сервер (редирект на HTTPS)
    server {
        listen 80;
        server_name localhost yourdomain.com;
        return 301 https://$server_name$request_uri;
    }

    # HTTPS сервер
    server {
        listen 443 ssl http2;
        server_name localhost yourdomain.com;

        # SSL сертификаты
        ssl_certificate /app/ssl/certs/cert.pem;
        ssl_certificate_key /app/ssl/keys/key.pem;

        # SSL настройки
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;
        ssl_session_cache shared:SSL:10m;
        ssl_session_timeout 10m;

        # Безопасность
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

        # API Gateway
        location /api/ {
            proxy_pass http://gateway;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        # Keycloak
        location /auth/ {
            proxy_pass http://gateway;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Frontend
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Статические файлы
        location /static/ {
            alias /app/frontend/build/static/;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
}
EOF

    # Шаблон docker-compose для продакшна
    cat > "$PACKAGE_DIR/configs/docker-compose.prod.template" << 'EOF'
# AI-НК - Шаблон Docker Compose для продакшна
# Скопируйте этот файл в docker-compose.prod.yaml и настройте

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
      - ./configs/postgresql/postgresql.conf:/etc/postgresql/postgresql.conf
    command: postgres -c config_file=/etc/postgresql/postgresql.conf
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'

  # Redis
  redis:
    image: redis:7-alpine
    container_name: ai-nk-redis
    command: redis-server --requirepass ${REDIS_PASSWORD} --appendonly yes
    volumes:
      - redis_data:/data
      - ./configs/redis/redis.conf:/usr/local/etc/redis/redis.conf
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'

  # Qdrant
  qdrant:
    image: qdrant/qdrant:latest
    container_name: ai-nk-qdrant
    volumes:
      - qdrant_data:/qdrant/storage
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:6333/health"]
      interval: 10s
      timeout: 5s
      retries: 5
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '1.0'

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
    volumes:
      - ./logs/gateway:/app/logs
    restart: unless-stopped
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
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'

  # Остальные сервисы...
  # (calculation-service, rag-service, chat-service, etc.)

volumes:
  norms_db_data:
  redis_data:
  qdrant_data:

networks:
  default:
    name: ai-nk-network
    driver: bridge
EOF

    log_success "Конфигурационные шаблоны созданы"
}

# Создание архива
create_archive() {
    log_info "Создание архива пакета..."
    
    cd ai-nk-deployment/packages
    
    # Создание tar.gz архива
    tar -czf "${PACKAGE_NAME}.tar.gz" "$PACKAGE_NAME"
    
    # Создание zip архива
    zip -r "${PACKAGE_NAME}.zip" "$PACKAGE_NAME"
    
    # Создание checksums
    md5sum "${PACKAGE_NAME}.tar.gz" > "${PACKAGE_NAME}.tar.gz.md5"
    md5sum "${PACKAGE_NAME}.zip" > "${PACKAGE_NAME}.zip.md5"
    
    sha256sum "${PACKAGE_NAME}.tar.gz" > "${PACKAGE_NAME}.tar.gz.sha256"
    sha256sum "${PACKAGE_NAME}.zip" > "${PACKAGE_NAME}.zip.sha256"
    
    # Удаление исходной папки
    rm -rf "$PACKAGE_NAME"
    
    cd ../..
    
    log_success "Архив создан: ai-nk-deployment/packages/${PACKAGE_NAME}.tar.gz"
    log_success "Архив создан: ai-nk-deployment/packages/${PACKAGE_NAME}.zip"
}

# Создание информации о пакете
create_package_info() {
    log_info "Создание информации о пакете..."
    
    cat > "ai-nk-deployment/packages/PACKAGE_INFO.md" << EOF
# AI-НК - Информация о пакетах

## Доступные пакеты

### ${PACKAGE_NAME}

- **Дата создания**: $(date)
- **Версия**: 1.0.0
- **Размер**: $(du -h "ai-nk-deployment/packages/${PACKAGE_NAME}.tar.gz" | cut -f1)
- **Формат**: tar.gz, zip

### Содержимое пакета

- Исходный код всех сервисов
- Скрипты установки и управления
- Конфигурационные шаблоны
- Документация
- Docker Compose файлы

### Установка

1. **Распаковка**:
   ```bash
   tar -xzf ${PACKAGE_NAME}.tar.gz
   cd ${PACKAGE_NAME}
   ```

2. **Установка**:
   ```bash
   ./install.sh
   ```

3. **Запуск**:
   ```bash
   cd ai-nk
   ./start.sh
   ```

### Проверка целостности

```bash
# MD5
md5sum -c ${PACKAGE_NAME}.tar.gz.md5

# SHA256
sha256sum -c ${PACKAGE_NAME}.tar.gz.sha256
```

### Системные требования

- Docker 20.10+
- Docker Compose 2.0+
- 8GB+ RAM
- 50GB+ свободного места
- Linux/macOS

### Поддержка

- Документация: docs/
- Установка: docs/INSTALLATION.md
- Настройка: docs/CONFIGURATION.md
- Поддержка: support@ai-nk.ru
EOF

    log_success "Информация о пакете создана"
}

# Основная функция
main() {
    echo "📦 AI-НК - Создание пакета для развертывания"
    echo "============================================="
    echo ""
    
    create_package_structure
    copy_source_code
    copy_installation_scripts
    create_documentation
    create_config_templates
    create_archive
    create_package_info
    
    echo ""
    echo "✅ Пакет создан успешно!"
    echo ""
    echo "📦 Файлы пакета:"
    echo "- ai-nk-deployment/packages/${PACKAGE_NAME}.tar.gz"
    echo "- ai-nk-deployment/packages/${PACKAGE_NAME}.zip"
    echo ""
    echo "📋 Информация:"
    echo "- ai-nk-deployment/packages/PACKAGE_INFO.md"
    echo ""
    echo "🚀 Готово к развертыванию!"
}

# Запуск
main "$@"
