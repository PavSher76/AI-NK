# AI-NK для MacBook Pro с Llama3

Это руководство поможет вам настроить и запустить проект AI-NK на MacBook Pro с оптимизацией для работы с моделью Llama3.

## 🚀 Быстрый старт

### Предварительные требования

1. **macOS** (рекомендуется macOS 13+)
2. **Docker Desktop для Mac** (версия 4.0+)
3. **Минимум 16GB RAM** (рекомендуется 32GB для лучшей производительности)
4. **Apple Silicon (M1/M2/M3)** или **Intel Mac**

### Установка

1. **Клонируйте репозиторий:**
   ```bash
   git clone <repository-url>
   cd AI-NK
   ```

2. **Запустите автоматическую настройку:**
   ```bash
   ./setup_macbook.sh
   ```

Скрипт автоматически:
- Проверит вашу систему
- Создаст необходимые директории
- Настроит SSL сертификаты
- Соберет и запустит все сервисы
- Установит модель Llama3
- Проверит доступность всех сервисов

## 📋 Системные требования

### Минимальные требования
- **RAM:** 16GB
- **CPU:** 8 ядер
- **Диск:** 50GB свободного места
- **macOS:** 12.0+

### Рекомендуемые требования
- **RAM:** 32GB
- **CPU:** 10+ ядер (M2 Pro/Max или Intel i7/i9)
- **Диск:** 100GB свободного места (SSD)
- **macOS:** 13.0+

## ⚙️ Оптимизация для MacBook Pro

### Настройки памяти
Проект оптимизирован для эффективного использования памяти MacBook Pro:

| Сервис | Лимит памяти | Резервирование |
|--------|-------------|----------------|
| Ollama (Llama3) | 12GB | 8GB |
| PostgreSQL | 2GB | 1GB |
| Qdrant | 2GB | 1GB |
| Document Parser | 2GB | 1GB |
| Rule Engine | 2GB | 1GB |
| API Gateway | 1GB | 512MB |
| RAG Service | 1GB | 512MB |

### Настройки для Apple Silicon
- Автоматическое определение архитектуры (ARM64/AMD64)
- Оптимизированные Docker образы
- Использование Metal Performance Shaders (MPS) для GPU ускорения

### Настройки для Llama3
- **Модель:** llama3.1:8b (оптимальный баланс производительности/качества)
- **GPU слои:** 35 (максимальное использование GPU)
- **CPU потоки:** 8 (оптимизировано для многоядерных процессоров)
- **Размер батча:** 512 (улучшенная производительность)

## 🔧 Управление сервисами

### Основные команды

```bash
# Запуск всех сервисов
./setup_macbook.sh

# Остановка сервисов
./setup_macbook.sh stop

# Перезапуск сервисов
./setup_macbook.sh restart

# Просмотр логов
./setup_macbook.sh logs

# Проверка статуса
./setup_macbook.sh status

# Полная очистка
./setup_macbook.sh clean
```

### Docker Compose команды

```bash
# Запуск с оптимизированной конфигурацией
docker-compose -f docker-compose.macbook.yaml up -d

# Остановка
docker-compose -f docker-compose.macbook.yaml down

# Просмотр логов
docker-compose -f docker-compose.macbook.yaml logs -f

# Пересборка образов
docker-compose -f docker-compose.macbook.yaml build --no-cache
```

## 🌐 Доступ к сервисам

После успешного запуска вы получите доступ к следующим сервисам:

| Сервис | URL | Логин/Пароль |
|--------|-----|--------------|
| **Frontend** | https://localhost | - |
| **Keycloak** | https://localhost:8081 | admin/admin |
| **Grafana** | http://localhost:3000 | admin/admin |
| **Prometheus** | http://localhost:9090 | - |
| **Ollama** | http://localhost:11434 | - |
| **API Gateway** | https://localhost:8443 | - |

## 🔍 Мониторинг и диагностика

### Проверка производительности

1. **Мониторинг через Grafana:**
   - Откройте http://localhost:3000
   - Логин: admin/admin
   - Дашборд "AI-NK Dashboard" покажет метрики всех сервисов

2. **Проверка использования ресурсов:**
   ```bash
   # Использование CPU и памяти
   docker stats
   
   # Логи Ollama
   docker-compose -f docker-compose.macbook.yaml logs ollama
   
   # Логи API Gateway
   docker-compose -f docker-compose.macbook.yaml logs gateway
   ```

### Оптимизация производительности

1. **Увеличение памяти для Ollama:**
   Отредактируйте `env.macbook`:
   ```bash
   OLLAMA_MEMORY_LIMIT=16G
   OLLAMA_MEMORY_RESERVATION=12G
   ```

2. **Настройка количества GPU слоев:**
   ```bash
   OLLAMA_GPU_LAYERS=40  # Больше GPU слоев = быстрее, но больше памяти
   ```

3. **Оптимизация размера батча:**
   ```bash
   OLLAMA_BATCH_SIZE=1024  # Больше батч = быстрее, но больше памяти
   ```

## 🛠️ Устранение неполадок

### Частые проблемы

1. **Недостаточно памяти:**
   ```bash
   # Уменьшите лимиты памяти в env.macbook
   OLLAMA_MEMORY_LIMIT=8G
   OLLAMA_MEMORY_RESERVATION=6G
   ```

2. **Медленная загрузка модели:**
   ```bash
   # Проверьте интернет соединение
   # Модель llama3.1:8b весит ~4.7GB
   ```

3. **Проблемы с SSL сертификатами:**
   ```bash
   # Пересоздайте сертификаты
   rm -rf ssl/*
   ./setup_macbook.sh
   ```

4. **Конфликты портов:**
   ```bash
   # Измените порты в env.macbook
   GATEWAY_PORT=8444
   FRONTEND_PORT=444
   ```

### Логи и диагностика

```bash
# Просмотр всех логов
docker-compose -f docker-compose.macbook.yaml logs

# Логи конкретного сервиса
docker-compose -f docker-compose.macbook.yaml logs ollama
docker-compose -f docker-compose.macbook.yaml logs gateway

# Проверка статуса контейнеров
docker-compose -f docker-compose.macbook.yaml ps

# Проверка использования ресурсов
docker stats
```

## 🔄 Обновление

### Обновление проекта

```bash
# Остановите сервисы
./setup_macbook.sh stop

# Обновите код
git pull

# Пересоберите и запустите
./setup_macbook.sh
```

### Обновление модели Llama3

```bash
# Удалите старую модель
curl -X DELETE http://localhost:11434/api/delete -d '{"name": "llama3.1:8b"}'

# Установите новую версию
curl -X POST http://localhost:11434/api/pull -d '{"name": "llama3.1:8b"}'
```

## 📊 Производительность

### Ожидаемые показатели на MacBook Pro

| Конфигурация | Время ответа | Токенов/сек | Использование памяти |
|--------------|--------------|-------------|---------------------|
| M1 Pro (16GB) | 2-5 сек | 15-25 | 12-14GB |
| M2 Pro (16GB) | 1-3 сек | 20-30 | 12-14GB |
| M2 Max (32GB) | 1-2 сек | 25-35 | 12-16GB |
| Intel i7 (16GB) | 3-7 сек | 10-20 | 12-14GB |

### Оптимизация для вашей системы

1. **Для систем с 16GB RAM:**
   - Используйте модель llama3.1:8b
   - Установите OLLAMA_GPU_LAYERS=30
   - Ограничьте другие сервисы

2. **Для систем с 32GB+ RAM:**
   - Можете использовать llama3.1:70b
   - Увеличьте OLLAMA_GPU_LAYERS до 40
   - Увеличьте размеры батчей

## 🤝 Поддержка

Если у вас возникли проблемы:

1. Проверьте раздел "Устранение неполадок"
2. Просмотрите логи: `./setup_macbook.sh logs`
3. Проверьте статус сервисов: `./setup_macbook.sh status`
4. Создайте issue в репозитории с подробным описанием проблемы

## 📝 Лицензия

Проект распространяется под лицензией MIT. См. файл [LICENSE](LICENSE) для подробностей.
