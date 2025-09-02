import logging
import requests
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio

# Настройка логирования
logger = logging.getLogger(__name__)
chat_logger = logging.getLogger("chat")

class VLLMChatService:
    """Сервис для чатов с использованием vLLM и GPT-OSS"""
    
    def __init__(self, vllm_url: str = "http://localhost:8000"):
        self.vllm_url = vllm_url
        self.model_name = "gpt-oss"
        logger.info(f"🤖 [VLLM_CHAT] Initialized with {self.model_name} at {vllm_url}")
    
    def generate_response(self, message: str, history: List[Dict[str, str]] = None, 
                         system_prompt: str = None, max_tokens: int = 2048) -> Dict[str, Any]:
        """Генерация ответа с использованием vLLM"""
        try:
            # Формируем промпт
            if system_prompt:
                prompt = f"{system_prompt}\n\n"
            else:
                prompt = "Ты - полезный ассистент для работы с нормативными документами. Отвечай на вопросы пользователя четко и по существу.\n\n"
            
            # Добавляем историю диалога
            if history:
                for entry in history:
                    if entry.get('role') == 'user':
                        prompt += f"Пользователь: {entry.get('content', '')}\n"
                    elif entry.get('role') == 'assistant':
                        prompt += f"Ассистент: {entry.get('content', '')}\n"
            
            # Добавляем текущий вопрос
            prompt += f"Пользователь: {message}\nАссистент:"
            
            # Подготавливаем запрос к vLLM
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "max_tokens": max_tokens,
                "temperature": 0.7,
                "top_p": 0.9,
                "stop": ["Пользователь:", "\n\n"],
                "stream": False
            }
            
            # Отправляем запрос к vLLM
            response = requests.post(
                f"{self.vllm_url}/v1/completions",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                generated_text = result.get("choices", [{}])[0].get("text", "").strip()
                
                if generated_text:
                    chat_logger.info(f"✅ [CHAT] Generated response for message: '{message[:100]}...'")
                    
                    return {
                        "status": "success",
                        "response": generated_text,
                        "model": self.model_name,
                        "tokens_used": result.get("usage", {}).get("total_tokens", 0),
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    raise ValueError("Empty response received from vLLM")
            else:
                raise Exception(f"vLLM API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"❌ [CHAT] Error generating response: {e}")
            return {
                "status": "error",
                "response": f"Произошла ошибка при генерации ответа: {str(e)}",
                "model": self.model_name,
                "tokens_used": 0,
                "timestamp": datetime.now().isoformat()
            }
    
    def generate_ntd_consultation_response(self, message: str, search_results: List[Dict[str, Any]], 
                                         user_id: str, history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """Генерация ответа для консультации НТД с использованием найденных документов"""
        try:
            logger.info(f"💬 [NTD_CONSULTATION] Generating consultation response for: '{message[:100]}...'")
            
            if not search_results:
                return {
                    "status": "success",
                    "response": "К сожалению, я не нашел релевантной информации в базе нормативных документов. Попробуйте переформулировать ваш вопрос или обратитесь к актуальным нормативным документам.",
                    "sources": [],
                    "confidence": 0.0,
                    "documents_used": 0,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Формируем контекст из найденных документов
            context = "На основе найденных документов:\n\n"
            for i, result in enumerate(search_results[:3], 1):  # Топ-3 результата
                context += f"{i}. {result.get('document_title', 'Unknown')}\n"
                context += f"   Раздел: {result.get('section', 'Unknown')}\n"
                context += f"   Содержание: {result.get('content', '')[:300]}...\n\n"
            
            # Формируем системный промпт
            system_prompt = f"""Ты - эксперт по нормативным документам. Используй предоставленную информацию для ответа на вопрос пользователя.

Контекст:
{context}

Инструкции:
1. Отвечай на основе предоставленных документов
2. Если информации недостаточно, укажи это
3. Будь точным и ссылайся на конкретные документы
4. Используй профессиональную терминологию
5. Структурируй ответ логично

Вопрос пользователя: {message}"""
            
            # Генерируем ответ
            chat_response = self.generate_response(
                message=message,
                history=history,
                system_prompt=system_prompt,
                max_tokens=2048
            )
            
            if chat_response["status"] == "success":
                # Формируем источники
                sources = []
                for result in search_results[:3]:
                    source = {
                        'document_code': result.get('code', ''),
                        'document_title': result.get('document_title', ''),
                        'section': result.get('section', ''),
                        'page': result.get('page', 1),
                        'content_preview': result.get('content', '')[:200] + "..." if len(result.get('content', '')) > 200 else result.get('content', ''),
                        'relevance_score': result.get('score', 0)
                    }
                    sources.append(source)
                
                # Рассчитываем уверенность на основе релевантности
                top_score = search_results[0].get('score', 0) if search_results else 0
                confidence = min(top_score, 1.0) if top_score > 0 else 0.0
                
                return {
                    "status": "success",
                    "response": chat_response["response"],
                    "sources": sources,
                    "confidence": confidence,
                    "documents_used": len(search_results),
                    "model": self.model_name,
                    "tokens_used": chat_response.get("tokens_used", 0),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return chat_response
                
        except Exception as e:
            logger.error(f"❌ [NTD_CONSULTATION] Error generating consultation response: {e}")
            return {
                "status": "error",
                "response": f"Произошла ошибка при обработке вашего запроса: {str(e)}",
                "sources": [],
                "confidence": 0.0,
                "documents_used": 0,
                "model": self.model_name,
                "tokens_used": 0,
                "timestamp": datetime.now().isoformat()
            }
    
    def health_check(self) -> Dict[str, Any]:
        """Проверка здоровья vLLM сервиса"""
        try:
            # Проверяем доступность vLLM
            response = requests.get(f"{self.vllm_url}/v1/models", timeout=10)
            
            if response.status_code == 200:
                models = response.json().get("data", [])
                gpt_oss_available = any("gpt-oss" in model.get("id", "") for model in models)
                
                return {
                    "status": "healthy" if gpt_oss_available else "degraded",
                    "vllm_url": self.vllm_url,
                    "model_available": gpt_oss_available,
                    "available_models": [model.get("id") for model in models],
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "status": "unhealthy",
                    "vllm_url": self.vllm_url,
                    "error": f"HTTP {response.status_code}",
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"❌ [HEALTH] vLLM health check error: {e}")
            return {
                "status": "unhealthy",
                "vllm_url": self.vllm_url,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Получение статистики vLLM сервиса"""
        try:
            # Получаем информацию о моделях
            response = requests.get(f"{self.vllm_url}/v1/models", timeout=10)
            
            if response.status_code == 200:
                models = response.json().get("data", [])
                
                stats = {
                    "total_models": len(models),
                    "models": [model.get("id") for model in models],
                    "gpt_oss_available": any("gpt-oss" in model.get("id", "") for model in models),
                    "vllm_url": self.vllm_url,
                    "timestamp": datetime.now().isoformat()
                }
                
                return stats
            else:
                return {
                    "error": f"Failed to get models: HTTP {response.status_code}",
                    "vllm_url": self.vllm_url,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"❌ [STATS] Error getting vLLM stats: {e}")
            return {
                "error": str(e),
                "vllm_url": self.vllm_url,
                "timestamp": datetime.now().isoformat()
            }
