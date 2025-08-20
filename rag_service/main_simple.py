from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor
import asyncio
import httpx
import json
import logging
from datetime import datetime
import os
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import numpy as np
import hashlib

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="RAG Service", description="RAG сервис для нормоконтроля", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Модели данных
class NormDocument(BaseModel):
    id: int
    code: str
    version: str
    title: str
    content: str
    category: str
    importance: int

class SearchQuery(BaseModel):
    query: str
    limit: int = 10
    threshold: float = 0.7

class SearchResult(BaseModel):
    id: int
    code: str
    version: str
    title: str
    content: str
    category: str
    importance: int
    similarity_score: float
    source: str

class IndexingRequest(BaseModel):
    document_ids: List[int]

class DocumentIndexingRequest(BaseModel):
    document_id: int
    document_title: str
    content: str
    chapter: str = ""
    section: str = ""
    page_number: int = 1

# Конфигурация
POSTGRES_URL = os.getenv("POSTGRES_URL", "postgresql://norms_user:norms_password@norms-db:5432/norms_db")
QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
COLLECTION_NAME = "norms_embeddings"

# Инициализация клиентов
def get_postgres_connection():
    return psycopg2.connect(POSTGRES_URL)

def get_qdrant_client():
    return QdrantClient(QDRANT_URL)

# Простая функция для создания эмбеддингов (хеш-вектор)
def create_simple_embedding(text: str, vector_size: int = 384) -> List[float]:
    """Создает простой эмбеддинг на основе хеша текста"""
    # Создаем хеш текста
    text_hash = hashlib.md5(text.encode()).hexdigest()
    
    # Преобразуем хеш в вектор
    vector = []
    for i in range(0, len(text_hash), 2):
        if len(vector) >= vector_size:
            break
        hex_pair = text_hash[i:i+2]
        value = int(hex_pair, 16) / 255.0  # Нормализуем к [0, 1]
        vector.append(value)
    
    # Дополняем вектор до нужного размера
    while len(vector) < vector_size:
        vector.append(0.0)
    
    return vector[:vector_size]

# Инициализация коллекции Qdrant
def init_qdrant_collection():
    try:
        client = get_qdrant_client()
        
        # Проверяем существование коллекции
        collections = client.get_collections()
        collection_names = [col.name for col in collections.collections]
        
        if COLLECTION_NAME not in collection_names:
            # Создаем коллекцию
            client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE)
            )
            logger.info(f"Создана коллекция Qdrant: {COLLECTION_NAME}")
        else:
            logger.info(f"Коллекция Qdrant уже существует: {COLLECTION_NAME}")
            
    except Exception as e:
        logger.error(f"Ошибка инициализации Qdrant: {e}")

# API endpoints
@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    try:
        # Проверяем подключение к PostgreSQL
        conn = get_postgres_connection()
        conn.close()
        
        # Проверяем подключение к Qdrant
        client = get_qdrant_client()
        client.get_collections()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "postgresql": "connected",
                "qdrant": "connected",
                "embedding_model": "simple_hash_based"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents", response_model=List[NormDocument])
async def get_documents(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    category: Optional[str] = None
):
    """Получение списка нормативных документов"""
    try:
        conn = get_postgres_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
        SELECT id, document_number as code, version, document_name as title, document_type as content, document_type as category, 1 as importance
        FROM normative_documents
        WHERE 1=1
        """
        params = []
        
        if category:
            query += " AND category = %s"
            params.append(category)
        
        query += " ORDER BY importance DESC, id LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        documents = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return [NormDocument(**doc) for doc in documents]
        
    except Exception as e:
        logger.error(f"Ошибка получения документов: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/index", response_model=Dict[str, Any])
async def index_documents(request: IndexingRequest):
    """Индексация документов в векторную базу"""
    try:
        conn = get_postgres_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Получаем документы для индексации
        if request.document_ids:
            placeholders = ','.join(['%s'] * len(request.document_ids))
            query = f"""
            SELECT id, document_number as code, version, document_name as title, document_type as content, document_type as category, 1 as importance
            FROM normative_documents
            WHERE id IN ({placeholders})
            """
            cursor.execute(query, request.document_ids)
        else:
            # Индексируем все документы
            query = """
            SELECT id, document_number as code, version, document_name as title, document_type as content, document_type as category, 1 as importance
            FROM normative_documents
            """
            cursor.execute(query)
        
        documents = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if not documents:
            return {"message": "Нет документов для индексации", "indexed_count": 0}
        
        # Создаем эмбеддинги
        points = []
        for doc in documents:
            # Создаем текст для эмбеддинга
            text = f"{doc['title']} {doc['content']}"
            
            # Создаем простой эмбеддинг
            embedding = create_simple_embedding(text)
            
            point = PointStruct(
                id=doc['id'],
                vector=embedding,
                payload={
                    "code": doc['code'],
                    "version": doc['version'],
                    "title": doc['title'],
                    "content": doc['content'],
                    "category": doc['category'],
                    "importance": doc['importance']
                }
            )
            points.append(point)
        
        # Загружаем в Qdrant
        client = get_qdrant_client()
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=points
        )
        
        logger.info(f"Проиндексировано {len(documents)} документов")
        
        return {
            "message": "Документы успешно проиндексированы",
            "indexed_count": len(documents),
            "collection": COLLECTION_NAME
        }
        
    except Exception as e:
        logger.error(f"Ошибка индексации: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/index-document", response_model=Dict[str, Any])
async def index_single_document(request: DocumentIndexingRequest):
    """Индексация одного документа от document-parser"""
    try:
        # Создаем эмбеддинг для контента
        embedding = create_simple_embedding(request.content)
        
        # Создаем точку для Qdrant
        point = PointStruct(
            id=request.document_id,
            vector=embedding,
            payload={
                "document_id": request.document_id,
                "title": request.document_title,
                "content": request.content,
                "chapter": request.chapter,
                "section": request.section,
                "page_number": request.page_number,
                "category": "uploaded_document"
            }
        )
        
        # Загружаем в Qdrant
        client = get_qdrant_client()
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=[point]
        )
        
        logger.info(f"Проиндексирован документ {request.document_id}: {request.document_title}")
        
        return {
            "message": "Документ успешно проиндексирован",
            "document_id": request.document_id,
            "title": request.document_title,
            "collection": COLLECTION_NAME
        }
        
    except Exception as e:
        logger.error(f"Ошибка индексации документа: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search", response_model=List[SearchResult])
async def search_documents(query: SearchQuery):
    """Семантический поиск по нормативным документам"""
    try:
        # Создаем эмбеддинг для запроса
        query_embedding = create_simple_embedding(query.query)
        
        # Ищем в Qdrant
        client = get_qdrant_client()
        search_results = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_embedding,
            limit=query.limit,
            score_threshold=query.threshold
        )
        
        # Формируем результаты
        results = []
        for result in search_results:
            search_result = SearchResult(
                id=result.id,
                code=result.payload["code"],
                version=result.payload["version"],
                title=result.payload["title"],
                content=result.payload["content"],
                category=result.payload["category"],
                importance=result.payload["importance"],
                similarity_score=result.score,
                source="vector_search"
            )
            results.append(search_result)
        
        return results
        
    except Exception as e:
        logger.error(f"Ошибка поиска: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/search/hybrid")
async def hybrid_search(
    query: str = Query(..., description="Поисковый запрос"),
    limit: int = Query(10, ge=1, le=50),
    semantic_weight: float = Query(0.7, ge=0.0, le=1.0)
):
    """Гибридный поиск (семантический + ключевые слова)"""
    try:
        # Семантический поиск
        query_embedding = create_simple_embedding(query)
        client = get_qdrant_client()
        
        semantic_results = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_embedding,
            limit=limit * 2,  # Получаем больше результатов для реранжирования
            score_threshold=0.5
        )
        
        # Получаем полную информацию о документах
        conn = get_postgres_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Простой текстовый поиск в PostgreSQL
        text_query = """
        SELECT id, document_number as code, version, document_name as title, document_type as content, document_type as category, 1 as importance
        FROM normative_documents
        WHERE document_name ILIKE %s OR document_type ILIKE %s
        ORDER BY 1 DESC
        LIMIT %s
        """
        search_pattern = f"%{query}%"
        cursor.execute(text_query, [search_pattern, search_pattern, limit])
        text_results = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Объединяем и ранжируем результаты
        combined_results = {}
        
        # Добавляем семантические результаты
        for result in semantic_results:
            combined_results[result.id] = {
                "id": result.id,
                "code": result.payload["code"],
                "version": result.payload["version"],
                "title": result.payload["title"],
                "content": result.payload["content"],
                "category": result.payload["category"],
                "importance": result.payload["importance"],
                "semantic_score": result.score,
                "text_score": 0.0,
                "final_score": result.score * semantic_weight
            }
        
        # Добавляем текстовые результаты
        for doc in text_results:
            if doc['id'] in combined_results:
                combined_results[doc['id']]['text_score'] = 1.0
                combined_results[doc['id']]['final_score'] += (1.0 - semantic_weight)
            else:
                combined_results[doc['id']] = {
                    "id": doc['id'],
                    "code": doc['code'],
                    "version": doc['version'],
                    "title": doc['title'],
                    "content": doc['content'],
                    "category": doc['category'],
                    "importance": doc['importance'],
                    "semantic_score": 0.0,
                    "text_score": 1.0,
                    "final_score": 1.0 - semantic_weight
                }
        
        # Сортируем по финальному скору
        sorted_results = sorted(
            combined_results.values(),
            key=lambda x: x['final_score'],
            reverse=True
        )[:limit]
        
        # Формируем ответ
        results = []
        for result in sorted_results:
            search_result = SearchResult(
                id=result["id"],
                code=result["code"],
                version=result["version"],
                title=result["title"],
                content=result["content"],
                category=result["category"],
                importance=result["importance"],
                similarity_score=result["final_score"],
                source="hybrid_search"
            )
            results.append(search_result)
        
        return results
        
    except Exception as e:
        logger.error(f"Ошибка гибридного поиска: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_stats():
    """Статистика индексации"""
    try:
        # Статистика PostgreSQL
        conn = get_postgres_connection()
        cursor = conn.cursor()
        
        # Считаем только документы из uploaded_documents (загруженные пользователем)
        # которые отображаются в интерфейсе на вкладке "Нормативные документы"
        cursor.execute("SELECT COUNT(*) FROM uploaded_documents WHERE processing_status = 'completed'")
        total_documents = cursor.fetchone()[0]
        
        # Получаем распределение по категориям только из uploaded_documents
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN original_filename ILIKE '%ГОСТ%' THEN 'ГОСТ'
                    WHEN original_filename ILIKE '%СП%' THEN 'СП'
                    WHEN original_filename ILIKE '%СНиП%' THEN 'СНиП'
                    WHEN original_filename ILIKE '%ТР ТС%' THEN 'ТР ТС'
                    ELSE 'Другие'
                END as category,
                COUNT(*)
            FROM uploaded_documents 
            WHERE processing_status = 'completed'
            GROUP BY 
                CASE 
                    WHEN original_filename ILIKE '%ГОСТ%' THEN 'ГОСТ'
                    WHEN original_filename ILIKE '%СП%' THEN 'СП'
                    WHEN original_filename ILIKE '%СНиП%' THEN 'СНиП'
                    WHEN original_filename ILIKE '%ТР ТС%' THEN 'ТР ТС'
                    ELSE 'Другие'
                END
        """)
        category_stats = dict(cursor.fetchall())
        
        cursor.close()
        conn.close()
        
        # Статистика Qdrant
        try:
            client = get_qdrant_client()
            # Используем прямой HTTP запрос для получения статистики
            import httpx
            response = httpx.get(f"{QDRANT_URL}/collections/{COLLECTION_NAME}")
            if response.status_code == 200:
                data = response.json()
                indexed_count = data.get("result", {}).get("points_count", 0)
                logger.info(f"Qdrant статистика: {indexed_count} точек в коллекции {COLLECTION_NAME}")
            else:
                logger.warning(f"Не удалось получить статистику Qdrant: HTTP {response.status_code}")
                indexed_count = 0
        except Exception as e:
            logger.warning(f"Не удалось получить статистику Qdrant: {e}")
            indexed_count = 0
        
        return {
            "total_documents": total_documents,
            "indexed_documents": indexed_count,
            "indexing_progress": f"{(indexed_count/total_documents*100):.1f}%" if total_documents > 0 else "0%",
            "category_distribution": category_stats,
            "collection_name": COLLECTION_NAME
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Инициализация при запуске
@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске сервиса"""
    logger.info("Запуск RAG сервиса (упрощенная версия)...")
    init_qdrant_collection()
    logger.info("RAG сервис готов к работе")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
