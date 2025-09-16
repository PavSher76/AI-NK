"""
Модуль Нормоконтроль - 2
Расширенная система проверки формата и оформления документов
"""

__version__ = "2.0.0"
__author__ = "AI-NK Team"

from .main import NormControl2Service
from .validators import (
    ESKDValidator,
    SPDSValidator,
    TitleBlockValidator,
    UnitsValidator,
    FontsValidator,
    ScalesValidator,
    NotationsValidator
)
from .models import (
    ValidationResult,
    ValidationIssue,
    IssueSeverity,
    DocumentFormat,
    ComplianceStatus
)

__all__ = [
    "NormControl2Service",
    "ESKDValidator",
    "SPDSValidator", 
    "TitleBlockValidator",
    "UnitsValidator",
    "FontsValidator",
    "ScalesValidator",
    "NotationsValidator",
    "ValidationResult",
    "ValidationIssue",
    "IssueSeverity",
    "DocumentFormat",
    "ComplianceStatus"
]
