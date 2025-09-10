#!/usr/bin/env python3
"""
Тест функций без импорта классов
"""

import sys
import os
import re

# Добавляем путь к модулям
sys.path.append(os.path.join(os.path.dirname(__file__), 'rag_service'))

def test_metadata_extraction_functions():
    """Тест функций извлечения метаданных"""
    print("🔍 Тестирование функций извлечения метаданных...")
    
    try:
        # Импортируем только функции, а не классы
        import importlib.util
        
        # Загружаем модуль metadata_extractor
        spec = importlib.util.spec_from_file_location(
            "metadata_extractor", 
            "/Users/macbook/Projects/AI/AIReviewer/AI-NK/rag_service/services/metadata_extractor.py"
        )
        metadata_module = importlib.util.module_from_spec(spec)
        
        # Выполняем код модуля
        with open("/Users/macbook/Projects/AI/AIReviewer/AI-NK/rag_service/services/metadata_extractor.py", "r") as f:
            code = f.read()
        
        # Заменяем импорты на заглушки
        code = code.replace("import logging", "# import logging")
        code = code.replace("import re", "# import re")
        code = code.replace("import hashlib", "# import hashlib")
        code = code.replace("from datetime import datetime", "# from datetime import datetime")
        code = code.replace("from typing import Dict, Any, List, Tuple", "# from typing import Dict, Any, List, Tuple")
        
        # Добавляем заглушки
        code = """
import logging
import re
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Tuple

""" + code
        
        # Выполняем код
        exec(code, globals())
        
        # Создаем экземпляр класса
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
        
        print("✅ Все тесты функций извлечения метаданных пройдены")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования функций извлечения метаданных: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_document_parsing_functions():
    """Тест функций парсинга документов"""
    print("\n🔍 Тестирование функций парсинга документов...")
    
    try:
        # Загружаем модуль document_parser
        with open("/Users/macbook/Projects/AI/AIReviewer/AI-NK/rag_service/services/document_parser.py", "r") as f:
            code = f.read()
        
        # Заменяем импорты на заглушки
        code = code.replace("import logging", "# import logging")
        code = code.replace("import os", "# import os")
        code = code.replace("import tempfile", "# import tempfile")
        code = code.replace("from typing import Optional", "# from typing import Optional")
        
        # Добавляем заглушки
        code = """
import logging
import os
import tempfile
from typing import Optional

""" + code
        
        # Выполняем код
        exec(code, globals())
        
        # Создаем экземпляр класса
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
        
        print("✅ Все тесты функций парсинга документов пройдены")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования функций парсинга документов: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_regex_patterns():
    """Тест регулярных выражений для парсинга документов"""
    print("\n🔍 Тестирование регулярных выражений...")
    
    try:
        # Паттерны для различных типов документов
        patterns = [
            # ГОСТ
            (r'ГОСТ\s+(\d+(?:\.\d+)*)-(\d{4})', 'GOST'),
            (r'ГОСТ\s+(\d+(?:\.\d+)*)', 'GOST'),
            
            # СП (Свод правил)
            (r'СП\s+(\d+(?:\.\d+)*)\.(\d{4})', 'SP'),
            (r'СП\s+(\d+(?:\.\d+)*)', 'SP'),
            
            # СНиП
            (r'СНиП\s+(\d+(?:\.\d+)*)-(\d{4})', 'SNiP'),
            (r'СНиП\s+(\d+(?:\.\d+)*)\.(\d{4})', 'SNiP'),
            (r'СНиП\s+(\d+(?:\.\d+)*)-(\d{2})(?:\.|$)', 'SNiP'),
            (r'СНиП\s+(\d+(?:\.\d+)*)', 'SNiP'),
            
            # ФНП
            (r'ФНП\s+(\d+(?:\.\d+)*)-(\d{4})', 'FNP'),
            (r'ФНП\s+(\d+(?:\.\d+)*)', 'FNP'),
            
            # ПБ (Правила безопасности)
            (r'ПБ\s+(\d+(?:\.\d+)*)-(\d{4})', 'CORP_STD'),
            (r'ПБ\s+(\d+(?:\.\d+)*)', 'CORP_STD'),
            
            # А (Альбом)
            (r'А(\d+(?:\.\d+)*)\.(\d{4})', 'CORP_STD'),
            (r'А(\d+(?:\.\d+)*)', 'CORP_STD'),
        ]
        
        test_cases = [
            ("СП 22.13330.2016.pdf", "SP", "22.13330", "2016"),
            ("СНиП 2.01.07-85.pdf", "SNiP", "2.01.07", "85"),
            ("ГОСТ 27751-2014.pdf", "GOST", "27751", "2014"),
            ("ПБ 03-428-02.pdf", "CORP_STD", "03-428", "02"),
        ]
        
        for filename, expected_type, expected_number, expected_year in test_cases:
            # Убираем расширение файла
            name = filename.replace('.pdf', '').replace('.docx', '').replace('.doc', '')
            
            found = False
            for pattern, doc_type in patterns:
                match = re.search(pattern, name, re.IGNORECASE)
                if match:
                    groups = match.groups()
                    if len(groups) == 2:
                        doc_number = groups[0]
                        year_str = groups[1]
                        
                        if doc_type == expected_type and doc_number == expected_number and year_str == expected_year:
                            print(f"✅ {filename}: {doc_type} {doc_number} {year_str} - корректно")
                            found = True
                            break
            
            if not found:
                print(f"❌ {filename}: не найден подходящий паттерн")
                return False
        
        print("✅ Все тесты регулярных выражений пройдены")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования регулярных выражений: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("🚀 Тестирование функций модулей RAG сервиса")
    print("=" * 60)
    
    tests = [
        ("Регулярные выражения", test_regex_patterns),
        ("Функции парсинга документов", test_document_parsing_functions),
        ("Функции извлечения метаданных", test_metadata_extraction_functions),
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
        print("🎉 Все тесты пройдены! Функции модулей работают корректно.")
        print("\n📝 Заключение:")
        print("1. Модули созданы успешно")
        print("2. Функции работают корректно")
        print("3. Готовы к использованию в Docker среде")
        return 0
    else:
        print("⚠️ Некоторые тесты провалены. Проверьте ошибки выше.")
        return 1

if __name__ == "__main__":
    exit(main())
