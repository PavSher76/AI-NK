from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn
import logging
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Импорт сервиса
from vllm_ollama_service import OllamaService

# Модели Pydantic
class ChatRequest(BaseModel):
    message: str
    model: str = "gpt-oss:20b"
    history: Optional[List[Dict[str, str]]] = None
    max_tokens: int = 2048

class ChatResponse(BaseModel):
    status: str
    response: str
    model: str
    timestamp: str
    tokens_used: Optional[int] = None

# Создание FastAPI приложения
app = FastAPI(
    title="VLLM + Ollama Integration Service",
    description="Сервис интеграции vLLM с локально установленным Ollama",
    version="1.0.0"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Инициализация сервиса
ollama_service = OllamaService()

# ============================================================================
# API эндпоинты
# ============================================================================

@app.get("/")
async def root_endpoint():
    """Корневой эндпоинт"""
    return {
        "service": "VLLM + Ollama Integration Service",
        "version": "1.0.0",
        "description": "Сервис интеграции vLLM с локально установленным Ollama",
        "endpoints": {
            "health": "/health",
            "models": "/models",
            "chat": "/chat",
            "stats": "/stats"
        },
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_endpoint():
    """Проверка здоровья сервиса"""
    try:
        health_status = ollama_service.health_check()
        return health_status
    except Exception as e:
        logger.error(f"❌ [HEALTH] Health check error: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/models")
async def models_endpoint():
    """Получение списка доступных моделей Ollama"""
    try:
        models = ollama_service.get_ollama_models()
        return models
    except Exception as e:
        logger.error(f"❌ [MODELS] Error getting models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """Генерация ответа через Ollama"""
    try:
        logger.info(f"💬 [CHAT] Processing chat request with model: {request.model}")
        
        response = ollama_service.generate_response_with_ollama(
            message=request.message,
            model_name=request.model,
            history=request.history,
            max_tokens=request.max_tokens
        )
        
        return response
        
    except Exception as e:
        logger.error(f"❌ [CHAT] Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def stats_endpoint():
    """Получение статистики сервиса"""
    try:
        stats = ollama_service.get_stats()
        return stats
    except Exception as e:
        logger.error(f"❌ [STATS] Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Запуск сервиса
# ============================================================================

if __name__ == "__main__":
    logger.info("🚀 [OLLAMA_SERVICE] Starting Ollama Integration Service...")
    
    # Проверяем доступность Ollama
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            bge_m3_available = any("bge-m3" in model.get("name", "") for model in models)
            gpt_oss_available = any("gpt-oss" in model.get("name", "") for model in models)
            
            if bge_m3_available:
                logger.info("✅ [OLLAMA_SERVICE] BGE-M3 model is available in Ollama")
            else:
                logger.warning("⚠️ [OLLAMA_SERVICE] BGE-M3 model not found in Ollama")
                
            if gpt_oss_available:
                logger.info("✅ [OLLAMA_SERVICE] GPT-OSS model is available in Ollama")
            else:
                logger.warning("⚠️ [OLLAMA_SERVICE] GPT-OSS model not found in Ollama")
        else:
            logger.error("❌ [OLLAMA_SERVICE] Cannot connect to Ollama")
    except Exception as e:
        logger.error(f"❌ [OLLAMA_SERVICE] Error checking Ollama: {e}")
    
    # Запускаем сервис
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8005,
        reload=True,
        log_level="info"
    )
