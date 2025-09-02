import logging
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime
import qdrant_client
from qdrant_client.models import Distance, VectorParams, PointStruct
import psycopg2
from psycopg2.extras import RealDictCursor
import re
import requests
import json

# Настройка логирования
logger = logging.getLogger(__name__)
model_logger = logging.getLogger("model")

class OllamaEmbeddingService:
    """Сервис для работы с эмбеддингами через Ollama BGE-M3"""
    
    def __init__(self, ollama_url: str = "http://10.112.123.18:11434"):
        self.ollama_url = ollama_url
        self.model_name = "bge-m3"
        logger.info(f"🤖 [OLLAMA_EMBEDDING] Initialized with {self.model_name} at {ollama_url}")
    
    def create_embedding(self, text: str) -> List[float]:
        """Создание эмбеддинга для текста с использованием Ollama BGE-M3"""
        try:
            # Подготавливаем запрос к Ollama
            payload = {
                "model": self.model_name,
                "prompt": text,
                "options": {
                    "embedding_only": True
                }
            }
            
            # Отправляем запрос к Ollama
            response = requests.post(
                f"{self.ollama_url}/api/embeddings",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                embedding = result.get("embedding", [])
                
                if embedding:
                    # Нормализуем эмбеддинг
                    embedding_array = np.array(embedding)
                    normalized_embedding = embedding_array / np.linalg.norm(embedding_array)
                    
                    model_logger.info(f"✅ [EMBEDDING] Generated embedding for text: '{text[:100]}...'")
                    return normalized_embedding.tolist()
                else:
                    raise ValueError("Empty embedding received from Ollama")
            else:
                raise Exception(f"Ollama API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"❌ [EMBEDDING] Error creating embedding: {e}")
            raise e

class DatabaseManager:
    """Менеджер для работы с базой данных PostgreSQL"""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
    
    def get_cursor(self):
        """Получение курсора для работы с базой данных"""
        connection = psycopg2.connect(self.connection_string)
        return connection.cursor(cursor_factory=RealDictCursor)

class OllamaRAGService:
    """RAG сервис с использованием Ollama BGE-M3 для эмбеддингов"""
    
    def __init__(self):
        # Конфигурация
        self.QDRANT_URL = "http://qdrant:6333"  # Qdrant в Docker
        self.POSTGRES_URL = "postgresql://norms_user:norms_password@norms-db:5432/norms_db"  # БД в Docker
        self.VECTOR_COLLECTION = "normative_documents"
        self.VECTOR_SIZE = 1024  # Размер эмбеддинга BGE-M3
        
        # Инициализация клиентов
        self.qdrant_client = qdrant_client.QdrantClient(self.QDRANT_URL)
        self.db_manager = DatabaseManager(self.POSTGRES_URL)
        self.embedding_service = OllamaEmbeddingService()
        
        logger.info("🚀 [OLLAMA_RAG_SERVICE] Ollama RAG Service initialized")
    
    def extract_document_code(self, document_title: str) -> str:
        """
        Извлекает код документа из названия (ГОСТ, СП, СНиП и т.д.)
        """
        try:
            patterns = [
                r'ГОСТ\s+[\d\.-]+', r'СП\s+[\d\.-]+', r'СНиП\s+[\d\.-]+',
                r'ТР\s+ТС\s+[\d\.-]+', r'СТО\s+[\d\.-]+', r'РД\s+[\d\.-]+',
            ]
            for pattern in patterns:
                match = re.search(pattern, document_title, re.IGNORECASE)
                if match:
                    return match.group(0).strip()
            return ""
        except Exception as e:
            logger.warning(f"⚠️ [CODE_EXTRACTION] Error extracting document code: {e}")
            return ""
    
    def index_document_chunks(self, document_id: int, chunks: List[Dict[str, Any]]) -> bool:
        """Индексация чанков документа в Qdrant"""
        try:
            logger.info(f"📝 [INDEXING] Starting indexing for document {document_id} with {len(chunks)} chunks")
            
            points = []
            
            for chunk in chunks:
                try:
                    # Создаем эмбеддинг для чанка
                    content = chunk.get('content', '')
                    if not content.strip():
                        continue
                    
                    embedding = self.embedding_service.create_embedding(content)
                    
                    # Генерируем числовой ID для Qdrant
                    qdrant_id = hash(f"{document_id}_{chunk['chunk_id']}") % (2**63 - 1)
                    if qdrant_id < 0:
                        qdrant_id = abs(qdrant_id)
                    
                    # Извлекаем код документа
                    document_title = chunk.get('document_title', '')
                    code = self.extract_document_code(document_title)
                    
                    # Создаем точку для Qdrant
                    point = PointStruct(
                        id=qdrant_id,
                        vector=embedding,
                        payload={
                            'document_id': document_id,
                            'chunk_id': chunk['chunk_id'],
                            'code': code,
                            'title': document_title,
                            'section_title': chunk.get('section_title', ''),
                            'content': content,
                            'chunk_type': chunk.get('chunk_type', ''),
                            'page': chunk.get('page', 1),
                            'section': chunk.get('section', ''),
                            'metadata': chunk.get('metadata', {})
                        }
                    )
                    points.append(point)
                    
                except Exception as e:
                    logger.error(f"❌ [INDEXING] Error processing chunk {chunk.get('chunk_id', 'unknown')}: {e}")
                    continue
            
            if points:
                # Добавляем точки в Qdrant
                self.qdrant_client.upsert(
                    collection_name=self.VECTOR_COLLECTION,
                    points=points
                )
                logger.info(f"✅ [INDEXING] Successfully indexed {len(points)} chunks for document {document_id}")
                return True
            else:
                logger.warning(f"⚠️ [INDEXING] No valid chunks to index for document {document_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ [INDEXING] Error indexing document {document_id}: {e}")
            return False
    
    def hybrid_search(self, query: str, k: int = 8, document_filter: Optional[str] = None, 
                     chapter_filter: Optional[str] = None, chunk_type_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Гибридный поиск по нормативным документам"""
        try:
            logger.info(f"🔍 [HYBRID_SEARCH] Performing hybrid search for query: '{query}' with k={k}")
            
            # Создаем эмбеддинг для запроса
            query_embedding = self.embedding_service.create_embedding(query)
            
            # Формируем фильтры для поиска
            must_conditions = []
            
            if document_filter and document_filter != 'all':
                must_conditions.append({
                    "key": "code",
                    "match": {"value": document_filter}
                })
            
            if chapter_filter:
                must_conditions.append({
                    "key": "section",
                    "match": {"value": chapter_filter}
                })
            
            if chunk_type_filter:
                must_conditions.append({
                    "key": "chunk_type",
                    "match": {"value": chunk_type_filter}
                })
            
            # Выполняем поиск в Qdrant
            search_result = self.qdrant_client.search(
                collection_name=self.VECTOR_COLLECTION,
                query_vector=query_embedding,
                query_filter={"must": must_conditions} if must_conditions else None,
                limit=k,
                with_payload=True,
                with_vectors=False
            )
            
            # Формируем результаты
            results = []
            for point in search_result:
                result = {
                    'id': point.id,
                    'score': point.score,
                    'document_id': point.payload.get('document_id'),
                    'chunk_id': point.payload.get('chunk_id'),
                    'code': point.payload.get('code'),
                    'document_title': point.payload.get('title'),
                    'section_title': point.payload.get('section_title'),
                    'content': point.payload.get('content'),
                    'chunk_type': point.payload.get('chunk_type'),
                    'page': point.payload.get('page'),
                    'section': point.payload.get('section'),
                    'metadata': point.payload.get('metadata', {})
                }
                results.append(result)
            
            logger.info(f"✅ [HYBRID_SEARCH] Found {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"❌ [HYBRID_SEARCH] Error during hybrid search: {e}")
            raise e
    
    def get_ntd_consultation(self, message: str, user_id: str, history: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Получение консультации по НТД"""
        try:
            logger.info(f"💬 [NTD_CONSULTATION] Processing consultation request: '{message[:100]}...'")
            
            # Выполняем поиск по запросу
            search_results = self.hybrid_search(message, k=5)
            
            if not search_results:
                return {
                    "status": "success",
                    "response": "К сожалению, я не нашел релевантной информации в базе нормативных документов. Попробуйте переформулировать ваш вопрос или обратитесь к актуальным нормативным документам.",
                    "sources": [],
                    "confidence": 0.0,
                    "documents_used": 0,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Формируем ответ на основе найденных документов
            top_result = search_results[0]
            confidence = min(top_result['score'], 1.0) if top_result['score'] > 0 else 0.0
            
            # Формируем источники
            sources = []
            for result in search_results[:3]:  # Топ-3 результата
                source = {
                    'document_code': result['code'],
                    'document_title': result['document_title'],
                    'section': result['section'],
                    'page': result['page'],
                    'content_preview': result['content'][:200] + "..." if len(result['content']) > 200 else result['content'],
                    'relevance_score': result['score']
                }
                sources.append(source)
            
            # Формируем ответ
            response = f"На основе найденных документов, вот ответ на ваш вопрос:\n\n"
            response += f"**{top_result['document_title']}**\n"
            response += f"Раздел: {top_result['section']}\n\n"
            response += f"{top_result['content']}\n\n"
            response += f"Для получения дополнительной информации обратитесь к полному тексту документа."
            
            return {
                "status": "success",
                "response": response,
                "sources": sources,
                "confidence": confidence,
                "documents_used": len(search_results),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ [NTD_CONSULTATION] Error during consultation: {e}")
            return {
                "status": "error",
                "response": f"Произошла ошибка при обработке вашего запроса: {str(e)}",
                "sources": [],
                "confidence": 0.0,
                "documents_used": 0,
                "timestamp": datetime.now().isoformat()
            }
    
    def get_documents(self) -> List[Dict[str, Any]]:
        """Получение списка документов из базы данных"""
        try:
            with self.db_manager.get_cursor() as cursor:
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
            with self.db_manager.get_cursor() as cursor:
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
            with self.db_manager.get_cursor() as cursor:
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
                        'section': chunk['section']
                    })
                
                return result
                
        except Exception as e:
            logger.error(f"❌ [GET_DOCUMENT_CHUNKS] Error getting chunks for document {document_id}: {e}")
            return []
    
    def delete_document_indexes(self, document_id: int) -> bool:
        """Удаление индексов документа из Qdrant"""
        try:
            logger.info(f"🗑️ [DELETE_INDEXES] Deleting indexes for document {document_id}")
            
            # Получаем все чанки документа
            chunks = self.get_document_chunks(document_id)
            if not chunks:
                logger.warning(f"⚠️ [DELETE_INDEXES] No chunks found for document {document_id}")
                return True
            
            # Формируем список ID для удаления из Qdrant
            point_ids = []
            for chunk in chunks:
                qdrant_id = hash(f"{document_id}_{chunk['chunk_id']}") % (2**63 - 1)
                if qdrant_id < 0:
                    qdrant_id = abs(qdrant_id)
                point_ids.append(qdrant_id)
            
            # Удаляем точки из Qdrant
            if point_ids:
                self.qdrant_client.delete(
                    collection_name=self.VECTOR_COLLECTION,
                    points_selector=point_ids
                )
                logger.info(f"✅ [DELETE_INDEXES] Deleted {len(point_ids)} points from Qdrant for document {document_id}")
            
            # Удаляем чанки из PostgreSQL
            with self.db_manager.get_cursor() as cursor:
                cursor.execute("DELETE FROM normative_chunks WHERE document_id = %s", (document_id,))
                deleted_chunks = cursor.rowcount
                logger.info(f"✅ [DELETE_INDEXES] Deleted {deleted_chunks} chunks from PostgreSQL for document {document_id}")
                # Фиксируем транзакцию
                cursor.connection.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ [DELETE_INDEXES] Error deleting indexes for document {document_id}: {e}")
            return False
    
    def delete_document(self, document_id: int) -> bool:
        """Полное удаление документа и всех связанных данных"""
        try:
            logger.info(f"🗑️ [DELETE_DOCUMENT] Deleting document {document_id}")
            
            # 1. Удаляем индексы из Qdrant
            indexes_deleted = self.delete_document_indexes(document_id)
            
            # 2. Удаляем извлеченные элементы и сам документ в одной транзакции
            with self.db_manager.get_cursor() as cursor:
                # Удаляем извлеченные элементы
                cursor.execute("DELETE FROM extracted_elements WHERE uploaded_document_id = %s", (document_id,))
                deleted_elements = cursor.rowcount
                logger.info(f"✅ [DELETE_DOCUMENT] Deleted {deleted_elements} extracted elements for document {document_id}")
                
                # Удаляем сам документ
                cursor.execute("DELETE FROM uploaded_documents WHERE id = %s", (document_id,))
                deleted_documents = cursor.rowcount
                logger.info(f"✅ [DELETE_DOCUMENT] Deleted {deleted_documents} documents for document {document_id}")
                
                # Фиксируем транзакцию
                cursor.connection.commit()
            
            if deleted_documents == 0:
                logger.warning(f"⚠️ [DELETE_DOCUMENT] Document {document_id} not found")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ [DELETE_DOCUMENT] Error deleting document {document_id}: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Получение статистики сервиса"""
        try:
            # Статистика Qdrant через прямой HTTP запрос
            import requests
            qdrant_response = requests.get(f"{self.QDRANT_URL}/collections/{self.VECTOR_COLLECTION}", timeout=5)
            qdrant_stats = {
                'collection_name': self.VECTOR_COLLECTION,
                'vectors_count': 0,
                'indexed_vectors': 0,
                'status': 'unknown'
            }
            
            if qdrant_response.status_code == 200:
                qdrant_data = qdrant_response.json()
                result = qdrant_data.get('result', {})
                qdrant_stats.update({
                    'vectors_count': result.get('points_count', 0),
                    'indexed_vectors': result.get('indexed_vectors_count', 0),
                    'status': result.get('status', 'unknown')
                })
            
            # Статистика PostgreSQL
            with self.db_manager.get_cursor() as cursor:
                cursor.execute("SELECT COUNT(*) as total_documents FROM uploaded_documents")
                total_docs = cursor.fetchone()['total_documents']
                
                cursor.execute("SELECT COUNT(*) as total_chunks FROM normative_chunks")
                total_chunks = cursor.fetchone()['total_chunks']
                
                cursor.execute("SELECT COUNT(*) as pending_docs FROM uploaded_documents WHERE processing_status = 'pending'")
                pending_docs = cursor.fetchone()['pending_docs']
                
                # Подсчитываем общее количество токенов
                cursor.execute("SELECT COALESCE(SUM(token_count), 0) as total_tokens FROM uploaded_documents")
                total_tokens = cursor.fetchone()['total_tokens']
            
            db_stats = {
                'total_documents': total_docs,
                'total_chunks': total_chunks,
                'pending_documents': pending_docs,
                'total_tokens': total_tokens
            }
            
            return {
                'qdrant': qdrant_stats,
                'postgresql': db_stats,
                'embedding_model': 'bge-m3 (Ollama)',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ [GET_STATS] Error getting stats: {e}")
            # Возвращаем базовую статистику даже при ошибке
            try:
                with self.db_manager.get_cursor() as cursor:
                    cursor.execute("SELECT COUNT(*) as total_documents FROM uploaded_documents")
                    total_docs = cursor.fetchone()['total_documents']
                    
                    cursor.execute("SELECT COUNT(*) as total_chunks FROM normative_chunks")
                    total_chunks = cursor.fetchone()['total_chunks']
                    
                    cursor.execute("SELECT COALESCE(SUM(token_count), 0) as total_tokens FROM uploaded_documents")
                    total_tokens = cursor.fetchone()['total_tokens']
                
                return {
                    'qdrant': {
                        'collection_name': self.VECTOR_COLLECTION,
                        'vectors_count': 0,  # Не можем получить из Qdrant
                        'indexed_vectors': 0,
                        'status': 'error'
                    },
                    'postgresql': {
                        'total_documents': total_docs,
                        'total_chunks': total_chunks,
                        'pending_documents': 0,
                        'total_tokens': total_tokens
                    },
                    'embedding_model': 'bge-m3 (Ollama)',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
            except Exception as fallback_error:
                logger.error(f"❌ [GET_STATS] Fallback error: {fallback_error}")
                return {
                    'error': f"Primary error: {str(e)}, Fallback error: {str(fallback_error)}",
                    'timestamp': datetime.now().isoformat()
                }

    def save_document_to_db(self, document_id: int, filename: str, original_filename: str, 
                           file_type: str, file_size: int, document_hash: str, 
                           category: str, document_type: str) -> int:
        """Сохранение документа в базу данных"""
        try:
            with self.db_manager.get_cursor() as cursor:
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
            with self.db_manager.get_cursor() as cursor:
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

    async def process_document_async(self, document_id: int, content: bytes, filename: str) -> bool:
        """Асинхронная обработка документа"""
        try:
            logger.info(f"🔄 [PROCESS_ASYNC] Starting processing for document {document_id}")
            
            # Извлекаем текст из документа
            text_content = await self.extract_text_from_document(content, filename)
            if not text_content:
                logger.error(f"❌ [PROCESS_ASYNC] Failed to extract text from document {document_id}")
                return False
            
            # Разбиваем на чанки
            chunks = self.create_chunks(text_content, document_id, filename)
            if not chunks:
                logger.error(f"❌ [PROCESS_ASYNC] Failed to create chunks for document {document_id}")
                return False
            
            # Создаем эмбеддинги и сохраняем в Qdrant
            success = await self.index_chunks_async(chunks, document_id)
            if not success:
                logger.error(f"❌ [PROCESS_ASYNC] Failed to index chunks for document {document_id}")
                return False
            
            # Обновляем количество токенов
            token_count = len(text_content.split())
            with self.db_manager.get_cursor() as cursor:
                cursor.execute("""
                    UPDATE uploaded_documents 
                    SET token_count = %s
                    WHERE id = %s
                """, (token_count, document_id))
                cursor.connection.commit()
            
            logger.info(f"✅ [PROCESS_ASYNC] Document {document_id} processed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ [PROCESS_ASYNC] Error processing document {document_id}: {e}")
            return False

    async def extract_text_from_document(self, content: bytes, filename: str) -> str:
        """Извлечение текста из документа"""
        try:
            import tempfile
            import os
            
            # Создаем временный файл
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{filename.split('.')[-1]}") as temp_file:
                temp_file.write(content)
                temp_file_path = temp_file.name
            
            try:
                if filename.lower().endswith('.pdf'):
                    return await self.extract_text_from_pdf(temp_file_path)
                elif filename.lower().endswith('.docx'):
                    return await self.extract_text_from_docx(temp_file_path)
                elif filename.lower().endswith('.txt'):
                    return content.decode('utf-8', errors='ignore')
                else:
                    logger.error(f"❌ [EXTRACT_TEXT] Unsupported file type: {filename}")
                    return ""
            finally:
                # Удаляем временный файл
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except Exception as e:
            logger.error(f"❌ [EXTRACT_TEXT] Error extracting text: {e}")
            return ""

    async def extract_text_from_pdf(self, file_path: str) -> str:
        """Извлечение текста из PDF"""
        try:
            import PyPDF2
            
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text() + "\n"
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"❌ [EXTRACT_PDF] Error extracting text from PDF: {e}")
            return ""

    async def extract_text_from_docx(self, file_path: str) -> str:
        """Извлечение текста из DOCX"""
        try:
            from docx import Document
            
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"❌ [EXTRACT_DOCX] Error extracting text from DOCX: {e}")
            return ""

    def create_chunks(self, text: str, document_id: int, filename: str) -> List[Dict[str, Any]]:
        """Создание чанков из текста"""
        try:
            chunks = []
            sentences = text.split('.')
            chunk_size = 1000  # Примерный размер чанка в символах
            current_chunk = ""
            chunk_id = 1
            
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                
                if len(current_chunk) + len(sentence) > chunk_size and current_chunk:
                    # Сохраняем текущий чанк
                    chunks.append({
                        'chunk_id': f"doc_{document_id}_chunk_{chunk_id}",
                        'document_id': document_id,
                        'document_title': filename,
                        'content': current_chunk.strip(),
                        'chunk_type': 'paragraph'
                    })
                    current_chunk = sentence
                    chunk_id += 1
                else:
                    current_chunk += sentence + ". "
            
            # Добавляем последний чанк
            if current_chunk.strip():
                chunks.append({
                    'chunk_id': f"doc_{document_id}_chunk_{chunk_id}",
                    'document_id': document_id,
                    'document_title': filename,
                    'content': current_chunk.strip(),
                    'chunk_type': 'paragraph'
                })
            
            logger.info(f"✅ [CREATE_CHUNKS] Created {len(chunks)} chunks for document {document_id}")
            return chunks
            
        except Exception as e:
            logger.error(f"❌ [CREATE_CHUNKS] Error creating chunks: {e}")
            return []

    async def index_chunks_async(self, chunks: List[Dict[str, Any]], document_id: int) -> bool:
        """Асинхронная индексация чанков"""
        try:
            # Сохраняем чанки в PostgreSQL
            with self.db_manager.get_cursor() as cursor:
                for chunk in chunks:
                    cursor.execute("""
                        INSERT INTO normative_chunks 
                        (chunk_id, clause_id, document_id, document_title, chunk_type, content)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        chunk['chunk_id'],
                        chunk['chunk_id'],  # Используем chunk_id как clause_id
                        chunk['document_id'],
                        chunk['document_title'],
                        chunk['chunk_type'],
                        chunk['content']
                    ))
                cursor.connection.commit()
            
            # Создаем эмбеддинги и сохраняем в Qdrant
            for chunk in chunks:
                # Создаем эмбеддинг
                embedding = self.embedding_service.create_embedding(chunk['content'])
                if embedding is None:
                    logger.warning(f"⚠️ [INDEX_CHUNKS] Failed to create embedding for chunk {chunk['chunk_id']}")
                    continue
                
                # Сохраняем в Qdrant
                point_id = hash(chunk['chunk_id']) % (2**63 - 1)
                if point_id < 0:
                    point_id = abs(point_id)
                
                # Преобразуем эмбеддинг в список
                if hasattr(embedding, 'tolist'):
                    vector = embedding.tolist()
                else:
                    vector = list(embedding)
                
                point = PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={
                        'chunk_id': chunk['chunk_id'],
                        'document_id': chunk['document_id'],
                        'document_title': chunk['document_title'],
                        'content': chunk['content'],
                        'chunk_type': chunk['chunk_type']
                    }
                )
                
                self.qdrant_client.upsert(
                    collection_name=self.VECTOR_COLLECTION,
                    points=[point]
                )
            
            logger.info(f"✅ [INDEX_CHUNKS] Indexed {len(chunks)} chunks for document {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ [INDEX_CHUNKS] Error indexing chunks: {e}")
            return False
