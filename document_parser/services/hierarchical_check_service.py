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
            logger.info(f"📊 [HIERARCHICAL] Memory usage before check: {check_memory_pressure()}")
            start_time = datetime.now()
            
            # Этап 1: Быстрая проверка первой страницы
            logger.info(f"📄 [HIERARCHICAL] Stage 1: Quick first page analysis")
            stage1_start = datetime.now()
            first_page_info = await self.analyze_first_page(document_id)
            stage1_time = (datetime.now() - stage1_start).total_seconds()
            logger.info(f"📄 [HIERARCHICAL] Stage 1 completed in {stage1_time:.2f}s")
            logger.info(f"📄 [HIERARCHICAL] Stage 1 result: {first_page_info.get('project_info', {}).get('project_name', 'Unknown')}")
            
            # Этап 2: Проверка всего документа на соответствие нормам
            logger.info(f"📋 [HIERARCHICAL] Stage 2: Full document norm compliance check")
            stage2_start = datetime.now()
            norm_compliance_results = await self.check_norm_compliance(document_id, first_page_info)
            stage2_time = (datetime.now() - stage2_start).total_seconds()
            logger.info(f"📋 [HIERARCHICAL] Stage 2 completed in {stage2_time:.2f}s")
            logger.info(f"📋 [HIERARCHICAL] Stage 2 findings: {norm_compliance_results.get('total_findings', 0)} total, {norm_compliance_results.get('critical_findings', 0)} critical")
            
            # Этап 3: Выявление разделов и организация проверки по разделам
            logger.info(f"📑 [HIERARCHICAL] Stage 3: Document sections identification and organization")
            stage3_start = datetime.now()
            section_analysis = await self.analyze_document_sections(document_id, first_page_info)
            stage3_time = (datetime.now() - stage3_start).total_seconds()
            logger.info(f"📑 [HIERARCHICAL] Stage 3 completed in {stage3_time:.2f}s")
            logger.info(f"📑 [HIERARCHICAL] Stage 3 sections identified: {len(section_analysis.get('sections', []))}")
            
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
            save_start = datetime.now()
            await self.save_hierarchical_check_result(document_id, result)
            save_time = (datetime.now() - save_start).total_seconds()
            logger.info(f"💾 [HIERARCHICAL] Results saved in {save_time:.2f}s")
            
            logger.info(f"✅ [HIERARCHICAL] Hierarchical check completed for document {document_id} in {total_time:.2f}s")
            logger.info(f"📊 [HIERARCHICAL] Memory usage after check: {check_memory_pressure()}")
            logger.info(f"📈 [HIERARCHICAL] Performance summary:")
            logger.info(f"   - Stage 1 (First page): {stage1_time:.2f}s")
            logger.info(f"   - Stage 2 (Norm compliance): {stage2_time:.2f}s")
            logger.info(f"   - Stage 3 (Sections): {stage3_time:.2f}s")
            logger.info(f"   - Save results: {save_time:.2f}s")
            logger.info(f"   - Total time: {total_time:.2f}s")
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
            logger.debug(f"📄 [FIRST_PAGE] Fetching first page content for document {document_id}")
            first_page = self.get_first_page_content(document_id)
            if not first_page:
                logger.error(f"📄 [FIRST_PAGE] First page not found for document {document_id}")
                return {"error": "First page not found"}
            
            logger.debug(f"📄 [FIRST_PAGE] First page content length: {len(first_page.get('content', ''))} characters")
            
            # Анализируем содержимое первой страницы
            logger.debug(f"📄 [FIRST_PAGE] Extracting project info from content")
            project_info = await self.extract_project_info(first_page.get("content", ""))
            logger.debug(f"📄 [FIRST_PAGE] Extracting document metadata from content")
            document_metadata = await self.extract_document_metadata(first_page.get("content", ""))
            
            analysis_result = {
                "page_number": 1,
                "content_length": len(first_page.get("content", "")),
                "project_info": project_info,
                "document_metadata": document_metadata,
                "analysis_timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"📄 [FIRST_PAGE] Project info extracted: {project_info.get('project_name', 'Unknown')} - {project_info.get('project_stage', 'Unknown')}")
            logger.info(f"📄 [FIRST_PAGE] Document metadata: {document_metadata.get('document_mark', 'Unknown')} - {document_metadata.get('scale', 'Unknown')}")
            
            logger.info(f"📄 [FIRST_PAGE] First page analysis completed: {analysis_result.get('project_info', {}).get('project_name', 'Unknown')}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"❌ [FIRST_PAGE] First page analysis failed: {e}")
            return {"error": str(e)}
    
    async def extract_project_info(self, content: str) -> Dict[str, Any]:
        """Извлечение информации о проекте из первой страницы"""
        try:
            logger.info(f"🔍 [PROJECT_INFO] Extracting project information from content")
            logger.debug(f"🔍 [PROJECT_INFO] Content length: {len(content)} characters")
            
            # Инициализируем результат
            project_info = {
                "project_name": "Неизвестный проект",
                "project_stage": "Неизвестная стадия",
                "project_type": "Строительный",
                "document_set": "Неизвестный комплект",
                "project_code": "Неизвестный шифр",
                "confidence": 0.5
            }
            
            # Разбиваем контент на строки
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            logger.debug(f"🔍 [PROJECT_INFO] Processing {len(lines)} non-empty lines")
            
            # Поиск шифра проекта (паттерн: Е110-0038-УКК.24.848-РД-01-02.12.032-АР)
            project_code = self.extract_project_code(content)
            if project_code:
                project_info["project_code"] = project_code
                project_info["confidence"] += 0.2
                logger.info(f"🔍 [PROJECT_INFO] Found project code: {project_code}")
            
            # Поиск названия проекта
            project_name = self.extract_project_name(content, lines)
            if project_name:
                project_info["project_name"] = project_name
                project_info["confidence"] += 0.2
                logger.info(f"🔍 [PROJECT_INFO] Found project name: {project_name}")
            
            # Определение стадии проектирования
            project_stage = self.extract_project_stage(content)
            if project_stage:
                project_info["project_stage"] = project_stage
                project_info["confidence"] += 0.1
                logger.info(f"🔍 [PROJECT_INFO] Found project stage: {project_stage}")
            
            # Определение марки комплекта
            document_set = self.extract_document_set(content, project_code)
            if document_set:
                project_info["document_set"] = document_set
                project_info["confidence"] += 0.2
                logger.info(f"🔍 [PROJECT_INFO] Found document set: {document_set}")
            
            # Ограничиваем уверенность до 1.0
            project_info["confidence"] = min(project_info["confidence"], 1.0)
            
            logger.info(f"🔍 [PROJECT_INFO] Final project info: {project_info}")
            return project_info
            
        except Exception as e:
            logger.error(f"❌ [PROJECT_INFO] Error extracting project info: {e}")
            return {"project_name": "Неизвестный проект", "error": str(e)}
    
    def extract_project_code(self, content: str) -> Optional[str]:
        """Извлечение шифра проекта"""
        try:
            # Паттерны для поиска шифра проекта
            import re
            
            # Паттерн для шифра типа Е110-0038-УКК.24.848-РД-01-02.12.032-АР
            patterns = [
                r'[А-Я]\d{3}-\d{4}-[А-Я]{2,3}\.\d{2}\.\d{3}-[А-Я]{2}-\d{2}-\d{2}\.\d{3}-[А-Я]{2}',
                r'[А-Я]\d{3}-\d{4}-[А-Я]{2,3}\.\d{2}\.\d{3}-[А-Я]{2}-\d{2}-\d{2}\.\d{3}-[А-Я]{2}',
                r'[А-Я]\d{3}-\d{4}-[А-Я]{2,3}\.\d{2}\.\d{3}-[А-Я]{2}-\d{2}-\d{2}\.\d{3}-[А-Я]{2}',
                r'[А-Я]\d{3}-\d{4}-[А-Я]{2,3}\.\d{2}\.\d{3}-[А-Я]{2}-\d{2}-\d{2}\.\d{3}-[А-Я]{2}'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, content)
                if matches:
                    return matches[0]
            
            # Поиск по ключевым словам
            lines = content.split('\n')
            for line in lines:
                if any(keyword in line.upper() for keyword in ['Е110', 'УКК', 'РД', 'АР']):
                    # Извлекаем код из строки
                    words = line.split()
                    for word in words:
                        if any(keyword in word.upper() for keyword in ['Е110', 'УКК', 'РД', 'АР']):
                            return word.strip()
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting project code: {e}")
            return None
    
    def extract_project_name(self, content: str, lines: List[str]) -> Optional[str]:
        """Извлечение названия проекта"""
        try:
            # Ключевые слова для поиска названия проекта
            keywords = ['комбинат', 'фабрика', 'завод', 'комплекс', 'объект', 'сооружение']
            
            # Ищем строки с ключевыми словами и собираем все связанные строки
            project_name_parts = []
            found_keyword = False
            
            for i, line in enumerate(lines):
                line_lower = line.lower()
                line_stripped = line.strip()
                
                # Проверяем, содержит ли строка ключевые слова
                if any(keyword in line_lower for keyword in keywords):
                    found_keyword = True
                    if len(line_stripped) > 10:
                        project_name_parts.append(line_stripped)
                    
                    # Собираем следующие строки, которые могут быть частью названия
                    for j in range(i + 1, min(i + 5, len(lines))):  # Проверяем следующие 4 строки
                        next_line = lines[j].strip()
                        if len(next_line) > 5 and not next_line.isdigit():
                            # Если строка содержит технические термины или продолжение названия
                            if any(term in next_line.lower() for term in ['мощность', 'млн', 'год', 'месторождение', 'район', 'область', 'рудник', 'комплекс', 'ствол', 'копер']):
                                project_name_parts.append(next_line)
                            elif next_line.isupper() and len(next_line) > 10:
                                project_name_parts.append(next_line)
                            else:
                                break
                    break
            
            # Если нашли части названия, объединяем их
            if project_name_parts:
                return ' '.join(project_name_parts)
            
            # Поиск по паттерну "НАЗВАНИЕ ПРОЕКТА"
            for line in lines:
                if 'название' in line.lower() and 'проект' in line.lower():
                    # Ищем следующую строку с названием
                    line_index = lines.index(line)
                    if line_index + 1 < len(lines):
                        next_line = lines[line_index + 1].strip()
                        if len(next_line) > 10:
                            return next_line
            
            # Поиск по верхнему регистру (часто название проекта пишется заглавными буквами)
            for line in lines:
                if line.isupper() and len(line.strip()) > 20:
                    return line.strip()
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting project name: {e}")
            return None
    
    def extract_project_stage(self, content: str) -> Optional[str]:
        """Извлечение стадии проектирования"""
        try:
            content_lower = content.lower()
            
            if 'рабочая документация' in content_lower or 'рабочая' in content_lower:
                return "Рабочая документация"
            elif 'проектная документация' in content_lower or 'проектная' in content_lower:
                return "Проектная документация"
            elif 'эскизная документация' in content_lower or 'эскизная' in content_lower:
                return "Эскизная документация"
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting project stage: {e}")
            return None
    
    def extract_document_set(self, content: str, project_code: Optional[str]) -> Optional[str]:
        """Извлечение марки комплекта документов"""
        try:
            content_lower = content.lower()
            
            # Определение по шифру проекта
            if project_code:
                if '-АР' in project_code.upper():
                    return "Архитектурные решения"
                elif '-КР' in project_code.upper():
                    return "Конструктивные решения"
                elif '-ОВ' in project_code.upper():
                    return "Отопление и вентиляция"
                elif '-ВК' in project_code.upper():
                    return "Водоснабжение и канализация"
                elif '-ЭС' in project_code.upper():
                    return "Электроснабжение"
                elif '-СС' in project_code.upper():
                    return "Сети связи"
                elif '-ПОС' in project_code.upper():
                    return "Проект организации строительства"
                elif '-ПТ' in project_code.upper():
                    return "Проект производства работ"
            
            # Определение по ключевым словам в контенте
            if 'архитектурн' in content_lower:
                return "Архитектурные решения"
            elif 'конструктивн' in content_lower:
                return "Конструктивные решения"
            elif 'отоплен' in content_lower or 'вентиляц' in content_lower:
                return "Отопление и вентиляция"
            elif 'водоснабжен' in content_lower or 'канализац' in content_lower:
                return "Водоснабжение и канализация"
            elif 'электроснабжен' in content_lower:
                return "Электроснабжение"
            elif 'связ' in content_lower:
                return "Сети связи"
            elif 'организац' in content_lower and 'строительств' in content_lower:
                return "Проект организации строительства"
            elif 'производств' in content_lower and 'работ' in content_lower:
                return "Проект производства работ"
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting document set: {e}")
            return None
    
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
            
            logger.info(f"📋 [NORM_COMPLIANCE] Project stage: {project_stage}, Document set: {document_set}")
            
            # Получаем все страницы документа
            logger.debug(f"📋 [NORM_COMPLIANCE] Fetching all pages content for document {document_id}")
            pages = self.get_all_pages_content(document_id)
            
            # Получаем реальное количество уникальных страниц
            total_pages = len(set(page["page_number"] for page in pages))
            compliant_pages = 0
            findings = []
            
            logger.info(f"📋 [NORM_COMPLIANCE] Total pages to check: {total_pages}")
            
            for page_data in pages:
                page_number = page_data["page_number"]
                content = page_data["content"]
                
                logger.info(f"📋 [NORM_COMPLIANCE] Checking page {page_number}/{total_pages} (content length: {len(content)} chars)")
                
                # Проверяем страницу на соответствие нормам
                page_start = datetime.now()
                page_findings = await self.check_page_norm_compliance(
                    content, page_number, project_stage, document_set
                )
                page_time = (datetime.now() - page_start).total_seconds()
                
                findings.extend(page_findings)
                
                if not page_findings:
                    compliant_pages += 1
                
                logger.debug(f"📋 [NORM_COMPLIANCE] Page {page_number} checked in {page_time:.2f}s, findings: {len(page_findings)}")
            
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
                        "content": result[0],  # element_content
                        "page_number": result[1]  # page_number
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
                        "content": row[0],  # element_content
                        "page_number": row[1]  # page_number
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
