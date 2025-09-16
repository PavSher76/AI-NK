"""
Валидатор обозначений
"""

import logging
import re
from typing import Dict, Any, List, Optional
from ..models import ValidationIssue, IssueSeverity, NotationInfo

logger = logging.getLogger(__name__)


class NotationsValidator:
    """Валидатор обозначений"""
    
    def __init__(self):
        self.notation_requirements = self._load_notation_requirements()
        self.standard_symbols = self._load_standard_symbols()
        self.standard_abbreviations = self._load_standard_abbreviations()
    
    def _load_notation_requirements(self) -> Dict[str, Any]:
        """Загрузка требований к обозначениям"""
        return {
            "gost_21_501_2018": {
                "name": "ГОСТ 21.501-2018 Правила выполнения архитектурно-строительных чертежей",
                "requirements": {
                    "symbols": {
                        "diameter": "Ø",
                        "radius": "R",
                        "square": "□",
                        "angle": "∠",
                        "parallel": "∥",
                        "perpendicular": "⊥",
                        "plus_minus": "±",
                        "degree": "°"
                    },
                    "abbreviations": {
                        "millimeter": "мм",
                        "centimeter": "см",
                        "meter": "м",
                        "kilometer": "км",
                        "square_meter": "м²",
                        "cubic_meter": "м³",
                        "degree": "°",
                        "minute": "'",
                        "second": "\""
                    }
                }
            },
            "gost_r_21_101_2020": {
                "name": "ГОСТ Р 21.101-2020 Система проектной документации",
                "requirements": {
                    "references": {
                        "gost_reference": r"ГОСТ\s+\d+\.\d+-\d+",
                        "sp_reference": r"СП\s+\d+\.\d+\.\d+",
                        "snip_reference": r"СНиП\s+\d+\.\d+\.\d+",
                        "section_reference": r"п\.\s*\d+",
                        "figure_reference": r"рис\.\s*\d+",
                        "table_reference": r"табл\.\s*\d+"
                    }
                }
            }
        }
    
    def _load_standard_symbols(self) -> List[str]:
        """Загрузка стандартных символов"""
        return [
            "Ø", "R", "□", "∠", "∥", "⊥", "±", "°", "×", "÷", "≈", "≠", "≤", "≥", 
            "∞", "∑", "∏", "√", "∆", "∇", "∂", "∫", "∮", "∝", "≡", "≅", "∼", "≈"
        ]
    
    def _load_standard_abbreviations(self) -> List[str]:
        """Загрузка стандартных сокращений"""
        return [
            "мм", "см", "м", "км", "м²", "м³", "°", "'", "\"", "кг", "т", "г",
            "Н", "кН", "МН", "Па", "кПа", "МПа", "Вт", "кВт", "МВт", "А", "В", "Ом"
        ]
    
    def validate_notations(self, notation_info: Optional[NotationInfo]) -> List[ValidationIssue]:
        """Основная валидация обозначений"""
        issues = []
        
        if not notation_info:
            issues.append(ValidationIssue(
                id="missing_notation_info",
                category="notations",
                severity=IssueSeverity.MEDIUM,
                title="Отсутствует информация об обозначениях",
                description="Не удалось определить обозначения в документе",
                recommendation="Проверить наличие символов, сокращений и ссылок в документе"
            ))
            return issues
        
        # Валидация символов
        symbols_issues = self._validate_symbols(notation_info.symbols)
        issues.extend(symbols_issues)
        
        # Валидация сокращений
        abbreviations_issues = self._validate_abbreviations(notation_info.abbreviations)
        issues.extend(abbreviations_issues)
        
        # Валидация ссылок
        references_issues = self._validate_references(notation_info.references)
        issues.extend(references_issues)
        
        # Валидация стандартности
        standard_issues = self._validate_standard_notations(notation_info)
        issues.extend(standard_issues)
        
        return issues
    
    def _validate_symbols(self, symbols: List[str]) -> List[ValidationIssue]:
        """Валидация символов"""
        issues = []
        
        if not symbols:
            issues.append(ValidationIssue(
                id="no_symbols",
                category="notations",
                severity=IssueSeverity.LOW,
                title="Отсутствуют символы",
                description="В документе не обнаружены специальные символы",
                recommendation="Добавить необходимые символы для размеров и обозначений"
            ))
            return issues
        
        for i, symbol in enumerate(symbols):
            symbol_issues = self._validate_single_symbol(symbol, i)
            issues.extend(symbol_issues)
        
        return issues
    
    def _validate_single_symbol(self, symbol: str, index: int) -> List[ValidationIssue]:
        """Валидация одного символа"""
        issues = []
        
        if not symbol:
            return issues
        
        # Проверка на стандартность
        if symbol not in self.standard_symbols:
            issues.append(ValidationIssue(
                id=f"non_standard_symbol_{symbol}_{index}",
                category="notations",
                severity=IssueSeverity.LOW,
                title=f"Нестандартный символ: {symbol}",
                description=f"Символ '{symbol}' не является стандартным для технических документов",
                recommendation=f"Использовать стандартные символы: {', '.join(self.standard_symbols[:10])}"
            ))
        
        # Проверка на соответствие ГОСТ
        gost_symbols = list(self.notation_requirements["gost_21_501_2018"]["requirements"]["symbols"].values())
        if symbol not in gost_symbols:
            issues.append(ValidationIssue(
                id=f"non_gost_symbol_{symbol}_{index}",
                category="notations",
                severity=IssueSeverity.MEDIUM,
                title=f"Символ не соответствует ГОСТ: {symbol}",
                description=f"Символ '{symbol}' не указан в ГОСТ 21.501-2018",
                recommendation=f"Использовать символы согласно ГОСТ: {', '.join(gost_symbols)}"
            ))
        
        return issues
    
    def _validate_abbreviations(self, abbreviations: List[str]) -> List[ValidationIssue]:
        """Валидация сокращений"""
        issues = []
        
        if not abbreviations:
            issues.append(ValidationIssue(
                id="no_abbreviations",
                category="notations",
                severity=IssueSeverity.LOW,
                title="Отсутствуют сокращения",
                description="В документе не обнаружены сокращения единиц измерений",
                recommendation="Добавить сокращения единиц измерений"
            ))
            return issues
        
        for i, abbreviation in enumerate(abbreviations):
            abbrev_issues = self._validate_single_abbreviation(abbreviation, i)
            issues.extend(abbrev_issues)
        
        return issues
    
    def _validate_single_abbreviation(self, abbreviation: str, index: int) -> List[ValidationIssue]:
        """Валидация одного сокращения"""
        issues = []
        
        if not abbreviation:
            return issues
        
        # Проверка на стандартность
        if abbreviation not in self.standard_abbreviations:
            issues.append(ValidationIssue(
                id=f"non_standard_abbreviation_{abbreviation}_{index}",
                category="notations",
                severity=IssueSeverity.LOW,
                title=f"Нестандартное сокращение: {abbreviation}",
                description=f"Сокращение '{abbreviation}' не является стандартным",
                recommendation=f"Использовать стандартные сокращения: {', '.join(self.standard_abbreviations[:10])}"
            ))
        
        # Проверка на соответствие ГОСТ
        gost_abbreviations = list(self.notation_requirements["gost_21_501_2018"]["requirements"]["abbreviations"].values())
        if abbreviation not in gost_abbreviations:
            issues.append(ValidationIssue(
                id=f"non_gost_abbreviation_{abbreviation}_{index}",
                category="notations",
                severity=IssueSeverity.MEDIUM,
                title=f"Сокращение не соответствует ГОСТ: {abbreviation}",
                description=f"Сокращение '{abbreviation}' не указано в ГОСТ 21.501-2018",
                recommendation=f"Использовать сокращения согласно ГОСТ: {', '.join(gost_abbreviations)}"
            ))
        
        return issues
    
    def _validate_references(self, references: List[str]) -> List[ValidationIssue]:
        """Валидация ссылок"""
        issues = []
        
        if not references:
            issues.append(ValidationIssue(
                id="no_references",
                category="notations",
                severity=IssueSeverity.LOW,
                title="Отсутствуют ссылки",
                description="В документе не обнаружены ссылки на нормативные документы",
                recommendation="Добавить ссылки на применяемые нормативные документы"
            ))
            return issues
        
        for i, reference in enumerate(references):
            ref_issues = self._validate_single_reference(reference, i)
            issues.extend(ref_issues)
        
        return issues
    
    def _validate_single_reference(self, reference: str, index: int) -> List[ValidationIssue]:
        """Валидация одной ссылки"""
        issues = []
        
        if not reference:
            return issues
        
        # Проверка формата ссылок
        reference_patterns = self.notation_requirements["gost_r_21_101_2020"]["requirements"]["references"]
        
        valid_format = False
        for pattern_name, pattern in reference_patterns.items():
            if re.search(pattern, reference, re.IGNORECASE):
                valid_format = True
                break
        
        if not valid_format:
            issues.append(ValidationIssue(
                id=f"invalid_reference_format_{reference}_{index}",
                category="notations",
                severity=IssueSeverity.MEDIUM,
                title=f"Неправильный формат ссылки: {reference}",
                description=f"Ссылка '{reference}' не соответствует стандартному формату",
                recommendation="Использовать стандартный формат ссылок (ГОСТ, СП, СНиП, п., рис., табл.)"
            ))
        
        return issues
    
    def _validate_standard_notations(self, notation_info: NotationInfo) -> List[ValidationIssue]:
        """Валидация стандартности обозначений"""
        issues = []
        
        if not notation_info.is_standard:
            issues.append(ValidationIssue(
                id="non_standard_notations",
                category="notations",
                severity=IssueSeverity.LOW,
                title="Использование нестандартных обозначений",
                description="В документе используются нестандартные обозначения",
                recommendation="Использовать стандартные обозначения согласно ГОСТ"
            ))
        
        # Проверка отсутствующих стандартных обозначений
        if notation_info.missing_standard:
            for missing in notation_info.missing_standard:
                issues.append(ValidationIssue(
                    id=f"missing_standard_notation_{missing}",
                    category="notations",
                    severity=IssueSeverity.LOW,
                    title=f"Отсутствует стандартное обозначение: {missing}",
                    description=f"В документе отсутствует стандартное обозначение '{missing}'",
                    recommendation=f"Добавить стандартное обозначение '{missing}'"
                ))
        
        return issues
    
    def validate_notation_consistency(self, notations_list: List[NotationInfo]) -> List[ValidationIssue]:
        """Валидация согласованности обозначений"""
        issues = []
        
        if len(notations_list) < 2:
            return issues
        
        # Проверка согласованности символов
        all_symbols = []
        for notation in notations_list:
            all_symbols.extend(notation.symbols)
        
        if all_symbols:
            unique_symbols = set(all_symbols)
            if len(unique_symbols) > 20:  # Слишком много разных символов
                issues.append(ValidationIssue(
                    id="too_many_different_symbols",
                    category="notations",
                    severity=IssueSeverity.LOW,
                    title="Слишком много разных символов",
                    description=f"В документе используется {len(unique_symbols)} разных символов",
                    recommendation="Унифицировать символы для лучшей читаемости"
                ))
        
        # Проверка согласованности сокращений
        all_abbreviations = []
        for notation in notations_list:
            all_abbreviations.extend(notation.abbreviations)
        
        if all_abbreviations:
            unique_abbreviations = set(all_abbreviations)
            if len(unique_abbreviations) > 15:  # Слишком много разных сокращений
                issues.append(ValidationIssue(
                    id="too_many_different_abbreviations",
                    category="notations",
                    severity=IssueSeverity.LOW,
                    title="Слишком много разных сокращений",
                    description=f"В документе используется {len(unique_abbreviations)} разных сокращений",
                    recommendation="Унифицировать сокращения для лучшей читаемости"
                ))
        
        return issues
    
    def validate_notation_completeness(self, notation_info: NotationInfo, document_type: str) -> List[ValidationIssue]:
        """Валидация полноты обозначений в зависимости от типа документа"""
        issues = []
        
        required_symbols = self._get_required_symbols_for_document_type(document_type)
        required_abbreviations = self._get_required_abbreviations_for_document_type(document_type)
        
        # Проверка наличия обязательных символов
        for required_symbol in required_symbols:
            if required_symbol not in notation_info.symbols:
                issues.append(ValidationIssue(
                    id=f"missing_required_symbol_{required_symbol}",
                    category="notations",
                    severity=IssueSeverity.MEDIUM,
                    title=f"Отсутствует обязательный символ: {required_symbol}",
                    description=f"Для типа документа '{document_type}' требуется символ '{required_symbol}'",
                    recommendation=f"Добавить символ '{required_symbol}' в документ"
                ))
        
        # Проверка наличия обязательных сокращений
        for required_abbreviation in required_abbreviations:
            if required_abbreviation not in notation_info.abbreviations:
                issues.append(ValidationIssue(
                    id=f"missing_required_abbreviation_{required_abbreviation}",
                    category="notations",
                    severity=IssueSeverity.MEDIUM,
                    title=f"Отсутствует обязательное сокращение: {required_abbreviation}",
                    description=f"Для типа документа '{document_type}' требуется сокращение '{required_abbreviation}'",
                    recommendation=f"Добавить сокращение '{required_abbreviation}' в документ"
                ))
        
        return issues
    
    def _get_required_symbols_for_document_type(self, document_type: str) -> List[str]:
        """Получение обязательных символов для типа документа"""
        requirements = {
            "architectural": ["Ø", "R", "°", "±"],
            "structural": ["Ø", "R", "°", "±", "∥", "⊥"],
            "mechanical": ["Ø", "R", "°", "±", "×"],
            "electrical": ["Ø", "°", "±", "×"],
            "general": ["Ø", "R", "°", "±"]
        }
        
        return requirements.get(document_type.lower(), requirements["general"])
    
    def _get_required_abbreviations_for_document_type(self, document_type: str) -> List[str]:
        """Получение обязательных сокращений для типа документа"""
        requirements = {
            "architectural": ["мм", "м", "м²", "°"],
            "structural": ["мм", "м", "м²", "°", "Н", "кН"],
            "mechanical": ["мм", "м", "м²", "°", "Н", "кН", "Па", "кПа"],
            "electrical": ["мм", "м", "м²", "°", "А", "В", "Вт"],
            "general": ["мм", "м", "м²", "°"]
        }
        
        return requirements.get(document_type.lower(), requirements["general"])
