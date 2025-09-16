"""
Валидатор масштабов
"""

import logging
import re
from typing import Dict, Any, List, Optional
from ..models import ValidationIssue, IssueSeverity, ScaleInfo

logger = logging.getLogger(__name__)


class ScalesValidator:
    """Валидатор масштабов"""
    
    def __init__(self):
        self.scale_requirements = self._load_scale_requirements()
        self.standard_scales = self._load_standard_scales()
        self.scale_categories = self._load_scale_categories()
    
    def _load_scale_requirements(self) -> Dict[str, Any]:
        """Загрузка требований к масштабам"""
        return {
            "gost_21_501_2018": {
                "name": "ГОСТ 21.501-2018 Правила выполнения архитектурно-строительных чертежей",
                "requirements": {
                    "numerical_scales": [
                        "1:1", "1:2", "1:5", "1:10", "1:20", "1:25", "1:50", "1:100", 
                        "1:200", "1:500", "1:1000", "1:2000", "1:5000", "1:10000",
                        "2:1", "5:1", "10:1", "20:1", "50:1", "100:1"
                    ],
                    "graphical_scales": True,
                    "text_scales": False,
                    "position": "bottom_right",
                    "font_size": 3.5
                }
            },
            "gost_r_21_101_2020": {
                "name": "ГОСТ Р 21.101-2020 Система проектной документации",
                "requirements": {
                    "scale_requirements": {
                        "plans": ["1:50", "1:100", "1:200"],
                        "sections": ["1:50", "1:100", "1:200"],
                        "details": ["1:1", "1:2", "1:5", "1:10", "1:20"],
                        "facades": ["1:50", "1:100", "1:200"]
                    }
                }
            }
        }
    
    def _load_standard_scales(self) -> List[str]:
        """Загрузка стандартных масштабов"""
        return [
            "1:1", "1:2", "1:5", "1:10", "1:20", "1:25", "1:50", "1:100", 
            "1:200", "1:500", "1:1000", "1:2000", "1:5000", "1:10000",
            "2:1", "5:1", "10:1", "20:1", "50:1", "100:1"
        ]
    
    def _load_scale_categories(self) -> Dict[str, List[str]]:
        """Загрузка категорий масштабов"""
        return {
            "reduction": ["1:2", "1:5", "1:10", "1:20", "1:25", "1:50", "1:100", "1:200", "1:500", "1:1000", "1:2000", "1:5000", "1:10000"],
            "enlargement": ["2:1", "5:1", "10:1", "20:1", "50:1", "100:1"],
            "natural": ["1:1"]
        }
    
    def validate_scales(self, scales: List[ScaleInfo]) -> List[ValidationIssue]:
        """Основная валидация масштабов"""
        issues = []
        
        if not scales:
            issues.append(ValidationIssue(
                id="no_scales",
                category="scales",
                severity=IssueSeverity.HIGH,
                title="Отсутствуют масштабы",
                description="В документе не указаны масштабы",
                recommendation="Указать масштабы согласно ГОСТ 21.501-2018"
            ))
            return issues
        
        for i, scale in enumerate(scales):
            scale_issues = self._validate_single_scale(scale, i)
            issues.extend(scale_issues)
        
        # Валидация согласованности масштабов
        consistency_issues = self._validate_scale_consistency(scales)
        issues.extend(consistency_issues)
        
        return issues
    
    def _validate_single_scale(self, scale: ScaleInfo, index: int) -> List[ValidationIssue]:
        """Валидация одного масштаба"""
        issues = []
        
        # Проверка значения масштаба
        value_issues = self._validate_scale_value(scale.value, index)
        issues.extend(value_issues)
        
        # Проверка типа масштаба
        type_issues = self._validate_scale_type(scale.type, index)
        issues.extend(type_issues)
        
        # Проверка позиции масштаба
        position_issues = self._validate_scale_position(scale.position, index)
        issues.extend(position_issues)
        
        # Проверка стандартности масштаба
        standard_issues = self._validate_scale_standard(scale, index)
        issues.extend(standard_issues)
        
        return issues
    
    def _validate_scale_value(self, value: str, index: int) -> List[ValidationIssue]:
        """Валидация значения масштаба"""
        issues = []
        
        if not value:
            issues.append(ValidationIssue(
                id=f"missing_scale_value_{index}",
                category="scales",
                severity=IssueSeverity.HIGH,
                title=f"Отсутствует значение масштаба {index + 1}",
                description=f"Не указано значение масштаба {index + 1}",
                recommendation="Указать значение масштаба"
            ))
            return issues
        
        # Проверка формата масштаба
        scale_pattern = r"^\d+:\d+$"
        if not re.match(scale_pattern, value):
            issues.append(ValidationIssue(
                id=f"invalid_scale_format_{value}_{index}",
                category="scales",
                severity=IssueSeverity.HIGH,
                title=f"Неправильный формат масштаба: {value}",
                description=f"Масштаб '{value}' не соответствует формату 'X:Y'",
                recommendation="Использовать формат масштаба 'X:Y' (например, 1:100)"
            ))
            return issues
        
        # Проверка на деление на ноль
        try:
            parts = value.split(":")
            if len(parts) == 2:
                numerator = int(parts[0])
                denominator = int(parts[1])
                if denominator == 0:
                    issues.append(ValidationIssue(
                        id=f"scale_division_by_zero_{value}_{index}",
                        category="scales",
                        severity=IssueSeverity.CRITICAL,
                        title=f"Деление на ноль в масштабе: {value}",
                        description=f"Масштаб '{value}' содержит деление на ноль",
                        recommendation="Исправить масштаб, исключив деление на ноль"
                    ))
                elif numerator == 0:
                    issues.append(ValidationIssue(
                        id=f"scale_zero_numerator_{value}_{index}",
                        category="scales",
                        severity=IssueSeverity.HIGH,
                        title=f"Нулевой числитель в масштабе: {value}",
                        description=f"Масштаб '{value}' имеет нулевой числитель",
                        recommendation="Исправить масштаб, указав ненулевой числитель"
                    ))
        except ValueError:
            issues.append(ValidationIssue(
                id=f"scale_invalid_numbers_{value}_{index}",
                category="scales",
                severity=IssueSeverity.HIGH,
                title=f"Некорректные числа в масштабе: {value}",
                description=f"Масштаб '{value}' содержит некорректные числа",
                recommendation="Использовать целые числа в формате 'X:Y'"
            ))
        
        return issues
    
    def _validate_scale_type(self, scale_type: str, index: int) -> List[ValidationIssue]:
        """Валидация типа масштаба"""
        issues = []
        
        if not scale_type:
            issues.append(ValidationIssue(
                id=f"missing_scale_type_{index}",
                category="scales",
                severity=IssueSeverity.MEDIUM,
                title=f"Отсутствует тип масштаба {index + 1}",
                description=f"Не указан тип масштаба {index + 1}",
                recommendation="Указать тип масштаба (numerical, graphical, text)"
            ))
            return issues
        
        valid_types = ["numerical", "graphical", "text"]
        if scale_type not in valid_types:
            issues.append(ValidationIssue(
                id=f"invalid_scale_type_{scale_type}_{index}",
                category="scales",
                severity=IssueSeverity.MEDIUM,
                title=f"Некорректный тип масштаба: {scale_type}",
                description=f"Тип масштаба '{scale_type}' не является стандартным",
                recommendation=f"Использовать стандартные типы: {', '.join(valid_types)}"
            ))
        
        # Проверка соответствия ГОСТ
        gost_requirements = self.scale_requirements["gost_21_501_2018"]["requirements"]
        if scale_type == "text" and not gost_requirements["text_scales"]:
            issues.append(ValidationIssue(
                id=f"text_scale_not_allowed_{index}",
                category="scales",
                severity=IssueSeverity.MEDIUM,
                title="Текстовый масштаб не рекомендуется",
                description="Текстовые масштабы не рекомендуются согласно ГОСТ 21.501-2018",
                recommendation="Использовать численные или графические масштабы"
            ))
        
        return issues
    
    def _validate_scale_position(self, position: Optional[Dict[str, float]], index: int) -> List[ValidationIssue]:
        """Валидация позиции масштаба"""
        issues = []
        
        if not position:
            issues.append(ValidationIssue(
                id=f"missing_scale_position_{index}",
                category="scales",
                severity=IssueSeverity.LOW,
                title=f"Отсутствует позиция масштаба {index + 1}",
                description=f"Не указана позиция масштаба {index + 1}",
                recommendation="Указать позицию масштаба на чертеже"
            ))
            return issues
        
        # Проверка на разумные координаты
        if position.get("x", 0) < 0 or position.get("y", 0) < 0:
            issues.append(ValidationIssue(
                id=f"negative_scale_position_{index}",
                category="scales",
                severity=IssueSeverity.LOW,
                title=f"Отрицательные координаты масштаба {index + 1}",
                description=f"Масштаб {index + 1} имеет отрицательные координаты",
                recommendation="Проверить правильность определения позиции масштаба"
            ))
        
        return issues
    
    def _validate_scale_standard(self, scale: ScaleInfo, index: int) -> List[ValidationIssue]:
        """Валидация стандартности масштаба"""
        issues = []
        
        if not scale.is_standard:
            issues.append(ValidationIssue(
                id=f"non_standard_scale_{scale.value}_{index}",
                category="scales",
                severity=IssueSeverity.MEDIUM,
                title=f"Нестандартный масштаб: {scale.value}",
                description=f"Масштаб '{scale.value}' не является стандартным",
                recommendation=f"Использовать стандартные масштабы: {', '.join(self.standard_scales[:10])}"
            ))
        
        return issues
    
    def _validate_scale_consistency(self, scales: List[ScaleInfo]) -> List[ValidationIssue]:
        """Валидация согласованности масштабов"""
        issues = []
        
        if len(scales) < 2:
            return issues
        
        # Проверка на использование разных типов масштабов
        scale_types = [s.type for s in scales if s.type]
        if len(set(scale_types)) > 1:
            issues.append(ValidationIssue(
                id="mixed_scale_types",
                category="scales",
                severity=IssueSeverity.LOW,
                title="Смешанные типы масштабов",
                description=f"В документе используются разные типы масштабов: {', '.join(set(scale_types))}",
                recommendation="Использовать единый тип масштабов для согласованности"
            ))
        
        # Проверка на разумное количество масштабов
        if len(scales) > 10:
            issues.append(ValidationIssue(
                id="too_many_scales",
                category="scales",
                severity=IssueSeverity.LOW,
                title="Слишком много масштабов",
                description=f"В документе указано {len(scales)} масштабов",
                recommendation="Проверить необходимость всех масштабов и удалить дублирующиеся"
            ))
        
        return issues
    
    def validate_scales_by_context(self, scales: List[ScaleInfo], context: str) -> List[ValidationIssue]:
        """Валидация масштабов в зависимости от контекста"""
        issues = []
        
        if context not in self.scale_requirements["gost_r_21_101_2020"]["requirements"]["scale_requirements"]:
            return issues
        
        required_scales = self.scale_requirements["gost_r_21_101_2020"]["requirements"]["scale_requirements"][context]
        
        for i, scale in enumerate(scales):
            if scale.value not in required_scales:
                issues.append(ValidationIssue(
                    id=f"inappropriate_scale_for_context_{scale.value}_{i}",
                    category="scales",
                    severity=IssueSeverity.MEDIUM,
                    title=f"Неподходящий масштаб для {context}: {scale.value}",
                    description=f"Масштаб '{scale.value}' не рекомендуется для {context}",
                    recommendation=f"Использовать подходящие масштабы для {context}: {', '.join(required_scales)}"
                ))
        
        return issues
    
    def validate_scale_accuracy(self, scales: List[ScaleInfo]) -> List[ValidationIssue]:
        """Валидация точности масштабов"""
        issues = []
        
        for i, scale in enumerate(scales):
            if not scale.value:
                continue
            
            try:
                parts = scale.value.split(":")
                if len(parts) == 2:
                    numerator = int(parts[0])
                    denominator = int(parts[1])
                    
                    # Проверка на слишком большие числа
                    if numerator > 10000 or denominator > 10000:
                        issues.append(ValidationIssue(
                            id=f"scale_too_large_{scale.value}_{i}",
                            category="scales",
                            severity=IssueSeverity.LOW,
                            title=f"Слишком большой масштаб: {scale.value}",
                            description=f"Масштаб '{scale.value}' содержит очень большие числа",
                            recommendation="Проверить правильность масштаба"
                        ))
                    
                    # Проверка на дробные масштабы
                    if numerator != 1 and denominator != 1:
                        ratio = numerator / denominator
                        if ratio < 0.001 or ratio > 1000:
                            issues.append(ValidationIssue(
                                id=f"scale_extreme_ratio_{scale.value}_{i}",
                                category="scales",
                                severity=IssueSeverity.MEDIUM,
                                title=f"Экстремальный масштаб: {scale.value}",
                                description=f"Масштаб '{scale.value}' имеет экстремальное соотношение",
                                recommendation="Проверить правильность масштаба"
                            ))
            
            except (ValueError, ZeroDivisionError):
                # Ошибки уже обработаны в _validate_scale_value
                pass
        
        return issues
