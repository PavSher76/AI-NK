"""
Векторный индексатор для архива технической документации
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from qdrant_client.http.exceptions import UnexpectedResponse

from .models import DocumentSection
from .config import QDRANT_URL, QDRANT_COLLECTION_NAME, EMBEDDING_DIMENSION

logger = logging.getLogger(__name__)

class ArchiveVectorIndexer:
    """Векторный индексатор для архива технической документации"""
    
    def __init__(self, qdrant_url: str = QDRANT_URL):
        self.qdrant_url = qdrant_url
        self.collection_name = QDRANT_COLLECTION_NAME
        self.client = None
        self._init_client()
    
    def _init_client(self):
        """Инициализация клиента Qdrant"""
        try:
            self.client = QdrantClient(url=self.qdrant_url)
            logger.info(f"✅ [VECTOR_INDEXER] Qdrant client initialized: {self.qdrant_url}")
        except Exception as e:
            logger.error(f"❌ [VECTOR_INDEXER] Error initializing Qdrant client: {e}")
            raise
    
    async def ensure_collection_exists(self):
        """Создание коллекции, если она не существует"""
        try:
            # Проверяем, существует ли коллекция
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.collection_name not in collection_names:
                # Создаем коллекцию
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=EMBEDDING_DIMENSION,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"✅ [VECTOR_INDEXER] Collection created: {self.collection_name}")
            else:
                logger.info(f"ℹ️ [VECTOR_INDEXER] Collection already exists: {self.collection_name}")
                
        except Exception as e:
            logger.error(f"❌ [VECTOR_INDEXER] Error ensuring collection exists: {e}")
            raise
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Генерация эмбеддинга для текста"""
        try:
            # Здесь должна быть интеграция с моделью эмбеддингов
            # Пока используем простую хеш-функцию для демонстрации
            import hashlib
            
            # Создаем хеш от текста
            text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
            
            # Преобразуем хеш в вектор фиксированной размерности
            # Это не настоящий эмбеддинг, но подходит для демонстрации
            vector = []
            for i in range(0, len(text_hash), 2):
                hex_pair = text_hash[i:i+2]
                value = int(hex_pair, 16) / 255.0  # Нормализуем к [0, 1]
                vector.append(value)
            
            # Дополняем до нужной размерности
            while len(vector) < EMBEDDING_DIMENSION:
                vector.append(0.0)
            
            # Обрезаем до нужной размерности
            vector = vector[:EMBEDDING_DIMENSION]
            
            logger.debug(f"🔍 [GENERATE_EMBEDDING] Generated embedding for text: {len(text)} chars")
            return vector
            
        except Exception as e:
            logger.error(f"❌ [GENERATE_EMBEDDING] Error generating embedding: {e}")
            return [0.0] * EMBEDDING_DIMENSION
    
    async def index_document_sections(self, document_id: int, sections: List[DocumentSection]) -> bool:
        """Индексация разделов документа в векторную базу"""
        try:
            await self.ensure_collection_exists()
            
            points = []
            
            for section in sections:
                # Генерируем эмбеддинг для содержимого раздела
                embedding = await self.generate_embedding(section.section_content)
                
                # Создаем точку для Qdrant
                point_id = f"{document_id}_{section.id}" if section.id else f"{document_id}_{hash(section.section_content)}"
                
                point = PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        'document_id': document_id,
                        'section_id': section.id,
                        'section_number': section.section_number,
                        'section_title': section.section_title,
                        'section_content': section.section_content,
                        'page_number': section.page_number,
                        'section_type': section.section_type,
                        'importance_level': section.importance_level,
                        'created_at': section.created_at.isoformat() if section.created_at else None
                    }
                )
                points.append(point)
            
            # Загружаем точки в Qdrant
            if points:
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=points
                )
                
                logger.info(f"✅ [INDEX_SECTIONS] Indexed {len(points)} sections for document {document_id}")
                return True
            else:
                logger.warning(f"⚠️ [INDEX_SECTIONS] No sections to index for document {document_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ [INDEX_SECTIONS] Error indexing sections: {e}")
            return False
    
    async def search_similar_sections(self, query: str, project_code: str = None, 
                                    limit: int = 10, score_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Поиск похожих разделов"""
        try:
            await self.ensure_collection_exists()
            
            # Генерируем эмбеддинг для запроса
            query_embedding = await self.generate_embedding(query)
            
            # Строим фильтр
            filter_conditions = {}
            if project_code:
                # Здесь нужно будет добавить фильтр по project_code
                # Пока что ищем по всем документам
                pass
            
            # Выполняем поиск
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                score_threshold=score_threshold,
                with_payload=True
            )
            
            # Форматируем результаты
            results = []
            for result in search_results:
                results.append({
                    'id': result.id,
                    'score': result.score,
                    'document_id': result.payload.get('document_id'),
                    'section_id': result.payload.get('section_id'),
                    'section_number': result.payload.get('section_number'),
                    'section_title': result.payload.get('section_title'),
                    'section_content': result.payload.get('section_content'),
                    'page_number': result.payload.get('page_number'),
                    'section_type': result.payload.get('section_type'),
                    'importance_level': result.payload.get('importance_level')
                })
            
            logger.info(f"🔍 [SEARCH_SECTIONS] Found {len(results)} similar sections for query")
            return results
            
        except Exception as e:
            logger.error(f"❌ [SEARCH_SECTIONS] Error searching sections: {e}")
            return []
    
    async def delete_document_sections(self, document_id: int) -> bool:
        """Удаление разделов документа из векторной базы"""
        try:
            # Удаляем все точки с document_id в payload
            self.client.delete(
                collection_name=self.collection_name,
                points_selector={
                    "filter": {
                        "must": [
                            {
                                "key": "document_id",
                                "match": {"value": document_id}
                            }
                        ]
                    }
                }
            )
            
            logger.info(f"✅ [DELETE_SECTIONS] Deleted sections for document {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ [DELETE_SECTIONS] Error deleting sections: {e}")
            return False
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """Получение статистики коллекции"""
        try:
            collection_info = self.client.get_collection(self.collection_name)
            
            stats = {
                'collection_name': self.collection_name,
                'vectors_count': collection_info.vectors_count,
                'indexed_vectors_count': collection_info.indexed_vectors_count,
                'points_count': collection_info.points_count,
                'segments_count': collection_info.segments_count,
                'status': collection_info.status,
                'optimizer_status': collection_info.optimizer_status,
                'payload_schema': collection_info.payload_schema
            }
            
            logger.info(f"📊 [COLLECTION_STATS] Retrieved stats for collection {self.collection_name}")
            return stats
            
        except Exception as e:
            logger.error(f"❌ [COLLECTION_STATS] Error getting collection stats: {e}")
            return {
                'collection_name': self.collection_name,
                'error': str(e)
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """Проверка здоровья векторного индексатора"""
        try:
            # Проверяем подключение к Qdrant
            collections = self.client.get_collections()
            
            # Проверяем существование коллекции
            collection_exists = self.collection_name in [col.name for col in collections.collections]
            
            return {
                'status': 'healthy' if collection_exists else 'unhealthy',
                'qdrant_connected': True,
                'collection_exists': collection_exists,
                'collection_name': self.collection_name,
                'total_collections': len(collections.collections)
            }
            
        except Exception as e:
            logger.error(f"❌ [VECTOR_INDEXER] Health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'qdrant_connected': False,
                'collection_exists': False
            }
