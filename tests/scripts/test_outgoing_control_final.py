#!/usr/bin/env python3
"""
Повторное тестирование системы выходного контроля корреспонденции
с использованием файла E320.E32C-OUT-03484_от_20.05.2025_с_грубыми_ошибками
"""

import requests
import json
import time
from datetime import datetime
from pathlib import Path

class FinalOutgoingControlTester:
    """Финальный тестер системы выходного контроля корреспонденции"""
    
    def __init__(self):
        self.outgoing_control_url = "http://localhost:8006"
        self.spellchecker_url = "http://localhost:8007"
        self.test_document_path = "TestDocs/for_check/E320.E32C-OUT-03484_от_20.05.2025_с_грубыми_ошибками.pdf"
        self.document_id = None
        self.test_results = []
        self.start_time = datetime.now()
        
    def log_test(self, test_name, status, details=None, error=None, metrics=None):
        """Логирование результата теста"""
        result = {
            "test_name": test_name,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "details": details,
            "error": error,
            "metrics": metrics
        }
        self.test_results.append(result)
        
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_icon} {test_name}: {status}")
        if details:
            print(f"   Детали: {details}")
        if metrics:
            print(f"   Метрики: {metrics}")
        if error:
            print(f"   Ошибка: {error}")
        print()
    
    def test_system_health(self):
        """Тест 1: Проверка здоровья системы"""
        print("🔍 Тест 1: Проверка здоровья системы")
        print("="*60)
        
        # Проверка outgoing-control-service
        try:
            response = requests.get(f"{self.outgoing_control_url}/health", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                self.log_test(
                    "Outgoing Control Service Health",
                    "PASS",
                    f"Статус: {health_data.get('status')}, Spellchecker: {health_data.get('spellchecker_service')}"
                )
            else:
                self.log_test("Outgoing Control Service Health", "FAIL", error=f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Outgoing Control Service Health", "FAIL", error=str(e))
        
        # Проверка spellchecker-service
        try:
            response = requests.get(f"{self.spellchecker_url}/health", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                hunspell_status = "✅ Работает" if health_data.get('hunspell_available') else "❌ Недоступен"
                lt_status = "✅ Работает" if health_data.get('languagetool_available') else "❌ Недоступен"
                
                self.log_test(
                    "Spellchecker Service Health",
                    "PASS",
                    f"Статус: {health_data.get('status')}, Hunspell: {hunspell_status}, LanguageTool: {lt_status}",
                    metrics={
                        "hunspell_available": health_data.get('hunspell_available'),
                        "languagetool_available": health_data.get('languagetool_available')
                    }
                )
            else:
                self.log_test("Spellchecker Service Health", "FAIL", error=f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Spellchecker Service Health", "FAIL", error=str(e))
    
    def test_document_upload(self):
        """Тест 2: Загрузка тестового документа"""
        print("🔍 Тест 2: Загрузка тестового документа")
        print("="*60)
        
        try:
            if not Path(self.test_document_path).exists():
                self.log_test("Document Upload", "FAIL", error="Файл не найден")
                return False
            
            with open(self.test_document_path, 'rb') as f:
                filename = Path(self.test_document_path).name
                files = {'file': (filename, f, 'application/pdf')}
                response = requests.post(f"{self.outgoing_control_url}/upload", files=files, timeout=30)
            
            if response.status_code == 200:
                doc_data = response.json()
                self.document_id = doc_data.get('document_id') or doc_data.get('id')
                
                metrics = {
                    "document_id": self.document_id,
                    "filename": doc_data.get('filename'),
                    "text_length": len(doc_data.get('text', '')),
                    "pages_count": doc_data.get('pages_count', 0),
                    "chunks_count": doc_data.get('chunks_count', 0)
                }
                
                self.log_test(
                    "Document Upload",
                    "PASS",
                    f"Документ загружен: {doc_data.get('filename')}, ID: {self.document_id}",
                    metrics=metrics
                )
                return True
            else:
                self.log_test("Document Upload", "FAIL", error=f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Document Upload", "FAIL", error=str(e))
            return False
    
    def test_spellcheck_analysis(self):
        """Тест 3: Анализ проверки орфографии"""
        print("🔍 Тест 3: Анализ проверки орфографии")
        print("="*60)
        
        if not self.document_id:
            self.log_test("Spellcheck Analysis", "SKIP", "Документ не загружен")
            return
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.outgoing_control_url}/spellcheck",
                json={"document_id": self.document_id},
                timeout=60
            )
            end_time = time.time()
            
            if response.status_code == 200:
                result = response.json()
                spell_results = result.get('spell_check_results', {})
                
                metrics = {
                    "total_words": spell_results.get('total_words', 0),
                    "misspelled_count": spell_results.get('misspelled_count', 0),
                    "accuracy": spell_results.get('accuracy', 0),
                    "method": spell_results.get('method', 'unknown'),
                    "processing_time": end_time - start_time,
                    "errors_found": len(spell_results.get('errors', []))
                }
                
                # Анализ найденных ошибок
                errors = spell_results.get('errors', [])
                error_types = {}
                for error in errors:
                    error_type = error.get('type', 'unknown')
                    error_types[error_type] = error_types.get(error_type, 0) + 1
                
                # Примеры ошибок
                sample_errors = errors[:5] if errors else []
                
                self.log_test(
                    "Spellcheck Analysis",
                    "PASS",
                    f"Найдено {metrics['misspelled_count']} ошибок из {metrics['total_words']} слов (точность: {metrics['accuracy']:.2f}%)",
                    error=None,
                    metrics=metrics
                )
            else:
                self.log_test("Spellcheck Analysis", "FAIL", error=f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Spellcheck Analysis", "FAIL", error=str(e))
    
    def test_grammar_check_analysis(self):
        """Тест 4: Анализ проверки грамматики"""
        print("🔍 Тест 4: Анализ проверки грамматики")
        print("="*60)
        
        if not self.document_id:
            self.log_test("Grammar Check Analysis", "SKIP", "Документ не загружен")
            return
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.outgoing_control_url}/grammar-check",
                json={"document_id": self.document_id},
                timeout=60
            )
            end_time = time.time()
            
            if response.status_code == 200:
                result = response.json()
                grammar_results = result.get('grammar_results', {})
                
                metrics = {
                    "total_errors": grammar_results.get('total_errors', 0),
                    "method": grammar_results.get('method', 'unknown'),
                    "processing_time": end_time - start_time,
                    "errors_found": len(grammar_results.get('errors', []))
                }
                
                # Анализ найденных ошибок
                errors = grammar_results.get('errors', [])
                error_types = {}
                for error in errors:
                    error_type = error.get('type', 'unknown')
                    error_types[error_type] = error_types.get(error_type, 0) + 1
                
                # Примеры ошибок
                sample_errors = errors[:5] if errors else []
                
                self.log_test(
                    "Grammar Check Analysis",
                    "PASS",
                    f"Найдено {metrics['total_errors']} грамматических ошибок",
                    error=None,
                    metrics=metrics
                )
            else:
                self.log_test("Grammar Check Analysis", "FAIL", error=f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Grammar Check Analysis", "FAIL", error=str(e))
    
    def test_comprehensive_check_analysis(self):
        """Тест 5: Анализ комплексной проверки"""
        print("🔍 Тест 5: Анализ комплексной проверки")
        print("="*60)
        
        if not self.document_id:
            self.log_test("Comprehensive Check Analysis", "SKIP", "Документ не загружен")
            return
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.outgoing_control_url}/comprehensive-check",
                json={"document_id": self.document_id},
                timeout=120
            )
            end_time = time.time()
            
            if response.status_code == 200:
                result = response.json()
                comprehensive_results = result.get('comprehensive_results', {})
                
                # Результаты орфографии
                spelling = comprehensive_results.get('spelling', {})
                grammar = comprehensive_results.get('grammar', {})
                
                metrics = {
                    "total_errors": comprehensive_results.get('total_errors', 0),
                    "spelling_errors": spelling.get('misspelled_count', 0),
                    "grammar_errors": grammar.get('total_errors', 0),
                    "overall_accuracy": comprehensive_results.get('overall_accuracy', 0),
                    "processing_time": end_time - start_time,
                    "spelling_method": spelling.get('method', 'unknown'),
                    "grammar_method": grammar.get('method', 'unknown')
                }
                
                # Анализ всех ошибок
                all_errors = comprehensive_results.get('all_errors', [])
                error_types = {}
                for error in all_errors:
                    error_type = error.get('type', 'unknown')
                    error_types[error_type] = error_types.get(error_type, 0) + 1
                
                # Примеры ошибок
                sample_errors = all_errors[:10] if all_errors else []
                
                self.log_test(
                    "Comprehensive Check Analysis",
                    "PASS",
                    f"Всего ошибок: {metrics['total_errors']} (орфография: {metrics['spelling_errors']}, грамматика: {metrics['grammar_errors']})",
                    error=None,
                    metrics=metrics
                )
            else:
                self.log_test("Comprehensive Check Analysis", "FAIL", error=f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Comprehensive Check Analysis", "FAIL", error=str(e))
    
    def test_llm_processing(self):
        """Тест 6: Обработка LLM"""
        print("🔍 Тест 6: Обработка LLM")
        print("="*60)
        
        if not self.document_id:
            self.log_test("LLM Processing", "SKIP", "Документ не загружен")
            return
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.outgoing_control_url}/expert-analysis",
                json={"document_id": self.document_id},
                timeout=120
            )
            end_time = time.time()
            
            if response.status_code == 200:
                result = response.json()
                
                metrics = {
                    "status": result.get('status'),
                    "processing_time": end_time - start_time,
                    "has_analysis": bool(result.get('expert_analysis'))
                }
                
                self.log_test(
                    "LLM Processing",
                    "PASS",
                    f"Статус: {metrics['status']}, Время: {metrics['processing_time']:.2f}с",
                    metrics=metrics
                )
            else:
                self.log_test("LLM Processing", "FAIL", error=f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("LLM Processing", "FAIL", error=str(e))
    
    def test_report_generation(self):
        """Тест 7: Генерация отчета"""
        print("🔍 Тест 7: Генерация отчета")
        print("="*60)
        
        if not self.document_id:
            self.log_test("Report Generation", "SKIP", "Документ не загружен")
            return
        
        try:
            start_time = time.time()
            response = requests.get(
                f"{self.outgoing_control_url}/report/{self.document_id}",
                timeout=60
            )
            end_time = time.time()
            
            if response.status_code == 200:
                result = response.json()
                
                metrics = {
                    "status": result.get('status'),
                    "verdict": result.get('verdict', 'N/A'),
                    "processing_time": end_time - start_time,
                    "has_report": bool(result.get('report'))
                }
                
                self.log_test(
                    "Report Generation",
                    "PASS",
                    f"Статус: {metrics['status']}, Вердикт: {metrics['verdict']}",
                    metrics=metrics
                )
            else:
                self.log_test("Report Generation", "FAIL", error=f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Report Generation", "FAIL", error=str(e))
    
    def test_performance_benchmark(self):
        """Тест 8: Бенчмарк производительности"""
        print("🔍 Тест 8: Бенчмарк производительности")
        print("="*60)
        
        test_texts = [
            "Это есть тестовый текст с ошибками орфографии",
            "саа тветствии с письмом заказчика",
            "техникокоммерческое при дложение по а бъекту",
            "не получен ы падтверждение стоимости работ",
            "утачнить парядок р игистрации ОПО"
        ]
        
        performance_results = []
        
        for i, text in enumerate(test_texts):
            try:
                start_time = time.time()
                response = requests.post(
                    f"{self.spellchecker_url}/comprehensive-check",
                    json={"text": text, "language": "ru"},
                    timeout=30
                )
                end_time = time.time()
                
                if response.status_code == 200:
                    result = response.json()
                    comprehensive = result.get('comprehensive', {})
                    
                    performance_results.append({
                        "text_length": len(text),
                        "processing_time": end_time - start_time,
                        "total_errors": comprehensive.get('total_errors', 0),
                        "accuracy": comprehensive.get('overall_accuracy', 0)
                    })
                else:
                    performance_results.append({
                        "text_length": len(text),
                        "processing_time": -1,
                        "total_errors": -1,
                        "accuracy": -1
                    })
            except Exception as e:
                performance_results.append({
                    "text_length": len(text),
                    "processing_time": -1,
                    "total_errors": -1,
                    "accuracy": -1
                })
        
        # Расчет средних показателей
        valid_results = [r for r in performance_results if r['processing_time'] > 0]
        if valid_results:
            avg_processing_time = sum(r['processing_time'] for r in valid_results) / len(valid_results)
            avg_accuracy = sum(r['accuracy'] for r in valid_results) / len(valid_results)
            total_errors = sum(r['total_errors'] for r in valid_results)
            
            metrics = {
                "avg_processing_time": avg_processing_time,
                "avg_accuracy": avg_accuracy,
                "total_errors_found": total_errors,
                "tests_completed": len(valid_results),
                "tests_failed": len(performance_results) - len(valid_results)
            }
            
            self.log_test(
                "Performance Benchmark",
                "PASS",
                f"Среднее время: {avg_processing_time:.3f}с, Средняя точность: {avg_accuracy:.2f}%",
                metrics=metrics
            )
        else:
            self.log_test("Performance Benchmark", "FAIL", error="Все тесты производительности провалились")
    
    def test_error_detection_accuracy(self):
        """Тест 9: Точность обнаружения ошибок"""
        print("🔍 Тест 9: Точность обнаружения ошибок")
        print("="*60)
        
        # Известные ошибки из документа
        known_errors = [
            ("саа тветствии", "в соответствии"),
            ("оценк а", "оценка"),
            ("при дложение", "предложение"),
            ("а бъекту", "объекту"),
            ("не получен ы", "не получены"),
            ("падтверждение", "подтверждение"),
            ("гаранти и", "гарантии"),
            ("пре оритетно сти", "приоритетности"),
            ("са гласование", "согласование"),
            ("неполучен а", "не получен"),
            ("твет", "ответ"),
            ("предпра ектной", "предпроектной"),
            ("са вещаний", "совещаний"),
            ("инфо рмация", "информация"),
            ("раннее", "ранее"),
            ("пр аекту", "проекту"),
            ("пра шу", "прошу"),
            ("поттвердить", "подтвердить"),
            ("га товность", "готовность"),
            ("дагавора", "договора"),
            ("расмотреть", "рассмотреть"),
            ("обь ем", "объем"),
            ("стадийн ость", "стадийность"),
            ("праектирования", "проектирования"),
            ("па скольку", "поскольку"),
            ("утачнить", "уточнить"),
            ("парядок", "порядок"),
            ("р игистрации", "регистрации"),
            ("Пр аект", "Проект")
        ]
        
        detection_results = []
        
        for error_text, correct_text in known_errors:
            try:
                response = requests.post(
                    f"{self.spellchecker_url}/comprehensive-check",
                    json={"text": error_text, "language": "ru"},
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    comprehensive = result.get('comprehensive', {})
                    all_errors = comprehensive.get('all_errors', [])
                    
                    # Проверяем, найдена ли ошибка
                    error_found = len(all_errors) > 0
                    detection_results.append({
                        "error_text": error_text,
                        "correct_text": correct_text,
                        "detected": error_found,
                        "errors_found": len(all_errors)
                    })
                else:
                    detection_results.append({
                        "error_text": error_text,
                        "correct_text": correct_text,
                        "detected": False,
                        "errors_found": 0
                    })
            except Exception as e:
                detection_results.append({
                    "error_text": error_text,
                    "correct_text": correct_text,
                    "detected": False,
                    "errors_found": 0
                })
        
        # Расчет метрик
        total_errors = len(detection_results)
        detected_errors = sum(1 for r in detection_results if r['detected'])
        detection_rate = (detected_errors / total_errors * 100) if total_errors > 0 else 0
        
        metrics = {
            "total_known_errors": total_errors,
            "detected_errors": detected_errors,
            "detection_rate": detection_rate,
            "missed_errors": total_errors - detected_errors
        }
        
        # Примеры пропущенных ошибок
        missed_errors = [r for r in detection_results if not r['detected']]
        
        self.log_test(
            "Error Detection Accuracy",
            "PASS" if detection_rate >= 70 else "WARN",
            f"Обнаружено {detected_errors} из {total_errors} ошибок ({detection_rate:.1f}%)",
            error=None,
            metrics=metrics
        )
    
    def generate_final_report(self):
        """Генерация итогового отчета"""
        print("\n" + "="*80)
        print("📊 ИТОГОВЫЙ ОТЧЕТ ПОВТОРНОГО ТЕСТИРОВАНИЯ")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed_tests = len([r for r in self.test_results if r['status'] == 'FAIL'])
        skipped_tests = len([r for r in self.test_results if r['status'] == 'SKIP'])
        warning_tests = len([r for r in self.test_results if r['status'] == 'WARN'])
        
        print(f"📈 Общая статистика:")
        print(f"   Всего тестов: {total_tests}")
        print(f"   ✅ Пройдено: {passed_tests}")
        print(f"   ❌ Провалено: {failed_tests}")
        print(f"   ⚠️  Предупреждения: {warning_tests}")
        print(f"   ⏭️  Пропущено: {skipped_tests}")
        print(f"   📊 Успешность: {(passed_tests/total_tests*100):.1f}%")
        
        print(f"\n⏱️ Время выполнения: {datetime.now() - self.start_time}")
        
        # Анализ ключевых метрик
        print(f"\n🔍 Ключевые метрики:")
        
        # Найдем тесты с метриками
        for result in self.test_results:
            if result.get('metrics'):
                metrics = result['metrics']
                test_name = result['test_name']
                
                if 'accuracy' in metrics:
                    print(f"   {test_name}: Точность {metrics['accuracy']:.2f}%")
                if 'total_errors' in metrics:
                    print(f"   {test_name}: Найдено ошибок {metrics['total_errors']}")
                if 'processing_time' in metrics:
                    print(f"   {test_name}: Время обработки {metrics['processing_time']:.3f}с")
                if 'detection_rate' in metrics:
                    print(f"   {test_name}: Процент обнаружения {metrics['detection_rate']:.1f}%")
        
        print(f"\n📋 Детальные результаты:")
        for result in self.test_results:
            status_icon = "✅" if result['status'] == "PASS" else "❌" if result['status'] == "FAIL" else "⚠️" if result['status'] == "WARN" else "⏭️"
            print(f"   {status_icon} {result['test_name']}: {result['status']}")
            if result.get('details'):
                print(f"      Детали: {result['details']}")
            if result.get('error'):
                print(f"      Ошибка: {result['error']}")
        
        # Сохранение отчета в файл
        report_data = {
            "test_summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "skipped_tests": skipped_tests,
                "warning_tests": warning_tests,
                "success_rate": passed_tests/total_tests*100,
                "execution_time": str(datetime.now() - self.start_time),
                "test_document": self.test_document_path,
                "document_id": self.document_id
            },
            "test_results": self.test_results,
            "timestamp": datetime.now().isoformat()
        }
        
        report_file = f"outgoing_control_final_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Детальный отчет сохранен в файл: {report_file}")
        
        return report_data
    
    def run_all_tests(self):
        """Запуск всех тестов"""
        print("🚀 ПОВТОРНОЕ ТЕСТИРОВАНИЕ СИСТЕМЫ ВЫХОДНОГО КОНТРОЛЯ КОРРЕСПОНДЕНЦИИ")
        print("="*80)
        print(f"📄 Тестовый документ: {self.test_document_path}")
        print(f"⏰ Время тестирования: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
        print("="*80)
        print()
        
        # Тест 1: Проверка здоровья системы
        self.test_system_health()
        
        # Тест 2: Загрузка документа
        if self.test_document_upload():
            # Тест 3: Анализ проверки орфографии
            self.test_spellcheck_analysis()
            
            # Тест 4: Анализ проверки грамматики
            self.test_grammar_check_analysis()
            
            # Тест 5: Анализ комплексной проверки
            self.test_comprehensive_check_analysis()
            
            # Тест 6: Обработка LLM
            self.test_llm_processing()
            
            # Тест 7: Генерация отчета
            self.test_report_generation()
        
        # Тест 8: Бенчмарк производительности
        self.test_performance_benchmark()
        
        # Тест 9: Точность обнаружения ошибок
        self.test_error_detection_accuracy()
        
        # Генерация итогового отчета
        return self.generate_final_report()


def main():
    """Основная функция"""
    tester = FinalOutgoingControlTester()
    report = tester.run_all_tests()
    return report


if __name__ == "__main__":
    main()
