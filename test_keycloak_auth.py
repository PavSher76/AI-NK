#!/usr/bin/env python3
"""
Тестовый скрипт для демонстрации работы с Keycloak аутентификацией
"""

import requests
import json
import jwt
from datetime import datetime

def test_keycloak_authentication():
    """Тестирует полный цикл аутентификации через Keycloak"""
    
    print("🔑 [TEST] Keycloak Authentication Test")
    print("=" * 50)
    
    # 1. Получаем токен от Keycloak
    print("1. Получение JWT токена от Keycloak...")
    try:
        token_response = requests.post(
            "https://localhost:8081/realms/ai-nk/protocol/openid-connect/token",
            data={
                "grant_type": "password",
                "client_id": "ai-nk-frontend",
                "username": "admin",
                "password": "admin"
            },
            verify=False,
            timeout=10
        )
        
        if token_response.status_code == 200:
            token_data = token_response.json()
            access_token = token_data["access_token"]
            print(f"✅ Токен получен успешно")
            print(f"   Тип: {token_data['token_type']}")
            print(f"   Время жизни: {token_data['expires_in']} секунд")
        else:
            print(f"❌ Ошибка получения токена: {token_response.status_code}")
            print(f"   Ответ: {token_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка подключения к Keycloak: {e}")
        return False
    
    # 2. Декодируем JWT токен (без проверки подписи для демонстрации)
    print("\n2. Анализ JWT токена...")
    try:
        # Декодируем токен без проверки подписи
        payload = jwt.decode(access_token, options={"verify_signature": False})
        
        print(f"✅ JWT токен декодирован успешно")
        print(f"   Пользователь: {payload.get('preferred_username')}")
        print(f"   Email: {payload.get('email')}")
        print(f"   Роли: {payload.get('realm_access', {}).get('roles', [])}")
        print(f"   Issuer: {payload.get('iss')}")
        print(f"   Audience: {payload.get('azp')}")
        print(f"   Истекает: {datetime.fromtimestamp(payload.get('exp', 0))}")
        
    except Exception as e:
        print(f"❌ Ошибка декодирования JWT: {e}")
        return False
    
    # 3. Тестируем доступ к API через Gateway
    print("\n3. Тестирование доступа к API через Gateway...")
    try:
        api_response = requests.get(
            "https://localhost/api/documents",
            headers={
                "Authorization": f"Bearer {access_token}"
            },
            verify=False,
            timeout=10
        )
        
        if api_response.status_code == 200:
            documents = api_response.json()
            print(f"✅ API доступен через JWT токен")
            print(f"   Получено документов: {len(documents.get('documents', []))}")
            
            # Показываем информацию о документах
            for doc in documents.get('documents', [])[:3]:  # Показываем первые 3
                print(f"   - {doc.get('original_filename', 'Unknown')} (ID: {doc.get('id')})")
                
        else:
            print(f"❌ Ошибка доступа к API: {api_response.status_code}")
            print(f"   Ответ: {api_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка подключения к API: {e}")
        return False
    
    # 4. Тестируем подключение к PostgreSQL с JWT токеном
    print("\n4. Тестирование подключения к PostgreSQL...")
    try:
        # Тестируем через document-parser
        db_response = requests.get(
            "https://localhost/api/checkable-documents",
            headers={
                "Authorization": f"Bearer {access_token}"
            },
            verify=False,
            timeout=10
        )
        
        if db_response.status_code == 200:
            checkable_docs = db_response.json()
            print(f"✅ Подключение к PostgreSQL через JWT токен успешно")
            print(f"   Получено проверяемых документов: {len(checkable_docs.get('documents', []))}")
        else:
            print(f"❌ Ошибка подключения к PostgreSQL: {db_response.status_code}")
            print(f"   Ответ: {db_response.text}")
            
    except Exception as e:
        print(f"❌ Ошибка подключения к PostgreSQL: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Тест Keycloak аутентификации завершен успешно!")
    return True

def test_user_roles():
    """Тестирует различные роли пользователей"""
    
    print("\n🔑 [TEST] User Roles Test")
    print("=" * 50)
    
    # Тестируем пользователя с ролью user
    print("1. Тестирование пользователя с ролью 'user'...")
    try:
        user_token_response = requests.post(
            "https://localhost:8081/realms/ai-nk/protocol/openid-connect/token",
            data={
                "grant_type": "password",
                "client_id": "ai-nk-frontend",
                "username": "user",
                "password": "password123"
            },
            verify=False,
            timeout=10
        )
        
        if user_token_response.status_code == 200:
            user_token_data = user_token_response.json()
            user_access_token = user_token_data["access_token"]
            
            # Декодируем токен
            user_payload = jwt.decode(user_access_token, options={"verify_signature": False})
            print(f"✅ Пользователь 'user' аутентифицирован")
            print(f"   Роли: {user_payload.get('realm_access', {}).get('roles', [])}")
            
            # Тестируем доступ к API
            user_api_response = requests.get(
                "https://localhost/api/documents",
                headers={
                    "Authorization": f"Bearer {user_access_token}"
                },
                verify=False,
                timeout=10
            )
            
            if user_api_response.status_code == 200:
                print(f"✅ Пользователь 'user' имеет доступ к API")
            else:
                print(f"❌ Пользователь 'user' не имеет доступа к API: {user_api_response.status_code}")
                
        else:
            print(f"❌ Ошибка аутентификации пользователя 'user': {user_token_response.status_code}")
            
    except Exception as e:
        print(f"❌ Ошибка тестирования ролей: {e}")

if __name__ == "__main__":
    # Основной тест аутентификации
    success = test_keycloak_authentication()
    
    if success:
        # Тест ролей пользователей
        test_user_roles()
    
    print("\n🎉 Тестирование завершено!")
