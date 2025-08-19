# 🚀 AI-НК - Система нормоконтроля

## 📋 Описание

AI-НК - это интеллектуальная система автоматизированного нормоконтроля документов, использующая искусственный интеллект для проверки соответствия нормативным требованиям.

## ✨ Возможности

- 🤖 **AI-чат с загрузкой файлов** - Обработка документов через чат-интерфейс
- 📄 **Обработка документов** - Поддержка PDF, Word, Excel форматов
- 🔍 **Нормоконтроль документов** - Автоматическая проверка соответствия нормам
- 📊 **Аналитика и отчеты** - Детальная статистика и отчеты
- 🔐 **Безопасная аутентификация** - Keycloak с OIDC
- 📱 **Адаптивный интерфейс** - Современный веб-интерфейс
- 📈 **Мониторинг** - Prometheus + Grafana

## 🏗️ Архитектура

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

## 🚀 Быстрый старт

### Требования
- Docker 20.0+
- Docker Compose 2.0+
- 8GB RAM (рекомендуется 16GB)
- 20GB свободного места

### Установка

1. **Клонирование или распаковка**:
   ```bash
   # Если используете Git
   git clone <repository-url> ai-nk
   cd ai-nk
   
   # Или распаковка архива
   tar -xzf ai-nk-deployment-package.tar.gz
   cd ai-nk
   ```

2. **Запуск установки**:
   ```bash
   chmod +x install.sh
   ./install.sh
   ```

3. **Доступ к системе**:
   - Frontend: https://localhost
   - Keycloak: https://localhost:8081
   - Grafana: http://localhost:3000

### Тестовые пользователи
- **Администратор**: admin/admin
- **Пользователь**: user/password123

## 🛠️ Управление

### Скрипты управления
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
```

## 📊 Мониторинг

### Grafana
- URL: http://localhost:3000
- Логин: admin
- Пароль: admin

### Prometheus
- URL: http://localhost:9090

### Проверка здоровья
```bash
# Frontend
curl -k https://localhost/health

# Gateway
curl -k https://localhost:8443/healthz

# Document Parser
curl http://localhost:8001/health

# Ollama
curl http://localhost:11434/api/tags
```

## ⚙️ Конфигурация

### Переменные окружения
Основные настройки в файле `.env`:
```bash
# Базы данных
POSTGRES_DB=norms_db
POSTGRES_USER=norms_user
POSTGRES_PASSWORD=norms_password

# Redis
REDIS_PASSWORD=redispass

# Keycloak
KEYCLOAK_ADMIN=admin
KEYCLOAK_ADMIN_PASSWORD=admin

# Порты
FRONTEND_PORT=443
GATEWAY_PORT=8443
KEYCLOAK_PORT=8081
```

### SSL сертификаты
Система использует самоподписанные сертификаты для разработки.
Для продакшена замените файлы в директории `ssl/`.

## 🔧 Устранение неполадок

### Общие проблемы

#### Порт занят
```bash
# Проверка занятых портов
sudo netstat -tulpn | grep :443

# Изменение порта в .env
FRONTEND_PORT=8443
```

#### Недостаточно памяти
```bash
# Проверка использования памяти
docker stats

# Увеличение swap (Linux)
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

#### Проблемы с SSL
```bash
# Пересоздание сертификатов
rm -rf ssl/*
./install.sh
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

## 🔒 Безопасность

### Рекомендации для продакшена

1. **Измените пароли по умолчанию** в файле `.env`
2. **Используйте реальные SSL сертификаты**
3. **Настройте файрвол**
4. **Регулярно обновляйте систему**

## 📈 Масштабирование

### Горизонтальное масштабирование
```bash
# Масштабирование сервисов
docker-compose up -d --scale document-parser=3
docker-compose up -d --scale rule-engine=2
```

### Оптимизация производительности
1. Увеличьте ресурсы в `docker-compose.yaml`
2. Настройте кэширование
3. Оптимизируйте базу данных

## 📞 Поддержка

### Полезные команды
```bash
# Проверка состояния системы
docker-compose ps

# Просмотр ресурсов
docker stats

# Очистка неиспользуемых ресурсов
docker system prune -a
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

## 📚 Документация

- [Руководство по установке](INSTALLATION_GUIDE.md)
- [Рекомендации по улучшению](../IMPROVEMENT_RECOMMENDATIONS.md)
- [Технические улучшения](../TECHNICAL_IMPROVEMENTS.md)

## 📄 Лицензия

[Укажите лицензию]

## 👥 Контакты

[Укажите контактную информацию]

---

**AI-НК** - Интеллектуальная система нормоконтроля документов
