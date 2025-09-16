"""
Валидатор шрифтов
"""

import logging
import re
from typing import Dict, Any, List, Optional
from ..models import ValidationIssue, IssueSeverity, FontInfo

logger = logging.getLogger(__name__)


class FontsValidator:
    """Валидатор шрифтов"""
    
    def __init__(self):
        self.font_requirements = self._load_font_requirements()
        self.standard_fonts = self._load_standard_fonts()
        self.font_sizes = self._load_standard_font_sizes()
    
    def _load_font_requirements(self) -> Dict[str, Any]:
        """Загрузка требований к шрифтам"""
        return {
            "gost_21_501_2018": {
                "name": "ГОСТ 21.501-2018 Правила выполнения архитектурно-строительных чертежей",
                "requirements": {
                    "standard_fonts": ["Arial", "Times New Roman", "Calibri"],
                    "min_size": 2.5,
                    "max_size": 14.0,
                    "standard_sizes": [2.5, 3.5, 5.0, 7.0, 10.0, 14.0],
                    "line_spacing": 1.2,
                    "character_spacing": 0.0
                }
            },
            "gost_r_21_101_2020": {
                "name": "ГОСТ Р 21.101-2020 Система проектной документации",
                "requirements": {
                    "title_font": {
                        "family": "Arial",
                        "size": 14.0,
                        "weight": "bold"
                    },
                    "body_font": {
                        "family": "Arial",
                        "size": 3.5,
                        "weight": "normal"
                    },
                    "caption_font": {
                        "family": "Arial",
                        "size": 2.5,
                        "weight": "normal"
                    }
                }
            }
        }
    
    def _load_standard_fonts(self) -> List[str]:
        """Загрузка стандартных шрифтов"""
        return [
            "Arial", "Times New Roman", "Calibri", "Tahoma", "Verdana",
            "Helvetica", "Courier New", "Georgia", "Palatino", "Garamond"
        ]
    
    def _load_standard_font_sizes(self) -> List[float]:
        """Загрузка стандартных размеров шрифтов"""
        return [2.5, 3.5, 5.0, 7.0, 10.0, 14.0, 18.0, 24.0, 36.0, 48.0]
    
    def validate_fonts(self, fonts: List[FontInfo]) -> List[ValidationIssue]:
        """Основная валидация шрифтов"""
        issues = []
        
        if not fonts:
            issues.append(ValidationIssue(
                id="no_fonts_detected",
                category="fonts",
                severity=IssueSeverity.MEDIUM,
                title="Не удалось определить шрифты",
                description="В документе не удалось распознать шрифты",
                recommendation="Проверить качество документа и наличие текста"
            ))
            return issues
        
        for i, font in enumerate(fonts):
            font_issues = self._validate_single_font(font, i)
            issues.extend(font_issues)
        
        # Валидация согласованности шрифтов
        consistency_issues = self._validate_font_consistency(fonts)
        issues.extend(consistency_issues)
        
        return issues
    
    def _validate_single_font(self, font: FontInfo, index: int) -> List[ValidationIssue]:
        """Валидация одного шрифта"""
        issues = []
        
        # Проверка семейства шрифта
        family_issues = self._validate_font_family(font.family, index)
        issues.extend(family_issues)
        
        # Проверка размера шрифта
        size_issues = self._validate_font_size(font.size, index)
        issues.extend(size_issues)
        
        # Проверка стиля шрифта
        style_issues = self._validate_font_style(font.style, index)
        issues.extend(style_issues)
        
        # Проверка веса шрифта
        weight_issues = self._validate_font_weight(font.weight, index)
        issues.extend(weight_issues)
        
        # Проверка цвета шрифта
        color_issues = self._validate_font_color(font.color, index)
        issues.extend(color_issues)
        
        return issues
    
    def _validate_font_family(self, family: str, index: int) -> List[ValidationIssue]:
        """Валидация семейства шрифта"""
        issues = []
        
        if not family:
            issues.append(ValidationIssue(
                id=f"missing_font_family_{index}",
                category="fonts",
                severity=IssueSeverity.MEDIUM,
                title=f"Отсутствует семейство шрифта {index + 1}",
                description=f"Не удалось определить семейство шрифта {index + 1}",
                recommendation="Проверить качество документа и наличие текста"
            ))
            return issues
        
        # Проверка на стандартность
        if family not in self.standard_fonts:
            issues.append(ValidationIssue(
                id=f"non_standard_font_family_{family}_{index}",
                category="fonts",
                severity=IssueSeverity.LOW,
                title=f"Нестандартное семейство шрифта: {family}",
                description=f"Шрифт '{family}' не рекомендуется для технических документов",
                recommendation=f"Использовать стандартные шрифты: {', '.join(self.standard_fonts[:5])}"
            ))
        
        # Проверка на соответствие ГОСТ
        gost_fonts = self.font_requirements["gost_21_501_2018"]["requirements"]["standard_fonts"]
        if family not in gost_fonts:
            issues.append(ValidationIssue(
                id=f"non_gost_font_family_{family}_{index}",
                category="fonts",
                severity=IssueSeverity.MEDIUM,
                title=f"Шрифт не соответствует ГОСТ: {family}",
                description=f"Шрифт '{family}' не указан в ГОСТ 21.501-2018",
                recommendation=f"Использовать шрифты согласно ГОСТ: {', '.join(gost_fonts)}"
            ))
        
        return issues
    
    def _validate_font_size(self, size: float, index: int) -> List[ValidationIssue]:
        """Валидация размера шрифта"""
        issues = []
        
        if size <= 0:
            issues.append(ValidationIssue(
                id=f"invalid_font_size_{size}_{index}",
                category="fonts",
                severity=IssueSeverity.HIGH,
                title=f"Некорректный размер шрифта: {size}",
                description=f"Размер шрифта {size} не может быть отрицательным или нулевым",
                recommendation="Исправить размер шрифта"
            ))
            return issues
        
        # Проверка минимального размера
        min_size = self.font_requirements["gost_21_501_2018"]["requirements"]["min_size"]
        if size < min_size:
            issues.append(ValidationIssue(
                id=f"too_small_font_size_{size}_{index}",
                category="fonts",
                severity=IssueSeverity.HIGH,
                title=f"Слишком мелкий шрифт: {size}",
                description=f"Размер шрифта {size} меньше минимального {min_size}",
                recommendation=f"Увеличить размер шрифта до {min_size} или больше"
            ))
        
        # Проверка максимального размера
        max_size = self.font_requirements["gost_21_501_2018"]["requirements"]["max_size"]
        if size > max_size:
            issues.append(ValidationIssue(
                id=f"too_large_font_size_{size}_{index}",
                category="fonts",
                severity=IssueSeverity.MEDIUM,
                title=f"Слишком крупный шрифт: {size}",
                description=f"Размер шрифта {size} больше максимального {max_size}",
                recommendation=f"Уменьшить размер шрифта до {max_size} или меньше"
            ))
        
        # Проверка на стандартность размера
        if size not in self.font_sizes:
            closest_size = min(self.font_sizes, key=lambda x: abs(x - size))
            issues.append(ValidationIssue(
                id=f"non_standard_font_size_{size}_{index}",
                category="fonts",
                severity=IssueSeverity.LOW,
                title=f"Нестандартный размер шрифта: {size}",
                description=f"Размер шрифта {size} не является стандартным",
                recommendation=f"Использовать стандартный размер: {closest_size}"
            ))
        
        return issues
    
    def _validate_font_style(self, style: str, index: int) -> List[ValidationIssue]:
        """Валидация стиля шрифта"""
        issues = []
        
        if not style:
            return issues
        
        valid_styles = ["normal", "italic", "oblique"]
        if style not in valid_styles:
            issues.append(ValidationIssue(
                id=f"invalid_font_style_{style}_{index}",
                category="fonts",
                severity=IssueSeverity.LOW,
                title=f"Некорректный стиль шрифта: {style}",
                description=f"Стиль шрифта '{style}' не является стандартным",
                recommendation=f"Использовать стандартные стили: {', '.join(valid_styles)}"
            ))
        
        return issues
    
    def _validate_font_weight(self, weight: str, index: int) -> List[ValidationIssue]:
        """Валидация веса шрифта"""
        issues = []
        
        if not weight:
            return issues
        
        valid_weights = ["normal", "bold", "bolder", "lighter", "100", "200", "300", "400", "500", "600", "700", "800", "900"]
        if weight not in valid_weights:
            issues.append(ValidationIssue(
                id=f"invalid_font_weight_{weight}_{index}",
                category="fonts",
                severity=IssueSeverity.LOW,
                title=f"Некорректный вес шрифта: {weight}",
                description=f"Вес шрифта '{weight}' не является стандартным",
                recommendation=f"Использовать стандартные веса: {', '.join(valid_weights[:5])}"
            ))
        
        return issues
    
    def _validate_font_color(self, color: str, index: int) -> List[ValidationIssue]:
        """Валидация цвета шрифта"""
        issues = []
        
        if not color:
            return issues
        
        # Проверка на черный цвет (стандарт для технических документов)
        if color.lower() not in ["black", "#000000", "#000", "rgb(0,0,0)"]:
            issues.append(ValidationIssue(
                id=f"non_black_font_color_{color}_{index}",
                category="fonts",
                severity=IssueSeverity.LOW,
                title=f"Нестандартный цвет шрифта: {color}",
                description=f"Цвет шрифта '{color}' не является стандартным для технических документов",
                recommendation="Использовать черный цвет для текста в технических документах"
            ))
        
        return issues
    
    def _validate_font_consistency(self, fonts: List[FontInfo]) -> List[ValidationIssue]:
        """Валидация согласованности шрифтов"""
        issues = []
        
        if len(fonts) < 2:
            return issues
        
        # Проверка согласованности семейств шрифтов
        families = [f.family for f in fonts if f.family]
        if len(set(families)) > 3:  # Допускается до 3 разных семейств
            issues.append(ValidationIssue(
                id="too_many_font_families",
                category="fonts",
                severity=IssueSeverity.MEDIUM,
                title="Слишком много разных семейств шрифтов",
                description=f"В документе используется {len(set(families))} разных семейств шрифтов",
                recommendation="Использовать не более 2-3 семейств шрифтов для единообразия"
            ))
        
        # Проверка согласованности размеров шрифтов
        sizes = [f.size for f in fonts if f.size > 0]
        if sizes:
            size_variance = max(sizes) - min(sizes)
            if size_variance > 10:  # Большая разница в размерах
                issues.append(ValidationIssue(
                    id="inconsistent_font_sizes",
                    category="fonts",
                    severity=IssueSeverity.LOW,
                    title="Несогласованные размеры шрифтов",
                    description=f"Размеры шрифтов варьируются от {min(sizes)} до {max(sizes)}",
                    recommendation="Унифицировать размеры шрифтов для лучшей читаемости"
                ))
        
        return issues
    
    def validate_font_requirements_by_context(self, fonts: List[FontInfo], context: str) -> List[ValidationIssue]:
        """Валидация шрифтов в зависимости от контекста"""
        issues = []
        
        if context == "title":
            title_requirements = self.font_requirements["gost_r_21_101_2020"]["requirements"]["title_font"]
            for i, font in enumerate(fonts):
                if font.family != title_requirements["family"]:
                    issues.append(ValidationIssue(
                        id=f"incorrect_title_font_family_{i}",
                        category="fonts",
                        severity=IssueSeverity.MEDIUM,
                        title="Неправильное семейство шрифта для заголовка",
                        description=f"Заголовок использует шрифт '{font.family}', ожидается '{title_requirements['family']}'",
                        recommendation=f"Использовать шрифт '{title_requirements['family']}' для заголовков"
                    ))
                
                if font.size != title_requirements["size"]:
                    issues.append(ValidationIssue(
                        id=f"incorrect_title_font_size_{i}",
                        category="fonts",
                        severity=IssueSeverity.MEDIUM,
                        title="Неправильный размер шрифта для заголовка",
                        description=f"Заголовок использует размер {font.size}, ожидается {title_requirements['size']}",
                        recommendation=f"Использовать размер {title_requirements['size']} для заголовков"
                    ))
        
        elif context == "body":
            body_requirements = self.font_requirements["gost_r_21_101_2020"]["requirements"]["body_font"]
            for i, font in enumerate(fonts):
                if font.family != body_requirements["family"]:
                    issues.append(ValidationIssue(
                        id=f"incorrect_body_font_family_{i}",
                        category="fonts",
                        severity=IssueSeverity.LOW,
                        title="Неправильное семейство шрифта для основного текста",
                        description=f"Основной текст использует шрифт '{font.family}', ожидается '{body_requirements['family']}'",
                        recommendation=f"Использовать шрифт '{body_requirements['family']}' для основного текста"
                    ))
        
        elif context == "caption":
            caption_requirements = self.font_requirements["gost_r_21_101_2020"]["requirements"]["caption_font"]
            for i, font in enumerate(fonts):
                if font.size != caption_requirements["size"]:
                    issues.append(ValidationIssue(
                        id=f"incorrect_caption_font_size_{i}",
                        category="fonts",
                        severity=IssueSeverity.LOW,
                        title="Неправильный размер шрифта для подписей",
                        description=f"Подписи используют размер {font.size}, ожидается {caption_requirements['size']}",
                        recommendation=f"Использовать размер {caption_requirements['size']} для подписей"
                    ))
        
        return issues
