#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы SpellChecker Service
"""

import requests
import json
import time

# Конфигурация
API_BASE = "https://localhost:8443/api/spellchecker"
TEST_TEXT = """
Привет! Это тестовый документ для проверки орфографии и грамматики.

В этом тексте есть несколько ошибок:
- орфографические ошибки: "привет" (правильно), "ошибка" (правильно)
- грамматические ошибки: "это есть" (избыточность), "несколько ошибок" (согласование)

Также проверим длинные слова и слова с цифрами: "супердлинноеслово123" и "тест123".

Пунктуация тоже важна: где запятые, где точки, где восклицательные знаки!

Проверим согласование: "красивый дом" и "красивая машина".

Это есть избыточность в тексте.
"""

def test_health():
    """Проверка здоровья сервиса"""
    print("🔍 Проверка здоровья SpellChecker Service...")
    
    try:
        response = requests.get(f"{API_BASE}/health", verify=False)
        if response.status_code == 200:
            data = response.json()
            print("✅ Сервис работает")
            print(f"📊 Статус: {data['status']}")
            print(f"🔤 Hunspell доступен: {data['hunspell_available']}")
            print(f"📝 LanguageTool доступен: {data['languagetool_available']}")
            return True
        else:
            print(f"❌ Сервис недоступен: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

def test_spell_check():
    """Тест проверки орфографии"""
    print("\n🔍 Тестирование проверки орфографии...")
    
    try:
        data = {
            "text": TEST_TEXT,
            "language": "ru",
            "check_spelling": True,
            "check_grammar": False
        }
        
        response = requests.post(
            f"{API_BASE}/spellcheck",
            json=data,
            verify=False,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Проверка орфографии завершена")
            print(f"📊 Результаты: {json.dumps(result, indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ Ошибка проверки орфографии: {response.status_code}")
            print(f"📝 Ответ: {response.text}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def test_grammar_check():
    """Тест проверки грамматики"""
    print("\n🔍 Тестирование проверки грамматики...")
    
    try:
        data = {
            "text": TEST_TEXT,
            "language": "ru",
            "check_spelling": False,
            "check_grammar": True
        }
        
        response = requests.post(
            f"{API_BASE}/grammar-check",
            json=data,
            verify=False,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Проверка грамматики завершена")
            print(f"📊 Результаты: {json.dumps(result, indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ Ошибка проверки грамматики: {response.status_code}")
            print(f"📝 Ответ: {response.text}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def test_comprehensive_check():
    """Тест комплексной проверки"""
    print("\n🔍 Тестирование комплексной проверки...")
    
    try:
        data = {
            "text": TEST_TEXT,
            "language": "ru",
            "check_spelling": True,
            "check_grammar": True
        }
        
        response = requests.post(
            f"{API_BASE}/comprehensive-check",
            json=data,
            verify=False,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Комплексная проверка завершена")
            print(f"📊 Результаты: {json.dumps(result, indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ Ошибка комплексной проверки: {response.status_code}")
            print(f"📝 Ответ: {response.text}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def test_languages():
    """Тест получения поддерживаемых языков"""
    print("\n🔍 Тестирование получения языков...")
    
    try:
        response = requests.get(f"{API_BASE}/languages", verify=False)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Языки получены")
            print(f"📊 Результаты: {json.dumps(result, indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ Ошибка получения языков: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def test_stats():
    """Тест получения статистики"""
    print("\n🔍 Тестирование получения статистики...")
    
    try:
        response = requests.get(f"{API_BASE}/stats", verify=False)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Статистика получена")
            print(f"📊 Результаты: {json.dumps(result, indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ Ошибка получения статистики: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    print("🚀 Запуск тестов SpellChecker Service")
    print("=" * 50)
    
    # Проверяем здоровье сервиса
    if not test_health():
        print("\n❌ Сервис недоступен, завершаем тестирование")
        exit(1)
    
    # Ждем немного, чтобы сервис полностью запустился
    time.sleep(2)
    
    # Запускаем тесты
    test_spell_check()
    test_grammar_check()
    test_comprehensive_check()
    test_languages()
    test_stats()
    
    print("\n✅ Тестирование завершено!")
