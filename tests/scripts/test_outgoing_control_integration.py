#!/usr/bin/env python3
"""
Тестовый скрипт для проверки интеграции spellchecker-service с outgoing-control-service
"""

import requests
import json
import time

# Конфигурация
OUTGOING_CONTROL_URL = "http://localhost:8006"
SPELLCHECKER_URL = "http://localhost:8007"

def test_health_checks():
    """Проверка здоровья сервисов"""
    print("🔍 Проверка здоровья сервисов...")
    
    # Проверяем outgoing-control-service
    try:
        response = requests.get(f"{OUTGOING_CONTROL_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Outgoing Control Service: {data['status']}")
            print(f"📊 Spellchecker Service: {data.get('spellchecker_service', 'unknown')}")
        else:
            print(f"❌ Outgoing Control Service: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Outgoing Control Service: {e}")
    
    # Проверяем spellchecker-service напрямую
    try:
        response = requests.get(f"{SPELLCHECKER_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Spellchecker Service: {data['status']}")
            print(f"🔤 Hunspell: {data.get('hunspell_available', False)}")
            print(f"📝 LanguageTool: {data.get('languagetool_available', False)}")
        else:
            print(f"❌ Spellchecker Service: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Spellchecker Service: {e}")

def test_document_upload():
    """Тест загрузки документа"""
    print("\n🔍 Тестирование загрузки документа...")
    
    test_content = """Привет! Это тестовый документ для проверки интеграции.

В этом документе есть несколько проблем:
- Орфографические ошибки: "ошибкаа" (должно быть "ошибка")
- Грамматические ошибки: "это есть" (избыточность)
- Длинные слова: "супердлинноеслово123"

Проверим, как работает интеграция между сервисами.
"""
    
    try:
        files = {'file': ('test_integration.txt', test_content, 'text/plain')}
        response = requests.post(f"{OUTGOING_CONTROL_URL}/upload", files=files)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Документ загружен: {data['document_id']}")
            return data['document_id']
        else:
            print(f"❌ Ошибка загрузки: {response.status_code}")
            print(f"📝 Ответ: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None

def test_spellcheck_integration(document_id, text):
    """Тест проверки орфографии через интеграцию"""
    print("\n🔍 Тестирование проверки орфографии...")
    
    try:
        data = {
            "document_id": document_id,
            "text": text
        }
        
        response = requests.post(
            f"{OUTGOING_CONTROL_URL}/spellcheck",
            json=data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Проверка орфографии завершена")
            print(f"📊 Метод: {result.get('method', 'unknown')}")
            if 'spell_check_results' in result:
                spell_results = result['spell_check_results']
                print(f"📝 Всего слов: {spell_results.get('total_words', 0)}")
                print(f"❌ Ошибок: {spell_results.get('misspelled_count', 0)}")
                print(f"📈 Точность: {spell_results.get('accuracy', 0):.1f}%")
        else:
            print(f"❌ Ошибка проверки орфографии: {response.status_code}")
            print(f"📝 Ответ: {response.text}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def test_grammar_check_integration(document_id, text):
    """Тест проверки грамматики через интеграцию"""
    print("\n🔍 Тестирование проверки грамматики...")
    
    try:
        data = {
            "document_id": document_id,
            "text": text
        }
        
        response = requests.post(
            f"{OUTGOING_CONTROL_URL}/grammar-check",
            json=data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Проверка грамматики завершена")
            print(f"📊 Метод: {result.get('method', 'unknown')}")
            if 'grammar_results' in result:
                grammar_results = result['grammar_results']
                print(f"❌ Грамматических ошибок: {grammar_results.get('total_errors', 0)}")
                for error in grammar_results.get('errors', [])[:3]:  # Показываем первые 3 ошибки
                    print(f"  - {error.get('message', 'Unknown error')}")
        else:
            print(f"❌ Ошибка проверки грамматики: {response.status_code}")
            print(f"📝 Ответ: {response.text}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def test_comprehensive_check_integration(document_id, text):
    """Тест комплексной проверки через интеграцию"""
    print("\n🔍 Тестирование комплексной проверки...")
    
    try:
        data = {
            "document_id": document_id,
            "text": text
        }
        
        response = requests.post(
            f"{OUTGOING_CONTROL_URL}/comprehensive-check",
            json=data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Комплексная проверка завершена")
            print(f"📊 Метод: {result.get('method', 'unknown')}")
            print(f"⏱️ Время обработки: {result.get('processing_time', 0):.4f}с")
            
            if 'comprehensive_results' in result:
                comp_results = result['comprehensive_results']
                print(f"📝 Всего слов: {comp_results.get('spelling', {}).get('total_words', 0)}")
                print(f"❌ Орфографических ошибок: {comp_results.get('spelling', {}).get('misspelled_count', 0)}")
                print(f"❌ Грамматических ошибок: {comp_results.get('grammar', {}).get('total_errors', 0)}")
                print(f"📈 Общая точность: {comp_results.get('overall_accuracy', 0):.1f}%")
                
                # Показываем найденные ошибки
                all_errors = comp_results.get('all_errors', [])
                if all_errors:
                    print("\n🔍 Найденные ошибки:")
                    for i, error in enumerate(all_errors[:5], 1):  # Показываем первые 5 ошибок
                        print(f"  {i}. {error.get('message', 'Unknown error')}")
                        print(f"     Контекст: {error.get('context', 'N/A')}")
                        if 'replacements' in error and error['replacements']:
                            print(f"     Предложения: {', '.join(error['replacements'][:3])}")
        else:
            print(f"❌ Ошибка комплексной проверки: {response.status_code}")
            print(f"📝 Ответ: {response.text}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def test_spellchecker_status():
    """Тест получения статуса spellchecker-service"""
    print("\n🔍 Тестирование статуса spellchecker-service...")
    
    try:
        response = requests.get(f"{OUTGOING_CONTROL_URL}/spellchecker-status")
        if response.status_code == 200:
            data = response.json()
            print("✅ Статус получен")
            print(f"📊 Статус: {data.get('status', 'unknown')}")
            print(f"🔤 Hunspell: {data.get('hunspell_available', False)}")
            print(f"📝 LanguageTool: {data.get('languagetool_available', False)}")
        else:
            print(f"❌ Ошибка получения статуса: {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def test_spellchecker_stats():
    """Тест получения статистики spellchecker-service"""
    print("\n🔍 Тестирование статистики spellchecker-service...")
    
    try:
        response = requests.get(f"{OUTGOING_CONTROL_URL}/spellchecker-stats")
        if response.status_code == 200:
            data = response.json()
            print("✅ Статистика получена")
            print(f"📊 Данные: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ Ошибка получения статистики: {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    print("🚀 Запуск тестов интеграции spellchecker-service с outgoing-control-service")
    print("=" * 80)
    
    # Проверяем здоровье сервисов
    test_health_checks()
    
    # Загружаем тестовый документ
    document_id = test_document_upload()
    if not document_id:
        print("\n❌ Не удалось загрузить документ, завершаем тестирование")
        exit(1)
    
    # Тестовый текст с ошибками
    test_text = """Привет! Это тестовый документ с ошибками орфографии. 
Слово ошибка написано правильно, но ошибкаа - с ошибкой. 
Это есть избыточность в тексте. 
Также проверим длинные слова: супердлинноеслово123."""
    
    # Запускаем тесты
    test_spellcheck_integration(document_id, test_text)
    test_grammar_check_integration(document_id, test_text)
    test_comprehensive_check_integration(document_id, test_text)
    test_spellchecker_status()
    test_spellchecker_stats()
    
    print("\n✅ Тестирование интеграции завершено!")
