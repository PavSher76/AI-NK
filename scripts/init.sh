#!/bin/bash

# Скрипт инициализации AI-NK системы
set -e

echo "🔧 Инициализация AI-NK системы..."

# Создаем необходимые директории
mkdir -p /app/uploads /app/temp /app/logs /app/data /app/reports /app/models

# Устанавливаем права доступа
chown -R ai-nk:ai-nk /app
chmod -R 755 /app

# Инициализация базы данных (если используется внешняя БД)
if [ -n "$POSTGRES_HOST" ] && [ -n "$POSTGRES_DB" ]; then
    echo "🗄️  Инициализация базы данных..."
    
    # Ждем готовности PostgreSQL
    echo "⏳ Ожидание готовности PostgreSQL..."
    until pg_isready -h "$POSTGRES_HOST" -p "${POSTGRES_PORT:-5432}" -U "$POSTGRES_USER"; do
        echo "   PostgreSQL не готов, ожидание..."
        sleep 2
    done
    
    # Выполняем SQL скрипты инициализации
    if [ -d "/app/sql" ]; then
        echo "📝 Выполнение SQL скриптов..."
        for sql_file in /app/sql/*.sql; do
            if [ -f "$sql_file" ]; then
                echo "   Выполнение $(basename "$sql_file")..."
                PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "${POSTGRES_PORT:-5432}" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f "$sql_file"
            fi
        done
    fi
fi

# Инициализация Qdrant (если используется)
if [ -n "$QDRANT_HOST" ]; then
    echo "🔍 Инициализация Qdrant..."
    
    # Ждем готовности Qdrant
    echo "⏳ Ожидание готовности Qdrant..."
    until curl -f "http://$QDRANT_HOST:${QDRANT_PORT:-6333}/health" >/dev/null 2>&1; do
        echo "   Qdrant не готов, ожидание..."
        sleep 2
    done
fi

# Инициализация Redis (если используется)
if [ -n "$REDIS_HOST" ]; then
    echo "🔴 Инициализация Redis..."
    
    # Ждем готовности Redis
    echo "⏳ Ожидание готовности Redis..."
    until redis-cli -h "$REDIS_HOST" -p "${REDIS_PORT:-6379}" ping >/dev/null 2>&1; do
        echo "   Redis не готов, ожидание..."
        sleep 2
    done
fi

# Создание конфигурационных файлов
echo "⚙️  Создание конфигурационных файлов..."

# Создаем .env файл для сервисов
cat > /app/.env << EOF
# Database Configuration
POSTGRES_HOST=${POSTGRES_HOST:-localhost}
POSTGRES_PORT=${POSTGRES_PORT:-5432}
POSTGRES_DB=${POSTGRES_DB:-norms_db}
POSTGRES_USER=${POSTGRES_USER:-norms_user}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-norms_password}

# Redis Configuration
REDIS_HOST=${REDIS_HOST:-localhost}
REDIS_PORT=${REDIS_PORT:-6379}
REDIS_PASSWORD=${REDIS_PASSWORD:-redispass}

# Qdrant Configuration
QDRANT_HOST=${QDRANT_HOST:-localhost}
QDRANT_PORT=${QDRANT_PORT:-6333}

# Service URLs
GATEWAY_URL=${GATEWAY_URL:-https://localhost:8443}
DOCUMENT_PARSER_URL=${DOCUMENT_PARSER_URL:-http://localhost:8001}
RAG_SERVICE_URL=${RAG_SERVICE_URL:-http://localhost:8003}
RULE_ENGINE_URL=${RULE_ENGINE_URL:-http://localhost:8002}
CALCULATION_SERVICE_URL=${CALCULATION_SERVICE_URL:-http://localhost:8004}
VLLM_SERVICE_URL=${VLLM_SERVICE_URL:-http://localhost:8005}
OUTGOING_CONTROL_SERVICE_URL=${OUTGOING_CONTROL_SERVICE_URL:-http://localhost:8006}
SPELLCHECKER_SERVICE_URL=${SPELLCHECKER_SERVICE_URL:-http://localhost:8007}

# Security
JWT_SECRET_KEY=${JWT_SECRET_KEY:-your-secret-key-here}
JWT_ALGORITHM=${JWT_ALGORITHM:-HS256}
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=${JWT_ACCESS_TOKEN_EXPIRE_MINUTES:-30}

# File Upload Limits
MAX_FILE_SIZE=${MAX_FILE_SIZE:-104857600}
MAX_CHECKABLE_DOCUMENT_SIZE=${MAX_CHECKABLE_DOCUMENT_SIZE:-104857600}
MAX_NORMATIVE_DOCUMENT_SIZE=${MAX_NORMATIVE_DOCUMENT_SIZE:-209715200}

# Timeouts
LLM_REQUEST_TIMEOUT=${LLM_REQUEST_TIMEOUT:-120}
PAGE_PROCESSING_TIMEOUT=${PAGE_PROCESSING_TIMEOUT:-300}

# Logging
LOG_LEVEL=${LOG_LEVEL:-INFO}
TZ=${TZ:-Europe/Moscow}
EOF

# Создаем конфигурацию Nginx
cat > /etc/nginx/conf.d/ai-nk.conf << 'EOF'
upstream document_parser {
    server localhost:8001;
}

upstream rag_service {
    server localhost:8003;
}

upstream rule_engine {
    server localhost:8002;
}

upstream calculation_service {
    server localhost:8004;
}

upstream vllm_service {
    server localhost:8005;
}

upstream outgoing_control_service {
    server localhost:8006;
}

upstream spellchecker_service {
    server localhost:8007;
}

upstream gateway {
    server localhost:8443;
}

server {
    listen 80;
    server_name localhost;
    
    # Frontend
    location / {
        root /app/frontend/build;
        index index.html;
        try_files $uri $uri/ /index.html;
    }
    
    # API Gateway
    location /api/ {
        proxy_pass https://gateway/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_ssl_verify off;
    }
    
    # Health check
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
    
    # Static files
    location /static/ {
        alias /app/frontend/build/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}

server {
    listen 443 ssl;
    server_name localhost;
    
    ssl_certificate /app/ssl/frontend.crt;
    ssl_certificate_key /app/ssl/frontend.key;
    
    # Frontend
    location / {
        root /app/frontend/build;
        index index.html;
        try_files $uri $uri/ /index.html;
    }
    
    # API Gateway
    location /api/ {
        proxy_pass https://gateway/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_ssl_verify off;
    }
    
    # Health check
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
EOF

echo "✅ Инициализация завершена!"