import logging
import requests
import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
import time

# Настройка логирования
logger = logging.getLogger(__name__)
chat_logger = logging.getLogger("chat")

class OllamaStatusChecker:
    """Проверка статуса локально установленного Ollama"""
    
    def __init__(self, ollama_url: str = None):
        self.ollama_url = ollama_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.last_check = None
        self.status_cache = None
        self.cache_duration = int(os.getenv("OLLAMA_CACHE_DURATION", "30"))  # секунды
    
    def check_ollama_status(self) -> Dict[str, Any]:
        """Проверка статуса Ollama"""
        try:
            current_time = time.time()
            
            # Проверяем кэш
            if (self.status_cache and self.last_check and 
                current_time - self.last_check < self.cache_duration):
                return self.status_cache
            
            # Проверяем доступность Ollama
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=10)
            
            if response.status_code == 200:
                models = response.json().get("models", [])
                
                # Проверяем наличие ключевых моделей
                bge_m3_available = any("bge-m3" in model.get("name", "") for model in models)
                gpt_oss_available = any("gpt-oss" in model.get("name", "") for model in models)
                
                status = {
                    "status": "healthy" if (bge_m3_available or gpt_oss_available) else "degraded",
                    "ollama_url": self.ollama_url,
                    "available_models": [model.get("name") for model in models],
                    "bge_m3_available": bge_m3_available,
                    "gpt_oss_available": gpt_oss_available,
                    "total_models": len(models),
                    "last_check": datetime.now().isoformat(),
                    "response_time_ms": response.elapsed.total_seconds() * 1000
                }
            else:
                status = {
                    "status": "unhealthy",
                    "ollama_url": self.ollama_url,
                    "error": f"HTTP {response.status_code}",
                    "last_check": datetime.now().isoformat()
                }
            
            # Обновляем кэш
            self.status_cache = status
            self.last_check = current_time
            
            return status
            
        except Exception as e:
            logger.error(f"❌ [OLLAMA_STATUS] Error checking Ollama status: {e}")
            status = {
                "status": "unhealthy",
                "ollama_url": self.ollama_url,
                "error": str(e),
                "last_check": datetime.now().isoformat()
            }
            
            # Обновляем кэш
            self.status_cache = status
            self.last_check = current_time
            
            return status
    
    def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Получение информации о конкретной модели"""
        try:
            # Используем POST запрос для /api/show
            response = requests.post(f"{self.ollama_url}/api/show", 
                                 json={"name": model_name}, timeout=15)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"⚠️ [OLLAMA_STATUS] Failed to get model info for {model_name}: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ [OLLAMA_STATUS] Error getting model info for {model_name}: {e}")
            return None

class OllamaService:
    """Ollama сервис с интеграцией локальных моделей"""
    
    def __init__(self, ollama_url: str = None):
        # Используем localhost для доступа к Ollama
        self.ollama_url = ollama_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        
        self.ollama_checker = OllamaStatusChecker(self.ollama_url)
        self.max_tokens = int(os.getenv("OLLAMA_MAX_TOKENS", "2048"))
        self.temperature = float(os.getenv("OLLAMA_TEMPERATURE", "0.7"))
        self.top_p = float(os.getenv("OLLAMA_TOP_P", "0.9"))
        self.timeout = int(os.getenv("OLLAMA_TIMEOUT", "120"))
        logger.info(f"🤖 [VLLM_OLLAMA] Initialized with Ollama at {self.ollama_url}")
        logger.info(f"🔧 [VLLM_OLLAMA] Configuration: max_tokens={self.max_tokens}, temperature={self.temperature}, timeout={self.timeout}s")
    
    def health_check(self) -> Dict[str, Any]:
        """Проверка здоровья сервиса"""
        try:
            # Проверяем Ollama
            ollama_status = self.ollama_checker.check_ollama_status()
            
            # Общий статус зависит только от Ollama
            overall_status = ollama_status["status"]
            
            return {
                "status": overall_status,
                "services": {
                    "ollama": ollama_status
                },
                "configuration": {
                    "ollama_url": self.ollama_url,
                    "max_tokens": self.max_tokens,
                    "temperature": self.temperature,
                    "timeout": self.timeout
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ [HEALTH] Health check error: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_ollama_models(self) -> Dict[str, Any]:
        """Получение списка доступных моделей Ollama"""
        try:
            status = self.ollama_checker.check_ollama_status()
            logger.info(f"🔍 [OLLAMA_MODELS] Ollama status: {status['status']}")
            
            if status["status"] == "healthy":
                models_info = []
                available_models = status.get("available_models", [])
                logger.info(f"🔍 [OLLAMA_MODELS] Processing {len(available_models)} models: {available_models}")
                
                for model_name in available_models:
                    # Добавляем базовую информацию о модели
                    model_info = {
                        "name": model_name,
                        "status": "available",
                        "type": "ollama_model"
                    }
                    models_info.append(model_info)
                    logger.info(f"✅ [OLLAMA_MODELS] Added model: {model_name}")
                
                logger.info(f"📊 [OLLAMA_MODELS] Total models processed: {len(models_info)}")
                
                result = {
                    "status": "success",
                    "models": models_info,
                    "total_count": len(models_info),
                    "ollama_status": status,
                    "timestamp": datetime.now().isoformat()
                }
                logger.info(f"📤 [OLLAMA_MODELS] Returning result: {result}")
                return result
            else:
                logger.warning(f"⚠️ [OLLAMA_MODELS] Ollama is not healthy: {status}")
                return {
                    "status": "error",
                    "error": "Ollama is not healthy",
                    "ollama_status": status,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"❌ [OLLAMA_MODELS] Error getting Ollama models: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def generate_response_with_ollama(self, message: str, model_name: str = "gpt-oss:20b",
                                    history: List[Dict[str, str]] = None, 
                                    max_tokens: int = None) -> Dict[str, Any]:
        """Генерация ответа с использованием Ollama"""
        try:
            # Используем переданный max_tokens или значение по умолчанию
            max_tokens = max_tokens or self.max_tokens
            
            logger.info(f"💬 [OLLAMA_GENERATION] Generating response with {model_name}, max_tokens={max_tokens}")
            
            # Проверяем статус Ollama
            ollama_status = self.ollama_checker.check_ollama_status()
            if ollama_status["status"] != "healthy":
                return {
                    "status": "error",
                    "response": f"Ollama is not available: {ollama_status.get('error', 'Unknown error')}",
                    "model": model_name,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Проверяем доступность модели
            if not any(model_name in model for model in ollama_status.get("available_models", [])):
                return {
                    "status": "error",
                    "response": f"Model {model_name} is not available in Ollama",
                    "model": model_name,
                    "available_models": ollama_status.get("available_models", []),
                    "timestamp": datetime.now().isoformat()
                }
            
            # Формируем промпт
            if history:
                prompt = ""
                for entry in history:
                    if entry.get('role') == 'user':
                        prompt += f"User: {entry.get('content', '')}\n"
                    elif entry.get('role') == 'assistant':
                        prompt += f"Assistant: {entry.get('content', '')}\n"
                prompt += f"User: {message}\nAssistant:"
            else:
                prompt = f"User: {message}\nAssistant:"
            
            # Отправляем запрос к Ollama
            payload = {
                "model": model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": self.temperature,
                    "top_p": self.top_p
                }
            }
            
            logger.info(f"📤 [OLLAMA_GENERATION] Sending request to Ollama: {model_name}")
            logger.info(f"📤 [OLLAMA_GENERATION] Request URL: {self.ollama_url}/api/generate")
            logger.info(f"📤 [OLLAMA_GENERATION] Request payload: {payload}")
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            
            logger.info(f"📥 [OLLAMA_GENERATION] Response status: {response.status_code}")
            logger.info(f"📥 [OLLAMA_GENERATION] Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"📥 [OLLAMA_GENERATION] Raw response from Ollama: {result}")
                generated_text = result.get("response", "").strip()
                
                logger.info(f"📝 [OLLAMA_GENERATION] Generated text: '{generated_text}' (length: {len(generated_text)})")
                
                if generated_text:
                    chat_logger.info(f"✅ [OLLAMA_GENERATION] Generated response with {model_name}")
                    
                    return {
                        "status": "success",
                        "response": generated_text,
                        "model": model_name,
                        "prompt_tokens": result.get("prompt_eval_count", 0),
                        "response_tokens": result.get("eval_count", 0),
                        "total_tokens": result.get("prompt_eval_count", 0) + result.get("eval_count", 0),
                        "generation_time_ms": result.get("eval_duration", 0) / 1_000_000,  # конвертируем наносекунды в миллисекунды
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    logger.warning(f"⚠️ [OLLAMA_GENERATION] Empty response from Ollama for {model_name}")
                    return {
                        "status": "error",
                        "response": "Empty response from Ollama",
                        "model": model_name,
                        "timestamp": datetime.now().isoformat()
                    }
            else:
                return {
                    "status": "error",
                    "response": f"Ollama API error: {response.status_code} - {response.text}",
                    "model": model_name,
                    "timestamp": datetime.now().isoformat()
                }
                
        except requests.exceptions.Timeout:
            logger.error(f"⏰ [OLLAMA_GENERATION] Timeout error for {model_name}")
            return {
                "status": "error",
                "response": f"Request timeout after {self.timeout} seconds",
                "model": model_name,
                "timestamp": datetime.now().isoformat()
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"🌐 [OLLAMA_GENERATION] Request error for {model_name}: {e}")
            return {
                "status": "error",
                "response": f"Request error: {str(e)}",
                "model": model_name,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"❌ [OLLAMA_GENERATION] Unexpected error for {model_name}: {e}")
            logger.exception(f"❌ [OLLAMA_GENERATION] Full traceback for {model_name}")
            return {
                "status": "error",
                "response": f"Unexpected error: {str(e)}",
                "model": model_name,
                "timestamp": datetime.now().isoformat()
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Получение статистики сервиса"""
        try:
            # Статистика Ollama
            ollama_status = self.ollama_checker.check_ollama_status()
            
            return {
                "ollama": ollama_status,
                "service_type": "VLLM + Ollama Integration",
                "configuration": {
                    "ollama_url": self.ollama_url,
                    "max_tokens": self.max_tokens,
                    "temperature": self.temperature,
                    "timeout": self.timeout
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ [STATS] Error getting stats: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
