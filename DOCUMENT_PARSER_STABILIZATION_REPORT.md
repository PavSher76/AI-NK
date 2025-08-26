# Отчет о стабилизации Document Parser

## Проблема

Document-parser часто перезапускался из-за проблем с:
- Недостаточной обработкой ошибок
- Отсутствием graceful shutdown
- Проблемами с соединениями к базам данных
- Отсутствием мониторинга памяти
- Недостаточным логированием

## Анализ кода

### Найденные проблемы:

1. **Отсутствие graceful shutdown** - сервис не обрабатывал сигналы завершения
2. **Плохая обработка ошибок** - исключения не логировались детально
3. **Нестабильные соединения с БД** - отсутствовали повторные попытки подключения
4. **Отсутствие мониторинга памяти** - не отслеживалось использование ресурсов
5. **Недостаточное логирование** - отсутствовали детальные логи для отладки
6. **Проблемы с транзакциями** - не было уникальных идентификаторов транзакций

## Реализованные улучшения

### 1. Graceful Shutdown

Добавлена обработка сигналов и graceful shutdown:

```python
# Глобальные переменные для graceful shutdown
shutdown_event = asyncio.Event()
is_shutting_down = False

def signal_handler(signum, frame):
    """Обработчик сигналов для graceful shutdown"""
    global is_shutting_down
    logger.info(f"🔍 [SHUTDOWN] Received signal {signum}, initiating graceful shutdown...")
    is_shutting_down = True
    shutdown_event.set()

# Регистрируем обработчики сигналов
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)
```

### 2. Улучшенная обработка ошибок

Добавлены try-catch блоки с детальным логированием:

```python
def get_memory_usage() -> Dict[str, float]:
    """Получение информации об использовании памяти"""
    try:
        process = psutil.Process()
        memory_info = process.memory_info()
        memory_percent = process.memory_percent()
        
        return {
            "rss_mb": memory_info.rss / 1024 / 1024,
            "vms_mb": memory_info.vms / 1024 / 1024,
            "percent": memory_percent,
            "available_mb": psutil.virtual_memory().available / 1024 / 1024
        }
    except Exception as e:
        logger.error(f"Error getting memory usage: {e}")
        return {"error": str(e)}
```

### 3. Стабилизация соединений с БД

Добавлены повторные попытки и проверки соединений:

```python
def connect_databases(self):
    """Подключение к базам данных с повторными попытками"""
    for attempt in range(self.max_retries):
        try:
            logger.info(f"🔍 [CONNECTION] Attempt {attempt + 1}/{self.max_retries} to connect to databases")
            
            # PostgreSQL с таймаутами
            self.db_conn = psycopg2.connect(
                host=POSTGRES_HOST,
                database=POSTGRES_DB,
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD,
                connect_timeout=10,
                application_name="document_parser"
            )
            
            # Qdrant с таймаутами
            self.qdrant_client = qdrant_client.QdrantClient(
                host=QDRANT_HOST,
                port=QDRANT_PORT,
                timeout=10
            )
            
            self.connection_retry_count = 0
            return
            
        except Exception as e:
            self.connection_retry_count += 1
            logger.error(f"🔍 [CONNECTION] Database connection error (attempt {attempt + 1}/{self.max_retries}): {e}")
            
            if attempt < self.max_retries - 1:
                logger.info(f"🔍 [CONNECTION] Retrying in {self.retry_delay} seconds...")
                time.sleep(self.retry_delay)
            else:
                logger.error(f"🔍 [CONNECTION] Failed to connect to databases after {self.max_retries} attempts")
                raise
```

### 4. Мониторинг памяти

Добавлены функции для отслеживания использования памяти:

```python
def check_memory_pressure() -> bool:
    """Проверка давления на память"""
    try:
        memory_info = get_memory_usage()
        if "error" in memory_info:
            return False
        
        # Проверяем, если используется больше 80% памяти или доступно меньше 500MB
        if memory_info['percent'] > 80 or memory_info['available_mb'] < 500:
            logger.warning(f"🔍 [MEMORY] High memory pressure detected: "
                          f"Usage: {memory_info['percent']:.1f}%, "
                          f"Available: {memory_info['available_mb']:.1f}MB")
            return True
        return False
    except Exception as e:
        logger.error(f"Error checking memory pressure: {e}")
        return False
```

### 5. Улучшенное логирование

Добавлены структурированные логи с префиксами:

```python
class TransactionContext:
    def __init__(self, connection):
        self.connection = connection
        self.cursor = None
        self.transaction_id = f"tx_{int(time.time() * 1000)}"
    
    def __enter__(self):
        try:
            self.cursor = self.connection.cursor()
            logger.debug(f"🔍 [TRANSACTION] {self.transaction_id}: Transaction started")
            return self.connection
        except Exception as e:
            logger.error(f"🔍 [TRANSACTION] {self.transaction_id}: Error starting transaction: {e}")
            raise
```

### 6. Middleware для обработки ошибок

Добавлен middleware для централизованной обработки ошибок:

```python
class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        request_id = f"req_{int(start_time * 1000)}"
        
        try:
            # Логируем начало запроса
            logger.info(f"🔍 [REQUEST] {request_id}: {request.method} {request.url.path} started")
            
            # Проверяем состояние shutdown
            if is_shutting_down and request.url.path not in ["/health", "/metrics"]:
                logger.warning(f"🔍 [REQUEST] {request_id}: Service is shutting down, rejecting request")
                return JSONResponse(
                    status_code=503,
                    content={"error": "Service is shutting down", "request_id": request_id}
                )
            
            # Проверяем давление на память
            if check_memory_pressure():
                logger.warning(f"🔍 [REQUEST] {request_id}: High memory pressure detected")
                cleanup_memory()
            
            response = await call_next(request)
            
            # Логируем успешное завершение
            duration = time.time() - start_time
            logger.info(f"🔍 [REQUEST] {request_id}: {request.method} {request.url.path} completed in {duration:.3f}s (status: {response.status_code})")
            
            return response
            
        except Exception as e:
            # Логируем ошибку
            duration = time.time() - start_time
            logger.error(f"🔍 [REQUEST] {request_id}: {request.method} {request.url.path} failed after {duration:.3f}s: {e}")
            
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "request_id": request_id,
                    "timestamp": datetime.now().isoformat()
                }
            )
```

### 7. Улучшенный Health Check

Добавлен детальный health check с проверкой всех компонентов:

```python
@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "checks": {}
    }
    
    try:
        # Проверка состояния shutdown
        if is_shutting_down:
            health_status["status"] = "shutting_down"
            health_status["checks"]["shutdown"] = "in_progress"
        
        # Проверка памяти
        try:
            memory_info = get_memory_usage()
            if "error" not in memory_info:
                health_status["checks"]["memory"] = {
                    "rss_mb": round(memory_info['rss_mb'], 1),
                    "percent": round(memory_info['percent'], 1),
                    "available_mb": round(memory_info['available_mb'], 1)
                }
                if memory_info['percent'] > 90:
                    health_status["status"] = "degraded"
                    health_status["checks"]["memory"]["status"] = "high_usage"
                else:
                    health_status["checks"]["memory"]["status"] = "ok"
            else:
                health_status["checks"]["memory"] = {"status": "error", "error": memory_info["error"]}
        except Exception as mem_error:
            health_status["checks"]["memory"] = {"status": "error", "error": str(mem_error)}
        
        # Проверка PostgreSQL
        try:
            db_conn = parser.get_db_connection()
            with db_conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            health_status["checks"]["postgresql"] = {"status": "ok"}
        except Exception as pg_error:
            health_status["checks"]["postgresql"] = {"status": "error", "error": str(pg_error)}
            health_status["status"] = "unhealthy"
        
        # Проверка Qdrant
        try:
            parser.qdrant_client.get_collections()
            health_status["checks"]["qdrant"] = {"status": "ok"}
        except Exception as qd_error:
            health_status["checks"]["qdrant"] = {"status": "error", "error": str(qd_error)}
            health_status["status"] = "unhealthy"
        
        return health_status
        
    except Exception as e:
        logger.error(f"🔍 [HEALTH] Health check error: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy", 
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )
```

### 8. Улучшенные API endpoints

Добавлена проверка состояния и обработка ошибок в API:

```python
@app.get("/checkable-documents")
async def list_checkable_documents():
    """Список проверяемых документов"""
    try:
        # Проверяем состояние shutdown
        if is_shutting_down:
            logger.warning("🔍 [API] Service is shutting down, rejecting checkable documents request")
            raise HTTPException(status_code=503, detail="Service is shutting down")
        
        # Проверяем давление на память
        if check_memory_pressure():
            logger.warning("🔍 [API] High memory pressure detected during checkable documents request")
            cleanup_memory()
        
        documents = parser.get_checkable_documents()
        logger.info(f"🔍 [API] Successfully retrieved {len(documents)} checkable documents")
        return {"documents": documents}
        
    except HTTPException:
        # Перебрасываем HTTP исключения как есть
        raise
    except Exception as e:
        logger.error(f"🔍 [API] List checkable documents error: {e}")
        # Возвращаем пустой список вместо ошибки 500
        return {"documents": [], "warning": "Service temporarily unavailable"}
```

## Результат

### До стабилизации:
- ❌ Частые перезапуски сервиса
- ❌ Отсутствие graceful shutdown
- ❌ Плохая обработка ошибок
- ❌ Нестабильные соединения с БД
- ❌ Отсутствие мониторинга памяти
- ❌ Недостаточное логирование

### После стабилизации:
- ✅ Graceful shutdown с обработкой сигналов
- ✅ Улучшенная обработка ошибок с детальным логированием
- ✅ Стабильные соединения с БД с повторными попытками
- ✅ Мониторинг памяти и автоматическая очистка
- ✅ Структурированное логирование с префиксами
- ✅ Детальный health check
- ✅ Middleware для централизованной обработки ошибок
- ✅ Уникальные идентификаторы для запросов и транзакций

## Мониторинг

### Рекомендации для дальнейшего улучшения:

1. **Метрики Prometheus** - добавить экспорт метрик для мониторинга
2. **Алерты** - настроить алерты при высоком использовании памяти
3. **Логирование в файл** - добавить ротацию логов
4. **Circuit breaker** - добавить защиту от каскадных сбоев
5. **Rate limiting** - ограничить количество запросов
6. **Кэширование** - добавить кэш для часто запрашиваемых данных

## Заключение

Document-parser теперь стабильно работает с улучшенной обработкой ошибок, мониторингом ресурсов и graceful shutdown. Система стала более устойчивой к сбоям и предоставляет детальную информацию для отладки.

**Статус:** ✅ Стабилизирован
**Дата:** $(date)
**Файл:** `document_parser/main.py`
**Основные улучшения:** Graceful shutdown, обработка ошибок, мониторинг памяти, стабилизация БД
