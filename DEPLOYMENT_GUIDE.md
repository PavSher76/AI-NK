# 🚀 Руководство по развертыванию AI-NK

## Обзор

AI-NK - это система нормоконтроля с использованием искусственного интеллекта, упакованная в Docker контейнеры для простого развертывания на любом хосте.

## 📋 Требования

### Системные требования
- **ОС**: Linux, macOS, Windows (с WSL2)
- **RAM**: Минимум 8GB, рекомендуется 16GB+
- **CPU**: Минимум 4 ядра, рекомендуется 8+ ядер
- **Диск**: Минимум 50GB свободного места
- **Docker**: версия 20.10+
- **Docker Compose**: версия 2.0+

### Проверка требований
```bash
# Проверка версии Docker
docker --version

# Проверка версии Docker Compose
docker-compose --version

# Проверка доступной памяти
free -h

# Проверка доступного места на диске
df -h
```

## 🛠️ Быстрый старт

### 1. Клонирование репозитория
```bash
git clone <repository-url>
cd AI-NK
```

### 2. Настройка прав доступа
```bash
chmod +x build-and-deploy.sh
chmod +x scripts/start.sh
chmod +x scripts/init.sh
```

### 3. Полное развертывание
```bash
./build-and-deploy.sh deploy
```

Эта команда выполнит:
- ✅ Проверку зависимостей
- ✅ Создание конфигурационных файлов
- ✅ Сборку Docker образа
- ✅ Запуск всех сервисов
- ✅ Проверку состояния системы

## 🔧 Управление системой

### Основные команды
```bash
# Полное развертывание
./build-and-deploy.sh deploy

# Только сборка образа
./build-and-deploy.sh build

# Только запуск системы
./build-and-deploy.sh start

# Остановка системы
./build-and-deploy.sh stop

# Перезапуск системы
./build-and-deploy.sh restart

# Просмотр статуса
./build-and-deploy.sh status

# Просмотр логов
./build-and-deploy.sh logs

# Очистка системы
./build-and-deploy.sh cleanup
```

### Ручное управление через Docker Compose
```bash
# Запуск системы
docker-compose -f docker-compose.production.yml up -d

# Остановка системы
docker-compose -f docker-compose.production.yml down

# Просмотр логов
docker-compose -f docker-compose.production.yml logs -f

# Перезапуск конкретного сервиса
docker-compose -f docker-compose.production.yml restart ai-nk
```

## 🌐 Доступ к системе

После успешного развертывания система будет доступна по следующим адресам:

### Основные интерфейсы
- **Веб-интерфейс**: http://localhost
- **HTTPS**: https://localhost
- **API Gateway**: https://localhost:8443

### Микросервисы
- **Document Parser**: http://localhost:8001
- **Rule Engine**: http://localhost:8002
- **RAG Service**: http://localhost:8003
- **Calculation Service**: http://localhost:8004
- **VLLM Service**: http://localhost:8005
- **Outgoing Control**: http://localhost:8006
- **Spellchecker**: http://localhost:8007

### База данных и кэш
- **PostgreSQL**: localhost:5432
- **Qdrant**: http://localhost:6333
- **Redis**: localhost:6379

### Мониторинг (опционально)
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000
- **Keycloak**: http://localhost:8081

## ⚙️ Конфигурация

### Файл .env
Основные настройки системы находятся в файле `.env`:

```bash
# База данных
POSTGRES_HOST=norms-db
POSTGRES_PORT=5432
POSTGRES_DB=norms_db
POSTGRES_USER=norms_user
POSTGRES_PASSWORD=norms_password

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=redispass

# Qdrant
QDRANT_HOST=qdrant
QDRANT_PORT=6333

# Безопасность
JWT_SECRET_KEY=your-secret-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Лимиты файлов
MAX_FILE_SIZE=104857600
MAX_CHECKABLE_DOCUMENT_SIZE=104857600
MAX_NORMATIVE_DOCUMENT_SIZE=209715200

# Таймауты
LLM_REQUEST_TIMEOUT=120
PAGE_PROCESSING_TIMEOUT=300

# Логирование
LOG_LEVEL=INFO
TZ=Europe/Moscow
```

### Настройка SSL сертификатов
Для работы HTTPS поместите сертификаты в папку `ssl/`:
- `ssl/frontend.crt` - SSL сертификат
- `ssl/frontend.key` - приватный ключ

## 📊 Мониторинг и логи

### Просмотр логов
```bash
# Все сервисы
docker-compose -f docker-compose.production.yml logs -f

# Конкретный сервис
docker-compose -f docker-compose.production.yml logs -f ai-nk

# Последние 100 строк
docker-compose -f docker-compose.production.yml logs --tail=100 ai-nk
```

### Мониторинг ресурсов
```bash
# Использование ресурсов контейнерами
docker stats

# Информация о контейнерах
docker-compose -f docker-compose.production.yml ps

# Использование диска
docker system df
```

### Health checks
```bash
# Проверка состояния системы
curl http://localhost/health

# Проверка API Gateway
curl https://localhost:8443/health

# Проверка конкретного сервиса
curl http://localhost:8001/health
```

## 🔧 Устранение неполадок

### Частые проблемы

#### 1. Порт уже используется
```bash
# Проверка занятых портов
netstat -tulpn | grep :80
netstat -tulpn | grep :443

# Остановка конфликтующих сервисов
sudo systemctl stop nginx
sudo systemctl stop apache2
```

#### 2. Недостаточно памяти
```bash
# Проверка использования памяти
free -h
docker stats

# Очистка неиспользуемых ресурсов
docker system prune -a
```

#### 3. Проблемы с базой данных
```bash
# Проверка логов PostgreSQL
docker-compose -f docker-compose.production.yml logs norms-db

# Перезапуск базы данных
docker-compose -f docker-compose.production.yml restart norms-db
```

#### 4. Проблемы с правами доступа
```bash
# Исправление прав доступа
sudo chown -R 1000:1000 ./uploads ./logs ./data
chmod -R 755 ./uploads ./logs ./data
```

### Восстановление системы
```bash
# Полная очистка и пересборка
./build-and-deploy.sh cleanup
./build-and-deploy.sh deploy
```

## 📈 Масштабирование

### Горизонтальное масштабирование
```yaml
# В docker-compose.production.yml
services:
  ai-nk:
    deploy:
      replicas: 3
```

### Настройка ресурсов
```yaml
# Ограничение ресурсов
services:
  ai-nk:
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2.0'
        reservations:
          memory: 2G
          cpus: '1.0'
```

## 🔒 Безопасность

### Рекомендации по безопасности
1. **Измените пароли по умолчанию** в файле `.env`
2. **Используйте SSL сертификаты** для HTTPS
3. **Ограничьте доступ к портам** базы данных и Redis
4. **Регулярно обновляйте** Docker образы
5. **Мониторьте логи** на предмет подозрительной активности

### Настройка файрвола
```bash
# UFW (Ubuntu)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw deny 5432/tcp  # Закрыть доступ к PostgreSQL
sudo ufw deny 6379/tcp  # Закрыть доступ к Redis
```

## 📝 Обновление системы

### Обновление до новой версии
```bash
# Остановка системы
./build-and-deploy.sh stop

# Обновление кода
git pull origin main

# Пересборка и запуск
./build-and-deploy.sh deploy
```

### Резервное копирование
```bash
# Создание бэкапа данных
docker-compose -f docker-compose.production.yml exec norms-db pg_dump -U norms_user norms_db > backup.sql

# Восстановление из бэкапа
docker-compose -f docker-compose.production.yml exec -T norms-db psql -U norms_user norms_db < backup.sql
```

## 🆘 Поддержка

### Получение помощи
1. Проверьте логи: `./build-and-deploy.sh logs`
2. Проверьте статус: `./build-and-deploy.sh status`
3. Обратитесь к документации проекта
4. Создайте issue в репозитории

### Полезные команды для диагностики
```bash
# Информация о системе
docker version
docker-compose version
uname -a
free -h
df -h

# Состояние контейнеров
docker ps -a
docker-compose -f docker-compose.production.yml ps

# Использование ресурсов
docker stats --no-stream
```

---

**Примечание**: Данное руководство предназначено для развертывания AI-NK системы в production среде. Для разработки используйте соответствующие конфигурации из папки `docker-compose.*.yaml`.
