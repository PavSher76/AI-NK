import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from models.data_models import DocumentInspectionResult, PageResult, Finding, FindingType, SeverityLevel
from database.connection import DatabaseConnection
from utils.memory_utils import check_memory_pressure, cleanup_memory

logger = logging.getLogger(__name__)

class HierarchicalCheckService:
    """Сервис для иерархической проверки документов"""
    
    def __init__(self, db_connection: DatabaseConnection):
        self.db_connection = db_connection
    
    async def perform_hierarchical_check(self, document_id: int) -> Dict[str, Any]:
        """Выполнение иерархической проверки документа"""
        try:
            logger.info(f"🚀 [HIERARCHICAL] Starting hierarchical check for document {document_id}")
            start_time = datetime.now()
            
            # Этап 1: Быстрая проверка первой страницы
            logger.info(f"📄 [HIERARCHICAL] Stage 1: Quick first page analysis")
            first_page_info = await self.analyze_first_page(document_id)
            
            # Этап 2: Проверка всего документа на соответствие нормам
            logger.info(f"📋 [HIERARCHICAL] Stage 2: Full document norm compliance check")
            norm_compliance_results = await self.check_norm_compliance(document_id, first_page_info)
            
            # Этап 3: Выявление разделов и организация проверки по разделам
            logger.info(f"📑 [HIERARCHICAL] Stage 3: Document sections identification and organization")
            section_analysis = await self.analyze_document_sections(document_id, first_page_info)
            
            # Формирование общего результата
            total_time = (datetime.now() - start_time).total_seconds()
            
            result = {
                "document_id": document_id,
                "check_type": "hierarchical",
                "execution_time": total_time,
                "stages": {
                    "first_page_analysis": first_page_info,
                    "norm_compliance": norm_compliance_results,
                    "section_analysis": section_analysis
                },
                "summary": {
                    "project_info": first_page_info.get("project_info", {}),
                    "total_findings": norm_compliance_results.get("total_findings", 0),
                    "sections_identified": len(section_analysis.get("sections", [])),
                    "overall_status": self.determine_overall_status(norm_compliance_results)
                }
            }
            
            # Сохранение результатов
            await self.save_hierarchical_check_result(document_id, result)
            
            logger.info(f"✅ [HIERARCHICAL] Hierarchical check completed for document {document_id} in {total_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"❌ [HIERARCHICAL] Hierarchical check failed for document {document_id}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "document_id": document_id
            }
    
    async def analyze_first_page(self, document_id: int) -> Dict[str, Any]:
        """Этап 1: Быстрая проверка первой страницы и получение общей информации"""
        try:
            logger.info(f"📄 [FIRST_PAGE] Analyzing first page for document {document_id}")
            
            # Получаем первую страницу документа
            first_page = self.get_first_page_content(document_id)
            if not first_page:
                return {"error": "First page not found"}
            
            # Анализируем содержимое первой страницы
            analysis_result = {
                "page_number": 1,
                "content_length": len(first_page.get("content", "")),
                "project_info": await self.extract_project_info(first_page.get("content", "")),
                "document_metadata": await self.extract_document_metadata(first_page.get("content", "")),
                "analysis_timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"📄 [FIRST_PAGE] First page analysis completed: {analysis_result.get('project_info', {}).get('project_name', 'Unknown')}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"❌ [FIRST_PAGE] First page analysis failed: {e}")
            return {"error": str(e)}
    
    async def extract_project_info(self, content: str) -> Dict[str, Any]:
        """Извлечение информации о проекте из первой страницы"""
        try:
            # Здесь должна быть логика извлечения информации о проекте
            # Пока возвращаем заглушку
            project_info = {
                "project_name": "Проект по умолчанию",
                "project_stage": "Рабочая документация",
                "project_type": "Строительный",
                "document_set": "Конструктивные решения",
                "confidence": 0.8
            }
            
            # Простая логика извлечения (можно заменить на LLM)
            if "проект" in content.lower():
                # Извлекаем название проекта
                lines = content.split('\n')
                for line in lines:
                    if "проект" in line.lower() and len(line.strip()) > 10:
                        project_info["project_name"] = line.strip()
                        break
            
            if "рабочая" in content.lower():
                project_info["project_stage"] = "Рабочая документация"
            elif "проектная" in content.lower():
                project_info["project_stage"] = "Проектная документация"
            
            return project_info
            
        except Exception as e:
            logger.error(f"Error extracting project info: {e}")
            return {"project_name": "Неизвестный проект", "error": str(e)}
    
    async def extract_document_metadata(self, content: str) -> Dict[str, Any]:
        """Извлечение метаданных документа"""
        try:
            metadata = {
                "document_type": "Чертеж",
                "document_mark": "КР",
                "document_number": "01",
                "revision": "0",
                "scale": "1:100",
                "sheet_number": "1",
                "total_sheets": "1"
            }
            
            # Простая логика извлечения метаданных
            lines = content.split('\n')
            for line in lines:
                line_lower = line.lower()
                if "масштаб" in line_lower or "1:" in line:
                    metadata["scale"] = line.strip()
                elif "лист" in line_lower:
                    metadata["sheet_number"] = line.strip()
                elif "марка" in line_lower:
                    metadata["document_mark"] = line.strip()
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting document metadata: {e}")
            return {"error": str(e)}
    
    async def check_norm_compliance(self, document_id: int, first_page_info: Dict[str, Any]) -> Dict[str, Any]:
        """Этап 2: Проверка всего документа на соответствие нормам"""
        try:
            logger.info(f"📋 [NORM_COMPLIANCE] Checking norm compliance for document {document_id}")
            
            # Получаем информацию о проекте
            project_info = first_page_info.get("project_info", {})
            project_stage = project_info.get("project_stage", "Рабочая документация")
            document_set = project_info.get("document_set", "Конструктивные решения")
            
            # Получаем все страницы документа
            pages = self.get_all_pages_content(document_id)
            
            findings = []
            total_pages = len(pages)
            compliant_pages = 0
            
            for page_data in pages:
                page_number = page_data["page_number"]
                content = page_data["content"]
                
                logger.info(f"📋 [NORM_COMPLIANCE] Checking page {page_number}/{total_pages}")
                
                # Проверяем страницу на соответствие нормам
                page_findings = await self.check_page_norm_compliance(
                    content, page_number, project_stage, document_set
                )
                
                findings.extend(page_findings)
                
                if not page_findings:
                    compliant_pages += 1
            
            result = {
                "project_stage": project_stage,
                "document_set": document_set,
                "total_pages": total_pages,
                "compliant_pages": compliant_pages,
                "compliance_percentage": (compliant_pages / total_pages * 100) if total_pages > 0 else 0,
                "findings": findings,
                "total_findings": len(findings),
                "critical_findings": len([f for f in findings if f.get("severity", 0) >= 4]),
                "warning_findings": len([f for f in findings if f.get("severity", 0) == 3]),
                "info_findings": len([f for f in findings if f.get("severity", 0) <= 2])
            }
            
            logger.info(f"📋 [NORM_COMPLIANCE] Norm compliance check completed: {result['total_findings']} findings")
            return result
            
        except Exception as e:
            logger.error(f"❌ [NORM_COMPLIANCE] Norm compliance check failed: {e}")
            return {"error": str(e)}
    
    async def check_page_norm_compliance(self, content: str, page_number: int, 
                                       project_stage: str, document_set: str) -> List[Dict[str, Any]]:
        """Проверка одной страницы на соответствие нормам"""
        findings = []
        
        try:
            # Простая логика проверки (можно заменить на LLM)
            
            # Проверка на наличие обязательных элементов
            if "общие данные" in content.lower():
                if "масштаб" not in content.lower():
                    findings.append({
                        "type": "warning",
                        "severity": 3,
                        "category": "general_data",
                        "title": "Отсутствует масштаб",
                        "description": f"На странице {page_number} отсутствует указание масштаба",
                        "recommendation": "Добавить масштаб в раздел 'Общие данные'",
                        "page_number": page_number
                    })
            
            # Проверка на соответствие стадии проектирования
            if project_stage == "Рабочая документация":
                if "спецификация" not in content.lower() and "ведомость" not in content.lower():
                    findings.append({
                        "type": "info",
                        "severity": 2,
                        "category": "working_documentation",
                        "title": "Рекомендуется добавить спецификацию",
                        "description": f"Для рабочей документации рекомендуется включить спецификацию на странице {page_number}",
                        "recommendation": "Добавить спецификацию материалов и изделий",
                        "page_number": page_number
                    })
            
            # Проверка на соответствие марке комплекта
            if document_set == "Конструктивные решения":
                if "арматура" in content.lower() and "класс" not in content.lower():
                    findings.append({
                        "type": "warning",
                        "severity": 3,
                        "category": "structural_solutions",
                        "title": "Не указан класс арматуры",
                        "description": f"На странице {page_number} указана арматура без класса",
                        "recommendation": "Указать класс арматуры согласно СП 63.13330",
                        "page_number": page_number
                    })
            
        except Exception as e:
            logger.error(f"Error checking page {page_number} norm compliance: {e}")
            findings.append({
                "type": "error",
                "severity": 5,
                "category": "system_error",
                "title": "Ошибка проверки страницы",
                "description": f"Ошибка при проверке страницы {page_number}: {e}",
                "recommendation": "Повторить проверку",
                "page_number": page_number
            })
        
        return findings
    
    async def analyze_document_sections(self, document_id: int, first_page_info: Dict[str, Any]) -> Dict[str, Any]:
        """Этап 3: Выявление разделов документации и организация проверки"""
        try:
            logger.info(f"📑 [SECTIONS] Analyzing document sections for document {document_id}")
            
            # Получаем все страницы
            pages = self.get_all_pages_content(document_id)
            
            sections = []
            current_section = None
            
            for page_data in pages:
                page_number = page_data["page_number"]
                content = page_data["content"]
                
                # Определяем раздел страницы
                section_info = await self.identify_page_section(content, page_number)
                
                if section_info["section_type"] != current_section:
                    current_section = section_info["section_type"]
                    sections.append({
                        "section_type": current_section,
                        "start_page": page_number,
                        "end_page": page_number,
                        "pages_count": 1,
                        "section_name": section_info["section_name"],
                        "check_priority": section_info["check_priority"]
                    })
                else:
                    # Обновляем последний раздел
                    if sections:
                        sections[-1]["end_page"] = page_number
                        sections[-1]["pages_count"] += 1
            
            result = {
                "sections": sections,
                "total_sections": len(sections),
                "section_analysis": {
                    "general_data_section": next((s for s in sections if s["section_type"] == "general_data"), None),
                    "main_content_sections": [s for s in sections if s["section_type"] == "main_content"],
                    "specification_sections": [s for s in sections if s["section_type"] == "specification"]
                }
            }
            
            logger.info(f"📑 [SECTIONS] Document sections analysis completed: {len(sections)} sections identified")
            return result
            
        except Exception as e:
            logger.error(f"❌ [SECTIONS] Document sections analysis failed: {e}")
            return {"error": str(e)}
    
    async def identify_page_section(self, content: str, page_number: int) -> Dict[str, Any]:
        """Определение раздела страницы"""
        try:
            content_lower = content.lower()
            
            # Определяем тип раздела
            if "общие данные" in content_lower or "общие сведения" in content_lower:
                return {
                    "section_type": "general_data",
                    "section_name": "Общие данные",
                    "check_priority": "high"
                }
            elif "спецификация" in content_lower or "ведомость" in content_lower:
                return {
                    "section_type": "specification",
                    "section_name": "Спецификация",
                    "check_priority": "medium"
                }
            elif "узлы" in content_lower or "детали" in content_lower:
                return {
                    "section_type": "details",
                    "section_name": "Узлы и детали",
                    "check_priority": "medium"
                }
            else:
                return {
                    "section_type": "main_content",
                    "section_name": "Основное содержание",
                    "check_priority": "normal"
                }
                
        except Exception as e:
            logger.error(f"Error identifying page section: {e}")
            return {
                "section_type": "unknown",
                "section_name": "Неизвестный раздел",
                "check_priority": "low"
            }
    
    def determine_overall_status(self, norm_compliance_results: Dict[str, Any]) -> str:
        """Определение общего статуса проверки"""
        try:
            critical_findings = norm_compliance_results.get("critical_findings", 0)
            warning_findings = norm_compliance_results.get("warning_findings", 0)
            compliance_percentage = norm_compliance_results.get("compliance_percentage", 0)
            
            if critical_findings > 0:
                return "fail"
            elif warning_findings > 0 or compliance_percentage < 80:
                return "warning"
            else:
                return "pass"
                
        except Exception as e:
            logger.error(f"Error determining overall status: {e}")
            return "unknown"
    
    def get_first_page_content(self, document_id: int) -> Optional[Dict[str, Any]]:
        """Получение содержимого первой страницы"""
        try:
            with self.db_connection.get_db_connection().cursor() as cursor:
                cursor.execute("""
                    SELECT element_content, page_number
                    FROM checkable_elements
                    WHERE checkable_document_id = %s AND page_number = 1
                    ORDER BY id
                    LIMIT 1
                """, (document_id,))
                
                result = cursor.fetchone()
                if result:
                    return {
                        "content": result["element_content"],
                        "page_number": result["page_number"]
                    }
                return None
                
        except Exception as e:
            logger.error(f"Error getting first page content: {e}")
            return None
    
    def get_all_pages_content(self, document_id: int) -> List[Dict[str, Any]]:
        """Получение содержимого всех страниц"""
        try:
            with self.db_connection.get_db_connection().cursor() as cursor:
                cursor.execute("""
                    SELECT element_content, page_number
                    FROM checkable_elements
                    WHERE checkable_document_id = %s
                    ORDER BY page_number, id
                """, (document_id,))
                
                pages = []
                for row in cursor.fetchall():
                    pages.append({
                        "content": row["element_content"],
                        "page_number": row["page_number"]
                    })
                
                return pages
                
        except Exception as e:
            logger.error(f"Error getting all pages content: {e}")
            return []
    
    async def save_hierarchical_check_result(self, document_id: int, result: Dict[str, Any]):
        """Сохранение результатов иерархической проверки"""
        try:
            def _save_result(conn):
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO hierarchical_check_results 
                        (checkable_document_id, analysis_date, check_type, execution_time,
                         project_info, norm_compliance_summary, sections_analysis, overall_status)
                        VALUES (%s, CURRENT_TIMESTAMP, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        document_id,
                        result.get("check_type", "hierarchical"),
                        result.get("execution_time", 0),
                        str(result.get("stages", {}).get("first_page_analysis", {}).get("project_info", {})),
                        str(result.get("stages", {}).get("norm_compliance", {})),
                        str(result.get("stages", {}).get("section_analysis", {})),
                        result.get("summary", {}).get("overall_status", "unknown")
                    ))
                    
                    result_id = cursor.fetchone()[0]
                    logger.info(f"Saved hierarchical check result {result_id} for document {document_id}")
                    return result_id
            
            result_id = self.db_connection.execute_in_transaction(_save_result)
            return result_id
                
        except Exception as e:
            logger.error(f"Save hierarchical check result error: {e}")
            raise
