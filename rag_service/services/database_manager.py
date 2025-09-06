import logging
from typing import Dict, Any, List, Optional, Union
from contextlib import contextmanager
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool

# Настройка логирования
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Улучшенный менеджер для работы с базой данных PostgreSQL с разделением на чтение и запись"""
    
    def __init__(self, connection_string: str, min_connections: int = 1, max_connections: int = 10):
        self.connection_string = connection_string
        self.min_connections = min_connections
        self.max_connections = max_connections
        
        # Создаем пул соединений для записи
        self._write_pool = None
        # Создаем пул соединений для чтения (read-only)
        self._read_pool = None
        
        # Инициализируем пулы соединений
        self._init_connection_pools()
    
    def _init_connection_pools(self):
        """Инициализация пулов соединений"""
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
            
            logger.info(f"✅ [DB_MANAGER] Connection pools initialized (read: {self.min_connections}-{self.max_connections}, write: {self.min_connections}-{self.max_connections})")
            
        except Exception as e:
            logger.error(f"❌ [DB_MANAGER] Error initializing connection pools: {e}")
            raise
    
    @contextmanager
    def get_read_connection(self):
        """Контекстный менеджер для получения соединения на чтение"""
        connection = None
        try:
            connection = self._read_pool.getconn()
            yield connection
        except Exception as e:
            logger.error(f"❌ [DB_MANAGER] Error in read connection: {e}")
            if connection:
                try:
                    connection.rollback()
                except Exception as rollback_error:
                    logger.error(f"❌ [DB_MANAGER] Error during read rollback: {rollback_error}")
            raise
        finally:
            if connection:
                self._read_pool.putconn(connection)
    
    @contextmanager
    def get_write_connection(self):
        """Контекстный менеджер для получения соединения на запись"""
        connection = None
        try:
            connection = self._write_pool.getconn()
            yield connection
        except Exception as e:
            logger.error(f"❌ [DB_MANAGER] Error in write connection: {e}")
            if connection:
                try:
                    connection.rollback()
                except Exception as rollback_error:
                    logger.error(f"❌ [DB_MANAGER] Error during write rollback: {rollback_error}")
            raise
        finally:
            if connection:
                self._write_pool.putconn(connection)
    
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
                return cursor.fetchone() if cursor.description else None
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
            
            saved_id = result[0] if result else document_id
            logger.info(f"✅ [SAVE_DOCUMENT] Document saved with ID: {saved_id}")
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
                SELECT chunk_id, content, chapter as section_title, chunk_type, page_number as page, section
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
                    'chunk_type': chunk['chunk_type'],
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
