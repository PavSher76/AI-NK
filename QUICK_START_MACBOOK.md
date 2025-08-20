# 🚀 Быстрый старт AI-NK для MacBook Pro

## Шаг 1: Проверка системы

Убедитесь, что у вас установлены:
- ✅ macOS 12.0+
- ✅ Docker Desktop для Mac
- ✅ Минимум 16GB RAM (рекомендуется 32GB)

## Шаг 2: Запуск оптимизации

```bash
# Оптимизация для вашей системы
./optimize_performance.sh
```

Этот скрипт автоматически:
- Проанализирует вашу систему
- Оптимизирует настройки Docker
- Настроит переменные окружения под вашу конфигурацию
- Проведет тест производительности

## Шаг 3: Запуск проекта

```bash
# Полная установка и запуск
./setup_macbook.sh
```

Скрипт автоматически:
- Создаст необходимые директории
- Настроит SSL сертификаты
- Соберет и запустит все сервисы
- Установит модель Llama3
- Проверит доступность всех сервисов

## Шаг 4: Доступ к сервисам

После успешного запуска:

| Сервис | URL | Логин/Пароль |
|--------|-----|--------------|
| **Frontend** | https://localhost | - |
| **Keycloak** | https://localhost:8081 | admin/admin |
| **Grafana** | http://localhost:3000 | admin/admin |

## 🔧 Управление

```bash
# Остановка сервисов
./setup_macbook.sh stop

# Перезапуск
./setup_macbook.sh restart

# Просмотр логов
./setup_macbook.sh logs

# Проверка статуса
./setup_macbook.sh status
```

## 🎯 Оптимизация производительности

```bash
# Дополнительная оптимизация
./optimize_performance.sh

# Только тест производительности
./optimize_performance.sh test

# Рекомендации для вашей системы
./optimize_performance.sh recommendations
```

## 📊 Мониторинг

- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Docker Stats**: `docker stats`

## 🛠️ Устранение проблем

### Недостаточно памяти
```bash
# Уменьшите лимиты в env.macbook
OLLAMA_MEMORY_LIMIT=8G
OLLAMA_MEMORY_RESERVATION=6G
```

### Медленная работа
```bash
# Перезапустите с оптимизацией
./optimize_performance.sh
./setup_macbook.sh restart
```

### Проблемы с SSL
```bash
# Пересоздайте сертификаты
rm -rf ssl/*
./setup_macbook.sh
```

## 📈 Ожидаемая производительность

| Система | Время ответа | Токенов/сек |
|---------|--------------|-------------|
| M1 Pro (16GB) | 2-5 сек | 15-25 |
| M2 Pro (16GB) | 1-3 сек | 20-30 |
| M2 Max (32GB) | 1-2 сек | 25-35 |

## 🆘 Поддержка

Если что-то не работает:

1. Проверьте логи: `./setup_macbook.sh logs`
2. Проверьте статус: `./setup_macbook.sh status`
3. Запустите оптимизацию: `./optimize_performance.sh`
4. Перезапустите: `./setup_macbook.sh restart`

---

**Готово!** Ваш AI-NK оптимизирован для MacBook Pro и готов к работе с Llama3! 🎉
