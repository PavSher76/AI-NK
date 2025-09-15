"""
Интеграционный модуль для ультимативного анализатора документов
Обеспечивает интеграцию с существующей системой иерархического контроля
"""

import logging
import time
from typing import Dict, Any, List, Optional
from pathlib import Path
from ultimate_document_analyzer import UltimateDocumentAnalyzer, DocumentType, PageType, SeverityLevel

logger = logging.getLogger(__name__)


class UltimateAnalyzerIntegration:
    """Интеграционный класс для ультимативного анализатора документов"""
    
    def __init__(self):
        self.ultimate_analyzer = UltimateDocumentAnalyzer()
        self.fallback_enabled = True
        self.performance_metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'average_processing_time': 0.0
        }
    
    def analyze_document_for_hierarchical_control(self, file_path: str) -> Dict[str, Any]:
        """
        Анализ документа для иерархического контроля с использованием ультимативного анализатора
        """
        start_time = time.time()
        self.performance_metrics['total_requests'] += 1
        
        try:
            logger.info(f"Начинаем анализ документа с ультимативным анализатором: {file_path}")
            
            # Анализ с помощью ультимативного анализатора
            ultimate_result = self.ultimate_analyzer.analyze_document(file_path)
            
            if ultimate_result['success']:
                # Конвертируем результат в формат иерархического контроля
                hierarchical_result = self._convert_to_hierarchical_format(ultimate_result)
                
                processing_time = time.time() - start_time
                self.performance_metrics['successful_requests'] += 1
                self._update_average_processing_time(processing_time)
                
                logger.info(f"Успешно проанализирован документ за {processing_time:.3f} сек")
                return hierarchical_result
            else:
                logger.warning(f"Ультимативный анализатор не смог обработать документ: {ultimate_result.get('error')}")
                if self.fallback_enabled:
                    return self._fallback_analysis(file_path, start_time)
                else:
                    return self._create_error_result(ultimate_result.get('error', 'Unknown error'))
        
        except Exception as e:
            logger.error(f"Ошибка в ультимативном анализаторе: {e}")
            if self.fallback_enabled:
                return self._fallback_analysis(file_path, start_time)
            else:
                return self._create_error_result(str(e))
    
    def _convert_to_hierarchical_format(self, ultimate_result: Dict[str, Any]) -> Dict[str, Any]:
        """Конвертация результатов ультимативного анализатора в формат иерархического контроля"""
        
        # Извлекаем основную информацию
        file_info = {
            'filename': ultimate_result['file_name'],
            'file_size': ultimate_result['file_size'],
            'file_size_mb': ultimate_result['file_size'] / (1024 * 1024),
            'file_hash': ultimate_result['file_hash'],
            'analysis_time': ultimate_result['analysis_time']
        }
        
        # Анализ имени файла
        filename_analysis = ultimate_result['filename_analysis']
        document_info = {
            'project_number': filename_analysis.get('project_number'),
            'document_type': filename_analysis['document_type'].value,
            'mark': filename_analysis.get('mark'),
            'revision': filename_analysis.get('revision'),
            'language': filename_analysis.get('language'),
            'confidence': filename_analysis.get('confidence', 0.0)
        }
        
        # Анализ содержимого
        content_analysis = ultimate_result['content_analysis']
        content_info = {
            'has_stamp': content_analysis['has_stamp'],
            'has_scale': content_analysis['has_scale'],
            'has_dimensions': content_analysis['has_dimensions'],
            'has_materials': content_analysis['has_materials'],
            'has_markings': content_analysis['has_markings'],
            'compliance_indicators': content_analysis['compliance_indicators']
        }
        
        # Структура документа
        doc_structure = ultimate_result['document_structure']
        structure_info = {
            'estimated_pages': doc_structure['estimated_pages'],
            'document_type': doc_structure['document_type'].value,
            'file_size_mb': doc_structure['file_size_mb'],
            'content_indicators': doc_structure['content_indicators']
        }
        
        # Общий анализ
        overall_analysis = ultimate_result['overall_analysis']
        analysis_summary = {
            'total_pages': overall_analysis['total_pages'],
            'compliance_score': overall_analysis['compliance_score'],
            'average_confidence': overall_analysis['average_confidence'],
            'total_issues': overall_analysis['total_issues'],
            'critical_issues': overall_analysis['critical_issues'],
            'warning_issues': overall_analysis['warning_issues'],
            'info_issues': overall_analysis['info_issues'],
            'page_types_distribution': overall_analysis['page_types_distribution']
        }
        
        # Анализ страниц
        pages_analysis = ultimate_result['pages_analysis']
        pages_info = self._extract_pages_info(pages_analysis)
        
        # Элементы документа
        elements_info = self._extract_elements_info(pages_analysis)
        
        # Быстрые метаданные
        quick_metadata = ultimate_result['quick_metadata']
        metadata_info = {
            'document_id': quick_metadata['document_id'],
            'compliance_status': quick_metadata['compliance_status'],
            'has_drawings': quick_metadata['has_drawings'],
            'has_specifications': quick_metadata['has_specifications'],
            'critical_issues_count': quick_metadata['critical_issues_count']
        }
        
        # Формируем результат в формате иерархического контроля
        hierarchical_result = {
            'success': True,
            'file_info': file_info,
            'document_info': document_info,
            'content_info': content_info,
            'structure_info': structure_info,
            'analysis_summary': analysis_summary,
            'pages_info': pages_info,
            'elements_info': elements_info,
            'metadata_info': metadata_info,
            'ultimate_analyzer_used': True,
            'processing_timestamp': time.time()
        }
        
        return hierarchical_result
    
    def _extract_pages_info(self, pages_analysis: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Извлечение информации о страницах"""
        pages_info = {
            'total_pages': len(pages_analysis),
            'pages': []
        }
        
        for page in pages_analysis:
            page_info = {
                'page_number': page['page_number'],
                'page_type': page['page_type'].value,
                'char_count': page['char_count'],
                'word_count': page['word_count'],
                'confidence_score': page['confidence_score'],
                'has_stamp': page['stamp_info'].has_stamp,
                'has_scale': bool(page['stamp_info'].scale),
                'elements_count': len(page['drawing_elements']),
                'issues_count': len(page['compliance_issues'])
            }
            
            # Информация из штампа
            stamp_info = page['stamp_info']
            if stamp_info.has_stamp:
                page_info['stamp_info'] = {
                    'sheet_number': stamp_info.sheet_number,
                    'revision': stamp_info.revision,
                    'inventory_number': stamp_info.inventory_number,
                    'scale': stamp_info.scale,
                    'project_number': stamp_info.project_number,
                    'object_name': stamp_info.object_name,
                    'stage': stamp_info.stage,
                    'document_set': stamp_info.document_set
                }
            
            # Элементы чертежа
            if page['drawing_elements']:
                page_info['drawing_elements'] = [
                    {
                        'element_type': element.element_type,
                        'value': element.value,
                        'unit': element.unit,
                        'confidence': element.confidence
                    }
                    for element in page['drawing_elements']
                ]
            
            # Проблемы соответствия
            if page['compliance_issues']:
                page_info['compliance_issues'] = [
                    {
                        'issue_type': issue.issue_type,
                        'severity': issue.severity.value,
                        'description': issue.description,
                        'recommendation': issue.recommendation,
                        'norm_reference': issue.norm_reference
                    }
                    for issue in page['compliance_issues']
                ]
            
            pages_info['pages'].append(page_info)
        
        return pages_info
    
    def _extract_elements_info(self, pages_analysis: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Извлечение информации об элементах документа"""
        all_elements = []
        total_elements = 0
        
        for page in pages_analysis:
            elements = page['drawing_elements']
            total_elements += len(elements)
            
            for element in elements:
                element_info = {
                    'page_number': page['page_number'],
                    'element_type': element.element_type,
                    'value': element.value,
                    'unit': element.unit,
                    'confidence': element.confidence,
                    'bbox': element.bbox,
                    'metadata': element.metadata
                }
                all_elements.append(element_info)
        
        # Группировка элементов по типам
        elements_by_type = {}
        for element in all_elements:
            element_type = element['element_type']
            if element_type not in elements_by_type:
                elements_by_type[element_type] = []
            elements_by_type[element_type].append(element)
        
        return {
            'total_elements': total_elements,
            'elements_by_type': elements_by_type,
            'all_elements': all_elements
        }
    
    def _fallback_analysis(self, file_path: str, start_time: float) -> Dict[str, Any]:
        """Fallback анализ при неудаче ультимативного анализатора"""
        logger.info(f"Выполняем fallback анализ для документа: {file_path}")
        
        try:
            # Здесь можно добавить вызов оригинального парсера
            # Пока возвращаем базовую информацию
            fallback_result = {
                'success': True,
                'file_info': {
                    'filename': Path(file_path).name,
                    'file_size': Path(file_path).stat().st_size,
                    'file_hash': 'fallback_hash',
                    'analysis_time': time.time() - start_time
                },
                'document_info': {
                    'project_number': None,
                    'document_type': 'unknown',
                    'mark': None,
                    'revision': None,
                    'language': 'RU',
                    'confidence': 0.0
                },
                'content_info': {
                    'has_stamp': False,
                    'has_scale': False,
                    'has_dimensions': False,
                    'has_materials': False,
                    'has_markings': False,
                    'compliance_indicators': []
                },
                'structure_info': {
                    'estimated_pages': 1,
                    'document_type': 'unknown',
                    'file_size_mb': Path(file_path).stat().st_size / (1024 * 1024),
                    'content_indicators': []
                },
                'analysis_summary': {
                    'total_pages': 1,
                    'compliance_score': 0.0,
                    'average_confidence': 0.0,
                    'total_issues': 1,
                    'critical_issues': 1,
                    'warning_issues': 0,
                    'info_issues': 0,
                    'page_types_distribution': {'unknown': 1}
                },
                'pages_info': {
                    'total_pages': 1,
                    'pages': [{
                        'page_number': 1,
                        'page_type': 'unknown',
                        'char_count': 0,
                        'word_count': 0,
                        'confidence_score': 0.0,
                        'has_stamp': False,
                        'has_scale': False,
                        'elements_count': 0,
                        'issues_count': 1
                    }]
                },
                'elements_info': {
                    'total_elements': 0,
                    'elements_by_type': {},
                    'all_elements': []
                },
                'metadata_info': {
                    'document_id': 'unknown',
                    'compliance_status': 'error',
                    'has_drawings': False,
                    'has_specifications': False,
                    'critical_issues_count': 1
                },
                'ultimate_analyzer_used': False,
                'fallback_used': True,
                'processing_timestamp': time.time()
            }
            
            processing_time = time.time() - start_time
            self.performance_metrics['failed_requests'] += 1
            self._update_average_processing_time(processing_time)
            
            logger.warning(f"Fallback анализ завершен за {processing_time:.3f} сек")
            return fallback_result
            
        except Exception as e:
            logger.error(f"Ошибка в fallback анализе: {e}")
            return self._create_error_result(str(e))
    
    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """Создание результата с ошибкой"""
        return {
            'success': False,
            'error': error_message,
            'ultimate_analyzer_used': False,
            'fallback_used': False,
            'processing_timestamp': time.time()
        }
    
    def _update_average_processing_time(self, processing_time: float):
        """Обновление средней времени обработки"""
        total_requests = self.performance_metrics['total_requests']
        current_avg = self.performance_metrics['average_processing_time']
        
        # Вычисляем новое среднее значение
        new_avg = ((current_avg * (total_requests - 1)) + processing_time) / total_requests
        self.performance_metrics['average_processing_time'] = new_avg
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Получение метрик производительности"""
        return self.performance_metrics.copy()
    
    def reset_metrics(self):
        """Сброс метрик производительности"""
        self.performance_metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'average_processing_time': 0.0
        }
    
    def set_fallback_enabled(self, enabled: bool):
        """Включение/отключение fallback механизма"""
        self.fallback_enabled = enabled
        logger.info(f"Fallback механизм {'включен' if enabled else 'отключен'}")


def create_ultimate_analyzer_integration() -> UltimateAnalyzerIntegration:
    """Фабричная функция для создания интеграционного модуля"""
    return UltimateAnalyzerIntegration()


# Пример использования
if __name__ == "__main__":
    # Создание интеграционного модуля
    integration = create_ultimate_analyzer_integration()
    
    # Тестирование на документе
    test_file = "tests/TestDocs/for_check/3401-21089-РД-01-220-221-АР_4_0_RU_IFC (1).pdf"
    
    print("🚀 Тестирование интеграции ультимативного анализатора")
    print("=" * 60)
    
    # Анализ документа
    result = integration.analyze_document_for_hierarchical_control(test_file)
    
    if result['success']:
        print("✅ Анализ выполнен успешно")
        print(f"📄 Файл: {result['file_info']['filename']}")
        print(f"📊 Размер: {result['file_info']['file_size_mb']:.2f} МБ")
        print(f"⏱️ Время: {result['file_info']['analysis_time']:.3f} сек")
        print(f"🏗️ Тип: {result['document_info']['document_type']}")
        print(f"📋 Марка: {result['document_info']['mark']}")
        print(f"📄 Страниц: {result['analysis_summary']['total_pages']}")
        print(f"📈 Соответствие: {result['analysis_summary']['compliance_score']:.1f}%")
        print(f"🔧 Элементов: {result['elements_info']['total_elements']}")
        print(f"⚡ Ультимативный анализатор: {'Да' if result['ultimate_analyzer_used'] else 'Нет'}")
    else:
        print(f"❌ Ошибка анализа: {result.get('error', 'Unknown error')}")
    
    # Метрики производительности
    metrics = integration.get_performance_metrics()
    print(f"\n📊 Метрики производительности:")
    print(f"  Всего запросов: {metrics['total_requests']}")
    print(f"  Успешных: {metrics['successful_requests']}")
    print(f"  Неудачных: {metrics['failed_requests']}")
    print(f"  Среднее время: {metrics['average_processing_time']:.3f} сек")
