"""
Модуль для обработки и очистки текста
Содержит функции для очистки, нормализации и структурирования текста
"""

import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TextChunk:
    """Класс для представления текстового чанка"""
    content: str
    chunk_id: int
    hierarchy: Dict[str, Any]
    metadata: Dict[str, Any]


class TextProcessor:
    """Класс для обработки и очистки текста"""
    
    def __init__(self):
        """Инициализация процессора текста"""
        self.cyrillic_pattern = re.compile(r'[а-яё]', re.IGNORECASE)
        self.latin_pattern = re.compile(r'[a-z]', re.IGNORECASE)
        self.digit_pattern = re.compile(r'\d')
        self.punctuation_pattern = re.compile(r'[.,!?;:()[\]{}"\'-]')
    
    # def clean_text(self, text: str, preserve_structure: bool = True) -> str:
    #     """
    #     Очистка текста от лишних символов и нормализация
    #     
    #     Args:
    #         text: Исходный текст
    #         preserve_structure: Сохранять структуру документа (переносы строк)
    #         
    #     Returns:
    #         Очищенный текст
    #     """
    #     if not text:
    #         return ""
    #     
    #     # Удаляем невидимые символы и специальные пробелы
    #     text = re.sub(r'[\u00A0\u2000-\u200F\u2028-\u202F\u205F\u3000]', ' ', text)
    #     
    #     # Исправляем разрывы слов в PDF (пробел между буквами одного слова)
    #     if self.cyrillic_pattern.search(text):
    #         text = self._fix_cyrillic_word_breaks(text)
    #     
    #     # Удаляем множественные пробелы в строках
    #     text = re.sub(r'[ \t]+', ' ', text)
    #     
    #     if preserve_structure:
    #         # Удаляем пробелы в начале и конце строк
    #         lines = text.split('\n')
    #         lines = [line.strip() for line in lines]
    #         text = '\n'.join(lines)
    #         
    #         # Удаляем лишние переносы строк (более 2 подряд)
    #         text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    #     else:
    #         # Удаляем все переносы строк
    #         text = re.sub(r'\s+', ' ', text)
    #         text = text.strip()
    #     
    #     # Удаляем пробелы перед знаками препинания
    #     text = re.sub(r'\s+([.,!?;:])', r'\1', text)
    #     
    #     # Удаляем пробелы после открывающих скобок и перед закрывающими
    #     text = re.sub(r'\(\s+', '(', text)
    #     text = re.sub(r'\s+\)', ')', text)
    #     
    #     # Удаляем пробелы в кавычках
    #     text = re.sub(r'"\s+', '"', text)
    #     text = re.sub(r'\s+"', '"', text)
    #     
    #     return text.strip()
    
    def _fix_cyrillic_word_breaks(self, text: str) -> str:
        """
        Исправление разрывов слов в кириллическом тексте
        
        Args:
            text: Исходный текст
            
        Returns:
            Текст с исправленными разрывами слов
        """
        # Применяем несколько раз для сложных случаев
        for _ in range(3):
            # Исправляем разрывы внутри слов (буква + пробел + буква)
            text = re.sub(r'([а-яё])\s+([а-яё])', r'\1\2', text)
        
        # Исправляем разрывы между словами и знаками препинания
        text = re.sub(r'([а-яё])\s+([.,!?;:])', r'\1\2', text)
        text = re.sub(r'([.,!?;:])\s+([а-яё])', r'\1 \2', text)
        
        # Исправляем специфичные проблемы с разрывами слов
        fixes = [
            (r'\bсмежны\s+х\b', 'смежных'),
            (r'\bпро\s+ектирование\b', 'проектирование'),
            (r'\bтребова\s+ниям\b', 'требованиям'),
            (r'\bсв\s+одов\b', 'сводов'),
            (r'\bустанов\s+ленные\b', 'установленные'),
            (r'\bтехнических\s+решен\s+ий\b', 'технических решений'),
            (r'\bдальнейшему\s+производству\b', 'дальнейшему производству'),
            (r'\bсодержащих\s+установ\s+ленные\b', 'содержащих установленные'),
            (r'\bтех\s+нический\b', 'технический'),
            (r'\bбезопасн\s+ости\b', 'безопасности'),
            (r'\bрегулировании\s+и\b', 'регулировании'),
            (r'\bзданий\s+и\s+соор\s+ужений\b', 'зданий и сооружений'),
            (r'\bпротивопожарной\s+защиты\b', 'противопожарной защиты'),
            (r'\bэвакуационные\s+пути\b', 'эвакуационные пути'),
            (r'\bобеспечения\s+огнестойкости\b', 'обеспечения огнестойкости'),
            (r'\bограничение\s+распространения\b', 'ограничение распространения'),
            (r'\bобъектах\s+за\s+щиты\b', 'объектах защиты'),
            (r'\bобъемно-планировочным\s+и\b', 'объемно-планировочным'),
            (r'\bконструктивным\s+решениям\b', 'конструктивным решениям'),
            (r'\bпроизводственные\s+здания\b', 'производственные здания'),
            (r'\bактуализированная\s+редакция\b', 'актуализированная редакция'),
            (r'\bадминистративные\s+и\s+бытовые\b', 'административные и бытовые'),
            (r'\bзда\s+ния\b', 'здания'),
            (r'\bактуализированная\s+ре\s+дакция\b', 'актуализированная редакция'),
            (r'\bкровли\s+актуализированная\b', 'кровли. Актуализированная'),
            (r'\bтепловая\s+защита\b', 'тепловая защита'),
            (r'\bестественное\s+и\s+иску\s+ственное\b', 'естественное и искусственное'),
            (r'\bосвещение\s+актуализированная\b', 'освещение. Актуализированная'),
            (r'\bредакция\s+снип\b', 'редакция СНиП'),
            (r'\bсаа\s+тветствии\b', 'саатветствии'),
            (r'\bв\s+соответствии\b', 'в соответствии'),
            (r'\bв\s+соответствие\b', 'в соответствие'),
            (r'\bв\s+соответствии\s+с\b', 'в соответствии с'),
            (r'\bв\s+соответствие\s+с\b', 'в соответствие с'),
        ]
        
        for pattern, replacement in fixes:
            text = re.sub(pattern, replacement, text)
        
        return text
    
    def normalize_whitespace(self, text: str) -> str:
        """
        Нормализация пробелов в тексте
        
        Args:
            text: Исходный текст
            
        Returns:
            Текст с нормализованными пробелами
        """
        # Заменяем все виды пробелов на обычные
        text = re.sub(r'[\u00A0\u2000-\u200F\u2028-\u202F\u205F\u3000]', ' ', text)
        
        # Удаляем множественные пробелы
        text = re.sub(r' +', ' ', text)
        
        # Удаляем пробелы в начале и конце строк
        lines = text.split('\n')
        lines = [line.strip() for line in lines]
        text = '\n'.join(lines)
        
        return text.strip()
    
    def detect_language(self, text: str) -> str:
        """
        Определение языка текста
        
        Args:
            text: Исходный текст
            
        Returns:
            Код языка ('ru', 'en', 'mixed', 'unknown')
        """
        if not text:
            return 'unknown'
        
        # Подсчитываем символы разных типов
        cyrillic_count = len(self.cyrillic_pattern.findall(text))
        latin_count = len(self.latin_pattern.findall(text))
        total_letters = cyrillic_count + latin_count
        
        if total_letters == 0:
            return 'unknown'
        
        cyrillic_ratio = cyrillic_count / total_letters
        
        if cyrillic_ratio > 0.7:
            return 'ru'
        elif cyrillic_ratio < 0.3:
            return 'en'
        else:
            return 'mixed'
    
    def extract_sentences(self, text: str) -> List[str]:
        """
        Извлечение предложений из текста
        
        Args:
            text: Исходный текст
            
        Returns:
            Список предложений
        """
        if not text:
            return []
        
        # Более точное разделение предложений для русского языка
        sentence_pattern = r'(?<=[.!?])\s+(?=[А-ЯЁ])|(?<=[.!?])\s*\n(?=[А-ЯЁ])'
        sentences = re.split(sentence_pattern, text)
        
        # Очищаем предложения от лишних пробелов
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences
    
    def extract_paragraphs(self, text: str) -> List[str]:
        """
        Извлечение абзацев из текста
        
        Args:
            text: Исходный текст
            
        Returns:
            Список абзацев
        """
        if not text:
            return []
        
        # Разделяем по двойным переносам строк
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        return paragraphs
    
    def hierarchical_chunking(self, text: str) -> List[TextChunk]:
        """
        Иерархическое разделение текста на чанки: Раздел → Абзац → Предложение
        
        Args:
            text: Исходный текст
            
        Returns:
            Список текстовых чанков с иерархической структурой
        """
        chunks = []
        chunk_id = 1
        
        # Сначала разделяем на абзацы
        paragraphs = self.extract_paragraphs(text)
        
        current_section = ""
        section_number = 1
        
        for para_num, paragraph in enumerate(paragraphs, 1):
            if not paragraph:
                continue
            
            # Проверяем, является ли абзац заголовком раздела
            if re.match(r'^\d+\.?\s+[А-ЯЁ]', paragraph):
                current_section = paragraph
                section_number += 1
                
                # Заголовок как отдельный чанк
                chunk = TextChunk(
                    content=paragraph,
                    chunk_id=chunk_id,
                    hierarchy={
                        "section_number": section_number,
                        "section_title": paragraph,
                        "paragraph_number": para_num,
                        "sentence_number": 1
                    },
                    metadata={
                        "length": len(paragraph),
                        "word_count": len(paragraph.split()),
                        "type": "header"
                    }
                )
                chunks.append(chunk)
                chunk_id += 1
                continue
            
            # Разделяем абзац на предложения
            sentences = self.extract_sentences(paragraph)
            
            for sent_num, sentence in enumerate(sentences, 1):
                if not sentence:
                    continue
                
                # Создаем иерархический чанк
                chunk = TextChunk(
                    content=sentence,
                    chunk_id=chunk_id,
                    hierarchy={
                        "section_number": section_number,
                        "section_title": current_section,
                        "paragraph_number": para_num,
                        "sentence_number": sent_num
                    },
                    metadata={
                        "length": len(sentence),
                        "word_count": len(sentence.split()),
                        "type": "sentence"
                    }
                )
                chunks.append(chunk)
                chunk_id += 1
        
        # Если не удалось разделить на разделы, используем простую структуру
        if not chunks:
            chunks = self._create_simple_chunks(text)
        
        return chunks
    
    def _create_simple_chunks(self, text: str) -> List[TextChunk]:
        """
        Создание простых чанков без иерархии
        
        Args:
            text: Исходный текст
            
        Returns:
            Список простых чанков
        """
        chunks = []
        chunk_id = 1
        
        # Разделяем на абзацы
        paragraphs = self.extract_paragraphs(text)
        
        for para_num, paragraph in enumerate(paragraphs, 1):
            if not paragraph:
                continue
                
            # Разделяем абзац на предложения
            sentences = self.extract_sentences(paragraph)
            
            for sent_num, sentence in enumerate(sentences, 1):
                if not sentence:
                    continue
                
                chunk = TextChunk(
                    content=sentence,
                    chunk_id=chunk_id,
                    hierarchy={
                        "section_number": 1,
                        "section_title": "Основной текст",
                        "paragraph_number": para_num,
                        "sentence_number": sent_num
                    },
                    metadata={
                        "length": len(sentence),
                        "word_count": len(sentence.split()),
                        "type": "sentence"
                    }
                )
                chunks.append(chunk)
                chunk_id += 1
        
        return chunks
    
    def create_fixed_size_chunks(self, text: str, chunk_size: int = 1000, overlap: int = 100) -> List[TextChunk]:
        """
        Создание чанков фиксированного размера
        
        Args:
            text: Исходный текст
            chunk_size: Размер чанка в символах
            overlap: Перекрытие между чанками
            
        Returns:
            Список чанков фиксированного размера
        """
        chunks = []
        words = text.split()
        chunk_id = 1
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk_words = words[i:i + chunk_size]
            chunk_text = ' '.join(chunk_words)
            
            chunk = TextChunk(
                content=chunk_text,
                chunk_id=chunk_id,
                hierarchy={
                    "section_number": 1,
                    "section_title": "Фиксированные чанки",
                    "paragraph_number": 1,
                    "sentence_number": 1
                },
                metadata={
                    "length": len(chunk_text),
                    "word_count": len(chunk_words),
                    "type": "fixed_size",
                    "start_word": i,
                    "end_word": min(i + chunk_size, len(words))
                }
            )
            chunks.append(chunk)
            chunk_id += 1
        
        return chunks
    
    def get_text_statistics(self, text: str) -> Dict[str, Any]:
        """
        Получение статистики по тексту
        
        Args:
            text: Исходный текст
            
        Returns:
            Словарь со статистикой
        """
        if not text:
            return {
                "char_count": 0,
                "word_count": 0,
                "sentence_count": 0,
                "paragraph_count": 0,
                "language": "unknown"
            }
        
        sentences = self.extract_sentences(text)
        paragraphs = self.extract_paragraphs(text)
        words = text.split()
        
        return {
            "char_count": len(text),
            "word_count": len(words),
            "sentence_count": len(sentences),
            "paragraph_count": len(paragraphs),
            "language": self.detect_language(text),
            "avg_words_per_sentence": len(words) / len(sentences) if sentences else 0,
            "avg_sentences_per_paragraph": len(sentences) / len(paragraphs) if paragraphs else 0
        }


# Функции для обратной совместимости
def clean_text(text: str, preserve_structure: bool = True) -> str:
    """
    Очистка текста (функция для обратной совместимости)
    
    Args:
        text: Исходный текст
        preserve_structure: Сохранять структуру документа
        
    Returns:
        Очищенный текст
    """
    processor = TextProcessor()
    return processor.clean_text(text, preserve_structure)


def hierarchical_text_chunking(text: str) -> List[Dict[str, Any]]:
    """
    Иерархическое разделение текста на чанки (функция для обратной совместимости)
    
    Args:
        text: Исходный текст
        
    Returns:
        Список чанков в формате словарей
    """
    processor = TextProcessor()
    chunks = processor.hierarchical_chunking(text)
    
    # Преобразуем TextChunk в словари для обратной совместимости
    return [
        {
            "chunk_id": chunk.chunk_id,
            "text": chunk.content,
            "hierarchy": chunk.hierarchy,
            "metadata": chunk.metadata
        }
        for chunk in chunks
    ]
