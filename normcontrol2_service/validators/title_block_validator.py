"""
Валидатор основной надписи и спецификаций
"""

import logging
import re
from typing import Dict, Any, List, Optional
from ..models import ValidationIssue, IssueSeverity, TitleBlockInfo

logger = logging.getLogger(__name__)


class TitleBlockValidator:
    """Валидатор основной надписи и спецификаций"""
    
    def __init__(self):
        self.title_block_requirements = self._load_title_block_requirements()
        self.specification_requirements = self._load_specification_requirements()
    
    def _load_title_block_requirements(self) -> Dict[str, Any]:
        """Загрузка требований к основной надписи"""
        return {
            "gost_21_501_2018": {
                "name": "ГОСТ 21.501-2018 Правила выполнения архитектурно-строительных чертежей",
                "requirements": {
                    "position": {
                        "x_min": 0, "x_max": 10,
                        "y_min": 0, "y_max": 10,
                        "width": 185, "height": 55
                    },
                    "required_fields": {
                        "project_name": {"required": True, "max_length": 50},
                        "project_number": {"required": True, "pattern": r"^\d{4}-\d{5}$"},
                        "document_name": {"required": True, "max_length": 100},
                        "document_number": {"required": True, "pattern": r"^\d{3}-\d{3}$"},
                        "scale": {"required": True, "pattern": r"^\d+:\d+$"},
                        "sheet_number": {"required": True, "pattern": r"^\d+$"},
                        "total_sheets": {"required": True, "pattern": r"^\d+$"},
                        "designer": {"required": True, "max_length": 30},
                        "checker": {"required": True, "max_length": 30},
                        "approver": {"required": True, "max_length": 30},
                        "date": {"required": True, "pattern": r"^\d{2}\.\d{2}\.\d{4}$"}
                    },
                    "font_requirements": {
                        "family": "Arial",
                        "size": 3.5,
                        "weight": "normal"
                    }
                }
            }
        }
    
    def _load_specification_requirements(self) -> Dict[str, Any]:
        """Загрузка требований к спецификациям"""
        return {
            "gost_21_101_2020": {
                "name": "ГОСТ Р 21.101-2020 Система проектной документации",
                "requirements": {
                    "specification_structure": {
                        "header": True,
                        "item_number": True,
                        "designation": True,
                        "name": True,
                        "quantity": True,
                        "mass": True,
                        "note": True
                    },
                    "formatting": {
                        "table_format": True,
                        "borders": True,
                        "alignment": "left",
                        "font_size": 3.5
                    }
                }
            }
        }
    
    def validate_title_block(self, title_block: Optional[TitleBlockInfo]) -> List[ValidationIssue]:
        """Валидация основной надписи"""
        issues = []
        
        if not title_block:
            issues.append(ValidationIssue(
                id="missing_title_block",
                category="title_block",
                severity=IssueSeverity.CRITICAL,
                title="Отсутствует основная надпись",
                description="Документ не содержит основную надпись",
                recommendation="Добавить основную надпись согласно ГОСТ 21.501-2018"
            ))
            return issues
        
        if not title_block.has_title_block:
            issues.append(ValidationIssue(
                id="no_title_block_detected",
                category="title_block",
                severity=IssueSeverity.CRITICAL,
                title="Основная надпись не обнаружена",
                description="Не удалось распознать основную надпись на документе",
                recommendation="Проверить наличие и правильность оформления основной надписи"
            ))
            return issues
        
        # Валидация обязательных полей
        field_issues = self._validate_required_fields(title_block)
        issues.extend(field_issues)
        
        # Валидация форматов полей
        format_issues = self._validate_field_formats(title_block)
        issues.extend(format_issues)
        
        # Валидация позиции и размера
        position_issues = self._validate_position_and_size(title_block)
        issues.extend(position_issues)
        
        return issues
    
    def _validate_required_fields(self, title_block: TitleBlockInfo) -> List[ValidationIssue]:
        """Валидация обязательных полей"""
        issues = []
        
        required_fields = self.title_block_requirements["gost_21_501_2018"]["requirements"]["required_fields"]
        
        for field_name, field_config in required_fields.items():
            if field_config["required"]:
                field_value = getattr(title_block, field_name, None)
                if not field_value:
                    issues.append(ValidationIssue(
                        id=f"missing_required_field_{field_name}",
                        category="title_block",
                        severity=IssueSeverity.HIGH,
                        title=f"Отсутствует обязательное поле: {field_name}",
                        description=f"В основной надписи не указано поле '{field_name}'",
                        recommendation=f"Заполнить поле '{field_name}' в основной надписи"
                    ))
        
        return issues
    
    def _validate_field_formats(self, title_block: TitleBlockInfo) -> List[ValidationIssue]:
        """Валидация форматов полей"""
        issues = []
        
        required_fields = self.title_block_requirements["gost_21_501_2018"]["requirements"]["required_fields"]
        
        for field_name, field_config in required_fields.items():
            field_value = getattr(title_block, field_name, None)
            if not field_value:
                continue
            
            # Проверка максимальной длины
            if "max_length" in field_config:
                if len(str(field_value)) > field_config["max_length"]:
                    issues.append(ValidationIssue(
                        id=f"field_too_long_{field_name}",
                        category="title_block",
                        severity=IssueSeverity.MEDIUM,
                        title=f"Поле '{field_name}' слишком длинное",
                        description=f"Поле '{field_name}' превышает максимальную длину {field_config['max_length']} символов",
                        recommendation=f"Сократить поле '{field_name}' до {field_config['max_length']} символов"
                    ))
            
            # Проверка формата по регулярному выражению
            if "pattern" in field_config:
                if not re.match(field_config["pattern"], str(field_value)):
                    issues.append(ValidationIssue(
                        id=f"field_format_incorrect_{field_name}",
                        category="title_block",
                        severity=IssueSeverity.HIGH,
                        title=f"Неправильный формат поля: {field_name}",
                        description=f"Поле '{field_name}' не соответствует требуемому формату",
                        recommendation=f"Исправить формат поля '{field_name}' согласно ГОСТ 21.501-2018"
                    ))
        
        return issues
    
    def _validate_position_and_size(self, title_block: TitleBlockInfo) -> List[ValidationIssue]:
        """Валидация позиции и размера основной надписи"""
        issues = []
        
        if not title_block.position or not title_block.size:
            issues.append(ValidationIssue(
                id="missing_title_block_dimensions",
                category="title_block",
                severity=IssueSeverity.MEDIUM,
                title="Отсутствует информация о размерах основной надписи",
                description="Не удалось определить позицию и размер основной надписи",
                recommendation="Проверить правильность оформления основной надписи"
            ))
            return issues
        
        # Проверка позиции
        position_req = self.title_block_requirements["gost_21_501_2018"]["requirements"]["position"]
        
        if (title_block.position["x"] < position_req["x_min"] or 
            title_block.position["x"] > position_req["x_max"]):
            issues.append(ValidationIssue(
                id="incorrect_title_block_x_position",
                category="title_block",
                severity=IssueSeverity.MEDIUM,
                title="Неправильная позиция основной надписи по X",
                description=f"Основная надпись расположена на X={title_block.position['x']}, ожидается {position_req['x_min']}-{position_req['x_max']}",
                recommendation="Переместить основную надпись в правый нижний угол"
            ))
        
        if (title_block.position["y"] < position_req["y_min"] or 
            title_block.position["y"] > position_req["y_max"]):
            issues.append(ValidationIssue(
                id="incorrect_title_block_y_position",
                category="title_block",
                severity=IssueSeverity.MEDIUM,
                title="Неправильная позиция основной надписи по Y",
                description=f"Основная надпись расположена на Y={title_block.position['y']}, ожидается {position_req['y_min']}-{position_req['y_max']}",
                recommendation="Переместить основную надпись в правый нижний угол"
            ))
        
        # Проверка размера
        if (abs(title_block.size["width"] - position_req["width"]) > 5 or 
            abs(title_block.size["height"] - position_req["height"]) > 5):
            issues.append(ValidationIssue(
                id="incorrect_title_block_size",
                category="title_block",
                severity=IssueSeverity.LOW,
                title="Неправильный размер основной надписи",
                description=f"Размер основной надписи {title_block.size['width']}x{title_block.size['height']} не соответствует стандарту {position_req['width']}x{position_req['height']}",
                recommendation="Исправить размер основной надписи согласно ГОСТ 21.501-2018"
            ))
        
        return issues
    
    def validate_specifications(self, specifications: List[Dict[str, Any]]) -> List[ValidationIssue]:
        """Валидация спецификаций"""
        issues = []
        
        if not specifications:
            issues.append(ValidationIssue(
                id="no_specifications",
                category="specifications",
                severity=IssueSeverity.MEDIUM,
                title="Отсутствуют спецификации",
                description="В документе не обнаружены спецификации",
                recommendation="Добавить спецификации согласно ГОСТ Р 21.101-2020"
            ))
            return issues
        
        for i, spec in enumerate(specifications):
            spec_issues = self._validate_single_specification(spec, i)
            issues.extend(spec_issues)
        
        return issues
    
    def _validate_single_specification(self, spec: Dict[str, Any], index: int) -> List[ValidationIssue]:
        """Валидация одной спецификации"""
        issues = []
        
        required_fields = self.specification_requirements["gost_21_101_2020"]["requirements"]["specification_structure"]
        
        for field_name, required in required_fields.items():
            if required and not spec.get(field_name):
                issues.append(ValidationIssue(
                    id=f"missing_spec_field_{field_name}_{index}",
                    category="specifications",
                    severity=IssueSeverity.HIGH,
                    title=f"Отсутствует поле '{field_name}' в спецификации {index + 1}",
                    description=f"В спецификации {index + 1} отсутствует обязательное поле '{field_name}'",
                    recommendation=f"Заполнить поле '{field_name}' в спецификации {index + 1}"
                ))
        
        # Проверка формата таблицы
        if not spec.get("is_table_format", False):
            issues.append(ValidationIssue(
                id=f"incorrect_spec_format_{index}",
                category="specifications",
                severity=IssueSeverity.MEDIUM,
                title=f"Неправильный формат спецификации {index + 1}",
                description=f"Спецификация {index + 1} должна быть оформлена в виде таблицы",
                recommendation="Оформить спецификацию в виде таблицы согласно ГОСТ Р 21.101-2020"
            ))
        
        return issues
    
    def validate_title_block_consistency(self, title_blocks: List[TitleBlockInfo]) -> List[ValidationIssue]:
        """Валидация согласованности основной надписи между листами"""
        issues = []
        
        if len(title_blocks) < 2:
            return issues
        
        # Проверка согласованности номера проекта
        project_numbers = [tb.project_number for tb in title_blocks if tb.project_number]
        if len(set(project_numbers)) > 1:
            issues.append(ValidationIssue(
                id="inconsistent_project_numbers",
                category="title_block_consistency",
                severity=IssueSeverity.HIGH,
                title="Несогласованные номера проекта",
                description="В основной надписи разных листов указаны разные номера проекта",
                recommendation="Привести номера проекта к единому значению"
            ))
        
        # Проверка согласованности названия проекта
        project_names = [tb.project_name for tb in title_blocks if tb.project_name]
        if len(set(project_names)) > 1:
            issues.append(ValidationIssue(
                id="inconsistent_project_names",
                category="title_block_consistency",
                severity=IssueSeverity.HIGH,
                title="Несогласованные названия проекта",
                description="В основной надписи разных листов указаны разные названия проекта",
                recommendation="Привести названия проекта к единому значению"
            ))
        
        # Проверка согласованности общего количества листов
        total_sheets = [tb.total_sheets for tb in title_blocks if tb.total_sheets]
        if len(set(total_sheets)) > 1:
            issues.append(ValidationIssue(
                id="inconsistent_total_sheets",
                category="title_block_consistency",
                severity=IssueSeverity.MEDIUM,
                title="Несогласованное общее количество листов",
                description="В основной надписи разных листов указано разное общее количество листов",
                recommendation="Привести общее количество листов к единому значению"
            ))
        
        return issues
