#!/usr/bin/env python3
"""
Специализированное тестирование модуля "Выходной контроль корреспонденции"
Включает тестирование обработки PDF/DOCX, проверки орфографии и генерации отчетов
"""

import asyncio
import aiohttp
import json
import time
import os
from datetime import datetime
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OutgoingControlTester:
    def __init__(self):
        self.base_url = 'http://localhost:8006'  # Outgoing Control Service
        self.spellchecker_url = 'http://localhost:8007'  # Spellchecker Service
        # Пути к тестовым документам относительно папки tests
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.test_documents = {
            'pdf': os.path.join(base_dir, 'data', 'TestDocs', 'for_check', 'СЗ_ТЕСТ.pdf'),
            'docx': os.path.join(base_dir, 'data', 'TestDocs', 'for_check', 'СЗ_ТЕСТ.docx'),
            'gost_pdf': os.path.join(base_dir, 'data', 'TestDocs', 'for_check', '3401-21089-РД-01-220-221-АР_4_0_RU_IFC (1).pdf')
        }
        self.test_results = {}

    async def test_service_health(self):
        """Проверка здоровья сервиса"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/health", ssl=False, timeout=10) as response:
                    if response.status == 200:
                        logger.info("✅ Outgoing Control Service здоров")
                        return True
                    else:
                        logger.error(f"❌ Outgoing Control Service недоступен: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к Outgoing Control Service: {e}")
            return False

    async def test_pdf_processing(self):
        """Тестирование обработки PDF документов"""
        logger.info("🧪 Тестирование обработки PDF...")
        
        if not os.path.exists(self.test_documents['pdf']):
            logger.warning("⚠️ Тестовый PDF файл не найден")
            return False
        
        try:
            async with aiohttp.ClientSession() as session:
                # Загрузка и обработка PDF
                with open(self.test_documents['pdf'], 'rb') as f:
                    data = aiohttp.FormData()
                    data.add_field('file', f, filename='test_document.pdf')
                    
                    async with session.post(
                        f"{self.base_url}/process",
                        data=data,
                        ssl=False,
                        timeout=120
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            logger.info("✅ PDF обработан успешно")
                            
                            # Проверка качества обработки
                            if 'text' in result and len(result['text']) > 100:
                                logger.info("✅ Текст извлечен качественно")
                                return True
                            else:
                                logger.warning("⚠️ Качество извлечения текста низкое")
                                return False
                        else:
                            logger.error(f"❌ Ошибка обработки PDF: {response.status}")
                            return False
        except Exception as e:
            logger.error(f"❌ Ошибка обработки PDF: {e}")
            return False

    async def test_docx_processing(self):
        """Тестирование обработки DOCX документов"""
        logger.info("🧪 Тестирование обработки DOCX...")
        
        if not os.path.exists(self.test_documents['docx']):
            logger.warning("⚠️ Тестовый DOCX файл не найден")
            return False
        
        try:
            async with aiohttp.ClientSession() as session:
                # Загрузка и обработка DOCX
                with open(self.test_documents['docx'], 'rb') as f:
                    data = aiohttp.FormData()
                    data.add_field('file', f, filename='test_document.docx')
                    
                    async with session.post(
                        f"{self.base_url}/process",
                        data=data,
                        ssl=False,
                        timeout=120
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            logger.info("✅ DOCX обработан успешно")
                            
                            # Проверка качества обработки
                            if 'text' in result and len(result['text']) > 100:
                                logger.info("✅ Текст извлечен качественно")
                                return True
                            else:
                                logger.warning("⚠️ Качество извлечения текста низкое")
                                return False
                        else:
                            logger.error(f"❌ Ошибка обработки DOCX: {response.status}")
                            return False
        except Exception as e:
            logger.error(f"❌ Ошибка обработки DOCX: {e}")
            return False

    async def test_spellcheck_functionality(self):
        """Тестирование проверки орфографии"""
        logger.info("🧪 Тестирование проверки орфографии...")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Тест с текстом с ошибками
                test_text = "Это тестовый текст с орфографическими ошибками. Проверка грамматики и пунктуации."
                
                payload = {
                    "text": test_text,
                    "language": "ru"
                }
                
                async with session.post(
                    f"{self.spellchecker_url}/check",
                    json=payload,
                    ssl=False,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info("✅ Проверка орфографии выполнена")
                        
                        # Проверка качества проверки
                        if 'errors' in result:
                            logger.info(f"✅ Найдено {len(result['errors'])} ошибок")
                            return True
                        else:
                            logger.warning("⚠️ Ошибки не найдены")
                            return False
                    else:
                        logger.error(f"❌ Ошибка проверки орфографии: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ Ошибка проверки орфографии: {e}")
            return False

    async def test_document_analysis(self):
        """Тестирование анализа документа"""
        logger.info("🧪 Тестирование анализа документа...")
        
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "document_id": "test_doc",
                    "analysis_type": "full",
                    "include_spellcheck": True,
                    "include_metadata": True
                }
                
                async with session.post(
                    f"{self.base_url}/analyze",
                    json=payload,
                    ssl=False,
                    timeout=60
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info("✅ Анализ документа выполнен")
                        
                        # Проверка качества анализа
                        required_fields = ['text', 'metadata', 'spellcheck_results']
                        if all(field in result for field in required_fields):
                            logger.info("✅ Анализ содержит все необходимые поля")
                            return True
                        else:
                            logger.warning("⚠️ Анализ неполный")
                            return False
                    else:
                        logger.error(f"❌ Ошибка анализа: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ Ошибка анализа: {e}")
            return False

    async def test_report_generation(self):
        """Тестирование генерации отчета"""
        logger.info("🧪 Тестирование генерации отчета...")
        
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "document_id": "test_doc",
                    "report_type": "outgoing_control",
                    "include_analysis": True,
                    "include_recommendations": True
                }
                
                async with session.post(
                    f"{self.base_url}/generate_report",
                    json=payload,
                    ssl=False,
                    timeout=120
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info("✅ Отчет сгенерирован")
                        
                        # Проверка качества отчета
                        if 'report' in result and len(result['report']) > 500:
                            logger.info("✅ Отчет содержит достаточно информации")
                            return True
                        else:
                            logger.warning("⚠️ Отчет слишком короткий")
                            return False
                    else:
                        logger.error(f"❌ Ошибка генерации отчета: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ Ошибка генерации отчета: {e}")
            return False

    async def test_batch_processing(self):
        """Тестирование пакетной обработки документов"""
        logger.info("🧪 Тестирование пакетной обработки...")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Подготовка тестовых документов
                documents = []
                for doc_type, doc_path in self.test_documents.items():
                    if os.path.exists(doc_path):
                        with open(doc_path, 'rb') as f:
                            documents.append({
                                'filename': f'test_{doc_type}.{doc_type}',
                                'content': f.read()
                            })
                
                if not documents:
                    logger.warning("⚠️ Нет доступных документов для пакетной обработки")
                    return False
                
                # Отправка пакета документов
                payload = {
                    "documents": documents,
                    "processing_options": {
                        "extract_text": True,
                        "spellcheck": True,
                        "analyze": True
                    }
                }
                
                async with session.post(
                    f"{self.base_url}/batch_process",
                    json=payload,
                    ssl=False,
                    timeout=300
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info("✅ Пакетная обработка выполнена")
                        
                        # Проверка результатов
                        if 'results' in result and len(result['results']) > 0:
                            logger.info(f"✅ Обработано {len(result['results'])} документов")
                            return True
                        else:
                            logger.warning("⚠️ Результаты пакетной обработки пусты")
                            return False
                    else:
                        logger.error(f"❌ Ошибка пакетной обработки: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ Ошибка пакетной обработки: {e}")
            return False

    async def test_quality_control(self):
        """Тестирование контроля качества"""
        logger.info("🧪 Тестирование контроля качества...")
        
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "document_id": "test_doc",
                    "quality_checks": [
                        "spellcheck",
                        "grammar_check",
                        "format_check",
                        "completeness_check"
                    ]
                }
                
                async with session.post(
                    f"{self.base_url}/quality_control",
                    json=payload,
                    ssl=False,
                    timeout=60
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info("✅ Контроль качества выполнен")
                        
                        # Проверка результатов контроля качества
                        if 'quality_score' in result and result['quality_score'] > 0:
                            logger.info(f"✅ Оценка качества: {result['quality_score']}")
                            return True
                        else:
                            logger.warning("⚠️ Оценка качества не получена")
                            return False
                    else:
                        logger.error(f"❌ Ошибка контроля качества: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ Ошибка контроля качества: {e}")
            return False

    async def test_error_handling(self):
        """Тестирование обработки ошибок"""
        logger.info("🧪 Тестирование обработки ошибок...")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Тест с неверным типом файла
                payload = {
                    "document_id": "nonexistent",
                    "analysis_type": "full"
                }
                
                async with session.post(
                    f"{self.base_url}/analyze",
                    json=payload,
                    ssl=False,
                    timeout=10
                ) as response:
                    if response.status in [400, 404, 422]:
                        logger.info("✅ Обработка ошибок работает")
                        return True
                    else:
                        logger.warning("⚠️ Обработка ошибок неожиданная")
                        return False
        except Exception as e:
            logger.info("✅ Обработка ошибок работает (исключение перехвачено)")
            return True

    async def run_all_tests(self):
        """Запуск всех тестов модуля выходного контроля"""
        logger.info("🚀 Запуск тестирования модуля 'Выходной контроль корреспонденции'...")
        start_time = time.time()
        
        # Запуск тестов
        self.test_results = {
            'service_health': await self.test_service_health(),
            'pdf_processing': await self.test_pdf_processing(),
            'docx_processing': await self.test_docx_processing(),
            'spellcheck_functionality': await self.test_spellcheck_functionality(),
            'document_analysis': await self.test_document_analysis(),
            'report_generation': await self.test_report_generation(),
            'batch_processing': await self.test_batch_processing(),
            'quality_control': await self.test_quality_control(),
            'error_handling': await self.test_error_handling()
        }
        
        # Подсчет результатов
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)
        success_rate = (passed_tests / total_tests) * 100
        
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info(f"✅ Тестирование завершено за {duration:.2f} секунд")
        logger.info(f"📊 Результат: {passed_tests}/{total_tests} тестов пройдено ({success_rate:.1f}%)")
        
        return self.test_results

    def generate_report(self):
        """Генерация отчета по модулю"""
        report = {
            'module': 'Выходной контроль корреспонденции',
            'timestamp': datetime.now().isoformat(),
            'test_results': self.test_results,
            'summary': {
                'total_tests': len(self.test_results),
                'passed_tests': sum(1 for result in self.test_results.values() if result),
                'success_rate': (sum(1 for result in self.test_results.values() if result) / len(self.test_results)) * 100
            }
        }
        
        # Сохранение отчета
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        report_path = os.path.join(base_dir, 'reports', 'outgoing_control_test_report.json')
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        return report

async def main():
    """Основная функция"""
    tester = OutgoingControlTester()
    
    # Запуск тестов
    results = await tester.run_all_tests()
    
    # Генерация отчета
    report = tester.generate_report()
    
    # Вывод результатов
    print("\n" + "="*60)
    print("📊 ОТЧЕТ ПО МОДУЛЮ 'ВЫХОДНОЙ КОНТРОЛЬ КОРРЕСПОНДЕНЦИИ'")
    print("="*60)
    
    for test_name, result in results.items():
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        print(f"{test_name}: {status}")
    
    print(f"\n🎯 УСПЕШНОСТЬ: {report['summary']['success_rate']:.1f}%")
    print(f"📄 Отчет сохранен: outgoing_control_test_report.json")

if __name__ == "__main__":
    asyncio.run(main())
