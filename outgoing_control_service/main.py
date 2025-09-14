from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
import uvicorn
import os
import json
import uuid
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
import asyncio
import aiofiles
from pathlib import Path

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Импорты для обработки документов
import requests

# Импорт общего модуля утилит
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils import parse_document, parse_document_from_bytes, clean_text, hierarchical_text_chunking

# Локальный fallback проверщик (упрощенный)

# Конфигурация внешних сервисов
SPELLCHECKER_SERVICE_URL = os.getenv("SPELLCHECKER_SERVICE_URL", "http://spellchecker-service:8007")
VLLM_SERVICE_URL = os.getenv("VLLM_SERVICE_URL", "http://ai-nk-vllm-1:8005")

# Функции для работы с spellchecker-service
async def call_spellchecker_service(text: str, check_type: str = "comprehensive") -> Dict[str, Any]:
    """Вызов spellchecker-service для проверки текста"""
    try:
        # Всегда используем comprehensive-check, так как spellchecker-service не поддерживает отдельные endpoints
        url = f"{SPELLCHECKER_SERVICE_URL}/comprehensive-check"
        data = {
            "text": text,
            "language": "ru",
            "check_spelling": True,
            "check_grammar": True
        }
        
        # Логируем время отправки запроса
        request_time = datetime.now().isoformat()
        request_log = f"POST {url} | Data: {len(text)} chars | Check type: {check_type}"
        logger.info(f"Отправляем запрос в spellchecker-service в {request_time}")
        
        response = requests.post(url, json=data, timeout=30)
        response.raise_for_status()
        
        # Логируем время получения ответа
        response_time = datetime.now().isoformat()
        result = response.json()
        response_log = f"Status: {result.get('status', 'unknown')} | Response size: {len(str(result))} chars"
        logger.info(f"Получен ответ от spellchecker-service в {response_time}")
        
        # Адаптируем результат для разных типов проверки
        if check_type == "spellcheck" and "comprehensive" in result:
            result["spelling"] = result["comprehensive"]["spelling"]
        elif check_type == "grammar-check" and "comprehensive" in result:
            result["grammar"] = result["comprehensive"]["grammar"]
        
        # Добавляем отладочную информацию
        result["debug_info"] = {
            "spellchecker_request_time": request_time,
            "spellchecker_response_time": response_time,
            "spellchecker_request_log": request_log,
            "spellchecker_response_log": response_log
        }
        
        return result
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка вызова spellchecker-service: {e}")
        # Fallback на локальный проверщик
        return await fallback_spell_check(text)
    except Exception as e:
        logger.error(f"Неожиданная ошибка при вызове spellchecker-service: {e}")
        return await fallback_spell_check(text)

async def call_system_llm(prompt: str) -> Dict[str, Any]:
    """Системная LLM обработка без обращения к внешнему сервису"""
    try:
        # Логируем время начала обработки
        request_time = datetime.now().isoformat()
        request_log = f"SYSTEM LLM | Prompt: {len(prompt)} chars | Local processing"
        logger.info(f"Начинаем системную LLM обработку в {request_time}")
        
        # Простая системная обработка на основе ключевых слов
        analysis_text = generate_system_analysis(prompt)
        
        # Логируем время завершения
        response_time = datetime.now().isoformat()
        response_log = f"Response size: {len(analysis_text)} chars | System processing completed"
        logger.info(f"Системная LLM обработка завершена в {response_time}")
        
        return {
            "response": analysis_text,
            "debug_info": {
                "vllm_request_time": request_time,
                "vllm_response_time": response_time,
                "vllm_request_log": request_log,
                "vllm_response_log": response_log
            }
        }
    except Exception as e:
        response_time = datetime.now().isoformat()
        logger.error(f"Ошибка системной LLM обработки: {e}")
        return {
            "status": "error", 
            "message": str(e),
            "debug_info": {
                "vllm_request_time": request_time if 'request_time' in locals() else None,
                "vllm_response_time": response_time,
                "vllm_request_log": request_log if 'request_log' in locals() else None,
                "vllm_response_log": f"ERROR: {str(e)}"
            }
        }

def generate_system_analysis(prompt: str) -> str:
    """Генерация системного анализа на основе ключевых слов"""
    # Извлекаем информацию о spellchecker из промпта
    spell_check_info = "Результаты автоматической проверки не доступны"
    if "spell_check_results" in prompt:
        # Простое извлечение информации об ошибках
        if "ошибок" in prompt.lower():
            spell_check_info = "Найдены орфографические ошибки, требующие проверки"
    
    # Простой системный анализ
    analysis = f"""
## АНАЛИЗ РЕЗУЛЬТАТОВ SPELLCHECKER
- **Всего найдено ошибок**: Требует проверки
- **Реальные ошибки**: Требует ручной проверки
- **Исключенные ложные срабатывания**: Требует ручной проверки

## ДЕЛОВОЙ СТИЛЬ
- **Статус**: Требует доработки
- **Найденные нарушения**: Требует ручной проверки
- **Рекомендации**: Проверить соответствие корпоративным стандартам

## КОРПОРАТИВНАЯ ЭТИКА
- **Статус**: Требует доработки
- **Найденные нарушения**: Требует ручной проверки
- **Рекомендации**: Проверить соблюдение делового этикета

## ПОЛНОТА И ЛОГИКА
- **Статус**: Требует доработки
- **Найденные нарушения**: Требует ручной проверки
- **Рекомендации**: Проверить логическую структуру документа

## ЮРИДИЧЕСКАЯ И ФАКТОЛОГИЧЕСКАЯ ТОЧНОСТЬ
- **Статус**: Требует доработки
- **Найденные нарушения**: Требует ручной проверки
- **Рекомендации**: Проверить точность данных и ссылок

## ЯЗЫКОВЫЕ АСПЕКТЫ
- **Реальные орфографические ошибки**: {spell_check_info}
- **Грамматические нарушения**: Требует ручной проверки
- **Стилистические замечания**: Требует ручной проверки

### ДЕТАЛЬНЫЙ ПЕРЕЧЕНЬ ОРФОГРАФИЧЕСКИХ ОШИБОК:
Системная модель не может выполнить детальный анализ. Требуется использование внешней LLM модели.

## ЦЕЛЕСООБРАЗНОСТЬ ОТПРАВКИ
- **ВЕРДИКТ**: ТРЕБУЕТ ДОРАБОТКИ
- **Обоснование**: Системная модель не может выполнить полный анализ. Рекомендуется использовать внешнюю LLM модель для детальной проверки.
- **Критические нарушения**: Требует ручной проверки
- **Рекомендации по доработке**: Использовать внешнюю LLM модель для полного анализа

**ПРИМЕЧАНИЕ**: Данный анализ выполнен системной моделью. Для получения детального анализа рекомендуется использовать внешнюю LLM модель.
"""
    return analysis

async def call_vllm_service(prompt: str, model: str = None) -> Dict[str, Any]:
    """Вызов vllm-service для LLM обработки"""
    try:
        # Используем выбранную модель или модель по умолчанию
        selected_model = model or settings_db.get("selected_llm_model", "llama3.1:8b")
        
        # Если выбрана системная модель, используем локальную обработку
        if selected_model == "system":
            return await call_system_llm(prompt)
        
        url = f"{VLLM_SERVICE_URL}/chat"
        data = {
            "message": prompt,
            "model": selected_model,
            "max_tokens": 1000
        }
        
        # Логируем время отправки запроса
        request_time = datetime.now().isoformat()
        request_log = f"POST {url} | Prompt: {len(prompt)} chars | Model: {selected_model}"
        logger.info(f"Отправляем запрос в vllm-service в {request_time} с моделью {selected_model}")
        
        response = requests.post(url, json=data, timeout=300)
        response.raise_for_status()
        
        # Логируем время получения ответа
        response_time = datetime.now().isoformat()
        result = response.json()
        response_log = f"Response size: {len(str(result))} chars | Has response: {'response' in result}"
        logger.info(f"Получен ответ от vllm-service в {response_time}")
        
        # Добавляем отладочную информацию
        result["debug_info"] = {
            "vllm_request_time": request_time,
            "vllm_response_time": response_time,
            "vllm_request_log": request_log,
            "vllm_response_log": response_log
        }
        
        return result
    except Exception as e:
        response_time = datetime.now().isoformat()
        logger.error(f"Ошибка вызова vllm-service: {e}")
        return {
            "status": "error", 
            "message": str(e),
            "debug_info": {
                "vllm_request_time": request_time if 'request_time' in locals() else None,
                "vllm_response_time": response_time,
                "vllm_request_log": request_log if 'request_log' in locals() else None,
                "vllm_response_log": f"ERROR: {str(e)}"
            }
        }

def parse_llm_spelling_analysis(analysis_text: str, original_errors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Парсинг детального анализа орфографических ошибок от LLM"""
    detailed_errors = []
    
    try:
        # Ищем секцию с детальным перечнем ошибок
        if "ДЕТАЛЬНЫЙ ПЕРЕЧЕНЬ ОРФОГРАФИЧЕСКИХ ОШИБОК" in analysis_text:
            # Извлекаем текст секции
            start_marker = "ДЕТАЛЬНЫЙ ПЕРЕЧЕНЬ ОРФОГРАФИЧЕСКИХ ОШИБОК"
            end_marker = "## ЦЕЛЕСООБРАЗНОСТЬ ОТПРАВКИ"
            
            start_idx = analysis_text.find(start_marker)
            end_idx = analysis_text.find(end_marker)
            
            if start_idx != -1 and end_idx != -1:
                section_text = analysis_text[start_idx:end_idx]
                
                # Парсим каждую ошибку
                lines = section_text.split('\n')
                current_error = {}
                
                for line in lines:
                    line = line.strip()
                    if line.startswith('1. **Слово с ошибкой**:'):
                        if current_error:
                            detailed_errors.append(current_error)
                        current_error = {
                            'original_word': line.split(':', 1)[1].strip().strip('[]'),
                            'context': '',
                            'expert_assessment': '',
                            'justification': '',
                            'correct_spelling': '',
                            'impact': ''
                        }
                    elif line.startswith('2. **Контекст**:'):
                        current_error['context'] = line.split(':', 1)[1].strip().strip('[]')
                    elif line.startswith('3. **Оценка эксперта**:'):
                        current_error['expert_assessment'] = line.split(':', 1)[1].strip().strip('[]')
                    elif line.startswith('4. **Обоснование**:'):
                        current_error['justification'] = line.split(':', 1)[1].strip().strip('[]')
                    elif line.startswith('5. **Правильное написание**:'):
                        current_error['correct_spelling'] = line.split(':', 1)[1].strip().strip('[]')
                    elif line.startswith('6. **Влияние на документ**:'):
                        current_error['impact'] = line.split(':', 1)[1].strip().strip('[]')
                
                # Добавляем последнюю ошибку
                if current_error:
                    detailed_errors.append(current_error)
        
        # Если детальный анализ не найден, создаем базовую структуру
        if not detailed_errors and original_errors:
            for error in original_errors:
                detailed_errors.append({
                    'original_word': error.get('word', ''),
                    'context': error.get('context', ''),
                    'expert_assessment': 'требует проверки',
                    'justification': 'автоматически обнаружено spellchecker',
                    'correct_spelling': ', '.join(error.get('suggestions', [])[:3]),
                    'impact': 'незначительно'
                })
        
    except Exception as e:
        logger.error(f"Ошибка парсинга анализа LLM: {e}")
        # Fallback к базовой структуре
        for error in original_errors:
            detailed_errors.append({
                'original_word': error.get('word', ''),
                'context': error.get('context', ''),
                'expert_assessment': 'требует проверки',
                'justification': 'автоматически обнаружено spellchecker',
                'correct_spelling': ', '.join(error.get('suggestions', [])[:3]),
                'impact': 'незначительно'
            })
    
    return detailed_errors

async def double_check_errors_with_llm(text: str, errors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Двойная проверка найденных ошибок через LLM"""
    if not errors:
        return errors
    
    try:
        # Формируем промпт для LLM
        errors_text = "\n".join([
            f"- Слово: '{error.get('word', '')}' | Контекст: '{error.get('context', '')}' | Тип: {error.get('type', '')}"
            for error in errors
        ])
        
        prompt = f"""
Вы - эксперт по русскому языку. Проанализируйте найденные "ошибки" в тексте и определите, являются ли они реальными ошибками или ложными срабатываниями.

ИСХОДНЫЙ ТЕКСТ:
{text}

НАЙДЕННЫЕ "ОШИБКИ":
{errors_text}

ИНСТРУКЦИИ:
1. Для каждой найденной "ошибки" определите, является ли она реальной ошибкой
2. Учитывайте контекст использования слова
3. Учитывайте, что это деловой документ с техническими терминами, именами, названиями организаций
4. Учитывайте, что могут быть сокращения, аббревиатуры, коды
5. Учитывайте, что могут быть английские слова в деловом контексте

ОТВЕТЬТЕ В ФОРМАТЕ JSON:
{{
    "verified_errors": [
        {{
            "word": "слово",
            "is_real_error": true/false,
            "reason": "объяснение решения",
            "confidence": 0.0-1.0
        }}
    ]
}}

Если слово является реальной ошибкой, установите "is_real_error": true.
Если слово корректно в данном контексте, установите "is_real_error": false.
"""
        
        # Вызываем LLM
        selected_model = settings_db.get("selected_llm_model", "llama3.1:8b")
        llm_result = await call_vllm_service(prompt, selected_model)
        
        if "response" not in llm_result:
            logger.warning("LLM проверка не удалась, возвращаем исходные ошибки")
            return errors
        
        # Парсим ответ LLM
        try:
            llm_response = llm_result["response"]
            # Извлекаем JSON из ответа
            import re
            json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
            if json_match:
                llm_analysis = json.loads(json_match.group())
                verified_errors = llm_analysis.get("verified_errors", [])
                
                # Фильтруем ошибки на основе анализа LLM
                real_errors = []
                for i, error in enumerate(errors):
                    if i < len(verified_errors):
                        verification = verified_errors[i]
                        if verification.get("is_real_error", True):  # По умолчанию считаем ошибкой
                            # Добавляем информацию от LLM
                            error["llm_verification"] = {
                                "is_real_error": verification.get("is_real_error", True),
                                "reason": verification.get("reason", ""),
                                "confidence": verification.get("confidence", 0.8)
                            }
                            real_errors.append(error)
                        else:
                            logger.info(f"LLM исключил ложное срабатывание: {error.get('word', '')} - {verification.get('reason', '')}")
                    else:
                        # Если LLM не проанализировал эту ошибку, оставляем её
                        real_errors.append(error)
                
                logger.info(f"LLM проверка завершена: {len(errors)} -> {len(real_errors)} ошибок")
                return real_errors
            else:
                logger.warning("Не удалось найти JSON в ответе LLM")
                return errors
                
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON от LLM: {e}")
            return errors
            
    except Exception as e:
        logger.error(f"Ошибка двойной проверки через LLM: {e}")
        return errors

async def fallback_spell_check(text: str) -> Dict[str, Any]:
    """Резервная проверка орфографии и грамматики (упрощенная)"""
    try:
        # Простая проверка на основе эвристических правил
        words = text.split()
        total_words = len([w for w in words if w.isalpha()])
        
        # Простая проверка на избыточность
        grammar_errors = []
        if "это есть" in text.lower():
            grammar_errors.append({
                "message": "Возможная избыточность: 'это есть'",
                "context": "это есть",
                "offset": text.lower().find("это есть"),
                "length": 8,
                "replacements": ["упростите выражение"],
                "rule_id": "REDUNDANCY",
                "type": "grammar",
                "confidence": 0.6
            })
        
        comprehensive_result = {
            "spelling": {
                "total_words": total_words,
                "misspelled_count": 0,
                "errors": [],
                "accuracy": 100.0,
                "method": "fallback"
            },
            "grammar": {
                "errors": grammar_errors,
                "total_errors": len(grammar_errors),
                "method": "fallback"
            },
            "total_errors": len(grammar_errors),
            "all_errors": grammar_errors,
            "overall_accuracy": max(0, (total_words - len(grammar_errors)) / total_words * 100) if total_words > 0 else 100
        }
        
        return {
            "status": "success",
            "text": text,
            "language": "ru",
            "comprehensive": comprehensive_result,
            "processing_time": 0.001,
            "method": "fallback"
        }
    except Exception as e:
        logger.error(f"Ошибка fallback проверки: {e}")
        return {
            "status": "error",
            "text": text,
            "language": "ru",
            "comprehensive": {
                "spelling": {"total_words": 0, "misspelled_count": 0, "errors": [], "accuracy": 0},
                "grammar": {"errors": [], "total_errors": 0},
                "total_errors": 0,
                "all_errors": [],
                "overall_accuracy": 0
            },
            "processing_time": 0.001,
            "method": "error"
        }

app = FastAPI(title="Outgoing Control Service", version="1.0.0")

# CORS настройки
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Конфигурация
UPLOAD_DIR = "uploads/outgoing_control"
REPORTS_DIR = "reports/outgoing_control"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

# Инициализация сервисов (спелчекер временно отключен)
# spell_checker = SpellChecker(language='ru')

# База данных в памяти (в реальном проекте использовать PostgreSQL)
documents_db = {}
reports_db = {}
settings_db = {
    "llm_prompt": """Вы - эксперт по выходному контролю технической документации (ТДО). 
Ваша задача - проверить исходящую корреспонденцию на соответствие требованиям ТДО.

АНАЛИЗ РЕЗУЛЬТАТОВ SPELLCHECKER:
Перед началом анализа внимательно изучите результаты автоматической проверки орфографии и грамматики. Ваша задача - исключить ложные срабатывания и сосредоточиться на реальных ошибках.

РЕЗУЛЬТАТЫ АВТОМАТИЧЕСКОЙ ПРОВЕРКИ:
{spell_check_results}

ИНСТРУКЦИИ ПО АНАЛИЗУ SPELLCHECKER:
1. Проанализируйте каждую найденную "ошибку" в контексте документа
2. Исключите ложные срабатывания (технические термины, имена, сокращения, коды)
3. Оставьте только реальные орфографические и грамматические ошибки
4. Учитывайте деловой стиль и корпоративную терминологию

ОСНОВНЫЕ КРИТЕРИИ ПРОВЕРКИ:

1. **ДЕЛОВОЙ СТИЛЬ:**
   - Соответствие корпоративным стандартам
   - Профессиональная лексика и терминология
   - Структурированность изложения
   - Официально-деловой тон

2. **КОРПОРАТИВНАЯ ЭТИКА:**
   - Соблюдение делового этикета
   - Корректность обращений и подписей
   - Соответствие корпоративным стандартам
   - Профессиональная вежливость

3. **ПОЛНОТА И ЛОГИКА:**
   - Полнота изложения материала
   - Логическая структура документа
   - Последовательность изложения
   - Наличие всех необходимых разделов

4. **ЮРИДИЧЕСКАЯ И ФАКТОЛОГИЧЕСКАЯ ТОЧНОСТЬ:**
   - Корректность ссылок на нормативные документы
   - Точность технических данных
   - Соответствие ГОСТам и СНиПам
   - Правильность расчетов и формул

5. **ЯЗЫКОВЫЕ АСПЕКТЫ (после фильтрации spellchecker):**
   - Реальные орфографические ошибки
   - Грамматические нарушения
   - Стилистическая корректность
   - Терминологическая точность

СТРУКТУРА ОТЧЕТА:

## АНАЛИЗ РЕЗУЛЬТАТОВ SPELLCHECKER
- **Всего найдено ошибок**: [количество]
- **Реальные ошибки**: [количество после фильтрации]
- **Исключенные ложные срабатывания**: [количество и причины]

## ДЕЛОВОЙ СТИЛЬ
- **Статус**: [соответствует/требует доработки]
- **Найденные нарушения**: [список]
- **Рекомендации**: [список]

## КОРПОРАТИВНАЯ ЭТИКА
- **Статус**: [соответствует/требует доработки]
- **Найденные нарушения**: [список]
- **Рекомендации**: [список]

## ПОЛНОТА И ЛОГИКА
- **Статус**: [соответствует/требует доработки]
- **Найденные нарушения**: [список]
- **Рекомендации**: [список]

## ЮРИДИЧЕСКАЯ И ФАКТОЛОГИЧЕСКАЯ ТОЧНОСТЬ
- **Статус**: [соответствует/требует доработки]
- **Найденные нарушения**: [список]
- **Рекомендации**: [список]

## ЯЗЫКОВЫЕ АСПЕКТЫ
- **Реальные орфографические ошибки**: [детальный список с контекстом и оценкой эксперта]
- **Грамматические нарушения**: [список]
- **Стилистические замечания**: [список]

### ДЕТАЛЬНЫЙ ПЕРЕЧЕНЬ ОРФОГРАФИЧЕСКИХ ОШИБОК:
Для каждой найденной ошибки укажите:
1. **Слово с ошибкой**: [исходное слово]
2. **Контекст**: [предложение или фраза, где найдена ошибка]
3. **Оценка эксперта**: [реальная ошибка/ложное срабатывание]
4. **Обоснование**: [почему это ошибка или почему это корректно]
5. **Правильное написание**: [если это ошибка]
6. **Влияние на документ**: [критично/незначительно/не влияет]

## ЦЕЛЕСООБРАЗНОСТЬ ОТПРАВКИ
- **ВЕРДИКТ**: [ГОТОВ К ОТПРАВКЕ/ТРЕБУЕТ ДОРАБОТКИ/НЕ ГОТОВ К ОТПРАВКЕ]
- **Обоснование**: [детальное обоснование решения]
- **Критические нарушения**: [список критических нарушений, если есть]
- **Рекомендации по доработке**: [приоритетный список исправлений]

ДОКУМЕНТ ДЛЯ ПРОВЕРКИ:
{text}

Начните анализ с изучения результатов spellchecker и исключения ложных срабатываний, затем проведите комплексную проверку по всем критериям.""",
    "selected_llm_model": "llama3.1:8b"
}

# Промпт для эксперта выходного контроля ТДО
EXPERT_PROMPT = """
Вы - эксперт по выходному контролю технической документации (ТДО). 
Ваша задача - проверить исходящую корреспонденцию на соответствие требованиям ТДО.

АНАЛИЗ РЕЗУЛЬТАТОВ SPELLCHECKER:
Перед началом анализа внимательно изучите результаты автоматической проверки орфографии и грамматики. Ваша задача - исключить ложные срабатывания и сосредоточиться на реальных ошибках.

РЕЗУЛЬТАТЫ АВТОМАТИЧЕСКОЙ ПРОВЕРКИ:
{spell_check_results}

ИНСТРУКЦИИ ПО АНАЛИЗУ SPELLCHECKER:
1. Проанализируйте каждую найденную "ошибку" в контексте документа
2. Исключите ложные срабатывания (технические термины, имена, сокращения, коды)
3. Оставьте только реальные орфографические и грамматические ошибки
4. Учитывайте деловой стиль и корпоративную терминологию

ОСНОВНЫЕ КРИТЕРИИ ПРОВЕРКИ:

1. **ДЕЛОВОЙ СТИЛЬ:**
   - Соответствие корпоративным стандартам
   - Профессиональная лексика и терминология
   - Структурированность изложения
   - Официально-деловой тон

2. **КОРПОРАТИВНАЯ ЭТИКА:**
   - Соблюдение делового этикета
   - Корректность обращений и подписей
   - Соответствие корпоративным стандартам
   - Профессиональная вежливость

3. **ПОЛНОТА И ЛОГИКА:**
   - Полнота изложения материала
   - Логическая структура документа
   - Последовательность изложения
   - Наличие всех необходимых разделов

4. **ЮРИДИЧЕСКАЯ И ФАКТОЛОГИЧЕСКАЯ ТОЧНОСТЬ:**
   - Корректность ссылок на нормативные документы
   - Точность технических данных
   - Соответствие ГОСТам и СНиПам
   - Правильность расчетов и формул

5. **ЯЗЫКОВЫЕ АСПЕКТЫ (после фильтрации spellchecker):**
   - Реальные орфографические ошибки
   - Грамматические нарушения
   - Стилистическая корректность
   - Терминологическая точность

СТРУКТУРА ОТЧЕТА:

## АНАЛИЗ РЕЗУЛЬТАТОВ SPELLCHECKER
- **Всего найдено ошибок**: [количество]
- **Реальные ошибки**: [количество после фильтрации]
- **Исключенные ложные срабатывания**: [количество и причины]

## ДЕЛОВОЙ СТИЛЬ
- **Статус**: [соответствует/требует доработки]
- **Найденные нарушения**: [список]
- **Рекомендации**: [список]

## КОРПОРАТИВНАЯ ЭТИКА
- **Статус**: [соответствует/требует доработки]
- **Найденные нарушения**: [список]
- **Рекомендации**: [список]

## ПОЛНОТА И ЛОГИКА
- **Статус**: [соответствует/требует доработки]
- **Найденные нарушения**: [список]
- **Рекомендации**: [список]

## ЮРИДИЧЕСКАЯ И ФАКТОЛОГИЧЕСКАЯ ТОЧНОСТЬ
- **Статус**: [соответствует/требует доработки]
- **Найденные нарушения**: [список]
- **Рекомендации**: [список]

## ЯЗЫКОВЫЕ АСПЕКТЫ
- **Реальные орфографические ошибки**: [детальный список с контекстом и оценкой эксперта]
- **Грамматические нарушения**: [список]
- **Стилистические замечания**: [список]

### ДЕТАЛЬНЫЙ ПЕРЕЧЕНЬ ОРФОГРАФИЧЕСКИХ ОШИБОК:
Для каждой найденной ошибки укажите:
1. **Слово с ошибкой**: [исходное слово]
2. **Контекст**: [предложение или фраза, где найдена ошибка]
3. **Оценка эксперта**: [реальная ошибка/ложное срабатывание]
4. **Обоснование**: [почему это ошибка или почему это корректно]
5. **Правильное написание**: [если это ошибка]
6. **Влияние на документ**: [критично/незначительно/не влияет]

## ЦЕЛЕСООБРАЗНОСТЬ ОТПРАВКИ
- **ВЕРДИКТ**: [ГОТОВ К ОТПРАВКЕ/ТРЕБУЕТ ДОРАБОТКИ/НЕ ГОТОВ К ОТПРАВКЕ]
- **Обоснование**: [детальное обоснование решения]
- **Критические нарушения**: [список критических нарушений, если есть]
- **Рекомендации по доработке**: [приоритетный список исправлений]

ДОКУМЕНТ ДЛЯ ПРОВЕРКИ:
{text}

Начните анализ с изучения результатов spellchecker и исключения ложных срабатываний, затем проведите комплексную проверку по всем критериям.
"""

@app.get("/health")
async def health_check():
    """Проверка состояния сервиса"""
    # Проверяем доступность spellchecker-service
    spellchecker_status = "unknown"
    try:
        response = requests.get(f"{SPELLCHECKER_SERVICE_URL}/health", timeout=5)
        if response.status_code == 200:
            spellchecker_data = response.json()
            spellchecker_status = spellchecker_data.get("status", "unknown")
    except Exception as e:
        logger.warning(f"Spellchecker service недоступен: {e}")
        spellchecker_status = "unavailable"
    
    return {
        "status": "healthy", 
        "service": "outgoing_control",
        "spellchecker_service": spellchecker_status
    }

@app.get("/spellchecker-status")
async def get_spellchecker_status():
    """Получение статуса spellchecker-service"""
    try:
        response = requests.get(f"{SPELLCHECKER_SERVICE_URL}/health", timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            return {"status": "error", "message": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/spellchecker-stats")
async def get_spellchecker_stats():
    """Получение статистики spellchecker-service"""
    try:
        response = requests.get(f"{SPELLCHECKER_SERVICE_URL}/stats", timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            return {"status": "error", "message": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/settings")
async def get_settings():
    """Получение настроек"""
    return settings_db


@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Загрузка документа для проверки"""
    try:
        # Генерируем уникальный ID документа
        document_id = str(uuid.uuid4())
        
        # Сохраняем файл
        file_path = os.path.join(UPLOAD_DIR, f"{document_id}_{file.filename}")
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Парсим документ
        parsed_content = await parse_document(file_path)
        
        # Сохраняем информацию о документе
        upload_time = datetime.now().isoformat()
        document_info = {
            "id": document_id,
            "filename": file.filename,
            "title": file.filename.replace('.pdf', '').replace('.doc', '').replace('.docx', ''),
            "file_path": file_path,
            "text": parsed_content["text"],
            "pages": parsed_content["pages"],
            "chunks": parsed_content["chunks"],
            "status": "uploaded",
            "created_at": upload_time,
            "uploaded_at": upload_time,
            "spell_check_results": None,
            "expert_analysis": None,
            "consolidated_report": None
        }
        
        documents_db[document_id] = document_info
        
        return {
            "status": "success",
            "document_id": document_id,
            "filename": file.filename,
            "text": parsed_content["text"],
            "pages_count": len(parsed_content["pages"]),
            "chunks_count": len(parsed_content["chunks"])
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка загрузки документа: {str(e)}")

@app.post("/spellcheck")
async def spell_check_document(request: Dict[str, Any]):
    """Проверка орфографии документа с помощью spellchecker-service"""
    try:
        document_id = request["document_id"]
        
        if document_id not in documents_db:
            raise HTTPException(status_code=404, detail="Документ не найден")
        
        # Получаем текст документа
        document = documents_db[document_id]
        text = document["text"]
        
        # Используем spellchecker-service
        logger.info(f"Начинаем проверку орфографии для документа {document_id} через spellchecker-service")
        spell_check_result = await call_spellchecker_service(text, "spellcheck")
        
        if spell_check_result["status"] == "success":
            spell_check_results = spell_check_result["spelling"]
            
            # Двойная проверка найденных ошибок через LLM
            errors = spell_check_results.get("errors", [])
            if errors:
                logger.info(f"Начинаем двойную проверку {len(errors)} орфографических ошибок через LLM")
                verified_errors = await double_check_errors_with_llm(text, errors)
                
                # Обновляем результаты с проверенными ошибками
                spell_check_results["errors"] = verified_errors
                spell_check_results["misspelled_count"] = len(verified_errors)
                
                logger.info(f"Двойная проверка орфографии завершена: {len(errors)} -> {len(verified_errors)} ошибок")
            
            documents_db[document_id]["spell_check_results"] = spell_check_results
            documents_db[document_id]["spell_check_debug_info"] = spell_check_result.get("debug_info", {})
            documents_db[document_id]["status"] = "spell_checked"
            
            logger.info(f"Проверка орфографии завершена для документа {document_id}: {spell_check_results['misspelled_count']} ошибок")
            
            return {
                "status": "success",
                "spell_check_results": spell_check_results,
                "method": spell_check_result.get("method", "unknown")
            }
        else:
            raise HTTPException(status_code=500, detail="Ошибка spellchecker-service")
        
    except Exception as e:
        logger.error(f"Ошибка проверки орфографии: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка проверки орфографии: {str(e)}")

@app.post("/grammar-check")
async def grammar_check_document(request: Dict[str, Any]):
    """Проверка грамматики документа с помощью spellchecker-service"""
    try:
        document_id = request["document_id"]
        
        if document_id not in documents_db:
            raise HTTPException(status_code=404, detail="Документ не найден")
        
        # Получаем текст документа
        document = documents_db[document_id]
        text = document["text"]
        
        # Используем spellchecker-service
        logger.info(f"Начинаем проверку грамматики для документа {document_id} через spellchecker-service")
        grammar_check_result = await call_spellchecker_service(text, "grammar-check")
        
        if grammar_check_result["status"] == "success":
            grammar_results = grammar_check_result["grammar"]
            
            # Двойная проверка найденных ошибок через LLM
            errors = grammar_results.get("errors", [])
            if errors:
                logger.info(f"Начинаем двойную проверку {len(errors)} грамматических ошибок через LLM")
                verified_errors = await double_check_errors_with_llm(text, errors)
                
                # Обновляем результаты с проверенными ошибками
                grammar_results["errors"] = verified_errors
                grammar_results["total_errors"] = len(verified_errors)
                
                logger.info(f"Двойная проверка грамматики завершена: {len(errors)} -> {len(verified_errors)} ошибок")
            
            # Сохраняем результаты
            if "grammar_check_results" not in documents_db[document_id]:
                documents_db[document_id]["grammar_check_results"] = {}
            
            documents_db[document_id]["grammar_check_results"] = grammar_results
            documents_db[document_id]["grammar_check_debug_info"] = grammar_check_result.get("debug_info", {})
            
            logger.info(f"Проверка грамматики завершена для документа {document_id}: {grammar_results['total_errors']} ошибок")
            
            return {
                "status": "success",
                "grammar_results": grammar_results,
                "method": grammar_check_result.get("method", "unknown")
            }
        else:
            raise HTTPException(status_code=500, detail="Ошибка spellchecker-service")
        
    except Exception as e:
        logger.error(f"Ошибка проверки грамматики: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка проверки грамматики: {str(e)}")

@app.post("/comprehensive-check")
async def comprehensive_check_document(request: Dict[str, Any]):
    """Комплексная проверка орфографии и грамматики с помощью spellchecker-service"""
    try:
        document_id = request["document_id"]
        
        if document_id not in documents_db:
            raise HTTPException(status_code=404, detail="Документ не найден")
        
        # Получаем текст документа
        document = documents_db[document_id]
        text = document["text"]
        
        # Используем spellchecker-service для комплексной проверки
        logger.info(f"Начинаем комплексную проверку для документа {document_id} через spellchecker-service")
        comprehensive_result = await call_spellchecker_service(text, "comprehensive")
        
        if comprehensive_result["status"] == "success":
            comprehensive_results = comprehensive_result["comprehensive"]
            
            # Двойная проверка найденных ошибок через LLM
            all_errors = comprehensive_results.get("all_errors", [])
            if all_errors:
                logger.info(f"Начинаем двойную проверку {len(all_errors)} ошибок через LLM")
                verified_errors = await double_check_errors_with_llm(text, all_errors)
                
                # Обновляем результаты с проверенными ошибками
                comprehensive_results["all_errors"] = verified_errors
                comprehensive_results["total_errors"] = len(verified_errors)
                
                # Обновляем ошибки орфографии и грамматики отдельно
                spelling_errors = [e for e in verified_errors if e.get("type") == "spelling"]
                grammar_errors = [e for e in verified_errors if e.get("type") == "grammar"]
                
                if "spelling" in comprehensive_results:
                    comprehensive_results["spelling"]["errors"] = spelling_errors
                    comprehensive_results["spelling"]["misspelled_count"] = len(spelling_errors)
                
                if "grammar" in comprehensive_results:
                    comprehensive_results["grammar"]["errors"] = grammar_errors
                    comprehensive_results["grammar"]["total_errors"] = len(grammar_errors)
                
                logger.info(f"Двойная проверка завершена: {len(all_errors)} -> {len(verified_errors)} ошибок")
            
            # Сохраняем результаты
            documents_db[document_id]["comprehensive_check_results"] = comprehensive_results
            documents_db[document_id]["comprehensive_check_debug_info"] = comprehensive_result.get("debug_info", {})
            documents_db[document_id]["status"] = "comprehensively_checked"
            
            logger.info(f"Комплексная проверка завершена для документа {document_id}: {comprehensive_results['total_errors']} ошибок")
            
            return {
                "status": "success",
                "comprehensive_results": comprehensive_results,
                "method": comprehensive_result.get("method", "unknown"),
                "processing_time": comprehensive_result.get("processing_time", 0)
            }
        else:
            raise HTTPException(status_code=500, detail="Ошибка spellchecker-service")
        
    except Exception as e:
        logger.error(f"Ошибка комплексной проверки: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка комплексной проверки: {str(e)}")

@app.post("/expert-analysis")
async def expert_analysis(request: Dict[str, Any]):
    """Экспертная проверка документа"""
    try:
        document_id = request["document_id"]
        
        if document_id not in documents_db:
            raise HTTPException(status_code=404, detail="Документ не найден")
        
        # Получаем данные из базы данных
        document = documents_db[document_id]
        text = document["text"]
        spell_check_results = document.get("spell_check_results", {})
        
        # Если нет результатов проверки орфографии, выполняем проверку
        spell_check_debug_info = {}
        if not spell_check_results:
            logger.info(f"Выполняем проверку орфографии для документа {document_id}")
            spell_check_result = await call_spellchecker_service(text, "spellcheck")
            if spell_check_result["status"] == "success":
                spell_check_results = spell_check_result["spelling"]
                spell_check_debug_info = spell_check_result.get("debug_info", {})
                documents_db[document_id]["spell_check_results"] = spell_check_results
                documents_db[document_id]["spell_check_debug_info"] = spell_check_debug_info
            else:
                spell_check_results = {"errors": [], "accuracy": 100}
        else:
            # Получаем сохраненную отладочную информацию
            spell_check_debug_info = documents_db[document_id].get("spell_check_debug_info", {})
        
        # Формируем промпт для эксперта (используем настраиваемый промпт)
        prompt = settings_db.get("llm_prompt", EXPERT_PROMPT).format(
            text=text,
            spell_check_results=json.dumps(spell_check_results, ensure_ascii=False, indent=2)
        )
        
        # Вызываем LLM для экспертного анализа
        selected_model = settings_db.get("selected_llm_model", "llama3.1:8b")
        logger.info(f"Начинаем экспертный анализ документа {document_id} через LLM с моделью {selected_model}")
        llm_result = await call_vllm_service(prompt, selected_model)
        
        if "response" in llm_result:
            analysis_text = llm_result["response"]
            logger.info(f"LLM анализ завершен для документа {document_id}")
        else:
            logger.warning("LLM анализ не удался, используем упрощенный анализ")
            # Fallback анализ
            error_count = len(spell_check_results.get('errors', []))
            accuracy = spell_check_results.get('accuracy', 0)
            
            analysis_text = f"""
            ЭКСПЕРТНЫЙ АНАЛИЗ ДОКУМЕНТА (УПРОЩЕННЫЙ)
            
            Документ: {document_id}
            Дата анализа: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            
            РЕЗУЛЬТАТЫ ОРФОГРАФИЧЕСКОЙ ПРОВЕРКИ:
            - Найдено ошибок: {error_count}
            - Точность: {accuracy:.1f}%
            
            ВЕРДИКТ: {'ДОКУМЕНТ ГОТОВ К ОТПРАВКЕ' if error_count == 0 else 'ТРЕБУЕТСЯ ДОРАБОТКА'}
            
            ОБЩАЯ ОЦЕНКА:
            Документ прошел базовую проверку. Рекомендуется исправить орфографические ошибки перед отправкой.
            """
        
        # Парсим детальный анализ от LLM
        detailed_errors = []
        if "response" in llm_result:
            detailed_errors = parse_llm_spelling_analysis(analysis_text, spell_check_results.get('errors', []))
        
        # Извлекаем вердикт из анализа LLM
        verdict = "ТРЕБУЕТСЯ ДОРАБОТКИ"
        verdict_color = "warning"
        
        if "ГОТОВ К ОТПРАВКЕ" in analysis_text.upper():
            verdict = "ДОКУМЕНТ ГОТОВ К ОТПРАВКЕ"
            verdict_color = "success"
        elif "НЕ ГОТОВ К ОТПРАВКЕ" in analysis_text.upper():
            verdict = "НЕ ГОТОВ К ОТПРАВКЕ"
            verdict_color = "error"
        elif "ТРЕБУЕТ ДОРАБОТКИ" in analysis_text.upper():
            verdict = "ТРЕБУЕТСЯ ДОРАБОТКИ"
            verdict_color = "warning"
        
        # Определяем общий балл на основе вердикта
        if verdict == "ДОКУМЕНТ ГОТОВ К ОТПРАВКЕ":
            overall_score = 90
            compliance_status = "compliant"
        elif verdict == "ТРЕБУЕТСЯ ДОРАБОТКИ":
            overall_score = 60
            compliance_status = "partial"
        else:
            overall_score = 30
            compliance_status = "non_compliant"
        
        # Собираем отладочную информацию
        debug_info = {
            "spellchecker_debug": spell_check_debug_info,
            "vllm_debug": llm_result.get('debug_info', {}),
            "analysis_generation_time": datetime.now().isoformat()
        }
        
        # Добавляем отладочную информацию в конец отчета
        debug_section = f"""

## ОТЛАДОЧНАЯ ИНФОРМАЦИЯ

### ИЗВЛЕЧЕННЫЙ ТЕКСТ ДОКУМЕНТА:
- **Размер текста**: {len(text)} символов
- **Количество строк**: {text.count(chr(10)) + 1}
- **Время извлечения**: {document.get('uploaded_at', 'N/A')}
- **Имя файла**: {document.get('filename', 'N/A')}

**СОДЕРЖИМОЕ ТЕКСТА:**
```
{text}
```

### SPELLCHECKER SERVICE:
- **Запрос отправлен**: {debug_info['spellchecker_debug'].get('spellchecker_request_time', 'N/A')}
- **Лог запроса**: {debug_info['spellchecker_debug'].get('spellchecker_request_log', 'N/A')}
- **Ответ получен**: {debug_info['spellchecker_debug'].get('spellchecker_response_time', 'N/A')}
- **Лог ответа**: {debug_info['spellchecker_debug'].get('spellchecker_response_log', 'N/A')}

### VLLM SERVICE:
- **Запрос отправлен**: {debug_info['vllm_debug'].get('vllm_request_time', 'N/A')}
- **Лог запроса**: {debug_info['vllm_debug'].get('vllm_request_log', 'N/A')}
- **Ответ получен**: {debug_info['vllm_debug'].get('vllm_response_time', 'N/A')}
- **Лог ответа**: {debug_info['vllm_debug'].get('vllm_response_log', 'N/A')}

### ОБЩАЯ ИНФОРМАЦИЯ:
- **Время генерации отчета**: {debug_info['analysis_generation_time']}
- **LLM использован**: {'Да' if "response" in llm_result else 'Нет'}
"""
        
        # Добавляем отладочную секцию к анализу
        analysis_text_with_debug = analysis_text + debug_section
        
        expert_analysis = {
            "analysis_text": analysis_text_with_debug,
            "overall_score": overall_score,
            "verdict": verdict,
            "verdict_color": verdict_color,
            "spelling_errors": spell_check_results.get('errors', []),
            "detailed_spelling_errors": detailed_errors,
            "spelling_accuracy": spell_check_results.get('accuracy', 0),
            "violations": [
                {
                    "type": "spelling",
                    "description": f"Найдено {len(spell_check_results.get('errors', []))} орфографических ошибок",
                    "severity": "medium"
                }
            ] if spell_check_results.get('errors') else [],
            "recommendations": [
                "Исправить орфографические ошибки",
                "Проверить соответствие стандартам оформления",
                "Убедиться в наличии всех необходимых подписей"
            ],
            "compliance_status": compliance_status,
            "generated_at": datetime.now().isoformat(),
            "llm_used": "response" in llm_result,
            "debug_info": debug_info
        }
        
        # Сохраняем результаты
        documents_db[document_id]["expert_analysis"] = expert_analysis
        documents_db[document_id]["status"] = "expert_analyzed"
        
        return {
            "status": "success",
            "expert_analysis": expert_analysis
        }
        
    except Exception as e:
        logger.error(f"Ошибка экспертного анализа: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка экспертного анализа: {str(e)}")

@app.post("/consolidate")
async def consolidate_results(request: Dict[str, Any]):
    """Консолидация результатов проверки"""
    try:
        document_id = request["document_id"]
        
        if document_id not in documents_db:
            raise HTTPException(status_code=404, detail="Документ не найден")
        
        # Получаем данные из базы данных
        document = documents_db[document_id]
        spell_check_results = document.get("spell_check_results", {})
        expert_analysis = document.get("expert_analysis", {})
        original_text = document["text"]
        
        # Создаем консолидированный отчет
        consolidated_report = {
            "document_id": document_id,
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_issues": len(spell_check_results.get("errors", [])) + len(expert_analysis.get("violations", [])),
                "spell_errors": len(spell_check_results.get("errors", [])),
                "expert_violations": len(expert_analysis.get("violations", [])),
                "overall_score": expert_analysis.get("overall_score", 0),
                "compliance_status": expert_analysis.get("compliance_status", "unknown")
            },
            "spell_check": spell_check_results,
            "expert_analysis": expert_analysis,
            "recommendations": generate_final_recommendations(spell_check_results, expert_analysis),
            "action_items": generate_action_items(spell_check_results, expert_analysis)
        }
        
        # Сохраняем отчет
        documents_db[document_id]["consolidated_report"] = consolidated_report
        documents_db[document_id]["status"] = "completed"
        
        # Сохраняем отчет в файл
        report_path = os.path.join(REPORTS_DIR, f"report_{document_id}.json")
        async with aiofiles.open(report_path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(consolidated_report, ensure_ascii=False, indent=2))
        
        return {
            "status": "success",
            "consolidated_report": consolidated_report
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка консолидации результатов: {str(e)}")

@app.get("/documents")
async def get_documents():
    """Получение списка документов"""
    return {
        "status": "success",
        "documents": list(documents_db.values())
    }

@app.get("/documents/{document_id}")
async def get_document(document_id: str):
    """Получение информации о документе"""
    if document_id not in documents_db:
        raise HTTPException(status_code=404, detail="Документ не найден")
    
    return {
        "status": "success",
        "document": documents_db[document_id]
    }

@app.get("/report/{document_id}")
async def get_report(document_id: str):
    """Получение отчета по документу"""
    if document_id not in documents_db:
        raise HTTPException(status_code=404, detail="Документ не найден")
    
    document = documents_db[document_id]
    if not document.get("consolidated_report"):
        raise HTTPException(status_code=404, detail="Отчет не готов")
    
    # Генерируем HTML отчет
    html_report = generate_html_report(document)
    
    return JSONResponse(
        content={"html_report": html_report},
        media_type="application/json"
    )

@app.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """Удаление документа"""
    if document_id not in documents_db:
        raise HTTPException(status_code=404, detail="Документ не найден")
    
    document = documents_db[document_id]
    
    # Удаляем файл
    if os.path.exists(document["file_path"]):
        os.remove(document["file_path"])
    
    # Удаляем отчет
    report_path = os.path.join(REPORTS_DIR, f"report_{document_id}.json")
    if os.path.exists(report_path):
        os.remove(report_path)
    
    # Удаляем из базы данных
    del documents_db[document_id]
    
    return {"status": "success", "message": "Документ удален"}

# Вспомогательные функции

# Функция extract_text_with_pdfminer удалена - используется общий модуль utils

# Функция clean_pdf_text удалена - используется clean_text из общего модуля utils

def clean_extracted_text(text: str) -> str:
    """Очистка извлеченного текста с использованием общего модуля utils"""
    return clean_text(text, preserve_structure=True)

def hierarchical_text_chunking(text: str) -> List[Dict[str, Any]]:
    """Иерархическое разделение текста на чанки с использованием общего модуля utils"""
    from utils import hierarchical_text_chunking as utils_hierarchical_chunking
    return utils_hierarchical_chunking(text)

async def parse_document(file_path: str) -> Dict[str, Any]:
    """Парсинг документа с использованием общего модуля utils"""
    try:
        # Используем универсальный парсер из модуля utils
        from utils import parse_document as utils_parse_document
        result = utils_parse_document(file_path)
        
        if not result.get("success", False):
            raise Exception(f"Ошибка парсинга документа: {result.get('error', 'Неизвестная ошибка')}")
        
        # Адаптируем результат к ожидаемому формату
        return {
            "text": result["text"],
            "pages": result.get("pages", []),
            "chunks": result.get("chunks", [])
        }
        
    except Exception as e:
        logger.error(f"❌ [DOCUMENT_PROCESS] Ошибка парсинга документа {file_path}: {e}")
        raise Exception(f"Ошибка парсинга документа: {str(e)}")

def extract_score(analysis_text: str) -> int:
    """Извлечение общей оценки из текста анализа"""
    # Простая логика извлечения оценки (в реальном проекте использовать более сложную)
    if "отлично" in analysis_text.lower() or "excellent" in analysis_text.lower():
        return 90
    elif "хорошо" in analysis_text.lower() or "good" in analysis_text.lower():
        return 75
    elif "удовлетворительно" in analysis_text.lower() or "satisfactory" in analysis_text.lower():
        return 60
    elif "неудовлетворительно" in analysis_text.lower() or "unsatisfactory" in analysis_text.lower():
        return 30
    else:
        return 50

def extract_violations(analysis_text: str) -> List[Dict[str, str]]:
    """Извлечение нарушений из текста анализа"""
    violations = []
    # Простая логика извлечения нарушений
    lines = analysis_text.split('\n')
    for line in lines:
        if any(keyword in line.lower() for keyword in ['нарушение', 'ошибка', 'несоответствие', 'проблема']):
            violations.append({
                "type": "general",
                "description": line.strip(),
                "severity": "medium"
            })
    return violations

def extract_recommendations(analysis_text: str) -> List[str]:
    """Извлечение рекомендаций из текста анализа"""
    recommendations = []
    lines = analysis_text.split('\n')
    for line in lines:
        if any(keyword in line.lower() for keyword in ['рекомендуется', 'необходимо', 'следует', 'требуется']):
            recommendations.append(line.strip())
    return recommendations

def determine_compliance(analysis_text: str) -> str:
    """Определение статуса соответствия"""
    if "соответствует" in analysis_text.lower() or "compliant" in analysis_text.lower():
        return "compliant"
    elif "не соответствует" in analysis_text.lower() or "non-compliant" in analysis_text.lower():
        return "non-compliant"
    else:
        return "partial"

def generate_final_recommendations(spell_check: Dict, expert_analysis: Dict) -> List[str]:
    """Генерация финальных рекомендаций"""
    recommendations = []
    
    # Рекомендации по орфографии
    if spell_check.get("misspelled_count", 0) > 0:
        recommendations.append(f"Исправить {spell_check['misspelled_count']} орфографических ошибок")
    
    # Рекомендации эксперта
    expert_recs = expert_analysis.get("recommendations", [])
    recommendations.extend(expert_recs)
    
    return recommendations

def generate_action_items(spell_check: Dict, expert_analysis: Dict) -> List[Dict[str, str]]:
    """Генерация пунктов действий"""
    action_items = []
    
    # Действия по орфографии
    for error in spell_check.get("errors", []):
        action_items.append({
            "type": "spell_check",
            "description": f"Исправить слово '{error['word']}' в контексте: {error['context'][:100]}...",
            "priority": "high",
            "suggestions": error.get("suggestions", [])
        })
    
    # Действия по экспертному анализу
    for violation in expert_analysis.get("violations", []):
        action_items.append({
            "type": "expert_violation",
            "description": violation.get("description", ""),
            "priority": "medium",
            "severity": violation.get("severity", "medium")
        })
    
    return action_items

def generate_html_report(document: Dict[str, Any]) -> str:
    """Генерация HTML отчета"""
    expert_analysis = document.get("expert_analysis", {})
    spell_check = document.get("spell_check_results", {})
    
    # Получаем данные
    verdict = expert_analysis.get("verdict", "НЕ ОПРЕДЕЛЕН")
    verdict_color = expert_analysis.get("verdict_color", "warning")
    spelling_errors = expert_analysis.get("spelling_errors", [])
    spelling_accuracy = expert_analysis.get("spelling_accuracy", 0)
    overall_score = expert_analysis.get("overall_score", 0)
    violations = expert_analysis.get("violations", [])
    recommendations = expert_analysis.get("recommendations", [])
    
    # Генерируем HTML для орфографических ошибок
    spelling_errors_html = ""
    if spelling_errors:
        spelling_errors_html = "<h4>Найденные орфографические ошибки:</h4><ul>"
        for i, error in enumerate(spelling_errors, 1):
            suggestions = error.get('suggestions', [])
            suggestions_text = f" (предложения: {', '.join(suggestions[:3])})" if suggestions else ""
            spelling_errors_html += f"""
            <li>
                <strong>{i}. Слово: "{error.get('word', 'N/A')}"</strong><br>
                <em>Контекст:</em> {error.get('context', 'N/A')}{suggestions_text}
            </li>
            """
        spelling_errors_html += "</ul>"
    else:
        spelling_errors_html = "<p class='success'>✅ Орфографических ошибок не найдено</p>"
    
    # Определяем цвет вердикта
    verdict_class = {
        "success": "success",
        "warning": "warning", 
        "error": "error"
    }.get(verdict_color, "warning")
    
    html = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Отчет по выходному контролю - {document['filename']}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
            .header {{ text-align: center; margin-bottom: 30px; border-bottom: 2px solid #333; padding-bottom: 20px; }}
            .section {{ margin: 20px 0; }}
            .section-title {{ font-size: 18px; font-weight: bold; color: #2c3e50; margin-bottom: 15px; border-bottom: 1px solid #3498db; padding-bottom: 5px; }}
            .summary {{ background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }}
            .verdict {{ padding: 15px; border-radius: 8px; margin: 20px 0; text-align: center; font-weight: bold; font-size: 18px; }}
            .verdict.success {{ background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }}
            .verdict.warning {{ background-color: #fff3cd; color: #856404; border: 1px solid #ffeaa7; }}
            .verdict.error {{ background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }}
            .error {{ color: #e74c3c; }}
            .warning {{ color: #f39c12; }}
            .success {{ color: #27ae60; }}
            .recommendation {{ background-color: #e8f4fd; padding: 10px; margin: 10px 0; border-left: 4px solid #3498db; }}
            .action-item {{ background-color: #fff3cd; padding: 10px; margin: 10px 0; border-left: 4px solid #ffc107; }}
            .spelling-errors {{ background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin: 15px 0; }}
            .spelling-errors ul {{ margin: 10px 0; padding-left: 20px; }}
            .spelling-errors li {{ margin: 10px 0; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Отчет по выходному контролю корреспонденции</h1>
            <h2>{document['filename']}</h2>
            <p>Дата создания: {document['created_at']}</p>
        </div>
        
        <div class="verdict {verdict_class}">
            ВЕРДИКТ: {verdict}
        </div>
        
        <div class="summary">
            <h3>Сводка</h3>
            <p><strong>Общая оценка:</strong> {overall_score}/100</p>
            <p><strong>Орфографических ошибок:</strong> {len(spelling_errors)}</p>
            <p><strong>Точность орфографии:</strong> {spelling_accuracy:.1f}%</p>
            <p><strong>Нарушений:</strong> {len(violations)}</p>
        </div>
        
        <div class="section">
            <h3 class="section-title">Орфографическая проверка</h3>
            <div class="spelling-errors">
                {spelling_errors_html}
            </div>
        </div>
        
        <div class="section">
            <h3 class="section-title">Рекомендации</h3>
            {''.join([f'<div class="recommendation">{rec}</div>' for rec in recommendations])}
        </div>
        
        <div class="section">
            <h3 class="section-title">Детальный анализ эксперта</h3>
            <div style="white-space: pre-line; background-color: #f8f9fa; padding: 15px; border-radius: 8px;">
                {expert_analysis.get('analysis_text', 'Анализ недоступен')}
            </div>
        </div>
    </body>
    </html>
    """
    
    return html

@app.get("/settings")
async def get_settings():
    """Получение настроек системы"""
    return {
        "llm_prompt": settings_db.get("llm_prompt", ""),
        "selected_llm_model": settings_db.get("selected_llm_model", "llama3.1:8b")
    }

@app.post("/settings")
async def update_settings(request: Dict[str, Any]):
    """Обновление настроек системы"""
    try:
        if "llm_prompt" in request:
            settings_db["llm_prompt"] = request["llm_prompt"]
        
        if "selected_llm_model" in request:
            settings_db["selected_llm_model"] = request["selected_llm_model"]
        
        logger.info(f"Настройки обновлены: {request}")
        return {"status": "success", "message": "Настройки успешно обновлены"}
    except Exception as e:
        logger.error(f"Ошибка обновления настроек: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка обновления настроек: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8006)
