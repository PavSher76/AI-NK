"""
Конфигурация для calculation_service
"""
import os
from typing import Optional

# Настройки базы данных
DATABASE_URL: str = os.getenv(
    'DATABASE_URL', 
    'postgresql://norms_user:norms_password@localhost:5432/norms_db'
)

# Настройки JWT
JWT_SECRET_KEY: str = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
JWT_ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

# Настройки Qdrant
QDRANT_URL: str = os.getenv('QDRANT_URL', 'http://localhost:6333')
QDRANT_API_KEY: Optional[str] = os.getenv('QDRANT_API_KEY')

# Настройки сервера
HOST: str = os.getenv('HOST', '0.0.0.0')
PORT: int = int(os.getenv('PORT', '8002'))
DEBUG: bool = os.getenv('DEBUG', 'False').lower() == 'true'

# Настройки CORS
CORS_ORIGINS: list = [
    "http://localhost:3000",
    "http://localhost:3001", 
    "http://frontend:3000",
    "http://frontend:3001"
]

# Настройки логирования
LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'DEBUG')
LOG_FORMAT: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_FILE: str = 'calculation_service.log'

# Настройки расчетов
MAX_CALCULATION_RESULTS: int = 1000
CALCULATION_TIMEOUT: int = 300  # 5 минут

# Настройки файлов
MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
ALLOWED_FILE_TYPES: list = ['.docx', '.pdf', '.txt']
