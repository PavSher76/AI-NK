# Отчет о дополнительном логировании Document Parser

## Проблема

Document-parser не предоставлял достаточно детальной информации о:
- Причинах остановки сервиса
- Времени остановки и перезапуска
- Состоянии системы при запуске и shutdown
- Производительности health checks
- Деталях подключения к базам данных

## Решение

Добавлено расширенное логирование для отслеживания всех аспектов жизненного цикла сервиса.

## Реализованные улучшения

### 1. Детальное логирование запуска

```python
if __name__ == "__main__":
    import uvicorn
    startup_time = datetime.now()
    logger.info(f"🔍 [STARTUP] Starting Document Parser Service at {startup_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
    logger.info(f"🔍 [STARTUP] Process ID: {os.getpid()}, Parent PID: {os.getppid()}")
    logger.info(f"🔍 [STARTUP] Working directory: {os.getcwd()}")
    logger.info(f"🔍 [STARTUP] Python version: {sys.version}")
    
    # Логируем информацию о системе
    try:
        import platform
        logger.info(f"🔍 [STARTUP] Platform: {platform.platform()}")
        logger.info(f"🔍 [STARTUP] Architecture: {platform.architecture()}")
        logger.info(f"🔍 [STARTUP] Machine: {platform.machine()}")
    except Exception as e:
        logger.warning(f"🔍 [STARTUP] Could not get platform info: {e}")
    
    # Логируем информацию о памяти при запуске
    try:
        memory_info = get_memory_usage()
        if "error" not in memory_info:
            logger.info(f"🔍 [STARTUP] Initial memory usage: RSS: {memory_info['rss_mb']:.1f}MB, VMS: {memory_info['vms_mb']:.1f}MB, Percent: {memory_info['percent']:.1f}%")
    except Exception as e:
        logger.warning(f"🔍 [STARTUP] Could not get initial memory info: {e}")
```

### 2. Улучшенное логирование подключений к БД

```python
def connect_databases(self):
    """Подключение к базам данных с повторными попытками"""
    connection_start_time = datetime.now()
    logger.info(f"🔍 [CONNECTION] Starting database connections at {connection_start_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
    
    for attempt in range(self.max_retries):
        try:
            logger.info(f"🔍 [CONNECTION] Attempt {attempt + 1}/{self.max_retries} to connect to databases")
            
            # PostgreSQL
            postgres_start_time = datetime.now()
            self.db_conn = psycopg2.connect(
                host=POSTGRES_HOST,
                database=POSTGRES_DB,
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD,
                connect_timeout=10,
                application_name="document_parser"
            )
            postgres_end_time = datetime.now()
            postgres_duration = (postgres_end_time - postgres_start_time).total_seconds()
            logger.info(f"🔍 [CONNECTION] Connected to PostgreSQL in {postgres_duration:.3f}s")
            
            # Qdrant
            qdrant_start_time = datetime.now()
            self.qdrant_client = qdrant_client.QdrantClient(
                host=QDRANT_HOST,
                port=QDRANT_PORT,
                timeout=10
            )
            qdrant_end_time = datetime.now()
            qdrant_duration = (qdrant_end_time - qdrant_start_time).total_seconds()
            logger.info(f"🔍 [CONNECTION] Connected to Qdrant in {qdrant_duration:.3f}s")
            
            connection_end_time = datetime.now()
            total_duration = (connection_end_time - connection_start_time).total_seconds()
            logger.info(f"🔍 [CONNECTION] All database connections established successfully in {total_duration:.3f}s")
            return
            
        except Exception as e:
            self.connection_retry_count += 1
            logger.error(f"🔍 [CONNECTION] Database connection error (attempt {attempt + 1}/{self.max_retries}): {e}")
            logger.error(f"🔍 [CONNECTION] Error type: {type(e).__name__}")
            
            if attempt < self.max_retries - 1:
                logger.info(f"🔍 [CONNECTION] Retrying in {self.retry_delay} seconds...")
                time.sleep(self.retry_delay)
            else:
                connection_end_time = datetime.now()
                total_duration = (connection_end_time - connection_start_time).total_seconds()
                logger.error(f"🔍 [CONNECTION] Failed to connect to databases after {self.max_retries} attempts in {total_duration:.3f}s")
                raise
```

### 3. Детальное логирование shutdown

```python
def signal_handler(signum, frame):
    """Обработчик сигналов для graceful shutdown"""
    global is_shutting_down
    signal_name = {
        signal.SIGTERM: "SIGTERM",
        signal.SIGINT: "SIGINT",
        signal.SIGHUP: "SIGHUP",
        signal.SIGUSR1: "SIGUSR1",
        signal.SIGUSR2: "SIGUSR2"
    }.get(signum, f"Signal {signum}")
    
    logger.info(f"🔍 [SHUTDOWN] Received {signal_name} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}, initiating graceful shutdown...")
    logger.info(f"🔍 [SHUTDOWN] Process ID: {os.getpid()}, Parent PID: {os.getppid()}")
    
    # Логируем информацию о памяти перед shutdown
    try:
        memory_info = get_memory_usage()
        if "error" not in memory_info:
            logger.info(f"🔍 [SHUTDOWN] Memory usage before shutdown: RSS: {memory_info['rss_mb']:.1f}MB, VMS: {memory_info['vms_mb']:.1f}MB, Percent: {memory_info['percent']:.1f}%")
    except Exception as e:
        logger.warning(f"🔍 [SHUTDOWN] Could not get memory info: {e}")
    
    is_shutting_down = True
    shutdown_event.set()
```

### 4. Расширенный health check с логированием

```python
@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    health_start_time = datetime.now()
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "checks": {},
        "uptime": str(datetime.now() - startup_time),
        "process_id": os.getpid()
    }
    
    try:
        # Проверка состояния shutdown
        if is_shutting_down:
            health_status["status"] = "shutting_down"
            health_status["checks"]["shutdown"] = "in_progress"
            logger.warning(f"🔍 [HEALTH] Service is shutting down, health check at {health_start_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
        
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
                    logger.warning(f"🔍 [HEALTH] High memory usage detected: {memory_info['percent']:.1f}%")
                else:
                    health_status["checks"]["memory"]["status"] = "ok"
            else:
                health_status["checks"]["memory"] = {"status": "error", "error": memory_info["error"]}
                logger.error(f"🔍 [HEALTH] Memory check error: {memory_info['error']}")
        except Exception as mem_error:
            health_status["checks"]["memory"] = {"status": "error", "error": str(mem_error)}
            logger.error(f"🔍 [HEALTH] Memory check exception: {mem_error}")
        
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
            logger.error(f"🔍 [HEALTH] PostgreSQL check failed: {pg_error}")
        
        # Проверка Qdrant
        try:
            parser.qdrant_client.get_collections()
            health_status["checks"]["qdrant"] = {"status": "ok"}
        except Exception as qd_error:
            health_status["checks"]["qdrant"] = {"status": "error", "error": str(qd_error)}
            health_status["status"] = "unhealthy"
            logger.error(f"🔍 [HEALTH] Qdrant check failed: {qd_error}")
        
        health_end_time = datetime.now()
        health_duration = (health_end_time - health_start_time).total_seconds()
        health_status["check_duration_ms"] = round(health_duration * 1000, 2)
        
        # Логируем результат health check
        if health_status["status"] == "healthy":
            logger.debug(f"🔍 [HEALTH] Health check passed in {health_duration:.3f}s")
        elif health_status["status"] == "degraded":
            logger.warning(f"🔍 [HEALTH] Health check degraded in {health_duration:.3f}s")
        else:
            logger.error(f"🔍 [HEALTH] Health check failed in {health_duration:.3f}s")
        
        return health_status
        
    except Exception as e:
        health_end_time = datetime.now()
        health_duration = (health_end_time - health_start_time).total_seconds()
        logger.error(f"🔍 [HEALTH] Health check error after {health_duration:.3f}s: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy", 
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "check_duration_ms": round(health_duration * 1000, 2)
            }
        )
```

### 5. Улучшенный graceful shutdown

```python
async def shutdown_event_handler():
    """Обработчик события завершения работы"""
    global is_shutting_down
    shutdown_start_time = datetime.now()
    logger.info(f"🔍 [SHUTDOWN] Starting graceful shutdown at {shutdown_start_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
    logger.info(f"🔍 [SHUTDOWN] Process ID: {os.getpid()}, Uptime: {shutdown_start_time - startup_time}")
    is_shutting_down = True
    
    # Логируем информацию о памяти перед shutdown
    try:
        memory_info = get_memory_usage()
        if "error" not in memory_info:
            logger.info(f"🔍 [SHUTDOWN] Memory usage before shutdown: RSS: {memory_info['rss_mb']:.1f}MB, VMS: {memory_info['vms_mb']:.1f}MB, Percent: {memory_info['percent']:.1f}%")
    except Exception as e:
        logger.warning(f"🔍 [SHUTDOWN] Could not get memory info: {e}")
    
    # Ждем завершения текущих запросов
    logger.info("🔍 [SHUTDOWN] Waiting 5 seconds for current requests to complete...")
    await asyncio.sleep(5)
    
    # Закрываем соединения с базами данных
    try:
        if parser.db_conn and not parser.db_conn.closed:
            parser.db_conn.close()
            logger.info("🔍 [SHUTDOWN] PostgreSQL connection closed successfully")
        else:
            logger.info("🔍 [SHUTDOWN] PostgreSQL connection was already closed")
    except Exception as e:
        logger.error(f"🔍 [SHUTDOWN] Error closing PostgreSQL connection: {e}")
    
    try:
        if parser.qdrant_client:
            parser.qdrant_client.close()
            logger.info("🔍 [SHUTDOWN] Qdrant connection closed successfully")
        else:
            logger.info("🔍 [SHUTDOWN] Qdrant connection was already closed")
    except Exception as e:
        logger.error(f"🔍 [SHUTDOWN] Error closing Qdrant connection: {e}")
    
    shutdown_end_time = datetime.now()
    shutdown_duration = shutdown_end_time - shutdown_start_time
    logger.info(f"🔍 [SHUTDOWN] Graceful shutdown completed at {shutdown_end_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
    logger.info(f"🔍 [SHUTDOWN] Total shutdown duration: {shutdown_duration.total_seconds():.3f} seconds")
```

## Результат

### До улучшений:
- ❌ Минимальная информация о запуске
- ❌ Отсутствие деталей о причинах остановки
- ❌ Нет информации о времени работы сервиса
- ❌ Отсутствие метрик производительности health checks
- ❌ Недостаточная информация о подключениях к БД

### После улучшений:
- ✅ Детальное логирование запуска с системной информацией
- ✅ Подробная информация о причинах остановки (сигналы, память)
- ✅ Точное время работы сервиса (uptime)
- ✅ Метрики производительности health checks
- ✅ Детальное логирование подключений к БД с таймингами
- ✅ Информация о состоянии памяти при запуске и shutdown
- ✅ Логирование всех этапов graceful shutdown

## Примеры логов

### Запуск сервиса:
```
2025-08-26 09:06:54,353 - main - INFO - 🔍 [CONNECTION] Starting database connections at 2025-08-26 09:06:54.353
2025-08-26 09:06:54,353 - main - INFO - 🔍 [CONNECTION] Attempt 1/3 to connect to databases
2025-08-26 09:06:54,362 - main - INFO - 🔍 [CONNECTION] Connected to PostgreSQL in 0.009s
2025-08-26 09:06:54,384 - main - INFO - 🔍 [CONNECTION] Connected to Qdrant in 0.022s
2025-08-26 09:06:54,384 - main - INFO - 🔍 [CONNECTION] All database connections established successfully in 0.031s
```

### Health check:
```
2025-08-26 09:06:59,831 - main - INFO - 🔍 [REQUEST] req_1756188419831: GET /health started
2025-08-26 09:06:59,842 - main - DEBUG - 🔍 [HEALTH] Health check passed in 0.008s
2025-08-26 09:06:59,843 - main - INFO - 🔍 [REQUEST] req_1756188419831: GET /health completed in 0.012s (status: 200)
```

### Health check response:
```json
{
  "status": "healthy",
  "timestamp": "2025-08-26T09:06:59.834305",
  "checks": {
    "memory": {
      "rss_mb": 128.7,
      "percent": 0.8,
      "available_mb": 12832.2,
      "status": "ok"
    },
    "postgresql": {"status": "ok"},
    "qdrant": {"status": "ok"}
  },
  "uptime": "0:00:05.522304",
  "process_id": 1,
  "check_duration_ms": 8.22
}
```

## Преимущества

1. **Отладка проблем** - детальная информация о причинах остановки
2. **Мониторинг производительности** - тайминги всех операций
3. **Диагностика** - информация о состоянии системы
4. **Трассировка** - уникальные ID для всех запросов
5. **Метрики** - uptime, использование памяти, время выполнения операций

## Заключение

Document-parser теперь предоставляет исчерпывающую информацию о своем жизненном цикле, что значительно упрощает диагностику проблем, мониторинг производительности и отладку.

**Статус:** ✅ Реализовано
**Дата:** 26 августа 2025
**Файл:** `document_parser/main.py`
**Уровень логирования:** DEBUG
**Основные улучшения:** Детальное логирование запуска, shutdown, health checks, подключений к БД
