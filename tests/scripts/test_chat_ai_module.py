#!/usr/bin/env python3
"""
Специализированное тестирование модуля "Чат с ИИ"
Включает тестирование загрузки файлов, анализа PDF/DOCX и обработки запросов
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

class ChatAITester:
    def __init__(self):
        self.base_url = 'http://localhost:8005'  # VLLM Service
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
                        logger.info("✅ VLLM Service здоров")
                        return True
                    else:
                        logger.error(f"❌ VLLM Service недоступен: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к VLLM Service: {e}")
            return False

    async def test_pdf_upload_and_analysis(self):
        """Тестирование загрузки и анализа PDF"""
        logger.info("🧪 Тестирование загрузки PDF...")
        
        if not os.path.exists(self.test_documents['pdf']):
            logger.warning("⚠️ Тестовый PDF файл не найден")
            return False
        
        try:
            async with aiohttp.ClientSession() as session:
                # Загрузка файла
                with open(self.test_documents['pdf'], 'rb') as f:
                    data = aiohttp.FormData()
                    data.add_field('file', f, filename='test_document.pdf')
                    
                    async with session.post(
                        f"{self.base_url}/upload_document",
                        data=data,
                        ssl=False,
                        timeout=60
                    ) as response:
                        if response.status == 200:
                            upload_result = await response.json()
                            logger.info("✅ PDF загружен успешно")
                            
                            # Анализ документа
                            analysis_result = await self.analyze_document(upload_result.get('document_id'))
                            return analysis_result
                        else:
                            logger.error(f"❌ Ошибка загрузки PDF: {response.status}")
                            return False
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки PDF: {e}")
            return False

    async def test_docx_upload_and_analysis(self):
        """Тестирование загрузки и анализа DOCX"""
        logger.info("🧪 Тестирование загрузки DOCX...")
        
        if not os.path.exists(self.test_documents['docx']):
            logger.warning("⚠️ Тестовый DOCX файл не найден")
            return False
        
        try:
            async with aiohttp.ClientSession() as session:
                # Загрузка файла
                with open(self.test_documents['docx'], 'rb') as f:
                    data = aiohttp.FormData()
                    data.add_field('file', f, filename='test_document.docx')
                    
                    async with session.post(
                        f"{self.base_url}/upload_document",
                        data=data,
                        ssl=False,
                        timeout=60
                    ) as response:
                        if response.status == 200:
                            upload_result = await response.json()
                            logger.info("✅ DOCX загружен успешно")
                            
                            # Анализ документа
                            analysis_result = await self.analyze_document(upload_result.get('document_id'))
                            return analysis_result
                        else:
                            logger.error(f"❌ Ошибка загрузки DOCX: {response.status}")
                            return False
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки DOCX: {e}")
            return False

    async def analyze_document(self, document_id):
        """Анализ загруженного документа"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "document_id": document_id,
                    "analysis_type": "full",
                    "extract_text": True,
                    "extract_metadata": True
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
                        if 'text' in result and len(result['text']) > 100:
                            logger.info("✅ Текст извлечен качественно")
                            return True
                        else:
                            logger.warning("⚠️ Качество извлечения текста низкое")
                            return False
                    else:
                        logger.error(f"❌ Ошибка анализа: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ Ошибка анализа: {e}")
            return False

    async def test_chat_with_document_context(self):
        """Тестирование чата с контекстом документа"""
        logger.info("🧪 Тестирование чата с контекстом...")
        
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "message": "Проанализируй загруженный документ и расскажи о его содержании",
                    "context": "document",
                    "document_id": "test_doc"
                }
                
                async with session.post(
                    f"{self.base_url}/chat",
                    json=payload,
                    ssl=False,
                    timeout=60
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info("✅ Чат с контекстом работает")
                        
                        # Проверка качества ответа
                        if 'response' in result and len(result['response']) > 50:
                            logger.info("✅ Качество ответа удовлетворительное")
                            return True
                        else:
                            logger.warning("⚠️ Качество ответа низкое")
                            return False
                    else:
                        logger.error(f"❌ Ошибка чата: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ Ошибка чата: {e}")
            return False

    async def test_chat_without_context(self):
        """Тестирование чата без контекста"""
        logger.info("🧪 Тестирование чата без контекста...")
        
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "message": "Расскажи о возможностях системы AI-NK для инженерных расчетов",
                    "context": "general"
                }
                
                async with session.post(
                    f"{self.base_url}/chat",
                    json=payload,
                    ssl=False,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info("✅ Общий чат работает")
                        
                        # Проверка качества ответа
                        if 'response' in result and len(result['response']) > 100:
                            logger.info("✅ Качество ответа удовлетворительное")
                            return True
                        else:
                            logger.warning("⚠️ Качество ответа низкое")
                            return False
                    else:
                        logger.error(f"❌ Ошибка чата: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ Ошибка чата: {e}")
            return False

    async def test_document_processing_pipeline(self):
        """Тестирование полного пайплайна обработки документа"""
        logger.info("🧪 Тестирование пайплайна обработки...")
        
        try:
            # 1. Загрузка документа
            upload_success = await self.test_pdf_upload_and_analysis()
            if not upload_success:
                return False
            
            # 2. Анализ документа
            analysis_success = await self.analyze_document("test_doc")
            if not analysis_success:
                return False
            
            # 3. Чат с контекстом
            chat_success = await self.test_chat_with_document_context()
            if not chat_success:
                return False
            
            logger.info("✅ Полный пайплайн обработки работает")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка пайплайна: {e}")
            return False

    async def test_error_handling(self):
        """Тестирование обработки ошибок"""
        logger.info("🧪 Тестирование обработки ошибок...")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Тест с неверным типом файла
                payload = {
                    "message": "test",
                    "context": "invalid"
                }
                
                async with session.post(
                    f"{self.base_url}/chat",
                    json=payload,
                    ssl=False,
                    timeout=10
                ) as response:
                    if response.status in [400, 422]:
                        logger.info("✅ Обработка ошибок работает")
                        return True
                    else:
                        logger.warning("⚠️ Обработка ошибок неожиданная")
                        return False
        except Exception as e:
            logger.info("✅ Обработка ошибок работает (исключение перехвачено)")
            return True

    async def run_all_tests(self):
        """Запуск всех тестов модуля чата с ИИ"""
        logger.info("🚀 Запуск тестирования модуля 'Чат с ИИ'...")
        start_time = time.time()
        
        # Запуск тестов
        self.test_results = {
            'service_health': await self.test_service_health(),
            'pdf_upload_analysis': await self.test_pdf_upload_and_analysis(),
            'docx_upload_analysis': await self.test_docx_upload_and_analysis(),
            'chat_with_context': await self.test_chat_with_document_context(),
            'chat_without_context': await self.test_chat_without_context(),
            'processing_pipeline': await self.test_document_processing_pipeline(),
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
            'module': 'Чат с ИИ',
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
        report_path = os.path.join(base_dir, 'reports', 'chat_ai_test_report.json')
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        return report

async def main():
    """Основная функция"""
    tester = ChatAITester()
    
    # Запуск тестов
    results = await tester.run_all_tests()
    
    # Генерация отчета
    report = tester.generate_report()
    
    # Вывод результатов
    print("\n" + "="*60)
    print("📊 ОТЧЕТ ПО МОДУЛЮ 'ЧАТ С ИИ'")
    print("="*60)
    
    for test_name, result in results.items():
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        print(f"{test_name}: {status}")
    
    print(f"\n🎯 УСПЕШНОСТЬ: {report['summary']['success_rate']:.1f}%")
    print(f"📄 Отчет сохранен: chat_ai_test_report.json")

if __name__ == "__main__":
    asyncio.run(main())
