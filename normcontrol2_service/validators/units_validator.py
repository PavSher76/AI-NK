"""
Валидатор единиц измерений
"""

import logging
import re
from typing import Dict, Any, List, Optional
from ..models import ValidationIssue, IssueSeverity, UnitsInfo

logger = logging.getLogger(__name__)


class UnitsValidator:
    """Валидатор единиц измерений"""
    
    def __init__(self):
        self.standard_units = self._load_standard_units()
        self.unit_conversion_factors = self._load_conversion_factors()
    
    def _load_standard_units(self) -> Dict[str, List[str]]:
        """Загрузка стандартных единиц измерений"""
        return {
            "length": {
                "metric": ["мм", "см", "м", "км"],
                "imperial": ["дюйм", "фут", "ярд", "миля"],
                "si": ["m", "mm", "cm", "km"]
            },
            "area": {
                "metric": ["мм²", "см²", "м²", "га"],
                "imperial": ["дюйм²", "фут²", "ярд²", "акр"],
                "si": ["m²", "mm²", "cm²", "ha"]
            },
            "volume": {
                "metric": ["мм³", "см³", "м³", "л"],
                "imperial": ["дюйм³", "фут³", "галлон"],
                "si": ["m³", "mm³", "cm³", "l"]
            },
            "angle": {
                "metric": ["°", "град", "рад"],
                "si": ["°", "rad"]
            },
            "temperature": {
                "metric": ["°C", "°F", "K"],
                "si": ["K", "°C"]
            },
            "mass": {
                "metric": ["г", "кг", "т"],
                "imperial": ["унция", "фунт", "тонна"],
                "si": ["g", "kg", "t"]
            },
            "force": {
                "metric": ["Н", "кН", "МН"],
                "imperial": ["фунт-сила", "kip"],
                "si": ["N", "kN", "MN"]
            },
            "pressure": {
                "metric": ["Па", "кПа", "МПа", "атм"],
                "imperial": ["psi", "psf"],
                "si": ["Pa", "kPa", "MPa"]
            }
        }
    
    def _load_conversion_factors(self) -> Dict[str, Dict[str, float]]:
        """Загрузка коэффициентов пересчета единиц"""
        return {
            "length": {
                "mm_to_m": 0.001,
                "cm_to_m": 0.01,
                "km_to_m": 1000,
                "inch_to_m": 0.0254,
                "foot_to_m": 0.3048
            },
            "area": {
                "mm2_to_m2": 0.000001,
                "cm2_to_m2": 0.0001,
                "ha_to_m2": 10000
            },
            "volume": {
                "mm3_to_m3": 0.000000001,
                "cm3_to_m3": 0.000001,
                "l_to_m3": 0.001
            },
            "angle": {
                "deg_to_rad": 0.0174533,
                "grad_to_rad": 0.015708
            },
            "temperature": {
                "c_to_k": 273.15,
                "f_to_c": lambda f: (f - 32) * 5/9
            }
        }
    
    def validate_units(self, units_info: Optional[UnitsInfo]) -> List[ValidationIssue]:
        """Основная валидация единиц измерений"""
        issues = []
        
        if not units_info:
            issues.append(ValidationIssue(
                id="missing_units_info",
                category="units",
                severity=IssueSeverity.MEDIUM,
                title="Отсутствует информация о единицах измерений",
                description="Не удалось определить единицы измерений в документе",
                recommendation="Проверить наличие размеров и единиц измерений в документе"
            ))
            return issues
        
        # Валидация единиц длины
        length_issues = self._validate_length_units(units_info.length_unit)
        issues.extend(length_issues)
        
        # Валидация единиц площади
        area_issues = self._validate_area_units(units_info.area_unit)
        issues.extend(area_issues)
        
        # Валидация единиц объема
        volume_issues = self._validate_volume_units(units_info.volume_unit)
        issues.extend(volume_issues)
        
        # Валидация единиц углов
        angle_issues = self._validate_angle_units(units_info.angle_unit)
        issues.extend(angle_issues)
        
        # Валидация единиц температуры
        temperature_issues = self._validate_temperature_units(units_info.temperature_unit)
        issues.extend(temperature_issues)
        
        # Валидация метрической системы
        metric_issues = self._validate_metric_system(units_info)
        issues.extend(metric_issues)
        
        # Валидация стандартности единиц
        standard_issues = self._validate_standard_units(units_info)
        issues.extend(standard_issues)
        
        return issues
    
    def _validate_length_units(self, length_unit: str) -> List[ValidationIssue]:
        """Валидация единиц длины"""
        issues = []
        
        if not length_unit:
            issues.append(ValidationIssue(
                id="missing_length_unit",
                category="units",
                severity=IssueSeverity.HIGH,
                title="Отсутствует единица измерения длины",
                description="В документе не указана единица измерения длины",
                recommendation="Указать единицу измерения длины (мм, см, м)"
            ))
            return issues
        
        # Проверка на стандартность
        all_length_units = []
        for unit_list in self.standard_units["length"].values():
            all_length_units.extend(unit_list)
        
        if length_unit not in all_length_units:
            issues.append(ValidationIssue(
                id=f"non_standard_length_unit_{length_unit}",
                category="units",
                severity=IssueSeverity.MEDIUM,
                title=f"Нестандартная единица измерения длины: {length_unit}",
                description=f"Единица измерения длины '{length_unit}' не является стандартной",
                recommendation=f"Использовать стандартные единицы: {', '.join(self.standard_units['length']['metric'])}"
            ))
        
        # Проверка на метрическую систему
        if length_unit not in self.standard_units["length"]["metric"]:
            issues.append(ValidationIssue(
                id=f"non_metric_length_unit_{length_unit}",
                category="units",
                severity=IssueSeverity.LOW,
                title=f"Неметрическая единица измерения длины: {length_unit}",
                description=f"Единица измерения длины '{length_unit}' не является метрической",
                recommendation="Использовать метрические единицы измерения (мм, см, м)"
            ))
        
        return issues
    
    def _validate_area_units(self, area_unit: str) -> List[ValidationIssue]:
        """Валидация единиц площади"""
        issues = []
        
        if not area_unit:
            issues.append(ValidationIssue(
                id="missing_area_unit",
                category="units",
                severity=IssueSeverity.MEDIUM,
                title="Отсутствует единица измерения площади",
                description="В документе не указана единица измерения площади",
                recommendation="Указать единицу измерения площади (мм², см², м²)"
            ))
            return issues
        
        # Проверка на стандартность
        all_area_units = []
        for unit_list in self.standard_units["area"].values():
            all_area_units.extend(unit_list)
        
        if area_unit not in all_area_units:
            issues.append(ValidationIssue(
                id=f"non_standard_area_unit_{area_unit}",
                category="units",
                severity=IssueSeverity.MEDIUM,
                title=f"Нестандартная единица измерения площади: {area_unit}",
                description=f"Единица измерения площади '{area_unit}' не является стандартной",
                recommendation=f"Использовать стандартные единицы: {', '.join(self.standard_units['area']['metric'])}"
            ))
        
        return issues
    
    def _validate_volume_units(self, volume_unit: str) -> List[ValidationIssue]:
        """Валидация единиц объема"""
        issues = []
        
        if not volume_unit:
            issues.append(ValidationIssue(
                id="missing_volume_unit",
                category="units",
                severity=IssueSeverity.LOW,
                title="Отсутствует единица измерения объема",
                description="В документе не указана единица измерения объема",
                recommendation="Указать единицу измерения объема (мм³, см³, м³)"
            ))
            return issues
        
        # Проверка на стандартность
        all_volume_units = []
        for unit_list in self.standard_units["volume"].values():
            all_volume_units.extend(unit_list)
        
        if volume_unit not in all_volume_units:
            issues.append(ValidationIssue(
                id=f"non_standard_volume_unit_{volume_unit}",
                category="units",
                severity=IssueSeverity.LOW,
                title=f"Нестандартная единица измерения объема: {volume_unit}",
                description=f"Единица измерения объема '{volume_unit}' не является стандартной",
                recommendation=f"Использовать стандартные единицы: {', '.join(self.standard_units['volume']['metric'])}"
            ))
        
        return issues
    
    def _validate_angle_units(self, angle_unit: str) -> List[ValidationIssue]:
        """Валидация единиц углов"""
        issues = []
        
        if not angle_unit:
            issues.append(ValidationIssue(
                id="missing_angle_unit",
                category="units",
                severity=IssueSeverity.LOW,
                title="Отсутствует единица измерения углов",
                description="В документе не указана единица измерения углов",
                recommendation="Указать единицу измерения углов (°, град, рад)"
            ))
            return issues
        
        # Проверка на стандартность
        all_angle_units = []
        for unit_list in self.standard_units["angle"].values():
            all_angle_units.extend(unit_list)
        
        if angle_unit not in all_angle_units:
            issues.append(ValidationIssue(
                id=f"non_standard_angle_unit_{angle_unit}",
                category="units",
                severity=IssueSeverity.LOW,
                title=f"Нестандартная единица измерения углов: {angle_unit}",
                description=f"Единица измерения углов '{angle_unit}' не является стандартной",
                recommendation=f"Использовать стандартные единицы: {', '.join(self.standard_units['angle']['metric'])}"
            ))
        
        return issues
    
    def _validate_temperature_units(self, temperature_unit: str) -> List[ValidationIssue]:
        """Валидация единиц температуры"""
        issues = []
        
        if not temperature_unit:
            issues.append(ValidationIssue(
                id="missing_temperature_unit",
                category="units",
                severity=IssueSeverity.LOW,
                title="Отсутствует единица измерения температуры",
                description="В документе не указана единица измерения температуры",
                recommendation="Указать единицу измерения температуры (°C, °F, K)"
            ))
            return issues
        
        # Проверка на стандартность
        all_temperature_units = []
        for unit_list in self.standard_units["temperature"].values():
            all_temperature_units.extend(unit_list)
        
        if temperature_unit not in all_temperature_units:
            issues.append(ValidationIssue(
                id=f"non_standard_temperature_unit_{temperature_unit}",
                category="units",
                severity=IssueSeverity.LOW,
                title=f"Нестандартная единица измерения температуры: {temperature_unit}",
                description=f"Единица измерения температуры '{temperature_unit}' не является стандартной",
                recommendation=f"Использовать стандартные единицы: {', '.join(self.standard_units['temperature']['metric'])}"
            ))
        
        return issues
    
    def _validate_metric_system(self, units_info: UnitsInfo) -> List[ValidationIssue]:
        """Валидация использования метрической системы"""
        issues = []
        
        if not units_info.is_metric:
            issues.append(ValidationIssue(
                id="non_metric_system",
                category="units",
                severity=IssueSeverity.MEDIUM,
                title="Использование неметрической системы единиц",
                description="В документе используются неметрические единицы измерений",
                recommendation="Перевести все единицы измерений в метрическую систему"
            ))
        
        return issues
    
    def _validate_standard_units(self, units_info: UnitsInfo) -> List[ValidationIssue]:
        """Валидация стандартности единиц"""
        issues = []
        
        if not units_info.is_standard:
            issues.append(ValidationIssue(
                id="non_standard_units",
                category="units",
                severity=IssueSeverity.LOW,
                title="Использование нестандартных единиц измерений",
                description="В документе используются нестандартные единицы измерений",
                recommendation="Использовать стандартные единицы измерений согласно ГОСТ"
            ))
        
        return issues
    
    def validate_units_consistency(self, units_list: List[UnitsInfo]) -> List[ValidationIssue]:
        """Валидация согласованности единиц измерений"""
        issues = []
        
        if len(units_list) < 2:
            return issues
        
        # Проверка согласованности единиц длины
        length_units = [u.length_unit for u in units_list if u.length_unit]
        if len(set(length_units)) > 1:
            issues.append(ValidationIssue(
                id="inconsistent_length_units",
                category="units_consistency",
                severity=IssueSeverity.HIGH,
                title="Несогласованные единицы измерения длины",
                description=f"В документе используются разные единицы измерения длины: {', '.join(set(length_units))}",
                recommendation="Привести все единицы измерения длины к единому значению"
            ))
        
        # Проверка согласованности единиц площади
        area_units = [u.area_unit for u in units_list if u.area_unit]
        if len(set(area_units)) > 1:
            issues.append(ValidationIssue(
                id="inconsistent_area_units",
                category="units_consistency",
                severity=IssueSeverity.MEDIUM,
                title="Несогласованные единицы измерения площади",
                description=f"В документе используются разные единицы измерения площади: {', '.join(set(area_units))}",
                recommendation="Привести все единицы измерения площади к единому значению"
            ))
        
        # Проверка согласованности метрической системы
        metric_systems = [u.is_metric for u in units_list]
        if len(set(metric_systems)) > 1:
            issues.append(ValidationIssue(
                id="inconsistent_metric_system",
                category="units_consistency",
                severity=IssueSeverity.HIGH,
                title="Несогласованное использование метрической системы",
                description="В документе одновременно используются метрические и неметрические единицы",
                recommendation="Привести все единицы измерений к метрической системе"
            ))
        
        return issues
