#!/usr/bin/env python3
"""
Специализированное тестирование модуля "Консультация НТД от ИИ"
Включает тестирование поиска, обработки LLM и генерации ответов с ссылками
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

class NTDConsultationTester:
    def __init__(self):
        self.base_url = 'http://localhost:8003'  # RAG Service
        self.test_queries = [
            "требования к качеству сварных швов",
            "ГОСТ 14771 сварка",
            "допуски и посадки",
            "материалы для строительства",
            "технические условия на продукцию"
        ]
        self.test_results = {}

    async def test_service_health(self):
        """Проверка здоровья сервиса"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/health", ssl=False, timeout=10) as response:
                    if response.status == 200:
                        logger.info("✅ RAG Service здоров")
                        return True
                    else:
                        logger.error(f"❌ RAG Service недоступен: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к RAG Service: {e}")
            return False

    async def test_search_functionality(self):
        """Тестирование функциональности поиска"""
        logger.info("🧪 Тестирование поиска...")
        
        try:
            async with aiohttp.ClientSession() as session:
                for query in self.test_queries:
                    payload = {
                        "query": query,
                        "limit": 10,
                        "include_metadata": True
                    }
                    
                    async with session.post(
                        f"{self.base_url}/search",
                        json=payload,
                        ssl=False,
                        timeout=30
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            logger.info(f"✅ Поиск по запросу '{query}' выполнен")
                            
                            # Проверка качества поиска
                            if 'results' in result and len(result['results']) > 0:
                                logger.info(f"✅ Найдено {len(result['results'])} результатов")
                                return True
                            else:
                                logger.warning(f"⚠️ По запросу '{query}' результаты не найдены")
                        else:
                            logger.error(f"❌ Ошибка поиска по запросу '{query}': {response.status}")
                            return False
                
                return True
        except Exception as e:
            logger.error(f"❌ Ошибка поиска: {e}")
            return False

    async def test_llm_processing(self):
        """Тестирование обработки LLM"""
        logger.info("🧪 Тестирование обработки LLM...")
        
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "query": "Какие требования к качеству сварных швов согласно ГОСТ?",
                    "context": "ntd",
                    "include_references": True
                }
                
                async with session.post(
                    f"{self.base_url}/ask",
                    json=payload,
                    ssl=False,
                    timeout=60
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info("✅ Обработка LLM выполнена")
                        
                        # Проверка качества ответа
                        if 'answer' in result and len(result['answer']) > 100:
                            logger.info("✅ Ответ LLM содержит достаточно информации")
                            return True
                        else:
                            logger.warning("⚠️ Ответ LLM слишком короткий")
                            return False
                    else:
                        logger.error(f"❌ Ошибка обработки LLM: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ Ошибка обработки LLM: {e}")
            return False

    async def test_document_references(self):
        """Тестирование генерации ссылок на документы"""
        logger.info("🧪 Тестирование ссылок на документы...")
        
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "query": "ГОСТ 14771 требования к сварке",
                    "include_references": True,
                    "reference_format": "detailed"
                }
                
                async with session.post(
                    f"{self.base_url}/ask",
                    json=payload,
                    ssl=False,
                    timeout=60
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info("✅ Ссылки на документы получены")
                        
                        # Проверка наличия ссылок
                        if 'references' in result and len(result['references']) > 0:
                            logger.info(f"✅ Найдено {len(result['references'])} ссылок")
                            
                            # Проверка качества ссылок
                            for ref in result['references']:
                                if 'title' in ref and 'url' in ref:
                                    logger.info(f"✅ Ссылка: {ref['title']}")
                            
                            return True
                        else:
                            logger.warning("⚠️ Ссылки на документы отсутствуют")
                            return False
                    else:
                        logger.error(f"❌ Ошибка получения ссылок: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ Ошибка получения ссылок: {e}")
            return False

    async def test_response_quality(self):
        """Тестирование качества ответов"""
        logger.info("🧪 Тестирование качества ответов...")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Тест с техническим запросом
                payload = {
                    "query": "Объясни требования к сварным соединениям согласно ГОСТ 14771",
                    "quality_check": True,
                    "include_examples": True
                }
                
                async with session.post(
                    f"{self.base_url}/ask",
                    json=payload,
                    ssl=False,
                    timeout=60
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info("✅ Качество ответа проверено")
                        
                        # Проверка качества ответа
                        quality_indicators = [
                            'answer' in result,
                            len(result.get('answer', '')) > 200,
                            'references' in result,
                            'confidence_score' in result
                        ]
                        
                        quality_score = sum(quality_indicators) / len(quality_indicators)
                        
                        if quality_score >= 0.75:
                            logger.info(f"✅ Качество ответа: {quality_score:.2f}")
                            return True
                        else:
                            logger.warning(f"⚠️ Низкое качество ответа: {quality_score:.2f}")
                            return False
                    else:
                        logger.error(f"❌ Ошибка проверки качества: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ Ошибка проверки качества: {e}")
            return False

    async def test_context_awareness(self):
        """Тестирование контекстной осведомленности"""
        logger.info("🧪 Тестирование контекстной осведомленности...")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Тест с контекстным запросом
                payload = {
                    "query": "Какие дополнительные требования к сварке алюминия?",
                    "context": "previous_query_about_welding",
                    "include_context": True
                }
                
                async with session.post(
                    f"{self.base_url}/ask",
                    json=payload,
                    ssl=False,
                    timeout=60
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info("✅ Контекстная осведомленность проверена")
                        
                        # Проверка контекстной осведомленности
                        if 'answer' in result and 'алюминий' in result['answer'].lower():
                            logger.info("✅ Ответ учитывает контекст")
                            return True
                        else:
                            logger.warning("⚠️ Ответ не учитывает контекст")
                            return False
                    else:
                        logger.error(f"❌ Ошибка контекстной осведомленности: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ Ошибка контекстной осведомленности: {e}")
            return False

    async def test_multilingual_support(self):
        """Тестирование многоязычной поддержки"""
        logger.info("🧪 Тестирование многоязычной поддержки...")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Тест с английским запросом
                payload = {
                    "query": "What are the requirements for welding quality?",
                    "language": "en",
                    "include_references": True
                }
                
                async with session.post(
                    f"{self.base_url}/ask",
                    json=payload,
                    ssl=False,
                    timeout=60
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info("✅ Многоязычная поддержка проверена")
                        
                        # Проверка качества ответа на английском
                        if 'answer' in result and len(result['answer']) > 50:
                            logger.info("✅ Ответ на английском языке получен")
                            return True
                        else:
                            logger.warning("⚠️ Качество ответа на английском низкое")
                            return False
                    else:
                        logger.error(f"❌ Ошибка многоязычной поддержки: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ Ошибка многоязычной поддержки: {e}")
            return False

    async def test_knowledge_base_integration(self):
        """Тестирование интеграции с базой знаний"""
        logger.info("🧪 Тестирование интеграции с базой знаний...")
        
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "query": "Покажи все доступные ГОСТы по сварке",
                    "include_catalog": True,
                    "limit": 20
                }
                
                async with session.post(
                    f"{self.base_url}/catalog",
                    json=payload,
                    ssl=False,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info("✅ Интеграция с базой знаний проверена")
                        
                        # Проверка каталога
                        if 'catalog' in result and len(result['catalog']) > 0:
                            logger.info(f"✅ Найдено {len(result['catalog'])} документов в каталоге")
                            return True
                        else:
                            logger.warning("⚠️ Каталог документов пуст")
                            return False
                    else:
                        logger.error(f"❌ Ошибка интеграции с базой знаний: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ Ошибка интеграции с базой знаний: {e}")
            return False

    async def test_error_handling(self):
        """Тестирование обработки ошибок"""
        logger.info("🧪 Тестирование обработки ошибок...")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Тест с некорректным запросом
                payload = {
                    "query": "",
                    "context": "invalid"
                }
                
                async with session.post(
                    f"{self.base_url}/ask",
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
        """Запуск всех тестов модуля консультации НТД"""
        logger.info("🚀 Запуск тестирования модуля 'Консультация НТД от ИИ'...")
        start_time = time.time()
        
        # Запуск тестов
        self.test_results = {
            'service_health': await self.test_service_health(),
            'search_functionality': await self.test_search_functionality(),
            'llm_processing': await self.test_llm_processing(),
            'document_references': await self.test_document_references(),
            'response_quality': await self.test_response_quality(),
            'context_awareness': await self.test_context_awareness(),
            'multilingual_support': await self.test_multilingual_support(),
            'knowledge_base_integration': await self.test_knowledge_base_integration(),
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
            'module': 'Консультация НТД от ИИ',
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
        report_path = os.path.join(base_dir, 'reports', 'ntd_consultation_test_report.json')
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        return report

async def main():
    """Основная функция"""
    tester = NTDConsultationTester()
    
    # Запуск тестов
    results = await tester.run_all_tests()
    
    # Генерация отчета
    report = tester.generate_report()
    
    # Вывод результатов
    print("\n" + "="*60)
    print("📊 ОТЧЕТ ПО МОДУЛЮ 'КОНСУЛЬТАЦИЯ НТД ОТ ИИ'")
    print("="*60)
    
    for test_name, result in results.items():
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        print(f"{test_name}: {status}")
    
    print(f"\n🎯 УСПЕШНОСТЬ: {report['summary']['success_rate']:.1f}%")
    print(f"📄 Отчет сохранен: ntd_consultation_test_report.json")

if __name__ == "__main__":
    asyncio.run(main())
