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

# Импорт Ollama RAG сервиса
from services.ollama_rag_service import OllamaRAGService

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
    model: str = "gpt-oss:latest"
    history: Optional[List[Dict[str, str]]] = None
    max_tokens: Optional[int] = None

class ChatResponse(BaseModel):
    status: str
    response: str
    model: str
    timestamp: str
    tokens_used: Optional[int] = None
    generation_time_ms: Optional[float] = None

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

def get_ollama_rag_service():
    """Ленивая инициализация Ollama RAG сервиса"""
    global ollama_rag_service
    if ollama_rag_service is None:
        ollama_rag_service = OllamaRAGService()
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
    """Реиндексация всех документов"""
    try:
        logger.info("🔄 [REINDEX] Starting document reindexing...")
        
        # Получаем все документы
        documents = get_ollama_rag_service().get_documents()
        
        if not documents:
            return {
                "status": "success",
                "message": "No documents to reindex",
                "reindexed_count": 0,
                "total_documents": 0
            }
        
        logger.info(f"🔄 [REINDEX] Found {len(documents)} documents to reindex")
        
        reindexed_count = 0
        total_chunks = 0
        
        for document in documents:
            try:
                document_id = document['id']
                document_title = document['title']
                
                logger.info(f"🔄 [REINDEX] Reindexing document {document_id}: {document_title}")
                
                # Получаем чанки документа
                chunks = get_ollama_rag_service().get_document_chunks(document_id)
                
                if not chunks:
                    logger.warning(f"⚠️ [REINDEX] No chunks found for document {document_id}")
                    continue
                
                # Подготавливаем чанки для индексации
                chunks_for_indexing = []
                for chunk in chunks:
                    chunk_data = {
                        'id': chunk['chunk_id'],
                        'document_id': document_id,
                        'chunk_id': chunk['chunk_id'],
                        'content': chunk['content'],
                        'page': chunk.get('page_number', 1),
                        'section_title': chunk.get('chapter', ''),
                        'section': chunk.get('section', ''),
                        'document_title': document_title,
                        'title': document_title,
                        'code': get_ollama_rag_service().extract_document_code(document_title),
                        'category': document.get('category', ''),
                        'chunk_type': 'paragraph'
                    }
                    chunks_for_indexing.append(chunk_data)
                
                # Индексируем чанки
                success = get_ollama_rag_service().index_document_chunks(document_id, chunks_for_indexing)
                
                if success:
                    reindexed_count += 1
                    total_chunks += len(chunks)
                    logger.info(f"✅ [REINDEX] Document {document_id} reindexed successfully ({len(chunks)} chunks)")
                else:
                    logger.error(f"❌ [REINDEX] Failed to index document {document_id}")
                
            except Exception as e:
                logger.error(f"❌ [REINDEX] Error reindexing document {document_id}: {e}")
                continue
        
        logger.info(f"✅ [REINDEX] Reindexing completed. {reindexed_count}/{len(documents)} documents reindexed")
        
        return {
            "status": "success",
            "message": f"Reindexing completed. {reindexed_count} documents reindexed",
            "reindexed_count": reindexed_count,
            "total_documents": len(documents),
            "total_chunks": total_chunks
        }
        
    except Exception as e:
        logger.error(f"❌ [REINDEX] Reindexing error: {e}")
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

@app.post("/reindex")
async def reindex_documents_endpoint():
    """Переиндексация всех документов"""
    try:
        logger.info("🔄 [REINDEX] Starting document reindexing...")
        
        rag_service = get_ollama_rag_service()
        
        # Получаем все документы
        with rag_service.db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT ud.id, ud.original_filename as document_title, ud.category
                FROM uploaded_documents ud
                WHERE ud.processing_status = 'completed'
                ORDER BY ud.upload_date DESC
            """)
            documents = cursor.fetchall()
        
        if not documents:
            return {
                "status": "success",
                "message": "No documents to reindex",
                "documents_processed": 0,
                "timestamp": datetime.now().isoformat()
            }
        
        total_processed = 0
        total_chunks = 0
        
        for document in documents:
            try:
                document_id = document['id']
                document_title = document['document_title']
                
                logger.info(f"📝 [REINDEX] Processing document {document_id}: {document_title}")
                
                # Получаем чанки документа
                chunks = rag_service.get_document_chunks(document_id)
                
                if chunks:
                    # Добавляем информацию о документе к каждому чанку
                    for chunk in chunks:
                        chunk['document_title'] = document_title
                    
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
        
        logger.info(f"✅ [REINDEX] Reindexing completed. Processed {total_processed} documents with {total_chunks} chunks")
        
        return {
            "status": "success",
            "message": "Document reindexing completed",
            "documents_processed": total_processed,
            "total_chunks": total_chunks,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ [REINDEX] Error during reindexing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
    """Чат с ИИ через Ollama"""
    try:
        logger.info(f"💬 [CHAT] Processing chat request with model: {request.model}")
        
        # Создаем временный сервис для чата
        import requests
        import time
        
        start_time = time.time()
        
        # Формируем запрос к Ollama
        payload = {
            "model": request.model,
            "prompt": request.message,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": request.max_tokens or 2048
            }
        }
        
        if request.history:
            # Добавляем историю в промпт
            context = "\n".join([f"User: {msg.get('user', '')}\nAssistant: {msg.get('assistant', '')}" for msg in request.history])
            payload["prompt"] = f"{context}\nUser: {request.message}\nAssistant:"
        
        response = requests.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=120)
        
        if response.status_code == 200:
            result = response.json()
            response_text = result.get("response", "")
            
            generation_time = (time.time() - start_time) * 1000
            
            return ChatResponse(
                status="success",
                response=response_text,
                model=request.model,
                timestamp=datetime.now().isoformat(),
                tokens_used=result.get("eval_count", 0),
                generation_time_ms=generation_time
            )
        else:
            logger.error(f"❌ [CHAT] Ollama API error: {response.status_code} - {response.text}")
            raise HTTPException(status_code=500, detail=f"Ollama API error: {response.status_code}")
            
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
            with rag_service.db_manager.get_cursor() as cursor:
                cursor.execute("SELECT 1")
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

@app.get("/metrics")
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

@app.get("/")
async def root_endpoint():
    """Корневой эндпоинт"""
    return {
        "service": "Ollama RAG Service",
        "version": "2.0.0",
        "description": "RAG сервис для работы с нормативными документами с использованием Ollama BGE-M3",
        "endpoints": {
            "search": "/search",
            "chat": "/chat",
            "models": "/models",
            "ntd_consultation": "/ntd-consultation/chat",
            "documents": "/documents",
            "reindex": "/reindex",
            "health": "/health",
            "metrics": "/metrics",
            "stats": "/stats"
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
