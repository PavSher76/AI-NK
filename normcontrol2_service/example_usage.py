"""
Пример использования модуля Нормоконтроль - 2
"""

import logging
from pathlib import Path
from normcontrol2_service import NormControl2Service
from normcontrol2_service.models import DocumentFormat, ComplianceStatus

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def example_validate_pdf_document():
    """Пример валидации PDF документа"""
    print("=" * 80)
    print("ПРИМЕР ВАЛИДАЦИИ PDF ДОКУМЕНТА")
    print("=" * 80)
    
    # Инициализация сервиса
    service = NormControl2Service()
    
    # Путь к тестовому документу
    file_path = "test_document.pdf"
    
    if not Path(file_path).exists():
        print(f"❌ Файл {file_path} не найден")
        return
    
    try:
        # Выполнение валидации
        print(f"🔍 Валидация документа: {file_path}")
        result = service.validate_document(file_path)
        
        # Вывод результатов
        print_validation_results(result)
        
    except Exception as e:
        print(f"❌ Ошибка валидации: {e}")


def example_validate_dwg_document():
    """Пример валидации DWG документа"""
    print("=" * 80)
    print("ПРИМЕР ВАЛИДАЦИИ DWG ДОКУМЕНТА")
    print("=" * 80)
    
    # Инициализация сервиса
    service = NormControl2Service()
    
    # Путь к тестовому документу
    file_path = "test_document.dwg"
    
    if not Path(file_path).exists():
        print(f"❌ Файл {file_path} не найден")
        return
    
    try:
        # Выполнение валидации
        print(f"🔍 Валидация документа: {file_path}")
        result = service.validate_document(file_path)
        
        # Вывод результатов
        print_validation_results(result)
        
    except Exception as e:
        print(f"❌ Ошибка валидации: {e}")


def example_batch_validation():
    """Пример пакетной валидации"""
    print("=" * 80)
    print("ПРИМЕР ПАКЕТНОЙ ВАЛИДАЦИИ")
    print("=" * 80)
    
    # Инициализация сервиса
    service = NormControl2Service()
    
    # Список файлов для валидации
    file_paths = [
        "document1.pdf",
        "document2.dwg",
        "document3.dxf",
        "document4.docx"
    ]
    
    print(f"📁 Валидация {len(file_paths)} документов:")
    for file_path in file_paths:
        print(f"  - {file_path}")
    
    print()
    
    # Валидация каждого документа
    results = []
    for file_path in file_paths:
        if Path(file_path).exists():
            try:
                print(f"🔍 Валидация: {file_path}")
                result = service.validate_document(file_path)
                results.append(result)
                print(f"  ✅ Статус: {result.overall_status.value}")
                print(f"  📊 Оценка: {result.compliance_score:.1f}%")
                print(f"  ⚠️ Проблем: {result.total_issues}")
                print()
            except Exception as e:
                print(f"  ❌ Ошибка: {e}")
                print()
        else:
            print(f"  ❌ Файл не найден: {file_path}")
            print()
    
    # Сводная статистика
    if results:
        print("📊 СВОДНАЯ СТАТИСТИКА:")
        print(f"  Всего документов: {len(results)}")
        print(f"  Средняя оценка: {sum(r.compliance_score for r in results) / len(results):.1f}%")
        print(f"  Всего проблем: {sum(r.total_issues for r in results)}")
        
        # Статистика по статусам
        status_counts = {}
        for result in results:
            status = result.overall_status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        print("  Статусы:")
        for status, count in status_counts.items():
            print(f"    {status}: {count}")


def print_validation_results(result):
    """Красивый вывод результатов валидации"""
    print(f"\n📄 РЕЗУЛЬТАТЫ ВАЛИДАЦИИ")
    print(f"  Документ: {result.document_name}")
    print(f"  Формат: {result.document_format.value}")
    print(f"  ID: {result.document_id}")
    print(f"  Время валидации: {result.validation_time}")
    
    print(f"\n📊 ОБЩАЯ ОЦЕНКА")
    print(f"  Статус: {get_status_emoji(result.overall_status)} {result.overall_status.value}")
    print(f"  Оценка соответствия: {result.compliance_score:.1f}%")
    
    print(f"\n⚠️ ПРОБЛЕМЫ")
    print(f"  Всего: {result.total_issues}")
    print(f"  Критических: {result.critical_issues}")
    print(f"  Высокого приоритета: {result.high_issues}")
    print(f"  Среднего приоритета: {result.medium_issues}")
    print(f"  Низкого приоритета: {result.low_issues}")
    print(f"  Информационных: {result.info_issues}")
    
    # Проблемы по категориям
    if result.categories:
        print(f"\n📋 ПРОБЛЕМЫ ПО КАТЕГОРИЯМ")
        for category, data in result.categories.items():
            print(f"  {category}: {data['total_issues']} проблем")
            if data['critical_issues'] > 0:
                print(f"    Критических: {data['critical_issues']}")
            if data['high_issues'] > 0:
                print(f"    Высокого приоритета: {data['high_issues']}")
    
    # Рекомендации
    if result.recommendations:
        print(f"\n💡 РЕКОМЕНДАЦИИ")
        for i, rec in enumerate(result.recommendations, 1):
            print(f"  {i}. {rec}")
    
    # Детали проблем
    if result.issues:
        print(f"\n🔍 ДЕТАЛИ ПРОБЛЕМ")
        for i, issue in enumerate(result.issues[:10], 1):  # Показываем первые 10
            print(f"  {i}. [{issue.severity.value.upper()}] {issue.title}")
            print(f"     {issue.description}")
            print(f"     💡 {issue.recommendation}")
            if issue.page_number:
                print(f"     📄 Страница: {issue.page_number}")
            print()
        
        if len(result.issues) > 10:
            print(f"  ... и еще {len(result.issues) - 10} проблем")


def get_status_emoji(status: ComplianceStatus) -> str:
    """Получение эмодзи для статуса"""
    emoji_map = {
        ComplianceStatus.COMPLIANT: "✅",
        ComplianceStatus.COMPLIANT_WITH_WARNINGS: "⚠️",
        ComplianceStatus.NON_COMPLIANT: "❌",
        ComplianceStatus.CRITICAL_ISSUES: "🚫",
        ComplianceStatus.NEEDS_REVIEW: "🔍"
    }
    return emoji_map.get(status, "❓")


def example_custom_validation():
    """Пример кастомной валидации с настройками"""
    print("=" * 80)
    print("ПРИМЕР КАСТОМНОЙ ВАЛИДАЦИИ")
    print("=" * 80)
    
    # Инициализация сервиса
    service = NormControl2Service()
    
    # Путь к тестовому документу
    file_path = "test_document.pdf"
    
    if not Path(file_path).exists():
        print(f"❌ Файл {file_path} не найден")
        return
    
    try:
        # Выполнение валидации с кастомным ID
        print(f"🔍 Валидация документа: {file_path}")
        result = service.validate_document(file_path, document_id="custom_doc_001")
        
        # Вывод результатов
        print_validation_results(result)
        
        # Дополнительный анализ
        print(f"\n🔬 ДОПОЛНИТЕЛЬНЫЙ АНАЛИЗ")
        print(f"  Время валидации: {result.metadata.get('validation_time_seconds', 0):.2f} сек")
        print(f"  Размер файла: {result.metadata.get('file_size', 0) / 1024 / 1024:.2f} МБ")
        print(f"  Количество страниц: {result.metadata.get('page_count', 0)}")
        
    except Exception as e:
        print(f"❌ Ошибка валидации: {e}")


if __name__ == "__main__":
    print("🚀 ЗАПУСК ПРИМЕРОВ ИСПОЛЬЗОВАНИЯ МОДУЛЯ НОРМОКОНТРОЛЬ - 2")
    print()
    
    # Пример 1: Валидация PDF документа
    example_validate_pdf_document()
    print()
    
    # Пример 2: Валидация DWG документа
    example_validate_dwg_document()
    print()
    
    # Пример 3: Пакетная валидация
    example_batch_validation()
    print()
    
    # Пример 4: Кастомная валидация
    example_custom_validation()
    print()
    
    print("✅ ПРИМЕРЫ ЗАВЕРШЕНЫ")
