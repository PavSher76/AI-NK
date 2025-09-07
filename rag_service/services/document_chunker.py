import logging
import re
from typing import List, Dict, Any

# Настройка логирования
logger = logging.getLogger(__name__)

class DocumentChunker:
    """Класс для разбиения документов на чанки"""
    
    def __init__(self):
        pass
    
    def create_chunks(self, text: str, document_id: int, filename: str) -> List[Dict[str, Any]]:
        """Создание чанков из текста документа с правильной нумерацией страниц и структурой"""
        try:
            logger.info(f"📝 [CREATE_CHUNKS] Creating chunks for document {document_id}")
            
            # Разбиваем текст на страницы по маркерам "Страница X из Y"
            page_pattern = r'Страница\s+(\d+)\s+из\s+(\d+)'
            page_matches = list(re.finditer(page_pattern, text))
            
            chunks = []
            chunk_id = 1
            
            if page_matches:
                # Если найдены маркеры страниц, разбиваем по ним
                logger.info(f"📄 [CREATE_CHUNKS] Found {len(page_matches)} page markers in document")
                
                for i, match in enumerate(page_matches):
                    page_num = int(match.group(1))
                    start_pos = match.end()
                    
                    # Определяем конец страницы (начало следующей или конец текста)
                    if i + 1 < len(page_matches):
                        end_pos = page_matches[i + 1].start()
                    else:
                        end_pos = len(text)
                    
                    # Извлекаем текст страницы
                    page_text = text[start_pos:end_pos].strip()
                    
                    if page_text:
                        # Извлекаем структуру страницы (главы, разделы)
                        page_structure = self._extract_page_structure(page_text, page_num)
                        
                        # Разбиваем страницу на чанки
                        page_chunks = self._split_page_into_chunks(page_text, chunk_size=1000)
                        
                        for chunk_text in page_chunks:
                            # Определяем к какой главе/разделу относится чанк
                            chunk_structure = self._identify_chunk_structure(chunk_text, page_structure)
                            
                            chunks.append({
                                'chunk_id': f"{document_id}_{page_num}_{chunk_id}",
                                'document_id': document_id,
                                'document_title': filename,
                                'content': chunk_text.strip(),
                                'chunk_type': 'paragraph',
                                'page': page_num,
                                'chapter': chunk_structure.get('chapter', ''),
                                'section': chunk_structure.get('section', '')
                            })
                            chunk_id += 1
            else:
                # Если маркеры страниц не найдены, разбиваем весь текст на чанки
                logger.info(f"📄 [CREATE_CHUNKS] No page markers found, treating as single page document")
                page_chunks = self._split_page_into_chunks(text, chunk_size=1000)
                
                # Извлекаем общую структуру документа
                document_structure = self._extract_document_structure(text)
                
                for chunk_text in page_chunks:
                    # Определяем к какой главе/разделу относится чанк
                    chunk_structure = self._identify_chunk_structure(chunk_text, document_structure)
                    
                    chunks.append({
                        'chunk_id': f"{document_id}_1_{chunk_id}",
                        'document_id': document_id,
                        'document_title': filename,
                        'content': chunk_text.strip(),
                        'chunk_type': 'paragraph',
                        'page': 1,
                        'chapter': chunk_structure.get('chapter', ''),
                        'section': chunk_structure.get('section', '')
                    })
                    chunk_id += 1
            
            logger.info(f"✅ [CREATE_CHUNKS] Created {len(chunks)} chunks for document {document_id}")
            return chunks
            
        except Exception as e:
            logger.error(f"❌ [CREATE_CHUNKS] Error creating chunks: {e}")
            return []
    
    def _split_page_into_chunks(self, text: str, chunk_size: int = 1000) -> List[str]:
        """Разбиение текста страницы на гранулярные чанки с улучшенной логикой"""
        try:
            # Импортируем конфигурацию
            from config.chunking_config import get_chunking_config, validate_chunking_config
            
            # Получаем конфигурацию чанкования
            config = get_chunking_config('default')
            
            # Валидируем конфигурацию
            if not validate_chunking_config(config):
                logger.warning("⚠️ [CHUNKING] Invalid chunking config, using fallback")
                return self._simple_split_into_chunks(text, chunk_size)
            
            # Параметры гранулярного чанкования из конфигурации
            target_tokens = config['target_tokens']
            min_tokens = config['min_tokens']
            max_tokens = config['max_tokens']
            overlap_ratio = config['overlap_ratio']
            
            logger.info(f"📝 [CHUNKING] Using config: target={target_tokens}, min={min_tokens}, max={max_tokens}, overlap={overlap_ratio}")
            logger.info(f"📝 [CHUNKING] Input text length: {len(text)} characters")
            
            # Разбиваем текст на предложения
            sentences = self._split_into_sentences(text, config)
            logger.info(f"📝 [CHUNKING] Split into {len(sentences)} sentences")
            
            if not sentences:
                logger.warning("⚠️ [CHUNKING] No sentences found, using fallback")
                return self._simple_split_into_chunks(text, chunk_size)
            
            chunks = []
            current_chunk = []
            current_tokens = 0
            
            logger.info(f"📝 [CHUNKING] Starting chunk creation process...")
            
            # Обрабатываем каждое предложение
            for i, sentence in enumerate(sentences):
                sentence_tokens = self._estimate_tokens(sentence, config)
                logger.info(f"📝 [CHUNKING] Sentence {i+1}: {sentence_tokens} tokens, length: {len(sentence)}")
                
                # Проверяем, нужно ли начать новый чанк
                if current_tokens + sentence_tokens > max_tokens and current_chunk:
                    logger.info(f"📝 [CHUNKING] Max tokens exceeded ({current_tokens + sentence_tokens} > {max_tokens}), creating chunk")
                    # Создаем чанк
                    chunk_text = ' '.join(current_chunk)
                    chunks.append(chunk_text.strip())
                    logger.info(f"📝 [CHUNKING] Created chunk {len(chunks)}: {len(chunk_text)} chars, {current_tokens} tokens")
                    
                    # Начинаем новый чанк с перекрытием
                    overlap_sentences = self._get_overlap_sentences(current_chunk, overlap_ratio, config)
                    current_chunk = overlap_sentences
                    current_tokens = sum(self._estimate_tokens(s, config) for s in overlap_sentences)
                    logger.info(f"📝 [CHUNKING] Started new chunk with {len(overlap_sentences)} overlap sentences, {current_tokens} tokens")
                
                # Добавляем предложение к текущему чанку
                current_chunk.append(sentence)
                current_tokens += sentence_tokens
                logger.info(f"📝 [CHUNKING] Added sentence to current chunk: {current_tokens} tokens total")
                
                # Проверяем, достигли ли целевого размера
                if current_tokens >= target_tokens and current_tokens >= min_tokens:
                    logger.info(f"📝 [CHUNKING] Target size reached ({current_tokens} >= {target_tokens}), creating chunk")
                    # Создаем чанк
                    chunk_text = ' '.join(current_chunk)
                    chunks.append(chunk_text.strip())
                    logger.info(f"📝 [CHUNKING] Created chunk {len(chunks)}: {len(chunk_text)} chars, {current_tokens} tokens")
                    
                    # Начинаем новый чанк с перекрытием
                    overlap_sentences = self._get_overlap_sentences(current_chunk, overlap_ratio, config)
                    current_chunk = overlap_sentences
                    current_tokens = sum(self._estimate_tokens(s, config) for s in overlap_sentences)
                    logger.info(f"📝 [CHUNKING] Started new chunk with {len(overlap_sentences)} overlap sentences, {current_tokens} tokens")
            
            # Добавляем последний чанк, если он не пустой
            if current_chunk and current_tokens >= min_tokens:
                logger.info(f"📝 [CHUNKING] Adding final chunk: {current_tokens} tokens")
                chunk_text = ' '.join(current_chunk)
                chunks.append(chunk_text.strip())
                logger.info(f"📝 [CHUNKING] Created final chunk {len(chunks)}: {len(chunk_text)} chars, {current_tokens} tokens")
            elif current_chunk:
                logger.info(f"📝 [CHUNKING] Final chunk too small ({current_tokens} < {min_tokens}), merging with previous")
                if chunks:
                    # Объединяем с последним чанком
                    last_chunk = chunks[-1]
                    merged_chunk = last_chunk + ' ' + ' '.join(current_chunk)
                    chunks[-1] = merged_chunk
                    logger.info(f"📝 [CHUNKING] Merged final chunk with previous: {len(merged_chunk)} chars")
                else:
                    # Если нет предыдущих чанков, создаем один
                    chunk_text = ' '.join(current_chunk)
                    chunks.append(chunk_text.strip())
                    logger.info(f"📝 [CHUNKING] Created single chunk: {len(chunk_text)} chars, {current_tokens} tokens")
            
            # Проверяем, что у нас есть чанки перед применением логики склейки
            if not chunks:
                logger.warning("⚠️ [CHUNKING] No chunks created, using fallback")
                return self._simple_split_into_chunks(text, chunk_size)
            
            # Применяем логику склейки с заголовками если включена
            if config.get('merge_enabled', True):
                logger.info(f"📝 [CHUNKING] Applying header merging logic to {len(chunks)} chunks...")
                chunks = self._merge_chunks_with_headers(chunks, config)
                logger.info(f"📝 [CHUNKING] After merging: {len(chunks)} chunks")
            
            logger.info(f"✅ [CHUNKING] Created {len(chunks)} granular chunks")
            return chunks
            
        except Exception as e:
            logger.error(f"❌ [GRANULAR_CHUNKS] Error creating granular chunks: {e}")
            import traceback
            logger.error(f"❌ [GRANULAR_CHUNKS] Traceback: {traceback.format_exc()}")
            # Fallback к простому разбиению
            return self._simple_split_into_chunks(text, chunk_size)

    def _split_into_sentences(self, text: str, config: dict) -> List[str]:
        """Разбиение текста на предложения с учетом нормативных документов"""
        try:
            # Получаем паттерны из конфигурации
            sentence_patterns = config.get('sentence_patterns', [
                r'[.!?]+(?=\s+[А-ЯЁ\d])',  # Обычные предложения
                r'[.!?]+(?=\s+\d+\.)',      # Перед номерами пунктов
                r'[.!?]+(?=\s+[А-ЯЁ]\s)',  # Перед заголовками
                r'[.!?]+(?=\s*$)'           # В конце текста
            ])
            
            # Объединяем все паттерны
            combined_pattern = '|'.join(sentence_patterns)
            
            # Разбиваем текст
            sentences = re.split(combined_pattern, text)
            
            # Очищаем и фильтруем предложения
            min_length = config.get('min_sentence_length', 10)
            cleaned_sentences = []
            for sentence in sentences:
                sentence = sentence.strip()
                if sentence and len(sentence) > min_length:
                    cleaned_sentences.append(sentence)
            
            return cleaned_sentences
            
        except Exception as e:
            logger.error(f"❌ [SENTENCE_SPLIT] Error splitting into sentences: {e}")
            # Fallback: простое разбиение по точкам
            return [s.strip() for s in text.split('.') if s.strip()]
    
    def _estimate_tokens(self, text: str, config: dict) -> int:
        """Оценка количества токенов в тексте"""
        try:
            # Получаем коэффициент из конфигурации
            tokens_per_char = config.get('tokens_per_char', 4)
            return max(1, len(text) // tokens_per_char)
        except Exception as e:
            logger.error(f"❌ [TOKEN_ESTIMATION] Error estimating tokens: {e}")
            return len(text) // 4
    
    def _get_overlap_sentences(self, sentences: List[str], overlap_ratio: float, config: dict) -> List[str]:
        """Получение предложений для перекрытия между чанками"""
        try:
            if not sentences:
                return []
            
            # Выбираем последние предложения для перекрытия
            min_overlap = config.get('min_overlap_sentences', 1)
            overlap_count = max(min_overlap, int(len(sentences) * overlap_ratio))
            return sentences[-overlap_count:]
            
        except Exception as e:
            logger.error(f"❌ [OVERLAP] Error getting overlap sentences: {e}")
            return sentences[-1:] if sentences else []
    
    def _merge_chunks_with_headers(self, chunks: List[str], config: dict) -> List[str]:
        """Склейка чанков с заголовками для предотвращения обрыва цитат"""
        try:
            if len(chunks) <= 1:
                return chunks
            
            merged_chunks = []
            current_chunk = chunks[0]
            
            for i in range(1, len(chunks)):
                next_chunk = chunks[i]
                
                # Проверяем, нужно ли объединить чанки
                should_merge = self._should_merge_chunks(current_chunk, next_chunk, config)
                
                if should_merge:
                    # Объединяем чанки
                    current_chunk = current_chunk + ' ' + next_chunk
                else:
                    # Добавляем текущий чанк и начинаем новый
                    merged_chunks.append(current_chunk)
                    current_chunk = next_chunk
            
            # Добавляем последний чанк
            merged_chunks.append(current_chunk)
            
            logger.info(f"📝 [MERGE_HEADERS] Merged {len(chunks)} chunks into {len(merged_chunks)} chunks")
            return merged_chunks
            
        except Exception as e:
            logger.error(f"❌ [MERGE_HEADERS] Error merging chunks: {e}")
            return chunks
    
    def _should_merge_chunks(self, chunk1: str, chunk2: str, config: dict) -> bool:
        """Определение необходимости объединения чанков"""
        try:
            # Проверяем размер объединенного чанка
            combined_tokens = self._estimate_tokens(chunk1, config) + self._estimate_tokens(chunk2, config)
            
            # Если объединенный чанк слишком большой, не объединяем
            max_merged = config.get('max_merged_tokens', 1200)
            if combined_tokens > max_merged:
                return False
            
            # Получаем паттерны заголовков из конфигурации
            header_patterns = config.get('header_patterns', ['глава', 'раздел', 'часть', 'пункт'])
            
            # Проверяем, заканчивается ли первый чанк заголовком
            if any(pattern in chunk1.lower() for pattern in header_patterns):
                return True
            
            # Проверяем, начинается ли второй чанк с продолжения предложения
            if chunk2 and not chunk2[0].isupper():
                return True
            
            # Проверяем, есть ли незавершенные конструкции
            unfinished_patterns = config.get('unfinished_patterns', {})
            
            # Проверяем кавычки
            quotes = unfinished_patterns.get('quotes', ['"', '«', '»'])
            if any(chunk1.count(q) % 2 != 0 for q in quotes):
                return True
            
            # Проверяем скобки
            brackets = unfinished_patterns.get('brackets', ['(', '[', '{'])
            if any(chunk1.count(b) != chunk1.count(self._get_closing_bracket(b)) for b in brackets):
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ [MERGE_LOGIC] Error in merge logic: {e}")
            return False
    
    def _get_closing_bracket(self, opening_bracket: str) -> str:
        """Получение закрывающей скобки для открывающей"""
        bracket_pairs = {
            '(': ')',
            '[': ']',
            '{': '}',
            '<': '>'
        }
        return bracket_pairs.get(opening_bracket, '')

    def _simple_split_into_chunks(self, text: str, chunk_size: int = 1000) -> List[str]:
        """Простое разбиение текста на чанки, используя регулярные выражения."""
        chunks = []
        sentences = re.split(r'[.!?]+', text)
        current_chunk = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            if len(current_chunk) + len(sentence) > chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                current_chunk += sentence + ". "
        
        # Добавляем последний чанк
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks

    def _extract_page_structure(self, page_text: str, page_num: int) -> Dict[str, Any]:
        """Извлечение структуры страницы (главы, разделы)"""
        try:
            structure = {
                'page': page_num,
                'chapters': [],
                'sections': [],
                'headers': []
            }
            
            # Паттерны для поиска заголовков глав и разделов
            chapter_patterns = [
                r'^ГЛАВА\s+(\d+)\s*[\.\-]?\s*(.+)$',
                r'^Глава\s+(\d+)\s*[\.\-]?\s*(.+)$',
                r'^РАЗДЕЛ\s+(\d+)\s*[\.\-]?\s*(.+)$',
                r'^Раздел\s+(\d+)\s*[\.\-]?\s*(.+)$',
                r'^ЧАСТЬ\s+(\d+)\s*[\.\-]?\s*(.+)$',
                r'^Часть\s+(\d+)\s*[\.\-]?\s*(.+)$'
            ]
            
            section_patterns = [
                r'^(\d+\.\d+)\s+(.+)$',
                r'^(\d+\.\d+\.\d+)\s+(.+)$',
                r'^(\d+\.\d+\.\d+\.\d+)\s+(.+)$',
                r'^(\d+)\s+(.+)$'
            ]
            
            lines = page_text.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Проверяем паттерны глав
                for pattern in chapter_patterns:
                    match = re.match(pattern, line, re.IGNORECASE)
                    if match:
                        structure['chapters'].append({
                            'number': match.group(1),
                            'title': match.group(2).strip(),
                            'line': line
                        })
                        break
                
                # Проверяем паттерны разделов
                for pattern in section_patterns:
                    match = re.match(pattern, line)
                    if match:
                        structure['sections'].append({
                            'number': match.group(1),
                            'title': match.group(2).strip(),
                            'line': line
                        })
                        break
                
                # Проверяем на заголовки (строки в верхнем регистре)
                if line.isupper() and len(line) > 5 and len(line) < 100:
                    structure['headers'].append(line)
            
            return structure
            
        except Exception as e:
            logger.error(f"❌ [EXTRACT_PAGE_STRUCTURE] Error extracting page structure: {e}")
            return {'page': page_num, 'chapters': [], 'sections': [], 'headers': []}
    
    def _extract_document_structure(self, text: str) -> Dict[str, Any]:
        """Извлечение общей структуры документа"""
        try:
            structure = {
                'chapters': [],
                'sections': [],
                'headers': []
            }
            
            # Паттерны для поиска заголовков
            chapter_patterns = [
                r'^ГЛАВА\s+(\d+)\s*[\.\-]?\s*(.+)$',
                r'^Глава\s+(\d+)\s*[\.\-]?\s*(.+)$',
                r'^РАЗДЕЛ\s+(\d+)\s*[\.\-]?\s*(.+)$',
                r'^Раздел\s+(\d+)\s*[\.\-]?\s*(.+)$'
            ]
            
            section_patterns = [
                r'^(\d+\.\d+)\s+(.+)$',
                r'^(\d+\.\d+\.\d+)\s+(.+)$',
                r'^(\d+\.\d+\.\d+\.\d+)\s+(.+)$'
            ]
            
            lines = text.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Проверяем паттерны глав
                for pattern in chapter_patterns:
                    match = re.match(pattern, line, re.IGNORECASE)
                    if match:
                        structure['chapters'].append({
                            'number': match.group(1),
                            'title': match.group(2).strip(),
                            'line': line
                        })
                        break
                
                # Проверяем паттерны разделов
                for pattern in section_patterns:
                    match = re.match(pattern, line)
                    if match:
                        structure['sections'].append({
                            'number': match.group(1),
                            'title': match.group(2).strip(),
                            'line': line
                        })
                        break
            
            return structure
            
        except Exception as e:
            logger.error(f"❌ [EXTRACT_DOCUMENT_STRUCTURE] Error extracting document structure: {e}")
            return {'chapters': [], 'sections': [], 'headers': []}
    
    def _identify_chunk_structure(self, chunk_text: str, structure: Dict[str, Any]) -> Dict[str, str]:
        """Определение к какой главе/разделу относится чанк"""
        try:
            result = {'chapter': '', 'section': ''}
            
            if not structure or not chunk_text:
                return result
            
            # Ищем ближайший заголовок раздела в чанке
            section_patterns = [
                r'(\d+\.\d+\.\d+\.\d+)\s+(.+)',
                r'(\d+\.\d+\.\d+)\s+(.+)',
                r'(\d+\.\d+)\s+(.+)',
                r'(\d+)\s+(.+)'
            ]
            
            for pattern in section_patterns:
                match = re.search(pattern, chunk_text)
                if match:
                    section_number = match.group(1)
                    section_title = match.group(2).strip()
                    
                    # Ищем соответствующую главу
                    chapter_num = section_number.split('.')[0]
                    for chapter in structure.get('chapters', []):
                        if chapter['number'] == chapter_num:
                            result['chapter'] = f"Глава {chapter_num}. {chapter['title']}"
                            break
                    
                    result['section'] = f"{section_number}. {section_title}"
                    break
            
            # Если не нашли раздел, ищем главу
            if not result['section']:
                chapter_patterns = [
                    r'ГЛАВА\s+(\d+)\s*[\.\-]?\s*(.+)',
                    r'Глава\s+(\d+)\s*[\.\-]?\s*(.+)',
                    r'РАЗДЕЛ\s+(\d+)\s*[\.\-]?\s*(.+)',
                    r'Раздел\s+(\d+)\s*[\.\-]?\s*(.+)'
                ]
                
                for pattern in chapter_patterns:
                    match = re.search(pattern, chunk_text, re.IGNORECASE)
                    if match:
                        chapter_num = match.group(1)
                        chapter_title = match.group(2).strip()
                        result['chapter'] = f"Глава {chapter_num}. {chapter_title}"
                        break
            
            return result
            
        except Exception as e:
            logger.error(f"❌ [IDENTIFY_CHUNK_STRUCTURE] Error identifying chunk structure: {e}")
            return {'chapter': '', 'section': ''}
