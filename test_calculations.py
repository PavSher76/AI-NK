#!/usr/bin/env python3
"""
Тест расчетного модуля AI-НК
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'calculation_service'))

def test_calculation_engine():
    """Тест расчетного движка"""
    try:
        # Импортируем только расчетный движок без базы данных
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'calculation_service'))
        from calculations import CalculationEngine
        
        print("✅ Расчетный движок загружен успешно")
        
        # Создаем экземпляр движка
        engine = CalculationEngine()
        
        print("✅ Экземпляр движка создан")
        
        # Получаем список типов расчетов
        calculation_types = engine.get_calculation_types()
        print(f"✅ Найдено типов расчетов: {len(calculation_types)}")
        
        # Выводим список типов расчетов
        for calc_type_info in calculation_types:
            print(f"  📊 {calc_type_info.type}: {calc_type_info.name}")
            print(f"     Описание: {calc_type_info.description}")
            if calc_type_info.categories:
                print(f"     Категории: {', '.join(calc_type_info.categories)}")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании расчетного движка: {e}")
        return False

def test_normative_documents():
    """Тест нормативных документов"""
    try:
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'calculation_service'))
        from calculations import CalculationEngine
        engine = CalculationEngine()
        
        print("📋 ПРОВЕРКА НОРМАТИВНЫХ ДОКУМЕНТОВ:")
        print("=" * 50)
        
        # Получаем схемы параметров для каждого типа расчета
        for calc_type_info in engine.get_calculation_types():
            try:
                schema = engine._get_parameters_schema(calc_type_info.type)
                if 'normative_document' in schema.get('properties', {}):
                    default_norm = schema['properties']['normative_document'].get('default', 'Не указан')
                    print(f"  {calc_type_info.type}: {default_norm}")
            except Exception as e:
                print(f"  {calc_type_info.type}: Ошибка получения схемы - {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при проверке нормативных документов: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("🧪 ТЕСТИРОВАНИЕ РАСЧЕТНОГО МОДУЛЯ AI-НК")
    print("=" * 50)
    
    # Тест 1: Расчетный движок
    print("\n1️⃣ Тест расчетного движка:")
    test1_result = test_calculation_engine()
    
    # Тест 2: Нормативные документы
    print("\n2️⃣ Тест нормативных документов:")
    test2_result = test_normative_documents()
    
    # Итоги
    print("\n" + "=" * 50)
    print("📊 ИТОГИ ТЕСТИРОВАНИЯ:")
    print(f"  Расчетный движок: {'✅ ПРОЙДЕН' if test1_result else '❌ ПРОВАЛЕН'}")
    print(f"  Нормативные документы: {'✅ ПРОЙДЕН' if test2_result else '❌ ПРОВАЛЕН'}")
    
    if test1_result and test2_result:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        return 0
    else:
        print("\n⚠️  НЕКОТОРЫЕ ТЕСТЫ ПРОВАЛЕНЫ")
        return 1

if __name__ == "__main__":
    sys.exit(main())
