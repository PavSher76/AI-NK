# 🚀 AI-NK с Llama3.1:70b для MacBook Pro

Это руководство поможет вам настроить и запустить проект AI-NK с мощной моделью **Llama3.1:70b** на MacBook Pro.

## ⚠️ Важные требования

### Минимальные требования для 70b модели:
- **RAM:** 32GB (обязательно!)
- **CPU:** 10+ ядер (M2 Pro/Max или Intel i7/i9)
- **Диск:** 100GB свободного места (SSD)
- **macOS:** 13.0+
- **Интернет:** Стабильное соединение для загрузки модели (~40GB)

### Рекомендуемые требования:
- **RAM:** 64GB+ для оптимальной производительности
- **CPU:** M2 Max/M3 Max или Intel i9
- **Диск:** 200GB+ свободного места
- **Архитектура:** Apple Silicon (ARM64) для лучшей производительности

## 🚀 Быстрый старт

### Шаг 1: Проверка системы

```bash
# Проверка памяти
sysctl -n hw.memsize | awk '{print $0/1024/1024/1024 "GB"}'

# Проверка архитектуры
uname -m

# Проверка свободного места
df -h .
```

### Шаг 2: Запуск системы с 70b

```bash
# Полная установка и запуск с 70b моделью
./setup_macbook_70b.sh
```

**Внимание:** Загрузка модели займет 30-60 минут в зависимости от скорости интернета!

## 📊 Сравнение моделей

| Модель | Размер | RAM | Время ответа | Качество |
|--------|--------|-----|--------------|----------|
| llama3.1:8b | ~4.7GB | 16GB | 1-3 сек | Хорошее |
| llama3.1:70b | ~40GB | 32GB+ | 5-15 сек | Отличное |

## ⚙️ Оптимизация для 70b

### Настройки памяти
```bash
# Для 32GB RAM
OLLAMA_MEMORY_LIMIT=24G
OLLAMA_MEMORY_RESERVATION=20G

# Для 64GB+ RAM
OLLAMA_MEMORY_LIMIT=32G
OLLAMA_MEMORY_RESERVATION=28G
```

### Настройки производительности
```bash
# Оптимальные настройки для 70b
OLLAMA_GPU_LAYERS=40
OLLAMA_CPU_THREADS=12
OLLAMA_BATCH_SIZE=1024
OLLAMA_CONTEXT_SIZE=8192
```

## 🔧 Управление 70b системой

### Основные команды

```bash
# Запуск системы с 70b
./setup_macbook_70b.sh

# Остановка сервисов
./setup_macbook_70b.sh stop

# Перезапуск
./setup_macbook_70b.sh restart

# Просмотр логов
./setup_macbook_70b.sh logs

# Проверка статуса
./setup_macbook_70b.sh status

# Тест производительности
./setup_macbook_70b.sh test
```

### Docker Compose команды для 70b

```bash
# Запуск с 70b конфигурацией
docker-compose -f docker-compose.macbook.70b.yaml up -d

# Остановка
docker-compose -f docker-compose.macbook.70b.yaml down

# Просмотр логов
docker-compose -f docker-compose.macbook.70b.yaml logs -f ollama

# Пересборка образов
docker-compose -f docker-compose.macbook.70b.yaml build --no-cache
```

## 🌐 Доступ к сервисам

После успешного запуска:

| Сервис | URL | Логин/Пароль |
|--------|-----|--------------|
| **Frontend** | https://localhost | - |
| **Keycloak** | https://localhost:8081 | admin/admin |
| **Grafana** | http://localhost:3000 | admin/admin |
| **Ollama** | http://localhost:11434 | - |

## 📈 Мониторинг производительности

### Проверка использования ресурсов

```bash
# Мониторинг Docker контейнеров
docker stats

# Логи Ollama с 70b моделью
docker-compose -f docker-compose.macbook.70b.yaml logs -f ollama

# Проверка модели
curl http://localhost:11434/api/tags
```

### Ожидаемые показатели

| Конфигурация | Время ответа | Токенов/сек | Использование памяти |
|--------------|--------------|-------------|---------------------|
| M2 Pro (32GB) | 5-10 сек | 8-15 | 24-28GB |
| M2 Max (64GB) | 3-7 сек | 12-20 | 28-32GB |
| M3 Max (128GB) | 2-5 сек | 15-25 | 32-40GB |

## 🛠️ Устранение неполадок

### Проблемы с памятью

```bash
# Уменьшите лимиты памяти
# Отредактируйте env.macbook.70b:
OLLAMA_MEMORY_LIMIT=20G
OLLAMA_MEMORY_RESERVATION=16G
```

### Медленная загрузка модели

```bash
# Проверьте интернет соединение
# Модель 70b весит ~40GB
# Используйте стабильное соединение

# Проверка прогресса загрузки
curl http://localhost:11434/api/tags
```

### Проблемы с производительностью

```bash
# Оптимизация для вашей системы
./optimize_performance.sh

# Увеличьте GPU слои (если достаточно памяти)
OLLAMA_GPU_LAYERS=45

# Уменьшите размер батча (если проблемы с памятью)
OLLAMA_BATCH_SIZE=512
```

### Ошибки запуска

```bash
# Полная очистка и перезапуск
./setup_macbook_70b.sh clean
./setup_macbook_70b.sh

# Проверка логов
./setup_macbook_70b.sh logs
```

## 🔄 Переключение между моделями

### С 8b на 70b

```bash
# Остановите текущую систему
./setup_macbook.sh stop

# Запустите с 70b
./setup_macbook_70b.sh
```

### С 70b на 8b

```bash
# Остановите 70b систему
./setup_macbook_70b.sh stop

# Запустите с 8b
./setup_macbook.sh
```

## 📊 Сравнение конфигураций

### Файлы конфигурации

| Модель | Env файл | Docker Compose | Скрипт |
|--------|----------|----------------|--------|
| 8b | `env.macbook` | `docker-compose.macbook.yaml` | `setup_macbook.sh` |
| 70b | `env.macbook.70b` | `docker-compose.macbook.70b.yaml` | `setup_macbook_70b.sh` |

### Настройки ресурсов

| Сервис | 8b модель | 70b модель |
|--------|-----------|------------|
| Ollama | 12GB/8GB | 24GB/20GB |
| vLLM | 2GB/1GB | 4GB/2GB |
| Gateway | 1GB/512MB | 1GB/512MB |
| PostgreSQL | 2GB/1GB | 2GB/1GB |

## 🎯 Рекомендации по использованию

### Для разработки и тестирования
- Используйте **llama3.1:8b** - быстрее, меньше ресурсов
- Подходит для быстрого прототипирования

### Для продакшена и серьезных задач
- Используйте **llama3.1:70b** - лучшее качество ответов
- Требует больше ресурсов, но дает превосходные результаты

### Оптимизация для вашей системы

```bash
# Автоматическая оптимизация
./optimize_performance.sh

# Ручная настройка для 70b
# Отредактируйте env.macbook.70b под вашу систему
```

## 🔍 Диагностика

### Проверка модели

```bash
# Информация о модели
curl http://localhost:8000/model-info

# Тест генерации
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.1:70b",
    "prompt": "Hello, how are you?",
    "stream": false,
    "options": {
      "num_predict": 50,
      "temperature": 0.7
    }
  }'
```

### Мониторинг через Grafana

1. Откройте http://localhost:3000
2. Логин: admin/admin
3. Дашборд "AI-NK Dashboard" покажет метрики всех сервисов
4. Особое внимание уделите метрикам Ollama и использованию памяти

## 🆘 Поддержка

Если у вас возникли проблемы:

1. **Проверьте требования:** Убедитесь, что у вас достаточно RAM (32GB+)
2. **Проверьте логи:** `./setup_macbook_70b.sh logs`
3. **Проверьте статус:** `./setup_macbook_70b.sh status`
4. **Запустите тест:** `./setup_macbook_70b.sh test`
5. **Очистите и перезапустите:** `./setup_macbook_70b.sh clean && ./setup_macbook_70b.sh`

## 📝 Примечания

- **Время загрузки:** Модель 70b загружается 30-60 минут
- **Память:** Система может быть медленной при недостатке RAM
- **Температура:** MacBook может нагреваться при работе с 70b
- **Батарея:** При работе от батареи производительность может снижаться

---

**Готово!** Ваш AI-NK настроен для работы с мощной моделью Llama3.1:70b! 🎉

> 💡 **Совет:** Для лучшей производительности используйте MacBook подключенным к сети и с хорошим охлаждением.
