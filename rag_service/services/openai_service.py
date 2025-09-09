"""
Сервис для работы с OpenAI API (GPT-4o-mini)
"""

import logging
import os
import requests
from typing import List, Dict, Any, Optional
import time

logger = logging.getLogger(__name__)

# Получаем API ключ OpenAI из переменной окружения
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")


class OpenAIService:
    """Сервис для работы с OpenAI API"""
    
    def __init__(self, api_key: str = None, base_url: str = None):
        self.api_key = api_key or OPENAI_API_KEY
        self.base_url = base_url or OPENAI_BASE_URL
        
        if not self.api_key:
            logger.warning("⚠️ [OPENAI] API ключ не найден. Установите OPENAI_API_KEY в переменных окружения.")
        
        logger.info(f"🤖 [OPENAI] Initialized with base URL: {self.base_url}")
    
    def generate_response(self, message: str, history: Optional[List[Dict[str, str]]] = None,
                         model: str = "gpt-4o-mini", max_tokens: Optional[int] = None,
                         temperature: float = 0.3, turbo_mode: bool = True) -> Dict[str, Any]:
        """
        Генерация ответа через OpenAI API
        
        Args:
            message: Сообщение пользователя
            history: История чата
            model: Модель для использования
            max_tokens: Максимальное количество токенов
            temperature: Температура генерации
            turbo_mode: Режим турбо (влияет на параметры)
            
        Returns:
            Словарь с ответом и метаданными
        """
        try:
            if not self.api_key:
                raise Exception("OpenAI API ключ не настроен")
            
            start_time = time.time()
            
            # Настраиваем параметры для турбо режима
            if turbo_mode:
                temperature = 0.3
                max_tokens = max_tokens or 1024
                system_prompt = self._get_turbo_system_prompt()
            else:
                temperature = 0.6
                max_tokens = max_tokens or 2048
                system_prompt = self._get_standard_system_prompt()
            
            # Формируем сообщения для API
            messages = [{"role": "system", "content": system_prompt}]
            
            # Добавляем историю чата
            if history:
                for msg in history:
                    if 'user' in msg and 'assistant' in msg:
                        messages.append({"role": "user", "content": msg['user']})
                        messages.append({"role": "assistant", "content": msg['assistant']})
            
            # Добавляем текущее сообщение
            messages.append({"role": "user", "content": message})
            
            # Формируем запрос к OpenAI API
            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": False
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            logger.info(f"🚀 [OPENAI] Generating response with model: {model}, turbo_mode: {turbo_mode}")
            
            # Отправляем запрос к OpenAI API
            response = requests.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result["choices"][0]["message"]["content"]
                
                generation_time = (time.time() - start_time) * 1000
                usage = result.get("usage", {})
                tokens_used = usage.get("total_tokens", 0)
                
                logger.info(f"✅ [OPENAI] Generated response in {generation_time:.1f}ms, tokens: {tokens_used}")
                
                return {
                    "response": response_text,
                    "tokens_used": tokens_used,
                    "generation_time_ms": generation_time,
                    "turbo_mode": turbo_mode,
                    "model": model,
                    "usage": usage
                }
            else:
                error_detail = response.text
                logger.error(f"❌ [OPENAI] API error: {response.status_code} - {error_detail}")
                raise Exception(f"OpenAI API error: {response.status_code} - {error_detail}")
                
        except Exception as e:
            logger.error(f"❌ [OPENAI] Error generating response: {e}")
            raise e
    
    def _get_turbo_system_prompt(self) -> str:
        """Системный промпт для турбо режима"""
        return """Ты - полезный ИИ-ассистент в режиме "Турбо". 
Отвечай кратко, точно и по существу. Используй простые формулировки и давай прямые ответы.
Фокусируйся на главном и избегай излишних деталей."""
    
    def _get_standard_system_prompt(self) -> str:
        """Стандартный системный промпт"""
        return """Ты - полезный ИИ-ассистент. 
Отвечай подробно и структурированно, используя логические рассуждения.
Разбивай сложные вопросы на части и объясняй свои выводы."""
    
    def health_check(self) -> bool:
        """Проверка здоровья сервиса"""
        try:
            if not self.api_key:
                return False
            
            # Простой запрос для проверки API
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 1
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=10
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"❌ [OPENAI] Health check failed: {e}")
            return False
    
    def get_available_models(self) -> List[str]:
        """Получение списка доступных моделей"""
        return [
            "gpt-4o-mini",
            "gpt-4o",
            "gpt-4-turbo",
            "gpt-3.5-turbo"
        ]







