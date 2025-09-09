"""
Модуль для работы с базой данных
"""
import logging
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from typing import List, Dict, Any, Optional
from datetime import datetime

from config import DATABASE_URL
from models import CalculationCreate, CalculationResponse, CalculationUpdate

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Менеджер для работы с базой данных"""
    
    def __init__(self):
        self.database_url = DATABASE_URL
        self._init_database()
    
    def _init_database(self):
        """Инициализация базы данных"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Создание таблицы расчетов, если она не существует
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS calculations (
                            id SERIAL PRIMARY KEY,
                            name VARCHAR(255) NOT NULL,
                            description TEXT,
                            type VARCHAR(100) NOT NULL,
                            category VARCHAR(100) NOT NULL,
                            parameters JSONB,
                            results JSONB,
                            status VARCHAR(50) DEFAULT 'created',
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            user_id INTEGER
                        )
                    """)
                    
                    # Добавление колонки user_id, если она не существует
                    cursor.execute("""
                        ALTER TABLE calculations 
                        ADD COLUMN IF NOT EXISTS user_id INTEGER
                    """)
                    
                    # Добавление колонки created_by, если она не существует
                    cursor.execute("""
                        ALTER TABLE calculations 
                        ADD COLUMN IF NOT EXISTS created_by INTEGER
                    """)
                    
                    # Создание индексов
                    cursor.execute("""
                        CREATE INDEX IF NOT EXISTS idx_calculations_type 
                        ON calculations(type)
                    """)
                    
                    cursor.execute("""
                        CREATE INDEX IF NOT EXISTS idx_calculations_category 
                        ON calculations(category)
                    """)
                    
                    cursor.execute("""
                        CREATE INDEX IF NOT EXISTS idx_calculations_user_id 
                        ON calculations(user_id)
                    """)
                    
                    conn.commit()
                    logger.info("✅ Database initialized successfully")
                    
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """Контекстный менеджер для получения соединения с БД"""
        conn = None
        try:
            conn = psycopg2.connect(self.database_url)
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"❌ Database connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    @contextmanager
    def get_cursor(self):
        """Контекстный менеджер для получения курсора"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                yield cursor
    
    def create_calculation(self, calculation: CalculationCreate, user_id: Optional[int] = None) -> int:
        """Создание нового расчета"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO calculations (name, description, type, category, parameters, user_id, created_by)
                    VALUES (%(name)s, %(description)s, %(type)s, %(category)s, %(parameters)s, %(user_id)s, %(created_by)s)
                    RETURNING id
                """, {
                    'name': calculation.name,
                    'description': calculation.description,
                    'type': calculation.type,
                    'category': calculation.category,
                    'parameters': json.dumps(calculation.parameters) if calculation.parameters else None,
                    'user_id': user_id,
                    'created_by': user_id or 1  # Используем user_id или 1 по умолчанию
                })
                
                result = cursor.fetchone()
                calculation_id = result['id']
                
                cursor.connection.commit()
                logger.info(f"✅ Calculation created with ID: {calculation_id}")
                return calculation_id
                
        except Exception as e:
            logger.error(f"❌ Error creating calculation: {e}")
            raise
    
    def get_calculation(self, calculation_id: int) -> Optional[CalculationResponse]:
        """Получение расчета по ID"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM calculations WHERE id = %s
                """, (calculation_id,))
                
                result = cursor.fetchone()
                if result:
                    logger.info(f"🔍 [DEBUG] Database result: {result}")
                    calculation = CalculationResponse(**dict(result))
                    logger.info(f"🔍 [DEBUG] CalculationResponse object: {calculation}")
                    logger.info(f"🔍 [DEBUG] CalculationResponse type: {calculation.type}")
                    return calculation
                return None
                
        except Exception as e:
            logger.error(f"❌ Error getting calculation {calculation_id}: {e}")
            raise
    
    def get_calculations(self, user_id: Optional[int] = None, 
                        calculation_type: Optional[str] = None,
                        category: Optional[str] = None,
                        limit: int = 100, offset: int = 0) -> List[CalculationResponse]:
        """Получение списка расчетов"""
        try:
            with self.get_cursor() as cursor:
                query = "SELECT * FROM calculations WHERE 1=1"
                params = []
                
                if user_id is not None:
                    query += " AND user_id = %s"
                    params.append(user_id)
                
                if calculation_type:
                    query += " AND type = %s"
                    params.append(calculation_type)
                
                if category:
                    query += " AND category = %s"
                    params.append(category)
                
                query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
                params.extend([limit, offset])
                
                cursor.execute(query, params)
                results = cursor.fetchall()
                
                return [CalculationResponse(**dict(row)) for row in results]
                
        except Exception as e:
            logger.error(f"❌ Error getting calculations: {e}")
            raise
    
    def update_calculation(self, calculation_id: int, 
                          calculation_update: CalculationUpdate) -> Optional[CalculationResponse]:
        """Обновление расчета"""
        try:
            with self.get_cursor() as cursor:
                # Подготовка полей для обновления
                update_fields = []
                params = []
                
                if calculation_update.name is not None:
                    update_fields.append("name = %s")
                    params.append(calculation_update.name)
                
                if calculation_update.description is not None:
                    update_fields.append("description = %s")
                    params.append(calculation_update.description)
                
                if calculation_update.parameters is not None:
                    update_fields.append("parameters = %s")
                    params.append(json.dumps(calculation_update.parameters))
                
                if not update_fields:
                    return self.get_calculation(calculation_id)
                
                update_fields.append("updated_at = CURRENT_TIMESTAMP")
                params.append(calculation_id)
                
                query = f"""
                    UPDATE calculations 
                    SET {', '.join(update_fields)}
                    WHERE id = %s
                    RETURNING *
                """
                
                cursor.execute(query, params)
                result = cursor.fetchone()
                
                if result:
                    cursor.connection.commit()
                    return CalculationResponse(**dict(result))
                return None
                
        except Exception as e:
            logger.error(f"❌ Error updating calculation {calculation_id}: {e}")
            raise
    
    def delete_calculation(self, calculation_id: int) -> bool:
        """Удаление расчета"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("""
                    DELETE FROM calculations WHERE id = %s
                """, (calculation_id,))
                
                deleted_count = cursor.rowcount
                cursor.connection.commit()
                
                if deleted_count > 0:
                    logger.info(f"✅ Calculation {calculation_id} deleted")
                    return True
                return False
                
        except Exception as e:
            logger.error(f"❌ Error deleting calculation {calculation_id}: {e}")
            raise
    
    def update_calculation_results(self, calculation_id: int, 
                                 results: Dict[str, Any], 
                                 status: str = "completed") -> bool:
        """Обновление результатов расчета"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("""
                    UPDATE calculations 
                    SET result = %s, status = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (json.dumps(results), status, calculation_id))
                
                updated_count = cursor.rowcount
                cursor.connection.commit()
                
                if updated_count > 0:
                    logger.info(f"✅ Calculation {calculation_id} results updated")
                    return True
                return False
                
        except Exception as e:
            logger.error(f"❌ Error updating calculation results {calculation_id}: {e}")
            raise
    
    def get_calculation_stats(self) -> Dict[str, Any]:
        """Получение статистики по расчетам"""
        try:
            with self.get_cursor() as cursor:
                # Общее количество расчетов
                cursor.execute("SELECT COUNT(*) as total FROM calculations")
                total = cursor.fetchone()['total']
                
                # Количество по типам
                cursor.execute("""
                    SELECT type, COUNT(*) as count 
                    FROM calculations 
                    GROUP BY type
                """)
                by_type = {row['type']: row['count'] for row in cursor.fetchall()}
                
                # Количество по категориям
                cursor.execute("""
                    SELECT category, COUNT(*) as count 
                    FROM calculations 
                    GROUP BY category
                """)
                by_category = {row['category']: row['count'] for row in cursor.fetchall()}
                
                # Количество по статусам
                cursor.execute("""
                    SELECT status, COUNT(*) as count 
                    FROM calculations 
                    GROUP BY status
                """)
                by_status = {row['status']: row['count'] for row in cursor.fetchall()}
                
                return {
                    'total': total,
                    'by_type': by_type,
                    'by_category': by_category,
                    'by_status': by_status
                }
                
        except Exception as e:
            logger.error(f"❌ Error getting calculation stats: {e}")
            raise


# Глобальный экземпляр менеджера базы данных
db_manager = DatabaseManager()
