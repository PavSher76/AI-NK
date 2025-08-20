#!/bin/bash

# AI-НК - Система нормоконтроля
# Скрипт установки и настройки

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции для вывода
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Проверка требований
check_requirements() {
    print_info "Проверка системных требований..."
    
    # Проверка Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker не установлен. Установите Docker и попробуйте снова."
        exit 1
    fi
    
    # Проверка Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose не установлен. Установите Docker Compose и попробуйте снова."
        exit 1
    fi
    
    # Проверка версии Docker
    DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | cut -d'.' -f1)
    if [ "$DOCKER_VERSION" -lt 20 ]; then
        print_error "Требуется Docker версии 20.0 или выше."
        exit 1
    fi
    
    # Проверка доступной памяти
    MEMORY_GB=$(free -g | awk '/^Mem:/{print $2}')
    if [ "$MEMORY_GB" -lt 8 ]; then
        print_warning "Рекомендуется минимум 8GB RAM. Доступно: ${MEMORY_GB}GB"
    fi
    
    # Проверка свободного места
    DISK_GB=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
    if [ "$DISK_GB" -lt 20 ]; then
        print_warning "Рекомендуется минимум 20GB свободного места. Доступно: ${DISK_GB}GB"
    fi
    
    print_success "Системные требования проверены"
}

# Создание конфигурационных файлов
create_configs() {
    print_info "Создание конфигурационных файлов..."
    
    # Создание .env файла
    if [ ! -f .env ]; then
        cat > .env << EOF
# AI-НК Конфигурация
COMPOSE_PROJECT_NAME=ai-nk

# Базы данных
POSTGRES_DB=norms_db
POSTGRES_USER=norms_user
POSTGRES_PASSWORD=norms_password

# Redis
REDIS_PASSWORD=redispass

# Keycloak
KEYCLOAK_ADMIN=admin
KEYCLOAK_ADMIN_PASSWORD=admin

# Ollama
OLLAMA_MODEL=llama2

# Порты
FRONTEND_PORT=443
GATEWAY_PORT=8443
KEYCLOAK_PORT=8081
OLLAMA_PORT=11434
POSTGRES_PORT=5432
QDANT_PORT=6333

# Мониторинг
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
EOF
        print_success "Создан файл .env"
    fi
    
    # Создание директорий
    mkdir -p {ssl,uploads,temp,logs,backups}
    print_success "Созданы необходимые директории"
}

# Генерация SSL сертификатов
generate_ssl() {
    print_info "Генерация SSL сертификатов..."
    
    if [ ! -f ssl/frontend.crt ] || [ ! -f ssl/frontend.key ]; then
        mkdir -p ssl
        
        # Генерация самоподписанных сертификатов
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout ssl/frontend.key \
            -out ssl/frontend.crt \
            -subj "/C=RU/ST=Moscow/L=Moscow/O=AI-NK/OU=IT/CN=localhost"
        
        # Копирование для Gateway
        cp ssl/frontend.crt ssl/gateway.crt
        cp ssl/frontend.key ssl/gateway.key
        
        print_success "SSL сертификаты сгенерированы"
    else
        print_info "SSL сертификаты уже существуют"
    fi
}

# Настройка Keycloak
setup_keycloak() {
    print_info "Настройка Keycloak..."
    
    # Создание realm конфигурации
    mkdir -p keycloak
    cat > keycloak/ai-nk-realm.json << EOF
{
  "realm": "ai-nk",
  "enabled": true,
  "displayName": "AI-НК",
  "displayNameHtml": "<div class=\"kc-logo-text\"><span>AI-НК</span></div>",
  "users": [
    {
      "username": "admin",
      "enabled": true,
      "emailVerified": true,
      "firstName": "Администратор",
      "lastName": "Системы",
      "email": "admin@ai-nk.local",
      "credentials": [
        {
          "type": "password",
          "value": "admin",
          "temporary": false
        }
      ],
      "realmRoles": ["admin"]
    },
    {
      "username": "user",
      "enabled": true,
      "emailVerified": true,
      "firstName": "Пользователь",
      "lastName": "Тестовый",
      "email": "user@ai-nk.local",
      "credentials": [
        {
          "type": "password",
          "value": "password123",
          "temporary": false
        }
      ],
      "realmRoles": ["user"]
    }
  ],
  "roles": {
    "realm": [
      {
        "name": "admin",
        "description": "Администратор системы"
      },
      {
        "name": "user",
        "description": "Обычный пользователь"
      }
    ]
  },
  "clients": [
    {
      "clientId": "ai-nk-frontend",
      "enabled": true,
      "publicClient": true,
      "standardFlowEnabled": true,
      "directAccessGrantsEnabled": true,
      "redirectUris": ["https://localhost/*", "http://localhost/*"],
      "webOrigins": ["https://localhost", "http://localhost"],
      "attributes": {
        "saml.assertion.signature": "false",
        "saml.force.post.binding": "false",
        "saml.multivalued.roles": "false",
        "saml.encrypt": "false",
        "saml.server.signature": "false",
        "saml.server.signature.keyinfo.ext": "false",
        "exclude.session.state.from.auth.response": "false",
        "saml_force_name_id_format": "false",
        "saml.client.signature": "false",
        "tls.client.certificate.bound.access.tokens": "false",
        "saml.authnstatement": "false",
        "display.on.consent.screen": "false",
        "saml.onetimeuse.condition": "false"
      }
    }
  ]
}
EOF
    
    print_success "Конфигурация Keycloak создана"
}

# Загрузка модели Ollama
download_ollama_model() {
    print_info "Загрузка модели Ollama..."
    
    # Запуск Ollama для загрузки модели
    docker-compose up -d ollama
    
    # Ожидание запуска Ollama
    print_info "Ожидание запуска Ollama..."
    sleep 30
    
    # Загрузка модели
    docker-compose exec -T ollama ollama pull llama2
    
    print_success "Модель Ollama загружена"
}

# Сборка и запуск системы
build_and_start() {
    print_info "Сборка и запуск системы AI-НК..."
    
    # Остановка существующих контейнеров
    docker-compose down 2>/dev/null || true
    
    # Сборка образов
    print_info "Сборка Docker образов..."
    docker-compose build --no-cache
    
    # Запуск системы
    print_info "Запуск системы..."
    docker-compose up -d
    
    # Ожидание запуска всех сервисов
    print_info "Ожидание запуска сервисов..."
    sleep 60
    
    print_success "Система AI-НК запущена"
}

# Проверка работоспособности
health_check() {
    print_info "Проверка работоспособности системы..."
    
    # Проверка frontend
    if curl -k -s https://localhost > /dev/null; then
        print_success "Frontend доступен"
    else
        print_warning "Frontend недоступен"
    fi
    
    # Проверка Gateway
    if curl -k -s https://localhost:8443/healthz > /dev/null; then
        print_success "Gateway доступен"
    else
        print_warning "Gateway недоступен"
    fi
    
    # Проверка Keycloak
    if curl -k -s https://localhost:8081/realms/ai-nk > /dev/null; then
        print_success "Keycloak доступен"
    else
        print_warning "Keycloak недоступен"
    fi
    
    # Проверка Ollama
    if curl -s http://localhost:11434/api/tags > /dev/null; then
        print_success "Ollama доступен"
    else
        print_warning "Ollama недоступен"
    fi
}

# Создание скриптов управления
create_management_scripts() {
    print_info "Создание скриптов управления..."
    
    # Скрипт запуска
    cat > start.sh << 'EOF'
#!/bin/bash
echo "Запуск системы AI-НК..."
docker-compose up -d
echo "Система запущена. Доступна по адресу: https://localhost"
EOF
    
    # Скрипт остановки
    cat > stop.sh << 'EOF'
#!/bin/bash
echo "Остановка системы AI-НК..."
docker-compose down
echo "Система остановлена"
EOF
    
    # Скрипт перезапуска
    cat > restart.sh << 'EOF'
#!/bin/bash
echo "Перезапуск системы AI-НК..."
docker-compose down
docker-compose up -d
echo "Система перезапущена"
EOF
    
    # Скрипт просмотра логов
    cat > logs.sh << 'EOF'
#!/bin/bash
if [ -z "$1" ]; then
    echo "Просмотр всех логов..."
    docker-compose logs -f
else
    echo "Просмотр логов сервиса: $1"
    docker-compose logs -f "$1"
fi
EOF
    
    # Скрипт резервного копирования
    cat > backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "Создание резервной копии в $BACKUP_DIR..."

# Резервная копия баз данных
docker-compose exec -T norms-db pg_dump -U norms_user norms_db > "$BACKUP_DIR/norms_db.sql"
docker-compose exec -T keycloak-db pg_dump -U keycloak keycloak > "$BACKUP_DIR/keycloak_db.sql"

# Резервная копия загруженных файлов
tar -czf "$BACKUP_DIR/uploads.tar.gz" uploads/

# Резервная копия конфигурации
tar -czf "$BACKUP_DIR/config.tar.gz" .env keycloak/ ssl/

echo "Резервная копия создана: $BACKUP_DIR"
EOF
    
    # Скрипт восстановления
    cat > restore.sh << 'EOF'
#!/bin/bash
if [ -z "$1" ]; then
    echo "Использование: ./restore.sh <путь_к_резервной_копии>"
    exit 1
fi

BACKUP_DIR="$1"
if [ ! -d "$BACKUP_DIR" ]; then
    echo "Ошибка: директория $BACKUP_DIR не найдена"
    exit 1
fi

echo "Восстановление из резервной копии: $BACKUP_DIR"

# Остановка системы
docker-compose down

# Восстановление баз данных
docker-compose up -d norms-db keycloak-db
sleep 10
docker-compose exec -T norms-db psql -U norms_user -d norms_db -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
docker-compose exec -T norms-db psql -U norms_user -d norms_db < "$BACKUP_DIR/norms_db.sql"

docker-compose exec -T keycloak-db psql -U keycloak -d keycloak -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
docker-compose exec -T keycloak-db psql -U keycloak -d keycloak < "$BACKUP_DIR/keycloak_db.sql"

# Восстановление файлов
tar -xzf "$BACKUP_DIR/uploads.tar.gz"

# Восстановление конфигурации
tar -xzf "$BACKUP_DIR/config.tar.gz"

# Запуск системы
docker-compose up -d

echo "Восстановление завершено"
EOF
    
    # Делаем скрипты исполняемыми
    chmod +x start.sh stop.sh restart.sh logs.sh backup.sh restore.sh
    
    print_success "Скрипты управления созданы"
}

# Создание документации
create_documentation() {
    print_info "Создание документации..."
    
    # README
    cat > README.md << 'EOF'
# AI-НК - Система нормоконтроля

## Описание
AI-НК - это интеллектуальная система автоматизированного нормоконтроля документов, использующая искусственный интеллект для проверки соответствия нормативным требованиям.

## Возможности
- 🤖 AI-чат с загрузкой файлов
- 📄 Обработка документов (PDF, Word, Excel)
- 🔍 Нормоконтроль документов
- 📊 Аналитика и отчеты
- 🔐 Безопасная аутентификация
- 📱 Адаптивный интерфейс

## Быстрый старт

### Требования
- Docker 20.0+
- Docker Compose
- 8GB RAM (рекомендуется)
- 20GB свободного места

### Установка
```bash
# Клонирование репозитория
git clone <repository-url>
cd ai-nk

# Запуск установки
./install.sh
```

### Доступ к системе
- **Frontend**: https://localhost
- **Keycloak**: https://localhost:8081
- **Grafana**: http://localhost:3000 (admin/admin)

### Тестовые пользователи
- **Администратор**: admin/admin
- **Пользователь**: user/password123

## Управление системой

### Запуск
```bash
./start.sh
```

### Остановка
```bash
./stop.sh
```

### Перезапуск
```bash
./restart.sh
```

### Просмотр логов
```bash
./logs.sh [сервис]
```

### Резервное копирование
```bash
./backup.sh
```

### Восстановление
```bash
./restore.sh <путь_к_резервной_копии>
```

## Архитектура

### Сервисы
- **Frontend**: React.js + Nginx
- **Gateway**: FastAPI (API Gateway)
- **Document Parser**: Обработка документов
- **Rule Engine**: Проверка норм
- **RAG Service**: Поиск по нормам
- **Keycloak**: Аутентификация
- **Ollama**: LLM модели
- **PostgreSQL**: Основная БД
- **Qdrant**: Векторная БД
- **Redis**: Кэширование

### Порты
- 443: Frontend (HTTPS)
- 8443: Gateway (HTTPS)
- 8081: Keycloak
- 11434: Ollama
- 5432: PostgreSQL
- 6333: Qdrant
- 3000: Grafana
- 9090: Prometheus

## Конфигурация

### Переменные окружения
Основные настройки находятся в файле `.env`:
- Пароли баз данных
- Порты сервисов
- Настройки безопасности

### SSL сертификаты
Система использует самоподписанные сертификаты для разработки.
Для продакшена замените файлы в директории `ssl/`.

## Мониторинг

### Grafana
- URL: http://localhost:3000
- Логин: admin
- Пароль: admin

### Prometheus
- URL: http://localhost:9090

## Безопасность

### Аутентификация
- Keycloak с OIDC
- Поддержка 2FA
- Роли и разрешения

### Шифрование
- HTTPS для всех соединений
- Шифрование данных в БД
- Безопасные пароли

## Поддержка

### Логи
Логи всех сервисов доступны через:
```bash
./logs.sh [сервис]
```

### Диагностика
```bash
# Проверка состояния сервисов
docker-compose ps

# Проверка ресурсов
docker stats

# Проверка сетевых соединений
docker network ls
```

### Обновление
```bash
# Остановка системы
./stop.sh

# Обновление кода
git pull

# Пересборка и запуск
docker-compose build --no-cache
./start.sh
```

## Лицензия
[Укажите лицензию]

## Контакты
[Укажите контактную информацию]
EOF
    
    print_success "Документация создана"
}

# Основная функция
main() {
    echo "=========================================="
    echo "    AI-НК - Установка системы нормоконтроля"
    echo "=========================================="
    echo ""
    
    # Проверка прав администратора
    if [ "$EUID" -eq 0 ]; then
        print_warning "Скрипт запущен с правами root. Рекомендуется запуск от обычного пользователя."
    fi
    
    # Выполнение этапов установки
    check_requirements
    create_configs
    generate_ssl
    setup_keycloak
    build_and_start
    download_ollama_model
    create_management_scripts
    create_documentation
    health_check
    
    echo ""
    echo "=========================================="
    print_success "Установка завершена успешно!"
    echo "=========================================="
    echo ""
    echo "🌐 Frontend: https://localhost"
    echo "🔐 Keycloak: https://localhost:8081"
    echo "📊 Grafana: http://localhost:3000"
    echo ""
    echo "👤 Тестовые пользователи:"
    echo "   Администратор: admin/admin"
    echo "   Пользователь: user/password123"
    echo ""
    echo "📖 Документация: README.md"
    echo "🛠  Скрипты управления: ./start.sh, ./stop.sh, ./restore.sh"
    echo ""
    print_info "Для начала работы откройте https://localhost"
}

# Запуск основной функции
main "$@"
