#!/usr/bin/env python3
"""
Основной RAG сервис для работы с нормативными документами
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
