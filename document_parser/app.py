import os
import signal
import logging
import asyncio
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from core.config import LOG_LEVEL, LOG_FORMAT
from database.connection import DatabaseConnection
from services.norm_control_service import NormControlService
from utils.memory_utils import log_memory_usage

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/app/document_parser.log')
    ]
)
logger = logging.getLogger(__name__)

# Глобальные переменные
db_connection = None
norm_control_service = None
startup_time = None

def signal_handler(signum, frame):
    """Обработчик сигналов для graceful shutdown"""
    logger.info(f"Received signal {signum}, starting graceful shutdown...")
    if db_connection:
        db_connection.close_connections()
    logger.info("Graceful shutdown completed")
    exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    global db_connection, norm_control_service, startup_time
    
    # Startup
    startup_time = datetime.now()
    logger.info(f"🚀 [STARTUP] Starting Document Parser Service at {startup_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
    
    try:
        # Инициализация подключений к базам данных
        logger.info("🔍 [STARTUP] Initializing database connections...")
        db_connection = DatabaseConnection()
        
        # Инициализация сервисов
        logger.info("🔍 [STARTUP] Initializing services...")
        norm_control_service = NormControlService(db_connection)
        
        # Логирование использования памяти
        log_memory_usage("startup")
        
        logger.info("✅ [STARTUP] Document Parser Service started successfully")
        yield
        
    except Exception as e:
        logger.error(f"❌ [STARTUP] Failed to start Document Parser Service: {e}")
        raise
    finally:
        # Shutdown
        logger.info("🔄 [SHUTDOWN] Starting shutdown process...")
        if db_connection:
            db_connection.close_connections()
        logger.info("✅ [SHUTDOWN] Document Parser Service shutdown completed")

# Создание FastAPI приложения
app = FastAPI(
    title="Document Parser Service",
    description="Сервис для обработки и анализа документов",
    version="1.0.0",
    lifespan=lifespan
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency для получения сервиса
def get_norm_control_service() -> NormControlService:
    if norm_control_service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return norm_control_service

# Health check endpoint
@app.get("/health")
async def health_check():
    """Проверка состояния сервиса"""
    try:
        if db_connection and db_connection.db_conn and not db_connection.db_conn.closed:
            return {
                "status": "healthy",
                "service": "document-parser",
                "uptime": (datetime.now() - startup_time).total_seconds() if startup_time else 0,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy",
                    "service": "document-parser",
                    "error": "Database connection not available",
                    "timestamp": datetime.now().isoformat()
                }
            )
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "document-parser",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

# Metrics endpoint
@app.get("/metrics")
async def get_metrics():
    """Получение метрик сервиса"""
    try:
        from utils.memory_utils import get_memory_usage
        
        memory_info = get_memory_usage()
        uptime = (datetime.now() - startup_time).total_seconds() if startup_time else 0
        
        return {
            "service": "document-parser",
            "uptime_seconds": uptime,
            "memory_usage_mb": memory_info.get("rss_mb", 0),
            "memory_percent": memory_info.get("percent", 0),
            "available_memory_mb": memory_info.get("available_mb", 0),
            "database_connected": db_connection.db_conn is not None and not db_connection.db_conn.closed if db_connection else False,
            "qdrant_connected": db_connection.qdrant_client is not None if db_connection else False,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Metrics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Асинхронная функция для выполнения проверки нормоконтроля
async def perform_async_norm_control_check(document_id: int, document_content: str):
    """Асинхронное выполнение проверки нормоконтроля"""
    try:
        logger.info(f"🚀 [ASYNC_CHECK] Starting async norm control check for document {document_id}")
        
        # Выполняем проверку документа
        result = await norm_control_service.perform_norm_control_check(document_id, document_content)
        
        # Обновляем статус на "completed"
        update_checkable_document_status(document_id, "completed")
        
        logger.info(f"✅ [ASYNC_CHECK] Async norm control check completed for document {document_id}")
        
    except Exception as e:
        logger.error(f"❌ [ASYNC_CHECK] Async norm control check failed for document {document_id}: {e}")
        # Обновляем статус на "error"
        try:
            update_checkable_document_status(document_id, "error")
        except Exception:
            pass

def update_checkable_document_status(document_id: int, status: str):
    """Обновление статуса проверяемого документа"""
    def _update_status(conn):
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE checkable_documents 
                SET processing_status = %s
                WHERE id = %s
            """, (status, document_id))
            logger.info(f"Updated checkable document {document_id} status to: {status}")
    
    try:
        db_connection.execute_in_transaction(_update_status)
    except Exception as e:
        logger.error(f"Error updating checkable document status: {e}")
        raise

# API endpoints
@app.post("/checkable-documents/{document_id}/check")
async def trigger_norm_control_check(
    document_id: int,
    norm_control_service: NormControlService = Depends(get_norm_control_service)
):
    """Принудительный запуск проверки нормоконтроля"""
    try:
        # Проверяем существование документа
        document = get_checkable_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Проверяем текущий статус документа
        if document.get("processing_status") == "processing":
            return {
                "status": "already_processing",
                "message": "Document is already being processed"
            }
        
        # Обновляем статус на "processing"
        update_checkable_document_status(document_id, "processing")
        
        # Получаем содержимое документа
        with db_connection.db_conn.cursor() as cursor:
            cursor.execute("""
                SELECT element_content
                FROM checkable_elements
                WHERE checkable_document_id = %s
                ORDER BY page_number, id
            """, (document_id,))
            elements = cursor.fetchall()
        
        if not elements:
            update_checkable_document_status(document_id, "error")
            raise HTTPException(status_code=404, detail="Document content not found")
        
        # Объединяем содержимое
        document_content = "\n\n".join([elem["element_content"] for elem in elements])
        
        # Запускаем асинхронную проверку
        asyncio.create_task(
            perform_async_norm_control_check(document_id, document_content)
        )
        
        return {
            "status": "started",
            "message": "Norm control check started asynchronously",
            "document_id": document_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Trigger norm control check error: {e}")
        # Обновляем статус на "error" в случае ошибки
        try:
            update_checkable_document_status(document_id, "error")
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=str(e))

def get_checkable_document(document_id: int):
    """Получение информации о проверяемом документе"""
    def _get_document(conn):
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT id, original_filename, file_type, file_size, upload_date, 
                           processing_status, category, review_deadline, review_status, 
                           assigned_reviewer
                    FROM checkable_documents 
                    WHERE id = %s
                """, (document_id,))
                document = cursor.fetchone()
                return dict(document) if document else None
        except Exception as db_error:
            logger.error(f"🔍 [DATABASE] Error in _get_document: {db_error}")
            raise
    
    try:
        logger.debug(f"🔍 [DATABASE] Starting read-only transaction for get_checkable_document {document_id}")
        result = db_connection.execute_in_read_only_transaction(_get_document)
        logger.debug(f"🔍 [DATABASE] Successfully retrieved checkable document {document_id} using read-only transaction")
        return result
    except Exception as e:
        logger.error(f"Get checkable document error: {e}")
        return None

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8001,
        reload=False,
        log_level=LOG_LEVEL.lower()
    )
