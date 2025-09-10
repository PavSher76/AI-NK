"""
Главный модуль calculation_service (рефакторенная версия)
"""
import os
import sys
import time
import logging
import asyncio
import signal
from datetime import datetime
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

import qdrant_client
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.security import OAuth2PasswordRequestForm
import uvicorn

# Импорт наших модулей
from config import (
    HOST, PORT, DEBUG, CORS_ORIGINS, LOG_LEVEL, LOG_FORMAT, LOG_FILE,
    QDRANT_URL, QDRANT_API_KEY
)
from models import (
    CalculationCreate, CalculationResponse, CalculationUpdate, CalculationExecute,
    HealthResponse, ErrorResponse
)
from auth import auth_service, get_current_active_user
from database import db_manager
from calculations import calculation_engine
from utils.calculation_docx_generator import CalculationDOCXGenerator

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper()),
    format=LOG_FORMAT,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE)
    ]
)
logger = logging.getLogger(__name__)

# Инициализируем startup_time
startup_time = datetime.now()

# Глобальные переменные для graceful shutdown
shutdown_event = asyncio.Event()
is_shutting_down = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    global startup_time
    startup_time = datetime.now()
    logger.info("🚀 Calculation service starting up...")
    
    # Инициализация Qdrant клиента
    try:
        qdrant_client.QdrantClient(
            url=QDRANT_URL,
            api_key=QDRANT_API_KEY
        )
        logger.info("✅ Qdrant client initialized")
    except Exception as e:
        logger.warning(f"⚠️ Qdrant client initialization failed: {e}")
    
    yield
    
    # Graceful shutdown
    global is_shutting_down
    is_shutting_down = True
    shutdown_event.set()
    logger.info("🛑 Calculation service shutting down...")


# Создание FastAPI приложения
app = FastAPI(
    title="Calculation Service",
    description="Сервис для выполнения инженерных расчетов",
    version="1.0.0",
    lifespan=lifespan
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware для логирования запросов
@app.middleware("http")
async def log_requests(request, call_next):
    """Логирование HTTP запросов"""
    request_id = f"req_{int(time.time() * 1000)}"
    logger.info(f"🔍 [REQUEST] {request_id}: {request.method} {request.url.path}")
    
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    logger.info(f"🔍 [RESPONSE] {request_id}: {response.status_code} ({process_time:.3f}s)")
    return response


# Обработчики сигналов для graceful shutdown
def signal_handler(signum, frame):
    """Обработчик сигналов для graceful shutdown"""
    global is_shutting_down
    is_shutting_down = True
    shutdown_event.set()
    logger.info(f"🛑 Received signal {signum}, initiating graceful shutdown...")


signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)


# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Проверка состояния сервиса"""
    if is_shutting_down:
        raise HTTPException(status_code=503, detail="Service is shutting down")
    
    try:
        # Проверка памяти
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        logger.debug(f"🔍 [HEALTH] Memory check: RSS: {memory_info.rss/1024/1024:.1f}MB, VMS: {memory_info.vms/1024/1024:.1f}MB")
        
        # Проверка PostgreSQL
        try:
            with db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
            logger.debug("🔍 [HEALTH] PostgreSQL check: healthy")
        except Exception as e:
            logger.error(f"🔍 [HEALTH] PostgreSQL check failed: {e}")
            raise HTTPException(status_code=503, detail="Database connection failed")
        
        # Проверка Qdrant
        try:
            client = qdrant_client.QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
            client.get_collections()
            logger.debug("🔍 [HEALTH] Qdrant check: healthy")
        except Exception as e:
            logger.warning(f"🔍 [HEALTH] Qdrant check failed: {e}")
        
        uptime = (datetime.now() - startup_time).total_seconds()
        logger.debug(f"🔍 [HEALTH] Health check passed in {time.time() - time.time():.3f}s")
        
        return HealthResponse(
            status="healthy",
            timestamp=datetime.now(),
            uptime=uptime,
            version="1.0.0",
            services={
                "database": "healthy",
                "qdrant": "healthy" if QDRANT_URL else "disabled"
            }
        )
        
    except Exception as e:
        logger.error(f"🔍 [HEALTH] Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Health check failed")


# Аутентификация
@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Получение JWT токена для авторизации"""
    if is_shutting_down:
        raise HTTPException(status_code=503, detail="Service is shutting down")

    logger.info(f"🔍 [AUTH] Login attempt for user: {form_data.username}")
    
    try:
        user = auth_service.authenticate_user(form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        from datetime import timedelta
        access_token_expires = timedelta(minutes=auth_service.access_token_expire_minutes)
        access_token = auth_service.create_access_token(
            data={"sub": user.username, "user_id": user.id, "role": user.role},
            expires_delta=access_token_expires
        )
        
        logger.info(f"🔍 [AUTH] Successful login for user: {user.username}")
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"🔍 [AUTH] Login error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/me")
async def read_users_me(current_user = Depends(get_current_active_user)):
    """Получение информации о текущем пользователе"""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role,
        "permissions": current_user.permissions
    }


# CRUD операции с расчетами
@app.post("/calculations", response_model=CalculationResponse)
async def create_calculation(
    calculation: CalculationCreate
):
    """Создание нового расчета"""
    if is_shutting_down:
        raise HTTPException(status_code=503, detail="Service is shutting down")
    
    try:
        calculation_id = db_manager.create_calculation(calculation, user_id=1)  # Используем фиксированный user_id для демо
        created_calculation = db_manager.get_calculation(calculation_id)
        
        logger.info(f"✅ Calculation created: {calculation_id}")
        return created_calculation
        
    except Exception as e:
        logger.error(f"❌ Error creating calculation: {e}")
        raise HTTPException(status_code=500, detail="Failed to create calculation")


@app.get("/calculations", response_model=List[CalculationResponse])
async def get_calculations(
    calculation_type: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """Получение списка расчетов"""
    if is_shutting_down:
        raise HTTPException(status_code=503, detail="Service is shutting down")
    
    try:
        calculations = db_manager.get_calculations(
            user_id=1,  # Используем фиксированный user_id для демо
            calculation_type=calculation_type,
            category=category,
            limit=limit,
            offset=offset
        )
        return calculations
        
    except Exception as e:
        logger.error(f"❌ Error getting calculations: {e}")
        raise HTTPException(status_code=500, detail="Failed to get calculations")


@app.get("/calculations/{calculation_id}", response_model=CalculationResponse)
async def get_calculation(
    calculation_id: int
):
    """Получение расчета по ID"""
    if is_shutting_down:
        raise HTTPException(status_code=503, detail="Service is shutting down")
    
    try:
        calculation = db_manager.get_calculation(calculation_id)
        if not calculation:
            raise HTTPException(status_code=404, detail="Calculation not found")
        
        return calculation
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting calculation {calculation_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get calculation")


@app.put("/calculations/{calculation_id}", response_model=CalculationResponse)
async def update_calculation(
    calculation_id: int,
    calculation_update: CalculationUpdate
):
    """Обновление расчета"""
    if is_shutting_down:
        raise HTTPException(status_code=503, detail="Service is shutting down")
    
    try:
        updated_calculation = db_manager.update_calculation(calculation_id, calculation_update)
        if not updated_calculation:
            raise HTTPException(status_code=404, detail="Calculation not found")
        
        logger.info(f"✅ Calculation updated: {calculation_id}")
        return updated_calculation
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating calculation {calculation_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update calculation")


@app.delete("/calculations/{calculation_id}")
async def delete_calculation(
    calculation_id: int
):
    """Удаление расчета"""
    if is_shutting_down:
        raise HTTPException(status_code=503, detail="Service is shutting down")
    
    try:
        success = db_manager.delete_calculation(calculation_id)
        if not success:
            raise HTTPException(status_code=404, detail="Calculation not found")
        
        logger.info(f"✅ Calculation deleted: {calculation_id}")
        return {"message": "Calculation deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting calculation {calculation_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete calculation")


# Информация о типах расчетов
@app.get("/calculations/structural/types")
async def get_structural_calculation_types():
    """Получение доступных типов расчетов"""
    if is_shutting_down:
        raise HTTPException(status_code=503, detail="Service is shutting down")
    
    try:
        return calculation_engine.get_calculation_types()
        
    except Exception as e:
        logger.error(f"❌ Error getting calculation types: {e}")
        raise HTTPException(status_code=500, detail="Failed to get calculation types")


# Выполнение структурных расчетов (для совместимости с фронтендом)
@app.post("/calculations/structural/execute")
async def execute_structural_calculation(
    calculation_data: dict
):
    """Выполнение структурного расчета (для совместимости с фронтендом)"""
    if is_shutting_down:
        raise HTTPException(status_code=503, detail="Service is shutting down")
    
    try:
        calculation_type = calculation_data.get("calculation_type")
        parameters = calculation_data.get("parameters", {})
        
        if not calculation_type:
            raise HTTPException(status_code=400, detail="calculation_type is required")
        
        # Выполняем расчет напрямую через движок
        results = calculation_engine.execute_calculation_by_type(calculation_type, parameters)
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error executing structural calculation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to execute structural calculation: {str(e)}")


# Информация о типах расчетов дегазации
@app.get("/calculations/degasification/types")
async def get_degasification_calculation_types():
    """Получение доступных типов расчетов дегазации"""
    if is_shutting_down:
        raise HTTPException(status_code=503, detail="Service is shutting down")
    
    try:
        return calculation_engine.get_calculation_types()
        
    except Exception as e:
        logger.error(f"❌ Error getting degasification calculation types: {e}")
        raise HTTPException(status_code=500, detail="Failed to get degasification calculation types")


# Информация о типах электротехнических расчетов
@app.get("/calculations/electrical/types")
async def get_electrical_calculation_types():
    """Получение доступных типов электротехнических расчетов"""
    if is_shutting_down:
        raise HTTPException(status_code=503, detail="Service is shutting down")
    
    try:
        return calculation_engine.get_calculation_types()
        
    except Exception as e:
        logger.error(f"❌ Error getting electrical calculation types: {e}")
        raise HTTPException(status_code=500, detail="Failed to get electrical calculation types")


# Информация о типах теплотехнических расчетов
@app.get("/calculations/thermal/types")
async def get_thermal_calculation_types():
    """Получение доступных типов теплотехнических расчетов"""
    if is_shutting_down:
        raise HTTPException(status_code=503, detail="Service is shutting down")
    
    try:
        return calculation_engine.get_calculation_types()
        
    except Exception as e:
        logger.error(f"❌ Error getting thermal calculation types: {e}")
        raise HTTPException(status_code=500, detail="Failed to get thermal calculation types")


# Информация о типах вентиляционных расчетов
@app.get("/calculations/ventilation/types")
async def get_ventilation_calculation_types():
    """Получение доступных типов вентиляционных расчетов"""
    if is_shutting_down:
        raise HTTPException(status_code=503, detail="Service is shutting down")
    
    try:
        return calculation_engine.get_calculation_types()
        
    except Exception as e:
        logger.error(f"❌ Error getting ventilation calculation types: {e}")
        raise HTTPException(status_code=500, detail="Failed to get ventilation calculation types")


# Выполнение расчетов дегазации (для совместимости с фронтендом)
@app.post("/calculations/degasification/execute")
async def execute_degasification_calculation(
    calculation_data: dict
):
    """Выполнение расчета дегазации (для совместимости с фронтендом)"""
    if is_shutting_down:
        raise HTTPException(status_code=503, detail="Service is shutting down")
    
    try:
        calculation_type = calculation_data.get("calculation_type")
        parameters = calculation_data.get("parameters", {})
        
        # Выполнение расчета
        results = calculation_engine.execute_calculation_by_type(calculation_type, parameters)
        
        logger.info(f"✅ Degasification calculation executed successfully")
        return results
        
    except Exception as e:
        logger.error(f"❌ Error executing degasification calculation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to execute degasification calculation: {str(e)}")


# Выполнение электротехнических расчетов (для совместимости с фронтендом)
@app.post("/calculations/electrical/execute")
async def execute_electrical_calculation(
    calculation_data: dict
):
    """Выполнение электротехнического расчета (для совместимости с фронтендом)"""
    if is_shutting_down:
        raise HTTPException(status_code=503, detail="Service is shutting down")
    
    try:
        calculation_type = calculation_data.get("calculation_type")
        parameters = calculation_data.get("parameters", {})
        
        # Выполнение расчета
        results = calculation_engine.execute_calculation_by_type(calculation_type, parameters)
        
        logger.info(f"✅ Electrical calculation executed successfully")
        return results
        
    except Exception as e:
        logger.error(f"❌ Error executing electrical calculation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to execute electrical calculation: {str(e)}")


# Выполнение теплотехнических расчетов (для совместимости с фронтендом)
@app.post("/calculations/thermal/execute")
async def execute_thermal_calculation(
    calculation_data: dict
):
    """Выполнение теплотехнического расчета (для совместимости с фронтендом)"""
    if is_shutting_down:
        raise HTTPException(status_code=503, detail="Service is shutting down")
    
    try:
        calculation_type = calculation_data.get("calculation_type")
        parameters = calculation_data.get("parameters", {})
        
        # Выполнение расчета
        results = calculation_engine.execute_calculation_by_type(calculation_type, parameters)
        
        logger.info(f"✅ Thermal calculation executed successfully")
        return results
        
    except Exception as e:
        logger.error(f"❌ Error executing thermal calculation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to execute thermal calculation: {str(e)}")


# Выполнение вентиляционных расчетов (для совместимости с фронтендом)
@app.post("/calculations/ventilation/execute")
async def execute_ventilation_calculation(
    calculation_data: dict
):
    """Выполнение вентиляционного расчета (для совместимости с фронтендом)"""
    if is_shutting_down:
        raise HTTPException(status_code=503, detail="Service is shutting down")
    
    try:
        calculation_type = calculation_data.get("calculation_type")
        parameters = calculation_data.get("parameters", {})
        
        # Выполнение расчета
        results = calculation_engine.execute_calculation_by_type(calculation_type, parameters)
        
        logger.info(f"✅ Ventilation calculation executed successfully")
        return results
        
    except Exception as e:
        logger.error(f"❌ Error executing ventilation calculation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to execute ventilation calculation: {str(e)}")


# Общий эндпоинт для выполнения расчетов по типу
@app.post("/calculations/{calculation_type}/execute")
async def execute_calculation_by_type_endpoint(
    calculation_type: str,
    calculation_data: dict
):
    """Выполнение расчета по типу"""
    if is_shutting_down:
        raise HTTPException(status_code=503, detail="Service is shutting down")
    
    try:
        parameters = calculation_data.get("parameters", {})
        
        # Выполнение расчета
        results = calculation_engine.execute_calculation_by_type(calculation_type, parameters)
        
        logger.info(f"✅ {calculation_type} calculation executed successfully")
        return results
        
    except Exception as e:
        logger.error(f"❌ Error executing {calculation_type} calculation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to execute {calculation_type} calculation: {str(e)}")


# Экспорт расчетов в DOCX
@app.get("/calculations/{calculation_id}/export-docx")
async def export_calculation_docx(
    calculation_id: int
):
    """Экспорт расчета в формате DOCX"""
    if is_shutting_down:
        raise HTTPException(status_code=503, detail="Service is shutting down")
    
    try:
        # Получение расчета из базы данных
        calculation = db_manager.get_calculation(calculation_id)
        if not calculation:
            raise HTTPException(status_code=404, detail="Calculation not found")
        
        # Генерация DOCX
        docx_generator = CalculationDOCXGenerator()
        docx_content = docx_generator.generate_calculation_report(calculation)
        
        # Возврат файла
        return Response(
            content=docx_content,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f"attachment; filename=calculation_{calculation_id}.docx"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error exporting calculation {calculation_id} to DOCX: {e}")
        raise HTTPException(status_code=500, detail="Failed to export calculation")


# Метрики
@app.get("/metrics")
async def get_metrics():
    """Получение метрик сервиса"""
    if is_shutting_down:
        raise HTTPException(status_code=503, detail="Service is shutting down")
    
    try:
        stats = db_manager.get_calculation_stats()
        uptime = (datetime.now() - startup_time).total_seconds()
        
        return {
            "uptime_seconds": uptime,
            "calculations": stats,
            "service_status": "running" if not is_shutting_down else "shutting_down"
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get metrics")


# Обработчик ошибок
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Глобальный обработчик исключений"""
    logger.error(f"❌ Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            detail="Internal server error",
            error_code="INTERNAL_ERROR"
        ).dict()
    )


# Выполнение расчетов (общий эндпоинт - должен быть в конце)
@app.post("/calculations/{calculation_id}/execute")
async def execute_calculation(
    calculation_id: int,
    calculation_execute: CalculationExecute
):
    """Выполнение расчета"""
    if is_shutting_down:
        raise HTTPException(status_code=503, detail="Service is shutting down")
    
    try:
        logger.info(f"🔍 [DEBUG] Executing calculation {calculation_id} with parameters: {calculation_execute.parameters}")
        logger.info(f"🔍 [DEBUG] calculation_execute object: {calculation_execute}")
        logger.info(f"🔍 [DEBUG] calculation_execute.parameters: {calculation_execute.parameters}")
        results = calculation_engine.execute_calculation(calculation_id, calculation_execute.parameters)
        return results
        
    except Exception as e:
        logger.error(f"❌ Error executing calculation {calculation_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to execute {calculation_id} calculation: {str(e)}")


# ===== ВОДОСНАБЖЕНИЕ И ВОДООТВЕДЕНИЕ =====

@app.get("/calculations/water_supply/types")
async def get_water_supply_calculation_types():
    """Получение доступных типов расчетов водоснабжения"""
    if is_shutting_down:
        raise HTTPException(status_code=503, detail="Service is shutting down")
    
    try:
        return calculation_engine.get_calculation_types()
        
    except Exception as e:
        logger.error(f"❌ Error getting water supply calculation types: {e}")
        raise HTTPException(status_code=500, detail="Failed to get water supply calculation types")

@app.post("/calculations/water_supply/execute")
async def execute_water_supply_calculation(
    calculation_data: dict
):
    """Выполнение расчета водоснабжения (для совместимости с фронтендом)"""
    if is_shutting_down:
        raise HTTPException(status_code=503, detail="Service is shutting down")
    
    try:
        calculation_type = calculation_data.get("calculation_type")
        parameters = calculation_data.get("parameters", {})
        
        # Выполнение расчета
        results = calculation_engine.execute_calculation_by_type(calculation_type, parameters)
        
        logger.info(f"✅ Water supply calculation executed successfully")
        return results
        
    except Exception as e:
        logger.error(f"❌ Error executing water supply calculation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to execute water supply calculation: {str(e)}")


# ===== ПОЖАРНАЯ БЕЗОПАСНОСТЬ =====

@app.get("/calculations/fire_safety/types")
async def get_fire_safety_calculation_types():
    """Получение доступных типов расчетов пожарной безопасности"""
    if is_shutting_down:
        raise HTTPException(status_code=503, detail="Service is shutting down")
    
    try:
        return calculation_engine.get_calculation_types()
        
    except Exception as e:
        logger.error(f"❌ Error getting fire safety calculation types: {e}")
        raise HTTPException(status_code=500, detail="Failed to get fire safety calculation types")

@app.post("/calculations/fire_safety/execute")
async def execute_fire_safety_calculation(
    calculation_data: dict
):
    """Выполнение расчета пожарной безопасности (для совместимости с фронтендом)"""
    if is_shutting_down:
        raise HTTPException(status_code=503, detail="Service is shutting down")
    
    try:
        calculation_type = calculation_data.get("calculation_type")
        parameters = calculation_data.get("parameters", {})
        
        # Выполнение расчета
        results = calculation_engine.execute_calculation_by_type(calculation_type, parameters)
        
        logger.info(f"✅ Fire safety calculation executed successfully")
        return results
        
    except Exception as e:
        logger.error(f"❌ Error executing fire safety calculation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to execute fire safety calculation: {str(e)}")


# ===== АКУСТИЧЕСКИЕ РАСЧЕТЫ =====

@app.get("/calculations/acoustic/types")
async def get_acoustic_calculation_types():
    """Получение доступных типов акустических расчетов"""
    if is_shutting_down:
        raise HTTPException(status_code=503, detail="Service is shutting down")
    
    try:
        return calculation_engine.get_calculation_types()
        
    except Exception as e:
        logger.error(f"❌ Error getting acoustic calculation types: {e}")
        raise HTTPException(status_code=500, detail="Failed to get acoustic calculation types")

@app.post("/calculations/acoustic/execute")
async def execute_acoustic_calculation(
    calculation_data: dict
):
    """Выполнение акустического расчета (для совместимости с фронтендом)"""
    if is_shutting_down:
        raise HTTPException(status_code=503, detail="Service is shutting down")
    
    try:
        calculation_type = calculation_data.get("calculation_type")
        parameters = calculation_data.get("parameters", {})
        
        # Выполнение расчета
        results = calculation_engine.execute_calculation_by_type(calculation_type, parameters)
        
        logger.info(f"✅ Acoustic calculation executed successfully")
        return results
        
    except Exception as e:
        logger.error(f"❌ Error executing acoustic calculation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to execute acoustic calculation: {str(e)}")


# ===== ОСВЕЩЕНИЕ И ИНСОЛЯЦИЯ =====

@app.get("/calculations/lighting/types")
async def get_lighting_calculation_types():
    """Получение доступных типов расчетов освещения"""
    if is_shutting_down:
        raise HTTPException(status_code=503, detail="Service is shutting down")
    
    try:
        return calculation_engine.get_calculation_types()
        
    except Exception as e:
        logger.error(f"❌ Error getting lighting calculation types: {e}")
        raise HTTPException(status_code=500, detail="Failed to get lighting calculation types")

@app.post("/calculations/lighting/execute")
async def execute_lighting_calculation(
    calculation_data: dict
):
    """Выполнение расчета освещения (для совместимости с фронтендом)"""
    if is_shutting_down:
        raise HTTPException(status_code=503, detail="Service is shutting down")
    
    try:
        calculation_type = calculation_data.get("calculation_type")
        parameters = calculation_data.get("parameters", {})
        
        # Выполнение расчета
        results = calculation_engine.execute_calculation_by_type(calculation_type, parameters)
        
        logger.info(f"✅ Lighting calculation executed successfully")
        return results
        
    except Exception as e:
        logger.error(f"❌ Error executing lighting calculation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to execute lighting calculation: {str(e)}")


# ===== ИНЖЕНЕРНО-ГЕОЛОГИЧЕСКИЕ РАСЧЕТЫ =====

@app.get("/calculations/geological/types")
async def get_geological_calculation_types():
    """Получение доступных типов инженерно-геологических расчетов"""
    if is_shutting_down:
        raise HTTPException(status_code=503, detail="Service is shutting down")
    
    try:
        return calculation_engine.get_calculation_types()
        
    except Exception as e:
        logger.error(f"❌ Error getting geological calculation types: {e}")
        raise HTTPException(status_code=500, detail="Failed to get geological calculation types")

@app.post("/calculations/geological/execute")
async def execute_geological_calculation(
    calculation_data: dict
):
    """Выполнение инженерно-геологического расчета (для совместимости с фронтендом)"""
    if is_shutting_down:
        raise HTTPException(status_code=503, detail="Service is shutting down")
    
    try:
        calculation_type = calculation_data.get("calculation_type")
        parameters = calculation_data.get("parameters", {})
        
        # Выполнение расчета
        results = calculation_engine.execute_calculation_by_type(calculation_type, parameters)
        
        logger.info(f"✅ Geological calculation executed successfully")
        return results
        
    except Exception as e:
        logger.error(f"❌ Error executing geological calculation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to execute geological calculation: {str(e)}")


# Получение типов расчетов защиты от БПЛА
@app.get("/calculations/uav_protection/types")
async def get_uav_protection_calculation_types():
    """Получение типов расчетов защиты от БПЛА"""
    if is_shutting_down:
        raise HTTPException(status_code=503, detail="Service is shutting down")
    
    try:
        types = calculation_engine.get_calculation_types()
        uav_types = [t for t in types if t.type == "uav_protection"]
        return {"types": [t.dict() for t in uav_types]}
        
    except Exception as e:
        logger.error(f"❌ Error getting UAV protection calculation types: {e}")
        raise HTTPException(status_code=500, detail="Failed to get UAV protection calculation types")

@app.post("/calculations/uav_protection/execute")
async def execute_uav_protection_calculation(
    calculation_data: dict
):
    """Выполнение расчета защиты от БПЛА (для совместимости с фронтендом)"""
    if is_shutting_down:
        raise HTTPException(status_code=503, detail="Service is shutting down")
    
    try:
        calculation_type = calculation_data.get("calculation_type")
        parameters = calculation_data.get("parameters", {})
        
        logger.info(f"🔍 [DEBUG] Executing UAV protection calculation: {calculation_type}")
        logger.info(f"🔍 [DEBUG] Parameters: {parameters}")
        
        results = calculation_engine.execute_calculation_by_type("uav_protection", parameters)
        return results
        
    except Exception as e:
        logger.error(f"❌ Error executing UAV protection calculation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to execute UAV protection calculation: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        reload=DEBUG,
        log_level=LOG_LEVEL.lower()
    )
