#!/usr/bin/env python3
"""
Тестовый скрипт для проверки установки gpt-oss
"""

import sys
import os

def test_imports():
    """Тест импорта модулей gpt-oss"""
    try:
        import gpt_oss
        print("✅ gpt_oss импортирован успешно")
        
        # Проверка доступных модулей
        modules = ['torch', 'metal', 'tools']
        for module in modules:
            try:
                __import__(f'gpt_oss.{module}')
                print(f"✅ gpt_oss.{module} доступен")
            except ImportError as e:
                print(f"⚠️  gpt_oss.{module} недоступен: {e}")
        
        return True
    except ImportError as e:
        print(f"❌ Ошибка импорта gpt_oss: {e}")
        return False

def test_metal_backend():
    """Тест Metal бэкенда"""
    try:
        import gpt_oss.metal
        print("✅ Metal бэкенд доступен")
        
        # Проверка наличия примеров
        try:
            from gpt_oss.metal.examples import generate
            print("✅ Metal примеры доступны")
        except ImportError as e:
            print(f"⚠️  Metal примеры недоступны: {e}")
        
        return True
    except ImportError as e:
        print(f"❌ Metal бэкенд недоступен: {e}")
        return False

def main():
    print("🧪 Тестирование установки gpt-oss")
    print("=" * 40)
    
    # Тест импортов
    imports_ok = test_imports()
    
    # Тест Metal бэкенда
    metal_ok = test_metal_backend()
    
    print("\n" + "=" * 40)
    if imports_ok and metal_ok:
        print("🎉 Все тесты пройдены! gpt-oss установлен корректно")
        print("\n📋 Следующие шаги:")
        print("1. Запустите: ./download_gpt_oss_model.sh")
        print("2. Активируйте окружение: source activate_gpt_oss.sh")
        print("3. Запустите модель: python gpt_oss/metal/examples/generate.py <путь_к_модели> -p 'ваш_вопрос'")
    else:
        print("❌ Некоторые тесты не пройдены")
        sys.exit(1)

if __name__ == "__main__":
    main()
