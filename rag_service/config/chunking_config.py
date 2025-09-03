"""
Конфигурация для гранулярного чанкования документов
"""

# Параметры гранулярного чанкования
CHUNKING_CONFIG = {
    # Размеры чанков в токенах
    'target_tokens': 800,      # Целевое количество токенов (среднее между min и max)
    'min_tokens': 512,         # Минимальное количество токенов
    'max_tokens': 1200,        # Максимальное количество токенов
    
    # Перекрытие между чанками
    'overlap_ratio': 0.2,      # Перекрытие между чанками (20%)
    'min_overlap_sentences': 1, # Минимальное количество предложений для перекрытия
    
    # Логика склейки чанков
    'merge_enabled': True,     # Включить логику склейки с заголовками
    'max_merged_tokens': 1200, # Максимальный размер объединенного чанка
    
    # Паттерны для разбиения на предложения
    'sentence_patterns': [
        r'[.!?]+(?=\s+[А-ЯЁ\d])',  # Обычные предложения
        r'[.!?]+(?=\s+\d+\.)',      # Перед номерами пунктов
        r'[.!?]+(?=\s+[А-ЯЁ]\s)',  # Перед заголовками
        r'[.!?]+(?=\s*$)'           # В конце текста
    ],
    
    # Минимальная длина предложения
    'min_sentence_length': 10,
    
    # Паттерны для определения заголовков
    'header_patterns': [
        'глава', 'раздел', 'часть', 'пункт', 'подпункт',
        'статья', 'параграф', 'абзац', 'подраздел'
    ],
    
    # Паттерны для определения незавершенных конструкций
    'unfinished_patterns': {
        'quotes': ['"', '«', '»'],           # Кавычки
        'brackets': ['(', '[', '{'],         # Скобки
        'lists': ['-', '•', '1.', '2.']     # Списки
    },
    
    # Эвристика для оценки токенов
    'tokens_per_char': 4,      # 1 токен ≈ 4 символа для русского текста
    
    # Fallback параметры
    'fallback_chunk_size': 1000,  # Размер чанка для fallback режима
    'enable_fallback': True        # Включить fallback режим
}

# Специфичные настройки для разных типов документов
DOCUMENT_TYPE_CONFIGS = {
    'gost': {
        'target_tokens': 600,      # ГОСТ документы - более мелкие чанки
        'min_tokens': 400,
        'max_tokens': 800,
        'overlap_ratio': 0.25,     # Больше перекрытия для точности
    },
    'sp': {
        'target_tokens': 800,      # СП документы - стандартный размер
        'min_tokens': 512,
        'max_tokens': 1200,
        'overlap_ratio': 0.2,
    },
    'snip': {
        'target_tokens': 1000,     # СНиП документы - крупные чанки
        'min_tokens': 600,
        'max_tokens': 1500,
        'overlap_ratio': 0.15,     # Меньше перекрытия
    },
    'corporate': {
        'target_tokens': 700,      # Корпоративные документы
        'min_tokens': 450,
        'max_tokens': 1000,
        'overlap_ratio': 0.2,
    }
}

def get_chunking_config(document_type: str = 'default') -> dict:
    """
    Получение конфигурации чанкования для конкретного типа документа
    
    Args:
        document_type: Тип документа ('gost', 'sp', 'snip', 'corporate', 'default')
    
    Returns:
        dict: Конфигурация чанкования
    """
    base_config = CHUNKING_CONFIG.copy()
    
    if document_type in DOCUMENT_TYPE_CONFIGS:
        # Объединяем базовую конфигурацию с типовой
        type_config = DOCUMENT_TYPE_CONFIGS[document_type]
        base_config.update(type_config)
    
    return base_config

def validate_chunking_config(config: dict) -> bool:
    """
    Валидация конфигурации чанкования
    
    Args:
        config: Конфигурация для валидации
    
    Returns:
        bool: True если конфигурация корректна
    """
    try:
        # Проверяем обязательные поля
        required_fields = ['target_tokens', 'min_tokens', 'max_tokens', 'overlap_ratio']
        for field in required_fields:
            if field not in config:
                return False
        
        # Проверяем логические ограничения
        if config['min_tokens'] >= config['max_tokens']:
            return False
        
        if config['target_tokens'] < config['min_tokens'] or config['target_tokens'] > config['max_tokens']:
            return False
        
        if config['overlap_ratio'] < 0 or config['overlap_ratio'] > 1:
            return False
        
        return True
        
    except Exception:
        return False

# Экспортируем основную конфигурацию
DEFAULT_CONFIG = get_chunking_config('default')
