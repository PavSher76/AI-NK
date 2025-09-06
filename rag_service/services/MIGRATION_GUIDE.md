# Руководство по миграции на модульную архитектуру

## Обзор изменений

Файл `ollama_rag_service.py` (2344 строки) был разбит на модули для упрощения работы и поддержки.

## Созданные модули

### 1. `embedding_service.py` (73 строки)
- `OllamaEmbeddingService` - работа с эмбеддингами через Ollama BGE-M3

### 2. `database_manager.py` (200 строк)
- `DatabaseManager` - управление базой данных PostgreSQL

### 3. `document_parser.py` (120 строк)
- `DocumentParser` - парсинг различных типов документов

### 4. `metadata_extractor.py` (200 строк)
- `MetadataExtractor` - извлечение и обработка метаданных документов

### 5. `document_chunker.py` (400 строк)
- `DocumentChunker` - разбиение документов на чанки

### 6. `ollama_rag_service_refactored.py` (514 строк)
- `OllamaRAGService` - основной сервис с модульной архитектурой

### 7. `ollama_rag_service_methods.py` (500 строк)
- `OllamaRAGServiceMethods` - дополнительные методы основного сервиса

## Шаги миграции

### Шаг 1: Обновление импортов

#### В файле `rag_service/api/endpoints.py`:
```python
# Заменить
from services.ollama_rag_service import OllamaRAGService

# На
from services.ollama_rag_service_refactored import OllamaRAGService
```

#### В файле `rag_service/ollama_main.py`:
```python
# Заменить
from services.ollama_rag_service import OllamaRAGService

# На
from services.ollama_rag_service_refactored import OllamaRAGService
```

### Шаг 2: Проверка совместимости

API остается полностью совместимым. Все методы работают так же:

```python
# Создание сервиса
rag_service = OllamaRAGService()

# Все методы работают как раньше
results = rag_service.hybrid_search("запрос", k=5)
consultation = rag_service.get_ntd_consultation("вопрос", "user_id")
documents = rag_service.get_documents()
stats = rag_service.get_stats()
```

### Шаг 3: Тестирование

#### Тест основного функционала:
```python
# Тест создания сервиса
rag_service = OllamaRAGService()
assert rag_service is not None

# Тест получения статистики
stats = rag_service.get_stats()
assert 'qdrant' in stats
assert 'postgresql' in stats

# Тест получения документов
documents = rag_service.get_documents()
assert isinstance(documents, list)
```

#### Тест отдельных модулей:
```python
# Тест модуля эмбеддингов
from services.embedding_service import OllamaEmbeddingService
embedding_service = OllamaEmbeddingService()
embedding = embedding_service.create_embedding("тестовый текст")
assert len(embedding) == 1024

# Тест модуля метаданных
from services.metadata_extractor import MetadataExtractor
metadata_extractor = MetadataExtractor()
metadata = metadata_extractor.extract_document_metadata("СП 22.13330.2016.pdf", 1)
assert metadata['doc_type'] == 'SP'
assert metadata['doc_number'] == '22.13330'
```

### Шаг 4: Обновление Docker

Убедитесь, что все модули включены в Docker образ:

```dockerfile
# В Dockerfile добавьте все новые файлы
COPY rag_service/services/embedding_service.py /app/services/
COPY rag_service/services/database_manager.py /app/services/
COPY rag_service/services/document_parser.py /app/services/
COPY rag_service/services/metadata_extractor.py /app/services/
COPY rag_service/services/document_chunker.py /app/services/
COPY rag_service/services/ollama_rag_service_refactored.py /app/services/
COPY rag_service/services/ollama_rag_service_methods.py /app/services/
```

### Шаг 5: Перезапуск сервисов

```bash
# Перезапуск RAG сервиса
docker-compose restart rag-service

# Проверка логов
docker logs ai-nk-rag-service-1 --tail 50
```

## Проверка работоспособности

### 1. Проверка запуска сервиса
```bash
# Проверка, что сервис запустился без ошибок
docker logs ai-nk-rag-service-1 | grep "Ollama RAG Service initialized with modular architecture"
```

### 2. Проверка API
```bash
# Проверка статистики
curl -X GET http://localhost:8003/stats

# Проверка документов
curl -X GET http://localhost:8003/documents
```

### 3. Проверка функциональности
```bash
# Тест реиндексации
curl -X POST http://localhost:8003/reindex -H "Content-Type: application/json" -d '{}'

# Тест консультации
curl -X POST http://localhost:8003/ntd-consultation \
  -H "Content-Type: application/json" \
  -d '{"message": "Что такое СП 22.13330.2016?", "user_id": "test"}'
```

## Откат изменений

Если возникнут проблемы, можно откатиться к старой версии:

### 1. Восстановление импортов
```python
# Вернуть старые импорты
from services.ollama_rag_service import OllamaRAGService
```

### 2. Перезапуск сервиса
```bash
docker-compose restart rag-service
```

## Преимущества новой архитектуры

### 1. **Упрощение разработки**
- Каждый модуль имеет четкую ответственность
- Легче находить и исправлять ошибки
- Простое добавление новых функций

### 2. **Улучшение тестирования**
- Можно тестировать модули независимо
- Более точное тестирование отдельных компонентов
- Упрощенное создание mock-объектов

### 3. **Повышение производительности**
- Модули загружаются только при необходимости
- Возможность оптимизации отдельных компонентов
- Лучшее управление памятью

### 4. **Упрощение поддержки**
- Изменения в одном модуле не влияют на другие
- Легче понимать код
- Простое добавление новых разработчиков

## Заключение

Миграция на модульную архитектуру значительно упрощает работу с RAG сервисом. Все изменения обратно совместимы, API остается неизменным, но код становится более читаемым и поддерживаемым.

После миграции рекомендуется:
1. Протестировать все основные функции
2. Обновить документацию
3. Обучить команду новой структуре
4. Планировать дальнейшее развитие модулей
