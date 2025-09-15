from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn
import hashlib
import time
import asyncio
import json
import logging
import os
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

# Получаем URL Ollama из переменной окружения
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434")

# Импорт Ollama RAG сервиса (новая модульная архитектура)
from services.ollama_rag_service_refactored import OllamaRAGService
from services.reranker_service import BGERerankerService

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

# Модели Pydantic для чата
class ChatRequest(BaseModel):
    message: str
    model: str = "llama3.1:8b"
    history: Optional[List[Dict[str, str]]] = None
    max_tokens: Optional[int] = None
    turbo_mode: bool = False  # Турбо режим рассуждения
    reasoning_depth: str = "balanced"  # Глубина рассуждения: "fast", "balanced", "deep"

class ChatResponse(BaseModel):
    status: str
    response: str
    model: str
    timestamp: str
    tokens_used: Optional[int] = None
    generation_time_ms: Optional[float] = None
    turbo_mode: bool = False
    reasoning_depth: str = "balanced"
    reasoning_steps: Optional[int] = None  # Количество шагов рассуждения

class EmbeddingRequest(BaseModel):
    text: str

class EmbeddingResponse(BaseModel):
    status: str
    embedding: List[float]
    text_length: int
    timestamp: str

# Создание FastAPI приложения
app = FastAPI(
    title="Ollama RAG Service",
    description="RAG сервис для работы с нормативными документами с использованием Ollama BGE-M3",
    version="2.0.0"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Инициализация Ollama RAG сервиса (ленивая загрузка)
ollama_rag_service = None

# Глобальная переменная для хранения статуса асинхронной реиндексации
async_reindex_status = {}

def get_ollama_rag_service():
    """Ленивая инициализация Ollama RAG сервиса"""
    global ollama_rag_service
    if ollama_rag_service is None:
        logger.info(f"🔄 [RAG_SERVICE] Creating new OllamaRAGService instance")
        ollama_rag_service = OllamaRAGService()
        logger.info(f"✅ [RAG_SERVICE] OllamaRAGService instance created: {id(ollama_rag_service)}")
    else:
        logger.info(f"♻️ [RAG_SERVICE] Reusing existing OllamaRAGService instance: {id(ollama_rag_service)}")
    return ollama_rag_service

# ============================================================================
# API эндпоинты для документов
# ============================================================================

@app.get("/documents")
async def documents_endpoint():
    """Получение списка нормативных документов"""
    return get_ollama_rag_service().get_documents()

@app.get("/stats")
async def stats_endpoint():
    """Получение детальной статистики сервиса"""
    try:
        rag_service = get_ollama_rag_service()
        stats = rag_service.get_stats()
        return stats
    except Exception as e:
        logger.error(f"❌ [STATS] Error getting stats: {e}")
        return {
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/documents/stats")
async def documents_stats_endpoint():
    """Получение статистики нормативных документов для фронтенда"""
    try:
        rag_service = get_ollama_rag_service()
        stats = rag_service.get_stats()
        
        # Формируем статистику в формате для фронтенда
        return {
            "tokens": stats.get('postgresql', {}).get('total_tokens', 0),
            "chunks": stats.get('postgresql', {}).get('total_chunks', 0),
            "vectors": stats.get('qdrant', {}).get('vectors_count', 0),
            "documents": stats.get('postgresql', {}).get('total_documents', 0),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ [DOCUMENTS_STATS] Error getting documents stats: {e}")
        return {
            "tokens": 0,
            "chunks": 0,
            "vectors": 0,
            "documents": 0,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/documents/{document_id}/chunks")
async def document_chunks_endpoint(document_id: int):
    """Получение чанков документа"""
    return get_ollama_rag_service().get_document_chunks(document_id)

@app.delete("/documents/{document_id}")
async def delete_document_endpoint(document_id: int):
    """Удаление документа"""
    try:
        success = get_ollama_rag_service().delete_document(document_id)
        if success:
            return {"status": "success", "message": f"Document {document_id} deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail=f"Document {document_id} not found")
    except Exception as e:
        logger.error(f"❌ [DELETE_DOCUMENT] Error deleting document {document_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reindex")
async def reindex_documents_endpoint():
    """Полная реиндексация всех документов с очисткой Qdrant"""
    try:
        logger.info("🔄 [REINDEX] Starting full document reindexing with Qdrant cleanup...")
        
        rag_service = get_ollama_rag_service()
        
        # 1. Очищаем Qdrant коллекцию
        logger.info("🗑️ [REINDEX] Clearing Qdrant collection...")
        try:
            success = rag_service.qdrant_service.clear_collection()
            if success:
                logger.info("✅ [REINDEX] Qdrant collection cleared")
            else:
                logger.warning("⚠️ [REINDEX] Failed to clear Qdrant collection")
        except Exception as e:
            logger.warning(f"⚠️ [REINDEX] Error clearing Qdrant collection: {e}")
        
        # 2. Убеждаемся, что коллекция существует
        logger.info("🆕 [REINDEX] Ensuring Qdrant collection exists...")
        try:
            rag_service.qdrant_service._ensure_collection_exists()
            logger.info("✅ [REINDEX] Qdrant collection ensured")
        except Exception as e:
            logger.error(f"❌ [REINDEX] Error ensuring Qdrant collection: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to ensure Qdrant collection: {e}")
        
        # 3. Получаем все документы из базы данных
        documents = rag_service.db_manager.execute_read_query("""
            SELECT ud.id, ud.original_filename as document_title, ud.category
            FROM uploaded_documents ud
            WHERE ud.processing_status = 'completed'
            ORDER BY ud.upload_date DESC
        """)
        
        if not documents:
            return {
                "status": "success",
                "message": "No documents to reindex",
                "documents_processed": 0,
                "timestamp": datetime.now().isoformat()
            }
        
        logger.info(f"🔄 [REINDEX] Found {len(documents)} documents to reindex")
        
        total_processed = 0
        total_chunks = 0
        
        # 4. Индексируем каждый документ
        for document in documents:
            try:
                document_id = document['id']
                document_title = document['document_title']
                
                logger.info(f"📝 [REINDEX] Processing document {document_id}: {document_title}")
                
                # Получаем чанки документа
                chunks = rag_service.get_document_chunks(document_id)
                
                if chunks:
                    # Добавляем информацию о документе к каждому чанку (убираем расширение)
                    import re
                    document_title_clean = re.sub(r'\.(pdf|txt|doc|docx)$', '', document_title, flags=re.IGNORECASE)
                    for chunk in chunks:
                        chunk['document_title'] = document_title_clean
                    
                    # Индексируем чанки
                    success = rag_service.index_document_chunks(document_id, chunks)
                    
                    if success:
                        total_processed += 1
                        total_chunks += len(chunks)
                        logger.info(f"✅ [REINDEX] Successfully indexed document {document_id} with {len(chunks)} chunks")
                    else:
                        logger.error(f"❌ [REINDEX] Failed to index document {document_id}")
                else:
                    logger.warning(f"⚠️ [REINDEX] No chunks found for document {document_id}")
                    
            except Exception as e:
                logger.error(f"❌ [REINDEX] Error processing document {document.get('id', 'unknown')}: {e}")
                continue
        
        logger.info(f"✅ [REINDEX] Full reindexing completed. Processed {total_processed} documents with {total_chunks} chunks")
        
        return {
            "status": "success",
            "message": "Full document reindexing completed",
            "documents_processed": total_processed,
            "total_chunks": total_chunks,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ [REINDEX] Error during full reindexing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/documents/{document_id}/indexes")
async def delete_document_indexes_endpoint(document_id: int):
    """Удаление индексов документа"""
    try:
        success = get_ollama_rag_service().delete_document_indexes(document_id)
        
        if success:
            return {
                "status": "success",
                "message": f"Indexes for document {document_id} deleted successfully",
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=404, detail=f"Document {document_id} not found")
            
    except Exception as e:
        logger.error(f"❌ [DELETE_INDEXES] Error deleting indexes for document {document_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reindex/async")
async def async_reindex_documents_endpoint():
    """Асинхронная реиндексация всех документов с очисткой Qdrant"""
    try:
        logger.info("🔄 [ASYNC_REINDEX] Starting async document reindexing...")
        
        # Создаем уникальный ID задачи
        import uuid
        task_id = str(uuid.uuid4())
        
        # Запускаем реиндексацию в фоновом режиме
        import asyncio
        asyncio.create_task(perform_async_reindex_with_status(task_id))
        
        return {
            "status": "started",
            "message": "Async reindexing started",
            "task_id": task_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ [ASYNC_REINDEX] Error starting async reindexing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/reindex/status/{task_id}")
async def get_reindex_status_endpoint(task_id: str):
    """Получение статуса асинхронной реиндексации"""
    try:
        logger.info(f"📊 [REINDEX_STATUS] Getting status for task {task_id}")
        
        # Проверяем статус задачи
        if task_id in async_reindex_status:
            return async_reindex_status[task_id]
        else:
            return {
                "status": "not_found",
                "message": "Task not found",
                "timestamp": datetime.now().isoformat()
            }
        
    except Exception as e:
        logger.error(f"❌ [REINDEX_STATUS] Error getting status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def perform_async_reindex_with_status(task_id: str):
    """Выполнение асинхронной реиндексации с обновлением статуса"""
    try:
        logger.info(f"🔄 [ASYNC_REINDEX] Performing async reindexing for task {task_id}...")
        
        # Обновляем статус на "running"
        async_reindex_status[task_id] = {
            "status": "running",
            "message": "Reindexing in progress...",
            "progress": 0,
            "total_documents": 0,
            "reindexed_count": 0,
            "timestamp": datetime.now().isoformat()
        }
        
        rag_service = get_ollama_rag_service()
        
        # 1. Очищаем Qdrant коллекцию
        logger.info("🗑️ [ASYNC_REINDEX] Clearing Qdrant collection...")
        try:
            success = rag_service.qdrant_service.clear_collection()
            if success:
                logger.info("✅ [ASYNC_REINDEX] Qdrant collection cleared")
            else:
                logger.warning("⚠️ [ASYNC_REINDEX] Failed to clear Qdrant collection")
        except Exception as e:
            logger.warning(f"⚠️ [ASYNC_REINDEX] Error clearing Qdrant collection: {e}")
        
        # 2. Убеждаемся, что коллекция существует
        logger.info("🆕 [ASYNC_REINDEX] Ensuring Qdrant collection exists...")
        try:
            rag_service.qdrant_service._ensure_collection_exists()
            logger.info("✅ [ASYNC_REINDEX] Qdrant collection ensured")
        except Exception as e:
            logger.error(f"❌ [ASYNC_REINDEX] Error ensuring Qdrant collection: {e}")
            async_reindex_status[task_id] = {
                "status": "error",
                "message": f"Failed to ensure Qdrant collection: {e}",
                "timestamp": datetime.now().isoformat()
            }
            return
        
        # 3. Получаем все документы из базы данных
        documents = rag_service.db_manager.execute_read_query("""
            SELECT ud.id, ud.original_filename as document_title, ud.category
            FROM uploaded_documents ud
            WHERE ud.processing_status = 'completed'
            ORDER BY ud.upload_date DESC
        """)
        
        if not documents:
            logger.info("ℹ️ [ASYNC_REINDEX] No documents to reindex")
            async_reindex_status[task_id] = {
                "status": "completed",
                "message": "No documents to reindex",
                "progress": 100,
                "total_documents": 0,
                "reindexed_count": 0,
                "timestamp": datetime.now().isoformat()
            }
            return
        
        logger.info(f"🔄 [ASYNC_REINDEX] Found {len(documents)} documents to reindex")
        
        # Обновляем статус с общим количеством документов
        async_reindex_status[task_id] = {
            "status": "running",
            "message": f"Reindexing {len(documents)} documents...",
            "progress": 0,
            "total_documents": len(documents),
            "reindexed_count": 0,
            "timestamp": datetime.now().isoformat()
        }
        
        total_processed = 0
        total_chunks = 0
        
        # 4. Индексируем каждый документ
        for i, document in enumerate(documents):
            try:
                document_id = document['id']
                document_title = document['document_title']
                
                logger.info(f"📝 [ASYNC_REINDEX] Processing document {document_id}: {document_title} ({i+1}/{len(documents)})")
                
                # Обновляем статус прогресса
                progress = int((i / len(documents)) * 100)
                async_reindex_status[task_id] = {
                    "status": "running",
                    "message": f"Processing document {i+1} of {len(documents)}: {document_title}",
                    "progress": progress,
                    "total_documents": len(documents),
                    "reindexed_count": total_processed,
                    "current_document": document_title,
                    "timestamp": datetime.now().isoformat()
                }
                
                # Получаем чанки документа
                chunks = rag_service.get_document_chunks(document_id)
                
                if chunks:
                    # Добавляем информацию о документе к каждому чанку (убираем расширение)
                    import re
                    document_title_clean = re.sub(r'\.(pdf|txt|doc|docx)$', '', document_title, flags=re.IGNORECASE)
                    for chunk in chunks:
                        chunk['document_title'] = document_title_clean
                    
                    # Индексируем чанки
                    success = rag_service.index_document_chunks(document_id, chunks)
                    
                    if success:
                        total_processed += 1
                        total_chunks += len(chunks)
                        logger.info(f"✅ [ASYNC_REINDEX] Successfully indexed document {document_id} with {len(chunks)} chunks")
                    else:
                        logger.error(f"❌ [ASYNC_REINDEX] Failed to index document {document_id}")
                else:
                    logger.warning(f"⚠️ [ASYNC_REINDEX] No chunks found for document {document_id}")
                    
            except Exception as e:
                logger.error(f"❌ [ASYNC_REINDEX] Error processing document {document.get('id', 'unknown')}: {e}")
                continue
        
        # Обновляем финальный статус
        async_reindex_status[task_id] = {
            "status": "completed",
            "message": f"Reindexing completed. {total_processed} documents reindexed with {total_chunks} chunks",
            "progress": 100,
            "total_documents": len(documents),
            "reindexed_count": total_processed,
            "total_chunks": total_chunks,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"✅ [ASYNC_REINDEX] Async reindexing completed. Processed {total_processed} documents with {total_chunks} chunks")
        
    except Exception as e:
        logger.error(f"❌ [ASYNC_REINDEX] Error during async reindexing: {e}")
        async_reindex_status[task_id] = {
            "status": "error",
            "message": f"Reindexing failed: {e}",
            "timestamp": datetime.now().isoformat()
        }

async def perform_async_reindex():
    """Выполнение асинхронной реиндексации (старая версия для совместимости)"""
    try:
        logger.info("🔄 [ASYNC_REINDEX] Performing async reindexing...")
        
        rag_service = get_ollama_rag_service()
        
        # 1. Очищаем Qdrant коллекцию
        logger.info("🗑️ [ASYNC_REINDEX] Clearing Qdrant collection...")
        try:
            success = rag_service.qdrant_service.clear_collection()
            if success:
                logger.info("✅ [ASYNC_REINDEX] Qdrant collection cleared")
            else:
                logger.warning("⚠️ [ASYNC_REINDEX] Failed to clear Qdrant collection")
        except Exception as e:
            logger.warning(f"⚠️ [ASYNC_REINDEX] Error clearing Qdrant collection: {e}")
        
        # 2. Убеждаемся, что коллекция существует
        logger.info("🆕 [ASYNC_REINDEX] Ensuring Qdrant collection exists...")
        try:
            rag_service.qdrant_service._ensure_collection_exists()
            logger.info("✅ [ASYNC_REINDEX] Qdrant collection ensured")
        except Exception as e:
            logger.error(f"❌ [ASYNC_REINDEX] Error ensuring Qdrant collection: {e}")
            return
        
        # 3. Получаем все документы из базы данных
        documents = rag_service.db_manager.execute_read_query("""
            SELECT ud.id, ud.original_filename as document_title, ud.category
            FROM uploaded_documents ud
            WHERE ud.processing_status = 'completed'
            ORDER BY ud.upload_date DESC
        """)
        
        if not documents:
            logger.info("ℹ️ [ASYNC_REINDEX] No documents to reindex")
            return
        
        logger.info(f"🔄 [ASYNC_REINDEX] Found {len(documents)} documents to reindex")
        
        total_processed = 0
        total_chunks = 0
        
        # 4. Индексируем каждый документ
        for document in documents:
            try:
                document_id = document['id']
                document_title = document['document_title']
                
                logger.info(f"📝 [ASYNC_REINDEX] Processing document {document_id}: {document_title}")
                
                # Получаем чанки документа
                chunks = rag_service.get_document_chunks(document_id)
                
                if chunks:
                    # Добавляем информацию о документе к каждому чанку (убираем расширение)
                    import re
                    document_title_clean = re.sub(r'\.(pdf|txt|doc|docx)$', '', document_title, flags=re.IGNORECASE)
                    for chunk in chunks:
                        chunk['document_title'] = document_title_clean
                    
                    # Индексируем чанки
                    success = rag_service.index_document_chunks(document_id, chunks)
                    
                    if success:
                        total_processed += 1
                        total_chunks += len(chunks)
                        logger.info(f"✅ [ASYNC_REINDEX] Successfully indexed document {document_id} with {len(chunks)} chunks")
                    else:
                        logger.error(f"❌ [ASYNC_REINDEX] Failed to index document {document_id}")
                else:
                    logger.warning(f"⚠️ [ASYNC_REINDEX] No chunks found for document {document_id}")
                    
            except Exception as e:
                logger.error(f"❌ [ASYNC_REINDEX] Error processing document {document.get('id', 'unknown')}: {e}")
                continue
        
        logger.info(f"✅ [ASYNC_REINDEX] Async reindexing completed. Processed {total_processed} documents with {total_chunks} chunks")
        
    except Exception as e:
        logger.error(f"❌ [ASYNC_REINDEX] Error during async reindexing: {e}")

@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    category: str = Form("other"),
    description: str = Form("")
):
    """Загрузка нормативного документа"""
    logger.info(f"📤 [UPLOAD] Uploading normative document: {file.filename}")
    try:
        # Проверяем тип файла
        if not file.filename.lower().endswith(('.pdf', '.docx', '.txt')):
            raise HTTPException(status_code=400, detail="Unsupported file type. Only PDF, DOCX, and TXT files are allowed.")
        
        # Читаем содержимое файла
        content = await file.read()
        file_size = len(content)
        
        # Проверяем размер файла (максимум 50 MB)
        max_file_size = 50 * 1024 * 1024  # 50 MB
        if file_size > max_file_size:
            raise HTTPException(
                status_code=413, 
                detail=f"File too large. Maximum size is {max_file_size // (1024*1024)} MB"
            )
        
        # Генерируем хеш документа для дедупликации
        document_hash = hashlib.sha256(content).hexdigest()
        
        # Генерируем уникальный ID документа
        document_id = int(time.time() * 1000) % 100000000  # 8-значное число
        
        # Сохраняем документ в базу данных
        try:
            rag_service = get_ollama_rag_service()
            saved_document_id = rag_service.save_document_to_db(
                document_id=document_id,
                filename=file.filename,
                original_filename=file.filename,
                file_type=file.filename.split('.')[-1].lower(),
                file_size=file_size,
                document_hash=document_hash,
                category=category,
                document_type='normative'
            )
            
            logger.info(f"✅ [UPLOAD] Document saved to database with ID: {saved_document_id}")
            
            # Запускаем асинхронную обработку документа
            logger.info(f"🔄 [UPLOAD] Starting document processing for {saved_document_id}")
            asyncio.create_task(process_normative_document_async(saved_document_id, content, file.filename))
            
            return {
                "status": "success",
                "document_id": saved_document_id,
                "filename": file.filename,
                "file_size": file_size,
                "message": f"Document uploaded successfully and processing started"
            }
            
        except Exception as e:
            logger.error(f"❌ [UPLOAD] Database error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [UPLOAD] Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_normative_document_async(document_id: int, content: bytes, filename: str):
    """Асинхронная обработка нормативного документа"""
    logger.info(f"🔄 [PROCESS] Starting async processing for document {document_id}")
    try:
        rag_service = get_ollama_rag_service()
        
        # Обновляем статус на "processing"
        rag_service.update_document_status(document_id, "processing")
        
        # Обрабатываем документ
        success = await rag_service.process_document_async(document_id, content, filename)
        
        if success:
            rag_service.update_document_status(document_id, "completed")
            logger.info(f"✅ [PROCESS] Document {document_id} processed successfully")
        else:
            rag_service.update_document_status(document_id, "failed", "Processing failed")
            logger.error(f"❌ [PROCESS] Document {document_id} processing failed")
            
    except Exception as e:
        logger.error(f"❌ [PROCESS] Error processing document {document_id}: {e}")
        try:
            rag_service = get_ollama_rag_service()
            rag_service.update_document_status(document_id, "failed", str(e))
        except:
            pass

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
        # Получаем Ollama RAG сервис
        rag_service = get_ollama_rag_service()
        
        # Логируем запрос к модели эмбеддингов
        model_logger.info(f"🤖 [EMBEDDING_REQUEST] Generating embeddings for query: '{query[:100]}...'")
        
        results = rag_service.hybrid_search(
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
    try:
        rag_service = get_ollama_rag_service()
        result = rag_service.get_ntd_consultation(request.message, request.user_id)
        return result
    except Exception as e:
        logger.error(f"❌ [NTD_CONSULTATION] Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/structured-context")
async def get_structured_context_endpoint(request: dict):
    """Получение структурированного контекста для запроса"""
    try:
        logger.info("🏗️ [STRUCTURED_CONTEXT] Structured context request received")
        rag_service = get_ollama_rag_service()
        
        # Извлекаем параметры из запроса
        message = request.get("message", "")
        k = request.get("k", 8)
        document_filter = request.get("document_filter")
        chapter_filter = request.get("chapter_filter")
        chunk_type_filter = request.get("chunk_type_filter")
        use_reranker = request.get("use_reranker", True)
        fast_mode = request.get("fast_mode", False)
        use_mmr = request.get("use_mmr", True)
        use_intent_classification = request.get("use_intent_classification", True)
        
        # Проверяем, что это OllamaRAGService
        if hasattr(rag_service, 'get_structured_context'):
            response = rag_service.get_structured_context(
                query=message,
                k=k,
                document_filter=document_filter,
                chapter_filter=chapter_filter,
                chunk_type_filter=chunk_type_filter,
                use_reranker=use_reranker,
                fast_mode=fast_mode,
                use_mmr=use_mmr,
                use_intent_classification=use_intent_classification
            )
        else:
            # Fallback для старого RAG сервиса
            search_results = rag_service.hybrid_search(message, k=k)
            response = {
                "query": message,
                "timestamp": datetime.now().isoformat(),
                "context": [
                    {
                        "doc": result.get('code', ''),
                        "section": result.get('section', ''),
                        "page": result.get('page', 1),
                        "snippet": result.get('content', '')[:200] + '...' if len(result.get('content', '')) > 200 else result.get('content', ''),
                        "why": "fallback",
                        "score": result.get('score', 0.0),
                        "document_title": result.get('document_title', ''),
                        "section_title": result.get('section_title', ''),
                        "chunk_type": result.get('chunk_type', ''),
                        "metadata": result.get('metadata', {})
                    }
                    for result in search_results
                ],
                "meta_summary": {
                    "query_type": "fallback",
                    "documents_found": len(search_results),
                    "sections_covered": len(set(result.get('section', '') for result in search_results)),
                    "avg_relevance": sum(result.get('score', 0) for result in search_results) / len(search_results) if search_results else 0,
                    "coverage_quality": "fallback",
                    "key_documents": list(set(result.get('code', '') for result in search_results[:3] if result.get('code'))),
                    "key_sections": list(set(result.get('section', '') for result in search_results[:3] if result.get('section')))
                },
                "total_candidates": len(search_results),
                "avg_score": sum(result.get('score', 0) for result in search_results) / len(search_results) if search_results else 0
            }
        
        logger.info(f"✅ [STRUCTURED_CONTEXT] Structured context generated successfully")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [STRUCTURED_CONTEXT] Context generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ntd-consultation/stats")
async def ntd_consultation_stats_endpoint():
    """Получение статистики консультаций НТД"""
    try:
        rag_service = get_ollama_rag_service()
        stats = rag_service.get_stats()
        return {
            "status": "success",
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ [NTD_CONSULTATION_STATS] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/ntd-consultation/cache")
async def clear_consultation_cache_endpoint():
    """Очистить кэш консультаций НТД"""
    return {
        "status": "success",
        "message": "Cache cleared successfully",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/ntd-consultation/cache/stats")
async def get_consultation_cache_stats_endpoint():
    """Получить статистику кэша консультаций НТД"""
    return {
        "status": "success",
        "cache_stats": {
            "cache_type": "No caching implemented",
            "cache_size": 0,
            "cache_hits": 0,
            "cache_misses": 0
        },
        "timestamp": datetime.now().isoformat()
    }

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """Чат с ИИ через Ollama с поддержкой турбо режима рассуждения"""
    try:
        logger.info(f"💬 [CHAT] Processing chat request with model: {request.model}, turbo_mode: {request.turbo_mode}, reasoning_depth: {request.reasoning_depth}")
        
        # Импортируем сервис турбо рассуждения
        from services.turbo_reasoning_service import TurboReasoningService
        
        # Создаем сервис турбо рассуждения
        turbo_service = TurboReasoningService()
        
        # Генерируем ответ с выбранным режимом
        result = turbo_service.generate_response(
            message=request.message,
            history=request.history,
            turbo_mode=request.turbo_mode,
            reasoning_depth=request.reasoning_depth,
            max_tokens=request.max_tokens
        )
        
        return ChatResponse(
            status="success",
            response=result["response"],
            model=result["model"],
            timestamp=datetime.now().isoformat(),
            tokens_used=result["tokens_used"],
            generation_time_ms=result["generation_time_ms"],
            turbo_mode=result["turbo_mode"],
            reasoning_depth=result["reasoning_depth"],
            reasoning_steps=result["reasoning_steps"]
        )
            
    except Exception as e:
        logger.error(f"❌ [CHAT] Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models")
async def models_endpoint():
    """Получение списка доступных моделей Ollama"""
    try:
        logger.info("🔍 [MODELS] Getting available Ollama models")
        
        import requests
        
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=10)
        
        if response.status_code == 200:
            models_data = response.json()
            models = models_data.get("models", [])
            
            # Фильтруем только модели для чата (исключаем bge-m3)
            chat_models = [
                {
                    "name": model.get("name", ""),
                    "model": model.get("model", ""),
                    "size": model.get("size", 0),
                    "parameter_size": model.get("details", {}).get("parameter_size", ""),
                    "quantization": model.get("details", {}).get("quantization_level", ""),
                    "family": model.get("details", {}).get("family", "")
                }
                for model in models
                if "bge-m3" not in model.get("name", "").lower()
            ]
            
            return {
                "status": "success",
                "models": chat_models,
                "total_count": len(chat_models),
                "ollama_status": "healthy",
                "timestamp": datetime.now().isoformat()
            }
        else:
            logger.error(f"❌ [MODELS] Ollama API error: {response.status_code}")
            raise HTTPException(status_code=500, detail=f"Ollama API error: {response.status_code}")
            
    except Exception as e:
        logger.error(f"❌ [MODELS] Error getting models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/reasoning-modes")
async def reasoning_modes_endpoint():
    """Получение информации о доступных режимах рассуждения"""
    try:
        logger.info("🧠 [REASONING_MODES] Getting available reasoning modes")
        
        from services.turbo_reasoning_service import TurboReasoningService
        
        # Создаем сервис для получения информации о режимах
        turbo_service = TurboReasoningService()
        
        # Получаем режимы рассуждения
        reasoning_modes = turbo_service.get_reasoning_modes()
        
        # Проверяем здоровье сервиса
        service_health = turbo_service.health_check()
        
        return {
            "status": "success",
            "reasoning_modes": reasoning_modes,
            "service_health": "healthy" if service_health else "unhealthy",
            "total_modes": len(reasoning_modes),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ [REASONING_MODES] Error getting reasoning modes: {e}")
        return {
            "status": "error",
            "error": str(e),
            "service_health": "unhealthy",
            "timestamp": datetime.now().isoformat()
        }

@app.get("/hybrid_search_stats")
async def hybrid_search_stats_endpoint():
    """Получение статистики гибридного поиска"""
    try:
        logger.info("📊 [HYBRID_STATS] Getting hybrid search statistics")
        
        rag_service_instance = get_rag_service()
        stats = rag_service_instance.get_hybrid_search_stats()
        
        logger.info("✅ [HYBRID_STATS] Statistics retrieved successfully")
        return stats
        
    except Exception as e:
        logger.error(f"❌ [HYBRID_STATS] Error getting hybrid search stats: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/chat_documents_stats")
async def chat_documents_stats_endpoint():
    """Получение статистики документов чата"""
    try:
        # Получаем статистику коллекции chat_documents из Qdrant
        import requests
        
        qdrant_url = "http://qdrant:6333"
        collection_name = "chat_documents"
        
        try:
            response = requests.get(f"{qdrant_url}/collections/{collection_name}", timeout=10)
            if response.status_code == 200:
                result = response.json()
                return {
                    "total_documents": result['result']['points_count'],
                    "indexed_vectors": result['result']['indexed_vectors_count'],
                    "collection_status": result['result']['status'],
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "total_documents": 0,
                    "indexed_vectors": 0,
                    "collection_status": "not_found",
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            return {
                "total_documents": 0,
                "indexed_vectors": 0,
                "collection_status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"❌ [CHAT_DOCUMENTS_STATS] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/embeddings")
async def create_embedding_endpoint(request: EmbeddingRequest):
    """Создание эмбеддинга для текста"""
    try:
        logger.info(f"🔍 [EMBEDDINGS] Creating embedding for text: '{request.text[:100]}...'")
        
        rag_service = get_ollama_rag_service()
        embedding = rag_service.embedding_service.create_embedding(request.text)
        
        return EmbeddingResponse(
            status="success",
            embedding=embedding,
            text_length=len(request.text),
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"❌ [EMBEDDINGS] Error creating embedding: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/embeddings")
async def create_embedding_get_endpoint(text: str):
    """Создание эмбеддинга для текста (GET запрос)"""
    try:
        logger.info(f"🔍 [EMBEDDINGS] Creating embedding for text: '{text[:100]}...'")
        
        rag_service = get_ollama_rag_service()
        embedding = rag_service.embedding_service.create_embedding(text)
        
        return EmbeddingResponse(
            status="success",
            embedding=embedding,
            text_length=len(text),
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"❌ [EMBEDDINGS] Error creating embedding: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/test-chunking")
async def test_chunking_endpoint():
    """Тестовый эндпоинт для проверки гранулярного чанкования"""
    try:
        logger.info("🧪 [TEST_CHUNKING] Testing granular chunking functionality...")
        
        # Тестовый текст
        test_text = """
        Страница 1 из 2
        
        СП 22.13330.2016 "Основания зданий и сооружений"
        
        Глава 1. Общие положения
        
        1.1. Настоящий свод правил устанавливает требования к проектированию оснований зданий и сооружений.
        
        1.2. Основания должны обеспечивать надежность и долговечность зданий и сооружений.
        
        1.3. При проектировании оснований следует учитывать:
        - инженерно-геологические условия;
        - конструктивные особенности зданий;
        - технологические требования.
        
        Глава 2. Инженерно-геологические изыскания
        
        2.1. Инженерно-геологические изыскания должны выполняться в соответствии с требованиями СП 47.13330.
        
        2.2. Объем изысканий определяется сложностью инженерно-геологических условий.
        
        Страница 2 из 2
        
        Глава 3. Расчет оснований
        
        3.1. Расчет оснований выполняется по предельным состояниям.
        
        3.2. При расчете учитываются:
        - нагрузки от зданий и сооружений;
        - собственный вес грунтов;
        - гидродинамические воздействия.
        
        3.3. Коэффициент надежности по нагрузке принимается не менее 1,2.
        
        Глава 4. Конструктивные решения
        
        4.1. Конструктивные решения оснований должны обеспечивать:
        - равномерность осадок;
        - устойчивость откосов;
        - защиту от подтопления.
        
        4.2. При устройстве фундаментов следует предусматривать:
        - гидроизоляцию;
        - дренаж;
        - вентиляцию подполий.
        
        4.3. Материалы фундаментов должны соответствовать требованиям по прочности и долговечности.
        """
        
        logger.info(f"📄 [TEST_CHUNKING] Test text length: {len(test_text)} characters")
        
        # Создаем чанки с помощью новой логики
        rag_service = get_ollama_rag_service()
        
        # Тестируем разбиение на предложения
        try:
            from config.chunking_config import get_chunking_config
            config = get_chunking_config('default')
            logger.info(f"🔧 [TEST_CHUNKING] Using config: {config}")
            
            sentences = rag_service._split_into_sentences(test_text, config)
            logger.info(f"🔤 [TEST_CHUNKING] Split into {len(sentences)} sentences")
            
            if sentences:
                logger.info(f"📝 [TEST_CHUNKING] First sentence: {sentences[0][:100]}...")
                logger.info(f"📝 [TEST_CHUNKING] Last sentence: {sentences[-1][:100]}...")
            
        except Exception as e:
            logger.error(f"❌ [TEST_CHUNKING] Error in sentence splitting: {e}")
            sentences = []
        
        # Тестируем создание чанков
        try:
            chunks = rag_service._split_page_into_chunks(test_text, 1000)
            logger.info(f"📝 [TEST_CHUNKING] Created {len(chunks)} chunks")
            
            if chunks:
                logger.info(f"📝 [TEST_CHUNKING] First chunk: {chunks[0][:100]}...")
                logger.info(f"📝 [TEST_CHUNKING] Last chunk: {chunks[-1][:100]}...")
            
        except Exception as e:
            logger.error(f"❌ [TEST_CHUNKING] Error in chunk creation: {e}")
            chunks = []
        
        # Анализируем результаты
        chunk_analysis = []
        for i, chunk in enumerate(chunks):
            try:
                # Оцениваем количество токенов
                estimated_tokens = rag_service._estimate_tokens(chunk, {'tokens_per_char': 4})
                
                chunk_info = {
                    'chunk_id': i + 1,
                    'content_length': len(chunk),
                    'estimated_tokens': estimated_tokens,
                    'content_preview': chunk[:100] + '...' if len(chunk) > 100 else chunk,
                    'sentences_count': len(chunk.split('.')),
                    'has_headers': any(word in chunk.lower() for word in ['глава', 'раздел', 'часть', 'пункт'])
                }
                chunk_analysis.append(chunk_info)
            except Exception as e:
                logger.error(f"❌ [TEST_CHUNKING] Error analyzing chunk {i}: {e}")
        
        logger.info(f"✅ [TEST_CHUNKING] Created {len(chunks)} chunks successfully")
        
        return {
            "status": "success",
            "message": "Granular chunking test completed",
            "total_chunks": len(chunks),
            "chunks": chunk_analysis,
            "test_text_length": len(test_text),
            "sentences_count": len(sentences),
            "config_used": config if 'config' in locals() else None,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ [TEST_CHUNKING] Error in chunking test: {e}")
        import traceback
        logger.error(f"❌ [TEST_CHUNKING] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/test-reranker")
async def test_reranker_endpoint():
    """Тестовый эндпоинт для проверки реранкинга"""
    try:
        logger.info("🔄 [TEST_RERANKER] Testing reranker functionality...")
        
        # Получаем RAG сервис
        rag_service = get_ollama_rag_service()
        
        # Тестовый запрос
        test_query = "Требования к проектированию оснований зданий"
        
        logger.info(f"🔍 [TEST_RERANKER] Test query: '{test_query}'")
        
        # Выполняем поиск с реранкингом
        try:
            results_with_reranker = rag_service.hybrid_search(
                query=test_query,
                k=8,
                use_reranker=True,
                fast_mode=False  # Отключаем быстрый режим для тестирования
            )
            
            logger.info(f"✅ [TEST_RERANKER] Search with reranker completed, found {len(results_with_reranker)} results")
            
            # Анализируем результаты
            reranked_analysis = []
            for i, result in enumerate(results_with_reranker):
                result_info = {
                    'rank': i + 1,
                    'document_title': result.get('document_title', 'Unknown'),
                    'rerank_score': result.get('rerank_score', 'N/A'),
                    'vector_score': result.get('score', 'N/A'),
                    'content_preview': result.get('content', '')[:100] + '...' if result.get('content') else 'No content'
                }
                reranked_analysis.append(result_info)
            
            return {
                "status": "success",
                "message": "Reranker test completed",
                "query": test_query,
                "total_results": len(results_with_reranker),
                "results": reranked_analysis,
                "reranker_enabled": True,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ [TEST_RERANKER] Error during search with reranker: {e}")
            return {
                "status": "error",
                "message": f"Error during search: {str(e)}",
                "query": test_query,
                "reranker_enabled": False,
                "timestamp": datetime.now().isoformat()
            }
        
    except Exception as e:
        logger.error(f"❌ [TEST_RERANKER] Error in reranker test: {e}")
        import traceback
        logger.error(f"❌ [TEST_RERANKER] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/test-turbo-reasoning")
async def test_turbo_reasoning_endpoint():
    """Тестовый эндпоинт для проверки турбо режима рассуждения"""
    try:
        logger.info("🚀 [TEST_TURBO_REASONING] Testing turbo reasoning functionality...")
        
        # Получаем сервис турбо рассуждения
        from services.turbo_reasoning_service import TurboReasoningService
        
        turbo_service = TurboReasoningService()
        
        # Тестовое сообщение
        test_message = "Объясни, как работает искусственный интеллект в простых терминах"
        
        # Тестируем разные режимы
        test_results = {}
        
        # 1. Турбо режим
        try:
            logger.info("🧪 [TEST_TURBO_REASONING] Testing turbo mode...")
            turbo_result = turbo_service.generate_response(
                message=test_message,
                turbo_mode=True
            )
            test_results["turbo"] = {
                "response_preview": turbo_result["response"][:200] + "..." if len(turbo_result["response"]) > 200 else turbo_result["response"],
                "generation_time_ms": turbo_result["generation_time_ms"],
                "tokens_used": turbo_result["tokens_used"],
                "reasoning_steps": turbo_result["reasoning_steps"]
            }
        except Exception as e:
            logger.error(f"❌ [TEST_TURBO_REASONING] Turbo mode error: {e}")
            test_results["turbo"] = {"error": str(e)}
        
        # 2. Быстрый режим
        try:
            logger.info("🧪 [TEST_TURBO_REASONING] Testing fast mode...")
            fast_result = turbo_service.generate_response(
                message=test_message,
                reasoning_depth="fast"
            )
            test_results["fast"] = {
                "response_preview": fast_result["response"][:200] + "..." if len(fast_result["response"]) > 200 else fast_result["response"],
                "generation_time_ms": fast_result["generation_time_ms"],
                "tokens_used": fast_result["tokens_used"],
                "reasoning_steps": fast_result["reasoning_steps"]
            }
        except Exception as e:
            logger.error(f"❌ [TEST_TURBO_REASONING] Fast mode error: {e}")
            test_results["fast"] = {"error": str(e)}
        
        # 3. Сбалансированный режим
        try:
            logger.info("🧪 [TEST_TURBO_REASONING] Testing balanced mode...")
            balanced_result = turbo_service.generate_response(
                message=test_message,
                reasoning_depth="balanced"
            )
            test_results["balanced"] = {
                "response_preview": balanced_result["response"][:200] + "..." if len(balanced_result["response"]) > 200 else balanced_result["response"],
                "generation_time_ms": balanced_result["generation_time_ms"],
                "tokens_used": balanced_result["tokens_used"],
                "reasoning_steps": balanced_result["reasoning_steps"]
            }
        except Exception as e:
            logger.error(f"❌ [TEST_TURBO_REASONING] Balanced mode error: {e}")
            test_results["balanced"] = {"error": str(e)}
        
        # 4. Глубокий режим
        try:
            logger.info("🧪 [TEST_TURBO_REASONING] Testing deep mode...")
            deep_result = turbo_service.generate_response(
                message=test_message,
                reasoning_depth="deep"
            )
            test_results["deep"] = {
                "response_preview": deep_result["response"][:200] + "..." if len(deep_result["response"]) > 200 else deep_result["response"],
                "generation_time_ms": deep_result["generation_time_ms"],
                "tokens_used": deep_result["tokens_used"],
                "reasoning_steps": deep_result["reasoning_steps"]
            }
        except Exception as e:
            logger.error(f"❌ [TEST_TURBO_REASONING] Deep mode error: {e}")
            test_results["deep"] = {"error": str(e)}
        
        logger.info("✅ [TEST_TURBO_REASONING] All modes tested successfully")
        
        return {
            "status": "success",
            "message": "Turbo reasoning test completed",
            "test_message": test_message,
            "results": test_results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ [TEST_TURBO_REASONING] Error in turbo reasoning test: {e}")
        import traceback
        logger.error(f"❌ [TEST_TURBO_REASONING] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Системные эндпоинты
# ============================================================================

@app.get("/health")
async def health_endpoint():
    """Проверка здоровья сервиса"""
    try:
        # Проверяем подключение к Ollama
        import requests
        ollama_response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        ollama_status = "healthy" if ollama_response.status_code == 200 else "unhealthy"
        
        # Проверяем подключение к Qdrant
        qdrant_response = requests.get("http://qdrant:6333/collections", timeout=5)
        qdrant_status = "healthy" if qdrant_response.status_code == 200 else "unhealthy"
        
        # Проверяем подключение к PostgreSQL
        rag_service = get_ollama_rag_service()
        try:
            rag_service.db_manager.execute_read_query("SELECT 1")
            postgres_status = "healthy"
        except:
            postgres_status = "unhealthy"
        
        return {
            "status": "healthy" if all(s == "healthy" for s in [ollama_status, qdrant_status, postgres_status]) else "degraded",
            "services": {
                "ollama": ollama_status,
                "qdrant": qdrant_status,
                "postgresql": postgres_status
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ [HEALTH] Health check error: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/metrics", response_class=PlainTextResponse)
async def metrics_endpoint():
    """Получение метрик Prometheus"""
    try:
        rag_service = get_ollama_rag_service()
        stats = rag_service.get_stats()
        
        # Формируем метрики в формате Prometheus
        metrics = []
        metrics.append(f"# HELP rag_service_vectors_total Total number of vectors in Qdrant")
        metrics.append(f"# TYPE rag_service_vectors_total gauge")
        metrics.append(f"rag_service_vectors_total {stats.get('qdrant', {}).get('vectors_count', 0)}")
        
        metrics.append(f"# HELP rag_service_documents_total Total number of documents in PostgreSQL")
        metrics.append(f"# TYPE rag_service_documents_total gauge")
        metrics.append(f"rag_service_documents_total {stats.get('postgresql', {}).get('total_documents', 0)}")
        
        metrics.append(f"# HELP rag_service_chunks_total Total number of chunks in PostgreSQL")
        metrics.append(f"# TYPE rag_service_chunks_total gauge")
        metrics.append(f"rag_service_chunks_total {stats.get('postgresql', {}).get('total_chunks', 0)}")
        
        metrics.append(f"# HELP rag_service_tokens_total Total number of tokens in documents")
        metrics.append(f"# TYPE rag_service_tokens_total gauge")
        metrics.append(f"rag_service_tokens_total {stats.get('postgresql', {}).get('total_tokens', 0)}")
        
        return "\n".join(metrics)
        
    except Exception as e:
        logger.error(f"❌ [METRICS] Error getting metrics: {e}")
        return f"# Error getting metrics: {e}"

@app.post("/clear-collection")
async def clear_collection_endpoint():
    """Очистка всей коллекции Qdrant"""
    try:
        logger.info("🧹 [CLEAR_COLLECTION] Starting collection cleanup...")
        
        # Получаем RAG сервис
        rag_service = get_ollama_rag_service()
        
        # Очищаем коллекцию
        success = rag_service.clear_collection()
        
        if success:
            logger.info("✅ [CLEAR_COLLECTION] Collection cleared successfully")
            return {
                "status": "success",
                "message": "Collection cleared successfully",
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to clear collection")
            
    except Exception as e:
        logger.error(f"❌ [CLEAR_COLLECTION] Error clearing collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Корневой эндпоинт
# ============================================================================

# Новые endpoints для устойчивой индексации
@app.post("/indexing/start")
async def start_indexing_service_endpoint():
    """Запуск сервиса устойчивой индексации"""
    from api.endpoints import start_indexing_service
    return start_indexing_service()

@app.post("/indexing/stop")
async def stop_indexing_service_endpoint():
    """Остановка сервиса устойчивой индексации"""
    from api.endpoints import stop_indexing_service
    return stop_indexing_service()

@app.get("/indexing/status")
async def get_indexing_service_status_endpoint():
    """Получение статуса сервиса устойчивой индексации"""
    from api.endpoints import get_indexing_service_status
    return get_indexing_service_status()

@app.post("/indexing/retry-failed")
async def retry_failed_documents_endpoint(max_retries: int = 3):
    """Повторная попытка индексации неудачных документов"""
    from api.endpoints import retry_failed_documents
    return retry_failed_documents(max_retries)

@app.get("/indexing/pending")
async def get_pending_documents_endpoint():
    """Получение документов, ожидающих индексации"""
    from api.endpoints import get_pending_documents
    return get_pending_documents()

@app.get("/indexing/failed")
async def get_failed_documents_endpoint(max_retries: int = 3):
    """Получение документов с неудачной индексацией"""
    from api.endpoints import get_failed_documents
    return get_failed_documents(max_retries)

@app.get("/database/health")
async def get_database_health_endpoint():
    """Получение состояния здоровья базы данных"""
    from api.endpoints import get_database_health
    return get_database_health()

@app.get("/")
async def root_endpoint():
    """Корневой эндпоинт"""
    return {
        "service": "Ollama RAG Service",
        "version": "2.1.0",
        "description": "RAG сервис для работы с нормативными документами с использованием Ollama BGE-M3",
        "features": {
            "resilient_indexing": True,
            "connection_retry": True,
            "automatic_recovery": True
        },
        "endpoints": {
            "search": "/search",
            "chat": "/chat",
            "models": "/models",
            "ntd_consultation": "/ntd-consultation/chat",
            "documents": "/documents",
            "reindex": "/reindex",
            "health": "/health",
            "metrics": "/metrics",
            "stats": "/stats",
            "indexing": {
                "start": "/indexing/start",
                "stop": "/indexing/stop",
                "status": "/indexing/status",
                "retry_failed": "/indexing/retry-failed",
                "pending": "/indexing/pending",
                "failed": "/indexing/failed"
            },
            "database": {
                "health": "/database/health"
            }
        },
        "timestamp": datetime.now().isoformat()
    }

# ============================================================================
# Запуск сервиса
# ============================================================================

if __name__ == "__main__":
    logger.info("🚀 [OLLAMA_RAG_SERVICE] Starting Ollama RAG Service...")
    
    # Проверяем доступность Ollama
    try:
        import requests
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            bge_m3_available = any("bge-m3" in model.get("name", "") for model in models)
            if bge_m3_available:
                logger.info("✅ [OLLAMA_RAG_SERVICE] BGE-M3 model is available in Ollama")
            else:
                logger.warning("⚠️ [OLLAMA_RAG_SERVICE] BGE-M3 model not found in Ollama")
        else:
            logger.error("❌ [OLLAMA_RAG_SERVICE] Cannot connect to Ollama")
    except Exception as e:
        logger.error(f"❌ [OLLAMA_RAG_SERVICE] Error checking Ollama: {e}")
    
    # Запускаем сервис
    uvicorn.run(
        "ollama_main:app",
        host="0.0.0.0",
        port=8003,
        reload=True,
        log_level="info"
    )
