"""
Интегрированный сервис иерархического контроля с ультимативным анализатором
Объединяет функциональность иерархического контроля с ультимативным анализатором документов
"""

import logging
import time
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from simple_enhanced_parser import SimpleEnhancedDocumentParser
from ultimate_analyzer_integration import UltimateAnalyzerIntegration

logger = logging.getLogger(__name__)


class IntegratedHierarchicalService:
    """Интегрированный сервис иерархического контроля"""
    
    def __init__(self):
        self.enhanced_parser = SimpleEnhancedDocumentParser()
        self.ultimate_integration = UltimateAnalyzerIntegration()
        self.use_ultimate_analyzer = True
        
        # Метрики производительности
        self.performance_metrics = {
            'total_checks': 0,
            'successful_checks': 0,
            'failed_checks': 0,
            'ultimate_analyzer_used': 0,
            'fallback_used': 0,
            'average_processing_time': 0.0
        }
    
    def perform_hierarchical_check(self, file_path: str) -> Dict[str, Any]:
        """
        Выполнение иерархической проверки с использованием ультимативного анализатора
        """
        start_time = time.time()
        self.performance_metrics['total_checks'] += 1
        
        logger.info(f"Начинаем иерархическую проверку документа: {file_path}")
        
        try:
            # Анализ документа с помощью ультимативного анализатора
            if self.use_ultimate_analyzer:
                ultimate_result = self.ultimate_integration.analyze_document_for_hierarchical_control(file_path)
                
                if ultimate_result['success']:
                    # Выполняем иерархическую проверку на основе результатов ультимативного анализатора
                    hierarchical_result = self._perform_hierarchical_analysis(ultimate_result)
                    
                    processing_time = time.time() - start_time
                    self.performance_metrics['successful_checks'] += 1
                    self.performance_metrics['ultimate_analyzer_used'] += 1
                    self._update_average_processing_time(processing_time)
                    
                    logger.info(f"Иерархическая проверка завершена успешно за {processing_time:.3f} сек")
                    return hierarchical_result
                else:
                    logger.warning(f"Ультимативный анализатор не смог обработать документ: {ultimate_result.get('error')}")
            
            # Fallback к обычному парсеру
            logger.info("Переключаемся на обычный парсер")
            parser_result = self.enhanced_parser.parse_document(file_path)
            
            if parser_result['success']:
                # Выполняем иерархическую проверку на основе результатов парсера
                hierarchical_result = self._perform_hierarchical_analysis_from_parser(parser_result)
                
                processing_time = time.time() - start_time
                self.performance_metrics['successful_checks'] += 1
                self.performance_metrics['fallback_used'] += 1
                self._update_average_processing_time(processing_time)
                
                logger.info(f"Иерархическая проверка завершена с fallback за {processing_time:.3f} сек")
                return hierarchical_result
            else:
                raise Exception(f"Парсер не смог обработать документ: {parser_result.get('error')}")
        
        except Exception as e:
            processing_time = time.time() - start_time
            self.performance_metrics['failed_checks'] += 1
            self._update_average_processing_time(processing_time)
            
            logger.error(f"Ошибка в иерархической проверке: {e}")
            return self._create_error_result(str(e))
    
    def _perform_hierarchical_analysis(self, ultimate_result: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнение иерархического анализа на основе результатов ультимативного анализатора"""
        
        # Извлекаем информацию из результата ультимативного анализатора
        document_info = ultimate_result['document_info']
        analysis_summary = ultimate_result['analysis_summary']
        pages_info = ultimate_result['pages_info']
        elements_info = ultimate_result['elements_info']
        content_info = ultimate_result['content_info']
        
        # Определяем релевантные НТД на основе типа документа
        relevant_ntd = self._get_relevant_ntd(document_info['document_type'], document_info['mark'])
        
        # Анализ соответствия нормам
        norm_compliance = self._analyze_norm_compliance(
            analysis_summary, 
            content_info, 
            pages_info, 
            elements_info
        )
        
        # Анализ разделов
        sections_analysis = self._analyze_sections(pages_info, elements_info)
        
        # Определяем общий статус
        overall_status = self._determine_overall_status(norm_compliance, analysis_summary)
        
        # Формируем результат иерархической проверки
        hierarchical_result = {
            'success': True,
            'hierarchical_result': {
                'project_info': {
                    'project_number': document_info['project_number'],
                    'document_type': document_info['document_type'],
                    'mark': document_info['mark'],
                    'revision': document_info['revision']
                },
                'norm_compliance_summary': norm_compliance,
                'sections_analysis': sections_analysis,
                'overall_status': overall_status,
                'execution_time': time.time(),
                'ultimate_analyzer_used': True,
                'relevant_ntd': relevant_ntd
            },
            'file_info': ultimate_result['file_info'],
            'processing_metadata': {
                'total_pages': analysis_summary['total_pages'],
                'compliance_score': analysis_summary['compliance_score'],
                'total_elements': elements_info['total_elements'],
                'ultimate_analyzer_used': True
            }
        }
        
        return hierarchical_result
    
    def _perform_hierarchical_analysis_from_parser(self, parser_result: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнение иерархического анализа на основе результатов парсера"""
        
        # Извлекаем информацию из результата парсера
        metadata = parser_result['metadata']
        pages = parser_result['pages']
        
        # Определяем релевантные НТД
        relevant_ntd = self._get_relevant_ntd(metadata['document_type'], metadata['mark'])
        
        # Базовый анализ соответствия нормам
        norm_compliance = {
            'findings': [],
            'page_sizes': [len(page['text']) for page in pages],
            'total_pages': metadata['total_pages'],
            'document_set': metadata.get('mark', 'Unknown'),
            'relevant_ntd': relevant_ntd,
            'info_findings': 0,
            'project_stage': 'Рабочая документация',
            'total_findings': 0,
            'compliant_pages': metadata['total_pages'],
            'warning_findings': 0,
            'critical_findings': 0,
            'compliance_percentage': metadata['compliance_score']
        }
        
        # Базовый анализ разделов
        sections_analysis = {
            'sections': [],
            'total_sections': 1,
            'section_analysis': {
                'title_section': pages[0] if pages else None,
                'details_sections': pages[1:] if len(pages) > 1 else [],
                'general_data_section': None,
                'main_content_sections': pages,
                'specification_sections': []
            },
            'general_data_analysis': None,
            'detailed_sections_analysis': {
                'total_sections': 1,
                'sections_analysis': [],
                'overall_compliance': 'unknown'
            }
        }
        
        # Определяем общий статус
        overall_status = 'warning' if metadata['compliance_score'] < 80 else 'success'
        
        # Формируем результат иерархической проверки
        hierarchical_result = {
            'success': True,
            'hierarchical_result': {
                'project_info': {
                    'project_number': metadata['project_number'],
                    'document_type': metadata['document_type'],
                    'mark': metadata['mark'],
                    'revision': metadata['revision']
                },
                'norm_compliance_summary': norm_compliance,
                'sections_analysis': sections_analysis,
                'overall_status': overall_status,
                'execution_time': time.time(),
                'ultimate_analyzer_used': False,
                'relevant_ntd': relevant_ntd
            },
            'file_info': {
                'filename': parser_result['file_name'],
                'file_size': parser_result['file_size'],
                'file_hash': parser_result['file_hash'],
                'analysis_time': parser_result['analysis_time']
            },
            'processing_metadata': {
                'total_pages': metadata['total_pages'],
                'compliance_score': metadata['compliance_score'],
                'total_elements': len(parser_result.get('elements', [])),
                'ultimate_analyzer_used': False
            }
        }
        
        return hierarchical_result
    
    def _get_relevant_ntd(self, document_type: str, mark: str) -> List[str]:
        """Получение релевантных НТД на основе типа документа и марки"""
        ntd_mapping = {
            'architectural_drawing': ['ГОСТ 21.501-2018', 'ГОСТ Р 21.101-2020', 'СП 48.13330.2019'],
            'structural_drawing': ['ГОСТ 21.501-2018', 'ГОСТ Р 21.101-2020', 'СП 16.13330.2017'],
            'metal_structures_drawing': ['ГОСТ 21.501-2018', 'ГОСТ Р 21.101-2020', 'ГОСТ 23118-2012'],
            'ventilation_drawing': ['ГОСТ 21.501-2018', 'ГОСТ Р 21.101-2020', 'СП 60.13330.2020'],
            'plumbing_drawing': ['ГОСТ 21.501-2018', 'ГОСТ Р 21.101-2020', 'СП 30.13330.2020'],
            'electrical_drawing': ['ГОСТ 21.501-2018', 'ГОСТ Р 21.101-2020', 'СП 256.1325800.2016']
        }
        
        return ntd_mapping.get(document_type, ['ГОСТ 21.501-2018', 'ГОСТ Р 21.101-2020'])
    
    def _analyze_norm_compliance(self, analysis_summary: Dict[str, Any], content_info: Dict[str, Any], 
                                pages_info: Dict[str, Any], elements_info: Dict[str, Any]) -> Dict[str, Any]:
        """Анализ соответствия нормам"""
        
        findings = []
        total_findings = 0
        critical_findings = 0
        warning_findings = 0
        info_findings = 0
        
        # Проверка наличия штампа
        if not content_info['has_stamp']:
            findings.append({
                'type': 'critical',
                'description': 'Отсутствует штамп чертежа',
                'norm_reference': 'ГОСТ 21.501-2018',
                'page': 1
            })
            critical_findings += 1
            total_findings += 1
        
        # Проверка наличия масштаба
        if not content_info['has_scale']:
            findings.append({
                'type': 'warning',
                'description': 'Не указан масштаб чертежа',
                'norm_reference': 'ГОСТ 21.501-2018',
                'page': 1
            })
            warning_findings += 1
            total_findings += 1
        
        # Проверка наличия размеров
        if not content_info['has_dimensions']:
            findings.append({
                'type': 'info',
                'description': 'Отсутствуют размеры на чертеже',
                'norm_reference': 'ГОСТ 21.501-2018',
                'page': 1
            })
            info_findings += 1
            total_findings += 1
        
        # Анализ страниц
        page_sizes = [page['char_count'] for page in pages_info['pages']]
        compliant_pages = sum(1 for page in pages_info['pages'] if page['confidence_score'] > 0.5)
        
        return {
            'findings': findings,
            'page_sizes': page_sizes,
            'total_pages': analysis_summary['total_pages'],
            'document_set': 'Архитектурные решения',
            'relevant_ntd': ['ГОСТ 21.501-2018', 'ГОСТ Р 21.101-2020'],
            'info_findings': info_findings,
            'project_stage': 'Рабочая документация',
            'total_findings': total_findings,
            'compliant_pages': compliant_pages,
            'warning_findings': warning_findings,
            'critical_findings': critical_findings,
            'compliance_percentage': analysis_summary['compliance_score']
        }
    
    def _analyze_sections(self, pages_info: Dict[str, Any], elements_info: Dict[str, Any]) -> Dict[str, Any]:
        """Анализ разделов документа"""
        
        sections = []
        title_section = None
        general_data_section = None
        main_content_sections = []
        specification_sections = []
        
        # Анализ страниц по типам
        for page in pages_info['pages']:
            page_type = page['page_type']
            
            if page_type == 'title_page':
                title_section = page
            elif page_type == 'general_data_page':
                general_data_section = page
            elif page_type == 'specification_page':
                specification_sections.append(page)
            else:
                main_content_sections.append(page)
        
        return {
            'sections': sections,
            'total_sections': len(sections),
            'section_analysis': {
                'title_section': title_section,
                'details_sections': [],
                'general_data_section': general_data_section,
                'main_content_sections': main_content_sections,
                'specification_sections': specification_sections
            },
            'general_data_analysis': general_data_section,
            'detailed_sections_analysis': {
                'total_sections': len(sections),
                'sections_analysis': [],
                'overall_compliance': 'unknown'
            }
        }
    
    def _determine_overall_status(self, norm_compliance: Dict[str, Any], analysis_summary: Dict[str, Any]) -> str:
        """Определение общего статуса"""
        
        if norm_compliance['critical_findings'] > 0:
            return 'error'
        elif norm_compliance['warning_findings'] > 0 or analysis_summary['compliance_score'] < 80:
            return 'warning'
        else:
            return 'success'
    
    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """Создание результата с ошибкой"""
        return {
            'success': False,
            'error': error_message,
            'hierarchical_result': {
                'overall_status': 'error',
                'execution_time': time.time()
            }
        }
    
    def _update_average_processing_time(self, processing_time: float):
        """Обновление средней времени обработки"""
        total_checks = self.performance_metrics['total_checks']
        current_avg = self.performance_metrics['average_processing_time']
        
        # Вычисляем новое среднее значение
        new_avg = ((current_avg * (total_checks - 1)) + processing_time) / total_checks
        self.performance_metrics['average_processing_time'] = new_avg
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Получение метрик производительности"""
        return self.performance_metrics.copy()
    
    def reset_metrics(self):
        """Сброс метрик производительности"""
        self.performance_metrics = {
            'total_checks': 0,
            'successful_checks': 0,
            'failed_checks': 0,
            'ultimate_analyzer_used': 0,
            'fallback_used': 0,
            'average_processing_time': 0.0
        }


def create_integrated_hierarchical_service() -> IntegratedHierarchicalService:
    """Фабричная функция для создания интегрированного сервиса"""
    return IntegratedHierarchicalService()


# Пример использования
if __name__ == "__main__":
    # Создание интегрированного сервиса
    service = create_integrated_hierarchical_service()
    
    # Тестирование на документе
    test_file = "tests/TestDocs/for_check/3401-21089-РД-01-220-221-АР_4_0_RU_IFC (1).pdf"
    
    print("🚀 Тестирование интегрированного сервиса иерархического контроля")
    print("=" * 70)
    
    # Выполнение иерархической проверки
    result = service.perform_hierarchical_check(test_file)
    
    if result['success']:
        print("✅ Иерархическая проверка выполнена успешно")
        
        hierarchical_result = result['hierarchical_result']
        print(f"📄 Файл: {result['file_info']['filename']}")
        print(f"📊 Размер: {result['file_info']['file_size'] / (1024 * 1024):.2f} МБ")
        print(f"⏱️ Время: {result['file_info']['analysis_time']:.3f} сек")
        print(f"🏗️ Тип: {hierarchical_result['project_info']['document_type']}")
        print(f"📋 Марка: {hierarchical_result['project_info']['mark']}")
        print(f"📄 Страниц: {hierarchical_result['norm_compliance_summary']['total_pages']}")
        print(f"📈 Соответствие: {hierarchical_result['norm_compliance_summary']['compliance_percentage']:.1f}%")
        print(f"🔧 Элементов: {result['processing_metadata']['total_elements']}")
        print(f"⚡ Ультимативный анализатор: {'Да' if hierarchical_result['ultimate_analyzer_used'] else 'Нет'}")
        print(f"📋 Статус: {hierarchical_result['overall_status']}")
        
        # Анализ соответствия нормам
        norm_compliance = hierarchical_result['norm_compliance_summary']
        print(f"\n📊 Анализ соответствия нормам:")
        print(f"  Всего нарушений: {norm_compliance['total_findings']}")
        print(f"  Критических: {norm_compliance['critical_findings']}")
        print(f"  Предупреждений: {norm_compliance['warning_findings']}")
        print(f"  Информационных: {norm_compliance['info_findings']}")
        print(f"  Соответствующих страниц: {norm_compliance['compliant_pages']}")
        
        # Релевантные НТД
        print(f"\n📋 Релевантные НТД:")
        for ntd in hierarchical_result['relevant_ntd']:
            print(f"  - {ntd}")
        
        # Найденные нарушения
        if norm_compliance['findings']:
            print(f"\n⚠️ Найденные нарушения:")
            for i, finding in enumerate(norm_compliance['findings'], 1):
                print(f"  {i}. {finding['description']} ({finding['type']})")
                print(f"     Норма: {finding['norm_reference']}")
                print(f"     Страница: {finding['page']}")
    else:
        print(f"❌ Ошибка иерархической проверки: {result.get('error', 'Unknown error')}")
    
    # Метрики производительности
    metrics = service.get_performance_metrics()
    print(f"\n📊 Метрики производительности:")
    print(f"  Всего проверок: {metrics['total_checks']}")
    print(f"  Успешных: {metrics['successful_checks']}")
    print(f"  Неудачных: {metrics['failed_checks']}")
    print(f"  Ультимативный анализатор: {metrics['ultimate_analyzer_used']}")
    print(f"  Fallback: {metrics['fallback_used']}")
    print(f"  Среднее время: {metrics['average_processing_time']:.3f} сек")
