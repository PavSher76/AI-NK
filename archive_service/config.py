"""
Конфигурация для сервиса архива технической документации
"""

import os
from typing import Dict, Any

# Настройки базы данных
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/ai_nk_db")

# Настройки файлового хранилища
UPLOAD_DIR = os.getenv("ARCHIVE_UPLOAD_DIR", "/app/uploads/archive")
MAX_FILE_SIZE = int(os.getenv("ARCHIVE_MAX_FILE_SIZE", 100 * 1024 * 1024))  # 100 MB
ALLOWED_FILE_TYPES = ['.pdf', '.docx', '.xlsx', '.dwg', '.ifc', '.txt']

# Настройки обработки документов
CHUNK_SIZE = int(os.getenv("ARCHIVE_CHUNK_SIZE", 1000))
CHUNK_OVERLAP = int(os.getenv("ARCHIVE_CHUNK_OVERLAP", 200))
MAX_TOKENS = int(os.getenv("ARCHIVE_MAX_TOKENS", 10000))

# Настройки векторной базы данных
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_COLLECTION_NAME = "archive_documents"

# Настройки эмбеддингов
EMBEDDING_MODEL = os.getenv("ARCHIVE_EMBEDDING_MODEL", "BGE-M3")
EMBEDDING_DIMENSION = int(os.getenv("ARCHIVE_EMBEDDING_DIMENSION", 1536))

# Настройки логирования
LOG_LEVEL = os.getenv("ARCHIVE_LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Настройки пакетной обработки
BATCH_SIZE = int(os.getenv("ARCHIVE_BATCH_SIZE", 10))
MAX_CONCURRENT_UPLOADS = int(os.getenv("ARCHIVE_MAX_CONCURRENT_UPLOADS", 5))

# Типы технических документов
DOCUMENT_TYPES = {
    "PD": "Проектная документация",
    "RD": "Рабочая документация", 
    "TEO": "Технико-экономическое обоснование",
    "DRAWING": "Чертеж",
    "SPECIFICATION": "Спецификация",
    "CALCULATION": "Расчет",
    "REPORT": "Отчет",
    "OTHER": "Прочее"
}

# Уровни важности разделов
IMPORTANCE_LEVELS = {
    1: "Низкая",
    2: "Средняя", 
    3: "Высокая",
    4: "Критическая",
    5: "Критически важная"
}

# Типы связей между документами
RELATION_TYPES = {
    "REFERENCES": "Ссылается на",
    "DEPENDS_ON": "Зависит от",
    "SUPERSEDES": "Заменяет",
    "RELATED_TO": "Связан с",
    "CONTAINS": "Содержит",
    "PART_OF": "Является частью"
}

# Настройки извлечения ШИФР проекта
PROJECT_CODE_PATTERNS = [
    r'[А-Я]{2,4}-\d{2,4}-\d{2,4}',  # Пример: ПР-2024-001
    r'[А-Я]{2,4}\.\d{2,4}\.\d{2,4}',  # Пример: ПР.2024.001
    r'[А-Я]{2,4}_\d{2,4}_\d{2,4}',  # Пример: ПР_2024_001
    r'\d{2,4}-[А-Я]{2,4}-\d{2,4}',  # Пример: 2024-ПР-001
    r'[А-Я]{2,4}\d{2,4}',  # Пример: ПР2024001
]

# Настройки валидации
VALIDATION_RULES = {
    "project_code_required": True,
    "document_type_required": True,
    "document_name_required": True,
    "min_file_size": 1024,  # 1 KB
    "max_file_size": MAX_FILE_SIZE,
    "allowed_extensions": ALLOWED_FILE_TYPES
}

def get_config() -> Dict[str, Any]:
    """Получение конфигурации сервиса"""
    return {
        "database_url": DATABASE_URL,
        "upload_dir": UPLOAD_DIR,
        "max_file_size": MAX_FILE_SIZE,
        "allowed_file_types": ALLOWED_FILE_TYPES,
        "chunk_size": CHUNK_SIZE,
        "chunk_overlap": CHUNK_OVERLAP,
        "max_tokens": MAX_TOKENS,
        "qdrant_url": QDRANT_URL,
        "qdrant_collection": QDRANT_COLLECTION_NAME,
        "embedding_model": EMBEDDING_MODEL,
        "embedding_dimension": EMBEDDING_DIMENSION,
        "batch_size": BATCH_SIZE,
        "max_concurrent_uploads": MAX_CONCURRENT_UPLOADS,
        "document_types": DOCUMENT_TYPES,
        "importance_levels": IMPORTANCE_LEVELS,
        "relation_types": RELATION_TYPES,
        "project_code_patterns": PROJECT_CODE_PATTERNS,
        "validation_rules": VALIDATION_RULES
    }
