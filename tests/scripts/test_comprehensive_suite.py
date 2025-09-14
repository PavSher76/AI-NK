#!/usr/bin/env python3
"""
Комплексное тестирование функционала проекта AI-NK
Включает тестирование всех основных модулей системы
"""

import asyncio
import aiohttp
import json
import time
import os
import sys
from datetime import datetime
from pathlib import Path
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('comprehensive_test_report.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ComprehensiveTestSuite:
    def __init__(self):
        self.base_urls = {
            'gateway': 'https://localhost:8443',
            'frontend': 'https://localhost:443',
            'outgoing_control': 'http://localhost:8006',
            'rag_service': 'http://localhost:8003',
            'vllm_service': 'http://localhost:8005',
            'document_parser': 'http://localhost:8001',
            'spellchecker': 'http://localhost:8007',
            'calculation_service': 'http://localhost:8004',
            'rule_engine': 'http://localhost:8002'
        }
        
        self.test_results = {
            'chat_ai': {},
            'outgoing_control': {},
            'ntd_consultation': {},
            'normative_docs': {},
            'norm_control': {},
            'calculations': {},
            'overall_status': 'PENDING'
        }
        
        self.test_documents = {
            'pdf': 'TestDocs/for_check/СЗ_ТЕСТ.pdf',
            'docx': 'TestDocs/for_check/СЗ_ТЕСТ.docx',
            'gost_pdf': 'TestDocs/for_check/3401-21089-РД-01-220-221-АР_4_0_RU_IFC (1).pdf'
        }

    async def test_service_health(self, service_name, url):
        """Проверка здоровья сервиса"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{url}/health", ssl=False, timeout=10) as response:
                    if response.status == 200:
                        logger.info(f"✅ {service_name} - здоров")
                        return True
                    else:
                        logger.error(f"❌ {service_name} - статус {response.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ {service_name} - ошибка подключения: {e}")
            return False

    async def test_chat_ai_functionality(self):
        """Тестирование чата с ИИ и загрузки файлов"""
        logger.info("🧪 Тестирование чата с ИИ...")
        
        results = {
            'service_health': False,
            'file_upload_pdf': False,
            'file_upload_docx': False,
            'chat_response': False,
            'document_analysis': False
        }
        
        # Проверка здоровья сервиса
        results['service_health'] = await self.test_service_health(
            'VLLM Service', self.base_urls['vllm_service']
        )
        
        if results['service_health']:
            # Тест загрузки PDF
            if os.path.exists(self.test_documents['pdf']):
                results['file_upload_pdf'] = await self.test_file_upload(
                    'pdf', self.test_documents['pdf']
                )
            
            # Тест загрузки DOCX
            if os.path.exists(self.test_documents['docx']):
                results['file_upload_docx'] = await self.test_file_upload(
                    'docx', self.test_documents['docx']
                )
            
            # Тест чата
            results['chat_response'] = await self.test_chat_response()
            
            # Тест анализа документа
            results['document_analysis'] = await self.test_document_analysis()
        
        self.test_results['chat_ai'] = results
        return results

    async def test_file_upload(self, file_type, file_path):
        """Тестирование загрузки файла"""
        try:
            async with aiohttp.ClientSession() as session:
                with open(file_path, 'rb') as f:
                    data = aiohttp.FormData()
                    data.add_field('file', f, filename=f'test.{file_type}')
                    
                    async with session.post(
                        f"{self.base_urls['vllm_service']}/upload_document",
                        data=data,
                        ssl=False,
                        timeout=30
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            logger.info(f"✅ Загрузка {file_type.upper()} успешна")
                            return True
                        else:
                            logger.error(f"❌ Ошибка загрузки {file_type.upper()}: {response.status}")
                            return False
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки {file_type.upper()}: {e}")
            return False

    async def test_chat_response(self):
        """Тестирование ответа чата"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "message": "Привет! Расскажи о возможностях системы AI-NK",
                    "context": "test"
                }
                
                async with session.post(
                    f"{self.base_urls['vllm_service']}/chat",
                    json=payload,
                    ssl=False,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info("✅ Ответ чата получен")
                        return True
                    else:
                        logger.error(f"❌ Ошибка чата: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ Ошибка чата: {e}")
            return False

    async def test_document_analysis(self):
        """Тестирование анализа документа"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "document_id": "test_doc",
                    "analysis_type": "full"
                }
                
                async with session.post(
                    f"{self.base_urls['vllm_service']}/analyze",
                    json=payload,
                    ssl=False,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info("✅ Анализ документа выполнен")
                        return True
                    else:
                        logger.error(f"❌ Ошибка анализа: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ Ошибка анализа: {e}")
            return False

    async def test_outgoing_control_functionality(self):
        """Тестирование выходного контроля корреспонденции"""
        logger.info("🧪 Тестирование выходного контроля...")
        
        results = {
            'service_health': False,
            'pdf_processing': False,
            'docx_processing': False,
            'spellcheck': False,
            'report_generation': False
        }
        
        # Проверка здоровья сервиса
        results['service_health'] = await self.test_service_health(
            'Outgoing Control Service', self.base_urls['outgoing_control']
        )
        
        if results['service_health']:
            # Тест обработки PDF
            if os.path.exists(self.test_documents['pdf']):
                results['pdf_processing'] = await self.test_outgoing_control_processing(
                    'pdf', self.test_documents['pdf']
                )
            
            # Тест обработки DOCX
            if os.path.exists(self.test_documents['docx']):
                results['docx_processing'] = await self.test_outgoing_control_processing(
                    'docx', self.test_documents['docx']
                )
            
            # Тест проверки орфографии
            results['spellcheck'] = await self.test_spellcheck()
            
            # Тест генерации отчета
            results['report_generation'] = await self.test_report_generation()
        
        self.test_results['outgoing_control'] = results
        return results

    async def test_outgoing_control_processing(self, file_type, file_path):
        """Тестирование обработки документа в выходном контроле"""
        try:
            async with aiohttp.ClientSession() as session:
                with open(file_path, 'rb') as f:
                    data = aiohttp.FormData()
                    data.add_field('file', f, filename=f'test.{file_type}')
                    
                    async with session.post(
                        f"{self.base_urls['outgoing_control']}/process",
                        data=data,
                        ssl=False,
                        timeout=60
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            logger.info(f"✅ Обработка {file_type.upper()} в выходном контроле успешна")
                            return True
                        else:
                            logger.error(f"❌ Ошибка обработки {file_type.upper()}: {response.status}")
                            return False
        except Exception as e:
            logger.error(f"❌ Ошибка обработки {file_type.upper()}: {e}")
            return False

    async def test_spellcheck(self):
        """Тестирование проверки орфографии"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "text": "Это тестовый текст для проверки орфографии и грамматики.",
                    "language": "ru"
                }
                
                async with session.post(
                    f"{self.base_urls['spellchecker']}/check",
                    json=payload,
                    ssl=False,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info("✅ Проверка орфографии выполнена")
                        return True
                    else:
                        logger.error(f"❌ Ошибка проверки орфографии: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ Ошибка проверки орфографии: {e}")
            return False

    async def test_report_generation(self):
        """Тестирование генерации отчета"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "document_id": "test_doc",
                    "report_type": "outgoing_control"
                }
                
                async with session.post(
                    f"{self.base_urls['outgoing_control']}/generate_report",
                    json=payload,
                    ssl=False,
                    timeout=60
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info("✅ Генерация отчета выполнена")
                        return True
                    else:
                        logger.error(f"❌ Ошибка генерации отчета: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ Ошибка генерации отчета: {e}")
            return False

    async def test_ntd_consultation_functionality(self):
        """Тестирование консультации НТД"""
        logger.info("🧪 Тестирование консультации НТД...")
        
        results = {
            'service_health': False,
            'search_functionality': False,
            'llm_processing': False,
            'document_references': False,
            'response_quality': False
        }
        
        # Проверка здоровья сервиса
        results['service_health'] = await self.test_service_health(
            'RAG Service', self.base_urls['rag_service']
        )
        
        if results['service_health']:
            # Тест поиска
            results['search_functionality'] = await self.test_ntd_search()
            
            # Тест обработки LLM
            results['llm_processing'] = await self.test_ntd_llm_processing()
            
            # Тест ссылок на документы
            results['document_references'] = await self.test_document_references()
            
            # Тест качества ответа
            results['response_quality'] = await self.test_response_quality()
        
        self.test_results['ntd_consultation'] = results
        return results

    async def test_ntd_search(self):
        """Тестирование поиска в НТД"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "query": "требования к качеству сварных швов",
                    "limit": 10
                }
                
                async with session.post(
                    f"{self.base_urls['rag_service']}/search",
                    json=payload,
                    ssl=False,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info("✅ Поиск в НТД выполнен")
                        return True
                    else:
                        logger.error(f"❌ Ошибка поиска: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ Ошибка поиска: {e}")
            return False

    async def test_ntd_llm_processing(self):
        """Тестирование обработки LLM"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "query": "Какие требования к качеству сварных швов?",
                    "context": "ntd"
                }
                
                async with session.post(
                    f"{self.base_urls['rag_service']}/ask",
                    json=payload,
                    ssl=False,
                    timeout=60
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info("✅ Обработка LLM выполнена")
                        return True
                    else:
                        logger.error(f"❌ Ошибка LLM: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ Ошибка LLM: {e}")
            return False

    async def test_document_references(self):
        """Тестирование ссылок на документы"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "query": "ГОСТ 14771",
                    "include_references": True
                }
                
                async with session.post(
                    f"{self.base_urls['rag_service']}/ask",
                    json=payload,
                    ssl=False,
                    timeout=60
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        if 'references' in result and result['references']:
                            logger.info("✅ Ссылки на документы получены")
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
        """Тестирование качества ответа"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "query": "Объясни требования к сварным соединениям",
                    "quality_check": True
                }
                
                async with session.post(
                    f"{self.base_urls['rag_service']}/ask",
                    json=payload,
                    ssl=False,
                    timeout=60
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        # Проверка качества ответа
                        if 'answer' in result and len(result['answer']) > 100:
                            logger.info("✅ Качество ответа удовлетворительное")
                            return True
                        else:
                            logger.warning("⚠️ Качество ответа низкое")
                            return False
                    else:
                        logger.error(f"❌ Ошибка проверки качества: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ Ошибка проверки качества: {e}")
            return False

    async def test_normative_docs_functionality(self):
        """Тестирование нормативных документов"""
        logger.info("🧪 Тестирование нормативных документов...")
        
        results = {
            'service_health': False,
            'document_upload': False,
            'document_search': False,
            'document_retrieval': False,
            'metadata_extraction': False
        }
        
        # Проверка здоровья сервиса
        results['service_health'] = await self.test_service_health(
            'Document Parser', self.base_urls['document_parser']
        )
        
        if results['service_health']:
            # Тест загрузки документа
            results['document_upload'] = await self.test_document_upload()
            
            # Тест поиска документа
            results['document_search'] = await self.test_document_search()
            
            # Тест получения документа
            results['document_retrieval'] = await self.test_document_retrieval()
            
            # Тест извлечения метаданных
            results['metadata_extraction'] = await self.test_metadata_extraction()
        
        self.test_results['normative_docs'] = results
        return results

    async def test_document_upload(self):
        """Тестирование загрузки документа"""
        try:
            async with aiohttp.ClientSession() as session:
                with open(self.test_documents['pdf'], 'rb') as f:
                    data = aiohttp.FormData()
                    data.add_field('file', f, filename='test_normative.pdf')
                    
                    async with session.post(
                        f"{self.base_urls['document_parser']}/upload/checkable",
                        data=data,
                        ssl=False,
                        timeout=60
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            logger.info("✅ Загрузка нормативного документа успешна")
                            return True
                        else:
                            logger.error(f"❌ Ошибка загрузки: {response.status}")
                            return False
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки: {e}")
            return False

    async def test_document_search(self):
        """Тестирование поиска документа"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "query": "ГОСТ",
                    "document_type": "normative"
                }
                
                async with session.post(
                    f"{self.base_urls['document_parser']}/search",
                    json=payload,
                    ssl=False,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info("✅ Поиск нормативных документов выполнен")
                        return True
                    else:
                        logger.error(f"❌ Ошибка поиска: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ Ошибка поиска: {e}")
            return False

    async def test_document_retrieval(self):
        """Тестирование получения документа"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_urls['document_parser']}/document/test_doc",
                    ssl=False,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info("✅ Получение документа выполнено")
                        return True
                    else:
                        logger.error(f"❌ Ошибка получения: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ Ошибка получения: {e}")
            return False

    async def test_metadata_extraction(self):
        """Тестирование извлечения метаданных"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "document_id": "test_doc",
                    "extract_metadata": True
                }
                
                async with session.post(
                    f"{self.base_urls['document_parser']}/extract_metadata",
                    json=payload,
                    ssl=False,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info("✅ Извлечение метаданных выполнено")
                        return True
                    else:
                        logger.error(f"❌ Ошибка извлечения: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ Ошибка извлечения: {e}")
            return False

    async def test_norm_control_functionality(self):
        """Тестирование нормоконтроля"""
        logger.info("🧪 Тестирование нормоконтроля...")
        
        results = {
            'service_health': False,
            'rule_engine': False,
            'validation': False,
            'compliance_check': False,
            'report_generation': False
        }
        
        # Проверка здоровья сервиса
        results['service_health'] = await self.test_service_health(
            'Rule Engine', self.base_urls['rule_engine']
        )
        
        if results['service_health']:
            # Тест движка правил
            results['rule_engine'] = await self.test_rule_engine()
            
            # Тест валидации
            results['validation'] = await self.test_validation()
            
            # Тест проверки соответствия
            results['compliance_check'] = await self.test_compliance_check()
            
            # Тест генерации отчета
            results['report_generation'] = await self.test_norm_control_report()
        
        self.test_results['norm_control'] = results
        return results

    async def test_rule_engine(self):
        """Тестирование движка правил"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "document_type": "technical_drawing",
                    "rules": ["dimension_check", "symbol_check"]
                }
                
                async with session.post(
                    f"{self.base_urls['rule_engine']}/validate",
                    json=payload,
                    ssl=False,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info("✅ Движок правил работает")
                        return True
                    else:
                        logger.error(f"❌ Ошибка движка правил: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ Ошибка движка правил: {e}")
            return False

    async def test_validation(self):
        """Тестирование валидации"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "document_data": {
                        "type": "drawing",
                        "dimensions": [100, 200, 50],
                        "tolerance": 0.1
                    }
                }
                
                async with session.post(
                    f"{self.base_urls['rule_engine']}/validate_document",
                    json=payload,
                    ssl=False,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info("✅ Валидация выполнена")
                        return True
                    else:
                        logger.error(f"❌ Ошибка валидации: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ Ошибка валидации: {e}")
            return False

    async def test_compliance_check(self):
        """Тестирование проверки соответствия"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "standard": "ГОСТ 2.307-68",
                    "document_data": {"type": "drawing"}
                }
                
                async with session.post(
                    f"{self.base_urls['rule_engine']}/compliance_check",
                    json=payload,
                    ssl=False,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info("✅ Проверка соответствия выполнена")
                        return True
                    else:
                        logger.error(f"❌ Ошибка проверки соответствия: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ Ошибка проверки соответствия: {e}")
            return False

    async def test_norm_control_report(self):
        """Тестирование генерации отчета нормоконтроля"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "document_id": "test_doc",
                    "report_type": "norm_control"
                }
                
                async with session.post(
                    f"{self.base_urls['rule_engine']}/generate_report",
                    json=payload,
                    ssl=False,
                    timeout=60
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info("✅ Отчет нормоконтроля сгенерирован")
                        return True
                    else:
                        logger.error(f"❌ Ошибка генерации отчета: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ Ошибка генерации отчета: {e}")
            return False

    async def test_calculations_functionality(self):
        """Тестирование расчетов"""
        logger.info("🧪 Тестирование расчетов...")
        
        results = {
            'service_health': False,
            'api_calculations': False,
            'frontend_calculations': False,
            'calculation_types': {},
            'accuracy_tests': False
        }
        
        # Проверка здоровья сервиса
        results['service_health'] = await self.test_service_health(
            'Calculation Service', self.base_urls['calculation_service']
        )
        
        if results['service_health']:
            # Тест различных типов расчетов
            calculation_types = [
                'welding_strength',
                'material_properties',
                'safety_factors',
                'dimension_tolerances'
            ]
            
            for calc_type in calculation_types:
                results['calculation_types'][calc_type] = await self.test_calculation_type(calc_type)
            
            # Тест API расчетов
            results['api_calculations'] = await self.test_api_calculations()
            
            # Тест фронтенд расчетов
            results['frontend_calculations'] = await self.test_frontend_calculations()
            
            # Тест точности расчетов
            results['accuracy_tests'] = await self.test_calculation_accuracy()
        
        self.test_results['calculations'] = results
        return results

    async def test_calculation_type(self, calc_type):
        """Тестирование конкретного типа расчета"""
        try:
            async with aiohttp.ClientSession() as session:
                # Тестовые данные для разных типов расчетов
                test_data = {
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
                    },
                    'dimension_tolerances': {
                        'nominal': 100,
                        'tolerance_class': 'H7',
                        'measurement': 100.05
                    }
                }
                
                payload = {
                    'calculation_type': calc_type,
                    'parameters': test_data[calc_type]
                }
                
                async with session.post(
                    f"{self.base_urls['calculation_service']}/calculate",
                    json=payload,
                    ssl=False,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"✅ Расчет {calc_type} выполнен")
                        return True
                    else:
                        logger.error(f"❌ Ошибка расчета {calc_type}: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ Ошибка расчета {calc_type}: {e}")
            return False

    async def test_api_calculations(self):
        """Тестирование API расчетов"""
        try:
            async with aiohttp.ClientSession() as session:
                # Комплексный тест расчетов
                payload = {
                    'calculations': [
                        {
                            'type': 'welding_strength',
                            'parameters': {'material': 'steel', 'thickness': 10, 'load': 1000}
                        },
                        {
                            'type': 'safety_factors',
                            'parameters': {'load': 1000, 'safety_factor': 2.5}
                        }
                    ]
                }
                
                async with session.post(
                    f"{self.base_urls['calculation_service']}/batch_calculate",
                    json=payload,
                    ssl=False,
                    timeout=60
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info("✅ API расчеты выполнены")
                        return True
                    else:
                        logger.error(f"❌ Ошибка API расчетов: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ Ошибка API расчетов: {e}")
            return False

    async def test_frontend_calculations(self):
        """Тестирование фронтенд расчетов"""
        try:
            async with aiohttp.ClientSession() as session:
                # Тест фронтенд интерфейса
                async with session.get(
                    f"{self.base_urls['frontend']}/calculations",
                    ssl=False,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        logger.info("✅ Фронтенд расчетов доступен")
                        return True
                    else:
                        logger.error(f"❌ Ошибка фронтенда: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ Ошибка фронтенда: {e}")
            return False

    async def test_calculation_accuracy(self):
        """Тестирование точности расчетов"""
        try:
            async with aiohttp.ClientSession() as session:
                # Тест с известными результатами
                payload = {
                    'calculation_type': 'welding_strength',
                    'parameters': {
                        'material': 'steel',
                        'thickness': 10,
                        'weld_type': 'butt',
                        'load': 1000
                    },
                    'expected_result': 100  # Ожидаемый результат
                }
                
                async with session.post(
                    f"{self.base_urls['calculation_service']}/calculate",
                    json=payload,
                    ssl=False,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        # Проверка точности (допустимая погрешность 5%)
                        if 'result' in result:
                            calculated = result['result']
                            expected = payload['parameters']['load'] / 10  # Упрощенная формула
                            accuracy = abs(calculated - expected) / expected
                            if accuracy < 0.05:  # 5% погрешность
                                logger.info("✅ Точность расчетов удовлетворительная")
                                return True
                            else:
                                logger.warning(f"⚠️ Низкая точность расчетов: {accuracy:.2%}")
                                return False
                        else:
                            logger.error("❌ Результат расчета не получен")
                            return False
                    else:
                        logger.error(f"❌ Ошибка проверки точности: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ Ошибка проверки точности: {e}")
            return False

    async def run_all_tests(self):
        """Запуск всех тестов"""
        logger.info("🚀 Запуск комплексного тестирования AI-NK...")
        start_time = time.time()
        
        # Запуск тестов по модулям
        await self.test_chat_ai_functionality()
        await self.test_outgoing_control_functionality()
        await self.test_ntd_consultation_functionality()
        await self.test_normative_docs_functionality()
        await self.test_norm_control_functionality()
        await self.test_calculations_functionality()
        
        # Подсчет общего статуса
        total_tests = 0
        passed_tests = 0
        
        for module, results in self.test_results.items():
            if module != 'overall_status':
                for test_name, result in results.items():
                    total_tests += 1
                    if result:
                        passed_tests += 1
        
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        if success_rate >= 80:
            self.test_results['overall_status'] = 'PASSED'
        elif success_rate >= 60:
            self.test_results['overall_status'] = 'PARTIAL'
        else:
            self.test_results['overall_status'] = 'FAILED'
        
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info(f"✅ Тестирование завершено за {duration:.2f} секунд")
        logger.info(f"📊 Результат: {passed_tests}/{total_tests} тестов пройдено ({success_rate:.1f}%)")
        
        return self.test_results

    def generate_comprehensive_report(self):
        """Генерация комплексного отчета"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'test_results': self.test_results,
            'summary': self._generate_summary()
        }
        
        # Сохранение отчета
        with open('comprehensive_test_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        # Генерация HTML отчета
        self._generate_html_report(report)
        
        return report

    def _generate_summary(self):
        """Генерация сводки результатов"""
        summary = {
            'total_modules': 6,
            'modules_tested': 0,
            'overall_status': self.test_results['overall_status'],
            'module_status': {}
        }
        
        for module, results in self.test_results.items():
            if module != 'overall_status':
                module_tests = sum(1 for result in results.values() if isinstance(result, bool))
                module_passed = sum(1 for result in results.values() if result is True)
                module_success_rate = (module_passed / module_tests) * 100 if module_tests > 0 else 0
                
                summary['module_status'][module] = {
                    'tests_total': module_tests,
                    'tests_passed': module_passed,
                    'success_rate': module_success_rate,
                    'status': 'PASSED' if module_success_rate >= 80 else 'FAILED'
                }
                
                if module_tests > 0:
                    summary['modules_tested'] += 1
        
        return summary

    def _generate_html_report(self, report):
        """Генерация HTML отчета"""
        html_content = f"""
        <!DOCTYPE html>
        <html lang="ru">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Отчет о тестировании AI-NK</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #2c3e50; color: white; padding: 20px; border-radius: 5px; }}
                .module {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
                .passed {{ background-color: #d4edda; border-color: #c3e6cb; }}
                .failed {{ background-color: #f8d7da; border-color: #f5c6cb; }}
                .test {{ margin: 10px 0; padding: 10px; background-color: #f8f9fa; border-radius: 3px; }}
                .status {{ font-weight: bold; }}
                .passed-status {{ color: #28a745; }}
                .failed-status {{ color: #dc3545; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Отчет о комплексном тестировании AI-NK</h1>
                <p>Время тестирования: {report['timestamp']}</p>
                <p>Общий статус: <span class="status {'passed-status' if report['test_results']['overall_status'] == 'PASSED' else 'failed-status'}">{report['test_results']['overall_status']}</span></p>
            </div>
        """
        
        for module, results in report['test_results'].items():
            if module != 'overall_status':
                module_class = 'passed' if report['summary']['module_status'][module]['status'] == 'PASSED' else 'failed'
                html_content += f"""
                <div class="module {module_class}">
                    <h2>{module.replace('_', ' ').title()}</h2>
                    <p>Статус: <span class="status {'passed-status' if report['summary']['module_status'][module]['status'] == 'PASSED' else 'failed-status'}">{report['summary']['module_status'][module]['status']}</span></p>
                    <p>Успешность: {report['summary']['module_status'][module]['success_rate']:.1f}%</p>
                """
                
                for test_name, result in results.items():
                    if isinstance(result, bool):
                        test_class = 'passed-status' if result else 'failed-status'
                        html_content += f"""
                        <div class="test">
                            <span class="status {test_class}">{'✅' if result else '❌'}</span> {test_name}
                        </div>
                        """
                
                html_content += "</div>"
        
        html_content += """
        </body>
        </html>
        """
        
        with open('comprehensive_test_report.html', 'w', encoding='utf-8') as f:
            f.write(html_content)

async def main():
    """Основная функция"""
    test_suite = ComprehensiveTestSuite()
    
    # Запуск тестов
    results = await test_suite.run_all_tests()
    
    # Генерация отчета
    report = test_suite.generate_comprehensive_report()
    
    # Вывод результатов
    print("\n" + "="*80)
    print("📊 КОМПЛЕКСНЫЙ ОТЧЕТ О ТЕСТИРОВАНИИ AI-NK")
    print("="*80)
    
    for module, results in test_suite.test_results.items():
        if module != 'overall_status':
            print(f"\n🔧 {module.replace('_', ' ').upper()}:")
            for test_name, result in results.items():
                status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
                print(f"  {test_name}: {status}")
    
    print(f"\n🎯 ОБЩИЙ СТАТУС: {test_suite.test_results['overall_status']}")
    print(f"📈 УСПЕШНОСТЬ: {report['summary']['modules_tested']}/{report['summary']['total_modules']} модулей")
    
    print("\n📄 Отчеты сохранены:")
    print("  - comprehensive_test_report.json")
    print("  - comprehensive_test_report.html")
    print("  - comprehensive_test_report.log")

if __name__ == "__main__":
    asyncio.run(main())
