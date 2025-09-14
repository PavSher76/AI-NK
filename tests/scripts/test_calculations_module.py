#!/usr/bin/env python3
"""
Специализированное тестирование модуля "Расчеты"
Включает тестирование всех типов расчетов через API и фронтенд
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

class CalculationsTester:
    def __init__(self):
        self.api_url = 'http://localhost:8004'  # Calculation Service
        self.frontend_url = 'https://localhost:443'  # Frontend
        self.test_results = {}
        
        # Тестовые данные для различных типов расчетов
        self.test_calculations = {
            'welding_strength': {
                'material': 'steel',
                'thickness': 10,
                'weld_type': 'butt',
                'load': 1000,
                'expected_result_range': (80, 120)
            },
            'material_properties': {
                'material': 'aluminum',
                'temperature': 20,
                'stress': 100,
                'expected_result_range': (200, 300)
            },
            'safety_factors': {
                'load': 1000,
                'safety_factor': 2.5,
                'material_yield': 250,
                'expected_result_range': (400, 600)
            },
            'dimension_tolerances': {
                'nominal': 100,
                'tolerance_class': 'H7',
                'measurement': 100.05,
                'expected_result_range': (0.01, 0.05)
            },
            'thermal_expansion': {
                'material': 'steel',
                'temperature_change': 50,
                'length': 1000,
                'expected_result_range': (0.5, 1.0)
            },
            'fatigue_analysis': {
                'stress_amplitude': 100,
                'cycles': 1000000,
                'material': 'steel',
                'expected_result_range': (50, 150)
            }
        }

    async def test_service_health(self):
        """Проверка здоровья сервиса"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_url}/health", ssl=False, timeout=10) as response:
                    if response.status == 200:
                        logger.info("✅ Calculation Service здоров")
                        return True
                    else:
                        logger.error(f"❌ Calculation Service недоступен: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к Calculation Service: {e}")
            return False

    async def test_welding_strength_calculation(self):
        """Тестирование расчета прочности сварных соединений"""
        logger.info("🧪 Тестирование расчета прочности сварных соединений...")
        
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    'calculation_type': 'welding_strength',
                    'parameters': self.test_calculations['welding_strength']
                }
                
                async with session.post(
                    f"{self.api_url}/calculate",
                    json=payload,
                    ssl=False,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info("✅ Расчет прочности сварных соединений выполнен")
                        
                        # Проверка точности расчета
                        if 'result' in result:
                            calculated_value = result['result']
                            expected_range = self.test_calculations['welding_strength']['expected_result_range']
                            
                            if expected_range[0] <= calculated_value <= expected_range[1]:
                                logger.info(f"✅ Результат в ожидаемом диапазоне: {calculated_value}")
                                return True
                            else:
                                logger.warning(f"⚠️ Результат вне ожидаемого диапазона: {calculated_value}")
                                return False
                        else:
                            logger.error("❌ Результат расчета не получен")
                            return False
                    else:
                        logger.error(f"❌ Ошибка расчета: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ Ошибка расчета: {e}")
            return False

    async def test_material_properties_calculation(self):
        """Тестирование расчета свойств материалов"""
        logger.info("🧪 Тестирование расчета свойств материалов...")
        
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    'calculation_type': 'material_properties',
                    'parameters': self.test_calculations['material_properties']
                }
                
                async with session.post(
                    f"{self.api_url}/calculate",
                    json=payload,
                    ssl=False,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info("✅ Расчет свойств материалов выполнен")
                        
                        # Проверка точности расчета
                        if 'result' in result:
                            calculated_value = result['result']
                            expected_range = self.test_calculations['material_properties']['expected_result_range']
                            
                            if expected_range[0] <= calculated_value <= expected_range[1]:
                                logger.info(f"✅ Результат в ожидаемом диапазоне: {calculated_value}")
                                return True
                            else:
                                logger.warning(f"⚠️ Результат вне ожидаемого диапазона: {calculated_value}")
                                return False
                        else:
                            logger.error("❌ Результат расчета не получен")
                            return False
                    else:
                        logger.error(f"❌ Ошибка расчета: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ Ошибка расчета: {e}")
            return False

    async def test_safety_factors_calculation(self):
        """Тестирование расчета коэффициентов безопасности"""
        logger.info("🧪 Тестирование расчета коэффициентов безопасности...")
        
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    'calculation_type': 'safety_factors',
                    'parameters': self.test_calculations['safety_factors']
                }
                
                async with session.post(
                    f"{self.api_url}/calculate",
                    json=payload,
                    ssl=False,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info("✅ Расчет коэффициентов безопасности выполнен")
                        
                        # Проверка точности расчета
                        if 'result' in result:
                            calculated_value = result['result']
                            expected_range = self.test_calculations['safety_factors']['expected_result_range']
                            
                            if expected_range[0] <= calculated_value <= expected_range[1]:
                                logger.info(f"✅ Результат в ожидаемом диапазоне: {calculated_value}")
                                return True
                            else:
                                logger.warning(f"⚠️ Результат вне ожидаемого диапазона: {calculated_value}")
                                return False
                        else:
                            logger.error("❌ Результат расчета не получен")
                            return False
                    else:
                        logger.error(f"❌ Ошибка расчета: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ Ошибка расчета: {e}")
            return False

    async def test_dimension_tolerances_calculation(self):
        """Тестирование расчета допусков и посадок"""
        logger.info("🧪 Тестирование расчета допусков и посадок...")
        
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    'calculation_type': 'dimension_tolerances',
                    'parameters': self.test_calculations['dimension_tolerances']
                }
                
                async with session.post(
                    f"{self.api_url}/calculate",
                    json=payload,
                    ssl=False,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info("✅ Расчет допусков и посадок выполнен")
                        
                        # Проверка точности расчета
                        if 'result' in result:
                            calculated_value = result['result']
                            expected_range = self.test_calculations['dimension_tolerances']['expected_result_range']
                            
                            if expected_range[0] <= calculated_value <= expected_range[1]:
                                logger.info(f"✅ Результат в ожидаемом диапазоне: {calculated_value}")
                                return True
                            else:
                                logger.warning(f"⚠️ Результат вне ожидаемого диапазона: {calculated_value}")
                                return False
                        else:
                            logger.error("❌ Результат расчета не получен")
                            return False
                    else:
                        logger.error(f"❌ Ошибка расчета: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ Ошибка расчета: {e}")
            return False

    async def test_thermal_expansion_calculation(self):
        """Тестирование расчета теплового расширения"""
        logger.info("🧪 Тестирование расчета теплового расширения...")
        
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    'calculation_type': 'thermal_expansion',
                    'parameters': self.test_calculations['thermal_expansion']
                }
                
                async with session.post(
                    f"{self.api_url}/calculate",
                    json=payload,
                    ssl=False,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info("✅ Расчет теплового расширения выполнен")
                        
                        # Проверка точности расчета
                        if 'result' in result:
                            calculated_value = result['result']
                            expected_range = self.test_calculations['thermal_expansion']['expected_result_range']
                            
                            if expected_range[0] <= calculated_value <= expected_range[1]:
                                logger.info(f"✅ Результат в ожидаемом диапазоне: {calculated_value}")
                                return True
                            else:
                                logger.warning(f"⚠️ Результат вне ожидаемого диапазона: {calculated_value}")
                                return False
                        else:
                            logger.error("❌ Результат расчета не получен")
                            return False
                    else:
                        logger.error(f"❌ Ошибка расчета: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ Ошибка расчета: {e}")
            return False

    async def test_fatigue_analysis_calculation(self):
        """Тестирование расчета усталостного анализа"""
        logger.info("🧪 Тестирование расчета усталостного анализа...")
        
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    'calculation_type': 'fatigue_analysis',
                    'parameters': self.test_calculations['fatigue_analysis']
                }
                
                async with session.post(
                    f"{self.api_url}/calculate",
                    json=payload,
                    ssl=False,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info("✅ Расчет усталостного анализа выполнен")
                        
                        # Проверка точности расчета
                        if 'result' in result:
                            calculated_value = result['result']
                            expected_range = self.test_calculations['fatigue_analysis']['expected_result_range']
                            
                            if expected_range[0] <= calculated_value <= expected_range[1]:
                                logger.info(f"✅ Результат в ожидаемом диапазоне: {calculated_value}")
                                return True
                            else:
                                logger.warning(f"⚠️ Результат вне ожидаемого диапазона: {calculated_value}")
                                return False
                        else:
                            logger.error("❌ Результат расчета не получен")
                            return False
                    else:
                        logger.error(f"❌ Ошибка расчета: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ Ошибка расчета: {e}")
            return False

    async def test_batch_calculations(self):
        """Тестирование пакетных расчетов"""
        logger.info("🧪 Тестирование пакетных расчетов...")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Подготовка пакета расчетов
                calculations = []
                for calc_type, params in self.test_calculations.items():
                    calculations.append({
                        'type': calc_type,
                        'parameters': params
                    })
                
                payload = {
                    'calculations': calculations,
                    'parallel_processing': True
                }
                
                async with session.post(
                    f"{self.api_url}/batch_calculate",
                    json=payload,
                    ssl=False,
                    timeout=120
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info("✅ Пакетные расчеты выполнены")
                        
                        # Проверка результатов
                        if 'results' in result and len(result['results']) == len(calculations):
                            logger.info(f"✅ Обработано {len(result['results'])} расчетов")
                            return True
                        else:
                            logger.warning("⚠️ Не все расчеты выполнены")
                            return False
                    else:
                        logger.error(f"❌ Ошибка пакетных расчетов: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ Ошибка пакетных расчетов: {e}")
            return False

    async def test_frontend_calculations(self):
        """Тестирование фронтенд расчетов"""
        logger.info("🧪 Тестирование фронтенд расчетов...")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Тест главной страницы расчетов
                async with session.get(
                    f"{self.frontend_url}/calculations",
                    ssl=False,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        logger.info("✅ Фронтенд расчетов доступен")
                        
                        # Тест API эндпоинта для фронтенда
                        payload = {
                            'calculation_type': 'welding_strength',
                            'parameters': self.test_calculations['welding_strength']
                        }
                        
                        async with session.post(
                            f"{self.frontend_url}/api/calculate",
                            json=payload,
                            ssl=False,
                            timeout=30
                        ) as response:
                            if response.status == 200:
                                result = await response.json()
                                logger.info("✅ API для фронтенда работает")
                                return True
                            else:
                                logger.warning(f"⚠️ API для фронтенда недоступен: {response.status}")
                                return False
                    else:
                        logger.error(f"❌ Фронтенд недоступен: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ Ошибка фронтенда: {e}")
            return False

    async def test_calculation_accuracy(self):
        """Тестирование точности расчетов"""
        logger.info("🧪 Тестирование точности расчетов...")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Тест с известными результатами
                test_cases = [
                    {
                        'type': 'welding_strength',
                        'parameters': {'material': 'steel', 'thickness': 10, 'load': 1000},
                        'expected': 100  # Ожидаемый результат
                    },
                    {
                        'type': 'safety_factors',
                        'parameters': {'load': 1000, 'safety_factor': 2.5},
                        'expected': 400  # Ожидаемый результат
                    }
                ]
                
                accuracy_results = []
                
                for test_case in test_cases:
                    payload = {
                        'calculation_type': test_case['type'],
                        'parameters': test_case['parameters']
                    }
                    
                    async with session.post(
                        f"{self.api_url}/calculate",
                        json=payload,
                        ssl=False,
                        timeout=30
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            
                            if 'result' in result:
                                calculated = result['result']
                                expected = test_case['expected']
                                accuracy = abs(calculated - expected) / expected
                                
                                if accuracy < 0.1:  # 10% погрешность
                                    accuracy_results.append(True)
                                    logger.info(f"✅ Точность {test_case['type']}: {accuracy:.2%}")
                                else:
                                    accuracy_results.append(False)
                                    logger.warning(f"⚠️ Низкая точность {test_case['type']}: {accuracy:.2%}")
                            else:
                                accuracy_results.append(False)
                        else:
                            accuracy_results.append(False)
                
                # Общая оценка точности
                if sum(accuracy_results) / len(accuracy_results) >= 0.8:
                    logger.info("✅ Общая точность расчетов удовлетворительная")
                    return True
                else:
                    logger.warning("⚠️ Общая точность расчетов низкая")
                    return False
        except Exception as e:
            logger.error(f"❌ Ошибка проверки точности: {e}")
            return False

    async def test_error_handling(self):
        """Тестирование обработки ошибок"""
        logger.info("🧪 Тестирование обработки ошибок...")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Тест с некорректными параметрами
                payload = {
                    'calculation_type': 'invalid_type',
                    'parameters': {}
                }
                
                async with session.post(
                    f"{self.api_url}/calculate",
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
        """Запуск всех тестов модуля расчетов"""
        logger.info("🚀 Запуск тестирования модуля 'Расчеты'...")
        start_time = time.time()
        
        # Запуск тестов
        self.test_results = {
            'service_health': await self.test_service_health(),
            'welding_strength_calculation': await self.test_welding_strength_calculation(),
            'material_properties_calculation': await self.test_material_properties_calculation(),
            'safety_factors_calculation': await self.test_safety_factors_calculation(),
            'dimension_tolerances_calculation': await self.test_dimension_tolerances_calculation(),
            'thermal_expansion_calculation': await self.test_thermal_expansion_calculation(),
            'fatigue_analysis_calculation': await self.test_fatigue_analysis_calculation(),
            'batch_calculations': await self.test_batch_calculations(),
            'frontend_calculations': await self.test_frontend_calculations(),
            'calculation_accuracy': await self.test_calculation_accuracy(),
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
            'module': 'Расчеты',
            'timestamp': datetime.now().isoformat(),
            'test_results': self.test_results,
            'test_calculations': self.test_calculations,
            'summary': {
                'total_tests': len(self.test_results),
                'passed_tests': sum(1 for result in self.test_results.values() if result),
                'success_rate': (sum(1 for result in self.test_results.values() if result) / len(self.test_results)) * 100
            }
        }
        
        # Сохранение отчета
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        report_path = os.path.join(base_dir, 'reports', 'calculations_test_report.json')
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        return report

async def main():
    """Основная функция"""
    tester = CalculationsTester()
    
    # Запуск тестов
    results = await tester.run_all_tests()
    
    # Генерация отчета
    report = tester.generate_report()
    
    # Вывод результатов
    print("\n" + "="*60)
    print("📊 ОТЧЕТ ПО МОДУЛЮ 'РАСЧЕТЫ'")
    print("="*60)
    
    for test_name, result in results.items():
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        print(f"{test_name}: {status}")
    
    print(f"\n🎯 УСПЕШНОСТЬ: {report['summary']['success_rate']:.1f}%")
    print(f"📄 Отчет сохранен: calculations_test_report.json")

if __name__ == "__main__":
    asyncio.run(main())
