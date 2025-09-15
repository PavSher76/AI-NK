"""
Интегрированная система нормоконтроля с ультимативным анализатором документов
Объединяет все компоненты для полной автоматизации проверки нормоконтролем
"""

import logging
import os
import json
import time
from typing import Dict, Any, List, Optional
from pathlib import Path
from enhanced_normcontrol_analyzer import EnhancedNormControlAnalyzer

logger = logging.getLogger(__name__)


class IntegratedNormControlSystem:
    """Интегрированная система нормоконтроля"""
    
    def __init__(self):
        self.analyzer = EnhancedNormControlAnalyzer()
        self.results_cache = {}
        self.batch_results = []
    
    def process_document(self, file_path: str) -> Dict[str, Any]:
        """Обработка одного документа"""
        try:
            logger.info(f"Обработка документа: {file_path}")
            
            # Анализ документа
            result = self.analyzer.analyze_document_for_normcontrol(file_path)
            
            # Кэширование результата
            if result['success']:
                file_hash = result['document_analysis']['file_hash']
                self.results_cache[file_hash] = result
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка обработки документа {file_path}: {e}")
            return {
                'success': False,
                'error': str(e),
                'file_path': file_path
            }
    
    def process_batch(self, file_paths: List[str]) -> Dict[str, Any]:
        """Обработка пакета документов"""
        start_time = time.time()
        batch_results = []
        
        logger.info(f"Начало обработки пакета из {len(file_paths)} документов")
        
        for file_path in file_paths:
            result = self.process_document(file_path)
            batch_results.append(result)
        
        # Анализ результатов пакета
        batch_analysis = self._analyze_batch_results(batch_results)
        
        batch_summary = {
            'success': True,
            'total_documents': len(file_paths),
            'processed_documents': len([r for r in batch_results if r['success']]),
            'failed_documents': len([r for r in batch_results if not r['success']]),
            'processing_time': time.time() - start_time,
            'results': batch_results,
            'batch_analysis': batch_analysis
        }
        
        self.batch_results.append(batch_summary)
        return batch_summary
    
    def _analyze_batch_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Анализ результатов пакетной обработки"""
        successful_results = [r for r in results if r['success']]
        
        if not successful_results:
            return {
                'total_issues': 0,
                'critical_issues': 0,
                'warning_issues': 0,
                'info_issues': 0,
                'average_compliance': 0.0,
                'status_distribution': {},
                'recommendations': []
            }
        
        # Подсчет проблем
        total_issues = 0
        critical_issues = 0
        warning_issues = 0
        info_issues = 0
        
        # Распределение статусов
        status_distribution = {}
        
        # Средняя оценка соответствия
        compliance_scores = []
        
        for result in successful_results:
            onk_compliance = result['onk_compliance']
            total_issues += onk_compliance['total_issues']
            critical_issues += onk_compliance['critical_issues']
            warning_issues += onk_compliance['warning_issues']
            info_issues += onk_compliance['info_issues']
            
            status = result['normcontrol_report']['status']
            status_distribution[status] = status_distribution.get(status, 0) + 1
            
            compliance_scores.append(onk_compliance['overall_score'])
        
        average_compliance = sum(compliance_scores) / len(compliance_scores) if compliance_scores else 0.0
        
        # Генерация рекомендаций
        recommendations = []
        if critical_issues > 0:
            recommendations.append(f"Устранить {critical_issues} критических нарушений")
        if warning_issues > 0:
            recommendations.append(f"Исправить {warning_issues} предупреждений")
        if average_compliance < 80:
            recommendations.append("Повысить общее качество документов")
        
        return {
            'total_issues': total_issues,
            'critical_issues': critical_issues,
            'warning_issues': warning_issues,
            'info_issues': info_issues,
            'average_compliance': average_compliance,
            'status_distribution': status_distribution,
            'recommendations': recommendations
        }
    
    def generate_batch_report(self, batch_id: int = None) -> Dict[str, Any]:
        """Генерация отчета по пакету"""
        if batch_id is None:
            batch_id = len(self.batch_results) - 1
        
        if batch_id >= len(self.batch_results):
            return {'error': 'Batch not found'}
        
        batch = self.batch_results[batch_id]
        
        report = {
            'batch_id': batch_id,
            'generated_at': time.time(),
            'summary': {
                'total_documents': batch['total_documents'],
                'processed_documents': batch['processed_documents'],
                'failed_documents': batch['failed_documents'],
                'processing_time': batch['processing_time'],
                'success_rate': (batch['processed_documents'] / batch['total_documents']) * 100
            },
            'analysis': batch['batch_analysis'],
            'documents': []
        }
        
        # Детали по каждому документу
        for result in batch['results']:
            if result['success']:
                doc_info = {
                    'file_name': result['normcontrol_report']['document_info']['file_name'],
                    'project_number': result['normcontrol_report']['document_analysis']['project_number'],
                    'mark': result['normcontrol_report']['document_analysis']['mark'],
                    'status': result['normcontrol_report']['status'],
                    'compliance_score': result['onk_compliance']['overall_score'],
                    'total_issues': result['onk_compliance']['total_issues'],
                    'critical_issues': result['onk_compliance']['critical_issues']
                }
                report['documents'].append(doc_info)
        
        return report
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики системы"""
        total_documents = sum(batch['total_documents'] for batch in self.batch_results)
        processed_documents = sum(batch['processed_documents'] for batch in self.batch_results)
        total_issues = sum(
            batch['batch_analysis']['total_issues'] 
            for batch in self.batch_results
        )
        
        return {
            'total_batches': len(self.batch_results),
            'total_documents': total_documents,
            'processed_documents': processed_documents,
            'success_rate': (processed_documents / total_documents) * 100 if total_documents > 0 else 0,
            'total_issues_found': total_issues,
            'cache_size': len(self.results_cache)
        }


def main():
    """Основная функция для демонстрации системы"""
    print("🚀 ИНТЕГРИРОВАННАЯ СИСТЕМА НОРМОКОНТРОЛЯ")
    print("=" * 80)
    
    # Создание системы
    system = IntegratedNormControlSystem()
    
    # Тестовые документы
    test_documents = [
        "tests/TestDocs/for_check/3401-21089-РД-01-220-221-АР_4_0_RU_IFC (1).pdf",
        "tests/TestDocs/Norms/Корпоративные/Перечень НТД для руководства внутри ОНК по маркам.pdf",
        "tests/TestDocs/Norms/Корпоративные/Чек-лист перед НК ПТИ.pdf"
    ]
    
    # Обработка пакета документов
    print(f"📄 Обработка пакета из {len(test_documents)} документов...")
    batch_result = system.process_batch(test_documents)
    
    # Вывод результатов
    print(f"\n📊 РЕЗУЛЬТАТЫ ОБРАБОТКИ:")
    print(f"  Всего документов: {batch_result['total_documents']}")
    print(f"  Обработано успешно: {batch_result['processed_documents']}")
    print(f"  Ошибок: {batch_result['failed_documents']}")
    print(f"  Время обработки: {batch_result['processing_time']:.2f} сек")
    
    # Анализ пакета
    analysis = batch_result['batch_analysis']
    print(f"\n📈 АНАЛИЗ ПАКЕТА:")
    print(f"  Всего проблем: {analysis['total_issues']}")
    print(f"  Критических: {analysis['critical_issues']}")
    print(f"  Предупреждений: {analysis['warning_issues']}")
    print(f"  Информационных: {analysis['info_issues']}")
    print(f"  Средняя оценка соответствия: {analysis['average_compliance']:.1f}%")
    
    # Распределение статусов
    print(f"\n📋 РАСПРЕДЕЛЕНИЕ СТАТУСОВ:")
    for status, count in analysis['status_distribution'].items():
        print(f"  {status}: {count}")
    
    # Рекомендации
    if analysis['recommendations']:
        print(f"\n💡 РЕКОМЕНДАЦИИ:")
        for i, rec in enumerate(analysis['recommendations'], 1):
            print(f"  {i}. {rec}")
    
    # Генерация отчета
    report = system.generate_batch_report()
    print(f"\n📋 ОТЧЕТ ПО ПАКЕТУ:")
    print(f"  ID пакета: {report['batch_id']}")
    print(f"  Успешность: {report['summary']['success_rate']:.1f}%")
    print(f"  Время обработки: {report['summary']['processing_time']:.2f} сек")
    
    # Статистика системы
    stats = system.get_statistics()
    print(f"\n📊 СТАТИСТИКА СИСТЕМЫ:")
    print(f"  Всего пакетов: {stats['total_batches']}")
    print(f"  Всего документов: {stats['total_documents']}")
    print(f"  Обработано: {stats['processed_documents']}")
    print(f"  Успешность: {stats['success_rate']:.1f}%")
    print(f"  Найдено проблем: {stats['total_issues_found']}")
    print(f"  Размер кэша: {stats['cache_size']}")
    
    # Сохранение результатов
    output_file = f"integrated_normcontrol_results_{int(time.time())}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(batch_result, f, ensure_ascii=False, indent=2)
    print(f"\n💾 Результаты сохранены в {output_file}")


if __name__ == "__main__":
    main()
