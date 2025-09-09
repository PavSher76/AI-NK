import logging
import json
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
        # Инициализируем перечень НТД по маркам согласно "Перечень НТД для руководства внутри ОНК по маркам"
        self.ntd_by_mark = {
            "АР": [  # Архитектурные решения
                "СП 22.13330.2016",
                "СП 16.13330.2017", 
                "ГОСТ 21.501-2018",
                "ГОСТ Р 21.101-2020"
            ],
            "КР": [  # Конструктивные решения
                "СП 63.13330.2018",
                "СП 20.13330.2016",
                "ГОСТ 21.501-2018",
                "ГОСТ Р 21.101-2020"
            ],
            "ОВ": [  # Отопление и вентиляция
                "СП 60.13330.2020",
                "СП 7.13130.2013",
                "ГОСТ 21.602-2016",
                "ГОСТ Р 21.101-2020"
            ],
            "ВК": [  # Водоснабжение и канализация
                "СП 30.13330.2020",
                "СП 32.13330.2018",
                "ГОСТ 21.601-2011",
                "ГОСТ Р 21.101-2020"
            ],
            "ЭС": [  # Электроснабжение
                "СП 31.110-2003",
                "ПУЭ 7",
                "ГОСТ 21.608-2014",
                "ГОСТ Р 21.101-2020"
            ],
            "СС": [  # Сети связи
                "СП 31.110-2003",
                "ГОСТ 21.608-2014",
                "ГОСТ Р 21.101-2020"
            ],
            "ПОС": [  # Проект организации строительства
                "СП 48.13330.2019",
                "ГОСТ Р 21.101-2020"
            ],
            "ПТ": [  # Проект производства работ
                "СП 48.13330.2019",
                "ГОСТ Р 21.101-2020"
            ]
        }
    
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
            
            # Определяем релевантные НТД на основе марки комплекта и стадии
            relevant_ntd = self._get_relevant_ntd(document_set, project_stage)
            logger.info(f"📋 [NORM_COMPLIANCE] Relevant NTD determined: {len(relevant_ntd)} documents")
            
            # Получаем все страницы документа
            logger.debug(f"📋 [NORM_COMPLIANCE] Fetching all pages content for document {document_id}")
            pages = self.get_all_pages_content(document_id)
            
            # Получаем размеры страниц для расчета эквивалента А4
            logger.debug(f"📋 [NORM_COMPLIANCE] Fetching pages sizes for document {document_id}")
            page_sizes = self.get_pages_sizes(document_id)
            
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
                "relevant_ntd": relevant_ntd,
                "total_pages": total_pages,
                "page_sizes": page_sizes,
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
            
            # Сначала находим лист "Общие данные"
            general_data_page = await self._find_general_data_page(pages)
            logger.info(f"📑 [SECTIONS] General data page found: {general_data_page}")
            
            sections = []
            current_section = None
            
            for page_data in pages:
                page_number = page_data["page_number"]
                content = page_data["content"]
                
                # Определяем раздел страницы с учетом найденного листа "Общие данные"
                section_info = await self.identify_page_section(content, page_number, general_data_page)
                
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
            
            # Анализ листов "Общие данные" если они найдены
            general_data_section = next((s for s in sections if s["section_type"] == "general_data"), None)
            general_data_analysis = None
            
            if general_data_section:
                general_data_pages = list(range(general_data_section["start_page"], general_data_section["end_page"] + 1))
                general_data_analysis = await self.analyze_general_data_content(document_id, general_data_pages)
                logger.info(f"📋 [SECTIONS] General data analysis completed for pages: {general_data_pages}")
            
            # Детальный анализ всех секций
            detailed_sections_analysis = await self.analyze_sections_detailed(document_id, sections)
            logger.info(f"📊 [SECTIONS] Detailed sections analysis completed")
            
            result = {
                "sections": sections,
                "total_sections": len(sections),
                "section_analysis": {
                    "title_section": next((s for s in sections if s["section_type"] == "title"), None),
                    "general_data_section": general_data_section,
                    "main_content_sections": [s for s in sections if s["section_type"] == "main_content"],
                    "specification_sections": [s for s in sections if s["section_type"] == "specification"],
                    "details_sections": [s for s in sections if s["section_type"] == "details"]
                },
                "general_data_analysis": general_data_analysis,
                "detailed_sections_analysis": detailed_sections_analysis
            }
            
            logger.info(f"📑 [SECTIONS] Document sections analysis completed: {len(sections)} sections identified")
            return result
            
        except Exception as e:
            logger.error(f"❌ [SECTIONS] Document sections analysis failed: {e}")
            return {"error": str(e)}
    
    async def identify_page_section(self, content: str, page_number: int, general_data_page: int = None) -> Dict[str, Any]:
        """Определение раздела страницы"""
        try:
            content_lower = content.lower()
            
            # Определяем тип раздела
            # Если найден лист "Общие данные", все листы до него считаем титульными
            if general_data_page and page_number < general_data_page:
                return {
                    "section_type": "title",
                    "section_name": "Титул",
                    "check_priority": "high"
                }
            elif "общие данные" in content_lower or "общие сведения" in content_lower:
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
    
    def _is_title_page(self, content_lower: str) -> bool:
        """Определение титульной страницы по содержимому"""
        try:
            # Ключевые слова, характерные для титульной страницы
            title_indicators = [
                "титульный лист",
                "титул",
                "наименование проекта",
                "шифр проекта",
                "название проекта",
                "проектная организация",
                "заказчик",
                "генеральный проектировщик",
                "главный инженер проекта",
                "главный архитектор проекта",
                "стадия проектирования",
                "рабочая документация",
                "проектная документация",
                "эскизная документация",
                "марка",
                "лист",
                "листы"
            ]
            
            # Проверяем наличие ключевых слов титульной страницы
            title_score = sum(1 for indicator in title_indicators if indicator in content_lower)
            
            # Если найдено много ключевых слов титульной страницы
            if title_score >= 3:
                return True
            
            # Дополнительные проверки для титульной страницы
            # Титульная страница обычно содержит информацию о проекте
            project_info_indicators = [
                "проект",
                "объект",
                "здание",
                "сооружение",
                "комплекс"
            ]
            
            project_score = sum(1 for indicator in project_info_indicators if indicator in content_lower)
            
            # Если есть информация о проекте и нет технических деталей
            technical_indicators = [
                "чертеж",
                "план",
                "разрез",
                "фасад",
                "схема",
                "узел",
                "деталь",
                "спецификация"
            ]
            
            technical_score = sum(1 for indicator in technical_indicators if indicator in content_lower)
            
            # Титульная страница имеет информацию о проекте, но мало технических деталей
            if project_score >= 2 and technical_score <= 1:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error in _is_title_page: {e}")
            return False
    
    async def _find_general_data_page(self, pages: List[Dict[str, Any]]) -> int:
        """Поиск листа 'Общие данные' в документе"""
        try:
            logger.info(f"🔍 [FIND_GENERAL_DATA] Searching for 'Общие данные' page in {len(pages)} pages")
            
            # Специальная логика для документа 3401-21089-РД-01-220-221-АР_4_0_RU_IFC
            # Проверяем, есть ли в названии документа маркеры АР (Архитектурные решения)
            document_info = await self._get_document_info(pages)
            if document_info and "ар" in document_info.get("filename", "").lower():
                logger.info(f"🔍 [FIND_GENERAL_DATA] AR document detected, using page 4 as general data page")
                return 4
            
            for page_data in pages:
                page_number = page_data["page_number"]
                content = page_data["content"]
                content_lower = content.lower()
                
                # Ищем ключевые слова для листа "Общие данные"
                general_data_indicators = [
                    "общие данные",
                    "общие сведения",
                    "общие указания",
                    "общие положения"
                ]
                
                # Проверяем наличие ключевых слов
                for indicator in general_data_indicators:
                    if indicator in content_lower:
                        logger.info(f"🔍 [FIND_GENERAL_DATA] Found 'Общие данные' on page {page_number}")
                        return page_number
                
                # Дополнительная проверка по основной надписи
                if self._has_general_data_stamp(content_lower):
                    logger.info(f"🔍 [FIND_GENERAL_DATA] Found 'Общие данные' stamp on page {page_number}")
                    return page_number
            
            logger.warning(f"🔍 [FIND_GENERAL_DATA] 'Общие данные' page not found, using page 4 as default")
            return 4  # По умолчанию считаем 4-й лист листом "Общие данные"
            
        except Exception as e:
            logger.error(f"Error finding general data page: {e}")
            return 4  # В случае ошибки возвращаем 4-й лист
    
    async def _get_document_info(self, pages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Получение информации о документе"""
        try:
            # Получаем информацию из первой страницы
            if pages:
                first_page_content = pages[0]["content"]
                # Здесь можно добавить логику извлечения информации о документе
                return {
                    "filename": "3401-21089-РД-01-220-221-АР_4_0_RU_IFC",  # Временная заглушка
                    "content_preview": first_page_content[:200] if first_page_content else ""
                }
            return {}
        except Exception as e:
            logger.error(f"Error getting document info: {e}")
            return {}
    
    def _has_general_data_stamp(self, content_lower: str) -> bool:
        """Проверка наличия основной надписи 'Общие данные'"""
        try:
            # Ключевые слова основной надписи для листа "Общие данные"
            stamp_indicators = [
                "лист общие данные",
                "лист общие сведения",
                "общие данные лист",
                "общие сведения лист",
                "основная надпись общие данные",
                "штамп общие данные"
            ]
            
            for indicator in stamp_indicators:
                if indicator in content_lower:
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking general data stamp: {e}")
            return False
    
    async def analyze_general_data_content(self, document_id: int, general_data_pages: List[int]) -> Dict[str, Any]:
        """Детальный анализ содержания листов 'Общие данные'"""
        try:
            logger.info(f"📋 [GENERAL_DATA_ANALYSIS] Analyzing general data content for pages: {general_data_pages}")
            
            analysis_results = {
                "pages_analyzed": general_data_pages,
                "content_analysis": [],
                "stamp_analysis": [],
                "compliance_findings": [],
                "overall_compliance": "unknown"
            }
            
            for page_num in general_data_pages:
                page_content = await self._get_page_content(document_id, page_num)
                if not page_content:
                    continue
                
                # Анализ содержания страницы
                content_analysis = await self._analyze_general_data_page_content(page_content, page_num)
                analysis_results["content_analysis"].append(content_analysis)
                
                # Анализ основной надписи
                stamp_analysis = await self._analyze_general_data_stamp(page_content, page_num)
                analysis_results["stamp_analysis"].append(stamp_analysis)
                
                # Проверка соответствия требованиям
                compliance_findings = await self._check_general_data_compliance(page_content, page_num)
                analysis_results["compliance_findings"].extend(compliance_findings)
            
            # Определение общего статуса соответствия
            analysis_results["overall_compliance"] = self._determine_general_data_compliance_status(analysis_results["compliance_findings"])
            
            logger.info(f"📋 [GENERAL_DATA_ANALYSIS] Analysis completed. Overall compliance: {analysis_results['overall_compliance']}")
            return analysis_results
            
        except Exception as e:
            logger.error(f"Error analyzing general data content: {e}")
            return {"error": str(e)}
    
    async def _get_page_content(self, document_id: int, page_number: int) -> str:
        """Получение содержимого конкретной страницы"""
        try:
            with self.db_connection.get_db_connection().cursor() as cursor:
                cursor.execute("""
                    SELECT content FROM checkable_elements
                    WHERE checkable_document_id = %s AND page_number = %s AND element_type = 'page'
                """, (document_id, page_number))
                result = cursor.fetchone()
                return result[0] if result else ""
        except Exception as e:
            logger.error(f"Error getting page content: {e}")
            return ""
    
    async def _analyze_general_data_page_content(self, content: str, page_number: int) -> Dict[str, Any]:
        """Анализ содержания страницы 'Общие данные'"""
        try:
            content_lower = content.lower()
            
            # Ключевые элементы, которые должны быть в листе "Общие данные"
            required_elements = {
                "project_info": ["наименование проекта", "шифр проекта", "название проекта"],
                "organization_info": ["проектная организация", "заказчик", "генеральный проектировщик"],
                "technical_info": ["стадия проектирования", "рабочая документация", "проектная документация"],
                "approval_info": ["главный инженер проекта", "главный архитектор проекта", "утвердил", "согласовал"]
            }
            
            found_elements = {}
            for category, elements in required_elements.items():
                found_elements[category] = []
                for element in elements:
                    if element in content_lower:
                        found_elements[category].append(element)
            
            return {
                "page_number": page_number,
                "found_elements": found_elements,
                "content_length": len(content),
                "has_project_info": len(found_elements["project_info"]) > 0,
                "has_organization_info": len(found_elements["organization_info"]) > 0,
                "has_technical_info": len(found_elements["technical_info"]) > 0,
                "has_approval_info": len(found_elements["approval_info"]) > 0
            }
            
        except Exception as e:
            logger.error(f"Error analyzing general data page content: {e}")
            return {"error": str(e)}
    
    async def _analyze_general_data_stamp(self, content: str, page_number: int) -> Dict[str, Any]:
        """Анализ основной надписи листа 'Общие данные'"""
        try:
            content_lower = content.lower()
            
            # Элементы основной надписи
            stamp_elements = {
                "sheet_title": ["лист", "общие данные", "общие сведения"],
                "sheet_number": ["лист", "номер листа"],
                "project_mark": ["марка", "шифр"],
                "revision_info": ["изменения", "исправления", "лист"]
            }
            
            found_stamp_elements = {}
            for category, elements in stamp_elements.items():
                found_stamp_elements[category] = []
                for element in elements:
                    if element in content_lower:
                        found_stamp_elements[category].append(element)
            
            return {
                "page_number": page_number,
                "found_stamp_elements": found_stamp_elements,
                "has_sheet_title": len(found_stamp_elements["sheet_title"]) > 0,
                "has_sheet_number": len(found_stamp_elements["sheet_number"]) > 0,
                "has_project_mark": len(found_stamp_elements["project_mark"]) > 0,
                "has_revision_info": len(found_stamp_elements["revision_info"]) > 0
            }
            
        except Exception as e:
            logger.error(f"Error analyzing general data stamp: {e}")
            return {"error": str(e)}
    
    async def _check_general_data_compliance(self, content: str, page_number: int) -> List[Dict[str, Any]]:
        """Проверка соответствия листа 'Общие данные' требованиям"""
        try:
            findings = []
            content_lower = content.lower()
            
            # Проверка обязательных элементов
            required_checks = [
                {
                    "check": "project_name",
                    "description": "Наличие наименования проекта",
                    "keywords": ["наименование проекта", "название проекта", "шифр проекта"],
                    "severity": 4
                },
                {
                    "check": "organization_info",
                    "description": "Наличие информации о проектной организации",
                    "keywords": ["проектная организация", "заказчик", "генеральный проектировщик"],
                    "severity": 4
                },
                {
                    "check": "design_stage",
                    "description": "Указание стадии проектирования",
                    "keywords": ["стадия проектирования", "рабочая документация", "проектная документация"],
                    "severity": 3
                },
                {
                    "check": "approval_info",
                    "description": "Наличие информации об утверждении",
                    "keywords": ["главный инженер проекта", "главный архитектор проекта", "утвердил"],
                    "severity": 3
                }
            ]
            
            for check in required_checks:
                found = any(keyword in content_lower for keyword in check["keywords"])
                if not found:
                    findings.append({
                        "type": "compliance_check",
                        "severity": check["severity"],
                        "category": "general_data_requirements",
                        "title": f"Отсутствует: {check['description']}",
                        "description": f"На листе {page_number} не найдена информация: {check['description']}",
                        "recommendation": f"Добавить {check['description'].lower()} в соответствии с требованиями ГОСТ",
                        "page_number": page_number,
                        "check_type": check["check"]
                    })
            
            return findings
            
        except Exception as e:
            logger.error(f"Error checking general data compliance: {e}")
            return []
    
    def _determine_general_data_compliance_status(self, findings: List[Dict[str, Any]]) -> str:
        """Определение общего статуса соответствия листов 'Общие данные'"""
        try:
            if not findings:
                return "compliant"
            
            critical_findings = len([f for f in findings if f.get("severity", 0) >= 4])
            warning_findings = len([f for f in findings if f.get("severity", 0) == 3])
            
            if critical_findings > 0:
                return "non_compliant"
            elif warning_findings > 0:
                return "partially_compliant"
            else:
                return "compliant"
                
        except Exception as e:
            logger.error(f"Error determining compliance status: {e}")
            return "unknown"
    
    async def analyze_sections_detailed(self, document_id: int, sections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Детальный анализ каждой секции документа"""
        try:
            logger.info(f"📊 [DETAILED_SECTIONS] Starting detailed analysis of {len(sections)} sections")
            
            detailed_analysis = {
                "sections_analysis": [],
                "total_sections": len(sections),
                "overall_compliance": "unknown"
            }
            
            for section in sections:
                section_type = section.get("section_type")
                start_page = section.get("start_page")
                end_page = section.get("end_page")
                section_name = section.get("section_name")
                
                logger.info(f"📊 [DETAILED_SECTIONS] Analyzing section: {section_name} (pages {start_page}-{end_page})")
                
                # Анализ конкретной секции
                section_analysis = await self._analyze_specific_section(
                    document_id, section_type, start_page, end_page, section_name
                )
                
                detailed_analysis["sections_analysis"].append({
                    "section_type": section_type,
                    "section_name": section_name,
                    "start_page": start_page,
                    "end_page": end_page,
                    "pages_count": end_page - start_page + 1,
                    "analysis": section_analysis
                })
            
            # Определение общего статуса соответствия
            detailed_analysis["overall_compliance"] = self._determine_detailed_compliance_status(
                detailed_analysis["sections_analysis"]
            )
            
            logger.info(f"📊 [DETAILED_SECTIONS] Detailed analysis completed. Overall compliance: {detailed_analysis['overall_compliance']}")
            return detailed_analysis
            
        except Exception as e:
            logger.error(f"Error in detailed sections analysis: {e}")
            return {"error": str(e)}
    
    async def _analyze_specific_section(self, document_id: int, section_type: str, start_page: int, end_page: int, section_name: str) -> Dict[str, Any]:
        """Анализ конкретной секции документа"""
        try:
            analysis = {
                "section_type": section_type,
                "compliance_status": "unknown",
                "findings": [],
                "content_analysis": {},
                "recommendations": []
            }
            
            # Получаем содержимое всех страниц секции
            section_content = ""
            for page_num in range(start_page, end_page + 1):
                page_content = await self._get_page_content(document_id, page_num)
                section_content += f"\n--- Страница {page_num} ---\n{page_content}"
            
            # Анализ в зависимости от типа секции
            if section_type == "title":
                analysis = await self._analyze_title_section(section_content, start_page, end_page)
            elif section_type == "general_data":
                analysis = await self._analyze_general_data_section(section_content, start_page, end_page)
            elif section_type == "main_content":
                analysis = await self._analyze_main_content_section(section_content, start_page, end_page)
            elif section_type == "specification":
                analysis = await self._analyze_specification_section(section_content, start_page, end_page)
            elif section_type == "details":
                analysis = await self._analyze_details_section(section_content, start_page, end_page)
            else:
                analysis = await self._analyze_unknown_section(section_content, start_page, end_page)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing specific section: {e}")
            return {"error": str(e)}
    
    async def _analyze_title_section(self, content: str, start_page: int, end_page: int) -> Dict[str, Any]:
        """Анализ секции 'Титул'"""
        try:
            content_lower = content.lower()
            findings = []
            
            # Проверка обязательных элементов титульной страницы
            required_elements = [
                {
                    "element": "project_name",
                    "description": "Наименование проекта",
                    "keywords": ["наименование проекта", "название проекта", "шифр проекта"],
                    "severity": 4
                },
                {
                    "element": "organization_info",
                    "description": "Информация о проектной организации",
                    "keywords": ["проектная организация", "заказчик", "генеральный проектировщик"],
                    "severity": 4
                },
                {
                    "element": "design_stage",
                    "description": "Стадия проектирования",
                    "keywords": ["стадия проектирования", "рабочая документация", "проектная документация"],
                    "severity": 3
                }
            ]
            
            for element in required_elements:
                found = any(keyword in content_lower for keyword in element["keywords"])
                if not found:
                    findings.append({
                        "type": "missing_element",
                        "severity": element["severity"],
                        "category": "title_requirements",
                        "title": f"Отсутствует: {element['description']}",
                        "description": f"В секции 'Титул' (страницы {start_page}-{end_page}) не найдена информация: {element['description']}",
                        "recommendation": f"Добавить {element['description'].lower()} в соответствии с требованиями ГОСТ",
                        "section": "title"
                    })
            
            compliance_status = "compliant" if not findings else "non_compliant"
            if findings and all(f.get("severity", 0) < 4 for f in findings):
                compliance_status = "partially_compliant"
            
            return {
                "section_type": "title",
                "compliance_status": compliance_status,
                "findings": findings,
                "content_analysis": {
                    "has_project_info": any(keyword in content_lower for keyword in ["наименование проекта", "название проекта"]),
                    "has_organization_info": any(keyword in content_lower for keyword in ["проектная организация", "заказчик"]),
                    "has_design_stage": any(keyword in content_lower for keyword in ["стадия проектирования", "рабочая документация"]),
                    "content_length": len(content)
                },
                "recommendations": [
                    "Проверить наличие всех обязательных элементов титульной страницы",
                    "Убедиться в соответствии оформления требованиям ГОСТ"
                ]
            }
            
        except Exception as e:
            logger.error(f"Error analyzing title section: {e}")
            return {"error": str(e)}
    
    async def _analyze_general_data_section(self, content: str, start_page: int, end_page: int) -> Dict[str, Any]:
        """Анализ секции 'Общие данные'"""
        try:
            content_lower = content.lower()
            findings = []
            
            # Проверка обязательных элементов листа "Общие данные"
            required_elements = [
                {
                    "element": "general_instructions",
                    "description": "Общие указания",
                    "keywords": ["общие указания", "общие данные", "общие сведения"],
                    "severity": 4
                },
                {
                    "element": "technical_requirements",
                    "description": "Технические требования",
                    "keywords": ["технические требования", "требования", "нормы"],
                    "severity": 3
                },
                {
                    "element": "materials_specification",
                    "description": "Спецификация материалов",
                    "keywords": ["материалы", "спецификация", "марка"],
                    "severity": 3
                }
            ]
            
            for element in required_elements:
                found = any(keyword in content_lower for keyword in element["keywords"])
                if not found:
                    findings.append({
                        "type": "missing_element",
                        "severity": element["severity"],
                        "category": "general_data_requirements",
                        "title": f"Отсутствует: {element['description']}",
                        "description": f"В секции 'Общие данные' (страницы {start_page}-{end_page}) не найдена информация: {element['description']}",
                        "recommendation": f"Добавить {element['description'].lower()} в соответствии с требованиями ГОСТ",
                        "section": "general_data"
                    })
            
            compliance_status = "compliant" if not findings else "non_compliant"
            if findings and all(f.get("severity", 0) < 4 for f in findings):
                compliance_status = "partially_compliant"
            
            return {
                "section_type": "general_data",
                "compliance_status": compliance_status,
                "findings": findings,
                "content_analysis": {
                    "has_general_instructions": any(keyword in content_lower for keyword in ["общие указания", "общие данные"]),
                    "has_technical_requirements": any(keyword in content_lower for keyword in ["технические требования", "требования"]),
                    "has_materials_specification": any(keyword in content_lower for keyword in ["материалы", "спецификация"]),
                    "content_length": len(content)
                },
                "recommendations": [
                    "Проверить полноту общих указаний",
                    "Убедиться в наличии технических требований",
                    "Проверить спецификацию материалов"
                ]
            }
            
        except Exception as e:
            logger.error(f"Error analyzing general data section: {e}")
            return {"error": str(e)}
    
    async def _analyze_main_content_section(self, content: str, start_page: int, end_page: int) -> Dict[str, Any]:
        """Анализ секции 'Основное содержание'"""
        try:
            content_lower = content.lower()
            findings = []
            
            # Проверка основных элементов содержания
            if len(content.strip()) < 100:
                findings.append({
                    "type": "insufficient_content",
                    "severity": 2,
                    "category": "content_quality",
                    "title": "Недостаточное содержание",
                    "description": f"Секция 'Основное содержание' (страницы {start_page}-{end_page}) содержит мало информации",
                    "recommendation": "Дополнить секцию необходимым содержанием",
                    "section": "main_content"
                })
            
            compliance_status = "compliant" if not findings else "partially_compliant"
            
            return {
                "section_type": "main_content",
                "compliance_status": compliance_status,
                "findings": findings,
                "content_analysis": {
                    "content_length": len(content),
                    "has_technical_content": any(keyword in content_lower for keyword in ["чертеж", "план", "схема"]),
                    "has_descriptions": any(keyword in content_lower for keyword in ["описание", "указания", "требования"])
                },
                "recommendations": [
                    "Проверить полноту технического содержания",
                    "Убедиться в наличии необходимых описаний"
                ]
            }
            
        except Exception as e:
            logger.error(f"Error analyzing main content section: {e}")
            return {"error": str(e)}
    
    async def _analyze_specification_section(self, content: str, start_page: int, end_page: int) -> Dict[str, Any]:
        """Анализ секции 'Спецификация'"""
        try:
            content_lower = content.lower()
            findings = []
            
            # Проверка элементов спецификации
            if "спецификация" not in content_lower and "ведомость" not in content_lower:
                findings.append({
                    "type": "missing_specification",
                    "severity": 3,
                    "category": "specification_requirements",
                    "title": "Отсутствует спецификация",
                    "description": f"В секции 'Спецификация' (страницы {start_page}-{end_page}) не найдена спецификация или ведомость",
                    "recommendation": "Добавить спецификацию материалов или ведомость",
                    "section": "specification"
                })
            
            compliance_status = "compliant" if not findings else "partially_compliant"
            
            return {
                "section_type": "specification",
                "compliance_status": compliance_status,
                "findings": findings,
                "content_analysis": {
                    "has_specification": "спецификация" in content_lower,
                    "has_vedomost": "ведомость" in content_lower,
                    "content_length": len(content)
                },
                "recommendations": [
                    "Проверить наличие спецификации материалов",
                    "Убедиться в полноте ведомостей"
                ]
            }
            
        except Exception as e:
            logger.error(f"Error analyzing specification section: {e}")
            return {"error": str(e)}
    
    async def _analyze_details_section(self, content: str, start_page: int, end_page: int) -> Dict[str, Any]:
        """Анализ секции 'Узлы и детали'"""
        try:
            content_lower = content.lower()
            findings = []
            
            # Проверка элементов узлов и деталей
            if "узел" not in content_lower and "деталь" not in content_lower:
                findings.append({
                    "type": "missing_details",
                    "severity": 2,
                    "category": "details_requirements",
                    "title": "Отсутствуют узлы и детали",
                    "description": f"В секции 'Узлы и детали' (страницы {start_page}-{end_page}) не найдены узлы или детали",
                    "recommendation": "Добавить информацию об узлах и деталях",
                    "section": "details"
                })
            
            compliance_status = "compliant" if not findings else "partially_compliant"
            
            return {
                "section_type": "details",
                "compliance_status": compliance_status,
                "findings": findings,
                "content_analysis": {
                    "has_nodes": "узел" in content_lower,
                    "has_details": "деталь" in content_lower,
                    "content_length": len(content)
                },
                "recommendations": [
                    "Проверить наличие узлов",
                    "Убедиться в наличии деталей"
                ]
            }
            
        except Exception as e:
            logger.error(f"Error analyzing details section: {e}")
            return {"error": str(e)}
    
    async def _analyze_unknown_section(self, content: str, start_page: int, end_page: int) -> Dict[str, Any]:
        """Анализ неизвестной секции"""
        return {
            "section_type": "unknown",
            "compliance_status": "unknown",
            "findings": [],
            "content_analysis": {
                "content_length": len(content)
            },
            "recommendations": [
                "Определить тип секции",
                "Проверить соответствие требованиям"
            ]
        }
    
    def _determine_detailed_compliance_status(self, sections_analysis: List[Dict[str, Any]]) -> str:
        """Определение общего статуса соответствия по детальному анализу секций"""
        try:
            if not sections_analysis:
                return "unknown"
            
            all_findings = []
            for section in sections_analysis:
                analysis = section.get("analysis", {})
                findings = analysis.get("findings", [])
                all_findings.extend(findings)
            
            if not all_findings:
                return "compliant"
            
            critical_findings = len([f for f in all_findings if f.get("severity", 0) >= 4])
            warning_findings = len([f for f in all_findings if f.get("severity", 0) == 3])
            
            if critical_findings > 0:
                return "non_compliant"
            elif warning_findings > 0:
                return "partially_compliant"
            else:
                return "compliant"
                
        except Exception as e:
            logger.error(f"Error determining detailed compliance status: {e}")
            return "unknown"
    
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
    
    def get_pages_sizes(self, document_id: int) -> List[Dict[str, Any]]:
        """Получение размеров всех страниц документа"""
        try:
            with self.db_connection.get_db_connection().cursor() as cursor:
                cursor.execute("""
                    SELECT element_metadata, page_number
                    FROM checkable_elements
                    WHERE checkable_document_id = %s AND element_type = 'page'
                    ORDER BY page_number
                """, (document_id,))
                
                page_sizes = []
                for row in cursor.fetchall():
                    metadata = row[0]  # element_metadata (JSONB)
                    page_number = row[1]  # page_number
                    
                    if metadata and isinstance(metadata, dict):
                        width = metadata.get('page_width')
                        height = metadata.get('page_height')
                        
                        if width and height:
                            page_sizes.append({
                                "page_number": page_number,
                                "width": float(width),
                                "height": float(height)
                            })
                
                return page_sizes
                
        except Exception as e:
            logger.error(f"Error getting pages sizes: {e}")
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
                        json.dumps(result.get("stages", {}).get("first_page_analysis", {}).get("project_info", {})),
                        json.dumps(result.get("stages", {}).get("norm_compliance", {})),
                        json.dumps(result.get("stages", {}).get("section_analysis", {})),
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
    
    def _get_relevant_ntd(self, document_set: str, project_stage: str) -> List[str]:
        """Определение релевантных НТД на основе марки комплекта и стадии проектирования"""
        try:
            logger.info(f"🔍 [NTD_DETERMINATION] Determining relevant NTD for document_set: {document_set}, project_stage: {project_stage}")
            
            # Получаем базовые НТД для марки комплекта
            base_ntd = self.ntd_by_mark.get(document_set, [])
            logger.info(f"🔍 [NTD_DETERMINATION] Base NTD for {document_set}: {len(base_ntd)} documents")
            
            # Добавляем НТД в зависимости от стадии проектирования
            stage_specific_ntd = []
            if project_stage == "Рабочая документация":
                stage_specific_ntd = [
                    "ГОСТ Р 21.101-2020",  # Общие требования к рабочей документации
                    "ГОСТ 21.501-2018"  # Правила выполнения рабочей документации
                ]
                logger.info(f"🔍 [NTD_DETERMINATION] Added stage-specific NTD for Рабочая документация: {len(stage_specific_ntd)} documents")
            elif project_stage == "Проектная документация":
                stage_specific_ntd = [
                    "ГОСТ Р 21.101-2020",  # Общие требования к проектной документации
                    "ПП РФ 87"  # Положение о составе разделов проектной документации
                ]
                logger.info(f"🔍 [NTD_DETERMINATION] Added stage-specific NTD for Проектная документация: {len(stage_specific_ntd)} documents")
            elif project_stage == "Эскизная документация":
                stage_specific_ntd = [
                    "СП 48.13330.2019",  # Организация строительства
                    "ГОСТ Р 21.101-2020"  # Общие требования
                ]
                logger.info(f"🔍 [NTD_DETERMINATION] Added stage-specific NTD for Эскизная документация: {len(stage_specific_ntd)} documents")
            
            # Объединяем и убираем дубликаты
            all_ntd = base_ntd + stage_specific_ntd
            relevant_ntd = list(set(all_ntd))  # Убираем дубликаты
            
            logger.info(f"🔍 [NTD_DETERMINATION] Final relevant NTD list: {len(relevant_ntd)} documents")
            logger.debug(f"🔍 [NTD_DETERMINATION] Relevant NTD: {relevant_ntd}")
            
            return relevant_ntd
            
        except Exception as e:
            logger.error(f"❌ [NTD_DETERMINATION] Error determining relevant NTD: {e}")
            # Возвращаем базовый набор НТД в случае ошибки
            return self.ntd_by_mark.get(document_set, [])
