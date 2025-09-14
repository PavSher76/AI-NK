#!/usr/bin/env python3
"""
Тестовый скрипт для проверки гранулярного чанкования документов
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'rag_service'))

from services.ollama_rag_service import OllamaRAGService
from config.chunking_config import get_chunking_config, validate_chunking_config

def test_chunking_config():
    """Тестирование конфигурации чанкования"""
    print("🔧 Тестирование конфигурации чанкования...")
    
    # Тестируем базовую конфигурацию
    config = get_chunking_config('default')
    print(f"✅ Базовая конфигурация: {config['target_tokens']} токенов, перекрытие {config['overlap_ratio']}")
    
    # Тестируем конфигурацию для ГОСТ
    gost_config = get_chunking_config('gost')
    print(f"✅ ГОСТ конфигурация: {gost_config['target_tokens']} токенов, перекрытие {gost_config['overlap_ratio']}")
    
    # Валидируем конфигурации
    print(f"✅ Валидация базовой конфигурации: {validate_chunking_config(config)}")
    print(f"✅ Валидация ГОСТ конфигурации: {validate_chunking_config(gost_config)}")
    
    return True

def test_granular_chunking():
    """Тестирование гранулярного чанкования"""
    print("\n📝 Тестирование гранулярного чанкования...")
    
    try:
        # Создаем экземпляр RAG сервиса
        rag_service = OllamaRAGService()
        
        # Тестовый текст нормативного документа
        test_text = """
        Страница 1 из 3
        
        СП 22.13330.2016 "Основания зданий и сооружений"
        
        Глава 1. Общие положения
        
        1.1. Настоящий свод правил устанавливает требования к проектированию оснований зданий и сооружений.
        
        1.2. Основания должны обеспечивать надежность и долговечность зданий и сооружений.
        
        1.3. При проектировании оснований следует учитывать:
        - инженерно-геологические условия;
        - конструктивные особенности зданий;
        - технологические требования.
        
        Глава 2. Инженерно-геологические изыскания
        
        2.1. Инженерно-геологические изыскания должны выполняться в соответствии с требованиями СП 47.13330.
        
        2.2. Объем изысканий определяется сложностью инженерно-геологических условий.
        
        Страница 2 из 3
        
        Глава 3. Расчет оснований
        
        3.1. Расчет оснований выполняется по предельным состояниям.
        
        3.2. При расчете учитываются:
        - нагрузки от зданий и сооружений;
        - собственный вес грунтов;
        - гидродинамические воздействия.
        
        3.3. Коэффициент надежности по нагрузке принимается не менее 1,2.
        
        Глава 4. Конструктивные решения
        
        4.1. Конструктивные решения оснований должны обеспечивать:
        - равномерность осадок;
        - устойчивость откосов;
        - защиту от подтопления.
        
        Страница 3 из 3
        
        4.2. При устройстве фундаментов следует предусматривать:
        - гидроизоляцию;
        - дренаж;
        - вентиляцию подполий.
        
        4.3. Материалы фундаментов должны соответствовать требованиям по прочности и долговечности.
        """
        
        print(f"📄 Тестовый текст: {len(test_text)} символов")
        
        # Тестируем создание чанков
        chunks = rag_service._split_page_into_chunks(test_text, 1000)
        
        print(f"✅ Создано {len(chunks)} чанков:")
        
        for i, chunk in enumerate(chunks):
            estimated_tokens = rag_service._estimate_tokens(chunk, get_chunking_config('default'))
            print(f"  Чанк {i+1}: {len(chunk)} символов, ~{estimated_tokens} токенов")
            print(f"    Содержание: {chunk[:100]}...")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании чанкования: {e}")
        return False

def test_sentence_splitting():
    """Тестирование разбиения на предложения"""
    print("\n🔤 Тестирование разбиения на предложения...")
    
    try:
        rag_service = OllamaRAGService()
        config = get_chunking_config('default')
        
        test_text = "Это первое предложение. Это второе предложение с номером 1.2. Третье предложение начинается с заголовка. Четвертое предложение."
        
        sentences = rag_service._split_into_sentences(test_text, config)
        
        print(f"✅ Разбито на {len(sentences)} предложений:")
        for i, sentence in enumerate(sentences):
            print(f"  {i+1}. {sentence}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при разбиении на предложения: {e}")
        return False

def test_token_estimation():
    """Тестирование оценки токенов"""
    print("\n🔢 Тестирование оценки токенов...")
    
    try:
        rag_service = OllamaRAGService()
        config = get_chunking_config('default')
        
        test_texts = [
            "Короткий текст",
            "Это предложение средней длины для тестирования оценки токенов.",
            "Длинное предложение с множеством слов для проверки корректности работы алгоритма оценки количества токенов в тексте нормативных документов."
        ]
        
        for text in test_texts:
            tokens = rag_service._estimate_tokens(text, config)
            print(f"  '{text[:30]}...': ~{tokens} токенов")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при оценке токенов: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("🧪 Тестирование гранулярного чанкования документов")
    print("=" * 60)
    
    tests = [
        ("Конфигурация чанкования", test_chunking_config),
        ("Разбиение на предложения", test_sentence_splitting),
        ("Оценка токенов", test_token_estimation),
        ("Гранулярное чанкование", test_granular_chunking),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Критическая ошибка в тесте '{test_name}': {e}")
            results.append((test_name, False))
    
    # Выводим результаты
    print("\n" + "=" * 60)
    print("📊 Результаты тестирования:")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Итого: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 Все тесты пройдены успешно!")
        return 0
    else:
        print("⚠️ Некоторые тесты не пройдены")
        return 1

if __name__ == "__main__":
    sys.exit(main())
