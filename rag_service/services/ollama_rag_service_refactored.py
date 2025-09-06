import logging
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

# Импорты модулей
from .embedding_service import OllamaEmbeddingService
from .database_manager import DatabaseManager
from .document_parser import DocumentParser
from .metadata_extractor import MetadataExtractor
from .document_chunker import DocumentChunker
from .qdrant_service import QdrantService
from .reranker_service import BGERerankerService
from .bge_reranker_service import BGERankingService
from .hybrid_search_service import HybridSearchService
from .mmr_service import MMRService
from .intent_classifier_service import IntentClassifierService
from .context_builder_service import ContextBuilderService

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OllamaRAGService:
    """RAG сервис с использованием Ollama BGE-M3 для эмбеддингов"""
    
    def __init__(self):
        # Конфигурация
        self.QDRANT_URL = "http://qdrant:6333"  # Qdrant в Docker
        self.POSTGRES_URL = "postgresql://norms_user:norms_password@norms-db:5432/norms_db"  # БД в Docker
        self.VECTOR_COLLECTION = "normative_documents"
        self.VECTOR_SIZE = 1024  # Размер эмбеддинга BGE-M3
        
        # Инициализация модулей
        self.qdrant_service = QdrantService(self.QDRANT_URL, self.VECTOR_COLLECTION, self.VECTOR_SIZE)
        self.db_manager = DatabaseManager(self.POSTGRES_URL)
        self.embedding_service = OllamaEmbeddingService()
        self.document_parser = DocumentParser()
        self.metadata_extractor = MetadataExtractor()
        self.document_chunker = DocumentChunker()
        self.reranker_service = BGERerankerService()  # Старый реранкер для fallback
        self.bge_reranker_service = BGERankingService()  # Новый BGE реранкер
        
        # Инициализация гибридного поиска
        self.hybrid_search_service = HybridSearchService(
            db_connection=self.db_manager.get_connection(),
            embedding_service=self.embedding_service,
            qdrant_service=self.qdrant_service,
            alpha=0.6,  # Больше веса для dense поиска
            use_rrf=True,
            rrf_k=60
        )
        
        # Инициализация MMR сервиса
        self.mmr_service = MMRService(
            lambda_param=0.7,  # Баланс релевантности и разнообразия
            similarity_threshold=0.8
        )
        
        # Инициализация классификатора намерений
        self.intent_classifier = IntentClassifierService()
        
        # Инициализация сервиса построения контекста
        self.context_builder = ContextBuilderService()
        
        logger.info("🚀 [OLLAMA_RAG_SERVICE] Ollama RAG Service initialized with modular architecture")
        
        # Инициализируем методы
        from .ollama_rag_service_methods import OllamaRAGServiceMethods
        self.methods = OllamaRAGServiceMethods(self)
    
    def get_structured_context(self, query: str, k: int = 8, document_filter: Optional[str] = None, 
                              chapter_filter: Optional[str] = None, chunk_type_filter: Optional[str] = None,
                              use_reranker: bool = True, fast_mode: bool = False, use_mmr: bool = True,
                              use_intent_classification: bool = True) -> Dict[str, Any]:
        """
        Получение структурированного контекста для запроса
        """
        try:
            logger.info(f"🏗️ [STRUCTURED_CONTEXT] Building structured context for query: '{query[:50]}...'")
            
            # Выполняем гибридный поиск
            search_results = self.methods.hybrid_search(
                query=query,
                k=k,
                document_filter=document_filter,
                chapter_filter=chapter_filter,
                chunk_type_filter=chunk_type_filter,
                use_reranker=use_reranker,
                fast_mode=fast_mode,
                use_mmr=use_mmr,
                use_intent_classification=use_intent_classification
            )
            
            if not search_results:
                logger.warning(f"⚠️ [STRUCTURED_CONTEXT] No search results found for query: '{query}'")
                return {
                    "query": query,
                    "timestamp": datetime.now().isoformat(),
                    "context": [],
                    "meta_summary": {
                        "query_type": "no_results",
                        "documents_found": 0,
                        "sections_covered": 0,
                        "avg_relevance": 0.0,
                        "coverage_quality": "нет результатов",
                        "key_documents": [],
                        "key_sections": []
                    },
                    "total_candidates": 0,
                    "avg_score": 0.0
                }
            
            # Строим структурированный контекст
            structured_context = self.context_builder.build_structured_context(search_results, query)
            
            logger.info(f"✅ [STRUCTURED_CONTEXT] Structured context built with {structured_context['total_candidates']} candidates")
            return structured_context
            
        except Exception as e:
            logger.error(f"❌ [STRUCTURED_CONTEXT] Error building structured context: {e}")
            return {
                "query": query,
                "timestamp": datetime.now().isoformat(),
                "context": [],
                "meta_summary": {
                    "query_type": "error",
                    "documents_found": 0,
                    "sections_covered": 0,
                    "avg_relevance": 0.0,
                    "coverage_quality": "ошибка",
                    "key_documents": [],
                    "key_sections": []
                },
                "total_candidates": 0,
                "avg_score": 0.0,
                "error": str(e)
            }
    
    def extract_document_code(self, document_title: str) -> str:
        """Извлекает код документа из названия (ГОСТ, СП, СНиП и т.д.)"""
        return self.document_parser.extract_document_code(document_title)
    
    def index_document_chunks(self, document_id: int, chunks: List[Dict[str, Any]]) -> bool:
        """Индексация чанков документа в Qdrant"""
        try:
            logger.info(f"📝 [INDEXING] Starting indexing for document {document_id} with {len(chunks)} chunks")
            
            # Получаем метаданные документа
            logger.info(f"🔍 [INDEXING] Getting metadata for document_id: {document_id}")
            document_metadata = self.methods._get_document_metadata(document_id)
            logger.info(f"🔍 [INDEXING] Retrieved metadata: {document_metadata}")
            
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
                    
                    # Создаем метаданные чанка
                    chunk_metadata = self.metadata_extractor.create_chunk_metadata(chunk, document_metadata)
                    
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
                            'metadata': chunk_metadata
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
    
    # Делегирование методов
    def hybrid_search(self, *args, **kwargs):
        return self.methods.hybrid_search(*args, **kwargs)
    
    def get_ntd_consultation(self, *args, **kwargs):
        return self.methods.get_ntd_consultation(*args, **kwargs)
    
    def get_documents(self):
        return self.db_manager.get_documents()
    
    def get_documents_from_uploaded(self, document_type: str = 'all'):
        return self.db_manager.get_documents_from_uploaded(document_type)
    
    def get_document_chunks(self, document_id: int):
        return self.db_manager.get_document_chunks(document_id)
    
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
            db_stats = self.db_manager.get_stats()
            
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
                db_stats = self.db_manager.get_stats()
                
                return {
                    'qdrant': {
                        'collection_name': self.VECTOR_COLLECTION,
                        'vectors_count': 0,  # Не можем получить из Qdrant
                        'indexed_vectors': 0,
                        'status': 'error'
                    },
                    'postgresql': db_stats,
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
        return self.db_manager.save_document_to_db(
            document_id, filename, original_filename, file_type, 
            file_size, document_hash, category, document_type
        )

    def update_document_status(self, document_id: int, status: str, error_message: str = None):
        return self.db_manager.update_document_status(document_id, status, error_message)

    async def process_document_async(self, document_id: int, content: bytes, filename: str) -> bool:
        """Асинхронная обработка документа"""
        try:
            logger.info(f"🔄 [PROCESS_ASYNC] Starting processing for document {document_id}")
            
            # Извлекаем текст из документа
            text_content = await self.document_parser.extract_text_from_document(content, filename)
            if not text_content:
                logger.error(f"❌ [PROCESS_ASYNC] Failed to extract text from document {document_id}")
                return False
            
            # Разбиваем на чанки
            chunks = self.document_chunker.create_chunks(text_content, document_id, filename)
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

    async def index_chunks_async(self, chunks: List[Dict[str, Any]], document_id: int) -> bool:
        """Асинхронная индексация чанков"""
        try:
            # Получаем метаданные документа
            logger.info(f"🔍 [INDEX_CHUNKS_ASYNC] Getting metadata for document_id: {document_id}")
            document_metadata = self.methods._get_document_metadata(document_id)
            logger.info(f"🔍 [INDEX_CHUNKS_ASYNC] Retrieved metadata: {document_metadata}")
            
            # Сохраняем чанки в PostgreSQL
            with self.db_manager.get_cursor() as cursor:
                for chunk in chunks:
                    cursor.execute("""
                        INSERT INTO normative_chunks 
                        (chunk_id, clause_id, document_id, document_title, chunk_type, content, page_number, chapter, section)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        chunk['chunk_id'],
                        chunk['chunk_id'],  # Используем chunk_id как clause_id
                        chunk['document_id'],
                        chunk['document_title'],
                        chunk['chunk_type'],
                        chunk['content'],
                        chunk.get('page', 1),  # page_number
                        chunk.get('chapter', ''),  # chapter
                        chunk.get('section', '')   # section
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
                
                # Создаем метаданные чанка
                chunk_metadata = self.metadata_extractor.create_chunk_metadata(chunk, document_metadata)
                
                payload = {
                    'chunk_id': chunk['chunk_id'],
                    'document_id': chunk['document_id'],
                    'document_title': chunk['document_title'],
                    'content': chunk['content'],
                    'chunk_type': chunk['chunk_type'],
                    'page': chunk.get('page', 1),
                    'chapter': chunk.get('chapter', ''),
                    'section': chunk.get('section', ''),
                    'metadata': chunk_metadata
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
    
    def get_hybrid_search_stats(self) -> Dict[str, Any]:
        """Получение статистики гибридного поиска"""
        try:
            stats = self.hybrid_search_service.get_search_stats()
            bge_reranker_stats = self.bge_reranker_service.get_reranking_stats()
            mmr_stats = self.mmr_service.get_mmr_stats()
            intent_classifier_stats = self.intent_classifier.get_intent_stats()
            
            return {
                "status": "success",
                "stats": stats,
                "bge_reranker": bge_reranker_stats,
                "mmr": mmr_stats,
                "intent_classifier": intent_classifier_stats,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"❌ [HYBRID_STATS] Error getting hybrid search stats: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
