"""
Сервис классификации намерений запроса для нормативных документов
"""

import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import requests
import os
from datetime import datetime

logger = logging.getLogger(__name__)

# Получаем URL Ollama из переменной окружения
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434")

class IntentType(Enum):
    """Типы намерений запроса"""
    DEFINITION = "definition"           # Определения и термины
    APPLICABILITY = "applicability"     # Область применения
    REQUIREMENTS = "requirements"       # Требования и обязательства
    PROCEDURE = "procedure"            # Процедуры и методы
    EXCEPTIONS = "exceptions"          # Исключения и особые случаи
    GENERAL = "general"                # Общие вопросы

@dataclass
class IntentClassification:
    """Результат классификации намерения"""
    intent_type: IntentType
    confidence: float
    keywords: List[str]
    reasoning: str
    suggested_sections: List[str]

@dataclass
class QueryRewriting:
    """Результат переписывания запроса"""
    original_query: str
    intent_type: IntentType
    rewritten_queries: List[str]
    section_filters: List[str]
    chunk_type_filters: List[str]

class IntentClassifierService:
    """Сервис для классификации намерений запроса"""
    
    def __init__(self, ollama_url: str = None, model_name: str = "llama3.1:8b"):
        self.ollama_url = ollama_url or OLLAMA_URL
        self.model_name = model_name
        
        # Ключевые слова для каждого типа намерения
        self.intent_keywords = {
            IntentType.DEFINITION: [
                "определение", "термин", "понятие", "что такое", "означает", "расшифровка",
                "аббревиатура", "сокращение", "значение", "смысл", "определить", "описать",
                "классификация", "тип", "вид", "категория", "группа", "разновидность"
            ],
            IntentType.APPLICABILITY: [
                "применение", "область", "сфера", "где", "когда", "для чего", "назначение",
                "использование", "применимо", "подходит", "соответствует", "относится",
                "распространяется", "действует", "действительно", "актуально", "релевантно"
            ],
            IntentType.REQUIREMENTS: [
                "требование", "обязательно", "должен", "необходимо", "нужно", "следует",
                "обязан", "требуется", "предусмотрено", "установлено", "определено",
                "норма", "стандарт", "критерий", "условие", "параметр", "характеристика",
                "показатель", "величина", "размер", "расстояние", "высота", "ширина"
            ],
            IntentType.PROCEDURE: [
                "процедура", "метод", "способ", "порядок", "алгоритм", "этап", "шаг",
                "выполнение", "осуществление", "проведение", "реализация", "применение",
                "действие", "операция", "процесс", "технология", "техника", "прием",
                "как", "каким образом", "последовательность", "стадия", "фаза"
            ],
            IntentType.EXCEPTIONS: [
                "исключение", "особый", "специальный", "отдельный", "частный", "конкретный",
                "не распространяется", "не применяется", "не относится", "не действует",
                "кроме", "за исключением", "помимо", "исключая", "не включая",
                "ограничение", "ограничено", "не допускается", "запрещено", "нельзя"
            ]
        }
        
        # Маппинг намерений на разделы документов
        self.intent_to_sections = {
            IntentType.DEFINITION: [
                "термины и определения", "определения", "термины", "понятия",
                "сокращения", "аббревиатуры", "глоссарий", "словарь терминов"
            ],
            IntentType.APPLICABILITY: [
                "область применения", "сфера применения", "назначение", "применение",
                "распространение", "действие", "применимость", "использование"
            ],
            IntentType.REQUIREMENTS: [
                "требования", "общие требования", "технические требования",
                "нормативные требования", "обязательные требования", "параметры",
                "характеристики", "показатели", "критерии", "условия"
            ],
            IntentType.PROCEDURE: [
                "методы", "процедуры", "порядок", "алгоритм", "этапы", "стадии",
                "выполнение", "осуществление", "проведение", "реализация",
                "технология", "техника", "приемы", "операции"
            ],
            IntentType.EXCEPTIONS: [
                "исключения", "особые случаи", "ограничения", "запреты",
                "не распространяется", "не применяется", "не относится"
            ]
        }
        
        # Маппинг намерений на типы чанков
        self.intent_to_chunk_types = {
            IntentType.DEFINITION: ["definition", "term", "glossary"],
            IntentType.APPLICABILITY: ["scope", "application", "coverage"],
            IntentType.REQUIREMENTS: ["requirement", "mandatory", "obligatory"],
            IntentType.PROCEDURE: ["procedure", "method", "process", "step"],
            IntentType.EXCEPTIONS: ["exception", "limitation", "restriction"]
        }
        
        logger.info(f"🎯 [INTENT_CLASSIFIER] Initialized with {self.model_name} at {self.ollama_url}")
    
    def classify_intent(self, query: str) -> IntentClassification:
        """
        Классификация намерения запроса
        
        Args:
            query: Поисковый запрос
            
        Returns:
            Результат классификации намерения
        """
        try:
            logger.info(f"🎯 [INTENT_CLASSIFIER] Classifying intent for query: '{query[:100]}...'")
            
            # Сначала пробуем правило-основанную классификацию
            rule_based_result = self._rule_based_classification(query)
            
            # Если уверенность высокая, используем результат
            if rule_based_result.confidence >= 0.8:
                logger.info(f"✅ [INTENT_CLASSIFIER] Rule-based classification: {rule_based_result.intent_type.value} (confidence: {rule_based_result.confidence:.3f})")
                return rule_based_result
            
            # Иначе используем ML-классификацию
            ml_result = self._ml_classification(query)
            
            # Выбираем лучший результат
            if ml_result.confidence > rule_based_result.confidence:
                logger.info(f"✅ [INTENT_CLASSIFIER] ML classification: {ml_result.intent_type.value} (confidence: {ml_result.confidence:.3f})")
                return ml_result
            else:
                logger.info(f"✅ [INTENT_CLASSIFIER] Rule-based classification: {rule_based_result.intent_type.value} (confidence: {rule_based_result.confidence:.3f})")
                return rule_based_result
                
        except Exception as e:
            logger.error(f"❌ [INTENT_CLASSIFIER] Error classifying intent: {e}")
            # Возвращаем общий тип при ошибке
            return IntentClassification(
                intent_type=IntentType.GENERAL,
                confidence=0.5,
                keywords=[],
                reasoning="Ошибка классификации, используется общий тип",
                suggested_sections=[]
            )
    
    def _rule_based_classification(self, query: str) -> IntentClassification:
        """Правило-основанная классификация намерения"""
        try:
            query_lower = query.lower()
            intent_scores = {}
            
            # Вычисляем скор-ы для каждого типа намерения
            for intent_type, keywords in self.intent_keywords.items():
                score = 0
                matched_keywords = []
                
                for keyword in keywords:
                    if keyword in query_lower:
                        score += 1
                        matched_keywords.append(keyword)
                
                # Нормализуем скор
                if keywords:
                    intent_scores[intent_type] = {
                        'score': score / len(keywords),
                        'keywords': matched_keywords
                    }
            
            # Выбираем намерение с максимальным скор-ом
            if intent_scores:
                best_intent = max(intent_scores.items(), key=lambda x: x[1]['score'])
                intent_type = best_intent[0]
                score_data = best_intent[1]
                
                # Вычисляем уверенность
                confidence = min(0.95, score_data['score'] * 2)  # Масштабируем до 0.95
                
                return IntentClassification(
                    intent_type=intent_type,
                    confidence=confidence,
                    keywords=score_data['keywords'],
                    reasoning=f"Правило-основанная классификация: найдено {len(score_data['keywords'])} ключевых слов",
                    suggested_sections=self.intent_to_sections.get(intent_type, [])
                )
            else:
                return IntentClassification(
                    intent_type=IntentType.GENERAL,
                    confidence=0.3,
                    keywords=[],
                    reasoning="Не найдено ключевых слов для классификации",
                    suggested_sections=[]
                )
                
        except Exception as e:
            logger.error(f"❌ [INTENT_CLASSIFIER] Error in rule-based classification: {e}")
            return IntentClassification(
                intent_type=IntentType.GENERAL,
                confidence=0.1,
                keywords=[],
                reasoning=f"Ошибка в правило-основанной классификации: {e}",
                suggested_sections=[]
            )
    
    def _ml_classification(self, query: str) -> IntentClassification:
        """ML-классификация намерения с использованием Ollama"""
        try:
            # Создаем промпт для классификации
            prompt = f"""Задача: Классифицировать намерение запроса к нормативным документам.

Запрос: "{query}"

Типы намерений:
1. definition - запрос определений, терминов, понятий
2. applicability - запрос области применения, сферы действия
3. requirements - запрос требований, обязательств, норм
4. procedure - запрос процедур, методов, алгоритмов
5. exceptions - запрос исключений, ограничений, особых случаев
6. general - общие вопросы

Ответь в формате JSON:
{{
    "intent_type": "тип_намерения",
    "confidence": 0.0-1.0,
    "reasoning": "объяснение выбора",
    "keywords": ["ключевые", "слова"]
}}"""

            # Отправляем запрос к Ollama
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,  # Низкая температура для консистентности
                    "top_p": 0.9,
                    "num_predict": 200
                }
            }
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                generated_text = result.get('response', '').strip()
                
                # Парсим JSON ответ
                classification_data = self._parse_classification_response(generated_text)
                
                if classification_data:
                    intent_type = IntentType(classification_data.get('intent_type', 'general'))
                    confidence = float(classification_data.get('confidence', 0.5))
                    reasoning = classification_data.get('reasoning', 'ML классификация')
                    keywords = classification_data.get('keywords', [])
                    
                    return IntentClassification(
                        intent_type=intent_type,
                        confidence=confidence,
                        keywords=keywords,
                        reasoning=reasoning,
                        suggested_sections=self.intent_to_sections.get(intent_type, [])
                    )
            
            # Если ML классификация не удалась, возвращаем общий тип
            return IntentClassification(
                intent_type=IntentType.GENERAL,
                confidence=0.3,
                keywords=[],
                reasoning="ML классификация не удалась",
                suggested_sections=[]
            )
            
        except Exception as e:
            logger.error(f"❌ [INTENT_CLASSIFIER] Error in ML classification: {e}")
            return IntentClassification(
                intent_type=IntentType.GENERAL,
                confidence=0.1,
                keywords=[],
                reasoning=f"Ошибка в ML классификации: {e}",
                suggested_sections=[]
            )
    
    def _parse_classification_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Парсинг ответа от ML модели"""
        try:
            import json
            
            # Ищем JSON в ответе
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
            
            return None
            
        except Exception as e:
            logger.warning(f"⚠️ [INTENT_CLASSIFIER] Error parsing classification response: {e}")
            return None
    
    def rewrite_query(self, query: str, intent_classification: IntentClassification) -> QueryRewriting:
        """
        Переписывание запроса на основе классификации намерения
        
        Args:
            query: Исходный запрос
            intent_classification: Результат классификации намерения
            
        Returns:
            Переписанные запросы и фильтры
        """
        try:
            logger.info(f"🔄 [INTENT_CLASSIFIER] Rewriting query for intent: {intent_classification.intent_type.value}")
            
            intent_type = intent_classification.intent_type
            
            # Генерируем переписанные запросы
            rewritten_queries = self._generate_rewritten_queries(query, intent_type)
            
            # Получаем фильтры для разделов
            section_filters = self.intent_to_sections.get(intent_type, [])
            
            # Получаем фильтры для типов чанков
            chunk_type_filters = self.intent_to_chunk_types.get(intent_type, [])
            
            return QueryRewriting(
                original_query=query,
                intent_type=intent_type,
                rewritten_queries=rewritten_queries,
                section_filters=section_filters,
                chunk_type_filters=chunk_type_filters
            )
            
        except Exception as e:
            logger.error(f"❌ [INTENT_CLASSIFIER] Error rewriting query: {e}")
            return QueryRewriting(
                original_query=query,
                intent_type=IntentType.GENERAL,
                rewritten_queries=[query],
                section_filters=[],
                chunk_type_filters=[]
            )
    
    def _generate_rewritten_queries(self, query: str, intent_type: IntentType) -> List[str]:
        """Генерация переписанных запросов для конкретного типа намерения"""
        try:
            rewritten_queries = [query]  # Всегда включаем исходный запрос
            
            # Добавляем специфичные запросы в зависимости от типа намерения
            if intent_type == IntentType.DEFINITION:
                rewritten_queries.extend([
                    f"определение {query}",
                    f"что такое {query}",
                    f"термин {query}",
                    f"понятие {query}"
                ])
            elif intent_type == IntentType.APPLICABILITY:
                rewritten_queries.extend([
                    f"область применения {query}",
                    f"где применяется {query}",
                    f"сфера использования {query}",
                    f"назначение {query}"
                ])
            elif intent_type == IntentType.REQUIREMENTS:
                rewritten_queries.extend([
                    f"требования к {query}",
                    f"нормы для {query}",
                    f"обязательные условия {query}",
                    f"параметры {query}"
                ])
            elif intent_type == IntentType.PROCEDURE:
                rewritten_queries.extend([
                    f"метод {query}",
                    f"процедура {query}",
                    f"как выполнить {query}",
                    f"порядок {query}"
                ])
            elif intent_type == IntentType.EXCEPTIONS:
                rewritten_queries.extend([
                    f"исключения для {query}",
                    f"ограничения {query}",
                    f"не применяется к {query}",
                    f"особые случаи {query}"
                ])
            
            # Удаляем дубликаты и ограничиваем количество
            unique_queries = list(dict.fromkeys(rewritten_queries))[:5]
            
            return unique_queries
            
        except Exception as e:
            logger.error(f"❌ [INTENT_CLASSIFIER] Error generating rewritten queries: {e}")
            return [query]
    
    def get_intent_stats(self) -> Dict[str, Any]:
        """Получение статистики классификатора намерений"""
        return {
            "service_type": "intent_classifier",
            "model_name": self.model_name,
            "intent_types": [intent.value for intent in IntentType],
            "keywords_count": {intent.value: len(keywords) for intent, keywords in self.intent_keywords.items()},
            "sections_mapping": {intent.value: len(sections) for intent, sections in self.intent_to_sections.items()},
            "chunk_types_mapping": {intent.value: len(types) for intent, types in self.intent_to_chunk_types.items()},
            "timestamp": datetime.now().isoformat()
        }
    
    def health_check(self) -> bool:
        """Проверка здоровья сервиса классификации намерений"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [model.get("name") for model in models]
                return self.model_name in model_names
            return False
        except Exception as e:
            logger.error(f"❌ [INTENT_CLASSIFIER] Health check failed: {e}")
            return False
