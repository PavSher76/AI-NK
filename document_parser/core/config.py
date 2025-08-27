import os
from typing import Dict, Any

# Конфигурация базы данных
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "norms-db")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "norms_db")
POSTGRES_USER = os.getenv("POSTGRES_USER", "norms_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "norms_password")

# Конфигурация Qdrant
QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))

# Конфигурация Redis
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

# Конфигурация сервисов
RULE_ENGINE_URL = os.getenv("RULE_ENGINE_URL", "http://rule-engine:8003")
RAG_SERVICE_URL = os.getenv("RAG_SERVICE_URL", "http://rag-service:8004")

# Конфигурация приложения
UPLOAD_DIR = "/app/uploads"
TEMP_DIR = "/app/temp"
REPORT_FORMAT_DIR = "/app/report_format"

# Лимиты и таймауты
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
MAX_RETRIES = 3
RETRY_DELAY = 5  # секунды
CONNECTION_TIMEOUT = 10
REQUEST_TIMEOUT = 30

# Настройки OCR
OCR_LANGUAGES = ["rus", "eng"]
OCR_CONFIG = "--oem 3 --psm 6"

# Настройки логирования
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Настройки модели
MODEL_CACHE_DIR = "/app/models"
TRANSFORMERS_CACHE = MODEL_CACHE_DIR
HF_HOME = MODEL_CACHE_DIR

# Настройки памяти
MEMORY_PRESSURE_THRESHOLD = 80  # процент использования памяти
MIN_AVAILABLE_MEMORY = 500  # МБ

# Настройки асинхронной обработки
ASYNC_CHECK_POLLING_INTERVAL = 3  # секунды
ASYNC_CHECK_TIMEOUT = 600  # секунды (10 минут)

def get_database_config() -> Dict[str, Any]:
    """Получение конфигурации базы данных"""
    return {
        "host": POSTGRES_HOST,
        "port": POSTGRES_PORT,
        "database": POSTGRES_DB,
        "user": POSTGRES_USER,
        "password": POSTGRES_PASSWORD,
        "connect_timeout": CONNECTION_TIMEOUT,
        "application_name": "document_parser"
    }

def get_qdrant_config() -> Dict[str, Any]:
    """Получение конфигурации Qdrant"""
    return {
        "host": QDRANT_HOST,
        "port": QDRANT_PORT,
        "timeout": CONNECTION_TIMEOUT
    }

def get_redis_config() -> Dict[str, Any]:
    """Получение конфигурации Redis"""
    return {
        "host": REDIS_HOST,
        "port": REDIS_PORT,
        "decode_responses": True
    }
