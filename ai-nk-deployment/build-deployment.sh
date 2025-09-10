#!/bin/bash

# AI-НК - Создание полного пакета развертывания
# Создает готовый к развертыванию пакет со всеми необходимыми файлами

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
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
PACKAGE_NAME="ai-nk-deployment-${TIMESTAMP}"
PACKAGE_DIR="ai-nk-deployment/packages/${PACKAGE_NAME}"

# Создание структуры пакета
create_package_structure() {
    log_info "Создание структуры пакета..."
    
    mkdir -p "$PACKAGE_DIR"
    mkdir -p "$PACKAGE_DIR/ai-nk"
    mkdir -p "$PACKAGE_DIR/scripts"
    mkdir -p "$PACKAGE_DIR/docs"
    mkdir -p "$PACKAGE_DIR/configs"
    mkdir -p "$PACKAGE_DIR/examples"
    
    log_success "Структура пакета создана"
}

# Копирование исходного кода
copy_source_code() {
    log_info "Копирование исходного кода..."
    
    # Переход в корневую директорию проекта
    cd ..
    
    # Основные сервисы
    cp -r calculation_service "ai-nk-deployment/packages/$PACKAGE_NAME/ai-nk/"
    cp -r rag_service "ai-nk-deployment/packages/$PACKAGE_NAME/ai-nk/"
    cp -r chat_service "ai-nk-deployment/packages/$PACKAGE_NAME/ai-nk/"
    cp -r gateway "ai-nk-deployment/packages/$PACKAGE_NAME/ai-nk/"
    cp -r frontend "ai-nk-deployment/packages/$PACKAGE_NAME/ai-nk/"
    cp -r keycloak "ai-nk-deployment/packages/$PACKAGE_NAME/ai-nk/"
    cp -r document_parser "ai-nk-deployment/packages/$PACKAGE_NAME/ai-nk/"
    cp -r vllm_service "ai-nk-deployment/packages/$PACKAGE_NAME/ai-nk/"
    cp -r rule_engine "ai-nk-deployment/packages/$PACKAGE_NAME/ai-nk/"
    
    # Конфигурационные файлы
    cp docker-compose.yaml "ai-nk-deployment/packages/$PACKAGE_NAME/ai-nk/"
    cp docker-compose.prod.yaml "ai-nk-deployment/packages/$PACKAGE_NAME/ai-nk/"
    cp nginx.conf "ai-nk-deployment/packages/$PACKAGE_NAME/ai-nk/"
    cp config.py "ai-nk-deployment/packages/$PACKAGE_NAME/ai-nk/"
    
    # SQL скрипты
    cp -r sql "ai-nk-deployment/packages/$PACKAGE_NAME/ai-nk/"
    
    # Конфигурации
    cp -r configs "ai-nk-deployment/packages/$PACKAGE_NAME/ai-nk/"
    
    # Документация
    cp README.md "ai-nk-deployment/packages/$PACKAGE_NAME/ai-nk/"
    cp LICENSE "ai-nk-deployment/packages/$PACKAGE_NAME/ai-nk/"
    cp CHANGELOG.md "ai-nk-deployment/packages/$PACKAGE_NAME/ai-nk/"
    cp DEPLOYMENT.md "ai-nk-deployment/packages/$PACKAGE_NAME/ai-nk/"
    cp INSTALLATION_GUIDE.md "ai-nk-deployment/packages/$PACKAGE_NAME/ai-nk/"
    
    # Возврат в директорию скрипта
    cd ai-nk-deployment
    
    log_success "Исходный код скопирован"
}

# Копирование скриптов
copy_scripts() {
    log_info "Копирование скриптов..."
    
    cp scripts/install.sh "$PACKAGE_DIR/scripts/"
    cp scripts/quick-deploy.sh "$PACKAGE_DIR/scripts/"
    cp scripts/create-package.sh "$PACKAGE_DIR/scripts/"
    
    # Создание главного скрипта установки
    cat > "$PACKAGE_DIR/install.sh" << 'EOF'
#!/bin/bash

# AI-НК - Главный скрипт установки
set -e

echo "🚀 AI-НК - Установка системы нормоконтроля"
echo "=========================================="

# Проверка аргументов
MODE=${1:-production}

if [ "$MODE" = "dev" ] || [ "$MODE" = "development" ]; then
    echo "🔧 Режим разработки"
    chmod +x scripts/quick-deploy.sh
    ./scripts/quick-deploy.sh
else
    echo "🏭 Продакшн режим"
    chmod +x scripts/install.sh
    ./scripts/install.sh
fi

echo "✅ Установка завершена!"
EOF

    chmod +x "$PACKAGE_DIR/install.sh"
    chmod +x "$PACKAGE_DIR/scripts/"*.sh
    
    log_success "Скрипты скопированы"
}

# Создание документации
create_documentation() {
    log_info "Создание документации..."
    
    # Основной README
    cat > "$PACKAGE_DIR/README.md" << 'EOF'
# AI-НК - Система нормоконтроля

## Описание

AI-НК - это комплексная система нормоконтроля с использованием искусственного интеллекта для анализа строительной документации и обеспечения соответствия нормативным требованиям.

## Возможности

- 📄 **Анализ документов**: Автоматический анализ строительной документации
- 🔍 **Нормоконтроль**: Проверка соответствия нормативным требованиям
- 🧮 **Инженерные расчеты**: Выполнение различных типов расчетов
- 💬 **Чат-бот**: Интеллектуальный помощник для консультаций
- 📊 **Отчеты**: Генерация детальных отчетов и рекомендаций
- 🔐 **Безопасность**: Надежная аутентификация и авторизация
- 📈 **Мониторинг**: Полный мониторинг системы и производительности

## Архитектура

Система построена на микросервисной архитектуре:

- **API Gateway** - единая точка входа для всех API
- **Calculation Service** - сервис инженерных расчетов
- **RAG Service** - сервис поиска и анализа документов
- **Chat Service** - сервис чат-бота
- **Document Parser** - сервис парсинга документов
- **VLLM Service** - сервис языковых моделей
- **Frontend** - веб-интерфейс пользователя

## Быстрый старт

### Автоматическая установка

1. **Запуск установщика**:
   ```bash
   ./install.sh
   ```

2. **Запуск системы**:
   ```bash
   cd ai-nk
   ./start.sh
   ```

3. **Доступ к системе**:
   - Веб-интерфейс: https://localhost
   - API: https://localhost/api

### Быстрое развертывание для разработки

```bash
./install.sh dev
```

## Системные требования

### Минимальные требования
- **ОС**: Linux (Ubuntu 20.04+) или macOS (10.15+)
- **RAM**: 8GB
- **Диск**: 50GB свободного места
- **CPU**: 4 ядра
- **Docker**: 20.10+
- **Docker Compose**: 2.0+

### Рекомендуемые требования
- **ОС**: Linux (Ubuntu 22.04+) или macOS (12+)
- **RAM**: 16GB+
- **Диск**: 100GB+ SSD
- **CPU**: 8+ ядер

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

```env
# Основные настройки
PROJECT_NAME=AI-НК
ENVIRONMENT=production
DEBUG=false

# База данных
POSTGRES_DB=norms_db
POSTGRES_USER=norms_user
POSTGRES_PASSWORD=secure_password

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=secure_password

# JWT
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
```

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

### Prometheus и Grafana

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001 (admin/admin)

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

## API

### Основные эндпоинты

- `GET /api/health` - проверка здоровья системы
- `POST /api/auth/login` - аутентификация
- `GET /api/documents` - список документов
- `POST /api/documents/upload` - загрузка документа
- `POST /api/calculations/execute` - выполнение расчета
- `GET /api/chat/message` - отправка сообщения в чат

### Документация API

Полная документация API доступна по адресу: https://localhost/api/docs

## Разработка

### Локальная разработка

1. **Клонирование репозитория**:
   ```bash
   git clone <repository-url>
   cd ai-nk
   ```

2. **Запуск в режиме разработки**:
   ```bash
   ./start.sh dev
   ```

3. **Разработка сервисов**:
   ```bash
   # Пересборка конкретного сервиса
   docker-compose up -d --build calculation-service
   ```

### Структура проекта

```
ai-nk/
├── calculation_service/    # Сервис расчетов
├── rag_service/           # RAG сервис
├── chat_service/          # Чат сервис
├── gateway/               # API Gateway
├── frontend/              # Веб-интерфейс
├── keycloak/              # Аутентификация
├── document_parser/       # Парсер документов
├── vllm_service/          # Языковые модели
├── rule_engine/           # Движок правил
├── sql/                   # SQL скрипты
├── configs/               # Конфигурации
├── scripts/               # Скрипты управления
└── docs/                  # Документация
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

- **Документация**: [docs/](docs/)
- **Поддержка**: support@ai-nk.ru
- **Баг-трекер**: https://github.com/ai-nk/issues
- **Форум**: https://forum.ai-nk.ru

## Лицензия

Проект распространяется под лицензией MIT. См. файл [LICENSE](LICENSE).

## Авторы

- AI-НК Team
- Контрибьюторы: [CONTRIBUTORS.md](CONTRIBUTORS.md)

## Changelog

История изменений доступна в файле [CHANGELOG.md](CHANGELOG.md).
EOF

    # Руководство по установке
    cat > "$PACKAGE_DIR/docs/INSTALLATION.md" << 'EOF'
# Руководство по установке AI-НК

## Обзор

Это руководство поможет вам установить и настроить систему AI-НК на вашем сервере.

## Системные требования

### Минимальные требования
- **ОС**: Linux (Ubuntu 20.04+) или macOS (10.15+)
- **RAM**: 8GB
- **Диск**: 50GB свободного места
- **CPU**: 4 ядра
- **Docker**: 20.10+
- **Docker Compose**: 2.0+

### Рекомендуемые требования
- **ОС**: Linux (Ubuntu 22.04+) или macOS (12+)
- **RAM**: 16GB+
- **Диск**: 100GB+ SSD
- **CPU**: 8+ ядер

## Предварительная подготовка

### Установка Docker

#### Ubuntu/Debian
```bash
# Обновление пакетов
sudo apt-get update

# Установка зависимостей
sudo apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release

# Добавление GPG ключа Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Добавление репозитория Docker
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Установка Docker
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io

# Добавление пользователя в группу docker
sudo usermod -aG docker $USER
```

#### macOS
```bash
# Установка Homebrew (если не установлен)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Установка Docker Desktop
brew install --cask docker
```

### Установка Docker Compose

```bash
# Ubuntu/Debian
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# macOS
brew install docker-compose
```

### Проверка установки

```bash
# Проверка Docker
docker --version
docker-compose --version

# Проверка прав
docker run hello-world
```

## Установка AI-НК

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

1. **Создание структуры проекта**:
   ```bash
   mkdir -p ai-nk/{data,logs,ssl,uploads,backups}
   mkdir -p ai-nk/data/{postgres,redis,qdrant}
   mkdir -p ai-nk/logs/{gateway,calculation-service,rag-service,chat-service,frontend}
   mkdir -p ai-nk/ssl/{certs,keys}
   mkdir -p ai-nk/uploads/{documents,reports}
   mkdir -p ai-nk/backups/{database,configs}
   ```

2. **Копирование файлов**:
   ```bash
   cp -r calculation_service ai-nk/
   cp -r rag_service ai-nk/
   cp -r chat_service ai-nk/
   cp -r gateway ai-nk/
   cp -r frontend ai-nk/
   cp -r keycloak ai-nk/
   cp -r document_parser ai-nk/
   cp -r vllm_service ai-nk/
   cp -r rule_engine ai-nk/
   cp docker-compose.yaml ai-nk/
   cp docker-compose.prod.yaml ai-nk/
   cp nginx.conf ai-nk/
   cp config.py ai-nk/
   cp -r sql ai-nk/
   cp -r configs ai-nk/
   ```

3. **Создание конфигурации**:
   ```bash
   cp configs/.env.template ai-nk/.env
   # Отредактируйте .env файл
   ```

4. **Генерация SSL сертификатов**:
   ```bash
   cd ai-nk/ssl
   openssl req -x509 -newkey rsa:4096 -keyout keys/key.pem -out certs/cert.pem \
     -days 365 -nodes -subj "/C=RU/ST=Moscow/L=Moscow/O=AI-НК/OU=IT/CN=localhost"
   chmod 600 keys/*.pem
   chmod 644 certs/*.pem
   cd ../..
   ```

5. **Запуск сервисов**:
   ```bash
   cd ai-nk
   docker-compose up -d
   ```

## Проверка установки

### Проверка статуса сервисов

```bash
# Статус контейнеров
docker-compose ps

# Логи сервисов
docker-compose logs

# Проверка здоровья
curl -f http://localhost/health
```

### Проверка веб-интерфейса

1. Откройте браузер
2. Перейдите по адресу: https://localhost
3. Должен загрузиться интерфейс AI-НК

### Проверка API

```bash
# Проверка API Gateway
curl -f https://localhost/api/health

# Проверка сервиса расчетов
curl -f https://localhost/api/calculations/types

# Проверка RAG сервиса
curl -f https://localhost/api/rag/health
```

## Настройка после установки

### Создание администратора

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

### Настройка Keycloak

1. Откройте https://localhost/auth
2. Войдите как администратор (admin / пароль из .env)
3. Создайте realm для AI-НК
4. Настройте клиентов и роли

### Настройка мониторинга

1. **Prometheus**: http://localhost:9090
2. **Grafana**: http://localhost:3001 (admin/admin)
3. Импортируйте дашборды из `configs/grafana/`

## Устранение неполадок

### Проблемы с Docker

```bash
# Перезапуск Docker
sudo systemctl restart docker

# Очистка Docker
docker system prune -a

# Проверка логов Docker
sudo journalctl -u docker.service
```

### Проблемы с портами

```bash
# Проверка занятых портов
netstat -tulpn | grep -E ':(80|443|5432|6379)'

# Освобождение портов
sudo fuser -k 80/tcp
sudo fuser -k 443/tcp
```

### Проблемы с базой данных

```bash
# Сброс базы данных
docker-compose down
docker volume rm ai-nk_norms_db_data
docker-compose up -d

# Проверка подключения к базе данных
docker-compose exec norms-db psql -U norms_user -d norms_db -c "SELECT version();"
```

### Проблемы с SSL

```bash
# Проверка сертификатов
openssl x509 -in ssl/certs/cert.pem -text -noout

# Перегенерация сертификатов
rm ssl/certs/cert.pem ssl/keys/key.pem
openssl req -x509 -newkey rsa:4096 -keyout ssl/keys/key.pem -out ssl/certs/cert.pem \
  -days 365 -nodes -subj "/C=RU/ST=Moscow/L=Moscow/O=AI-НК/OU=IT/CN=localhost"
```

## Обновление

### Автоматическое обновление

```bash
# Создание резервной копии
./backup.sh

# Обновление системы
./update.sh
```

### Ручное обновление

1. **Остановка сервисов**:
   ```bash
   ./stop.sh
   ```

2. **Обновление кода**:
   ```bash
   git pull origin main
   ```

3. **Обновление образов**:
   ```bash
   docker-compose pull
   ```

4. **Запуск сервисов**:
   ```bash
   ./start.sh
   ```

## Удаление

### Полное удаление

1. **Остановка сервисов**:
   ```bash
   ./stop.sh
   ```

2. **Удаление контейнеров и томов**:
   ```bash
   docker-compose down --volumes --remove-orphans
   ```

3. **Удаление данных**:
   ```bash
   rm -rf ai-nk/
   ```

4. **Очистка Docker**:
   ```bash
   docker system prune -a
   ```

## Поддержка

При возникновении проблем:

1. Проверьте логи: `./monitor.sh`
2. Проверьте статус: `docker-compose ps`
3. Обратитесь в поддержку: support@ai-nk.ru
EOF

    log_success "Документация создана"
}

# Создание примеров
create_examples() {
    log_info "Создание примеров..."
    
    # Пример конфигурации для продакшна
    cat > "$PACKAGE_DIR/examples/production.env" << 'EOF'
# AI-НК - Пример конфигурации для продакшна

# Основные настройки
PROJECT_NAME=AI-НК
PROJECT_VERSION=1.0.0
ENVIRONMENT=production
DEBUG=false

# База данных
POSTGRES_DB=norms_db
POSTGRES_USER=norms_user
POSTGRES_PASSWORD=CHANGE_ME_SECURE_PASSWORD
POSTGRES_HOST=norms-db
POSTGRES_PORT=5432

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=CHANGE_ME_SECURE_PASSWORD

# Qdrant
QDRANT_HOST=qdrant
QDRANT_PORT=6333
QDRANT_API_KEY=CHANGE_ME_SECURE_API_KEY

# Keycloak
KEYCLOAK_ADMIN_USER=admin
KEYCLOAK_ADMIN_PASSWORD=CHANGE_ME_SECURE_PASSWORD
KEYCLOAK_DB_PASSWORD=CHANGE_ME_SECURE_PASSWORD

# JWT
JWT_SECRET_KEY=CHANGE_ME_VERY_SECURE_JWT_SECRET_KEY_64_CHARS_LONG
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# API Gateway
GATEWAY_HOST=yourdomain.com
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
CORS_ORIGINS=["https://yourdomain.com", "https://www.yourdomain.com"]
RATE_LIMIT_REQUESTS=1000
RATE_LIMIT_WINDOW=60

# Файлы
MAX_FILE_SIZE=100MB
ALLOWED_FILE_TYPES=["pdf", "doc", "docx", "txt", "rtf"]

# AI модели
DEFAULT_MODEL=gpt-4
MODEL_TEMPERATURE=0.7
MAX_TOKENS=4000

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
EMAIL_USE_TLS=true

# Интеграции
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
OLLAMA_HOST=http://ollama:11434
EOF

    # Пример скрипта для автоматического развертывания
    cat > "$PACKAGE_DIR/examples/auto-deploy.sh" << 'EOF'
#!/bin/bash

# AI-НК - Автоматическое развертывание
# Пример скрипта для автоматического развертывания на сервере

set -e

# Конфигурация
DOMAIN="yourdomain.com"
EMAIL="admin@yourdomain.com"
DB_PASSWORD=$(openssl rand -base64 32)
REDIS_PASSWORD=$(openssl rand -base64 32)
JWT_SECRET=$(openssl rand -base64 64)

echo "🚀 Автоматическое развертывание AI-НК на $DOMAIN"

# Обновление системы
echo "📦 Обновление системы..."
apt-get update
apt-get upgrade -y

# Установка зависимостей
echo "🔧 Установка зависимостей..."
apt-get install -y curl wget git unzip

# Установка Docker
echo "🐳 Установка Docker..."
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
rm get-docker.sh

# Установка Docker Compose
echo "📦 Установка Docker Compose..."
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Создание пользователя для AI-НК
echo "👤 Создание пользователя..."
useradd -m -s /bin/bash ai-nk
usermod -aG docker ai-nk

# Клонирование репозитория
echo "📥 Клонирование репозитория..."
sudo -u ai-nk git clone <repository-url> /home/ai-nk/ai-nk
cd /home/ai-nk/ai-nk

# Создание конфигурации
echo "⚙️ Создание конфигурации..."
sudo -u ai-nk cp examples/production.env .env
sudo -u ai-nk sed -i "s/yourdomain.com/$DOMAIN/g" .env
sudo -u ai-nk sed -i "s/CHANGE_ME_SECURE_PASSWORD/$DB_PASSWORD/g" .env
sudo -u ai-nk sed -i "s/CHANGE_ME_SECURE_API_KEY/$REDIS_PASSWORD/g" .env
sudo -u ai-nk sed -i "s/CHANGE_ME_VERY_SECURE_JWT_SECRET_KEY_64_CHARS_LONG/$JWT_SECRET/g" .env

# Генерация SSL сертификатов
echo "🔐 Генерация SSL сертификатов..."
sudo -u ai-nk mkdir -p ssl/{certs,keys}
sudo -u ai-nk openssl req -x509 -newkey rsa:4096 -keyout ssl/keys/key.pem -out ssl/certs/cert.pem \
  -days 365 -nodes -subj "/C=RU/ST=Moscow/L=Moscow/O=AI-НК/OU=IT/CN=$DOMAIN"

# Запуск сервисов
echo "🚀 Запуск сервисов..."
sudo -u ai-nk docker-compose up -d

# Ожидание готовности
echo "⏳ Ожидание готовности сервисов..."
sleep 60

# Проверка статуса
echo "🔍 Проверка статуса..."
sudo -u ai-nk docker-compose ps

echo "✅ Развертывание завершено!"
echo "🌐 Веб-интерфейс: https://$DOMAIN"
echo "📊 API: https://$DOMAIN/api"
echo "🔐 Keycloak: https://$DOMAIN/auth"
EOF

    chmod +x "$PACKAGE_DIR/examples/auto-deploy.sh"
    
    log_success "Примеры созданы"
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
    
    # Создание информации о пакете
    cat > "${PACKAGE_NAME}.info" << EOF
AI-НК Deployment Package Information
====================================

Package Name: ${PACKAGE_NAME}
Created: $(date)
Version: 1.0.0
Size: $(du -h "${PACKAGE_NAME}.tar.gz" | cut -f1)

Contents:
- Complete AI-НК source code
- Installation scripts
- Configuration templates
- Documentation
- Examples
- Docker Compose files

Installation:
1. Extract: tar -xzf ${PACKAGE_NAME}.tar.gz
2. Install: cd ${PACKAGE_NAME} && ./install.sh
3. Start: cd ai-nk && ./start.sh

System Requirements:
- Docker 20.10+
- Docker Compose 2.0+
- 8GB+ RAM
- 50GB+ free space
- Linux/macOS

Support:
- Documentation: docs/
- Support: support@ai-nk.ru
- Issues: https://github.com/ai-nk/issues
EOF

    # Удаление исходной папки
    rm -rf "$PACKAGE_NAME"
    
    cd ../..
    
    log_success "Архив создан: ai-nk-deployment/packages/${PACKAGE_NAME}.tar.gz"
    log_success "Архив создан: ai-nk-deployment/packages/${PACKAGE_NAME}.zip"
}

# Создание информации о пакете
create_package_info() {
    log_info "Создание информации о пакете..."
    
    cat > "ai-nk-deployment/packages/README.md" << EOF
# AI-НК - Пакеты развертывания

## Доступные пакеты

### ${PACKAGE_NAME}

- **Дата создания**: $(date)
- **Версия**: 1.0.0
- **Размер**: $(du -h "ai-nk-deployment/packages/${PACKAGE_NAME}.tar.gz" | cut -f1)
- **Формат**: tar.gz, zip

### Содержимое пакета

- ✅ Исходный код всех сервисов
- ✅ Скрипты установки и управления
- ✅ Конфигурационные шаблоны
- ✅ Полная документация
- ✅ Docker Compose файлы
- ✅ Примеры конфигураций
- ✅ SSL сертификаты (самоподписанные)

### Установка

1. **Распаковка**:
   \`\`\`bash
   tar -xzf ${PACKAGE_NAME}.tar.gz
   cd ${PACKAGE_NAME}
   \`\`\`

2. **Установка**:
   \`\`\`bash
   ./install.sh
   \`\`\`

3. **Запуск**:
   \`\`\`bash
   cd ai-nk
   ./start.sh
   \`\`\`

### Быстрая установка для разработки

\`\`\`bash
./install.sh dev
\`\`\`

### Проверка целостности

\`\`\`bash
# MD5
md5sum -c ${PACKAGE_NAME}.tar.gz.md5

# SHA256
sha256sum -c ${PACKAGE_NAME}.tar.gz.sha256
\`\`\`

### Системные требования

- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **RAM**: 8GB+ (рекомендуется 16GB+)
- **Диск**: 50GB+ свободного места
- **ОС**: Linux (Ubuntu 20.04+) или macOS (10.15+)

### Поддержка

- **Документация**: [docs/](docs/)
- **Установка**: [docs/INSTALLATION.md](docs/INSTALLATION.md)
- **Настройка**: [docs/CONFIGURATION.md](docs/CONFIGURATION.md)
- **Поддержка**: support@ai-nk.ru
- **Баг-трекер**: https://github.com/ai-nk/issues

### Лицензия

MIT License. См. файл LICENSE.

---

**AI-НК Team** - Система нормоконтроля с использованием ИИ
EOF

    log_success "Информация о пакете создана"
}

# Основная функция
main() {
    echo "📦 AI-НК - Создание полного пакета развертывания"
    echo "================================================"
    echo ""
    
    create_package_structure
    copy_source_code
    copy_scripts
    create_documentation
    create_examples
    create_archive
    create_package_info
    
    echo ""
    echo "✅ Пакет развертывания создан успешно!"
    echo ""
    echo "📦 Файлы пакета:"
    echo "- ai-nk-deployment/packages/${PACKAGE_NAME}.tar.gz"
    echo "- ai-nk-deployment/packages/${PACKAGE_NAME}.zip"
    echo ""
    echo "📋 Информация:"
    echo "- ai-nk-deployment/packages/README.md"
    echo "- ai-nk-deployment/packages/${PACKAGE_NAME}.info"
    echo ""
    echo "🚀 Готово к развертыванию!"
    echo ""
    echo "📖 Для установки:"
    echo "1. tar -xzf ${PACKAGE_NAME}.tar.gz"
    echo "2. cd ${PACKAGE_NAME}"
    echo "3. ./install.sh"
    echo "4. cd ai-nk && ./start.sh"
}

# Запуск
main "$@"
