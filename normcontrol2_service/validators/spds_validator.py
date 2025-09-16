"""
Валидатор соответствия СПДС (Система проектной документации для строительства)
"""

import logging
import re
from typing import Dict, Any, List, Optional
from ..models import ValidationIssue, IssueSeverity, DocumentMetadata

logger = logging.getLogger(__name__)


class SPDSValidator:
    """Валидатор соответствия требованиям СПДС"""
    
    def __init__(self):
        self.spds_requirements = self._load_spds_requirements()
        self.standard_marks = self._load_standard_marks()
        self.project_stages = self._load_project_stages()
    
    def _load_spds_requirements(self) -> Dict[str, Any]:
        """Загрузка требований СПДС"""
        return {
            "sp_48_13330_2019": {
                "name": "СП 48.13330.2019 Организация строительства",
                "requirements": {
                    "project_documentation": {
                        "stages": ["Проектная документация", "Рабочая документация"],
                        "composition": {
                            "project_documentation": [
                                "Пояснительная записка",
                                "Схема планировочной организации земельного участка",
                                "Архитектурные решения",
                                "Конструктивные и объемно-планировочные решения",
                                "Инженерно-технические мероприятия",
                                "Проект организации строительства",
                                "Проект организации работ по сносу",
                                "Мероприятия по охране окружающей среды",
                                "Мероприятия по обеспечению пожарной безопасности",
                                "Мероприятия по обеспечению доступа инвалидов",
                                "Смета на строительство объектов капитального строительства",
                                "Иная документация"
                            ],
                            "working_documentation": [
                                "Рабочие чертежи",
                                "Спецификации оборудования",
                                "Ведомости объемов работ",
                                "Локальные сметы"
                            ]
                        }
                    }
                }
            },
            "sp_70_13330_2012": {
                "name": "СП 70.13330.2012 Несущие и ограждающие конструкции",
                "requirements": {
                    "structural_drawings": {
                        "required_views": ["plans", "sections", "details"],
                        "dimensioning": True,
                        "reinforcement_drawings": True,
                        "specifications": True
                    }
                }
            },
            "sp_16_13330_2017": {
                "name": "СП 16.13330.2017 Стальные конструкции",
                "requirements": {
                    "steel_structures": {
                        "connection_details": True,
                        "welding_symbols": True,
                        "bolt_specifications": True,
                        "material_specifications": True
                    }
                }
            }
        }
    
    def _load_standard_marks(self) -> List[str]:
        """Загрузка стандартных марок документов"""
        return [
            "АР", "КЖ", "КМ", "ОВ", "ВК", "ЭО", "СС", "АС", "ТХ", "ПЗ",
            "АИ", "АВ", "АК", "АМ", "АП", "АС", "АТ", "АУ", "АФ", "АХ",
            "КД", "КИ", "КЛ", "КН", "КО", "КП", "КР", "КС", "КТ", "КУ"
        ]
    
    def _load_project_stages(self) -> List[str]:
        """Загрузка стадий проектирования"""
        return [
            "Проектная документация",
            "Рабочая документация", 
            "Исполнительная документация",
            "Проектная документация для строительства"
        ]
    
    def validate_document(self, document_data: Dict[str, Any]) -> List[ValidationIssue]:
        """Основная валидация документа на соответствие СПДС"""
        issues = []
        
        # Валидация марки документа
        mark_issues = self._validate_document_mark(document_data.get("mark"))
        issues.extend(mark_issues)
        
        # Валидация стадии проектирования
        stage_issues = self._validate_project_stage(document_data.get("project_stage"))
        issues.extend(stage_issues)
        
        # Валидация состава документации
        composition_issues = self._validate_document_composition(document_data)
        issues.extend(composition_issues)
        
        # Валидация технических требований
        technical_issues = self._validate_technical_requirements(document_data)
        issues.extend(technical_issues)
        
        # Валидация метаданных
        metadata_issues = self._validate_metadata(document_data.get("metadata"))
        issues.extend(metadata_issues)
        
        return issues
    
    def _validate_document_mark(self, mark: Optional[str]) -> List[ValidationIssue]:
        """Валидация марки документа"""
        issues = []
        
        if not mark:
            issues.append(ValidationIssue(
                id="missing_document_mark",
                category="document_mark",
                severity=IssueSeverity.CRITICAL,
                title="Отсутствует марка документа",
                description="В документе не указана марка согласно СПДС",
                recommendation="Указать марку документа в соответствии с СП 48.13330.2019"
            ))
            return issues
        
        if mark not in self.standard_marks:
            issues.append(ValidationIssue(
                id=f"non_standard_mark_{mark}",
                category="document_mark",
                severity=IssueSeverity.HIGH,
                title=f"Нестандартная марка документа: {mark}",
                description=f"Марка '{mark}' не соответствует стандартным маркам СПДС",
                recommendation=f"Использовать стандартные марки: {', '.join(self.standard_marks[:10])}"
            ))
        
        return issues
    
    def _validate_project_stage(self, stage: Optional[str]) -> List[ValidationIssue]:
        """Валидация стадии проектирования"""
        issues = []
        
        if not stage:
            issues.append(ValidationIssue(
                id="missing_project_stage",
                category="project_stage",
                severity=IssueSeverity.HIGH,
                title="Отсутствует стадия проектирования",
                description="В документе не указана стадия проектирования",
                recommendation="Указать стадию проектирования согласно СП 48.13330.2019"
            ))
            return issues
        
        if stage not in self.project_stages:
            issues.append(ValidationIssue(
                id=f"non_standard_stage_{stage}",
                category="project_stage",
                severity=IssueSeverity.MEDIUM,
                title=f"Нестандартная стадия проектирования: {stage}",
                description=f"Стадия '{stage}' не соответствует стандартным стадиям СПДС",
                recommendation=f"Использовать стандартные стадии: {', '.join(self.project_stages)}"
            ))
        
        return issues
    
    def _validate_document_composition(self, document_data: Dict[str, Any]) -> List[ValidationIssue]:
        """Валидация состава документации"""
        issues = []
        
        project_stage = document_data.get("project_stage", "")
        mark = document_data.get("mark", "")
        
        # Определение требуемого состава на основе стадии и марки
        required_composition = self._get_required_composition(project_stage, mark)
        
        if not required_composition:
            issues.append(ValidationIssue(
                id="unknown_composition_requirements",
                category="document_composition",
                severity=IssueSeverity.MEDIUM,
                title="Не удалось определить требования к составу",
                description=f"Для стадии '{project_stage}' и марки '{mark}' не определен состав документации",
                recommendation="Проверить соответствие стадии и марки стандартам СПДС"
            ))
            return issues
        
        # Проверка наличия обязательных разделов
        document_sections = document_data.get("sections", [])
        for required_section in required_composition:
            if not any(section.get("name", "").lower() == required_section.lower() 
                      for section in document_sections):
                issues.append(ValidationIssue(
                    id=f"missing_section_{required_section}",
                    category="document_composition",
                    severity=IssueSeverity.HIGH,
                    title=f"Отсутствует раздел: {required_section}",
                    description=f"В документе отсутствует обязательный раздел '{required_section}'",
                    recommendation=f"Добавить раздел '{required_section}' согласно СП 48.13330.2019"
                ))
        
        return issues
    
    def _get_required_composition(self, project_stage: str, mark: str) -> List[str]:
        """Получение требуемого состава документации"""
        if project_stage == "Проектная документация":
            return self.spds_requirements["sp_48_13330_2019"]["requirements"]["project_documentation"]["composition"]["project_documentation"]
        elif project_stage == "Рабочая документация":
            return self.spds_requirements["sp_48_13330_2019"]["requirements"]["project_documentation"]["composition"]["working_documentation"]
        else:
            return []
    
    def _validate_technical_requirements(self, document_data: Dict[str, Any]) -> List[ValidationIssue]:
        """Валидация технических требований"""
        issues = []
        
        mark = document_data.get("mark", "")
        
        # Валидация для архитектурных решений
        if mark == "АР":
            arch_issues = self._validate_architectural_requirements(document_data)
            issues.extend(arch_issues)
        
        # Валидация для конструктивных решений
        elif mark in ["КЖ", "КМ"]:
            struct_issues = self._validate_structural_requirements(document_data)
            issues.extend(struct_issues)
        
        # Валидация для инженерных систем
        elif mark in ["ОВ", "ВК", "ЭО", "СС"]:
            eng_issues = self._validate_engineering_requirements(document_data)
            issues.extend(eng_issues)
        
        return issues
    
    def _validate_architectural_requirements(self, document_data: Dict[str, Any]) -> List[ValidationIssue]:
        """Валидация требований для архитектурных решений"""
        issues = []
        
        # Проверка наличия планов
        if not document_data.get("has_plans", False):
            issues.append(ValidationIssue(
                id="missing_architectural_plans",
                category="architectural_requirements",
                severity=IssueSeverity.HIGH,
                title="Отсутствуют архитектурные планы",
                description="В архитектурных решениях должны быть планы этажей",
                recommendation="Добавить планы этажей согласно СП 70.13330.2012"
            ))
        
        # Проверка наличия фасадов
        if not document_data.get("has_facades", False):
            issues.append(ValidationIssue(
                id="missing_facades",
                category="architectural_requirements",
                severity=IssueSeverity.HIGH,
                title="Отсутствуют фасады",
                description="В архитектурных решениях должны быть фасады здания",
                recommendation="Добавить фасады согласно СП 70.13330.2012"
            ))
        
        # Проверка наличия разрезов
        if not document_data.get("has_sections", False):
            issues.append(ValidationIssue(
                id="missing_sections",
                category="architectural_requirements",
                severity=IssueSeverity.MEDIUM,
                title="Отсутствуют разрезы",
                description="Рекомендуется добавить разрезы здания",
                recommendation="Добавить разрезы для лучшего понимания конструкции"
            ))
        
        return issues
    
    def _validate_structural_requirements(self, document_data: Dict[str, Any]) -> List[ValidationIssue]:
        """Валидация требований для конструктивных решений"""
        issues = []
        
        # Проверка наличия планов конструкций
        if not document_data.get("has_structural_plans", False):
            issues.append(ValidationIssue(
                id="missing_structural_plans",
                category="structural_requirements",
                severity=IssueSeverity.HIGH,
                title="Отсутствуют планы конструкций",
                description="В конструктивных решениях должны быть планы конструкций",
                recommendation="Добавить планы конструкций согласно СП 16.13330.2017"
            ))
        
        # Проверка наличия схем армирования
        if not document_data.get("has_reinforcement_drawings", False):
            issues.append(ValidationIssue(
                id="missing_reinforcement_drawings",
                category="structural_requirements",
                severity=IssueSeverity.HIGH,
                title="Отсутствуют схемы армирования",
                description="В конструктивных решениях должны быть схемы армирования",
                recommendation="Добавить схемы армирования согласно СП 16.13330.2017"
            ))
        
        # Проверка наличия деталей узлов
        if not document_data.get("has_connection_details", False):
            issues.append(ValidationIssue(
                id="missing_connection_details",
                category="structural_requirements",
                severity=IssueSeverity.MEDIUM,
                title="Отсутствуют детали узлов",
                description="Рекомендуется добавить детали узлов соединений",
                recommendation="Добавить детали узлов для ясности конструкции"
            ))
        
        return issues
    
    def _validate_engineering_requirements(self, document_data: Dict[str, Any]) -> List[ValidationIssue]:
        """Валидация требований для инженерных систем"""
        issues = []
        
        # Проверка наличия планов инженерных систем
        if not document_data.get("has_engineering_plans", False):
            issues.append(ValidationIssue(
                id="missing_engineering_plans",
                category="engineering_requirements",
                severity=IssueSeverity.HIGH,
                title="Отсутствуют планы инженерных систем",
                description="В инженерных решениях должны быть планы систем",
                recommendation="Добавить планы инженерных систем"
            ))
        
        # Проверка наличия схем
        if not document_data.get("has_schemes", False):
            issues.append(ValidationIssue(
                id="missing_engineering_schemes",
                category="engineering_requirements",
                severity=IssueSeverity.MEDIUM,
                title="Отсутствуют схемы инженерных систем",
                description="Рекомендуется добавить схемы инженерных систем",
                recommendation="Добавить схемы для лучшего понимания систем"
            ))
        
        return issues
    
    def _validate_metadata(self, metadata: Optional[DocumentMetadata]) -> List[ValidationIssue]:
        """Валидация метаданных документа"""
        issues = []
        
        if not metadata:
            issues.append(ValidationIssue(
                id="missing_metadata",
                category="metadata",
                severity=IssueSeverity.LOW,
                title="Отсутствуют метаданные документа",
                description="Не удалось получить метаданные документа",
                recommendation="Проверить качество и формат документа"
            ))
            return issues
        
        # Проверка наличия автора
        if not metadata.author:
            issues.append(ValidationIssue(
                id="missing_author",
                category="metadata",
                severity=IssueSeverity.MEDIUM,
                title="Отсутствует информация об авторе",
                description="В метаданных документа не указан автор",
                recommendation="Указать автора документа в метаданных"
            ))
        
        # Проверка наличия заголовка
        if not metadata.title:
            issues.append(ValidationIssue(
                id="missing_title",
                category="metadata",
                severity=IssueSeverity.MEDIUM,
                title="Отсутствует заголовок документа",
                description="В метаданных документа не указан заголовок",
                recommendation="Указать заголовок документа в метаданных"
            ))
        
        return issues
