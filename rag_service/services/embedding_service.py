import logging
import numpy as np
from typing import List
import requests
import os

# Настройка логирования
logger = logging.getLogger(__name__)
model_logger = logging.getLogger("model")

# Получаем URL Ollama из переменной окружения
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434")

class OllamaEmbeddingService:
    """Сервис для работы с эмбеддингами через Ollama BGE-M3"""
    
    def __init__(self, ollama_url: str = None):
        self.ollama_url = ollama_url or OLLAMA_URL
        self.model_name = "bge-m3"
        logger.info(f"🤖 [OLLAMA_EMBEDDING] Initialized with {self.model_name} at {self.ollama_url}")
    
    def create_embedding(self, text: str) -> List[float]:
        """Создание эмбеддинга для текста с использованием Ollama BGE-M3"""
        try:
            # Подготавливаем запрос к Ollama
            payload = {
                "model": self.model_name,
                "prompt": text,
                "options": {
                    "embedding_only": True
                }
            }
            
            # Отправляем запрос к Ollama
            response = requests.post(
                f"{self.ollama_url}/api/embeddings",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                embedding = result.get("embedding", [])
                
                if embedding:
                    # Нормализуем эмбеддинг
                    embedding_array = np.array(embedding)
                    normalized_embedding = embedding_array / np.linalg.norm(embedding_array)
                    
                    model_logger.info(f"✅ [EMBEDDING] Generated embedding for text: '{text[:100]}...'")
                    return normalized_embedding.tolist()
                else:
                    raise ValueError("Empty embedding received from Ollama")
            else:
                raise Exception(f"Ollama API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"❌ [EMBEDDING] Error creating embedding: {e}")
            raise e
