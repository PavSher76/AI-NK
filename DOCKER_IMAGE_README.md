# 🐳 AI-NK Docker Image

## 📥 Загрузка готового образа

### Скачать образ

```bash
# Скачать готовый образ AI-NK v1.0.0
wget https://github.com/PavSher76/AI-NK/releases/download/v1.0.0/ai-nk-v1.0.0.tar.gz

# Или использовать curl
curl -L -o ai-nk-v1.0.0.tar.gz https://github.com/PavSher76/AI-NK/releases/download/v1.0.0/ai-nk-v1.0.0.tar.gz
```

### Загрузить образ в Docker

```bash
# Загрузить образ в локальный Docker
docker load < ai-nk-v1.0.0.tar.gz

# Проверить, что образ загружен
docker images | grep ai-nk
```

### Запустить систему

```bash
# Запустить AI-NK систему
docker run -d \
  --name ai-nk \
  -p 80:80 \
  -p 8001:8001 \
  -p 8002:8002 \
  -p 8003:8003 \
  -p 8004:8004 \
  -v ai-nk-data:/app/data \
  -v ai-nk-logs:/app/logs \
  -v ai-nk-uploads:/app/uploads \
  ai-nk:latest

# Открыть в браузере
open http://localhost
```

## 🔧 Сборка образа из исходного кода

### Требования
- Docker 20.10+
- 4GB RAM (минимум)
- 10GB свободного места

### Сборка

```bash
# Клонировать репозиторий
git clone https://github.com/PavSher76/AI-NK.git
cd AI-NK

# Собрать образ
chmod +x build-image.sh
./build-image.sh --build

# Сохранить образ в файл
./build-image.sh --save ai-nk-custom.tar.gz
```

## 📊 Информация об образе

| Параметр | Значение |
|----------|----------|
| **Размер образа** | ~464MB |
| **Версия** | 1.0.0 |
| **Основа** | Python 3.11-slim |
| **Frontend** | React (собранный) |
| **Сервисы** | Все компоненты AI-NK |

## 🌐 Доступные сервисы

| Сервис | URL | Описание |
|--------|-----|----------|
| **Frontend** | http://localhost | Веб-интерфейс |
| **API Gateway** | http://localhost/api | API системы |
| **Document Parser** | http://localhost:8001 | Парсинг документов |
| **RAG Service** | http://localhost:8002 | Векторный поиск |
| **Rule Engine** | http://localhost:8003 | Проверка норм |

## 🛠️ Управление контейнером

```bash
# Проверка статуса
docker ps | grep ai-nk

# Просмотр логов
docker logs ai-nk

# Остановка
docker stop ai-nk

# Перезапуск
docker restart ai-nk

# Удаление
docker rm -f ai-nk
```

## 📁 Данные

Образ использует следующие тома:
- `ai-nk-data` - База данных PostgreSQL
- `ai-nk-logs` - Логи системы
- `ai-nk-uploads` - Загруженные документы

## 🔧 Конфигурация

### Переменные окружения

```bash
docker run -d \
  --name ai-nk \
  -e MAX_NORMATIVE_DOCUMENT_SIZE=104857600 \
  -e MAX_CHECKABLE_DOCUMENT_SIZE=104857600 \
  -e POSTGRES_PASSWORD=your_password \
  -p 80:80 \
  ai-nk:latest
```

### Изменение портов

```bash
docker run -d \
  --name ai-nk \
  -p 8080:80 \
  -p 8081:8001 \
  -p 8082:8002 \
  -p 8083:8003 \
  -p 8084:8004 \
  ai-nk:latest
```

## 🚨 Устранение неполадок

### Проблемы с портами
```bash
# Проверка занятых портов
lsof -i :80
lsof -i :8001

# Изменение портов
docker run -p 8080:80 ... ai-nk:latest
```

### Проблемы с памятью
```bash
# Ограничение памяти
docker run --memory=4g --memory-swap=6g ... ai-nk:latest
```

### Сброс данных
```bash
# Удаление томов
docker volume rm ai-nk-data ai-nk-logs ai-nk-uploads

# Пересоздание контейнера
docker rm -f ai-nk
docker run -d ... ai-nk:latest
```

## 📞 Поддержка

### Полезные команды

```bash
# Полная диагностика
docker exec ai-nk curl -f http://localhost/health

# Просмотр логов приложения
docker exec ai-nk tail -f /app/logs/*.log

# Подключение к контейнеру
docker exec -it ai-nk bash

# Статистика контейнера
docker stats ai-nk
```

### Создание бэкапа

```bash
# Бэкап базы данных
docker exec ai-nk pg_dump -h localhost -U norms_user norms_db > backup.sql

# Бэкап загруженных файлов
docker cp ai-nk:/app/uploads ./backup-uploads
```

## 📄 Лицензирование

**AI-NK System** является коммерческим продуктом и требует приобретения лицензии для использования.

Для получения лицензии обращайтесь:
- **Email:** [contact@ai-nk.com](mailto:contact@ai-nk.com)
- **Веб-сайт:** [www.ai-nk.com](https://www.ai-nk.com)

---

**© 2024 AI-NK System. Все права защищены.**
