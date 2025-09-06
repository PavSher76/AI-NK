import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class OllamaRAGServiceMethods:
    """Дополнительные методы для OllamaRAGService"""
    
    def __init__(self, rag_service):
        self.rag_service = rag_service
    
    def hybrid_search(self, query: str, k: int = 8, document_filter: Optional[str] = None, 
                     chapter_filter: Optional[str] = None, chunk_type_filter: Optional[str] = None, 
                     use_reranker: bool = True, fast_mode: bool = False, use_mmr: bool = True, 
                     use_intent_classification: bool = True) -> List[Dict[str, Any]]:
        """
        Гибридный поиск по нормативным документам с опциональным реранкингом
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
                    intent_classification = self.rag_service.intent_classifier.classify_intent(query)
                    query_rewriting = self.rag_service.intent_classifier.rewrite_query(query, intent_classification)
                    
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
            search_results = self.rag_service.hybrid_search_service.search(
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
                    reranked_results = self.rag_service.bge_reranker_service.rerank_with_fallback(
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
                        reranked_results = self.rag_service.reranker_service.rerank_search_results(
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
                            mmr_results = self.rag_service.mmr_service.diversify_results(
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
            query_embedding = self.rag_service.embedding_service.create_embedding(query)
            
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
            search_result = self.rag_service.qdrant_service.search_similar(
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
    
    def get_ntd_consultation(self, message: str, user_id: str, history: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Получение консультации по НТД с использованием структурированного контекста"""
        try:
            logger.info(f"💬 [NTD_CONSULTATION] Processing consultation request: '{message[:100]}...'")
            
            # Извлекаем код документа из запроса
            document_code = self.rag_service.document_parser.extract_document_code_from_query(message)
            logger.info(f"🔍 [NTD_CONSULTATION] Extracted document code: {document_code}")
            
            # Используем извлеченный код документа для поиска, если он найден
            search_query = document_code if document_code else message
            logger.info(f"🔍 [NTD_CONSULTATION] Using search query: {search_query}")
            
            # Отладочная информация о сервисах
            logger.info(f"🔍 [NTD_CONSULTATION] RAG service instance: {id(self.rag_service)}")
            logger.info(f"🔍 [NTD_CONSULTATION] Hybrid search service instance: {id(self.rag_service.hybrid_search_service)}")
            logger.info(f"🔍 [NTD_CONSULTATION] Qdrant service instance: {id(self.rag_service.hybrid_search_service.qdrant_service)}")
            
            # Получаем структурированный контекст
            structured_context = self.rag_service.get_structured_context(search_query, k=10)
            
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
            return f"**{top_result['document_title']}**\n\n{top_result['content']}"
    
    def _get_document_metadata(self, document_id: int) -> Dict[str, Any]:
        """Получение метаданных документа из базы данных"""
        try:
            with self.rag_service.db_manager.get_cursor() as cursor:
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
                        return self.rag_service.metadata_extractor.extract_document_metadata(original_filename, doc_id, file_path)
                    else:
                        logger.error(f"❌ [GET_DOCUMENT_METADATA] Invalid result format: {result}")
                        return self.rag_service.metadata_extractor.extract_document_metadata(f"error_doc_{document_id}", document_id)
                else:
                    logger.warning(f"⚠️ [GET_DOCUMENT_METADATA] Document {document_id} not found")
                    return self.rag_service.metadata_extractor.extract_document_metadata(f"unknown_doc_{document_id}", document_id)
                    
        except Exception as e:
            logger.error(f"❌ [GET_DOCUMENT_METADATA] Error getting document metadata: {e}")
            return self.rag_service.metadata_extractor.extract_document_metadata(f"error_doc_{document_id}", document_id)
