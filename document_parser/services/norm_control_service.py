import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from models.data_models import NormControlResult, Finding, FindingType, SeverityLevel
from database.connection import DatabaseConnection, TransactionContext
from utils.memory_utils import check_memory_pressure, cleanup_memory

logger = logging.getLogger(__name__)

class NormControlService:
    """Сервис для выполнения проверки нормоконтроля"""
    
    def __init__(self, db_connection: DatabaseConnection):
        self.db_connection = db_connection
    
    async def perform_norm_control_check(self, document_id: int, document_content: str) -> Dict[str, Any]:
        """Выполнение проверки нормоконтроля для документа по страницам с применением LLM"""
        try:
            logger.info(f"Starting norm control check for document {document_id}")
            logger.info(f"Document content length: {len(document_content)} characters")
            
            # Разбиваем документ на страницы в соответствии с реальной структурой PDF
            pages = self.split_document_into_pages(document_id)
            logger.info(f"Document split into {len(pages)} pages based on PDF structure")
            
            # Проверяем каждую страницу отдельно
            page_results = []
            total_findings = 0
            total_critical_findings = 0
            total_warning_findings = 0
            total_info_findings = 0
            all_findings = []
            
            for page_data in pages:
                logger.info(f"Processing page {page_data['page_number']} of {len(pages)}")
                
                # Проверяем страницу
                page_result = await self.perform_norm_control_check_for_page(document_id, page_data)
                
                if page_result["status"] == "success":
                    result_data = page_result["result"]
                    page_results.append(result_data)
                    
                    # Собираем статистику
                    total_findings += result_data.get("total_findings", 0)
                    total_critical_findings += result_data.get("critical_findings", 0)
                    total_warning_findings += result_data.get("warning_findings", 0)
                    total_info_findings += result_data.get("info_findings", 0)
                    
                    # Собираем все findings
                    page_findings = result_data.get("findings", [])
                    for finding in page_findings:
                        finding["page_number"] = page_data["page_number"]
                    all_findings.extend(page_findings)
                    
                    logger.info(f"Page {page_data['page_number']} processed successfully")
                else:
                    logger.error(f"Failed to process page {page_data['page_number']}: {page_result.get('error', 'Unknown error')}")
                    # Добавляем пустой результат для страницы
                    page_results.append({
                        "page_number": page_data["page_number"],
                        "overall_status": "error",
                        "confidence": 0.0,
                        "total_findings": 0,
                        "critical_findings": 0,
                        "warning_findings": 0,
                        "info_findings": 0,
                        "findings": [],
                        "summary": f"Ошибка обработки страницы: {page_result.get('error', 'Unknown error')}",
                        "compliance_percentage": 0
                    })
            
            # Формируем общий результат
            overall_status = "pass"
            if total_critical_findings > 0:
                overall_status = "fail"
            elif total_warning_findings > 0:
                overall_status = "uncertain"
            
            # Вычисляем общий процент соответствия
            total_pages = len(pages)
            successful_pages = len([r for r in page_results if r.get("overall_status") == "pass"])
            compliance_percentage = (successful_pages / total_pages * 100) if total_pages > 0 else 0
            
            # Формируем общий отчет
            combined_result = {
                "overall_status": overall_status,
                "confidence": 0.8,  # Высокая уверенность при постраничной проверке
                "total_findings": total_findings,
                "critical_findings": total_critical_findings,
                "warning_findings": total_warning_findings,
                "info_findings": total_info_findings,
                "total_pages": total_pages,
                "successful_pages": successful_pages,
                "page_results": page_results,
                "findings": all_findings,
                "summary": f"Проверка завершена. Обработано {total_pages} страниц. Найдено {total_findings} нарушений.",
                "compliance_percentage": compliance_percentage,
                "recommendations": f"Общие рекомендации: {total_critical_findings} критических нарушений, {total_warning_findings} предупреждений, {total_info_findings} замечаний."
            }
            
            # Сохраняем результат в базу данных
            await self.save_norm_control_result(document_id, combined_result)
            
            return {
                "status": "success",
                "result": combined_result,
                "pages_processed": len(pages)
            }
            
        except Exception as e:
            logger.error(f"Norm control check error: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def split_document_into_pages(self, document_id: int) -> List[Dict[str, Any]]:
        """Разбиение документа на страницы"""
        try:
            with self.db_connection.get_db_connection().cursor() as cursor:
                cursor.execute("""
                    SELECT element_content, page_number
                    FROM checkable_elements
                    WHERE checkable_document_id = %s
                    ORDER BY page_number
                """, (document_id,))
                
                pages = []
                for row in cursor.fetchall():
                    pages.append({
                        "page_number": row[1],  # page_number
                        "content": row[0]  # element_content
                    })
                
                return pages
        except Exception as e:
            logger.error(f"Error splitting document into pages: {e}")
            return []
    
    async def perform_norm_control_check_for_page(self, document_id: int, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнение проверки нормоконтроля для одной страницы"""
        try:
            page_number = page_data["page_number"]
            content = page_data["content"]
            
            logger.info(f"Processing page {page_number} with content length: {len(content)}")
            
            # Здесь должна быть логика проверки с использованием LLM
            # Пока возвращаем заглушку
            findings = []
            
            # Пример findings
            if len(content) > 1000:
                findings.append({
                    "type": "warning",
                    "severity": 3,
                    "category": "content_length",
                    "title": "Длинный текст на странице",
                    "description": f"Страница {page_number} содержит {len(content)} символов",
                    "recommendation": "Рассмотрите возможность разбиения на несколько страниц"
                })
            
            result = {
                "page_number": page_number,
                "overall_status": "pass" if not findings else "warning",
                "confidence": 0.9,
                "total_findings": len(findings),
                "critical_findings": len([f for f in findings if f.get("severity", 0) >= 4]),
                "warning_findings": len([f for f in findings if f.get("severity", 0) == 3]),
                "info_findings": len([f for f in findings if f.get("severity", 0) <= 2]),
                "findings": findings,
                "summary": f"Страница {page_number} проверена",
                "compliance_percentage": 100 if not findings else 80
            }
            
            return {
                "status": "success",
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Error processing page {page_data.get('page_number', 'unknown')}: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def save_norm_control_result(self, document_id: int, check_result: Dict[str, Any]):
        """Сохранение результата проверки нормоконтроля в базу данных"""
        try:
            def _save_result(conn):
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO norm_control_results 
                        (checkable_document_id, analysis_date, analysis_type, model_used, analysis_status,
                         total_findings, critical_findings, warning_findings, info_findings)
                        VALUES (%s, CURRENT_TIMESTAMP, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        document_id,
                        "norm_control",
                        "llama3.1:8b",
                        check_result.get("overall_status", "uncertain"),
                        check_result.get("total_findings", 0),
                        check_result.get("critical_findings", 0),
                        check_result.get("warning_findings", 0),
                        check_result.get("info_findings", 0)
                    ))
                    
                    result_id = cursor.fetchone()[0]
                    logger.info(f"Saved norm control result {result_id} for document {document_id}")
                    return result_id
            
            result_id = self.db_connection.execute_in_transaction(_save_result)
            
            # Сохраняем детальную информацию о каждом нарушении
            findings = check_result.get("findings", [])
            if findings:
                await self.save_findings_detailed(result_id, findings, document_id)
                logger.info(f"Saved {len(findings)} detailed findings for result {result_id}")
            
            return result_id
                
        except Exception as e:
            logger.error(f"Save norm control result error: {e}")
            raise
    
    async def save_findings_detailed(self, result_id: int, findings: List[Dict[str, Any]], document_id: int):
        """Сохранение детальной информации о каждом нарушении"""
        import json
        
        def _save_findings(conn):
            with conn.cursor() as cursor:
                for finding in findings:
                    # Определяем тип нарушения
                    finding_type = finding.get('type', 'violation')
                    if finding_type == 'critical':
                        finding_type = 'violation'
                        severity_level = 5
                    elif finding_type == 'warning':
                        finding_type = 'warning'
                        severity_level = 3
                    elif finding_type == 'info':
                        finding_type = 'info'
                        severity_level = 1
                    else:
                        severity_level = 2
                    
                    # Определяем категорию на основе кода
                    code = finding.get('code', '')
                    category = self.determine_finding_category(code, finding.get('description', ''))
                    
                    # Ищем связанный нормативный документ (clause_id)
                    clause_id = self.find_related_clause_id(finding, cursor)
                    
                    # Формируем ссылку на место в документе
                    element_reference = {
                        "page_number": finding.get('page_number', 1),
                        "finding_code": code,
                        "location": finding.get('location', 'Не указано'),
                        "element_type": finding.get('element_type', 'text'),
                        "bounding_box": finding.get('bounding_box', None)
                    }
                    
                    cursor.execute("""
                        INSERT INTO findings 
                        (norm_control_result_id, finding_type, severity_level, category,
                         title, description, recommendation, related_clause_id,
                         related_clause_text, element_reference, rule_applied, confidence_score)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        result_id,
                        finding_type,
                        severity_level,
                        category,
                        finding.get('title', finding.get('description', 'Нарушение требований'))[:200],
                        finding.get('description', ''),
                        finding.get('recommendation', ''),
                        clause_id,
                        finding.get('related_clause_text', ''),
                        json.dumps(element_reference),
                        finding.get('rule_applied', ''),
                        finding.get('confidence_score', 0.8)
                    ))
        
        try:
            self.db_connection.execute_in_transaction(_save_findings)
        except Exception as e:
            logger.error(f"Error saving findings: {e}")
            raise
    
    def determine_finding_category(self, code: str, description: str) -> str:
        """Определение категории нарушения"""
        # Простая логика определения категории
        if "общие" in description.lower() or "general" in description.lower():
            return "general_requirements"
        elif "текст" in description.lower() or "text" in description.lower():
            return "text_part"
        elif "график" in description.lower() or "graphic" in description.lower():
            return "graphical_part"
        else:
            return "compliance"
    
    def find_related_clause_id(self, finding: Dict[str, Any], cursor) -> Optional[int]:
        """Поиск связанного нормативного документа"""
        try:
            # Простая логика поиска связанного документа
            code = finding.get('code', '')
            if code:
                cursor.execute("""
                    SELECT id FROM normative_clauses 
                    WHERE code = %s OR title ILIKE %s
                    LIMIT 1
                """, (code, f"%{code}%"))
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            logger.warning(f"Error finding related clause: {e}")
        
        return None
