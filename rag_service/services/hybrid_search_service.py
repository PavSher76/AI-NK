"""
Сервис гибридного поиска с BM25 + Dense поиском, Alpha смешиванием и Reciprocal Rank Fusion
"""

import logging
import math
import re
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter, defaultdict
import numpy as np
from dataclasses import dataclass
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    """Результат поиска с метаданными"""
    id: str
    score: float
    document_id: str
    chunk_id: str
    code: str
    document_title: str
    section_title: str
    content: str
    chunk_type: str
    page: int
    section: str
    metadata: Dict[str, Any]
    search_type: str  # 'bm25', 'dense', 'hybrid'
    rank: int = 0

class BM25Search:
    """Реализация BM25 поиска"""
    
    def __init__(self, k1: float = 1.2, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.doc_freqs = defaultdict(int)
        self.idf = {}
        self.doc_len = {}
        self.avgdl = 0
        self.corpus_size = 0
        self.doc_freqs = defaultdict(int)
        self.freqs = defaultdict(dict)
        
    def _tokenize(self, text: str) -> List[str]:
        """Токенизация текста с учетом русского языка"""
        # Удаляем пунктуацию и приводим к нижнему регистру
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        # Разбиваем на слова
        tokens = text.split()
        # Фильтруем короткие слова и стоп-слова
        stop_words = {'и', 'в', 'на', 'с', 'по', 'для', 'от', 'до', 'из', 'к', 'о', 'у', 'за', 'при', 'без', 'через', 'над', 'под', 'между', 'среди', 'вокруг', 'около', 'близ', 'далеко', 'здесь', 'там', 'где', 'когда', 'как', 'что', 'кто', 'который', 'это', 'тот', 'этот', 'такой', 'какой', 'весь', 'все', 'вся', 'всё', 'каждый', 'любой', 'другой', 'иной', 'сам', 'сама', 'само', 'сами', 'себя', 'себе', 'собой', 'мой', 'моя', 'моё', 'мои', 'твой', 'твоя', 'твоё', 'твои', 'его', 'её', 'их', 'наш', 'наша', 'наше', 'наши', 'ваш', 'ваша', 'ваше', 'ваши'}
        return [token for token in tokens if len(token) > 2 and token not in stop_words]
    
    def fit(self, documents: List[Dict[str, Any]]):
        """Обучение BM25 на корпусе документов"""
        logger.info(f"🔍 [BM25] Training BM25 on {len(documents)} documents")
        
        self.corpus_size = len(documents)
        self.doc_freqs = defaultdict(int)
        self.freqs = defaultdict(dict)
        self.doc_len = {}
        
        # Собираем статистики
        for doc in documents:
            doc_id = doc['chunk_id']
            content = doc.get('content', '')
            tokens = self._tokenize(content)
            
            self.doc_len[doc_id] = len(tokens)
            self.freqs[doc_id] = Counter(tokens)
            
            # Подсчитываем частоту документов для каждого термина
            for token in set(tokens):
                self.doc_freqs[token] += 1
        
        # Вычисляем среднюю длину документа
        self.avgdl = sum(self.doc_len.values()) / len(self.doc_len) if self.doc_len else 0
        
        # Вычисляем IDF для каждого термина
        for term, freq in self.doc_freqs.items():
            self.idf[term] = math.log((self.corpus_size - freq + 0.5) / (freq + 0.5))
        
        logger.info(f"✅ [BM25] Training completed. Corpus size: {self.corpus_size}, avg doc length: {self.avgdl:.2f}")
    
    def search(self, query: str, documents: List[Dict[str, Any]], k: int = 10) -> List[SearchResult]:
        """Поиск по запросу"""
        query_tokens = self._tokenize(query)
        scores = {}
        
        for doc in documents:
            doc_id = doc['chunk_id']
            score = 0
            
            for token in query_tokens:
                if token in self.freqs[doc_id]:
                    tf = self.freqs[doc_id][token]
                    idf = self.idf.get(token, 0)
                    
                    # Формула BM25
                    score += idf * (tf * (self.k1 + 1)) / (tf + self.k1 * (1 - self.b + self.b * (self.doc_len[doc_id] / self.avgdl)))
            
            if score > 0:
                scores[doc_id] = score
        
        # Сортируем по убыванию score
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        # Формируем результаты
        results = []
        for rank, (doc_id, score) in enumerate(sorted_scores[:k]):
            doc = next((d for d in documents if d['chunk_id'] == doc_id), None)
            if doc:
                result = SearchResult(
                    id=doc_id,
                    score=score,
                    document_id=doc.get('document_id', ''),
                    chunk_id=doc.get('chunk_id', ''),
                    code=doc.get('code', ''),
                    document_title=doc.get('document_title', ''),
                    section_title=doc.get('section_title', ''),
                    content=doc.get('content', ''),
                    chunk_type=doc.get('chunk_type', ''),
                    page=doc.get('page', 0),
                    section=doc.get('section', ''),
                    metadata=doc.get('metadata', {}),
                    search_type='bm25',
                    rank=rank + 1
                )
                results.append(result)
        
        logger.info(f"✅ [BM25] Found {len(results)} results for query: '{query}'")
        return results

class DenseSearch:
    """Dense поиск с использованием векторных эмбеддингов"""
    
    def __init__(self, embedding_service, qdrant_service):
        self.embedding_service = embedding_service
        self.qdrant_service = qdrant_service
    
    def search(self, query: str, k: int = 10, filters: Optional[Dict] = None) -> List[SearchResult]:
        """Dense поиск по векторным эмбеддингам"""
        try:
            logger.info(f"🔍 [DENSE] Performing dense search for query: '{query}' with k={k}")
            
            # Создаем эмбеддинг для запроса
            query_embedding = self.embedding_service.create_embedding(query)
            
            # Выполняем поиск в Qdrant
            search_result = self.qdrant_service.search_similar(
                query_vector=query_embedding,
                limit=k,
                filters=filters
            )
            
            # Формируем результаты
            results = []
            for rank, point in enumerate(search_result):
                result = SearchResult(
                    id=str(point['id']),
                    score=point['score'],
                    document_id=point['payload'].get('document_id', ''),
                    chunk_id=point['payload'].get('chunk_id', ''),
                    code=point['payload'].get('code', ''),
                    document_title=point['payload'].get('title', ''),
                    section_title=point['payload'].get('section_title', ''),
                    content=point['payload'].get('content', ''),
                    chunk_type=point['payload'].get('chunk_type', ''),
                    page=point['payload'].get('page', 0),
                    section=point['payload'].get('section', ''),
                    metadata=point['payload'].get('metadata', {}),
                    search_type='dense',
                    rank=rank + 1
                )
                results.append(result)
            
            logger.info(f"✅ [DENSE] Found {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"❌ [DENSE] Error during dense search: {e}")
            return []

class AlphaBlending:
    """Alpha смешивание результатов BM25 и Dense поиска"""
    
    def __init__(self, alpha: float = 0.5):
        self.alpha = alpha  # Вес для dense поиска, (1-alpha) для BM25
    
    def blend_scores(self, bm25_results: List[SearchResult], dense_results: List[SearchResult]) -> List[SearchResult]:
        """Смешивание результатов с alpha весами"""
        logger.info(f"🔄 [ALPHA] Blending results with alpha={self.alpha}")
        
        # Нормализуем scores для каждого типа поиска
        bm25_scores = [r.score for r in bm25_results]
        dense_scores = [r.score for r in dense_results]
        
        if bm25_scores:
            bm25_max = max(bm25_scores)
            bm25_min = min(bm25_scores)
            bm25_range = bm25_max - bm25_min if bm25_max != bm25_min else 1
        else:
            bm25_max = bm25_min = bm25_range = 1
        
        if dense_scores:
            dense_max = max(dense_scores)
            dense_min = min(dense_scores)
            dense_range = dense_max - dense_min if dense_max != dense_min else 1
        else:
            dense_max = dense_min = dense_range = 1
        
        # Создаем словарь результатов по ID
        results_dict = {}
        
        # Добавляем BM25 результаты
        for result in bm25_results:
            normalized_score = (result.score - bm25_min) / bm25_range
            blended_score = (1 - self.alpha) * normalized_score
            results_dict[result.id] = result
            results_dict[result.id].score = blended_score
        
        # Добавляем/обновляем Dense результаты
        for result in dense_results:
            normalized_score = (result.score - dense_min) / dense_range
            dense_score = self.alpha * normalized_score
            
            if result.id in results_dict:
                # Комбинируем scores
                results_dict[result.id].score += dense_score
            else:
                # Создаем новый результат
                result.score = dense_score
                results_dict[result.id] = result
        
        # Сортируем по убыванию score
        blended_results = sorted(results_dict.values(), key=lambda x: x.score, reverse=True)
        
        logger.info(f"✅ [ALPHA] Blending completed. {len(blended_results)} unique results")
        return blended_results

class ReciprocalRankFusion:
    """Reciprocal Rank Fusion для комбинирования рангов"""
    
    def __init__(self, k: int = 60):
        self.k = k  # Параметр для RRF
    
    def fuse_ranks(self, bm25_results: List[SearchResult], dense_results: List[SearchResult]) -> List[SearchResult]:
        """Объединение рангов с помощью RRF"""
        logger.info(f"🔄 [RRF] Fusing ranks with k={self.k}")
        
        # Создаем словарь для подсчета RRF scores
        rrf_scores = defaultdict(float)
        results_dict = {}
        
        # Обрабатываем BM25 результаты
        for rank, result in enumerate(bm25_results):
            rrf_score = 1.0 / (self.k + rank + 1)
            rrf_scores[result.id] += rrf_score
            results_dict[result.id] = result
        
        # Обрабатываем Dense результаты
        for rank, result in enumerate(dense_results):
            rrf_score = 1.0 / (self.k + rank + 1)
            rrf_scores[result.id] += rrf_score
            if result.id not in results_dict:
                results_dict[result.id] = result
        
        # Обновляем scores и сортируем
        for result_id, result in results_dict.items():
            result.score = rrf_scores[result_id]
            result.search_type = 'hybrid'
        
        fused_results = sorted(results_dict.values(), key=lambda x: x.score, reverse=True)
        
        logger.info(f"✅ [RRF] Rank fusion completed. {len(fused_results)} results")
        return fused_results

class HybridSearchService:
    """Главный сервис гибридного поиска"""
    
    def __init__(self, db_connection, embedding_service, qdrant_service, 
                 alpha: float = 0.5, use_rrf: bool = True, rrf_k: int = 60):
        self.db_conn = db_connection
        self.embedding_service = embedding_service
        self.qdrant_service = qdrant_service
        
        # Инициализируем компоненты
        self.bm25_search = BM25Search()
        self.dense_search = DenseSearch(embedding_service, qdrant_service)
        self.alpha_blending = AlphaBlending(alpha)
        self.rrf = ReciprocalRankFusion(rrf_k) if use_rrf else None
        
        # Параметры
        self.alpha = alpha
        self.use_rrf = use_rrf
        self.rrf_k = rrf_k
        
        # Кэш для BM25
        self._bm25_trained = False
        self._documents_cache = []
        
        logger.info(f"✅ [HYBRID_SEARCH] Initialized with alpha={alpha}, use_rrf={use_rrf}, rrf_k={rrf_k}")
    
    def _load_documents_for_bm25(self) -> List[Dict[str, Any]]:
        """Загрузка документов для обучения BM25"""
        if self._bm25_trained and self._documents_cache:
            return self._documents_cache
        
        try:
            logger.info("📚 [HYBRID_SEARCH] Loading documents for BM25 training")
            
            with self.db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT 
                        chunk_id,
                        document_id,
                        document_title,
                        chapter,
                        section,
                        page_number,
                        chunk_type,
                        content,
                        metadata
                    FROM normative_chunks 
                    WHERE content IS NOT NULL AND LENGTH(content) > 10
                    ORDER BY document_id, chunk_id
                """)
                
                documents = cursor.fetchall()
                self._documents_cache = [dict(doc) for doc in documents]
                
                logger.info(f"✅ [HYBRID_SEARCH] Loaded {len(self._documents_cache)} documents for BM25")
                return self._documents_cache
                
        except Exception as e:
            logger.error(f"❌ [HYBRID_SEARCH] Error loading documents: {e}")
            return []
    
    def _train_bm25(self):
        """Обучение BM25 на корпусе документов"""
        if self._bm25_trained:
            return
        
        documents = self._load_documents_for_bm25()
        if documents:
            self.bm25_search.fit(documents)
            self._bm25_trained = True
        else:
            logger.warning("⚠️ [HYBRID_SEARCH] No documents available for BM25 training")
    
    def search(self, query: str, k: int = 10, 
               document_filter: Optional[str] = None,
               chapter_filter: Optional[str] = None,
               chunk_type_filter: Optional[str] = None,
               use_alpha_blending: bool = True,
               use_rrf: Optional[bool] = None) -> List[SearchResult]:
        """
        Гибридный поиск с BM25 + Dense + Alpha смешивание + RRF
        
        Args:
            query: Поисковый запрос
            k: Количество результатов
            document_filter: Фильтр по документу
            chapter_filter: Фильтр по главе
            chunk_type_filter: Фильтр по типу чанка
            use_alpha_blending: Использовать alpha смешивание
            use_rrf: Использовать RRF (переопределяет настройку по умолчанию)
        """
        try:
            logger.info(f"🔍 [HYBRID_SEARCH] Starting hybrid search for: '{query}' with k={k}")
            
            # Определяем количество результатов для каждого типа поиска
            search_k = max(k * 2, 20)  # Ищем больше, чем нужно для лучшего качества
            
            # 1. Dense поиск
            dense_filters = self._build_filters(document_filter, chapter_filter, chunk_type_filter)
            dense_results = self.dense_search.search(query, k=search_k, filters=dense_filters)
            
            # 2. BM25 поиск
            self._train_bm25()
            documents = self._load_documents_for_bm25()
            
            # Применяем фильтры к документам для BM25
            if document_filter or chapter_filter or chunk_type_filter:
                documents = self._filter_documents(documents, document_filter, chapter_filter, chunk_type_filter)
            
            bm25_results = self.bm25_search.search(query, documents, k=search_k)
            
            logger.info(f"📊 [HYBRID_SEARCH] BM25: {len(bm25_results)}, Dense: {len(dense_results)}")
            
            # 3. Выбираем метод комбинирования
            if use_rrf is None:
                use_rrf = self.use_rrf
            
            if use_rrf:
                # Reciprocal Rank Fusion
                final_results = self.rrf.fuse_ranks(bm25_results, dense_results)
            elif use_alpha_blending:
                # Alpha смешивание
                final_results = self.alpha_blending.blend_scores(bm25_results, dense_results)
            else:
                # Простое объединение (приоритет dense)
                final_results = dense_results + [r for r in bm25_results if r.id not in [d.id for d in dense_results]]
                final_results = sorted(final_results, key=lambda x: x.score, reverse=True)
            
            # Ограничиваем количество результатов
            final_results = final_results[:k]
            
            # Обновляем ранги
            for rank, result in enumerate(final_results):
                result.rank = rank + 1
            
            logger.info(f"✅ [HYBRID_SEARCH] Hybrid search completed. {len(final_results)} final results")
            return final_results
            
        except Exception as e:
            logger.error(f"❌ [HYBRID_SEARCH] Error during hybrid search: {e}")
            return []
    
    def _build_filters(self, document_filter: Optional[str], 
                      chapter_filter: Optional[str], 
                      chunk_type_filter: Optional[str]) -> Optional[Dict]:
        """Построение фильтров для Qdrant"""
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
        
        return {"must": must_conditions} if must_conditions else None
    
    def _filter_documents(self, documents: List[Dict[str, Any]], 
                         document_filter: Optional[str],
                         chapter_filter: Optional[str], 
                         chunk_type_filter: Optional[str]) -> List[Dict[str, Any]]:
        """Фильтрация документов для BM25"""
        filtered = documents
        
        if document_filter and document_filter != 'all':
            filtered = [d for d in filtered if d.get('code') == document_filter]
        
        if chapter_filter:
            filtered = [d for d in filtered if d.get('section') == chapter_filter]
        
        if chunk_type_filter:
            filtered = [d for d in filtered if d.get('chunk_type') == chunk_type_filter]
        
        return filtered
    
    def get_search_stats(self) -> Dict[str, Any]:
        """Получение статистики поиска"""
        return {
            "bm25_trained": self._bm25_trained,
            "documents_cached": len(self._documents_cache),
            "alpha": self.alpha,
            "use_rrf": self.use_rrf,
            "rrf_k": self.rrf_k,
            "corpus_size": self.bm25_search.corpus_size if self._bm25_trained else 0,
            "avg_doc_length": self.bm25_search.avgdl if self._bm25_trained else 0
        }
