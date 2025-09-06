"""
Конфигурация логирования для VLLM сервиса
"""
import os
import logging
import logging.handlers
from datetime import datetime
import json

def setup_ollama_json_logging():
    """Настройка JSON логирования для Ollama"""
    
    # Создаем директорию для логов если её нет
    log_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    # Создаем логгер для Ollama JSON
    ollama_json_logger = logging.getLogger("ollama_json")
    ollama_json_logger.setLevel(logging.INFO)
    
    # Очищаем существующие обработчики
    ollama_json_logger.handlers.clear()
    
    # Создаем ротируемый обработчик файла
    json_log_file = os.path.join(log_dir, "ollama_requests.jsonl")
    json_handler = logging.handlers.RotatingFileHandler(
        json_log_file,
        maxBytes=50 * 1024 * 1024,  # 50MB
        backupCount=10,  # Храним 10 файлов
        mode='a',
        encoding='utf-8'
    )
    json_handler.setLevel(logging.INFO)
    
    # Создаем форматтер для JSON
    class JSONFormatter(logging.Formatter):
        def format(self, record):
            # Извлекаем данные из record
            log_data = {
                "timestamp": datetime.fromtimestamp(record.created).isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "request_id": getattr(record, 'request_id', None),
                "model": getattr(record, 'model', None),
                "request_data": getattr(record, 'request_data', None),
                "response_data": getattr(record, 'response_data', None),
                "metrics": getattr(record, 'metrics', None),
                "error": getattr(record, 'error', None)
            }
            return json.dumps(log_data, ensure_ascii=False, separators=(',', ':'))
    
    json_formatter = JSONFormatter()
    json_handler.setFormatter(json_formatter)
    ollama_json_logger.addHandler(json_handler)
    
    # Предотвращаем дублирование логов в родительских логгерах
    ollama_json_logger.propagate = False
    
    return ollama_json_logger

def setup_general_logging():
    """Настройка общего логирования"""
    
    # Создаем директорию для логов если её нет
    log_dir = os.path.join(os.path.dirname(__file__), "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    # Настройка основного логгера
    log_level = os.getenv("LOG_LEVEL", "INFO")
    
    # Создаем ротируемый обработчик для общих логов
    general_log_file = os.path.join(log_dir, "vllm_service.log")
    general_handler = logging.handlers.RotatingFileHandler(
        general_log_file,
        maxBytes=20 * 1024 * 1024,  # 20MB
        backupCount=5,  # Храним 5 файлов
        mode='a',
        encoding='utf-8'
    )
    general_handler.setLevel(getattr(logging, log_level.upper()))
    
    # Форматтер для общих логов
    general_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    general_handler.setFormatter(general_formatter)
    
    # Настраиваем корневой логгер
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    root_logger.addHandler(general_handler)
    
    # Также добавляем консольный вывод для разработки
    if os.getenv("LOG_TO_CONSOLE", "true").lower() == "true":
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, log_level.upper()))
        console_handler.setFormatter(general_formatter)
        root_logger.addHandler(console_handler)
    
    return root_logger

def get_log_stats():
    """Получение статистики логов"""
    log_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
    
    stats = {
        "log_directory": log_dir,
        "files": []
    }
    
    if os.path.exists(log_dir):
        for filename in os.listdir(log_dir):
            if filename.endswith(('.log', '.jsonl')):
                filepath = os.path.join(log_dir, filename)
                file_stats = os.stat(filepath)
                stats["files"].append({
                    "name": filename,
                    "size_bytes": file_stats.st_size,
                    "size_mb": round(file_stats.st_size / (1024 * 1024), 2),
                    "modified": datetime.fromtimestamp(file_stats.st_mtime).isoformat()
                })
    
    return stats

def cleanup_old_logs(days_to_keep=30):
    """Очистка старых логов"""
    import time
    
    log_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
    current_time = time.time()
    cutoff_time = current_time - (days_to_keep * 24 * 60 * 60)
    
    cleaned_files = []
    
    if os.path.exists(log_dir):
        for filename in os.listdir(log_dir):
            if filename.endswith(('.log', '.jsonl')):
                filepath = os.path.join(log_dir, filename)
                file_mtime = os.path.getmtime(filepath)
                
                if file_mtime < cutoff_time:
                    try:
                        os.remove(filepath)
                        cleaned_files.append(filename)
                    except Exception as e:
                        logging.error(f"Failed to remove old log file {filename}: {e}")
    
    return cleaned_files
