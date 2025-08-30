from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn

# Импорты из модулей
from .api.endpoints import (
    get_documents,
    get_stats,
    get_document_chunks,
    get_documents_stats,
    delete_document,
    delete_document_indexes,
    reindex_documents,
    ntd_consultation_chat,
    ntd_consultation_stats,
    health_check,
    get_metrics
)

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
    """Реиндексация всех документов"""
    return reindex_documents()

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
async def internal_error_handler(request: Request, exc: HTTPException):
    return {"error": "Internal server error", "detail": str(exc.detail)}

# ============================================================================
# Запуск приложения
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "main_new:app",
        host="0.0.0.0",
        port=8003,
        reload=True,
        log_level="info"
    )
