"""
Сервис для реранкинга результатов поиска с помощью кросс-энкодера BGE-Reranker
"""

import logging
import requests
import os
from typing import List, Dict, Any, Tuple
import numpy as np

logger = logging.getLogger(__name__)

# Получаем URL Ollama из переменной окружения
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434")


class BGERerankerService:
    """Сервис для реранкинга с использованием BGE-Reranker через Ollama"""
    
    def __init__(self, ollama_url: str = None, model_name: str = "llama3.1:8b"):
        self.ollama_url = ollama_url or OLLAMA_URL
        self.model_name = model_name
        logger.info(f"🔄 [RERANKER] Initialized with {self.model_name} at {self.ollama_url}")
    
    def rerank_search_results(self, query: str, search_results: List[Dict[str, Any]], 
                            top_k: int = 8, initial_top_k: int = 50) -> List[Dict[str, Any]]:
        """
        Реранкинг результатов поиска с помощью кросс-энкодера
        
        Args:
            query: Поисковый запрос
            search_results: Результаты поиска от векторного поиска
            top_k: Количество финальных результатов
            initial_top_k: Количество результатов для реранкинга (должно быть >= top_k)
        
        Returns:
            Пересортированный список результатов
        """
        try:
            if not search_results:
                logger.warning("⚠️ [RERANKER] No search results to rerank")
                return []
            
            # Ограничиваем количество результатов для реранкинга
            candidates = search_results[:initial_top_k]
            logger.info(f"🔄 [RERANKER] Reranking {len(candidates)} candidates for query: '{query[:100]}...'")
            
            if len(candidates) <= top_k:
                logger.info(f"✅ [RERANKER] Not enough candidates for reranking, returning top {len(candidates)}")
                return candidates
            
            # Создаем пары запрос-документ для реранкинга
            query_document_pairs = []
            for result in candidates:
                content = result.get('content', '')
                if content.strip():
                    query_document_pairs.append({
                        'query': query,
                        'document': content,
                        'result': result
                    })
            
            if not query_document_pairs:
                logger.warning("⚠️ [RERANKER] No valid content for reranking")
                return candidates[:top_k]
            
            # Выполняем реранкинг
            reranked_scores = self._get_rerank_scores(query_document_pairs)
            
            # Сортируем результаты по новым скор-ам
            reranked_results = []
            for i, score in enumerate(reranked_scores):
                if i < len(candidates):
                    result = candidates[i].copy()
                    result['rerank_score'] = score
                    reranked_results.append(result)
            
            # Сортируем по убыванию скор-а реранкинга
            reranked_results.sort(key=lambda x: x.get('rerank_score', 0), reverse=True)
            
            # Возвращаем топ-k результатов
            final_results = reranked_results[:top_k]
            
            logger.info(f"✅ [RERANKER] Successfully reranked {len(candidates)} → {len(final_results)} results")
            
            # Логируем топ-3 результата для анализа
            for i, result in enumerate(final_results[:3]):
                logger.info(f"🏆 [RERANKER] Top {i+1}: score={result.get('rerank_score', 0):.4f}, "
                          f"title='{result.get('document_title', 'Unknown')[:50]}...'")
            
            return final_results
            
        except Exception as e:
            logger.error(f"❌ [RERANKER] Error during reranking: {e}")
            # В случае ошибки возвращаем исходные результаты
            return search_results[:top_k]
    
    def _get_rerank_scores(self, query_document_pairs: List[Dict[str, Any]]) -> List[float]:
        """
        Получение скор-ов реранкинга для пар запрос-документ
        
        Args:
            query_document_pairs: Список пар запрос-документ
            
        Returns:
            Список скор-ов реранкинга
        """
        try:
            scores = []
            
            for pair in query_document_pairs:
                query = pair['query']
                document = pair['document']
                
                # Создаем промпт для реранкинга
                prompt = f"""Запрос: {query}

Документ: {document}

Оцените, насколько документ отвечает на запрос. Поставьте оценку от 1 до 10, где:
10 - документ полностью отвечает на запрос
5 - документ частично отвечает на запрос  
1 - документ не отвечает на запрос

Оценка:"""
                
                # Отправляем запрос к Ollama
                payload = {
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Низкая температура для консистентности
                        "top_p": 0.9,
                        "num_predict": 10  # Ограничиваем длину ответа
                    }
                }
                
                response = requests.post(
                    f"{self.ollama_url}/api/generate",
                    json=payload,
                    timeout=15  # Уменьшаем таймаут
                )
                
                if response.status_code == 200:
                    result = response.json()
                    generated_text = result.get('response', '').strip()
                    
                    # Извлекаем числовой скор из ответа
                    score = self._extract_score_from_response(generated_text)
                    scores.append(score)
                    
                    logger.debug(f"🔄 [RERANKER] Query: '{query[:50]}...' → Score: {score}")
                else:
                    logger.warning(f"⚠️ [RERANKER] Ollama API error: {response.status_code}")
                    scores.append(0.0)
            
            # Нормализуем скор-ы к диапазону [0, 1]
            if scores:
                min_score = min(scores)
                max_score = max(scores)
                if max_score > min_score:
                    scores = [(s - min_score) / (max_score - min_score) for s in scores]
                else:
                    scores = [0.5] * len(scores)  # Если все скор-ы одинаковые
            
            return scores
            
        except Exception as e:
            logger.error(f"❌ [RERANKER] Error getting rerank scores: {e}")
            # Возвращаем нейтральные скор-ы
            return [0.5] * len(query_document_pairs)
    
    def _extract_score_from_response(self, response_text: str) -> float:
        """
        Извлечение числового скор-а из ответа модели
        
        Args:
            response_text: Текст ответа от модели
            
        Returns:
            Числовой скор (0.0 - 1.0)
        """
        try:
            # Ищем числовые значения в ответе
            import re
            
            # Паттерны для поиска скор-ов (в порядке приоритета)
            patterns = [
                r'оценка[:\s]*(\d+)',  # "оценка: 8"
                r'(\d+)\s*из\s*10',  # "8 из 10"
                r'(\d+)/10',  # "8/10"
                r'(\d+)',  # Простые числа (последний приоритет)
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, response_text.lower())
                if matches:
                    try:
                        score = float(matches[0])
                        
                        # Нормализуем к диапазону [0, 1] (шкала 1-10)
                        if score > 10:  # Если скор больше 10
                            score = score / 100
                        elif score > 1:  # Если скор по 10-балльной шкале
                            score = (score - 1) / 9  # Преобразуем 1-10 в 0-1
                        
                        # Ограничиваем диапазон
                        score = max(0.0, min(1.0, score))
                        
                        return score
                    except ValueError:
                        continue
            
            # Если не удалось извлечь скор, используем эвристику
            # Анализируем ключевые слова в ответе
            positive_words = ['релевантн', 'хорош', 'отличн', 'высок', 'сильн', 'точн', 'подходящ']
            negative_words = ['нерелевантн', 'плох', 'слаб', 'низк', 'неточн', 'неподходящ']
            
            response_lower = response_text.lower()
            positive_count = sum(1 for word in positive_words if word in response_lower)
            negative_count = sum(1 for word in negative_words if word in response_lower)
            
            if positive_count > negative_count:
                return 0.8  # Высокая релевантность
            elif negative_count > positive_count:
                return 0.2  # Низкая релевантность
            else:
                return 0.5  # Нейтральная релевантность
                
        except Exception as e:
            logger.warning(f"⚠️ [RERANKER] Error extracting score from response: {e}")
            return 0.5  # Нейтральный скор по умолчанию
    
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
            logger.error(f"❌ [RERANKER] Health check failed: {e}")
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
                            "status": "available"
                        }
            return {"name": self.model_name, "status": "not_found"}
        except Exception as e:
            logger.error(f"❌ [RERANKER] Error getting model info: {e}")
            return {"name": self.model_name, "status": "error"}
