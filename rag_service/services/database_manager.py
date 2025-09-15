import logging
from typing import Dict, Any, List, Optional, Union
from contextlib import contextmanager
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
import time
import random
from functools import wraps

# Настройка логирования
logger = logging.getLogger(__name__)

def retry_on_connection_error(max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0, exponential_base: float = 2.0):
    """Декоратор для повторных попыток при ошибках соединения"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except (psycopg2.OperationalError, psycopg2.InterfaceError, psycopg2.DatabaseError) as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(f"❌ [RETRY] Max retries ({max_retries}) exceeded for {func.__name__}: {e}")
                        raise e
                    
                    # Вычисляем задержку с экспоненциальным backoff и jitter
                    delay = min(base_delay * (exponential_base ** attempt), max_delay)
                    jitter = random.uniform(0.1, 0.3) * delay
                    total_delay = delay + jitter
                    
                    logger.warning(f"⚠️ [RETRY] Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}: {e}")
                    logger.info(f"🔄 [RETRY] Retrying in {total_delay:.2f} seconds...")
                    time.sleep(total_delay)
                    
                except Exception as e:
                    # Для других типов ошибок не делаем повторные попытки
                    logger.error(f"❌ [ERROR] Non-retryable error in {func.__name__}: {e}")
                    raise e
            
            # Этот код никогда не должен выполниться, но на всякий случай
            if last_exception:
                raise last_exception
                
        return wrapper
    return decorator

class DatabaseManager:
    """Улучшенный менеджер для работы с базой данных PostgreSQL с разделением на чтение и запись"""
    
    def __init__(self, connection_string: str, min_connections: int = 1, max_connections: int = 10, 
                 max_retries: int = 3, retry_delay: float = 1.0):
        self.connection_string = connection_string
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Создаем пул соединений для записи
        self._write_pool = None
        # Создаем пул соединений для чтения (read-only)
        self._read_pool = None
        
        # Флаг для отслеживания состояния пулов
        self._pools_initialized = False
        
        # Инициализируем пулы соединений
        self._init_connection_pools()
    
    @retry_on_connection_error(max_retries=5, base_delay=2.0, max_delay=30.0)
    def _init_connection_pools(self):
        """Инициализация пулов соединений с повторными попытками"""
        try:
            # Пул для записи
            self._write_pool = SimpleConnectionPool(
                self.min_connections,
                self.max_connections,
                self.connection_string
            )
            
            # Пул для чтения (отдельный пул для операций чтения)
            self._read_pool = SimpleConnectionPool(
                self.min_connections,
                self.max_connections,
                self.connection_string
            )
            
            self._pools_initialized = True
            logger.info(f"✅ [DB_MANAGER] Connection pools initialized (read: {self.min_connections}-{self.max_connections}, write: {self.min_connections}-{self.max_connections})")
            
        except Exception as e:
            logger.error(f"❌ [DB_MANAGER] Error initializing connection pools: {e}")
            self._pools_initialized = False
            raise
    
    def _ensure_pools_initialized(self):
        """Проверка и переинициализация пулов соединений при необходимости"""
        if not self._pools_initialized or not self._write_pool or not self._read_pool:
            logger.warning("⚠️ [DB_MANAGER] Connection pools not initialized, attempting to reinitialize...")
            self._init_connection_pools()
    
    def _recreate_pools(self):
        """Пересоздание пулов соединений при критических ошибках"""
        try:
            logger.warning("🔄 [DB_MANAGER] Recreating connection pools...")
            
            # Закрываем существующие пулы
            if self._write_pool:
                try:
                    self._write_pool.closeall()
                except Exception as e:
                    logger.warning(f"⚠️ [DB_MANAGER] Error closing write pool: {e}")
            
            if self._read_pool:
                try:
                    self._read_pool.closeall()
                except Exception as e:
                    logger.warning(f"⚠️ [DB_MANAGER] Error closing read pool: {e}")
            
            # Пересоздаем пулы
            self._write_pool = None
            self._read_pool = None
            self._pools_initialized = False
            
            self._init_connection_pools()
            logger.info("✅ [DB_MANAGER] Connection pools recreated successfully")
            
        except Exception as e:
            logger.error(f"❌ [DB_MANAGER] Error recreating connection pools: {e}")
            raise
    
    @contextmanager
    def get_read_connection(self):
        """Контекстный менеджер для получения соединения на чтение с повторными попытками"""
        connection = None
        attempt = 0
        max_attempts = self.max_retries + 1
        
        while attempt < max_attempts:
            try:
                self._ensure_pools_initialized()
                connection = self._read_pool.getconn()
                yield connection
                return
                
            except (psycopg2.OperationalError, psycopg2.InterfaceError, psycopg2.DatabaseError) as e:
                attempt += 1
                logger.warning(f"⚠️ [READ_CONNECTION] Attempt {attempt}/{max_attempts} failed: {e}")
                
                if connection:
                    try:
                        self._read_pool.putconn(connection, close=True)
                    except Exception as put_error:
                        logger.warning(f"⚠️ [READ_CONNECTION] Error putting connection back: {put_error}")
                    connection = None
                
                if attempt >= max_attempts:
                    logger.error(f"❌ [READ_CONNECTION] Max attempts exceeded, recreating pools...")
                    try:
                        self._recreate_pools()
                    except Exception as recreate_error:
                        logger.error(f"❌ [READ_CONNECTION] Failed to recreate pools: {recreate_error}")
                    raise e
                
                # Ждем перед следующей попыткой
                delay = min(self.retry_delay * (2 ** (attempt - 1)), 30.0)
                time.sleep(delay)
                
            except Exception as e:
                logger.error(f"❌ [READ_CONNECTION] Non-retryable error: {e}")
                if connection:
                    try:
                        connection.rollback()
                    except Exception as rollback_error:
                        logger.error(f"❌ [READ_CONNECTION] Error during rollback: {rollback_error}")
                raise
            finally:
                if connection and attempt < max_attempts:
                    try:
                        self._read_pool.putconn(connection)
                    except Exception as put_error:
                        logger.warning(f"⚠️ [READ_CONNECTION] Error putting connection back in finally: {put_error}")
    
    @contextmanager
    def get_write_connection(self):
        """Контекстный менеджер для получения соединения на запись с повторными попытками"""
        connection = None
        attempt = 0
        max_attempts = self.max_retries + 1
        
        while attempt < max_attempts:
            try:
                self._ensure_pools_initialized()
                connection = self._write_pool.getconn()
                yield connection
                return
                
            except (psycopg2.OperationalError, psycopg2.InterfaceError, psycopg2.DatabaseError) as e:
                attempt += 1
                logger.warning(f"⚠️ [WRITE_CONNECTION] Attempt {attempt}/{max_attempts} failed: {e}")
                
                if connection:
                    try:
                        self._write_pool.putconn(connection, close=True)
                    except Exception as put_error:
                        logger.warning(f"⚠️ [WRITE_CONNECTION] Error putting connection back: {put_error}")
                    connection = None
                
                if attempt >= max_attempts:
                    logger.error(f"❌ [WRITE_CONNECTION] Max attempts exceeded, recreating pools...")
                    try:
                        self._recreate_pools()
                    except Exception as recreate_error:
                        logger.error(f"❌ [WRITE_CONNECTION] Failed to recreate pools: {recreate_error}")
                    raise e
                
                # Ждем перед следующей попыткой
                delay = min(self.retry_delay * (2 ** (attempt - 1)), 30.0)
                time.sleep(delay)
                
            except Exception as e:
                logger.error(f"❌ [WRITE_CONNECTION] Non-retryable error: {e}")
                if connection:
                    try:
                        connection.rollback()
                    except Exception as rollback_error:
                        logger.error(f"❌ [WRITE_CONNECTION] Error during rollback: {rollback_error}")
                raise
            finally:
                if connection and attempt < max_attempts:
                    try:
                        self._write_pool.putconn(connection)
                    except Exception as put_error:
                        logger.warning(f"⚠️ [WRITE_CONNECTION] Error putting connection back in finally: {put_error}")
    
    @contextmanager
    def get_read_cursor(self):
        """Контекстный менеджер для получения курсора на чтение"""
        with self.get_read_connection() as connection:
            cursor = None
            try:
                cursor = connection.cursor(cursor_factory=RealDictCursor)
                yield cursor
            except Exception as e:
                logger.error(f"❌ [DB_MANAGER] Error in read cursor: {e}")
                if connection:
                    try:
                        connection.rollback()
                    except Exception as rollback_error:
                        logger.error(f"❌ [DB_MANAGER] Error during read cursor rollback: {rollback_error}")
                raise
            finally:
                if cursor:
                    cursor.close()
    
    @contextmanager
    def get_write_cursor(self):
        """Контекстный менеджер для получения курсора на запись"""
        with self.get_write_connection() as connection:
            cursor = None
            try:
                cursor = connection.cursor(cursor_factory=RealDictCursor)
                yield cursor, connection
            except Exception as e:
                logger.error(f"❌ [DB_MANAGER] Error in write cursor: {e}")
                if connection:
                    try:
                        connection.rollback()
                    except Exception as rollback_error:
                        logger.error(f"❌ [DB_MANAGER] Error during write cursor rollback: {rollback_error}")
                raise
            finally:
                if cursor:
                    cursor.close()
    
    def execute_read_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Выполнение запроса на чтение с улучшенной обработкой ошибок"""
        try:
            with self.get_read_cursor() as cursor:
                cursor.execute(query, params or ())
                results = cursor.fetchall()
                return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"❌ [DB_MANAGER] Error executing read query: {e}")
            logger.error(f"❌ [DB_MANAGER] Query: {query}")
            logger.error(f"❌ [DB_MANAGER] Params: {params}")
            return []
    
    def execute_write_query(self, query: str, params: Optional[tuple] = None, commit: bool = True) -> Optional[Any]:
        """Выполнение запроса на запись с улучшенной обработкой ошибок"""
        try:
            with self.get_write_cursor() as (cursor, connection):
                cursor.execute(query, params or ())
                if commit:
                    connection.commit()
                # Для INSERT ... RETURNING запросов всегда пытаемся получить результат
                try:
                    result = cursor.fetchone()
                    logger.info(f"🔍 [EXECUTE_WRITE_QUERY] fetchone() result: {result}, type: {type(result)}")
                    return result
                except Exception as e:
                    # Если нет результата (например, для обычных INSERT без RETURNING)
                    logger.info(f"🔍 [EXECUTE_WRITE_QUERY] fetchone() failed: {e}")
                    return None
        except Exception as e:
            logger.error(f"❌ [DB_MANAGER] Error executing write query: {e}")
            logger.error(f"❌ [DB_MANAGER] Query: {query}")
            logger.error(f"❌ [DB_MANAGER] Params: {params}")
            raise
    
    def health_check(self) -> Dict[str, Any]:
        """Проверка здоровья соединений с базой данных"""
        try:
            # Проверяем соединение на чтение
            with self.get_read_connection() as read_conn:
                with read_conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    read_ok = cursor.fetchone()[0] == 1
            
            # Проверяем соединение на запись
            with self.get_write_connection() as write_conn:
                with write_conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    write_ok = cursor.fetchone()[0] == 1
            
            return {
                "status": "healthy" if read_ok and write_ok else "unhealthy",
                "read_connection": "ok" if read_ok else "error",
                "write_connection": "ok" if write_ok else "error",
                "read_pool_size": len(self._read_pool._pool) if self._read_pool else 0,
                "write_pool_size": len(self._write_pool._pool) if self._write_pool else 0
            }
        except Exception as e:
            logger.error(f"❌ [DB_MANAGER] Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    def close_all_connections(self):
        """Закрытие всех соединений"""
        try:
            if self._read_pool:
                self._read_pool.closeall()
            if self._write_pool:
                self._write_pool.closeall()
            logger.info("✅ [DB_MANAGER] All connections closed")
        except Exception as e:
            logger.error(f"❌ [DB_MANAGER] Error closing connections: {e}")
    
    # Обратная совместимость
    def get_connection(self):
        """Получение соединения с базой данных (для обратной совместимости)"""
        logger.warning("⚠️ [DB_MANAGER] Using deprecated get_connection() method. Use get_read_connection() or get_write_connection() instead.")
        return self._write_pool.getconn() if self._write_pool else None
    
    def get_cursor(self):
        """Получение курсора для работы с базой данных (для обратной совместимости)"""
        logger.warning("⚠️ [DB_MANAGER] Using deprecated get_cursor() method. Use get_read_cursor() or get_write_cursor() instead.")
        connection = self.get_connection()
        if connection:
            return connection.cursor(cursor_factory=RealDictCursor)
        return None
    
    def save_document_to_db(self, document_id: int, filename: str, original_filename: str, 
                           file_type: str, file_size: int, document_hash: str, 
                           category: str, document_type: str) -> int:
        """Сохранение документа в базу данных"""
        try:
            # Проверяем, не загружен ли уже документ с таким хешем (используем соединение на чтение)
            existing_docs = self.execute_read_query("""
                SELECT id FROM uploaded_documents 
                WHERE document_hash = %s
            """, (document_hash,))
            
            if existing_docs:
                raise Exception("Document with this content already exists")
            
            # Сохраняем документ в базу данных (используем соединение на запись)
            logger.info(f"🔍 [SAVE_DOCUMENT] Attempting to save document with ID: {document_id}")
            result = self.execute_write_query("""
                INSERT INTO uploaded_documents 
                (id, filename, original_filename, file_type, file_size, document_hash, 
                 category, document_type, processing_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'pending')
                RETURNING id
            """, (
                document_id,
                filename,
                original_filename,
                file_type,
                file_size,
                document_hash,
                category,
                document_type
            ))
            
            logger.info(f"🔍 [SAVE_DOCUMENT] Query result: {result}, type: {type(result)}")
            
            # Для INSERT ... RETURNING result должен содержать RealDictRow с ID
            if result:
                # RealDictRow можно использовать как словарь
                if hasattr(result, 'get'):
                    saved_id = result.get('id', document_id)
                elif hasattr(result, '__getitem__'):
                    saved_id = result[0] if len(result) > 0 else document_id
                else:
                    saved_id = document_id
                logger.info(f"✅ [SAVE_DOCUMENT] Document saved with ID from result: {saved_id}")
            else:
                # Fallback на переданный document_id
                saved_id = document_id
                logger.warning(f"⚠️ [SAVE_DOCUMENT] No result from query, using fallback ID: {saved_id}")
            return saved_id
            
        except Exception as e:
            logger.error(f"❌ [SAVE_DOCUMENT] Error saving document: {e}")
            raise

    def update_document_status(self, document_id: int, status: str, error_message: str = None):
        """Обновление статуса обработки документа"""
        try:
            if error_message:
                self.execute_write_query("""
                    UPDATE uploaded_documents 
                    SET processing_status = %s, processing_error = %s
                    WHERE id = %s
                """, (status, error_message, document_id))
            else:
                self.execute_write_query("""
                    UPDATE uploaded_documents 
                    SET processing_status = %s, processing_error = NULL
                    WHERE id = %s
                """, (status, document_id))
            
            logger.info(f"✅ [UPDATE_STATUS] Document {document_id} status updated to: {status}")
            
        except Exception as e:
            logger.error(f"❌ [UPDATE_STATUS] Error updating document {document_id} status: {e}")
            raise

    def get_documents(self) -> List[Dict[str, Any]]:
        """Получение списка документов из базы данных (использует соединение на чтение)"""
        try:
            documents = self.execute_read_query("""
                SELECT ud.id, ud.original_filename, ud.category, ud.processing_status, ud.upload_date, 
                       ud.file_size, COALESCE(ud.token_count, 0) as token_count,
                       COALESCE(chunk_counts.chunks_count, 0) as chunks_count
                FROM uploaded_documents ud
                LEFT JOIN (
                    SELECT document_id, COUNT(*) as chunks_count 
                    FROM normative_chunks 
                    GROUP BY document_id
                ) chunk_counts ON ud.id = chunk_counts.document_id
                ORDER BY ud.upload_date DESC
            """)
            
            result = []
            for doc in documents:
                result.append({
                    'id': doc['id'],
                    'title': doc['original_filename'],
                    'original_filename': doc['original_filename'],
                    'filename': doc['original_filename'],
                    'category': doc['category'],
                    'status': doc['processing_status'],
                    'processing_status': doc['processing_status'],
                    'upload_date': doc['upload_date'].isoformat() if doc['upload_date'] else None,
                    'file_size': doc['file_size'],
                    'token_count': doc['token_count'],
                    'vector_indexed': doc['processing_status'] == 'completed',
                    'chunks_count': doc['chunks_count']
                })
            
            logger.info(f"📋 [GET_DOCUMENTS] Retrieved {len(result)} documents")
            return result
            
        except Exception as e:
            logger.error(f"❌ [GET_DOCUMENTS] Error getting documents: {e}")
            return []

    def get_documents_from_uploaded(self, document_type: str = 'all') -> List[Dict[str, Any]]:
        """Получение документов из таблицы uploaded_documents (использует соединение на чтение)"""
        try:
            documents = self.execute_read_query("""
                SELECT ud.id, ud.original_filename, ud.category, ud.processing_status, ud.upload_date, 
                       ud.file_size, COALESCE(ud.token_count, 0) as token_count,
                       COALESCE(chunk_counts.chunks_count, 0) as chunks_count
                FROM uploaded_documents ud
                LEFT JOIN (
                    SELECT document_id, COUNT(*) as chunks_count 
                    FROM normative_chunks 
                    GROUP BY document_id
                ) chunk_counts ON ud.id = chunk_counts.document_id
                WHERE ud.category = %s OR %s = 'all'
                ORDER BY ud.upload_date DESC
            """, (document_type, document_type))
            
            result = []
            for doc in documents:
                result.append({
                    'id': doc['id'],
                    'title': doc['original_filename'],
                    'original_filename': doc['original_filename'],
                    'filename': doc['original_filename'],
                    'category': doc['category'],
                    'status': doc['processing_status'],
                    'processing_status': doc['processing_status'],
                    'upload_date': doc['upload_date'].isoformat() if doc['upload_date'] else None,
                    'file_size': doc['file_size'],
                    'token_count': doc['token_count'],
                    'vector_indexed': doc['processing_status'] == 'completed',
                    'chunks_count': doc['chunks_count']
                })
            
            logger.info(f"📋 [GET_DOCUMENTS_FROM_UPLOADED] Retrieved {len(result)} documents of type '{document_type}'")
            return result
                
        except Exception as e:
            logger.error(f"❌ [GET_DOCUMENTS_FROM_UPLOADED] Error getting documents: {e}")
            return []

    def get_document_chunks(self, document_id: int) -> List[Dict[str, Any]]:
        """Получение чанков документа (использует соединение на чтение)"""
        try:
            # Получаем название документа
            document_results = self.execute_read_query("""
                SELECT original_filename 
                FROM uploaded_documents 
                WHERE id = %s
            """, (document_id,))
            
            # Убираем расширение файла из названия
            import re
            original_filename = document_results[0]['original_filename'] if document_results else f"Document_{document_id}"
            document_title = re.sub(r'\.(pdf|txt|doc|docx)$', '', original_filename, flags=re.IGNORECASE)
            logger.info(f"🔍 [GET_DOCUMENT_CHUNKS] Document title: {document_title}")
            
            # Получаем чанки документа
            chunks = self.execute_read_query("""
                SELECT chunk_id, content, chapter as section_title, page_number as page, section
                FROM normative_chunks
                WHERE document_id = %s
                ORDER BY page_number, chunk_id
            """, (document_id,))
            
            result = []
            for chunk in chunks:
                result.append({
                    'chunk_id': chunk['chunk_id'],
                    'content': chunk['content'],
                    'section_title': chunk['section_title'],
                    'chunk_type': 'paragraph',  # Устанавливаем тип по умолчанию
                    'page': chunk['page'],
                    'section': chunk['section'],
                    'document_title': document_title  # Добавляем название документа
                })
            
            logger.info(f"📋 [GET_DOCUMENT_CHUNKS] Retrieved {len(result)} chunks for document {document_id} ({document_title})")
            return result
                
        except Exception as e:
            logger.error(f"❌ [GET_DOCUMENT_CHUNKS] Error getting chunks for document {document_id}: {e}")
            return []

    def get_stats(self) -> Dict[str, Any]:
        """Получение статистики базы данных (использует соединение на чтение)"""
        try:
            # Выполняем все запросы статистики через соединение на чтение
            total_docs_result = self.execute_read_query("SELECT COUNT(*) as total_documents FROM uploaded_documents")
            total_docs = total_docs_result[0]['total_documents'] if total_docs_result else 0
            
            total_chunks_result = self.execute_read_query("SELECT COUNT(*) as total_chunks FROM normative_chunks")
            total_chunks = total_chunks_result[0]['total_chunks'] if total_chunks_result else 0
            
            pending_docs_result = self.execute_read_query("SELECT COUNT(*) as pending_docs FROM uploaded_documents WHERE processing_status = 'pending'")
            pending_docs = pending_docs_result[0]['pending_docs'] if pending_docs_result else 0
            
            # Подсчитываем общее количество токенов
            total_tokens_result = self.execute_read_query("SELECT COALESCE(SUM(token_count), 0) as total_tokens FROM uploaded_documents")
            total_tokens = total_tokens_result[0]['total_tokens'] if total_tokens_result else 0
            
            stats = {
                'total_documents': total_docs,
                'total_chunks': total_chunks,
                'pending_documents': pending_docs,
                'total_tokens': total_tokens
            }
            
            logger.info(f"📊 [GET_STATS] Retrieved stats: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"❌ [GET_STATS] Error getting stats: {e}")
            return {
                'total_documents': 0,
                'total_chunks': 0,
                'pending_documents': 0,
                'total_tokens': 0
            }
    
    def get_pending_documents_for_indexing(self) -> List[Dict[str, Any]]:
        """Получение документов, ожидающих индексации"""
        try:
            pending_docs = self.execute_read_query("""
                SELECT id, original_filename, category, processing_status, upload_date
                FROM uploaded_documents 
                WHERE processing_status IN ('pending', 'failed')
                ORDER BY upload_date ASC
            """)
            
            logger.info(f"📋 [PENDING_DOCS] Found {len(pending_docs)} documents pending indexing")
            return pending_docs
            
        except Exception as e:
            logger.error(f"❌ [PENDING_DOCS] Error getting pending documents: {e}")
            return []
    
    def mark_document_for_retry(self, document_id: int, error_message: str = None):
        """Помечаем документ для повторной попытки индексации"""
        try:
            self.execute_write_query("""
                UPDATE uploaded_documents 
                SET processing_status = 'pending', 
                    processing_error = %s,
                    retry_count = COALESCE(retry_count, 0) + 1,
                    last_retry_attempt = NOW()
                WHERE id = %s
            """, (error_message, document_id))
            
            logger.info(f"🔄 [RETRY_MARK] Document {document_id} marked for retry")
            
        except Exception as e:
            logger.error(f"❌ [RETRY_MARK] Error marking document {document_id} for retry: {e}")
            raise
    
    def get_documents_with_failed_indexing(self, max_retries: int = 3) -> List[Dict[str, Any]]:
        """Получение документов с неудачной индексацией для повторной попытки"""
        try:
            failed_docs = self.execute_read_query("""
                SELECT id, original_filename, category, processing_status, processing_error, 
                       COALESCE(retry_count, 0) as retry_count, last_retry_attempt
                FROM uploaded_documents 
                WHERE processing_status = 'failed' 
                  AND COALESCE(retry_count, 0) < %s
                ORDER BY last_retry_attempt ASC NULLS FIRST, upload_date ASC
            """, (max_retries,))
            
            logger.info(f"🔄 [FAILED_DOCS] Found {len(failed_docs)} documents for retry (max_retries={max_retries})")
            return failed_docs
            
        except Exception as e:
            logger.error(f"❌ [FAILED_DOCS] Error getting failed documents: {e}")
            return []
    
    def update_indexing_progress(self, document_id: int, progress_percent: int, status_message: str = None):
        """Обновление прогресса индексации документа"""
        try:
            self.execute_write_query("""
                UPDATE uploaded_documents 
                SET processing_status = 'indexing',
                    indexing_progress = %s,
                    processing_error = %s,
                    last_processing_update = NOW()
                WHERE id = %s
            """, (progress_percent, status_message, document_id))
            
            logger.debug(f"📊 [PROGRESS] Document {document_id} indexing progress: {progress_percent}%")
            
        except Exception as e:
            logger.error(f"❌ [PROGRESS] Error updating progress for document {document_id}: {e}")
            raise
