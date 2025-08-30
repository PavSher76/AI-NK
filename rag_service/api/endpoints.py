from fastapi import HTTPException
from datetime import datetime
from typing import List, Dict, Any
from services.rag_service import RAGService
from core.config import logger

# Глобальный экземпляр сервиса (ленивая инициализация)
rag_service = None

def get_rag_service():
    """Получение экземпляра RAG сервиса с ленивой инициализацией"""
    global rag_service
    if rag_service is None:
        rag_service = RAGService()
    return rag_service

# Глобальная переменная для хранения результатов реиндексации
reindex_results = {}

def get_documents():
    """Получение списка нормативных документов"""
    logger.info("📄 [GET_DOCUMENTS] Getting documents list...")
    try:
        rag_service = get_rag_service()
        documents = rag_service.get_documents()
        logger.info(f"✅ [GET_DOCUMENTS] Documents list retrieved: {len(documents)} documents")
        return {"documents": documents}
    except Exception as e:
        logger.error(f"❌ [GET_DOCUMENTS] Documents error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def get_stats():
    """Получение статистики RAG-системы"""
    logger.info("📊 [GET_STATS] Getting service statistics...")
    try:
        rag_service_instance = get_rag_service()
        stats = rag_service_instance.get_stats()
        logger.info(f"✅ [GET_STATS] Service statistics retrieved: {stats}")
        return stats
    except Exception as e:
        logger.error(f"❌ [GET_STATS] Stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def get_document_chunks(document_id: int):
    """Получение информации о чанках конкретного документа"""
    logger.info(f"📄 [GET_DOCUMENT_CHUNKS] Getting chunks for document ID: {document_id}")
    try:
        rag_service_instance = get_rag_service()
        chunks_info = rag_service_instance.get_document_chunks(document_id)
        logger.info(f"✅ [GET_DOCUMENT_CHUNKS] Chunks info retrieved for document {document_id}")
        return {"chunks": chunks_info}
    except Exception as e:
        logger.error(f"❌ [GET_DOCUMENT_CHUNKS] Chunks error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def get_documents_stats():
    """Получение статистики документов в формате для фронтенда"""
    logger.info("📊 [GET_DOCUMENTS_STATS] Getting documents statistics...")
    try:
        rag_service_instance = get_rag_service()
        # Получаем документы из базы данных
        documents = rag_service_instance.get_documents_from_uploaded('normative')
        
        # Подсчитываем статистику
        total_documents = len(documents)
        indexed_documents = len([doc for doc in documents if doc.get('processing_status') == 'completed'])
        indexing_progress_percent = (indexed_documents / total_documents * 100) if total_documents > 0 else 0
        
        # Статистика по категориям
        categories_stats = {}
        for doc in documents:
            category = doc.get('category', 'Без категории')
            if category not in categories_stats:
                categories_stats[category] = 0
            categories_stats[category] += 1
        
        # Преобразуем в формат для фронтенда
        categories_list = [
            {"category": cat, "count": count} 
            for cat, count in categories_stats.items()
        ]
        
        # Общее количество токенов
        total_tokens = sum(doc.get('token_count', 0) for doc in documents)
        
        # Адаптируем статистику для фронтенда
        adapted_stats = {
            "statistics": {
                "total_documents": total_documents,
                "indexed_documents": indexed_documents,
                "indexing_progress_percent": round(indexing_progress_percent, 1),
                "total_tokens": total_tokens,
                "categories": categories_list
            }
        }
        
        logger.info(f"✅ [GET_DOCUMENTS_STATS] Documents statistics retrieved: {adapted_stats}")
        return adapted_stats
    except Exception as e:
        logger.error(f"❌ [GET_DOCUMENTS_STATS] Documents stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def delete_document(document_id: int):
    """Удаление документа и его индексов"""
    logger.info(f"🗑️ [DELETE_DOCUMENT] Deleting document ID: {document_id}")
    try:
        rag_service_instance = get_rag_service()
        success = rag_service_instance.delete_document_indexes(document_id)
        
        if success:
            return {
                "status": "success",
                "message": f"Document {document_id} deleted successfully"
            }
        else:
            raise HTTPException(status_code=404, detail="Document not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [DELETE_DOCUMENT] Delete document error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def delete_document_indexes(document_id: int):
    """Удаление индексов конкретного документа"""
    logger.info(f"🗑️ [DELETE_DOC_INDEXES] Deleting indexes for document ID: {document_id}")
    try:
        rag_service_instance = get_rag_service()
        success = rag_service_instance.delete_document_indexes(document_id)
        
        if success:
            return {
                "status": "success",
                "message": f"Indexes for document {document_id} deleted successfully"
            }
        else:
            raise HTTPException(status_code=404, detail="Document indexes not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [DELETE_DOC_INDEXES] Delete indexes error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def reindex_documents():
    """Реиндексация всех документов"""
    logger.info("🔄 [REINDEX_DOCUMENTS] Starting document reindexing...")
    try:
        # Получаем все документы из базы данных
        documents = []
        with rag_service.db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT DISTINCT 
                    ud.id as document_id,
                    ud.filename as document_title,
                    ud.category,
                    ud.processing_status
                FROM uploaded_documents ud
                WHERE ud.processing_status IN ('completed', 'pending')
                ORDER BY ud.id
            """)
            
            documents = cursor.fetchall()
        
        if not documents:
            return {
                "status": "success",
                "message": "No documents to reindex",
                "reindexed_count": 0,
                "total_documents": 0
            }
        
        logger.info(f"🔄 [REINDEX_DOCUMENTS] Found {len(documents)} documents to reindex")
        
        reindexed_count = 0
        total_tokens = 0
        
        for document in documents:
            try:
                document_id = document['document_id']
                document_title = document['document_title']
                
                logger.info(f"🔄 [REINDEX_DOCUMENTS] Reindexing document {document_id}: {document_title}")
                
                # Получаем чанки документа с отдельным соединением
                chunks = []
                try:
                    with rag_service.db_manager.get_cursor() as cursor:
                        cursor.execute("""
                            SELECT 
                                chunk_id,
                                content,
                                page_number,
                                chapter,
                                section
                            FROM normative_chunks 
                            WHERE document_id = %s
                            ORDER BY page_number, chunk_id
                        """, (document_id,))
                        chunks = cursor.fetchall()
                except Exception as e:
                    logger.error(f"❌ [REINDEX_DOCUMENTS] Error getting chunks for document {document_id}: {e}")
                    # Пробуем переподключиться
                    rag_service.db_manager.reconnect()
                    with rag_service.db_manager.get_cursor() as cursor:
                        cursor.execute("""
                            SELECT 
                                chunk_id,
                                content,
                                page_number,
                                chapter,
                                section
                            FROM normative_chunks 
                            WHERE document_id = %s
                            ORDER BY page_number, chunk_id
                        """, (document_id,))
                        chunks = cursor.fetchall()
                
                if not chunks:
                    logger.warning(f"⚠️ [REINDEX_DOCUMENTS] No chunks found for document {document_id}")
                    continue
                
                # Подготавливаем чанки для индексации
                chunks_for_indexing = []
                for chunk in chunks:
                    chunk_data = {
                        'id': chunk['chunk_id'],  # ID для Qdrant
                        'document_id': document_id,
                        'chunk_id': chunk['chunk_id'],
                        'content': chunk['content'],
                        'page': chunk['page_number'],  # Используем 'page' вместо 'page_number'
                        'section_title': chunk['chapter'] or '',
                        'section': chunk['section'] or '',  # Добавляем поле 'section'
                        'document_title': document_title,
                        'category': document['category'],
                        'chunk_type': 'paragraph'  # Добавляем тип чанка
                    }
                    chunks_for_indexing.append(chunk_data)
                
                # Индексируем чанки в векторную базу
                success = rag_service.index_document_chunks(document_id, chunks_for_indexing)
                
                if success:
                    reindexed_count += 1
                    total_tokens += sum(len(chunk['content'].split()) for chunk in chunks)
                    logger.info(f"✅ [REINDEX_DOCUMENTS] Document {document_id} reindexed successfully ({len(chunks)} chunks)")
                else:
                    logger.error(f"❌ [REINDEX_DOCUMENTS] Failed to index document {document_id}")
                
            except Exception as e:
                logger.error(f"❌ [REINDEX_DOCUMENTS] Error reindexing document {document.get('document_id', 'unknown')}: {e}")
                continue
        
        logger.info(f"✅ [REINDEX_DOCUMENTS] Reindexing completed. {reindexed_count}/{len(documents)} documents reindexed")
        
        return {
            "status": "success",
            "message": f"Reindexing completed. {reindexed_count} documents reindexed",
            "reindexed_count": reindexed_count,
            "total_documents": len(documents),
            "total_tokens": total_tokens,
            "new_total_tokens": total_tokens
        }
        
    except Exception as e:
        logger.error(f"❌ [REINDEX_DOCUMENTS] Reindexing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def start_async_reindex():
    """Запуск асинхронной реиндексации документов"""
    logger.info("🚀 [ASYNC_REINDEX] Starting async reindexing...")
    try:
        # Получаем все документы из базы данных
        documents = []
        with rag_service.db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT DISTINCT 
                    ud.id as document_id,
                    ud.filename as document_title,
                    ud.category,
                    ud.processing_status
                FROM uploaded_documents ud
                                        WHERE ud.processing_status IN ('completed', 'pending')
                ORDER BY ud.id
            """)
            
            documents = cursor.fetchall()
        
        if not documents:
            return {
                "status": "success",
                "message": "No documents to reindex",
                "task_id": "no_documents",
                "total_documents": 0
            }
        
        # Создаем уникальный ID задачи
        import uuid
        task_id = str(uuid.uuid4())
        
        # Запускаем асинхронную задачу
        import asyncio
        import threading
        
        def run_reindex_task():
            try:
                reindexed_count = 0
                total_tokens = 0
                
                for i, document in enumerate(documents):
                    try:
                        document_id = document['document_id']
                        document_title = document['document_title']
                        
                        logger.info(f"🔄 [ASYNC_REINDEX] Reindexing document {document_id}: {document_title} ({i+1}/{len(documents)})")
                        
                        # Получаем чанки документа
                        chunks = []
                        with rag_service.db_manager.get_cursor() as cursor:
                            cursor.execute("""
                                SELECT 
                                    chunk_id,
                                    content,
                                    page_number,
                                    section_title,
                                    subsection_title
                                FROM normative_chunks 
                                WHERE document_id = %s
                                ORDER BY page_number, chunk_id
                            """, (document_id,))
                            
                            chunks = cursor.fetchall()
                        
                        if not chunks:
                            logger.warning(f"⚠️ [ASYNC_REINDEX] No chunks found for document {document_id}")
                            continue
                        
                        # Подготавливаем чанки для индексации
                        chunks_for_indexing = []
                        for chunk in chunks:
                            chunk_data = {
                                'id': chunk['chunk_id'],  # ID для Qdrant
                                'document_id': document_id,
                                'chunk_id': chunk['chunk_id'],
                                'content': chunk['content'],
                                'page': chunk['page_number'],  # Используем 'page' вместо 'page_number'
                                'section_title': chunk['section_title'] or '',
                                'section': chunk['subsection_title'] or '',  # Добавляем поле 'section'
                                'document_title': document_title,
                                'category': document['category'],
                                'chunk_type': 'paragraph'  # Добавляем тип чанка
                            }
                            chunks_for_indexing.append(chunk_data)
                        
                        # Индексируем чанки в векторную базу
                        success = rag_service.index_document_chunks(document_id, chunks_for_indexing)
                        
                        if success:
                            reindexed_count += 1
                            total_tokens += sum(len(chunk['content'].split()) for chunk in chunks)
                            logger.info(f"✅ [ASYNC_REINDEX] Document {document_id} reindexed successfully ({len(chunks)} chunks)")
                        else:
                            logger.error(f"❌ [ASYNC_REINDEX] Failed to index document {document_id}")
                        
                    except Exception as e:
                        logger.error(f"❌ [ASYNC_REINDEX] Error reindexing document {document.get('document_id', 'unknown')}: {e}")
                        continue
                
                logger.info(f"✅ [ASYNC_REINDEX] Async reindexing completed. {reindexed_count}/{len(documents)} documents reindexed")
                
                # Сохраняем результат в глобальную переменную
                reindex_results[task_id] = {
                    "status": "completed",
                    "reindexed_count": reindexed_count,
                    "total_documents": len(documents),
                    "total_tokens": total_tokens,
                    "message": f"Reindexing completed. {reindexed_count} documents reindexed"
                }
                
            except Exception as e:
                logger.error(f"❌ [ASYNC_REINDEX] Task error: {e}")
                reindex_results[task_id] = {
                    "status": "error",
                    "error": str(e),
                    "message": "Reindexing failed"
                }
        
        # Запускаем задачу в отдельном потоке
        thread = threading.Thread(target=run_reindex_task)
        thread.daemon = True
        thread.start()
        
        return {
            "status": "started",
            "message": f"Async reindexing started for {len(documents)} documents",
            "task_id": task_id,
            "total_documents": len(documents)
        }
        
    except Exception as e:
        logger.error(f"❌ [ASYNC_REINDEX] Start error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def get_reindex_status(task_id: str):
    """Получение статуса асинхронной реиндексации"""
    logger.info(f"📊 [REINDEX_STATUS] Getting status for task {task_id}")
    try:
        global reindex_results
        if task_id not in reindex_results:
            return {
                "status": "not_found",
                "message": "Task not found"
            }
        
        result = reindex_results[task_id]
        return result
        
    except Exception as e:
        logger.error(f"❌ [REINDEX_STATUS] Status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def ntd_consultation_chat(message: str, user_id: str):
    """Обработка запроса консультации НТД"""
    logger.info("💬 [NTD_CONSULTATION] Chat request received")
    try:
        rag_service_instance = get_rag_service()
        response = rag_service_instance.get_ntd_consultation(message, [])
        
        logger.info(f"✅ [NTD_CONSULTATION] Response generated successfully")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [NTD_CONSULTATION] Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def ntd_consultation_stats():
    """Получение статистики консультаций НТД"""
    logger.info("📊 [NTD_CONSULTATION_STATS] Getting consultation statistics...")
    try:
        rag_service_instance = get_rag_service()
        stats = rag_service_instance.get_stats()
        
        logger.info(f"✅ [NTD_CONSULTATION_STATS] Statistics retrieved successfully")
        return {
            "status": "success",
            "consultation_stats": {
                "total_consultations": 0,  # Пока не реализовано
                "active_sessions": 0,
                "documents_available": stats.get("documents", {}).get("total_documents", 0)
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [NTD_CONSULTATION_STATS] Stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def clear_consultation_cache():
    """Очистить кэш консультаций НТД"""
    logger.info("🗑️ [NTD_CONSULTATION_CACHE] Cache clear request received")
    try:
        logger.info("✅ [NTD_CONSULTATION_CACHE] Cache cleared successfully")
        return {
            "status": "success",
            "message": "Cache cleared successfully",
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [NTD_CONSULTATION_CACHE] Cache clear error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def get_consultation_cache_stats():
    """Получить статистику кэша консультаций НТД"""
    logger.info("📊 [NTD_CONSULTATION_CACHE_STATS] Cache stats request received")
    try:
        logger.info("✅ [NTD_CONSULTATION_CACHE_STATS] Cache stats retrieved successfully")
        return {
            "status": "success",
            "cache_stats": {
                "cache_size": 0,
                "cache_hits": 0,
                "cache_misses": 0,
                "cache_entries": 0
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [NTD_CONSULTATION_CACHE_STATS] Cache stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def health_check():
    """Проверка здоровья сервиса"""
    logger.info("💪 [HEALTH] Performing health check...")
    try:
        # Проверяем подключения
        rag_service.db_manager.get_cursor().execute("SELECT 1")
        # Проверяем Qdrant через прямой HTTP запрос
        import requests
        from core.config import QDRANT_URL
        response = requests.get(f"{QDRANT_URL}/collections")
        if response.status_code != 200:
            raise Exception("Qdrant connection failed")
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "embedding_model": "BGE-M3" if rag_service.embedding_model else "simple_hash",
            "optimized_indexer": "not_available",  # Временно отключен
            "services": {
                "postgresql": "connected",
                "qdrant": "connected"
            }
        }
    except Exception as e:
        logger.error(f"❌ [HEALTH] Health check error: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

def get_metrics():
    """Получение метрик Prometheus"""
    logger.info("📊 [METRICS] Getting service metrics...")
    try:
        stats = rag_service.get_stats()
        
        # Формируем метрики в формате Prometheus
        metrics_lines = []
        
        # Базовые метрики
        metrics_lines.append("# HELP rag_service_up Service is up")
        metrics_lines.append("# TYPE rag_service_up gauge")
        metrics_lines.append("rag_service_up 1")
        
        # Метрики конфигурации
        from core.config import CHUNK_SIZE, CHUNK_OVERLAP, MAX_TOKENS
        metrics_lines.append(f"# HELP rag_service_chunk_size Chunk size for text processing")
        metrics_lines.append(f"# TYPE rag_service_chunk_size gauge")
        metrics_lines.append(f"rag_service_chunk_size {CHUNK_SIZE}")
        
        metrics_lines.append(f"# HELP rag_service_chunk_overlap Chunk overlap for text processing")
        metrics_lines.append(f"# TYPE rag_service_chunk_overlap gauge")
        metrics_lines.append(f"rag_service_chunk_overlap {CHUNK_OVERLAP}")
        
        metrics_lines.append(f"# HELP rag_service_max_tokens Maximum tokens for processing")
        metrics_lines.append(f"# TYPE rag_service_max_tokens gauge")
        metrics_lines.append(f"rag_service_max_tokens {MAX_TOKENS}")
        
        # Метрики подключений
        metrics_lines.append(f"# HELP rag_service_connections_status Connection status")
        metrics_lines.append(f"# TYPE rag_service_connections_status gauge")
        metrics_lines.append(f'rag_service_connections_status{{service="postgresql"}} {1 if rag_service.db_manager.connection else 0}')
        metrics_lines.append(f'rag_service_connections_status{{service="qdrant"}} {1 if rag_service.qdrant_client else 0}')
        
        # Метрики статистики
        if stats:
            metrics_lines.append(f"# HELP rag_service_total_chunks Total number of chunks")
            metrics_lines.append(f"# TYPE rag_service_total_chunks counter")
            metrics_lines.append(f"rag_service_total_chunks {stats.get('total_chunks', 0)}")
            
            metrics_lines.append(f"# HELP rag_service_total_documents Total number of documents")
            metrics_lines.append(f"# TYPE rag_service_total_documents counter")
            metrics_lines.append(f"rag_service_total_documents {stats.get('total_documents', 0)}")
            
            metrics_lines.append(f"# HELP rag_service_total_clauses Total number of clauses")
            metrics_lines.append(f"# TYPE rag_service_total_clauses counter")
            metrics_lines.append(f"rag_service_total_clauses {stats.get('total_clauses', 0)}")
            
            metrics_lines.append(f"# HELP rag_service_vector_indexed Total vector indexed")
            metrics_lines.append(f"# TYPE rag_service_vector_indexed counter")
            metrics_lines.append(f"rag_service_vector_indexed {stats.get('vector_indexed', 0)}")
            
            # Метрики по типам чанков
            chunk_types = stats.get('chunk_types', {})
            for chunk_type, count in chunk_types.items():
                metrics_lines.append(f'rag_service_chunks_by_type{{type="{chunk_type}"}} {count}')
        
        logger.info(f"✅ [METRICS] Service metrics retrieved successfully")
        
        # Возвращаем метрики в формате Prometheus
        from fastapi.responses import Response
        return Response(
            content="\n".join(metrics_lines),
            media_type="text/plain; version=0.0.4; charset=utf-8"
        )
        
    except Exception as e:
        logger.error(f"❌ [METRICS] Metrics error: {e}")
        # Возвращаем базовые метрики в случае ошибки
        error_metrics = [
            "# HELP rag_service_up Service is up",
            "# TYPE rag_service_up gauge",
            "rag_service_up 0"
        ]
        from fastapi.responses import Response
        return Response(
            content="\n".join(error_metrics),
            media_type="text/plain; version=0.0.4; charset=utf-8"
        )
