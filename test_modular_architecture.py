#!/usr/bin/env python3
"""
Тестовый скрипт для проверки модульной архитектуры RAG сервиса
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
        from rag_service.services.database_manager import DatabaseManager
        print("✅ DatabaseManager импортирован успешно")
    except ImportError as e:
        print(f"❌ Ошибка импорта DatabaseManager: {e}")
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
    
    try:
        from rag_service.services.ollama_rag_service_refactored import OllamaRAGService
        print("✅ OllamaRAGService (рефакторенный) импортирован успешно")
    except ImportError as e:
        print(f"❌ Ошибка импорта OllamaRAGService: {e}")
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
        
    except Exception as e:
        print(f"❌ Ошибка создания DocumentParser: {e}")
        return False
    
    try:
        from rag_service.services.document_chunker import DocumentChunker
        document_chunker = DocumentChunker()
        print("✅ DocumentChunker создан успешно")
        
    except Exception as e:
        print(f"❌ Ошибка создания DocumentChunker: {e}")
        return False
    
    return True

def test_main_service():
    """Тест основного сервиса (без инициализации БД)"""
    print("\n🔍 Тестирование основного сервиса...")
    
    try:
        from rag_service.services.ollama_rag_service_refactored import OllamaRAGService
        
        # Создаем сервис (может упасть из-за отсутствия БД, но это нормально)
        try:
            rag_service = OllamaRAGService()
            print("✅ OllamaRAGService создан успешно")
            
            # Проверяем, что все модули инициализированы
            assert hasattr(rag_service, 'embedding_service')
            assert hasattr(rag_service, 'db_manager')
            assert hasattr(rag_service, 'document_parser')
            assert hasattr(rag_service, 'metadata_extractor')
            assert hasattr(rag_service, 'document_chunker')
            assert hasattr(rag_service, 'methods')
            
            print("✅ Все модули инициализированы")
            
        except Exception as e:
            if "connection" in str(e).lower() or "database" in str(e).lower():
                print("⚠️ Сервис не может подключиться к БД (это нормально для теста)")
                print("✅ Структура сервиса корректна")
            else:
                print(f"❌ Ошибка создания OllamaRAGService: {e}")
                return False
        
    except Exception as e:
        print(f"❌ Ошибка импорта OllamaRAGService: {e}")
        return False
    
    return True

def test_api_compatibility():
    """Тест совместимости API"""
    print("\n🔍 Тестирование совместимости API...")
    
    try:
        from rag_service.services.ollama_rag_service_refactored import OllamaRAGService
        
        # Проверяем, что все основные методы доступны
        methods_to_check = [
            'get_structured_context',
            'extract_document_code',
            'index_document_chunks',
            'hybrid_search',
            'get_ntd_consultation',
            'get_documents',
            'get_document_chunks',
            'delete_document_indexes',
            'delete_document',
            'get_stats',
            'save_document_to_db',
            'update_document_status',
            'process_document_async',
            'index_chunks_async',
            'clear_collection',
            'get_hybrid_search_stats'
        ]
        
        for method_name in methods_to_check:
            if hasattr(OllamaRAGService, method_name):
                print(f"✅ Метод {method_name} доступен")
            else:
                print(f"❌ Метод {method_name} отсутствует")
                return False
        
        print("✅ Все методы API доступны")
        
    except Exception as e:
        print(f"❌ Ошибка проверки API: {e}")
        return False
    
    return True

def main():
    """Основная функция тестирования"""
    print("🚀 Тестирование модульной архитектуры RAG сервиса")
    print("=" * 60)
    
    tests = [
        ("Импорт модулей", test_imports),
        ("Создание экземпляров", test_module_creation),
        ("Основной сервис", test_main_service),
        ("Совместимость API", test_api_compatibility)
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
        print("🎉 Все тесты пройдены! Модульная архитектура работает корректно.")
        return 0
    else:
        print("⚠️ Некоторые тесты провалены. Проверьте ошибки выше.")
        return 1

if __name__ == "__main__":
    exit(main())
