import os
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Конфигурация сервисов
QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
POSTGRES_URL = os.getenv("POSTGRES_URL", "postgresql://norms_user:norms_password@norms-db:5432/norms_db")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://vllm:8000")  # Изменено на VLLM Adapter
VECTOR_COLLECTION = "normative_documents"
CHECKABLE_COLLECTION = "checkable_documents"
BM25_COLLECTION = "normative_bm25"

# Константы для чанкинга
CHUNK_SIZE = 500  # ~400-600 токенов
CHUNK_OVERLAP = 75  # ~50-100 токенов
MAX_TOKENS = 1000

# Названия коллекций
VECTOR_COLLECTION = "normative_documents"
CHECKABLE_COLLECTION = "checkable_documents"
BM25_COLLECTION = "normative_bm25"

logger.info(f"🔧 [CONFIG] RAG Service Configuration:")
logger.info(f"🔧 [CONFIG] POSTGRES_URL: {POSTGRES_URL}")
logger.info(f"🔧 [CONFIG] QDRANT_URL: {QDRANT_URL}")
logger.info(f"🔧 [CONFIG] OLLAMA_URL: {OLLAMA_URL}")
logger.info(f"🔧 [CONFIG] CHUNK_SIZE: {CHUNK_SIZE}")
logger.info(f"🔧 [CONFIG] CHUNK_OVERLAP: {CHUNK_OVERLAP}")
logger.info(f"🔧 [CONFIG] VECTOR_COLLECTION: {VECTOR_COLLECTION}")
