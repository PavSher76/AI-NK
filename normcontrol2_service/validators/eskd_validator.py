"""
Валидатор соответствия ЕСКД (Единая система конструкторской документации)
"""

import logging
import re
from typing import Dict, Any, List, Optional
from ..models import ValidationIssue, IssueSeverity, TitleBlockInfo, FontInfo, ScaleInfo

logger = logging.getLogger(__name__)


class ESKDValidator:
    """Валидатор соответствия требованиям ЕСКД"""
    
    def __init__(self):
        self.eskd_requirements = self._load_eskd_requirements()
        self.standard_scales = self._load_standard_scales()
        self.standard_fonts = self._load_standard_fonts()
    
    def _load_eskd_requirements(self) -> Dict[str, Any]:
        """Загрузка требований ЕСКД"""
        return {
            "gost_21_501_2018": {
                "name": "ГОСТ 21.501-2018 Правила выполнения архитектурно-строительных чертежей",
                "requirements": {
                    "title_block": {
                        "required_fields": [
                            "project_name", "project_number", "document_name", 
                            "document_number", "scale", "sheet_number", "total_sheets",
                            "designer", "checker", "approver", "date"
                        ],
                        "position": {"x": 0, "y": 0, "width": 185, "height": 55},
                        "font_size": 3.5
                    },
                    "drawing_elements": {
                        "line_types": ["solid", "dashed", "dash_dot", "dotted"],
                        "line_weights": [0.13, 0.18, 0.25, 0.35, 0.5, 0.7, 1.0, 1.4, 2.0],
                        "dimension_style": "iso"
                    },
                    "text_requirements": {
                        "font_family": "Arial",
                        "min_size": 2.5,
                        "max_size": 14.0,
                        "standard_sizes": [2.5, 3.5, 5.0, 7.0, 10.0, 14.0]
                    }
                }
            },
            "gost_r_21_101_2020": {
                "name": "ГОСТ Р 21.101-2020 Система проектной документации для строительства",
                "requirements": {
                    "document_structure": {
                        "title_page": True,
                        "general_data": True,
                        "working_drawings": True,
                        "specifications": True
                    },
                    "naming_convention": {
                        "pattern": r"^\d{4}-\d{5}-\w{2}-\d{2}-\d{3}-\d{3}-\w{2}_\d+_\d+_\w+",
                        "marks": ["АР", "КЖ", "КМ", "ОВ", "ВК", "ЭО", "СС", "АС", "ТХ", "ПЗ"]
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
    
    def _load_standard_fonts(self) -> List[str]:
        """Загрузка стандартных шрифтов"""
        return ["Arial", "Times New Roman", "Calibri", "Tahoma", "Verdana"]
    
    def validate_document(self, document_data: Dict[str, Any]) -> List[ValidationIssue]:
        """Основная валидация документа на соответствие ЕСКД"""
        issues = []
        
        # Валидация основной надписи
        title_block_issues = self._validate_title_block(document_data.get("title_block"))
        issues.extend(title_block_issues)
        
        # Валидация масштабов
        scales_issues = self._validate_scales(document_data.get("scales", []))
        issues.extend(scales_issues)
        
        # Валидация шрифтов
        fonts_issues = self._validate_fonts(document_data.get("fonts", []))
        issues.extend(fonts_issues)
        
        # Валидация линий и размеров
        drawing_issues = self._validate_drawing_elements(document_data.get("drawing_elements", []))
        issues.extend(drawing_issues)
        
        # Валидация структуры документа
        structure_issues = self._validate_document_structure(document_data)
        issues.extend(structure_issues)
        
        return issues
    
    def _validate_title_block(self, title_block: Optional[TitleBlockInfo]) -> List[ValidationIssue]:
        """Валидация основной надписи"""
        issues = []
        
        if not title_block:
            issues.append(ValidationIssue(
                id="missing_title_block",
                category="title_block",
                severity=IssueSeverity.CRITICAL,
                title="Отсутствует основная надпись",
                description="Документ не содержит основную надпись согласно ГОСТ 21.501-2018",
                recommendation="Добавить основную надпись в правом нижнем углу листа"
            ))
            return issues
        
        if not title_block.has_title_block:
            issues.append(ValidationIssue(
                id="no_title_block",
                category="title_block",
                severity=IssueSeverity.CRITICAL,
                title="Основная надпись не обнаружена",
                description="Не удалось распознать основную надпись на документе",
                recommendation="Проверить наличие и правильность оформления основной надписи"
            ))
            return issues
        
        # Проверка обязательных полей
        required_fields = self.eskd_requirements["gost_21_501_2018"]["requirements"]["title_block"]["required_fields"]
        for field in required_fields:
            if not getattr(title_block, field, None):
                issues.append(ValidationIssue(
                    id=f"missing_{field}",
                    category="title_block",
                    severity=IssueSeverity.HIGH,
                    title=f"Отсутствует поле '{field}' в основной надписи",
                    description=f"В основной надписи не указано поле '{field}'",
                    recommendation=f"Заполнить поле '{field}' в основной надписи"
                ))
        
        # Проверка позиции основной надписи
        if title_block.position:
            expected_pos = self.eskd_requirements["gost_21_501_2018"]["requirements"]["title_block"]["position"]
            if (title_block.position["x"] < expected_pos["x"] - 10 or 
                title_block.position["x"] > expected_pos["x"] + 10):
                issues.append(ValidationIssue(
                    id="incorrect_title_block_position_x",
                    category="title_block",
                    severity=IssueSeverity.MEDIUM,
                    title="Неправильное расположение основной надписи по X",
                    description=f"Основная надпись расположена на X={title_block.position['x']}, ожидается {expected_pos['x']}",
                    recommendation="Переместить основную надпись в правый нижний угол"
                ))
        
        return issues
    
    def _validate_scales(self, scales: List[ScaleInfo]) -> List[ValidationIssue]:
        """Валидация масштабов"""
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
        
        for scale in scales:
            if not scale.is_standard:
                issues.append(ValidationIssue(
                    id=f"non_standard_scale_{scale.value}",
                    category="scales",
                    severity=IssueSeverity.MEDIUM,
                    title=f"Нестандартный масштаб: {scale.value}",
                    description=f"Масштаб {scale.value} не является стандартным",
                    recommendation=f"Использовать стандартный масштаб из ряда: {', '.join(self.standard_scales[:10])}"
                ))
            
            if scale.type not in ["numerical", "graphical"]:
                issues.append(ValidationIssue(
                    id=f"incorrect_scale_type_{scale.value}",
                    category="scales",
                    severity=IssueSeverity.LOW,
                    title=f"Неправильный тип масштаба: {scale.value}",
                    description=f"Масштаб {scale.value} должен быть численным или графическим",
                    recommendation="Указать масштаб в численном или графическом виде"
                ))
        
        return issues
    
    def _validate_fonts(self, fonts: List[FontInfo]) -> List[ValidationIssue]:
        """Валидация шрифтов"""
        issues = []
        
        if not fonts:
            issues.append(ValidationIssue(
                id="no_fonts",
                category="fonts",
                severity=IssueSeverity.MEDIUM,
                title="Не удалось определить шрифты",
                description="В документе не удалось распознать шрифты",
                recommendation="Проверить качество документа и наличие текста"
            ))
            return issues
        
        for font in fonts:
            # Проверка стандартности шрифта
            if font.family not in self.standard_fonts:
                issues.append(ValidationIssue(
                    id=f"non_standard_font_{font.family}",
                    category="fonts",
                    severity=IssueSeverity.LOW,
                    title=f"Нестандартный шрифт: {font.family}",
                    description=f"Шрифт {font.family} не рекомендуется для технических документов",
                    recommendation=f"Использовать стандартные шрифты: {', '.join(self.standard_fonts)}"
                ))
            
            # Проверка размера шрифта
            standard_sizes = self.eskd_requirements["gost_21_501_2018"]["requirements"]["text_requirements"]["standard_sizes"]
            if font.size not in standard_sizes:
                closest_size = min(standard_sizes, key=lambda x: abs(x - font.size))
                issues.append(ValidationIssue(
                    id=f"non_standard_font_size_{font.size}",
                    category="fonts",
                    severity=IssueSeverity.LOW,
                    title=f"Нестандартный размер шрифта: {font.size}",
                    description=f"Размер шрифта {font.size} не является стандартным",
                    recommendation=f"Использовать стандартный размер: {closest_size}"
                ))
            
            # Проверка минимального размера
            min_size = self.eskd_requirements["gost_21_501_2018"]["requirements"]["text_requirements"]["min_size"]
            if font.size < min_size:
                issues.append(ValidationIssue(
                    id=f"too_small_font_{font.size}",
                    category="fonts",
                    severity=IssueSeverity.MEDIUM,
                    title=f"Слишком мелкий шрифт: {font.size}",
                    description=f"Размер шрифта {font.size} меньше минимального {min_size}",
                    recommendation=f"Увеличить размер шрифта до {min_size} или больше"
                ))
        
        return issues
    
    def _validate_drawing_elements(self, drawing_elements: List[Dict[str, Any]]) -> List[ValidationIssue]:
        """Валидация чертежных элементов"""
        issues = []
        
        if not drawing_elements:
            issues.append(ValidationIssue(
                id="no_drawing_elements",
                category="drawing_elements",
                severity=IssueSeverity.MEDIUM,
                title="Отсутствуют чертежные элементы",
                description="В документе не обнаружены чертежные элементы",
                recommendation="Добавить чертежи, размеры и условные обозначения"
            ))
            return issues
        
        # Проверка типов линий
        standard_line_types = self.eskd_requirements["gost_21_501_2018"]["requirements"]["drawing_elements"]["line_types"]
        for element in drawing_elements:
            if "line_type" in element and element["line_type"] not in standard_line_types:
                issues.append(ValidationIssue(
                    id=f"non_standard_line_type_{element['line_type']}",
                    category="drawing_elements",
                    severity=IssueSeverity.LOW,
                    title=f"Нестандартный тип линии: {element['line_type']}",
                    description=f"Тип линии {element['line_type']} не соответствует стандарту",
                    recommendation=f"Использовать стандартные типы линий: {', '.join(standard_line_types)}"
                ))
        
        return issues
    
    def _validate_document_structure(self, document_data: Dict[str, Any]) -> List[ValidationIssue]:
        """Валидация структуры документа"""
        issues = []
        
        # Проверка соответствия имени файла стандарту
        filename = document_data.get("filename", "")
        naming_pattern = self.eskd_requirements["gost_r_21_101_2020"]["requirements"]["naming_convention"]["pattern"]
        
        if not re.match(naming_pattern, filename):
            issues.append(ValidationIssue(
                id="incorrect_filename_format",
                category="document_structure",
                severity=IssueSeverity.MEDIUM,
                title="Неправильный формат имени файла",
                description=f"Имя файла '{filename}' не соответствует стандарту ГОСТ Р 21.101-2020",
                recommendation="Переименовать файл согласно стандарту: XXXX-XXXXX-XX-XX-XXX-XXX-XX_X_X_XX"
            ))
        
        # Проверка наличия обязательных разделов
        required_sections = self.eskd_requirements["gost_r_21_101_2020"]["requirements"]["document_structure"]
        for section, required in required_sections.items():
            if required and not document_data.get(section, False):
                issues.append(ValidationIssue(
                    id=f"missing_{section}",
                    category="document_structure",
                    severity=IssueSeverity.HIGH,
                    title=f"Отсутствует раздел: {section}",
                    description=f"В документе отсутствует обязательный раздел '{section}'",
                    recommendation=f"Добавить раздел '{section}' согласно ГОСТ Р 21.101-2020"
                ))
        
        return issues
