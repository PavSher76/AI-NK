"""
Модуль для извлечения текста из PDF документов
Содержит улучшенные функции извлечения текста с использованием pdfminer и PyPDF2
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

logger = logging.getLogger(__name__)


class PDFTextExtractor:
    """Класс для извлечения текста из PDF документов"""
    
    def __init__(self, prefer_pdfminer: bool = True):
        """
        Инициализация экстрактора
        
        Args:
            prefer_pdfminer: Предпочитать pdfminer для извлечения текста (более точный)
        """
        self.prefer_pdfminer = prefer_pdfminer
        
        if not PDF2_AVAILABLE and not PDFMINER_AVAILABLE:
            raise ImportError("Необходимо установить PyPDF2 или pdfminer.six для работы с PDF")
    
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
                cleaned_page_text = self._clean_extracted_text(page_text)
                
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
                    cleaned_page_text = self._clean_extracted_text(page_text)
                    
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
                cleaned_page_text = self._clean_extracted_text(page_text)
                
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
    
    def _clean_extracted_text(self, text: str) -> str:
        """
        Очистка извлеченного текста от лишних пробелов и символов с сохранением структуры
        
        Args:
            text: Исходный текст
            
        Returns:
            Очищенный текст
        """
        import re
        
        # Удаляем невидимые символы и специальные пробелы
        text = re.sub(r'[\u00A0\u2000-\u200F\u2028-\u202F\u205F\u3000]', ' ', text)
        
        # Исправляем разрывы слов в PDF (пробел между буквами одного слова)
        # Паттерн: буква + пробел + буква (внутри слова)
        # Применяем несколько раз для сложных случаев
        for _ in range(3):
            text = re.sub(r'([а-яё])\s+([а-яё])', r'\1\2', text)
        
        # Исправляем разрывы между словами и знаками препинания
        text = re.sub(r'([а-яё])\s+([.,!?;:])', r'\1\2', text)
        text = re.sub(r'([.,!?;:])\s+([а-яё])', r'\1 \2', text)
        
        # Исправляем специфичные проблемы с разрывами слов
        text = re.sub(r'\bсмежны\s+х\b', 'смежных', text)
        text = re.sub(r'\bпро\s+ектирование\b', 'проектирование', text)
        text = re.sub(r'\bтребова\s+ниям\b', 'требованиям', text)
        text = re.sub(r'\bсв\s+одов\b', 'сводов', text)
        text = re.sub(r'\bустанов\s+ленные\b', 'установленные', text)
        text = re.sub(r'\bтехнических\s+решен\s+ий\b', 'технических решений', text)
        text = re.sub(r'\bдальнейшему\s+производству\b', 'дальнейшему производству', text)
        text = re.sub(r'\bсодержащих\s+установ\s+ленные\b', 'содержащих установленные', text)
        text = re.sub(r'\bтех\s+нический\b', 'технический', text)
        text = re.sub(r'\bбезопасн\s+ости\b', 'безопасности', text)
        text = re.sub(r'\bрегулировании\s+и\b', 'регулировании', text)
        text = re.sub(r'\bзданий\s+и\s+соор\s+ужений\b', 'зданий и сооружений', text)
        text = re.sub(r'\bпротивопожарной\s+защиты\b', 'противопожарной защиты', text)
        text = re.sub(r'\bэвакуационные\s+пути\b', 'эвакуационные пути', text)
        text = re.sub(r'\bобеспечения\s+огнестойкости\b', 'обеспечения огнестойкости', text)
        text = re.sub(r'\bограничение\s+распространения\b', 'ограничение распространения', text)
        text = re.sub(r'\bобъектах\s+за\s+щиты\b', 'объектах защиты', text)
        text = re.sub(r'\bобъемно-планировочным\s+и\b', 'объемно-планировочным', text)
        text = re.sub(r'\bконструктивным\s+решениям\b', 'конструктивным решениям', text)
        text = re.sub(r'\bпроизводственные\s+здания\b', 'производственные здания', text)
        text = re.sub(r'\bактуализированная\s+редакция\b', 'актуализированная редакция', text)
        text = re.sub(r'\bадминистративные\s+и\s+бытовые\b', 'административные и бытовые', text)
        text = re.sub(r'\bзда\s+ния\b', 'здания', text)
        text = re.sub(r'\bактуализированная\s+ре\s+дакция\b', 'актуализированная редакция', text)
        text = re.sub(r'\bкровли\s+актуализированная\b', 'кровли. Актуализированная', text)
        text = re.sub(r'\bтепловая\s+защита\b', 'тепловая защита', text)
        text = re.sub(r'\bактуализированная\s+ре\s+дакция\b', 'актуализированная редакция', text)
        text = re.sub(r'\bестественное\s+и\s+иску\s+ственное\b', 'естественное и искусственное', text)
        text = re.sub(r'\bосвещение\s+актуализированная\b', 'освещение. Актуализированная', text)
        text = re.sub(r'\bредакция\s+снип\b', 'редакция СНиП', text)
        
        # Исправляем проблему с "саатветствии" -> "саа тветствии"
        text = re.sub(r'\bсаа\s+тветствии\b', 'саатветствии', text)
        text = re.sub(r'\bв\s+соответствии\b', 'в соответствии', text)
        text = re.sub(r'\bв\s+соответствие\b', 'в соответствие', text)
        text = re.sub(r'\bв\s+соответствии\b', 'в соответствии', text)
        
        # Исправляем другие частые проблемы с пробелами в PDF
        text = re.sub(r'\bв\s+соответствии\s+с\b', 'в соответствии с', text)
        text = re.sub(r'\bв\s+соответствие\s+с\b', 'в соответствие с', text)
        text = re.sub(r'\bв\s+соответствии\s+с\b', 'в соответствии с', text)
        
        # Удаляем множественные пробелы в строках, но сохраняем переносы строк
        text = re.sub(r'[ \t]+', ' ', text)
        
        # Удаляем пробелы в начале и конце строк
        lines = text.split('\n')
        lines = [line.strip() for line in lines]
        text = '\n'.join(lines)
        
        # Удаляем лишние переносы строк (более 2 подряд)
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        # Удаляем пробелы перед знаками препинания
        text = re.sub(r'\s+([.,!?;:])', r'\1', text)
        
        # Удаляем пробелы после открывающих скобок и перед закрывающими
        text = re.sub(r'\(\s+', '(', text)
        text = re.sub(r'\s+\)', ')', text)
        
        # Удаляем пробелы в кавычках
        text = re.sub(r'"\s+', '"', text)
        text = re.sub(r'\s+"', '"', text)
        
        return text.strip()
    
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
