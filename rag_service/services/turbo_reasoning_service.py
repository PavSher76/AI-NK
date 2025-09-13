"""
Сервис для турбо режима рассуждения с поддержкой GPT-4o-mini
"""

import logging
import requests
import os
from typing import List, Dict, Any, Optional
import time

logger = logging.getLogger(__name__)

# Получаем URL Ollama из переменной окружения
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434")

# Импортируем OpenAI сервис
from .openai_service import OpenAIService


class TurboReasoningService:
    """Сервис для турбо режима рассуждения с поддержкой GPT-4o-mini"""
    
    def __init__(self, ollama_url: str = None):
        self.ollama_url = ollama_url or OLLAMA_URL
        self.model_name = "llama3.1:8b"
        
        # Инициализируем OpenAI сервис для турбо режима
        self.openai_service = OpenAIService()
        
        logger.info(f"🚀 [TURBO_REASONING] Initialized with {self.model_name} at {self.ollama_url}")
        logger.info(f"🤖 [TURBO_REASONING] OpenAI service initialized for turbo mode")
    
    def generate_response(self, message: str, history: Optional[List[Dict[str, str]]] = None,
                        turbo_mode: bool = False, reasoning_depth: str = "balanced",
                        max_tokens: Optional[int] = None) -> Dict[str, Any]:
        """
        Генерация ответа с настраиваемым режимом рассуждения
        
        Args:
            message: Сообщение пользователя
            history: История чата
            turbo_mode: Включить турбо режим (использует GPT-4o-mini)
            reasoning_depth: Глубина рассуждения ("fast", "balanced", "deep")
            max_tokens: Максимальное количество токенов
            
        Returns:
            Словарь с ответом и метаданными
        """
        try:
            # В турбо режиме используем OpenAI GPT-4o-mini
            if turbo_mode:
                logger.info(f"🚀 [TURBO_REASONING] Using GPT-4o-mini for turbo mode")
                return self._generate_openai_response(message, history, max_tokens)
            
            # В обычном режиме используем локальную модель GPT-OSS
            return self._generate_ollama_response(message, history, reasoning_depth, max_tokens)
                
        except Exception as e:
            logger.error(f"❌ [TURBO_REASONING] Error generating response: {e}")
            raise e
    
    def _generate_openai_response(self, message: str, history: Optional[List[Dict[str, str]]] = None,
                                 max_tokens: Optional[int] = None) -> Dict[str, Any]:
        """Генерация ответа через OpenAI API (турбо режим)"""
        try:
            result = self.openai_service.generate_response(
                message=message,
                history=history,
                model="gpt-4o-mini",
                max_tokens=max_tokens,
                turbo_mode=True
            )
            
            # Добавляем дополнительные поля для совместимости
            result.update({
                "reasoning_depth": "turbo",
                "reasoning_steps": 1,  # Турбо режим - минимальные шаги
                "model": "gpt-4o-mini"
            })
            
            return result
            
        except Exception as e:
            logger.error(f"❌ [TURBO_REASONING] OpenAI API error: {e}")
            # Fallback на локальную модель
            logger.info("🔄 [TURBO_REASONING] Falling back to local GPT-OSS model")
            return self._generate_ollama_response(message, history, "fast", max_tokens)
    
    def _generate_ollama_response(self, message: str, history: Optional[List[Dict[str, str]]] = None,
                                 reasoning_depth: str = "balanced", max_tokens: Optional[int] = None) -> Dict[str, Any]:
        """Генерация ответа через Ollama API (обычный режим)"""
        try:
            start_time = time.time()
            
            # Настраиваем параметры в зависимости от глубины рассуждения
            if reasoning_depth == "fast":
                temperature = 0.4
                top_p = 0.85
                top_k = 30
                repeat_penalty = 1.15
                max_tokens = max_tokens or 1536
                reasoning_prompt = self._get_fast_reasoning_prompt()
            elif reasoning_depth == "deep":
                temperature = 0.7
                top_p = 0.95
                top_k = 50
                repeat_penalty = 1.2
                max_tokens = max_tokens or 3072
                reasoning_prompt = self._get_deep_reasoning_prompt()
            else:  # balanced
                temperature = 0.6
                top_p = 0.9
                top_k = 40
                repeat_penalty = 1.15
                max_tokens = max_tokens or 2048
                reasoning_prompt = self._get_balanced_reasoning_prompt()
            
            # Формируем контекст с историей
            context = self._build_context(message, history, reasoning_prompt)
            
            # Формируем запрос к Ollama
            payload = {
                "model": self.model_name,
                "prompt": context,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "top_p": top_p,
                    "top_k": top_k,
                    "repeat_penalty": repeat_penalty,
                    "num_predict": max_tokens
                }
            }
            
            logger.info(f"🚀 [TURBO_REASONING] Generating response with Ollama, depth: {reasoning_depth}")
            
            # Отправляем запрос к Ollama
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=300 if reasoning_depth == "deep" else 120
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get("response", "")
                
                generation_time = (time.time() - start_time) * 1000
                tokens_used = result.get("eval_count", 0)
                
                # Анализируем ответ для подсчета шагов рассуждения
                reasoning_steps = self._count_reasoning_steps(response_text, reasoning_depth)
                
                logger.info(f"✅ [TURBO_REASONING] Generated response in {generation_time:.1f}ms, tokens: {tokens_used}")
                
                return {
                    "response": response_text,
                    "tokens_used": tokens_used,
                    "generation_time_ms": generation_time,
                    "turbo_mode": False,
                    "reasoning_depth": reasoning_depth,
                    "reasoning_steps": reasoning_steps,
                    "model": self.model_name
                }
            else:
                raise Exception(f"Ollama API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"❌ [TURBO_REASONING] Ollama API error: {e}")
            raise e
    
    def _build_context(self, message: str, history: Optional[List[Dict[str, str]]] = None, 
                      reasoning_prompt: str = "") -> str:
        """Построение контекста для запроса"""
        context_parts = []
        
        # Добавляем инструкции по рассуждению
        if reasoning_prompt:
            context_parts.append(reasoning_prompt)
        
        # Добавляем историю чата
        if history:
            for msg in history:
                user_msg = msg.get('user', '')
                assistant_msg = msg.get('assistant', '')
                if user_msg and assistant_msg:
                    context_parts.append(f"User: {user_msg}")
                    context_parts.append(f"Assistant: {assistant_msg}")
        
        # Добавляем текущее сообщение
        context_parts.append(f"User: {message}")
        context_parts.append("Assistant:")
        
        return "\n\n".join(context_parts)
    
    def _get_fast_reasoning_prompt(self) -> str:
        """Промпт для быстрого рассуждения"""
        return """Ты - полезный ИИ-ассистент. Отвечай кратко и по существу. 
Используй простые рассуждения и давай прямые ответы."""
    
    def _get_balanced_reasoning_prompt(self) -> str:
        """Промпт для сбалансированного рассуждения"""
        return """Ты - полезный ИИ-ассистент. Отвечай подробно, но структурированно.
Используй логические рассуждения, разбивай сложные вопросы на части и объясняй свои выводы."""
    
    def _get_deep_reasoning_prompt(self) -> str:
        """Промпт для глубокого рассуждения"""
        return """Ты - эксперт-аналитик с глубокими знаниями. Отвечай максимально подробно и обоснованно.

При ответе используй:
1. Пошаговое рассуждение
2. Анализ различных аспектов вопроса
3. Примеры и аналогии
4. Логические выводы
5. Возможные альтернативы

Структурируй ответ с помощью маркеров и подзаголовков."""
    
    def _count_reasoning_steps(self, response: str, reasoning_depth: str) -> int:
        """Подсчет количества шагов рассуждения в ответе"""
        try:
            # Считаем различные маркеры рассуждения
            step_indicators = [
                r'\d+\.',           # 1., 2., 3.
                r'•\s',             # • 
                r'-\s',             # -
                r'→\s',             # →
                r'Шаг\s*\d+',       # Шаг 1
                r'Этап\s*\d+',      # Этап 1
                r'Сначала',          # Сначала
                r'Затем',           # Затем
                r'Далее',           # Далее
                r'Наконец',         # Наконец
                r'В итоге',         # В итоге
                r'Вывод',           # Вывод
                r'Заключение'       # Заключение
            ]
            
            import re
            total_steps = 0
            
            for pattern in step_indicators:
                matches = re.findall(pattern, response, re.IGNORECASE)
                total_steps += len(matches)
            
            # Если не нашли маркеры, оцениваем по длине и структуре
            if total_steps == 0:
                if reasoning_depth == "deep":
                    total_steps = max(3, len(response.split('\n')) // 5)
                elif reasoning_depth == "balanced":
                    total_steps = max(2, len(response.split('\n')) // 8)
                else:  # fast
                    total_steps = 1
            
            return total_steps
            
        except Exception as e:
            logger.warning(f"⚠️ [TURBO_REASONING] Error counting reasoning steps: {e}")
            return 1
    
    def get_reasoning_modes(self) -> Dict[str, Dict[str, Any]]:
        """Получение доступных режимов рассуждения"""
        return {
            "fast": {
                "name": "Быстрый",
                "description": "Краткие ответы, простые рассуждения",
                "temperature": 0.4,
                "max_tokens": 1024,
                "estimated_time": "5-15 секунд"
            },
            "balanced": {
                "name": "Сбалансированный",
                "description": "Подробные ответы с логическими рассуждениями",
                "temperature": 0.6,
                "max_tokens": 2048,
                "estimated_time": "15-30 секунд"
            },
            "deep": {
                "name": "Глубокий",
                "description": "Детальный анализ с пошаговыми рассуждениями",
                "temperature": 0.7,
                "max_tokens": 3072,
                "estimated_time": "30-60 секунд"
            },
            "turbo": {
                "name": "Турбо",
                "description": "Максимально быстрые ответы",
                "temperature": 0.3,
                "max_tokens": 1024,
                "estimated_time": "3-10 секунд"
            }
        }
    
    def health_check(self) -> bool:
        """Проверка здоровья сервиса"""
        try:
            # Проверяем Ollama
            ollama_healthy = False
            try:
                response = requests.get(f"{self.ollama_url}/api/tags", timeout=10)
                if response.status_code == 200:
                    models = response.json().get("models", [])
                    model_names = [model.get("name") for model in models]
                    ollama_healthy = self.model_name in model_names
            except Exception as e:
                logger.warning(f"⚠️ [TURBO_REASONING] Ollama health check failed: {e}")
            
            # Проверяем OpenAI
            openai_healthy = self.openai_service.health_check()
            
            # Сервис здоров, если работает хотя бы один из провайдеров
            is_healthy = ollama_healthy or openai_healthy
            
            logger.info(f"🏥 [TURBO_REASONING] Health check - Ollama: {ollama_healthy}, OpenAI: {openai_healthy}, Overall: {is_healthy}")
            
            return is_healthy
            
        except Exception as e:
            logger.error(f"❌ [TURBO_REASONING] Health check failed: {e}")
            return False
