import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any, Optional
from core.config import POSTGRES_URL, logger

class DatabaseManager:
    """Менеджер для работы с базой данных"""
    
    def __init__(self):
        self.connection = None
        self.connect()
    
    def connect(self):
        """Подключение к базе данных"""
        try:
            self.connection = psycopg2.connect(POSTGRES_URL)
            logger.info("✅ [DB] Connected to PostgreSQL")
        except Exception as e:
            logger.error(f"❌ [DB] Database connection error: {e}")
            raise
    
    def reconnect(self):
        """Переподключение к базе данных"""
        try:
            if self.connection and not self.connection.closed:
                self.connection.close()
            self.connection = psycopg2.connect(POSTGRES_URL)
            logger.info("✅ [DB] Reconnected to PostgreSQL")
        except Exception as e:
            logger.error(f"❌ [DB] Reconnection error: {e}")
            raise
    
    def get_cursor(self):
        """Получение курсора с RealDictCursor"""
        if not self.connection or self.connection.closed:
            self.connect()
        return self.connection.cursor(cursor_factory=RealDictCursor)
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Выполнение запроса с возвратом результатов"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"❌ [DB] Query execution error: {e}")
            raise
    
    def execute_update(self, query: str, params: tuple = None) -> int:
        """Выполнение запроса на обновление"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute(query, params)
                self.connection.commit()
                return cursor.rowcount
        except Exception as e:
            logger.error(f"❌ [DB] Update execution error: {e}")
            self.connection.rollback()
            raise
    
    def table_exists(self, table_name: str) -> bool:
        """Проверка существования таблицы"""
        query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = %s
            );
        """
        result = self.execute_query(query, (table_name,))
        return result[0]['exists'] if result else False
    
    def get_documents_from_uploaded(self, document_type: str = 'normative') -> List[Dict[str, Any]]:
        """Получение документов из таблицы uploaded_documents"""
        query = """
            SELECT 
                id,
                original_filename as title,
                file_type,
                file_size,
                upload_date,
                processing_status,
                category,
                document_type,
                token_count
            FROM uploaded_documents 
            WHERE document_type = %s
            ORDER BY original_filename ASC
        """
        return self.execute_query(query, (document_type,))
    
    def get_documents_from_chunks(self) -> List[Dict[str, Any]]:
        """Получение документов из таблицы normative_chunks"""
        query = """
            SELECT DISTINCT 
                nc.document_id,
                nc.document_title,
                COUNT(*) as chunks_count,
                MIN(nc.page_number) as first_page,
                MAX(nc.page_number) as last_page,
                STRING_AGG(DISTINCT nc.chunk_type, ', ') as chunk_types,
                ud.category
            FROM normative_chunks nc
            LEFT JOIN uploaded_documents ud ON nc.document_id = ud.id
            GROUP BY nc.document_id, nc.document_title, ud.category
            ORDER BY nc.document_title ASC
        """
        return self.execute_query(query)
    
    def get_document_chunks(self, document_id: int) -> List[Dict[str, Any]]:
        """Получение чанков документа"""
        query = """
            SELECT 
                chunk_id,
                clause_id,
                chapter,
                section,
                page_number,
                chunk_type,
                LENGTH(content) as content_length,
                created_at
            FROM normative_chunks 
            WHERE document_id = %s
            ORDER BY page_number ASC, chunk_id ASC
        """
        return self.execute_query(query, (document_id,))
    
    def get_stats(self) -> Dict[str, Any]:
        """Получение статистики"""
        stats = {}
        
        # Статистика чанков
        if self.table_exists('normative_chunks'):
            chunks_stats = self.execute_query("SELECT COUNT(*) as total FROM normative_chunks")
            stats['total_chunks'] = chunks_stats[0]['total'] if chunks_stats else 0
            
            # Статистика документов
            docs_stats = self.execute_query("SELECT COUNT(DISTINCT document_id) as total FROM normative_chunks")
            stats['total_documents'] = docs_stats[0]['total'] if docs_stats else 0
            
            # Статистика пунктов
            clauses_stats = self.execute_query("SELECT COUNT(DISTINCT clause_id) as total FROM normative_chunks")
            stats['total_clauses'] = clauses_stats[0]['total'] if clauses_stats else 0
            
            # Распределение по типам чанков
            chunk_types = self.execute_query("""
                SELECT chunk_type, COUNT(*) as count 
                FROM normative_chunks 
                GROUP BY chunk_type
            """)
            stats['chunk_types'] = {row['chunk_type']: row['count'] for row in chunk_types}
        else:
            stats.update({
                'total_chunks': 0,
                'total_documents': 0,
                'total_clauses': 0,
                'chunk_types': {}
            })
        
        # Статистика векторов в Qdrant
        stats['vector_indexed'] = 0  # Будет заполнено отдельно
        
        # Распределение по категориям
        if self.table_exists('uploaded_documents'):
            categories = self.execute_query("""
                SELECT category, COUNT(*) as count 
                FROM uploaded_documents 
                WHERE document_type = 'normative'
                GROUP BY category
            """)
            stats['categories'] = {row['category'] or 'other': row['count'] for row in categories}
        else:
            stats['categories'] = {}
        
        return stats
