"""
Менеджер базы данных для сервиса архива технической документации
"""

import logging
import hashlib
import os
from typing import Dict, Any, List, Optional, Union
from contextlib import contextmanager
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
from datetime import datetime

from .models import (
    ArchiveDocument, DocumentSection, DocumentRelation, 
    ArchiveProject, DocumentSearchRequest, DocumentSearchResponse,
    ProjectStats, DocumentType, ProcessingStatus, ProjectStatus
)
from .config import DATABASE_URL

logger = logging.getLogger(__name__)

class ArchiveDatabaseManager:
    """Менеджер базы данных для архива технической документации"""
    
    def __init__(self, connection_string: str = DATABASE_URL, min_connections: int = 1, max_connections: int = 10):
        self.connection_string = connection_string
        self.min_connections = min_connections
        self.max_connections = max_connections
        
        # Создаем пулы соединений
        self._write_pool = None
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
            
            # Пул для чтения
            self._read_pool = SimpleConnectionPool(
                self.min_connections,
                self.max_connections,
                self.connection_string
            )
            
            logger.info(f"✅ [ARCHIVE_DB] Connection pools initialized (read: {self.min_connections}-{self.max_connections}, write: {self.min_connections}-{self.max_connections})")
            
        except Exception as e:
            logger.error(f"❌ [ARCHIVE_DB] Error initializing connection pools: {e}")
            raise
    
    @contextmanager
    def get_read_connection(self):
        """Контекстный менеджер для получения соединения на чтение"""
        connection = None
        try:
            connection = self._read_pool.getconn()
            yield connection
        except Exception as e:
            logger.error(f"❌ [ARCHIVE_DB] Error in read connection: {e}")
            if connection:
                try:
                    connection.rollback()
                except Exception as rollback_error:
                    logger.error(f"❌ [ARCHIVE_DB] Error during read rollback: {rollback_error}")
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
            logger.error(f"❌ [ARCHIVE_DB] Error in write connection: {e}")
            if connection:
                try:
                    connection.rollback()
                except Exception as rollback_error:
                    logger.error(f"❌ [ARCHIVE_DB] Error during write rollback: {rollback_error}")
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
                logger.error(f"❌ [ARCHIVE_DB] Error in read cursor: {e}")
                if connection:
                    try:
                        connection.rollback()
                    except Exception as rollback_error:
                        logger.error(f"❌ [ARCHIVE_DB] Error during read cursor rollback: {rollback_error}")
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
                logger.error(f"❌ [ARCHIVE_DB] Error in write cursor: {e}")
                if connection:
                    try:
                        connection.rollback()
                    except Exception as rollback_error:
                        logger.error(f"❌ [ARCHIVE_DB] Error during write cursor rollback: {rollback_error}")
                raise
            finally:
                if cursor:
                    cursor.close()
    
    def execute_read_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Выполнение запроса на чтение"""
        try:
            with self.get_read_cursor() as cursor:
                cursor.execute(query, params or ())
                results = cursor.fetchall()
                return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"❌ [ARCHIVE_DB] Error executing read query: {e}")
            logger.error(f"❌ [ARCHIVE_DB] Query: {query}")
            logger.error(f"❌ [ARCHIVE_DB] Params: {params}")
            return []
    
    def execute_write_query(self, query: str, params: Optional[tuple] = None, commit: bool = True) -> Optional[Any]:
        """Выполнение запроса на запись"""
        try:
            with self.get_write_cursor() as (cursor, connection):
                cursor.execute(query, params or ())
                if commit:
                    connection.commit()
                try:
                    result = cursor.fetchone()
                    return result
                except Exception:
                    return None
        except Exception as e:
            logger.error(f"❌ [ARCHIVE_DB] Error executing write query: {e}")
            logger.error(f"❌ [ARCHIVE_DB] Query: {query}")
            logger.error(f"❌ [ARCHIVE_DB] Params: {params}")
            raise
    
    def save_document(self, document: ArchiveDocument) -> int:
        """Сохранение документа в архив"""
        try:
            # Проверяем, не загружен ли уже документ с таким хешем
            if document.document_hash:
                existing_docs = self.execute_read_query("""
                    SELECT id FROM archive_documents 
                    WHERE document_hash = %s
                """, (document.document_hash,))
                
                if existing_docs:
                    raise Exception("Document with this content already exists")
            
            # Сохраняем документ
            result = self.execute_write_query("""
                INSERT INTO archive_documents 
                (project_code, document_type, document_number, document_name, 
                 original_filename, file_type, file_size, file_path, document_hash,
                 processing_status, token_count, version, revision_date, author, 
                 department, status, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                document.project_code,
                document.document_type.value,
                document.document_number,
                document.document_name,
                document.original_filename,
                document.file_type,
                document.file_size,
                document.file_path,
                document.document_hash,
                document.processing_status.value,
                document.token_count,
                document.version,
                document.revision_date,
                document.author,
                document.department,
                document.status,
                document.metadata
            ))
            
            if result:
                document_id = result.get('id') if isinstance(result, dict) else result[0]
                logger.info(f"✅ [SAVE_DOCUMENT] Document saved with ID: {document_id}")
                return document_id
            else:
                raise Exception("Failed to save document")
                
        except Exception as e:
            logger.error(f"❌ [SAVE_DOCUMENT] Error saving document: {e}")
            raise
    
    def save_document_section(self, section: DocumentSection) -> int:
        """Сохранение раздела документа"""
        try:
            result = self.execute_write_query("""
                INSERT INTO archive_document_sections 
                (archive_document_id, section_number, section_title, section_content,
                 page_number, section_type, importance_level, embedding)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                section.archive_document_id,
                section.section_number,
                section.section_title,
                section.section_content,
                section.page_number,
                section.section_type,
                section.importance_level,
                section.embedding
            ))
            
            if result:
                section_id = result.get('id') if isinstance(result, dict) else result[0]
                logger.info(f"✅ [SAVE_SECTION] Section saved with ID: {section_id}")
                return section_id
            else:
                raise Exception("Failed to save section")
                
        except Exception as e:
            logger.error(f"❌ [SAVE_SECTION] Error saving section: {e}")
            raise
    
    def save_project(self, project: ArchiveProject) -> int:
        """Сохранение проекта"""
        try:
            result = self.execute_write_query("""
                INSERT INTO archive_projects 
                (project_code, project_name, project_description, project_manager,
                 department, start_date, end_date, status, total_documents, 
                 total_sections, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (project_code) DO UPDATE SET
                    project_name = EXCLUDED.project_name,
                    project_description = EXCLUDED.project_description,
                    project_manager = EXCLUDED.project_manager,
                    department = EXCLUDED.department,
                    start_date = EXCLUDED.start_date,
                    end_date = EXCLUDED.end_date,
                    status = EXCLUDED.status,
                    metadata = EXCLUDED.metadata,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id
            """, (
                project.project_code,
                project.project_name,
                project.project_description,
                project.project_manager,
                project.department,
                project.start_date,
                project.end_date,
                project.status.value,
                project.total_documents,
                project.total_sections,
                project.metadata
            ))
            
            if result:
                project_id = result.get('id') if isinstance(result, dict) else result[0]
                logger.info(f"✅ [SAVE_PROJECT] Project saved with ID: {project_id}")
                return project_id
            else:
                raise Exception("Failed to save project")
                
        except Exception as e:
            logger.error(f"❌ [SAVE_PROJECT] Error saving project: {e}")
            raise
    
    def get_documents_by_project(self, project_code: str) -> List[ArchiveDocument]:
        """Получение документов по ШИФР проекта"""
        try:
            results = self.execute_read_query("""
                SELECT * FROM archive_documents 
                WHERE project_code = %s
                ORDER BY upload_date DESC
            """, (project_code,))
            
            documents = []
            for row in results:
                document = ArchiveDocument(
                    id=row['id'],
                    project_code=row['project_code'],
                    document_type=DocumentType(row['document_type']),
                    document_number=row['document_number'],
                    document_name=row['document_name'],
                    original_filename=row['original_filename'],
                    file_type=row['file_type'],
                    file_size=row['file_size'],
                    file_path=row['file_path'],
                    document_hash=row['document_hash'],
                    upload_date=row['upload_date'],
                    processing_status=ProcessingStatus(row['processing_status']),
                    processing_error=row['processing_error'],
                    token_count=row['token_count'],
                    version=row['version'],
                    revision_date=row['revision_date'],
                    author=row['author'],
                    department=row['department'],
                    status=row['status'],
                    metadata=row['metadata'] or {},
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )
                documents.append(document)
            
            logger.info(f"📋 [GET_DOCUMENTS_BY_PROJECT] Retrieved {len(documents)} documents for project {project_code}")
            return documents
            
        except Exception as e:
            logger.error(f"❌ [GET_DOCUMENTS_BY_PROJECT] Error getting documents: {e}")
            return []
    
    def get_document_sections(self, document_id: int) -> List[DocumentSection]:
        """Получение разделов документа"""
        try:
            results = self.execute_read_query("""
                SELECT * FROM archive_document_sections 
                WHERE archive_document_id = %s
                ORDER BY page_number, section_number
            """, (document_id,))
            
            sections = []
            for row in results:
                section = DocumentSection(
                    id=row['id'],
                    archive_document_id=row['archive_document_id'],
                    section_number=row['section_number'],
                    section_title=row['section_title'],
                    section_content=row['section_content'],
                    page_number=row['page_number'],
                    section_type=row['section_type'],
                    importance_level=row['importance_level'],
                    embedding=row['embedding'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )
                sections.append(section)
            
            logger.info(f"📋 [GET_DOCUMENT_SECTIONS] Retrieved {len(sections)} sections for document {document_id}")
            return sections
            
        except Exception as e:
            logger.error(f"❌ [GET_DOCUMENT_SECTIONS] Error getting sections: {e}")
            return []
    
    def search_documents(self, search_request: DocumentSearchRequest) -> DocumentSearchResponse:
        """Поиск документов по критериям"""
        try:
            # Строим WHERE условия
            where_conditions = []
            params = []
            
            if search_request.project_code:
                where_conditions.append("project_code = %s")
                params.append(search_request.project_code)
            
            if search_request.document_type:
                where_conditions.append("document_type = %s")
                params.append(search_request.document_type.value)
            
            if search_request.search_query:
                where_conditions.append("(document_name ILIKE %s OR document_number ILIKE %s)")
                search_pattern = f"%{search_request.search_query}%"
                params.extend([search_pattern, search_pattern])
            
            if search_request.date_from:
                where_conditions.append("upload_date >= %s")
                params.append(search_request.date_from)
            
            if search_request.date_to:
                where_conditions.append("upload_date <= %s")
                params.append(search_request.date_to)
            
            if search_request.author:
                where_conditions.append("author ILIKE %s")
                params.append(f"%{search_request.author}%")
            
            if search_request.department:
                where_conditions.append("department ILIKE %s")
                params.append(f"%{search_request.department}%")
            
            if search_request.status:
                where_conditions.append("status = %s")
                params.append(search_request.status)
            
            # Строим запрос
            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
            
            # Подсчитываем общее количество
            count_query = f"SELECT COUNT(*) as total FROM archive_documents WHERE {where_clause}"
            count_result = self.execute_read_query(count_query, tuple(params))
            total_count = count_result[0]['total'] if count_result else 0
            
            # Получаем документы с пагинацией
            query = f"""
                SELECT * FROM archive_documents 
                WHERE {where_clause}
                ORDER BY upload_date DESC
                LIMIT %s OFFSET %s
            """
            params.extend([search_request.limit, search_request.offset])
            
            results = self.execute_read_query(query, tuple(params))
            
            documents = []
            for row in results:
                document = ArchiveDocument(
                    id=row['id'],
                    project_code=row['project_code'],
                    document_type=DocumentType(row['document_type']),
                    document_number=row['document_number'],
                    document_name=row['document_name'],
                    original_filename=row['original_filename'],
                    file_type=row['file_type'],
                    file_size=row['file_size'],
                    file_path=row['file_path'],
                    document_hash=row['document_hash'],
                    upload_date=row['upload_date'],
                    processing_status=ProcessingStatus(row['processing_status']),
                    processing_error=row['processing_error'],
                    token_count=row['token_count'],
                    version=row['version'],
                    revision_date=row['revision_date'],
                    author=row['author'],
                    department=row['department'],
                    status=row['status'],
                    metadata=row['metadata'] or {},
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )
                documents.append(document)
            
            has_more = (search_request.offset + len(documents)) < total_count
            
            response = DocumentSearchResponse(
                documents=documents,
                total_count=total_count,
                page=search_request.offset // search_request.limit + 1,
                page_size=search_request.limit,
                has_more=has_more
            )
            
            logger.info(f"🔍 [SEARCH_DOCUMENTS] Found {len(documents)} documents (total: {total_count})")
            return response
            
        except Exception as e:
            logger.error(f"❌ [SEARCH_DOCUMENTS] Error searching documents: {e}")
            return DocumentSearchResponse()
    
    def get_project_stats(self, project_code: str) -> Optional[ProjectStats]:
        """Получение статистики проекта"""
        try:
            # Получаем информацию о проекте
            project_result = self.execute_read_query("""
                SELECT * FROM archive_projects 
                WHERE project_code = %s
            """, (project_code,))
            
            if not project_result:
                return None
            
            project_row = project_result[0]
            
            # Получаем статистику по типам документов
            type_stats = self.execute_read_query("""
                SELECT document_type, COUNT(*) as count, SUM(file_size) as total_size
                FROM archive_documents 
                WHERE project_code = %s
                GROUP BY document_type
            """, (project_code,))
            
            documents_by_type = {row['document_type']: row['count'] for row in type_stats}
            total_size = sum(row['total_size'] or 0 for row in type_stats)
            
            # Получаем статистику по статусам обработки
            status_stats = self.execute_read_query("""
                SELECT processing_status, COUNT(*) as count
                FROM archive_documents 
                WHERE project_code = %s
                GROUP BY processing_status
            """, (project_code,))
            
            processing_status = {row['processing_status']: row['count'] for row in status_stats}
            
            # Получаем дату последней загрузки
            last_upload_result = self.execute_read_query("""
                SELECT MAX(upload_date) as last_upload
                FROM archive_documents 
                WHERE project_code = %s
            """, (project_code,))
            
            last_upload = last_upload_result[0]['last_upload'] if last_upload_result else None
            
            stats = ProjectStats(
                project_code=project_code,
                project_name=project_row['project_name'],
                total_documents=project_row['total_documents'],
                documents_by_type=documents_by_type,
                total_sections=project_row['total_sections'],
                total_size=total_size,
                last_upload=last_upload,
                processing_status=processing_status
            )
            
            logger.info(f"📊 [GET_PROJECT_STATS] Retrieved stats for project {project_code}")
            return stats
            
        except Exception as e:
            logger.error(f"❌ [GET_PROJECT_STATS] Error getting project stats: {e}")
            return None
    
    def update_document_status(self, document_id: int, status: ProcessingStatus, error_message: str = None):
        """Обновление статуса обработки документа"""
        try:
            if error_message:
                self.execute_write_query("""
                    UPDATE archive_documents 
                    SET processing_status = %s, processing_error = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (status.value, error_message, document_id))
            else:
                self.execute_write_query("""
                    UPDATE archive_documents 
                    SET processing_status = %s, processing_error = NULL, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (status.value, document_id))
            
            logger.info(f"✅ [UPDATE_DOCUMENT_STATUS] Document {document_id} status updated to: {status.value}")
            
        except Exception as e:
            logger.error(f"❌ [UPDATE_DOCUMENT_STATUS] Error updating document {document_id} status: {e}")
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
            logger.error(f"❌ [ARCHIVE_DB] Health check failed: {e}")
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
            logger.info("✅ [ARCHIVE_DB] All connections closed")
        except Exception as e:
            logger.error(f"❌ [ARCHIVE_DB] Error closing connections: {e}")
