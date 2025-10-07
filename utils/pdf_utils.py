"""
Модуль для извлечения текста из PDF документов
Содержит улучшенные функции извлечения текста с использованием pdfminer, PyPDF2 и OCR
"""

import logging
import io
from typing import Dict, Any, List, Optional
from pathlib import Path

# Импорты для работы с PDF
try:
    import PyPDF2
    PDF2_AVAILABLE = True
except ImportError:
    PDF2_AVAILABLE = False

try:
    from pdfminer.high_level import extract_text, extract_pages
    from pdfminer.layout import LAParams, LTTextContainer
    from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
    from pdfminer.converter import TextConverter
    from pdfminer.pdfpage import PDFPage
    PDFMINER_AVAILABLE = True
except ImportError:
    PDFMINER_AVAILABLE = False

# Импорт OCR процессора
try:
    from .ocr_processor import OCRProcessor
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

logger = logging.getLogger(__name__)


class PDFTextExtractor:
    """Класс для извлечения текста из PDF документов с поддержкой OCR"""
    
    def __init__(self, prefer_pdfminer: bool = True, use_ocr: bool = True, ocr_languages: List[str] = None):
        """
        Инициализация экстрактора
        
        Args:
            prefer_pdfminer: Предпочитать pdfminer для извлечения текста (более точный)
            use_ocr: Использовать OCR для распознавания таблиц и чертежей
            ocr_languages: Языки для OCR (по умолчанию: rus+eng)
        """
        self.prefer_pdfminer = prefer_pdfminer
        self.use_ocr = use_ocr and OCR_AVAILABLE
        self.ocr_languages = ocr_languages or ["rus", "eng"]
        
        if not PDF2_AVAILABLE and not PDFMINER_AVAILABLE:
            raise ImportError("Необходимо установить PyPDF2 или pdfminer.six для работы с PDF")
        
        # Инициализируем OCR процессор если доступен
        if self.use_ocr:
            try:
                self.ocr_processor = OCRProcessor(languages=self.ocr_languages)
                logger.info("✅ [PDF_EXTRACT] OCR процессор инициализирован")
            except Exception as e:
                logger.warning(f"⚠️ [PDF_EXTRACT] Не удалось инициализировать OCR: {e}")
                self.use_ocr = False
    
    def extract_text_from_file(self, file_path: str) -> Dict[str, Any]:
        """
        Извлечение текста из PDF файла
        
        Args:
            file_path: Путь к PDF файлу
            
        Returns:
            Словарь с извлеченным текстом и метаданными
        """
        try:
            if self.prefer_pdfminer and PDFMINER_AVAILABLE:
                return self._extract_with_pdfminer(file_path)
            elif PDF2_AVAILABLE:
                return self._extract_with_pypdf2(file_path)
            else:
                raise Exception("Нет доступных библиотек для извлечения текста из PDF")
                
        except Exception as e:
            logger.error(f"❌ [PDF_EXTRACT] Ошибка извлечения текста из {file_path}: {e}")
            # Пробуем альтернативный метод
            if self.prefer_pdfminer and PDF2_AVAILABLE:
                logger.info("🔄 [PDF_EXTRACT] Пробуем PyPDF2 как fallback")
                return self._extract_with_pypdf2(file_path)
            elif PDFMINER_AVAILABLE:
                logger.info("🔄 [PDF_EXTRACT] Пробуем pdfminer как fallback")
                return self._extract_with_pdfminer(file_path)
            else:
                raise Exception(f"Не удалось извлечь текст из PDF: {e}")
    
    def extract_text_from_bytes(self, file_content: bytes) -> Dict[str, Any]:
        """
        Извлечение текста из PDF в виде байтов
        
        Args:
            file_content: Содержимое PDF файла в байтах
            
        Returns:
            Словарь с извлеченным текстом и метаданными
        """
        try:
            if self.prefer_pdfminer and PDFMINER_AVAILABLE:
                return self._extract_with_pdfminer_bytes(file_content)
            elif PDF2_AVAILABLE:
                return self._extract_with_pypdf2_bytes(file_content)
            else:
                raise Exception("Нет доступных библиотек для извлечения текста из PDF")
                
        except Exception as e:
            logger.error(f"❌ [PDF_EXTRACT] Ошибка извлечения текста из байтов: {e}")
            # Пробуем альтернативный метод
            if self.prefer_pdfminer and PDF2_AVAILABLE:
                logger.info("🔄 [PDF_EXTRACT] Пробуем PyPDF2 как fallback")
                return self._extract_with_pypdf2_bytes(file_content)
            elif PDFMINER_AVAILABLE:
                logger.info("🔄 [PDF_EXTRACT] Пробуем pdfminer как fallback")
                return self._extract_with_pdfminer_bytes(file_content)
            else:
                raise Exception(f"Не удалось извлечь текст из PDF: {e}")
    
    def _extract_with_pdfminer(self, file_path: str) -> Dict[str, Any]:
        """Извлечение текста с помощью pdfminer (более точный)"""
        try:
            pages = []
            full_text = ""
            
            # Настройки для лучшего извлечения текста
            laparams = LAParams(
                word_margin=0.1,
                char_margin=2.0,
                line_margin=0.5,
                boxes_flow=0.5,
                all_texts=True
            )
            
            # Извлекаем текст по страницам
            for page_num, page_layout in enumerate(extract_pages(file_path, laparams=laparams), 1):
                page_text = ""
                
                # Извлекаем текст из элементов страницы
                for element in page_layout:
                    if isinstance(element, LTTextContainer):
                        page_text += element.get_text()
                
                # Очищаем текст страницы
                cleaned_page_text = page_text
                
                pages.append({
                    "page_number": page_num,
                    "text": cleaned_page_text,
                    "raw_text": page_text,
                    "char_count": len(cleaned_page_text),
                    "word_count": len(cleaned_page_text.split())
                })
                full_text += cleaned_page_text + "\n"
            
            logger.info(f"📄 [PDFMINER] Извлечено {len(pages)} страниц из PDF")
            return {
                "success": True,
                "text": full_text.strip(),
                "pages": pages,
                "total_pages": len(pages),
                "method": "pdfminer",
                "metadata": {
                    "total_chars": len(full_text),
                    "total_words": len(full_text.split()),
                    "avg_chars_per_page": len(full_text) // len(pages) if pages else 0
                }
            }
            
        except Exception as e:
            logger.error(f"❌ [PDFMINER] Ошибка извлечения текста: {str(e)}")
            raise Exception(f"Ошибка извлечения текста с pdfminer: {str(e)}")
    
    def _extract_with_pdfminer_bytes(self, file_content: bytes) -> Dict[str, Any]:
        """Извлечение текста с помощью pdfminer из байтов"""
        try:
            # Создаем временный файл
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name
            
            try:
                result = self._extract_with_pdfminer(temp_file_path)
                return result
            finally:
                # Удаляем временный файл
                Path(temp_file_path).unlink(missing_ok=True)
                
        except Exception as e:
            logger.error(f"❌ [PDFMINER_BYTES] Ошибка извлечения текста из байтов: {str(e)}")
            raise Exception(f"Ошибка извлечения текста с pdfminer из байтов: {str(e)}")
    
    def _extract_with_pypdf2(self, file_path: str) -> Dict[str, Any]:
        """Извлечение текста с помощью PyPDF2"""
        try:
            pages = []
            full_text = ""
            
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                total_pages = len(pdf_reader.pages)
                
                for page_num in range(total_pages):
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    
                    # Очищаем текст страницы
                    cleaned_page_text = page_text
                    
                    pages.append({
                        "page_number": page_num + 1,
                        "text": cleaned_page_text,
                        "raw_text": page_text,
                        "char_count": len(cleaned_page_text),
                        "word_count": len(cleaned_page_text.split())
                    })
                    full_text += cleaned_page_text + "\n"
            
            logger.info(f"📄 [PYPDF2] Извлечено {len(pages)} страниц из PDF")
            return {
                "success": True,
                "text": full_text.strip(),
                "pages": pages,
                "total_pages": len(pages),
                "method": "pypdf2",
                "metadata": {
                    "total_chars": len(full_text),
                    "total_words": len(full_text.split()),
                    "avg_chars_per_page": len(full_text) // len(pages) if pages else 0
                }
            }
            
        except Exception as e:
            logger.error(f"❌ [PYPDF2] Ошибка извлечения текста: {str(e)}")
            raise Exception(f"Ошибка извлечения текста с PyPDF2: {str(e)}")
    
    def _extract_with_pypdf2_bytes(self, file_content: bytes) -> Dict[str, Any]:
        """Извлечение текста с помощью PyPDF2 из байтов"""
        try:
            pages = []
            full_text = ""
            
            pdf_file = io.BytesIO(file_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            total_pages = len(pdf_reader.pages)
            
            for page_num in range(total_pages):
                page = pdf_reader.pages[page_num]
                page_text = page.extract_text()
                
                # Очищаем текст страницы
                cleaned_page_text = page_text
                
                pages.append({
                    "page_number": page_num + 1,
                    "text": cleaned_page_text,
                    "raw_text": page_text,
                    "char_count": len(cleaned_page_text),
                    "word_count": len(cleaned_page_text.split())
                })
                full_text += cleaned_page_text + "\n"
            
            logger.info(f"📄 [PYPDF2_BYTES] Извлечено {len(pages)} страниц из PDF")
            return {
                "success": True,
                "text": full_text.strip(),
                "pages": pages,
                "total_pages": len(pages),
                "method": "pypdf2",
                "metadata": {
                    "total_chars": len(full_text),
                    "total_words": len(full_text.split()),
                    "avg_chars_per_page": len(full_text) // len(pages) if pages else 0
                }
            }
            
        except Exception as e:
            logger.error(f"❌ [PYPDF2_BYTES] Ошибка извлечения текста: {str(e)}")
            raise Exception(f"Ошибка извлечения текста с PyPDF2 из байтов: {str(e)}")
    
    
    def create_chunks(self, text: str, chunk_size: int = 1000, overlap: int = 100) -> List[Dict[str, Any]]:
        """
        Разделение текста на чанки для обработки
        
        Args:
            text: Исходный текст
            chunk_size: Размер чанка в символах
            overlap: Перекрытие между чанками
            
        Returns:
            Список чанков с метаданными
        """
        chunks = []
        words = text.split()
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk_words = words[i:i + chunk_size]
            chunk_text = ' '.join(chunk_words)
            
            chunks.append({
                'content': chunk_text,
                'start_word': i,
                'end_word': min(i + chunk_size, len(words)),
                'char_count': len(chunk_text),
                'word_count': len(chunk_words)
            })
        
        return chunks
    
    def extract_with_ocr(self, file_path: str) -> Dict[str, Any]:
        """
        Извлечение текста с использованием OCR для распознавания таблиц и чертежей
        
        Args:
            file_path: Путь к PDF файлу
            
        Returns:
            Словарь с результатами OCR обработки
        """
        if not self.use_ocr:
            logger.warning("⚠️ [PDF_EXTRACT] OCR не доступен, используем стандартное извлечение")
            return self.extract_text_from_file(file_path)
        
        try:
            logger.info(f"🔍 [PDF_EXTRACT] Начинаем OCR обработку: {file_path}")
            
            # Сначала пробуем стандартное извлечение
            standard_result = self.extract_text_from_file(file_path)
            
            # Затем добавляем OCR обработку
            ocr_result = self.ocr_processor.process_pdf_with_ocr(file_path)
            
            if ocr_result.get('success', False):
                # Объединяем результаты
                combined_result = {
                    "success": True,
                    "text": standard_result.get("text", ""),
                    "pages": standard_result.get("pages", []),
                    "total_pages": standard_result.get("total_pages", 0),
                    "method": "standard+ocr",
                    "ocr_data": {
                        "tables": ocr_result.get("tables", []),
                        "drawings": ocr_result.get("drawings", []),
                        "processing_time": ocr_result.get("processing_time", 0)
                    },
                    "metadata": standard_result.get("metadata", {})
                }
                
                # Добавляем OCR текст к основному тексту
                ocr_text = ""
                for table in ocr_result.get("tables", []):
                    ocr_text += f"\n\n[ТАБЛИЦА {table.get('table_number', '')} на странице {table.get('page_number', '')}]:\n"
                    ocr_text += table.get("text", "")
                
                for drawing in ocr_result.get("drawings", []):
                    ocr_text += f"\n\n[ЧЕРТЕЖ {drawing.get('drawing_number', '')} на странице {drawing.get('page_number', '')}]:\n"
                    ocr_text += drawing.get("text", "")
                
                combined_result["text"] += ocr_text
                
                logger.info(f"✅ [PDF_EXTRACT] OCR обработка завершена. Найдено {len(ocr_result.get('tables', []))} таблиц и {len(ocr_result.get('drawings', []))} чертежей")
                return combined_result
            else:
                logger.warning(f"⚠️ [PDF_EXTRACT] OCR обработка не удалась: {ocr_result.get('error', 'Неизвестная ошибка')}")
                return standard_result
                
        except Exception as e:
            logger.error(f"❌ [PDF_EXTRACT] Ошибка OCR обработки: {e}")
            # Возвращаем стандартный результат в случае ошибки OCR
            return self.extract_text_from_file(file_path)


# Функции для обратной совместимости
def extract_text_from_pdf_file(file_path: str, prefer_pdfminer: bool = True) -> Dict[str, Any]:
    """
    Извлечение текста из PDF файла (функция для обратной совместимости)
    
    Args:
        file_path: Путь к PDF файлу
        prefer_pdfminer: Предпочитать pdfminer для извлечения текста
        
    Returns:
        Словарь с извлеченным текстом и метаданными
    """
    extractor = PDFTextExtractor(prefer_pdfminer=prefer_pdfminer)
    return extractor.extract_text_from_file(file_path)


def extract_text_from_pdf_bytes(file_content: bytes, prefer_pdfminer: bool = True) -> Dict[str, Any]:
    """
    Извлечение текста из PDF в виде байтов (функция для обратной совместимости)
    
    Args:
        file_content: Содержимое PDF файла в байтах
        prefer_pdfminer: Предпочитать pdfminer для извлечения текста
        
    Returns:
        Словарь с извлеченным текстом и метаданными
    """
    extractor = PDFTextExtractor(prefer_pdfminer=prefer_pdfminer)
    return extractor.extract_text_from_bytes(file_content)
