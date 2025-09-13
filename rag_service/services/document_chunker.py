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
                            
                            # Создаем расширенные метаданные структуры
                            structure_metadata = self._create_structure_metadata(chunk_text, page_structure, chunk_structure)
                            
                            chunks.append({
                                'chunk_id': f"{document_id}_{page_num}_{chunk_id}",
                                'document_id': document_id,
                                'document_title': filename,
                                'content': chunk_text.strip(),
                                'chunk_type': 'paragraph',
                                'page': page_num,
                                'chapter': chunk_structure.get('chapter', ''),
                                'section': chunk_structure.get('section', ''),
                                'structure_metadata': structure_metadata
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
                    
                    # Создаем расширенные метаданные структуры
                    structure_metadata = self._create_structure_metadata(chunk_text, document_structure, chunk_structure)
                    
                    chunks.append({
                        'chunk_id': f"{document_id}_1_{chunk_id}",
                        'document_id': document_id,
                        'document_title': filename,
                        'content': chunk_text.strip(),
                        'chunk_type': 'paragraph',
                        'page': 1,
                        'chapter': chunk_structure.get('chapter', ''),
                        'section': chunk_structure.get('section', ''),
                        'structure_metadata': structure_metadata
                    })
                    chunk_id += 1
            
            logger.info(f"✅ [CREATE_CHUNKS] Created {len(chunks)} chunks for document {document_id}")
            return chunks
            
        except Exception as e:
            logger.error(f"❌ [CREATE_CHUNKS] Error creating chunks: {e}")
            return []
    
    def _split_page_into_chunks(self, text: str, chunk_size: int = 1000) -> List[str]:
        """Разбиение текста страницы на иерархические чанки с сохранением структуры"""
        try:
            # Импортируем конфигурацию
            from config.chunking_config import get_chunking_config, validate_chunking_config
            
            # Получаем конфигурацию чанкования
            config = get_chunking_config('default')
            
            # Валидируем конфигурацию
            if not validate_chunking_config(config):
                logger.warning("⚠️ [CHUNKING] Invalid chunking config, using fallback")
                return self._simple_split_into_chunks(text, chunk_size)
            
            # Проверяем, включено ли семантическое чанкование
            if config.get('semantic_chunking', True):
                logger.info("📝 [CHUNKING] Using semantic chunking with meaning-based analysis")
                logger.info(f"📝 [CHUNKING] Input text length: {len(text)} characters")
                
                # Создаем семантические чанки
                semantic_chunks = self._create_semantic_chunks(text, config)
                
                if semantic_chunks:
                    logger.info(f"✅ [CHUNKING] Created {len(semantic_chunks)} semantic chunks")
                    return semantic_chunks
                else:
                    logger.warning("⚠️ [CHUNKING] No semantic chunks created, falling back to hierarchical")
            
            # Проверяем, включено ли иерархическое чанкование
            if not config.get('hierarchical_chunking', True):
                logger.info("📝 [CHUNKING] Hierarchical chunking disabled, using standard chunking")
                return self._standard_chunking(text, config)
            
            logger.info("📝 [CHUNKING] Using hierarchical chunking with structure preservation")
            logger.info(f"📝 [CHUNKING] Input text length: {len(text)} characters")
            
            # Извлекаем структуру документа
            document_structure = self._extract_document_structure(text)
            logger.info(f"📝 [CHUNKING] Extracted structure: {len(document_structure['chapters'])} chapters, {len(document_structure['sections'])} sections")
            
            # Создаем иерархические чанки
            hierarchical_chunks = self._create_hierarchical_chunks(text, document_structure, config)
            
            if not hierarchical_chunks:
                logger.warning("⚠️ [CHUNKING] No hierarchical chunks created, using fallback")
                return self._simple_split_into_chunks(text, chunk_size)
            
            logger.info(f"✅ [CHUNKING] Created {len(hierarchical_chunks)} hierarchical chunks")
            return hierarchical_chunks
            
        except Exception as e:
            logger.error(f"❌ [HIERARCHICAL_CHUNKS] Error creating hierarchical chunks: {e}")
            import traceback
            logger.error(f"❌ [HIERARCHICAL_CHUNKS] Traceback: {traceback.format_exc()}")
            # Fallback к простому разбиению
            return self._simple_split_into_chunks(text, chunk_size)

    def _standard_chunking(self, text: str, config: dict) -> List[str]:
        """Стандартное чанкование без иерархии"""
        try:
            # Параметры гранулярного чанкования из конфигурации
            target_tokens = config['target_tokens']
            min_tokens = config['min_tokens']
            max_tokens = config['max_tokens']
            overlap_ratio = config['overlap_ratio']
            
            logger.info(f"📝 [STANDARD_CHUNKING] Using config: target={target_tokens}, min={min_tokens}, max={max_tokens}, overlap={overlap_ratio}")
            
            # Разбиваем текст на предложения
            sentences = self._split_into_sentences(text, config)
            logger.info(f"📝 [STANDARD_CHUNKING] Split into {len(sentences)} sentences")
            
            if not sentences:
                logger.warning("⚠️ [STANDARD_CHUNKING] No sentences found, using fallback")
                return self._simple_split_into_chunks(text, 1000)
            
            chunks = []
            current_chunk = []
            current_tokens = 0
            
            # Обрабатываем каждое предложение
            for i, sentence in enumerate(sentences):
                sentence_tokens = self._estimate_tokens(sentence, config)
                
                # Проверяем, нужно ли начать новый чанк
                if current_tokens + sentence_tokens > max_tokens and current_chunk:
                    # Создаем чанк
                    chunk_text = ' '.join(current_chunk)
                    chunks.append(chunk_text.strip())
                    
                    # Начинаем новый чанк с перекрытием
                    overlap_sentences = self._get_overlap_sentences(current_chunk, overlap_ratio, config)
                    current_chunk = overlap_sentences
                    current_tokens = sum(self._estimate_tokens(s, config) for s in overlap_sentences)
                
                # Добавляем предложение к текущему чанку
                current_chunk.append(sentence)
                current_tokens += sentence_tokens
                
                # Проверяем, достигли ли целевого размера
                if current_tokens >= target_tokens and current_tokens >= min_tokens:
                    # Создаем чанк
                    chunk_text = ' '.join(current_chunk)
                    chunks.append(chunk_text.strip())
                    
                    # Начинаем новый чанк с перекрытием
                    overlap_sentences = self._get_overlap_sentences(current_chunk, overlap_ratio, config)
                    current_chunk = overlap_sentences
                    current_tokens = sum(self._estimate_tokens(s, config) for s in overlap_sentences)
            
            # Добавляем последний чанк, если он не пустой
            if current_chunk and current_tokens >= min_tokens:
                chunk_text = ' '.join(current_chunk)
                chunks.append(chunk_text.strip())
            elif current_chunk:
                if chunks:
                    # Объединяем с последним чанком
                    last_chunk = chunks[-1]
                    merged_chunk = last_chunk + ' ' + ' '.join(current_chunk)
                    chunks[-1] = merged_chunk
                else:
                    # Если нет предыдущих чанков, создаем один
                    chunk_text = ' '.join(current_chunk)
                    chunks.append(chunk_text.strip())
            
            logger.info(f"✅ [STANDARD_CHUNKING] Created {len(chunks)} standard chunks")
            return chunks
            
        except Exception as e:
            logger.error(f"❌ [STANDARD_CHUNKING] Error in standard chunking: {e}")
            return self._simple_split_into_chunks(text, 1000)

    def _create_semantic_chunks(self, text: str, config: dict) -> List[str]:
        """Создание семантических чанков на основе смысла"""
        try:
            logger.info("📝 [SEMANTIC_CHUNKS] Creating semantic chunks with meaning-based analysis")
            
            # Параметры семантического чанкования
            target_tokens = config['target_tokens']
            min_tokens = config['min_tokens']
            max_tokens = config['max_tokens']
            overlap_ratio = config['overlap_ratio']
            semantic_threshold = config.get('semantic_similarity_threshold', 0.7)
            window_size = config.get('semantic_window_size', 3)
            topic_change_threshold = config.get('topic_change_threshold', 0.3)
            
            # Разбиваем текст на предложения
            sentences = self._split_into_sentences(text, config)
            logger.info(f"📝 [SEMANTIC_CHUNKS] Split into {len(sentences)} sentences")
            
            if not sentences:
                logger.warning("⚠️ [SEMANTIC_CHUNKS] No sentences found")
                return []
            
            # Анализируем семантическую структуру
            semantic_analysis = self._analyze_semantic_structure(sentences, config)
            
            # Определяем границы семантических блоков
            semantic_boundaries = self._find_semantic_boundaries(sentences, semantic_analysis, config)
            
            # Создаем семантические чанки
            semantic_chunks = self._create_chunks_from_semantic_boundaries(
                sentences, semantic_boundaries, config
            )
            
            # Применяем семантическое объединение близких чанков
            if config.get('semantic_merge_threshold', 0.85) > 0:
                semantic_chunks = self._merge_semantically_similar_chunks(semantic_chunks, config)
            
            logger.info(f"✅ [SEMANTIC_CHUNKS] Created {len(semantic_chunks)} semantic chunks")
            return semantic_chunks
            
        except Exception as e:
            logger.error(f"❌ [SEMANTIC_CHUNKS] Error creating semantic chunks: {e}")
            return []

    def _analyze_semantic_structure(self, sentences: List[str], config: dict) -> Dict[str, Any]:
        """Анализ семантической структуры текста"""
        try:
            from config.chunking_config import get_semantic_patterns
            import re
            
            patterns = get_semantic_patterns()
            
            analysis = {
                'topic_indicators': [],
                'coherence_indicators': [],
                'semantic_boundaries': [],
                'domain_keywords': [],
                'sentence_semantics': []
            }
            
            for i, sentence in enumerate(sentences):
                sentence_analysis = {
                    'index': i,
                    'text': sentence,
                    'topic_indicators': [],
                    'coherence_indicators': [],
                    'semantic_boundaries': [],
                    'domain_keywords': [],
                    'semantic_score': 0.0
                }
                
                # Анализируем индикаторы тем
                for pattern in patterns['topic_indicators']:
                    if re.search(pattern, sentence, re.IGNORECASE):
                        sentence_analysis['topic_indicators'].append(pattern)
                        analysis['topic_indicators'].append(i)
                
                # Анализируем индикаторы связности
                for pattern in patterns['coherence_indicators']:
                    if re.search(pattern, sentence, re.IGNORECASE):
                        sentence_analysis['coherence_indicators'].append(pattern)
                        analysis['coherence_indicators'].append(i)
                
                # Анализируем семантические границы
                for pattern in patterns['semantic_boundaries']:
                    if re.search(pattern, sentence, re.IGNORECASE):
                        sentence_analysis['semantic_boundaries'].append(pattern)
                        analysis['semantic_boundaries'].append(i)
                
                # Анализируем доменные ключевые слова
                for domain, domain_patterns in patterns['domain_specific'].items():
                    for pattern in domain_patterns:
                        if re.search(pattern, sentence, re.IGNORECASE):
                            sentence_analysis['domain_keywords'].append((domain, pattern))
                            analysis['domain_keywords'].append((i, domain, pattern))
                
                # Вычисляем семантический балл предложения
                sentence_analysis['semantic_score'] = self._calculate_semantic_score(sentence_analysis)
                
                analysis['sentence_semantics'].append(sentence_analysis)
            
            logger.info(f"📝 [SEMANTIC_ANALYSIS] Found {len(analysis['topic_indicators'])} topic indicators, {len(analysis['semantic_boundaries'])} boundaries")
            return analysis
            
        except Exception as e:
            logger.error(f"❌ [SEMANTIC_ANALYSIS] Error analyzing semantic structure: {e}")
            return {'sentence_semantics': []}

    def _calculate_semantic_score(self, sentence_analysis: Dict[str, Any]) -> float:
        """Вычисление семантического балла предложения"""
        try:
            score = 0.0
            
            # Баллы за различные индикаторы
            score += len(sentence_analysis['topic_indicators']) * 0.3
            score += len(sentence_analysis['coherence_indicators']) * 0.2
            score += len(sentence_analysis['semantic_boundaries']) * 0.4
            score += len(sentence_analysis['domain_keywords']) * 0.1
            
            # Нормализуем до 0-1
            return min(score, 1.0)
            
        except Exception as e:
            logger.error(f"❌ [SEMANTIC_SCORE] Error calculating semantic score: {e}")
            return 0.0

    def _find_semantic_boundaries(self, sentences: List[str], analysis: Dict[str, Any], config: dict) -> List[int]:
        """Поиск семантических границ в тексте"""
        try:
            boundaries = []
            window_size = config.get('semantic_window_size', 3)
            topic_change_threshold = config.get('topic_change_threshold', 0.3)
            
            # Добавляем границы на основе семантических индикаторов
            for boundary_idx in analysis['semantic_boundaries']:
                if boundary_idx not in boundaries:
                    boundaries.append(boundary_idx)
            
            # Анализируем изменения темы в скользящем окне
            for i in range(window_size, len(sentences) - window_size):
                # Вычисляем семантическое сходство в окне
                window_similarity = self._calculate_window_similarity(
                    sentences, i, window_size, analysis
                )
                
                # Если сходство ниже порога, это граница
                if window_similarity < topic_change_threshold:
                    if i not in boundaries:
                        boundaries.append(i)
            
            # Сортируем границы
            boundaries.sort()
            
            logger.info(f"📝 [SEMANTIC_BOUNDARIES] Found {len(boundaries)} semantic boundaries")
            return boundaries
            
        except Exception as e:
            logger.error(f"❌ [SEMANTIC_BOUNDARIES] Error finding semantic boundaries: {e}")
            return []

    def _calculate_window_similarity(self, sentences: List[str], center_idx: int, window_size: int, analysis: Dict[str, Any]) -> float:
        """Вычисление семантического сходства в окне"""
        try:
            # Получаем предложения в окне
            start_idx = max(0, center_idx - window_size)
            end_idx = min(len(sentences), center_idx + window_size + 1)
            
            window_sentences = sentences[start_idx:end_idx]
            
            if len(window_sentences) < 2:
                return 1.0
            
            # Простой анализ сходства на основе ключевых слов
            similarity_scores = []
            
            for i in range(len(window_sentences) - 1):
                sent1 = window_sentences[i].lower()
                sent2 = window_sentences[i + 1].lower()
                
                # Извлекаем ключевые слова (простые существительные и прилагательные)
                words1 = set([w for w in sent1.split() if len(w) > 3 and w.isalpha()])
                words2 = set([w for w in sent2.split() if len(w) > 3 and w.isalpha()])
                
                if words1 and words2:
                    # Вычисляем коэффициент Жаккара
                    intersection = len(words1.intersection(words2))
                    union = len(words1.union(words2))
                    jaccard = intersection / union if union > 0 else 0.0
                    similarity_scores.append(jaccard)
            
            # Возвращаем среднее сходство
            return sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0.0
            
        except Exception as e:
            logger.error(f"❌ [WINDOW_SIMILARITY] Error calculating window similarity: {e}")
            return 0.0

    def _create_chunks_from_semantic_boundaries(self, sentences: List[str], boundaries: List[int], config: dict) -> List[str]:
        """Создание чанков на основе семантических границ"""
        try:
            chunks = []
            target_tokens = config['target_tokens']
            min_tokens = config['min_tokens']
            max_tokens = config['max_tokens']
            
            # Добавляем границы в начале и конце
            all_boundaries = [0] + boundaries + [len(sentences)]
            all_boundaries = sorted(list(set(all_boundaries)))
            
            for i in range(len(all_boundaries) - 1):
                start_idx = all_boundaries[i]
                end_idx = all_boundaries[i + 1]
                
                # Получаем предложения для чанка
                chunk_sentences = sentences[start_idx:end_idx]
                
                if not chunk_sentences:
                    continue
                
                # Создаем текст чанка
                chunk_text = ' '.join(chunk_sentences)
                chunk_tokens = self._estimate_tokens(chunk_text, config)
                
                # Проверяем размер чанка
                if chunk_tokens < min_tokens:
                    # Если чанк слишком мал, объединяем со следующим
                    if i + 2 < len(all_boundaries):
                        next_start = all_boundaries[i + 1]
                        next_end = all_boundaries[i + 2]
                        next_sentences = sentences[next_start:next_end]
                        chunk_sentences.extend(next_sentences)
                        chunk_text = ' '.join(chunk_sentences)
                        chunk_tokens = self._estimate_tokens(chunk_text, config)
                
                if chunk_tokens > max_tokens:
                    # Если чанк слишком большой, разбиваем на части
                    sub_chunks = self._split_large_chunk(chunk_sentences, config)
                    chunks.extend(sub_chunks)
                else:
                    chunks.append(chunk_text.strip())
            
            return chunks
            
        except Exception as e:
            logger.error(f"❌ [SEMANTIC_CHUNKS_CREATION] Error creating chunks from boundaries: {e}")
            return []

    def _split_large_chunk(self, sentences: List[str], config: dict) -> List[str]:
        """Разбиение большого чанка на меньшие части"""
        try:
            chunks = []
            target_tokens = config['target_tokens']
            max_tokens = config['max_tokens']
            
            current_chunk = []
            current_tokens = 0
            
            for sentence in sentences:
                sentence_tokens = self._estimate_tokens(sentence, config)
                
                if current_tokens + sentence_tokens > max_tokens and current_chunk:
                    # Создаем чанк
                    chunk_text = ' '.join(current_chunk)
                    chunks.append(chunk_text.strip())
                    
                    # Начинаем новый чанк
                    current_chunk = [sentence]
                    current_tokens = sentence_tokens
                else:
                    current_chunk.append(sentence)
                    current_tokens += sentence_tokens
            
            # Добавляем последний чанк
            if current_chunk:
                chunk_text = ' '.join(current_chunk)
                chunks.append(chunk_text.strip())
            
            return chunks
            
        except Exception as e:
            logger.error(f"❌ [SPLIT_LARGE_CHUNK] Error splitting large chunk: {e}")
            return []

    def _merge_semantically_similar_chunks(self, chunks: List[str], config: dict) -> List[str]:
        """Объединение семантически близких чанков"""
        try:
            merge_threshold = config.get('semantic_merge_threshold', 0.85)
            
            if len(chunks) <= 1:
                return chunks
            
            merged_chunks = []
            i = 0
            
            while i < len(chunks):
                current_chunk = chunks[i]
                merged_chunk = current_chunk
                
                # Проверяем сходство со следующими чанками
                j = i + 1
                while j < len(chunks):
                    next_chunk = chunks[j]
                    
                    # Вычисляем семантическое сходство
                    similarity = self._calculate_chunk_similarity(current_chunk, next_chunk)
                    
                    if similarity >= merge_threshold:
                        # Объединяем чанки
                        merged_chunk += ' ' + next_chunk
                        j += 1
                    else:
                        break
                
                merged_chunks.append(merged_chunk.strip())
                i = j
            
            logger.info(f"📝 [SEMANTIC_MERGE] Merged {len(chunks)} chunks into {len(merged_chunks)} chunks")
            return merged_chunks
            
        except Exception as e:
            logger.error(f"❌ [SEMANTIC_MERGE] Error merging similar chunks: {e}")
            return chunks

    def _calculate_chunk_similarity(self, chunk1: str, chunk2: str) -> float:
        """Вычисление семантического сходства между чанками"""
        try:
            # Простой анализ сходства на основе ключевых слов
            words1 = set([w.lower() for w in chunk1.split() if len(w) > 3 and w.isalpha()])
            words2 = set([w.lower() for w in chunk2.split() if len(w) > 3 and w.isalpha()])
            
            if not words1 or not words2:
                return 0.0
            
            # Вычисляем коэффициент Жаккара
            intersection = len(words1.intersection(words2))
            union = len(words1.union(words2))
            
            return intersection / union if union > 0 else 0.0
            
        except Exception as e:
            logger.error(f"❌ [CHUNK_SIMILARITY] Error calculating chunk similarity: {e}")
            return 0.0

    def _create_hierarchical_chunks(self, text: str, structure: Dict[str, Any], config: dict) -> List[str]:
        """Создание иерархических чанков с сохранением структуры"""
        try:
            logger.info("📝 [HIERARCHICAL_CHUNKS] Creating hierarchical chunks with structure preservation")
            
            # Параметры чанкования
            target_tokens = config['target_tokens']
            min_tokens = config['min_tokens']
            max_tokens = config['max_tokens']
            overlap_ratio = config['overlap_ratio']
            preserve_structure = config.get('preserve_structure', True)
            chapter_boundaries = config.get('chapter_boundaries', True)
            section_boundaries = config.get('section_boundaries', True)
            
            chunks = []
            
            # Если нет структуры, используем стандартное чанкование
            if not structure['chapters'] and not structure['sections']:
                logger.info("📝 [HIERARCHICAL_CHUNKS] No structure found, using standard chunking")
                return self._standard_chunking(text, config)
            
            # Разбиваем текст на предложения
            sentences = self._split_into_sentences(text, config)
            logger.info(f"📝 [HIERARCHICAL_CHUNKS] Split into {len(sentences)} sentences")
            
            if not sentences:
                logger.warning("⚠️ [HIERARCHICAL_CHUNKS] No sentences found")
                return []
            
            # Создаем карту предложений к структуре
            sentence_structure_map = self._map_sentences_to_structure(sentences, structure)
            
            # Группируем предложения по структурным единицам
            structural_units = self._group_sentences_by_structure(sentences, sentence_structure_map, structure)
            
            # Создаем чанки с учетом структуры
            for unit in structural_units:
                unit_chunks = self._create_chunks_for_structural_unit(unit, config)
                chunks.extend(unit_chunks)
            
            logger.info(f"✅ [HIERARCHICAL_CHUNKS] Created {len(chunks)} hierarchical chunks")
            return chunks
            
        except Exception as e:
            logger.error(f"❌ [HIERARCHICAL_CHUNKS] Error creating hierarchical chunks: {e}")
            return []

    def _map_sentences_to_structure(self, sentences: List[str], structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Создание карты предложений к структурным элементам"""
        try:
            sentence_map = []
            
            for i, sentence in enumerate(sentences):
                sentence_info = {
                    'index': i,
                    'text': sentence,
                    'chapter': None,
                    'section': None,
                    'subsection': None,
                    'paragraph': None,
                    'special_structure': None
                }
                
                # Определяем принадлежность к главе
                for chapter in structure['chapters']:
                    if chapter['title'].lower() in sentence.lower() or chapter['number'] in sentence:
                        sentence_info['chapter'] = chapter
                        break
                
                # Определяем принадлежность к разделу
                for section in structure['sections']:
                    if section['number'] in sentence or section['title'].lower() in sentence.lower():
                        sentence_info['section'] = section
                        break
                
                # Определяем принадлежность к абзацу
                for paragraph in structure['paragraphs']:
                    if paragraph['text'].lower() in sentence.lower():
                        sentence_info['paragraph'] = paragraph
                        break
                
                # Определяем принадлежность к специальной структуре
                for special in structure['special_structures']:
                    if special['text'].lower() in sentence.lower():
                        sentence_info['special_structure'] = special
                        break
                
                sentence_map.append(sentence_info)
            
            return sentence_map
            
        except Exception as e:
            logger.error(f"❌ [MAP_SENTENCES] Error mapping sentences to structure: {e}")
            return []

    def _group_sentences_by_structure(self, sentences: List[str], sentence_map: List[Dict[str, Any]], structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Группировка предложений по структурным единицам"""
        try:
            structural_units = []
            current_unit = None
            
            for i, sentence_info in enumerate(sentence_map):
                # Определяем текущую структурную единицу
                current_chapter = sentence_info.get('chapter')
                current_section = sentence_info.get('section')
                current_paragraph = sentence_info.get('paragraph')
                current_special = sentence_info.get('special_structure')
                
                # Проверяем, нужно ли начать новую структурную единицу
                should_start_new_unit = False
                
                if current_unit is None:
                    should_start_new_unit = True
                elif current_chapter and current_chapter != current_unit.get('chapter'):
                    should_start_new_unit = True
                elif current_section and current_section != current_unit.get('section'):
                    should_start_new_unit = True
                elif current_special and current_special != current_unit.get('special_structure'):
                    should_start_new_unit = True
                
                if should_start_new_unit:
                    # Сохраняем предыдущую единицу
                    if current_unit:
                        structural_units.append(current_unit)
                    
                    # Начинаем новую единицу
                    current_unit = {
                        'chapter': current_chapter,
                        'section': current_section,
                        'paragraph': current_paragraph,
                        'special_structure': current_special,
                        'sentences': [sentence_info['text']],
                        'start_index': i,
                        'end_index': i
                    }
                else:
                    # Добавляем предложение к текущей единице
                    current_unit['sentences'].append(sentence_info['text'])
                    current_unit['end_index'] = i
            
            # Добавляем последнюю единицу
            if current_unit:
                structural_units.append(current_unit)
            
            logger.info(f"📝 [GROUP_SENTENCES] Created {len(structural_units)} structural units")
            return structural_units
            
        except Exception as e:
            logger.error(f"❌ [GROUP_SENTENCES] Error grouping sentences: {e}")
            return []

    def _create_chunks_for_structural_unit(self, unit: Dict[str, Any], config: dict) -> List[str]:
        """Создание чанков для структурной единицы"""
        try:
            sentences = unit['sentences']
            if not sentences:
                return []
            
            # Параметры чанкования
            target_tokens = config['target_tokens']
            min_tokens = config['min_tokens']
            max_tokens = config['max_tokens']
            overlap_ratio = config['overlap_ratio']
            
            chunks = []
            current_chunk = []
            current_tokens = 0
            
            # Обрабатываем предложения структурной единицы
            for sentence in sentences:
                sentence_tokens = self._estimate_tokens(sentence, config)
                
                # Проверяем, нужно ли начать новый чанк
                if current_tokens + sentence_tokens > max_tokens and current_chunk:
                    # Создаем чанк
                    chunk_text = ' '.join(current_chunk)
                    chunks.append(chunk_text.strip())
                    
                    # Начинаем новый чанк с перекрытием
                    overlap_sentences = self._get_overlap_sentences(current_chunk, overlap_ratio, config)
                    current_chunk = overlap_sentences
                    current_tokens = sum(self._estimate_tokens(s, config) for s in overlap_sentences)
                
                # Добавляем предложение к текущему чанку
                current_chunk.append(sentence)
                current_tokens += sentence_tokens
                
                # Проверяем, достигли ли целевого размера
                if current_tokens >= target_tokens and current_tokens >= min_tokens:
                    # Создаем чанк
                    chunk_text = ' '.join(current_chunk)
                    chunks.append(chunk_text.strip())
                    
                    # Начинаем новый чанк с перекрытием
                    overlap_sentences = self._get_overlap_sentences(current_chunk, overlap_ratio, config)
                    current_chunk = overlap_sentences
                    current_tokens = sum(self._estimate_tokens(s, config) for s in overlap_sentences)
            
            # Добавляем последний чанк, если он не пустой
            if current_chunk and current_tokens >= min_tokens:
                chunk_text = ' '.join(current_chunk)
                chunks.append(chunk_text.strip())
            elif current_chunk:
                if chunks:
                    # Объединяем с последним чанком
                    last_chunk = chunks[-1]
                    merged_chunk = last_chunk + ' ' + ' '.join(current_chunk)
                    chunks[-1] = merged_chunk
                else:
                    # Если нет предыдущих чанков, создаем один
                    chunk_text = ' '.join(current_chunk)
                    chunks.append(chunk_text.strip())
            
            return chunks
            
        except Exception as e:
            logger.error(f"❌ [CREATE_CHUNKS_FOR_UNIT] Error creating chunks for structural unit: {e}")
            return []

    def _create_structure_metadata(self, chunk_text: str, structure: Dict[str, Any], chunk_structure: Dict[str, str]) -> Dict[str, Any]:
        """Создание расширенных метаданных структуры для чанка"""
        try:
            metadata = {
                'hierarchy_level': 0,
                'chapter_info': None,
                'section_info': None,
                'subsection_info': None,
                'paragraph_info': None,
                'special_structure_info': None,
                'structural_context': [],
                'document_type': 'unknown'
            }
            
            # Определяем уровень иерархии
            if chunk_structure.get('chapter'):
                metadata['hierarchy_level'] = 1
            if chunk_structure.get('section'):
                metadata['hierarchy_level'] = 2
            
            # Ищем информацию о главе
            for chapter in structure.get('chapters', []):
                if chapter['title'].lower() in chunk_text.lower() or chapter['number'] in chunk_text:
                    metadata['chapter_info'] = {
                        'number': chapter['number'],
                        'title': chapter['title'],
                        'line': chapter.get('line', 0),
                        'level': chapter.get('level', 1)
                    }
                    break
            
            # Ищем информацию о разделе
            for section in structure.get('sections', []):
                if section['number'] in chunk_text or section['title'].lower() in chunk_text.lower():
                    metadata['section_info'] = {
                        'number': section['number'],
                        'title': section['title'],
                        'line': section.get('line', 0),
                        'level': section.get('level', 2),
                        'chapter': section.get('chapter')
                    }
                    break
            
            # Ищем информацию об абзаце
            for paragraph in structure.get('paragraphs', []):
                if paragraph['text'].lower() in chunk_text.lower():
                    metadata['paragraph_info'] = {
                        'text': paragraph['text'],
                        'line': paragraph.get('line', 0),
                        'section': paragraph.get('section'),
                        'chapter': paragraph.get('chapter')
                    }
                    break
            
            # Ищем информацию о специальной структуре
            for special in structure.get('special_structures', []):
                if special['text'].lower() in chunk_text.lower():
                    metadata['special_structure_info'] = {
                        'type': special['type'],
                        'number': special.get('number'),
                        'text': special['text'],
                        'line': special.get('line', 0)
                    }
                    break
            
            # Создаем контекст структуры
            structural_context = []
            if metadata['chapter_info']:
                structural_context.append(f"Глава {metadata['chapter_info']['number']}: {metadata['chapter_info']['title']}")
            if metadata['section_info']:
                structural_context.append(f"Раздел {metadata['section_info']['number']}: {metadata['section_info']['title']}")
            if metadata['paragraph_info']:
                structural_context.append(f"Абзац: {metadata['paragraph_info']['text'][:50]}...")
            if metadata['special_structure_info']:
                structural_context.append(f"{metadata['special_structure_info']['type']}: {metadata['special_structure_info']['text']}")
            
            metadata['structural_context'] = structural_context
            
            # Определяем тип документа по содержимому
            chunk_lower = chunk_text.lower()
            if any(keyword in chunk_lower for keyword in ['гост', 'государственный стандарт']):
                metadata['document_type'] = 'gost'
            elif any(keyword in chunk_lower for keyword in ['сп', 'свод правил']):
                metadata['document_type'] = 'sp'
            elif any(keyword in chunk_lower for keyword in ['снип', 'строительные нормы']):
                metadata['document_type'] = 'snip'
            elif any(keyword in chunk_lower for keyword in ['корпоративный', 'внутренний']):
                metadata['document_type'] = 'corporate'
            
            return metadata
            
        except Exception as e:
            logger.error(f"❌ [CREATE_STRUCTURE_METADATA] Error creating structure metadata: {e}")
            return {
                'hierarchy_level': 0,
                'chapter_info': None,
                'section_info': None,
                'subsection_info': None,
                'paragraph_info': None,
                'special_structure_info': None,
                'structural_context': [],
                'document_type': 'unknown'
            }

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
        """Извлечение общей структуры документа с улучшенной иерархией"""
        try:
            # Импортируем улучшенные паттерны
            from config.chunking_config import get_hierarchical_patterns
            
            structure = {
                'chapters': [],
                'sections': [],
                'paragraphs': [],
                'special_structures': [],
                'headers': []
            }
            
            # Получаем улучшенные паттерны
            patterns = get_hierarchical_patterns()
            chapter_patterns = patterns['chapters']
            section_patterns = patterns['sections']
            paragraph_patterns = patterns['paragraphs']
            special_patterns = patterns['special_structures']
            
            lines = text.split('\n')
            current_chapter = None
            current_section = None
            
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line:
                    continue
                
                # Проверяем паттерны глав
                for pattern in chapter_patterns:
                    match = re.match(pattern, line, re.IGNORECASE)
                    if match:
                        current_chapter = {
                            'number': match.group(1),
                            'title': match.group(2).strip(),
                            'line': line_num,
                            'level': 1
                        }
                        structure['chapters'].append(current_chapter)
                        current_section = None
                        break
                
                # Проверяем паттерны разделов
                for pattern in section_patterns:
                    match = re.match(pattern, line)
                    if match:
                        section_number = match.group(1)
                        section_title = match.group(2).strip()
                        
                        # Определяем уровень вложенности
                        level = len(section_number.split('.'))
                        
                        current_section = {
                            'number': section_number,
                            'title': section_title,
                            'line': line_num,
                            'level': level,
                            'chapter': current_chapter['number'] if current_chapter else None
                        }
                        structure['sections'].append(current_section)
                        break
                
                # Проверяем паттерны абзацев
                for pattern in paragraph_patterns:
                    match = re.match(pattern, line)
                    if match:
                        paragraph = {
                            'text': match.group(1).strip(),
                            'line': line_num,
                            'section': current_section['number'] if current_section else None,
                            'chapter': current_chapter['number'] if current_chapter else None
                        }
                        structure['paragraphs'].append(paragraph)
                        break
                
                # Проверяем специальные структуры
                for pattern in special_patterns:
                    match = re.match(pattern, line, re.IGNORECASE)
                    if match:
                        special = {
                            'type': 'table' if 'Таблица' in line else 'figure' if 'Рисунок' in line else 'appendix' if 'Приложение' in line else 'other',
                            'number': match.group(1) if match.groups() else None,
                            'line': line_num,
                            'text': line
                        }
                        structure['special_structures'].append(special)
                        break
            
            return structure
            
        except Exception as e:
            logger.error(f"❌ [EXTRACT_DOCUMENT_STRUCTURE] Error extracting document structure: {e}")
            return {'chapters': [], 'sections': [], 'paragraphs': [], 'special_structures': [], 'headers': []}
    
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
