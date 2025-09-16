"""
API интерфейс для модуля Нормоконтроль - 2
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import json

from .main import NormControl2Service
from .models import ValidationResult, ComplianceStatus

logger = logging.getLogger(__name__)

# Создание роутера
router = APIRouter(tags=["Нормоконтроль-2"])

# Функция для получения сервиса
def get_normcontrol2_service() -> NormControl2Service:
    """Получение экземпляра сервиса"""
    from .app import normcontrol2_service
    if normcontrol2_service is None:
        raise HTTPException(status_code=503, detail="Сервис не инициализирован")
    return normcontrol2_service


class ValidationRequest(BaseModel):
    """Запрос на валидацию документа"""
    file_path: str
    document_id: Optional[str] = None
    validation_options: Optional[Dict[str, Any]] = None


class ValidationResponse(BaseModel):
    """Ответ с результатами валидации"""
    success: bool
    document_id: str
    document_name: str
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
    """Ответ с информацией о проблеме"""
    id: str
    category: str
    severity: str
    title: str
    description: str
    recommendation: str
    page_number: Optional[int] = None
    coordinates: Optional[Dict[str, float]] = None
    rule_reference: Optional[str] = None


@router.post("/validate", response_model=ValidationResponse)
async def validate_document(
    file_path: str = Form(...),
    document_id: Optional[str] = Form(None),
    validation_options: Optional[str] = Form(None)
):
    """
    Валидация документа на соответствие ЕСКД/СПДС
    """
    try:
        # Парсинг опций валидации
        options = {}
        if validation_options:
            try:
                options = json.loads(validation_options)
            except json.JSONDecodeError:
                logger.warning(f"Не удалось распарсить опции валидации: {validation_options}")
        
        # Выполнение валидации
        result = normcontrol2_service.validate_document(file_path, document_id)
        
        # Преобразование результата в ответ
        response = ValidationResponse(
            success=True,
            document_id=result.document_id,
            document_name=result.document_name,
            overall_status=result.overall_status.value,
            compliance_score=result.compliance_score,
            total_issues=result.total_issues,
            critical_issues=result.critical_issues,
            high_issues=result.high_issues,
            medium_issues=result.medium_issues,
            low_issues=result.low_issues,
            info_issues=result.info_issues,
            categories=result.categories,
            recommendations=result.recommendations,
            validation_time=result.validation_time.isoformat(),
            metadata=result.metadata
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Ошибка валидации документа {file_path}: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка валидации: {str(e)}")


@router.get("/validate/{document_id}/issues", response_model=List[IssueResponse])
async def get_document_issues(document_id: str):
    """
    Получение списка проблем для документа
    """
    try:
        # Здесь должна быть логика получения результатов валидации по ID
        # Пока возвращаем заглушку
        return []
        
    except Exception as e:
        logger.error(f"Ошибка получения проблем для документа {document_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения проблем: {str(e)}")


@router.get("/validate/{document_id}/status")
async def get_document_status(document_id: str):
    """
    Получение статуса валидации документа
    """
    try:
        # Здесь должна быть логика получения статуса по ID
        # Пока возвращаем заглушку
        return {
            "document_id": document_id,
            "status": "completed",
            "compliance_score": 85.0,
            "total_issues": 5
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения статуса для документа {document_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения статуса: {str(e)}")


@router.get("/validate/{document_id}/report")
async def get_validation_report(document_id: str):
    """
    Получение отчета о валидации документа
    """
    try:
        # Здесь должна быть логика генерации отчета
        # Пока возвращаем заглушку
        return {
            "document_id": document_id,
            "report_type": "validation_report",
            "generated_at": "2024-01-01T00:00:00Z",
            "summary": {
                "total_issues": 5,
                "critical_issues": 0,
                "high_issues": 2,
                "medium_issues": 2,
                "low_issues": 1,
                "info_issues": 0
            },
            "recommendations": [
                "Исправить формат основной надписи",
                "Унифицировать единицы измерений"
            ]
        }
        
    except Exception as e:
        logger.error(f"Ошибка генерации отчета для документа {document_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка генерации отчета: {str(e)}")


@router.get("/health")
async def health_check():
    """
    Проверка состояния сервиса
    """
    return {
        "status": "healthy",
        "service": "normcontrol2",
        "version": "2.0.0",
        "timestamp": "2024-01-01T00:00:00Z"
    }


@router.get("/rules")
async def get_validation_rules():
    """
    Получение правил валидации
    """
    return {
        "eskd_rules": {
            "gost_21_501_2018": "Правила выполнения архитектурно-строительных чертежей",
            "gost_r_21_101_2020": "Система проектной документации для строительства"
        },
        "spds_rules": {
            "sp_48_13330_2019": "Организация строительства",
            "sp_70_13330_2012": "Несущие и ограждающие конструкции"
        },
        "validation_categories": [
            "title_block",
            "fonts",
            "scales",
            "units",
            "notations",
            "document_structure",
            "drawing_elements"
        ]
    }


@router.post("/batch_validate")
async def batch_validate_documents(
    file_paths: List[str] = Form(...),
    validation_options: Optional[str] = Form(None)
):
    """
    Пакетная валидация документов
    """
    try:
        # Парсинг опций валидации
        options = {}
        if validation_options:
            try:
                options = json.loads(validation_options)
            except json.JSONDecodeError:
                logger.warning(f"Не удалось распарсить опции валидации: {validation_options}")
        
        results = []
        for file_path in file_paths:
            try:
                result = normcontrol2_service.validate_document(file_path)
                results.append({
                    "file_path": file_path,
                    "success": True,
                    "document_id": result.document_id,
                    "overall_status": result.overall_status.value,
                    "compliance_score": result.compliance_score,
                    "total_issues": result.total_issues
                })
            except Exception as e:
                results.append({
                    "file_path": file_path,
                    "success": False,
                    "error": str(e)
                })
        
        return {
            "success": True,
            "total_documents": len(file_paths),
            "processed_documents": len([r for r in results if r["success"]]),
            "failed_documents": len([r for r in results if not r["success"]]),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Ошибка пакетной валидации: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка пакетной валидации: {str(e)}")


@router.get("/statistics")
async def get_validation_statistics():
    """
    Получение статистики валидации
    """
    # Здесь должна быть логика получения статистики
    # Пока возвращаем заглушку
    return {
        "total_documents_validated": 0,
        "average_compliance_score": 0.0,
        "most_common_issues": [],
        "validation_categories": {
            "title_block": 0,
            "fonts": 0,
            "scales": 0,
            "units": 0,
            "notations": 0
        }
    }
