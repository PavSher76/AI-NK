# Отчет по реализации устойчивой индексации RAG-Service

## Обзор

Реализован функционал устойчивой индексации для RAG-Service с поддержкой:
- Повторных попыток подключения к базе данных
- Автоматического восстановления соединений
- Продолжения индексации после сбоев
- Мониторинга состояния системы

## Основные компоненты

### 1. Улучшенный DatabaseManager

**Файл:** `rag_service/services/database_manager.py`

#### Новые возможности:
- **Декоратор retry_on_connection_error**: Автоматические повторные попытки с экспоненциальным backoff
- **Улучшенные контекстные менеджеры**: Поддержка повторных попыток для read/write соединений
- **Автоматическое пересоздание пулов**: При критических ошибках соединения
- **Методы для управления индексацией**: Отслеживание прогресса и повторных попыток

#### Ключевые методы:
```python
@retry_on_connection_error(max_retries=3, base_delay=1.0, max_delay=60.0)
def _init_connection_pools(self)

def _ensure_pools_initialized(self)
def _recreate_pools(self)
def get_pending_documents_for_indexing(self)
def mark_document_for_retry(self, document_id, error_message)
def get_documents_with_failed_indexing(self, max_retries=3)
def update_indexing_progress(self, document_id, progress_percent, status_message)
```

### 2. ResilientIndexingService

**Файл:** `rag_service/services/indexing_service.py`

#### Архитектура:
- **Многопоточная обработка**: До 3 параллельных worker потоков
- **Очередь задач**: Приоритизация и управление задачами индексации
- **Автоматические повторные попытки**: С экспоненциальной задержкой
- **Мониторинг**: Отслеживание зависших задач и восстановление

#### Ключевые классы:
```python
class IndexingStatus(Enum):
    PENDING = "pending"
    INDEXING = "indexing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"

@dataclass
class IndexingTask:
    document_id: int
    filename: str
    content: bytes
    category: str
    retry_count: int = 0
    max_retries: int = 3
    priority: int = 0
    created_at: datetime = None
    last_attempt: datetime = None
```

#### Основные методы:
```python
def start(self)  # Запуск сервиса
def stop(self)   # Остановка сервиса
def add_indexing_task(self, document_id, filename, content, category, priority, max_retries)
def get_status(self)  # Получение статуса
```

### 3. Интеграция с OllamaRAGService

**Файл:** `rag_service/services/ollama_rag_service_refactored.py`

#### Новые методы:
```python
def start_indexing_service(self)
def stop_indexing_service(self)
def get_indexing_service_status(self)
def add_document_for_indexing(self, document_id, filename, content, category, priority, max_retries)
def retry_failed_documents(self, max_retries=3)
```

### 4. API Endpoints

**Файл:** `rag_service/api/endpoints.py`

#### Новые endpoints:
- `POST /indexing/start` - Запуск сервиса индексации
- `POST /indexing/stop` - Остановка сервиса индексации
- `GET /indexing/status` - Статус сервиса индексации
- `POST /indexing/retry-failed` - Повтор неудачных документов
- `GET /indexing/pending` - Документы в очереди
- `GET /indexing/failed` - Неудачные документы
- `GET /database/health` - Состояние БД

## Механизм повторных попыток

### 1. Экспоненциальный Backoff
```python
delay = min(base_delay * (exponential_base ** attempt), max_delay)
jitter = random.uniform(0.1, 0.3) * delay
total_delay = delay + jitter
```

### 2. Типы ошибок для повторных попыток
- `psycopg2.OperationalError` - Проблемы с соединением
- `psycopg2.InterfaceError` - Проблемы с интерфейсом
- `psycopg2.DatabaseError` - Ошибки базы данных

### 3. Стратегия восстановления
1. **Повторная попытка** с увеличивающейся задержкой
2. **Пересоздание пулов** при критических ошибках
3. **Помечание документов** для повторной обработки
4. **Мониторинг зависших задач** (таймаут 10 минут)

## Мониторинг и статистика

### Статистика индексации:
```json
{
  "is_running": true,
  "uptime_seconds": 3600,
  "queue_size": 5,
  "active_tasks": 2,
  "failed_tasks": 1,
  "stats": {
    "total_processed": 100,
    "successful": 95,
    "failed": 3,
    "retries": 7
  },
  "worker_threads": 3
}
```

### Состояние базы данных:
```json
{
  "status": "healthy",
  "read_connection": "ok",
  "write_connection": "ok",
  "read_pool_size": 5,
  "write_pool_size": 5
}
```

## Использование

### 1. Запуск сервиса индексации
```bash
curl -X POST http://localhost:8000/indexing/start
```

### 2. Добавление документа для индексации
```python
ollama_rag_service = OllamaRAGService()
ollama_rag_service.add_document_for_indexing(
    document_id=123,
    filename="document.pdf",
    content=file_content,
    category="gost",
    priority=0,
    max_retries=3
)
```

### 3. Проверка статуса
```bash
curl http://localhost:8000/indexing/status
```

### 4. Повтор неудачных документов
```bash
curl -X POST "http://localhost:8000/indexing/retry-failed?max_retries=3"
```

## Преимущества реализации

### 1. Устойчивость к сбоям
- Автоматическое восстановление соединений
- Продолжение работы после временных сбоев
- Отслеживание и повторная обработка неудачных задач

### 2. Масштабируемость
- Многопоточная обработка
- Приоритизация задач
- Управление ресурсами

### 3. Мониторинг
- Детальная статистика
- Отслеживание прогресса
- Выявление проблем

### 4. Гибкость
- Настраиваемые параметры повторных попыток
- Различные стратегии восстановления
- API для управления

## Конфигурация

### Параметры DatabaseManager:
```python
DatabaseManager(
    connection_string="postgresql://...",
    min_connections=1,
    max_connections=10,
    max_retries=3,
    retry_delay=1.0
)
```

### Параметры ResilientIndexingService:
```python
ResilientIndexingService(
    db_manager=db_manager,
    qdrant_service=qdrant_service,
    embedding_service=embedding_service,
    max_concurrent_tasks=3
)
```

## Логирование

Все операции логируются с соответствующими эмодзи:
- 🚀 Запуск сервисов
- ✅ Успешные операции
- ❌ Ошибки
- ⚠️ Предупреждения
- 🔄 Повторные попытки
- 📊 Статистика
- 🏥 Состояние здоровья

## Заключение

Реализованный функционал обеспечивает:
1. **Надежность** - автоматическое восстановление после сбоев
2. **Производительность** - многопоточная обработка
3. **Мониторинг** - детальное отслеживание состояния
4. **Управляемость** - API для контроля процесса

Система готова к использованию в продакшене и обеспечивает стабильную работу индексации документов даже при временных сбоях инфраструктуры.
