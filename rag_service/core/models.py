from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, List, Optional

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

@dataclass
class DocumentInfo:
    """Информация о документе"""
    id: int
    title: str
    file_type: str
    file_size: int
    upload_date: str
    processing_status: str
    category: str
    document_type: str
    token_count: int
    chunks_count: int
    status: str

@dataclass
class SearchResult:
    """Результат поиска"""
    content: str
    document_title: str
    page_number: int
    score: float
    metadata: Dict[str, Any]
