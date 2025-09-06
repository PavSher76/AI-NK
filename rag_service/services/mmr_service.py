"""
Сервис MMR (Maximal Marginal Relevance) для обеспечения разнообразия результатов поиска
"""

import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import re
from collections import defaultdict
import math

logger = logging.getLogger(__name__)

@dataclass
class MMRResult:
    """Результат MMR с метаданными"""
    id: str
    score: float
    mmr_score: float
    relevance_score: float
    diversity_score: float
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
    search_type: str
    rank: int = 0

class MMRService:
    """Сервис для MMR (Maximal Marginal Relevance) диверсификации"""
    
    def __init__(self, lambda_param: float = 0.7, similarity_threshold: float = 0.8):
        """
        Инициализация MMR сервиса
        
        Args:
            lambda_param: Параметр баланса между релевантностью и разнообразием (0.0-1.0)
                        0.0 - только разнообразие, 1.0 - только релевантность
            similarity_threshold: Порог схожести для определения дубликатов
        """
        self.lambda_param = lambda_param
        self.similarity_threshold = similarity_threshold
        
        logger.info(f"🔄 [MMR] Initialized with lambda={lambda_param}, threshold={similarity_threshold}")
    
    def diversify_results(self, results: List[Dict[str, Any]], k: int = 8, 
                         query: str = "", use_semantic_similarity: bool = True) -> List[MMRResult]:
        """
        Применение MMR для диверсификации результатов
        
        Args:
            results: Список результатов поиска
            k: Количество финальных результатов
            query: Поисковый запрос для вычисления релевантности
            use_semantic_similarity: Использовать семантическое сходство или текстовое
        
        Returns:
            Список диверсифицированных результатов
        """
        try:
            if not results or len(results) <= k:
                logger.info(f"✅ [MMR] Not enough results for diversification: {len(results)} <= {k}")
                return self._convert_to_mmr_results(results)
            
            logger.info(f"🔄 [MMR] Diversifying {len(results)} results → {k} with lambda={self.lambda_param}")
            
            # Конвертируем результаты в MMR формат
            mmr_results = self._convert_to_mmr_results(results)
            
            # Вычисляем релевантность к запросу
            if query:
                self._compute_relevance_scores(mmr_results, query)
            
            # Применяем MMR алгоритм
            diversified_results = self._apply_mmr_algorithm(mmr_results, k, use_semantic_similarity)
            
            # Обновляем ранги
            for rank, result in enumerate(diversified_results):
                result.rank = rank + 1
            
            logger.info(f"✅ [MMR] Diversification completed: {len(diversified_results)} results")
            
            # Логируем топ-3 результата
            for i, result in enumerate(diversified_results[:3]):
                logger.info(f"🏆 [MMR] Top {i+1}: mmr_score={result.mmr_score:.4f}, "
                          f"relevance={result.relevance_score:.4f}, diversity={result.diversity_score:.4f}, "
                          f"title='{result.document_title[:50]}...'")
            
            return diversified_results
            
        except Exception as e:
            logger.error(f"❌ [MMR] Error during diversification: {e}")
            # Возвращаем исходные результаты в случае ошибки
            return self._convert_to_mmr_results(results[:k])
    
    def _convert_to_mmr_results(self, results: List[Dict[str, Any]]) -> List[MMRResult]:
        """Конвертация результатов в MMR формат"""
        mmr_results = []
        for result in results:
            mmr_result = MMRResult(
                id=result.get('id', ''),
                score=result.get('score', 0.0),
                mmr_score=result.get('score', 0.0),
                relevance_score=result.get('score', 0.0),
                diversity_score=0.0,
                document_id=result.get('document_id', ''),
                chunk_id=result.get('chunk_id', ''),
                code=result.get('code', ''),
                document_title=result.get('document_title', ''),
                section_title=result.get('section_title', ''),
                content=result.get('content', ''),
                chunk_type=result.get('chunk_type', ''),
                page=result.get('page', 0),
                section=result.get('section', ''),
                metadata=result.get('metadata', {}),
                search_type=result.get('search_type', 'hybrid')
            )
            mmr_results.append(mmr_result)
        return mmr_results
    
    def _compute_relevance_scores(self, results: List[MMRResult], query: str):
        """Вычисление релевантности к запросу"""
        try:
            query_tokens = self._tokenize(query.lower())
            query_tf = self._compute_tf(query_tokens)
            
            for result in results:
                content_tokens = self._tokenize(result.content.lower())
                content_tf = self._compute_tf(content_tokens)
                
                # Вычисляем косинусное сходство
                similarity = self._cosine_similarity(query_tf, content_tf)
                result.relevance_score = similarity
                
        except Exception as e:
            logger.warning(f"⚠️ [MMR] Error computing relevance scores: {e}")
            # Используем исходные скор-ы как релевантность
            for result in results:
                result.relevance_score = result.score
    
    def _apply_mmr_algorithm(self, results: List[MMRResult], k: int, 
                           use_semantic_similarity: bool = True) -> List[MMRResult]:
        """
        Применение MMR алгоритма
        
        MMR = λ * Relevance(d) - (1-λ) * max(Similarity(d, di)) for di in S
        """
        try:
            if not results:
                return []
            
            # Сортируем по релевантности для начального выбора
            results.sort(key=lambda x: x.relevance_score, reverse=True)
            
            # Выбираем первый результат (самый релевантный)
            selected = [results[0]]
            remaining = results[1:]
            
            # Итеративно выбираем остальные результаты
            while len(selected) < k and remaining:
                best_result = None
                best_mmr_score = float('-inf')
                
                for candidate in remaining:
                    # Вычисляем максимальное сходство с уже выбранными
                    max_similarity = 0.0
                    for selected_result in selected:
                        similarity = self._compute_similarity(
                            candidate, selected_result, use_semantic_similarity
                        )
                        max_similarity = max(max_similarity, similarity)
                    
                    # Вычисляем MMR скор
                    mmr_score = (self.lambda_param * candidate.relevance_score - 
                               (1 - self.lambda_param) * max_similarity)
                    
                    candidate.mmr_score = mmr_score
                    candidate.diversity_score = max_similarity
                    
                    if mmr_score > best_mmr_score:
                        best_mmr_score = mmr_score
                        best_result = candidate
                
                if best_result:
                    selected.append(best_result)
                    remaining.remove(best_result)
                else:
                    break
            
            return selected
            
        except Exception as e:
            logger.error(f"❌ [MMR] Error in MMR algorithm: {e}")
            return results[:k]
    
    def _compute_similarity(self, result1: MMRResult, result2: MMRResult, 
                          use_semantic_similarity: bool = True) -> float:
        """
        Вычисление сходства между двумя результатами
        
        Args:
            result1: Первый результат
            result2: Второй результат
            use_semantic_similarity: Использовать семантическое сходство
        
        Returns:
            Коэффициент сходства (0.0-1.0)
        """
        try:
            # Проверяем на дубликаты по ID
            if result1.id == result2.id:
                return 1.0
            
            # Проверяем на дубликаты по документу и чанку
            if (result1.document_id == result2.document_id and 
                result1.chunk_id == result2.chunk_id):
                return 0.9
            
            # Проверяем на дубликаты по документу
            if result1.document_id == result2.document_id:
                return 0.7
            
            # Проверяем на дубликаты по коду документа
            if result1.code == result2.code and result1.code:
                return 0.6
            
            if use_semantic_similarity:
                # Семантическое сходство на основе контента
                return self._compute_content_similarity(result1.content, result2.content)
            else:
                # Простое текстовое сходство
                return self._compute_text_similarity(result1.content, result2.content)
                
        except Exception as e:
            logger.warning(f"⚠️ [MMR] Error computing similarity: {e}")
            return 0.0
    
    def _compute_content_similarity(self, content1: str, content2: str) -> float:
        """Вычисление семантического сходства контента"""
        try:
            # Токенизация
            tokens1 = self._tokenize(content1.lower())
            tokens2 = self._tokenize(content2.lower())
            
            if not tokens1 or not tokens2:
                return 0.0
            
            # Вычисляем TF векторы
            tf1 = self._compute_tf(tokens1)
            tf2 = self._compute_tf(tokens2)
            
            # Косинусное сходство
            similarity = self._cosine_similarity(tf1, tf2)
            
            # Дополнительная проверка на ключевые слова
            common_tokens = set(tokens1) & set(tokens2)
            if common_tokens:
                # Увеличиваем сходство если есть общие ключевые слова
                keyword_boost = len(common_tokens) / max(len(tokens1), len(tokens2))
                similarity = min(1.0, similarity + keyword_boost * 0.2)
            
            return similarity
            
        except Exception as e:
            logger.warning(f"⚠️ [MMR] Error computing content similarity: {e}")
            return 0.0
    
    def _compute_text_similarity(self, text1: str, text2: str) -> float:
        """Вычисление простого текстового сходства"""
        try:
            # Jaccard сходство
            words1 = set(self._tokenize(text1.lower()))
            words2 = set(self._tokenize(text2.lower()))
            
            if not words1 or not words2:
                return 0.0
            
            intersection = len(words1 & words2)
            union = len(words1 | words2)
            
            return intersection / union if union > 0 else 0.0
            
        except Exception as e:
            logger.warning(f"⚠️ [MMR] Error computing text similarity: {e}")
            return 0.0
    
    def _tokenize(self, text: str) -> List[str]:
        """Токенизация текста с учетом русского языка"""
        # Удаляем пунктуацию и приводим к нижнему регистру
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        # Разбиваем на слова
        tokens = text.split()
        # Фильтруем короткие слова и стоп-слова
        stop_words = {
            'и', 'в', 'на', 'с', 'по', 'для', 'от', 'до', 'из', 'к', 'о', 'у', 'за', 'при', 'без', 
            'через', 'над', 'под', 'между', 'среди', 'вокруг', 'около', 'близ', 'далеко', 'здесь', 
            'там', 'где', 'когда', 'как', 'что', 'кто', 'который', 'это', 'тот', 'этот', 'такой', 
            'какой', 'весь', 'все', 'вся', 'всё', 'каждый', 'любой', 'другой', 'иной', 'сам', 
            'сама', 'само', 'сами', 'себя', 'себе', 'собой', 'мой', 'моя', 'моё', 'мои', 'твой', 
            'твоя', 'твоё', 'твои', 'его', 'её', 'их', 'наш', 'наша', 'наше', 'наши', 'ваш', 
            'ваша', 'ваше', 'ваши', 'или', 'но', 'а', 'да', 'нет', 'не', 'ни', 'же', 'ли', 'бы', 
            'б', 'то', 'же', 'ли', 'бы', 'б', 'то', 'же', 'ли', 'бы', 'б'
        }
        return [token for token in tokens if len(token) > 2 and token not in stop_words]
    
    def _compute_tf(self, tokens: List[str]) -> Dict[str, float]:
        """Вычисление TF (Term Frequency)"""
        if not tokens:
            return {}
        
        token_count = len(tokens)
        tf = defaultdict(float)
        
        for token in tokens:
            tf[token] += 1.0
        
        # Нормализация
        for token in tf:
            tf[token] /= token_count
        
        return dict(tf)
    
    def _cosine_similarity(self, tf1: Dict[str, float], tf2: Dict[str, float]) -> float:
        """Вычисление косинусного сходства между TF векторами"""
        try:
            # Получаем все уникальные токены
            all_tokens = set(tf1.keys()) | set(tf2.keys())
            
            if not all_tokens:
                return 0.0
            
            # Создаем векторы
            vector1 = [tf1.get(token, 0.0) for token in all_tokens]
            vector2 = [tf2.get(token, 0.0) for token in all_tokens]
            
            # Вычисляем косинусное сходство
            dot_product = sum(a * b for a, b in zip(vector1, vector2))
            norm1 = math.sqrt(sum(a * a for a in vector1))
            norm2 = math.sqrt(sum(b * b for b in vector2))
            
            if norm1 == 0.0 or norm2 == 0.0:
                return 0.0
            
            return dot_product / (norm1 * norm2)
            
        except Exception as e:
            logger.warning(f"⚠️ [MMR] Error computing cosine similarity: {e}")
            return 0.0
    
    def get_diversity_stats(self, results: List[MMRResult]) -> Dict[str, Any]:
        """Получение статистики разнообразия"""
        try:
            if not results:
                return {"diversity_score": 0.0, "unique_documents": 0, "duplicate_ratio": 0.0}
            
            # Подсчитываем уникальные документы
            unique_docs = set()
            unique_codes = set()
            total_similarity = 0.0
            similarity_pairs = 0
            
            for i, result1 in enumerate(results):
                unique_docs.add(result1.document_id)
                unique_codes.add(result1.code)
                
                for j, result2 in enumerate(results[i+1:], i+1):
                    similarity = self._compute_similarity(result1, result2, True)
                    total_similarity += similarity
                    similarity_pairs += 1
            
            avg_similarity = total_similarity / similarity_pairs if similarity_pairs > 0 else 0.0
            diversity_score = 1.0 - avg_similarity
            duplicate_ratio = avg_similarity
            
            return {
                "diversity_score": diversity_score,
                "unique_documents": len(unique_docs),
                "unique_codes": len(unique_codes),
                "duplicate_ratio": duplicate_ratio,
                "avg_similarity": avg_similarity,
                "total_results": len(results)
            }
            
        except Exception as e:
            logger.error(f"❌ [MMR] Error computing diversity stats: {e}")
            return {"diversity_score": 0.0, "error": str(e)}
    
    def get_mmr_stats(self) -> Dict[str, Any]:
        """Получение статистики MMR сервиса"""
        return {
            "lambda_param": self.lambda_param,
            "similarity_threshold": self.similarity_threshold,
            "service_type": "mmr_diversification",
            "timestamp": "2024-01-01T00:00:00Z"  # Будет обновлено при использовании
        }
