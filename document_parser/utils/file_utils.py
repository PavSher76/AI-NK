import hashlib
import os
import tempfile
import logging
from typing import Tuple, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

def calculate_file_hash(file_content: bytes) -> str:
    """Вычисление SHA-256 хеша файла"""
    return hashlib.sha256(file_content).hexdigest()

def get_file_info(file_content: bytes, filename: str) -> Tuple[str, int, str]:
    """Получение информации о файле"""
    file_hash = calculate_file_hash(file_content)
    file_size = len(file_content)
    file_type = Path(filename).suffix.lower()
    
    return file_hash, file_size, file_type

def create_temp_file(file_content: bytes, suffix: str = "") -> str:
    """Создание временного файла"""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(file_content)
            temp_file_path = temp_file.name
            logger.debug(f"Created temporary file: {temp_file_path}")
            return temp_file_path
    except Exception as e:
        logger.error(f"Error creating temporary file: {e}")
        raise

def cleanup_temp_file(file_path: str):
    """Удаление временного файла"""
    try:
        if os.path.exists(file_path):
            os.unlink(file_path)
            logger.debug(f"Cleaned up temporary file: {file_path}")
    except Exception as e:
        logger.warning(f"Error cleaning up temporary file {file_path}: {e}")

def ensure_directory_exists(directory_path: str):
    """Создание директории, если она не существует"""
    try:
        Path(directory_path).mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured directory exists: {directory_path}")
    except Exception as e:
        logger.error(f"Error creating directory {directory_path}: {e}")
        raise

def get_safe_filename(filename: str) -> str:
    """Получение безопасного имени файла"""
    # Удаляем небезопасные символы
    safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"
    safe_filename = "".join(c for c in filename if c in safe_chars)
    
    # Ограничиваем длину
    if len(safe_filename) > 255:
        name, ext = os.path.splitext(safe_filename)
        safe_filename = name[:255-len(ext)] + ext
    
    return safe_filename or "unnamed_file"

def validate_file_size(file_size: int, max_size: int) -> bool:
    """Проверка размера файла"""
    if file_size > max_size:
        logger.warning(f"File size {file_size} exceeds maximum allowed size {max_size}")
        return False
    return True

def validate_file_type(file_type: str, allowed_types: list) -> bool:
    """Проверка типа файла"""
    if file_type.lower() not in [t.lower() for t in allowed_types]:
        logger.warning(f"File type {file_type} is not in allowed types {allowed_types}")
        return False
    return True
