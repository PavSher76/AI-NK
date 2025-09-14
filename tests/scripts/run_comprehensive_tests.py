#!/usr/bin/env python3
"""
Главный скрипт для запуска всех тестов проекта AI-NK
Координирует выполнение всех модульных тестов и генерирует комплексный отчет
"""

import asyncio
import json
import time
from datetime import datetime
import logging
import sys
import os

# Импорт модульных тестеров
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from test_chat_ai_module import ChatAITester
from test_outgoing_control_module import OutgoingControlTester
from test_ntd_consultation_module import NTDConsultationTester
from test_calculations_module import CalculationsTester

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs', 'comprehensive_test_suite.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ComprehensiveTestRunner:
    def __init__(self):
        self.testers = {
            'chat_ai': ChatAITester(),
            'outgoing_control': OutgoingControlTester(),
            'ntd_consultation': NTDConsultationTester(),
            'calculations': CalculationsTester()
        }
        
        self.results = {}
        self.start_time = None
        self.end_time = None

    async def run_all_tests(self):
        """Запуск всех тестов"""
        logger.info("🚀 Запуск комплексного тестирования AI-NK...")
        self.start_time = time.time()
        
        # Запуск тестов по модулям
        for module_name, tester in self.testers.items():
            logger.info(f"🧪 Тестирование модуля: {module_name}")
            try:
                module_results = await tester.run_all_tests()
                self.results[module_name] = module_results
                logger.info(f"✅ Модуль {module_name} протестирован")
            except Exception as e:
                logger.error(f"❌ Ошибка тестирования модуля {module_name}: {e}")
                self.results[module_name] = {'error': str(e)}
        
        self.end_time = time.time()
        return self.results

    def calculate_overall_statistics(self):
        """Подсчет общей статистики"""
        total_tests = 0
        passed_tests = 0
        module_stats = {}
        
        for module_name, module_results in self.results.items():
            if 'error' in module_results:
                module_stats[module_name] = {
                    'status': 'ERROR',
                    'tests_total': 0,
                    'tests_passed': 0,
                    'success_rate': 0
                }
                continue
            
            module_tests = sum(1 for result in module_results.values() if isinstance(result, bool))
            module_passed = sum(1 for result in module_results.values() if result is True)
            module_success_rate = (module_passed / module_tests) * 100 if module_tests > 0 else 0
            
            module_stats[module_name] = {
                'status': 'PASSED' if module_success_rate >= 80 else 'FAILED',
                'tests_total': module_tests,
                'tests_passed': module_passed,
                'success_rate': module_success_rate
            }
            
            total_tests += module_tests
            passed_tests += module_passed
        
        overall_success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'overall_success_rate': overall_success_rate,
            'module_stats': module_stats,
            'duration': self.end_time - self.start_time if self.end_time and self.start_time else 0
        }

    def generate_comprehensive_report(self):
        """Генерация комплексного отчета"""
        statistics = self.calculate_overall_statistics()
        
        report = {
            'project': 'AI-NK',
            'test_suite': 'Comprehensive Testing Suite',
            'timestamp': datetime.now().isoformat(),
            'statistics': statistics,
            'module_results': self.results,
            'test_parameters': self.get_test_parameters()
        }
        
        # Сохранение JSON отчета
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        json_path = os.path.join(base_dir, 'reports', 'comprehensive_test_report.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        # Генерация HTML отчета
        self.generate_html_report(report)
        
        # Генерация текстового отчета
        self.generate_text_report(report)
        
        return report

    def get_test_parameters(self):
        """Получение параметров тестирования"""
        return {
            'test_documents': {
                'pdf': 'TestDocs/for_check/СЗ_ТЕСТ.pdf',
                'docx': 'TestDocs/for_check/СЗ_ТЕСТ.docx',
                'gost_pdf': 'TestDocs/for_check/3401-21089-РД-01-220-221-АР_4_0_RU_IFC (1).pdf'
            },
            'calculation_parameters': {
                'welding_strength': {
                    'material': 'steel',
                    'thickness': 10,
                    'weld_type': 'butt',
                    'load': 1000
                },
                'material_properties': {
                    'material': 'aluminum',
                    'temperature': 20,
                    'stress': 100
                },
                'safety_factors': {
                    'load': 1000,
                    'safety_factor': 2.5,
                    'material_yield': 250
                }
            },
            'test_queries': [
                "требования к качеству сварных швов",
                "ГОСТ 14771 сварка",
                "допуски и посадки",
                "материалы для строительства"
            ]
        }

    def generate_html_report(self, report):
        """Генерация HTML отчета"""
        html_content = f"""
        <!DOCTYPE html>
        <html lang="ru">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Отчет о комплексном тестировании AI-NK</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 1200px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; }}
                .header h1 {{ margin: 0; font-size: 2.5em; }}
                .header p {{ margin: 10px 0 0 0; font-size: 1.2em; opacity: 0.9; }}
                .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }}
                .stat-card {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); text-align: center; }}
                .stat-card h3 {{ margin: 0 0 10px 0; color: #333; }}
                .stat-card .value {{ font-size: 2em; font-weight: bold; color: #667eea; }}
                .module {{ margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 10px; background: white; }}
                .module-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }}
                .module-title {{ font-size: 1.5em; font-weight: bold; color: #333; }}
                .module-status {{ padding: 5px 15px; border-radius: 20px; font-weight: bold; }}
                .status-passed {{ background-color: #d4edda; color: #155724; }}
                .status-failed {{ background-color: #f8d7da; color: #721c24; }}
                .status-error {{ background-color: #fff3cd; color: #856404; }}
                .test {{ margin: 10px 0; padding: 15px; background-color: #f8f9fa; border-radius: 5px; border-left: 4px solid #ddd; }}
                .test.passed {{ border-left-color: #28a745; }}
                .test.failed {{ border-left-color: #dc3545; }}
                .test-name {{ font-weight: bold; margin-bottom: 5px; }}
                .test-status {{ font-size: 0.9em; }}
                .parameters {{ background-color: #e9ecef; padding: 20px; border-radius: 10px; margin-top: 30px; }}
                .parameters h3 {{ margin-top: 0; color: #495057; }}
                .parameter-group {{ margin: 15px 0; }}
                .parameter-group h4 {{ margin: 10px 0 5px 0; color: #6c757d; }}
                .parameter-group pre {{ background-color: #f8f9fa; padding: 10px; border-radius: 5px; overflow-x: auto; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Отчет о комплексном тестировании AI-NK</h1>
                    <p>Время тестирования: {report['timestamp']}</p>
                    <p>Общий статус: <strong>{'ПРОЙДЕНО' if report['statistics']['overall_success_rate'] >= 80 else 'ПРОВАЛЕНО'}</strong></p>
                </div>
                
                <div class="stats">
                    <div class="stat-card">
                        <h3>Общая успешность</h3>
                        <div class="value">{report['statistics']['overall_success_rate']:.1f}%</div>
                    </div>
                    <div class="stat-card">
                        <h3>Всего тестов</h3>
                        <div class="value">{report['statistics']['total_tests']}</div>
                    </div>
                    <div class="stat-card">
                        <h3>Пройдено тестов</h3>
                        <div class="value">{report['statistics']['passed_tests']}</div>
                    </div>
                    <div class="stat-card">
                        <h3>Время выполнения</h3>
                        <div class="value">{report['statistics']['duration']:.1f}с</div>
                    </div>
                </div>
        """
        
        # Добавление результатов по модулям
        for module_name, module_results in report['module_results'].items():
            module_stats = report['statistics']['module_stats'][module_name]
            status_class = f"status-{module_stats['status'].lower()}"
            
            html_content += f"""
                <div class="module">
                    <div class="module-header">
                        <div class="module-title">{module_name.replace('_', ' ').title()}</div>
                        <div class="module-status {status_class}">{module_stats['status']}</div>
                    </div>
                    <p>Успешность: {module_stats['success_rate']:.1f}% ({module_stats['tests_passed']}/{module_stats['tests_total']})</p>
            """
            
            if 'error' in module_results:
                html_content += f"""
                    <div class="test failed">
                        <div class="test-name">Ошибка тестирования</div>
                        <div class="test-status">❌ {module_results['error']}</div>
                    </div>
                """
            else:
                for test_name, result in module_results.items():
                    test_class = "passed" if result else "failed"
                    status_icon = "✅" if result else "❌"
                    status_text = "ПРОЙДЕН" if result else "ПРОВАЛЕН"
                    
                    html_content += f"""
                        <div class="test {test_class}">
                            <div class="test-name">{test_name.replace('_', ' ').title()}</div>
                            <div class="test-status">{status_icon} {status_text}</div>
                        </div>
                    """
            
            html_content += "</div>"
        
        # Добавление параметров тестирования
        html_content += """
                <div class="parameters">
                    <h3>Параметры тестирования</h3>
        """
        
        for param_group, params in report['test_parameters'].items():
            html_content += f"""
                    <div class="parameter-group">
                        <h4>{param_group.replace('_', ' ').title()}</h4>
                        <pre>{json.dumps(params, ensure_ascii=False, indent=2)}</pre>
                    </div>
            """
        
        html_content += """
                </div>
            </div>
        </body>
        </html>
        """
        
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        html_path = os.path.join(base_dir, 'reports', 'comprehensive_test_report.html')
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

    def generate_text_report(self, report):
        """Генерация текстового отчета"""
        text_content = f"""
ОТЧЕТ О КОМПЛЕКСНОМ ТЕСТИРОВАНИИ AI-NK
========================================

Время тестирования: {report['timestamp']}
Общая успешность: {report['statistics']['overall_success_rate']:.1f}%
Всего тестов: {report['statistics']['total_tests']}
Пройдено тестов: {report['statistics']['passed_tests']}
Время выполнения: {report['statistics']['duration']:.1f} секунд

РЕЗУЛЬТАТЫ ПО МОДУЛЯМ:
======================

"""
        
        for module_name, module_results in report['module_results'].items():
            module_stats = report['statistics']['module_stats'][module_name]
            
            text_content += f"""
{module_name.replace('_', ' ').upper()}:
  Статус: {module_stats['status']}
  Успешность: {module_stats['success_rate']:.1f}% ({module_stats['tests_passed']}/{module_stats['tests_total']})
  
"""
            
            if 'error' in module_results:
                text_content += f"  Ошибка: {module_results['error']}\n"
            else:
                for test_name, result in module_results.items():
                    status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
                    text_content += f"  {test_name}: {status}\n"
            
            text_content += "\n"
        
        text_content += """
ПАРАМЕТРЫ ТЕСТИРОВАНИЯ:
=======================

"""
        
        for param_group, params in report['test_parameters'].items():
            text_content += f"{param_group.replace('_', ' ').upper()}:\n"
            text_content += f"{json.dumps(params, ensure_ascii=False, indent=2)}\n\n"
        
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        txt_path = os.path.join(base_dir, 'reports', 'comprehensive_test_report.txt')
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(text_content)

    def print_summary(self, report):
        """Вывод сводки результатов"""
        print("\n" + "="*80)
        print("📊 КОМПЛЕКСНЫЙ ОТЧЕТ О ТЕСТИРОВАНИИ AI-NK")
        print("="*80)
        
        print(f"🕐 Время тестирования: {report['timestamp']}")
        print(f"🎯 Общая успешность: {report['statistics']['overall_success_rate']:.1f}%")
        print(f"📈 Всего тестов: {report['statistics']['total_tests']}")
        print(f"✅ Пройдено тестов: {report['statistics']['passed_tests']}")
        print(f"⏱️ Время выполнения: {report['statistics']['duration']:.1f} секунд")
        
        print("\n📋 РЕЗУЛЬТАТЫ ПО МОДУЛЯМ:")
        print("-" * 40)
        
        for module_name, module_results in report['module_results'].items():
            module_stats = report['statistics']['module_stats'][module_name]
            status_icon = "✅" if module_stats['status'] == 'PASSED' else "❌" if module_stats['status'] == 'FAILED' else "⚠️"
            
            print(f"{status_icon} {module_name.replace('_', ' ').upper()}: {module_stats['success_rate']:.1f}% ({module_stats['tests_passed']}/{module_stats['tests_total']})")
        
        print("\n📄 Отчеты сохранены:")
        print("  - comprehensive_test_report.json")
        print("  - comprehensive_test_report.html")
        print("  - comprehensive_test_report.txt")
        print("  - comprehensive_test_suite.log")

async def main():
    """Основная функция"""
    runner = ComprehensiveTestRunner()
    
    try:
        # Запуск всех тестов
        results = await runner.run_all_tests()
        
        # Генерация отчета
        report = runner.generate_comprehensive_report()
        
        # Вывод сводки
        runner.print_summary(report)
        
        # Возврат кода выхода
        if report['statistics']['overall_success_rate'] >= 80:
            sys.exit(0)  # Успешно
        else:
            sys.exit(1)  # Есть ошибки
            
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        sys.exit(2)  # Критическая ошибка

if __name__ == "__main__":
    asyncio.run(main())
