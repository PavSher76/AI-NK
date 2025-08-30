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
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
import uvicorn
import jwt

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

    def perform_structural_calculation(self, calculation_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнение расчета строительных конструкций"""
        try:
            logger.info(f"🔍 [CALCULATION] Starting structural calculation: {calculation_type}")
            
            if calculation_type == 'strength':
                return self._calculate_strength(parameters)
            elif calculation_type == 'stability':
                return self._calculate_stability(parameters)
            elif calculation_type == 'stiffness':
                return self._calculate_stiffness(parameters)
            elif calculation_type == 'cracking':
                return self._calculate_cracking(parameters)
            elif calculation_type == 'dynamic':
                return self._calculate_dynamic(parameters)
            else:
                raise ValueError(f"Unknown calculation type: {calculation_type}")
                
        except Exception as e:
            logger.error(f"🔍 [CALCULATION] Error in structural calculation: {e}")
            raise

    def _calculate_strength(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Расчет на прочность"""
        try:
            load_value = float(parameters.get('load_value', 0))
            section_area = float(parameters.get('section_area', 0))
            material_strength = float(parameters.get('material_strength', 0))
            safety_factor = float(parameters.get('safety_factor', 1.1))
            
            # Проверка входных данных
            if load_value <= 0 or section_area <= 0 or material_strength <= 0:
                raise ValueError("Все параметры должны быть положительными")
            
            # Расчет напряжения (МПа)
            stress = (load_value * 1000) / section_area  # кН -> Н, см² -> мм²
            
            # Расчет коэффициента использования
            utilization_ratio = (stress / material_strength) * 100
            
            # Расчет запаса прочности
            safety_margin = material_strength / stress
            
            # Проверка прочности
            is_safe = stress <= material_strength / safety_factor
            
            return {
                "calculation_type": "strength",
                "input_parameters": {
                    "load_value": load_value,
                    "section_area": section_area,
                    "material_strength": material_strength,
                    "safety_factor": safety_factor
                },
                "results": {
                    "stress": round(stress, 2),
                    "utilization_ratio": round(utilization_ratio, 2),
                    "safety_margin": round(safety_margin, 2),
                    "is_safe": is_safe
                },
                "units": {
                    "stress": "МПа",
                    "utilization_ratio": "%",
                    "safety_margin": ""
                },
                "formulas": {
                    "stress": "σ = N / A",
                    "utilization_ratio": "η = (σ / R) × 100%",
                    "safety_margin": "γ = R / σ"
                },
                "norms": ["СП 63.13330", "СП 16.13330", "EN 1992", "EN 1993"]
            }
            
        except Exception as e:
            logger.error(f"🔍 [CALCULATION] Error in strength calculation: {e}")
            raise

    def _calculate_stability(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Расчет на устойчивость"""
        try:
            element_length = float(parameters.get('element_length', 0))
            moment_of_inertia = float(parameters.get('moment_of_inertia', 0))
            elastic_modulus = float(parameters.get('elastic_modulus', 0))
            end_conditions = parameters.get('end_conditions', 'pinned')
            
            # Коэффициенты длины в зависимости от типа закрепления
            length_coefficients = {
                'pinned': 1.0,      # Шарнирное
                'fixed': 0.5,       # Жесткое
                'cantilever': 2.0   # Консольное
            }
            
            mu = length_coefficients.get(end_conditions, 1.0)
            
            # Расчет гибкости
            radius_of_gyration = (moment_of_inertia / 100) ** 0.5  # см⁴ -> см²
            slenderness = (mu * element_length * 100) / radius_of_gyration  # м -> см
            
            # Критическая гибкость для стали (приближенно)
            critical_slenderness = 100
            
            # Проверка устойчивости
            is_stable = slenderness <= critical_slenderness
            
            # Расчет критической силы (кН)
            critical_force = (3.14159 ** 2 * elastic_modulus * moment_of_inertia) / ((mu * element_length * 100) ** 2) / 1000
            
            return {
                "calculation_type": "stability",
                "input_parameters": {
                    "element_length": element_length,
                    "moment_of_inertia": moment_of_inertia,
                    "elastic_modulus": elastic_modulus,
                    "end_conditions": end_conditions
                },
                "results": {
                    "slenderness": round(slenderness, 2),
                    "critical_slenderness": critical_slenderness,
                    "critical_force": round(critical_force, 2),
                    "is_stable": is_stable,
                    "length_coefficient": mu
                },
                "units": {
                    "slenderness": "",
                    "critical_slenderness": "",
                    "critical_force": "кН",
                    "length_coefficient": ""
                },
                "formulas": {
                    "slenderness": "λ = μ × l / i",
                    "critical_force": "N_cr = π² × E × I / (μ × l)²"
                },
                "norms": ["СП 16.13330", "СП 63.13330", "EN 1993"]
            }
            
        except Exception as e:
            logger.error(f"🔍 [CALCULATION] Error in stability calculation: {e}")
            raise

    def _calculate_stiffness(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Расчет на жесткость (прогибы)"""
        try:
            span_length = float(parameters.get('span_length', 0))
            distributed_load = float(parameters.get('distributed_load', 0))
            moment_of_inertia = float(parameters.get('moment_of_inertia', 0))
            elastic_modulus = float(parameters.get('elastic_modulus', 0))
            
            # Расчет максимального прогиба (см)
            # Для равномерно распределенной нагрузки на шарнирно опертой балке
            max_deflection = (5 * distributed_load * (span_length * 100) ** 4) / (384 * elastic_modulus * moment_of_inertia)
            
            # Допустимый прогиб (1/200 от пролета)
            allowable_deflection = (span_length * 100) / 200
            
            # Проверка жесткости
            is_adequate = max_deflection <= allowable_deflection
            
            # Относительный прогиб
            relative_deflection = max_deflection / (span_length * 100) * 1000  # в промилле
            
            return {
                "calculation_type": "stiffness",
                "input_parameters": {
                    "span_length": span_length,
                    "distributed_load": distributed_load,
                    "moment_of_inertia": moment_of_inertia,
                    "elastic_modulus": elastic_modulus
                },
                "results": {
                    "max_deflection": round(max_deflection, 3),
                    "allowable_deflection": round(allowable_deflection, 3),
                    "relative_deflection": round(relative_deflection, 2),
                    "is_adequate": is_adequate
                },
                "units": {
                    "max_deflection": "см",
                    "allowable_deflection": "см",
                    "relative_deflection": "‰"
                },
                "formulas": {
                    "max_deflection": "f_max = 5 × q × l⁴ / (384 × E × I)",
                    "allowable_deflection": "f_allow = l / 200"
                },
                "norms": ["СП 63.13330", "СП 64.13330", "EN 1995"]
            }
            
        except Exception as e:
            logger.error(f"🔍 [CALCULATION] Error in stiffness calculation: {e}")
            raise

    def _calculate_cracking(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Расчет на трещиностойкость"""
        try:
            reinforcement_area = float(parameters.get('reinforcement_area', 0))
            concrete_class = parameters.get('concrete_class', 'B25')
            bending_moment = float(parameters.get('bending_moment', 0))
            crack_width_limit = float(parameters.get('crack_width_limit', 0.3))
            
            # Характеристики бетона по классам (МПа)
            concrete_strengths = {
                'B15': 11.0,
                'B20': 15.0,
                'B25': 18.5,
                'B30': 22.0,
                'B35': 25.5
            }
            
            concrete_strength = concrete_strengths.get(concrete_class, 18.5)
            
            # Расчет ширины раскрытия трещин (мм)
            # Упрощенная формула
            crack_width = (bending_moment * 1000) / (reinforcement_area * concrete_strength) * 0.1
            
            # Проверка трещиностойкости
            is_adequate = crack_width <= crack_width_limit
            
            return {
                "calculation_type": "cracking",
                "input_parameters": {
                    "reinforcement_area": reinforcement_area,
                    "concrete_class": concrete_class,
                    "bending_moment": bending_moment,
                    "crack_width_limit": crack_width_limit
                },
                "results": {
                    "crack_width": round(crack_width, 3),
                    "crack_width_limit": crack_width_limit,
                    "is_adequate": is_adequate,
                    "concrete_strength": concrete_strength
                },
                "units": {
                    "crack_width": "мм",
                    "crack_width_limit": "мм",
                    "concrete_strength": "МПа"
                },
                "formulas": {
                    "crack_width": "w = M / (A_s × R_bt) × k",
                    "concrete_strength": "R_bt - расчетное сопротивление бетона растяжению"
                },
                "norms": ["СП 63.13330", "EN 1992"]
            }
            
        except Exception as e:
            logger.error(f"🔍 [CALCULATION] Error in cracking calculation: {e}")
            raise

    def _calculate_dynamic(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Динамический расчет на сейсмические воздействия"""
        try:
            seismic_zone = int(parameters.get('seismic_zone', 6))
            soil_category = parameters.get('soil_category', 'B')
            structure_weight = float(parameters.get('structure_weight', 0))
            natural_period = float(parameters.get('natural_period', 0))
            
            # Коэффициенты сейсмичности по зонам
            seismic_coefficients = {
                6: 0.05,
                7: 0.1,
                8: 0.2,
                9: 0.4
            }
            
            # Коэффициенты грунта
            soil_coefficients = {
                'A': 1.0,
                'B': 1.2,
                'C': 1.5,
                'D': 2.0
            }
            
            k1 = seismic_coefficients.get(seismic_zone, 0.1)
            k2 = soil_coefficients.get(soil_category, 1.2)
            
            # Расчет сейсмической силы (кН)
            seismic_force = structure_weight * k1 * k2
            
            # Расчет ускорения (м/с²)
            acceleration = seismic_force * 9.81 / structure_weight
            
            # Проверка безопасности (упрощенно)
            is_safe = acceleration <= 2.0  # 2 м/с² как предельное ускорение
            
            return {
                "calculation_type": "dynamic",
                "input_parameters": {
                    "seismic_zone": seismic_zone,
                    "soil_category": soil_category,
                    "structure_weight": structure_weight,
                    "natural_period": natural_period
                },
                "results": {
                    "seismic_force": round(seismic_force, 2),
                    "acceleration": round(acceleration, 3),
                    "is_safe": is_safe,
                    "seismic_coefficient": k1,
                    "soil_coefficient": k2
                },
                "units": {
                    "seismic_force": "кН",
                    "acceleration": "м/с²",
                    "seismic_coefficient": "",
                    "soil_coefficient": ""
                },
                "formulas": {
                    "seismic_force": "S = W × k1 × k2",
                    "acceleration": "a = S × g / W"
                },
                "norms": ["СП 14.13330", "EN 1998"]
            }
            
        except Exception as e:
            logger.error(f"🔍 [CALCULATION] Error in dynamic calculation: {e}")
            raise

# OAuth2 схема для авторизации
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

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

# Модели для авторизации
class User(BaseModel):
    id: str
    username: str
    email: str
    role: str
    permissions: List[str] = []

class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[str] = None
    role: Optional[str] = None

# Конфигурация JWT
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Класс для работы с авторизацией
class AuthService:
    def __init__(self):
        self.secret_key = JWT_SECRET_KEY
        self.algorithm = JWT_ALGORITHM
        self.access_token_expire_minutes = ACCESS_TOKEN_EXPIRE_MINUTES
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        """Создание JWT токена"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[TokenData]:
        """Проверка JWT токена"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            username: str = payload.get("sub")
            user_id: str = payload.get("user_id")
            role: str = payload.get("role")
            if username is None:
                return None
            token_data = TokenData(username=username, user_id=user_id, role=role)
            return token_data
        except Exception:
            return None
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Аутентификация пользователя"""
        try:
            # В реальном приложении здесь будет проверка в базе данных
            # Пока используем заглушку
            if username == "test_user" and password == "test_password":
                return User(
                    id="1",
                    username=username,
                    email="test@example.com",
                    role="engineer",
                    permissions=["read", "write", "execute"]
                )
            return None
        except Exception as e:
            logger.error(f"🔍 [AUTH] Authentication error: {e}")
            return None
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Получение пользователя по ID"""
        try:
            # В реальном приложении здесь будет запрос к базе данных
            # Пока используем заглушку
            if user_id == "1":
                return User(
                    id=user_id,
                    username="test_user",
                    email="test@example.com",
                    role="engineer",
                    permissions=["read", "write", "execute"]
                )
            return None
        except Exception as e:
            logger.error(f"🔍 [AUTH] Error getting user by ID: {e}")
            return None

# Инициализация сервиса авторизации
auth_service = AuthService()

# Зависимости для авторизации
async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Получение текущего пользователя из JWT токена"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token_data = auth_service.verify_token(token)
        if token_data is None:
            raise credentials_exception
        
        user = auth_service.get_user_by_id(token_data.user_id)
        if user is None:
            raise credentials_exception
        
        return user
    except Exception as e:
        logger.error(f"🔍 [AUTH] Error getting current user: {e}")
        raise credentials_exception

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Получение активного пользователя"""
    if not current_user:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def require_permission(permission: str):
    """Декоратор для проверки прав доступа"""
    def permission_checker(current_user: User = Depends(get_current_active_user)):
        if permission not in current_user.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return current_user
    return permission_checker

# API endpoints для авторизации
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
                "role": user.role,
                "permissions": user.permissions
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"🔍 [AUTH] Login error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/me")
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Получение информации о текущем пользователе"""
    if is_shutting_down:
        raise HTTPException(status_code=503, detail="Service is shutting down")

    logger.info(f"🔍 [AUTH] User info request for: {current_user.username}")
    
    try:
        return {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "role": current_user.role,
            "permissions": current_user.permissions
        }
    except Exception as e:
        logger.error(f"🔍 [AUTH] Error getting user info: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

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
    current_user: User = Depends(get_current_active_user)
):
    """Получение списка расчетов пользователя"""
    if is_shutting_down:
        raise HTTPException(status_code=503, detail="Service is shutting down")

    logger.info(f"🔍 [API] Request list of calculations for user {current_user}")
    
    try:
        calculations = calculation_engine.get_calculations(current_user.id, limit, offset)
        logger.info(f"🔍 [API] Successfully retrieved {len(calculations)} calculations")
        return calculations
    except Exception as e:
        logger.error(f"🔍 [API] Error retrieving calculations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/calculations", response_model=CalculationResponse)
async def create_calculation(
    calculation: CalculationCreate,
    current_user: User = Depends(get_current_active_user)
):
    """Создание нового расчета"""
    if is_shutting_down:
        raise HTTPException(status_code=503, detail="Service is shutting down")

    logger.info(f"🔍 [API] Creating calculation: {calculation.name} of type {calculation.type}")
    
    try:
        calculation_data = calculation.model_dump()
        result = calculation_engine.create_calculation(calculation_data, current_user.id)
        logger.info(f"🔍 [API] Calculation created successfully: {result['id']}")
        return result
    except Exception as e:
        logger.error(f"🔍 [API] Error creating calculation: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/calculations/{calculation_id}", response_model=CalculationResponse)
async def get_calculation(
    calculation_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Получение конкретного расчета"""
    if is_shutting_down:
        raise HTTPException(status_code=503, detail="Service is shutting down")

    logger.info(f"🔍 [API] Request calculation {calculation_id} for user {current_user}")
    
    try:
        calculation = calculation_engine.get_calculation(calculation_id, current_user.id)
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
    current_user: User = Depends(get_current_active_user)
):
    """Обновление расчета"""
    if is_shutting_down:
        raise HTTPException(status_code=503, detail="Service is shutting down")

    logger.info(f"🔍 [API] Updating calculation {calculation_id}")
    
    try:
        update_data = {k: v for k, v in calculation_update.dict().items() if v is not None}
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        result = calculation_engine.update_calculation(calculation_id, current_user.id, update_data)
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
    current_user: User = Depends(get_current_active_user)
):
    """Удаление расчета"""
    if is_shutting_down:
        raise HTTPException(status_code=503, detail="Service is shutting down")

    logger.info(f"🔍 [API] Deleting calculation {calculation_id}")
    
    try:
        success = calculation_engine.delete_calculation(calculation_id, current_user.id)
        if not success:
            raise HTTPException(status_code=404, detail="Calculation not found")
        
        logger.info(f"🔍 [API] Calculation {calculation_id} deleted successfully")
        return {"message": "Calculation deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"🔍 [API] Error deleting calculation {calculation_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/calculations/structural/execute")
async def execute_structural_calculation(
    calculation_type: str,
    parameters: Dict[str, Any],
    current_user: User = Depends(require_permission("execute"))
):
    """Выполнение расчета строительных конструкций"""
    if is_shutting_down:
        raise HTTPException(status_code=503, detail="Service is shutting down")

    logger.info(f"🔍 [API] Executing structural calculation: {calculation_type}: Parameters: {parameters}")
    
    try:
        # Выполняем расчет
        calculation_start_time = datetime.now()
        result = calculation_engine.perform_structural_calculation(calculation_type, parameters)
        calculation_end_time = datetime.now()
        processing_time = (calculation_end_time - calculation_start_time).total_seconds()
        
        # Добавляем время обработки к результату
        result["processing_time"] = processing_time
        result["executed_at"] = calculation_end_time.isoformat()
        
        logger.info(f"🔍 [API] Structural calculation completed in {processing_time:.3f}s")
        return result
        
    except ValueError as e:
        logger.error(f"🔍 [API] Validation error in structural calculation: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"🔍 [API] Error executing structural calculation: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/calculations/{calculation_id}/execute")
async def execute_calculation(
    calculation_id: int,
    current_user: User = Depends(require_permission("execute"))
):
    """Выполнение расчета"""
    if is_shutting_down:
        raise HTTPException(status_code=503, detail="Service is shutting down")

    logger.info(f"🔍 [API] Executing calculation {calculation_id}")
    
    try:
        result = calculation_engine.execute_calculation(calculation_id, current_user.id)
        if not result:
            raise HTTPException(status_code=404, detail="Calculation not found")
        
        logger.info(f"🔍 [API] Calculation {calculation_id} executed successfully")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"🔍 [API] Error executing calculation {calculation_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/calculations/structural/types")
async def get_structural_calculation_types():
    """Получение доступных типов расчетов строительных конструкций"""
    if is_shutting_down:
        raise HTTPException(status_code=503, detail="Service is shutting down")

    logger.info(f"🔍 [API] Requesting structural calculation types")
    
    try:
        types = [
            {
                "id": "strength",
                "name": "Расчёт на прочность",
                "description": "Проверка прочности элементов конструкций",
                "norms": ["СП 63.13330", "СП 16.13330", "EN 1992", "EN 1993"],
                "parameters": [
                    {"name": "load_value", "label": "Расчетная нагрузка", "unit": "кН", "type": "number", "required": True},
                    {"name": "section_area", "label": "Площадь сечения", "unit": "см²", "type": "number", "required": True},
                    {"name": "material_strength", "label": "Расчетное сопротивление материала", "unit": "МПа", "type": "number", "required": True},
                    {"name": "safety_factor", "label": "Коэффициент надежности", "unit": "", "type": "number", "required": False}
                ]
            },
            {
                "id": "stability",
                "name": "Расчёт на устойчивость",
                "description": "Проверка устойчивости сжатых элементов",
                "norms": ["СП 16.13330", "СП 63.13330", "EN 1993"],
                "parameters": [
                    {"name": "element_length", "label": "Длина элемента", "unit": "м", "type": "number", "required": True},
                    {"name": "moment_of_inertia", "label": "Момент инерции", "unit": "см⁴", "type": "number", "required": True},
                    {"name": "elastic_modulus", "label": "Модуль упругости", "unit": "МПа", "type": "number", "required": True},
                    {"name": "end_conditions", "label": "Тип закрепления", "unit": "", "type": "select", "required": True, "options": ["pinned", "fixed", "cantilever"]}
                ]
            },
            {
                "id": "stiffness",
                "name": "Расчёт на жёсткость",
                "description": "Проверка прогибов и деформаций",
                "norms": ["СП 63.13330", "СП 64.13330", "EN 1995"],
                "parameters": [
                    {"name": "span_length", "label": "Пролет", "unit": "м", "type": "number", "required": True},
                    {"name": "distributed_load", "label": "Распределенная нагрузка", "unit": "кН/м", "type": "number", "required": True},
                    {"name": "moment_of_inertia", "label": "Момент инерции", "unit": "см⁴", "type": "number", "required": True},
                    {"name": "elastic_modulus", "label": "Модуль упругости", "unit": "МПа", "type": "number", "required": True}
                ]
            },
            {
                "id": "cracking",
                "name": "Расчёт на трещиностойкость",
                "description": "Проверка ширины раскрытия трещин",
                "norms": ["СП 63.13330", "EN 1992"],
                "parameters": [
                    {"name": "reinforcement_area", "label": "Площадь арматуры", "unit": "мм²", "type": "number", "required": True},
                    {"name": "concrete_class", "label": "Класс бетона", "unit": "", "type": "select", "required": True, "options": ["B15", "B20", "B25", "B30", "B35"]},
                    {"name": "bending_moment", "label": "Изгибающий момент", "unit": "кН·м", "type": "number", "required": True},
                    {"name": "crack_width_limit", "label": "Предельная ширина трещин", "unit": "мм", "type": "number", "required": True}
                ]
            },
            {
                "id": "dynamic",
                "name": "Динамический расчёт",
                "description": "Расчет на сейсмические воздействия",
                "norms": ["СП 14.13330", "EN 1998"],
                "parameters": [
                    {"name": "seismic_zone", "label": "Сейсмический район", "unit": "", "type": "select", "required": True, "options": ["6", "7", "8", "9"]},
                    {"name": "soil_category", "label": "Категория грунта", "unit": "", "type": "select", "required": True, "options": ["A", "B", "C", "D"]},
                    {"name": "structure_weight", "label": "Масса конструкции", "unit": "т", "type": "number", "required": True},
                    {"name": "natural_period", "label": "Собственный период колебаний", "unit": "с", "type": "number", "required": True}
                ]
            }
        ]
        
        logger.info(f"🔍 [API] Successfully returned {len(types)} structural calculation types")
        return types
        
    except Exception as e:
        logger.error(f"🔍 [API] Error getting structural calculation types: {e}")
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
