"""
Сервис проверки орфографии и грамматики с использованием Hunspell + LanguageTool
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
import os
import time
from pathlib import Path

# Импорты для проверки
from spell_checker import AdvancedSpellChecker

# Настройка логирования
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(
    title="SpellChecker Service",
    description="Сервис проверки орфографии и грамматики с использованием Hunspell + LanguageTool",
    version="1.0.0"
)

# CORS настройки
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Модели данных
class SpellCheckRequest(BaseModel):
    text: str
    language: str = "ru"
    check_grammar: bool = True
    check_spelling: bool = True

class SpellCheckResponse(BaseModel):
    status: str
    text: str
    language: str
    spelling: Optional[Dict[str, Any]] = None
    grammar: Optional[Dict[str, Any]] = None
    comprehensive: Optional[Dict[str, Any]] = None
    processing_time: float

class HealthResponse(BaseModel):
    status: str
    service: str
    hunspell_available: bool
    languagetool_available: bool
    version: str

# Инициализация проверщика
spell_checker = None

@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске"""
    global spell_checker
    try:
        logger.info("Инициализация SpellChecker Service...")
        spell_checker = AdvancedSpellChecker()
        logger.info("SpellChecker Service инициализирован успешно")
    except Exception as e:
        logger.error(f"Ошибка инициализации SpellChecker: {e}")
        raise

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Проверка здоровья сервиса"""
    try:
        hunspell_available = spell_checker.hunspell is not None if spell_checker else False
        languagetool_available = getattr(spell_checker, 'language_tool_available', False) if spell_checker else False
        
        return HealthResponse(
            status="healthy" if spell_checker else "unhealthy",
            service="spellchecker",
            hunspell_available=hunspell_available,
            languagetool_available=languagetool_available,
            version="1.0.0"
        )
    except Exception as e:
        logger.error(f"Ошибка проверки здоровья: {e}")
        return HealthResponse(
            status="unhealthy",
            service="spellchecker",
            hunspell_available=False,
            languagetool_available=False,
            version="1.0.0"
        )

@app.post("/spellcheck", response_model=SpellCheckResponse)
async def spell_check(request: SpellCheckRequest):
    """Проверка орфографии"""
    if not spell_checker:
        raise HTTPException(status_code=503, detail="SpellChecker не инициализирован")
    
    start_time = time.time()
    
    try:
        logger.info(f"Начинаем проверку орфографии для текста длиной {len(request.text)} символов")
        
        # Проверка орфографии
        spelling_result = spell_checker.check_spelling(request.text)
        
        processing_time = time.time() - start_time
        
        return SpellCheckResponse(
            status="success",
            text=request.text,
            language=request.language,
            spelling=spelling_result,
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"Ошибка проверки орфографии: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка проверки орфографии: {str(e)}")

@app.post("/grammar-check", response_model=SpellCheckResponse)
async def grammar_check(request: SpellCheckRequest):
    """Проверка грамматики"""
    if not spell_checker:
        raise HTTPException(status_code=503, detail="SpellChecker не инициализирован")
    
    start_time = time.time()
    
    try:
        logger.info(f"Начинаем проверку грамматики для текста длиной {len(request.text)} символов")
        
        # Проверка грамматики
        grammar_result = spell_checker.check_grammar(request.text)
        
        processing_time = time.time() - start_time
        
        return SpellCheckResponse(
            status="success",
            text=request.text,
            language=request.language,
            grammar=grammar_result,
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"Ошибка проверки грамматики: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка проверки грамматики: {str(e)}")

@app.post("/comprehensive-check", response_model=SpellCheckResponse)
async def comprehensive_check(request: SpellCheckRequest):
    """Комплексная проверка орфографии и грамматики"""
    if not spell_checker:
        raise HTTPException(status_code=503, detail="SpellChecker не инициализирован")
    
    start_time = time.time()
    
    try:
        logger.info(f"Начинаем комплексную проверку для текста длиной {len(request.text)} символов")
        
        # Комплексная проверка
        comprehensive_result = spell_checker.comprehensive_check(request.text)
        
        processing_time = time.time() - start_time
        
        return SpellCheckResponse(
            status="success",
            text=request.text,
            language=request.language,
            comprehensive=comprehensive_result,
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"Ошибка комплексной проверки: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка комплексной проверки: {str(e)}")

@app.get("/languages")
async def get_supported_languages():
    """Получение списка поддерживаемых языков"""
    return {
        "supported_languages": [
            {"code": "ru", "name": "Русский", "hunspell": True, "languagetool": True},
            {"code": "en", "name": "Английский", "hunspell": True, "languagetool": True},
            {"code": "de", "name": "Немецкий", "hunspell": True, "languagetool": True},
            {"code": "fr", "name": "Французский", "hunspell": True, "languagetool": True}
        ]
    }

@app.get("/stats")
async def get_service_stats():
    """Получение статистики сервиса"""
    if not spell_checker:
        return {"error": "SpellChecker не инициализирован"}
    
    return {
        "hunspell_initialized": spell_checker.hunspell is not None,
        "languagetool_initialized": spell_checker.language_tool is not None,
        "dictionary_size": len(spell_checker.dictionary) if hasattr(spell_checker, 'dictionary') else 0,
        "uptime": "N/A"  # Можно добавить отслеживание времени работы
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8007)
