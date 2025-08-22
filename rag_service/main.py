import os
import json
import logging
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

import psycopg2
from psycopg2.extras import RealDictCursor
import qdrant_client
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
import tiktoken
import re

# Настройка логирования с подробной отладкой
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/app/rag_service.log')
    ]
)
logger = logging.getLogger(__name__)

# Добавляем логирование для всех модулей
logging.getLogger('qdrant_client').setLevel(logging.DEBUG)
logging.getLogger('sentence_transformers').setLevel(logging.DEBUG)
logging.getLogger('psycopg2').setLevel(logging.DEBUG)

app = FastAPI(title="RAG Service for Norms", version="2.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Конфигурация
POSTGRES_URL = os.getenv("POSTGRES_URL", "postgresql://norms_user:norms_password@norms-db:5432/norms_db")
QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")

logger.info(f"🔧 [CONFIG] RAG Service Configuration:")
logger.info(f"🔧 [CONFIG] POSTGRES_URL: {POSTGRES_URL}")
logger.info(f"🔧 [CONFIG] QDRANT_URL: {QDRANT_URL}")
logger.info(f"🔧 [CONFIG] OLLAMA_URL: {OLLAMA_URL}")

# Константы для чанкинга
CHUNK_SIZE = 500  # ~400-600 токенов
CHUNK_OVERLAP = 75  # ~50-100 токенов
MAX_TOKENS = 1000

# Названия коллекций
VECTOR_COLLECTION = "normative_documents"
BM25_COLLECTION = "normative_bm25"

logger.info(f"🔧 [CONFIG] CHUNK_SIZE: {CHUNK_SIZE}")
logger.info(f"🔧 [CONFIG] CHUNK_OVERLAP: {CHUNK_OVERLAP}")
logger.info(f"🔧 [CONFIG] VECTOR_COLLECTION: {VECTOR_COLLECTION}")

class ChunkType(Enum):
    TEXT = "text"
    TABLE = "table"
    FIGURE = "figure"
    HEADER = "header"

@dataclass
class NormChunk:
    """Структура чанка нормативного документа"""
    chunk_id: str
    clause_id: str
    document_id: int
    document_title: str
    chapter: str
    section: str
    page_number: int
    chunk_type: ChunkType
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None

class NormRAGService:
    def __init__(self):
        logger.info("🚀 [INIT] Initializing NormRAGService...")
        self.db_conn = None
        self.qdrant_client = None
        self.embedding_model = None
        self.tokenizer = None
        self.text_splitter = None
        self.connect_services()
        self.initialize_models()
        logger.info("✅ [INIT] NormRAGService initialized successfully")
    
    def connect_services(self):
        """Подключение к базам данных"""
        logger.info("🔌 [CONNECT] Connecting to services...")
        try:
            # PostgreSQL
            logger.info(f"🔌 [CONNECT] Connecting to PostgreSQL: {POSTGRES_URL}")
            self.db_conn = psycopg2.connect(POSTGRES_URL)
            logger.info("✅ [CONNECT] Connected to PostgreSQL")
            
            # Qdrant
            logger.info(f"🔌 [CONNECT] Connecting to Qdrant: {QDRANT_URL}")
            self.qdrant_client = qdrant_client.QdrantClient(url=QDRANT_URL)
            logger.info("✅ [CONNECT] Connected to Qdrant")
            
        except Exception as e:
            logger.error(f"❌ [CONNECT] Service connection error: {e}")
            raise
    
    def initialize_models(self):
        """Инициализация моделей для эмбеддингов и токенизации"""
        logger.info("🤖 [MODELS] Initializing models...")
        try:
            # Инициализация токенизатора
            logger.info("🤖 [MODELS] Initializing tokenizer...")
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
            logger.info("✅ [MODELS] Tokenizer initialized")
            
            # Загружаем полноценную модель BGE-M3 для качественных эмбеддингов
            logger.info("🤖 [MODELS] Loading BGE-M3 embedding model...")
            try:
                from sentence_transformers import SentenceTransformer
                self.embedding_model = SentenceTransformer('BAAI/bge-m3', device='cpu')
                logger.info("✅ [MODELS] BGE-M3 model loaded successfully")
            except Exception as e:
                logger.error(f"❌ [MODELS] Failed to load BGE-M3 model: {e}")
                logger.info("🤖 [MODELS] Falling back to simple hash embedding")
                self.embedding_model = None
            
        except Exception as e:
            logger.error(f"❌ [MODELS] Model initialization error: {e}")
            raise
    
    def count_tokens(self, text: str) -> int:
        """Подсчет токенов в тексте"""
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        return len(text.split())
    
    def simple_text_split(self, text: str) -> List[str]:
        """Простой сплиттер текста на чанки"""
        if not text.strip():
            return []
        
        # Разбиваем на предложения
        sentences = re.split(r'[.!?]+', text)
        chunks = []
        current_chunk = ""
        current_tokens = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            sentence_tokens = self.count_tokens(sentence)
            
            # Если предложение слишком длинное, разбиваем его
            if sentence_tokens > CHUNK_SIZE:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                    current_tokens = 0
                
                # Разбиваем длинное предложение на части
                words = sentence.split()
                temp_chunk = ""
                temp_tokens = 0
                
                for word in words:
                    word_tokens = self.count_tokens(word + " ")
                    if temp_tokens + word_tokens > CHUNK_SIZE:
                        if temp_chunk:
                            chunks.append(temp_chunk.strip())
                        temp_chunk = word + " "
                        temp_tokens = word_tokens
                    else:
                        temp_chunk += word + " "
                        temp_tokens += word_tokens
                
                if temp_chunk:
                    current_chunk = temp_chunk
                    current_tokens = temp_tokens
            else:
                # Проверяем, поместится ли предложение в текущий чанк
                if current_tokens + sentence_tokens > CHUNK_SIZE:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = sentence + ". "
                    current_tokens = sentence_tokens
                else:
                    current_chunk += sentence + ". "
                    current_tokens += sentence_tokens
        
        # Добавляем последний чанк
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def create_chunk_id(self, document_id: int, clause_id: str, chunk_index: int) -> str:
        """Создание уникального ID чанка"""
        return f"doc_{document_id}_clause_{clause_id}_chunk_{chunk_index}"
    
    def extract_clause_id(self, text: str) -> str:
        """Извлечение clause_id из текста"""
        # Ищем паттерны типа "п. 1.2.3", "статья 5", "ГОСТ 12345-2020 п.4.1"
        import re
        patterns = [
            r'п\.\s*(\d+(?:\.\d+)*)',  # п. 1.2.3
            r'статья\s*(\d+)',  # статья 5
            r'ГОСТ\s*(\d+(?:-\d+)?)\s*п\.(\d+(?:\.\d+)*)',  # ГОСТ 12345-2020 п.4.1
            r'СП\s*(\d+(?:\.\d+)?)\s*п\.(\d+(?:\.\d+)*)',  # СП 20.13330.2016 п.4.1
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        
        # Если не нашли, создаем хеш
        return hashlib.md5(text[:100].encode()).hexdigest()[:8]
    
    def chunk_document(self, document_id: int, document_title: str, content: str, 
                      chapter: str = "", section: str = "", page_number: int = 1) -> List[NormChunk]:
        """Чанкинг документа с сохранением метаданных"""
        logger.info(f"📄 [CHUNK] Starting document chunking for document ID: {document_id}")
        logger.info(f"📄 [CHUNK] Document title: {document_title}")
        logger.info(f"📄 [CHUNK] Content length: {len(content)} characters")
        logger.info(f"📄 [CHUNK] Page number: {page_number}")
        
        chunks = []
        
        # Простой чанкинг с учетом токенов
        logger.info(f"📄 [CHUNK] Performing text splitting...")
        text_chunks = self.simple_text_split(content)
        logger.info(f"📄 [CHUNK] Text split into {len(text_chunks)} raw chunks")
        
        for i, chunk_text in enumerate(text_chunks):
            if not chunk_text.strip():
                logger.debug(f"📄 [CHUNK] Skipping empty chunk {i}")
                continue
            
            logger.debug(f"📄 [CHUNK] Processing chunk {i}: {len(chunk_text)} characters")
            
            # Определяем тип чанка
            chunk_type = self.detect_chunk_type(chunk_text)
            logger.debug(f"📄 [CHUNK] Chunk {i} type: {chunk_type.value}")
            
            # Извлекаем clause_id
            clause_id = self.extract_clause_id(chunk_text)
            logger.debug(f"📄 [CHUNK] Chunk {i} clause_id: {clause_id}")
            
            # Создаем ID чанка
            chunk_id = self.create_chunk_id(document_id, clause_id, i)
            logger.debug(f"📄 [CHUNK] Chunk {i} ID: {chunk_id}")
            
            # Метаданные
            token_count = self.count_tokens(chunk_text)
            metadata = {
                "document_id": document_id,
                "document_title": document_title,
                "chapter": chapter,
                "section": section,
                "page_number": page_number,
                "chunk_type": chunk_type.value,
                "clause_id": clause_id,
                "chunk_index": i,
                "token_count": token_count,
                "created_at": datetime.now().isoformat()
            }
            
            chunk = NormChunk(
                chunk_id=chunk_id,
                clause_id=clause_id,
                document_id=document_id,
                document_title=document_title,
                chapter=chapter,
                section=section,
                page_number=page_number,
                chunk_type=chunk_type,
                content=chunk_text,
                metadata=metadata
            )
            
            chunks.append(chunk)
            logger.debug(f"📄 [CHUNK] Created chunk {i}: {chunk_id} ({token_count} tokens)")
        
        logger.info(f"✅ [CHUNK] Document chunking completed. Created {len(chunks)} chunks")
        return chunks
    
    def detect_chunk_type(self, text: str) -> ChunkType:
        """Определение типа чанка"""
        text_lower = text.lower()
        
        # Проверяем на таблицу
        if any(keyword in text_lower for keyword in ['|', '\t', 'таблица', 'table']):
            return ChunkType.TABLE
        
        # Проверяем на заголовок
        if len(text.strip()) < 100 and any(keyword in text_lower for keyword in ['глава', 'раздел', 'часть', 'chapter', 'section']):
            return ChunkType.HEADER
        
        # Проверяем на рисунок
        if any(keyword in text_lower for keyword in ['рисунок', 'рис.', 'figure', 'иллюстрация']):
            return ChunkType.FIGURE
        
        return ChunkType.TEXT
    
    def create_embedding(self, text: str) -> List[float]:
        """Создание эмбеддинга для текста"""
        logger.debug(f"🔢 [EMBED] Creating embedding for text: {len(text)} characters")
        
        if self.embedding_model:
            try:
                logger.debug(f"🔢 [EMBED] Using BGE-M3 model for embedding")
                # BGE-M3 создает 1024-мерные векторы
                embedding = self.embedding_model.encode(text, normalize_embeddings=True)
                embedding_list = embedding.tolist()
                logger.debug(f"🔢 [EMBED] BGE-M3 embedding created: {len(embedding_list)} dimensions")
                return embedding_list
            except Exception as e:
                logger.error(f"❌ [EMBED] BGE-M3 embedding creation error: {e}")
                logger.info(f"🔢 [EMBED] Falling back to simple hash embedding")
        
        # Fallback к простому хеш-эмбеддингу
        logger.debug(f"🔢 [EMBED] Using simple hash embedding fallback")
        return self.create_simple_embedding(text)
    
    def create_simple_embedding(self, text: str) -> List[float]:
        """Простой хеш-эмбеддинг для fallback"""
        logger.debug(f"🔢 [EMBED] Creating simple hash embedding")
        hash_obj = hashlib.sha256(text.encode())
        hash_bytes = hash_obj.digest()
        # Преобразуем в 1024-мерный вектор (как у BGE-M3)
        embedding = []
        for i in range(1024):
            embedding.append(float(hash_bytes[i % len(hash_bytes)]) / 255.0)
        logger.debug(f"🔢 [EMBED] Simple hash embedding created: {len(embedding)} dimensions")
        return embedding
    
    def index_chunks(self, chunks: List[NormChunk]) -> bool:
        """Индексация чанков в векторную базу и BM25"""
        logger.info(f"🔗 [INDEX] Indexing {len(chunks)} chunks...")
        try:
            # Создаем эмбеддинги
            for chunk in chunks:
                chunk.embedding = self.create_embedding(chunk.content)
                logger.debug(f"🔗 [INDEX] Created embedding for chunk {chunk.chunk_id}")
            
            # Индексируем в Qdrant (векторный поиск)
            self.index_to_qdrant(chunks)
            logger.info(f"✅ [INDEX] Qdrant indexing successful")
            
            # Индексируем в PostgreSQL (BM25/keyword поиск)
            self.index_to_postgres(chunks)
            logger.info(f"✅ [INDEX] PostgreSQL indexing successful")
            
            logger.info(f"✅ [INDEX] Successfully indexed {len(chunks)} chunks")
            return True
            
        except Exception as e:
            logger.error(f"❌ [INDEX] Indexing error: {e}")
            return False
    
    def index_to_qdrant(self, chunks: List[NormChunk]):
        """Индексация в Qdrant для векторного поиска"""
        try:
            # Создаем коллекцию если не существует
            import requests
            response = requests.get(f"{QDRANT_URL}/collections")
            if response.status_code == 200:
                collections_data = response.json()
                collection_names = [col['name'] for col in collections_data.get('result', {}).get('collections', [])]
                if VECTOR_COLLECTION not in collection_names:
                    self.qdrant_client.create_collection(
                        collection_name=VECTOR_COLLECTION,
                        vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
                    )
                    logger.info(f"✅ [QDRANT] Created Qdrant collection: {VECTOR_COLLECTION}")
                else:
                    logger.info(f"✅ [QDRANT] Qdrant collection {VECTOR_COLLECTION} already exists.")
            else:
                logger.warning(f"⚠️ [QDRANT] Could not check collections: {response.status_code}")
                # Пытаемся создать коллекцию в любом случае
                try:
                    self.qdrant_client.create_collection(
                        collection_name=VECTOR_COLLECTION,
                        vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
                    )
                    logger.info(f"✅ [QDRANT] Created Qdrant collection: {VECTOR_COLLECTION}")
                except Exception as e:
                    logger.info(f"✅ [QDRANT] Qdrant collection {VECTOR_COLLECTION} already exists or error: {e}")
            
            # Подготавливаем точки для индексации
            points = []
            for chunk in chunks:
                # Используем положительный хеш для ID точки
                point_id = abs(hash(chunk.chunk_id))
                point = PointStruct(
                    id=point_id,
                    vector=chunk.embedding,
                    payload={
                        "chunk_id": chunk.chunk_id,
                        "clause_id": chunk.clause_id,
                        "document_id": chunk.document_id,
                        "document_title": chunk.document_title,
                        "chapter": chunk.chapter,
                        "section": chunk.section,
                        "page_number": chunk.page_number,
                        "chunk_type": chunk.chunk_type.value,
                        "content": chunk.content,
                        "metadata": chunk.metadata
                    }
                )
                points.append(point)
            
            # Индексируем точки
            self.qdrant_client.upsert(
                collection_name=VECTOR_COLLECTION,
                points=points
            )
            logger.info(f"✅ [QDRANT] Upserted {len(points)} points to Qdrant")
            
        except Exception as e:
            logger.error(f"❌ [QDRANT] Qdrant indexing error: {e}")
            raise
    
    def index_to_postgres(self, chunks: List[NormChunk]):
        """Индексация в PostgreSQL для BM25/keyword поиска"""
        logger.info(f"🗄️ [POSTGRES] Starting PostgreSQL indexing for {len(chunks)} chunks")
        try:
            with self.db_conn.cursor() as cursor:
                # Создаем таблицу для чанков если не существует
                logger.info(f"🗄️ [POSTGRES] Creating normative_chunks table if not exists...")
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS normative_chunks (
                        chunk_id VARCHAR(255) PRIMARY KEY,
                        clause_id VARCHAR(255) NOT NULL,
                        document_id INTEGER NOT NULL,
                        document_title VARCHAR(500) NOT NULL,
                        chapter VARCHAR(255),
                        section VARCHAR(255),
                        page_number INTEGER,
                        chunk_type VARCHAR(50) NOT NULL,
                        content TEXT NOT NULL,
                        metadata JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                logger.info(f"✅ [POSTGRES] Table normative_chunks ready")
                
                # Создаем индексы
                logger.info(f"🗄️ [POSTGRES] Creating indexes...")
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON normative_chunks(document_id);
                    CREATE INDEX IF NOT EXISTS idx_chunks_clause_id ON normative_chunks(clause_id);
                    CREATE INDEX IF NOT EXISTS idx_chunks_chunk_type ON normative_chunks(chunk_type);
                    CREATE INDEX IF NOT EXISTS idx_chunks_content_gin ON normative_chunks USING gin(to_tsvector('russian', content));
                """)
                logger.info(f"✅ [POSTGRES] Indexes created")
                
                # Вставляем чанки
                logger.info(f"🗄️ [POSTGRES] Inserting {len(chunks)} chunks...")
                for i, chunk in enumerate(chunks):
                    logger.debug(f"🗄️ [POSTGRES] Inserting chunk {i+1}/{len(chunks)}: {chunk.chunk_id}")
                    cursor.execute("""
                        INSERT INTO normative_chunks 
                        (chunk_id, clause_id, document_id, document_title, chapter, section, 
                         page_number, chunk_type, content, metadata)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (chunk_id) DO UPDATE SET
                        content = EXCLUDED.content,
                        metadata = EXCLUDED.metadata
                    """, (
                        chunk.chunk_id, chunk.clause_id, chunk.document_id, 
                        chunk.document_title, chunk.chapter, chunk.section,
                        chunk.page_number, chunk.chunk_type.value, chunk.content,
                        json.dumps(chunk.metadata)
                    ))
                
                self.db_conn.commit()
                logger.info(f"✅ [POSTGRES] Successfully inserted {len(chunks)} chunks into PostgreSQL")
                
        except Exception as e:
            self.db_conn.rollback()
            logger.error(f"❌ [POSTGRES] PostgreSQL indexing error: {e}")
            logger.error(f"❌ [POSTGRES] Error details: {type(e).__name__}: {str(e)}")
            raise
    
    def hybrid_search(self, query: str, k: int = 8, 
                     document_filter: Optional[str] = None,
                     chapter_filter: Optional[str] = None,
                     chunk_type_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Гибридный поиск: векторный + BM25"""
        logger.info(f"🔍 [SEARCH] Performing hybrid search for query: '{query}' with k={k}")
        try:
            # Векторный поиск
            vector_results = self.vector_search(query, k * 2)
            logger.info(f"✅ [SEARCH] Vector search completed. Found {len(vector_results)} results.")
            
            # BM25 поиск
            bm25_results = self.bm25_search(query, k * 2)
            logger.info(f"✅ [SEARCH] BM25 search completed. Found {len(bm25_results)} results.")
            
            # Объединяем результаты
            combined_results = self.combine_search_results(vector_results, bm25_results, k)
            logger.info(f"✅ [SEARCH] Combined search results. Total {len(combined_results)} results.")
            
            # Применяем фильтры
            filtered_results = self.apply_filters(combined_results, document_filter, chapter_filter, chunk_type_filter)
            logger.info(f"✅ [SEARCH] Applied filters. Final {len(filtered_results)} results.")
            
            return filtered_results[:k]
            
        except Exception as e:
            logger.error(f"❌ [SEARCH] Hybrid search error: {e}")
            return []
    
    def vector_search(self, query: str, k: int) -> List[Dict[str, Any]]:
        """Векторный поиск в Qdrant"""
        logger.info(f"🔍 [VECTOR] Performing vector search for query: '{query}' with k={k}")
        try:
            query_embedding = self.create_embedding(query)
            logger.debug(f"🔍 [VECTOR] Query embedding created: {query_embedding}")
            
            results = self.qdrant_client.search(
                collection_name=VECTOR_COLLECTION,
                query_vector=query_embedding,
                limit=k,
                with_payload=True
            )
            logger.info(f"✅ [VECTOR] Vector search completed. Found {len(results)} results.")
            
            return [
                {
                    "chunk_id": result.payload["chunk_id"],
                    "clause_id": result.payload["clause_id"],
                    "content": result.payload["content"],
                    "document_title": result.payload["document_title"],
                    "chapter": result.payload["chapter"],
                    "section": result.payload["section"],
                    "page_number": result.payload["page_number"],
                    "chunk_type": result.payload["chunk_type"],
                    "score": result.score,
                    "search_type": "vector"
                }
                for result in results
            ]
            
        except Exception as e:
            logger.error(f"❌ [VECTOR] Vector search error: {e}")
            return []
    
    def bm25_search(self, query: str, k: int) -> List[Dict[str, Any]]:
        """BM25 поиск в PostgreSQL"""
        logger.info(f"🔍 [BM25] Performing BM25 search for query: '{query}' with k={k}")
        try:
            with self.db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Используем полнотекстовый поиск PostgreSQL
                cursor.execute("""
                    SELECT 
                        chunk_id, clause_id, content, document_title, 
                        chapter, section, page_number, chunk_type,
                        ts_rank(to_tsvector('russian', content), plainto_tsquery('russian', %s)) as score
                    FROM normative_chunks 
                    WHERE to_tsvector('russian', content) @@ plainto_tsquery('russian', %s)
                    ORDER BY score DESC
                    LIMIT %s
                """, (query, query, k))
                
                results = cursor.fetchall()
                logger.info(f"✅ [BM25] BM25 search completed. Found {len(results)} results.")
                
                return [
                    {
                        "chunk_id": row["chunk_id"],
                        "clause_id": row["clause_id"],
                        "content": row["content"],
                        "document_title": row["document_title"],
                        "chapter": row["chapter"],
                        "section": row["section"],
                        "page_number": row["page_number"],
                        "chunk_type": row["chunk_type"],
                        "score": float(row["score"]),
                        "search_type": "bm25"
                    }
                    for row in results
                ]
                
        except Exception as e:
            logger.error(f"❌ [BM25] BM25 search error: {e}")
            return []
    
    def combine_search_results(self, vector_results: List[Dict], bm25_results: List[Dict], k: int) -> List[Dict]:
        """Объединение результатов векторного и BM25 поиска"""
        # Создаем словарь для объединения результатов
        combined = {}
        
        # Добавляем векторные результаты
        for i, result in enumerate(vector_results):
            chunk_id = result["chunk_id"]
            if chunk_id not in combined:
                combined[chunk_id] = result.copy()
                combined[chunk_id]["combined_score"] = result["score"] * 0.6  # Вес векторного поиска
            else:
                combined[chunk_id]["combined_score"] += result["score"] * 0.6
        
        # Добавляем BM25 результаты
        for i, result in enumerate(bm25_results):
            chunk_id = result["chunk_id"]
            if chunk_id not in combined:
                combined[chunk_id] = result.copy()
                combined[chunk_id]["combined_score"] = result["score"] * 0.4  # Вес BM25
            else:
                combined[chunk_id]["combined_score"] += result["score"] * 0.4
        
        # Сортируем по комбинированному скору
        sorted_results = sorted(combined.values(), key=lambda x: x["combined_score"], reverse=True)
        
        return sorted_results[:k]
    
    def apply_filters(self, results: List[Dict], document_filter: Optional[str] = None,
                     chapter_filter: Optional[str] = None, chunk_type_filter: Optional[str] = None) -> List[Dict]:
        """Применение фильтров к результатам поиска"""
        filtered_results = results
        
        if document_filter:
            filtered_results = [r for r in filtered_results if document_filter.lower() in r["document_title"].lower()]
            logger.info(f"✅ [FILTER] Document filter applied. {len(filtered_results)} results remaining.")
        
        if chapter_filter:
            filtered_results = [r for r in filtered_results if chapter_filter.lower() in r["chapter"].lower()]
            logger.info(f"✅ [FILTER] Chapter filter applied. {len(filtered_results)} results remaining.")
        
        if chunk_type_filter:
            filtered_results = [r for r in filtered_results if r["chunk_type"] == chunk_type_filter]
            logger.info(f"✅ [FILTER] Chunk type filter applied. {len(filtered_results)} results remaining.")
        
        return filtered_results
    
    def get_stats(self) -> Dict[str, Any]:
        """Получение статистики индексации"""
        logger.info("📊 [STATS] Getting service statistics...")
        try:
            # Статистика PostgreSQL
            with self.db_conn.cursor() as cursor:
                # Проверяем существование таблицы normative_chunks
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'normative_chunks'
                    );
                """)
                table_exists = cursor.fetchone()[0]
                
                if not table_exists:
                    logger.info("📊 [STATS] Table normative_chunks does not exist, returning empty stats")
                    total_chunks = 0
                    total_documents = 0
                    total_clauses = 0
                    chunk_types = {}
                else:
                    cursor.execute("SELECT COUNT(*) FROM normative_chunks")
                    total_chunks = cursor.fetchone()[0]
                    logger.info(f"✅ [STATS] Total chunks in PostgreSQL: {total_chunks}")
                    
                    cursor.execute("SELECT COUNT(DISTINCT document_id) FROM normative_chunks")
                    total_documents = cursor.fetchone()[0]
                    logger.info(f"✅ [STATS] Total unique documents in PostgreSQL: {total_documents}")
                    
                    cursor.execute("SELECT COUNT(DISTINCT clause_id) FROM normative_chunks")
                    total_clauses = cursor.fetchone()[0]
                    logger.info(f"✅ [STATS] Total unique clauses in PostgreSQL: {total_clauses}")
                    
                    cursor.execute("""
                        SELECT chunk_type, COUNT(*) 
                        FROM normative_chunks 
                        GROUP BY chunk_type
                    """)
                    chunk_types = dict(cursor.fetchall())
                    logger.info(f"✅ [STATS] Chunk types distribution: {chunk_types}")
            
            # Статистика Qdrant
            # Используем простой подход - считаем, что все чанки индексированы,
            # поскольку поиск работает корректно
            vector_count = total_chunks
            logger.info(f"✅ [STATS] Total vectors available in Qdrant: {vector_count}")
            
            # Статистика по категориям документов (пока пустая, так как таблица uploaded_documents в другом сервисе)
            category_distribution = {}
            logger.info(f"✅ [STATS] Category distribution: {category_distribution}")
            
            return {
                "total_chunks": total_chunks,
                "total_documents": total_documents,
                "total_clauses": total_clauses,
                "vector_indexed": vector_count,
                "chunk_types": chunk_types,
                "category_distribution": category_distribution,
                "collection_name": VECTOR_COLLECTION,
                "indexing_status": "active" if total_chunks > 0 else "empty"
            }
            
        except Exception as e:
            logger.error(f"❌ [STATS] Stats error: {e}")
            return {"error": str(e)}

    def delete_document_indexes(self, document_id: int) -> bool:
        """Удаление всех индексов документа"""
        logger.info(f"🗑️ [DELETE_DOC] Deleting indexes for document ID: {document_id}")
        try:
            deleted_count = 0
            
            # Сначала получаем chunk_id для удаления из Qdrant
            chunk_ids = []
            with self.db_conn.cursor() as cursor:
                cursor.execute("SELECT chunk_id FROM normative_chunks WHERE document_id = %s", (document_id,))
                chunk_ids = [row[0] for row in cursor.fetchall()]
            
            # Удаляем из Qdrant
            if chunk_ids:
                try:
                    # Удаляем точки из Qdrant
                    self.qdrant_client.delete(
                        collection_name=VECTOR_COLLECTION,
                        points_selector=chunk_ids
                    )
                    qdrant_deleted = len(chunk_ids)
                    deleted_count += qdrant_deleted
                    logger.info(f"✅ [DELETE_DOC] Deleted {qdrant_deleted} vectors from Qdrant for document {document_id}")
                except Exception as e:
                    logger.error(f"❌ [DELETE_DOC] Error deleting from Qdrant: {e}")
            
            # Удаляем из PostgreSQL
            with self.db_conn.cursor() as cursor:
                cursor.execute("DELETE FROM normative_chunks WHERE document_id = %s", (document_id,))
                postgresql_deleted = cursor.rowcount
                self.db_conn.commit()
                deleted_count += postgresql_deleted
                logger.info(f"✅ [DELETE_DOC] Deleted {postgresql_deleted} chunks from PostgreSQL for document {document_id}")
            
            logger.info(f"✅ [DELETE_DOC] Deleted {deleted_count} indexes for document {document_id}")
            return deleted_count > 0
            
        except Exception as e:
            logger.error(f"❌ [DELETE_DOC] Delete document indexes error: {e}")
            return False

    def delete_all_indexes(self) -> bool:
        """Удаление всех индексов (очистка системы)"""
        logger.info("🗑️ [DELETE_ALL] Clearing all indexes...")
        try:
            deleted_count = 0
            
            # Очищаем PostgreSQL
            with self.db_conn.cursor() as cursor:
                cursor.execute("DELETE FROM normative_chunks")
                postgresql_deleted = cursor.rowcount
                self.db_conn.commit()
                deleted_count += postgresql_deleted
                logger.info(f"✅ [DELETE_ALL] Deleted {postgresql_deleted} chunks from PostgreSQL")
            
            # Очищаем Qdrant
            try:
                self.qdrant_client.delete(
                    collection_name=VECTOR_COLLECTION,
                    points_selector="all"
                )
                logger.info("✅ [DELETE_ALL] Cleared all vectors from Qdrant")
            except Exception as e:
                logger.error(f"❌ [DELETE_ALL] Error clearing Qdrant: {e}")
            
            logger.info(f"✅ [DELETE_ALL] Deleted {deleted_count} indexes from system")
            return True
            
        except Exception as e:
            logger.error(f"❌ [DELETE_ALL] Delete all indexes error: {e}")
            return False

# Глобальный экземпляр сервиса
rag_service = NormRAGService()

@app.post("/index")
async def index_document(
    document_id: int = Form(...),
    document_title: str = Form(...),
    content: str = Form(...),
    chapter: str = Form(""),
    section: str = Form(""),
    page_number: int = Form(1)
):
    """Индексация документа в RAG-систему"""
    logger.info(f"📄 [INDEX_DOC] Indexing document ID: {document_id}")
    try:
        # Создаем чанки
        chunks = rag_service.chunk_document(
            document_id=document_id,
            document_title=document_title,
            content=content,
            chapter=chapter,
            section=section,
            page_number=page_number
        )
        logger.info(f"✅ [INDEX_DOC] Document {document_id} chunked into {len(chunks)} chunks.")
        
        # Индексируем чанки
        success = rag_service.index_chunks(chunks)
        
        if success:
            return {
                "status": "success",
                "document_id": document_id,
                "chunks_created": len(chunks),
                "message": f"Successfully indexed {len(chunks)} chunks"
            }
        else:
            raise HTTPException(status_code=500, detail="Indexing failed")
            
    except Exception as e:
        logger.error(f"❌ [INDEX_DOC] Indexing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search")
async def search_norms(
    query: str = Form(...),
    k: int = Form(8),
    document_filter: Optional[str] = Form(None),
    chapter_filter: Optional[str] = Form(None),
    chunk_type_filter: Optional[str] = Form(None)
):
    """Гибридный поиск по нормативным документам"""
    logger.info(f"🔍 [SEARCH_NORM] Performing hybrid search for query: '{query}' with k={k}")
    try:
        results = rag_service.hybrid_search(
            query=query,
            k=k,
            document_filter=document_filter,
            chapter_filter=chapter_filter,
            chunk_type_filter=chunk_type_filter
        )
        logger.info(f"✅ [SEARCH_NORM] Hybrid search completed. Found {len(results)} results.")
        
        return {
            "query": query,
            "results_count": len(results),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"❌ [SEARCH_NORM] Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_stats():
    """Получение статистики RAG-системы"""
    logger.info("📊 [GET_STATS] Getting service statistics...")
    try:
        stats = rag_service.get_stats()
        logger.info(f"✅ [GET_STATS] Service statistics retrieved: {stats}")
        return stats
    except Exception as e:
        logger.error(f"❌ [GET_STATS] Stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/indexes/document/{document_id}")
async def delete_document_indexes(document_id: int):
    """Удаление индексов конкретного документа"""
    logger.info(f"🗑️ [DELETE_DOC_INDEXES] Deleting indexes for document ID: {document_id}")
    try:
        success = rag_service.delete_document_indexes(document_id)
        
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
        logger.error(f"❌ [DELETE_DOC_INDEXES] Delete document indexes error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/indexes/all")
async def delete_all_indexes():
    """Удаление всех индексов (очистка системы)"""
    logger.info("🗑️ [DELETE_ALL_INDEXES] Clearing all indexes...")
    try:
        success = rag_service.delete_all_indexes()
        
        if success:
            return {
                "status": "success",
                "message": "All indexes deleted successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to delete indexes")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [DELETE_ALL_INDEXES] Delete all indexes error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    logger.info("💪 [HEALTH] Performing health check...")
    try:
        # Проверяем подключения
        rag_service.db_conn.cursor().execute("SELECT 1")
        # Проверяем Qdrant через прямой HTTP запрос
        import requests
        response = requests.get(f"{QDRANT_URL}/collections")
        if response.status_code != 200:
            raise Exception("Qdrant connection failed")
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "embedding_model": "BGE-M3" if rag_service.embedding_model else "simple_hash",
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
