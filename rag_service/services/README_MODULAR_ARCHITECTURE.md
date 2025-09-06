# Модульная архитектура RAG сервиса

## Обзор

Файл `ollama_rag_service.py` был разбит на модули для упрощения работы и поддержки. Новая архитектура разделяет функциональность на логические компоненты.

## Структура модулей

### 1. `embedding_service.py`
**Назначение**: Работа с эмбеддингами через Ollama BGE-M3
- `OllamaEmbeddingService` - создание эмбеддингов для текста
- Нормализация эмбеддингов
- Обработка ошибок API Ollama

### 2. `database_manager.py`
**Назначение**: Управление базой данных PostgreSQL
- `DatabaseManager` - подключение к БД и выполнение запросов
- Сохранение документов в БД
- Обновление статусов обработки
- Получение списков документов и чанков
- Статистика БД

### 3. `document_parser.py`
**Назначение**: Парсинг различных типов документов
- `DocumentParser` - извлечение текста из PDF, DOCX, TXT
- Извлечение кодов документов из названий
- Извлечение кодов документов из запросов пользователей

### 4. `metadata_extractor.py`
**Назначение**: Извлечение и обработка метаданных документов
- `MetadataExtractor` - парсинг названий документов
- Определение типов документов (ГОСТ, СП, СНиП и т.д.)
- Извлечение года издания
- Создание метаданных для чанков
- Вычисление checksum файлов

### 5. `document_chunker.py`
**Назначение**: Разбиение документов на чанки
- `DocumentChunker` - создание чанков с правильной структурой
- Гранулярное чанкование с перекрытием
- Извлечение структуры документа (главы, разделы)
- Определение принадлежности чанков к разделам

### 6. `ollama_rag_service_refactored.py`
**Назначение**: Основной сервис с модульной архитектурой
- `OllamaRAGService` - главный класс сервиса
- Инициализация всех модулей
- Делегирование вызовов к соответствующим модулям
- Координация работы между модулями

### 7. `ollama_rag_service_methods.py`
**Назначение**: Дополнительные методы основного сервиса
- `OllamaRAGServiceMethods` - методы для гибридного поиска
- Консультации по НТД
- Fallback методы
- Форматирование ответов

## Преимущества новой архитектуры

### 1. **Модульность**
- Каждый модуль отвечает за свою область функциональности
- Легко тестировать отдельные компоненты
- Простое добавление новых функций

### 2. **Читаемость**
- Код разделен на логические блоки
- Каждый файл имеет четкое назначение
- Упрощенная навигация по коду

### 3. **Поддержка**
- Легче находить и исправлять ошибки
- Изменения в одном модуле не влияют на другие
- Простое добавление новых типов документов

### 4. **Переиспользование**
- Модули можно использовать независимо
- Легко создавать новые сервисы на основе существующих модулей

## Использование

### Импорт основного сервиса
```python
from rag_service.services.ollama_rag_service_refactored import OllamaRAGService

# Создание экземпляра сервиса
rag_service = OllamaRAGService()

# Использование методов
results = rag_service.hybrid_search("запрос", k=5)
consultation = rag_service.get_ntd_consultation("вопрос", "user_id")
```

### Импорт отдельных модулей
```python
from rag_service.services.embedding_service import OllamaEmbeddingService
from rag_service.services.database_manager import DatabaseManager
from rag_service.services.metadata_extractor import MetadataExtractor

# Использование отдельных модулей
embedding_service = OllamaEmbeddingService()
db_manager = DatabaseManager(connection_string)
metadata_extractor = MetadataExtractor()
```

## Миграция

### Замена старого сервиса
1. Замените импорт:
   ```python
   # Старый импорт
   from rag_service.services.ollama_rag_service import OllamaRAGService
   
   # Новый импорт
   from rag_service.services.ollama_rag_service_refactored import OllamaRAGService
   ```

2. API остается совместимым - все методы работают так же

### Обновление импортов в других файлах
Обновите импорты в файлах, которые используют RAG сервис:
- `rag_service/api/endpoints.py`
- `rag_service/ollama_main.py`
- Другие файлы, импортирующие `OllamaRAGService`

## Тестирование

### Тестирование отдельных модулей
```python
# Тест модуля эмбеддингов
from rag_service.services.embedding_service import OllamaEmbeddingService

embedding_service = OllamaEmbeddingService()
embedding = embedding_service.create_embedding("тестовый текст")
assert len(embedding) == 1024
```

### Тестирование основного сервиса
```python
# Тест основного сервиса
from rag_service.services.ollama_rag_service_refactored import OllamaRAGService

rag_service = OllamaRAGService()
stats = rag_service.get_stats()
assert 'qdrant' in stats
assert 'postgresql' in stats
```

## Планы развития

1. **Добавление новых модулей**:
   - Модуль для работы с различными форматами документов
   - Модуль для кэширования результатов
   - Модуль для мониторинга производительности

2. **Улучшение существующих модулей**:
   - Добавление поддержки новых типов документов
   - Улучшение алгоритмов чанкования
   - Оптимизация работы с базой данных

3. **Интеграция**:
   - Создание интерфейсов для модулей
   - Добавление dependency injection
   - Создание фабрик для модулей

## Заключение

Новая модульная архитектура значительно упрощает работу с RAG сервисом, делая код более читаемым, тестируемым и поддерживаемым. Каждый модуль имеет четкую ответственность, что облегчает разработку и отладку.
