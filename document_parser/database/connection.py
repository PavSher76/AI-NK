import psycopg2
import qdrant_client
import time
import logging
from datetime import datetime
from typing import Optional
from psycopg2.extras import RealDictCursor

from core.config import (
    get_database_config, 
    get_qdrant_config, 
    MAX_RETRIES, 
    RETRY_DELAY
)

logger = logging.getLogger(__name__)

class DatabaseConnection:
    """Класс для управления подключениями к базам данных"""
    
    def __init__(self):
        self.db_conn = None
        self.qdrant_client = None
        self.connection_retry_count = 0
        self.max_retries = MAX_RETRIES
        self.retry_delay = RETRY_DELAY
        self.connect_databases()
    
    def connect_databases(self):
        """Подключение к базам данных с повторными попытками"""
        connection_start_time = datetime.now()
        logger.info(f"🔍 [CONNECTION] Starting database connections at {connection_start_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"🔍 [CONNECTION] Attempt {attempt + 1}/{self.max_retries} to connect to databases")
                
                # PostgreSQL
                postgres_start_time = datetime.now()
                db_config = get_database_config()
                self.db_conn = psycopg2.connect(**db_config)
                postgres_end_time = datetime.now()
                postgres_duration = (postgres_end_time - postgres_start_time).total_seconds()
                logger.info(f"🔍 [CONNECTION] Connected to PostgreSQL in {postgres_duration:.3f}s")
                
                # Qdrant
                qdrant_start_time = datetime.now()
                qdrant_config = get_qdrant_config()
                self.qdrant_client = qdrant_client.QdrantClient(**qdrant_config)
                qdrant_end_time = datetime.now()
                qdrant_duration = (qdrant_end_time - qdrant_start_time).total_seconds()
                logger.info(f"🔍 [CONNECTION] Connected to Qdrant in {qdrant_duration:.3f}s")
                
                # Сброс счетчика попыток при успешном подключении
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
        """Безопасное получение соединения с базой данных"""
        try:
            # Проверяем, что соединение существует и активно
            if self.db_conn is None or self.db_conn.closed:
                logger.info("🔍 [CONNECTION] Reconnecting to PostgreSQL...")
                db_config = get_database_config()
                self.db_conn = psycopg2.connect(**db_config)
                logger.info("🔍 [CONNECTION] Reconnected to PostgreSQL")
            
            # Проверяем, что соединение работает
            try:
                with self.db_conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    cursor.fetchone()
            except Exception as test_error:
                logger.warning(f"🔍 [CONNECTION] Database connection test failed: {test_error}")
                # Переподключаемся при ошибке теста
                if self.db_conn and not self.db_conn.closed:
                    try:
                        self.db_conn.close()
                    except:
                        pass
                
                db_config = get_database_config()
                self.db_conn = psycopg2.connect(**db_config)
                logger.info("🔍 [CONNECTION] Reconnected to PostgreSQL after test failure")
            
            return self.db_conn
            
        except Exception as e:
            logger.error(f"🔍 [CONNECTION] Database connection check failed: {e}")
            # Пытаемся переподключиться
            try:
                if self.db_conn and not self.db_conn.closed:
                    self.db_conn.close()
            except Exception as close_error:
                logger.error(f"🔍 [CONNECTION] Error closing connection: {close_error}")
            
            try:
                db_config = get_database_config()
                self.db_conn = psycopg2.connect(**db_config)
                logger.info("🔍 [CONNECTION] Reconnected to PostgreSQL after error")
                return self.db_conn
            except Exception as reconnect_error:
                logger.error(f"🔍 [CONNECTION] Failed to reconnect: {reconnect_error}")
                raise
    
    def get_qdrant_client(self):
        """Получение клиента Qdrant"""
        if self.qdrant_client is None:
            logger.info("🔍 [CONNECTION] Reconnecting to Qdrant...")
            qdrant_config = get_qdrant_config()
            self.qdrant_client = qdrant_client.QdrantClient(**qdrant_config)
            logger.info("🔍 [CONNECTION] Reconnected to Qdrant")
        
        return self.qdrant_client
    
    def close_connections(self):
        """Закрытие всех соединений"""
        try:
            if self.db_conn and not self.db_conn.closed:
                self.db_conn.close()
                logger.info("🔍 [CONNECTION] PostgreSQL connection closed")
        except Exception as e:
            logger.error(f"🔍 [CONNECTION] Error closing PostgreSQL connection: {e}")
        
        try:
            if self.qdrant_client:
                self.qdrant_client.close()
                logger.info("🔍 [CONNECTION] Qdrant connection closed")
        except Exception as e:
            logger.error(f"🔍 [CONNECTION] Error closing Qdrant connection: {e}")
    
    def execute_in_transaction(self, func):
        """Выполнение функции в транзакции"""
        conn = self.get_db_connection()
        with TransactionContext(conn) as transaction_conn:
            return func(transaction_conn)
    
    def execute_in_read_only_transaction(self, func):
        """Выполнение функции в транзакции только для чтения"""
        conn = self.get_db_connection()
        with ReadOnlyTransactionContext(conn) as transaction_conn:
            return func(transaction_conn)

class TransactionContext:
    """Контекстный менеджер для управления транзакциями PostgreSQL"""
    
    def __init__(self, connection):
        self.connection = connection
        self.cursor = None
        self.transaction_id = f"tx_{int(time.time() * 1000)}"
    
    def __enter__(self):
        """Начало транзакции"""
        try:
            self.cursor = self.connection.cursor()
            logger.debug(f"🔍 [TRANSACTION] {self.transaction_id}: Transaction started")
            return self.connection
        except Exception as e:
            logger.error(f"🔍 [TRANSACTION] {self.transaction_id}: Error starting transaction: {e}")
            raise
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Завершение транзакции с автоматическим commit/rollback"""
        try:
            if exc_type is None:
                # Нет исключений - коммитим транзакцию
                self.connection.commit()
                logger.debug(f"🔍 [TRANSACTION] {self.transaction_id}: Transaction committed successfully")
            else:
                # Есть исключения - откатываем транзакцию
                self.connection.rollback()
                logger.error(f"🔍 [TRANSACTION] {self.transaction_id}: Transaction rolled back due to error: {exc_type.__name__}: {exc_val}")
        except Exception as e:
            logger.error(f"🔍 [TRANSACTION] {self.transaction_id}: Error during transaction cleanup: {e}")
            # Пытаемся откатить транзакцию при ошибке очистки
            try:
                if not self.connection.closed:
                    self.connection.rollback()
                    logger.debug(f"🔍 [TRANSACTION] {self.transaction_id}: Emergency rollback completed")
            except Exception as rollback_error:
                logger.error(f"🔍 [TRANSACTION] {self.transaction_id}: Emergency rollback failed: {rollback_error}")
        finally:
            # Закрываем курсор
            if self.cursor:
                try:
                    self.cursor.close()
                    logger.debug(f"🔍 [TRANSACTION] {self.transaction_id}: Cursor closed")
                except Exception as cursor_error:
                    logger.error(f"🔍 [TRANSACTION] {self.transaction_id}: Error closing cursor: {cursor_error}")

class ReadOnlyTransactionContext:
    """Контекстный менеджер для операций только для чтения PostgreSQL"""
    
    def __init__(self, connection):
        self.connection = connection
        self.cursor = None
        self.transaction_id = f"read_tx_{int(time.time() * 1000)}"
    
    def __enter__(self):
        """Начало транзакции только для чтения"""
        try:
            self.cursor = self.connection.cursor()
            # Устанавливаем транзакцию только для чтения
            self.cursor.execute("SET TRANSACTION READ ONLY")
            logger.debug(f"🔍 [READ_TRANSACTION] {self.transaction_id}: Read-only transaction started")
            return self.connection
        except Exception as e:
            logger.error(f"🔍 [READ_TRANSACTION] {self.transaction_id}: Error starting read-only transaction: {e}")
            raise
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Завершение транзакции только для чтения"""
        try:
            if exc_type is None:
                # Нет исключений - коммитим транзакцию (для чтения это безопасно)
                self.connection.commit()
                logger.debug(f"🔍 [READ_TRANSACTION] {self.transaction_id}: Read-only transaction committed successfully")
            else:
                # Есть исключения - откатываем транзакцию
                self.connection.rollback()
                logger.error(f"🔍 [READ_TRANSACTION] {self.transaction_id}: Read-only transaction rolled back due to error: {exc_type.__name__}: {exc_val}")
        except Exception as e:
            logger.error(f"🔍 [READ_TRANSACTION] {self.transaction_id}: Error during read-only transaction cleanup: {e}")
            # Пытаемся откатить транзакцию при ошибке очистки
            try:
                if not self.connection.closed:
                    self.connection.rollback()
                    logger.debug(f"🔍 [READ_TRANSACTION] {self.transaction_id}: Emergency rollback completed")
            except Exception as rollback_error:
                logger.error(f"🔍 [READ_TRANSACTION] {self.transaction_id}: Emergency rollback failed: {rollback_error}")
        finally:
            # Закрываем курсор
            if self.cursor:
                try:
                    self.cursor.close()
                    logger.debug(f"🔍 [READ_TRANSACTION] {self.transaction_id}: Cursor closed")
                except Exception as cursor_error:
                    logger.error(f"🔍 [READ_TRANSACTION] {self.transaction_id}: Error closing cursor: {cursor_error}")
