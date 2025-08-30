from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn
import hashlib
import time
import asyncio
import json
import logging
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import qdrant_client
from qdrant_client.models import Distance, VectorParams, PointStruct
import numpy as np

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
model_logger = logging.getLogger("model")

# Импорты из модулей
from api.endpoints import (
    get_documents,
    get_stats,
    get_document_chunks,
    get_documents_stats,
    delete_document,
    delete_document_indexes,
    reindex_documents,
    start_async_reindex,
    get_reindex_status,
    ntd_consultation_chat,
    ntd_consultation_stats,
    clear_consultation_cache,
    get_consultation_cache_stats,
    health_check,
    get_metrics
)

# Импорт RAG сервиса
from services.rag_service import RAGService

# Модели Pydantic
class NTDConsultationRequest(BaseModel):
    message: str
    user_id: str

class NTDConsultationResponse(BaseModel):
    status: str
    response: str
    sources: List[Dict[str, Any]]
    confidence: float
    documents_used: int
    timestamp: str

class SearchRequest(BaseModel):
    query: str
    k: int = 8
    document_filter: Optional[str] = None
    chapter_filter: Optional[str] = None
    chunk_type_filter: Optional[str] = None

# Создание FastAPI приложения
app = FastAPI(
    title="RAG Service",
    description="Сервис для работы с нормативными документами и RAG-системой",
    version="1.0.0"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Инициализация RAG сервиса (ленивая загрузка)
rag_service = None

def get_rag_service():
    """Ленивая инициализация RAG сервиса"""
    global rag_service
    if rag_service is None:
        rag_service = RAGService()
    return rag_service

# ============================================================================
# API эндпоинты для документов
# ============================================================================

@app.get("/documents")
async def documents_endpoint():
    """Получение списка нормативных документов"""
    return get_documents()

@app.get("/stats")
async def stats_endpoint():
    """Получение статистики RAG-системы"""
    return get_stats()

@app.get("/documents/{document_id}/chunks")
async def document_chunks_endpoint(document_id: int):
    """Получение информации о чанках конкретного документа"""
    return get_document_chunks(document_id)

@app.get("/documents/stats")
async def documents_stats_endpoint():
    """Получение статистики документов в формате для фронтенда"""
    return get_documents_stats()

@app.delete("/documents/{document_id}")
async def delete_document_endpoint(document_id: int):
    """Удаление документа и его индексов"""
    return delete_document(document_id)

@app.delete("/indexes/document/{document_id}")
async def delete_document_indexes_endpoint(document_id: int):
    """Удаление индексов конкретного документа"""
    return delete_document_indexes(document_id)

@app.post("/reindex-documents")
async def reindex_documents_endpoint():
    """Реиндексация всех документов (синхронная)"""
    return reindex_documents()

@app.post("/reindex-documents/async")
async def start_async_reindex_endpoint():
    """Запуск асинхронной реиндексации документов"""
    return start_async_reindex()

@app.get("/reindex-documents/status/{task_id}")
async def get_reindex_status_endpoint(task_id: str):
    """Получение статуса асинхронной реиндексации"""
    return get_reindex_status(task_id)

@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    category: str = Form("other"),
    description: str = Form("")
):
    """Загрузка и индексация нормативного документа"""
    try:
        # Проверяем тип файла
        if not file.filename.lower().endswith(('.pdf', '.docx', '.txt')):
            raise HTTPException(status_code=400, detail="Unsupported file type. Only PDF, DOCX, and TXT files are allowed.")
        
        # Читаем содержимое файла
        content = await file.read()
        
        # Генерируем уникальный ID документа
        hash_part = int(hashlib.md5(f"{file.filename}_{content[:100]}".encode()).hexdigest()[:3], 16)
        time_part = int(time.time()) % 100000
        document_id = time_part * 1000 + hash_part
        
        # Получаем RAG сервис
        rag_service_instance = get_rag_service()
        
        # Сохраняем документ в базу данных
        try:
            with rag_service_instance.db_manager.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO uploaded_documents 
                    (id, original_filename, file_content, file_size, category, processing_status, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, NOW())
                """, (document_id, file.filename, content, len(content), category, 'processing'))
                cursor.connection.commit()
        except Exception as e:
            logger.error(f"❌ [UPLOAD] Database error: {e}")
            raise HTTPException(status_code=500, detail="Database error")
        
        # Запускаем асинхронную обработку документа
        asyncio.create_task(process_normative_document_async(document_id, content, file.filename, category))
        
        return {
            "status": "success",
            "document_id": document_id,
            "filename": file.filename,
            "message": f"Document uploaded successfully. Processing started in background."
        }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [UPLOAD] Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_normative_document_async(document_id: int, content: bytes, filename: str, category: str):
    """Асинхронная обработка нормативного документа"""
    try:
        logger.info(f"🔄 [ASYNC_PROCESS] Starting normative document processing for {document_id}")
        
        # Получаем RAG сервис
        rag_service_instance = get_rag_service()
        
        # Извлекаем текст из файла
        if filename.lower().endswith('.txt'):
            text_content = content.decode('utf-8', errors='ignore')
        elif filename.lower().endswith('.pdf'):
            # Простое извлечение текста из PDF (упрощенная версия)
            text_content = f"Содержимое PDF документа {filename}"
        else:
            text_content = f"Содержимое документа {filename}"
        
        # Создаем чанки
        chunks = create_document_chunks(text_content, document_id, filename)
        
        # Индексируем чанки
        success = rag_service_instance.index_document_chunks(document_id, chunks)
        
        if success:
            # Обновляем статус на "completed"
            with rag_service_instance.db_manager.get_cursor() as cursor:
                cursor.execute("""
                    UPDATE uploaded_documents 
                    SET processing_status = 'completed'
                    WHERE id = %s
                """, (document_id,))
                cursor.connection.commit()
            
            logger.info(f"✅ [ASYNC_PROCESS] Document {document_id} processed successfully")
        else:
            # Обновляем статус на "error"
            with rag_service_instance.db_manager.get_cursor() as cursor:
                cursor.execute("""
                    UPDATE uploaded_documents 
                    SET processing_status = 'error'
                    WHERE id = %s
                """, (document_id,))
                cursor.connection.commit()
            
            logger.error(f"❌ [ASYNC_PROCESS] Document {document_id} processing failed")
            
    except Exception as e:
        logger.error(f"❌ [ASYNC_PROCESS] Async processing failed for document {document_id}: {e}")
        # Обновляем статус на "error"
        try:
            rag_service_instance = get_rag_service()
            with rag_service_instance.db_manager.get_cursor() as cursor:
                cursor.execute("""
                    UPDATE uploaded_documents 
                    SET processing_status = 'error'
                    WHERE id = %s
                """, (document_id,))
                cursor.connection.commit()
        except Exception:
            pass

def create_document_chunks(text_content: str, document_id: int, filename: str) -> List[Dict[str, Any]]:
    """Создание чанков из текста документа"""
    chunks = []
    
    # Простое разбиение на чанки по абзацам
    paragraphs = text_content.split('\n\n')
    
    for i, paragraph in enumerate(paragraphs):
        if paragraph.strip():
            chunk = {
                'id': f"doc_{document_id}_chunk_{i}",
                'document_id': document_id,
                'content': paragraph.strip(),
                'page': 1,  # Упрощенная версия
                'section_title': '',
                'section': '',
                'document_title': filename,
                'category': 'normative',
                'chunk_type': 'paragraph'
            }
            chunks.append(chunk)
    
    return chunks

# ============================================================================
# API эндпоинты для поиска
# ============================================================================

@app.post("/search")
async def search_norms(
    query: str = Form(...),
    k: int = Form(8),
    document_filter: Optional[str] = Form(None),
    chapter_filter: Optional[str] = Form(None),
    chunk_type_filter: Optional[str] = Form(None)
):
    """Гибридный поиск по нормативным документам"""
    start_time = datetime.now()
    logger.info(f"🔍 [SEARCH_NORM] Performing hybrid search for query: '{query}' with k={k}")
    logger.info(f"🔍 [SEARCH_NORM] Filters: document={document_filter}, chapter={chapter_filter}, chunk_type={chunk_type_filter}")
    
    try:
        # Получаем RAG сервис
        rag_service_instance = get_rag_service()
        
        # Логируем запрос к модели эмбеддингов
        model_logger.info(f"🤖 [EMBEDDING_REQUEST] Generating embeddings for query: '{query[:100]}...'")
        
        results = rag_service_instance.hybrid_search(
            query=query,
            k=k,
            document_filter=document_filter,
            chapter_filter=chapter_filter,
            chunk_type_filter=chunk_type_filter
        )
        
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"✅ [SEARCH_NORM] Hybrid search completed in {execution_time:.2f}s. Found {len(results)} results.")
        
        # Логируем результаты поиска
        if results:
            top_result = results[0]
            model_logger.info(f"📊 [SEARCH_RESULTS] Top result: {top_result.get('document_title', 'Unknown')} - Score: {top_result.get('score', 0):.3f}")
            model_logger.debug(f"📊 [SEARCH_RESULTS] Top result content preview: {top_result.get('content', '')[:200]}...")
        
        return {
            "query": query,
            "results_count": len(results),
            "execution_time": execution_time,
            "results": results
        }
        
    except Exception as e:
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.error(f"❌ [SEARCH_NORM] Search error after {execution_time:.2f}s: {type(e).__name__}: {str(e)}")
        model_logger.error(f"❌ [EMBEDDING_ERROR] Failed to process query: '{query[:100]}...' - {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# API эндпоинты для консультации НТД
# ============================================================================

@app.post("/ntd-consultation/chat")
async def ntd_consultation_chat_endpoint(request: NTDConsultationRequest):
    """Обработка запроса консультации НТД"""
    return ntd_consultation_chat(request.message, request.user_id)

@app.get("/ntd-consultation/stats")
async def ntd_consultation_stats_endpoint():
    """Получение статистики консультаций НТД"""
    return ntd_consultation_stats()

@app.delete("/ntd-consultation/cache")
async def clear_consultation_cache_endpoint():
    """Очистить кэш консультаций НТД"""
    return clear_consultation_cache()

@app.get("/ntd-consultation/cache/stats")
async def get_consultation_cache_stats_endpoint():
    """Получить статистику кэша консультаций НТД"""
    try:
        result = await get_consultation_cache_stats()
        return {
            "status": "success",
            "cache_stats": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Системные эндпоинты
# ============================================================================

@app.get("/health")
async def health_endpoint():
    """Проверка здоровья сервиса"""
    return health_check()

@app.get("/metrics")
async def metrics_endpoint():
    """Получение метрик Prometheus"""
    return get_metrics()

# ============================================================================
# Корневой эндпоинт
# ============================================================================

@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "service": "RAG Service",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "documents": "/documents",
            "search": "/search",
            "stats": "/stats",
            "health": "/health",
            "metrics": "/metrics",
            "ntd_consultation": "/ntd-consultation/chat"
        }
    }

# ============================================================================
# Обработка ошибок
# ============================================================================

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    return {"error": "Endpoint not found", "path": request.url.path}

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    return {"error": "Internal server error", "detail": str(exc)}

# ============================================================================
# Запуск приложения
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8003,
        reload=True,
        log_level="info"
    )
