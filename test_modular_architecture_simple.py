#!/usr/bin/env python3
"""
Упрощенный тестовый скрипт для проверки модульной архитектуры RAG сервиса
(без подключения к базе данных)
"""

import sys
import os

# Добавляем путь к модулям
sys.path.append(os.path.join(os.path.dirname(__file__), 'rag_service'))

def test_imports():
    """Тест импорта всех модулей"""
    print("🔍 Тестирование импортов модулей...")
    
    try:
        from rag_service.services.embedding_service import OllamaEmbeddingService
        print("✅ OllamaEmbeddingService импортирован успешно")
    except ImportError as e:
        print(f"❌ Ошибка импорта OllamaEmbeddingService: {e}")
        return False
    
    try:
        from rag_service.services.document_parser import DocumentParser
        print("✅ DocumentParser импортирован успешно")
    except ImportError as e:
        print(f"❌ Ошибка импорта DocumentParser: {e}")
        return False
    
    try:
        from rag_service.services.metadata_extractor import MetadataExtractor
        print("✅ MetadataExtractor импортирован успешно")
    except ImportError as e:
        print(f"❌ Ошибка импорта MetadataExtractor: {e}")
        return False
    
    try:
        from rag_service.services.document_chunker import DocumentChunker
        print("✅ DocumentChunker импортирован успешно")
    except ImportError as e:
        print(f"❌ Ошибка импорта DocumentChunker: {e}")
        return False
    
    return True

def test_module_creation():
    """Тест создания экземпляров модулей"""
    print("\n🔍 Тестирование создания экземпляров модулей...")
    
    try:
        from rag_service.services.metadata_extractor import MetadataExtractor
        metadata_extractor = MetadataExtractor()
        print("✅ MetadataExtractor создан успешно")
        
        # Тест извлечения метаданных
        metadata = metadata_extractor.extract_document_metadata("СП 22.13330.2016.pdf", 1)
        print(f"✅ Метаданные извлечены: {metadata['doc_type']} - {metadata['doc_number']}")
        
        # Проверяем правильность извлечения
        assert metadata['doc_type'] == 'SP'
        assert metadata['doc_number'] == '22.13330'
        assert metadata['edition_year'] == 2016
        print("✅ Метаданные корректны")
        
    except Exception as e:
        print(f"❌ Ошибка создания MetadataExtractor: {e}")
        return False
    
    try:
        from rag_service.services.document_parser import DocumentParser
        document_parser = DocumentParser()
        print("✅ DocumentParser создан успешно")
        
        # Тест извлечения кода документа
        code = document_parser.extract_document_code("СП 22.13330.2016.pdf")
        print(f"✅ Код документа извлечен: {code}")
        
        # Проверяем правильность извлечения
        assert code == "СП 22.13330.2016"
        print("✅ Код документа корректен")
        
    except Exception as e:
        print(f"❌ Ошибка создания DocumentParser: {e}")
        return False
    
    try:
        from rag_service.services.document_chunker import DocumentChunker
        document_chunker = DocumentChunker()
        print("✅ DocumentChunker создан успешно")
        
        # Тест создания чанков
        test_text = "Это тестовый текст для проверки чанкинга. " * 50
        chunks = document_chunker.create_chunks(test_text, 1, "test.pdf")
        print(f"✅ Создано {len(chunks)} чанков")
        
        # Проверяем структуру чанков
        if chunks:
            chunk = chunks[0]
            assert 'chunk_id' in chunk
            assert 'content' in chunk
            assert 'document_id' in chunk
            print("✅ Структура чанков корректна")
        
    except Exception as e:
        print(f"❌ Ошибка создания DocumentChunker: {e}")
        return False
    
    return True

def test_metadata_extraction():
    """Тест извлечения метаданных для различных типов документов"""
    print("\n🔍 Тестирование извлечения метаданных...")
    
    try:
        from rag_service.services.metadata_extractor import MetadataExtractor
        metadata_extractor = MetadataExtractor()
        
        test_cases = [
            ("СП 22.13330.2016.pdf", "SP", "22.13330", 2016),
            ("СНиП 2.01.07-85.pdf", "SNiP", "2.01.07", 1985),
            ("ГОСТ 27751-2014.pdf", "GOST", "27751", 2014),
            ("ПБ 03-428-02.pdf", "CORP_STD", "03-428", 2002),
        ]
        
        for filename, expected_type, expected_number, expected_year in test_cases:
            metadata = metadata_extractor.extract_document_metadata(filename, 1)
            
            if metadata['doc_type'] == expected_type:
                print(f"✅ {filename}: тип {metadata['doc_type']} - корректно")
            else:
                print(f"❌ {filename}: ожидался {expected_type}, получен {metadata['doc_type']}")
                return False
            
            if metadata['doc_number'] == expected_number:
                print(f"✅ {filename}: номер {metadata['doc_number']} - корректно")
            else:
                print(f"❌ {filename}: ожидался {expected_number}, получен {metadata['doc_number']}")
                return False
            
            if metadata['edition_year'] == expected_year:
                print(f"✅ {filename}: год {metadata['edition_year']} - корректно")
            else:
                print(f"❌ {filename}: ожидался {expected_year}, получен {metadata['edition_year']}")
                return False
        
        print("✅ Все тесты метаданных пройдены")
        
    except Exception as e:
        print(f"❌ Ошибка тестирования метаданных: {e}")
        return False
    
    return True

def test_document_code_extraction():
    """Тест извлечения кодов документов"""
    print("\n🔍 Тестирование извлечения кодов документов...")
    
    try:
        from rag_service.services.document_parser import DocumentParser
        document_parser = DocumentParser()
        
        test_cases = [
            ("СП 22.13330.2016.pdf", "СП 22.13330.2016"),
            ("СНиП 2.01.07-85.pdf", "СНиП 2.01.07-85"),
            ("ГОСТ 27751-2014.pdf", "ГОСТ 27751-2014"),
            ("ПБ 03-428-02.pdf", "ПБ 03-428-02"),
        ]
        
        for filename, expected_code in test_cases:
            code = document_parser.extract_document_code(filename)
            
            if code == expected_code:
                print(f"✅ {filename}: код {code} - корректно")
            else:
                print(f"❌ {filename}: ожидался {expected_code}, получен {code}")
                return False
        
        print("✅ Все тесты кодов документов пройдены")
        
    except Exception as e:
        print(f"❌ Ошибка тестирования кодов документов: {e}")
        return False
    
    return True

def test_chunking():
    """Тест чанкинга документов"""
    print("\n🔍 Тестирование чанкинга документов...")
    
    try:
        from rag_service.services.document_chunker import DocumentChunker
        document_chunker = DocumentChunker()
        
        # Тест с простым текстом
        simple_text = "Это простой тестовый текст. " * 100
        chunks = document_chunker.create_chunks(simple_text, 1, "test.pdf")
        
        if len(chunks) > 0:
            print(f"✅ Создано {len(chunks)} чанков из простого текста")
            
            # Проверяем структуру первого чанка
            chunk = chunks[0]
            required_fields = ['chunk_id', 'document_id', 'document_title', 'content', 'chunk_type', 'page', 'chapter', 'section']
            
            for field in required_fields:
                if field in chunk:
                    print(f"✅ Поле {field} присутствует")
                else:
                    print(f"❌ Поле {field} отсутствует")
                    return False
        else:
            print("❌ Чанки не созданы")
            return False
        
        # Тест с текстом, содержащим структуру
        structured_text = """
        ГЛАВА 1. ОБЩИЕ ПОЛОЖЕНИЯ
        
        1.1. Настоящий свод правил устанавливает требования к проектированию оснований зданий и сооружений.
        
        1.2. Свод правил распространяется на проектирование оснований зданий и сооружений.
        
        ГЛАВА 2. ОСНОВАНИЯ
        
        2.1. Основания должны обеспечивать прочность и устойчивость зданий и сооружений.
        
        2.2. Основания должны быть спроектированы с учетом геологических условий.
        """ * 50
        
        chunks = document_chunker.create_chunks(structured_text, 2, "structured_test.pdf")
        
        if len(chunks) > 0:
            print(f"✅ Создано {len(chunks)} чанков из структурированного текста")
            
            # Проверяем, что некоторые чанки содержат информацию о главах
            has_chapter_info = any('ГЛАВА' in chunk.get('chapter', '') for chunk in chunks)
            if has_chapter_info:
                print("✅ Информация о главах извлечена")
            else:
                print("⚠️ Информация о главах не извлечена (может быть нормально)")
        else:
            print("❌ Чанки из структурированного текста не созданы")
            return False
        
        print("✅ Все тесты чанкинга пройдены")
        
    except Exception as e:
        print(f"❌ Ошибка тестирования чанкинга: {e}")
        return False
    
    return True

def main():
    """Основная функция тестирования"""
    print("🚀 Упрощенное тестирование модульной архитектуры RAG сервиса")
    print("=" * 70)
    
    tests = [
        ("Импорт модулей", test_imports),
        ("Создание экземпляров", test_module_creation),
        ("Извлечение метаданных", test_metadata_extraction),
        ("Извлечение кодов документов", test_document_code_extraction),
        ("Чанкинг документов", test_chunking)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 50)
        
        try:
            if test_func():
                print(f"✅ {test_name} - ПРОЙДЕН")
                passed += 1
            else:
                print(f"❌ {test_name} - ПРОВАЛЕН")
        except Exception as e:
            print(f"❌ {test_name} - ОШИБКА: {e}")
    
    print("\n" + "=" * 70)
    print(f"📊 Результаты тестирования: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 Все тесты пройдены! Модульная архитектура работает корректно.")
        print("\n📝 Следующие шаги:")
        print("1. Обновите импорты в rag_service/api/endpoints.py")
        print("2. Обновите импорты в rag_service/ollama_main.py")
        print("3. Перезапустите RAG сервис")
        print("4. Протестируйте функциональность в Docker")
        return 0
    else:
        print("⚠️ Некоторые тесты провалены. Проверьте ошибки выше.")
        return 1

if __name__ == "__main__":
    exit(main())
