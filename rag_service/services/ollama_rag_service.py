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
from .reranker_service import BGERerankerService
from .bge_reranker_service import BGERankingService
from .hybrid_search_service import HybridSearchService
from .mmr_service import MMRService
from .intent_classifier_service import IntentClassifierService
from .context_builder_service import ContextBuilderService

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
        self.connection = None
    
    def get_connection(self):
        """Получение соединения с базой данных"""
        if not self.connection or self.connection.closed:
            self.connection = psycopg2.connect(self.connection_string)
        return self.connection
    
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
        
        logger.info("🚀 [OLLAMA_RAG_SERVICE] Ollama RAG Service initialized with hybrid search and structured context")
    
    def get_structured_context(self, query: str, k: int = 8, document_filter: Optional[str] = None, 
                              chapter_filter: Optional[str] = None, chunk_type_filter: Optional[str] = None,
                              use_reranker: bool = True, fast_mode: bool = False, use_mmr: bool = True,
                              use_intent_classification: bool = True) -> Dict[str, Any]:
        """
        Получение структурированного контекста для запроса
        
        Args:
            query: Поисковый запрос
            k: Количество результатов для анализа
            document_filter: Фильтр по типу документа
            chapter_filter: Фильтр по главе
            chunk_type_filter: Фильтр по типу чанка
            use_reranker: Использовать ли реранкинг
            fast_mode: Быстрый режим
            use_mmr: Использовать ли MMR
            use_intent_classification: Использовать ли классификацию намерений
            
        Returns:
            Структурированный контекст с мета-сводкой
        """
        try:
            logger.info(f"🏗️ [STRUCTURED_CONTEXT] Building structured context for query: '{query[:50]}...'")
            
            # Выполняем гибридный поиск
            search_results = self.hybrid_search(
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
            
            # Получаем метаданные документа
            logger.info(f"🔍 [INDEXING] Getting metadata for document_id: {document_id}")
            document_metadata = self._get_document_metadata(document_id)
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
                    chunk_metadata = self._create_chunk_metadata(chunk, document_metadata)
                    
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
    
    def hybrid_search(self, query: str, k: int = 8, document_filter: Optional[str] = None, 
                     chapter_filter: Optional[str] = None, chunk_type_filter: Optional[str] = None, 
                     use_reranker: bool = True, fast_mode: bool = False, use_mmr: bool = True, 
                     use_intent_classification: bool = True) -> List[Dict[str, Any]]:
        """
        Гибридный поиск по нормативным документам с опциональным реранкингом
        
        Args:
            query: Поисковый запрос
            k: Количество финальных результатов
            document_filter: Фильтр по типу документа
            chapter_filter: Фильтр по главе
            chunk_type_filter: Фильтр по типу чанка
            use_reranker: Использовать ли реранкинг (по умолчанию True)
            fast_mode: Быстрый режим (отключает некоторые оптимизации)
            use_mmr: Использовать ли MMR для разнообразия (по умолчанию True)
            use_intent_classification: Использовать ли классификацию намерений (по умолчанию True)
        """
        try:
            logger.info(f"🔍 [HYBRID_SEARCH] Performing advanced hybrid search for query: '{query}' with k={k}")
            
            # Классификация намерения и переписывание запроса
            intent_classification = None
            query_rewriting = None
            enhanced_queries = [query]
            enhanced_filters = {
                'document_filter': document_filter,
                'chapter_filter': chapter_filter,
                'chunk_type_filter': chunk_type_filter
            }
            
            if use_intent_classification and not fast_mode:
                try:
                    logger.info(f"🎯 [HYBRID_SEARCH] Classifying intent for query: '{query[:50]}...'")
                    intent_classification = self.intent_classifier.classify_intent(query)
                    query_rewriting = self.intent_classifier.rewrite_query(query, intent_classification)
                    
                    # Используем переписанные запросы
                    enhanced_queries = query_rewriting.rewritten_queries
                    
                    # Обновляем фильтры на основе намерения
                    if query_rewriting.section_filters:
                        enhanced_filters['chapter_filter'] = query_rewriting.section_filters[0]  # Используем первый фильтр
                    if query_rewriting.chunk_type_filters:
                        enhanced_filters['chunk_type_filter'] = query_rewriting.chunk_type_filters[0]
                    
                    logger.info(f"✅ [HYBRID_SEARCH] Intent classified as: {intent_classification.intent_type.value} "
                              f"(confidence: {intent_classification.confidence:.3f})")
                    logger.info(f"🔄 [HYBRID_SEARCH] Generated {len(enhanced_queries)} enhanced queries")
                    
                except Exception as e:
                    logger.warning(f"⚠️ [HYBRID_SEARCH] Intent classification failed: {e}")
                    # Продолжаем с исходным запросом
            
            # Используем новый гибридный поиск
            # Ищем больше результатов для реранкинга и MMR
            search_k = 50 if use_reranker else (k * 2 if use_mmr else k)
            
            # Выполняем поиск с лучшим запросом
            best_query = enhanced_queries[0]  # Используем первый (лучший) запрос
            search_results = self.hybrid_search_service.search(
                query=best_query,
                k=search_k,
                document_filter=enhanced_filters['document_filter'],
                chapter_filter=enhanced_filters['chapter_filter'],
                chunk_type_filter=enhanced_filters['chunk_type_filter'],
                use_alpha_blending=True,
                use_rrf=True
            )
            
            # Преобразуем SearchResult в старый формат
            results = []
            for result in search_results:
                formatted_result = {
                    'id': result.id,
                    'score': result.score,
                    'document_id': result.document_id,
                    'chunk_id': result.chunk_id,
                    'code': result.code,
                    'document_title': result.document_title,
                    'section_title': result.section_title,
                    'content': result.content,
                    'chunk_type': result.chunk_type,
                    'page': result.page,
                    'section': result.section,
                    'metadata': result.metadata,
                    'search_type': result.search_type,
                    'rank': result.rank
                }
                
                # Добавляем информацию о намерении
                if intent_classification:
                    formatted_result['intent_type'] = intent_classification.intent_type.value
                    formatted_result['intent_confidence'] = intent_classification.confidence
                    formatted_result['intent_keywords'] = intent_classification.keywords
                    formatted_result['intent_reasoning'] = intent_classification.reasoning
                
                if query_rewriting:
                    formatted_result['enhanced_queries'] = query_rewriting.rewritten_queries
                    formatted_result['section_filters'] = query_rewriting.section_filters
                    formatted_result['chunk_type_filters'] = query_rewriting.chunk_type_filters
                
                results.append(formatted_result)
            
            logger.info(f"✅ [HYBRID_SEARCH] Found {len(results)} hybrid results")
            
            # Применяем реранкинг, если включен и не быстрый режим
            if use_reranker and not fast_mode and len(results) > k:
                logger.info(f"🔄 [HYBRID_SEARCH] Applying BGE reranking to {len(results)} results → {k} final results")
                try:
                    # Используем новый BGE реранкер с fallback
                    reranked_results = self.bge_reranker_service.rerank_with_fallback(
                        query=query,
                        search_results=results,
                        top_k=k,
                        initial_top_k=len(results)
                    )
                    
                    if reranked_results:
                        logger.info(f"✅ [HYBRID_SEARCH] BGE reranking completed successfully")
                        final_results = reranked_results
                    else:
                        logger.warning("⚠️ [HYBRID_SEARCH] BGE reranking failed, trying fallback")
                        # Fallback к старому реранкеру
                        reranked_results = self.reranker_service.rerank_search_results(
                            query=query,
                            search_results=results,
                            top_k=k,
                            initial_top_k=len(results)
                        )
                        if reranked_results:
                            logger.info(f"✅ [HYBRID_SEARCH] Fallback reranking completed")
                            final_results = reranked_results
                        else:
                            logger.warning("⚠️ [HYBRID_SEARCH] All reranking failed, using original results")
                            final_results = results[:k]
                    
                    # Применяем MMR для разнообразия
                    if use_mmr and not fast_mode and len(final_results) > k:
                        logger.info(f"🔄 [HYBRID_SEARCH] Applying MMR diversification to {len(final_results)} results → {k}")
                        try:
                            mmr_results = self.mmr_service.diversify_results(
                                results=final_results,
                                k=k,
                                query=query,
                                use_semantic_similarity=True
                            )
                            
                            # Конвертируем MMR результаты обратно в старый формат
                            diversified_results = []
                            for mmr_result in mmr_results:
                                formatted_result = {
                                    'id': mmr_result.id,
                                    'score': mmr_result.mmr_score,
                                    'document_id': mmr_result.document_id,
                                    'chunk_id': mmr_result.chunk_id,
                                    'code': mmr_result.code,
                                    'document_title': mmr_result.document_title,
                                    'section_title': mmr_result.section_title,
                                    'content': mmr_result.content,
                                    'chunk_type': mmr_result.chunk_type,
                                    'page': mmr_result.page,
                                    'section': mmr_result.section,
                                    'metadata': mmr_result.metadata,
                                    'search_type': mmr_result.search_type,
                                    'rank': mmr_result.rank,
                                    'mmr_score': mmr_result.mmr_score,
                                    'relevance_score': mmr_result.relevance_score,
                                    'diversity_score': mmr_result.diversity_score
                                }
                                diversified_results.append(formatted_result)
                            
                            logger.info(f"✅ [HYBRID_SEARCH] MMR diversification completed")
                            return diversified_results
                            
                        except Exception as e:
                            logger.error(f"❌ [HYBRID_SEARCH] Error during MMR diversification: {e}")
                            logger.info("🔄 [HYBRID_SEARCH] Falling back to reranked results")
                            return final_results[:k]
                    else:
                        return final_results[:k]
                        
                except Exception as e:
                    logger.error(f"❌ [HYBRID_SEARCH] Error during BGE reranking: {e}")
                    logger.info("🔄 [HYBRID_SEARCH] Falling back to original results")
                    return results[:k]
            else:
                # Если реранкинг не используется, быстрый режим или результатов мало
                if fast_mode:
                    logger.info(f"⚡ [HYBRID_SEARCH] Fast mode: returning top {k} results without reranking")
                return results[:k]
            
        except Exception as e:
            logger.error(f"❌ [HYBRID_SEARCH] Error during hybrid search: {e}")
            # Fallback к старому методу при ошибке
            return self._fallback_hybrid_search(query, k, document_filter, chapter_filter, chunk_type_filter)
    
    def _fallback_hybrid_search(self, query: str, k: int, document_filter: Optional[str] = None, 
                               chapter_filter: Optional[str] = None, chunk_type_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fallback метод для гибридного поиска (старая реализация)"""
        try:
            logger.info(f"🔄 [FALLBACK] Using fallback hybrid search for query: '{query}'")
            
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
                    'metadata': point['payload'].get('metadata', {}),
                    'search_type': 'fallback'
                }
                results.append(result)
            
            logger.info(f"✅ [FALLBACK] Found {len(results)} fallback results")
            return results
            
        except Exception as e:
            logger.error(f"❌ [FALLBACK] Error during fallback search: {e}")
            return []
    
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
    
    def get_ntd_consultation(self, message: str, user_id: str, history: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Получение консультации по НТД с использованием структурированного контекста"""
        try:
            logger.info(f"💬 [NTD_CONSULTATION] Processing consultation request: '{message[:100]}...'")
            
            # Извлекаем код документа из запроса
            document_code = self.extract_document_code_from_query(message)
            logger.info(f"🔍 [NTD_CONSULTATION] Extracted document code: {document_code}")
            
            # Получаем структурированный контекст
            structured_context = self.get_structured_context(message, k=10)
            
            if not structured_context.get('context'):
                return {
                    "status": "success",
                    "response": "К сожалению, я не нашел релевантной информации в базе нормативных документов. Попробуйте переформулировать ваш вопрос или обратитесь к актуальным нормативным документам.",
                    "sources": [],
                    "confidence": 0.0,
                    "documents_used": 0,
                    "structured_context": structured_context,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Получаем результаты поиска для совместимости
            search_results = []
            for context_item in structured_context['context']:
                search_results.append({
                    'code': context_item['doc'],
                    'document_title': context_item['document_title'],
                    'section': context_item['section'],
                    'page': context_item['page'],
                    'content': context_item.get('snippet', ''),
                    'score': context_item['score'],
                    'chunk_type': context_item.get('chunk_type', ''),
                    'metadata': context_item.get('metadata', {})
                })
            
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
            
            # Формируем источники с правильной информацией
            sources = []
            for result in search_results[:3]:  # Топ-3 результата
                source = {
                    'title': result['document_title'],
                    'filename': result['document_title'],
                    'page': result.get('page', 'Не указана'),
                    'section': result.get('section', 'Не указан'),
                    'document_code': result.get('code', ''),
                    'content_preview': result['content'][:200] + "..." if len(result['content']) > 200 else result['content'],
                    'relevance_score': result['score']
                }
                sources.append(source)
            
            # Формируем структурированный ответ с использованием нового контекста
            response = self._format_consultation_response_with_context(message, structured_context, top_result)
            
            return {
                "status": "success",
                "response": response,
                "sources": sources,
                "confidence": confidence,
                "documents_used": len(search_results),
                "structured_context": structured_context,
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
    
    def _format_consultation_response(self, message: str, search_results: List[Dict], top_result: Dict) -> str:
        """Форматирование ответа консультации с правильной структурой"""
        try:
            # Анализируем запрос для определения типа ответа
            query_lower = message.lower()
            
            # Определяем тип ответа
            if any(word in query_lower for word in ['какой', 'что', 'как', 'где', 'когда']):
                response_type = "информационный"
            elif any(word in query_lower for word in ['регламентирует', 'определяет', 'устанавливает']):
                response_type = "нормативный"
            else:
                response_type = "общий"
            
            # Формируем структурированный ответ
            response_parts = []
            
            # Заголовок ответа
            if response_type == "нормативный":
                response_parts.append("## 📋 Нормативное регулирование")
            elif response_type == "информационный":
                response_parts.append("## 💡 Информация по вашему вопросу")
            else:
                response_parts.append("## 📖 Ответ на основе нормативных документов")
            
            # Основной ответ
            response_parts.append("")
            response_parts.append(f"**{top_result['document_title']}**")
            response_parts.append(f"*Раздел: {top_result['section']}*")
            response_parts.append("")
            
            # Форматируем содержимое в абзацы
            content = top_result['content']
            if content:
                # Разбиваем на предложения и группируем в абзацы
                sentences = content.split('. ')
                paragraphs = []
                current_paragraph = []
                
                for sentence in sentences:
                    if sentence.strip():
                        current_paragraph.append(sentence.strip())
                        # Если абзац стал достаточно длинным, начинаем новый
                        if len(' '.join(current_paragraph)) > 200:
                            paragraphs.append(' '.join(current_paragraph))
                            current_paragraph = []
                
                # Добавляем последний абзац
                if current_paragraph:
                    paragraphs.append(' '.join(current_paragraph))
                
                # Добавляем абзацы в ответ
                for paragraph in paragraphs:
                    if paragraph.strip():
                        response_parts.append(paragraph.strip())
                        response_parts.append("")
            
            # Дополнительная информация из других результатов
            if len(search_results) > 1:
                response_parts.append("---")
                response_parts.append("## 📚 Дополнительная информация")
                response_parts.append("")
                
                for i, result in enumerate(search_results[1:3], 1):  # Берем еще 2 результата
                    if result['document_title'] != top_result['document_title']:
                        response_parts.append(f"**{result['document_title']}**")
                        response_parts.append(f"*Раздел: {result['section']}*")
                        response_parts.append("")
                        
                        # Краткое содержание
                        preview = result['content'][:300] + "..." if len(result['content']) > 300 else result['content']
                        response_parts.append(preview)
                        response_parts.append("")
            
            # Заключение
            response_parts.append("---")
            response_parts.append("## 📝 Рекомендации")
            response_parts.append("")
            response_parts.append("Для получения полной информации обратитесь к полному тексту указанных нормативных документов.")
            
            return "\n".join(response_parts)
            
        except Exception as e:
            logger.error(f"❌ [FORMAT_RESPONSE] Error formatting response: {e}")
            # Fallback к простому формату
            return f"**{top_result['document_title']}**\n\n{top_result['content']}"
    
    def _format_consultation_response_with_context(self, message: str, structured_context: Dict[str, Any], top_result: Dict) -> str:
        """Форматирование ответа консультации с использованием структурированного контекста"""
        try:
            # Анализируем запрос для определения типа ответа
            query_lower = message.lower()
            
            # Определяем тип ответа
            if any(word in query_lower for word in ['какой', 'что', 'как', 'где', 'когда']):
                response_type = "информационный"
            elif any(word in query_lower for word in ['регламентирует', 'определяет', 'устанавливает']):
                response_type = "нормативный"
            else:
                response_type = "общий"
            
            # Формируем структурированный ответ
            response_parts = []
            
            # Заголовок ответа
            if response_type == "нормативный":
                response_parts.append("## 📋 Нормативное регулирование")
            elif response_type == "информационный":
                response_parts.append("## 💡 Информация по вашему вопросу")
            else:
                response_parts.append("## 📖 Ответ на основе нормативных документов")
            
            # Мета-сводка
            meta_summary = structured_context.get('meta_summary', {})
            if meta_summary:
                response_parts.append("")
                response_parts.append(f"**📊 Анализ запроса:** {meta_summary.get('query_type', 'общая информация')}")
                response_parts.append(f"**📚 Найдено документов:** {meta_summary.get('documents_found', 0)}")
                response_parts.append(f"**📑 Разделов:** {meta_summary.get('sections_covered', 0)}")
                response_parts.append(f"**⭐ Качество покрытия:** {meta_summary.get('coverage_quality', 'неизвестно')}")
                
                if meta_summary.get('key_documents'):
                    response_parts.append(f"**🔑 Ключевые документы:** {', '.join(meta_summary['key_documents'][:3])}")
            
            response_parts.append("")
            response_parts.append("---")
            response_parts.append("")
            
            # Основной ответ на основе структурированного контекста
            context_items = structured_context.get('context', [])
            
            for i, item in enumerate(context_items[:3], 1):  # Показываем топ-3
                response_parts.append(f"### {i}. {item['doc']} - {item['document_title']}")
                response_parts.append(f"**Раздел:** {item['section']} - {item['section_title']}")
                response_parts.append(f"**Страница:** {item['page']}")
                response_parts.append(f"**Релевантность:** {item['score']:.2f} ({item['why']})")
                
                # Добавляем сводку, если есть
                if 'summary' in item:
                    summary = item['summary']
                    response_parts.append("")
                    response_parts.append(f"**📝 О разделе:** {summary['topic']}")
                    response_parts.append(f"**⚖️ Тип нормы:** {summary['norm_type']}")
                    
                    if summary['key_points']:
                        response_parts.append("**🔑 Ключевые моменты:**")
                        for point in summary['key_points'][:3]:  # Показываем до 3 ключевых моментов
                            response_parts.append(f"• {point}")
                    
                    response_parts.append(f"**🎯 Релевантность:** {summary['relevance_reason']}")
                
                response_parts.append("")
                response_parts.append(f"**Содержание:**")
                
                # Форматируем содержимое в абзацы
                content = item.get('snippet', '')
                if content:
                    # Разбиваем на предложения и группируем в абзацы
                    sentences = content.split('. ')
                    paragraphs = []
                    current_paragraph = []
                    
                    for sentence in sentences:
                        if sentence.strip():
                            current_paragraph.append(sentence.strip())
                            # Если абзац стал достаточно длинным, начинаем новый
                            if len(' '.join(current_paragraph)) > 200:
                                paragraphs.append(' '.join(current_paragraph))
                                current_paragraph = []
                    
                    # Добавляем последний абзац
                    if current_paragraph:
                        paragraphs.append(' '.join(current_paragraph))
                    
                    # Добавляем абзацы в ответ
                    for paragraph in paragraphs:
                        response_parts.append(paragraph)
                        response_parts.append("")
                else:
                    response_parts.append("Содержимое недоступно")
                
                response_parts.append("---")
                response_parts.append("")
            
            # Итоговая информация
            response_parts.append(f"**📈 Статистика поиска:**")
            response_parts.append(f"• Всего найдено: {structured_context.get('total_candidates', 0)} релевантных фрагментов")
            response_parts.append(f"• Средняя релевантность: {structured_context.get('avg_score', 0):.2f}")
            response_parts.append(f"• Время обработки: {structured_context.get('timestamp', 'неизвестно')}")
            
            return "\n".join(response_parts)
            
        except Exception as e:
            logger.error(f"❌ [CONSULTATION_FORMAT] Error formatting response: {e}")
            # Fallback к простому форматированию
            return self._format_consultation_response(message, [top_result], top_result)
    
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
        """Создание чанков из текста документа с правильной нумерацией страниц и структурой"""
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
                        # Извлекаем структуру страницы (главы, разделы)
                        page_structure = self._extract_page_structure(page_text, page_num)
                        
                        # Разбиваем страницу на чанки
                        page_chunks = self._split_page_into_chunks(page_text, chunk_size=1000)
                        
                        for chunk_text in page_chunks:
                            # Определяем к какой главе/разделу относится чанк
                            chunk_structure = self._identify_chunk_structure(chunk_text, page_structure)
                            
                            chunks.append({
                                'chunk_id': f"doc_{document_id}_page_{page_num}_chunk_{chunk_id}",
                                'document_id': document_id,
                                'document_title': filename,
                                'content': chunk_text.strip(),
                                'chunk_type': 'paragraph',
                                'page': page_num,
                                'chapter': chunk_structure.get('chapter', ''),
                                'section': chunk_structure.get('section', '')
                            })
                            chunk_id += 1
            else:
                # Если маркеры страниц не найдены, разбиваем весь текст на чанки
                logger.info(f"📄 [CREATE_CHUNKS] No page markers found, treating as single page document")
                page_chunks = self._split_page_into_chunks(text, chunk_size=1000)
                
                # Извлекаем общую структуру документа
                document_structure = self._extract_document_structure(text)
                
                for chunk_text in page_chunks:
                    # Определяем к какой главе/разделу относится чанк
                    chunk_structure = self._identify_chunk_structure(chunk_text, document_structure)
                    
                    chunks.append({
                        'chunk_id': f"doc_{document_id}_page_1_chunk_{chunk_id}",
                        'document_id': document_id,
                        'document_title': filename,
                        'content': chunk_text.strip(),
                        'chunk_type': 'paragraph',
                        'page': 1,
                        'chapter': chunk_structure.get('chapter', ''),
                        'section': chunk_structure.get('section', '')
                    })
                    chunk_id += 1
            
            logger.info(f"✅ [CREATE_CHUNKS] Created {len(chunks)} chunks for document {document_id}")
            return chunks
            
        except Exception as e:
            logger.error(f"❌ [CREATE_CHUNKS] Error creating chunks: {e}")
            return []
    
    def _split_page_into_chunks(self, text: str, chunk_size: int = 1000) -> List[str]:
        """Разбиение текста страницы на иерархические чанки с сохранением структуры"""
        try:
            # Импортируем конфигурацию
            from config.chunking_config import get_chunking_config, validate_chunking_config
            
            # Получаем конфигурацию чанкования
            config = get_chunking_config('default')
            
            # Валидируем конфигурацию
            if not validate_chunking_config(config):
                logger.warning("⚠️ [CHUNKING] Invalid chunking config, using fallback")
                return self._simple_split_into_chunks(text, chunk_size)
            
            # Проверяем, включено ли семантическое чанкование
            if config.get('semantic_chunking', True):
                logger.info("📝 [CHUNKING] Using semantic chunking with meaning-based analysis")
                logger.info(f"📝 [CHUNKING] Input text length: {len(text)} characters")
                
                # Создаем семантические чанки
                semantic_chunks = self._create_semantic_chunks(text, config)
                
                if semantic_chunks:
                    logger.info(f"✅ [CHUNKING] Created {len(semantic_chunks)} semantic chunks")
                    return semantic_chunks
                else:
                    logger.warning("⚠️ [CHUNKING] No semantic chunks created, falling back to hierarchical")
            
            # Проверяем, включено ли иерархическое чанкование
            if not config.get('hierarchical_chunking', True):
                logger.info("📝 [CHUNKING] Hierarchical chunking disabled, using standard chunking")
                return self._standard_chunking(text, config)
            
            logger.info("📝 [CHUNKING] Using hierarchical chunking with structure preservation")
            logger.info(f"📝 [CHUNKING] Input text length: {len(text)} characters")
            
            # Извлекаем структуру документа
            document_structure = self._extract_document_structure(text)
            logger.info(f"📝 [CHUNKING] Extracted structure: {len(document_structure['chapters'])} chapters, {len(document_structure['sections'])} sections")
            
            # Создаем иерархические чанки
            hierarchical_chunks = self._create_hierarchical_chunks(text, document_structure, config)
            
            if not hierarchical_chunks:
                logger.warning("⚠️ [CHUNKING] No hierarchical chunks created, using fallback")
                return self._simple_split_into_chunks(text, chunk_size)
            
            logger.info(f"✅ [CHUNKING] Created {len(hierarchical_chunks)} hierarchical chunks")
            return hierarchical_chunks
            
        except Exception as e:
            logger.error(f"❌ [HIERARCHICAL_CHUNKS] Error creating hierarchical chunks: {e}")
            import traceback
            logger.error(f"❌ [HIERARCHICAL_CHUNKS] Traceback: {traceback.format_exc()}")
            # Fallback к простому разбиению
            return self._simple_split_into_chunks(text, chunk_size)

    def _standard_chunking(self, text: str, config: dict) -> List[str]:
        """Стандартное чанкование без иерархии"""
        try:
            # Параметры гранулярного чанкования из конфигурации
            target_tokens = config['target_tokens']
            min_tokens = config['min_tokens']
            max_tokens = config['max_tokens']
            overlap_ratio = config['overlap_ratio']
            
            logger.info(f"📝 [STANDARD_CHUNKING] Using config: target={target_tokens}, min={min_tokens}, max={max_tokens}, overlap={overlap_ratio}")
            
            # Разбиваем текст на предложения
            sentences = self._split_into_sentences(text, config)
            logger.info(f"📝 [STANDARD_CHUNKING] Split into {len(sentences)} sentences")
            
            if not sentences:
                logger.warning("⚠️ [STANDARD_CHUNKING] No sentences found, using fallback")
                return self._simple_split_into_chunks(text, 1000)
            
            chunks = []
            current_chunk = []
            current_tokens = 0
            
            # Обрабатываем каждое предложение
            for i, sentence in enumerate(sentences):
                sentence_tokens = self._estimate_tokens(sentence, config)
                
                # Проверяем, нужно ли начать новый чанк
                if current_tokens + sentence_tokens > max_tokens and current_chunk:
                    # Создаем чанк
                    chunk_text = ' '.join(current_chunk)
                    chunks.append(chunk_text.strip())
                    
                    # Начинаем новый чанк с перекрытием
                    overlap_sentences = self._get_overlap_sentences(current_chunk, overlap_ratio, config)
                    current_chunk = overlap_sentences
                    current_tokens = sum(self._estimate_tokens(s, config) for s in overlap_sentences)
                
                # Добавляем предложение к текущему чанку
                current_chunk.append(sentence)
                current_tokens += sentence_tokens
                
                # Проверяем, достигли ли целевого размера
                if current_tokens >= target_tokens and current_tokens >= min_tokens:
                    # Создаем чанк
                    chunk_text = ' '.join(current_chunk)
                    chunks.append(chunk_text.strip())
                    
                    # Начинаем новый чанк с перекрытием
                    overlap_sentences = self._get_overlap_sentences(current_chunk, overlap_ratio, config)
                    current_chunk = overlap_sentences
                    current_tokens = sum(self._estimate_tokens(s, config) for s in overlap_sentences)
            
            # Добавляем последний чанк, если он не пустой
            if current_chunk and current_tokens >= min_tokens:
                chunk_text = ' '.join(current_chunk)
                chunks.append(chunk_text.strip())
            elif current_chunk:
                if chunks:
                    # Объединяем с последним чанком
                    last_chunk = chunks[-1]
                    merged_chunk = last_chunk + ' ' + ' '.join(current_chunk)
                    chunks[-1] = merged_chunk
                else:
                    # Если нет предыдущих чанков, создаем один
                    chunk_text = ' '.join(current_chunk)
                    chunks.append(chunk_text.strip())
            
            logger.info(f"✅ [STANDARD_CHUNKING] Created {len(chunks)} standard chunks")
            return chunks
            
        except Exception as e:
            logger.error(f"❌ [STANDARD_CHUNKING] Error in standard chunking: {e}")
            return self._simple_split_into_chunks(text, 1000)

    def _create_semantic_chunks(self, text: str, config: dict) -> List[str]:
        """Создание семантических чанков на основе смысла"""
        try:
            logger.info("📝 [SEMANTIC_CHUNKS] Creating semantic chunks with meaning-based analysis")
            
            # Параметры семантического чанкования
            target_tokens = config['target_tokens']
            min_tokens = config['min_tokens']
            max_tokens = config['max_tokens']
            overlap_ratio = config['overlap_ratio']
            semantic_threshold = config.get('semantic_similarity_threshold', 0.7)
            window_size = config.get('semantic_window_size', 3)
            topic_change_threshold = config.get('topic_change_threshold', 0.3)
            
            # Разбиваем текст на предложения
            sentences = self._split_into_sentences(text, config)
            logger.info(f"📝 [SEMANTIC_CHUNKS] Split into {len(sentences)} sentences")
            
            if not sentences:
                logger.warning("⚠️ [SEMANTIC_CHUNKS] No sentences found")
                return []
            
            # Анализируем семантическую структуру
            semantic_analysis = self._analyze_semantic_structure(sentences, config)
            
            # Определяем границы семантических блоков
            semantic_boundaries = self._find_semantic_boundaries(sentences, semantic_analysis, config)
            
            # Создаем семантические чанки
            semantic_chunks = self._create_chunks_from_semantic_boundaries(
                sentences, semantic_boundaries, config
            )
            
            # Применяем семантическое объединение близких чанков
            if config.get('semantic_merge_threshold', 0.85) > 0:
                semantic_chunks = self._merge_semantically_similar_chunks(semantic_chunks, config)
            
            logger.info(f"✅ [SEMANTIC_CHUNKS] Created {len(semantic_chunks)} semantic chunks")
            return semantic_chunks
            
        except Exception as e:
            logger.error(f"❌ [SEMANTIC_CHUNKS] Error creating semantic chunks: {e}")
            return []

    def _analyze_semantic_structure(self, sentences: List[str], config: dict) -> Dict[str, Any]:
        """Анализ семантической структуры текста"""
        try:
            from config.chunking_config import get_semantic_patterns
            import re
            
            patterns = get_semantic_patterns()
            
            analysis = {
                'topic_indicators': [],
                'coherence_indicators': [],
                'semantic_boundaries': [],
                'domain_keywords': [],
                'sentence_semantics': []
            }
            
            for i, sentence in enumerate(sentences):
                sentence_analysis = {
                    'index': i,
                    'text': sentence,
                    'topic_indicators': [],
                    'coherence_indicators': [],
                    'semantic_boundaries': [],
                    'domain_keywords': [],
                    'semantic_score': 0.0
                }
                
                # Анализируем индикаторы тем
                for pattern in patterns['topic_indicators']:
                    if re.search(pattern, sentence, re.IGNORECASE):
                        sentence_analysis['topic_indicators'].append(pattern)
                        analysis['topic_indicators'].append(i)
                
                # Анализируем индикаторы связности
                for pattern in patterns['coherence_indicators']:
                    if re.search(pattern, sentence, re.IGNORECASE):
                        sentence_analysis['coherence_indicators'].append(pattern)
                        analysis['coherence_indicators'].append(i)
                
                # Анализируем семантические границы
                for pattern in patterns['semantic_boundaries']:
                    if re.search(pattern, sentence, re.IGNORECASE):
                        sentence_analysis['semantic_boundaries'].append(pattern)
                        analysis['semantic_boundaries'].append(i)
                
                # Анализируем доменные ключевые слова
                for domain, domain_patterns in patterns['domain_specific'].items():
                    for pattern in domain_patterns:
                        if re.search(pattern, sentence, re.IGNORECASE):
                            sentence_analysis['domain_keywords'].append((domain, pattern))
                            analysis['domain_keywords'].append((i, domain, pattern))
                
                # Вычисляем семантический балл предложения
                sentence_analysis['semantic_score'] = self._calculate_semantic_score(sentence_analysis)
                
                analysis['sentence_semantics'].append(sentence_analysis)
            
            logger.info(f"📝 [SEMANTIC_ANALYSIS] Found {len(analysis['topic_indicators'])} topic indicators, {len(analysis['semantic_boundaries'])} boundaries")
            return analysis
            
        except Exception as e:
            logger.error(f"❌ [SEMANTIC_ANALYSIS] Error analyzing semantic structure: {e}")
            return {'sentence_semantics': []}

    def _calculate_semantic_score(self, sentence_analysis: Dict[str, Any]) -> float:
        """Вычисление семантического балла предложения"""
        try:
            score = 0.0
            
            # Баллы за различные индикаторы
            score += len(sentence_analysis['topic_indicators']) * 0.3
            score += len(sentence_analysis['coherence_indicators']) * 0.2
            score += len(sentence_analysis['semantic_boundaries']) * 0.4
            score += len(sentence_analysis['domain_keywords']) * 0.1
            
            # Нормализуем до 0-1
            return min(score, 1.0)
            
        except Exception as e:
            logger.error(f"❌ [SEMANTIC_SCORE] Error calculating semantic score: {e}")
            return 0.0

    def _find_semantic_boundaries(self, sentences: List[str], analysis: Dict[str, Any], config: dict) -> List[int]:
        """Поиск семантических границ в тексте"""
        try:
            boundaries = []
            window_size = config.get('semantic_window_size', 3)
            topic_change_threshold = config.get('topic_change_threshold', 0.3)
            
            # Добавляем границы на основе семантических индикаторов
            for boundary_idx in analysis['semantic_boundaries']:
                if boundary_idx not in boundaries:
                    boundaries.append(boundary_idx)
            
            # Анализируем изменения темы в скользящем окне
            for i in range(window_size, len(sentences) - window_size):
                # Вычисляем семантическое сходство в окне
                window_similarity = self._calculate_window_similarity(
                    sentences, i, window_size, analysis
                )
                
                # Если сходство ниже порога, это граница
                if window_similarity < topic_change_threshold:
                    if i not in boundaries:
                        boundaries.append(i)
            
            # Сортируем границы
            boundaries.sort()
            
            logger.info(f"📝 [SEMANTIC_BOUNDARIES] Found {len(boundaries)} semantic boundaries")
            return boundaries
            
        except Exception as e:
            logger.error(f"❌ [SEMANTIC_BOUNDARIES] Error finding semantic boundaries: {e}")
            return []

    def _calculate_window_similarity(self, sentences: List[str], center_idx: int, window_size: int, analysis: Dict[str, Any]) -> float:
        """Вычисление семантического сходства в окне"""
        try:
            # Получаем предложения в окне
            start_idx = max(0, center_idx - window_size)
            end_idx = min(len(sentences), center_idx + window_size + 1)
            
            window_sentences = sentences[start_idx:end_idx]
            
            if len(window_sentences) < 2:
                return 1.0
            
            # Простой анализ сходства на основе ключевых слов
            similarity_scores = []
            
            for i in range(len(window_sentences) - 1):
                sent1 = window_sentences[i].lower()
                sent2 = window_sentences[i + 1].lower()
                
                # Извлекаем ключевые слова (простые существительные и прилагательные)
                words1 = set([w for w in sent1.split() if len(w) > 3 and w.isalpha()])
                words2 = set([w for w in sent2.split() if len(w) > 3 and w.isalpha()])
                
                if words1 and words2:
                    # Вычисляем коэффициент Жаккара
                    intersection = len(words1.intersection(words2))
                    union = len(words1.union(words2))
                    jaccard = intersection / union if union > 0 else 0.0
                    similarity_scores.append(jaccard)
            
            # Возвращаем среднее сходство
            return sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0.0
            
        except Exception as e:
            logger.error(f"❌ [WINDOW_SIMILARITY] Error calculating window similarity: {e}")
            return 0.0

    def _create_chunks_from_semantic_boundaries(self, sentences: List[str], boundaries: List[int], config: dict) -> List[str]:
        """Создание чанков на основе семантических границ"""
        try:
            chunks = []
            target_tokens = config['target_tokens']
            min_tokens = config['min_tokens']
            max_tokens = config['max_tokens']
            
            # Добавляем границы в начале и конце
            all_boundaries = [0] + boundaries + [len(sentences)]
            all_boundaries = sorted(list(set(all_boundaries)))
            
            for i in range(len(all_boundaries) - 1):
                start_idx = all_boundaries[i]
                end_idx = all_boundaries[i + 1]
                
                # Получаем предложения для чанка
                chunk_sentences = sentences[start_idx:end_idx]
                
                if not chunk_sentences:
                    continue
                
                # Создаем текст чанка
                chunk_text = ' '.join(chunk_sentences)
                chunk_tokens = self._estimate_tokens(chunk_text, config)
                
                # Проверяем размер чанка
                if chunk_tokens < min_tokens:
                    # Если чанк слишком мал, объединяем со следующим
                    if i + 2 < len(all_boundaries):
                        next_start = all_boundaries[i + 1]
                        next_end = all_boundaries[i + 2]
                        next_sentences = sentences[next_start:next_end]
                        chunk_sentences.extend(next_sentences)
                        chunk_text = ' '.join(chunk_sentences)
                        chunk_tokens = self._estimate_tokens(chunk_text, config)
                
                if chunk_tokens > max_tokens:
                    # Если чанк слишком большой, разбиваем на части
                    sub_chunks = self._split_large_chunk(chunk_sentences, config)
                    chunks.extend(sub_chunks)
                else:
                    chunks.append(chunk_text.strip())
            
            return chunks
            
        except Exception as e:
            logger.error(f"❌ [SEMANTIC_CHUNKS_CREATION] Error creating chunks from boundaries: {e}")
            return []

    def _split_large_chunk(self, sentences: List[str], config: dict) -> List[str]:
        """Разбиение большого чанка на меньшие части"""
        try:
            chunks = []
            target_tokens = config['target_tokens']
            max_tokens = config['max_tokens']
            
            current_chunk = []
            current_tokens = 0
            
            for sentence in sentences:
                sentence_tokens = self._estimate_tokens(sentence, config)
                
                if current_tokens + sentence_tokens > max_tokens and current_chunk:
                    # Создаем чанк
                    chunk_text = ' '.join(current_chunk)
                    chunks.append(chunk_text.strip())
                    
                    # Начинаем новый чанк
                    current_chunk = [sentence]
                    current_tokens = sentence_tokens
                else:
                    current_chunk.append(sentence)
                    current_tokens += sentence_tokens
            
            # Добавляем последний чанк
            if current_chunk:
                chunk_text = ' '.join(current_chunk)
                chunks.append(chunk_text.strip())
            
            return chunks
            
        except Exception as e:
            logger.error(f"❌ [SPLIT_LARGE_CHUNK] Error splitting large chunk: {e}")
            return []

    def _merge_semantically_similar_chunks(self, chunks: List[str], config: dict) -> List[str]:
        """Объединение семантически близких чанков"""
        try:
            merge_threshold = config.get('semantic_merge_threshold', 0.85)
            
            if len(chunks) <= 1:
                return chunks
            
            merged_chunks = []
            i = 0
            
            while i < len(chunks):
                current_chunk = chunks[i]
                merged_chunk = current_chunk
                
                # Проверяем сходство со следующими чанками
                j = i + 1
                while j < len(chunks):
                    next_chunk = chunks[j]
                    
                    # Вычисляем семантическое сходство
                    similarity = self._calculate_chunk_similarity(current_chunk, next_chunk)
                    
                    if similarity >= merge_threshold:
                        # Объединяем чанки
                        merged_chunk += ' ' + next_chunk
                        j += 1
                    else:
                        break
                
                merged_chunks.append(merged_chunk.strip())
                i = j
            
            logger.info(f"📝 [SEMANTIC_MERGE] Merged {len(chunks)} chunks into {len(merged_chunks)} chunks")
            return merged_chunks
            
        except Exception as e:
            logger.error(f"❌ [SEMANTIC_MERGE] Error merging similar chunks: {e}")
            return chunks

    def _calculate_chunk_similarity(self, chunk1: str, chunk2: str) -> float:
        """Вычисление семантического сходства между чанками"""
        try:
            # Простой анализ сходства на основе ключевых слов
            words1 = set([w.lower() for w in chunk1.split() if len(w) > 3 and w.isalpha()])
            words2 = set([w.lower() for w in chunk2.split() if len(w) > 3 and w.isalpha()])
            
            if not words1 or not words2:
                return 0.0
            
            # Вычисляем коэффициент Жаккара
            intersection = len(words1.intersection(words2))
            union = len(words1.union(words2))
            
            return intersection / union if union > 0 else 0.0
            
        except Exception as e:
            logger.error(f"❌ [CHUNK_SIMILARITY] Error calculating chunk similarity: {e}")
            return 0.0

    def _create_hierarchical_chunks(self, text: str, structure: Dict[str, Any], config: dict) -> List[str]:
        """Создание иерархических чанков с сохранением структуры"""
        try:
            logger.info("📝 [HIERARCHICAL_CHUNKS] Creating hierarchical chunks with structure preservation")
            
            # Параметры чанкования
            target_tokens = config['target_tokens']
            min_tokens = config['min_tokens']
            max_tokens = config['max_tokens']
            overlap_ratio = config['overlap_ratio']
            preserve_structure = config.get('preserve_structure', True)
            chapter_boundaries = config.get('chapter_boundaries', True)
            section_boundaries = config.get('section_boundaries', True)
            
            chunks = []
            
            # Если нет структуры, используем стандартное чанкование
            if not structure['chapters'] and not structure['sections']:
                logger.info("📝 [HIERARCHICAL_CHUNKS] No structure found, using standard chunking")
                return self._standard_chunking(text, config)
            
            # Разбиваем текст на предложения
            sentences = self._split_into_sentences(text, config)
            logger.info(f"📝 [HIERARCHICAL_CHUNKS] Split into {len(sentences)} sentences")
            
            if not sentences:
                logger.warning("⚠️ [HIERARCHICAL_CHUNKS] No sentences found")
                return []
            
            # Создаем карту предложений к структуре
            sentence_structure_map = self._map_sentences_to_structure(sentences, structure)
            
            # Группируем предложения по структурным единицам
            structural_units = self._group_sentences_by_structure(sentences, sentence_structure_map, structure)
            
            # Создаем чанки с учетом структуры
            for unit in structural_units:
                unit_chunks = self._create_chunks_for_structural_unit(unit, config)
                chunks.extend(unit_chunks)
            
            logger.info(f"✅ [HIERARCHICAL_CHUNKS] Created {len(chunks)} hierarchical chunks")
            return chunks
            
        except Exception as e:
            logger.error(f"❌ [HIERARCHICAL_CHUNKS] Error creating hierarchical chunks: {e}")
            return []

    def _map_sentences_to_structure(self, sentences: List[str], structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Создание карты предложений к структурным элементам"""
        try:
            sentence_map = []
            
            for i, sentence in enumerate(sentences):
                sentence_info = {
                    'index': i,
                    'text': sentence,
                    'chapter': None,
                    'section': None,
                    'subsection': None,
                    'paragraph': None,
                    'special_structure': None
                }
                
                # Определяем принадлежность к главе
                for chapter in structure['chapters']:
                    if chapter['title'].lower() in sentence.lower() or chapter['number'] in sentence:
                        sentence_info['chapter'] = chapter
                        break
                
                # Определяем принадлежность к разделу
                for section in structure['sections']:
                    if section['number'] in sentence or section['title'].lower() in sentence.lower():
                        sentence_info['section'] = section
                        break
                
                # Определяем принадлежность к абзацу
                for paragraph in structure['paragraphs']:
                    if paragraph['text'].lower() in sentence.lower():
                        sentence_info['paragraph'] = paragraph
                        break
                
                # Определяем принадлежность к специальной структуре
                for special in structure['special_structures']:
                    if special['text'].lower() in sentence.lower():
                        sentence_info['special_structure'] = special
                        break
                
                sentence_map.append(sentence_info)
            
            return sentence_map
            
        except Exception as e:
            logger.error(f"❌ [MAP_SENTENCES] Error mapping sentences to structure: {e}")
            return []

    def _group_sentences_by_structure(self, sentences: List[str], sentence_map: List[Dict[str, Any]], structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Группировка предложений по структурным единицам"""
        try:
            structural_units = []
            current_unit = None
            
            for i, sentence_info in enumerate(sentence_map):
                # Определяем текущую структурную единицу
                current_chapter = sentence_info.get('chapter')
                current_section = sentence_info.get('section')
                current_paragraph = sentence_info.get('paragraph')
                current_special = sentence_info.get('special_structure')
                
                # Проверяем, нужно ли начать новую структурную единицу
                should_start_new_unit = False
                
                if current_unit is None:
                    should_start_new_unit = True
                elif current_chapter and current_chapter != current_unit.get('chapter'):
                    should_start_new_unit = True
                elif current_section and current_section != current_unit.get('section'):
                    should_start_new_unit = True
                elif current_special and current_special != current_unit.get('special_structure'):
                    should_start_new_unit = True
                
                if should_start_new_unit:
                    # Сохраняем предыдущую единицу
                    if current_unit:
                        structural_units.append(current_unit)
                    
                    # Начинаем новую единицу
                    current_unit = {
                        'chapter': current_chapter,
                        'section': current_section,
                        'paragraph': current_paragraph,
                        'special_structure': current_special,
                        'sentences': [sentence_info['text']],
                        'start_index': i,
                        'end_index': i
                    }
                else:
                    # Добавляем предложение к текущей единице
                    current_unit['sentences'].append(sentence_info['text'])
                    current_unit['end_index'] = i
            
            # Добавляем последнюю единицу
            if current_unit:
                structural_units.append(current_unit)
            
            logger.info(f"📝 [GROUP_SENTENCES] Created {len(structural_units)} structural units")
            return structural_units
            
        except Exception as e:
            logger.error(f"❌ [GROUP_SENTENCES] Error grouping sentences: {e}")
            return []

    def _create_chunks_for_structural_unit(self, unit: Dict[str, Any], config: dict) -> List[str]:
        """Создание чанков для структурной единицы"""
        try:
            sentences = unit['sentences']
            if not sentences:
                return []
            
            # Параметры чанкования
            target_tokens = config['target_tokens']
            min_tokens = config['min_tokens']
            max_tokens = config['max_tokens']
            overlap_ratio = config['overlap_ratio']
            
            chunks = []
            current_chunk = []
            current_tokens = 0
            
            # Обрабатываем предложения структурной единицы
            for sentence in sentences:
                sentence_tokens = self._estimate_tokens(sentence, config)
                
                # Проверяем, нужно ли начать новый чанк
                if current_tokens + sentence_tokens > max_tokens and current_chunk:
                    # Создаем чанк
                    chunk_text = ' '.join(current_chunk)
                    chunks.append(chunk_text.strip())
                    
                    # Начинаем новый чанк с перекрытием
                    overlap_sentences = self._get_overlap_sentences(current_chunk, overlap_ratio, config)
                    current_chunk = overlap_sentences
                    current_tokens = sum(self._estimate_tokens(s, config) for s in overlap_sentences)
                
                # Добавляем предложение к текущему чанку
                current_chunk.append(sentence)
                current_tokens += sentence_tokens
                
                # Проверяем, достигли ли целевого размера
                if current_tokens >= target_tokens and current_tokens >= min_tokens:
                    # Создаем чанк
                    chunk_text = ' '.join(current_chunk)
                    chunks.append(chunk_text.strip())
                    
                    # Начинаем новый чанк с перекрытием
                    overlap_sentences = self._get_overlap_sentences(current_chunk, overlap_ratio, config)
                    current_chunk = overlap_sentences
                    current_tokens = sum(self._estimate_tokens(s, config) for s in overlap_sentences)
            
            # Добавляем последний чанк, если он не пустой
            if current_chunk and current_tokens >= min_tokens:
                chunk_text = ' '.join(current_chunk)
                chunks.append(chunk_text.strip())
            elif current_chunk:
                if chunks:
                    # Объединяем с последним чанком
                    last_chunk = chunks[-1]
                    merged_chunk = last_chunk + ' ' + ' '.join(current_chunk)
                    chunks[-1] = merged_chunk
                else:
                    # Если нет предыдущих чанков, создаем один
                    chunk_text = ' '.join(current_chunk)
                    chunks.append(chunk_text.strip())
            
            return chunks
            
        except Exception as e:
            logger.error(f"❌ [CREATE_CHUNKS_FOR_UNIT] Error creating chunks for structural unit: {e}")
            return []

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
            # Получаем метаданные документа
            logger.info(f"🔍 [INDEX_CHUNKS_ASYNC] Getting metadata for document_id: {document_id}")
            document_metadata = self._get_document_metadata(document_id)
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
                chunk_metadata = self._create_chunk_metadata(chunk, document_metadata)
                
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
    
    def _extract_page_structure(self, page_text: str, page_num: int) -> Dict[str, Any]:
        """Извлечение структуры страницы (главы, разделы)"""
        try:
            structure = {
                'page': page_num,
                'chapters': [],
                'sections': [],
                'headers': []
            }
            
            # Паттерны для поиска заголовков глав и разделов
            chapter_patterns = [
                r'^ГЛАВА\s+(\d+)\s*[\.\-]?\s*(.+)$',
                r'^Глава\s+(\d+)\s*[\.\-]?\s*(.+)$',
                r'^РАЗДЕЛ\s+(\d+)\s*[\.\-]?\s*(.+)$',
                r'^Раздел\s+(\d+)\s*[\.\-]?\s*(.+)$',
                r'^ЧАСТЬ\s+(\d+)\s*[\.\-]?\s*(.+)$',
                r'^Часть\s+(\d+)\s*[\.\-]?\s*(.+)$'
            ]
            
            section_patterns = [
                r'^(\d+\.\d+)\s+(.+)$',
                r'^(\d+\.\d+\.\d+)\s+(.+)$',
                r'^(\d+\.\d+\.\d+\.\d+)\s+(.+)$',
                r'^(\d+)\s+(.+)$'
            ]
            
            lines = page_text.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Проверяем паттерны глав
                for pattern in chapter_patterns:
                    match = re.match(pattern, line, re.IGNORECASE)
                    if match:
                        structure['chapters'].append({
                            'number': match.group(1),
                            'title': match.group(2).strip(),
                            'line': line
                        })
                        break
                
                # Проверяем паттерны разделов
                for pattern in section_patterns:
                    match = re.match(pattern, line)
                    if match:
                        structure['sections'].append({
                            'number': match.group(1),
                            'title': match.group(2).strip(),
                            'line': line
                        })
                        break
                
                # Проверяем на заголовки (строки в верхнем регистре)
                if line.isupper() and len(line) > 5 and len(line) < 100:
                    structure['headers'].append(line)
            
            return structure
            
        except Exception as e:
            logger.error(f"❌ [EXTRACT_PAGE_STRUCTURE] Error extracting page structure: {e}")
            return {'page': page_num, 'chapters': [], 'sections': [], 'headers': []}
    
    def _extract_document_structure(self, text: str) -> Dict[str, Any]:
        """Извлечение общей структуры документа с улучшенной иерархией"""
        try:
            # Импортируем улучшенные паттерны
            from config.chunking_config import get_hierarchical_patterns
            
            structure = {
                'chapters': [],
                'sections': [],
                'paragraphs': [],
                'special_structures': [],
                'headers': []
            }
            
            # Получаем улучшенные паттерны
            patterns = get_hierarchical_patterns()
            chapter_patterns = patterns['chapters']
            section_patterns = patterns['sections']
            paragraph_patterns = patterns['paragraphs']
            special_patterns = patterns['special_structures']
            
            lines = text.split('\n')
            current_chapter = None
            current_section = None
            
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line:
                    continue
                
                # Проверяем паттерны глав
                for pattern in chapter_patterns:
                    match = re.match(pattern, line, re.IGNORECASE)
                    if match:
                        current_chapter = {
                            'number': match.group(1),
                            'title': match.group(2).strip(),
                            'line': line_num,
                            'level': 1
                        }
                        structure['chapters'].append(current_chapter)
                        current_section = None
                        break
                
                # Проверяем паттерны разделов
                for pattern in section_patterns:
                    match = re.match(pattern, line)
                    if match:
                        section_number = match.group(1)
                        section_title = match.group(2).strip()
                        
                        # Определяем уровень вложенности
                        level = len(section_number.split('.'))
                        
                        current_section = {
                            'number': section_number,
                            'title': section_title,
                            'line': line_num,
                            'level': level,
                            'chapter': current_chapter['number'] if current_chapter else None
                        }
                        structure['sections'].append(current_section)
                        break
                
                # Проверяем паттерны абзацев
                for pattern in paragraph_patterns:
                    match = re.match(pattern, line)
                    if match:
                        paragraph = {
                            'text': match.group(1).strip(),
                            'line': line_num,
                            'section': current_section['number'] if current_section else None,
                            'chapter': current_chapter['number'] if current_chapter else None
                        }
                        structure['paragraphs'].append(paragraph)
                        break
                
                # Проверяем специальные структуры
                for pattern in special_patterns:
                    match = re.match(pattern, line, re.IGNORECASE)
                    if match:
                        special = {
                            'type': 'table' if 'Таблица' in line else 'figure' if 'Рисунок' in line else 'appendix' if 'Приложение' in line else 'other',
                            'number': match.group(1) if match.groups() else None,
                            'line': line_num,
                            'text': line
                        }
                        structure['special_structures'].append(special)
                        break
            
            return structure
            
        except Exception as e:
            logger.error(f"❌ [EXTRACT_DOCUMENT_STRUCTURE] Error extracting document structure: {e}")
            return {'chapters': [], 'sections': [], 'paragraphs': [], 'special_structures': [], 'headers': []}
    
    def _identify_chunk_structure(self, chunk_text: str, structure: Dict[str, Any]) -> Dict[str, str]:
        """Определение к какой главе/разделу относится чанк"""
        try:
            result = {'chapter': '', 'section': ''}
            
            if not structure or not chunk_text:
                return result
            
            # Ищем ближайший заголовок раздела в чанке
            section_patterns = [
                r'(\d+\.\d+\.\d+\.\d+)\s+(.+)',
                r'(\d+\.\d+\.\d+)\s+(.+)',
                r'(\d+\.\d+)\s+(.+)',
                r'(\d+)\s+(.+)'
            ]
            
            for pattern in section_patterns:
                match = re.search(pattern, chunk_text)
                if match:
                    section_number = match.group(1)
                    section_title = match.group(2).strip()
                    
                    # Ищем соответствующую главу
                    chapter_num = section_number.split('.')[0]
                    for chapter in structure.get('chapters', []):
                        if chapter['number'] == chapter_num:
                            result['chapter'] = f"Глава {chapter_num}. {chapter['title']}"
                            break
                    
                    result['section'] = f"{section_number}. {section_title}"
                    break
            
            # Если не нашли раздел, ищем главу
            if not result['section']:
                chapter_patterns = [
                    r'ГЛАВА\s+(\d+)\s*[\.\-]?\s*(.+)',
                    r'Глава\s+(\d+)\s*[\.\-]?\s*(.+)',
                    r'РАЗДЕЛ\s+(\d+)\s*[\.\-]?\s*(.+)',
                    r'Раздел\s+(\d+)\s*[\.\-]?\s*(.+)'
                ]
                
                for pattern in chapter_patterns:
                    match = re.search(pattern, chunk_text, re.IGNORECASE)
                    if match:
                        chapter_num = match.group(1)
                        chapter_title = match.group(2).strip()
                        result['chapter'] = f"Глава {chapter_num}. {chapter_title}"
                        break
            
            return result
            
        except Exception as e:
            logger.error(f"❌ [IDENTIFY_CHUNK_STRUCTURE] Error identifying chunk structure: {e}")
            return {'chapter': '', 'section': ''}
    
    def _extract_document_metadata(self, filename: str, document_id: int, file_path: str = None) -> Dict[str, Any]:
        """Извлечение метаданных документа из названия файла"""
        try:
            import hashlib
            from datetime import datetime
            
            logger.info(f"🔍 [EXTRACT_DOCUMENT_METADATA] Called with: filename='{filename}', document_id={document_id}, file_path='{file_path}'")
            
            # Базовые метаданные
            metadata = {
                "doc_id": f"doc_{document_id}",
                "doc_type": "OTHER",
                "doc_number": "",
                "doc_title": filename,
                "edition_year": None,
                "status": "unknown",
                "replaced_by": None,
                "section": None,
                "paragraph": None,
                "page": None,
                "source_path": file_path or "",
                "source_url": None,
                "ingested_at": datetime.now().strftime("%Y-%m-%d"),
                "lang": "ru",
                "tags": [],
                "checksum": ""
            }
            
            # Извлекаем тип документа и номер
            logger.info(f"🔍 [EXTRACT_DOCUMENT_METADATA] Parsing filename: '{filename}'")
            doc_type, doc_number, edition_year = self._parse_document_name(filename)
            logger.info(f"🔍 [EXTRACT_DOCUMENT_METADATA] Parsed: doc_type='{doc_type}', doc_number='{doc_number}', edition_year='{edition_year}'")
            metadata["doc_type"] = doc_type
            metadata["doc_number"] = doc_number
            metadata["edition_year"] = edition_year
            
            # Генерируем уникальный doc_id
            if doc_number and edition_year:
                metadata["doc_id"] = f"{doc_type.lower()}_{doc_number}_{edition_year}"
            
            # Определяем статус документа
            metadata["status"] = self._determine_document_status(filename, doc_type, doc_number)
            
            # Извлекаем теги на основе типа документа
            metadata["tags"] = self._extract_document_tags(doc_type, doc_number, filename)
            
            # Вычисляем checksum если есть путь к файлу
            if file_path:
                metadata["checksum"] = self._calculate_file_checksum(file_path)
            
            return metadata
            
        except Exception as e:
            logger.error(f"❌ [EXTRACT_DOCUMENT_METADATA] Error extracting metadata: {e}")
            return {
                "doc_id": f"doc_{document_id}",
                "doc_type": "OTHER",
                "doc_number": "",
                "doc_title": filename,
                "edition_year": None,
                "status": "unknown",
                "replaced_by": None,
                "section": None,
                "paragraph": None,
                "page": None,
                "source_path": file_path or "",
                "source_url": None,
                "ingested_at": datetime.now().strftime("%Y-%m-%d"),
                "lang": "ru",
                "tags": [],
                "checksum": ""
            }
    
    def _parse_document_name(self, filename: str) -> tuple[str, str, int]:
        """Парсинг названия документа для извлечения типа, номера и года"""
        try:
            import re
            
            # Убираем расширение файла
            name = filename.replace('.pdf', '').replace('.docx', '').replace('.doc', '')
            
            # Паттерны для различных типов документов
            patterns = [
                # ГОСТ
                (r'ГОСТ\s+(\d+(?:\.\d+)*)-(\d{4})', 'GOST'),
                (r'ГОСТ\s+(\d+(?:\.\d+)*)', 'GOST'),
                
                # СП (Свод правил)
                (r'СП\s+(\d+(?:\.\d+)*)\.(\d{4})', 'SP'),
                (r'СП\s+(\d+(?:\.\d+)*)', 'SP'),
                
                # СНиП
                (r'СНиП\s+(\d+(?:\.\d+)*)-(\d{4})', 'SNiP'),
                (r'СНиП\s+(\d+(?:\.\d+)*)\.(\d{4})', 'SNiP'),
                (r'СНиП\s+(\d+(?:\.\d+)*)-(\d{2})(?:\.|$)', 'SNiP'),
                (r'СНиП\s+(\d+(?:\.\d+)*)', 'SNiP'),
                
                # ФНП
                (r'ФНП\s+(\d+(?:\.\d+)*)-(\d{4})', 'FNP'),
                (r'ФНП\s+(\d+(?:\.\d+)*)', 'FNP'),
                
                # ПБ (Правила безопасности)
                (r'ПБ\s+(\d+(?:\.\d+)*)-(\d{4})', 'CORP_STD'),
                (r'ПБ\s+(\d+(?:\.\d+)*)', 'CORP_STD'),
                
                # А (Альбом)
                (r'А(\d+(?:\.\d+)*)\.(\d{4})', 'CORP_STD'),
                (r'А(\d+(?:\.\d+)*)', 'CORP_STD'),
            ]
            
            for pattern, doc_type in patterns:
                match = re.search(pattern, name, re.IGNORECASE)
                if match:
                    groups = match.groups()
                    if len(groups) == 2:
                        # Есть год
                        doc_number = groups[0]
                        year_str = groups[1]
                        # Если год двухзначный, добавляем 19 или 20
                        if len(year_str) == 2:
                            year_int = int(year_str)
                            if year_int >= 0 and year_int <= 30:  # 2000-2030
                                edition_year = 2000 + year_int
                            else:  # 1930-1999
                                edition_year = 1900 + year_int
                        else:
                            edition_year = int(year_str)
                        return doc_type, doc_number, edition_year
                    else:
                        # Нет года, пытаемся найти его отдельно
                        doc_number = groups[0]
                        year_match = re.search(r'(\d{4})', name)
                        edition_year = int(year_match.group(1)) if year_match else None
                        return doc_type, doc_number, edition_year
            
            # Если не нашли стандартный паттерн, пытаемся извлечь год
            year_match = re.search(r'(\d{4})', name)
            edition_year = int(year_match.group(1)) if year_match else None
            
            return "OTHER", "", edition_year
            
        except Exception as e:
            logger.error(f"❌ [PARSE_DOCUMENT_NAME] Error parsing document name: {e}")
            return "OTHER", "", None
    
    def _determine_document_status(self, filename: str, doc_type: str, doc_number: str) -> str:
        """Определение статуса документа"""
        try:
            # Ключевые слова для определения статуса
            if any(word in filename.lower() for word in ['отменен', 'отменен', 'недействителен', 'repealed']):
                return "repealed"
            elif any(word in filename.lower() for word in ['заменен', 'заменяет', 'replaced', 'изм']):
                return "replaced"
            elif any(word in filename.lower() for word in ['действующий', 'актуальный', 'active']):
                return "active"
            else:
                return "unknown"
                
        except Exception as e:
            logger.error(f"❌ [DETERMINE_DOCUMENT_STATUS] Error determining status: {e}")
            return "unknown"
    
    def _extract_document_tags(self, doc_type: str, doc_number: str, filename: str) -> List[str]:
        """Извлечение тегов на основе типа и содержания документа"""
        try:
            tags = []
            
            # Теги на основе типа документа
            type_tags = {
                "GOST": ["государственный стандарт", "гост"],
                "SP": ["свод правил", "строительство"],
                "SNiP": ["строительные нормы", "строительство"],
                "FNP": ["федеральные нормы", "промышленность"],
                "CORP_STD": ["корпоративный стандарт", "внутренний стандарт"]
            }
            
            if doc_type in type_tags:
                tags.extend(type_tags[doc_type])
            
            # Теги на основе содержания в названии
            content_keywords = {
                "электр": ["электроснабжение", "электротехника"],
                "пожар": ["пожарная безопасность", "пожар"],
                "строит": ["строительство", "конструкции"],
                "безопасн": ["охрана труда", "безопасность"],
                "проект": ["проектирование", "проектная документация"],
                "конструкц": ["конструкции", "строительные конструкции"],
                "стальн": ["стальные конструкции", "металлоконструкции"],
                "документац": ["документооборот", "документация"]
            }
            
            filename_lower = filename.lower()
            for keyword, tag_list in content_keywords.items():
                if keyword in filename_lower:
                    tags.extend(tag_list)
            
            # Убираем дубликаты
            return list(set(tags))
            
        except Exception as e:
            logger.error(f"❌ [EXTRACT_DOCUMENT_TAGS] Error extracting tags: {e}")
            return []
    
    def _calculate_file_checksum(self, file_path: str) -> str:
        """Вычисление SHA256 checksum файла"""
        try:
            import hashlib
            
            hash_sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
            
        except Exception as e:
            logger.error(f"❌ [CALCULATE_FILE_CHECKSUM] Error calculating checksum: {e}")
            return ""
    
    def _get_document_metadata(self, document_id: int) -> Dict[str, Any]:
        """Получение метаданных документа из базы данных"""
        try:
            with self.db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT id, filename, original_filename, file_path, document_hash, document_type
                    FROM uploaded_documents 
                    WHERE id = %s
                """, (document_id,))
                
                result = cursor.fetchone()
                if result:
                    logger.info(f"🔍 [GET_DOCUMENT_METADATA] Raw result: {result}")
                    logger.info(f"🔍 [GET_DOCUMENT_METADATA] Result type: {type(result)}")
                    logger.info(f"🔍 [GET_DOCUMENT_METADATA] Result length: {len(result) if result else 0}")
                    
                    # Проверяем, что result - это кортеж
                    if isinstance(result, tuple) and len(result) >= 6:
                        doc_id, filename, original_filename, file_path, document_hash, document_type = result
                        logger.info(f"🔍 [GET_DOCUMENT_METADATA] Retrieved from DB: doc_id={doc_id}, filename={filename}, original_filename={original_filename}, file_path={file_path}")
                        # Используем original_filename для извлечения метаданных
                        return self._extract_document_metadata(original_filename, doc_id, file_path)
                    else:
                        logger.error(f"❌ [GET_DOCUMENT_METADATA] Invalid result format: {result}")
                        return self._extract_document_metadata(f"error_doc_{document_id}", document_id)
                else:
                    logger.warning(f"⚠️ [GET_DOCUMENT_METADATA] Document {document_id} not found")
                    return self._extract_document_metadata(f"unknown_doc_{document_id}", document_id)
                    
        except Exception as e:
            logger.error(f"❌ [GET_DOCUMENT_METADATA] Error getting document metadata: {e}")
            return self._extract_document_metadata(f"error_doc_{document_id}", document_id)
    
    def _create_chunk_metadata(self, chunk: Dict[str, Any], document_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Создание метаданных для чанка на основе метаданных документа"""
        try:
            # Копируем метаданные документа
            chunk_metadata = document_metadata.copy()
            
            # Обновляем специфичные для чанка поля
            chunk_metadata.update({
                "section": chunk.get('section', ''),
                "paragraph": self._extract_paragraph_from_chunk(chunk.get('content', '')),
                "page": chunk.get('page', 1),
                "chunk_id": chunk.get('chunk_id', ''),
                "chunk_type": chunk.get('chunk_type', 'paragraph')
            })
            
            return chunk_metadata
            
        except Exception as e:
            logger.error(f"❌ [CREATE_CHUNK_METADATA] Error creating chunk metadata: {e}")
            return document_metadata
    
    def _extract_paragraph_from_chunk(self, content: str) -> str:
        """Извлечение номера параграфа из содержимого чанка"""
        try:
            import re
            
            # Паттерны для поиска номеров параграфов
            paragraph_patterns = [
                r'(\d+\.\d+\.\d+\.\d+)',  # 5.2.1.1
                r'(\d+\.\d+\.\d+)',       # 5.2.1
                r'(\d+\.\d+)',            # 5.2
                r'п\.\s*(\d+\.\d+)',      # п.5.2
                r'пункт\s*(\d+\.\d+)',    # пункт 5.2
            ]
            
            for pattern in paragraph_patterns:
                match = re.search(pattern, content)
                if match:
                    return match.group(1)
            
            return ""
            
        except Exception as e:
            logger.error(f"❌ [EXTRACT_PARAGRAPH_FROM_CHUNK] Error extracting paragraph: {e}")
            return ""
