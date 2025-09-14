import logging
import os
import tempfile
import sys
from typing import Optional

# Импорт общего модуля утилит
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from utils import parse_document, parse_document_from_bytes

# Настройка логирования
logger = logging.getLogger(__name__)

class DocumentParser:
    """Класс для парсинга различных типов документов"""
    
    def __init__(self):
        pass
    
    async def extract_text_from_document(self, content: bytes, filename: str) -> str:
        """Извлечение текста из документа"""
        try:
            # Создаем временный файл
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{filename.split('.')[-1]}") as temp_file:
                temp_file.write(content)
                temp_file_path = temp_file.name
            
            try:
                if filename.lower().endswith('.pdf'):
                    return await self.extract_text_from_pdf(temp_file_path)
                elif filename.lower().endswith('.docx'):
                    return await self.extract_text_from_docx(temp_file_path)
                elif filename.lower().endswith('.txt'):
                    return content.decode('utf-8', errors='ignore')
                else:
                    logger.error(f"❌ [EXTRACT_TEXT] Unsupported file type: {filename}")
                    return ""
            finally:
                # Удаляем временный файл
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except Exception as e:
            logger.error(f"❌ [EXTRACT_TEXT] Error extracting text: {e}")
            return ""

    async def extract_text_from_pdf(self, file_path: str) -> str:
        """Извлечение текста из PDF с использованием общего модуля utils"""
        try:
            result = parse_document(file_path)
            if result.get("success", False):
                return result.get("text", "")
            else:
                logger.error(f"❌ [EXTRACT_PDF] Error extracting text from PDF: {result.get('error', 'Unknown error')}")
                return ""
        except Exception as e:
            logger.error(f"❌ [EXTRACT_PDF] Error extracting text from PDF: {e}")
            return ""

    async def extract_text_from_docx(self, file_path: str) -> str:
        """Извлечение текста из DOCX с использованием общего модуля utils"""
        try:
            result = parse_document(file_path)
            if result.get("success", False):
                return result.get("text", "")
            else:
                logger.error(f"❌ [EXTRACT_DOCX] Error extracting text from DOCX: {result.get('error', 'Unknown error')}")
                return ""
        except Exception as e:
            logger.error(f"❌ [EXTRACT_DOCX] Error extracting text from DOCX: {e}")
            return ""

    def extract_document_code(self, document_title: str) -> str:
        """
        Извлекает код документа из названия (ГОСТ, СП, СНиП и т.д.)
        """
        try:
            import re
            
            # Убираем расширение файла
            title_without_ext = re.sub(r'\.(pdf|txt|doc|docx)$', '', document_title, flags=re.IGNORECASE)
            
            patterns = [
                r'ГОСТ\s+[\d\.-]+', 
                r'СП\s+[\d\.-]+', 
                r'СНиП\s+[\d\.-]+',
                r'ТР\s+ТС\s+[\d\.-]+', 
                r'СТО\s+[\d\.-]+', 
                r'РД\s+[\d\.-]+',
                r'ТУ\s+[\d\.-]+',
                r'ПБ\s+[\d\.-]+',
                r'НПБ\s+[\d\.-]+',
                r'СПб\s+[\d\.-]+',
                r'МГСН\s+[\d\.-]+'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, title_without_ext, re.IGNORECASE)
                if match:
                    code = match.group(0).strip()
                    logger.info(f"🔍 [CODE_EXTRACTION] Extracted code '{code}' from title '{document_title}'")
                    return code
            
            logger.warning(f"⚠️ [CODE_EXTRACTION] No code pattern found in title: '{document_title}'")
            return ""
        except Exception as e:
            logger.warning(f"⚠️ [CODE_EXTRACTION] Error extracting document code: {e}")
            return ""

    def extract_document_code_from_query(self, query: str) -> Optional[str]:
        """Извлекает код документа из запроса пользователя"""
        try:
            import re
            
            # Паттерны для поиска кодов документов
            patterns = [
                r'СП\s+(\d+\.\d+\.\d+)',  # СП 22.13330.2016
                r'СНиП\s+(\d+\.\d+\.\d+)',  # СНиП 2.01.01-82
                r'ГОСТ\s+(\d+\.\d+\.\d+)',  # ГОСТ 27751-2014
                r'ТУ\s+(\d+\.\d+\.\d+)',   # ТУ 3812-001-12345678-2016
                r'ПБ\s+(\d+\.\d+\.\d+)',   # ПБ 03-428-02
                r'НПБ\s+(\d+\.\d+\.\d+)',  # НПБ 5-2000
                r'СПб\s+(\d+\.\d+\.\d+)',  # СПб 70.13330.2012
                r'МГСН\s+(\d+\.\d+\.\d+)'  # МГСН 4.19-2005
            ]
            
            for pattern in patterns:
                match = re.search(pattern, query, re.IGNORECASE)
                if match:
                    # Восстанавливаем полный код документа
                    if 'СП' in pattern:
                        return f"СП {match.group(1)}"
                    elif 'СНиП' in pattern:
                        return f"СНиП {match.group(1)}"
                    elif 'ГОСТ' in pattern:
                        return f"ГОСТ {match.group(1)}"
                    elif 'ТУ' in pattern:
                        return f"ТУ {match.group(1)}"
                    elif 'ПБ' in pattern:
                        return f"ПБ {match.group(1)}"
                    elif 'НПБ' in pattern:
                        return f"НПБ {match.group(1)}"
                    elif 'СПб' in pattern:
                        return f"СПб {match.group(1)}"
                    elif 'МГСН' in pattern:
                        return f"МГСН {match.group(1)}"
            
            return None
            
        except Exception as e:
            logger.error(f"❌ [DOCUMENT_CODE_EXTRACTION] Error extracting document code: {e}")
            return None
