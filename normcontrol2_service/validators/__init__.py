"""
Валидаторы для модуля Нормоконтроль - 2
"""

from .eskd_validator import ESKDValidator
from .spds_validator import SPDSValidator
from .title_block_validator import TitleBlockValidator
from .units_validator import UnitsValidator
from .fonts_validator import FontsValidator
from .scales_validator import ScalesValidator
from .notations_validator import NotationsValidator

__all__ = [
    "ESKDValidator",
    "SPDSValidator",
    "TitleBlockValidator",
    "UnitsValidator",
    "FontsValidator",
    "ScalesValidator",
    "NotationsValidator"
]
