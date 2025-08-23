"""
Keycloak JWT Middleware для Gateway
Обеспечивает проверку JWT токенов от Keycloak и передачу их в PostgreSQL
"""

import jwt
import requests
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, status
import json
import base64

class KeycloakMiddleware:
    def __init__(self, keycloak_url: str = "https://keycloak:8443", realm: str = "ai-nk"):
        self.keycloak_url = keycloak_url
        self.realm = realm
        self.public_key = None
        self._load_public_key()
    
    def _load_public_key(self):
        """Загружает публичный ключ из Keycloak"""
        try:
            # Получаем конфигурацию realm'а
            url = f"{self.keycloak_url}/realms/{self.realm}"
            response = requests.get(url, verify=False, timeout=10)
            response.raise_for_status()
            
            realm_config = response.json()
            
            # Получаем публичный ключ
            public_key_url = f"{self.keycloak_url}/realms/{self.realm}/protocol/openid-connect/certs"
            response = requests.get(public_key_url, verify=False, timeout=10)
            response.raise_for_status()
            
            keys = response.json()
            if 'keys' in keys and len(keys['keys']) > 0:
                # Берем первый ключ (обычно активный)
                key_data = keys['keys'][0]
                self.public_key = self._construct_public_key(key_data)
                print(f"🔑 [DEBUG] Keycloak: Public key loaded successfully")
            else:
                print(f"⚠️ [WARNING] Keycloak: No public keys found")
                
        except Exception as e:
            print(f"❌ [ERROR] Keycloak: Failed to load public key: {e}")
            # В случае ошибки используем None - токены не будут проверяться
            self.public_key = None
    
    def _construct_public_key(self, key_data: Dict[str, Any]) -> str:
        """Конструирует публичный ключ из данных Keycloak"""
        try:
            # Для RSA ключей
            if key_data.get('kty') == 'RSA':
                from cryptography.hazmat.primitives.asymmetric import rsa
                from cryptography.hazmat.primitives import serialization
                from cryptography.hazmat.backends import default_backend
                
                # Создаем публичный ключ из компонентов
                public_numbers = rsa.RSAPublicNumbers(
                    e=int.from_bytes(base64.urlsafe_b64decode(key_data['e'] + '=='), 'big'),
                    n=int.from_bytes(base64.urlsafe_b64decode(key_data['n'] + '=='), 'big')
                )
                public_key = public_numbers.public_key(backend=default_backend())
                
                # Экспортируем в PEM формат
                pem = public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                )
                return pem.decode('utf-8')
            else:
                print(f"⚠️ [WARNING] Keycloak: Unsupported key type: {key_data.get('kty')}")
                return None
                
        except Exception as e:
            print(f"❌ [ERROR] Keycloak: Failed to construct public key: {e}")
            return None
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Проверяет JWT токен от Keycloak"""
        try:
            if not self.public_key:
                print(f"⚠️ [WARNING] Keycloak: No public key available, skipping token verification")
                # Декодируем токен без проверки подписи
                payload = jwt.decode(token, options={"verify_signature": False})
                return payload
            
            # Проверяем токен с публичным ключом
            payload = jwt.decode(
                token,
                self.public_key,
                algorithms=['RS256'],
                audience='postgresql-client',
                issuer=f"{self.keycloak_url}/realms/{self.realm}"
            )
            
            print(f"✅ [DEBUG] Keycloak: Token verified successfully for user: {payload.get('preferred_username')}")
            return payload
            
        except jwt.ExpiredSignatureError:
            print(f"❌ [ERROR] Keycloak: Token expired")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired"
            )
        except jwt.InvalidTokenError as e:
            print(f"❌ [ERROR] Keycloak: Invalid token: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        except Exception as e:
            print(f"❌ [ERROR] Keycloak: Token verification error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token verification failed"
            )
    
    def extract_token_from_request(self, request: Request) -> Optional[str]:
        """Извлекает JWT токен из запроса"""
        # Проверяем заголовок Authorization
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header[7:]  # Убираем "Bearer "
        
        # Проверяем заголовок X-JWT-Token
        jwt_header = request.headers.get("X-JWT-Token")
        if jwt_header:
            return jwt_header
        
        return None
    
    def get_user_info(self, token: str) -> Dict[str, Any]:
        """Получает информацию о пользователе из токена"""
        payload = self.verify_token(token)
        if not payload:
            return {}
        
        return {
            "username": payload.get("preferred_username"),
            "email": payload.get("email"),
            "roles": payload.get("realm_access", {}).get("roles", []),
            "sub": payload.get("sub"),
            "exp": payload.get("exp")
        }
    
    def has_role(self, token: str, required_role: str) -> bool:
        """Проверяет, есть ли у пользователя требуемая роль"""
        user_info = self.get_user_info(token)
        roles = user_info.get("roles", [])
        return required_role in roles

# Создаем глобальный экземпляр middleware
keycloak_middleware = KeycloakMiddleware()
