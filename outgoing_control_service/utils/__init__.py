"""
Модуль утилит для работы с документами
Содержит универсальные функции для извлечения текста из различных форматов документов
"""

from .document_parser import (
    UniversalDocumentParser,
    parse_document,
    parse_document_from_bytes
)

from .pdf_utils import (
    PDFTextExtractor,
    extract_text_from_pdf_file,
    extract_text_from_pdf_bytes
)

from .docx_utils import (
    DOCXTextExtractor,
    extract_text_from_docx_file,
    extract_text_from_docx_bytes
)

from .text_processing import (
    TextProcessor,
    TextChunk,
    clean_text,
    hierarchical_text_chunking
)

# Версия модуля
__version__ = "1.0.0"

# Основные экспортируемые классы и функции
__all__ = [
    # Основные классы
    "UniversalDocumentParser",
    "PDFTextExtractor", 
    "DOCXTextExtractor",
    "TextProcessor",
    "TextChunk",
    
    # Функции для парсинга документов
    "parse_document",
    "parse_document_from_bytes",
    
    # Функции для работы с PDF
    "extract_text_from_pdf_file",
    "extract_text_from_pdf_bytes",
    
    # Функции для работы с DOCX
    "extract_text_from_docx_file", 
    "extract_text_from_docx_bytes",
    
    # Функции для обработки текста
    "clean_text",
    "hierarchical_text_chunking"
]

# Информация о модуле
__author__ = "AI-NK Team"
__description__ = "Универсальный модуль для извлечения и обработки текста из документов"
__supported_formats__ = [".pdf", ".docx", ".doc", ".txt"]


def get_supported_formats() -> list:
    """
    Получение списка поддерживаемых форматов документов
    
    Returns:
        Список поддерживаемых расширений файлов
    """
    return __supported_formats__.copy()


def get_module_info() -> dict:
    """
    Получение информации о модуле
    
    Returns:
        Словарь с информацией о модуле
    """
    return {
        "name": "AI-NK Document Utils",
        "version": __version__,
        "author": __author__,
        "description": __description__,
        "supported_formats": __supported_formats__,
        "main_classes": [
            "UniversalDocumentParser",
            "PDFTextExtractor",
            "DOCXTextExtractor", 
            "TextProcessor"
        ]
    }
