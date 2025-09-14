#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы Hunspell + LanguageTool
"""

import requests
import json
import time

# Конфигурация
API_BASE = "http://localhost:8443/api/outgoing-control"
TEST_TEXT = """
Привет! Это тестовый документ для проверки орфографии и грамматики.

В этом тексте есть несколько ошибок:
- орфографические ошибки: "привет" (правильно), "ошибка" (правильно)
- грамматические ошибки: "это есть" (избыточность), "несколько ошибок" (согласование)

Также проверим длинные слова и слова с цифрами: "супердлинноеслово123" и "тест123".

Пунктуация тоже важна: где запятые, где точки, где восклицательные знаки!

Проверим согласование: "красивый дом" и "красивая машина".
"""

def test_spell_check():
    """Тест проверки орфографии"""
    print("🔍 Тестирование проверки орфографии...")
    
    # Загружаем тестовый документ в outgoing control service
    files = {'file': ('test.txt', TEST_TEXT, 'text/plain')}
    upload_response = requests.post(f"http://localhost:8006/upload", files=files)
    
    if upload_response.status_code != 200:
        print(f"❌ Ошибка загрузки документа: {upload_response.text}")
        return
    
    document_data = upload_response.json()
    document_id = document_data["document_id"]
    print(f"✅ Документ загружен: {document_id}")
    
    # Проверяем орфографию
    spell_check_data = {
        "document_id": document_id,
        "text": TEST_TEXT
    }
    
    spell_response = requests.post(
        f"{API_BASE}/spellcheck",
        json=spell_check_data,
        headers={'Content-Type': 'application/json'}
    )
    
    if spell_response.status_code == 200:
        result = spell_response.json()
        print("✅ Проверка орфографии завершена")
        print(f"📊 Результаты: {json.dumps(result['spell_check_results'], indent=2, ensure_ascii=False)}")
    else:
        print(f"❌ Ошибка проверки орфографии: {spell_response.text}")

def test_grammar_check():
    """Тест проверки грамматики"""
    print("\n🔍 Тестирование проверки грамматики...")
    
    # Загружаем тестовый документ
    files = {'file': ('test.txt', TEST_TEXT, 'text/plain')}
    upload_response = requests.post(f"http://localhost:8006/upload", files=files)
    
    if upload_response.status_code != 200:
        print(f"❌ Ошибка загрузки документа: {upload_response.text}")
        return
    
    document_data = upload_response.json()
    document_id = document_data["document_id"]
    
    # Проверяем грамматику
    grammar_data = {
        "document_id": document_id,
        "text": TEST_TEXT
    }
    
    grammar_response = requests.post(
        f"{API_BASE}/grammar-check",
        json=grammar_data,
        headers={'Content-Type': 'application/json'}
    )
    
    if grammar_response.status_code == 200:
        result = grammar_response.json()
        print("✅ Проверка грамматики завершена")
        print(f"📊 Результаты: {json.dumps(result['grammar_results'], indent=2, ensure_ascii=False)}")
    else:
        print(f"❌ Ошибка проверки грамматики: {grammar_response.text}")

def test_comprehensive_check():
    """Тест комплексной проверки"""
    print("\n🔍 Тестирование комплексной проверки...")
    
    # Загружаем тестовый документ
    files = {'file': ('test.txt', TEST_TEXT, 'text/plain')}
    upload_response = requests.post(f"http://localhost:8006/upload", files=files)
    
    if upload_response.status_code != 200:
        print(f"❌ Ошибка загрузки документа: {upload_response.text}")
        return
    
    document_data = upload_response.json()
    document_id = document_data["document_id"]
    
    # Комплексная проверка
    comprehensive_data = {
        "document_id": document_id,
        "text": TEST_TEXT
    }
    
    comprehensive_response = requests.post(
        f"{API_BASE}/comprehensive-check",
        json=comprehensive_data,
        headers={'Content-Type': 'application/json'}
    )
    
    if comprehensive_response.status_code == 200:
        result = comprehensive_response.json()
        print("✅ Комплексная проверка завершена")
        print(f"📊 Результаты: {json.dumps(result['comprehensive_results'], indent=2, ensure_ascii=False)}")
    else:
        print(f"❌ Ошибка комплексной проверки: {comprehensive_response.text}")

def test_health():
    """Проверка здоровья сервиса"""
    print("🔍 Проверка здоровья сервиса...")
    
    try:
        response = requests.get(f"{API_BASE}/health")
        if response.status_code == 200:
            print("✅ Сервис работает")
            print(f"📊 Статус: {response.json()}")
        else:
            print(f"❌ Сервис недоступен: {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")

if __name__ == "__main__":
    print("🚀 Запуск тестов Hunspell + LanguageTool")
    print("=" * 50)
    
    # Проверяем здоровье сервиса
    test_health()
    
    # Ждем немного, чтобы сервис запустился
    time.sleep(2)
    
    # Запускаем тесты
    test_spell_check()
    test_grammar_check()
    test_comprehensive_check()
    
    print("\n✅ Тестирование завершено!")
