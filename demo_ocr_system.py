#!/usr/bin/env python3
"""
Демонстрационный скрипт для OCR системы распознавания таблиц и чертежей
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


def demo_ocr_system(pdf_path: str):
    """Демонстрация OCR системы"""
    try:
        print("🔍 Демонстрация OCR системы распознавания таблиц и чертежей")
        print("=" * 60)
        
        # Проверяем существование файла
        if not os.path.exists(pdf_path):
            print(f"❌ Файл не найден: {pdf_path}")
            return False
        
        print(f"📄 Обрабатываем файл: {pdf_path}")
        print()
        
        # 1. Демонстрация стандартного парсера
        print("1️⃣ Стандартный парсер (без OCR):")
        print("-" * 40)
        
        parser_standard = UniversalDocumentParser(use_ocr=False)
        result_standard = parser_standard.parse_document(pdf_path)
        
        if result_standard.get("success", False):
            text_standard = result_standard.get("text", "")
            print(f"✅ Извлечено {len(text_standard)} символов текста")
            print(f"📄 Страниц: {result_standard.get('total_pages', 0)}")
            print(f"🔧 Метод: {result_standard.get('method', 'N/A')}")
            
            # Показываем первые 200 символов
            if text_standard:
                print(f"📝 Начало текста: {text_standard[:200]}...")
        else:
            print(f"❌ Ошибка: {result_standard.get('error', 'Неизвестная ошибка')}")
        
        print()
        
        # 2. Демонстрация парсера с OCR
        print("2️⃣ Парсер с OCR (распознавание таблиц и чертежей):")
        print("-" * 40)
        
        parser_ocr = UniversalDocumentParser(use_ocr=True)
        result_ocr = parser_ocr.parse_document(pdf_path)
        
        if result_ocr.get("success", False):
            text_ocr = result_ocr.get("text", "")
            print(f"✅ Извлечено {len(text_ocr)} символов текста")
            print(f"📄 Страниц: {result_ocr.get('total_pages', 0)}")
            print(f"🔧 Метод: {result_ocr.get('method', 'N/A')}")
            
            # Показываем OCR данные
            ocr_data = result_ocr.get("ocr_data", {})
            if ocr_data:
                print(f"🔍 OCR данные:")
                print(f"   ⏱️ Время обработки: {ocr_data.get('processing_time', 0):.2f} сек")
                print(f"   📊 Таблиц найдено: {len(ocr_data.get('tables', []))}")
                print(f"   📐 Чертежей найдено: {len(ocr_data.get('drawings', []))}")
                
                # Показываем таблицы
                tables = ocr_data.get("tables", [])
                if tables:
                    print(f"\n📊 Найденные таблицы:")
                    for i, table in enumerate(tables, 1):
                        print(f"   Таблица {i}:")
                        print(f"     📄 Страница: {table.get('page_number', 'N/A')}")
                        print(f"     📏 Площадь: {table.get('area', 0)} пикселей")
                        print(f"     🎯 Уверенность: {table.get('confidence', 0):.2f}")
                        table_text = table.get('text', '')
                        if table_text:
                            print(f"     📝 Текст: {table_text[:100]}...")
                
                # Показываем чертежи
                drawings = ocr_data.get("drawings", [])
                if drawings:
                    print(f"\n📐 Найденные чертежи:")
                    for i, drawing in enumerate(drawings, 1):
                        print(f"   Чертеж {i}:")
                        print(f"     📄 Страница: {drawing.get('page_number', 'N/A')}")
                        print(f"     📏 Площадь: {drawing.get('area', 0)} пикселей")
                        print(f"     📐 Соотношение сторон: {drawing.get('aspect_ratio', 0):.2f}")
                        print(f"     🎯 Уверенность: {drawing.get('confidence', 0):.2f}")
                        drawing_text = drawing.get('text', '')
                        if drawing_text:
                            print(f"     📝 Текст: {drawing_text[:100]}...")
            
            # Показываем разницу в тексте
            if text_standard and text_ocr:
                diff = len(text_ocr) - len(text_standard)
                if diff > 0:
                    print(f"\n📈 Улучшение: OCR добавил {diff} символов текста")
                elif diff < 0:
                    print(f"\n📉 Изменение: OCR изменил текст на {abs(diff)} символов")
                else:
                    print(f"\n📊 Текст остался без изменений")
        else:
            print(f"❌ Ошибка: {result_ocr.get('error', 'Неизвестная ошибка')}")
        
        print()
        
        # 3. Демонстрация прямого OCR процессора
        print("3️⃣ Прямой OCR процессор:")
        print("-" * 40)
        
        ocr_processor = OCRProcessor()
        ocr_result = ocr_processor.process_pdf_with_ocr(pdf_path)
        
        if ocr_result.get("success", False):
            print(f"✅ OCR обработка успешна")
            print(f"📄 Страниц обработано: {ocr_result.get('total_pages', 0)}")
            print(f"⏱️ Время обработки: {ocr_result.get('processing_time', 0):.2f} сек")
            print(f"📊 Таблиц найдено: {len(ocr_result.get('tables', []))}")
            print(f"📐 Чертежей найдено: {len(ocr_result.get('drawings', []))}")
            
            # Показываем детали по страницам
            pages = ocr_result.get("pages", [])
            if pages:
                print(f"\n📄 Детали по страницам:")
                for page in pages:
                    page_num = page.get("page_number", "N/A")
                    confidence = page.get("confidence", 0)
                    tables_count = len(page.get("tables", []))
                    drawings_count = len(page.get("drawings", []))
                    print(f"   Страница {page_num}: уверенность {confidence:.2f}, таблиц {tables_count}, чертежей {drawings_count}")
        else:
            print(f"❌ Ошибка OCR: {ocr_result.get('error', 'Неизвестная ошибка')}")
        
        print()
        print("=" * 60)
        print("🎉 Демонстрация завершена!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка демонстрации: {e}")
        return False


def main():
    """Основная функция"""
    if len(sys.argv) != 2:
        print("Использование: python demo_ocr_system.py <путь_к_pdf_файлу>")
        print("\nПримеры:")
        print("  python demo_ocr_system.py test_new_document.pdf")
        print("  python demo_ocr_system.py /path/to/document.pdf")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    success = demo_ocr_system(pdf_path)
    
    if success:
        print("\n✅ Демонстрация прошла успешно!")
        sys.exit(0)
    else:
        print("\n❌ Демонстрация завершилась с ошибками")
        sys.exit(1)


if __name__ == "__main__":
    main()
