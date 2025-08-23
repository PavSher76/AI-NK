# 🚀 Развертывание AI-NK системы

## 📋 Обзор

AI-NK - это система автоматизированной проверки нормативной документации с использованием искусственного интеллекта. Данный документ описывает процесс быстрого развертывания системы на новой машине.

## 🎯 Быстрое развертывание

### Требования

- **Docker** (версия 20.10+)
- **Docker Compose** (версия 2.0+)
- **4GB RAM** (минимум)
- **10GB свободного места** на диске
- **Linux/macOS/Windows** с поддержкой Docker

### Автоматическое развертывание

1. **Клонирование репозитория:**
```bash
git clone <repository-url>
cd AI-NK
```

2. **Запуск развертывания:**
```bash
chmod +x deploy.sh
./deploy.sh --deploy
```

3. **Проверка работы:**
```bash
./deploy.sh --health
```

### Интерактивное меню

Для более детального контроля используйте интерактивное меню:

```bash
./deploy.sh --menu
```

## 🏗️ Архитектура системы

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   API Gateway   │    │  Document       │
│   (React)       │◄──►│   (FastAPI)     │◄──►│  Parser         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   RAG Service   │    │   Rule Engine   │
                       │   (Vector DB)   │    │   (LLM)         │
                       └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   PostgreSQL    │
                       │   (pgvector)    │
                       └─────────────────┘
```

## 🔧 Компоненты системы

### Основные сервисы

| Сервис | Порт | Описание |
|--------|------|----------|
| **Frontend** | 80 | React приложение |
| **API Gateway** | 8004 | Маршрутизация запросов |
| **Document Parser** | 8001 | Парсинг документов |
| **RAG Service** | 8002 | Векторный поиск |
| **Rule Engine** | 8003 | Проверка норм |
| **PostgreSQL** | 5432 | База данных |
| **Redis** | 6379 | Кэширование |
| **Qdrant** | 6333 | Векторная БД |

### Функциональность

- 📄 **Загрузка нормативных документов** (PDF, DOCX, DWG, IFC)
- 🔍 **Автоматическая индексация** с использованием BGE-M3
- 🤖 **ИИ-проверка нормоконтроля** с помощью LLM
- 📊 **Детальная отчетность** в PDF формате
- 🔄 **Асинхронная обработка** больших документов
- 📈 **Мониторинг и логирование**

## 🛠️ Управление системой

### Основные команды

```bash
# Полное развертывание
./deploy.sh --deploy

# Только сборка образа
./deploy.sh --build

# Запуск системы
./deploy.sh --start

# Остановка системы
./deploy.sh --stop

# Обновление системы
./deploy.sh --update

# Проверка здоровья
./deploy.sh --health

# Очистка системы
./deploy.sh --clean

# Интерактивное меню
./deploy.sh --menu
```

### Docker команды

```bash
# Просмотр логов
docker logs ai-nk-system

# Просмотр логов приложения
docker exec ai-nk-system tail -f /app/logs/*.log

# Подключение к контейнеру
docker exec -it ai-nk-system bash

# Перезапуск системы
docker-compose -f docker-compose.prod.yaml restart

# Остановка системы
docker-compose -f docker-compose.prod.yaml down
```

## 📊 Мониторинг

### Проверка состояния

```bash
# Проверка всех сервисов
curl http://localhost/health

# Проверка API Gateway
curl http://localhost:8004/health

# Проверка Document Parser
curl http://localhost:8001/health

# Проверка RAG Service
curl http://localhost:8002/health

# Проверка Rule Engine
curl http://localhost:8003/health
```

### Логи системы

```bash
# Основные логи
docker logs ai-nk-system

# Логи приложения
docker exec ai-nk-system tail -f /app/logs/document-parser.log
docker exec ai-nk-system tail -f /app/logs/rag-service.log
docker exec ai-nk-system tail -f /app/logs/rule-engine.log
docker exec ai-nk-system tail -f /app/logs/gateway.log

# Логи базы данных
docker exec ai-nk-system tail -f /app/logs/postgres.log
```

## 🔧 Конфигурация

### Переменные окружения

Основные настройки можно изменить в `docker-compose.prod.yaml`:

```yaml
environment:
  - MAX_NORMATIVE_DOCUMENT_SIZE=104857600  # 100MB
  - MAX_CHECKABLE_DOCUMENT_SIZE=104857600  # 100MB
  - POSTGRES_PASSWORD=norms_password
```

### Настройка портов

По умолчанию система использует следующие порты:

- **80** - Frontend (HTTP)
- **443** - Frontend (HTTPS)
- **8001** - Document Parser
- **8002** - RAG Service
- **8003** - Rule Engine
- **8004** - API Gateway

Для изменения портов отредактируйте `docker-compose.prod.yaml`.

## 🚨 Устранение неполадок

### Частые проблемы

#### 1. Порт уже занят
```bash
# Проверка занятых портов
lsof -i :80
lsof -i :8001

# Остановка конфликтующих сервисов
sudo systemctl stop nginx  # если использует порт 80
```

#### 2. Недостаточно памяти
```bash
# Проверка доступной памяти
free -h

# Увеличение swap (если необходимо)
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

#### 3. Проблемы с Docker
```bash
# Перезапуск Docker
sudo systemctl restart docker

# Очистка Docker
docker system prune -a
```

#### 4. Проблемы с базой данных
```bash
# Проверка подключения к БД
docker exec ai-nk-system psql -h localhost -U norms_user -d norms_db

# Сброс базы данных
docker exec ai-nk-system rm -f /app/data/.initialized
docker-compose -f docker-compose.prod.yaml down
./deploy.sh --deploy
```

### Логи ошибок

```bash
# Просмотр всех логов
docker logs ai-nk-system --tail 100

# Поиск ошибок
docker logs ai-nk-system 2>&1 | grep -i error

# Проверка статуса контейнера
docker ps -a | grep ai-nk
```

## 📈 Масштабирование

### Горизонтальное масштабирование

Для увеличения производительности можно запустить несколько экземпляров сервисов:

```yaml
# docker-compose.prod.yaml
services:
  document-parser:
    deploy:
      replicas: 3
  rag-service:
    deploy:
      replicas: 2
```

### Вертикальное масштабирование

Увеличение ресурсов для контейнера:

```yaml
# docker-compose.prod.yaml
services:
  ai-nk:
    deploy:
      resources:
        limits:
          memory: 8G
          cpus: '4.0'
        reservations:
          memory: 4G
          cpus: '2.0'
```

## 🔒 Безопасность

### Рекомендации по безопасности

1. **Измените пароли по умолчанию**
2. **Используйте HTTPS в продакшене**
3. **Настройте файрвол**
4. **Регулярно обновляйте систему**
5. **Мониторьте логи на предмет подозрительной активности**

### Настройка HTTPS

```bash
# Генерация SSL сертификата
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /path/to/private.key \
  -out /path/to/certificate.crt

# Настройка Nginx для HTTPS
# Отредактируйте nginx.conf
```

## 📞 Поддержка

### Полезные команды

```bash
# Полная диагностика системы
./deploy.sh --health
docker system df
docker stats

# Экспорт логов
docker logs ai-nk-system > ai-nk-logs.txt

# Создание бэкапа данных
docker exec ai-nk-system pg_dump -h localhost -U norms_user norms_db > backup.sql
```

### Контакты

При возникновении проблем:
1. Проверьте логи системы
2. Убедитесь в соответствии требованиям
3. Попробуйте перезапустить систему
4. Обратитесь к документации

---

**AI-NK System** - Автоматизированная проверка нормативной документации 🤖
