import logging
import requests
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
import time

# Настройка логирования
logger = logging.getLogger(__name__)
chat_logger = logging.getLogger("chat")

class OllamaStatusChecker:
    """Проверка статуса локально установленного Ollama"""
    
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.last_check = None
        self.status_cache = None
        self.cache_duration = 30  # секунды
    
    def check_ollama_status(self) -> Dict[str, Any]:
        """Проверка статуса Ollama"""
        try:
            current_time = time.time()
            
            # Проверяем кэш
            if (self.status_cache and self.last_check and 
                current_time - self.last_check < self.cache_duration):
                return self.status_cache
            
            # Проверяем доступность Ollama
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            
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
            response = requests.get(f"{self.ollama_url}/api/show", 
                                 json={"name": model_name}, timeout=10)
            
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
    
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.ollama_checker = OllamaStatusChecker(ollama_url)
        logger.info(f"🤖 [VLLM_OLLAMA] Initialized with Ollama at {ollama_url}")
    
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
            
            if status["status"] == "healthy":
                models_info = []
                for model_name in status.get("available_models", []):
                    model_info = self.ollama_checker.get_model_info(model_name)
                    if model_info:
                        models_info.append({
                            "name": model_name,
                            "size": model_info.get("modelfile", ""),
                            "parameters": model_info.get("parameters", ""),
                            "template": model_info.get("template", "")
                        })
                
                return {
                    "status": "success",
                    "models": models_info,
                    "total_count": len(models_info),
                    "timestamp": datetime.now().isoformat()
                }
            else:
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
                                    max_tokens: int = 2048) -> Dict[str, Any]:
        """Генерация ответа с использованием Ollama"""
        try:
            logger.info(f"💬 [OLLAMA_GENERATION] Generating response with {model_name}")
            
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
            
            # Формируем простой промпт
            prompt = message
            
            # Отправляем запрос к Ollama
            payload = {
                "model": model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "stop": ["Пользователь:", "\n\n"]
                }
            }
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"🔍 [DEBUG] Ollama response: {result}")
                generated_text = result.get("response", "").strip()
                logger.info(f"🔍 [DEBUG] Generated text: '{generated_text}'")
                
                if generated_text:
                    chat_logger.info(f"✅ [OLLAMA_GENERATION] Generated response with {model_name}")
                    
                    return {
                        "status": "success",
                        "response": generated_text,
                        "model": model_name,
                        "prompt_tokens": result.get("prompt_eval_count", 0),
                        "response_tokens": result.get("eval_count", 0),
                        "total_tokens": result.get("prompt_eval_count", 0) + result.get("eval_count", 0),
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    logger.warning(f"⚠️ [DEBUG] Empty response from Ollama for model {model_name}")
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
                
        except Exception as e:
            logger.error(f"❌ [OLLAMA_GENERATION] Error generating response: {e}")
            return {
                "status": "error",
                "response": f"Error generating response: {str(e)}",
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
                "service_type": "Ollama Integration Service",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ [STATS] Error getting stats: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
