import os
import signal
import logging
import asyncio
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from core.config import LOG_LEVEL, LOG_FORMAT
from database.connection import DatabaseConnection
from services.norm_control_service import NormControlService
from services.hierarchical_check_service import HierarchicalCheckService
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
hierarchical_check_service = None
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
    global db_connection, norm_control_service, hierarchical_check_service, startup_time
    
    # Startup
    startup_time = datetime.now()
    logger.info(f"🚀 [STARTUP] Starting Document Parser Service at {startup_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
    
    try:
        # Инициализация подключений к базам данных
        logger.info("🔍 [STARTUP] Initializing database connections...")
        db_connection = DatabaseConnection()
        
        # Инициализация сервисов
        logger.info("🔍 [STARTUP] Initializing services...")
        logger.info("🔍 [STARTUP] Creating NormControlService...")
        norm_control_service = NormControlService(db_connection)
        logger.info("🔍 [STARTUP] NormControlService created successfully")
        logger.info("🔍 [STARTUP] Creating HierarchicalCheckService...")
        hierarchical_check_service = HierarchicalCheckService(db_connection)
        logger.info("🔍 [STARTUP] HierarchicalCheckService created successfully")
        
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

# Настройка лимитов для загрузки файлов
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

class LargeFileMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Увеличиваем лимит для загрузки файлов
        if request.url.path.startswith("/upload"):
            # Устанавливаем больший лимит для загрузки
            request.scope["client_max_size"] = 100 * 1024 * 1024  # 100 MB
        return await call_next(request)

app.add_middleware(LargeFileMiddleware)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency для получения сервисов
def get_norm_control_service() -> NormControlService:
    if norm_control_service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return norm_control_service

def get_hierarchical_check_service() -> HierarchicalCheckService:
    if hierarchical_check_service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return hierarchical_check_service

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
    """Получение метрик сервиса в формате Prometheus"""
    try:
        from utils.memory_utils import get_memory_usage
        
        memory_info = get_memory_usage()
        uptime = (datetime.now() - startup_time).total_seconds() if startup_time else 0
        db_connected = 1 if (db_connection.db_conn is not None and not db_connection.db_conn.closed if db_connection else False) else 0
        qdrant_connected = 1 if (db_connection.qdrant_client is not None if db_connection else False) else 0
        
        # Формат метрик Prometheus
        metrics = f"""# HELP document_parser_uptime_seconds Время работы сервиса в секундах
# TYPE document_parser_uptime_seconds gauge
document_parser_uptime_seconds {uptime}

# HELP document_parser_memory_usage_mb Использование памяти в МБ
# TYPE document_parser_memory_usage_mb gauge
document_parser_memory_usage_mb {memory_info.get("rss_mb", 0)}

# HELP document_parser_memory_percent Процент использования памяти
# TYPE document_parser_memory_percent gauge
document_parser_memory_percent {memory_info.get("percent", 0)}

# HELP document_parser_available_memory_mb Доступная память в МБ
# TYPE document_parser_available_memory_mb gauge
document_parser_available_memory_mb {memory_info.get("available_mb", 0)}

# HELP document_parser_database_connected Статус подключения к базе данных
# TYPE document_parser_database_connected gauge
document_parser_database_connected {db_connected}

# HELP document_parser_qdrant_connected Статус подключения к Qdrant
# TYPE document_parser_qdrant_connected gauge
document_parser_qdrant_connected {qdrant_connected}

# HELP document_parser_info Информация о сервисе
# TYPE document_parser_info gauge
document_parser_info{{service="document-parser"}} 1
"""
        
        return Response(content=metrics, media_type="text/plain")
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
        document_content = "\n\n".join([elem[0] for elem in elements])  # element_content
        
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

# Получение списка проверяемых документов
@app.get("/checkable-documents")
async def get_checkable_documents():
    """Получение списка всех проверяемых документов"""
    try:
        def _get_documents(conn):
            try:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT id, original_filename, file_type, file_size, upload_date, 
                               processing_status, category, review_deadline, review_status, 
                               assigned_reviewer
                        FROM checkable_documents 
                        ORDER BY upload_date DESC
                    """)
                    documents = cursor.fetchall()
                    result = []
                    for doc in documents:
                        result.append({
                            'id': doc[0],
                            'original_filename': doc[1],
                            'file_type': doc[2],
                            'file_size': doc[3],
                            'upload_date': doc[4],
                            'processing_status': doc[5],
                            'category': doc[6],
                            'review_deadline': doc[7],
                            'review_status': doc[8],
                            'assigned_reviewer': doc[9]
                        })
                    return result
            except Exception as db_error:
                logger.error(f"🔍 [DATABASE] Error in _get_documents: {db_error}")
                raise
        
        try:
            logger.debug(f"🔍 [DATABASE] Starting read-only transaction for get_checkable_documents")
            documents = db_connection.execute_in_read_only_transaction(_get_documents)
            logger.debug(f"🔍 [DATABASE] Successfully retrieved {len(documents)} checkable documents using read-only transaction")
            return {"documents": documents}
        except Exception as e:
            logger.error(f"Get checkable documents error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get checkable documents error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Загрузка документа для проверки
@app.post("/upload/checkable")
async def upload_checkable_document(
    file: UploadFile = File(...),  # Убираем max_length, так как он не работает с UploadFile
    category: str = Form("other"),
    description: str = Form("")
):
    """Загрузка документа для проверки нормоконтроля"""
    logger.info(f"📤 [UPLOAD_CHECKABLE] Uploading document for check: {file.filename}")
    try:
        # Проверяем тип файла
        if not file.filename.lower().endswith(('.pdf', '.dwg', '.ifc', '.docx')):
            raise HTTPException(status_code=400, detail="Unsupported file type. Only PDF, DWG, IFC, and DOCX files are allowed.")
        
        # Читаем содержимое файла
        content = await file.read()
        file_size = len(content)
        
        # Проверяем размер файла (максимум 100 MB)
        max_file_size = 100 * 1024 * 1024  # 100 MB
        if file_size > max_file_size:
            raise HTTPException(
                status_code=413, 
                detail=f"File too large. Maximum size is {max_file_size // (1024*1024)} MB"
            )
        
        # Генерируем хеш документа для дедупликации
        import hashlib
        document_hash = hashlib.sha256(content).hexdigest()
        
        # Генерируем уникальный ID документа
        import time
        document_id = int(time.time() * 1000) % 100000000  # 8-значное число
        
        def _save_document(conn):
            try:
                with conn.cursor() as cursor:
                    # Проверяем, не загружен ли уже документ с таким хешем
                    cursor.execute("""
                        SELECT id FROM checkable_documents 
                        WHERE document_hash = %s
                    """, (document_hash,))
                    
                    if cursor.fetchone():
                        raise HTTPException(status_code=409, detail="Document with this content already exists")
                    
                    # Сохраняем документ в базу данных
                    cursor.execute("""
                        INSERT INTO checkable_documents 
                        (id, filename, original_filename, file_type, file_size, document_hash, category, review_deadline)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP + INTERVAL '2 days')
                        RETURNING id
                    """, (
                        document_id,
                        file.filename,
                        file.filename,
                        file.filename.split('.')[-1].lower(),
                        file_size,
                        document_hash,
                        category
                    ))
                    
                    saved_id = cursor.fetchone()[0]
                    conn.commit()
                    return saved_id
                    
            except HTTPException:
                raise
            except Exception as db_error:
                logger.error(f"🔍 [DATABASE] Error in _save_document: {db_error}")
                conn.rollback()
                raise
        
        try:
            logger.debug(f"🔍 [DATABASE] Starting transaction for upload_checkable_document")
            saved_document_id = db_connection.execute_in_transaction(_save_document)
            logger.debug(f"🔍 [DATABASE] Successfully saved checkable document {saved_document_id}")
            
            return {
                "status": "success",
                "document_id": saved_document_id,
                "filename": file.filename,
                "file_size": file_size,
                "message": f"Document uploaded successfully for checking"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Upload checkable document error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [UPLOAD_CHECKABLE] Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Иерархическая проверка документа
@app.post("/checkable-documents/{document_id}/hierarchical-check")
async def trigger_hierarchical_check(
    document_id: int,
    hierarchical_check_service: HierarchicalCheckService = Depends(get_hierarchical_check_service)
):
    """Запуск иерархической проверки документа"""
    try:
        logger.info(f"🎯 [API] Hierarchical check requested for document {document_id}")
        logger.info(f"🎯 [API] Request timestamp: {datetime.now().isoformat()}")
        
        # Проверяем существование документа
        logger.debug(f"🎯 [API] Checking document existence for ID {document_id}")
        document = get_checkable_document(document_id)
        if not document:
            logger.error(f"🎯 [API] Document {document_id} not found")
            raise HTTPException(status_code=404, detail="Document not found")
        
        logger.info(f"🎯 [API] Document found: {document.get('original_filename', 'Unknown')}")
        
        # Проверяем текущий статус документа
        current_status = document.get("processing_status", "unknown")
        logger.info(f"🎯 [API] Current document status: {current_status}")
        
        if current_status == "processing":
            logger.warning(f"🎯 [API] Document {document_id} is already being processed")
            return {
                "status": "already_processing",
                "message": "Document is already being processed"
            }
        
        # Обновляем статус на "processing"
        logger.info(f"🎯 [API] Updating document status to 'processing'")
        update_checkable_document_status(document_id, "processing")
        
        # Запускаем асинхронную иерархическую проверку
        logger.info(f"🎯 [API] Starting async hierarchical check task")
        asyncio.create_task(
            perform_async_hierarchical_check(document_id, hierarchical_check_service)
        )
        
        response = {
            "status": "started",
            "message": "Hierarchical check started asynchronously",
            "document_id": document_id,
            "check_type": "hierarchical"
        }
        
        logger.info(f"🎯 [API] Hierarchical check response: {response}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Trigger hierarchical check error: {e}")
        # Обновляем статус на "error" в случае ошибки
        try:
            update_checkable_document_status(document_id, "error")
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=str(e))

# Асинхронная функция для выполнения иерархической проверки
async def perform_async_hierarchical_check(document_id: int, hierarchical_check_service: HierarchicalCheckService):
    """Асинхронное выполнение иерархической проверки"""
    try:
        logger.info(f"🚀 [ASYNC_HIERARCHICAL] Starting async hierarchical check for document {document_id}")
        logger.info(f"🚀 [ASYNC_HIERARCHICAL] Async task started at: {datetime.now().isoformat()}")
        
        # Выполняем иерархическую проверку документа
        logger.info(f"🚀 [ASYNC_HIERARCHICAL] Calling hierarchical_check_service.perform_hierarchical_check")
        result = await hierarchical_check_service.perform_hierarchical_check(document_id)
        
        logger.info(f"🚀 [ASYNC_HIERARCHICAL] Hierarchical check result received: {result.get('check_type', 'unknown')}")
        logger.info(f"🚀 [ASYNC_HIERARCHICAL] Execution time: {result.get('execution_time', 0):.2f}s")
        
        # Обновляем статус на "completed"
        logger.info(f"🚀 [ASYNC_HIERARCHICAL] Updating document status to 'completed'")
        update_checkable_document_status(document_id, "completed")
        
        logger.info(f"✅ [ASYNC_HIERARCHICAL] Async hierarchical check completed for document {document_id}")
        logger.info(f"✅ [ASYNC_HIERARCHICAL] Async task completed at: {datetime.now().isoformat()}")
        
    except Exception as e:
        logger.error(f"❌ [ASYNC_HIERARCHICAL] Async hierarchical check failed for document {document_id}: {e}")
        # Обновляем статус на "error"
        try:
            update_checkable_document_status(document_id, "error")
        except Exception:
            pass

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
                if document:
                    # Преобразуем кортеж в словарь по позициям
                    return {
                        'id': document[0],
                        'original_filename': document[1],
                        'file_type': document[2],
                        'file_size': document[3],
                        'upload_date': document[4],
                        'processing_status': document[5],
                        'category': document[6],
                        'review_deadline': document[7],
                        'review_status': document[8],
                        'assigned_reviewer': document[9]
                    }
                return None
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

# Удаление проверяемого документа
@app.delete("/checkable-documents/{document_id}")
async def delete_checkable_document(document_id: int):
    """Удаление проверяемого документа"""
    try:
        logger.info(f"🗑️ [DELETE] Deleting checkable document ID: {document_id}")
        
        # Проверяем существование документа
        document = get_checkable_document(document_id)
        if not document:
            logger.error(f"🗑️ [DELETE] Document {document_id} not found")
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Удаляем документ из базы данных
        def _delete_document(conn):
            try:
                with conn.cursor() as cursor:
                    # Удаляем связанные результаты проверки
                    cursor.execute("""
                        DELETE FROM hierarchical_check_results 
                        WHERE checkable_document_id = %s
                    """, (document_id,))
                    logger.info(f"🗑️ [DELETE] Deleted hierarchical check results for document {document_id}")
                    
                    # Удаляем сам документ
                    cursor.execute("""
                        DELETE FROM checkable_documents 
                        WHERE id = %s
                    """, (document_id,))
                    deleted_count = cursor.rowcount
                    conn.commit()
                    
                    if deleted_count > 0:
                        logger.info(f"✅ [DELETE] Successfully deleted document {document_id}")
                        return True
                    else:
                        logger.error(f"❌ [DELETE] No document deleted for ID {document_id}")
                        return False
                        
            except Exception as db_error:
                logger.error(f"🔍 [DATABASE] Error in _delete_document: {db_error}")
                raise
        
        try:
            logger.debug(f"🔍 [DATABASE] Starting transaction for delete_checkable_document {document_id}")
            success = db_connection.execute_in_transaction(_delete_document)
            
            if success:
                return {
                    "status": "success",
                    "message": f"Document {document_id} deleted successfully"
                }
            else:
                raise HTTPException(status_code=404, detail="Document not found")
                
        except Exception as e:
            logger.error(f"🗑️ [DELETE] Database error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"🗑️ [DELETE] Delete checkable document error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Получение отчета о проверке
@app.get("/checkable-documents/{document_id}/report")
async def get_report(document_id: int):
    """Получение отчета о проверке документа"""
    try:
        # Проверяем существование документа
        document = get_checkable_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Получаем результаты проверки
        def _get_report(conn):
            try:
                with conn.cursor() as cursor:
                    # Получаем результаты иерархической проверки
                    cursor.execute("""
                        SELECT project_info, norm_compliance_summary, sections_analysis, 
                               overall_status, execution_time
                        FROM hierarchical_check_results
                        WHERE checkable_document_id = %s
                        ORDER BY analysis_date DESC
                        LIMIT 1
                    """, (document_id,))
                    hierarchical_result = cursor.fetchone()
                    
                    return {
                        'hierarchical_result': {
                            'project_info': hierarchical_result[0] if hierarchical_result else None,
                            'norm_compliance_summary': hierarchical_result[1] if hierarchical_result else None,
                            'sections_analysis': hierarchical_result[2] if hierarchical_result else None,
                            'overall_status': hierarchical_result[3] if hierarchical_result else None,
                            'execution_time': hierarchical_result[4] if hierarchical_result else None
                        } if hierarchical_result else None,
                        'document_info': {
                            'id': document.get('id'),
                            'original_filename': document.get('original_filename'),
                            'processing_status': document.get('processing_status')
                        }
                    }
            except Exception as db_error:
                logger.error(f"🔍 [DATABASE] Error in _get_report: {db_error}")
                raise
        
        try:
            logger.debug(f"🔍 [DATABASE] Starting read-only transaction for get_report {document_id}")
            report = db_connection.execute_in_read_only_transaction(_get_report)
            logger.debug(f"🔍 [DATABASE] Successfully retrieved report for document {document_id}")
            return report
        except Exception as e:
            logger.error(f"Get report error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get report error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Скачивание отчета в формате PDF
@app.get("/checkable-documents/{document_id}/download-report")
async def download_report(document_id: int):
    """Скачивание отчета о проверке в формате PDF"""
    try:
        # Проверяем существование документа
        document = get_checkable_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Получаем отчет
        report_response = await get_report(document_id)
        
        # Генерируем PDF отчет
        try:
            from utils.pdf_generator import PDFReportGenerator
            
            pdf_generator = PDFReportGenerator()
            pdf_content = pdf_generator.generate_report_pdf(report_response)
            
            # Формируем имя файла
            filename = f"report_{document_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
            # Возвращаем PDF файл
            from fastapi.responses import Response
            return Response(
                content=pdf_content,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}",
                    "Content-Length": str(len(pdf_content))
                }
            )
            
        except ImportError as e:
            logger.error(f"PDF generator import error: {e}")
            raise HTTPException(status_code=500, detail="PDF generation not available")
        except Exception as e:
            logger.error(f"PDF generation error: {e}")
            raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download report error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8001,
        reload=False,
        log_level=LOG_LEVEL.lower(),
        timeout_keep_alive=300,  # 5 минут для keep-alive
        timeout_graceful_shutdown=30  # 30 секунд для graceful shutdown
    )
