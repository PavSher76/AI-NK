#!/usr/bin/env python3
"""
Тестовый скрипт для проверки турбо режима с GPT-4o-mini
"""

import requests
import json
import os

# Настройки
RAG_SERVICE_URL = "http://localhost:8003"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

def test_turbo_chat():
    """Тестирование чата в турбо режиме"""
    
    if not OPENAI_API_KEY:
        print("❌ OPENAI_API_KEY не установлен")
        print("Установите переменную окружения: export OPENAI_API_KEY=your_key_here")
        return False
    
    print("🧪 Тестирование турбо режима чата...")
    print(f"🔑 API ключ: {OPENAI_API_KEY[:10]}...")
    
    # Тестовое сообщение
    test_message = "Привет! Как дела? Расскажи кратко о нормах проектирования."
    
    payload = {
        "message": test_message,
        "model": "gpt-oss:latest",
        "turbo_mode": True,
        "reasoning_depth": "balanced"
    }
    
    try:
        print(f"📤 Отправляем запрос: {test_message}")
        
        response = requests.post(
            f"{RAG_SERVICE_URL}/chat",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Ответ получен:")
            print(f"📝 Ответ: {result.get('response', '')[:200]}...")
            print(f"🤖 Модель: {result.get('model', 'unknown')}")
            print(f"⚡ Турбо режим: {result.get('turbo_mode', False)}")
            print(f"⏱️ Время генерации: {result.get('generation_time_ms', 0)}ms")
            print(f"🔢 Токенов использовано: {result.get('tokens_used', 0)}")
            return True
        else:
            print(f"❌ Ошибка HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def test_regular_chat():
    """Тестирование обычного чата"""
    
    print("\n🧪 Тестирование обычного режима чата...")
    
    test_message = "Привет! Как дела?"
    
    payload = {
        "message": test_message,
        "model": "gpt-oss:latest",
        "turbo_mode": False,
        "reasoning_depth": "balanced"
    }
    
    try:
        print(f"📤 Отправляем запрос: {test_message}")
        
        response = requests.post(
            f"{RAG_SERVICE_URL}/chat",
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Ответ получен:")
            print(f"📝 Ответ: {result.get('response', '')[:200]}...")
            print(f"🤖 Модель: {result.get('model', 'unknown')}")
            print(f"⚡ Турбо режим: {result.get('turbo_mode', False)}")
            print(f"⏱️ Время генерации: {result.get('generation_time_ms', 0)}ms")
            print(f"🔢 Токенов использовано: {result.get('tokens_used', 0)}")
            return True
        else:
            print(f"❌ Ошибка HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Тестирование чата с ИИ")
    print("=" * 50)
    
    # Проверяем доступность RAG-сервиса
    try:
        health_response = requests.get(f"{RAG_SERVICE_URL}/health", timeout=5)
        if health_response.status_code == 200:
            print("✅ RAG-сервис доступен")
        else:
            print("❌ RAG-сервис недоступен")
            exit(1)
    except Exception as e:
        print(f"❌ Не удается подключиться к RAG-сервису: {e}")
        exit(1)
    
    # Тестируем турбо режим
    turbo_success = test_turbo_chat()
    
    # Тестируем обычный режим
    regular_success = test_regular_chat()
    
    print("\n" + "=" * 50)
    print("📊 Результаты тестирования:")
    print(f"⚡ Турбо режим: {'✅ Работает' if turbo_success else '❌ Не работает'}")
    print(f"🔄 Обычный режим: {'✅ Работает' if regular_success else '❌ Не работает'}")
    
    if turbo_success and regular_success:
        print("🎉 Все тесты прошли успешно!")
    else:
        print("⚠️ Некоторые тесты не прошли")







