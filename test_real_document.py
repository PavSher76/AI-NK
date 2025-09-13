#!/usr/bin/env python3
"""
Тестирование реального документа с грубыми ошибками
"""

import requests
import json
import time
from datetime import datetime

class RealDocumentTester:
    """Тестер для реального документа с ошибками"""
    
    def __init__(self):
        self.outgoing_control_url = "http://localhost:8006"
        self.spellchecker_url = "http://localhost:8007"
        self.document_id = "cdb1daec-af47-4a37-9ce0-932cb7f2095b"
        
    def test_document_analysis(self):
        """Анализ загруженного документа"""
        print("🔍 Анализ загруженного документа")
        print("="*60)
        
        # Получаем информацию о документе
        try:
            response = requests.get(f"{self.outgoing_control_url}/documents", timeout=10)
            if response.status_code == 200:
                data = response.json()
                documents = data.get('documents', [])
                
                for doc in documents:
                    if doc['id'] == self.document_id:
                        print(f"📄 Документ: {doc['filename']}")
                        print(f"📊 Страниц: {doc['pages_count']}")
                        print(f"📝 Чанков: {doc['chunks_count']}")
                        print(f"📏 Длина текста: {len(doc['text'])} символов")
                        print(f"📅 Создан: {doc['created_at']}")
                        print(f"📋 Статус: {doc['status']}")
                        print()
                        
                        # Показываем первые 500 символов текста
                        text_preview = doc['text'][:500] + "..." if len(doc['text']) > 500 else doc['text']
                        print("📖 Превью текста:")
                        print("-" * 40)
                        print(text_preview)
                        print("-" * 40)
                        print()
                        break
        except Exception as e:
            print(f"❌ Ошибка получения информации о документе: {e}")
    
    def test_spellcheck_analysis(self):
        """Тестирование проверки орфографии"""
        print("🔍 Тестирование проверки орфографии")
        print("="*60)
        
        try:
            response = requests.post(
                f"{self.outgoing_control_url}/spellcheck",
                json={"document_id": self.document_id},
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                spell_results = result.get('spell_check_results', {})
                
                print(f"✅ Статус: {result.get('status')}")
                print(f"📊 Всего слов: {spell_results.get('total_words', 0)}")
                print(f"❌ Ошибок орфографии: {spell_results.get('misspelled_count', 0)}")
                print(f"📈 Точность: {spell_results.get('accuracy', 0):.2f}%")
                print(f"🔧 Метод: {spell_results.get('method', 'unknown')}")
                
                # Показываем найденные ошибки
                errors = spell_results.get('errors', [])
                if errors:
                    print(f"\n🔍 Найденные ошибки орфографии:")
                    for i, error in enumerate(errors[:10], 1):  # Показываем первые 10 ошибок
                        print(f"  {i}. Слово: '{error.get('word', 'N/A')}'")
                        print(f"     Позиция: {error.get('position', 'N/A')}")
                        print(f"     Контекст: {error.get('context', 'N/A')}")
                        print(f"     Предложения: {', '.join(error.get('suggestions', []))}")
                        print(f"     Уверенность: {error.get('confidence', 0):.2f}")
                        print()
                else:
                    print("✅ Ошибок орфографии не найдено")
            else:
                print(f"❌ Ошибка проверки орфографии: HTTP {response.status_code}")
                print(f"Ответ: {response.text}")
        except Exception as e:
            print(f"❌ Ошибка при проверке орфографии: {e}")
    
    def test_grammar_check_analysis(self):
        """Тестирование проверки грамматики"""
        print("🔍 Тестирование проверки грамматики")
        print("="*60)
        
        try:
            response = requests.post(
                f"{self.outgoing_control_url}/grammar-check",
                json={"document_id": self.document_id},
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                grammar_results = result.get('grammar_results', {})
                
                print(f"✅ Статус: {result.get('status')}")
                print(f"❌ Ошибок грамматики: {grammar_results.get('total_errors', 0)}")
                print(f"🔧 Метод: {grammar_results.get('method', 'unknown')}")
                
                # Показываем найденные ошибки
                errors = grammar_results.get('errors', [])
                if errors:
                    print(f"\n🔍 Найденные ошибки грамматики:")
                    for i, error in enumerate(errors[:10], 1):  # Показываем первые 10 ошибок
                        print(f"  {i}. Сообщение: {error.get('message', 'N/A')}")
                        print(f"     Контекст: {error.get('context', 'N/A')}")
                        print(f"     Позиция: {error.get('offset', 'N/A')}")
                        print(f"     Длина: {error.get('length', 'N/A')}")
                        print(f"     Замена: {', '.join(error.get('replacements', []))}")
                        print(f"     Правило: {error.get('rule_id', 'N/A')}")
                        print()
                else:
                    print("✅ Ошибок грамматики не найдено")
            else:
                print(f"❌ Ошибка проверки грамматики: HTTP {response.status_code}")
                print(f"Ответ: {response.text}")
        except Exception as e:
            print(f"❌ Ошибка при проверке грамматики: {e}")
    
    def test_comprehensive_check_analysis(self):
        """Тестирование комплексной проверки"""
        print("🔍 Тестирование комплексной проверки")
        print("="*60)
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.outgoing_control_url}/comprehensive-check",
                json={"document_id": self.document_id},
                timeout=120
            )
            end_time = time.time()
            
            if response.status_code == 200:
                result = response.json()
                comprehensive_results = result.get('comprehensive_results', {})
                
                print(f"✅ Статус: {result.get('status')}")
                print(f"⏱️ Время обработки: {end_time - start_time:.2f} секунд")
                print(f"🔧 Метод: {result.get('method', 'unknown')}")
                
                # Результаты орфографии
                spelling = comprehensive_results.get('spelling', {})
                print(f"\n📝 Результаты орфографии:")
                print(f"  Всего слов: {spelling.get('total_words', 0)}")
                print(f"  Ошибок: {spelling.get('misspelled_count', 0)}")
                print(f"  Точность: {spelling.get('accuracy', 0):.2f}%")
                print(f"  Метод: {spelling.get('method', 'unknown')}")
                
                # Результаты грамматики
                grammar = comprehensive_results.get('grammar', {})
                print(f"\n📚 Результаты грамматики:")
                print(f"  Ошибок: {grammar.get('total_errors', 0)}")
                print(f"  Метод: {grammar.get('method', 'unknown')}")
                
                # Общие результаты
                print(f"\n📊 Общие результаты:")
                print(f"  Всего ошибок: {comprehensive_results.get('total_errors', 0)}")
                print(f"  Общая точность: {comprehensive_results.get('overall_accuracy', 0):.2f}%")
                
                # Показываем все ошибки
                all_errors = comprehensive_results.get('all_errors', [])
                if all_errors:
                    print(f"\n🔍 Все найденные ошибки ({len(all_errors)}):")
                    for i, error in enumerate(all_errors[:15], 1):  # Показываем первые 15 ошибок
                        error_type = error.get('type', 'unknown')
                        word = error.get('word', 'N/A')
                        context = error.get('context', 'N/A')
                        confidence = error.get('confidence', 0)
                        
                        print(f"  {i}. [{error_type.upper()}] '{word}' (уверенность: {confidence:.2f})")
                        print(f"     Контекст: {context}")
                        if error.get('suggestions'):
                            print(f"     Предложения: {', '.join(error.get('suggestions', []))}")
                        print()
            else:
                print(f"❌ Ошибка комплексной проверки: HTTP {response.status_code}")
                print(f"Ответ: {response.text}")
        except Exception as e:
            print(f"❌ Ошибка при комплексной проверке: {e}")
    
    def test_manual_error_analysis(self):
        """Ручной анализ ошибок в документе"""
        print("🔍 Ручной анализ ошибок в документе")
        print("="*60)
        
        # Получаем текст документа
        try:
            response = requests.get(f"{self.outgoing_control_url}/documents", timeout=10)
            if response.status_code == 200:
                data = response.json()
                documents = data.get('documents', [])
                
                for doc in documents:
                    if doc['id'] == self.document_id:
                        text = doc['text']
                        break
                else:
                    print("❌ Документ не найден")
                    return
                
                # Ищем известные ошибки в тексте
                known_errors = [
                    ("саа тветствии", "в соответствии"),
                    ("оценк а", "оценка"),
                    ("при дложение", "предложение"),
                    ("а бъекту", "объекту"),
                    ("не получен ы", "не получены"),
                    ("падтверждение", "подтверждение"),
                    ("гаранти и", "гарантии"),
                    ("пре оритетно сти", "приоритетности"),
                    ("са гласование", "согласование"),
                    ("неполучен а", "не получен"),
                    ("твет", "ответ"),
                    ("предпра ектной", "предпроектной"),
                    ("са вещаний", "совещаний"),
                    ("инфо рмация", "информация"),
                    ("раннее", "ранее"),
                    ("пр аекту", "проекту"),
                    ("пра шу", "прошу"),
                    ("поттвердить", "подтвердить"),
                    ("га товность", "готовность"),
                    ("дагавора", "договора"),
                    ("расмотреть", "рассмотреть"),
                    ("обь ем", "объем"),
                    ("стадийн ость", "стадийность"),
                    ("праектирования", "проектирования"),
                    ("па скольку", "поскольку"),
                    ("утачнить", "уточнить"),
                    ("парядок", "порядок"),
                    ("р игистрации", "регистрации"),
                    ("Пр аект", "Проект"),
                    ("утачнить", "уточнить"),
                    ("парядок", "порядок")
                ]
                
                print("🔍 Найденные ошибки в тексте:")
                found_errors = []
                
                for error_word, correct_word in known_errors:
                    if error_word in text:
                        found_errors.append((error_word, correct_word))
                        print(f"  ❌ '{error_word}' → '{correct_word}'")
                
                print(f"\n📊 Статистика:")
                print(f"  Найдено ошибок: {len(found_errors)}")
                print(f"  Всего проверенных: {len(known_errors)}")
                print(f"  Процент обнаружения: {len(found_errors)/len(known_errors)*100:.1f}%")
                
        except Exception as e:
            print(f"❌ Ошибка при ручном анализе: {e}")
    
    def run_all_tests(self):
        """Запуск всех тестов"""
        print("🚀 ТЕСТИРОВАНИЕ РЕАЛЬНОГО ДОКУМЕНТА С ГРУБЫМИ ОШИБКАМИ")
        print("="*80)
        print(f"📄 Документ: E320.E32C-OUT-03484_от_20.05.2025_с_грубыми_ошибками.pdf")
        print(f"🆔 ID: {self.document_id}")
        print(f"⏰ Время тестирования: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
        print("="*80)
        print()
        
        # Тест 1: Анализ документа
        self.test_document_analysis()
        
        # Тест 2: Проверка орфографии
        self.test_spellcheck_analysis()
        
        # Тест 3: Проверка грамматики
        self.test_grammar_check_analysis()
        
        # Тест 4: Комплексная проверка
        self.test_comprehensive_check_analysis()
        
        # Тест 5: Ручной анализ ошибок
        self.test_manual_error_analysis()
        
        print("\n" + "="*80)
        print("✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
        print("="*80)


def main():
    """Основная функция"""
    tester = RealDocumentTester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()
