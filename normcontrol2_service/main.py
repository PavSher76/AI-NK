"""
Основной сервис модуля Нормоконтроль - 2
Расширенная система проверки формата и оформления документов
"""

import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

from .models import (
    ValidationResult, ValidationIssue, IssueSeverity, DocumentFormat, 
    ComplianceStatus, DocumentMetadata, TitleBlockInfo, FontInfo, 
    ScaleInfo, UnitsInfo, NotationInfo
)
from .validators import (
    ESKDValidator, SPDSValidator, TitleBlockValidator, UnitsValidator,
    FontsValidator, ScalesValidator, NotationsValidator
)

logger = logging.getLogger(__name__)


class NormControl2Service:
    """Основной сервис модуля Нормоконтроль - 2"""
    
    def __init__(self):
        self.eskd_validator = ESKDValidator()
        self.spds_validator = SPDSValidator()
        self.title_block_validator = TitleBlockValidator()
        self.units_validator = UnitsValidator()
        self.fonts_validator = FontsValidator()
        self.scales_validator = ScalesValidator()
        self.notations_validator = NotationsValidator()
        
        self.validation_rules = self._load_validation_rules()
        self.document_processors = self._load_document_processors()
    
    def _load_validation_rules(self) -> Dict[str, Any]:
        """Загрузка правил валидации"""
        return {
            "critical_issues_threshold": 1,
            "high_issues_threshold": 5,
            "medium_issues_threshold": 10,
            "compliance_score_weights": {
                "critical": 0.0,
                "high": 0.3,
                "medium": 0.6,
                "low": 0.8,
                "info": 1.0
            }
        }
    
    def _load_document_processors(self) -> Dict[str, Any]:
        """Загрузка процессоров документов"""
        return {
            "pdf": self._process_pdf_document,
            "dwg": self._process_dwg_document,
            "dxf": self._process_dxf_document,
            "docx": self._process_docx_document,
            "xlsx": self._process_xlsx_document
        }
    
    def validate_document(self, file_path: str, document_id: Optional[str] = None) -> ValidationResult:
        """Основная валидация документа"""
        start_time = time.time()
        
        try:
            # Определение формата документа
            document_format = self._detect_document_format(file_path)
            
            # Обработка документа
            document_data = self._process_document(file_path, document_format)
            
            # Извлечение метаданных
            metadata = self._extract_metadata(file_path, document_data)
            
            # Выполнение валидаций
            all_issues = []
            
            # Валидация ЕСКД
            eskd_issues = self.eskd_validator.validate_document(document_data)
            all_issues.extend(eskd_issues)
            
            # Валидация СПДС
            spds_issues = self.spds_validator.validate_document(document_data)
            all_issues.extend(spds_issues)
            
            # Валидация основной надписи
            title_block = document_data.get("title_block")
            if title_block:
                title_block_issues = self.title_block_validator.validate_title_block(title_block)
                all_issues.extend(title_block_issues)
            
            # Валидация единиц измерений
            units_info = document_data.get("units_info")
            if units_info:
                units_issues = self.units_validator.validate_units(units_info)
                all_issues.extend(units_issues)
            
            # Валидация шрифтов
            fonts = document_data.get("fonts", [])
            if fonts:
                fonts_issues = self.fonts_validator.validate_fonts(fonts)
                all_issues.extend(fonts_issues)
            
            # Валидация масштабов
            scales = document_data.get("scales", [])
            if scales:
                scales_issues = self.scales_validator.validate_scales(scales)
                all_issues.extend(scales_issues)
            
            # Валидация обозначений
            notation_info = document_data.get("notation_info")
            if notation_info:
                notation_issues = self.notations_validator.validate_notations(notation_info)
                all_issues.extend(notation_issues)
            
            # Анализ результатов
            analysis_result = self._analyze_validation_results(all_issues)
            
            # Создание результата валидации
            result = ValidationResult(
                document_id=document_id or str(int(time.time())),
                document_name=Path(file_path).name,
                document_format=document_format,
                validation_time=datetime.now(),
                overall_status=analysis_result["status"],
                compliance_score=analysis_result["compliance_score"],
                total_issues=analysis_result["total_issues"],
                critical_issues=analysis_result["critical_issues"],
                high_issues=analysis_result["high_issues"],
                medium_issues=analysis_result["medium_issues"],
                low_issues=analysis_result["low_issues"],
                info_issues=analysis_result["info_issues"],
                issues=all_issues,
                categories=analysis_result["categories"],
                recommendations=analysis_result["recommendations"],
                metadata={
                    "validation_time_seconds": time.time() - start_time,
                    "file_size": metadata.file_size if metadata else 0,
                    "page_count": metadata.page_count if metadata else 0
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка валидации документа {file_path}: {e}")
            return self._create_error_result(file_path, str(e), document_id)
    
    def _detect_document_format(self, file_path: str) -> DocumentFormat:
        """Определение формата документа"""
        extension = Path(file_path).suffix.lower()
        
        format_mapping = {
            ".pdf": DocumentFormat.PDF,
            ".dwg": DocumentFormat.DWG,
            ".dxf": DocumentFormat.DXF,
            ".docx": DocumentFormat.DOCX,
            ".xlsx": DocumentFormat.XLSX
        }
        
        return format_mapping.get(extension, DocumentFormat.UNKNOWN)
    
    def _process_document(self, file_path: str, document_format: DocumentFormat) -> Dict[str, Any]:
        """Обработка документа в зависимости от формата"""
        processor = self.document_processors.get(document_format.value)
        
        if not processor:
            raise ValueError(f"Неподдерживаемый формат документа: {document_format.value}")
        
        return processor(file_path)
    
    def _process_pdf_document(self, file_path: str) -> Dict[str, Any]:
        """Обработка PDF документа"""
        # Здесь должна быть интеграция с существующими парсерами PDF
        # Пока возвращаем заглушку
        return {
            "title_block": self._extract_title_block_from_pdf(file_path),
            "fonts": self._extract_fonts_from_pdf(file_path),
            "scales": self._extract_scales_from_pdf(file_path),
            "units_info": self._extract_units_from_pdf(file_path),
            "notation_info": self._extract_notations_from_pdf(file_path),
            "drawing_elements": self._extract_drawing_elements_from_pdf(file_path),
            "sections": self._extract_sections_from_pdf(file_path),
            "mark": self._extract_mark_from_pdf(file_path),
            "project_stage": self._extract_project_stage_from_pdf(file_path),
            "filename": Path(file_path).name
        }
    
    def _process_dwg_document(self, file_path: str) -> Dict[str, Any]:
        """Обработка DWG документа"""
        # Интеграция с парсером DWG
        return {
            "title_block": self._extract_title_block_from_dwg(file_path),
            "fonts": self._extract_fonts_from_dwg(file_path),
            "scales": self._extract_scales_from_dwg(file_path),
            "units_info": self._extract_units_from_dwg(file_path),
            "notation_info": self._extract_notations_from_dwg(file_path),
            "drawing_elements": self._extract_drawing_elements_from_dwg(file_path),
            "sections": self._extract_sections_from_dwg(file_path),
            "mark": self._extract_mark_from_dwg(file_path),
            "project_stage": self._extract_project_stage_from_dwg(file_path),
            "filename": Path(file_path).name
        }
    
    def _process_dxf_document(self, file_path: str) -> Dict[str, Any]:
        """Обработка DXF документа"""
        # Интеграция с парсером DXF
        return {
            "title_block": self._extract_title_block_from_dxf(file_path),
            "fonts": self._extract_fonts_from_dxf(file_path),
            "scales": self._extract_scales_from_dxf(file_path),
            "units_info": self._extract_units_from_dxf(file_path),
            "notation_info": self._extract_notations_from_dxf(file_path),
            "drawing_elements": self._extract_drawing_elements_from_dxf(file_path),
            "sections": self._extract_sections_from_dxf(file_path),
            "mark": self._extract_mark_from_dxf(file_path),
            "project_stage": self._extract_project_stage_from_dxf(file_path),
            "filename": Path(file_path).name
        }
    
    def _process_docx_document(self, file_path: str) -> Dict[str, Any]:
        """Обработка DOCX документа"""
        # Интеграция с парсером DOCX
        return {
            "title_block": self._extract_title_block_from_docx(file_path),
            "fonts": self._extract_fonts_from_docx(file_path),
            "scales": self._extract_scales_from_docx(file_path),
            "units_info": self._extract_units_from_docx(file_path),
            "notation_info": self._extract_notations_from_docx(file_path),
            "drawing_elements": self._extract_drawing_elements_from_docx(file_path),
            "sections": self._extract_sections_from_docx(file_path),
            "mark": self._extract_mark_from_docx(file_path),
            "project_stage": self._extract_project_stage_from_docx(file_path),
            "filename": Path(file_path).name
        }
    
    def _process_xlsx_document(self, file_path: str) -> Dict[str, Any]:
        """Обработка XLSX документа"""
        # Интеграция с парсером XLSX
        return {
            "title_block": self._extract_title_block_from_xlsx(file_path),
            "fonts": self._extract_fonts_from_xlsx(file_path),
            "scales": self._extract_scales_from_xlsx(file_path),
            "units_info": self._extract_units_from_xlsx(file_path),
            "notation_info": self._extract_notations_from_xlsx(file_path),
            "drawing_elements": self._extract_drawing_elements_from_xlsx(file_path),
            "sections": self._extract_sections_from_xlsx(file_path),
            "mark": self._extract_mark_from_xlsx(file_path),
            "project_stage": self._extract_project_stage_from_xlsx(file_path),
            "filename": Path(file_path).name
        }
    
    def _extract_metadata(self, file_path: str, document_data: Dict[str, Any]) -> DocumentMetadata:
        """Извлечение метаданных документа"""
        file_path_obj = Path(file_path)
        stat = file_path_obj.stat()
        
        return DocumentMetadata(
            file_size=stat.st_size,
            page_count=document_data.get("page_count", 1),
            creation_date=datetime.fromtimestamp(stat.st_ctime),
            modification_date=datetime.fromtimestamp(stat.st_mtime)
        )
    
    def _analyze_validation_results(self, issues: List[ValidationIssue]) -> Dict[str, Any]:
        """Анализ результатов валидации"""
        # Подсчет проблем по категориям
        critical_issues = sum(1 for issue in issues if issue.severity == IssueSeverity.CRITICAL)
        high_issues = sum(1 for issue in issues if issue.severity == IssueSeverity.HIGH)
        medium_issues = sum(1 for issue in issues if issue.severity == IssueSeverity.MEDIUM)
        low_issues = sum(1 for issue in issues if issue.severity == IssueSeverity.LOW)
        info_issues = sum(1 for issue in issues if issue.severity == IssueSeverity.INFO)
        
        total_issues = len(issues)
        
        # Определение статуса соответствия
        if critical_issues > 0:
            status = ComplianceStatus.CRITICAL_ISSUES
        elif high_issues > self.validation_rules["high_issues_threshold"]:
            status = ComplianceStatus.NON_COMPLIANT
        elif medium_issues > self.validation_rules["medium_issues_threshold"]:
            status = ComplianceStatus.NEEDS_REVIEW
        elif total_issues == 0:
            status = ComplianceStatus.COMPLIANT
        else:
            status = ComplianceStatus.COMPLIANT_WITH_WARNINGS
        
        # Расчет оценки соответствия
        compliance_score = self._calculate_compliance_score(issues)
        
        # Группировка по категориям
        categories = self._group_issues_by_category(issues)
        
        # Генерация рекомендаций
        recommendations = self._generate_recommendations(issues, status)
        
        return {
            "status": status,
            "compliance_score": compliance_score,
            "total_issues": total_issues,
            "critical_issues": critical_issues,
            "high_issues": high_issues,
            "medium_issues": medium_issues,
            "low_issues": low_issues,
            "info_issues": info_issues,
            "categories": categories,
            "recommendations": recommendations
        }
    
    def _calculate_compliance_score(self, issues: List[ValidationIssue]) -> float:
        """Расчет оценки соответствия"""
        if not issues:
            return 100.0
        
        weights = self.validation_rules["compliance_score_weights"]
        total_weight = 0.0
        weighted_score = 0.0
        
        for issue in issues:
            weight = weights.get(issue.severity.value, 1.0)
            total_weight += weight
            weighted_score += weight * weights[issue.severity.value]
        
        if total_weight == 0:
            return 100.0
        
        return (weighted_score / total_weight) * 100.0
    
    def _group_issues_by_category(self, issues: List[ValidationIssue]) -> Dict[str, Dict[str, Any]]:
        """Группировка проблем по категориям"""
        categories = {}
        
        for issue in issues:
            category = issue.category
            if category not in categories:
                categories[category] = {
                    "total_issues": 0,
                    "critical_issues": 0,
                    "high_issues": 0,
                    "medium_issues": 0,
                    "low_issues": 0,
                    "info_issues": 0,
                    "issues": []
                }
            
            categories[category]["total_issues"] += 1
            categories[category][f"{issue.severity.value}_issues"] += 1
            categories[category]["issues"].append(issue)
        
        return categories
    
    def _generate_recommendations(self, issues: List[ValidationIssue], status: ComplianceStatus) -> List[str]:
        """Генерация рекомендаций"""
        recommendations = []
        
        if status == ComplianceStatus.CRITICAL_ISSUES:
            recommendations.append("Устранить критические нарушения немедленно")
        elif status == ComplianceStatus.NON_COMPLIANT:
            recommendations.append("Исправить серьезные нарушения в кратчайшие сроки")
        elif status == ComplianceStatus.NEEDS_REVIEW:
            recommendations.append("Провести дополнительную проверку документа")
        
        # Рекомендации по категориям
        critical_categories = [issue.category for issue in issues if issue.severity == IssueSeverity.CRITICAL]
        if critical_categories:
            recommendations.append(f"Обратить особое внимание на категории: {', '.join(set(critical_categories))}")
        
        return recommendations
    
    def _create_error_result(self, file_path: str, error_message: str, document_id: Optional[str]) -> ValidationResult:
        """Создание результата с ошибкой"""
        return ValidationResult(
            document_id=document_id or str(int(time.time())),
            document_name=Path(file_path).name,
            document_format=DocumentFormat.UNKNOWN,
            validation_time=datetime.now(),
            overall_status=ComplianceStatus.NEEDS_REVIEW,
            compliance_score=0.0,
            total_issues=1,
            critical_issues=1,
            high_issues=0,
            medium_issues=0,
            low_issues=0,
            info_issues=0,
            issues=[ValidationIssue(
                id="validation_error",
                category="system",
                severity=IssueSeverity.CRITICAL,
                title="Ошибка валидации",
                description=error_message,
                recommendation="Проверить файл и повторить валидацию"
            )],
            categories={},
            recommendations=["Исправить ошибку и повторить валидацию"],
            metadata={"error": error_message}
        )
    
    # Заглушки для извлечения данных из документов
    # В реальной реализации здесь должна быть интеграция с существующими парсерами
    
    def _extract_title_block_from_pdf(self, file_path: str) -> Optional[TitleBlockInfo]:
        """Извлечение основной надписи из PDF"""
        # Интеграция с PDF парсером
        return None
    
    def _extract_fonts_from_pdf(self, file_path: str) -> List[FontInfo]:
        """Извлечение шрифтов из PDF"""
        # Интеграция с PDF парсером
        return []
    
    def _extract_scales_from_pdf(self, file_path: str) -> List[ScaleInfo]:
        """Извлечение масштабов из PDF"""
        # Интеграция с PDF парсером
        return []
    
    def _extract_units_from_pdf(self, file_path: str) -> Optional[UnitsInfo]:
        """Извлечение единиц измерений из PDF"""
        # Интеграция с PDF парсером
        return None
    
    def _extract_notations_from_pdf(self, file_path: str) -> Optional[NotationInfo]:
        """Извлечение обозначений из PDF"""
        # Интеграция с PDF парсером
        return None
    
    def _extract_drawing_elements_from_pdf(self, file_path: str) -> List[Dict[str, Any]]:
        """Извлечение чертежных элементов из PDF"""
        # Интеграция с PDF парсером
        return []
    
    def _extract_sections_from_pdf(self, file_path: str) -> List[Dict[str, Any]]:
        """Извлечение разделов из PDF"""
        # Интеграция с PDF парсером
        return []
    
    def _extract_mark_from_pdf(self, file_path: str) -> Optional[str]:
        """Извлечение марки из PDF"""
        # Интеграция с PDF парсером
        return None
    
    def _extract_project_stage_from_pdf(self, file_path: str) -> Optional[str]:
        """Извлечение стадии проекта из PDF"""
        # Интеграция с PDF парсером
        return None
    
    # Аналогичные методы для других форматов (заглушки)
    def _extract_title_block_from_dwg(self, file_path: str) -> Optional[TitleBlockInfo]:
        return None
    
    def _extract_fonts_from_dwg(self, file_path: str) -> List[FontInfo]:
        return []
    
    def _extract_scales_from_dwg(self, file_path: str) -> List[ScaleInfo]:
        return []
    
    def _extract_units_from_dwg(self, file_path: str) -> Optional[UnitsInfo]:
        return None
    
    def _extract_notations_from_dwg(self, file_path: str) -> Optional[NotationInfo]:
        return None
    
    def _extract_drawing_elements_from_dwg(self, file_path: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_sections_from_dwg(self, file_path: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_mark_from_dwg(self, file_path: str) -> Optional[str]:
        return None
    
    def _extract_project_stage_from_dwg(self, file_path: str) -> Optional[str]:
        return None
    
    # Аналогичные методы для DXF, DOCX, XLSX (заглушки)
    def _extract_title_block_from_dxf(self, file_path: str) -> Optional[TitleBlockInfo]:
        return None
    
    def _extract_fonts_from_dxf(self, file_path: str) -> List[FontInfo]:
        return []
    
    def _extract_scales_from_dxf(self, file_path: str) -> List[ScaleInfo]:
        return []
    
    def _extract_units_from_dxf(self, file_path: str) -> Optional[UnitsInfo]:
        return None
    
    def _extract_notations_from_dxf(self, file_path: str) -> Optional[NotationInfo]:
        return None
    
    def _extract_drawing_elements_from_dxf(self, file_path: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_sections_from_dxf(self, file_path: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_mark_from_dxf(self, file_path: str) -> Optional[str]:
        return None
    
    def _extract_project_stage_from_dxf(self, file_path: str) -> Optional[str]:
        return None
    
    def _extract_title_block_from_docx(self, file_path: str) -> Optional[TitleBlockInfo]:
        return None
    
    def _extract_fonts_from_docx(self, file_path: str) -> List[FontInfo]:
        return []
    
    def _extract_scales_from_docx(self, file_path: str) -> List[ScaleInfo]:
        return []
    
    def _extract_units_from_docx(self, file_path: str) -> Optional[UnitsInfo]:
        return None
    
    def _extract_notations_from_docx(self, file_path: str) -> Optional[NotationInfo]:
        return None
    
    def _extract_drawing_elements_from_docx(self, file_path: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_sections_from_docx(self, file_path: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_mark_from_docx(self, file_path: str) -> Optional[str]:
        return None
    
    def _extract_project_stage_from_docx(self, file_path: str) -> Optional[str]:
        return None
    
    def _extract_title_block_from_xlsx(self, file_path: str) -> Optional[TitleBlockInfo]:
        return None
    
    def _extract_fonts_from_xlsx(self, file_path: str) -> List[FontInfo]:
        return []
    
    def _extract_scales_from_xlsx(self, file_path: str) -> List[ScaleInfo]:
        return []
    
    def _extract_units_from_xlsx(self, file_path: str) -> Optional[UnitsInfo]:
        return None
    
    def _extract_notations_from_xlsx(self, file_path: str) -> Optional[NotationInfo]:
        return None
    
    def _extract_drawing_elements_from_xlsx(self, file_path: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_sections_from_xlsx(self, file_path: str) -> List[Dict[str, Any]]:
        return []
    
    def _extract_mark_from_xlsx(self, file_path: str) -> Optional[str]:
        return None
    
    def _extract_project_stage_from_xlsx(self, file_path: str) -> Optional[str]:
        return None
