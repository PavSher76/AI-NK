#!/usr/bin/env python3
"""
Основной RAG сервис для работы с нормативными документами
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn
import logging
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    tokens_used: int
    generation_time_ms: int
    turbo_mode: bool
    reasoning_depth: str
    reasoning_steps: int

# Импорт эндпоинтов
from api.endpoints import (
    get_documents,
    get_stats,
    get_document_chunks,
    get_documents_stats,
    reindex_documents,
    start_async_reindex,
    get_reindex_status,
    delete_document,
    delete_document_indexes,
    ntd_consultation_chat,
    ntd_consultation_stats,
    clear_consultation_cache,
    get_consultation_cache_stats,
    health_check,
    get_metrics
)

# Создание FastAPI приложения
app = FastAPI(
    title="RAG Service",
    description="Основной RAG сервис для работы с нормативными документами",
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

# ============================================================================
# API эндпоинты
# ============================================================================

@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "service": "RAG Service",
        "version": "1.0.0",
        "description": "Основной RAG сервис для работы с нормативными документами",
        "endpoints": {
            "documents": "/documents",
            "stats": "/stats",
            "documents_stats": "/documents/stats",
            "document_chunks": "/documents/{document_id}/chunks",
            "reindex": "/reindex",
            "async_reindex": "/reindex/async",
            "reindex_status": "/reindex/status/{task_id}",
            "delete_document": "/documents/{document_id}",
            "delete_indexes": "/documents/{document_id}/indexes",
            "chat": "/chat",
            "models": "/models",
            "ntd_consultation": "/ntd-consultation/chat",
            "ntd_consultation_stats": "/ntd-consultation/stats",
            "clear_cache": "/ntd-consultation/cache/clear",
            "cache_stats": "/ntd-consultation/cache/stats",
            "health": "/health",
            "metrics": "/metrics"
        },
        "timestamp": datetime.now().isoformat()
    }

@app.get("/documents")
async def documents():
    """Получение списка нормативных документов"""
    return get_documents()

@app.get("/stats")
async def stats():
    """Получение статистики RAG-системы"""
    return get_stats()

@app.get("/documents/stats")
async def documents_stats():
    """Получение статистики документов"""
    return get_documents_stats()

@app.get("/documents/{document_id}/chunks")
async def document_chunks(document_id: int):
    """Получение чанков документа"""
    return get_document_chunks(document_id)

@app.post("/reindex")
async def reindex():
    """Реиндексация всех документов"""
    return reindex_documents()

@app.post("/reindex/async")
async def async_reindex():
    """Запуск асинхронной реиндексации"""
    return start_async_reindex()

@app.get("/reindex/status/{task_id}")
async def reindex_status(task_id: str):
    """Получение статуса реиндексации"""
    return get_reindex_status(task_id)

@app.delete("/documents/{document_id}")
async def delete_doc(document_id: int):
    """Удаление документа"""
    return delete_document(document_id)

@app.delete("/documents/{document_id}/indexes")
async def delete_indexes(document_id: int):
    """Удаление индексов документа"""
    return delete_document_indexes(document_id)

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

@app.post("/ntd-consultation/chat")
async def ntd_chat(message: str, user_id: str):
    """Обработка запроса консультации НТД"""
    return ntd_consultation_chat(message, user_id)

@app.get("/ntd-consultation/stats")
async def ntd_stats():
    """Получение статистики консультаций НТД"""
    return ntd_consultation_stats()

@app.post("/ntd-consultation/cache/clear")
async def clear_cache():
    """Очистка кэша консультаций"""
    return clear_consultation_cache()

@app.get("/ntd-consultation/cache/stats")
async def cache_stats():
    """Получение статистики кэша"""
    return get_consultation_cache_stats()

@app.get("/health")
async def health():
    """Проверка здоровья сервиса"""
    return health_check()

@app.get("/models")
async def models_endpoint():
    """Получение списка доступных моделей Ollama"""
    try:
        logger.info("🔍 [MODELS] Getting available Ollama models")
        
        import requests
        
        # Получаем модели от Ollama
        ollama_url = "http://ollama:11434"
        response = requests.get(f"{ollama_url}/api/tags", timeout=10)
        
        if response.status_code == 200:
            models_data = response.json()
            models = models_data.get("models", [])
            
            # Фильтруем только модели для чата (исключаем bge-m3)
            chat_models = [
                {
                    "name": model.get("name", ""),
                    "model": model.get("model", ""),
                    "size": model.get("size", 0),
                    "details": {
                        "family": model.get("details", {}).get("family", "unknown"),
                        "parameter_size": model.get("details", {}).get("parameter_size", "unknown")
                    }
                }
                for model in models
                if not model.get("name", "").startswith("bge-m3")
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
            return {
                "status": "error",
                "models": [],
                "total_count": 0,
                "ollama_status": "unhealthy",
                "error": f"Ollama API error: {response.status_code}",
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"❌ [MODELS] Error getting models: {e}")
        return {
            "status": "error",
            "models": [],
            "total_count": 0,
            "ollama_status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/metrics")
async def metrics():
    """Получение метрик Prometheus"""
    return get_metrics()

# ============================================================================
# Запуск сервиса
# ============================================================================

if __name__ == "__main__":
    logger.info("🚀 [RAG_SERVICE] Starting RAG Service...")
    
    # Запускаем сервис
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8003,
        reload=True,
        log_level="info"
    )
