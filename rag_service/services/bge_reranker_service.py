"""
Сервис для реранкинга результатов поиска с помощью BGE-ranking-base
"""

import logging
import requests
import os
import json
from typing import List, Dict, Any, Tuple
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)

# Получаем URL Ollama из переменной окружения
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434")

class BGERankingService:
    """Сервис для реранкинга с использованием BGE-ranking-base через Ollama"""
    
    def __init__(self, ollama_url: str = None, model_name: str = "bge-ranking-base"):
        self.ollama_url = ollama_url or OLLAMA_URL
        self.model_name = model_name
        self.max_batch_size = 10  # Размер батча для обработки
        self.timeout = 30  # Таймаут для запросов
        
        logger.info(f"🔄 [BGE_RERANKER] Initialized with {self.model_name} at {self.ollama_url}")
    
    def rerank_search_results(self, query: str, search_results: List[Dict[str, Any]], 
                            top_k: int = 8, initial_top_k: int = 50) -> List[Dict[str, Any]]:
        """
        Реранкинг результатов поиска с помощью BGE-ranking-base
        
        Args:
            query: Поисковый запрос
            search_results: Результаты поиска от гибридного поиска
            top_k: Количество финальных результатов
            initial_top_k: Количество результатов для реранкинга
        
        Returns:
            Пересортированный список результатов
        """
        try:
            if not search_results:
                logger.warning("⚠️ [BGE_RERANKER] No search results to rerank")
                return []
            
            # Ограничиваем количество результатов для реранкинга
            candidates = search_results[:initial_top_k]
            logger.info(f"🔄 [BGE_RERANKER] Reranking {len(candidates)} candidates for query: '{query[:100]}...'")
            
            if len(candidates) <= top_k:
                logger.info(f"✅ [BGE_RERANKER] Not enough candidates for reranking, returning top {len(candidates)}")
                return candidates
            
            # Создаем пары запрос-документ для реранкинга
            query_document_pairs = []
            for result in candidates:
                content = result.get('content', '')
                if content.strip():
                    # Ограничиваем длину контента для эффективности
                    content = content[:2000]  # Максимум 2000 символов
                    query_document_pairs.append({
                        'query': query,
                        'document': content,
                        'result': result
                    })
            
            if not query_document_pairs:
                logger.warning("⚠️ [BGE_RERANKER] No valid content for reranking")
                return candidates[:top_k]
            
            # Выполняем реранкинг батчами
            reranked_scores = self._get_rerank_scores_batch(query_document_pairs)
            
            # Сортируем результаты по новым скор-ам
            reranked_results = []
            for i, score in enumerate(reranked_scores):
                if i < len(candidates):
                    result = candidates[i].copy()
                    result['rerank_score'] = score
                    result['original_score'] = result.get('score', 0)
                    result['search_type'] = result.get('search_type', 'hybrid')
                    reranked_results.append(result)
            
            # Сортируем по убыванию скор-а реранкинга
            reranked_results.sort(key=lambda x: x.get('rerank_score', 0), reverse=True)
            
            # Возвращаем топ-k результатов
            final_results = reranked_results[:top_k]
            
            logger.info(f"✅ [BGE_RERANKER] Successfully reranked {len(candidates)} → {len(final_results)} results")
            
            # Логируем топ-3 результата для анализа
            for i, result in enumerate(final_results[:3]):
                logger.info(f"🏆 [BGE_RERANKER] Top {i+1}: rerank_score={result.get('rerank_score', 0):.4f}, "
                          f"original_score={result.get('original_score', 0):.4f}, "
                          f"title='{result.get('document_title', 'Unknown')[:50]}...'")
            
            return final_results
            
        except Exception as e:
            logger.error(f"❌ [BGE_RERANKER] Error during reranking: {e}")
            # В случае ошибки возвращаем исходные результаты
            return search_results[:top_k]
    
    def _get_rerank_scores_batch(self, query_document_pairs: List[Dict[str, Any]]) -> List[float]:
        """
        Получение скор-ов реранкинга для пар запрос-документ батчами
        
        Args:
            query_document_pairs: Список пар запрос-документ
            
        Returns:
            Список скор-ов реранкинга
        """
        try:
            all_scores = []
            
            # Обрабатываем батчами для эффективности
            for i in range(0, len(query_document_pairs), self.max_batch_size):
                batch = query_document_pairs[i:i + self.max_batch_size]
                batch_scores = self._process_batch(batch)
                all_scores.extend(batch_scores)
                
                logger.debug(f"🔄 [BGE_RERANKER] Processed batch {i//self.max_batch_size + 1}, "
                           f"scores: {[f'{s:.3f}' for s in batch_scores]}")
            
            return all_scores
            
        except Exception as e:
            logger.error(f"❌ [BGE_RERANKER] Error getting rerank scores: {e}")
            # Возвращаем нейтральные скор-ы
            return [0.5] * len(query_document_pairs)
    
    def _process_batch(self, batch: List[Dict[str, Any]]) -> List[float]:
        """
        Обработка батча пар запрос-документ
        
        Args:
            batch: Батч пар запрос-документ
            
        Returns:
            Список скор-ов для батча
        """
        try:
            # Создаем промпт для BGE-ranking-base
            prompt_parts = []
            prompt_parts.append("Задача: Оцените релевантность документов к запросу.")
            prompt_parts.append("Формат ответа: Только числа от 0.0 до 1.0, по одному на строку.")
            prompt_parts.append("")
            
            for i, pair in enumerate(batch):
                query = pair['query']
                document = pair['document']
                
                prompt_parts.append(f"Запрос {i+1}: {query}")
                prompt_parts.append(f"Документ {i+1}: {document[:500]}...")  # Ограничиваем длину
                prompt_parts.append("")
            
            prompt_parts.append("Оценки релевантности (по одной на строку):")
            
            prompt = "\n".join(prompt_parts)
            
            # Отправляем запрос к Ollama
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.0,  # Нулевая температура для консистентности
                    "top_p": 0.1,
                    "num_predict": len(batch) * 10,  # Достаточно для чисел
                    "stop": ["\n\n", "Запрос", "Документ"]  # Стоп-слова
                }
            }
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                generated_text = result.get('response', '').strip()
                
                # Извлекаем числовые скор-ы из ответа
                scores = self._extract_scores_from_response(generated_text, len(batch))
                
                logger.debug(f"🔄 [BGE_RERANKER] Batch processed: {len(scores)} scores extracted")
                return scores
            else:
                logger.warning(f"⚠️ [BGE_RERANKER] Ollama API error: {response.status_code}")
                return [0.5] * len(batch)
                
        except Exception as e:
            logger.error(f"❌ [BGE_RERANKER] Error processing batch: {e}")
            return [0.5] * len(batch)
    
    def _extract_scores_from_response(self, response_text: str, expected_count: int) -> List[float]:
        """
        Извлечение числовых скор-ов из ответа модели
        
        Args:
            response_text: Текст ответа от модели
            expected_count: Ожидаемое количество скор-ов
            
        Returns:
            Список числовых скор-ов (0.0 - 1.0)
        """
        try:
            import re
            
            # Ищем все числа в ответе
            numbers = re.findall(r'\d+\.?\d*', response_text)
            
            scores = []
            for num_str in numbers:
                try:
                    score = float(num_str)
                    
                    # Нормализуем к диапазону [0, 1]
                    if score > 1.0:
                        score = score / 10.0  # Если скор больше 1, делим на 10
                    
                    # Ограничиваем диапазон
                    score = max(0.0, min(1.0, score))
                    scores.append(score)
                    
                except ValueError:
                    continue
            
            # Если не хватает скор-ов, дополняем нейтральными
            while len(scores) < expected_count:
                scores.append(0.5)
            
            # Если слишком много скор-ов, берем первые
            scores = scores[:expected_count]
            
            logger.debug(f"🔄 [BGE_RERANKER] Extracted {len(scores)} scores: {[f'{s:.3f}' for s in scores]}")
            return scores
            
        except Exception as e:
            logger.warning(f"⚠️ [BGE_RERANKER] Error extracting scores from response: {e}")
            return [0.5] * expected_count
    
    def rerank_with_fallback(self, query: str, search_results: List[Dict[str, Any]], 
                           top_k: int = 8, initial_top_k: int = 50) -> List[Dict[str, Any]]:
        """
        Реранкинг с fallback механизмом
        
        Args:
            query: Поисковый запрос
            search_results: Результаты поиска
            top_k: Количество финальных результатов
            initial_top_k: Количество результатов для реранкинга
        
        Returns:
            Пересортированный список результатов
        """
        try:
            # Пытаемся использовать BGE-ranking-base
            return self.rerank_search_results(query, search_results, top_k, initial_top_k)
            
        except Exception as e:
            logger.warning(f"⚠️ [BGE_RERANKER] BGE ranking failed, using fallback: {e}")
            
            # Fallback: простая сортировка по оригинальным скор-ам
            candidates = search_results[:initial_top_k]
            sorted_results = sorted(candidates, key=lambda x: x.get('score', 0), reverse=True)
            
            # Добавляем метку fallback
            for result in sorted_results[:top_k]:
                result['rerank_score'] = result.get('score', 0)
                result['rerank_method'] = 'fallback'
            
            logger.info(f"✅ [BGE_RERANKER] Fallback completed: {len(candidates)} → {top_k} results")
            return sorted_results[:top_k]
    
    def health_check(self) -> bool:
        """Проверка здоровья сервиса реранкинга"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [model.get("name") for model in models]
                return self.model_name in model_names
            return False
        except Exception as e:
            logger.error(f"❌ [BGE_RERANKER] Health check failed: {e}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """Получение информации о модели реранкинга"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=10)
            if response.status_code == 200:
                models = response.json().get("models", [])
                for model in models:
                    if model.get("name") == self.model_name:
                        return {
                            "name": model.get("name"),
                            "size": model.get("size"),
                            "modified_at": model.get("modified_at"),
                            "status": "available",
                            "type": "bge-ranking-base"
                        }
            return {"name": self.model_name, "status": "not_found"}
        except Exception as e:
            logger.error(f"❌ [BGE_RERANKER] Error getting model info: {e}")
            return {"name": self.model_name, "status": "error"}
    
    def get_reranking_stats(self) -> Dict[str, Any]:
        """Получение статистики реранкинга"""
        return {
            "model_name": self.model_name,
            "max_batch_size": self.max_batch_size,
            "timeout": self.timeout,
            "health_status": self.health_check(),
            "model_info": self.get_model_info(),
            "timestamp": datetime.now().isoformat()
        }
