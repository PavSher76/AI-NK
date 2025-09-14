#!/usr/bin/env python3
"""
Тестовый скрипт для проверки всех сервисов AI-NK
"""

import requests
import json
from datetime import datetime

def test_service(url, name):
    """Тестирование сервиса"""
    try:
        response = requests.get(f"{url}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            status = data.get('status', 'unknown')
            print(f"✅ {name}: {status}")
            return True
        else:
            print(f"❌ {name}: HTTP {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ {name}: недоступен - {e}")
        return False

def test_ollama():
    """Тестирование Ollama"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            models_count = len(data.get('models', []))
            print(f"✅ Ollama: доступен, {models_count} моделей")
            return True
        else:
            print(f"❌ Ollama: HTTP {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Ollama: недоступен - {e}")
        return False

def test_endpoints(url, name):
    """Тестирование эндпоинтов сервиса"""
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            endpoints = data.get('endpoints', {})
            print(f"📋 {name} эндпоинты: {len(endpoints)} доступно")
            return True
        else:
            print(f"❌ {name} эндпоинты: HTTP {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ {name} эндпоинты: недоступен - {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("🚀 Тестирование всех сервисов AI-NK")
    print("=" * 50)
    
    # Тестируем Ollama
    test_ollama()
    print()
    
    # Тестируем основные сервисы
    services = [
        ("http://localhost:8002", "Основной RAG Service"),
        ("http://localhost:8003", "Ollama RAG Service"),
        ("http://localhost:8005", "VLLM + Ollama Service")
    ]
    
    working_services = 0
    for url, name in services:
        if test_service(url, name):
            working_services += 1
        print()
    
    # Тестируем эндпоинты
    print("📋 Проверка эндпоинтов:")
    print("-" * 30)
    for url, name in services:
        test_endpoints(url, name)
    
    print()
    print("=" * 50)
    print(f"📊 Итоговый статус: {working_services}/3 сервисов работают")
    
    if working_services == 3:
        print("🎉 Все сервисы работают корректно!")
    elif working_services >= 2:
        print("⚠️  Большинство сервисов работают")
    else:
        print("❌ Много сервисов не работают")
    
    print(f"⏰ Время проверки: {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    main()
