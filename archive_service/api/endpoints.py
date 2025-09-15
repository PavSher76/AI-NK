"""
API эндпоинты для интеграции с существующей системой
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..models import (
    BatchUploadRequest, BatchUploadResponse, DocumentSearchRequest, 
    DocumentSearchResponse, ProjectStats, DocumentType
)
from ..database_manager import ArchiveDatabaseManager
from ..batch_upload_service import BatchUploadService
from ..vector_indexer import ArchiveVectorIndexer

logger = logging.getLogger(__name__)

# Создаем роутер для API
router = APIRouter(prefix="/archive", tags=["archive"])

def get_db_manager() -> ArchiveDatabaseManager:
    """Получение экземпляра менеджера базы данных"""
    from ..config import get_config
    config = get_config()
    return ArchiveDatabaseManager(connection_string=config['database_url'])

def get_batch_upload_service() -> BatchUploadService:
    """Получение экземпляра сервиса пакетной загрузки"""
    return BatchUploadService(get_db_manager())

def get_vector_indexer() -> ArchiveVectorIndexer:
    """Получение экземпляра векторного индексатора"""
    return ArchiveVectorIndexer()

@router.post("/upload/batch", response_model=BatchUploadResponse)
async def upload_documents_batch(
    request: BatchUploadRequest,
    batch_service: BatchUploadService = Depends(get_batch_upload_service)
):
    """Пакетная загрузка технической документации"""
    try:
        logger.info(f"📤 [ARCHIVE_API] Batch upload request for project {request.project_code}")
        
        response = await batch_service.upload_documents_batch(request)
        
        logger.info(f"✅ [ARCHIVE_API] Batch upload completed: {response.status}")
        return response
        
    except Exception as e:
        logger.error(f"❌ [ARCHIVE_API] Error in batch upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload/single")
async def upload_single_document(
    file: UploadFile = File(...),
    project_code: str = Form(...),
    document_type: str = Form("OTHER"),
    document_name: Optional[str] = Form(None),
    document_number: Optional[str] = Form(None),
    author: Optional[str] = Form(None),
    department: Optional[str] = Form(None),
    batch_service: BatchUploadService = Depends(get_batch_upload_service)
):
    """Загрузка одного документа в архив"""
    try:
        logger.info(f"📤 [ARCHIVE_API] Single upload request: {file.filename}")
        
        # Создаем временный файл
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1]}") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
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
            response = await batch_service.upload_documents_batch(request)
            
            return response
            
        finally:
            # Удаляем временный файл
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
        
    except Exception as e:
        logger.error(f"❌ [ARCHIVE_API] Error uploading single document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/projects/{project_code}/documents")
async def get_project_documents(
    project_code: str,
    db_manager: ArchiveDatabaseManager = Depends(get_db_manager)
):
    """Получение документов проекта по ШИФР"""
    try:
        logger.info(f"📋 [ARCHIVE_API] Getting documents for project {project_code}")
        
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
                    "version": doc.version,
                    "status": doc.status
                }
                for doc in documents
            ],
            "total_count": len(documents)
        }
        
    except Exception as e:
        logger.error(f"❌ [ARCHIVE_API] Error getting project documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/projects/{project_code}/stats")
async def get_project_stats(
    project_code: str,
    db_manager: ArchiveDatabaseManager = Depends(get_db_manager)
):
    """Получение статистики проекта"""
    try:
        logger.info(f"📊 [ARCHIVE_API] Getting stats for project {project_code}")
        
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
        logger.error(f"❌ [ARCHIVE_API] Error getting project stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/projects/{project_code}/sections")
async def get_project_sections(
    project_code: str,
    document_id: Optional[int] = None,
    db_manager: ArchiveDatabaseManager = Depends(get_db_manager)
):
    """Получение разделов документов проекта"""
    try:
        logger.info(f"📋 [ARCHIVE_API] Getting sections for project {project_code}")
        
        # Получаем документы проекта
        documents = db_manager.get_documents_by_project(project_code)
        
        all_sections = []
        for doc in documents:
            if document_id is None or doc.id == document_id:
                sections = db_manager.get_document_sections(doc.id)
                for section in sections:
                    all_sections.append({
                        "document_id": doc.id,
                        "document_name": doc.document_name,
                        "document_type": doc.document_type.value,
                        "section_id": section.id,
                        "section_number": section.section_number,
                        "section_title": section.section_title,
                        "section_content": section.section_content[:200] + "..." if len(section.section_content) > 200 else section.section_content,
                        "page_number": section.page_number,
                        "section_type": section.section_type,
                        "importance_level": section.importance_level
                    })
        
        return {
            "project_code": project_code,
            "sections": all_sections,
            "total_count": len(all_sections)
        }
        
    except Exception as e:
        logger.error(f"❌ [ARCHIVE_API] Error getting project sections: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search", response_model=DocumentSearchResponse)
async def search_documents(
    request: DocumentSearchRequest,
    db_manager: ArchiveDatabaseManager = Depends(get_db_manager)
):
    """Поиск документов в архиве"""
    try:
        logger.info(f"🔍 [ARCHIVE_API] Search request: {request.search_query}")
        
        response = db_manager.search_documents(request)
        
        return response
        
    except Exception as e:
        logger.error(f"❌ [ARCHIVE_API] Error searching documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search/similar")
async def search_similar_sections(
    query: str,
    project_code: Optional[str] = None,
    limit: int = 10,
    score_threshold: float = 0.7,
    vector_indexer: ArchiveVectorIndexer = Depends(get_vector_indexer)
):
    """Поиск похожих разделов по содержимому"""
    try:
        logger.info(f"🔍 [ARCHIVE_API] Similar search request: {query}")
        
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
        logger.error(f"❌ [ARCHIVE_API] Error searching similar sections: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/projects/{project_code}/progress")
async def get_upload_progress(
    project_code: str,
    batch_service: BatchUploadService = Depends(get_batch_upload_service)
):
    """Получение прогресса загрузки проекта"""
    try:
        logger.info(f"📈 [ARCHIVE_API] Getting upload progress for project {project_code}")
        
        progress = await batch_service.get_upload_progress(project_code)
        
        return progress
        
    except Exception as e:
        logger.error(f"❌ [ARCHIVE_API] Error getting upload progress: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/projects/{project_code}/cancel")
async def cancel_upload(
    project_code: str,
    batch_service: BatchUploadService = Depends(get_batch_upload_service)
):
    """Отмена загрузки проекта"""
    try:
        logger.info(f"🛑 [ARCHIVE_API] Cancelling upload for project {project_code}")
        
        success = await batch_service.cancel_upload(project_code)
        
        if success:
            return {"status": "success", "message": f"Upload cancelled for project {project_code}"}
        else:
            raise HTTPException(status_code=500, detail="Failed to cancel upload")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [ARCHIVE_API] Error cancelling upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/projects")
async def list_projects(
    limit: int = 50,
    offset: int = 0,
    db_manager: ArchiveDatabaseManager = Depends(get_db_manager)
):
    """Получение списка проектов"""
    try:
        logger.info(f"📋 [ARCHIVE_API] Getting projects list")
        
        # Получаем проекты из базы данных
        projects = db_manager.execute_read_query("""
            SELECT 
                project_code,
                project_name,
                total_documents,
                total_sections,
                status,
                created_at,
                updated_at
            FROM archive_projects 
            ORDER BY updated_at DESC
            LIMIT %s OFFSET %s
        """, (limit, offset))
        
        return {
            "projects": projects,
            "total_count": len(projects),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"❌ [ARCHIVE_API] Error getting projects list: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents/types")
async def get_document_types():
    """Получение доступных типов документов"""
    try:
        return {
            "document_types": [
                {"code": dt.value, "name": dt.name, "description": dt.value}
                for dt in DocumentType
            ]
        }
    except Exception as e:
        logger.error(f"❌ [ARCHIVE_API] Error getting document types: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """Проверка здоровья сервиса архива"""
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
        logger.error(f"❌ [ARCHIVE_API] Health check error: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
