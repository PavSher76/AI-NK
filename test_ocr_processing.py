#!/usr/bin/env python3
"""
Тестовый скрипт для проверки OCR обработки документов
"""

import sys
import os
import logging
from pathlib import Path

# Добавляем путь к модулям
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

from utils.document_parser import UniversalDocumentParser
from utils.ocr_processor import OCRProcessor

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_ocr_processing(pdf_path: str):
    """Тестирование OCR обработки PDF документа"""
    try:
        logger.info(f"🔍 [TEST] Начинаем тестирование OCR обработки: {pdf_path}")
        
        # Проверяем существование файла
        if not os.path.exists(pdf_path):
            logger.error(f"❌ [TEST] Файл не найден: {pdf_path}")
            return False
        
        # Создаем парсер с OCR
        parser = UniversalDocumentParser(use_ocr=True)
        
        # Парсим документ
        result = parser.parse_document(pdf_path)
        
        if result.get("success", False):
            logger.info("✅ [TEST] Парсинг документа успешен")
            
            # Выводим основную информацию
            print(f"\n📄 Информация о документе:")
            print(f"   Файл: {result.get('file_name', 'N/A')}")
            print(f"   Размер: {result.get('file_size', 0)} байт")
            print(f"   Страниц: {result.get('total_pages', 0)}")
            print(f"   Метод: {result.get('method', 'N/A')}")
            
            # Выводим информацию о тексте
            text = result.get("text", "")
            print(f"\n📝 Извлеченный текст:")
            print(f"   Длина: {len(text)} символов")
            print(f"   Слов: {len(text.split())}")
            
            # Выводим первые 500 символов
            if text:
                print(f"   Начало текста: {text[:500]}...")
            
            # Выводим информацию о OCR данных
            ocr_data = result.get("ocr_data", {})
            if ocr_data:
                print(f"\n🔍 OCR данные:")
                print(f"   Таблиц найдено: {len(ocr_data.get('tables', []))}")
                print(f"   Чертежей найдено: {len(ocr_data.get('drawings', []))}")
                print(f"   Время обработки: {ocr_data.get('processing_time', 0):.2f} сек")
                
                # Выводим информацию о таблицах
                tables = ocr_data.get("tables", [])
                if tables:
                    print(f"\n📊 Найденные таблицы:")
                    for i, table in enumerate(tables, 1):
                        print(f"   Таблица {i}:")
                        print(f"     Страница: {table.get('page_number', 'N/A')}")
                        print(f"     Площадь: {table.get('area', 0)}")
                        print(f"     Уверенность: {table.get('confidence', 0):.2f}")
                        table_text = table.get('text', '')
                        if table_text:
                            print(f"     Текст: {table_text[:200]}...")
                
                # Выводим информацию о чертежах
                drawings = ocr_data.get("drawings", [])
                if drawings:
                    print(f"\n📐 Найденные чертежи:")
                    for i, drawing in enumerate(drawings, 1):
                        print(f"   Чертеж {i}:")
                        print(f"     Страница: {drawing.get('page_number', 'N/A')}")
                        print(f"     Площадь: {drawing.get('area', 0)}")
                        print(f"     Соотношение сторон: {drawing.get('aspect_ratio', 0):.2f}")
                        print(f"     Уверенность: {drawing.get('confidence', 0):.2f}")
                        drawing_text = drawing.get('text', '')
                        if drawing_text:
                            print(f"     Текст: {drawing_text[:200]}...")
            
            # Выводим информацию о страницах
            pages = result.get("pages", [])
            if pages:
                print(f"\n📄 Информация о страницах:")
                for page in pages[:3]:  # Показываем первые 3 страницы
                    print(f"   Страница {page.get('page_number', 'N/A')}:")
                    print(f"     Символов: {page.get('char_count', 0)}")
                    print(f"     Слов: {page.get('word_count', 0)}")
                    page_text = page.get('text', '')
                    if page_text:
                        print(f"     Начало: {page_text[:100]}...")
            
            return True
            
        else:
            logger.error(f"❌ [TEST] Ошибка парсинга: {result.get('error', 'Неизвестная ошибка')}")
            return False
            
    except Exception as e:
        logger.error(f"❌ [TEST] Ошибка тестирования: {e}")
        return False


def test_ocr_processor_directly(pdf_path: str):
    """Прямое тестирование OCR процессора"""
    try:
        logger.info(f"🔍 [TEST] Прямое тестирование OCR процессора: {pdf_path}")
        
        # Создаем OCR процессор
        ocr_processor = OCRProcessor()
        
        # Обрабатываем PDF
        result = ocr_processor.process_pdf_with_ocr(pdf_path)
        
        if result.get("success", False):
            logger.info("✅ [TEST] OCR обработка успешна")
            
            print(f"\n🔍 Результаты OCR обработки:")
            print(f"   Страниц обработано: {result.get('total_pages', 0)}")
            print(f"   Время обработки: {result.get('processing_time', 0):.2f} сек")
            print(f"   Таблиц найдено: {len(result.get('tables', []))}")
            print(f"   Чертежей найдено: {len(result.get('drawings', []))}")
            
            return True
        else:
            logger.error(f"❌ [TEST] Ошибка OCR обработки: {result.get('error', 'Неизвестная ошибка')}")
            return False
            
    except Exception as e:
        logger.error(f"❌ [TEST] Ошибка прямого тестирования: {e}")
        return False


def main():
    """Основная функция"""
    if len(sys.argv) != 2:
        print("Использование: python test_ocr_processing.py <путь_к_pdf_файлу>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    print("🧪 Тестирование OCR обработки документов")
    print("=" * 50)
    
    # Тест 1: Парсинг с OCR
    print("\n1️⃣ Тестирование парсера с OCR:")
    success1 = test_ocr_processing(pdf_path)
    
    # Тест 2: Прямое тестирование OCR процессора
    print("\n2️⃣ Прямое тестирование OCR процессора:")
    success2 = test_ocr_processor_directly(pdf_path)
    
    # Результаты
    print("\n" + "=" * 50)
    print("📊 Результаты тестирования:")
    print(f"   Парсер с OCR: {'✅ Успешно' if success1 else '❌ Ошибка'}")
    print(f"   OCR процессор: {'✅ Успешно' if success2 else '❌ Ошибка'}")
    
    if success1 and success2:
        print("\n🎉 Все тесты прошли успешно!")
        sys.exit(0)
    else:
        print("\n⚠️ Некоторые тесты не прошли")
        sys.exit(1)


if __name__ == "__main__":
    main()
