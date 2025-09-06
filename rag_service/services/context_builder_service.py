import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import requests
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Получаем URL Ollama из переменной окружения
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434")

@dataclass
class ContextCandidate:
    """Структура для кандидата контекста"""
    doc: str  # Код документа (ГОСТ, СП и т.д.)
    section: str  # Раздел/глава
    page: int  # Номер страницы
    snippet: str  # Фрагмент текста
    why: str  # Причина релевантности (scope match, terms, etc.)
    score: float  # Оценка релевантности
    content: str  # Полное содержимое чанка
    chunk_id: str  # ID чанка
    document_title: str  # Полное название документа
    section_title: str  # Название раздела
    chunk_type: str  # Тип чанка
    metadata: Dict[str, Any]  # Дополнительные метаданные

@dataclass
class ContextSummary:
    """Структура для сводки контекста"""
    topic: str  # О чем раздел
    norm_type: str  # Тип нормы (обязательная/рекомендательная)
    key_points: List[str]  # Ключевые моменты
    relevance_reason: str  # Причина релевантности

class ContextBuilderService:
    """Сервис для построения структурированного контекста"""
    
    def __init__(self, ollama_url: str = None):
        self.ollama_url = ollama_url or OLLAMA_URL
        self.model_name = "llama3.2:3b"  # Модель для генерации сводок
        logger.info(f"🏗️ [CONTEXT_BUILDER] Initialized with {self.model_name} at {self.ollama_url}")
    
    def build_structured_context(self, search_results: List[Dict[str, Any]], query: str) -> Dict[str, Any]:
        """
        Построение структурированного контекста из результатов поиска
        
        Args:
            search_results: Результаты поиска из RAG системы
            query: Исходный запрос пользователя
            
        Returns:
            Структурированный контекст с мета-сводкой
        """
        try:
            logger.info(f"🏗️ [CONTEXT_BUILDER] Building structured context for {len(search_results)} results")
            
            # 1. Преобразуем результаты в кандидатов контекста
            candidates = self._convert_to_candidates(search_results)
            
            # 2. Дедупликация и слияние соседних чанков
            deduplicated_candidates = self._deduplicate_and_merge(candidates)
            
            # 3. Генерируем auto-summary для каждого кандидата
            enriched_candidates = self._generate_summaries(deduplicated_candidates, query)
            
            # 4. Формируем финальный структурированный контекст
            structured_context = self._build_final_context(enriched_candidates, query)
            
            logger.info(f"✅ [CONTEXT_BUILDER] Structured context built with {len(enriched_candidates)} candidates")
            return structured_context
            
        except Exception as e:
            logger.error(f"❌ [CONTEXT_BUILDER] Error building structured context: {e}")
            # Возвращаем fallback контекст
            return self._build_fallback_context(search_results, query)
    
    def _convert_to_candidates(self, search_results: List[Dict[str, Any]]) -> List[ContextCandidate]:
        """Преобразование результатов поиска в кандидатов контекста"""
        candidates = []
        
        for result in search_results:
            # Определяем причину релевантности
            why = self._determine_relevance_reason(result)
            
            candidate = ContextCandidate(
                doc=result.get('code', ''),
                section=result.get('section', ''),
                page=result.get('page', 1),
                snippet=result.get('content', '')[:200] + '...' if len(result.get('content', '')) > 200 else result.get('content', ''),
                why=why,
                score=result.get('score', 0.0),
                content=result.get('content', ''),
                chunk_id=result.get('chunk_id', ''),
                document_title=result.get('document_title', ''),
                section_title=result.get('section_title', ''),
                chunk_type=result.get('chunk_type', ''),
                metadata=result.get('metadata', {})
            )
            candidates.append(candidate)
        
        return candidates
    
    def _determine_relevance_reason(self, result: Dict[str, Any]) -> str:
        """Определение причины релевантности результата"""
        # Анализируем метаданные для определения типа совпадения
        search_type = result.get('search_type', '')
        score = result.get('score', 0.0)
        
        if search_type == 'exact_match':
            return "exact_match"
        elif search_type == 'semantic':
            return "semantic_match"
        elif search_type == 'keyword':
            return "keyword_match"
        elif score > 0.8:
            return "high_relevance"
        elif score > 0.6:
            return "medium_relevance"
        else:
            return "low_relevance"
    
    def _deduplicate_and_merge(self, candidates: List[ContextCandidate]) -> List[ContextCandidate]:
        """Дедупликация по doc+section и слияние соседних чанков"""
        logger.info(f"🔄 [CONTEXT_BUILDER] Deduplicating {len(candidates)} candidates")
        
        # Группируем по doc+section
        grouped = {}
        for candidate in candidates:
            key = f"{candidate.doc}_{candidate.section}"
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(candidate)
        
        # Сливаем кандидатов в каждой группе
        merged_candidates = []
        for key, group in grouped.items():
            if len(group) == 1:
                merged_candidates.append(group[0])
            else:
                # Сортируем по page и сливаем соседние
                group.sort(key=lambda x: x.page)
                merged = self._merge_adjacent_chunks(group)
                merged_candidates.extend(merged)
        
        logger.info(f"✅ [CONTEXT_BUILDER] Deduplication completed: {len(candidates)} -> {len(merged_candidates)}")
        return merged_candidates
    
    def _merge_adjacent_chunks(self, chunks: List[ContextCandidate]) -> List[ContextCandidate]:
        """Слияние соседних чанков одной секции"""
        if len(chunks) <= 1:
            return chunks
        
        merged = []
        current_chunk = chunks[0]
        
        for next_chunk in chunks[1:]:
            # Если страницы соседние (разница <= 2), сливаем
            if abs(next_chunk.page - current_chunk.page) <= 2:
                # Сливаем содержимое
                current_chunk.content += f"\n\n{next_chunk.content}"
                current_chunk.snippet = current_chunk.content[:200] + '...' if len(current_chunk.content) > 200 else current_chunk.content
                # Обновляем score (берем максимальный)
                current_chunk.score = max(current_chunk.score, next_chunk.score)
                # Обновляем why
                if next_chunk.score > current_chunk.score:
                    current_chunk.why = next_chunk.why
            else:
                # Не соседние, добавляем текущий и начинаем новый
                merged.append(current_chunk)
                current_chunk = next_chunk
        
        # Добавляем последний чанк
        merged.append(current_chunk)
        
        return merged
    
    def _generate_summaries(self, candidates: List[ContextCandidate], query: str) -> List[ContextCandidate]:
        """Генерация auto-summary для каждого кандидата"""
        logger.info(f"📝 [CONTEXT_BUILDER] Generating summaries for {len(candidates)} candidates")
        
        enriched_candidates = []
        for candidate in candidates:
            try:
                summary = self._generate_candidate_summary(candidate, query)
                # Добавляем сводку к кандидату
                candidate.summary = summary
                enriched_candidates.append(candidate)
            except Exception as e:
                logger.warning(f"⚠️ [CONTEXT_BUILDER] Failed to generate summary for {candidate.doc}: {e}")
                # Добавляем без сводки
                candidate.summary = None
                enriched_candidates.append(candidate)
        
        return enriched_candidates
    
    def _generate_candidate_summary(self, candidate: ContextCandidate, query: str) -> Optional[ContextSummary]:
        """Генерация сводки для одного кандидата"""
        try:
            # Формируем промпт для генерации сводки
            prompt = f"""
Проанализируй следующий фрагмент нормативного документа и создай краткую сводку (5-7 строк):

Документ: {candidate.doc} - {candidate.document_title}
Раздел: {candidate.section} - {candidate.section_title}
Запрос пользователя: {query}

Содержимое:
{candidate.content[:1000]}

Создай сводку в формате:
ТЕМА: [о чем раздел в 1-2 предложениях]
ТИП_НОРМЫ: [обязательная/рекомендательная/информационная]
КЛЮЧЕВЫЕ_МОМЕНТЫ: [3-4 ключевых момента через точку с запятой]
ПРИЧИНА_РЕЛЕВАНТНОСТИ: [почему этот фрагмент релевантен запросу]
"""

            # Отправляем запрос к Ollama
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.0,  # Детерминированный вывод
                        "top_p": 0.9,
                        "max_tokens": 200
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                summary_text = result.get('response', '').strip()
                
                # Парсим ответ
                return self._parse_summary_response(summary_text)
            else:
                logger.warning(f"⚠️ [CONTEXT_BUILDER] Ollama request failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ [CONTEXT_BUILDER] Error generating summary: {e}")
            return None
    
    def _parse_summary_response(self, summary_text: str) -> Optional[ContextSummary]:
        """Парсинг ответа с сводкой"""
        try:
            lines = summary_text.split('\n')
            topic = ""
            norm_type = ""
            key_points = []
            relevance_reason = ""
            
            for line in lines:
                line = line.strip()
                if line.startswith('ТЕМА:'):
                    topic = line.replace('ТЕМА:', '').strip()
                elif line.startswith('ТИП_НОРМЫ:'):
                    norm_type = line.replace('ТИП_НОРМЫ:', '').strip()
                elif line.startswith('КЛЮЧЕВЫЕ_МОМЕНТЫ:'):
                    points_text = line.replace('КЛЮЧЕВЫЕ_МОМЕНТЫ:', '').strip()
                    key_points = [p.strip() for p in points_text.split(';') if p.strip()]
                elif line.startswith('ПРИЧИНА_РЕЛЕВАНТНОСТИ:'):
                    relevance_reason = line.replace('ПРИЧИНА_РЕЛЕВАНТНОСТИ:', '').strip()
            
            return ContextSummary(
                topic=topic or "Не удалось определить тему",
                norm_type=norm_type or "неопределенный",
                key_points=key_points or [],
                relevance_reason=relevance_reason or "Релевантность не определена"
            )
            
        except Exception as e:
            logger.error(f"❌ [CONTEXT_BUILDER] Error parsing summary: {e}")
            return None
    
    def _build_final_context(self, candidates: List[ContextCandidate], query: str) -> Dict[str, Any]:
        """Построение финального структурированного контекста"""
        
        # Формируем JSON-массив объектов
        context_array = []
        for candidate in candidates:
            context_obj = {
                "doc": candidate.doc,
                "section": candidate.section,
                "page": candidate.page,
                "snippet": candidate.snippet,
                "why": candidate.why,
                "score": round(candidate.score, 3),
                "document_title": candidate.document_title,
                "section_title": candidate.section_title,
                "chunk_type": candidate.chunk_type,
                "metadata": candidate.metadata
            }
            
            # Добавляем сводку, если есть
            if hasattr(candidate, 'summary') and candidate.summary:
                context_obj["summary"] = {
                    "topic": candidate.summary.topic,
                    "norm_type": candidate.summary.norm_type,
                    "key_points": candidate.summary.key_points,
                    "relevance_reason": candidate.summary.relevance_reason
                }
            
            context_array.append(context_obj)
        
        # Создаем мета-сводку верхнего уровня
        meta_summary = self._generate_meta_summary(context_array, query)
        
        return {
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "context": context_array,
            "meta_summary": meta_summary,
            "total_candidates": len(context_array),
            "avg_score": round(sum(c["score"] for c in context_array) / len(context_array), 3) if context_array else 0
        }
    
    def _generate_meta_summary(self, context_array: List[Dict], query: str) -> Dict[str, Any]:
        """Генерация мета-сводки верхнего уровня"""
        try:
            # Анализируем контекст для создания сводки
            docs = list(set(c["doc"] for c in context_array if c["doc"]))
            sections = list(set(c["section"] for c in context_array if c["section"]))
            avg_score = sum(c["score"] for c in context_array) / len(context_array) if context_array else 0
            
            # Определяем тип запроса
            query_lower = query.lower()
            if any(word in query_lower for word in ['требования', 'обязательно', 'должен', 'необходимо']):
                query_type = "требования"
            elif any(word in query_lower for word in ['рекомендации', 'рекомендуется', 'желательно']):
                query_type = "рекомендации"
            elif any(word in query_lower for word in ['определение', 'что такое', 'означает']):
                query_type = "определения"
            else:
                query_type = "общая информация"
            
            return {
                "query_type": query_type,
                "documents_found": len(docs),
                "sections_covered": len(sections),
                "avg_relevance": round(avg_score, 3),
                "coverage_quality": "высокая" if avg_score > 0.7 else "средняя" if avg_score > 0.5 else "низкая",
                "key_documents": docs[:3],  # Топ-3 документа
                "key_sections": sections[:3]  # Топ-3 раздела
            }
            
        except Exception as e:
            logger.error(f"❌ [CONTEXT_BUILDER] Error generating meta summary: {e}")
            return {
                "query_type": "неопределенный",
                "documents_found": 0,
                "sections_covered": 0,
                "avg_relevance": 0.0,
                "coverage_quality": "неизвестно",
                "key_documents": [],
                "key_sections": []
            }
    
    def _build_fallback_context(self, search_results: List[Dict[str, Any]], query: str) -> Dict[str, Any]:
        """Fallback контекст в случае ошибки"""
        logger.warning("⚠️ [CONTEXT_BUILDER] Using fallback context")
        
        context_array = []
        for result in search_results[:5]:  # Берем топ-5
            context_obj = {
                "doc": result.get('code', ''),
                "section": result.get('section', ''),
                "page": result.get('page', 1),
                "snippet": result.get('content', '')[:200] + '...' if len(result.get('content', '')) > 200 else result.get('content', ''),
                "why": "fallback",
                "score": result.get('score', 0.0),
                "document_title": result.get('document_title', ''),
                "section_title": result.get('section_title', ''),
                "chunk_type": result.get('chunk_type', ''),
                "metadata": result.get('metadata', {})
            }
            context_array.append(context_obj)
        
        return {
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "context": context_array,
            "meta_summary": {
                "query_type": "fallback",
                "documents_found": len(context_array),
                "sections_covered": 0,
                "avg_relevance": 0.0,
                "coverage_quality": "fallback",
                "key_documents": [],
                "key_sections": []
            },
            "total_candidates": len(context_array),
            "avg_score": 0.0
        }
