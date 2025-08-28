#!/usr/bin/env python3
"""
Скрипт для автоматизации обучения системы AI-NK
Автор: AI Assistant
Версия: 1.0.0
"""

import os
import json
import time
import requests
import psycopg2
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('training.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class TrainingConfig:
    """Конфигурация для обучения системы"""
    api_base_url: str = "https://localhost/api"
    auth_token: str = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0cmFpbmluZy11c2VyIiwicHJlZmVycmVkX3VzZXJuYW1lIjoidHJhaW5pbmctdXNlciIsImV4cCI6OTk5OTk5OTk5OX0udHJhaW5pbmctc2lnbmF0dXJl"
    database_url: str = "postgresql://norms_user:norms_password@localhost:5432/norms_db"
    test_documents_path: str = "TestDocs/for_check"
    normative_documents_path: str = "TestDocs/Norms"
    max_processing_time: int = 300  # секунды
    quality_threshold: float = 0.85

class AINKTrainingSystem:
    """Система обучения AI-NK"""
    
    def __init__(self, config: TrainingConfig):
        self.config = config
        self.session = requests.Session()
        self.session.verify = False  # Отключаем проверку SSL для локальной разработки
        self.session.headers.update({
            'Authorization': f'Bearer {config.auth_token}'
        })
        
    def check_system_health(self) -> bool:
        """Проверка состояния системы"""
        try:
            response = self.session.get(f"{self.config.api_base_url}/health")
            if response.status_code == 200:
                logger.info("✅ Система работает корректно")
                return True
            else:
                logger.error(f"❌ Система недоступна: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к системе: {e}")
            return False
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Получение статистики системы"""
        try:
            response = self.session.get(f"{self.config.api_base_url}/documents/stats")
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"❌ Ошибка получения статистики: {response.status_code}")
                return {}
        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики: {e}")
            return {}
    
    def get_current_prompt(self) -> str:
        """Получение текущего промпта из базы данных"""
        try:
            conn = psycopg2.connect(self.config.database_url)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT setting_value FROM system_settings WHERE setting_key = 'normcontrol_prompt'"
            )
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if result:
                return result[0]
            else:
                logger.warning("⚠️ Промпт не найден в базе данных")
                return ""
        except Exception as e:
            logger.error(f"❌ Ошибка получения промпта: {e}")
            return ""
    
    def update_prompt(self, new_prompt: str) -> bool:
        """Обновление промпта в базе данных"""
        try:
            conn = psycopg2.connect(self.config.database_url)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE system_settings SET setting_value = %s, updated_at = CURRENT_TIMESTAMP WHERE setting_key = 'normcontrol_prompt'",
                (new_prompt,)
            )
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info("✅ Промпт успешно обновлен")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка обновления промпта: {e}")
            return False
    
    def upload_test_document(self, file_path: str) -> Optional[int]:
        """Загрузка тестового документа"""
        try:
            if not os.path.exists(file_path):
                logger.error(f"❌ Файл не найден: {file_path}")
                return None
            
            with open(file_path, 'rb') as f:
                files = {'file': f}
                response = self.session.post(
                    f"{self.config.api_base_url}/upload/checkable",
                    files=files
                )
            
            if response.status_code == 200:
                result = response.json()
                document_id = result.get('document_id')
                logger.info(f"✅ Документ загружен: {os.path.basename(file_path)} (ID: {document_id})")
                return document_id
            else:
                logger.error(f"❌ Ошибка загрузки документа: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки документа {file_path}: {e}")
            return None
    
    def wait_for_processing(self, document_id: int) -> bool:
        """Ожидание завершения обработки документа"""
        start_time = time.time()
        
        while time.time() - start_time < self.config.max_processing_time:
            try:
                response = self.session.get(f"{self.config.api_base_url}/checkable-documents")
                if response.status_code == 200:
                    documents = response.json().get('documents', [])
                    for doc in documents:
                        if doc.get('id') == document_id:
                            status = doc.get('processing_status')
                            if status == 'completed':
                                logger.info(f"✅ Документ {document_id} обработан")
                                return True
                            elif status == 'error':
                                logger.error(f"❌ Ошибка обработки документа {document_id}")
                                return False
                            else:
                                logger.info(f"⏳ Документ {document_id} в обработке...")
                                break
                
                time.sleep(5)  # Ждем 5 секунд перед следующей проверкой
            except Exception as e:
                logger.error(f"❌ Ошибка проверки статуса: {e}")
                time.sleep(5)
        
        logger.error(f"❌ Таймаут обработки документа {document_id}")
        return False
    
    def get_analysis_result(self, document_id: int) -> Optional[Dict[str, Any]]:
        """Получение результата анализа документа"""
        try:
            response = self.session.get(f"{self.config.api_base_url}/checkable-documents/{document_id}/report")
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"❌ Ошибка получения отчета: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"❌ Ошибка получения отчета: {e}")
            return None
    
    def calculate_quality_metrics(self, expected: Dict[str, Any], actual: Dict[str, Any]) -> Dict[str, float]:
        """Расчет метрик качества"""
        try:
            # Извлекаем нарушения из результатов
            expected_violations = set()
            actual_violations = set()
            
            # Ожидаемые нарушения
            for violation in expected.get('expected_violations', []):
                expected_violations.add(violation.get('description', ''))
            
            # Фактические нарушения
            norm_control_result = actual.get('norm_control_result', {})
            findings = norm_control_result.get('findings', [])
            
            for finding in findings:
                actual_violations.add(finding.get('description', ''))
            
            # Расчет метрик
            true_positives = len(expected_violations & actual_violations)
            precision = true_positives / len(actual_violations) if actual_violations else 0
            recall = true_positives / len(expected_violations) if expected_violations else 0
            f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            
            return {
                'precision': precision,
                'recall': recall,
                'f1_score': f1_score,
                'true_positives': true_positives,
                'false_positives': len(actual_violations) - true_positives,
                'false_negatives': len(expected_violations) - true_positives
            }
        except Exception as e:
            logger.error(f"❌ Ошибка расчета метрик: {e}")
            return {'precision': 0, 'recall': 0, 'f1_score': 0}
    
    def run_training_session(self, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Запуск сессии обучения"""
        logger.info("🚀 Начало сессии обучения системы AI-NK")
        
        results = {
            'session_start': datetime.now().isoformat(),
            'test_cases': [],
            'overall_metrics': {},
            'prompt_improvements': []
        }
        
        # Проверка состояния системы
        if not self.check_system_health():
            logger.error("❌ Система недоступна, обучение прервано")
            return results
        
        # Получение текущей статистики
        initial_stats = self.get_system_stats()
        logger.info(f"📊 Начальная статистика: {initial_stats}")
        
        # Обработка тестовых случаев
        total_metrics = {'precision': 0, 'recall': 0, 'f1_score': 0}
        successful_tests = 0
        
        for i, test_case in enumerate(test_cases, 1):
            logger.info(f"🧪 Тестовый случай {i}/{len(test_cases)}: {test_case['document_name']}")
            
            # Загрузка документа
            document_id = self.upload_test_document(test_case['file_path'])
            if not document_id:
                continue
            
            # Ожидание обработки
            if not self.wait_for_processing(document_id):
                continue
            
            # Получение результата
            analysis_result = self.get_analysis_result(document_id)
            if not analysis_result:
                continue
            
            # Расчет метрик
            metrics = self.calculate_quality_metrics(test_case['expected'], analysis_result)
            
            # Сохранение результата
            test_result = {
                'document_name': test_case['document_name'],
                'document_id': document_id,
                'metrics': metrics,
                'expected': test_case['expected'],
                'actual': analysis_result
            }
            results['test_cases'].append(test_result)
            
            # Накопление метрик
            total_metrics['precision'] += metrics['precision']
            total_metrics['recall'] += metrics['recall']
            total_metrics['f1_score'] += metrics['f1_score']
            successful_tests += 1
            
            logger.info(f"📈 Метрики для {test_case['document_name']}: F1={metrics['f1_score']:.3f}")
        
        # Расчет общих метрик
        if successful_tests > 0:
            results['overall_metrics'] = {
                'precision': total_metrics['precision'] / successful_tests,
                'recall': total_metrics['recall'] / successful_tests,
                'f1_score': total_metrics['f1_score'] / successful_tests,
                'successful_tests': successful_tests,
                'total_tests': len(test_cases)
            }
        
        results['session_end'] = datetime.now().isoformat()
        
        logger.info(f"✅ Сессия обучения завершена. Общий F1-score: {results['overall_metrics'].get('f1_score', 0):.3f}")
        
        return results
    
    def suggest_prompt_improvements(self, results: Dict[str, Any]) -> List[str]:
        """Предложение улучшений промпта на основе результатов"""
        improvements = []
        
        overall_metrics = results.get('overall_metrics', {})
        f1_score = overall_metrics.get('f1_score', 0)
        precision = overall_metrics.get('precision', 0)
        recall = overall_metrics.get('recall', 0)
        
        # Анализ проблем
        if f1_score < self.config.quality_threshold:
            if precision < 0.8:
                improvements.append("Увеличить точность: добавить более конкретные критерии классификации нарушений")
            if recall < 0.8:
                improvements.append("Увеличить полноту: расширить список проверяемых аспектов")
        
        # Анализ конкретных случаев
        for test_case in results.get('test_cases', []):
            metrics = test_case.get('metrics', {})
            if metrics.get('false_positives', 0) > 0:
                improvements.append("Уменьшить ложные срабатывания: уточнить критерии критических нарушений")
            if metrics.get('false_negatives', 0) > 0:
                improvements.append("Уменьшить пропуски: добавить проверку дополнительных аспектов")
        
        return list(set(improvements))  # Убираем дубликаты

def load_test_cases(config: TrainingConfig) -> List[Dict[str, Any]]:
    """Загрузка тестовых случаев из файлов"""
    test_cases = []
    
    # Структура папок для тестирования
    test_folders = {
        'Правильные': {'expected_status': 'соответствует', 'expected_violations': []},
        'С_ошибками': {'expected_status': 'не соответствует', 'expected_violations': ['sample_violation']},
        'Пограничные': {'expected_status': 'частично соответствует', 'expected_violations': ['minor_violation']}
    }
    
    for folder, expected in test_folders.items():
        folder_path = os.path.join(config.test_documents_path, folder)
        logger.info(f"🔍 Проверка папки: {folder_path}")
        
        if os.path.exists(folder_path):
            logger.info(f"✅ Папка существует: {folder_path}")
            for file_name in os.listdir(folder_path):
                if file_name.lower().endswith('.pdf'):
                    file_path = os.path.join(folder_path, file_name)
                    test_case = {
                        'document_name': file_name,
                        'file_path': file_path,
                        'category': folder,
                        'expected': expected
                    }
                    test_cases.append(test_case)
                    logger.info(f"📄 Найден тестовый документ: {file_name}")
        else:
            logger.warning(f"⚠️ Папка не найдена: {folder_path}")
    
    logger.info(f"📊 Всего найдено тестовых случаев: {len(test_cases)}")
    return test_cases

def main():
    """Основная функция"""
    print("🎓 Система обучения AI-NK")
    print("=" * 50)
    
    # Изменяем рабочую директорию на корневую папку проекта
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    os.chdir(project_root)
    
    print(f"📁 Рабочая директория: {os.getcwd()}")
    
    # Конфигурация
    config = TrainingConfig()
    
    # Создание системы обучения
    training_system = AINKTrainingSystem(config)
    
    # Загрузка тестовых случаев
    test_cases = load_test_cases(config)
    if not test_cases:
        print("❌ Тестовые документы не найдены")
        print(f"Ожидаемая структура: {config.test_documents_path}/")
        return
    
    print(f"📁 Найдено {len(test_cases)} тестовых документов")
    
    # Запуск обучения
    results = training_system.run_training_session(test_cases)
    
    # Анализ результатов
    overall_metrics = results.get('overall_metrics', {})
    print(f"\n📊 Результаты обучения:")
    print(f"  F1-Score: {overall_metrics.get('f1_score', 0):.3f}")
    print(f"  Precision: {overall_metrics.get('precision', 0):.3f}")
    print(f"  Recall: {overall_metrics.get('recall', 0):.3f}")
    print(f"  Успешных тестов: {overall_metrics.get('successful_tests', 0)}/{overall_metrics.get('total_tests', 0)}")
    
    # Предложения по улучшению
    improvements = training_system.suggest_prompt_improvements(results)
    if improvements:
        print(f"\n💡 Предложения по улучшению:")
        for i, improvement in enumerate(improvements, 1):
            print(f"  {i}. {improvement}")
    
    # Сохранение результатов
    with open('training_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Результаты сохранены в training_results.json")
    
    # Рекомендации
    f1_score = overall_metrics.get('f1_score', 0)
    if f1_score >= 0.9:
        print("🎉 Отличные результаты! Система готова к продакшену.")
    elif f1_score >= 0.8:
        print("👍 Хорошие результаты. Рекомендуется дополнительная настройка.")
    elif f1_score >= 0.7:
        print("⚠️ Средние результаты. Требуется значительная доработка промптов.")
    else:
        print("❌ Низкие результаты. Необходима серьезная переработка системы.")

if __name__ == "__main__":
    main()
