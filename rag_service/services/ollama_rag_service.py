import logging
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import re
import requests
import json
import os
from .qdrant_service import QdrantService

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
model_logger = logging.getLogger("model")

# Получаем URL Ollama из переменной окружения
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434")

class OllamaEmbeddingService:
    """Сервис для работы с эмбеддингами через Ollama BGE-M3"""
    
    def __init__(self, ollama_url: str = None):
        self.ollama_url = ollama_url or OLLAMA_URL
        self.model_name = "bge-m3"
        logger.info(f"🤖 [OLLAMA_EMBEDDING] Initialized with {self.model_name} at {self.ollama_url}")
    
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
        self.qdrant_service = QdrantService(self.QDRANT_URL, self.VECTOR_COLLECTION, self.VECTOR_SIZE)
        self.db_manager = DatabaseManager(self.POSTGRES_URL)
        self.embedding_service = OllamaEmbeddingService()
        
        logger.info("🚀 [OLLAMA_RAG_SERVICE] Ollama RAG Service initialized")
    

    
    def extract_document_code(self, document_title: str) -> str:
        """
        Извлекает код документа из названия (ГОСТ, СП, СНиП и т.д.)
        """
        try:
            # Убираем расширение файла
            title_without_ext = re.sub(r'\.(pdf|txt|doc|docx)$', '', document_title, flags=re.IGNORECASE)
            
            patterns = [
                r'ГОСТ\s+[\d\.-]+', 
                r'СП\s+[\d\.-]+', 
                r'СНиП\s+[\d\.-]+',
                r'ТР\s+ТС\s+[\d\.-]+', 
                r'СТО\s+[\d\.-]+', 
                r'РД\s+[\d\.-]+',
                r'ТУ\s+[\d\.-]+',
                r'ПБ\s+[\d\.-]+',
                r'НПБ\s+[\d\.-]+',
                r'СПб\s+[\d\.-]+',
                r'МГСН\s+[\d\.-]+'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, title_without_ext, re.IGNORECASE)
                if match:
                    code = match.group(0).strip()
                    logger.info(f"🔍 [CODE_EXTRACTION] Extracted code '{code}' from title '{document_title}'")
                    return code
            
            logger.warning(f"⚠️ [CODE_EXTRACTION] No code pattern found in title: '{document_title}'")
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
                    
                    logger.info(f"🔍 [INDEXING] Document title: '{document_title}', extracted code: '{code}'")
                    
                    # Создаем точку для Qdrant
                    point = self.qdrant_service.create_point(
                        point_id=qdrant_id,
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
                self.qdrant_service.upsert_points_batch(points)
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
            search_result = self.qdrant_service.search_similar(
                query_vector=query_embedding,
                limit=k,
                filters={"must": must_conditions} if must_conditions else None
            )
            
            # Формируем результаты
            results = []
            for point in search_result:
                result = {
                    'id': point['id'],
                    'score': point['score'],
                    'document_id': point['payload'].get('document_id'),
                    'chunk_id': point['payload'].get('chunk_id'),
                    'code': point['payload'].get('code'),
                    'document_title': point['payload'].get('title'),
                    'section_title': point['payload'].get('section_title'),
                    'content': point['payload'].get('content'),
                    'chunk_type': point['payload'].get('chunk_type'),
                    'page': point['payload'].get('page'),
                    'section': point['payload'].get('section'),
                    'metadata': point['payload'].get('metadata', {})
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
            
            # Извлекаем код документа из запроса
            document_code = self.extract_document_code_from_query(message)
            logger.info(f"🔍 [NTD_CONSULTATION] Extracted document code: {document_code}")
            
            # Выполняем поиск по запросу
            search_results = self.hybrid_search(message, k=10)
            
            if not search_results:
                return {
                    "status": "success",
                    "response": "К сожалению, я не нашел релевантной информации в базе нормативных документов. Попробуйте переформулировать ваш вопрос или обратитесь к актуальным нормативным документам.",
                    "sources": [],
                    "confidence": 0.0,
                    "documents_used": 0,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Если запрашивается конкретный документ, проверяем его наличие
            if document_code:
                # Ищем точное соответствие по коду документа
                exact_match = None
                for result in search_results:
                    if result.get('code') == document_code:
                        exact_match = result
                        break
                
                if exact_match:
                    logger.info(f"✅ [NTD_CONSULTATION] Found exact match for {document_code}")
                    top_result = exact_match
                    confidence = 1.0  # Высокая уверенность для точного совпадения
                else:
                    logger.warning(f"⚠️ [NTD_CONSULTATION] Document {document_code} not found in system")
                    # Возвращаем предупреждение о том, что запрашиваемый документ отсутствует
                    return {
                        "status": "warning",
                        "response": f"⚠️ **Внимание!** Запрашиваемый документ **{document_code}** отсутствует в системе.\n\n"
                                  f"Вот наиболее релевантная информация из доступных документов:\n\n"
                                  f"**{search_results[0]['document_title']}**\n"
                                  f"Раздел: {search_results[0]['section']}\n\n"
                                  f"{search_results[0]['content'][:500]}...\n\n"
                                  f"**Рекомендация:** Загрузите документ {document_code} в систему для получения точной консультации.",
                        "sources": [{
                            'document_code': search_results[0]['code'],
                            'document_title': search_results[0]['document_title'],
                            'section': search_results[0]['section'],
                            'page': search_results[0]['page'],
                            'content_preview': search_results[0]['content'][:200] + "..." if len(search_results[0]['content']) > 200 else search_results[0]['content'],
                            'relevance_score': search_results[0]['score'],
                            'note': 'Документ найден по семантическому поиску, но не является запрашиваемым'
                        }],
                        "confidence": 0.5,
                        "documents_used": 1,
                        "missing_document": document_code,
                        "timestamp": datetime.now().isoformat()
                    }
            else:
                # Если код документа не указан, используем обычный поиск
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
    
    def extract_document_code_from_query(self, query: str) -> Optional[str]:
        """Извлекает код документа из запроса пользователя"""
        try:
            # Паттерны для поиска кодов документов
            patterns = [
                r'СП\s+(\d+\.\d+\.\d+)',  # СП 22.13330.2016
                r'СНиП\s+(\d+\.\d+\.\d+)',  # СНиП 2.01.01-82
                r'ГОСТ\s+(\d+\.\d+\.\d+)',  # ГОСТ 27751-2014
                r'ТУ\s+(\d+\.\d+\.\d+)',   # ТУ 3812-001-12345678-2016
                r'ПБ\s+(\d+\.\d+\.\d+)',   # ПБ 03-428-02
                r'НПБ\s+(\d+\.\d+\.\d+)',  # НПБ 5-2000
                r'СПб\s+(\d+\.\d+\.\d+)',  # СПб 70.13330.2012
                r'МГСН\s+(\d+\.\d+\.\d+)'  # МГСН 4.19-2005
            ]
            
            for pattern in patterns:
                match = re.search(pattern, query, re.IGNORECASE)
                if match:
                    # Восстанавливаем полный код документа
                    if 'СП' in pattern:
                        return f"СП {match.group(1)}"
                    elif 'СНиП' in pattern:
                        return f"СНиП {match.group(1)}"
                    elif 'ГОСТ' in pattern:
                        return f"ГОСТ {match.group(1)}"
                    elif 'ТУ' in pattern:
                        return f"ТУ {match.group(1)}"
                    elif 'ПБ' in pattern:
                        return f"ПБ {match.group(1)}"
                    elif 'НПБ' in pattern:
                        return f"НПБ {match.group(1)}"
                    elif 'СПб' in pattern:
                        return f"СПб {match.group(1)}"
                    elif 'МГСН' in pattern:
                        return f"МГСН {match.group(1)}"
            
            return None
            
        except Exception as e:
            logger.error(f"❌ [DOCUMENT_CODE_EXTRACTION] Error extracting document code: {e}")
            return None
    
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
                # Получаем название документа
                cursor.execute("""
                    SELECT original_filename 
                    FROM uploaded_documents 
                    WHERE id = %s
                """, (document_id,))
                document_result = cursor.fetchone()
                document_title = document_result['original_filename'] if document_result else f"Document_{document_id}"
                
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
                # Удаляем точки из Qdrant
                self.qdrant_service.delete_points_by_document(document_id)
                logger.info(f"✅ [DELETE_INDEXES] Deleted points from Qdrant for document {document_id}")
            
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
            # Статистика Qdrant через сервис
            qdrant_info = self.qdrant_service.get_collection_info()
            qdrant_stats = {
                'collection_name': self.VECTOR_COLLECTION,
                'vectors_count': qdrant_info.get('points_count', 0),
                'indexed_vectors': qdrant_info.get('points_count', 0),
                'status': 'ok' if qdrant_info else 'unknown'
            }
            
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
        """Создание чанков из текста документа с правильной нумерацией страниц"""
        try:
            logger.info(f"📝 [CREATE_CHUNKS] Creating chunks for document {document_id}")
            
            # Разбиваем текст на страницы по маркерам "Страница X из Y"
            page_pattern = r'Страница\s+(\d+)\s+из\s+(\d+)'
            page_matches = list(re.finditer(page_pattern, text))
            
            chunks = []
            chunk_id = 1
            
            if page_matches:
                # Если найдены маркеры страниц, разбиваем по ним
                logger.info(f"📄 [CREATE_CHUNKS] Found {len(page_matches)} page markers in document")
                
                for i, match in enumerate(page_matches):
                    page_num = int(match.group(1))
                    start_pos = match.end()
                    
                    # Определяем конец страницы (начало следующей или конец текста)
                    if i + 1 < len(page_matches):
                        end_pos = page_matches[i + 1].start()
                    else:
                        end_pos = len(text)
                    
                    # Извлекаем текст страницы
                    page_text = text[start_pos:end_pos].strip()
                    
                    if page_text:
                        # Разбиваем страницу на чанки
                        page_chunks = self._split_page_into_chunks(page_text, chunk_size=1000)
                        
                        for chunk_text in page_chunks:
                            chunks.append({
                                'chunk_id': f"doc_{document_id}_page_{page_num}_chunk_{chunk_id}",
                                'document_id': document_id,
                                'document_title': filename,
                                'content': chunk_text.strip(),
                                'chunk_type': 'paragraph',
                                'page': page_num
                            })
                            chunk_id += 1
            else:
                # Если маркеры страниц не найдены, разбиваем весь текст на чанки
                logger.info(f"📄 [CREATE_CHUNKS] No page markers found, treating as single page document")
                page_chunks = self._split_page_into_chunks(text, chunk_size=1000)
                
                for chunk_text in page_chunks:
                    chunks.append({
                        'chunk_id': f"doc_{document_id}_page_1_chunk_{chunk_id}",
                        'document_id': document_id,
                        'document_title': filename,
                        'content': chunk_text.strip(),
                        'chunk_type': 'paragraph',
                        'page': 1
                    })
                    chunk_id += 1
            
            logger.info(f"✅ [CREATE_CHUNKS] Created {len(chunks)} chunks for document {document_id}")
            return chunks
            
        except Exception as e:
            logger.error(f"❌ [CREATE_CHUNKS] Error creating chunks: {e}")
            return []
    
    def _split_page_into_chunks(self, text: str, chunk_size: int = 1000) -> List[str]:
        """Разбиение текста страницы на гранулярные чанки с улучшенной логикой"""
        try:
            # Импортируем конфигурацию
            from config.chunking_config import get_chunking_config, validate_chunking_config
            
            # Получаем конфигурацию чанкования
            config = get_chunking_config('default')
            
            # Валидируем конфигурацию
            if not validate_chunking_config(config):
                logger.warning("⚠️ [CHUNKING] Invalid chunking config, using fallback")
                return self._simple_split_into_chunks(text, chunk_size)
            
            # Параметры гранулярного чанкования из конфигурации
            target_tokens = config['target_tokens']
            min_tokens = config['min_tokens']
            max_tokens = config['max_tokens']
            overlap_ratio = config['overlap_ratio']
            
            logger.info(f"📝 [CHUNKING] Using config: target={target_tokens}, min={min_tokens}, max={max_tokens}, overlap={overlap_ratio}")
            logger.info(f"📝 [CHUNKING] Input text length: {len(text)} characters")
            
            # Разбиваем текст на предложения
            sentences = self._split_into_sentences(text, config)
            logger.info(f"📝 [CHUNKING] Split into {len(sentences)} sentences")
            
            if not sentences:
                logger.warning("⚠️ [CHUNKING] No sentences found, using fallback")
                return self._simple_split_into_chunks(text, chunk_size)
            
            chunks = []
            current_chunk = []
            current_tokens = 0
            
            logger.info(f"📝 [CHUNKING] Starting chunk creation process...")
            
            # Обрабатываем каждое предложение
            for i, sentence in enumerate(sentences):
                sentence_tokens = self._estimate_tokens(sentence, config)
                logger.info(f"📝 [CHUNKING] Sentence {i+1}: {sentence_tokens} tokens, length: {len(sentence)}")
                
                # Проверяем, нужно ли начать новый чанк
                if current_tokens + sentence_tokens > max_tokens and current_chunk:
                    logger.info(f"📝 [CHUNKING] Max tokens exceeded ({current_tokens + sentence_tokens} > {max_tokens}), creating chunk")
                    # Создаем чанк
                    chunk_text = ' '.join(current_chunk)
                    chunks.append(chunk_text.strip())
                    logger.info(f"📝 [CHUNKING] Created chunk {len(chunks)}: {len(chunk_text)} chars, {current_tokens} tokens")
                    
                    # Начинаем новый чанк с перекрытием
                    overlap_sentences = self._get_overlap_sentences(current_chunk, overlap_ratio, config)
                    current_chunk = overlap_sentences
                    current_tokens = sum(self._estimate_tokens(s, config) for s in overlap_sentences)
                    logger.info(f"📝 [CHUNKING] Started new chunk with {len(overlap_sentences)} overlap sentences, {current_tokens} tokens")
                
                # Добавляем предложение к текущему чанку
                current_chunk.append(sentence)
                current_tokens += sentence_tokens
                logger.info(f"📝 [CHUNKING] Added sentence to current chunk: {current_tokens} tokens total")
                
                # Проверяем, достигли ли целевого размера
                if current_tokens >= target_tokens and current_tokens >= min_tokens:
                    logger.info(f"📝 [CHUNKING] Target size reached ({current_tokens} >= {target_tokens}), creating chunk")
                    # Создаем чанк
                    chunk_text = ' '.join(current_chunk)
                    chunks.append(chunk_text.strip())
                    logger.info(f"📝 [CHUNKING] Created chunk {len(chunks)}: {len(chunk_text)} chars, {current_tokens} tokens")
                    
                    # Начинаем новый чанк с перекрытием
                    overlap_sentences = self._get_overlap_sentences(current_chunk, overlap_ratio, config)
                    current_chunk = overlap_sentences
                    current_tokens = sum(self._estimate_tokens(s, config) for s in overlap_sentences)
                    logger.info(f"📝 [CHUNKING] Started new chunk with {len(overlap_sentences)} overlap sentences, {current_tokens} tokens")
            
            # Добавляем последний чанк, если он не пустой
            if current_chunk and current_tokens >= min_tokens:
                logger.info(f"📝 [CHUNKING] Adding final chunk: {current_tokens} tokens")
                chunk_text = ' '.join(current_chunk)
                chunks.append(chunk_text.strip())
                logger.info(f"📝 [CHUNKING] Created final chunk {len(chunks)}: {len(chunk_text)} chars, {current_tokens} tokens")
            elif current_chunk:
                logger.info(f"📝 [CHUNKING] Final chunk too small ({current_tokens} < {min_tokens}), merging with previous")
                if chunks:
                    # Объединяем с последним чанком
                    last_chunk = chunks[-1]
                    merged_chunk = last_chunk + ' ' + ' '.join(current_chunk)
                    chunks[-1] = merged_chunk
                    logger.info(f"📝 [CHUNKING] Merged final chunk with previous: {len(merged_chunk)} chars")
                else:
                    # Если нет предыдущих чанков, создаем один
                    chunk_text = ' '.join(current_chunk)
                    chunks.append(chunk_text.strip())
                    logger.info(f"📝 [CHUNKING] Created single chunk: {len(chunk_text)} chars, {current_tokens} tokens")
            
            # Проверяем, что у нас есть чанки перед применением логики склейки
            if not chunks:
                logger.warning("⚠️ [CHUNKING] No chunks created, using fallback")
                return self._simple_split_into_chunks(text, chunk_size)
            
            # Применяем логику склейки с заголовками если включена
            if config.get('merge_enabled', True):
                logger.info(f"📝 [CHUNKING] Applying header merging logic to {len(chunks)} chunks...")
                chunks = self._merge_chunks_with_headers(chunks, config)
                logger.info(f"📝 [CHUNKING] After merging: {len(chunks)} chunks")
            
            logger.info(f"✅ [CHUNKING] Created {len(chunks)} granular chunks")
            return chunks
            
        except Exception as e:
            logger.error(f"❌ [GRANULAR_CHUNKS] Error creating granular chunks: {e}")
            import traceback
            logger.error(f"❌ [GRANULAR_CHUNKS] Traceback: {traceback.format_exc()}")
            # Fallback к простому разбиению
            return self._simple_split_into_chunks(text, chunk_size)

    def _split_into_sentences(self, text: str, config: dict) -> List[str]:
        """Разбиение текста на предложения с учетом нормативных документов"""
        try:
            # Получаем паттерны из конфигурации
            sentence_patterns = config.get('sentence_patterns', [
                r'[.!?]+(?=\s+[А-ЯЁ\d])',  # Обычные предложения
                r'[.!?]+(?=\s+\d+\.)',      # Перед номерами пунктов
                r'[.!?]+(?=\s+[А-ЯЁ]\s)',  # Перед заголовками
                r'[.!?]+(?=\s*$)'           # В конце текста
            ])
            
            # Объединяем все паттерны
            combined_pattern = '|'.join(sentence_patterns)
            
            # Разбиваем текст
            sentences = re.split(combined_pattern, text)
            
            # Очищаем и фильтруем предложения
            min_length = config.get('min_sentence_length', 10)
            cleaned_sentences = []
            for sentence in sentences:
                sentence = sentence.strip()
                if sentence and len(sentence) > min_length:
                    cleaned_sentences.append(sentence)
            
            return cleaned_sentences
            
        except Exception as e:
            logger.error(f"❌ [SENTENCE_SPLIT] Error splitting into sentences: {e}")
            # Fallback: простое разбиение по точкам
            return [s.strip() for s in text.split('.') if s.strip()]
    
    def _estimate_tokens(self, text: str, config: dict) -> int:
        """Оценка количества токенов в тексте"""
        try:
            # Получаем коэффициент из конфигурации
            tokens_per_char = config.get('tokens_per_char', 4)
            return max(1, len(text) // tokens_per_char)
        except Exception as e:
            logger.error(f"❌ [TOKEN_ESTIMATION] Error estimating tokens: {e}")
            return len(text) // 4
    
    def _get_overlap_sentences(self, sentences: List[str], overlap_ratio: float, config: dict) -> List[str]:
        """Получение предложений для перекрытия между чанками"""
        try:
            if not sentences:
                return []
            
            # Выбираем последние предложения для перекрытия
            min_overlap = config.get('min_overlap_sentences', 1)
            overlap_count = max(min_overlap, int(len(sentences) * overlap_ratio))
            return sentences[-overlap_count:]
            
        except Exception as e:
            logger.error(f"❌ [OVERLAP] Error getting overlap sentences: {e}")
            return sentences[-1:] if sentences else []
    
    def _merge_chunks_with_headers(self, chunks: List[str], config: dict) -> List[str]:
        """Склейка чанков с заголовками для предотвращения обрыва цитат"""
        try:
            if len(chunks) <= 1:
                return chunks
            
            merged_chunks = []
            current_chunk = chunks[0]
            
            for i in range(1, len(chunks)):
                next_chunk = chunks[i]
                
                # Проверяем, нужно ли объединить чанки
                should_merge = self._should_merge_chunks(current_chunk, next_chunk, config)
                
                if should_merge:
                    # Объединяем чанки
                    current_chunk = current_chunk + ' ' + next_chunk
                else:
                    # Добавляем текущий чанк и начинаем новый
                    merged_chunks.append(current_chunk)
                    current_chunk = next_chunk
            
            # Добавляем последний чанк
            merged_chunks.append(current_chunk)
            
            logger.info(f"📝 [MERGE_HEADERS] Merged {len(chunks)} chunks into {len(merged_chunks)} chunks")
            return merged_chunks
            
        except Exception as e:
            logger.error(f"❌ [MERGE_HEADERS] Error merging chunks: {e}")
            return chunks
    
    def _should_merge_chunks(self, chunk1: str, chunk2: str, config: dict) -> bool:
        """Определение необходимости объединения чанков"""
        try:
            # Проверяем размер объединенного чанка
            combined_tokens = self._estimate_tokens(chunk1, config) + self._estimate_tokens(chunk2, config)
            
            # Если объединенный чанк слишком большой, не объединяем
            max_merged = config.get('max_merged_tokens', 1200)
            if combined_tokens > max_merged:
                return False
            
            # Получаем паттерны заголовков из конфигурации
            header_patterns = config.get('header_patterns', ['глава', 'раздел', 'часть', 'пункт'])
            
            # Проверяем, заканчивается ли первый чанк заголовком
            if any(pattern in chunk1.lower() for pattern in header_patterns):
                return True
            
            # Проверяем, начинается ли второй чанк с продолжения предложения
            if chunk2 and not chunk2[0].isupper():
                return True
            
            # Проверяем, есть ли незавершенные конструкции
            unfinished_patterns = config.get('unfinished_patterns', {})
            
            # Проверяем кавычки
            quotes = unfinished_patterns.get('quotes', ['"', '«', '»'])
            if any(chunk1.count(q) % 2 != 0 for q in quotes):
                return True
            
            # Проверяем скобки
            brackets = unfinished_patterns.get('brackets', ['(', '[', '{'])
            if any(chunk1.count(b) != chunk1.count(self._get_closing_bracket(b)) for b in brackets):
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ [MERGE_LOGIC] Error in merge logic: {e}")
            return False
    
    def _get_closing_bracket(self, opening_bracket: str) -> str:
        """Получение закрывающей скобки для открывающей"""
        bracket_pairs = {
            '(': ')',
            '[': ']',
            '{': '}',
            '<': '>'
        }
        return bracket_pairs.get(opening_bracket, '')

    def _simple_split_into_chunks(self, text: str, chunk_size: int = 1000) -> List[str]:
        """Простое разбиение текста на чанки, используя регулярные выражения."""
        chunks = []
        sentences = re.split(r'[.!?]+', text)
        current_chunk = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            if len(current_chunk) + len(sentence) > chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                current_chunk += sentence + ". "
        
        # Добавляем последний чанк
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks

    async def index_chunks_async(self, chunks: List[Dict[str, Any]], document_id: int) -> bool:
        """Асинхронная индексация чанков"""
        try:
            # Сохраняем чанки в PostgreSQL
            with self.db_manager.get_cursor() as cursor:
                for chunk in chunks:
                    cursor.execute("""
                        INSERT INTO normative_chunks 
                        (chunk_id, clause_id, document_id, document_title, chunk_type, content, page_number)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        chunk['chunk_id'],
                        chunk['chunk_id'],  # Используем chunk_id как clause_id
                        chunk['document_id'],
                        chunk['document_title'],
                        chunk['chunk_type'],
                        chunk['content'],
                        chunk.get('page', 1)  # Добавляем page_number
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
                
                payload = {
                    'chunk_id': chunk['chunk_id'],
                    'document_id': chunk['document_id'],
                    'document_title': chunk['document_title'],
                    'content': chunk['content'],
                    'chunk_type': chunk['chunk_type'],
                    'page': chunk.get('page', 1)  # Добавляем page в payload
                }
                
                self.qdrant_service.upsert_point(point_id, vector, payload)
            
            logger.info(f"✅ [INDEX_CHUNKS] Indexed {len(chunks)} chunks for document {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ [INDEX_CHUNKS] Error indexing chunks: {e}")
            return False

    def clear_collection(self) -> bool:
        """Очистка всей коллекции Qdrant"""
        try:
            logger.info("🧹 [CLEAR_COLLECTION] Clearing entire collection...")
            
            # Очищаем коллекцию
            success = self.qdrant_service.clear_collection()
            
            if success:
                logger.info("✅ [CLEAR_COLLECTION] Collection cleared successfully")
                return True
            else:
                logger.error("❌ [CLEAR_COLLECTION] Failed to clear collection")
                return False
            
        except Exception as e:
            logger.error(f"❌ [CLEAR_COLLECTION] Error clearing collection: {e}")
            return False
