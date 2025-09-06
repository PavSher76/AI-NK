"""
Сервис для работы с векторной базой Qdrant
"""

import logging
import qdrant_client
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchAny
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class QdrantService:
    """Сервис для работы с векторной базой Qdrant"""
    
    def __init__(self, qdrant_url: str, collection_name: str = "normative_documents", vector_size: int = 1024):
        self.qdrant_url = qdrant_url
        self.collection_name = collection_name
        self.vector_size = vector_size
        
        # Инициализация клиента
        self.client = qdrant_client.QdrantClient(qdrant_url)
        logger.info(f"🔍 [QDRANT] Initialized with {qdrant_url}, collection: {collection_name}")
        
        # Создаем коллекцию, если она не существует
        self._ensure_collection_exists()
    
    def _ensure_collection_exists(self):
        """Создание коллекции Qdrant, если она не существует"""
        try:
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.collection_name not in collection_names:
                logger.info(f"📝 [QDRANT] Creating collection '{self.collection_name}'...")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"✅ [QDRANT] Collection '{self.collection_name}' created successfully")
            else:
                logger.info(f"✅ [QDRANT] Collection '{self.collection_name}' already exists")
                
        except Exception as e:
            logger.error(f"❌ [QDRANT] Error ensuring collection exists: {e}")
            raise e
    
    def upsert_point(self, point_id: int, vector: List[float], payload: Dict[str, Any]) -> bool:
        """Добавление/обновление точки в коллекцию"""
        try:
            point = PointStruct(
                id=point_id,
                vector=vector,
                payload=payload
            )
            
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            
            logger.info(f"✅ [QDRANT] Successfully upserted point {point_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ [QDRANT] Error upserting point {point_id}: {e}")
            return False
    
    def upsert_points_batch(self, points: List[PointStruct]) -> bool:
        """Пакетное добавление/обновление точек"""
        try:
            if not points:
                logger.warning("⚠️ [QDRANT] No points to upsert")
                return False
            
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            logger.info(f"✅ [QDRANT] Successfully upserted {len(points)} points")
            return True
            
        except Exception as e:
            logger.error(f"❌ [QDRANT] Error upserting points batch: {e}")
            return False
    
    def search_similar(self, query_vector: List[float], limit: int = 8, 
                      filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Поиск похожих векторов"""
        try:
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=filters,
                limit=limit,
                with_payload=True,
                with_vectors=False
            )
            
            results = []
            for point in search_result:
                result = {
                    'id': point.id,
                    'score': point.score,
                    'payload': point.payload
                }
                results.append(result)
            
            logger.info(f"✅ [QDRANT] Found {len(results)} similar vectors")
            return results
            
        except Exception as e:
            logger.error(f"❌ [QDRANT] Error searching similar vectors: {e}")
            return []
    
    def delete_points_by_document(self, document_id: int) -> bool:
        """Удаление всех точек документа по document_id"""
        try:
            logger.info(f"🗑️ [QDRANT] Deleting points for document {document_id}")
            
            # Создаем фильтр для удаления точек по document_id
            points_selector = Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchAny(any=[document_id])
                    )
                ]
            )
            
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=points_selector
            )
            
            logger.info(f"✅ [QDRANT] Successfully deleted points for document {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ [QDRANT] Error deleting points for document {document_id}: {e}")
            return False
    
    def clear_collection(self) -> bool:
        """Очистка всей коллекции"""
        try:
            logger.info("🧹 [QDRANT] Clearing entire collection...")
            
            # Удаляем все точки
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="document_id",
                            match=MatchAny(any=list(range(1, 100000000)))
                        )
                    ]
                )
            )
            
            logger.info("✅ [QDRANT] Collection cleared successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ [QDRANT] Error clearing collection: {e}")
            return False
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Получение информации о коллекции"""
        # Используем HTTP API напрямую для избежания Pydantic ошибок
        try:
            import requests
            response = requests.get(f"{self.qdrant_url}/collections/{self.collection_name}")
            if response.status_code == 200:
                data = response.json()
                result = data.get('result', {})
                return {
                    "name": self.collection_name,
                    "vector_size": result.get('config', {}).get('params', {}).get('vectors', {}).get('size', 1024),
                    "distance": result.get('config', {}).get('params', {}).get('vectors', {}).get('distance', 'Cosine'),
                    "points_count": result.get('points_count', 0),
                    "indexed_vectors_count": result.get('indexed_vectors_count', 0),
                    "vectors_count": result.get('indexed_vectors_count', result.get('points_count', 0))
                }
            else:
                logger.error(f"❌ [QDRANT] HTTP API error: {response.status_code}")
                return {}
        except Exception as e:
            logger.error(f"❌ [QDRANT] Error getting collection info via HTTP API: {e}")
            # Fallback: попробуем через клиент (может работать частично)
            try:
                info = self.client.get_collection(self.collection_name)
                return {
                    "name": getattr(info, 'name', self.collection_name),
                    "vector_size": getattr(info.config.params.vectors, 'size', 1024),
                    "distance": getattr(info.config.params.vectors, 'distance', 'Cosine'),
                    "points_count": getattr(info, 'points_count', 0),
                    "indexed_vectors_count": getattr(info, 'indexed_vectors_count', getattr(info, 'points_count', 0)),
                    "vectors_count": getattr(info, 'indexed_vectors_count', getattr(info, 'points_count', 0))
                }
            except Exception as fallback_error:
                logger.error(f"❌ [QDRANT] Fallback client error: {fallback_error}")
            return {}
    
    def get_points_count(self) -> int:
        """Получение количества точек в коллекции"""
        try:
            # Используем HTTP API для избежания Pydantic ошибок
            import requests
            response = requests.get(f"{self.qdrant_url}/collections/{self.collection_name}")
            if response.status_code == 200:
                data = response.json()
                result = data.get('result', {})
                return result.get('points_count', 0)
            else:
                logger.error(f"❌ [QDRANT] HTTP API error: {response.status_code}")
                return 0
        except Exception as e:
            logger.error(f"❌ [QDRANT] Error getting points count: {e}")
            # Fallback через клиент
            try:
                info = self.client.get_collection(self.collection_name)
                return getattr(info, 'points_count', 0)
            except Exception as fallback_error:
                logger.error(f"❌ [QDRANT] Fallback client error: {fallback_error}")
                return 0
    
    def health_check(self) -> bool:
        """Проверка здоровья Qdrant"""
        try:
            # Используем HTTP API для проверки здоровья
            import requests
            response = requests.get(f"{self.qdrant_url}/collections")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"❌ [QDRANT] Health check failed: {e}")
            # Fallback через клиент
            try:
                collections = self.client.get_collections()
                return True
            except Exception as fallback_error:
                logger.error(f"❌ [QDRANT] Fallback health check failed: {fallback_error}")
                return False
    
    def create_point(self, point_id: int, vector: List[float], payload: Dict[str, Any]) -> PointStruct:
        """Создание точки для Qdrant"""
        return PointStruct(
            id=point_id,
            vector=vector,
            payload=payload
        )
    
    def get_points_by_document(self, document_id: int) -> List[Dict[str, Any]]:
        """Получение всех точек документа"""
        try:
            search_result = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="document_id",
                            match=MatchAny(any=[document_id])
                        )
                    ]
                ),
                limit=1000,
                with_payload=True,
                with_vectors=False
            )
            
            points = []
            for point in search_result[0]:  # scroll возвращает кортеж (points, next_page_offset)
                point_info = {
                    'id': point.id,
                    'payload': point.payload
                }
                points.append(point_info)
            
            logger.info(f"✅ [QDRANT] Found {len(points)} points for document {document_id}")
            return points
            
        except Exception as e:
            logger.error(f"❌ [QDRANT] Error getting points for document {document_id}: {e}")
            return []
