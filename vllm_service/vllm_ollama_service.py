import requests
import logging
import os
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
import json

logger = logging.getLogger(__name__)

class OllamaService:
    """Сервис для работы с Ollama API"""
    
    def __init__(self):
        self.ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.max_tokens = int(os.getenv("OLLAMA_MAX_TOKENS", "2048"))
        self.temperature = float(os.getenv("OLLAMA_TEMPERATURE", "0.7"))
        self.timeout = int(os.getenv("OLLAMA_TIMEOUT", "120"))
        self.top_p = float(os.getenv("OLLAMA_TOP_P", "0.9"))
        
        # Статистика
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_tokens": 0,
            "total_time_ms": 0,
            "last_request_time": None
        }
        
        logger.info(f"🔧 [OLLAMA_SERVICE] Initialized with URL: {self.ollama_url}")
    
    def health_check(self) -> Dict[str, Any]:
        """Проверка здоровья Ollama сервиса"""
        try:
            start_time = time.time()
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=10)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                models_data = response.json()
                models = models_data.get("models", [])
                
                # Проверяем наличие нужных моделей
                bge_m3_available = any("bge-m3" in model.get("name", "") for model in models)
                gpt_oss_available = any("gpt-oss" in model.get("name", "") for model in models)
                
                return {
                    "status": "healthy",
                    "services": {
                        "ollama": {
                            "status": "healthy",
                            "ollama_url": self.ollama_url,
                            "available_models": [model.get("name", "") for model in models],
                            "bge_m3_available": bge_m3_available,
                            "gpt_oss_available": gpt_oss_available,
                            "total_models": len(models),
                            "last_check": datetime.now().isoformat(),
                            "response_time_ms": round(response_time, 3)
                        }
                    },
                    "configuration": {
                        "ollama_url": self.ollama_url,
                        "max_tokens": self.max_tokens,
                        "temperature": self.temperature,
                        "timeout": self.timeout
                    },
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": f"Ollama returned status {response.status_code}",
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"❌ [OLLAMA_HEALTH] Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_ollama_models(self) -> Dict[str, Any]:
        """Получение списка доступных моделей"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=10)
            if response.status_code == 200:
                ollama_data = response.json()
                models = ollama_data.get("models", [])
                
                # Преобразуем модели в формат, ожидаемый фронтендом
                formatted_models = []
                for model in models:
                    formatted_model = {
                        "name": model.get("name", ""),
                        "status": "available",
                        "type": "ollama_model",
                        "size": model.get("size", 0),
                        "modified_at": model.get("modified_at", ""),
                        "details": model.get("details", {})
                    }
                    formatted_models.append(formatted_model)
                
                return {
                    "status": "success",
                    "models": formatted_models,
                    "total_count": len(formatted_models),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                raise Exception(f"Ollama API returned status {response.status_code}")
        except Exception as e:
            logger.error(f"❌ [OLLAMA_MODELS] Error getting models: {e}")
            return {
                "status": "error",
                "error": str(e),
                "models": [],
                "total_count": 0,
                "timestamp": datetime.now().isoformat()
            }
    
    def generate_response_with_ollama(
        self, 
        message: str, 
        model_name: str = "gpt-oss:latest",
        history: Optional[List[Dict[str, str]]] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """Генерация ответа через Ollama"""
        
        start_time = time.time()
        self.stats["total_requests"] += 1
        self.stats["last_request_time"] = datetime.now().isoformat()
        
        try:
            logger.info(f"💬 [OLLAMA_GENERATION] Generating response with {model_name}, max_tokens={max_tokens}")
            
            # Формируем промпт
            prompt = self._build_prompt(message, history)
            
            # Параметры запроса
            request_data = {
                "model": model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": max_tokens or self.max_tokens,
                    "temperature": self.temperature,
                    "top_p": self.top_p,
                    "stop": ["User:", "Assistant:"],
                    "repeat_penalty": 1.1,
                    "top_k": 40
                }
            }
            
            logger.info(f"📤 [OLLAMA_GENERATION] Sending request to Ollama: {model_name}")
            logger.info(f"📤 [OLLAMA_GENERATION] Request URL: {self.ollama_url}/api/generate")
            logger.info(f"📤 [OLLAMA_GENERATION] Request payload: {json.dumps(request_data, ensure_ascii=False)}")
            
            # Отправляем запрос
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=request_data,
                timeout=self.timeout
            )
            
            generation_time = (time.time() - start_time) * 1000
            
            logger.info(f"📥 [OLLAMA_GENERATION] Response status: {response.status_code}")
            logger.info(f"📥 [OLLAMA_GENERATION] Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                response_data = response.json()
                logger.info(f"📥 [OLLAMA_GENERATION] Raw response from Ollama: {json.dumps(response_data, ensure_ascii=False)}")
                
                generated_text = response_data.get("response", "").strip()
                thinking = response_data.get("thinking", "").strip()
                
                logger.info(f"📝 [OLLAMA_GENERATION] Generated text: '{generated_text}' (length: {len(generated_text)})")
                logger.info(f"🧠 [OLLAMA_GENERATION] Thinking: '{thinking[:100]}...' (length: {len(thinking)})")
                
                # Если response пустой, но есть thinking, используем thinking
                if not generated_text and thinking:
                    logger.info(f"🔄 [OLLAMA_GENERATION] Using thinking as response for {model_name}")
                    generated_text = thinking
                elif not generated_text:
                    logger.warning(f"⚠️ [OLLAMA_GENERATION] Empty response from Ollama for {model_name}")
                    self.stats["failed_requests"] += 1
                    return {
                        "status": "error",
                        "response": "Empty response from Ollama",
                        "model": model_name,
                        "timestamp": datetime.now().isoformat()
                    }
                
                # Подсчитываем токены (приблизительно)
                tokens_used = len(generated_text.split()) * 1.3  # Примерная оценка
                
                # Обновляем статистику
                self.stats["successful_requests"] += 1
                self.stats["total_tokens"] += int(tokens_used)
                self.stats["total_time_ms"] += generation_time
                
                return {
                    "status": "success",
                    "response": generated_text,
                    "model": model_name,
                    "timestamp": datetime.now().isoformat(),
                    "tokens_used": int(tokens_used),
                    "generation_time_ms": round(generation_time, 2)
                }
            else:
                logger.error(f"❌ [OLLAMA_GENERATION] HTTP error: {response.status_code}")
                self.stats["failed_requests"] += 1
                return {
                    "status": "error",
                    "response": f"HTTP error: {response.status_code}",
                    "model": model_name,
                    "timestamp": datetime.now().isoformat()
                }
                
        except requests.exceptions.Timeout:
            logger.error(f"⏰ [OLLAMA_GENERATION] Timeout error for {model_name}")
            self.stats["failed_requests"] += 1
            return {
                "status": "error",
                "response": f"Request timeout after {self.timeout} seconds",
                "model": model_name,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"❌ [OLLAMA_GENERATION] Error generating response: {e}")
            self.stats["failed_requests"] += 1
            return {
                "status": "error",
                "response": f"Error: {str(e)}",
                "model": model_name,
                "timestamp": datetime.now().isoformat()
            }
    
    def _build_prompt(self, message: str, history: Optional[List[Dict[str, str]]] = None) -> str:
        """Построение промпта для Ollama"""
        prompt_parts = []
        
        # Добавляем историю, если есть
        if history:
            for entry in history:
                role = entry.get("role", "user")
                content = entry.get("content", "")
                if role == "user":
                    prompt_parts.append(f"User: {content}")
                elif role == "assistant":
                    prompt_parts.append(f"Assistant: {content}")
        
        # Добавляем текущее сообщение
        prompt_parts.append(f"User: {message}")
        prompt_parts.append("Assistant:")
        
        return "\n".join(prompt_parts)
    
    def get_stats(self) -> Dict[str, Any]:
        """Получение статистики сервиса"""
        success_rate = 0
        if self.stats["total_requests"] > 0:
            success_rate = (self.stats["successful_requests"] / self.stats["total_requests"]) * 100
        
        avg_time = 0
        if self.stats["successful_requests"] > 0:
            avg_time = self.stats["total_time_ms"] / self.stats["successful_requests"]
        
        return {
            "status": "success",
            "statistics": {
                "total_requests": self.stats["total_requests"],
                "successful_requests": self.stats["successful_requests"],
                "failed_requests": self.stats["failed_requests"],
                "success_rate_percent": round(success_rate, 2),
                "total_tokens": self.stats["total_tokens"],
                "average_generation_time_ms": round(avg_time, 2),
                "last_request_time": self.stats["last_request_time"]
            },
            "configuration": {
                "ollama_url": self.ollama_url,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "timeout": self.timeout,
                "top_p": self.top_p
            },
            "timestamp": datetime.now().isoformat()
        }
