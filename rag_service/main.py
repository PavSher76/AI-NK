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

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# Константы для чанкинга
CHUNK_SIZE = 500  # ~400-600 токенов
CHUNK_OVERLAP = 75  # ~50-100 токенов
MAX_TOKENS = 1000

# Названия коллекций
VECTOR_COLLECTION = "normative_chunks"
BM25_COLLECTION = "normative_bm25"

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
        self.db_conn = None
        self.qdrant_client = None
        self.embedding_model = None
        self.tokenizer = None
        self.text_splitter = None
        self.connect_services()
        self.initialize_models()
    
    def connect_services(self):
        """Подключение к базам данных"""
        try:
            # PostgreSQL
            self.db_conn = psycopg2.connect(POSTGRES_URL)
            logger.info("Connected to PostgreSQL")
            
            # Qdrant
            self.qdrant_client = qdrant_client.QdrantClient(url=QDRANT_URL)
            logger.info("Connected to Qdrant")
            
        except Exception as e:
            logger.error(f"Service connection error: {e}")
            raise
    
    def initialize_models(self):
        """Инициализация моделей для эмбеддингов и токенизации"""
        try:
            # Используем BGE-M3 для многоязычных эмбеддингов
            self.embedding_model = SentenceTransformer('BAAI/bge-m3')
            logger.info("Loaded BGE-M3 embedding model")
            
            # Токенизатор для подсчета токенов
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
            
            # Простой текстовый сплиттер для чанкинга
            self.text_splitter = None  # Будем использовать простую реализацию
            logger.info("Using simple text splitter")
            
        except Exception as e:
            logger.error(f"Model initialization error: {e}")
            # Fallback к простой модели
            self.embedding_model = None
            self.tokenizer = None
            self.text_splitter = None
    
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
        chunks = []
        
        # Простой чанкинг с учетом токенов
        text_chunks = self.simple_text_split(content)
        
        for i, chunk_text in enumerate(text_chunks):
            if not chunk_text.strip():
                continue
            
            # Определяем тип чанка
            chunk_type = self.detect_chunk_type(chunk_text)
            
            # Извлекаем clause_id
            clause_id = self.extract_clause_id(chunk_text)
            
            # Создаем ID чанка
            chunk_id = self.create_chunk_id(document_id, clause_id, i)
            
            # Метаданные
            metadata = {
                "document_id": document_id,
                "document_title": document_title,
                "chapter": chapter,
                "section": section,
                "page_number": page_number,
                "chunk_type": chunk_type.value,
                "clause_id": clause_id,
                "chunk_index": i,
                "token_count": self.count_tokens(chunk_text),
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
        if self.embedding_model:
            try:
                embedding = self.embedding_model.encode(text, normalize_embeddings=True)
                return embedding.tolist()
            except Exception as e:
                logger.error(f"Embedding creation error: {e}")
        
        # Fallback к простому хеш-эмбеддингу
        return self.create_simple_embedding(text)
    
    def create_simple_embedding(self, text: str) -> List[float]:
        """Простой хеш-эмбеддинг для fallback"""
        hash_obj = hashlib.sha256(text.encode())
        hash_bytes = hash_obj.digest()
        # Преобразуем в 384-мерный вектор (как у BGE-M3)
        embedding = []
        for i in range(384):
            embedding.append(float(hash_bytes[i % len(hash_bytes)]) / 255.0)
        return embedding
    
    def index_chunks(self, chunks: List[NormChunk]) -> bool:
        """Индексация чанков в векторную базу и BM25"""
        try:
            # Создаем эмбеддинги
            for chunk in chunks:
                chunk.embedding = self.create_embedding(chunk.content)
            
            # Индексируем в Qdrant (векторный поиск)
            self.index_to_qdrant(chunks)
            
            # Индексируем в PostgreSQL (BM25/keyword поиск)
            self.index_to_postgres(chunks)
            
            logger.info(f"Successfully indexed {len(chunks)} chunks")
            return True
            
        except Exception as e:
            logger.error(f"Indexing error: {e}")
            return False
    
    def index_to_qdrant(self, chunks: List[NormChunk]):
        """Индексация в Qdrant для векторного поиска"""
        try:
            # Создаем коллекцию если не существует
            collections = self.qdrant_client.get_collections()
            if VECTOR_COLLECTION not in [col.name for col in collections.collections]:
                self.qdrant_client.create_collection(
                    collection_name=VECTOR_COLLECTION,
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
                )
                logger.info(f"Created Qdrant collection: {VECTOR_COLLECTION}")
            
            # Подготавливаем точки для индексации
            points = []
            for chunk in chunks:
                point = PointStruct(
                    id=hash(chunk.chunk_id),
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
            
        except Exception as e:
            logger.error(f"Qdrant indexing error: {e}")
            raise
    
    def index_to_postgres(self, chunks: List[NormChunk]):
        """Индексация в PostgreSQL для BM25/keyword поиска"""
        try:
            with self.db_conn.cursor() as cursor:
                # Создаем таблицу для чанков если не существует
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
                
                # Создаем индексы
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON normative_chunks(document_id);
                    CREATE INDEX IF NOT EXISTS idx_chunks_clause_id ON normative_chunks(clause_id);
                    CREATE INDEX IF NOT EXISTS idx_chunks_chunk_type ON normative_chunks(chunk_type);
                    CREATE INDEX IF NOT EXISTS idx_chunks_content_gin ON normative_chunks USING gin(to_tsvector('russian', content));
                """)
                
                # Вставляем чанки
                for chunk in chunks:
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
                
        except Exception as e:
            self.db_conn.rollback()
            logger.error(f"PostgreSQL indexing error: {e}")
            raise
    
    def hybrid_search(self, query: str, k: int = 8, 
                     document_filter: Optional[str] = None,
                     chapter_filter: Optional[str] = None,
                     chunk_type_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Гибридный поиск: векторный + BM25"""
        try:
            # Векторный поиск
            vector_results = self.vector_search(query, k * 2)
            
            # BM25 поиск
            bm25_results = self.bm25_search(query, k * 2)
            
            # Объединяем результаты
            combined_results = self.combine_search_results(vector_results, bm25_results, k)
            
            # Применяем фильтры
            filtered_results = self.apply_filters(combined_results, document_filter, chapter_filter, chunk_type_filter)
            
            return filtered_results[:k]
            
        except Exception as e:
            logger.error(f"Hybrid search error: {e}")
            return []
    
    def vector_search(self, query: str, k: int) -> List[Dict[str, Any]]:
        """Векторный поиск в Qdrant"""
        try:
            query_embedding = self.create_embedding(query)
            
            results = self.qdrant_client.search(
                collection_name=VECTOR_COLLECTION,
                query_vector=query_embedding,
                limit=k,
                with_payload=True
            )
            
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
            logger.error(f"Vector search error: {e}")
            return []
    
    def bm25_search(self, query: str, k: int) -> List[Dict[str, Any]]:
        """BM25 поиск в PostgreSQL"""
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
            logger.error(f"BM25 search error: {e}")
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
        
        if chapter_filter:
            filtered_results = [r for r in filtered_results if chapter_filter.lower() in r["chapter"].lower()]
        
        if chunk_type_filter:
            filtered_results = [r for r in filtered_results if r["chunk_type"] == chunk_type_filter]
        
        return filtered_results
    
    def get_stats(self) -> Dict[str, Any]:
        """Получение статистики индексации"""
        try:
            # Статистика PostgreSQL
            with self.db_conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM normative_chunks")
                total_chunks = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(DISTINCT document_id) FROM normative_chunks")
                total_documents = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(DISTINCT clause_id) FROM normative_chunks")
                total_clauses = cursor.fetchone()[0]
                
                cursor.execute("""
                    SELECT chunk_type, COUNT(*) 
                    FROM normative_chunks 
                    GROUP BY chunk_type
                """)
                chunk_types = dict(cursor.fetchall())
            
            # Статистика Qdrant
            try:
                collection_info = self.qdrant_client.get_collection(VECTOR_COLLECTION)
                vector_count = collection_info.points_count
            except:
                vector_count = 0
            
            return {
                "total_chunks": total_chunks,
                "total_documents": total_documents,
                "total_clauses": total_clauses,
                "vector_indexed": vector_count,
                "chunk_types": chunk_types,
                "indexing_status": "active" if total_chunks > 0 else "empty"
            }
            
        except Exception as e:
            logger.error(f"Stats error: {e}")
            return {"error": str(e)}

    def delete_document_indexes(self, document_id: int) -> bool:
        """Удаление всех индексов документа"""
        try:
            deleted_count = 0
            
            # Удаляем из PostgreSQL
            with self.db_conn.cursor() as cursor:
                cursor.execute("DELETE FROM normative_chunks WHERE document_id = %s", (document_id,))
                postgresql_deleted = cursor.rowcount
                self.db_conn.commit()
                deleted_count += postgresql_deleted
            
            # Удаляем из Qdrant
            try:
                # Получаем chunk_id для удаления из Qdrant
                with self.db_conn.cursor() as cursor:
                    cursor.execute("SELECT chunk_id FROM normative_chunks WHERE document_id = %s", (document_id,))
                    chunk_ids = [row[0] for row in cursor.fetchall()]
                
                if chunk_ids:
                    # Удаляем точки из Qdrant
                    self.qdrant_client.delete(
                        collection_name=VECTOR_COLLECTION,
                        points_selector=chunk_ids
                    )
                    qdrant_deleted = len(chunk_ids)
                    deleted_count += qdrant_deleted
                    logger.info(f"Deleted {qdrant_deleted} vectors from Qdrant for document {document_id}")
                
            except Exception as e:
                logger.error(f"Error deleting from Qdrant: {e}")
            
            logger.info(f"Deleted {deleted_count} indexes for document {document_id}")
            return deleted_count > 0
            
        except Exception as e:
            logger.error(f"Delete document indexes error: {e}")
            return False

    def delete_all_indexes(self) -> bool:
        """Удаление всех индексов (очистка системы)"""
        try:
            deleted_count = 0
            
            # Очищаем PostgreSQL
            with self.db_conn.cursor() as cursor:
                cursor.execute("DELETE FROM normative_chunks")
                postgresql_deleted = cursor.rowcount
                self.db_conn.commit()
                deleted_count += postgresql_deleted
            
            # Очищаем Qdrant
            try:
                self.qdrant_client.delete(
                    collection_name=VECTOR_COLLECTION,
                    points_selector="all"
                )
                logger.info("Cleared all vectors from Qdrant")
            except Exception as e:
                logger.error(f"Error clearing Qdrant: {e}")
            
            logger.info(f"Deleted {deleted_count} indexes from system")
            return True
            
        except Exception as e:
            logger.error(f"Delete all indexes error: {e}")
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
        logger.error(f"Indexing error: {e}")
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
    try:
        results = rag_service.hybrid_search(
            query=query,
            k=k,
            document_filter=document_filter,
            chapter_filter=chapter_filter,
            chunk_type_filter=chunk_type_filter
        )
        
        return {
            "query": query,
            "results_count": len(results),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_stats():
    """Получение статистики RAG-системы"""
    try:
        stats = rag_service.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/indexes/document/{document_id}")
async def delete_document_indexes(document_id: int):
    """Удаление индексов конкретного документа"""
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
        logger.error(f"Delete document indexes error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/indexes/all")
async def delete_all_indexes():
    """Удаление всех индексов (очистка системы)"""
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
        logger.error(f"Delete all indexes error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    try:
        # Проверяем подключения
        rag_service.db_conn.cursor().execute("SELECT 1")
        rag_service.qdrant_client.get_collections()
        
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
        logger.error(f"Health check error: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
