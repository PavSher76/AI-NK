#!/usr/bin/env python3
"""
Тест отдельных модулей без зависимостей от базы данных
"""

import sys
import os

# Добавляем путь к модулям
sys.path.append(os.path.join(os.path.dirname(__file__), 'rag_service'))

def test_metadata_extractor():
    """Тест модуля извлечения метаданных"""
    print("🔍 Тестирование MetadataExtractor...")
    
    try:
        from rag_service.services.metadata_extractor import MetadataExtractor
        metadata_extractor = MetadataExtractor()
        print("✅ MetadataExtractor создан успешно")
        
        # Тест извлечения метаданных
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
        
        print("✅ Все тесты MetadataExtractor пройдены")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования MetadataExtractor: {e}")
        return False

def test_document_parser():
    """Тест модуля парсинга документов"""
    print("\n🔍 Тестирование DocumentParser...")
    
    try:
        from rag_service.services.document_parser import DocumentParser
        document_parser = DocumentParser()
        print("✅ DocumentParser создан успешно")
        
        # Тест извлечения кодов документов
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
        
        # Тест извлечения кодов из запросов
        query_test_cases = [
            ("Что такое СП 22.13330.2016?", "СП 22.13330.2016"),
            ("Расскажи про СНиП 2.01.07-85", "СНиП 2.01.07-85"),
            ("ГОСТ 27751-2014 что это?", "ГОСТ 27751-2014"),
        ]
        
        for query, expected_code in query_test_cases:
            code = document_parser.extract_document_code_from_query(query)
            
            if code == expected_code:
                print(f"✅ Запрос '{query}': код {code} - корректно")
            else:
                print(f"❌ Запрос '{query}': ожидался {expected_code}, получен {code}")
                return False
        
        print("✅ Все тесты DocumentParser пройдены")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования DocumentParser: {e}")
        return False

def test_document_chunker():
    """Тест модуля чанкинга документов"""
    print("\n🔍 Тестирование DocumentChunker...")
    
    try:
        from rag_service.services.document_chunker import DocumentChunker
        document_chunker = DocumentChunker()
        print("✅ DocumentChunker создан успешно")
        
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
        
        print("✅ Все тесты DocumentChunker пройдены")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования DocumentChunker: {e}")
        return False

def test_embedding_service():
    """Тест модуля эмбеддингов (без подключения к Ollama)"""
    print("\n🔍 Тестирование OllamaEmbeddingService...")
    
    try:
        from rag_service.services.embedding_service import OllamaEmbeddingService
        embedding_service = OllamaEmbeddingService()
        print("✅ OllamaEmbeddingService создан успешно")
        
        # Проверяем, что сервис инициализирован
        assert hasattr(embedding_service, 'ollama_url')
        assert hasattr(embedding_service, 'model_name')
        assert embedding_service.model_name == "bge-m3"
        print("✅ Параметры сервиса корректны")
        
        print("✅ Все тесты OllamaEmbeddingService пройдены")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования OllamaEmbeddingService: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("🚀 Тестирование отдельных модулей RAG сервиса")
    print("=" * 60)
    
    tests = [
        ("MetadataExtractor", test_metadata_extractor),
        ("DocumentParser", test_document_parser),
        ("DocumentChunker", test_document_chunker),
        ("OllamaEmbeddingService", test_embedding_service),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 40)
        
        try:
            if test_func():
                print(f"✅ {test_name} - ПРОЙДЕН")
                passed += 1
            else:
                print(f"❌ {test_name} - ПРОВАЛЕН")
        except Exception as e:
            print(f"❌ {test_name} - ОШИБКА: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Результаты тестирования: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 Все тесты пройдены! Отдельные модули работают корректно.")
        print("\n📝 Следующие шаги:")
        print("1. Модули готовы к использованию")
        print("2. Обновите импорты в основных файлах")
        print("3. Протестируйте в Docker среде")
        return 0
    else:
        print("⚠️ Некоторые тесты провалены. Проверьте ошибки выше.")
        return 1

if __name__ == "__main__":
    exit(main())
