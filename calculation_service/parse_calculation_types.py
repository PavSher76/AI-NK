#!/usr/bin/env python3
"""
Скрипт для парсинга Excel файла с видами расчетов строительных конструкций
"""

import pandas as pd
import json
import os
from typing import List, Dict, Any

def parse_structural_calculations():
    """Парсинг видов расчетов строительных конструкций из Excel файла"""
    
    # Путь к файлу
    file_path = "Docs_templates/Виды_расчетов_строительных_конструкций_с_вводом.xlsx"
    
    if not os.path.exists(file_path):
        print(f"❌ Файл не найден: {file_path}")
        return []
    
    try:
        # Читаем Excel файл
        print(f"📖 Читаем файл: {file_path}")
        
        # Пробуем прочитать все листы
        excel_file = pd.ExcelFile(file_path)
        print(f"📊 Найдены листы: {excel_file.sheet_names}")
        
        calculation_types = []
        
        for sheet_name in excel_file.sheet_names:
            print(f"\n📋 Обрабатываем лист: {sheet_name}")
            
            # Читаем лист
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            print(f"📊 Размер данных: {df.shape}")
            print(f"📊 Колонки: {list(df.columns)}")
            
            # Показываем первые несколько строк
            print(f"📊 Первые строки:")
            print(df.head())
            
            # Парсим данные в зависимости от структуры
            if not df.empty:
                # Ищем колонки с названиями расчетов
                name_columns = [col for col in df.columns if any(keyword in str(col).lower() 
                                                               for keyword in ['название', 'вид', 'тип', 'расчет'])]
                
                if name_columns:
                    print(f"✅ Найдены колонки с названиями: {name_columns}")
                    
                    for idx, row in df.iterrows():
                        # Ищем непустые значения в колонках с названиями
                        for col in name_columns:
                            value = row[col]
                            if pd.notna(value) and str(value).strip():
                                calculation_type = {
                                    "id": f"structural_{sheet_name}_{idx}",
                                    "name": str(value).strip(),
                                    "category": "construction",
                                    "subcategory": sheet_name,
                                    "description": f"Расчет {str(value).strip()}",
                                    "norms": ["СП 20.13330.2016", "СП 16.13330.2017", "СП 63.13330.2018"],
                                    "icon": "🏗️",
                                    "parameters": {},
                                    "formula": "",
                                    "units": {}
                                }
                                
                                # Ищем дополнительные параметры в других колонках
                                for col_name in df.columns:
                                    if col_name != col and pd.notna(row[col_name]):
                                        param_value = row[col_name]
                                        if isinstance(param_value, (int, float, str)):
                                            calculation_type["parameters"][str(col_name)] = param_value
                                
                                calculation_types.append(calculation_type)
                                print(f"✅ Добавлен расчет: {calculation_type['name']}")
                
                else:
                    # Если не нашли специальные колонки, берем первую колонку
                    first_col = df.columns[0]
                    print(f"⚠️ Используем первую колонку: {first_col}")
                    
                    for idx, row in df.iterrows():
                        value = row[first_col]
                        if pd.notna(value) and str(value).strip():
                            calculation_type = {
                                "id": f"structural_{sheet_name}_{idx}",
                                "name": str(value).strip(),
                                "category": "construction",
                                "subcategory": sheet_name,
                                "description": f"Расчет {str(value).strip()}",
                                "norms": ["СП 20.13330.2016", "СП 16.13330.2017", "СП 63.13330.2018"],
                                "icon": "🏗️",
                                "parameters": {},
                                "formula": "",
                                "units": {}
                            }
                            
                            # Добавляем остальные колонки как параметры
                            for col_name in df.columns[1:]:
                                if pd.notna(row[col_name]):
                                    param_value = row[col_name]
                                    if isinstance(param_value, (int, float, str)):
                                        calculation_type["parameters"][str(col_name)] = param_value
                            
                            calculation_types.append(calculation_type)
                            print(f"✅ Добавлен расчет: {calculation_type['name']}")
        
        print(f"\n📊 Всего найдено видов расчетов: {len(calculation_types)}")
        
        # Сохраняем результат в JSON
        output_file = "structural_calculation_types.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(calculation_types, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Результат сохранен в: {output_file}")
        
        return calculation_types
        
    except Exception as e:
        print(f"❌ Ошибка при парсинге файла: {e}")
        import traceback
        traceback.print_exc()
        return []

def create_calculation_templates():
    """Создание шаблонов расчетов на основе парсинга"""
    
    calculation_types = parse_structural_calculations()
    
    if not calculation_types:
        print("❌ Не удалось получить виды расчетов")
        return
    
    # Создаем базовые шаблоны для каждого типа расчета
    templates = {}
    
    for calc_type in calculation_types:
        template = {
            "id": calc_type["id"],
            "name": calc_type["name"],
            "category": calc_type["category"],
            "subcategory": calc_type["subcategory"],
            "description": calc_type["description"],
            "norms": calc_type["norms"],
            "icon": calc_type["icon"],
            "input_fields": [
                {
                    "name": "material_strength",
                    "label": "Расчетное сопротивление материала, МПа",
                    "type": "number",
                    "required": True,
                    "default": 235,
                    "unit": "МПа"
                },
                {
                    "name": "section_area",
                    "label": "Площадь сечения, см²",
                    "type": "number",
                    "required": True,
                    "default": 100,
                    "unit": "см²"
                },
                {
                    "name": "load_value",
                    "label": "Расчетная нагрузка, кН",
                    "type": "number",
                    "required": True,
                    "default": 100,
                    "unit": "кН"
                },
                {
                    "name": "safety_factor",
                    "label": "Коэффициент надежности",
                    "type": "number",
                    "required": False,
                    "default": 1.1,
                    "unit": ""
                }
            ],
            "output_fields": [
                {
                    "name": "stress",
                    "label": "Напряжение",
                    "unit": "МПа",
                    "formula": "load_value * 1000 / section_area"
                },
                {
                    "name": "utilization_ratio",
                    "label": "Коэффициент использования",
                    "unit": "%",
                    "formula": "(stress / material_strength) * 100"
                },
                {
                    "name": "safety_margin",
                    "label": "Запас прочности",
                    "unit": "",
                    "formula": "material_strength / stress"
                }
            ],
            "formulas": {
                "stress": "load_value * 1000 / section_area",
                "utilization_ratio": "(stress / material_strength) * 100",
                "safety_margin": "material_strength / stress"
            },
            "validation_rules": [
                {
                    "field": "material_strength",
                    "rule": "min",
                    "value": 100,
                    "message": "Расчетное сопротивление должно быть не менее 100 МПа"
                },
                {
                    "field": "section_area",
                    "rule": "min",
                    "value": 1,
                    "message": "Площадь сечения должна быть положительной"
                },
                {
                    "field": "load_value",
                    "rule": "min",
                    "value": 0,
                    "message": "Нагрузка должна быть положительной"
                }
            ]
        }
        
        templates[calc_type["id"]] = template
    
    # Сохраняем шаблоны
    output_file = "calculation_templates.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(templates, f, ensure_ascii=False, indent=2)
    
    print(f"💾 Шаблоны расчетов сохранены в: {output_file}")
    print(f"📊 Создано шаблонов: {len(templates)}")

if __name__ == "__main__":
    print("🚀 Запуск парсинга видов расчетов строительных конструкций")
    create_calculation_templates()
    print("✅ Парсинг завершен")
