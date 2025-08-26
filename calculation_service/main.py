import os
import sys
import time
import logging
import asyncio
import signal
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

import psycopg2
from psycopg2.extras import RealDictCursor
import qdrant_client
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('calculation_service.log')
    ]
)
logger = logging.getLogger(__name__)

# Инициализируем startup_time после импорта datetime
startup_time = datetime.now()

# Глобальные переменные для graceful shutdown
shutdown_event = asyncio.Event()
is_shutting_down = False

# Модели данных
class CalculationCreate(BaseModel):
    name: str = Field(..., description="Название расчета")
    description: Optional[str] = Field(None, description="Описание расчета")
    type: str = Field(..., description="Тип расчета")
    category: str = Field(..., description="Категория расчета")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Параметры расчета")

class CalculationResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    type: str
    category: str
    status: str
    parameters: Dict[str, Any]
    result: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    created_by: str
    processing_time: Optional[float]

class CalculationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None

# Конфигурация базы данных
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'norms-db')
POSTGRES_DB = os.getenv('POSTGRES_DB', 'normcontrol')
POSTGRES_USER = os.getenv('POSTGRES_USER', 'normcontrol_user')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'normcontrol_password')

QDRANT_HOST = os.getenv('QDRANT_HOST', 'qdrant')
QDRANT_PORT = int(os.getenv('QDRANT_PORT', 6333))

# Класс для работы с расчетами
class CalculationEngine:
    def __init__(self):
        self.db_conn = None
        self.qdrant_client = None
        self.max_retries = 3
        self.retry_delay = 5
        self.connection_retry_count = 0

    def connect_databases(self):
        """Подключение к базам данных с повторными попытками"""
        connection_start_time = datetime.now()
        logger.info(f"🔍 [CONNECTION] Starting database connections at {connection_start_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")

        for attempt in range(self.max_retries):
            try:
                logger.info(f"🔍 [CONNECTION] Attempt {attempt + 1}/{self.max_retries} to connect to databases")

                # PostgreSQL
                postgres_start_time = datetime.now()
                self.db_conn = psycopg2.connect(
                    host=POSTGRES_HOST, database=POSTGRES_DB, user=POSTGRES_USER,
                    password=POSTGRES_PASSWORD, connect_timeout=10, application_name="calculation_service"
                )
                postgres_end_time = datetime.now()
                postgres_duration = (postgres_end_time - postgres_start_time).total_seconds()
                logger.info(f"🔍 [CONNECTION] Connected to PostgreSQL in {postgres_duration:.3f}s")

                # Qdrant
                qdrant_start_time = datetime.now()
                self.qdrant_client = qdrant_client.QdrantClient(
                    host=QDRANT_HOST, port=QDRANT_PORT, timeout=10
                )
                qdrant_end_time = datetime.now()
                qdrant_duration = (qdrant_end_time - qdrant_start_time).total_seconds()
                logger.info(f"🔍 [CONNECTION] Connected to Qdrant in {qdrant_duration:.3f}s")

                self.connection_retry_count = 0
                connection_end_time = datetime.now()
                total_duration = (connection_end_time - connection_start_time).total_seconds()
                logger.info(f"🔍 [CONNECTION] All database connections established successfully in {total_duration:.3f}s")
                return

            except Exception as e:
                self.connection_retry_count += 1
                logger.error(f"🔍 [CONNECTION] Database connection error (attempt {attempt + 1}/{self.max_retries}): {e}")
                logger.error(f"🔍 [CONNECTION] Error type: {type(e).__name__}")

                if attempt < self.max_retries - 1:
                    logger.info(f"🔍 [CONNECTION] Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                else:
                    connection_end_time = datetime.now()
                    total_duration = (connection_end_time - connection_start_time).total_seconds()
                    logger.error(f"🔍 [CONNECTION] Failed to connect to databases after {self.max_retries} attempts in {total_duration:.3f}s")
                    raise

    def get_db_connection(self):
        """Получение соединения с базой данных с проверкой и переподключением"""
        try:
            if self.db_conn is None or self.db_conn.closed:
                logger.warning("🔍 [DATABASE] Database connection is closed, reconnecting...")
                self.connect_databases()
            
            # Проверяем соединение
            with self.db_conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            
            return self.db_conn
        except Exception as e:
            logger.error(f"🔍 [DATABASE] Error getting database connection: {e}")
            self.connect_databases()
            return self.db_conn

    def create_tables(self):
        """Создание таблиц для расчетов"""
        try:
            conn = self.get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS calculations (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(255) NOT NULL,
                        description TEXT,
                        type VARCHAR(100) NOT NULL,
                        category VARCHAR(100) NOT NULL,
                        status VARCHAR(50) DEFAULT 'pending',
                        parameters JSONB DEFAULT '{}',
                        result JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        created_by VARCHAR(100) NOT NULL,
                        processing_time FLOAT,
                        error_message TEXT
                    )
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_calculations_type ON calculations(type);
                    CREATE INDEX IF NOT EXISTS idx_calculations_category ON calculations(category);
                    CREATE INDEX IF NOT EXISTS idx_calculations_status ON calculations(status);
                    CREATE INDEX IF NOT EXISTS idx_calculations_created_at ON calculations(created_at);
                    CREATE INDEX IF NOT EXISTS idx_calculations_created_by ON calculations(created_by);
                """)
                
                conn.commit()
                logger.info("🔍 [DATABASE] Calculation tables created successfully")
        except Exception as e:
            logger.error(f"🔍 [DATABASE] Error creating tables: {e}")
            raise

    def create_calculation(self, calculation_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Создание нового расчета"""
        try:
            conn = self.get_db_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                import json
                parameters = json.dumps(calculation_data.get('parameters', {}))
                
                cursor.execute("""
                    INSERT INTO calculations (name, description, type, category, parameters, created_by)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING *
                """, (
                    calculation_data['name'],
                    calculation_data.get('description'),
                    calculation_data['type'],
                    calculation_data['category'],
                    parameters,
                    user_id
                ))
                
                calculation = cursor.fetchone()
                conn.commit()
                
                logger.info(f"🔍 [DATABASE] Calculation created successfully: {calculation['id']}")
                return dict(calculation)
        except Exception as e:
            logger.error(f"🔍 [DATABASE] Error creating calculation: {e}")
            raise

    def get_calculations(self, user_id: str, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Получение списка расчетов пользователя"""
        try:
            conn = self.get_db_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM calculations 
                    WHERE created_by = %s 
                    ORDER BY created_at DESC 
                    LIMIT %s OFFSET %s
                """, (user_id, limit, offset))
                
                calculations = cursor.fetchall()
                logger.info(f"🔍 [DATABASE] Retrieved {len(calculations)} calculations for user {user_id}")
                return [dict(calc) for calc in calculations]
        except Exception as e:
            logger.error(f"🔍 [DATABASE] Error getting calculations: {e}")
            return []

    def get_calculation(self, calculation_id: int, user_id: str) -> Optional[Dict[str, Any]]:
        """Получение конкретного расчета"""
        try:
            conn = self.get_db_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM calculations 
                    WHERE id = %s AND created_by = %s
                """, (calculation_id, user_id))
                
                calculation = cursor.fetchone()
                if calculation:
                    logger.info(f"🔍 [DATABASE] Retrieved calculation {calculation_id}")
                    return dict(calculation)
                else:
                    logger.warning(f"🔍 [DATABASE] Calculation {calculation_id} not found for user {user_id}")
                    return None
        except Exception as e:
            logger.error(f"🔍 [DATABASE] Error getting calculation {calculation_id}: {e}")
            return None

    def update_calculation(self, calculation_id: int, user_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Обновление расчета"""
        try:
            conn = self.get_db_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Формируем SET часть запроса динамически
                set_parts = []
                values = []
                
                if 'name' in update_data:
                    set_parts.append("name = %s")
                    values.append(update_data['name'])
                
                if 'description' in update_data:
                    set_parts.append("description = %s")
                    values.append(update_data['description'])
                
                if 'parameters' in update_data:
                    set_parts.append("parameters = %s")
                    values.append(update_data['parameters'])
                
                if not set_parts:
                    return None
                
                set_parts.append("updated_at = CURRENT_TIMESTAMP")
                values.extend([calculation_id, user_id])
                
                query = f"""
                    UPDATE calculations 
                    SET {', '.join(set_parts)}
                    WHERE id = %s AND created_by = %s
                    RETURNING *
                """
                
                cursor.execute(query, values)
                calculation = cursor.fetchone()
                conn.commit()
                
                if calculation:
                    logger.info(f"🔍 [DATABASE] Calculation {calculation_id} updated successfully")
                    return dict(calculation)
                else:
                    logger.warning(f"🔍 [DATABASE] Calculation {calculation_id} not found for update")
                    return None
        except Exception as e:
            logger.error(f"🔍 [DATABASE] Error updating calculation {calculation_id}: {e}")
            return None

    def delete_calculation(self, calculation_id: int, user_id: str) -> bool:
        """Удаление расчета"""
        try:
            conn = self.get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("""
                    DELETE FROM calculations 
                    WHERE id = %s AND created_by = %s
                """, (calculation_id, user_id))
                
                deleted = cursor.rowcount > 0
                conn.commit()
                
                if deleted:
                    logger.info(f"🔍 [DATABASE] Calculation {calculation_id} deleted successfully")
                else:
                    logger.warning(f"🔍 [DATABASE] Calculation {calculation_id} not found for deletion")
                
                return deleted
        except Exception as e:
            logger.error(f"🔍 [DATABASE] Error deleting calculation {calculation_id}: {e}")
            return False

    def execute_calculation(self, calculation_id: int, user_id: str) -> Optional[Dict[str, Any]]:
        """Выполнение расчета"""
        try:
            # Получаем расчет
            calculation = self.get_calculation(calculation_id, user_id)
            if not calculation:
                return None
            
            # Обновляем статус на "processing"
            self.update_calculation_status(calculation_id, user_id, 'processing')
            
            start_time = time.time()
            
            # Выполняем расчет в зависимости от типа
            result = self.perform_calculation(calculation)
            
            processing_time = time.time() - start_time
            
            # Обновляем результат
            self.update_calculation_result(calculation_id, user_id, result, processing_time)
            
            logger.info(f"🔍 [CALCULATION] Calculation {calculation_id} completed in {processing_time:.3f}s")
            return result
            
        except Exception as e:
            logger.error(f"🔍 [CALCULATION] Error executing calculation {calculation_id}: {e}")
            self.update_calculation_status(calculation_id, user_id, 'error', str(e))
            return None

    def perform_calculation(self, calculation: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнение конкретного расчета"""
        calc_type = calculation['type']
        parameters = calculation.get('parameters', {})
        
        logger.info(f"🔍 [CALCULATION] Performing {calc_type} calculation with parameters: {parameters}")
        
        # Здесь будут реализованы конкретные алгоритмы расчетов
        # Пока возвращаем заглушку
        result = {
            'calculation_type': calc_type,
            'parameters': parameters,
            'result': {
                'status': 'completed',
                'message': f'Расчет {calc_type} выполнен успешно',
                'timestamp': datetime.now().isoformat()
            }
        }
        
        return result

    def update_calculation_status(self, calculation_id: int, user_id: str, status: str, error_message: str = None):
        """Обновление статуса расчета"""
        try:
            conn = self.get_db_connection()
            with conn.cursor() as cursor:
                if error_message:
                    cursor.execute("""
                        UPDATE calculations 
                        SET status = %s, error_message = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s AND created_by = %s
                    """, (status, error_message, calculation_id, user_id))
                else:
                    cursor.execute("""
                        UPDATE calculations 
                        SET status = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s AND created_by = %s
                    """, (status, calculation_id, user_id))
                
                conn.commit()
                logger.info(f"🔍 [DATABASE] Calculation {calculation_id} status updated to {status}")
        except Exception as e:
            logger.error(f"🔍 [DATABASE] Error updating calculation status: {e}")

    def update_calculation_result(self, calculation_id: int, user_id: str, result: Dict[str, Any], processing_time: float):
        """Обновление результата расчета"""
        try:
            conn = self.get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE calculations 
                    SET result = %s, processing_time = %s, status = 'completed', updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s AND created_by = %s
                """, (result, processing_time, calculation_id, user_id))
                
                conn.commit()
                logger.info(f"🔍 [DATABASE] Calculation {calculation_id} result updated")
        except Exception as e:
            logger.error(f"🔍 [DATABASE] Error updating calculation result: {e}")

# Инициализация движка расчетов
calculation_engine = CalculationEngine()

# Обработчики сигналов для graceful shutdown
def signal_handler(signum, frame):
    global is_shutting_down
    signal_name = {
        signal.SIGTERM: "SIGTERM",
        signal.SIGINT: "SIGINT",
        signal.SIGHUP: "SIGHUP",
        signal.SIGUSR1: "SIGUSR1",
        signal.SIGUSR2: "SIGUSR2"
    }.get(signum, f"Signal {signum}")

    logger.info(f"🔍 [SHUTDOWN] Received {signal_name} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}, initiating graceful shutdown...")
    logger.info(f"🔍 [SHUTDOWN] Process ID: {os.getpid()}, Parent PID: {os.getppid()}")

    try:
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        logger.info(f"🔍 [SHUTDOWN] Memory usage before shutdown: RSS: {memory_info.rss / 1024 / 1024:.1f}MB, VMS: {memory_info.vms / 1024 / 1024:.1f}MB")
    except Exception as e:
        logger.warning(f"🔍 [SHUTDOWN] Could not get memory info: {e}")

    is_shutting_down = True
    shutdown_event.set()

async def shutdown_event_handler():
    global is_shutting_down
    shutdown_start_time = datetime.now()
    logger.info(f"🔍 [SHUTDOWN] Starting graceful shutdown at {shutdown_start_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
    logger.info(f"🔍 [SHUTDOWN] Process ID: {os.getpid()}, Uptime: {shutdown_start_time - startup_time}")
    is_shutting_down = True

    try:
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        logger.info(f"🔍 [SHUTDOWN] Memory usage before shutdown: RSS: {memory_info.rss / 1024 / 1024:.1f}MB, VMS: {memory_info.vms / 1024 / 1024:.1f}MB")
    except Exception as e:
        logger.warning(f"🔍 [SHUTDOWN] Could not get memory info: {e}")

    logger.info("🔍 [SHUTDOWN] Waiting 5 seconds for current requests to complete...")
    await asyncio.sleep(5)

    try:
        if calculation_engine.db_conn and not calculation_engine.db_conn.closed:
            calculation_engine.db_conn.close()
            logger.info("🔍 [SHUTDOWN] PostgreSQL connection closed successfully")
        else:
            logger.info("🔍 [SHUTDOWN] PostgreSQL connection was already closed")
    except Exception as e:
        logger.error(f"🔍 [SHUTDOWN] Error closing PostgreSQL connection: {e}")

    try:
        if calculation_engine.qdrant_client:
            calculation_engine.qdrant_client.close()
            logger.info("🔍 [SHUTDOWN] Qdrant connection closed successfully")
        else:
            logger.info("🔍 [SHUTDOWN] Qdrant connection was already closed")
    except Exception as e:
        logger.error(f"🔍 [SHUTDOWN] Error closing Qdrant connection: {e}")

    shutdown_end_time = datetime.now()
    shutdown_duration = shutdown_end_time - shutdown_start_time
    logger.info(f"🔍 [SHUTDOWN] Graceful shutdown completed at {shutdown_end_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
    logger.info(f"🔍 [SHUTDOWN] Total shutdown duration: {shutdown_duration.total_seconds():.3f} seconds")

# Middleware для обработки ошибок
class ErrorHandlingMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request_id = f"req_{int(time.time() * 1000)}"
            logger.info(f"🔍 [REQUEST] {request_id}: {scope['method']} {scope['path']}")
            
            if is_shutting_down:
                logger.warning(f"🔍 [REQUEST] {request_id}: Service is shutting down, rejecting request")
                response = JSONResponse(
                    status_code=503,
                    content={"error": "Service is shutting down"}
                )
                await response(scope, receive, send)
                return

        await self.app(scope, receive, send)

# Создание FastAPI приложения
app = FastAPI(
    title="Calculation Service",
    description="Сервис инженерных расчетов в соответствии с нормами и методиками",
    version="1.0.0"
)

# Добавление middleware
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Обработчики событий
app.add_event_handler("startup", lambda: calculation_engine.connect_databases())
app.add_event_handler("startup", lambda: calculation_engine.create_tables())
app.add_event_handler("shutdown", shutdown_event_handler)

# Регистрация обработчиков сигналов
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

# Заглушка для получения пользователя (в реальном приложении здесь будет JWT токен)
def get_current_user():
    # В реальном приложении здесь будет проверка JWT токена
    return "test_user"

# API endpoints
@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    health_start_time = datetime.now()
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "checks": {},
        "uptime": str(datetime.now() - startup_time),
        "process_id": os.getpid()
    }

    try:
        if is_shutting_down:
            health_status["status"] = "shutting_down"
            health_status["checks"]["shutdown"] = "in_progress"
            logger.warning(f"🔍 [HEALTH] Service is shutting down, health check at {health_start_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")

        # Проверка памяти
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            health_status["checks"]["memory"] = {
                "rss_mb": round(memory_info.rss / 1024 / 1024, 1),
                "vms_mb": round(memory_info.vms / 1024 / 1024, 1),
                "percent": round(process.memory_percent(), 1)
            }
            logger.debug(f"🔍 [HEALTH] Memory check: RSS: {health_status['checks']['memory']['rss_mb']}MB, VMS: {health_status['checks']['memory']['vms_mb']}MB")
        except Exception as e:
            health_status["checks"]["memory"] = {"error": str(e)}
            logger.warning(f"🔍 [HEALTH] Memory check failed: {e}")

        # Проверка PostgreSQL
        try:
            conn = calculation_engine.get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            health_status["checks"]["postgresql"] = "healthy"
            logger.debug(f"🔍 [HEALTH] PostgreSQL check: healthy")
        except Exception as e:
            health_status["checks"]["postgresql"] = {"error": str(e)}
            health_status["status"] = "degraded"
            logger.warning(f"🔍 [HEALTH] PostgreSQL check failed: {e}")

        # Проверка Qdrant
        try:
            if calculation_engine.qdrant_client:
                calculation_engine.qdrant_client.get_collections()
                health_status["checks"]["qdrant"] = "healthy"
                logger.debug(f"🔍 [HEALTH] Qdrant check: healthy")
            else:
                health_status["checks"]["qdrant"] = {"error": "Not connected"}
                health_status["status"] = "degraded"
        except Exception as e:
            health_status["checks"]["qdrant"] = {"error": str(e)}
            health_status["status"] = "degraded"
            logger.warning(f"🔍 [HEALTH] Qdrant check failed: {e}")

        health_end_time = datetime.now()
        health_duration = (health_end_time - health_start_time).total_seconds()
        health_status["check_duration_ms"] = round(health_duration * 1000, 2)

        if health_status["status"] == "healthy":
            logger.debug(f"🔍 [HEALTH] Health check passed in {health_duration:.3f}s")
        elif health_status["status"] == "degraded":
            logger.warning(f"🔍 [HEALTH] Health check degraded in {health_duration:.3f}s")
        else:
            logger.error(f"🔍 [HEALTH] Health check failed in {health_duration:.3f}s")

        return health_status

    except Exception as e:
        health_end_time = datetime.now()
        health_duration = (health_end_time - health_start_time).total_seconds()
        logger.error(f"🔍 [HEALTH] Health check error after {health_duration:.3f}s: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "check_duration_ms": round(health_duration * 1000, 2)
            }
        )

@app.get("/calculations", response_model=List[CalculationResponse])
async def list_calculations(
    limit: int = 100,
    offset: int = 0,
    current_user: str = Depends(get_current_user)
):
    """Получение списка расчетов пользователя"""
    if is_shutting_down:
        raise HTTPException(status_code=503, detail="Service is shutting down")

    logger.info(f"🔍 [API] Request list of calculations for user {current_user}")
    
    try:
        calculations = calculation_engine.get_calculations(current_user, limit, offset)
        logger.info(f"🔍 [API] Successfully retrieved {len(calculations)} calculations")
        return calculations
    except Exception as e:
        logger.error(f"🔍 [API] Error retrieving calculations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/calculations", response_model=CalculationResponse)
async def create_calculation(
    calculation: CalculationCreate,
    current_user: str = Depends(get_current_user)
):
    """Создание нового расчета"""
    if is_shutting_down:
        raise HTTPException(status_code=503, detail="Service is shutting down")

    logger.info(f"🔍 [API] Creating calculation: {calculation.name} of type {calculation.type}")
    
    try:
        calculation_data = calculation.model_dump()
        result = calculation_engine.create_calculation(calculation_data, current_user)
        logger.info(f"🔍 [API] Calculation created successfully: {result['id']}")
        return result
    except Exception as e:
        logger.error(f"🔍 [API] Error creating calculation: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/calculations/{calculation_id}", response_model=CalculationResponse)
async def get_calculation(
    calculation_id: int,
    current_user: str = Depends(get_current_user)
):
    """Получение конкретного расчета"""
    if is_shutting_down:
        raise HTTPException(status_code=503, detail="Service is shutting down")

    logger.info(f"🔍 [API] Request calculation {calculation_id} for user {current_user}")
    
    try:
        calculation = calculation_engine.get_calculation(calculation_id, current_user)
        if not calculation:
            raise HTTPException(status_code=404, detail="Calculation not found")
        
        logger.info(f"🔍 [API] Successfully retrieved calculation {calculation_id}")
        return calculation
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"🔍 [API] Error retrieving calculation {calculation_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.put("/calculations/{calculation_id}", response_model=CalculationResponse)
async def update_calculation(
    calculation_id: int,
    calculation_update: CalculationUpdate,
    current_user: str = Depends(get_current_user)
):
    """Обновление расчета"""
    if is_shutting_down:
        raise HTTPException(status_code=503, detail="Service is shutting down")

    logger.info(f"🔍 [API] Updating calculation {calculation_id}")
    
    try:
        update_data = {k: v for k, v in calculation_update.dict().items() if v is not None}
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        result = calculation_engine.update_calculation(calculation_id, current_user, update_data)
        if not result:
            raise HTTPException(status_code=404, detail="Calculation not found")
        
        logger.info(f"🔍 [API] Calculation {calculation_id} updated successfully")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"🔍 [API] Error updating calculation {calculation_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.delete("/calculations/{calculation_id}")
async def delete_calculation(
    calculation_id: int,
    current_user: str = Depends(get_current_user)
):
    """Удаление расчета"""
    if is_shutting_down:
        raise HTTPException(status_code=503, detail="Service is shutting down")

    logger.info(f"🔍 [API] Deleting calculation {calculation_id}")
    
    try:
        success = calculation_engine.delete_calculation(calculation_id, current_user)
        if not success:
            raise HTTPException(status_code=404, detail="Calculation not found")
        
        logger.info(f"🔍 [API] Calculation {calculation_id} deleted successfully")
        return {"message": "Calculation deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"🔍 [API] Error deleting calculation {calculation_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/calculations/{calculation_id}/execute")
async def execute_calculation(
    calculation_id: int,
    current_user: str = Depends(get_current_user)
):
    """Выполнение расчета"""
    if is_shutting_down:
        raise HTTPException(status_code=503, detail="Service is shutting down")

    logger.info(f"🔍 [API] Executing calculation {calculation_id}")
    
    try:
        result = calculation_engine.execute_calculation(calculation_id, current_user)
        if not result:
            raise HTTPException(status_code=404, detail="Calculation not found")
        
        logger.info(f"🔍 [API] Calculation {calculation_id} executed successfully")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"🔍 [API] Error executing calculation {calculation_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    import uvicorn
    startup_time = datetime.now()
    logger.info(f"🔍 [STARTUP] Starting Calculation Service at {startup_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
    logger.info(f"🔍 [STARTUP] Process ID: {os.getpid()}, Parent PID: {os.getppid()}")
    logger.info(f"🔍 [STARTUP] Working directory: {os.getcwd()}")
    logger.info(f"🔍 [STARTUP] Python version: {sys.version}")

    try:
        import platform
        logger.info(f"🔍 [STARTUP] Platform: {platform.platform()}")
        logger.info(f"🔍 [STARTUP] Architecture: {platform.architecture()}")
        logger.info(f"🔍 [STARTUP] Machine: {platform.machine()}")
    except Exception as e:
        logger.warning(f"🔍 [STARTUP] Could not get platform info: {e}")

    try:
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        logger.info(f"🔍 [STARTUP] Initial memory usage: RSS: {memory_info.rss / 1024 / 1024:.1f}MB, VMS: {memory_info.vms / 1024 / 1024:.1f}MB")
    except Exception as e:
        logger.warning(f"🔍 [STARTUP] Could not get initial memory info: {e}")

    uvicorn.run(app, host="0.0.0.0", port=8002)
