"""
Модели данных для сервиса архива технической документации
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class DocumentType(str, Enum):
    """Типы технических документов"""
    PD = "PD"  # Проектная документация
    RD = "RD"  # Рабочая документация
    TEO = "TEO"  # Технико-экономическое обоснование
    DRAWING = "DRAWING"  # Чертеж
    SPECIFICATION = "SPECIFICATION"  # Спецификация
    CALCULATION = "CALCULATION"  # Расчет
    REPORT = "REPORT"  # Отчет
    OTHER = "OTHER"  # Прочее

class ProcessingStatus(str, Enum):
    """Статусы обработки документов"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class ProjectStatus(str, Enum):
    """Статусы проектов"""
    ACTIVE = "active"
    COMPLETED = "completed"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"

class RelationType(str, Enum):
    """Типы связей между документами"""
    REFERENCES = "references"
    DEPENDS_ON = "depends_on"
    SUPERSEDES = "supersedes"
    RELATED_TO = "related_to"
    CONTAINS = "contains"
    PART_OF = "part_of"

@dataclass
class ArchiveDocument:
    """Модель документа в архиве"""
    id: Optional[int] = None
    project_code: str = ""
    document_type: DocumentType = DocumentType.OTHER
    document_number: Optional[str] = None
    document_name: str = ""
    original_filename: str = ""
    file_type: str = ""
    file_size: int = 0
    file_path: Optional[str] = None
    document_hash: Optional[str] = None
    upload_date: Optional[datetime] = None
    processing_status: ProcessingStatus = ProcessingStatus.PENDING
    processing_error: Optional[str] = None
    token_count: int = 0
    version: str = "1.0"
    revision_date: Optional[datetime] = None
    author: Optional[str] = None
    department: Optional[str] = None
    status: str = "active"
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class DocumentSection:
    """Модель раздела документа"""
    id: Optional[int] = None
    archive_document_id: int = 0
    section_number: Optional[str] = None
    section_title: Optional[str] = None
    section_content: str = ""
    page_number: Optional[int] = None
    section_type: str = "text"
    importance_level: int = 1
    embedding: Optional[List[float]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class DocumentRelation:
    """Модель связи между документами"""
    id: Optional[int] = None
    source_document_id: int = 0
    target_document_id: int = 0
    relation_type: RelationType = RelationType.RELATED_TO
    relation_description: Optional[str] = None
    created_at: Optional[datetime] = None

@dataclass
class ArchiveProject:
    """Модель проекта в архиве"""
    id: Optional[int] = None
    project_code: str = ""
    project_name: str = ""
    project_description: Optional[str] = None
    project_manager: Optional[str] = None
    department: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: ProjectStatus = ProjectStatus.ACTIVE
    total_documents: int = 0
    total_sections: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class BatchUploadRequest:
    """Модель запроса пакетной загрузки"""
    project_code: str
    documents: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    auto_extract_sections: bool = True
    create_relations: bool = True
    processing_options: Dict[str, Any] = field(default_factory=dict)

@dataclass
class BatchUploadResponse:
    """Модель ответа пакетной загрузки"""
    status: str
    message: str
    project_code: str
    total_documents: int
    processed_documents: int
    failed_documents: int
    document_ids: List[int] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    processing_time: Optional[float] = None

@dataclass
class DocumentSearchRequest:
    """Модель запроса поиска документов"""
    project_code: Optional[str] = None
    document_type: Optional[DocumentType] = None
    search_query: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    author: Optional[str] = None
    department: Optional[str] = None
    status: Optional[str] = None
    limit: int = 100
    offset: int = 0

@dataclass
class DocumentSearchResponse:
    """Модель ответа поиска документов"""
    documents: List[ArchiveDocument] = field(default_factory=list)
    total_count: int = 0
    page: int = 0
    page_size: int = 100
    has_more: bool = False

@dataclass
class ProjectStats:
    """Модель статистики проекта"""
    project_code: str
    project_name: str
    total_documents: int
    documents_by_type: Dict[str, int] = field(default_factory=dict)
    total_sections: int
    total_size: int = 0
    last_upload: Optional[datetime] = None
    processing_status: Dict[str, int] = field(default_factory=dict)
