"""
Упрощенный API для модуля Нормоконтроль - 2
"""

import logging
import os
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Создание роутера
router = APIRouter(tags=["Нормоконтроль-2"])

# Функция для получения сервиса
def get_normcontrol2_service():
    """Получение экземпляра сервиса"""
    from app import normcontrol2_service
    if normcontrol2_service is None:
        raise HTTPException(status_code=503, detail="Сервис не инициализирован")
    return normcontrol2_service

# Модели данных
class ValidationResponse(BaseModel):
    """Ответ с результатами валидации"""
    success: bool
    document_id: str
    document_name: str
    document_format: str
    overall_status: str
    compliance_score: float
    total_issues: int
    critical_issues: int
    high_issues: int
    medium_issues: int
    low_issues: int
    info_issues: int
    categories: Dict[str, Any]
    recommendations: List[str]
    validation_time: str
    metadata: Dict[str, Any]

class IssueResponse(BaseModel):
    """Ответ с проблемами валидации"""
    success: bool
    document_id: str
    issues: List[Dict[str, Any]]
    total_count: int

class StatisticsResponse(BaseModel):
    """Ответ со статистикой"""
    success: bool
    statistics: Dict[str, Any]

class SettingsResponse(BaseModel):
    """Ответ с настройками"""
    success: bool
    settings: Dict[str, Any]

# Эндпоинты API

@router.get("/status")
async def get_service_status():
    """Получение статуса сервиса"""
    return {
        "status": "running",
        "service": "normcontrol2-service",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@router.post("/validate", response_model=ValidationResponse)
async def validate_document(
    file: UploadFile = File(...),
    validation_options: Optional[str] = Form(None),
    service = Depends(get_normcontrol2_service)
) -> ValidationResponse:
    """Валидация документа"""
    try:
        # Генерируем ID документа
        document_id = str(uuid.uuid4())
        
        # Сохраняем файл временно
        file_extension = os.path.splitext(file.filename)[1]
        temp_file_path = f"/tmp/normcontrol2_{document_id}{file_extension}"
        
        with open(temp_file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Парсим опции валидации
        options = {}
        if validation_options:
            import json
            try:
                options = json.loads(validation_options)
            except json.JSONDecodeError:
                options = {}
        
        # Выполняем валидацию (заглушка)
        result = await service.validate_document(
            document_id=document_id,
            file_path=temp_file_path,
            options=options
        )
        
        # Очищаем временный файл
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        
        return ValidationResponse(
            success=True,
            document_id=document_id,
            document_name=file.filename,
            document_format=file_extension[1:].upper(),
            overall_status=result.get("overall_status", "unknown"),
            compliance_score=result.get("compliance_score", 0.0),
            total_issues=result.get("total_issues", 0),
            critical_issues=result.get("critical_issues", 0),
            high_issues=result.get("high_issues", 0),
            medium_issues=result.get("medium_issues", 0),
            low_issues=result.get("low_issues", 0),
            info_issues=result.get("info_issues", 0),
            categories=result.get("categories", {}),
            recommendations=result.get("recommendations", []),
            validation_time=datetime.now().isoformat(),
            metadata=result.get("metadata", {})
        )
        
    except Exception as e:
        logger.error(f"Ошибка валидации документа: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка валидации: {str(e)}")

@router.get("/documents")
async def get_documents(service = Depends(get_normcontrol2_service)):
    """Получение списка документов"""
    try:
        documents = await service.get_documents()
        return {
            "success": True,
            "documents": documents
        }
    except Exception as e:
        logger.error(f"Ошибка получения документов: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка получения документов: {str(e)}")

@router.get("/validate/{document_id}/issues", response_model=IssueResponse)
async def get_document_issues(
    document_id: str,
    service = Depends(get_normcontrol2_service)
) -> IssueResponse:
    """Получение проблем документа"""
    try:
        issues = await service.get_document_issues(document_id)
        return IssueResponse(
            success=True,
            document_id=document_id,
            issues=issues,
            total_count=len(issues)
        )
    except Exception as e:
        logger.error(f"Ошибка получения проблем документа {document_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка получения проблем: {str(e)}")

@router.get("/validate/{document_id}/status")
async def get_document_status(
    document_id: str,
    service = Depends(get_normcontrol2_service)
):
    """Получение статуса валидации документа"""
    try:
        status = await service.get_document_status(document_id)
        return {
            "success": True,
            "document_id": document_id,
            "status": status
        }
    except Exception as e:
        logger.error(f"Ошибка получения статуса документа {document_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка получения статуса: {str(e)}")

@router.get("/validate/{document_id}/report")
async def get_document_report(
    document_id: str,
    service = Depends(get_normcontrol2_service)
):
    """Получение отчета о валидации документа"""
    try:
        report = await service.get_document_report(document_id)
        return {
            "success": True,
            "document_id": document_id,
            "report": report
        }
    except Exception as e:
        logger.error(f"Ошибка получения отчета документа {document_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка получения отчета: {str(e)}")

@router.post("/batch_validate")
async def batch_validate_documents(
    file_paths: List[str] = Form(...),
    validation_options: Optional[str] = Form(None),
    service = Depends(get_normcontrol2_service)
):
    """Пакетная валидация документов"""
    try:
        options = {}
        if validation_options:
            import json
            try:
                options = json.loads(validation_options)
            except json.JSONDecodeError:
                options = {}
        
        results = await service.batch_validate_documents(file_paths, options)
        return {
            "success": True,
            "results": results
        }
    except Exception as e:
        logger.error(f"Ошибка пакетной валидации: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка пакетной валидации: {str(e)}")

@router.get("/statistics", response_model=StatisticsResponse)
async def get_statistics(service = Depends(get_normcontrol2_service)) -> StatisticsResponse:
    """Получение статистики валидации"""
    try:
        stats = await service.get_statistics()
        return StatisticsResponse(
            success=True,
            statistics=stats
        )
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка получения статистики: {str(e)}")

@router.get("/rules")
async def get_validation_rules(service = Depends(get_normcontrol2_service)):
    """Получение правил валидации"""
    try:
        rules = await service.get_validation_rules()
        return {
            "success": True,
            "rules": rules
        }
    except Exception as e:
        logger.error(f"Ошибка получения правил: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка получения правил: {str(e)}")

@router.get("/settings", response_model=SettingsResponse)
async def get_settings(service = Depends(get_normcontrol2_service)) -> SettingsResponse:
    """Получение настроек"""
    try:
        settings = await service.get_settings()
        return SettingsResponse(
            success=True,
            settings=settings
        )
    except Exception as e:
        logger.error(f"Ошибка получения настроек: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка получения настроек: {str(e)}")

@router.post("/settings")
async def save_settings(
    settings: Dict[str, Any],
    service = Depends(get_normcontrol2_service)
):
    """Сохранение настроек"""
    try:
        await service.save_settings(settings)
        return {
            "success": True,
            "message": "Настройки сохранены"
        }
    except Exception as e:
        logger.error(f"Ошибка сохранения настроек: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения настроек: {str(e)}")

@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    service = Depends(get_normcontrol2_service)
):
    """Удаление документа"""
    try:
        await service.delete_document(document_id)
        return {
            "success": True,
            "message": "Документ удален"
        }
    except Exception as e:
        logger.error(f"Ошибка удаления документа {document_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка удаления документа: {str(e)}")

@router.post("/validate/{document_id}/revalidate")
async def revalidate_document(
    document_id: str,
    options: Optional[Dict[str, Any]] = None,
    service = Depends(get_normcontrol2_service)
):
    """Повторная валидация документа"""
    try:
        result = await service.revalidate_document(document_id, options or {})
        return {
            "success": True,
            "document_id": document_id,
            "result": result
        }
    except Exception as e:
        logger.error(f"Ошибка повторной валидации документа {document_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка повторной валидации: {str(e)}")

@router.get("/validate/{document_id}/export")
async def export_results(
    document_id: str,
    format: str = "json",
    service = Depends(get_normcontrol2_service)
):
    """Экспорт результатов валидации"""
    try:
        data = await service.export_results(document_id, format)
        return {
            "success": True,
            "document_id": document_id,
            "format": format,
            "data": data
        }
    except Exception as e:
        logger.error(f"Ошибка экспорта результатов документа {document_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка экспорта: {str(e)}")
