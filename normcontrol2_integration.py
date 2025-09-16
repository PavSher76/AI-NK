"""
Интеграция модуля Нормоконтроль - 2 с основной системой AI-NK
"""

import logging
import time
from typing import Dict, Any, Optional
from pathlib import Path

from normcontrol2_service import NormControl2Service
from normcontrol2_service.models import ValidationResult, ComplianceStatus

logger = logging.getLogger(__name__)


class NormControl2Integration:
    """Интеграция модуля Нормоконтроль - 2 с основной системой"""
    
    def __init__(self):
        self.normcontrol2_service = NormControl2Service()
        self.integration_config = self._load_integration_config()
    
    def _load_integration_config(self) -> Dict[str, Any]:
        """Загрузка конфигурации интеграции"""
        return {
            "auto_validation": True,
            "save_results": True,
            "results_directory": "normcontrol2_results",
            "notification_enabled": True,
            "integration_timeout": 300
        }
    
    def validate_document_integrated(self, file_path: str, document_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Интегрированная валидация документа с сохранением результатов
        """
        try:
            logger.info(f"🔍 [NORM2_INTEGRATION] Начало валидации документа: {file_path}")
            
            # Выполнение валидации
            result = self.normcontrol2_service.validate_document(file_path, document_id)
            
            # Сохранение результатов
            if self.integration_config["save_results"]:
                self._save_validation_results(result)
            
            # Уведомления
            if self.integration_config["notification_enabled"]:
                self._send_validation_notification(result)
            
            # Преобразование результата для интеграции
            integrated_result = self._convert_result_for_integration(result)
            
            logger.info(f"✅ [NORM2_INTEGRATION] Валидация завершена: {result.overall_status.value}")
            
            return integrated_result
            
        except Exception as e:
            logger.error(f"❌ [NORM2_INTEGRATION] Ошибка валидации {file_path}: {e}")
            return self._create_error_result(file_path, str(e), document_id)
    
    def _save_validation_results(self, result: ValidationResult) -> None:
        """Сохранение результатов валидации"""
        try:
            # Создание директории для результатов
            results_dir = Path(self.integration_config["results_directory"])
            results_dir.mkdir(exist_ok=True)
            
            # Генерация имени файла
            timestamp = int(time.time())
            filename = f"normcontrol2_result_{result.document_id}_{timestamp}.json"
            filepath = results_dir / filename
            
            # Сохранение результата
            import json
            result_dict = self._result_to_dict(result)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(result_dict, f, ensure_ascii=False, indent=2)
            
            logger.info(f"💾 [NORM2_INTEGRATION] Результаты сохранены: {filepath}")
            
        except Exception as e:
            logger.error(f"❌ [NORM2_INTEGRATION] Ошибка сохранения результатов: {e}")
    
    def _send_validation_notification(self, result: ValidationResult) -> None:
        """Отправка уведомления о результатах валидации"""
        try:
            # Определение уровня уведомления
            if result.overall_status == ComplianceStatus.CRITICAL_ISSUES:
                level = "CRITICAL"
            elif result.overall_status == ComplianceStatus.NON_COMPLIANT:
                level = "HIGH"
            elif result.overall_status == ComplianceStatus.NEEDS_REVIEW:
                level = "MEDIUM"
            else:
                level = "INFO"
            
            # Формирование сообщения
            message = f"""
🔍 НОРМОКОНТРОЛЬ - 2: Результаты валидации

📄 Документ: {result.document_name}
🆔 ID: {result.document_id}
📊 Статус: {result.overall_status.value}
📈 Оценка: {result.compliance_score:.1f}%

⚠️ Проблемы:
  • Всего: {result.total_issues}
  • Критических: {result.critical_issues}
  • Высокого приоритета: {result.high_issues}
  • Среднего приоритета: {result.medium_issues}

💡 Рекомендации:
{chr(10).join(f"  • {rec}" for rec in result.recommendations[:3])}
"""
            
            logger.info(f"📢 [NORM2_INTEGRATION] Уведомление [{level}]: {message.strip()}")
            
        except Exception as e:
            logger.error(f"❌ [NORM2_INTEGRATION] Ошибка отправки уведомления: {e}")
    
    def _convert_result_for_integration(self, result: ValidationResult) -> Dict[str, Any]:
        """Преобразование результата для интеграции с основной системой"""
        return {
            "success": True,
            "service": "normcontrol2",
            "document_id": result.document_id,
            "document_name": result.document_name,
            "document_format": result.document_format.value,
            "validation_time": result.validation_time.isoformat(),
            "overall_status": result.overall_status.value,
            "compliance_score": result.compliance_score,
            "total_issues": result.total_issues,
            "issues_by_severity": {
                "critical": result.critical_issues,
                "high": result.high_issues,
                "medium": result.medium_issues,
                "low": result.low_issues,
                "info": result.info_issues
            },
            "categories": result.categories,
            "recommendations": result.recommendations,
            "metadata": result.metadata,
            "integration_timestamp": time.time()
        }
    
    def _result_to_dict(self, result: ValidationResult) -> Dict[str, Any]:
        """Преобразование результата в словарь для JSON"""
        return {
            "document_id": result.document_id,
            "document_name": result.document_name,
            "document_format": result.document_format.value,
            "validation_time": result.validation_time.isoformat(),
            "overall_status": result.overall_status.value,
            "compliance_score": result.compliance_score,
            "total_issues": result.total_issues,
            "critical_issues": result.critical_issues,
            "high_issues": result.high_issues,
            "medium_issues": result.medium_issues,
            "low_issues": result.low_issues,
            "info_issues": result.info_issues,
            "issues": [
                {
                    "id": issue.id,
                    "category": issue.category,
                    "severity": issue.severity.value,
                    "title": issue.title,
                    "description": issue.description,
                    "recommendation": issue.recommendation,
                    "page_number": issue.page_number,
                    "coordinates": issue.coordinates,
                    "rule_reference": issue.rule_reference
                }
                for issue in result.issues
            ],
            "categories": result.categories,
            "recommendations": result.recommendations,
            "metadata": result.metadata
        }
    
    def _create_error_result(self, file_path: str, error_message: str, document_id: Optional[str]) -> Dict[str, Any]:
        """Создание результата с ошибкой"""
        return {
            "success": False,
            "service": "normcontrol2",
            "document_id": document_id or str(int(time.time())),
            "document_name": Path(file_path).name,
            "error": error_message,
            "validation_time": time.time(),
            "integration_timestamp": time.time()
        }
    
    def get_validation_statistics(self) -> Dict[str, Any]:
        """Получение статистики валидации"""
        try:
            results_dir = Path(self.integration_config["results_directory"])
            if not results_dir.exists():
                return {"total_validations": 0}
            
            # Подсчет файлов результатов
            result_files = list(results_dir.glob("normcontrol2_result_*.json"))
            total_validations = len(result_files)
            
            if total_validations == 0:
                return {"total_validations": 0}
            
            # Анализ результатов
            compliance_scores = []
            status_counts = {}
            category_counts = {}
            
            for result_file in result_files:
                try:
                    import json
                    with open(result_file, 'r', encoding='utf-8') as f:
                        result_data = json.load(f)
                    
                    compliance_scores.append(result_data.get("compliance_score", 0))
                    
                    status = result_data.get("overall_status", "unknown")
                    status_counts[status] = status_counts.get(status, 0) + 1
                    
                    categories = result_data.get("categories", {})
                    for category, data in categories.items():
                        category_counts[category] = category_counts.get(category, 0) + data.get("total_issues", 0)
                
                except Exception as e:
                    logger.warning(f"Ошибка чтения файла результата {result_file}: {e}")
                    continue
            
            # Расчет статистики
            avg_compliance_score = sum(compliance_scores) / len(compliance_scores) if compliance_scores else 0
            
            return {
                "total_validations": total_validations,
                "average_compliance_score": round(avg_compliance_score, 2),
                "status_distribution": status_counts,
                "category_issues": category_counts,
                "last_validation": max([f.stat().st_mtime for f in result_files]) if result_files else 0
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики: {e}")
            return {"error": str(e)}
    
    def cleanup_old_results(self, days_to_keep: int = 30) -> int:
        """Очистка старых результатов"""
        try:
            results_dir = Path(self.integration_config["results_directory"])
            if not results_dir.exists():
                return 0
            
            import time
            current_time = time.time()
            cutoff_time = current_time - (days_to_keep * 24 * 60 * 60)
            
            deleted_count = 0
            for result_file in results_dir.glob("normcontrol2_result_*.json"):
                if result_file.stat().st_mtime < cutoff_time:
                    result_file.unlink()
                    deleted_count += 1
            
            logger.info(f"🧹 [NORM2_INTEGRATION] Удалено старых результатов: {deleted_count}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Ошибка очистки старых результатов: {e}")
            return 0


# Глобальный экземпляр для интеграции
normcontrol2_integration = NormControl2Integration()


def validate_document_with_normcontrol2(file_path: str, document_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Функция для интеграции с основной системой
    """
    return normcontrol2_integration.validate_document_integrated(file_path, document_id)


def get_normcontrol2_statistics() -> Dict[str, Any]:
    """
    Получение статистики модуля Нормоконтроль - 2
    """
    return normcontrol2_integration.get_validation_statistics()


def cleanup_normcontrol2_results(days_to_keep: int = 30) -> int:
    """
    Очистка старых результатов модуля Нормоконтроль - 2
    """
    return normcontrol2_integration.cleanup_old_results(days_to_keep)


if __name__ == "__main__":
    # Тестирование интеграции
    print("🚀 ТЕСТИРОВАНИЕ ИНТЕГРАЦИИ МОДУЛЯ НОРМОКОНТРОЛЬ - 2")
    print()
    
    # Тестовый файл
    test_file = "test_document.pdf"
    
    if Path(test_file).exists():
        print(f"🔍 Тестирование валидации: {test_file}")
        result = validate_document_with_normcontrol2(test_file, "test_doc_001")
        
        print(f"✅ Результат: {result.get('success', False)}")
        print(f"📊 Статус: {result.get('overall_status', 'unknown')}")
        print(f"📈 Оценка: {result.get('compliance_score', 0):.1f}%")
        print(f"⚠️ Проблем: {result.get('total_issues', 0)}")
    else:
        print(f"❌ Тестовый файл {test_file} не найден")
    
    print()
    
    # Статистика
    print("📊 Статистика модуля:")
    stats = get_normcontrol2_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print()
    print("✅ Тестирование завершено")
