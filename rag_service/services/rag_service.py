import logging
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime
import qdrant_client
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
import psycopg2
from psycopg2.extras import RealDictCursor
import re

# Настройка логирования
logger = logging.getLogger(__name__)
model_logger = logging.getLogger("model")

class DatabaseManager:
    """Менеджер для работы с базой данных PostgreSQL"""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
    
    def get_cursor(self):
        """Получение курсора для работы с базой данных"""
        connection = psycopg2.connect(self.connection_string)
        return connection.cursor(cursor_factory=RealDictCursor)

class RAGService:
    """Сервис для работы с RAG-системой"""
    
    def __init__(self):
        # Конфигурация
        self.QDRANT_URL = "http://qdrant:6333"
        self.POSTGRES_URL = "postgresql://norms_user:norms_password@norms-db:5432/norms_db"
        self.VECTOR_COLLECTION = "normative_documents"
        self.VECTOR_SIZE = 1024
        
        # Инициализация клиентов
        self.qdrant_client = qdrant_client.QdrantClient(self.QDRANT_URL)
        self.db_manager = DatabaseManager(self.POSTGRES_URL)
        
        # Инициализация модели эмбеддингов (ленивая загрузка)
        self.embedding_model = None
        
        logger.info("🚀 [RAG_SERVICE] RAG Service initialized")
    
    def _load_embedding_model(self):
        """Загрузка модели эмбеддингов BGE-M3"""
        if self.embedding_model is None:
            try:
                logger.info("🤖 [EMBEDDING_MODEL] Loading BGE-M3 model...")
                self.embedding_model = SentenceTransformer('BAAI/bge-m3')
                logger.info("✅ [EMBEDDING_MODEL] BGE-M3 model loaded successfully")
            except Exception as e:
                logger.error(f"❌ [EMBEDDING_MODEL] Failed to load BGE-M3 model: {e}")
                raise e
    
    def create_embedding(self, text: str) -> List[float]:
        """Создание эмбеддинга для текста с использованием BGE-M3"""
        try:
            self._load_embedding_model()
            
            # Генерируем эмбеддинг
            embedding = self.embedding_model.encode(text, normalize_embeddings=True)
            
            # Преобразуем в список
            embedding_list = embedding.tolist()
            
            model_logger.info(f"✅ [EMBEDDING] Generated embedding for text: '{text[:100]}...'")
            return embedding_list
            
        except Exception as e:
            logger.error(f"❌ [EMBEDDING] Error creating embedding: {e}")
            raise e
    
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
                # Создаем эмбеддинг для чанка
                content = chunk.get('content', '')
                if not content.strip():
                    continue
                
                embedding = self.create_embedding(content)
                
                # Извлекаем код документа из названия
                document_title = chunk.get('document_title', '')
                code = self.extract_document_code(document_title)
                
                # Создание точки для Qdrant
                point = {
                    'id': chunk.get('id'),
                    'vector': embedding,
                    'payload': {
                        'document_id': document_id,
                        'code': code,  # Код документа (ГОСТ, СП и т.д.)
                        'title': document_title,  # Полное название документа
                        'section_title': chunk.get('section_title', ''),  # Заголовок раздела
                        'content': chunk.get('content', ''),
                        'chunk_type': chunk.get('chunk_type', 'paragraph'),
                        'page': chunk.get('page', 1),
                        'section': chunk.get('section', ''),
                        'metadata': chunk.get('metadata', {})
                    }
                }
                points.append(point)
            
            # Добавляем точки в Qdrant
            if points:
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
    
    def hybrid_search(self, query: str, k: int = 8,
                     document_filter: Optional[str] = None,
                     chapter_filter: Optional[str] = None,
                     chunk_type_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Гибридный поиск по нормативным документам"""
        try:
            logger.info(f"🔍 [SEARCH] Performing hybrid search for query: '{query}' with k={k}")
            
            # Векторный поиск
            vector_results = self.vector_search(query, k * 2)
            logger.info(f"✅ [SEARCH] Vector search completed. Found {len(vector_results)} results.")
            
            # BM25 поиск (пока не реализован, используем только векторный)
            bm25_results = []
            logger.info(f"✅ [SEARCH] BM25 search completed. Found {len(bm25_results)} results.")
            
            # Объединяем результаты
            combined_results = self.combine_search_results(vector_results, bm25_results, k)
            logger.info(f"✅ [SEARCH] Combined search results. Total {len(combined_results)} results.")
            
            # Применяем фильтры
            filtered_results = self.apply_search_filters(combined_results, document_filter, chapter_filter, chunk_type_filter)
            logger.info(f"✅ [SEARCH] Applied filters. Final {len(filtered_results)} results.")
            
            return filtered_results
            
        except Exception as e:
            logger.error(f"❌ [SEARCH] Hybrid search error: {e}")
            return []
    
    def vector_search(self, query: str, k: int) -> List[Dict[str, Any]]:
        """Векторный поиск в Qdrant"""
        try:
            logger.info(f"🔍 [VECTOR] Performing vector search for query: '{query}' with k={k}")
            
            # Создаем эмбеддинг для запроса
            query_embedding = self.create_embedding(query)
            
            # Выполняем поиск в Qdrant
            search_start = datetime.now()
            model_logger.info(f"🔍 [QDRANT_SEARCH] Searching in Qdrant collection: {self.VECTOR_COLLECTION}")
            
            results = self.qdrant_client.search(
                collection_name=self.VECTOR_COLLECTION,
                query_vector=query_embedding,
                limit=k,
                with_payload=True,
                with_vectors=False
            )
            
            search_time = (datetime.now() - search_start).total_seconds()
            total_time = search_time
            
            logger.info(f"✅ [VECTOR] Vector search completed in {total_time:.3f}s. Found {len(results)} results.")
            model_logger.info(f"✅ [QDRANT_SEARCH] Qdrant search completed in {search_time:.3f}s, found {len(results)} results")
            
            # Преобразуем результаты
            processed_results = []
            for result in results:
                processed_result = {
                    'id': result.id,
                    'score': result.score,
                    'document_id': result.payload.get('document_id'),
                    'code': result.payload.get('code', ''),
                    'title': result.payload.get('title', ''),
                    'section_title': result.payload.get('section_title', ''),
                    'content': result.payload.get('content', ''),
                    'chunk_type': result.payload.get('chunk_type', 'paragraph'),
                    'page': result.payload.get('page', 1),
                    'section': result.payload.get('section', ''),
                    'metadata': result.payload.get('metadata', {}),
                    'search_type': 'vector'
                }
                processed_results.append(processed_result)
            
            return processed_results
            
        except Exception as e:
            total_time = (datetime.now() - datetime.now()).total_seconds()
            logger.error(f"❌ [VECTOR] Vector search error after {total_time:.3f}s: {type(e).__name__}: {str(e)}")
            return []
    
    def bm25_search(self, query: str, k: int) -> List[Dict[str, Any]]:
        """BM25 поиск (пока не реализован)"""
        try:
            logger.info(f"🔍 [BM25] Performing BM25 search for query: '{query}' with k={k}")
            
            # TODO: Реализовать BM25 поиск
            results = []
            
            logger.info(f"✅ [BM25] BM25 search completed. Found {len(results)} results.")
            
            # Преобразуем результаты
            processed_results = []
            for result in results:
                processed_result = {
                    'id': result.get('id'),
                    'score': result.get('score', 0),
                    'document_id': result.get('document_id'),
                    'code': result.get('code', ''),
                    'title': result.get('title', ''),
                    'section_title': result.get('section_title', ''),
                    'content': result.get('content', ''),
                    'chunk_type': result.get('chunk_type', 'paragraph'),
                    'page': result.get('page', 1),
                    'section': result.get('section', ''),
                    'metadata': result.get('metadata', {}),
                    'search_type': 'bm25'
                }
                processed_results.append(processed_result)
            
            return processed_results
            
        except Exception as e:
            logger.error(f"❌ [BM25] BM25 search error: {e}")
            return []
    
    def combine_search_results(self, vector_results: List[Dict], bm25_results: List[Dict], k: int) -> List[Dict]:
        """Объединение результатов векторного и BM25 поиска"""
        try:
            # Создаем словарь для объединения результатов
            combined_dict = {}
            
            # Добавляем векторные результаты
            for result in vector_results:
                result_id = result['id']
                if result_id not in combined_dict:
                    combined_dict[result_id] = result
                    combined_dict[result_id]['combined_score'] = result['score']
                else:
                    # Если результат уже есть, обновляем комбинированный скор
                    combined_dict[result_id]['combined_score'] = max(
                        combined_dict[result_id]['combined_score'],
                        result['score']
                    )
            
            # Добавляем BM25 результаты
            for result in bm25_results:
                result_id = result['id']
                if result_id not in combined_dict:
                    combined_dict[result_id] = result
                    combined_dict[result_id]['combined_score'] = result['score']
                else:
                    # Если результат уже есть, обновляем комбинированный скор
                    combined_dict[result_id]['combined_score'] = max(
                        combined_dict[result_id]['combined_score'],
                        result['score']
                    )
            
            # Сортируем по комбинированному скору
            combined_results = list(combined_dict.values())
            combined_results.sort(key=lambda x: x['combined_score'], reverse=True)
            
            # Возвращаем топ-k результатов
            return combined_results[:k]
            
        except Exception as e:
            logger.error(f"❌ [COMBINE] Error combining search results: {e}")
            return []
    
    def apply_search_filters(self, results: List[Dict], 
                           document_filter: Optional[str] = None,
                           chapter_filter: Optional[str] = None,
                           chunk_type_filter: Optional[str] = None) -> List[Dict]:
        """Применение фильтров к результатам поиска"""
        try:
            filtered_results = results
            
            # Фильтр по документу
            if document_filter:
                filtered_results = [
                    result for result in filtered_results
                    if document_filter.lower() in result.get('title', '').lower()
                ]
            
            # Фильтр по главе
            if chapter_filter:
                filtered_results = [
                    result for result in filtered_results
                    if chapter_filter.lower() in result.get('section_title', '').lower()
                ]
            
            # Фильтр по типу чанка
            if chunk_type_filter:
                filtered_results = [
                    result for result in filtered_results
                    if chunk_type_filter.lower() == result.get('chunk_type', '').lower()
                ]
            
            return filtered_results
            
        except Exception as e:
            logger.error(f"❌ [FILTER] Error applying filters: {e}")
            return results
    
    def get_documents(self) -> List[Dict[str, Any]]:
        """Получение списка документов"""
        try:
            with self.db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT id, original_filename, category, processing_status, created_at
                    FROM uploaded_documents
                    ORDER BY created_at DESC
                """)
                documents = cursor.fetchall()
                return [dict(doc) for doc in documents]
        except Exception as e:
            logger.error(f"❌ [GET_DOCUMENTS] Error getting documents: {e}")
            return []
    
    def get_documents_from_uploaded(self, document_type: str = 'normative') -> List[Dict[str, Any]]:
        """Получение документов из таблицы uploaded_documents"""
        try:
            with self.db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT id, original_filename, category, processing_status, created_at, 
                           file_size, COALESCE(token_count, 0) as token_count
                    FROM uploaded_documents
                    WHERE category = %s OR %s = 'all'
                    ORDER BY created_at DESC
                """, (document_type, document_type))
                documents = cursor.fetchall()
                return [dict(doc) for doc in documents]
        except Exception as e:
            logger.error(f"❌ [GET_DOCUMENTS_FROM_UPLOADED] Error getting documents: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Получение статистики RAG-системы"""
        try:
            # Статистика документов
            with self.db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_documents,
                        COUNT(CASE WHEN processing_status = 'completed' THEN 1 END) as completed_documents,
                        COUNT(CASE WHEN processing_status = 'processing' THEN 1 END) as processing_documents,
                        COUNT(CASE WHEN processing_status = 'error' THEN 1 END) as error_documents
                    FROM uploaded_documents
                """)
                doc_stats = cursor.fetchone()
            
            # Статистика Qdrant
            try:
                collection_info = self.qdrant_client.get_collection(self.VECTOR_COLLECTION)
                qdrant_points = collection_info.points_count
            except Exception:
                qdrant_points = 0
            
            return {
                "documents": dict(doc_stats) if doc_stats else {},
                "qdrant": {
                    "collection": self.VECTOR_COLLECTION,
                    "points_count": qdrant_points
                },
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"❌ [GET_STATS] Error getting stats: {e}")
            return {}
    
    def get_document_chunks(self, document_id: int) -> List[Dict[str, Any]]:
        """Получение информации о чанках документа"""
        try:
            with self.db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT chunk_id, content, page_number, chapter, section
                    FROM normative_chunks
                    WHERE document_id = %s
                    ORDER BY page_number, chunk_id
                """, (document_id,))
                chunks = cursor.fetchall()
                return [dict(chunk) for chunk in chunks]
        except Exception as e:
            logger.error(f"❌ [GET_DOCUMENT_CHUNKS] Error getting chunks: {e}")
            return []
    
    def get_ntd_consultation(self, message: str, history: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Получение консультации НТД на основе поиска по документам"""
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
            sources = []
            response_parts = []
            
            for result in search_results[:3]:  # Берем топ-3 результата
                source = {
                    "title": result.get('title', 'Неизвестный документ'),
                    "code": result.get('code', ''),
                    "content": result.get('content', '')[:200] + '...',
                    "page": result.get('page', 1),
                    "score": result.get('score', 0)
                }
                sources.append(source)
                
                # Добавляем информацию о документе в ответ
                if result.get('code'):
                    response_parts.append(f"📄 **{result['code']}** - {result.get('title', '')}")
                else:
                    response_parts.append(f"📄 {result.get('title', '')}")
                
                response_parts.append(f"Содержание: {result.get('content', '')[:300]}...")
                response_parts.append("")
            
            # Формируем итоговый ответ
            if response_parts:
                response = "На основе поиска в базе нормативных документов, вот что я нашел:\n\n" + "\n".join(response_parts)
                response += f"\n\nНайдено {len(sources)} релевантных фрагментов из нормативных документов."
            else:
                response = "К сожалению, я не нашел релевантной информации в базе нормативных документов."
            
            return {
                "status": "success",
                "response": response,
                "sources": sources,
                "confidence": min(0.9, max(0.1, search_results[0].get('score', 0.5))),
                "documents_used": len(sources),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ [NTD_CONSULTATION] Error processing consultation: {e}")
            return {
                "status": "error",
                "response": "Произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте еще раз.",
                "sources": [],
                "confidence": 0.0,
                "documents_used": 0,
                "timestamp": datetime.now().isoformat()
            }
