import logging
import re
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Tuple

# Настройка логирования
logger = logging.getLogger(__name__)

class MetadataExtractor:
    """Класс для извлечения метаданных из документов"""
    
    def __init__(self):
        pass
    
    def extract_document_metadata(self, filename: str, document_id: int, file_path: str = None) -> Dict[str, Any]:
        """Извлечение метаданных документа из названия файла"""
        try:
            logger.info(f"🔍 [EXTRACT_DOCUMENT_METADATA] Called with: filename='{filename}', document_id={document_id}, file_path='{file_path}'")
            
            # Базовые метаданные
            metadata = {
                "doc_id": f"doc_{document_id}",
                "doc_type": "OTHER",
                "doc_number": "",
                "doc_title": filename,
                "edition_year": None,
                "status": "unknown",
                "replaced_by": None,
                "section": None,
                "paragraph": None,
                "page": None,
                "source_path": file_path or "",
                "source_url": None,
                "ingested_at": datetime.now().strftime("%Y-%m-%d"),
                "lang": "ru",
                "tags": [],
                "checksum": ""
            }
            
            # Извлекаем тип документа и номер
            logger.info(f"🔍 [EXTRACT_DOCUMENT_METADATA] Parsing filename: '{filename}'")
            doc_type, doc_number, edition_year = self._parse_document_name(filename)
            logger.info(f"🔍 [EXTRACT_DOCUMENT_METADATA] Parsed: doc_type='{doc_type}', doc_number='{doc_number}', edition_year='{edition_year}'")
            metadata["doc_type"] = doc_type
            metadata["doc_number"] = doc_number
            metadata["edition_year"] = edition_year
            
            # Генерируем уникальный doc_id
            if doc_number and edition_year:
                metadata["doc_id"] = f"{doc_type.lower()}_{doc_number}_{edition_year}"
            
            # Определяем статус документа
            metadata["status"] = self._determine_document_status(filename, doc_type, doc_number)
            
            # Извлекаем теги на основе типа документа
            metadata["tags"] = self._extract_document_tags(doc_type, doc_number, filename)
            
            # Вычисляем checksum если есть путь к файлу
            if file_path:
                metadata["checksum"] = self._calculate_file_checksum(file_path)
            
            return metadata
            
        except Exception as e:
            logger.error(f"❌ [EXTRACT_DOCUMENT_METADATA] Error extracting metadata: {e}")
            return {
                "doc_id": f"doc_{document_id}",
                "doc_type": "OTHER",
                "doc_number": "",
                "doc_title": filename,
                "edition_year": None,
                "status": "unknown",
                "replaced_by": None,
                "section": None,
                "paragraph": None,
                "page": None,
                "source_path": file_path or "",
                "source_url": None,
                "ingested_at": datetime.now().strftime("%Y-%m-%d"),
                "lang": "ru",
                "tags": [],
                "checksum": ""
            }
    
    def _parse_document_name(self, filename: str) -> Tuple[str, str, int]:
        """Парсинг названия документа для извлечения типа, номера и года"""
        try:
            # Убираем расширение файла
            name = filename.replace('.pdf', '').replace('.docx', '').replace('.doc', '')
            
            # Паттерны для различных типов документов
            patterns = [
                # ГОСТ
                (r'ГОСТ\s+(\d+(?:\.\d+)*)-(\d{4})', 'GOST'),
                (r'ГОСТ\s+(\d+(?:\.\d+)*)', 'GOST'),
                
                # СП (Свод правил)
                (r'СП\s+(\d+(?:\.\d+)*)\.(\d{4})', 'SP'),
                (r'СП\s+(\d+(?:\.\d+)*)', 'SP'),
                
                # СНиП
                (r'СНиП\s+(\d+(?:\.\d+)*)-(\d{4})', 'SNiP'),
                (r'СНиП\s+(\d+(?:\.\d+)*)\.(\d{4})', 'SNiP'),
                (r'СНиП\s+(\d+(?:\.\d+)*)-(\d{2})(?:\.|$)', 'SNiP'),
                (r'СНиП\s+(\d+(?:\.\d+)*)', 'SNiP'),
                
                # ФНП
                (r'ФНП\s+(\d+(?:\.\d+)*)-(\d{4})', 'FNP'),
                (r'ФНП\s+(\d+(?:\.\d+)*)', 'FNP'),
                
                # ПБ (Правила безопасности)
                (r'ПБ\s+(\d+(?:\.\d+)*)-(\d{4})', 'CORP_STD'),
                (r'ПБ\s+(\d+(?:\.\d+)*)', 'CORP_STD'),
                
                # А (Альбом)
                (r'А(\d+(?:\.\d+)*)\.(\d{4})', 'CORP_STD'),
                (r'А(\d+(?:\.\d+)*)\.(\d{2})', 'CORP_STD'),
                (r'А(\d+(?:\.\d+)*)', 'CORP_STD'),
            ]
            
            for pattern, doc_type in patterns:
                match = re.search(pattern, name, re.IGNORECASE)
                if match:
                    groups = match.groups()
                    if len(groups) == 2:
                        # Есть год
                        doc_number = groups[0]
                        year_str = groups[1]
                        # Если год двухзначный, добавляем 19 или 20
                        if len(year_str) == 2:
                            year_int = int(year_str)
                            if year_int >= 0 and year_int <= 30:  # 2000-2030
                                edition_year = 2000 + year_int
                            else:  # 1930-1999
                                edition_year = 1900 + year_int
                        else:
                            edition_year = int(year_str)
                        return doc_type, doc_number, edition_year
                    else:
                        # Нет года, пытаемся найти его отдельно
                        doc_number = groups[0]
                        year_match = re.search(r'(\d{4})', name)
                        edition_year = int(year_match.group(1)) if year_match else None
                        return doc_type, doc_number, edition_year
            
            # Если не нашли стандартный паттерн, пытаемся извлечь год
            year_match = re.search(r'(\d{4})', name)
            edition_year = int(year_match.group(1)) if year_match else None
            
            return "OTHER", "", edition_year
            
        except Exception as e:
            logger.error(f"❌ [PARSE_DOCUMENT_NAME] Error parsing document name: {e}")
            return "OTHER", "", None
    
    def _determine_document_status(self, filename: str, doc_type: str, doc_number: str) -> str:
        """Определение статуса документа"""
        try:
            # Ключевые слова для определения статуса
            if any(word in filename.lower() for word in ['отменен', 'отменен', 'недействителен', 'repealed']):
                return "repealed"
            elif any(word in filename.lower() for word in ['заменен', 'заменяет', 'replaced', 'изм']):
                return "replaced"
            elif any(word in filename.lower() for word in ['действующий', 'актуальный', 'active']):
                return "active"
            else:
                return "unknown"
                
        except Exception as e:
            logger.error(f"❌ [DETERMINE_DOCUMENT_STATUS] Error determining status: {e}")
            return "unknown"
    
    def _extract_document_tags(self, doc_type: str, doc_number: str, filename: str) -> List[str]:
        """Извлечение тегов на основе типа и содержания документа"""
        try:
            tags = []
            
            # Теги на основе типа документа
            type_tags = {
                "GOST": ["государственный стандарт", "гост"],
                "SP": ["свод правил", "строительство"],
                "SNiP": ["строительные нормы", "строительство"],
                "FNP": ["федеральные нормы", "промышленность"],
                "CORP_STD": ["корпоративный стандарт", "внутренний стандарт"]
            }
            
            if doc_type in type_tags:
                tags.extend(type_tags[doc_type])
            
            # Теги на основе содержания в названии
            content_keywords = {
                "электр": ["электроснабжение", "электротехника"],
                "пожар": ["пожарная безопасность", "пожар"],
                "строит": ["строительство", "конструкции"],
                "безопасн": ["охрана труда", "безопасность"],
                "проект": ["проектирование", "проектная документация"],
                "конструкц": ["конструкции", "строительные конструкции"],
                "стальн": ["стальные конструкции", "металлоконструкции"],
                "документац": ["документооборот", "документация"]
            }
            
            filename_lower = filename.lower()
            for keyword, tag_list in content_keywords.items():
                if keyword in filename_lower:
                    tags.extend(tag_list)
            
            # Убираем дубликаты
            return list(set(tags))
            
        except Exception as e:
            logger.error(f"❌ [EXTRACT_DOCUMENT_TAGS] Error extracting tags: {e}")
            return []
    
    def _calculate_file_checksum(self, file_path: str) -> str:
        """Вычисление SHA256 checksum файла"""
        try:
            hash_sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
            
        except Exception as e:
            logger.error(f"❌ [CALCULATE_FILE_CHECKSUM] Error calculating checksum: {e}")
            return ""
    
    def create_chunk_metadata(self, chunk: Dict[str, Any], document_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Создание метаданных для чанка на основе метаданных документа"""
        try:
            # Копируем метаданные документа
            chunk_metadata = document_metadata.copy()
            
            # Обновляем специфичные для чанка поля
            chunk_metadata.update({
                "section": chunk.get('section', ''),
                "paragraph": self._extract_paragraph_from_chunk(chunk.get('content', '')),
                "page": chunk.get('page', 1),
                "chunk_id": chunk.get('chunk_id', ''),
                "chunk_type": chunk.get('chunk_type', 'paragraph')
            })
            
            return chunk_metadata
            
        except Exception as e:
            logger.error(f"❌ [CREATE_CHUNK_METADATA] Error creating chunk metadata: {e}")
            return document_metadata
    
    def _extract_paragraph_from_chunk(self, content: str) -> str:
        """Извлечение номера параграфа из содержимого чанка"""
        try:
            # Паттерны для поиска номеров параграфов
            paragraph_patterns = [
                r'(\d+\.\d+\.\d+\.\d+)',  # 5.2.1.1
                r'(\d+\.\d+\.\d+)',       # 5.2.1
                r'(\d+\.\d+)',            # 5.2
                r'п\.\s*(\d+\.\d+)',      # п.5.2
                r'пункт\s*(\d+\.\d+)',    # пункт 5.2
            ]
            
            for pattern in paragraph_patterns:
                match = re.search(pattern, content)
                if match:
                    return match.group(1)
            
            return ""
            
        except Exception as e:
            logger.error(f"❌ [EXTRACT_PARAGRAPH_FROM_CHUNK] Error extracting paragraph: {e}")
            return ""
