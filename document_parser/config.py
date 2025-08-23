# Конфигурация проекта AI-NK
# Настройки лимитов и ограничений

# Лимиты для загрузки файлов
UPLOAD_LIMITS = {
    # Максимальный размер проверяемого документа (в байтах)
    "CHECKABLE_DOCUMENT_MAX_SIZE": 100 * 1024 * 1024,  # 100 МБ
    
    # Максимальный размер нормативного документа (в байтах)
    "NORMATIVE_DOCUMENT_MAX_SIZE": 200 * 1024 * 1024,  # 200 МБ
    
    # Максимальное количество страниц в документе
    "MAX_PAGES_PER_DOCUMENT": 1000,
    
    # Максимальное количество символов в тексте страницы
    "MAX_CHARS_PER_PAGE": 50000,
}

# Настройки обработки документов
PROCESSING_SETTINGS = {
    # Таймаут для обработки одной страницы (в секундах)
    "PAGE_PROCESSING_TIMEOUT": 300,
    
    # Таймаут для LLM запросов (в секундах)
    "LLM_REQUEST_TIMEOUT": 120,
    
    # Максимальное количество попыток для LLM запроса
    "LLM_MAX_RETRIES": 3,
    
    # Интервал между попытками (в секундах)
    "LLM_RETRY_INTERVAL": 5,
}

# Настройки базы данных
DATABASE_SETTINGS = {
    # Максимальное количество соединений в пуле
    "MAX_CONNECTIONS": 20,
    
    # Таймаут соединения (в секундах)
    "CONNECTION_TIMEOUT": 30,
}

# Настройки логирования
LOGGING_SETTINGS = {
    # Уровень логирования
    "LOG_LEVEL": "INFO",
    
    # Максимальный размер лог-файла (в байтах)
    "MAX_LOG_SIZE": 10 * 1024 * 1024,  # 10 МБ
    
    # Количество файлов логов для ротации
    "LOG_BACKUP_COUNT": 5,
}

# Настройки безопасности
SECURITY_SETTINGS = {
    # Разрешенные типы файлов
    "ALLOWED_FILE_TYPES": [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
        "text/plain",
        "image/jpeg",
        "image/png",
        "image/tiff"
    ],
    
    # Максимальное количество файлов в одной загрузке
    "MAX_FILES_PER_UPLOAD": 10,
}

# Функции для получения настроек
def get_upload_limit(limit_name: str) -> int:
    """Получение лимита загрузки по имени"""
    return UPLOAD_LIMITS.get(limit_name, 0)

def get_processing_setting(setting_name: str) -> int:
    """Получение настройки обработки по имени"""
    return PROCESSING_SETTINGS.get(setting_name, 0)

def get_database_setting(setting_name: str) -> int:
    """Получение настройки базы данных по имени"""
    return DATABASE_SETTINGS.get(setting_name, 0)

def get_logging_setting(setting_name: str) -> str:
    """Получение настройки логирования по имени"""
    return LOGGING_SETTINGS.get(setting_name, "INFO")

def get_security_setting(setting_name: str):
    """Получение настройки безопасности по имени"""
    return SECURITY_SETTINGS.get(setting_name, [])

# Константы для удобства использования
MAX_CHECKABLE_DOCUMENT_SIZE = get_upload_limit("CHECKABLE_DOCUMENT_MAX_SIZE")
MAX_NORMATIVE_DOCUMENT_SIZE = get_upload_limit("NORMATIVE_DOCUMENT_MAX_SIZE")
MAX_PAGES_PER_DOCUMENT = get_upload_limit("MAX_PAGES_PER_DOCUMENT")
PAGE_PROCESSING_TIMEOUT = get_processing_setting("PAGE_PROCESSING_TIMEOUT")
LLM_REQUEST_TIMEOUT = get_processing_setting("LLM_REQUEST_TIMEOUT")
