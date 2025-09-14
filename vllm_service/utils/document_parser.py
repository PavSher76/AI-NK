"""
Универсальный модуль для парсинга документов
Объединяет функциональность извлечения текста из различных форматов документов
"""

import logging
import os
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

from .pdf_utils import PDFTextExtractor, extract_text_from_pdf_file, extract_text_from_pdf_bytes
from .docx_utils import DOCXTextExtractor, extract_text_from_docx_file, extract_text_from_docx_bytes
from .text_processing import TextProcessor, TextChunk, hierarchical_text_chunking, clean_text

logger = logging.getLogger(__name__)


class UniversalDocumentParser:
    """Универсальный парсер документов для различных форматов"""
    
    def __init__(self, 
                 prefer_pdfminer: bool = True,
                 extract_tables: bool = True,
                 extract_headers: bool = True,
                 create_hierarchical_chunks: bool = True):
        """
        Инициализация парсера
        
        Args:
            prefer_pdfminer: Предпочитать pdfminer для PDF (более точный)
            extract_tables: Извлекать таблицы из DOCX
            extract_headers: Извлекать заголовки отдельно
            create_hierarchical_chunks: Создавать иерархические чанки
        """
        self.pdf_extractor = PDFTextExtractor(prefer_pdfminer=prefer_pdfminer)
        self.docx_extractor = DOCXTextExtractor(
            extract_tables=extract_tables, 
            extract_headers=extract_headers
        )
        self.text_processor = TextProcessor()
        self.create_hierarchical_chunks = create_hierarchical_chunks
        
        # Поддерживаемые форматы
        self.supported_formats = {
            '.pdf': self._parse_pdf,
            '.docx': self._parse_docx,
            '.doc': self._parse_docx,  # DOCX экстрактор может работать с DOC
            '.txt': self._parse_txt
        }
    
    def parse_document(self, file_path: str) -> Dict[str, Any]:
        """
        Парсинг документа по пути к файлу
        
        Args:
            file_path: Путь к файлу документа
            
        Returns:
            Словарь с извлеченным текстом и метаданными
        """
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                raise FileNotFoundError(f"Файл не найден: {file_path}")
            
            # Определяем формат файла
            file_extension = file_path.suffix.lower()
            
            if file_extension not in self.supported_formats:
                raise ValueError(f"Неподдерживаемый формат файла: {file_extension}")
            
            # Парсим документ
            parse_func = self.supported_formats[file_extension]
            result = parse_func(str(file_path))
            
            # Добавляем общую информацию
            result.update({
                "file_path": str(file_path),
                "file_name": file_path.name,
                "file_extension": file_extension,
                "file_size": file_path.stat().st_size
            })
            
            # Создаем чанки если требуется
            if self.create_hierarchical_chunks and result.get("success", False):
                text = result.get("text", "")
                if text:
                    chunks = self.text_processor.hierarchical_chunking(text)
                    result["chunks"] = [
                        {
                            "chunk_id": chunk.chunk_id,
                            "text": chunk.content,
                            "hierarchy": chunk.hierarchy,
                            "metadata": chunk.metadata
                        }
                        for chunk in chunks
                    ]
            
            logger.info(f"📄 [DOCUMENT_PARSER] Документ {file_path.name} успешно обработан")
            return result
            
        except Exception as e:
            logger.error(f"❌ [DOCUMENT_PARSER] Ошибка парсинга документа {file_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "file_path": str(file_path) if 'file_path' in locals() else None,
                "file_name": Path(file_path).name if 'file_path' in locals() else None
            }
    
    def parse_document_from_bytes(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Парсинг документа из байтов
        
        Args:
            file_content: Содержимое файла в байтах
            filename: Имя файла (для определения формата)
            
        Returns:
            Словарь с извлеченным текстом и метаданными
        """
        try:
            # Определяем формат файла по расширению
            file_extension = Path(filename).suffix.lower()
            
            if file_extension not in self.supported_formats:
                raise ValueError(f"Неподдерживаемый формат файла: {file_extension}")
            
            # Парсим документ
            if file_extension == '.pdf':
                result = self.pdf_extractor.extract_text_from_bytes(file_content)
            elif file_extension in ['.docx', '.doc']:
                result = self.docx_extractor.extract_text_from_bytes(file_content)
            elif file_extension == '.txt':
                result = self._parse_txt_bytes(file_content)
            else:
                raise ValueError(f"Неподдерживаемый формат файла: {file_extension}")
            
            # Добавляем общую информацию
            result.update({
                "file_name": filename,
                "file_extension": file_extension,
                "file_size": len(file_content)
            })
            
            # Создаем чанки если требуется
            if self.create_hierarchical_chunks and result.get("success", False):
                text = result.get("text", "")
                if text:
                    chunks = self.text_processor.hierarchical_chunking(text)
                    result["chunks"] = [
                        {
                            "chunk_id": chunk.chunk_id,
                            "text": chunk.content,
                            "hierarchy": chunk.hierarchy,
                            "metadata": chunk.metadata
                        }
                        for chunk in chunks
                    ]
            
            logger.info(f"📄 [DOCUMENT_PARSER] Документ {filename} успешно обработан из байтов")
            return result
            
        except Exception as e:
            logger.error(f"❌ [DOCUMENT_PARSER] Ошибка парсинга документа {filename} из байтов: {e}")
            return {
                "success": False,
                "error": str(e),
                "file_name": filename
            }
    
    def _parse_pdf(self, file_path: str) -> Dict[str, Any]:
        """Парсинг PDF файла"""
        try:
            result = self.pdf_extractor.extract_text_from_file(file_path)
            
            # Очищаем извлеченный текст
            if result.get("success", False) and result.get("text"):
                cleaned_text = self.text_processor.clean_text(result["text"])
                result["text"] = cleaned_text
                
                # Обновляем страницы с очищенным текстом
                if "pages" in result:
                    for page in result["pages"]:
                        if "text" in page:
                            page["text"] = self.text_processor.clean_text(page["text"])
            
            return result
            
        except Exception as e:
            logger.error(f"❌ [PDF_PARSE] Ошибка парсинга PDF {file_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "method": "pdf"
            }
    
    def _parse_docx(self, file_path: str) -> Dict[str, Any]:
        """Парсинг DOCX файла"""
        try:
            result = self.docx_extractor.extract_text_from_file(file_path)
            
            # Очищаем извлеченный текст
            if result.get("success", False) and result.get("text"):
                cleaned_text = self.text_processor.clean_text(result["text"])
                result["text"] = cleaned_text
                
                # Обновляем параграфы с очищенным текстом
                if "paragraphs" in result:
                    for para in result["paragraphs"]:
                        if "text" in para:
                            para["text"] = self.text_processor.clean_text(para["text"])
            
            return result
            
        except Exception as e:
            logger.error(f"❌ [DOCX_PARSE] Ошибка парсинга DOCX {file_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "method": "docx"
            }
    
    def _parse_txt(self, file_path: str) -> Dict[str, Any]:
        """Парсинг TXT файла"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
            
            # Очищаем текст
            cleaned_text = self.text_processor.clean_text(text)
            
            # Создаем структуру как у других форматов
            result = {
                "success": True,
                "text": cleaned_text,
                "pages": [{
                    "page_number": 1,
                    "text": cleaned_text,
                    "char_count": len(cleaned_text),
                    "word_count": len(cleaned_text.split())
                }],
                "method": "txt",
                "metadata": {
                    "total_chars": len(cleaned_text),
                    "total_words": len(cleaned_text.split()),
                    "language": self.text_processor.detect_language(cleaned_text)
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"❌ [TXT_PARSE] Ошибка парсинга TXT {file_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "method": "txt"
            }
    
    def _parse_txt_bytes(self, file_content: bytes) -> Dict[str, Any]:
        """Парсинг TXT файла из байтов"""
        try:
            text = file_content.decode('utf-8')
            
            # Очищаем текст
            cleaned_text = self.text_processor.clean_text(text)
            
            # Создаем структуру как у других форматов
            result = {
                "success": True,
                "text": cleaned_text,
                "pages": [{
                    "page_number": 1,
                    "text": cleaned_text,
                    "char_count": len(cleaned_text),
                    "word_count": len(cleaned_text.split())
                }],
                "method": "txt",
                "metadata": {
                    "total_chars": len(cleaned_text),
                    "total_words": len(cleaned_text.split()),
                    "language": self.text_processor.detect_language(cleaned_text)
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"❌ [TXT_PARSE_BYTES] Ошибка парсинга TXT из байтов: {e}")
            return {
                "success": False,
                "error": str(e),
                "method": "txt"
            }
    
    def get_supported_formats(self) -> List[str]:
        """
        Получение списка поддерживаемых форматов
        
        Returns:
            Список поддерживаемых расширений файлов
        """
        return list(self.supported_formats.keys())
    
    def get_text_statistics(self, text: str) -> Dict[str, Any]:
        """
        Получение статистики по тексту
        
        Args:
            text: Исходный текст
            
        Returns:
            Словарь со статистикой
        """
        return self.text_processor.get_text_statistics(text)


# Функции для обратной совместимости
def parse_document(file_path: str, 
                  prefer_pdfminer: bool = True,
                  extract_tables: bool = True,
                  extract_headers: bool = True,
                  create_hierarchical_chunks: bool = True) -> Dict[str, Any]:
    """
    Парсинг документа (функция для обратной совместимости)
    
    Args:
        file_path: Путь к файлу документа
        prefer_pdfminer: Предпочитать pdfminer для PDF
        extract_tables: Извлекать таблицы из DOCX
        extract_headers: Извлекать заголовки отдельно
        create_hierarchical_chunks: Создавать иерархические чанки
        
    Returns:
        Словарь с извлеченным текстом и метаданными
    """
    parser = UniversalDocumentParser(
        prefer_pdfminer=prefer_pdfminer,
        extract_tables=extract_tables,
        extract_headers=extract_headers,
        create_hierarchical_chunks=create_hierarchical_chunks
    )
    return parser.parse_document(file_path)


def parse_document_from_bytes(file_content: bytes, 
                            filename: str,
                            prefer_pdfminer: bool = True,
                            extract_tables: bool = True,
                            extract_headers: bool = True,
                            create_hierarchical_chunks: bool = True) -> Dict[str, Any]:
    """
    Парсинг документа из байтов (функция для обратной совместимости)
    
    Args:
        file_content: Содержимое файла в байтах
        filename: Имя файла
        prefer_pdfminer: Предпочитать pdfminer для PDF
        extract_tables: Извлекать таблицы из DOCX
        extract_headers: Извлекать заголовки отдельно
        create_hierarchical_chunks: Создавать иерархические чанки
        
    Returns:
        Словарь с извлеченным текстом и метаданными
    """
    parser = UniversalDocumentParser(
        prefer_pdfminer=prefer_pdfminer,
        extract_tables=extract_tables,
        extract_headers=extract_headers,
        create_hierarchical_chunks=create_hierarchical_chunks
    )
    return parser.parse_document_from_bytes(file_content, filename)
