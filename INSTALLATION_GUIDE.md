# 📋 Руководство по установке системы AI-НК

## 🎯 Обзор

AI-НК - это интеллектуальная система автоматизированного нормоконтроля документов, использующая искусственный интеллект для проверки соответствия нормативным требованиям.

## 📋 Системные требования

### Минимальные требования:
- **ОС**: Linux (Ubuntu 20.04+, CentOS 8+, RHEL 8+), macOS 10.15+, Windows 10/11 с WSL2
- **RAM**: 8GB (рекомендуется 16GB)
- **CPU**: 4 ядра (рекомендуется 8+ ядер)
- **Диск**: 20GB свободного места (рекомендуется 50GB+)
- **Docker**: 20.0+
- **Docker Compose**: 2.0+

### Рекомендуемые требования:
- **RAM**: 16GB+
- **CPU**: 8+ ядер
- **Диск**: SSD 100GB+
- **Сеть**: Стабильное интернет-соединение для загрузки моделей

## 🔧 Подготовка системы

### 1. Установка Docker

#### Ubuntu/Debian:
```bash
# Обновление пакетов
sudo apt update

# Установка зависимостей
sudo apt install -y apt-transport-https ca-certificates curl gnupg lsb-release

# Добавление GPG ключа Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Добавление репозитория Docker
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Установка Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io

# Добавление пользователя в группу docker
sudo usermod -aG docker $USER

# Запуск Docker
sudo systemctl start docker
sudo systemctl enable docker
```

#### CentOS/RHEL:
```bash
# Установка зависимостей
sudo yum install -y yum-utils

# Добавление репозитория Docker
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo

# Установка Docker
sudo yum install -y docker-ce docker-ce-cli containerd.io

# Запуск Docker
sudo systemctl start docker
sudo systemctl enable docker

# Добавление пользователя в группу docker
sudo usermod -aG docker $USER
```

#### macOS:
```bash
# Установка через Homebrew
brew install --cask docker

# Или скачать с официального сайта
# https://www.docker.com/products/docker-desktop
```

#### Windows:
1. Скачайте Docker Desktop с официального сайта
2. Установите и запустите Docker Desktop
3. Включите WSL2 в настройках

### 2. Установка Docker Compose

#### Linux:
```bash
# Установка Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Проверка установки
docker-compose --version
```

#### macOS/Windows:
Docker Compose включен в Docker Desktop.

### 3. Проверка установки

```bash
# Проверка Docker
docker --version
docker run hello-world

# Проверка Docker Compose
docker-compose --version
```

## 🚀 Установка AI-НК

### 1. Подготовка рабочей директории

```bash
# Создание директории для проекта
mkdir ai-nk
cd ai-nk

# Клонирование репозитория (если используется Git)
# git clone <repository-url> .

# Или распаковка архива
# tar -xzf ai-nk-deployment-package.tar.gz
```

### 2. Запуск автоматической установки

```bash
# Сделать скрипт исполняемым
chmod +x install.sh

# Запуск установки
./install.sh
```

### 3. Что делает скрипт установки

1. **Проверка требований**: Проверяет наличие Docker, Docker Compose и системных ресурсов
2. **Создание конфигурации**: Генерирует файлы `.env` и конфигурации
3. **Генерация SSL**: Создает самоподписанные SSL сертификаты
4. **Настройка Keycloak**: Создает realm и пользователей
5. **Сборка образов**: Собирает все Docker образы
6. **Запуск системы**: Запускает все сервисы
7. **Загрузка модели**: Загружает LLM модель в Ollama
8. **Проверка работоспособности**: Проверяет доступность всех сервисов

## ⚙️ Конфигурация

### Переменные окружения (.env)

Основные настройки находятся в файле `.env`:

```bash
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
```

### Изменение портов

Если порты заняты, измените их в файле `.env`:

```bash
# Изменение портов
FRONTEND_PORT=8443
GATEWAY_PORT=9443
KEYCLOAK_PORT=9081
```

### SSL сертификаты

Для продакшена замените самоподписанные сертификаты:

```bash
# Замена сертификатов
cp your-certificate.crt ssl/frontend.crt
cp your-private-key.key ssl/frontend.key
cp your-certificate.crt ssl/gateway.crt
cp your-private-key.key ssl/gateway.key
```

## 🌐 Доступ к системе

После успешной установки система будет доступна по следующим адресам:

### Основные сервисы:
- **Frontend**: https://localhost
- **Keycloak**: https://localhost:8081
- **Grafana**: http://localhost:3000

### API сервисы:
- **Gateway**: https://localhost:8443
- **Document Parser**: http://localhost:8001
- **Rule Engine**: http://localhost:8002
- **RAG Service**: http://localhost:8003

### Базы данных:
- **PostgreSQL**: localhost:5432
- **Qdrant**: http://localhost:6333
- **Redis**: localhost:6379

### Мониторинг:
- **Prometheus**: http://localhost:9090
- **Ollama**: http://localhost:11434

## 👤 Тестовые пользователи

Система создается с предустановленными пользователями:

### Администратор:
- **Логин**: admin
- **Пароль**: admin
- **Роль**: Администратор системы

### Пользователь:
- **Логин**: user
- **Пароль**: password123
- **Роль**: Обычный пользователь

## 🛠 Управление системой

### Скрипты управления

Система включает набор скриптов для управления:

```bash
# Запуск системы
./start.sh

# Остановка системы
./stop.sh

# Перезапуск системы
./restart.sh

# Просмотр логов
./logs.sh [сервис]

# Резервное копирование
./backup.sh

# Восстановление
./restore.sh <путь_к_резервной_копии>
```

### Ручное управление

```bash
# Запуск всех сервисов
docker-compose up -d

# Остановка всех сервисов
docker-compose down

# Просмотр статуса
docker-compose ps

# Просмотр логов
docker-compose logs -f [сервис]

# Пересборка образов
docker-compose build --no-cache
```

## 📊 Мониторинг

### Grafana

1. Откройте http://localhost:3000
2. Логин: admin
3. Пароль: admin
4. Дашборд "AI-НК - Система мониторинга" будет доступен автоматически

### Prometheus

1. Откройте http://localhost:9090
2. Перейдите в раздел "Targets" для проверки состояния сервисов
3. Используйте PromQL для создания запросов

### Проверка здоровья сервисов

```bash
# Проверка frontend
curl -k https://localhost/health

# Проверка gateway
curl -k https://localhost:8443/healthz

# Проверка document-parser
curl http://localhost:8001/health

# Проверка ollama
curl http://localhost:11434/api/tags
```

## 🔧 Устранение неполадок

### Общие проблемы

#### 1. Порт занят
```bash
# Проверка занятых портов
sudo netstat -tulpn | grep :443

# Изменение порта в .env
FRONTEND_PORT=8443
```

#### 2. Недостаточно памяти
```bash
# Проверка использования памяти
docker stats

# Увеличение swap (Linux)
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

#### 3. Проблемы с SSL
```bash
# Пересоздание сертификатов
rm -rf ssl/*
./install.sh
```

#### 4. Проблемы с базой данных
```bash
# Сброс базы данных
docker-compose down
docker volume rm ai-nk_norms_db_data
docker-compose up -d
```

### Логи сервисов

```bash
# Просмотр всех логов
./logs.sh

# Логи конкретного сервиса
./logs.sh frontend
./logs.sh gateway
./logs.sh document-parser
./logs.sh ollama
```

### Перезапуск сервиса

```bash
# Перезапуск конкретного сервиса
docker-compose restart [сервис]

# Примеры:
docker-compose restart frontend
docker-compose restart gateway
docker-compose restart ollama
```

## 🔒 Безопасность

### Рекомендации для продакшена

1. **Измените пароли по умолчанию**:
   ```bash
   # В файле .env
   POSTGRES_PASSWORD=your_secure_password
   REDIS_PASSWORD=your_secure_password
   KEYCLOAK_ADMIN_PASSWORD=your_secure_password
   ```

2. **Используйте реальные SSL сертификаты**:
   ```bash
   # Замените самоподписанные сертификаты
   cp your-domain.crt ssl/frontend.crt
   cp your-domain.key ssl/frontend.key
   ```

3. **Настройте файрвол**:
   ```bash
   # Ограничьте доступ к портам
   sudo ufw allow 443/tcp
   sudo ufw allow 80/tcp
   sudo ufw enable
   ```

4. **Регулярные обновления**:
   ```bash
   # Обновление системы
   ./stop.sh
   git pull
   docker-compose build --no-cache
   ./start.sh
   ```

## 📈 Масштабирование

### Горизонтальное масштабирование

```bash
# Масштабирование сервисов
docker-compose up -d --scale document-parser=3
docker-compose up -d --scale rule-engine=2
```

### Оптимизация производительности

1. **Увеличение ресурсов**:
   ```yaml
   # В docker-compose.yaml
   deploy:
     resources:
       limits:
         memory: 4G
         cpus: '2.0'
   ```

2. **Кэширование**:
   - Redis уже настроен для кэширования
   - Настройте CDN для статических файлов

3. **База данных**:
   - Настройте read replicas
   - Оптимизируйте индексы

## 📞 Поддержка

### Полезные команды

```bash
# Проверка состояния системы
docker-compose ps

# Просмотр ресурсов
docker stats

# Очистка неиспользуемых ресурсов
docker system prune -a

# Проверка сетевых соединений
docker network ls
docker network inspect ai-nk-network
```

### Логи и диагностика

```bash
# Экспорт логов
docker-compose logs > system_logs.txt

# Проверка конфигурации
docker-compose config

# Проверка образов
docker images | grep ai-nk
```

### Обновление системы

```bash
# Остановка системы
./stop.sh

# Обновление кода
git pull

# Пересборка и запуск
docker-compose build --no-cache
./start.sh
```

## 📝 Заключение

Система AI-НК успешно установлена и готова к использованию. Основные функции:

- ✅ AI-чат с загрузкой файлов
- ✅ Обработка документов (PDF, Word, Excel)
- ✅ Нормоконтроль документов
- ✅ Безопасная аутентификация
- ✅ Мониторинг и аналитика

Для начала работы откройте https://localhost и войдите с тестовыми учетными данными.

При возникновении проблем обратитесь к разделу "Устранение неполадок" или к документации проекта.
