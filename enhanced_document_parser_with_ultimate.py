"""
Улучшенный парсер документов с интеграцией ультимативного анализатора
Объединяет функциональность оригинального парсера с ультимативным анализатором
"""

import logging
import time
from typing import Dict, Any, List, Optional
from pathlib import Path
from ultimate_analyzer_integration import UltimateAnalyzerIntegration
from utils.document_parser import UniversalDocumentParser

logger = logging.getLogger(__name__)


class EnhancedDocumentParserWithUltimate:
    """Улучшенный парсер документов с интеграцией ультимативного анализатора"""
    
    def __init__(self):
        self.ultimate_integration = UltimateAnalyzerIntegration()
        self.original_parser = UniversalDocumentParser()
        self.use_ultimate_analyzer = True
        self.fallback_to_original = True
        
        # Метрики производительности
        self.performance_metrics = {
            'total_documents': 0,
            'ultimate_analyzer_success': 0,
            'original_parser_success': 0,
            'total_failures': 0,
            'average_processing_time': 0.0
        }
    
    def parse_document(self, file_path: str) -> Dict[str, Any]:
        """
        Парсинг документа с использованием ультимативного анализатора и fallback к оригинальному парсеру
        """
        start_time = time.time()
        self.performance_metrics['total_documents'] += 1
        
        logger.info(f"Начинаем парсинг документа: {file_path}")
        
        # Попытка использовать ультимативный анализатор
        if self.use_ultimate_analyzer:
            try:
                ultimate_result = self.ultimate_integration.analyze_document_for_hierarchical_control(file_path)
                
                if ultimate_result['success']:
                    processing_time = time.time() - start_time
                    self.performance_metrics['ultimate_analyzer_success'] += 1
                    self._update_average_processing_time(processing_time)
                    
                    logger.info(f"Успешно обработан ультимативным анализатором за {processing_time:.3f} сек")
                    return self._convert_ultimate_to_parser_format(ultimate_result)
                else:
                    logger.warning(f"Ультимативный анализатор не смог обработать документ: {ultimate_result.get('error')}")
                    
            except Exception as e:
                logger.error(f"Ошибка в ультимативном анализаторе: {e}")
        
        # Fallback к оригинальному парсеру
        if self.fallback_to_original:
            try:
                logger.info("Переключаемся на оригинальный парсер")
                original_result = self.original_parser.parse_document(file_path)
                
                processing_time = time.time() - start_time
                self.performance_metrics['original_parser_success'] += 1
                self._update_average_processing_time(processing_time)
                
                logger.info(f"Успешно обработан оригинальным парсером за {processing_time:.3f} сек")
                return self._add_enhancement_info(original_result, False)
                
            except Exception as e:
                logger.error(f"Ошибка в оригинальном парсере: {e}")
        
        # Если оба парсера не сработали
        processing_time = time.time() - start_time
        self.performance_metrics['total_failures'] += 1
        self._update_average_processing_time(processing_time)
        
        logger.error(f"Не удалось обработать документ ни одним из парсеров: {file_path}")
        return self._create_error_result("Все парсеры не смогли обработать документ")
    
    def parse_document_from_bytes(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """
        Парсинг документа из байтов с использованием ультимативного анализатора
        """
        start_time = time.time()
        self.performance_metrics['total_documents'] += 1
        
        logger.info(f"Начинаем парсинг документа из байтов: {filename}")
        
        # Сначала пробуем ультимативный анализатор
        if self.use_ultimate_analyzer:
            try:
                # Сохраняем временный файл для ультимативного анализатора
                temp_file = Path(f"/tmp/temp_document_{int(time.time())}_{filename}")
                with open(temp_file, 'wb') as f:
                    f.write(file_bytes)
                
                ultimate_result = self.ultimate_integration.analyze_document_for_hierarchical_control(str(temp_file))
                
                # Удаляем временный файл
                temp_file.unlink()
                
                if ultimate_result['success']:
                    processing_time = time.time() - start_time
                    self.performance_metrics['ultimate_analyzer_success'] += 1
                    self._update_average_processing_time(processing_time)
                    
                    logger.info(f"Успешно обработан ультимативным анализатором за {processing_time:.3f} сек")
                    return self._convert_ultimate_to_parser_format(ultimate_result)
                else:
                    logger.warning(f"Ультимативный анализатор не смог обработать документ: {ultimate_result.get('error')}")
                    
            except Exception as e:
                logger.error(f"Ошибка в ультимативном анализаторе: {e}")
        
        # Fallback к оригинальному парсеру
        if self.fallback_to_original:
            try:
                logger.info("Переключаемся на оригинальный парсер")
                original_result = self.original_parser.parse_document_from_bytes(file_bytes, filename)
                
                processing_time = time.time() - start_time
                self.performance_metrics['original_parser_success'] += 1
                self._update_average_processing_time(processing_time)
                
                logger.info(f"Успешно обработан оригинальным парсером за {processing_time:.3f} сек")
                return self._add_enhancement_info(original_result, False)
                
            except Exception as e:
                logger.error(f"Ошибка в оригинальном парсере: {e}")
        
        # Если оба парсера не сработали
        processing_time = time.time() - start_time
        self.performance_metrics['total_failures'] += 1
        self._update_average_processing_time(processing_time)
        
        logger.error(f"Не удалось обработать документ ни одним из парсеров: {filename}")
        return self._create_error_result("Все парсеры не смогли обработать документ")
    
    def _convert_ultimate_to_parser_format(self, ultimate_result: Dict[str, Any]) -> Dict[str, Any]:
        """Конвертация результата ультимативного анализатора в формат парсера"""
        
        # Базовый результат в формате парсера
        parser_result = {
            'success': True,
            'file_name': ultimate_result['file_info']['filename'],
            'file_size': ultimate_result['file_info']['file_size'],
            'file_hash': ultimate_result['file_info']['file_hash'],
            'analysis_time': ultimate_result['file_info']['analysis_time'],
            'pages': [],
            'metadata': {
                'total_pages': ultimate_result['analysis_summary']['total_pages'],
                'document_type': ultimate_result['document_info']['document_type'],
                'project_number': ultimate_result['document_info']['project_number'],
                'mark': ultimate_result['document_info']['mark'],
                'revision': ultimate_result['document_info']['revision'],
                'compliance_score': ultimate_result['analysis_summary']['compliance_score'],
                'ultimate_analyzer_used': True,
                'enhanced_parsing': True
            }
        }
        
        # Конвертация страниц
        for page_info in ultimate_result['pages_info']['pages']:
            page = {
                'page_number': page_info['page_number'],
                'text': '',  # Ультимативный анализатор не извлекает текст напрямую
                'metadata': {
                    'page_type': page_info['page_type'],
                    'char_count': page_info['char_count'],
                    'word_count': page_info['word_count'],
                    'confidence_score': page_info['confidence_score'],
                    'has_stamp': page_info['has_stamp'],
                    'has_scale': page_info['has_scale'],
                    'elements_count': page_info['elements_count'],
                    'issues_count': page_info['issues_count']
                }
            }
            
            # Добавляем информацию из штампа
            if 'stamp_info' in page_info:
                page['metadata']['stamp_info'] = page_info['stamp_info']
            
            # Добавляем элементы чертежа
            if 'drawing_elements' in page_info:
                page['metadata']['drawing_elements'] = page_info['drawing_elements']
            
            # Добавляем проблемы соответствия
            if 'compliance_issues' in page_info:
                page['metadata']['compliance_issues'] = page_info['compliance_issues']
            
            parser_result['pages'].append(page)
        
        # Добавляем информацию об элементах
        parser_result['elements'] = ultimate_result['elements_info']['all_elements']
        parser_result['elements_by_type'] = ultimate_result['elements_info']['elements_by_type']
        
        # Добавляем информацию о содержимом
        parser_result['content_analysis'] = ultimate_result['content_info']
        
        # Добавляем быстрые метаданные
        parser_result['quick_metadata'] = ultimate_result['metadata_info']
        
        return parser_result
    
    def _add_enhancement_info(self, original_result: Dict[str, Any], ultimate_used: bool) -> Dict[str, Any]:
        """Добавление информации об улучшениях к результату оригинального парсера"""
        if 'metadata' not in original_result:
            original_result['metadata'] = {}
        
        original_result['metadata']['ultimate_analyzer_used'] = ultimate_used
        original_result['metadata']['enhanced_parsing'] = True
        original_result['metadata']['fallback_used'] = not ultimate_used
        
        return original_result
    
    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """Создание результата с ошибкой"""
        return {
            'success': False,
            'error': error_message,
            'metadata': {
                'ultimate_analyzer_used': False,
                'enhanced_parsing': True,
                'fallback_used': False
            }
        }
    
    def _update_average_processing_time(self, processing_time: float):
        """Обновление средней времени обработки"""
        total_documents = self.performance_metrics['total_documents']
        current_avg = self.performance_metrics['average_processing_time']
        
        # Вычисляем новое среднее значение
        new_avg = ((current_avg * (total_documents - 1)) + processing_time) / total_documents
        self.performance_metrics['average_processing_time'] = new_avg
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Получение метрик производительности"""
        return self.performance_metrics.copy()
    
    def reset_metrics(self):
        """Сброс метрик производительности"""
        self.performance_metrics = {
            'total_documents': 0,
            'ultimate_analyzer_success': 0,
            'original_parser_success': 0,
            'total_failures': 0,
            'average_processing_time': 0.0
        }
    
    def set_ultimate_analyzer_enabled(self, enabled: bool):
        """Включение/отключение ультимативного анализатора"""
        self.use_ultimate_analyzer = enabled
        logger.info(f"Ультимативный анализатор {'включен' if enabled else 'отключен'}")
    
    def set_fallback_enabled(self, enabled: bool):
        """Включение/отключение fallback к оригинальному парсеру"""
        self.fallback_to_original = enabled
        logger.info(f"Fallback к оригинальному парсеру {'включен' if enabled else 'отключен'}")


def create_enhanced_document_parser() -> EnhancedDocumentParserWithUltimate:
    """Фабричная функция для создания улучшенного парсера документов"""
    return EnhancedDocumentParserWithUltimate()


# Пример использования
if __name__ == "__main__":
    # Создание улучшенного парсера
    parser = create_enhanced_document_parser()
    
    # Тестирование на документе
    test_file = "tests/TestDocs/for_check/3401-21089-РД-01-220-221-АР_4_0_RU_IFC (1).pdf"
    
    print("🚀 Тестирование улучшенного парсера документов")
    print("=" * 60)
    
    # Парсинг документа
    result = parser.parse_document(test_file)
    
    if result['success']:
        print("✅ Парсинг выполнен успешно")
        print(f"📄 Файл: {result['file_name']}")
        print(f"📊 Размер: {result['file_size'] / (1024 * 1024):.2f} МБ")
        print(f"⏱️ Время: {result['analysis_time']:.3f} сек")
        print(f"📄 Страниц: {result['metadata']['total_pages']}")
        print(f"🏗️ Тип: {result['metadata']['document_type']}")
        print(f"📋 Марка: {result['metadata']['mark']}")
        print(f"📈 Соответствие: {result['metadata']['compliance_score']:.1f}%")
        print(f"🔧 Элементов: {len(result.get('elements', []))}")
        print(f"⚡ Ультимативный анализатор: {'Да' if result['metadata']['ultimate_analyzer_used'] else 'Нет'}")
        print(f"🔄 Fallback: {'Да' if result['metadata'].get('fallback_used', False) else 'Нет'}")
    else:
        print(f"❌ Ошибка парсинга: {result.get('error', 'Unknown error')}")
    
    # Метрики производительности
    metrics = parser.get_performance_metrics()
    print(f"\n📊 Метрики производительности:")
    print(f"  Всего документов: {metrics['total_documents']}")
    print(f"  Ультимативный анализатор: {metrics['ultimate_analyzer_success']}")
    print(f"  Оригинальный парсер: {metrics['original_parser_success']}")
    print(f"  Неудач: {metrics['total_failures']}")
    print(f"  Среднее время: {metrics['average_processing_time']:.3f} сек")
