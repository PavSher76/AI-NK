from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn
import logging
import os
from datetime import datetime

# Настройка логирования
from logging_config import setup_general_logging, get_log_stats

# Настраиваем общее логирование
setup_general_logging()
logger = logging.getLogger(__name__)

# Импорт сервисов
from vllm_ollama_service import OllamaService
from chat_document_service import ChatDocumentService

# Модели Pydantic
class ChatRequest(BaseModel):
    message: str
    model: str = "llama3.1:8b"
    history: Optional[List[Dict[str, str]]] = None
    max_tokens: Optional[int] = None

class ChatResponse(BaseModel):
    status: str
    response: str
    model: str
    timestamp: str
    tokens_used: Optional[int] = None
    generation_time_ms: Optional[float] = None

class DocumentUploadResponse(BaseModel):
    status: str
    message: str
    document_id: Optional[str] = None
    file_name: Optional[str] = None
    chunks_count: Optional[int] = None
    error: Optional[str] = None

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

# Инициализация сервисов
ollama_service = OllamaService()
chat_document_service = ChatDocumentService()

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
            "stats": "/stats",
            "logs_stats": "/logs/stats",
            "upload_document": "/upload_document",
            "chat_documents_stats": "/chat_documents_stats"
        },
        "configuration": {
            "ollama_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            "max_tokens": os.getenv("OLLAMA_MAX_TOKENS", "2048"),
            "temperature": os.getenv("OLLAMA_TEMPERATURE", "0.7"),
            "timeout": os.getenv("OLLAMA_TIMEOUT", "120"),
            "max_file_size": "100MB"
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

@app.post("/upload_document")
async def upload_document_endpoint(
    file: UploadFile = File(...),
    message: str = Form("")
):
    """Загрузка и обработка документа для чата"""
    try:
        logger.info(f"📄 [UPLOAD_DOCUMENT] Processing document: {file.filename}")
        
        # Читаем содержимое файла
        file_content = await file.read()
        
        # Обрабатываем документ
        result = chat_document_service.process_document(
            file_content=file_content,
            file_type=file.content_type or "application/octet-stream",
            file_name=file.filename or "unknown",
            user_message=message
        )
        
        if result["success"]:
            return DocumentUploadResponse(
                status="success",
                message=f"Документ {file.filename} успешно обработан",
                document_id=result["document_id"],
                file_name=result["file_name"],
                chunks_count=result["chunks_count"]
            )
        else:
            return DocumentUploadResponse(
                status="error",
                message="Ошибка обработки документа",
                error=result["error"]
            )
            
    except Exception as e:
        logger.error(f"❌ [UPLOAD_DOCUMENT] Error processing document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat_with_document")
async def chat_with_document_endpoint(
    file: UploadFile = File(...),
    message: str = Form(""),
    model: str = Form("llama3.1:8b")
):
    """Чат с ИИ с загруженным документом"""
    try:
        logger.info(f"💬📄 [CHAT_WITH_DOCUMENT] Processing document: {file.filename}")
        
        # Читаем содержимое файла
        file_content = await file.read()
        
        # Обрабатываем документ
        result = chat_document_service.process_document(
            file_content=file_content,
            file_type=file.content_type or "application/octet-stream",
            file_name=file.filename or "unknown",
            user_message=message
        )
        
        if not result["success"]:
            logger.error(f"❌ [CHAT_WITH_DOCUMENT] Document processing failed: {result['error']}")
            raise HTTPException(status_code=400, detail=result["error"])
        
        # Отправляем запрос к ИИ с контекстом документа
        ai_response = ollama_service.generate_response_with_ollama(
            message=result["ai_context"],
            model_name=model,
            history=None,
            max_tokens=None
        )
        
        return {
            "status": "success",
            "document_processed": True,
            "document_id": result["document_id"],
            "file_name": result["file_name"],
            "chunks_count": result["chunks_count"],
            "ai_response": ai_response
        }
        
    except HTTPException as e:
        logger.error(f"❌ [CHAT_WITH_DOCUMENT] HTTP Error: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"❌ [CHAT_WITH_DOCUMENT] Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/chat_documents_stats")
async def chat_documents_stats_endpoint():
    """Получение статистики документов чата"""
    try:
        stats = chat_document_service.get_chat_documents_stats()
        return stats
    except Exception as e:
        logger.error(f"❌ [CHAT_DOCUMENTS_STATS] Error getting stats: {e}")
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

@app.get("/logs/stats")
async def logs_stats_endpoint():
    """Получение статистики логов"""
    try:
        log_stats = get_log_stats()
        return {
            "status": "success",
            "log_statistics": log_stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ [LOGS_STATS] Error getting log stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Запуск сервиса
# ============================================================================

if __name__ == "__main__":
    logger.info("🚀 [VLLM_OLLAMA_SERVICE] Starting VLLM + Ollama Integration Service...")
    
    # Проверяем доступность Ollama
    try:
        import requests
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        response = requests.get(f"{ollama_url}/api/tags", timeout=10)
        if response.status_code == 200:
            models = response.json().get("models", [])
            bge_m3_available = any("bge-m3" in model.get("name", "") for model in models)
            gpt_oss_available = any("gpt-oss" in model.get("name", "") for model in models)
            
            if bge_m3_available:
                logger.info("✅ [VLLM_OLLAMA_SERVICE] BGE-M3 model is available in Ollama")
            else:
                logger.warning("⚠️ [VLLM_OLLAMA_SERVICE] BGE-M3 model not found in Ollama")
                
            if gpt_oss_available:
                logger.info("✅ [VLLM_OLLAMA_SERVICE] GPT-OSS model is available in Ollama")
            else:
                logger.warning("⚠️ [VLLM_OLLAMA_SERVICE] GPT-OSS model not found in Ollama")
                
            logger.info(f"📊 [VLLM_OLLAMA_SERVICE] Total models available: {len(models)}")
        else:
            logger.error(f"❌ [VLLM_OLLAMA_SERVICE] Cannot connect to Ollama at {ollama_url}")
    except Exception as e:
        logger.error(f"❌ [VLLM_OLLAMA_SERVICE] Error checking Ollama: {e}")
    
    # Получаем конфигурацию из переменных окружения
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8005"))
    reload = os.getenv("RELOAD", "false").lower() == "true"
    log_level = os.getenv("LOG_LEVEL", "INFO")
    
    logger.info(f"🔧 [VLLM_OLLAMA_SERVICE] Configuration: host={host}, port={port}, reload={reload}")
    
    # Запускаем сервис
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level=log_level.lower()
    )
