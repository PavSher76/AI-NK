# Archive Service - Пакетная загрузка технической документации

Сервис для пакетной загрузки и индексации технической документации (ПД, РД, ТЭО) с группировкой по ШИФР проекта.

## Возможности

- **Пакетная загрузка** технической документации
- **Автоматическое извлечение ШИФР проекта** из имен файлов и содержимого
- **Определение типа документа** (ПД, РД, ТЭО, чертежи, спецификации)
- **Разбиение на разделы** с автоматическим извлечением структуры
- **Векторная индексация** для семантического поиска
- **Объединение документов** по общему ШИФР проекта
- **REST API** для интеграции с другими сервисами

## Архитектура

```
archive_service/
├── config.py              # Конфигурация сервиса
├── models.py              # Модели данных
├── database_manager.py    # Менеджер базы данных
├── document_processor.py  # Обработчик документов
├── batch_upload_service.py # Сервис пакетной загрузки
├── vector_indexer.py      # Векторный индексатор
├── document_merger.py     # Объединение документов
├── main.py               # Основное приложение
├── api/
│   └── endpoints.py      # API эндпоинты
├── requirements.txt      # Зависимости
└── Dockerfile           # Docker конфигурация
```

## Типы документов

- **ПД** - Проектная документация
- **РД** - Рабочая документация
- **ТЭО** - Технико-экономическое обоснование
- **DRAWING** - Чертежи
- **SPECIFICATION** - Спецификации
- **CALCULATION** - Расчеты
- **REPORT** - Отчеты
- **OTHER** - Прочее

## API Эндпоинты

### Пакетная загрузка
```http
POST /api/archive/upload/batch
Content-Type: application/json

{
  "project_code": "ПР-2024-001",
  "documents": [
    {
      "file_path": "/path/to/document.pdf",
      "document_type": "PD",
      "document_name": "Проектная документация",
      "author": "Иванов И.И."
    }
  ],
  "auto_extract_sections": true,
  "create_relations": true
}
```

### Загрузка одного документа
```http
POST /api/archive/upload/single
Content-Type: multipart/form-data

file: [файл]
project_code: ПР-2024-001
document_type: PD
document_name: Проектная документация
author: Иванов И.И.
```

### Получение документов проекта
```http
GET /api/archive/projects/{project_code}/documents
```

### Статистика проекта
```http
GET /api/archive/projects/{project_code}/stats
```

### Поиск документов
```http
POST /api/archive/search
Content-Type: application/json

{
  "project_code": "ПР-2024-001",
  "search_query": "требования безопасности",
  "document_type": "PD",
  "limit": 10
}
```

### Поиск похожих разделов
```http
POST /api/archive/search/similar
Content-Type: application/json

{
  "query": "требования к материалам",
  "project_code": "ПР-2024-001",
  "limit": 10,
  "score_threshold": 0.7
}
```

### Объединение документов
```http
POST /api/archive/projects/{project_code}/merge
Content-Type: application/json

{
  "output_format": "pdf",
  "include_sections": true
}
```

## Конфигурация

### Переменные окружения

- `DATABASE_URL` - URL базы данных PostgreSQL
- `QDRANT_URL` - URL векторной базы данных Qdrant
- `ARCHIVE_UPLOAD_DIR` - Директория для загруженных файлов
- `ARCHIVE_MAX_FILE_SIZE` - Максимальный размер файла (по умолчанию 100MB)
- `CHUNK_SIZE` - Размер чанка для обработки текста (по умолчанию 1000)
- `CHUNK_OVERLAP` - Перекрытие чанков (по умолчанию 200)

### Поддерживаемые форматы файлов

- PDF (.pdf)
- DOCX (.docx)
- XLSX (.xlsx)
- DWG (.dwg)
- IFC (.ifc)
- TXT (.txt)

## ШИФР проекта

Сервис автоматически извлекает ШИФР проекта из:
- Имени файла
- Содержимого документа

Поддерживаемые форматы:
- `ПР-2024-001`
- `ПР.2024.001`
- `ПР_2024_001`
- `2024-ПР-001`
- `ПР2024001`

## База данных

### Таблицы

- `archive_documents` - Документы архива
- `archive_document_sections` - Разделы документов
- `archive_document_relations` - Связи между документами
- `archive_projects` - Проекты

### Индексы

- По ШИФР проекта
- По типу документа
- По статусу обработки
- По дате загрузки
- Векторные индексы для поиска

## Развертывание

### Docker

```bash
# Сборка образа
docker build -t archive-service .

# Запуск контейнера
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:pass@localhost:5432/db \
  -e QDRANT_URL=http://localhost:6333 \
  archive-service
```

### Docker Compose

Сервис включен в основной `docker-compose.yaml`:

```yaml
archive-service:
  build: ./archive_service
  ports:
    - "8008:8000"
  environment:
    - DATABASE_URL=postgresql://...
    - QDRANT_URL=http://qdrant:6333
  volumes:
    - archive_uploads:/app/uploads/archive
    - archive_merged:/app/uploads/merged
```

## Мониторинг

### Health Check
```http
GET /api/archive/health
```

### Метрики
```http
GET /api/archive/metrics
```

### Статистика векторной базы
```http
GET /api/archive/vector/stats
```

## Логирование

Сервис использует структурированное логирование с уровнями:
- INFO - Общая информация
- DEBUG - Отладочная информация
- WARNING - Предупреждения
- ERROR - Ошибки

## Обработка ошибок

- Валидация входных данных
- Проверка размера файлов
- Обработка ошибок извлечения текста
- Retry механизмы для внешних сервисов
- Graceful degradation при недоступности сервисов

## Производительность

- Пакетная обработка документов
- Асинхронная загрузка
- Пулы соединений к БД
- Кэширование результатов
- Оптимизированные запросы

## Безопасность

- Валидация типов файлов
- Проверка размера файлов
- Санитизация входных данных
- Изоляция файлов по проектам
- Аутентификация через Gateway

## Примеры использования

### Python клиент

```python
import requests

# Загрузка документа
files = {'file': open('document.pdf', 'rb')}
data = {
    'project_code': 'ПР-2024-001',
    'document_type': 'PD',
    'author': 'Иванов И.И.'
}

response = requests.post(
    'http://localhost:8008/api/archive/upload/single',
    files=files,
    data=data
)

print(response.json())
```

### cURL

```bash
# Получение документов проекта
curl -X GET "http://localhost:8008/api/archive/projects/ПР-2024-001/documents"

# Поиск документов
curl -X POST "http://localhost:8008/api/archive/search" \
  -H "Content-Type: application/json" \
  -d '{
    "project_code": "ПР-2024-001",
    "search_query": "требования безопасности"
  }'
```

## Разработка

### Установка зависимостей

```bash
pip install -r requirements.txt
```

### Запуск в режиме разработки

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Тестирование

```bash
pytest tests/
```

## Лицензия

Проект использует ту же лицензию, что и основная система AI-NK.
