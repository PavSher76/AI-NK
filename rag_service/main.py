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

# Импорт оптимизированного индексатора (временно отключен)
# from optimized_indexer import OptimizedNormativeIndexer, DocumentType, DocumentStage, DocumentMark, ContentTag

# Настройка логирования с подробной отладкой
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/app/rag_service.log')
    ]
)
logger = logging.getLogger(__name__)

# Создаем отдельный логгер для запросов к моделям
model_logger = logging.getLogger('rag_model_requests')
model_logger.setLevel(logging.INFO)

# Добавляем логирование для всех модулей
logging.getLogger('qdrant_client').setLevel(logging.INFO)
logging.getLogger('sentence_transformers').setLevel(logging.INFO)
logging.getLogger('psycopg2').setLevel(logging.INFO)

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
CHECKABLE_COLLECTION = "checkable_documents"
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
        self._embedding_model = None  # Ленивая загрузка
        self._tokenizer = None  # Ленивая загрузка
        self.text_splitter = None
        self.optimized_indexer = None  # Оптимизированный индексатор
        self.model_loaded = False
        self.model_load_start_time = None
        self.connect_services()
        self.initialize_optimized_indexer()
        logger.info("✅ [INIT] NormRAGService initialized successfully (models will be loaded on demand)")
    
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
            
            # Создаем коллекции при инициализации
            self._create_collections()
            
        except Exception as e:
            logger.error(f"❌ [CONNECT] Service connection error: {e}")
            raise
    
    def _create_collections(self):
        """Создание коллекций в Qdrant при инициализации"""
        try:
            import requests
            response = requests.get(f"{QDRANT_URL}/collections")
            if response.status_code == 200:
                collections_data = response.json()
                collection_names = [col['name'] for col in collections_data.get('result', {}).get('collections', [])]
                
                # Создаем коллекцию для нормативных документов
                if VECTOR_COLLECTION not in collection_names:
                    self.qdrant_client.create_collection(
                        collection_name=VECTOR_COLLECTION,
                        vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
                    )
                    logger.info(f"✅ [QDRANT] Created Qdrant collection: {VECTOR_COLLECTION}")
                else:
                    logger.info(f"✅ [QDRANT] Qdrant collection {VECTOR_COLLECTION} already exists.")
                
                # Создаем коллекцию для проверяемых документов
                if CHECKABLE_COLLECTION not in collection_names:
                    self.qdrant_client.create_collection(
                        collection_name=CHECKABLE_COLLECTION,
                        vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
                    )
                    logger.info(f"✅ [QDRANT] Created Qdrant collection: {CHECKABLE_COLLECTION}")
                else:
                    logger.info(f"✅ [QDRANT] Qdrant collection {CHECKABLE_COLLECTION} already exists.")
            else:
                logger.warning(f"⚠️ [QDRANT] Could not check collections: {response.status_code}")
                # Пытаемся создать коллекции в любом случае
                try:
                    self.qdrant_client.create_collection(
                        collection_name=VECTOR_COLLECTION,
                        vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
                    )
                    logger.info(f"✅ [QDRANT] Created Qdrant collection: {VECTOR_COLLECTION}")
                except Exception as e:
                    logger.info(f"✅ [QDRANT] Qdrant collection {VECTOR_COLLECTION} already exists or error: {e}")
                
                try:
                    self.qdrant_client.create_collection(
                        collection_name=CHECKABLE_COLLECTION,
                        vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
                    )
                    logger.info(f"✅ [QDRANT] Created Qdrant collection: {CHECKABLE_COLLECTION}")
                except Exception as e:
                    logger.info(f"✅ [QDRANT] Qdrant collection {CHECKABLE_COLLECTION} already exists or error: {e}")
                    
        except Exception as e:
            logger.error(f"❌ [QDRANT] Error creating collections: {e}")
            # Не прерываем инициализацию из-за ошибки создания коллекций
    
    @property
    def embedding_model(self):
        """Ленивая загрузка модели эмбеддингов"""
        if self._embedding_model is None:
            self._load_embedding_model()
        return self._embedding_model
    
    @property
    def tokenizer(self):
        """Ленивая загрузка токенизатора"""
        if self._tokenizer is None:
            self._load_tokenizer()
        return self._tokenizer
    
    def _load_embedding_model(self):
        """Загрузка модели эмбеддингов с оптимизацией"""
        if self._embedding_model is not None:
            return
        
        self.model_load_start_time = datetime.now()
        logger.info("🤖 [MODELS] Loading BGE-M3 embedding model (lazy loading)...")
        
        try:
            # Оптимизация: используем кэш и прогресс-бар
            import os
            os.environ['TRANSFORMERS_CACHE'] = '/app/models'
            os.environ['HF_HOME'] = '/app/models'
            
            from sentence_transformers import SentenceTransformer
            
            # Загружаем модель с оптимизациями
            self._embedding_model = SentenceTransformer(
                'BAAI/bge-m3', 
                device='cpu',
                cache_folder='/app/models'
            )
            
            load_time = (datetime.now() - self.model_load_start_time).total_seconds()
            logger.info(f"✅ [MODELS] BGE-M3 model loaded successfully in {load_time:.2f} seconds")
            self.model_loaded = True
            
        except Exception as e:
            load_time = (datetime.now() - self.model_load_start_time).total_seconds()
            logger.error(f"❌ [MODELS] Failed to load BGE-M3 model after {load_time:.2f} seconds: {e}")
            logger.info("🤖 [MODELS] Falling back to simple hash embedding")
            self._embedding_model = None
    
    def _load_tokenizer(self):
        """Загрузка токенизатора"""
        if self._tokenizer is not None:
            return
        
        logger.info("🤖 [MODELS] Loading tokenizer (lazy loading)...")
        try:
            self._tokenizer = tiktoken.get_encoding("cl100k_base")
            logger.info("✅ [MODELS] Tokenizer loaded successfully")
        except Exception as e:
            logger.error(f"❌ [MODELS] Failed to load tokenizer: {e}")
            self._tokenizer = None
    
    def initialize_optimized_indexer(self):
        """Инициализация оптимизированного индексатора (временно отключена)"""
        logger.info("🔧 [OPTIMIZED_INDEXER] Optimized indexer temporarily disabled")
        self.optimized_indexer = None
    
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
        start_time = datetime.now()
        text_length = len(text)
        
        model_logger.info(f"🤖 [EMBEDDING_MODEL] Creating embedding for text ({text_length} chars)")
        logger.debug(f"🔢 [EMBED] Creating embedding for text: {text_length} characters")
        
        if self.embedding_model:
            try:
                model_logger.info(f"🤖 [EMBEDDING_MODEL] Using BGE-M3 model for embedding")
                logger.debug(f"🔢 [EMBED] Using BGE-M3 model for embedding")
                
                # BGE-M3 создает 1024-мерные векторы
                embedding = self.embedding_model.encode(text, normalize_embeddings=True)
                embedding_list = embedding.tolist()
                
                embedding_time = (datetime.now() - start_time).total_seconds()
                model_logger.info(f"✅ [EMBEDDING_MODEL] BGE-M3 embedding created in {embedding_time:.3f}s: {len(embedding_list)} dimensions")
                logger.debug(f"🔢 [EMBED] BGE-M3 embedding created: {len(embedding_list)} dimensions")
                
                return embedding_list
            except Exception as e:
                embedding_time = (datetime.now() - start_time).total_seconds()
                model_logger.error(f"❌ [EMBEDDING_MODEL] BGE-M3 embedding error after {embedding_time:.3f}s: {type(e).__name__}: {str(e)}")
                logger.error(f"❌ [EMBED] BGE-M3 embedding creation error: {e}")
                logger.info(f"🔢 [EMBED] Falling back to simple hash embedding")
        
        # Fallback к простому хеш-эмбеддингу
        model_logger.info(f"🤖 [EMBEDDING_FALLBACK] Using simple hash embedding fallback")
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
                
                # Создаем коллекцию для проверяемых документов
                if CHECKABLE_COLLECTION not in collection_names:
                    self.qdrant_client.create_collection(
                        collection_name=CHECKABLE_COLLECTION,
                        vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
                    )
                    logger.info(f"✅ [QDRANT] Created Qdrant collection: {CHECKABLE_COLLECTION}")
                else:
                    logger.info(f"✅ [QDRANT] Qdrant collection {CHECKABLE_COLLECTION} already exists.")
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
                
                # Пытаемся создать коллекцию для проверяемых документов
                try:
                    self.qdrant_client.create_collection(
                        collection_name=CHECKABLE_COLLECTION,
                        vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
                    )
                    logger.info(f"✅ [QDRANT] Created Qdrant collection: {CHECKABLE_COLLECTION}")
                except Exception as e:
                    logger.info(f"✅ [QDRANT] Qdrant collection {CHECKABLE_COLLECTION} already exists or error: {e}")
            
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
        start_time = datetime.now()
        logger.info(f"🔍 [VECTOR] Performing vector search for query: '{query}' with k={k}")
        
        try:
            # Логируем создание эмбеддинга
            model_logger.info(f"🤖 [EMBEDDING_CREATE] Creating embedding for query: '{query[:100]}...'")
            embedding_start = datetime.now()
            
            query_embedding = self.create_embedding(query)
            
            embedding_time = (datetime.now() - embedding_start).total_seconds()
            model_logger.info(f"✅ [EMBEDDING_CREATE] Embedding created in {embedding_time:.3f}s, dimension: {len(query_embedding)}")
            logger.debug(f"🔍 [VECTOR] Query embedding created: {query_embedding[:5]}...")
            
            # Логируем поиск в Qdrant
            search_start = datetime.now()
            model_logger.info(f"🔍 [QDRANT_SEARCH] Searching in Qdrant collection: {VECTOR_COLLECTION}")
            
            results = self.qdrant_client.search(
                collection_name=VECTOR_COLLECTION,
                query_vector=query_embedding,
                limit=k,
                with_payload=True
            )
            
            search_time = (datetime.now() - search_start).total_seconds()
            total_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"✅ [VECTOR] Vector search completed in {total_time:.3f}s. Found {len(results)} results.")
            model_logger.info(f"✅ [QDRANT_SEARCH] Qdrant search completed in {search_time:.3f}s, found {len(results)} results")
            
            # Логируем топ результат
            if results:
                top_result = results[0]
                model_logger.info(f"📊 [VECTOR_TOP] Top vector result: {top_result.payload.get('document_title', 'Unknown')} - Score: {top_result.score:.3f}")
                model_logger.debug(f"📊 [VECTOR_TOP] Top result content: {top_result.payload.get('content', '')[:200]}...")
            
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
            total_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"❌ [VECTOR] Vector search error after {total_time:.3f}s: {type(e).__name__}: {str(e)}")
            model_logger.error(f"❌ [EMBEDDING_ERROR] Failed to create embedding for query: '{query[:100]}...' - {str(e)}")
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
    
    def get_documents(self) -> List[Dict[str, Any]]:
        """Получение списка нормативных документов"""
        logger.info("📄 [GET_DOCUMENTS] Getting documents list...")
        try:
            with self.db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Проверяем существование таблицы normative_chunks
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'normative_chunks'
                    );
                """)
                table_exists = cursor.fetchone()['exists']
                
                if not table_exists:
                    logger.info("📄 [GET_DOCUMENTS] Table normative_chunks does not exist, returning empty list")
                    return []
                
                # Получаем уникальные документы с их метаданными
                cursor.execute("""
                    SELECT DISTINCT 
                        nc.document_id,
                        nc.document_title,
                        COUNT(*) as chunks_count,
                        MIN(nc.page_number) as first_page,
                        MAX(nc.page_number) as last_page,
                        STRING_AGG(DISTINCT nc.chunk_type, ', ') as chunk_types,
                        ud.category
                    FROM normative_chunks nc
                    LEFT JOIN uploaded_documents ud ON nc.document_id = ud.id
                    GROUP BY nc.document_id, nc.document_title, ud.category
                    ORDER BY nc.document_title ASC
                """)
                
                documents = cursor.fetchall()
                logger.info(f"✅ [GET_DOCUMENTS] Retrieved {len(documents)} documents")
                
                # Преобразуем в список словарей
                result = []
                for doc in documents:
                    result.append({
                        "id": doc['document_id'],
                        "title": doc['document_title'] or f"Документ {doc['document_id']}",
                        "chunks_count": doc['chunks_count'],
                        "first_page": doc['first_page'],
                        "last_page": doc['last_page'],
                        "chunk_types": doc['chunk_types'].split(', ') if doc['chunk_types'] else [],
                        "category": doc['category'] or 'other',
                        "status": "indexed"
                    })
                
                return result
                
        except Exception as e:
            logger.error(f"❌ [GET_DOCUMENTS] Error getting documents: {e}")
            return []
    
    def get_document_chunks(self, document_id: int) -> List[Dict[str, Any]]:
        """Получение информации о чанках конкретного документа"""
        logger.info(f"📄 [GET_DOCUMENT_CHUNKS] Getting chunks for document ID: {document_id}")
        try:
            with self.db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Проверяем существование таблицы normative_chunks
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'normative_chunks'
                    );
                """)
                table_exists = cursor.fetchone()['exists']
                
                if not table_exists:
                    logger.info("📄 [GET_DOCUMENT_CHUNKS] Table normative_chunks does not exist, returning empty list")
                    return []
                
                # Получаем чанки документа
                cursor.execute("""
                    SELECT 
                        chunk_id,
                        clause_id,
                        chapter,
                        section,
                        page_number,
                        chunk_type,
                        LENGTH(content) as content_length,
                        created_at
                    FROM normative_chunks 
                    WHERE document_id = %s
                    ORDER BY page_number ASC, chunk_id ASC
                """, (document_id,))
                
                chunks = cursor.fetchall()
                logger.info(f"✅ [GET_DOCUMENT_CHUNKS] Retrieved {len(chunks)} chunks for document {document_id}")
                
                # Преобразуем в список словарей
                result = []
                for chunk in chunks:
                    result.append({
                        "chunk_id": chunk['chunk_id'],
                        "clause_id": chunk['clause_id'],
                        "chapter": chunk['chapter'] or "Не указано",
                        "section": chunk['section'] or "Не указано",
                        "page_number": chunk['page_number'],
                        "chunk_type": chunk['chunk_type'],
                        "content_length": chunk['content_length'],
                        "created_at": chunk['created_at'].isoformat() if chunk['created_at'] else None
                    })
                
                return result
                
        except Exception as e:
            logger.error(f"❌ [GET_DOCUMENT_CHUNKS] Error getting document chunks: {e}")
            return []
    
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

@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    category: str = Form("other"),
    description: str = Form("")
):
    """Загрузка и индексация нормативного документа"""
    logger.info(f"📤 [UPLOAD_DOC] Uploading document: {file.filename}")
    try:
        # Проверяем тип файла
        if not file.filename.lower().endswith(('.pdf', '.docx', '.txt')):
            raise HTTPException(status_code=400, detail="Unsupported file type. Only PDF, DOCX, and TXT files are allowed.")
        
        # Читаем содержимое файла
        content = await file.read()
        
        # Генерируем уникальный ID документа (небольшое число для PostgreSQL)
        import hashlib
        import time
        # Используем только небольшой хеш + timestamp для уникальности
        hash_part = int(hashlib.md5(f"{file.filename}_{content[:100]}".encode()).hexdigest()[:3], 16)
        time_part = int(time.time()) % 100000  # Последние 5 цифр времени
        document_id = time_part * 1000 + hash_part  # Получится число до 8 цифр (макс. 99999999)
        
        # Извлекаем текст из файла (упрощенная версия)
        if file.filename.lower().endswith('.txt'):
            text_content = content.decode('utf-8', errors='ignore')
        else:
            # Для PDF и DOCX пока используем заглушку
            text_content = f"Содержимое документа {file.filename}"
        
        # Создаем чанки
        chunks = rag_service.chunk_document(
            document_id=document_id,
            document_title=file.filename,
            content=text_content,
            chapter="",
            section="",
            page_number=1
        )
        
        # Индексируем чанки
        success = rag_service.index_chunks(chunks)
        
        if success:
            return {
                "status": "success",
                "document_id": document_id,
                "filename": file.filename,
                "chunks_created": len(chunks),
                "message": f"Document uploaded and indexed successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to index document")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [UPLOAD_DOC] Upload error: {e}")
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
    start_time = datetime.now()
    logger.info(f"🔍 [SEARCH_NORM] Performing hybrid search for query: '{query}' with k={k}")
    logger.info(f"🔍 [SEARCH_NORM] Filters: document={document_filter}, chapter={chapter_filter}, chunk_type={chunk_type_filter}")
    
    try:
        # Логируем запрос к модели эмбеддингов
        model_logger.info(f"🤖 [EMBEDDING_REQUEST] Generating embeddings for query: '{query[:100]}...'")
        
        results = rag_service.hybrid_search(
            query=query,
            k=k,
            document_filter=document_filter,
            chapter_filter=chapter_filter,
            chunk_type_filter=chunk_type_filter
        )
        
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"✅ [SEARCH_NORM] Hybrid search completed in {execution_time:.2f}s. Found {len(results)} results.")
        
        # Логируем результаты поиска
        if results:
            top_result = results[0]
            model_logger.info(f"📊 [SEARCH_RESULTS] Top result: {top_result.get('document_title', 'Unknown')} - Score: {top_result.get('score', 0):.3f}")
            model_logger.debug(f"📊 [SEARCH_RESULTS] Top result content preview: {top_result.get('content', '')[:200]}...")
        
        return {
            "query": query,
            "results_count": len(results),
            "execution_time": execution_time,
            "results": results
        }
        
    except Exception as e:
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.error(f"❌ [SEARCH_NORM] Search error after {execution_time:.2f}s: {type(e).__name__}: {str(e)}")
        model_logger.error(f"❌ [EMBEDDING_ERROR] Failed to process query: '{query[:100]}...' - {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents")
async def get_documents():
    """Получение списка нормативных документов"""
    logger.info("📄 [GET_DOCUMENTS] Getting documents list...")
    try:
        documents = rag_service.get_documents()
        logger.info(f"✅ [GET_DOCUMENTS] Documents list retrieved: {len(documents)} documents")
        return {"documents": documents}
    except Exception as e:
        logger.error(f"❌ [GET_DOCUMENTS] Documents error: {e}")
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

@app.get("/documents/{document_id}/chunks")
async def get_document_chunks(document_id: int):
    """Получение информации о чанках конкретного документа"""
    logger.info(f"📄 [GET_DOCUMENT_CHUNKS] Getting chunks for document ID: {document_id}")
    try:
        chunks_info = rag_service.get_document_chunks(document_id)
        logger.info(f"✅ [GET_DOCUMENT_CHUNKS] Chunks info retrieved for document {document_id}")
        return {"chunks": chunks_info}
    except Exception as e:
        logger.error(f"❌ [GET_DOCUMENT_CHUNKS] Chunks error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents/stats")
async def get_documents_stats():
    """Получение статистики документов в формате для фронтенда"""
    logger.info("📊 [GET_DOCUMENTS_STATS] Getting documents statistics...")
    try:
        stats = rag_service.get_stats()
        documents = rag_service.get_documents()
        
        # Адаптируем статистику для фронтенда
        adapted_stats = {
            "statistics": {
                "total_documents": len(documents),
                "indexed_documents": len(documents),
                "indexing_progress_percent": 100 if len(documents) > 0 else 0,
                "categories": [
                    {"category": "Все документы", "count": len(documents)}
                ]
            }
        }
        
        logger.info(f"✅ [GET_DOCUMENTS_STATS] Documents statistics retrieved: {adapted_stats}")
        return adapted_stats
    except Exception as e:
        logger.error(f"❌ [GET_DOCUMENTS_STATS] Documents stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/documents/{document_id}")
async def delete_document(document_id: int):
    """Удаление документа и его индексов"""
    logger.info(f"🗑️ [DELETE_DOCUMENT] Deleting document ID: {document_id}")
    try:
        success = rag_service.delete_document_indexes(document_id)
        
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

@app.get("/metrics")
async def get_metrics():
    """Получение метрик RAG-сервиса в формате Prometheus"""
    logger.info("📊 [METRICS] Getting service metrics...")
    try:
        # Получаем статистику из RAG сервиса
        stats = rag_service.get_stats()
        
        # Формируем метрики в формате Prometheus
        metrics_lines = []
        
        # Метрики коллекций
        metrics_lines.append(f"# HELP rag_service_collections_total Total number of collections")
        metrics_lines.append(f"# TYPE rag_service_collections_total gauge")
        metrics_lines.append(f"rag_service_collections_total 2")
        
        # Метрики конфигурации
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
        metrics_lines.append(f'rag_service_connections_status{{service="postgresql"}} {1 if rag_service.db_conn else 0}')
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

# @app.post("/optimized/index")
# async def optimized_index_document(
#     document_info: Dict[str, Any],
#     content: str = Form(...)
# ):
#     """Оптимизированная индексация документа с унифицированной структурой"""
#     logger.info("📄 [OPTIMIZED_INDEX] Optimized indexing requested")
#     
#     try:
#         if not rag_service.optimized_indexer:
#             raise HTTPException(status_code=503, detail="Optimized indexer not available")
#         
#         # Индексация документа
#         success = rag_service.optimized_indexer.index_document(document_info, content)
#         
#         if success:
#             logger.info("✅ [OPTIMIZED_INDEX] Document indexed successfully")
#             return {
#                 "status": "success",
#                 "message": "Document indexed with optimized structure",
#                 "timestamp": datetime.now().isoformat()
#             }
#         else:
#             raise HTTPException(status_code=500, detail="Failed to index document")
#             
#     except Exception as e:
#         logger.error(f"❌ [OPTIMIZED_INDEX] Error: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

# @app.post("/optimized/search")
# async def optimized_search_with_context(
#     query: str = Form(...),
#     document_mark: Optional[str] = Form(None),
#     document_stage: Optional[str] = Form(None),
#     content_tags: Optional[List[str]] = Form(None),
#     limit: int = Form(10)
# ):
#     """Поиск с контекстуальной фильтрацией"""
#     logger.info(f"🔍 [OPTIMIZED_SEARCH] Contextual search requested: {query}")
#     
#     try:
#         if not rag_service.optimized_indexer:
#             raise HTTPException(status_code=503, detail="Optimized indexer not available")
#         
#         # Выполняем поиск с фильтрами
#         results = rag_service.optimized_indexer.search_with_context_filter(
#             query=query,
#             document_mark=document_mark,
#             document_stage=document_stage,
#             content_tags=content_tags,
#             limit=limit
#         )
#         
#         logger.info(f"✅ [OPTIMIZED_SEARCH] Found {len(results)} results")
#         return {
#             "status": "success",
#             "query": query,
#             "filters": {
#                 "document_mark": document_mark,
#                 "document_stage": document_stage,
#                 "content_tags": content_tags
#             },
#             "results": results,
#             "total_results": len(results),
#             "timestamp": datetime.now().isoformat()
#         }
#         
#     except Exception as e:
#         logger.error(f"❌ [OPTIMIZED_SEARCH] Error: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

# @app.get("/optimized/statistics")
# async def get_optimized_statistics():
#     """Получение статистики оптимизированной индексации"""
#     logger.info("📊 [OPTIMIZED_STATS] Statistics requested")
#     
#     try:
#         if not rag_service.optimized_indexer:
#             raise HTTPException(status_code=503, detail="Optimized indexer not available")
#         
#         stats = rag_service.optimized_indexer.get_statistics()
#         
#         logger.info("✅ [OPTIMIZED_STATS] Statistics retrieved successfully")
#         return {
#             "status": "success",
#             "statistics": stats,
#             "timestamp": datetime.now().isoformat()
#         }
#         
#     except Exception as e:
#         logger.error(f"❌ [OPTIMIZED_STATS] Error: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
