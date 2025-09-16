"""
FastAPI приложение для модуля Нормоконтроль - 2
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from api_simple import router as normcontrol2_router
from main_simple import NormControl2Service

# Настройка логирования
logging.basicConfig(
    level=os.getenv("NORMCONTROL2_LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Глобальный экземпляр сервиса
normcontrol2_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    global normcontrol2_service
    
    # Инициализация при запуске
    logger.info("Инициализация сервиса Нормоконтроль - 2...")
    normcontrol2_service = NormControl2Service()
    logger.info("Сервис Нормоконтроль - 2 успешно инициализирован")
    
    yield
    
    # Очистка при остановке
    logger.info("Остановка сервиса Нормоконтроль - 2...")

# Создание FastAPI приложения
app = FastAPI(
    title="Нормоконтроль - 2 API",
    description="API для расширенной проверки формата и оформления документов",
    version="1.0.0",
    lifespan=lifespan
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(normcontrol2_router, prefix="/normcontrol2", tags=["normcontrol2"])

# Health check эндпоинт
@app.get("/health")
async def health_check():
    """Проверка состояния сервиса"""
    return {
        "status": "healthy",
        "service": "normcontrol2-service",
        "version": "1.0.0",
        "timestamp": "2025-01-12T00:00:00Z"
    }

# Root эндпоинт
@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "message": "Нормоконтроль - 2 API",
        "version": "1.0.0",
        "docs": "/docs"
    }

# Обработчик ошибок
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Глобальный обработчик ошибок"""
    logger.error(f"Необработанная ошибка: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Внутренняя ошибка сервера",
            "detail": str(exc) if os.getenv("NORMCONTROL2_DEBUG", "false").lower() == "true" else "Ошибка обработки запроса"
        }
    )

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8010,
        reload=True,
        log_level="info"
    )
