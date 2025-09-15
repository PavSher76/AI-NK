"""
Основной модуль сервиса архива технической документации
"""

import logging
import os
import sys
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncio
from pathlib import Path

# Добавляем путь к корневой директории проекта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .models import (
    BatchUploadRequest, BatchUploadResponse, DocumentSearchRequest, 
    DocumentSearchResponse, ProjectStats, ArchiveDocument, DocumentType
)
from .database_manager import ArchiveDatabaseManager
from .batch_upload_service import BatchUploadService
from .vector_indexer import ArchiveVectorIndexer
from .config import get_config

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаем FastAPI приложение
app = FastAPI(
    title="Archive Service - Пакетная загрузка технической документации",
    description="Сервис для пакетной загрузки и индексации технической документации (ПД, РД, ТЭО) с группировкой по ШИФР проекта",
    version="1.0.0"
)

# Глобальные экземпляры сервисов
db_manager = None
batch_upload_service = None
vector_indexer = None

def get_db_manager() -> ArchiveDatabaseManager:
    """Получение экземпляра менеджера базы данных"""
    global db_manager
    if db_manager is None:
        config = get_config()
        db_manager = ArchiveDatabaseManager(connection_string=config['database_url'])
    return db_manager

def get_batch_upload_service() -> BatchUploadService:
    """Получение экземпляра сервиса пакетной загрузки"""
    global batch_upload_service
    if batch_upload_service is None:
        batch_upload_service = BatchUploadService(get_db_manager())
    return batch_upload_service

def get_vector_indexer() -> ArchiveVectorIndexer:
    """Получение экземпляра векторного индексатора"""
    global vector_indexer
    if vector_indexer is None:
        vector_indexer = ArchiveVectorIndexer()
    return vector_indexer

@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске"""
    try:
        logger.info("🚀 [STARTUP] Starting Archive Service...")
        
        # Инициализируем сервисы
        db_manager = get_db_manager()
        batch_upload_service = get_batch_upload_service()
        vector_indexer = get_vector_indexer()
        
        # Проверяем здоровье сервисов
        db_health = db_manager.health_check()
        vector_health = await vector_indexer.health_check()
        
        logger.info(f"✅ [STARTUP] Database health: {db_health['status']}")
        logger.info(f"✅ [STARTUP] Vector indexer health: {vector_health['status']}")
        
        logger.info("✅ [STARTUP] Archive Service started successfully")
        
    except Exception as e:
        logger.error(f"❌ [STARTUP] Error during startup: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Очистка при завершении"""
    try:
        logger.info("🛑 [SHUTDOWN] Shutting down Archive Service...")
        
        if db_manager:
            db_manager.close_all_connections()
        
        logger.info("✅ [SHUTDOWN] Archive Service shut down successfully")
        
    except Exception as e:
        logger.error(f"❌ [SHUTDOWN] Error during shutdown: {e}")

@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "service": "Archive Service",
        "description": "Пакетная загрузка технической документации",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    try:
        db_manager = get_db_manager()
        vector_indexer = get_vector_indexer()
        
        db_health = db_manager.health_check()
        vector_health = await vector_indexer.health_check()
        
        overall_status = "healthy" if (
            db_health['status'] == 'healthy' and 
            vector_health['status'] == 'healthy'
        ) else "unhealthy"
        
        return {
            "status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "services": {
                "database": db_health,
                "vector_indexer": vector_health
            }
        }
        
    except Exception as e:
        logger.error(f"❌ [HEALTH] Health check error: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.post("/upload/batch", response_model=BatchUploadResponse)
async def upload_documents_batch(request: BatchUploadRequest):
    """Пакетная загрузка документов"""
    try:
        logger.info(f"📤 [BATCH_UPLOAD] Starting batch upload for project {request.project_code}")
        
        batch_service = get_batch_upload_service()
        response = await batch_service.upload_documents_batch(request)
        
        logger.info(f"✅ [BATCH_UPLOAD] Batch upload completed: {response.status}")
        return response
        
    except Exception as e:
        logger.error(f"❌ [BATCH_UPLOAD] Error in batch upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload/single")
async def upload_single_document(
    file: UploadFile = File(...),
    project_code: str = Form(...),
    document_type: str = Form("OTHER"),
    document_name: Optional[str] = Form(None),
    document_number: Optional[str] = Form(None),
    author: Optional[str] = Form(None),
    department: Optional[str] = Form(None)
):
    """Загрузка одного документа"""
    try:
        logger.info(f"📤 [SINGLE_UPLOAD] Uploading single document: {file.filename}")
        
        # Сохраняем файл во временную директорию
        temp_dir = "/tmp/archive_uploads"
        os.makedirs(temp_dir, exist_ok=True)
        
        temp_file_path = os.path.join(temp_dir, file.filename)
        with open(temp_file_path, "wb") as temp_file:
            content = await file.read()
            temp_file.write(content)
        
        # Создаем запрос пакетной загрузки
        request = BatchUploadRequest(
            project_code=project_code,
            documents=[{
                'file_path': temp_file_path,
                'document_type': document_type,
                'document_name': document_name or file.filename,
                'document_number': document_number,
                'author': author,
                'department': department
            }],
            auto_extract_sections=True,
            create_relations=False
        )
        
        # Выполняем загрузку
        batch_service = get_batch_upload_service()
        response = await batch_service.upload_documents_batch(request)
        
        # Удаляем временный файл
        os.remove(temp_file_path)
        
        return response
        
    except Exception as e:
        logger.error(f"❌ [SINGLE_UPLOAD] Error uploading single document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/projects/{project_code}/documents")
async def get_project_documents(project_code: str):
    """Получение документов проекта"""
    try:
        logger.info(f"📋 [GET_PROJECT_DOCUMENTS] Getting documents for project {project_code}")
        
        db_manager = get_db_manager()
        documents = db_manager.get_documents_by_project(project_code)
        
        return {
            "project_code": project_code,
            "documents": [
                {
                    "id": doc.id,
                    "document_type": doc.document_type.value,
                    "document_name": doc.document_name,
                    "document_number": doc.document_number,
                    "original_filename": doc.original_filename,
                    "file_type": doc.file_type,
                    "file_size": doc.file_size,
                    "upload_date": doc.upload_date.isoformat() if doc.upload_date else None,
                    "processing_status": doc.processing_status.value,
                    "author": doc.author,
                    "department": doc.department,
                    "version": doc.version
                }
                for doc in documents
            ],
            "total_count": len(documents)
        }
        
    except Exception as e:
        logger.error(f"❌ [GET_PROJECT_DOCUMENTS] Error getting project documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/projects/{project_code}/stats")
async def get_project_stats(project_code: str):
    """Получение статистики проекта"""
    try:
        logger.info(f"📊 [GET_PROJECT_STATS] Getting stats for project {project_code}")
        
        db_manager = get_db_manager()
        stats = db_manager.get_project_stats(project_code)
        
        if not stats:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return {
            "project_code": stats.project_code,
            "project_name": stats.project_name,
            "total_documents": stats.total_documents,
            "documents_by_type": stats.documents_by_type,
            "total_sections": stats.total_sections,
            "total_size": stats.total_size,
            "last_upload": stats.last_upload.isoformat() if stats.last_upload else None,
            "processing_status": stats.processing_status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [GET_PROJECT_STATS] Error getting project stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search", response_model=DocumentSearchResponse)
async def search_documents(request: DocumentSearchRequest):
    """Поиск документов"""
    try:
        logger.info(f"🔍 [SEARCH] Searching documents with query: {request.search_query}")
        
        db_manager = get_db_manager()
        response = db_manager.search_documents(request)
        
        return response
        
    except Exception as e:
        logger.error(f"❌ [SEARCH] Error searching documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search/similar")
async def search_similar_sections(
    query: str,
    project_code: Optional[str] = None,
    limit: int = 10,
    score_threshold: float = 0.7
):
    """Поиск похожих разделов"""
    try:
        logger.info(f"🔍 [SEARCH_SIMILAR] Searching similar sections for query: {query}")
        
        vector_indexer = get_vector_indexer()
        results = await vector_indexer.search_similar_sections(
            query=query,
            project_code=project_code,
            limit=limit,
            score_threshold=score_threshold
        )
        
        return {
            "query": query,
            "project_code": project_code,
            "results": results,
            "total_found": len(results)
        }
        
    except Exception as e:
        logger.error(f"❌ [SEARCH_SIMILAR] Error searching similar sections: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/projects/{project_code}/progress")
async def get_upload_progress(project_code: str):
    """Получение прогресса загрузки проекта"""
    try:
        logger.info(f"📈 [GET_PROGRESS] Getting upload progress for project {project_code}")
        
        batch_service = get_batch_upload_service()
        progress = await batch_service.get_upload_progress(project_code)
        
        return progress
        
    except Exception as e:
        logger.error(f"❌ [GET_PROGRESS] Error getting upload progress: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/projects/{project_code}/cancel")
async def cancel_upload(project_code: str):
    """Отмена загрузки проекта"""
    try:
        logger.info(f"🛑 [CANCEL_UPLOAD] Cancelling upload for project {project_code}")
        
        batch_service = get_batch_upload_service()
        success = await batch_service.cancel_upload(project_code)
        
        if success:
            return {"status": "success", "message": f"Upload cancelled for project {project_code}"}
        else:
            raise HTTPException(status_code=500, detail="Failed to cancel upload")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [CANCEL_UPLOAD] Error cancelling upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/config")
async def get_service_config():
    """Получение конфигурации сервиса"""
    try:
        config = get_config()
        return {
            "status": "success",
            "config": config
        }
    except Exception as e:
        logger.error(f"❌ [GET_CONFIG] Error getting config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/vector/stats")
async def get_vector_stats():
    """Получение статистики векторной базы"""
    try:
        vector_indexer = get_vector_indexer()
        stats = await vector_indexer.get_collection_stats()
        
        return {
            "status": "success",
            "vector_stats": stats
        }
        
    except Exception as e:
        logger.error(f"❌ [GET_VECTOR_STATS] Error getting vector stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
