"""
Оптимизированная система индексации нормативной базы (RAG Base)
Включает унификацию структуры, гранулярный чанкинг и контекстуальную фильтрацию
"""

import os
import json
import logging
import hashlib
import re
from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import psycopg2
from psycopg2.extras import RealDictCursor
import qdrant_client
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue, Range
import numpy as np
# from sentence_transformers import SentenceTransformer  # Отключено для тестирования
import tiktoken

logger = logging.getLogger(__name__)

class DocumentType(Enum):
    """Типы нормативных документов"""
    GOST = "gost"
    SP = "sp"
    SNIP = "snip"
    TR = "tr"
    STU = "stu"
    METHODOLOGY = "methodology"
    CORPORATE = "corporate"

class DocumentStage(Enum):
    """Стадии проектирования"""
    PD = "pd"  # Проектная документация
    RD = "rd"  # Рабочая документация

class DocumentMark(Enum):
    """Марки комплектов документации"""
    AR = "ar"  # Архитектурные решения
    KR = "kr"  # Конструктивные решения
    EO = "eo"  # Электрооборудование
    VK = "vk"  # Водоснабжение и канализация
    OV = "ov"  # Отопление и вентиляция
    SS = "ss"  # Сети связи
    AS = "as"  # Автоматизация
    OTHER = "other"

class ContentTag(Enum):
    """Теги для классификации контента"""
    FORMATTING = "оформление"
    SIGNATURES = "подписи"
    STRUCTURE = "структура"
    TEXT = "текст"
    GRAPHICS = "графика"
    TABLES = "таблицы"
    CALCULATIONS = "расчеты"
    REQUIREMENTS = "требования"
    RECOMMENDATIONS = "рекомендации"
    EXAMPLES = "примеры"
    NOTES = "примечания"

@dataclass
class UnifiedNormativeStructure:
    """Унифицированная структура нормативного документа"""
    clause_id: str  # Уникальный идентификатор пункта (например, "ГОСТ 21.101-2020 п.6.5")
    section_title: str  # Заголовок раздела
    full_text: str  # Полный текст пункта
    tags: List[str]  # Теги для классификации
    document_type: DocumentType  # Тип документа
    document_number: str  # Номер документа
    clause_number: str  # Номер пункта
    importance_level: int  # Уровень важности (1-5)
    metadata: Dict[str, Any]  # Дополнительные метаданные

@dataclass
class SemanticChunk:
    """Семантический чанк с контекстом"""
    chunk_id: str
    clause_id: str
    content: str
    chunk_type: str  # "requirement", "recommendation", "note", "example"
    semantic_context: str  # Семантический контекст
    tags: List[str]
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None

class OptimizedNormativeIndexer:
    """Оптимизированный индексатор нормативной базы"""
    
    def __init__(self, db_conn, qdrant_client, embedding_model):
        self.db_conn = db_conn
        self.qdrant_client = qdrant_client
        self.embedding_model = embedding_model
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
        # Константы для оптимизированного чанкинга
        self.MAX_CHUNK_TOKENS = 300  # Уменьшенный размер для гранулярности
        self.MIN_CHUNK_TOKENS = 50   # Минимальный размер чанка
        self.OVERLAP_TOKENS = 30     # Перекрытие между чанками
        
        # Коллекции для разных типов поиска
        self.VECTOR_COLLECTION = "optimized_normative_documents"
        self.METADATA_COLLECTION = "normative_metadata"
        
        logger.info("🚀 [OPTIMIZED_INDEXER] Initialized OptimizedNormativeIndexer")
    
    def extract_clause_id(self, text: str, document_info: Dict[str, Any]) -> str:
        """Извлечение уникального clause_id из текста"""
        doc_type = document_info.get('document_type', '').upper()
        doc_number = document_info.get('document_number', '')
        
        # Паттерны для извлечения номера пункта
        patterns = [
            r'п\.\s*(\d+(?:\.\d+)*)',  # п. 1.2.3
            r'пункт\s*(\d+(?:\.\d+)*)',  # пункт 1.2.3
            r'статья\s*(\d+)',  # статья 5
            r'раздел\s*(\d+)',  # раздел 5
            r'(\d+\.\d+(?:\.\d+)*)',  # 1.2.3
            r'(\d+\.\d+)',  # 1.2
            r'(\d+)',  # 1
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                clause_number = match.group(1)
                return f"{doc_type} {doc_number} п.{clause_number}"
        
        # Если не нашли, создаем хеш
        text_hash = hashlib.md5(text[:100].encode()).hexdigest()[:8]
        return f"{doc_type} {doc_number} п.{text_hash}"
    
    def detect_content_tags(self, text: str) -> List[str]:
        """Определение тегов контента на основе анализа текста"""
        tags = []
        text_lower = text.lower()
        
        # Анализ по ключевым словам и паттернам
        if any(word in text_lower for word in ['подпись', 'подписан', 'утвержден', 'согласован']):
            tags.append(ContentTag.SIGNATURES.value)
        
        if any(word in text_lower for word in ['оформление', 'формат', 'шрифт', 'размер']):
            tags.append(ContentTag.FORMATTING.value)
        
        if any(word in text_lower for word in ['структура', 'состав', 'раздел', 'глава']):
            tags.append(ContentTag.STRUCTURE.value)
        
        if any(word in text_lower for word in ['таблица', 'табл.', 'таб.']):
            tags.append(ContentTag.TABLES.value)
        
        if any(word in text_lower for word in ['рисунок', 'рис.', 'чертеж', 'схема']):
            tags.append(ContentTag.GRAPHICS.value)
        
        if any(word in text_lower for word in ['расчет', 'вычисление', 'формула']):
            tags.append(ContentTag.CALCULATIONS.value)
        
        if any(word in text_lower for word in ['должен', 'обязательно', 'необходимо', 'требуется']):
            tags.append(ContentTag.REQUIREMENTS.value)
        
        if any(word in text_lower for word in ['рекомендуется', 'следует', 'желательно']):
            tags.append(ContentTag.RECOMMENDATIONS.value)
        
        if any(word in text_lower for word in ['например', 'пример', 'образец']):
            tags.append(ContentTag.EXAMPLES.value)
        
        if any(word in text_lower for word in ['примечание', 'прим.', 'замечание']):
            tags.append(ContentTag.NOTES.value)
        
        # По умолчанию добавляем тег "текст"
        if not tags:
            tags.append(ContentTag.TEXT.value)
        
        return tags
    
    def determine_importance_level(self, text: str, clause_type: str) -> int:
        """Определение уровня важности пункта"""
        text_lower = text.lower()
        
        # Критически важные требования
        if any(word in text_lower for word in ['должен', 'обязательно', 'необходимо', 'требуется', 'запрещается']):
            return 5
        
        # Важные требования
        if any(word in text_lower for word in ['следует', 'рекомендуется', 'желательно']):
            return 4
        
        # Обычные требования
        if clause_type in ['requirement', 'requirement']:
            return 3
        
        # Рекомендации
        if clause_type in ['recommendation', 'recommendation']:
            return 2
        
        # Информационные пункты
        return 1
    
    def semantic_chunking(self, text: str, clause_id: str) -> List[SemanticChunk]:
        """Семантический чанкинг на основе структуры и смысловых абзацев"""
        chunks = []
        
        # Разбиваем на абзацы
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        for i, paragraph in enumerate(paragraphs):
            if not paragraph.strip():
                continue
            
            # Определяем тип контента
            chunk_type = self.detect_chunk_type(paragraph)
            
            # Определяем семантический контекст
            semantic_context = self.extract_semantic_context(paragraph, clause_id)
            
            # Определяем теги
            tags = self.detect_content_tags(paragraph)
            
            # Создаем чанк
            chunk_id = f"{clause_id}_chunk_{i}"
            chunk = SemanticChunk(
                chunk_id=chunk_id,
                clause_id=clause_id,
                content=paragraph,
                chunk_type=chunk_type,
                semantic_context=semantic_context,
                tags=tags,
                metadata={
                    "paragraph_index": i,
                    "total_paragraphs": len(paragraphs),
                    "token_count": len(self.tokenizer.encode(paragraph)),
                    "created_at": datetime.now().isoformat()
                }
            )
            chunks.append(chunk)
        
        return chunks
    
    def detect_chunk_type(self, text: str) -> str:
        """Определение типа чанка"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['должен', 'обязательно', 'необходимо', 'требуется']):
            return "requirement"
        
        if any(word in text_lower for word in ['рекомендуется', 'следует', 'желательно']):
            return "recommendation"
        
        if any(word in text_lower for word in ['например', 'пример', 'образец']):
            return "example"
        
        if any(word in text_lower for word in ['примечание', 'прим.', 'замечание']):
            return "note"
        
        return "text"
    
    def extract_semantic_context(self, text: str, clause_id: str) -> str:
        """Извлечение семантического контекста"""
        # Извлекаем ключевые слова и фразы
        keywords = []
        
        # Ищем технические термины
        technical_terms = re.findall(r'\b[A-ZА-Я][a-zа-я]*(?:\s+[A-ZА-Я][a-zа-я]*)*\b', text)
        keywords.extend(technical_terms[:5])  # Берем первые 5 терминов
        
        # Ищем числовые значения
        numbers = re.findall(r'\d+(?:\.\d+)?', text)
        if numbers:
            keywords.append(f"числовые_значения: {len(numbers)}")
        
        # Ищем единицы измерения
        units = re.findall(r'\b(?:мм|см|м|км|кг|т|л|м³|м²|°C|%|Вт|кВт|А|В|Ом)\b', text)
        if units:
            keywords.append(f"единицы_измерения: {', '.join(set(units))}")
        
        return f"clause_id: {clause_id}, keywords: {', '.join(keywords)}"
    
    def create_metadata_filter(self, document_mark: Optional[str] = None, 
                             document_stage: Optional[str] = None,
                             content_tags: Optional[List[str]] = None) -> Filter:
        """Создание фильтра метаданных для контекстуального поиска"""
        conditions = []
        
        if document_mark:
            conditions.append(
                FieldCondition(
                    key="document_mark",
                    match=MatchValue(value=document_mark)
                )
            )
        
        if document_stage:
            conditions.append(
                FieldCondition(
                    key="document_stage",
                    match=MatchValue(value=document_stage)
                )
            )
        
        if content_tags:
            # Фильтр по тегам (хотя бы один тег должен совпадать)
            tag_conditions = []
            for tag in content_tags:
                tag_conditions.append(
                    FieldCondition(
                        key="tags",
                        match=MatchValue(value=tag)
                    )
                )
            # Используем OR логику для тегов
            conditions.extend(tag_conditions)
        
        return Filter(
            must=conditions
        ) if conditions else None
    
    def index_document(self, document_info: Dict[str, Any], content: str) -> bool:
        """Индексация документа с оптимизированной структурой"""
        try:
            logger.info(f"📄 [INDEX] Starting optimized indexing for document: {document_info.get('document_number')}")
            
            # Создаем унифицированную структуру
            unified_structure = self.create_unified_structure(document_info, content)
            
            # Семантический чанкинг
            semantic_chunks = self.semantic_chunking(unified_structure.full_text, unified_structure.clause_id)
            
            # Индексация в векторную базу
            self.index_chunks_to_vector_db(semantic_chunks, document_info)
            
            # Сохранение в PostgreSQL
            self.save_to_postgresql(unified_structure, semantic_chunks)
            
            logger.info(f"✅ [INDEX] Successfully indexed document with {len(semantic_chunks)} chunks")
            return True
            
        except Exception as e:
            logger.error(f"❌ [INDEX] Error indexing document: {e}")
            return False
    
    def create_unified_structure(self, document_info: Dict[str, Any], content: str) -> UnifiedNormativeStructure:
        """Создание унифицированной структуры документа"""
        clause_id = self.extract_clause_id(content, document_info)
        tags = self.detect_content_tags(content)
        importance_level = self.determine_importance_level(content, document_info.get('clause_type', 'text'))
        
        return UnifiedNormativeStructure(
            clause_id=clause_id,
            section_title=document_info.get('section_title', ''),
            full_text=content,
            tags=tags,
            document_type=DocumentType(document_info.get('document_type', 'gost')),
            document_number=document_info.get('document_number', ''),
            clause_number=document_info.get('clause_number', ''),
            importance_level=importance_level,
            metadata={
                'document_mark': document_info.get('document_mark'),
                'document_stage': document_info.get('document_stage'),
                'page_number': document_info.get('page_number'),
                'created_at': datetime.now().isoformat()
            }
        )
    
    def index_chunks_to_vector_db(self, chunks: List[SemanticChunk], document_info: Dict[str, Any]):
        """Индексация чанков в векторную базу данных"""
        logger.info(f"🔍 [VECTOR_DB] Indexing {len(chunks)} chunks to vector database")
        
        # Создаем коллекцию если не существует
        self.create_vector_collection()
        
        points = []
        for chunk in chunks:
            # Генерируем эмбеддинг
            if self.embedding_model:
                embedding = self.embedding_model.encode(chunk.content).tolist()
            else:
                # Fallback: простой хеш-эмбеддинг
                embedding = self.simple_hash_embedding(chunk.content)
            
            # Создаем точку для Qdrant
            point = PointStruct(
                id=hash(chunk.chunk_id) % (2**63),  # Qdrant требует int64
                vector=embedding,
                payload={
                    "chunk_id": chunk.chunk_id,
                    "clause_id": chunk.clause_id,
                    "content": chunk.content,
                    "chunk_type": chunk.chunk_type,
                    "semantic_context": chunk.semantic_context,
                    "tags": chunk.tags,
                    "document_type": document_info.get('document_type'),
                    "document_number": document_info.get('document_number'),
                    "document_mark": document_info.get('document_mark'),
                    "document_stage": document_info.get('document_stage'),
                    "importance_level": chunk.metadata.get('importance_level', 1),
                    "token_count": chunk.metadata.get('token_count', 0),
                    "created_at": chunk.metadata.get('created_at')
                }
            )
            points.append(point)
        
        # Вставляем точки в базу
        self.qdrant_client.upsert(
            collection_name=self.VECTOR_COLLECTION,
            points=points
        )
        
        logger.info(f"✅ [VECTOR_DB] Successfully indexed {len(points)} points")
    
    def create_vector_collection(self):
        """Создание векторной коллекции в Qdrant"""
        try:
            # Проверяем существование коллекции
            collections = self.qdrant_client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.VECTOR_COLLECTION not in collection_names:
                logger.info(f"🔧 [VECTOR_DB] Creating collection: {self.VECTOR_COLLECTION}")
                
                # Определяем размерность вектора
                vector_size = 1024  # BGE-M3 размерность
                if not self.embedding_model:
                    vector_size = 768  # Fallback размерность
                
                self.qdrant_client.create_collection(
                    collection_name=self.VECTOR_COLLECTION,
                    vectors_config=VectorParams(
                        size=vector_size,
                        distance=Distance.COSINE
                    )
                )
                
                # Создаем индексы для быстрого поиска
                self.qdrant_client.create_payload_index(
                    collection_name=self.VECTOR_COLLECTION,
                    field_name="document_type",
                    field_schema="keyword"
                )
                
                self.qdrant_client.create_payload_index(
                    collection_name=self.VECTOR_COLLECTION,
                    field_name="tags",
                    field_schema="keyword"
                )
                
                self.qdrant_client.create_payload_index(
                    collection_name=self.VECTOR_COLLECTION,
                    field_name="importance_level",
                    field_schema="integer"
                )
                
                logger.info(f"✅ [VECTOR_DB] Collection {self.VECTOR_COLLECTION} created successfully")
            else:
                logger.info(f"ℹ️ [VECTOR_DB] Collection {self.VECTOR_COLLECTION} already exists")
                
        except Exception as e:
            logger.error(f"❌ [VECTOR_DB] Error creating collection: {e}")
            raise
    
    def simple_hash_embedding(self, text: str) -> List[float]:
        """Простой хеш-эмбеддинг для fallback"""
        # Создаем хеш текста
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        
        # Преобразуем в числовой вектор
        vector = []
        for i in range(0, len(text_hash), 2):
            hex_pair = text_hash[i:i+2]
            vector.append(float(int(hex_pair, 16)) / 255.0)
        
        # Дополняем до нужной размерности
        while len(vector) < 768:
            vector.extend(vector[:min(768 - len(vector), len(vector))])
        
        return vector[:768]
    
    def save_to_postgresql(self, unified_structure: UnifiedNormativeStructure, chunks: List[SemanticChunk]):
        """Сохранение в PostgreSQL для дополнительного поиска"""
        try:
            with self.db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Сохраняем основную структуру
                cursor.execute("""
                    INSERT INTO document_clauses 
                    (clause_id, clause_number, section_title, clause_text, clause_type, importance_level, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (clause_id) DO UPDATE SET
                    clause_text = EXCLUDED.clause_text,
                    importance_level = EXCLUDED.importance_level,
                    metadata = EXCLUDED.metadata,
                    updated_at = CURRENT_TIMESTAMP
                """, (
                    unified_structure.clause_id,
                    unified_structure.clause_number,
                    unified_structure.section_title,
                    unified_structure.full_text,
                    'requirement',  # По умолчанию
                    unified_structure.importance_level,
                    json.dumps(unified_structure.metadata)
                ))
                
                # Сохраняем атрибуты (теги)
                for tag in unified_structure.tags:
                    cursor.execute("""
                        INSERT INTO clause_attributes 
                        (clause_id, attribute_name, attribute_value, attribute_type)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT DO NOTHING
                    """, (
                        unified_structure.clause_id,
                        'tag',
                        tag,
                        'text'
                    ))
                
                self.db_conn.commit()
                logger.info(f"✅ [POSTGRESQL] Saved unified structure and {len(chunks)} chunks")
                
        except Exception as e:
            logger.error(f"❌ [POSTGRESQL] Error saving to PostgreSQL: {e}")
            self.db_conn.rollback()
            raise
    
    def search_with_context_filter(self, query: str, 
                                 document_mark: Optional[str] = None,
                                 document_stage: Optional[str] = None,
                                 content_tags: Optional[List[str]] = None,
                                 limit: int = 10) -> List[Dict[str, Any]]:
        """Поиск с контекстуальной фильтрацией"""
        try:
            logger.info(f"🔍 [SEARCH] Contextual search with filters: mark={document_mark}, stage={document_stage}, tags={content_tags}")
            
            # Генерируем эмбеддинг запроса
            if self.embedding_model:
                query_embedding = self.embedding_model.encode(query).tolist()
            else:
                query_embedding = self.simple_hash_embedding(query)
            
            # Создаем фильтр метаданных
            metadata_filter = self.create_metadata_filter(document_mark, document_stage, content_tags)
            
            # Выполняем поиск
            search_result = self.qdrant_client.search(
                collection_name=self.VECTOR_COLLECTION,
                query_vector=query_embedding,
                query_filter=metadata_filter,
                limit=limit,
                with_payload=True,
                with_vectors=False
            )
            
            # Форматируем результаты
            results = []
            for point in search_result:
                results.append({
                    'chunk_id': point.payload.get('chunk_id'),
                    'clause_id': point.payload.get('clause_id'),
                    'content': point.payload.get('content'),
                    'chunk_type': point.payload.get('chunk_type'),
                    'semantic_context': point.payload.get('semantic_context'),
                    'tags': point.payload.get('tags', []),
                    'importance_level': point.payload.get('importance_level', 1),
                    'similarity_score': point.score,
                    'document_type': point.payload.get('document_type'),
                    'document_number': point.payload.get('document_number')
                })
            
            logger.info(f"✅ [SEARCH] Found {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"❌ [SEARCH] Error in contextual search: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики индексации"""
        try:
            # Статистика из Qdrant
            collection_info = self.qdrant_client.get_collection(self.VECTOR_COLLECTION)
            vector_count = collection_info.points_count
            
            # Статистика из PostgreSQL
            with self.db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SELECT COUNT(*) as total_clauses FROM document_clauses")
                clause_count = cursor.fetchone()['total_clauses']
                
                cursor.execute("SELECT COUNT(DISTINCT clause_id) as unique_clauses FROM document_clauses")
                unique_clauses = cursor.fetchone()['unique_clauses']
                
                cursor.execute("SELECT COUNT(*) as total_attributes FROM clause_attributes")
                attribute_count = cursor.fetchone()['total_attributes']
            
            return {
                'vector_database': {
                    'collection_name': self.VECTOR_COLLECTION,
                    'total_vectors': vector_count,
                    'status': 'active'
                },
                'postgresql': {
                    'total_clauses': clause_count,
                    'unique_clauses': unique_clauses,
                    'total_attributes': attribute_count
                },
                'optimization': {
                    'chunk_size': self.MAX_CHUNK_TOKENS,
                    'min_chunk_size': self.MIN_CHUNK_TOKENS,
                    'overlap_size': self.OVERLAP_TOKENS,
                    'semantic_chunking': True,
                    'contextual_filtering': True
                }
            }
            
        except Exception as e:
            logger.error(f"❌ [STATS] Error getting statistics: {e}")
            return {'error': str(e)}
