import logging
from typing import Dict, Any, List

# Настройка логирования
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Менеджер для работы с базой данных PostgreSQL"""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.connection = None
    
    def get_connection(self):
        """Получение соединения с базой данных"""
        import psycopg2
        if not self.connection or self.connection.closed:
            self.connection = psycopg2.connect(self.connection_string)
        return self.connection
    
    def get_cursor(self):
        """Получение курсора для работы с базой данных"""
        import psycopg2
        from psycopg2.extras import RealDictCursor
        # Используем то же соединение, что и get_connection()
        connection = self.get_connection()
        return connection.cursor(cursor_factory=RealDictCursor)
    
    def save_document_to_db(self, document_id: int, filename: str, original_filename: str, 
                           file_type: str, file_size: int, document_hash: str, 
                           category: str, document_type: str) -> int:
        """Сохранение документа в базу данных"""
        try:
            with self.get_cursor() as cursor:
                # Проверяем, не загружен ли уже документ с таким хешем
                cursor.execute("""
                    SELECT id FROM uploaded_documents 
                    WHERE document_hash = %s
                """, (document_hash,))
                
                if cursor.fetchone():
                    raise Exception("Document with this content already exists")
                
                # Сохраняем документ в базу данных
                cursor.execute("""
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
                
                saved_id = cursor.fetchone()['id']
                cursor.connection.commit()
                logger.info(f"✅ [SAVE_DOCUMENT] Document saved with ID: {saved_id}")
                return saved_id
                
        except Exception as e:
            logger.error(f"❌ [SAVE_DOCUMENT] Error saving document: {e}")
            raise

    def update_document_status(self, document_id: int, status: str, error_message: str = None):
        """Обновление статуса обработки документа"""
        try:
            with self.get_cursor() as cursor:
                if error_message:
                    cursor.execute("""
                        UPDATE uploaded_documents 
                        SET processing_status = %s, processing_error = %s
                        WHERE id = %s
                    """, (status, error_message, document_id))
                else:
                    cursor.execute("""
                        UPDATE uploaded_documents 
                        SET processing_status = %s, processing_error = NULL
                        WHERE id = %s
                    """, (status, document_id))
                
                cursor.connection.commit()
                logger.info(f"✅ [UPDATE_STATUS] Document {document_id} status updated to: {status}")
                
        except Exception as e:
            logger.error(f"❌ [UPDATE_STATUS] Error updating document {document_id} status: {e}")

    def get_documents(self) -> List[Dict[str, Any]]:
        """Получение списка документов из базы данных"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("""
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
                documents = cursor.fetchall()
                
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
                
                return result
                
        except Exception as e:
            logger.error(f"❌ [GET_DOCUMENTS] Error getting documents: {e}")
            return []

    def get_documents_from_uploaded(self, document_type: str = 'all') -> List[Dict[str, Any]]:
        """Получение документов из таблицы uploaded_documents"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("""
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
                documents = cursor.fetchall()
                
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
                
                return result
                
        except Exception as e:
            logger.error(f"❌ [GET_DOCUMENTS_FROM_UPLOADED] Error getting documents: {e}")
            return []

    def get_document_chunks(self, document_id: int) -> List[Dict[str, Any]]:
        """Получение чанков документа"""
        try:
            with self.get_cursor() as cursor:
                # Получаем название документа
                cursor.execute("""
                    SELECT original_filename 
                    FROM uploaded_documents 
                    WHERE id = %s
                """, (document_id,))
                document_result = cursor.fetchone()
                # Убираем расширение файла из названия
                import re
                original_filename = document_result['original_filename'] if document_result else f"Document_{document_id}"
                document_title = re.sub(r'\.(pdf|txt|doc|docx)$', '', original_filename, flags=re.IGNORECASE)
                
                # Получаем чанки документа
                cursor.execute("""
                    SELECT chunk_id, content, chapter as section_title, chunk_type, page_number as page, section
                    FROM normative_chunks
                    WHERE document_id = %s
                    ORDER BY page_number, chunk_id
                """, (document_id,))
                chunks = cursor.fetchall()
                
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
        """Получение статистики базы данных"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SELECT COUNT(*) as total_documents FROM uploaded_documents")
                total_docs = cursor.fetchone()['total_documents']
                
                cursor.execute("SELECT COUNT(*) as total_chunks FROM normative_chunks")
                total_chunks = cursor.fetchone()['total_chunks']
                
                cursor.execute("SELECT COUNT(*) as pending_docs FROM uploaded_documents WHERE processing_status = 'pending'")
                pending_docs = cursor.fetchone()['pending_docs']
                
                # Подсчитываем общее количество токенов
                cursor.execute("SELECT COALESCE(SUM(token_count), 0) as total_tokens FROM uploaded_documents")
                total_tokens = cursor.fetchone()['total_tokens']
            
            return {
                'total_documents': total_docs,
                'total_chunks': total_chunks,
                'pending_documents': pending_docs,
                'total_tokens': total_tokens
            }
            
        except Exception as e:
            logger.error(f"❌ [GET_STATS] Error getting stats: {e}")
            return {
                'total_documents': 0,
                'total_chunks': 0,
                'pending_documents': 0,
                'total_tokens': 0
            }
