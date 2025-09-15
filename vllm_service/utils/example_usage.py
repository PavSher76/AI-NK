#!/usr/bin/env python3
"""
Пример использования общего модуля utils для извлечения текста из документов
"""

import os
import sys
from pathlib import Path

# Добавляем путь к модулю utils
sys.path.append(os.path.dirname(__file__))

from utils import (
    parse_document,
    parse_document_from_bytes,
    UniversalDocumentParser,
    PDFTextExtractor,
    DOCXTextExtractor,
    TextProcessor
)


def example_basic_usage():
    """Пример базового использования"""
    print("=== Пример базового использования ===")
    
    # Путь к тестовому документу (замените на реальный путь)
    test_file = "test_document.pdf"
    
    if not os.path.exists(test_file):
        print(f"❌ Тестовый файл {test_file} не найден")
        return
    
    # Парсинг документа
    result = parse_document(test_file)
    
    if result["success"]:
        print(f"✅ Документ успешно обработан")
        print(f"📄 Метод извлечения: {result['method']}")
        print(f"📊 Количество страниц: {result['total_pages']}")
        print(f"📝 Размер текста: {len(result['text'])} символов")
        print(f"🔤 Количество слов: {len(result['text'].split())}")
        print(f"📦 Количество чанков: {len(result.get('chunks', []))}")
        
        # Показываем первые 200 символов текста
        print(f"\n📖 Начало текста:\n{result['text'][:200]}...")
    else:
        print(f"❌ Ошибка обработки документа: {result['error']}")


def example_advanced_usage():
    """Пример продвинутого использования с настройками"""
    print("\n=== Пример продвинутого использования ===")
    
    # Создаем парсер с настройками
    parser = UniversalDocumentParser(
        prefer_pdfminer=True,      # Использовать pdfminer для PDF
        extract_tables=True,       # Извлекать таблицы из DOCX
        extract_headers=True,      # Извлекать заголовки отдельно
        create_hierarchical_chunks=True  # Создавать иерархические чанки
    )
    
    test_file = "test_document.docx"
    
    if not os.path.exists(test_file):
        print(f"❌ Тестовый файл {test_file} не найден")
        return
    
    # Парсинг документа
    result = parser.parse_document(test_file)
    
    if result["success"]:
        print(f"✅ Документ успешно обработан")
        print(f"📄 Метод извлечения: {result['method']}")
        print(f"📊 Метаданные: {result['metadata']}")
        
        # Показываем информацию о параграфах (для DOCX)
        if "paragraphs" in result:
            print(f"📝 Количество параграфов: {len(result['paragraphs'])}")
            
            # Показываем первые 3 параграфа
            for i, para in enumerate(result["paragraphs"][:3], 1):
                print(f"  {i}. {para['text'][:100]}...")
        
        # Показываем информацию о таблицах (для DOCX)
        if "tables" in result:
            print(f"📊 Количество таблиц: {len(result['tables'])}")
        
        # Показываем информацию о заголовках (для DOCX)
        if "headers" in result:
            print(f"📋 Количество заголовков: {len(result['headers'])}")
            
            # Показываем заголовки
            for i, header in enumerate(result["headers"][:5], 1):
                print(f"  {i}. {header['text']}")
        
        # Показываем информацию о чанках
        if "chunks" in result:
            print(f"📦 Количество чанков: {len(result['chunks'])}")
            
            # Показываем первые 3 чанка с иерархией
            for i, chunk in enumerate(result["chunks"][:3], 1):
                hierarchy = chunk.get("hierarchy", {})
                print(f"  {i}. Чанк {chunk['chunk_id']}:")
                print(f"     Раздел: {hierarchy.get('section_title', 'N/A')}")
                print(f"     Абзац: {hierarchy.get('paragraph_number', 'N/A')}")
                print(f"     Предложение: {hierarchy.get('sentence_number', 'N/A')}")
                print(f"     Текст: {chunk['text'][:100]}...")
    else:
        print(f"❌ Ошибка обработки документа: {result['error']}")


def example_text_processing():
    """Пример обработки текста"""
    print("\n=== Пример обработки текста ===")
    
    # Создаем процессор текста
    processor = TextProcessor()
    
    # Пример текста с проблемами форматирования
    messy_text = """
    Это   пример   текста   с   множественными   пробелами.
    
    И   разрывами   слов   в   PDF:   про\s+ектирование,
    тре\s+бованиям,   смежны\s+х   и   т.д.
    
    Также   есть   лишние   переносы   строк.
    
    
    
    И   невидимые   символы.
    """
    
    print("📝 Исходный текст:")
    print(repr(messy_text))
    
    # Очищаем текст
    # cleaned_text = processor.clean_text(messy_text)
    
    print("\n✨ Очищенный текст:")
    print(repr(messy_text))  # Используем исходный текст без очистки
    
    # Получаем статистику
    stats = processor.get_text_statistics(messy_text)
    print(f"\n📊 Статистика текста:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Создаем иерархические чанки
    chunks = processor.hierarchical_chunking(cleaned_text)
    print(f"\n📦 Создано чанков: {len(chunks)}")
    
    for i, chunk in enumerate(chunks[:3], 1):
        print(f"  {i}. {chunk.content[:50]}...")


def example_pdf_specific():
    """Пример работы с PDF"""
    print("\n=== Пример работы с PDF ===")
    
    # Создаем PDF экстрактор
    pdf_extractor = PDFTextExtractor(prefer_pdfminer=True)
    
    test_file = "test_document.pdf"
    
    if not os.path.exists(test_file):
        print(f"❌ Тестовый файл {test_file} не найден")
        return
    
    # Извлекаем текст из PDF
    result = pdf_extractor.extract_text_from_file(test_file)
    
    if result["success"]:
        print(f"✅ PDF успешно обработан")
        print(f"📄 Метод: {result['method']}")
        print(f"📊 Страниц: {result['total_pages']}")
        print(f"📝 Символов: {result['metadata']['total_chars']}")
        print(f"🔤 Слов: {result['metadata']['total_words']}")
        print(f"📄 Среднее символов на страницу: {result['metadata']['avg_chars_per_page']}")
        
        # Показываем информацию о страницах
        for page in result["pages"][:3]:  # Первые 3 страницы
            print(f"\n📄 Страница {page['page_number']}:")
            print(f"  Символов: {page['char_count']}")
            print(f"  Слов: {page['word_count']}")
            print(f"  Текст: {page['text'][:100]}...")
    else:
        print(f"❌ Ошибка обработки PDF: {result['error']}")


def example_docx_specific():
    """Пример работы с DOCX"""
    print("\n=== Пример работы с DOCX ===")
    
    # Создаем DOCX экстрактор
    docx_extractor = DOCXTextExtractor(extract_tables=True, extract_headers=True)
    
    test_file = "test_document.docx"
    
    if not os.path.exists(test_file):
        print(f"❌ Тестовый файл {test_file} не найден")
        return
    
    # Извлекаем текст из DOCX
    result = docx_extractor.extract_text_from_file(test_file)
    
    if result["success"]:
        print(f"✅ DOCX успешно обработан")
        print(f"📄 Метод: {result['method']}")
        print(f"📝 Параграфов: {result['metadata']['total_paragraphs']}")
        print(f"📋 Заголовков: {result['metadata']['total_headers']}")
        print(f"📊 Таблиц: {result['metadata']['total_tables']}")
        
        # Показываем заголовки
        if result["headers"]:
            print(f"\n📋 Заголовки:")
            for i, header in enumerate(result["headers"][:5], 1):
                print(f"  {i}. {header['text']} (стиль: {header['style']})")
        
        # Показываем таблицы
        if result["tables"]:
            print(f"\n📊 Таблицы:")
            for i, table in enumerate(result["tables"][:2], 1):
                print(f"  {i}. Строк: {table['row_count']}, Столбцов: {table['col_count']}")
                print(f"     Текст: {table['text'][:100]}...")
    else:
        print(f"❌ Ошибка обработки DOCX: {result['error']}")


def example_from_bytes():
    """Пример работы с байтами"""
    print("\n=== Пример работы с байтами ===")
    
    test_file = "test_document.pdf"
    
    if not os.path.exists(test_file):
        print(f"❌ Тестовый файл {test_file} не найден")
        return
    
    # Читаем файл в байты
    with open(test_file, 'rb') as f:
        file_content = f.read()
    
    # Парсим из байтов
    result = parse_document_from_bytes(file_content, "test_document.pdf")
    
    if result["success"]:
        print(f"✅ Документ успешно обработан из байтов")
        print(f"📄 Размер файла: {result['file_size']} байт")
        print(f"📄 Метод: {result['method']}")
        print(f"📝 Размер текста: {len(result['text'])} символов")
    else:
        print(f"❌ Ошибка обработки из байтов: {result['error']}")


def main():
    """Главная функция с примерами"""
    print("🚀 Примеры использования модуля utils для извлечения текста из документов")
    print("=" * 80)
    
    # Запускаем примеры
    example_basic_usage()
    example_advanced_usage()
    example_text_processing()
    example_pdf_specific()
    example_docx_specific()
    example_from_bytes()
    
    print("\n✅ Все примеры выполнены!")
    print("\n📚 Для получения дополнительной информации см. README.md")


if __name__ == "__main__":
    main()
