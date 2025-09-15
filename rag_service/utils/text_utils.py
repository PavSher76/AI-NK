import re
import hashlib
from typing import List, Dict, Any
from core.models import ChunkType

# def clean_text(text: str) -> str:
#     """Очистка текста от лишних символов"""
#     if not text:
#         return ""
#     
#     # Удаляем лишние пробелы и переносы строк
#     text = re.sub(r'\s+', ' ', text.strip())
#     
#     # Удаляем специальные символы, но оставляем кириллицу, латиницу, цифры и основные знаки
#     text = re.sub(r'[^\w\s\-\.\,\;\:\!\?\(\)\[\]\{\}\"\'\–\—\№\§\©\®\™\°\±\×\÷\=\+\-\*\/\^\|\&\<\>\~]', '', text)
#     
#     return text

def split_text_into_chunks(text: str, chunk_size: int = 500, overlap: int = 75) -> List[str]:
    """Разбиение текста на чанки с перекрытием"""
    if not text:
        return []
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # Если это не последний чанк, ищем границу предложения
        if end < len(text):
            # Ищем ближайший конец предложения
            sentence_end = text.rfind('.', start, end)
            if sentence_end > start + chunk_size // 2:
                end = sentence_end + 1
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        # Следующий чанк с перекрытием
        start = end - overlap
        if start >= len(text):
            break
    
    return chunks

def generate_chunk_id(document_id: int, page_number: int, chunk_index: int) -> str:
    """Генерация уникального ID для чанка"""
    return f"doc_{document_id}_page_{page_number}_chunk_{chunk_index}"

def generate_clause_id(document_id: int, chapter: str, section: str) -> str:
    """Генерация ID для пункта документа"""
    base = f"doc_{document_id}"
    if chapter:
        base += f"_ch_{hashlib.md5(chapter.encode()).hexdigest()[:8]}"
    if section:
        base += f"_sec_{hashlib.md5(section.encode()).hexdigest()[:8]}"
    return base

def detect_chunk_type(content: str) -> ChunkType:
    """Определение типа чанка по содержимому"""
    content_lower = content.lower()
    
    # Проверяем на таблицу
    if re.search(r'\|\s*\w+', content) or re.search(r'\t\w+', content):
        return ChunkType.TABLE
    
    # Проверяем на заголовок
    if re.match(r'^[А-ЯЁ][А-ЯЁ\s\d\.\-]+$', content.strip()):
        return ChunkType.HEADER
    
    # Проверяем на рисунок
    if re.search(r'рис\.|рисунок|figure|иллюстрация', content_lower):
        return ChunkType.FIGURE
    
    # По умолчанию - текст
    return ChunkType.TEXT

def extract_metadata(content: str) -> Dict[str, Any]:
    """Извлечение метаданных из содержимого"""
    metadata = {
        "word_count": len(content.split()),
        "char_count": len(content),
        "has_numbers": bool(re.search(r'\d', content)),
        "has_units": bool(re.search(r'(мм|см|м|кг|т|л|м³|м²|°C|Вт|А|В)', content)),
        "has_references": bool(re.search(r'(ГОСТ|СП|СНиП|ПУЭ)', content))
    }
    
    return metadata
