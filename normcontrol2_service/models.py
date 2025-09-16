"""
Модели данных для модуля Нормоконтроль - 2
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime


class IssueSeverity(Enum):
    """Уровни серьезности проблем"""
    CRITICAL = "critical"      # Критическая - блокирует приемку
    HIGH = "high"              # Высокая - требует исправления
    MEDIUM = "medium"          # Средняя - рекомендуется исправить
    LOW = "low"                # Низкая - информационная
    INFO = "info"              # Информационная


class DocumentFormat(Enum):
    """Форматы документов"""
    PDF = "pdf"
    DWG = "dwg"
    DXF = "dxf"
    DOCX = "docx"
    XLSX = "xlsx"
    UNKNOWN = "unknown"


class ComplianceStatus(Enum):
    """Статусы соответствия"""
    COMPLIANT = "compliant"                    # Полностью соответствует
    COMPLIANT_WITH_WARNINGS = "compliant_warnings"  # Соответствует с предупреждениями
    NON_COMPLIANT = "non_compliant"            # Не соответствует
    CRITICAL_ISSUES = "critical_issues"        # Критические нарушения
    NEEDS_REVIEW = "needs_review"              # Требует проверки


@dataclass
class ValidationIssue:
    """Проблема при валидации"""
    id: str
    category: str
    severity: IssueSeverity
    title: str
    description: str
    recommendation: str
    page_number: Optional[int] = None
    coordinates: Optional[Dict[str, float]] = None
    rule_reference: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ValidationResult:
    """Результат валидации"""
    document_id: str
    document_name: str
    document_format: DocumentFormat
    validation_time: datetime
    overall_status: ComplianceStatus
    compliance_score: float
    total_issues: int
    critical_issues: int
    high_issues: int
    medium_issues: int
    low_issues: int
    info_issues: int
    issues: List[ValidationIssue]
    categories: Dict[str, Dict[str, Any]]
    recommendations: List[str]
    metadata: Dict[str, Any]


@dataclass
class ESKDRequirements:
    """Требования ЕСКД"""
    gost_21_501_2018: Dict[str, Any]
    gost_r_21_101_2020: Dict[str, Any]
    gost_21_1101_2013: Dict[str, Any]
    gost_21_201_2011: Dict[str, Any]


@dataclass
class SPDSRequirements:
    """Требования СПДС"""
    sp_48_13330_2019: Dict[str, Any]
    sp_70_13330_2012: Dict[str, Any]
    sp_16_13330_2017: Dict[str, Any]
    sp_20_13330_2016: Dict[str, Any]


@dataclass
class TitleBlockInfo:
    """Информация о основной надписи"""
    has_title_block: bool
    project_name: Optional[str] = None
    project_number: Optional[str] = None
    document_name: Optional[str] = None
    document_number: Optional[str] = None
    scale: Optional[str] = None
    sheet_number: Optional[str] = None
    total_sheets: Optional[str] = None
    designer: Optional[str] = None
    checker: Optional[str] = None
    approver: Optional[str] = None
    date: Optional[str] = None
    revision: Optional[str] = None
    position: Optional[Dict[str, float]] = None
    size: Optional[Dict[str, float]] = None


@dataclass
class FontInfo:
    """Информация о шрифте"""
    family: str
    size: float
    style: str
    weight: str
    color: str
    position: Dict[str, float]


@dataclass
class ScaleInfo:
    """Информация о масштабе"""
    value: str
    type: str  # "numerical", "graphical", "text"
    position: Dict[str, float]
    is_standard: bool


@dataclass
class UnitsInfo:
    """Информация о единицах измерения"""
    length_unit: str
    area_unit: str
    volume_unit: str
    angle_unit: str
    temperature_unit: str
    is_metric: bool
    is_standard: bool


@dataclass
class NotationInfo:
    """Информация об обозначениях"""
    symbols: List[str]
    abbreviations: List[str]
    references: List[str]
    is_standard: bool
    missing_standard: List[str]


@dataclass
class DocumentMetadata:
    """Метаданные документа"""
    file_size: int
    page_count: int
    creation_date: Optional[datetime] = None
    modification_date: Optional[datetime] = None
    author: Optional[str] = None
    title: Optional[str] = None
    subject: Optional[str] = None
    keywords: Optional[List[str]] = None
    producer: Optional[str] = None
    creator: Optional[str] = None
