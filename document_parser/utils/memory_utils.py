import psutil
import gc
import logging
from typing import Dict

logger = logging.getLogger(__name__)

def get_memory_usage() -> Dict[str, float]:
    """Получение информации об использовании памяти"""
    try:
        process = psutil.Process()
        memory_info = process.memory_info()
        memory_percent = process.memory_percent()
        
        return {
            "rss_mb": memory_info.rss / 1024 / 1024,  # RSS в МБ
            "vms_mb": memory_info.vms / 1024 / 1024,  # VMS в МБ
            "percent": memory_percent,  # Процент использования
            "available_mb": psutil.virtual_memory().available / 1024 / 1024  # Доступная память в МБ
        }
    except Exception as e:
        logger.error(f"Error getting memory usage: {e}")
        return {"error": str(e)}

def get_available_memory() -> float:
    """Получение доступной памяти в МБ"""
    try:
        return psutil.virtual_memory().available / 1024 / 1024
    except Exception as e:
        logger.error(f"Error getting available memory: {e}")
        return 0.0

def log_memory_usage(context: str = ""):
    """Логирование использования памяти"""
    try:
        memory_info = get_memory_usage()
        if "error" not in memory_info:
            logger.info(f"🔍 [DEBUG] DocumentParser: Memory usage {context}: "
                       f"RSS: {memory_info['rss_mb']:.1f}MB, "
                       f"VMS: {memory_info['vms_mb']:.1f}MB, "
                       f"Percent: {memory_info['percent']:.1f}%, "
                       f"Available: {memory_info['available_mb']:.1f}MB")
        else:
            logger.warning(f"🔍 [DEBUG] DocumentParser: Could not get memory usage {context}: {memory_info['error']}")
    except Exception as e:
        logger.error(f"Error in log_memory_usage: {e}")

def cleanup_memory():
    """Очистка памяти"""
    try:
        gc.collect()
        logger.info(f"🔍 [DEBUG] DocumentParser: Memory cleanup completed")
    except Exception as e:
        logger.error(f"Error in cleanup_memory: {e}")

def check_memory_pressure() -> bool:
    """Проверка давления на память"""
    try:
        memory_info = get_memory_usage()
        if "error" in memory_info:
            return False
        
        # Проверяем, если используется больше 80% памяти или доступно меньше 500MB
        if memory_info['percent'] > 80 or memory_info['available_mb'] < 500:
            logger.warning(f"🔍 [MEMORY] High memory pressure detected: "
                          f"Usage: {memory_info['percent']:.1f}%, "
                          f"Available: {memory_info['available_mb']:.1f}MB")
            return True
        return False
    except Exception as e:
        logger.error(f"Error checking memory pressure: {e}")
        return False
