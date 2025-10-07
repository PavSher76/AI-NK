"""
Модуль аутентификации и авторизации
"""
import logging
from datetime import datetime, timedelta
from typing import Optional
import jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer

from config import JWT_SECRET_KEY, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from models import User, TokenData

logger = logging.getLogger(__name__)

# OAuth2 схема
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class AuthService:
    """Сервис аутентификации и авторизации"""
    
    def __init__(self):
        self.secret_key = JWT_SECRET_KEY
        self.algorithm = JWT_ALGORITHM
        self.access_token_expire_minutes = ACCESS_TOKEN_EXPIRE_MINUTES
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        """Создание JWT токена"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[TokenData]:
        """Проверка JWT токена"""
        try:
            # Специальный токен для разработки
            if token == "disabled-auth":
                logger.info("🔍 [AUTH] Development token 'disabled-auth' accepted")
                return TokenData(
                    username="disabled_user",
                    user_id="disabled",
                    role="engineer"
                )
            
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            username: str = payload.get("sub")
            user_id: str = payload.get("user_id")
            role: str = payload.get("role")
            if username is None:
                return None
            token_data = TokenData(username=username, user_id=user_id, role=role)
            return token_data
        except Exception:
            return None
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Аутентификация пользователя"""
        try:
            # В реальном приложении здесь будет проверка в базе данных
            # Пока используем заглушку
            if username == "test_user" and password == "test_password":
                return User(
                    id="1",
                    username=username,
                    email="test@example.com",
                    role="engineer",
                    permissions=["read", "write", "execute"]
                )
            return None
        except Exception as e:
            logger.error(f"🔍 [AUTH] Authentication error: {e}")
            return None
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Получение пользователя по ID"""
        try:
            # Специальный пользователь для разработки
            if user_id == "disabled":
                return User(
                    id=user_id,
                    username="disabled_user",
                    email="disabled@example.com",
                    role="engineer",
                    permissions=["read", "write", "execute"]
                )
            
            # В реальном приложении здесь будет запрос к базе данных
            # Пока используем заглушку
            if user_id == "1":
                return User(
                    id=user_id,
                    username="test_user",
                    email="test@example.com",
                    role="engineer",
                    permissions=["read", "write", "execute"]
                )
            return None
        except Exception as e:
            logger.error(f"🔍 [AUTH] Error getting user by ID: {e}")
            return None


# Инициализация сервиса авторизации
auth_service = AuthService()


# Зависимости для авторизации
async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Получение текущего пользователя из JWT токена"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        logger.info(f"🔍 [AUTH] Received token: {token}")
        token_data = auth_service.verify_token(token)
        if token_data is None:
            logger.error(f"🔍 [AUTH] Token verification failed for token: {token}")
            raise credentials_exception
        
        logger.info(f"🔍 [AUTH] Token verified successfully for user: {token_data.username}")
        user = auth_service.get_user_by_id(token_data.user_id)
        if user is None:
            logger.error(f"🔍 [AUTH] User not found for ID: {token_data.user_id}")
            raise credentials_exception
        
        logger.info(f"🔍 [AUTH] User found: {user.username}")
        return user
    except Exception as e:
        logger.error(f"🔍 [AUTH] Error getting current user: {e}")
        raise credentials_exception


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Получение активного пользователя"""
    if not current_user:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def require_permission(permission: str):
    """Декоратор для проверки разрешений"""
    def permission_checker(current_user: User = Depends(get_current_active_user)):
        if permission not in current_user.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required"
            )
        return current_user
    return permission_checker


# Зависимости для различных уровней доступа
require_read_permission = require_permission("read")
require_write_permission = require_permission("write")
require_execute_permission = require_permission("execute")
