"""
Продвинутый модуль проверки орфографии и грамматики с использованием Hunspell + LanguageTool
"""

import re
import logging
import os
import time
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)
# Настройка логирования для модуля spell_checker
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class AdvancedSpellChecker:
    """Продвинутый проверщик орфографии и грамматики"""
    
    def __init__(self):
        self.hunspell = None
        self.language_tool = None
        self.dictionary = set()
        self._initialize_checkers()
    
    def _initialize_checkers(self):
        """Инициализация проверщиков"""
        # Инициализация Hunspell
        self._init_hunspell()
        
        # Инициализация LanguageTool
        self._init_language_tool()
        
        # Инициализация базового словаря
        self._init_dictionary()
        
        logger.info("AdvancedSpellChecker инициализирован успешно")
    
    def _init_hunspell(self):
        """Инициализация Hunspell"""
        logger.info("🔧 [HUNSPELL] Начинаем инициализацию Hunspell")
        start_time = time.time()
        
        try:
            import hunspell
            logger.info("🔧 [HUNSPELL] Модуль hunspell импортирован успешно")
            
            # Попробуем инициализировать Hunspell для русского языка
            try:
                logger.info("🔧 [HUNSPELL] Пытаемся инициализировать для русского языка...")
                self.hunspell = hunspell.HunSpell('/usr/share/hunspell/ru_RU.dic', '/usr/share/hunspell/ru_RU.aff')
                logger.info("✅ [HUNSPELL] Hunspell инициализирован для русского языка")
                
                # Проверим работу hunspell
                test_word = "тест"
                is_correct = self.hunspell.spell(test_word)
                suggestions = self.hunspell.suggest(test_word)
                logger.info(f"🔧 [HUNSPELL] Тестовая проверка: '{test_word}' -> {is_correct}, предложения: {suggestions[:3]}")
                
            except Exception as e:
                logger.warning(f"⚠️ [HUNSPELL] Не удалось инициализировать для ru_RU: {e}")
                # Попробуем английский
                try:
                    logger.info("🔧 [HUNSPELL] Пытаемся инициализировать для английского языка...")
                    self.hunspell = hunspell.HunSpell('/usr/share/hunspell/en_US.dic', '/usr/share/hunspell/en_US.aff')
                    logger.info("✅ [HUNSPELL] Hunspell инициализирован для английского языка")
                    
                    # Проверим работу hunspell
                    test_word = "test"
                    is_correct = self.hunspell.spell(test_word)
                    suggestions = self.hunspell.suggest(test_word)
                    logger.info(f"🔧 [HUNSPELL] Тестовая проверка: '{test_word}' -> {is_correct}, предложения: {suggestions[:3]}")
                    
                except Exception as e2:
                    logger.warning(f"⚠️ [HUNSPELL] Не удалось инициализировать для en_US: {e2}")
                    # Попробуем без указания путей (автопоиск)
                    try:
                        logger.info("🔧 [HUNSPELL] Пытаемся инициализировать с автопоиском словарей...")
                        self.hunspell = hunspell.HunSpell()
                        logger.info("✅ [HUNSPELL] Hunspell инициализирован с автопоиском словарей")
                        
                        # Проверим работу hunspell
                        test_word = "test"
                        is_correct = self.hunspell.spell(test_word)
                        suggestions = self.hunspell.suggest(test_word)
                        logger.info(f"🔧 [HUNSPELL] Тестовая проверка: '{test_word}' -> {is_correct}, предложения: {suggestions[:3]}")
                        
                    except Exception as e3:
                        logger.warning(f"⚠️ [HUNSPELL] Не удалось инициализировать с автопоиском: {e3}")
                        self.hunspell = None
            
        except ImportError:
            logger.warning("⚠️ [HUNSPELL] Модуль hunspell не установлен, используется упрощенная проверка")
            self.hunspell = None
        except Exception as e:
            logger.error(f"❌ [HUNSPELL] Ошибка инициализации Hunspell: {e}")
            self.hunspell = None
        
        init_time = time.time() - start_time
        if self.hunspell:
            logger.info(f"✅ [HUNSPELL] Инициализация завершена успешно за {init_time:.3f}с")
        else:
            logger.warning(f"⚠️ [HUNSPELL] Инициализация завершена с ошибками за {init_time:.3f}с")
    
    def _init_language_tool(self):
        """Инициализация LanguageTool"""
        try:
            import requests
            import time
            
            # Проверяем, доступен ли локальный LanguageTool сервис
            self.language_tool_url = "http://localhost:8081"
            self.language_tool_available = False
            
            # Ждем запуска сервиса
            for attempt in range(10):
                try:
                    response = requests.get(f"{self.language_tool_url}/v2/languages", timeout=5)
                    if response.status_code == 200:
                        self.language_tool_available = True
                        logger.info("LanguageTool сервис доступен на localhost:8081")
                        break
                except Exception as e:
                    logger.info(f"Попытка {attempt + 1}/10: LanguageTool сервис еще не готов: {e}")
                    time.sleep(2)
            
            if not self.language_tool_available:
                logger.warning("LanguageTool сервис недоступен, используется упрощенная проверка")
            else:
                self.language_tool = True  # Устанавливаем флаг для совместимости
            
        except ImportError:
            logger.warning("Модуль requests не установлен, используется упрощенная проверка")
        except Exception as e:
            logger.error(f"Ошибка инициализации LanguageTool: {e}")
    
    def _init_dictionary(self):
        """Инициализация базового словаря"""
        # Расширенный словарь русских слов
        self.dictionary = {
            # Основные слова
            'документ', 'проверка', 'орфография', 'грамматика', 'ошибка', 'исправление',
            'текст', 'слово', 'предложение', 'абзац', 'страница', 'файл', 'загрузка',
            'сохранение', 'отправка', 'получение', 'обработка', 'анализ', 'результат',
            'система', 'сервис', 'модуль', 'функция', 'метод', 'класс', 'объект',
            'данные', 'информация', 'содержание', 'структура', 'формат', 'версия',
            'настройка', 'конфигурация', 'параметр', 'опция', 'выбор', 'установка',
            'запуск', 'остановка', 'работа', 'выполнение', 'завершение', 'успех',
            'проблема', 'решение', 'помощь', 'поддержка', 'техническая',
            'пользователь', 'администратор', 'разработчик', 'тестировщик', 'аналитик',
            
            # Деловая лексика
            'договор', 'соглашение', 'контракт', 'протокол', 'акт', 'справка',
            'отчет', 'заключение', 'рекомендация', 'предложение', 'заявление',
            'уведомление', 'извещение', 'сообщение', 'информация', 'сведения',
            'документооборот', 'корреспонденция', 'переписка', 'коммуникация',
            
            # Техническая лексика
            'программирование', 'разработка', 'тестирование', 'отладка', 'интеграция',
            'деплой', 'развертывание', 'конфигурация', 'настройка', 'оптимизация',
            'производительность', 'безопасность', 'аутентификация', 'авторизация',
            'шифрование', 'кодирование', 'декодирование', 'сжатие', 'архивирование',
            
            # Общие слова
            'привет', 'здравствуйте', 'спасибо', 'пожалуйста', 'извините',
            'хорошо', 'плохо', 'отлично', 'замечательно', 'прекрасно',
            'важно', 'необходимо', 'обязательно', 'желательно', 'рекомендуется',
            'можно', 'нужно', 'следует', 'требуется', 'необходимо',
            
            # Организации и аббревиатуры
            'ооо', 'зао', 'оао', 'пао', 'ип', 'тд', 'тдо', 'пир', 'ркд', 'ниопс',
            'еврохим', 'протех', 'инжиниринг', 'белобородов', 'давлеткулов',
            'галушков', 'юрманова', 'сергеевна', 'илья', 'викторович',
            
            # Технические термины
            'концентрат', 'переработка', 'установка', 'проектирование', 'строительство',
            'объект', 'проект', 'задание', 'техническое', 'коммерческое',
            'стоимость', 'работы', 'гарантия', 'оплата', 'разъяснение',
            'стадийность', 'приоритетность', 'предварительный', 'запрос',
            'исходный', 'согласование', 'схема', 'документация', 'цех',
            'предпроектный', 'проработка', 'технологический', 'совещание',
            'изменение', 'объем', 'временный', 'подключение', 'трубопровод',
            'эстакада', 'подтверждение', 'готовность', 'заключение', 'рассмотрение',
            'комментарий', 'уточнение', 'критерий', 'разработка', 'проектная',
            'рабочая', 'регистрация', 'отдельный', 'состав', 'действующий',
            'приложение', 'уважением', 'директор', 'наименование', 'должность',
            'личная', 'подпись', 'фамилия', 'исполнитель', 'телефон', 'email',
            
            # Географические названия
            'россия', 'москва', 'дубининская', 'даниловский', 'северо', 'запад',
            
            # Английские слова (часто используемые в деловых документах)
            'office', 'eurochem', 'pte', 'out', 'gen', 'mail', 'ilya', 'beloborodov',
            'asya', 'yurmanova', 'e32c', 'e320', 'e230', 'dkc', 'ksp',
            
            # Сокращения и коды
            'огрн', 'инн', 'кпп', 'грк', 'рф', 'ехсз', 'пти', 'испо', 'опо'
        }
        
        logger.info(f"Базовый словарь инициализирован: {len(self.dictionary)} слов")
    
    def check_spelling(self, text: str) -> Dict[str, Any]:
        """Проверка орфографии"""
        if self.hunspell:
            return self._check_spelling_hunspell(text)
        else:
            return self._check_spelling_fallback(text)
    
    def _check_spelling_hunspell(self, text: str) -> Dict[str, Any]:
        """Проверка орфографии с помощью Hunspell"""
        logger.info(f"🔍 [HUNSPELL] Начинаем проверку орфографии с помощью Hunspell для текста длиной {len(text)} символов")
        start_time = time.time()
        
        try:
            words = self._extract_words(text)
            logger.info(f"🔍 [HUNSPELL] Извлечено {len(words)} слов для проверки")
            
            errors = []
            checked_words = 0
            skipped_words = 0
            dictionary_hits = 0
            false_positive_skips = 0
            
            for word in words:
                checked_words += 1
                
                # Пропускаем короткие слова, числа и специальные символы
                if len(word) < 3 or word.isdigit() or not word.isalpha():
                    skipped_words += 1
                    logger.debug(f"🔍 [HUNSPELL] Пропущено короткое слово/число: '{word}'")
                    continue
                
                # Пропускаем слова из расширенного словаря
                if word.lower() in self.dictionary:
                    dictionary_hits += 1
                    logger.debug(f"🔍 [HUNSPELL] Слово найдено в расширенном словаре: '{word}'")
                    continue
                
                # Пропускаем слова, которые выглядят как корректные
                if self._is_likely_correct_word(word):
                    skipped_words += 1
                    logger.debug(f"🔍 [HUNSPELL] Слово выглядит корректным: '{word}'")
                    continue
                
                # Проверяем слово через Hunspell
                logger.debug(f"🔍 [HUNSPELL] Проверяем слово: '{word}'")
                is_correct = self.hunspell.spell(word)
                
                if not is_correct:
                    logger.info(f"🔍 [HUNSPELL] Найдена ошибка в слове: '{word}'")
                    suggestions = self.hunspell.suggest(word)
                    logger.info(f"🔍 [HUNSPELL] Предложения для '{word}': {suggestions[:3]}")
                    
                    context = self._get_word_context(text, word)
                    
                    # Дополнительная проверка - возможно это правильное слово
                    if self._is_likely_false_positive(word, suggestions):
                        false_positive_skips += 1
                        logger.info(f"🔍 [HUNSPELL] Слово '{word}' пропущено как ложное срабатывание")
                        continue
                    
                    error_data = {
                        "word": word,
                        "position": text.find(word),
                        "context": context,
                        "suggestions": suggestions[:5],  # Ограничиваем до 5 предложений
                        "type": "spelling",
                        "confidence": 0.8  # Высокая уверенность для Hunspell
                    }
                    errors.append(error_data)
                    logger.info(f"🔍 [HUNSPELL] Добавлена ошибка: {error_data}")
                else:
                    logger.debug(f"🔍 [HUNSPELL] Слово корректно: '{word}'")
            
            processing_time = time.time() - start_time
            
            result = {
                "total_words": len(words),
                "checked_words": checked_words,
                "skipped_words": skipped_words,
                "dictionary_hits": dictionary_hits,
                "false_positive_skips": false_positive_skips,
                "misspelled_count": len(errors),
                "errors": errors,
                "accuracy": (len(words) - len(errors)) / len(words) * 100 if words else 100,
                "method": "hunspell",
                "processing_time": processing_time
            }
            
            logger.info(f"🔍 [HUNSPELL] Проверка завершена за {processing_time:.3f}с:")
            logger.info(f"🔍 [HUNSPELL] - Всего слов: {len(words)}")
            logger.info(f"🔍 [HUNSPELL] - Проверено: {checked_words}")
            logger.info(f"🔍 [HUNSPELL] - Пропущено: {skipped_words}")
            logger.info(f"🔍 [HUNSPELL] - Найдено в словаре: {dictionary_hits}")
            logger.info(f"🔍 [HUNSPELL] - Ложные срабатывания: {false_positive_skips}")
            logger.info(f"🔍 [HUNSPELL] - Ошибок найдено: {len(errors)}")
            logger.info(f"🔍 [HUNSPELL] - Точность: {result['accuracy']:.1f}%")
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка проверки орфографии Hunspell: {e}")
            return self._check_spelling_fallback(text)
    
    def _check_spelling_fallback(self, text: str) -> Dict[str, Any]:
        """Резервная проверка орфографии"""
        logger.info(f"🔍 [FALLBACK] Начинаем резервную проверку орфографии для текста длиной {len(text)} символов")
        start_time = time.time()
        
        words = self._extract_words(text)
        logger.info(f"🔍 [FALLBACK] Извлечено {len(words)} слов для проверки")
        
        errors = []
        checked_words = 0
        dictionary_hits = 0
        suspicious_words = 0
        
        for word in words:
            checked_words += 1
            
            # Пропускаем короткие слова, числа и специальные символы
            if len(word) < 3 or word.isdigit() or not word.isalpha():
                logger.debug(f"🔍 [FALLBACK] Пропущено короткое слово/число: '{word}'")
                continue
            
            # Проверяем слово по словарю
            if word.lower() not in self.dictionary:
                logger.debug(f"🔍 [FALLBACK] Слово не найдено в словаре: '{word}'")
                # Дополнительные проверки
                if self._is_suspicious_word(word):
                    suspicious_words += 1
                    logger.info(f"🔍 [FALLBACK] Найдена подозрительная ошибка в слове: '{word}'")
                    context = self._get_word_context(text, word)
                    suggestions = self._get_suggestions(word)
                    
                    error_data = {
                        "word": word,
                        "position": text.find(word),
                        "context": context,
                        "suggestions": suggestions,
                        "type": "spelling",
                        "confidence": 0.5  # Средняя уверенность для fallback
                    }
                    errors.append(error_data)
                    logger.info(f"🔍 [FALLBACK] Добавлена ошибка: {error_data}")
                else:
                    logger.debug(f"🔍 [FALLBACK] Слово не выглядит подозрительным: '{word}'")
            else:
                dictionary_hits += 1
                logger.debug(f"🔍 [FALLBACK] Слово найдено в словаре: '{word}'")
        
        processing_time = time.time() - start_time
        accuracy = (len(words) - len(errors)) / len(words) * 100 if words else 100
        
        logger.info(f"🔍 [FALLBACK] Резервная проверка завершена за {processing_time:.3f}с:")
        logger.info(f"🔍 [FALLBACK] - Всего слов: {len(words)}")
        logger.info(f"🔍 [FALLBACK] - Проверено: {checked_words}")
        logger.info(f"🔍 [FALLBACK] - Найдено в словаре: {dictionary_hits}")
        logger.info(f"🔍 [FALLBACK] - Подозрительных слов: {suspicious_words}")
        logger.info(f"🔍 [FALLBACK] - Ошибок найдено: {len(errors)}")
        logger.info(f"🔍 [FALLBACK] - Точность: {accuracy:.1f}%")
        
        return {
            "total_words": len(words),
            "checked_words": checked_words,
            "dictionary_hits": dictionary_hits,
            "suspicious_words": suspicious_words,
            "misspelled_count": len(errors),
            "errors": errors,
            "accuracy": accuracy,
            "method": "fallback",
            "processing_time": processing_time
        }
    
    def check_grammar(self, text: str) -> Dict[str, Any]:
        """Проверка грамматики"""
        if hasattr(self, 'language_tool_available') and self.language_tool_available:
            return self._check_grammar_languagetool_http(text)
        else:
            return self._check_grammar_fallback(text)
    
    def _check_grammar_languagetool(self, text: str) -> Dict[str, Any]:
        """Проверка грамматики с помощью LanguageTool"""
        try:
            matches = self.language_tool.check(text)
            grammar_errors = []
            
            for match in matches:
                grammar_errors.append({
                    "message": match.message,
                    "context": match.context,
                    "offset": match.offset,
                    "length": match.errorLength,
                    "replacements": match.replacements[:3],  # Ограничиваем до 3 предложений
                    "rule_id": match.ruleId,
                    "type": "grammar",
                    "confidence": 0.9  # Высокая уверенность для LanguageTool
                })
            
            return {
                "errors": grammar_errors,
                "total_errors": len(grammar_errors),
                "method": "languagetool"
            }
            
        except Exception as e:
            logger.error(f"Ошибка проверки грамматики LanguageTool: {e}")
            return self._check_grammar_fallback(text)
    
    def _check_grammar_languagetool_http(self, text: str) -> Dict[str, Any]:
        """Проверка грамматики с помощью LanguageTool через HTTP API"""
        try:
            import requests
            
            # Отправляем запрос к LanguageTool API
            response = requests.post(
                f"{self.language_tool_url}/v2/check",
                data={
                    'text': text,
                    'language': 'ru-RU'
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                grammar_errors = []
                
                for match in data.get('matches', []):
                    grammar_errors.append({
                        "message": match.get('message', ''),
                        "context": match.get('context', {}).get('text', ''),
                        "offset": match.get('offset', 0),
                        "length": match.get('length', 0),
                        "replacements": match.get('replacements', [])[:3],  # Ограничиваем до 3 предложений
                        "rule_id": match.get('rule', {}).get('id', ''),
                        "type": "grammar",
                        "confidence": 0.9  # Высокая уверенность для LanguageTool
                    })
                
                return {
                    "errors": grammar_errors,
                    "total_errors": len(grammar_errors),
                    "method": "languagetool_http"
                }
            else:
                logger.warning(f"LanguageTool API вернул статус {response.status_code}")
                return self._check_grammar_fallback(text)
            
        except Exception as e:
            logger.error(f"Ошибка проверки грамматики с LanguageTool HTTP API: {e}")
            return self._check_grammar_fallback(text)
    
    def _check_grammar_fallback(self, text: str) -> Dict[str, Any]:
        """Резервная проверка грамматики"""
        grammar_errors = []
        
        # Проверяем на избыточность
        redundancy_patterns = [
            (r'\bэто есть\b', "Возможная избыточность: 'это есть'"),
            (r'\bто есть\b', "Возможная избыточность: 'то есть'"),
            (r'\bтакже и\b', "Возможная избыточность: 'также и'"),
            (r'\bвместе с тем\b', "Возможная избыточность: 'вместе с тем'"),
            (r'\bв связи с тем\b', "Возможная избыточность: 'в связи с тем'")
        ]
        
        for pattern, message in redundancy_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                grammar_errors.append({
                    "message": message,
                    "context": match.group(),
                    "offset": match.start(),
                    "length": len(match.group()),
                    "replacements": ["упростите выражение"],
                    "rule_id": "REDUNDANCY",
                    "type": "grammar",
                    "confidence": 0.6  # Средняя уверенность для fallback
                })
        
        return {
            "errors": grammar_errors,
            "total_errors": len(grammar_errors),
            "method": "fallback"
        }
    
    def comprehensive_check(self, text: str) -> Dict[str, Any]:
        """Комплексная проверка орфографии и грамматики"""
        logger.info(f"🔍 [COMPREHENSIVE] Начинаем комплексную проверку для текста длиной {len(text)} символов")
        start_time = time.time()
        
        # Проверка орфографии
        logger.info("🔍 [COMPREHENSIVE] Запускаем проверку орфографии...")
        spelling_start = time.time()
        spelling_result = self.check_spelling(text)
        spelling_time = time.time() - spelling_start
        logger.info(f"🔍 [COMPREHENSIVE] Проверка орфографии завершена за {spelling_time:.3f}с")
        
        # Проверка грамматики
        logger.info("🔍 [COMPREHENSIVE] Запускаем проверку грамматики...")
        grammar_start = time.time()
        grammar_result = self.check_grammar(text)
        grammar_time = time.time() - grammar_start
        logger.info(f"🔍 [COMPREHENSIVE] Проверка грамматики завершена за {grammar_time:.3f}с")
        
        # Объединяем результаты
        all_errors = spelling_result["errors"] + grammar_result["errors"]
        
        # Сортируем ошибки по позиции в тексте
        all_errors.sort(key=lambda x: x.get("offset", x.get("position", 0)))
        
        processing_time = time.time() - start_time
        total_errors = len(all_errors)
        spelling_errors = spelling_result.get("misspelled_count", 0)
        grammar_errors = grammar_result.get("error_count", 0)
        overall_accuracy = self._calculate_overall_accuracy(spelling_result, grammar_result, text)
        
        logger.info(f"🔍 [COMPREHENSIVE] Комплексная проверка завершена за {processing_time:.3f}с:")
        logger.info(f"🔍 [COMPREHENSIVE] - Ошибок орфографии: {spelling_errors}")
        logger.info(f"🔍 [COMPREHENSIVE] - Ошибок грамматики: {grammar_errors}")
        logger.info(f"🔍 [COMPREHENSIVE] - Всего ошибок: {total_errors}")
        logger.info(f"🔍 [COMPREHENSIVE] - Общая точность: {overall_accuracy:.1f}%")
        
        return {
            "spelling": spelling_result,
            "grammar": grammar_result,
            "total_errors": total_errors,
            "all_errors": all_errors,
            "overall_accuracy": overall_accuracy,
            "methods": {
                "spelling": spelling_result.get("method", "unknown"),
                "grammar": grammar_result.get("method", "unknown")
            },
            "processing_time": processing_time
        }
    
    def _extract_words(self, text: str) -> List[str]:
        """Извлечение слов из текста"""
        # Убираем знаки препинания и разбиваем на слова
        words = re.findall(r'\b[а-яёА-ЯЁa-zA-Z]+\b', text.lower())
        return words
    
    def _get_word_context(self, text: str, word: str) -> str:
        """Получение контекста вокруг слова"""
        words = text.split()
        word_index = -1
        for i, w in enumerate(words):
            if word in w:
                word_index = i
                break
        
        if word_index == -1:
            return f"...{word}..."
        
        start = max(0, word_index - 3)
        end = min(len(words), word_index + 4)
        context_words = words[start:end]
        
        # Выделяем проблемное слово
        context = " ".join(context_words)
        if word in context:
            context = context.replace(word, f"**{word}**", 1)
        
        return context
    
    def _is_suspicious_word(self, word: str) -> bool:
        """Проверка, является ли слово подозрительным"""
        # Слова длиннее 15 символов
        if len(word) > 15:
            return True
        
        # Слова с повторяющимися символами
        if len(set(word)) < len(word) * 0.6:
            return True
        
        # Слова с необычными комбинациями
        unusual_patterns = [r'[а-яё]{3,}[a-z]', r'[a-z]{3,}[а-яё]', r'[0-9]{2,}']
        for pattern in unusual_patterns:
            if re.search(pattern, word):
                return True
        
        return False
    
    def _is_likely_correct_word(self, word: str) -> bool:
        """Проверка, является ли слово вероятно правильным"""
        word_lower = word.lower()
        
        # Проверяем по расширенному словарю
        if word_lower in self.dictionary:
            return True
        
        # Слова с заглавной буквы (имена, названия)
        if word[0].isupper() and len(word) > 2:
            return True
        
        # Короткие слова (2-3 символа)
        if len(word) <= 3:
            return True
        
        # Слова с дефисами (составные слова)
        if '-' in word:
            return True
        
        # Слова с цифрами (коды, номера)
        if any(c.isdigit() for c in word):
            return True
        
        # Английские слова в деловых документах
        english_business_words = {
            'office', 'email', 'mail', 'phone', 'fax', 'web', 'www', 'http',
            'https', 'com', 'ru', 'org', 'net', 'info', 'pdf', 'doc', 'docx',
            'xls', 'xlsx', 'ppt', 'pptx', 'zip', 'rar', 'jpg', 'png', 'gif',
            'mp3', 'mp4', 'avi', 'mov', 'wmv', 'flv', 'mkv', 'mpg', 'mpeg'
        }
        if word_lower in english_business_words:
            return True
        
        return False
    
    def _is_likely_false_positive(self, word: str, suggestions: List[str]) -> bool:
        """Проверка, является ли ошибка ложным срабатыванием"""
        word_lower = word.lower()
        
        # Если нет предложений, возможно это правильное слово
        if not suggestions:
            return True
        
        # Если предложения очень отличаются от исходного слова
        if suggestions:
            best_suggestion = suggestions[0].lower()
            # Если предложение сильно отличается (более 50% символов)
            if len(set(word_lower) & set(best_suggestion)) < len(word_lower) * 0.5:
                return True
        
        # Слова, которые часто являются ложными срабатываниями
        common_false_positives = {
            'ооо', 'зао', 'оао', 'пао', 'ип', 'тд', 'тдо', 'пир', 'ркд', 'ниопс',
            'еврохим', 'протех', 'инжиниринг', 'белобородов', 'давлеткулов',
            'галушков', 'юрманова', 'сергеевна', 'илья', 'викторович',
            'огрн', 'инн', 'кпп', 'грк', 'рф', 'ехсз', 'пти', 'испо', 'опо',
            'office', 'eurochem', 'pte', 'out', 'gen', 'mail', 'ilya', 'beloborodov',
            'asya', 'yurmanova', 'e32c', 'e320', 'e230', 'dkc', 'ksp'
        }
        if word_lower in common_false_positives:
            return True
        
        return False
    
    def _get_suggestions(self, word: str) -> List[str]:
        """Получение предложений по исправлению"""
        suggestions = []
        
        # Поиск похожих слов в словаре
        for dict_word in self.dictionary:
            if self._levenshtein_distance(word.lower(), dict_word) <= 2:
                suggestions.append(dict_word)
        
        # Ограничиваем количество предложений
        return suggestions[:5] if suggestions else ["проверьте написание"]
    
    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """Расчет расстояния Левенштейна"""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    def _calculate_overall_accuracy(self, spelling_result: Dict, grammar_result: Dict, text: str) -> float:
        """Расчет общей точности"""
        total_words = spelling_result["total_words"]
        spelling_errors = spelling_result["misspelled_count"]
        grammar_errors = grammar_result["total_errors"]
        
        # Учитываем и орфографические, и грамматические ошибки
        total_errors = spelling_errors + grammar_errors
        return max(0, (total_words - total_errors) / total_words * 100) if total_words > 0 else 100
