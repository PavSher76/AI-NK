import logging
import asyncio
from typing import List, Dict, Any, Optional
import httpx
from datetime import datetime
import numpy as np
import requests
# from sentence_transformers import SentenceTransformer  # Отключено для тестирования

logger = logging.getLogger(__name__)

class NTDConsultationService:
    """Сервис для консультации по нормативным документам"""
    
    def __init__(self, db_connection, qdrant_client, ollama_url: str = "http://vllm:8000", rag_service=None):
        self.db_conn = db_connection
        self.qdrant_client = qdrant_client
        self.ollama_url = ollama_url
        self.collection_name = "normative_documents"
        self.rag_service = rag_service  # Ссылка на основной RAG сервис
        self.embedding_model = None
        self._load_embedding_model()
        
    def _load_embedding_model(self):
        """Загрузка модели эмбеддингов"""
        try:
            # Если есть доступ к RAG сервису, используем его модель
            if self.rag_service and hasattr(self.rag_service, 'embedding_model'):
                self.embedding_model = self.rag_service.embedding_model
                logger.info("✅ [NTD_CONSULTATION] Using embedding model from RAG service")
            else:
                # Иначе загружаем собственную модель
                # Используем простые хеш-эмбеддинги для тестирования
                self.embedding_model = None
                logger.info("✅ [NTD_CONSULTATION] Using simple hash embeddings for testing")
        except Exception as e:
            logger.error(f"❌ [NTD_CONSULTATION] Error loading embedding model: {e}")
            self.embedding_model = None
    
    def get_consultation(self, message: str, history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Получить консультацию по нормативным документам (синхронная версия)
        """
        try:
            logger.info(f"🔍 [NTD_CONSULTATION] Processing question: {message[:100]}...")
            
            # 1. Поиск релевантных документов
            relevant_docs = self._search_relevant_documents(message)
            
            if not relevant_docs:
                logger.warning("⚠️ [NTD_CONSULTATION] No relevant documents found")
                return {
                    "response": "К сожалению, я не нашел релевантной информации в базе нормативных документов для вашего вопроса. Попробуйте переформулировать вопрос или обратитесь к специалисту.",
                    "sources": [],
                    "confidence": 0.0,
                    "documents_used": 0
                }
            
            # 2. Формирование контекста
            context = self._build_context(relevant_docs)
            
            # 3. Генерация ответа с помощью ИИ
            response = self._generate_simple_response(message, context)
            
            # 4. Подготовка источников
            sources = self._prepare_sources(relevant_docs)
            
            logger.info(f"✅ [NTD_CONSULTATION] Response generated successfully")
            
            return {
                "response": response,
                "sources": sources,
                "confidence": self._calculate_confidence(relevant_docs),
                "documents_used": len(relevant_docs)
            }
            
        except Exception as e:
            logger.error(f"❌ [NTD_CONSULTATION] Error: {e}")
            return {
                "response": "Произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте еще раз или обратитесь к администратору системы.",
                "sources": [],
                "confidence": 0.0,
                "error": str(e)
            }
    
    def _search_relevant_documents(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Поиск релевантных документов в базе
        """
        try:
            if not self.embedding_model:
                logger.warning("⚠️ [NTD_CONSULTATION] Embedding model not available, using fallback")
                return self._fallback_search(query, limit)
            
            # Используем централизованную модель эмбеддингов
            if self.rag_service and hasattr(self.rag_service, 'create_single_embedding'):
                query_embedding = self.rag_service.create_single_embedding(query)
            else:
                query_embedding = self.embedding_model.encode(query).tolist()
            
            if query_embedding is None:
                logger.warning("⚠️ [NTD_CONSULTATION] Failed to create query embedding, using fallback")
                return self._fallback_search(query, limit)
            
            search_results = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                with_payload=True,
                with_vectors=False,
                score_threshold=0.3
            )
            
            documents = []
            for result in search_results:
                doc_info = self._get_document_info(result.id)
                if doc_info:
                    documents.append({
                        "id": result.id,
                        "score": result.score,
                        "content": result.payload.get("content", ""),
                        "title": doc_info.get("title", ""),
                        "filename": doc_info.get("filename", ""),
                        "category": doc_info.get("category", ""),
                        "page": result.payload.get("page", 1),
                        "chunk_type": result.payload.get("chunk_type", "paragraph")
                    })
            
            logger.info(f"🔍 [NTD_CONSULTATION] Found {len(documents)} relevant documents")
            return documents
            
        except Exception as e:
            logger.error(f"❌ [NTD_CONSULTATION] Search error: {e}")
            return self._fallback_search(query, limit)
    
    def _fallback_search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Резервный поиск без векторизации"""
        try:
            def _search_in_db(conn):
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT 
                            nc.id, nc.document_id, nc.content, nc.chunk_type, nc.page_number,
                            ud.original_filename as title, ud.category
                        FROM normative_chunks nc
                        LEFT JOIN uploaded_documents ud ON nc.document_id = ud.id
                        WHERE nc.content ILIKE %s
                        ORDER BY nc.content ILIKE %s DESC, nc.id
                        LIMIT %s
                    """, (f'%{query}%', f'%{query}%', limit))
                    
                    results = cursor.fetchall()
                    documents = []
                    for row in results:
                        documents.append({
                            "id": row[0], "score": 0.5, "content": row[2], "title": row[5] or f"Документ {row[1]}",
                            "filename": row[5] or "", "category": row[6] or "unknown", "page": row[4] or 1,
                            "chunk_type": row[3] or "paragraph"
                        })
                    return documents
            
            return self.db_conn.execute_in_transaction(_search_in_db)
            
        except Exception as e:
            logger.error(f"❌ [NTD_CONSULTATION] Fallback search error: {e}")
            return []
    
    def _get_document_info(self, doc_id: int) -> Optional[Dict[str, Any]]:
        """Получить информацию о документе из БД"""
        try:
            def _get_info(conn):
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT ud.original_filename as title, ud.original_filename as filename,
                               ud.category, ud.upload_date
                        FROM uploaded_documents ud
                        WHERE ud.id = %s
                    """, (doc_id,))
                    result = cursor.fetchone()
                    if result:
                        return {"title": result[0], "filename": result[1], "category": result[2], "upload_date": result[3]}
                    return None
            
            return self.db_conn.execute_in_transaction(_get_info)
            
        except Exception as e:
            logger.error(f"❌ [NTD_CONSULTATION] Error getting document info: {e}")
            return None
    
    def _build_context(self, documents: List[Dict[str, Any]]) -> str:
        """Построение контекста из найденных документов"""
        if not documents: return ""
        context_parts = ["Релевантные нормативные документы:", "=" * 50]
        for i, doc in enumerate(documents, 1):
            context_parts.append(f"\nДокумент {i}: {doc['title']}")
            context_parts.append(f"Категория: {doc['category']}")
            context_parts.append(f"Страница: {doc['page']}")
            context_parts.append(f"Тип: {doc['chunk_type']}")
            context_parts.append(f"Релевантность: {doc['score']:.3f}")
            context_parts.append(f"Содержание:\n{doc['content'][:800]}...")
            context_parts.append("-" * 30)
        return "\n".join(context_parts)
    
    def _generate_simple_response(self, question: str, context: str = "") -> str:
        """
        Генерация ответа с контекстом (синхронная)
        """
        try:
            if context:
                prompt = f"""
Ты - эксперт по нормативным документам и стандартам. Отвечай на русском языке, основываясь на предоставленных документах.
Контекст из нормативных документов:
{context}
Вопрос пользователя: {question}
Пожалуйста, дай подробный и полезный ответ, основываясь на предоставленных документах. Если в документах нет информации для ответа, честно скажи об этом.
"""
            else:
                prompt = f"""
Ты - эксперт по нормативным документам и стандартам. Отвечай на русском языке.
Вопрос пользователя: {question}
Пожалуйста, дай подробный и полезный ответ, основываясь на своих знаниях о нормативных документах, стандартах и технических требованиях.
"""
            
            response = requests.post(
                f"{self.ollama_url}/v1/chat/completions",
                json={
                    "model": "llama3.1:8b",
                    "messages": [{"role": "system", "content": "Ты - эксперт по нормативным документам и стандартам. Отвечай на русском языке, основываясь на предоставленных документах."}, {"role": "user", "content": prompt}],
                    "temperature": 0.7, "max_tokens": 2000, "stream": False
                },
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"]
            else:
                logger.error(f"❌ [NTD_CONSULTATION] VLLM request failed: {response.status_code}")
                return "Извините, произошла ошибка при генерации ответа. Попробуйте позже."
                
        except Exception as e:
            logger.error(f"❌ [NTD_CONSULTATION] Error generating response: {e}")
            return "Извините, произошла ошибка при обработке запроса. Попробуйте позже."
    
    def _prepare_sources(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Подготовка списка источников для ответа"""
        sources = []
        for doc in documents:
            sources.append({
                "title": doc.get("title", "Неизвестный документ"), "filename": doc.get("filename", ""),
                "category": doc.get("category", ""), "page": doc.get("page", 1),
                "chunk_type": doc.get("chunk_type", "paragraph"), "relevance_score": round(doc.get("score", 0), 3),
                "content_preview": doc.get("content", "")[:200] + "..." if len(doc.get("content", "")) > 200 else doc.get("content", "")
            })
        sources.sort(key=lambda x: x["relevance_score"], reverse=True)
        return sources
    
    def _calculate_confidence(self, documents: List[Dict[str, Any]]) -> float:
        """Расчет уверенности в ответе на основе релевантности документов"""
        if not documents: return 0.0
        avg_score = sum(doc.get("score", 0) for doc in documents) / len(documents)
        confidence = min(avg_score, 1.0)
        return round(confidence, 3)
    
    async def get_consultation_async(self, message: str, history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Получить консультацию по нормативным документам (асинхронная версия)
        """
        try:
            logger.info(f"🔍 [NTD_CONSULTATION] Processing question: {message[:100]}...")
            relevant_docs = self._search_relevant_documents(message) # Still synchronous search
            if not relevant_docs:
                logger.warning("⚠️ [NTD_CONSULTATION] No relevant documents found")
                return {"response": "К сожалению, я не нашел релевантной информации...", "sources": [], "confidence": 0.0, "documents_used": 0}
            context = self._build_context(relevant_docs)
            response = await self._generate_async_response(message, context)
            sources = self._prepare_sources(relevant_docs)
            logger.info(f"✅ [NTD_CONSULTATION] Response generated successfully")
            return {"response": response, "sources": sources, "confidence": self._calculate_confidence(relevant_docs), "documents_used": len(relevant_docs)}
        except Exception as e:
            logger.error(f"❌ [NTD_CONSULTATION] Error: {e}")
            return {"response": "Произошла ошибка при обработке вашего запроса...", "sources": [], "confidence": 0.0, "error": str(e)}
    
    async def _generate_async_response(self, question: str, context: str = "") -> str:
        """
        Асинхронная генерация ответа с контекстом
        """
        try:
            if context:
                prompt = f"""
Ты - эксперт по нормативным документам и стандартам. Отвечай на русском языке, основываясь на предоставленных документах.
Контекст из нормативных документов:
{context}
Вопрос пользователя: {question}
Пожалуйста, дай подробный и полезный ответ, основываясь на предоставленных документах. Если в документах нет информации для ответа, честно скажи об этом.
"""
            else:
                prompt = f"""
Ты - эксперт по нормативным документам и стандартам. Отвечай на русском языке.
Вопрос пользователя: {question}
Пожалуйста, дай подробный и полезный ответ, основываясь на своих знаниях о нормативных документах, стандартах и технических требованиях.
"""
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.ollama_url}/v1/chat/completions",
                    json={"model": "llama3.1:8b", "messages": [{"role": "system", "content": "Ты - эксперт по нормативным документам и стандартам. Отвечай на русском языке, основываясь на предоставленных документах."}, {"role": "user", "content": prompt}], "temperature": 0.7, "max_tokens": 2000, "stream": False}
                )
                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    logger.error(f"❌ [NTD_CONSULTATION] VLLM request failed: {response.status_code}")
                    return "Извините, произошла ошибка при генерации ответа. Попробуйте позже."
        except Exception as e:
            logger.error(f"❌ [NTD_CONSULTATION] Error generating response: {e}")
            return "Извините, произошла ошибка при обработке запроса. Попробуйте позже."
    
    def get_ntd_consultations_stats(self) -> Dict[str, Any]:
        """Получение статистики консультаций НТД"""
        try:
            return {
                "total_consultations": 0, "successful_consultations": 0, "average_response_time": 0.0,
                "popular_questions": [], "last_consultation": None,
                "embedding_model_available": self.embedding_model is not None
            }
        except Exception as e:
            logger.error(f"❌ [NTD_CONSULTATION_STATS] Error: {e}")
            return {"error": str(e)}
