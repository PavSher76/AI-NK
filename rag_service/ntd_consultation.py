import logging
import asyncio
from typing import List, Dict, Any, Optional
import httpx
from datetime import datetime
import numpy as np
import requests
# from sentence_transformers import SentenceTransformer  # Отключено для тестирования
import hashlib
import json
from functools import lru_cache
import time

logger = logging.getLogger(__name__)

class NTDConsultationService:
    """Сервис для консультации по нормативным документам"""
    
    def __init__(self, db_connection, qdrant_client, ollama_url: str = "http://vllm:8000", rag_service=None):
        """
        Инициализация сервиса консультации НТД
        
        Args:
            db_connection: Подключение к PostgreSQL
            qdrant_client: Клиент Qdrant
            ollama_url: URL VLLM Adapter (по умолчанию http://vllm:8000)
            rag_service: Ссылка на основной RAG сервис для доступа к модели эмбеддингов
        """
        self.db_conn = db_connection
        self.qdrant_client = qdrant_client
        self.ollama_url = ollama_url
        self.collection_name = "normative_documents"
        self.rag_service = rag_service  # Ссылка на основной RAG сервис
        self.embedding_model = None
        self.cache = {}  # Простой кэш для частых запросов
        self.cache_ttl = 3600  # TTL кэша в секундах (1 час)
        
        # Параметры конфигурации
        self.SEARCH_LIMIT = 8  # Увеличено количество документов для поиска
        self.MAX_CONTEXT_LENGTH = 800  # Увеличена длина контекста
        self.MIN_CONTEXT_LENGTH = 200  # Минимальная длина контекста
        self.CONFIDENCE_THRESHOLD = 0.3  # Порог уверенности для ответа
        
        # Параметры LLM
        self.MODEL_NAME = "llama3.1:8b"
        self.TEMPERATURE = 0.7
        self.MAX_TOKENS = 2500  # Увеличено количество токенов
        
        self._load_embedding_model()
        
    def _load_embedding_model(self):
        """Загрузка модели эмбеддингов"""
        try:
            # Если есть доступ к RAG сервису, используем его модель
            if self.rag_service and hasattr(self.rag_service, 'embedding_model') and self.rag_service.embedding_model:
                self.embedding_model = self.rag_service.embedding_model
                logger.info("✅ [NTD_CONSULTATION] Using embedding model from RAG service")
            else:
                # Иначе загружаем собственную модель
                logger.info("🔧 [NTD_CONSULTATION] Using simple hash embeddings for testing...")
                # Используем простые хеш-эмбеддинги для тестирования
                self.embedding_model = None
                logger.info(f"✅ [NTD_CONSULTATION] Simple hash embeddings ready (1024 dimensions)")
                
        except Exception as e:
            logger.error(f"❌ [NTD_CONSULTATION] Error loading embedding model: {e}")
            self.embedding_model = None
    
    def _get_cache_key(self, message: str, history: List[Dict[str, str]] = None) -> str:
        """Генерация ключа кэша для запроса"""
        # Создаем хеш из сообщения и истории
        cache_data = {
            "message": message.lower().strip(),
            "history": history or []
        }
        cache_string = json.dumps(cache_data, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(cache_string.encode('utf-8')).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Получение ответа из кэша"""
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            if time.time() - cached_data['timestamp'] < self.cache_ttl:
                logger.info(f"📋 [NTD_CONSULTATION] Cache hit for query")
                return cached_data['response']
            else:
                # Удаляем устаревший кэш
                del self.cache[cache_key]
        return None
    
    def _save_to_cache(self, cache_key: str, response: Dict[str, Any]):
        """Сохранение ответа в кэш"""
        self.cache[cache_key] = {
            'response': response,
            'timestamp': time.time()
        }
        logger.info(f"💾 [NTD_CONSULTATION] Response cached")
        
    async def get_consultation(self, message: str, history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Получить консультацию по нормативным документам
        
        Args:
            message: Вопрос пользователя
            history: История диалога
            
        Returns:
            Dict с ответом и источниками
        """
        start_time = time.time()
        
        try:
            logger.info(f"🔍 [NTD_CONSULTATION] Processing question: {message[:100]}...")
            
            # Проверяем кэш
            cache_key = self._get_cache_key(message, history)
            cached_response = self._get_from_cache(cache_key)
            if cached_response:
                cached_response['cached'] = True
                return cached_response
            
            # 1. Поиск релевантных документов
            relevant_docs = await self._search_relevant_documents(message)
            
            if not relevant_docs:
                logger.warning("⚠️ [NTD_CONSULTATION] No relevant documents found")
                response = {
                    "response": "К сожалению, я не нашел релевантной информации в базе нормативных документов для вашего вопроса. Попробуйте переформулировать вопрос или обратитесь к специалисту.",
                    "sources": [],
                    "confidence": 0.0,
                    "documents_used": 0,
                    "processing_time": round(time.time() - start_time, 3)
                }
                self._save_to_cache(cache_key, response)
                return response
            
            # 2. Динамическое формирование контекста
            context = self._build_dynamic_context(relevant_docs, message)
            
            # 3. Генерация ответа с помощью ИИ
            response = await self._generate_response(message, context, history)
            
            # 4. Подготовка источников
            sources = self._prepare_sources(relevant_docs)
            
            # 5. Расчет уверенности
            confidence = self._calculate_confidence(relevant_docs, response)
            
            # 6. Формирование финального ответа
            final_response = {
                "response": response,
                "sources": sources,
                "confidence": confidence,
                "documents_used": len(relevant_docs),
                "processing_time": round(time.time() - start_time, 3),
                "context_length": len(context),
                "cached": False
            }
            
            # Сохраняем в кэш только успешные ответы
            if confidence > self.CONFIDENCE_THRESHOLD:
                self._save_to_cache(cache_key, final_response)
            
            logger.info(f"✅ [NTD_CONSULTATION] Response generated successfully in {final_response['processing_time']}s")
            
            return final_response
            
        except Exception as e:
            logger.error(f"❌ [NTD_CONSULTATION] Error: {e}")
            return {
                "response": "Произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте еще раз или обратитесь к администратору системы.",
                "sources": [],
                "confidence": 0.0,
                "documents_used": 0,
                "processing_time": round(time.time() - start_time, 3),
                "error": str(e),
                "cached": False
            }
    
    async def _search_relevant_documents(self, query: str, limit: int = None) -> List[Dict[str, Any]]:
        """
        Поиск релевантных документов в базе
        
        Args:
            query: Поисковый запрос
            limit: Максимальное количество документов
            
        Returns:
            Список релевантных документов
        """
        if limit is None:
            limit = self.SEARCH_LIMIT
            
        try:
            # 1. Реальная векторизация запроса
            query_vector = self._get_query_vector(query)
            
            if query_vector is None:
                logger.error("❌ [NTD_CONSULTATION] Failed to vectorize query")
                return []
            
            # 2. Поиск в Qdrant
            search_results = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit,
                with_payload=True,
                with_vectors=False,
                score_threshold=0.1  # Минимальный порог релевантности
            )
            
            if not search_results:
                logger.warning("⚠️ [NTD_CONSULTATION] No search results from Qdrant")
                return []
            
            # 3. Получение дополнительной информации из БД
            documents = []
            for result in search_results:
                doc_info = await self._get_document_info(result.id)
                if doc_info:
                    documents.append({
                        "id": result.id,
                        "score": result.score,
                        "content": result.payload.get("content", ""),
                        "title": doc_info.get("title", ""),
                        "filename": doc_info.get("filename", ""),
                        "category": doc_info.get("category", ""),
                        "page": result.payload.get("page", 1),
                        "chunk_type": result.payload.get("chunk_type", "text"),
                        "semantic_context": result.payload.get("semantic_context", ""),
                        "importance_level": result.payload.get("importance_level", 1)
                    })
            
            # 4. Сортировка по релевантности и важности
            documents.sort(key=lambda x: (x['score'], x['importance_level']), reverse=True)
            
            logger.info(f"🔍 [NTD_CONSULTATION] Found {len(documents)} relevant documents")
            return documents
            
        except Exception as e:
            logger.error(f"❌ [NTD_CONSULTATION] Search error: {e}")
            return []
    
    def _get_query_vector(self, query: str) -> Optional[List[float]]:
        """Получение вектора для поискового запроса"""
        try:
            if self.embedding_model:
                # Используем реальную модель BGE-M3
                embedding = self.embedding_model.encode(query, normalize_embeddings=True)
                logger.debug(f"🔢 [NTD_CONSULTATION] Query vectorized: {len(embedding)} dimensions")
                return embedding.tolist()
            else:
                logger.error("❌ [NTD_CONSULTATION] No embedding model available")
                return None
                
        except Exception as e:
            logger.error(f"❌ [NTD_CONSULTATION] Vectorization error: {e}")
            return None
    
    async def _get_document_info(self, doc_id: int) -> Optional[Dict[str, Any]]:
        """Получить информацию о документе из БД"""
        try:
            def _get_info(conn):
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT title, filename, category, upload_date, document_type, document_number
                        FROM uploaded_documents
                        WHERE id = %s
                    """, (doc_id,))
                    result = cursor.fetchone()
                    if result:
                        return {
                            "title": result[0],
                            "filename": result[1],
                            "category": result[2],
                            "upload_date": result[3],
                            "document_type": result[4],
                            "document_number": result[5]
                        }
                    return None
            
            return self.db_conn.execute_in_transaction(_get_info)
            
        except Exception as e:
            logger.error(f"❌ [NTD_CONSULTATION] Error getting document info: {e}")
            return None
    
    def _build_dynamic_context(self, documents: List[Dict[str, Any]], query: str) -> str:
        """Динамическое построение контекста из найденных документов"""
        context_parts = []
        total_length = 0
        
        # Анализируем запрос для определения приоритетов
        query_lower = query.lower()
        is_technical = any(word in query_lower for word in ['требования', 'нормы', 'стандарты', 'правила'])
        is_practical = any(word in query_lower for word in ['как', 'что делать', 'рекомендации', 'примеры'])
        
        for i, doc in enumerate(documents):
            if total_length >= self.MAX_CONTEXT_LENGTH:
                break
                
            # Определяем приоритет контента
            content = doc['content']
            if doc.get('semantic_context'):
                content = f"{doc['semantic_context']}\n{content}"
            
            # Ограничиваем длину контента
            max_content_length = min(600, self.MAX_CONTEXT_LENGTH - total_length - 200)
            if len(content) > max_content_length:
                content = content[:max_content_length] + "..."
            
            # Формируем структурированный контекст
            context_part = f"Документ {i+1}: {doc['title']}"
            if doc.get('document_number'):
                context_part += f" ({doc['document_number']})"
            context_part += f"\nКатегория: {doc['category']}"
            if doc.get('chunk_type') and doc['chunk_type'] != 'text':
                context_part += f"\nТип: {doc['chunk_type']}"
            context_part += f"\nРелевантность: {doc['score']:.3f}"
            context_part += f"\nСодержание:\n{content}\n---\n"
            
            context_parts.append(context_part)
            total_length += len(context_part)
        
        context = "\n".join(context_parts)
        
        # Добавляем метаинформацию
        if len(documents) > 0:
            context = f"Найдено документов: {len(documents)}\nСредняя релевантность: {sum(d['score'] for d in documents) / len(documents):.3f}\n\n{context}"
        
        logger.debug(f"📝 [NTD_CONSULTATION] Context built: {len(context)} characters")
        return context
    
    async def _generate_response(self, question: str, context: str, history: List[Dict[str, str]] = None) -> str:
        """
        Генерация ответа с помощью ИИ
        
        Args:
            question: Вопрос пользователя
            context: Контекст из документов
            history: История диалога
            
        Returns:
            Ответ ИИ
        """
        try:
            # Формирование промпта
            prompt = self._build_enhanced_prompt(question, context, history)
            
            # Отправка запроса к VLLM Adapter
            async with httpx.AsyncClient(timeout=90.0) as client:  # Увеличено время ожидания
                response = await client.post(
                    f"{self.ollama_url}/v1/chat/completions",
                    json={
                        "model": self.MODEL_NAME,
                        "messages": [
                            {
                                "role": "system",
                                "content": "Ты - эксперт по нормативным документам и стандартам. Отвечай на русском языке, основываясь на предоставленных документах."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "temperature": self.TEMPERATURE,
                        "max_tokens": self.MAX_TOKENS,
                        "stream": False,
                        "top_p": 0.9,
                        "frequency_penalty": 0.1,
                        "presence_penalty": 0.1
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    ai_response = data.get("choices", [{}])[0].get("message", {}).get("content", "Не удалось сгенерировать ответ.")
                    
                    # Постобработка ответа
                    ai_response = self._post_process_response(ai_response)
                    
                    return ai_response
                else:
                    logger.error(f"❌ [NTD_CONSULTATION] VLLM error: {response.status_code} - {response.text}")
                    return "Произошла ошибка при генерации ответа. Попробуйте еще раз."
                    
        except Exception as e:
            logger.error(f"❌ [NTD_CONSULTATION] Generation error: {e}")
            return "Произошла ошибка при генерации ответа. Попробуйте еще раз."
    
    def _build_enhanced_prompt(self, question: str, context: str, history: List[Dict[str, str]] = None) -> str:
        """Построение улучшенного промпта для ИИ"""
        
        system_prompt = """Ты - эксперт по нормативным документам и стандартам. Твоя задача - давать точные и полезные ответы на вопросы пользователей, основываясь на предоставленных нормативных документах.

ПРАВИЛА ОТВЕТА:
1. Отвечай ТОЛЬКО на основе предоставленных документов
2. Если в документах нет информации для ответа, честно скажи об этом
3. Цитируй конкретные пункты документов с указанием номера документа
4. Давай практические рекомендации и примеры
5. Отвечай на русском языке профессионально и точно
6. Структурируй ответ с использованием маркированных списков
7. Указывай источники информации в конце ответа
8. Если информация противоречива, укажи это

СТРУКТУРА ОТВЕТА:
- Краткий ответ на вопрос
- Детальное объяснение с цитатами
- Практические рекомендации
- Источники (номера документов)

Контекст из нормативных документов:
{context}

История диалога:
{history}

Вопрос пользователя: {question}

Ответ:"""

        # Формирование истории диалога
        history_text = ""
        if history:
            history_parts = []
            for msg in history[-3:]:  # Последние 3 сообщения
                role = "Пользователь" if msg["role"] == "user" else "ИИ"
                content = msg['content'][:200] + "..." if len(msg['content']) > 200 else msg['content']
                history_parts.append(f"{role}: {content}")
            history_text = "\n".join(history_parts)
        
        return system_prompt.format(
            context=context,
            history=history_text,
            question=question
        )
    
    def _post_process_response(self, response: str) -> str:
        """Постобработка ответа ИИ"""
        # Убираем лишние пробелы и переносы
        response = response.strip()
        
        # Убираем повторяющиеся фразы
        lines = response.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if line and line not in cleaned_lines:
                cleaned_lines.append(line)
        
        response = '\n'.join(cleaned_lines)
        
        # Добавляем структуру если её нет
        if not response.startswith(('•', '-', '1.', '2.')):
            # Разбиваем на абзацы и добавляем маркеры
            paragraphs = response.split('\n\n')
            if len(paragraphs) > 1:
                response = '\n\n'.join([f"• {p.strip()}" if not p.strip().startswith('•') else p.strip() for p in paragraphs])
        
        return response
    
    def _prepare_sources(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Подготовка списка источников для ответа"""
        sources = []
        
        for doc in documents:
            source = {
                "title": doc.get("title", "Неизвестный документ"),
                "filename": doc.get("filename", ""),
                "category": doc.get("category", ""),
                "page": doc.get("page", 1),
                "relevance_score": round(doc.get("score", 0), 3),
                "document_type": doc.get("document_type", ""),
                "document_number": doc.get("document_number", ""),
                "chunk_type": doc.get("chunk_type", "text")
            }
            
            # Добавляем дополнительную информацию
            if doc.get("semantic_context"):
                source["context"] = doc["semantic_context"][:100] + "..."
            
            sources.append(source)
        
        return sources
    
    def _calculate_confidence(self, documents: List[Dict[str, Any]], response: str) -> float:
        """Расчет уверенности в ответе на основе релевантности документов и качества ответа"""
        if not documents:
            return 0.0
        
        # Базовый скор на основе релевантности документов
        avg_score = sum(doc.get("score", 0) for doc in documents) / len(documents)
        
        # Бонус за количество документов
        doc_bonus = min(len(documents) / 5.0, 0.2)
        
        # Бонус за качество ответа
        response_quality = 0.0
        if response and len(response) > 100:
            response_quality = min(len(response) / 1000.0, 0.3)
        
        # Бонус за важность документов
        importance_bonus = sum(doc.get("importance_level", 1) for doc in documents) / len(documents) * 0.1
        
        # Итоговая уверенность
        confidence = avg_score + doc_bonus + response_quality + importance_bonus
        
        # Нормализация к диапазону 0-1
        confidence = min(confidence, 1.0)
        
        return round(confidence, 3)
    
    async def get_consultation_stats(self) -> Dict[str, Any]:
        """Получить статистику консультаций"""
        try:
            def _get_stats(conn):
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT 
                            COUNT(*) as total_consultations,
                            COUNT(DISTINCT user_id) as unique_users,
                            AVG(confidence_score) as avg_confidence,
                            MAX(created_at) as last_consultation,
                            AVG(processing_time) as avg_processing_time
                        FROM ntd_consultations
                        WHERE created_at >= NOW() - INTERVAL '30 days'
                    """)
                    result = cursor.fetchone()
                    return {
                        "total_consultations": result[0] or 0,
                        "unique_users": result[1] or 0,
                        "avg_confidence": round(result[2] or 0, 3),
                        "last_consultation": result[3],
                        "avg_processing_time": round(result[4] or 0, 3)
                    }
            
            stats = self.db_conn.execute_in_transaction(_get_stats)
            
            # Добавляем информацию о кэше
            stats["cache_size"] = len(self.cache)
            stats["cache_hit_rate"] = self._calculate_cache_hit_rate()
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ [NTD_CONSULTATION] Stats error: {e}")
            return {
                "total_consultations": 0,
                "unique_users": 0,
                "avg_confidence": 0.0,
                "last_consultation": None,
                "avg_processing_time": 0.0,
                "cache_size": len(self.cache),
                "cache_hit_rate": 0.0
            }
    
    def _calculate_cache_hit_rate(self) -> float:
        """Расчет процента попаданий в кэш"""
        # Простая реализация - можно улучшить с помощью счетчиков
        return 0.0  # Пока возвращаем 0, так как нет статистики
    
    async def clear_cache(self) -> Dict[str, Any]:
        """Очистка кэша"""
        cache_size = len(self.cache)
        self.cache.clear()
        logger.info(f"🗑️ [NTD_CONSULTATION] Cache cleared: {cache_size} entries")
        return {
            "status": "success",
            "cleared_entries": cache_size,
            "message": f"Cache cleared successfully. Removed {cache_size} entries."
        }
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Получить статистику кэша"""
        current_time = time.time()
        valid_entries = 0
        expired_entries = 0
        
        for entry in self.cache.values():
            if current_time - entry['timestamp'] < self.cache_ttl:
                valid_entries += 1
            else:
                expired_entries += 1
        
        return {
            "total_entries": len(self.cache),
            "valid_entries": valid_entries,
            "expired_entries": expired_entries,
            "cache_ttl": self.cache_ttl,
            "cache_size_mb": len(json.dumps(self.cache)) / (1024 * 1024)
        }
