import asyncio
import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import json
import time
from typing import Dict, Any

# Импортируем Keycloak middleware
try:
    from keycloak_middleware import keycloak_middleware
    KEYCLOAK_ENABLED = True
    print("🔑 [DEBUG] Gateway: Keycloak middleware loaded successfully")
except ImportError:
    KEYCLOAK_ENABLED = False
    print("⚠️ [WARNING] Gateway: Keycloak middleware not available, using fallback authentication")

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Конфигурация авторизации
def verify_token(authorization_header: str) -> bool:
    """Проверка токена авторизации"""
    print(f"🔍 [DEBUG] Gateway: verify_token called with: {authorization_header}")
    
    if not authorization_header:
        print(f"🔍 [DEBUG] Gateway: No authorization header provided")
        return False
    
    try:
        # Извлекаем токен из заголовка "Bearer <token>"
        if authorization_header.startswith("Bearer "):
            token = authorization_header[7:]  # Убираем "Bearer "
            print(f"🔍 [DEBUG] Gateway: Extracted token: {token[:20]}..." if len(token) > 20 else f"🔍 [DEBUG] Gateway: Extracted token: {token}")
            
            # Специальный токен для разработки
            if token == "disabled-auth":
                print(f"🔍 [DEBUG] Gateway: Development token 'disabled-auth' accepted")
                return True
            
            # Проверяем JWT токены от Keycloak
            if token.startswith("eyJ") and KEYCLOAK_ENABLED:
                try:
                    # Проверяем токен через Keycloak middleware
                    payload = keycloak_middleware.verify_token(token)
                    if payload:
                        print(f"🔍 [DEBUG] Gateway: Keycloak JWT token verified successfully for user: {payload.get('preferred_username')}")
                        return True
                    else:
                        print(f"🔍 [DEBUG] Gateway: Keycloak JWT token verification failed")
                        return False
                except Exception as e:
                    print(f"🔍 [DEBUG] Gateway: Keycloak JWT token verification error: {e}")
                    return False
            
            # Fallback для JWT токенов без Keycloak
            if token.startswith("eyJ"):
                print(f"🔍 [DEBUG] Gateway: JWT token detected and accepted (fallback): {token[:20]}...")
                return True
            
            print(f"🔍 [DEBUG] Gateway: Token not valid JWT: {token}")
            return False
        else:
            print(f"🔍 [DEBUG] Gateway: Authorization header doesn't start with 'Bearer ': {authorization_header}")
            return False
    except Exception as e:
        print(f"🔍 [DEBUG] Gateway: Token verification error: {e}")
        logger.error(f"Token verification error: {e}")
        return False

app = FastAPI(title="AI-Engineering Gateway", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Конфигурация сервисов
SERVICES = {
    "document-parser": "http://document-parser:8001",
    "rag-service": "http://rag-service:8003",
    "rule-engine": "http://rule-engine:8004",
    "calculation-service": "http://calculation-service:8002",
    "outgoing-control-service": "http://outgoing-control-service:8006",
    "spellchecker-service": "http://spellchecker-service:8007",
    "archive-service": "http://archive-service:8008",
    "analog-objects-service": "http://analog-objects-service:8009",
    "normcontrol2-service": "http://normcontrol2-service:8010",
    "ollama": "http://host.docker.internal:11434",  # Прямое подключение к Ollama
    "vllm": "http://vllm:8005"  # VLLM сервис в контейнере
}

print("🔍 [DEBUG] Gateway: Starting with services configuration:", SERVICES)

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    """Middleware для проверки авторизации"""
    print(f"🔍 [DEBUG] Gateway: Auth middleware - {request.method} {request.url.path}")
    
    # Отключаем авторизацию для всех путей фронтенда
    public_paths = [
        "/health", 
        "/metrics", 
        "/api/health",             # Эндпоинт для проверки здоровья RAG-сервиса
        "/api/documents",          # Эндпоинт для получения списка документов
        "/api/documents/stats",    # Эндпоинт для статистики документов
        "/api/documents/",         # Эндпоинт для получения чанков документа (с слэшем)
        "/api/upload",             # Эндпоинт для загрузки документов
        "/api/calculation/token",  # Эндпоинт для получения JWT токена
        "/api/calculation/me",     # Эндпоинт для получения информации о пользователе
        "/api/calculations",       # Эндпоинт для расчетов (без авторизации)
        "/api/calculation/calculations",  # Эндпоинт для расчетов через calculation prefix
        "/api/calculations/degasification",  # Эндпоинт для расчетов дегазации
        "/api/calculation/calculations/degasification",  # Эндпоинт для расчетов дегазации через calculation prefix
        "/api/calculations/degasification/types",  # Эндпоинт для типов расчетов дегазации
        "/api/calculations/degasification/execute",  # Эндпоинт для выполнения расчетов дегазации
        "/api/chat/tags",          # Эндпоинт для проверки статуса Ollama
        "/api/chat/health",        # Эндпоинт для проверки здоровья Ollama
        "/api/chat",               # Эндпоинт для чата с ИИ
        "/api/generate",           # Эндпоинт для генерации текста
        "/api/ntd-consultation/chat",  # Эндпоинт для консультации НТД
        "/api/ntd-consultation/stats", # Эндпоинт для статистики консультаций
        "/api/ntd-consultation/cache", # Эндпоинт для управления кэшем
        "/api/ntd-consultation/cache/stats", # Эндпоинт для статистики кэша
        "/api/checkable-documents", # Эндпоинт для проверяемых документов
        "/api/settings",           # Эндпоинт для настроек
        "/api/upload/checkable",   # Эндпоинт для загрузки проверяемых документов
        "/api/rules",              # Эндпоинт для правил
        "/api/calculations",       # Эндпоинт для расчетов
        "/api/rag",                # Эндпоинт для RAG сервиса
        "/api/rag/reasoning-modes", # Эндпоинт для режимов рассуждения
        "/api/ollama",             # Эндпоинт для Ollama
        "/api/vllm",               # Эндпоинт для vLLM
        "/api/outgoing-control",   # Эндпоинт для выходного контроля
        "/api/outgoing-control/",  # Эндпоинт для выходного контроля с слэшем
        "/api/spellchecker",       # Эндпоинт для проверки орфографии
        "/api/spellchecker/",      # Эндпоинт для проверки орфографии с слэшем
        "/api/reindex-documents",  # Эндпоинт для реиндексации документов
        "/api/reindex-documents/async",  # Эндпоинт для асинхронной реиндексации
        "/api/reindex-documents/status",  # Эндпоинт для статуса реиндексации
        "/api/normcontrol2",       # Эндпоинт для Нормоконтроль - 2
        "/api/normcontrol2/"       # Эндпоинт для Нормоконтроль - 2 с слэшем
    ]
    
    print(f"🔍 [DEBUG] Gateway: Checking path '{request.url.path}' against public paths: {public_paths}")
    
    # Проверяем точное совпадение
    if request.url.path in public_paths:
        print(f"🔍 [DEBUG] Gateway: Skipping auth for exact match {request.url.path}")
        return await call_next(request)
    
    # Проверяем префиксы для API путей
    api_prefixes = [
        "/api/upload",
        "/api/documents",
        "/api/chat",
        "/api/generate", 
        "/api/ntd-consultation",
        "/api/checkable-documents",
        "/api/settings",
        "/api/rules",
        "/api/calculations",
        "/api/rag",
        "/api/ollama",
        "/api/vllm",
        "/api/outgoing-control",
        "/api/spellchecker",
        "/api/reindex-documents",
        "/api/normcontrol2"
    ]
    
    for prefix in api_prefixes:
        if request.url.path.startswith(prefix):
            print(f"🔍 [DEBUG] Gateway: Skipping auth for prefix match {request.url.path} (prefix: {prefix})")
            return await call_next(request)
    
    print(f"🔍 [DEBUG] Gateway: Path '{request.url.path}' not in public paths or prefixes")
    
    # Проверяем заголовок авторизации
    authorization_header = request.headers.get("authorization")
    print(f"🔍 [DEBUG] Gateway: Authorization header: {authorization_header}")
    
    if not verify_token(authorization_header):
        print(f"🔍 [DEBUG] Gateway: Authorization failed for {request.url.path}")
        return JSONResponse(
            content={"detail": "Ошибка проверки токена в Gateway"},
            status_code=401
        )
    
    print(f"🔍 [DEBUG] Gateway: Authorization successful for {request.url.path}")
    return await call_next(request)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware для логирования всех запросов"""
    start_time = time.time()
    
    print(f"🔍 [DEBUG] Gateway: Incoming request - {request.method} {request.url.path}")
    print(f"🔍 [DEBUG] Gateway: Request headers: {dict(request.headers)}")
    
    # Логируем тело запроса для отладки
    if request.method in ["POST", "PUT", "PATCH"]:
        try:
            body = await request.body()
            print(f"🔍 [DEBUG] Gateway: Request body length: {len(body)} bytes")
            if len(body) < 1000:  # Логируем только небольшие тела
                print(f"🔍 [DEBUG] Gateway: Request body preview: {body[:200]}...")
        except Exception as e:
            print(f"🔍 [DEBUG] Gateway: Error reading request body: {e}")
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    print(f"🔍 [DEBUG] Gateway: Request processed in {process_time:.3f}s - Status: {response.status_code}")
    
    return response

async def proxy_request(request: Request, service_url: str, path: str = "") -> JSONResponse:
    """Проксирование запроса к сервису с подробным логированием"""
    print(f"🔍 [DEBUG] Gateway: Proxying request to {service_url}{path}")
    
    # Определяем метод запроса
    method = request.method
    print(f"🔍 [DEBUG] Gateway: Request method: {method}")
    
    # Подготавливаем заголовки
    headers = dict(request.headers)
    print(f"🔍 [DEBUG] Gateway: Original headers: {headers}")
    
    # Удаляем заголовки, которые могут вызвать проблемы
    headers_to_remove = ["host", "content-length"]
    for header in headers_to_remove:
        headers.pop(header.lower(), None)
    
    print(f"🔍 [DEBUG] Gateway: Cleaned headers: {headers}")
    
    # Подготавливаем URL с query параметрами
    target_url = f"{service_url}{path}"
    if request.url.query:
        target_url += f"?{request.url.query}"
    print(f"🔍 [DEBUG] Gateway: Target URL: {target_url}")
    
    try:
        async with httpx.AsyncClient(timeout=600.0) as client:
            print(f"🔍 [DEBUG] Gateway: Creating httpx client with timeout 600s")
            
            # Обработка multipart/form-data
            if "multipart/form-data" in headers.get("content-type", ""):
                print(f"🔍 [DEBUG] Gateway: Processing multipart/form-data request")
                print(f"🔍 [DEBUG] Gateway: Content-Type: {headers.get('content-type', 'Not set')}")
                
                # Читаем тело запроса
                body = await request.body()
                print(f"🔍 [DEBUG] Gateway: Body length: {len(body)} bytes")
                
                # Отправляем запрос с телом
                response = await client.post(
                    target_url,
                    content=body,
                    headers=headers
                )
                print(f"🔍 [DEBUG] Gateway: Response status: {response.status_code}")
                print(f"🔍 [DEBUG] Gateway: Response headers: {dict(response.headers)}")
                
                # Логируем ответ
                try:
                    response_text = response.text
                    print(f"🔍 [DEBUG] Gateway: Response body length: {len(response_text)}")
                    if len(response_text) < 500:  # Логируем только небольшие ответы
                        print(f"🔍 [DEBUG] Gateway: Response body: {response_text}")
                    else:
                        print(f"🔍 [DEBUG] Gateway: Response body preview: {response_text[:200]}...")
                except Exception as e:
                    print(f"🔍 [DEBUG] Gateway: Error reading response body: {e}")
                
                return JSONResponse(
                    content=response.json() if response.headers.get("content-type", "").startswith("application/json") else {"detail": response.text},
                    status_code=response.status_code
                )
            else:
                # Обычная обработка для других типов запросов
                print(f"🔍 [DEBUG] Gateway: Processing regular request")
                
                # Читаем тело запроса
                body = await request.body()
                print(f"🔍 [DEBUG] Gateway: Body length: {len(body)} bytes")
                
                # Отправляем запрос
                response = await client.request(
                    method,
                    target_url,
                    content=body,
                    headers=headers
                )
                print(f"🔍 [DEBUG] Gateway: Response status: {response.status_code}")
                
                # Проверяем тип контента
                content_type = response.headers.get("content-type", "")
                print(f"🔍 [DEBUG] Gateway: Response content-type: {content_type}")
                
                # Для PDF, DOCX и других бинарных типов возвращаем Response
                if (content_type.startswith("application/pdf") or 
                    content_type.startswith("application/octet-stream") or
                    content_type.startswith("application/vnd.openxmlformats-officedocument")):
                    print(f"🔍 [DEBUG] Gateway: Returning binary response for content-type: {content_type}")
                    from fastapi.responses import Response
                    return Response(
                        content=response.content,
                        media_type=content_type,
                        headers=dict(response.headers)
                    )
                else:
                    # Для JSON и текстовых ответов возвращаем JSONResponse
                    return JSONResponse(
                        content=response.json() if content_type.startswith("application/json") else {"detail": response.text},
                        status_code=response.status_code
                    )
                
    except httpx.ConnectError as e:
        print(f"🔍 [DEBUG] Gateway: Connection error to {service_url}: {e}")
        return JSONResponse(
            content={"detail": f"Service unavailable: {str(e)}"},
            status_code=503
        )
    except httpx.TimeoutException as e:
        print(f"🔍 [DEBUG] Gateway: Timeout error to {service_url}: {e}")
        return JSONResponse(
            content={"detail": f"Request timeout: {str(e)}"},
            status_code=504
        )
    except Exception as e:
        print(f"🔍 [DEBUG] Gateway: Unexpected error: {e}")
        return JSONResponse(
            content={"detail": f"Proxy error: {str(e)}"},
            status_code=500
        )

# Analog Objects Service endpoints (должен быть перед /api/v1/{path:path})
@app.api_route("/api/analog-objects", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def analog_objects_root_proxy(request: Request):
    """Проксирование запросов к корневому пути сервиса объектов аналогов"""
    print(f"🔍 [DEBUG] Gateway: Analog objects root proxy request")
    
    try:
        # Получаем URL сервиса объектов аналогов
        service_url = SERVICES.get("analog-objects-service")
        if not service_url:
            raise HTTPException(status_code=503, detail="Analog objects service not available")
        
        # Формируем полный URL
        full_url = f"{service_url}/api/analog-objects"
        
        # Получаем тело запроса
        body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            body = await request.body()
        
        # Получаем заголовки
        headers = dict(request.headers)
        
        # Удаляем заголовки, которые могут вызвать проблемы
        headers_to_remove = ["host", "content-length"]
        for header in headers_to_remove:
            headers.pop(header, None)
        
        print(f"🔍 [DEBUG] Gateway: Forwarding to {full_url}")
        
        # Выполняем запрос к сервису объектов аналогов
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.request(
                method=request.method,
                url=full_url,
                headers=headers,
                content=body,
                params=request.query_params
            )
            
            print(f"🔍 [DEBUG] Gateway: Analog objects service response: {response.status_code}")
            
            # Возвращаем ответ
            if response.headers.get("content-type", "").startswith("application/json"):
                return JSONResponse(
                    content=response.json(),
                    status_code=response.status_code,
                    headers=dict(response.headers)
                )
            else:
                from fastapi.responses import Response
                return Response(
                    content=response.content,
                    status_code=response.status_code,
                    headers=dict(response.headers)
                )
            
    except httpx.TimeoutException:
        print(f"🔍 [DEBUG] Gateway: Analog objects service timeout")
        raise HTTPException(status_code=504, detail="Analog objects service timeout")
    except httpx.ConnectError:
        print(f"🔍 [DEBUG] Gateway: Analog objects service connection error")
        raise HTTPException(status_code=503, detail="Analog objects service unavailable")
    except Exception as e:
        print(f"🔍 [DEBUG] Gateway: Analog objects proxy exception: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.api_route("/api/analog-objects/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def analog_objects_proxy(path: str, request: Request):
    """Проксирование запросов к сервису объектов аналогов"""
    print(f"🔍 [DEBUG] Gateway: Analog objects proxy request to path: {path}")
    
    try:
        # Получаем URL сервиса объектов аналогов
        service_url = SERVICES.get("analog-objects-service")
        if not service_url:
            raise HTTPException(status_code=503, detail="Analog objects service not available")
        
        # Формируем полный URL
        full_url = f"{service_url}/api/analog-objects/{path}"
        
        # Получаем тело запроса
        body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            body = await request.body()
        
        # Получаем заголовки
        headers = dict(request.headers)
        
        # Удаляем заголовки, которые могут вызвать проблемы
        headers_to_remove = ["host", "content-length"]
        for header in headers_to_remove:
            headers.pop(header, None)
        
        print(f"🔍 [DEBUG] Gateway: Forwarding to {full_url}")
        
        # Выполняем запрос к сервису объектов аналогов
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.request(
                method=request.method,
                url=full_url,
                headers=headers,
                content=body,
                params=request.query_params
            )
            
            print(f"🔍 [DEBUG] Gateway: Analog objects service response: {response.status_code}")
            
            # Возвращаем ответ
            if response.headers.get("content-type", "").startswith("application/json"):
                return JSONResponse(
                    content=response.json(),
                    status_code=response.status_code,
                    headers=dict(response.headers)
                )
            else:
                from fastapi.responses import Response
                return Response(
                    content=response.content,
                    status_code=response.status_code,
                    headers=dict(response.headers)
                )
            
    except httpx.TimeoutException:
        print(f"🔍 [DEBUG] Gateway: Analog objects service timeout")
        raise HTTPException(status_code=504, detail="Analog objects service timeout")
    except httpx.ConnectError:
        print(f"🔍 [DEBUG] Gateway: Analog objects service connection error")
        raise HTTPException(status_code=503, detail="Analog objects service unavailable")
    except Exception as e:
        print(f"🔍 [DEBUG] Gateway: Analog objects proxy exception: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Проксирование запросов к API v1 (должен быть перед /api/{path:path})
@app.api_route("/api/v1/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_api_v1(request: Request, path: str):
    """Проксирование запросов к API v1"""
    print(f"🔍 [DEBUG] Gateway: API v1 route called with path: {path}")
    
    # Определяем сервис на основе пути
    if path.startswith("documents"):
        service_url = SERVICES["rag-service"]
        print(f"🔍 [DEBUG] Gateway: Routing API v1 to rag-service: {service_url}")
        return await proxy_request(request, service_url, f"/{path}")
    elif path.startswith("checkable-documents"):
        service_url = SERVICES["document-parser"]
        print(f"🔍 [DEBUG] Gateway: Routing API v1 to document-parser: {service_url}")
        return await proxy_request(request, service_url, f"/{path}")
    elif path.startswith("calculations") or path.startswith("calculation"):
        service_url = SERVICES["calculation-service"]
        print(f"🔍 [DEBUG] Gateway: Routing API v1 to calculation-service: {service_url}")
        return await proxy_request(request, service_url, f"/{path}")
    elif path.startswith("rag"):
        service_url = SERVICES["rag-service"]
        print(f"🔍 [DEBUG] Gateway: Routing API v1 to rag-service: {service_url}")
        return await proxy_request(request, service_url, f"/{path}")
    else:
        # По умолчанию направляем к document-parser
        service_url = SERVICES["document-parser"]
        print(f"🔍 [DEBUG] Gateway: Routing API v1 to document-parser (default): {service_url}")
        return await proxy_request(request, service_url, f"/{path}")


# API Health check endpoint (должен быть перед общим /api/{path:path})
@app.get("/api/health")
async def api_health_check():
    """Проверка здоровья API через RAG service"""
    print("🔍 [DEBUG] Gateway: API Health check requested")
    
    try:
        # Проверяем RAG service
        rag_service_url = SERVICES["rag-service"]
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{rag_service_url}/health")
            if response.status_code == 200:
                rag_health = response.json()
                health_status = {
                    "status": "healthy",
                    "service": "gateway",
                    "rag_service": rag_health,
                    "timestamp": time.time()
                }
            else:
                health_status = {
                    "status": "unhealthy",
                    "service": "gateway",
                    "rag_service": {"status": "unhealthy", "error": f"HTTP {response.status_code}"},
                    "timestamp": time.time()
                }
    except Exception as e:
        health_status = {
            "status": "unhealthy",
            "service": "gateway",
            "rag_service": {"status": "unhealthy", "error": str(e)},
            "timestamp": time.time()
        }
    
    print(f"🔍 [DEBUG] Gateway: API Health check response: {health_status}")
    return health_status

# Проксирование запросов к document-parser
@app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_api(request: Request, path: str):
    """Проксирование API запросов к document-parser"""
    print(f"🔍 [DEBUG] Gateway: API route called with path: {path}")
    print(f"🔍 [DEBUG] Gateway: Full URL: {request.url}")
    
    # Определяем сервис на основе пути
    print(f"🔍 [DEBUG] Gateway: Checking path: '{path}'")
    
    # Проверяем новые endpoints отдельно
    if path.startswith("outgoing-control"):
        print(f"🔍 [DEBUG] Gateway: Routing outgoing-control to outgoing-control-service")
        service_url = SERVICES["outgoing-control-service"]
        # Убираем префикс outgoing-control из пути
        clean_path = path.replace("outgoing-control/", "")
        return await proxy_request(request, service_url, f"/{clean_path}")
    
    if path.startswith("spellchecker"):
        print(f"🔍 [DEBUG] Gateway: Routing spellchecker to spellchecker-service")
        service_url = SERVICES["spellchecker-service"]
        # Убираем префикс spellchecker из пути
        clean_path = path.replace("spellchecker/", "")
        return await proxy_request(request, service_url, f"/{clean_path}")
    
    if path.startswith("ollama/"):
        print(f"🔍 [DEBUG] Gateway: Routing ollama endpoint to document-parser with /api prefix")
        service_url = SERVICES["document-parser"]
        return await proxy_request(request, service_url, f"/api/{path}")
    
    if path.startswith("normcontrol/"):
        print(f"🔍 [DEBUG] Gateway: Routing normcontrol endpoint to document-parser with /api prefix")
        service_url = SERVICES["document-parser"]
        return await proxy_request(request, service_url, f"/api/{path}")
    
    if path.startswith("checkable-documents") or path.startswith("settings"):
        service_url = SERVICES["document-parser"]
        print(f"🔍 [DEBUG] Gateway: Routing to document-parser: {service_url}")
        return await proxy_request(request, service_url, f"/{path}")
    elif path.startswith("upload/checkable"):
        service_url = SERVICES["document-parser"]
        print(f"🔍 [DEBUG] Gateway: Routing upload/checkable to document-parser: {service_url}")
        return await proxy_request(request, service_url, f"/{path}")
    elif path.startswith("upload"):
        service_url = SERVICES["rag-service"]
        print(f"🔍 [DEBUG] Gateway: Routing upload to rag-service: {service_url}")
        return await proxy_request(request, service_url, f"/{path}")
    elif path.startswith("documents"):
        service_url = SERVICES["rag-service"]
        print(f"🔍 [DEBUG] Gateway: Routing to rag-service: {service_url}")
        return await proxy_request(request, service_url, f"/{path}")
    elif path.startswith("reindex-documents") or path.startswith("reindex"):
        service_url = SERVICES["rag-service"]
        print(f"🔍 [DEBUG] Gateway: Routing reindex to rag-service: {service_url}")
        # Преобразуем путь для RAG сервиса
        if path == "reindex-documents":
            clean_path = "reindex"
        elif path == "reindex-documents/async":
            clean_path = "reindex/async"
        elif path.startswith("reindex-documents/status/"):
            task_id = path.replace("reindex-documents/status/", "")
            clean_path = f"reindex/status/{task_id}"
        else:
            clean_path = path.replace("reindex-documents", "reindex")
        print(f"🔍 [DEBUG] Gateway: Cleaned path for RAG service: {clean_path}")
        return await proxy_request(request, service_url, f"/{clean_path}")
    elif path.startswith("ntd-consultation"):
        service_url = SERVICES["rag-service"]
        print(f"🔍 [DEBUG] Gateway: Routing NTD consultation to rag-service: {service_url}")
        return await proxy_request(request, service_url, f"/{path}")
    elif path.startswith("rag/"):
        service_url = SERVICES["rag-service"]
        # Убираем префикс "rag/" из пути
        path = path[4:]  # Убираем "rag/"
        print(f"🔍 [DEBUG] Gateway: Routing to rag-service: {service_url} with path: {path}")
        return await proxy_request(request, service_url, f"/{path}")
    elif path.startswith("rules"):
        service_url = SERVICES["rule-engine"]
        print(f"🔍 [DEBUG] Gateway: Routing to rule-engine: {service_url}")
        return await proxy_request(request, service_url, f"/{path}")
    elif path.startswith("calculations") or path.startswith("calculation"):
        service_url = SERVICES["calculation-service"]
        print(f"🔍 [DEBUG] Gateway: Routing to calculation-service: {service_url}")
        # Убираем префикс "calculation/" из пути, если он есть
        if path.startswith("calculation/"):
            path = path[12:]  # Убираем "calculation/"
        print(f"🔍 [DEBUG] Gateway: Proxying request to {service_url}/{path}")
        return await proxy_request(request, service_url, f"/{path}")
    elif path.startswith("chat/health"):
        service_url = SERVICES["vllm"]
        print(f"🔍 [DEBUG] Gateway: Routing chat/health to vllm service: {service_url}")
        return await proxy_request(request, service_url, "/health")
    elif path.startswith("chat/tags"):
        service_url = SERVICES["vllm"]
        print(f"🔍 [DEBUG] Gateway: Routing chat/tags to vllm service: {service_url}")
        return await proxy_request(request, service_url, "/models")
    elif path.startswith("chat") or path.startswith("generate"):
        service_url = SERVICES["vllm"]
        print(f"🔍 [DEBUG] Gateway: Routing to vllm service: {service_url} with path: {path}")
        # Для чата передаем путь без префикса api/
        clean_path = path.replace("api/", "") if path.startswith("api/") else path
        return await proxy_request(request, service_url, f"/{clean_path}")
    elif path.startswith("normcontrol2"):
        service_url = SERVICES["normcontrol2-service"]
        print(f"🔍 [DEBUG] Gateway: Routing normcontrol2 to service: {service_url}")
        # Убираем префикс api/ если есть, но оставляем normcontrol2
        clean_path = path.replace("api/", "") if path.startswith("api/") else path
        return await proxy_request(request, service_url, f"/{clean_path}")
    else:
        print(f"🔍 [DEBUG] Gateway: Unknown path, defaulting to document-parser")
        service_url = SERVICES["document-parser"]
        return await proxy_request(request, service_url, f"/{path}")

# Проксирование запросов к VLLM
@app.api_route("/v1/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_vllm(request: Request, path: str):
    """Проксирование запросов к VLLM"""
    print(f"🔍 [DEBUG] Gateway: VLLM route called with path: {path}")
    
    service_url = SERVICES["vllm"]
    return await proxy_request(request, service_url, f"/api/{path}")

# Проксирование запросов к Ollama API
@app.api_route("/ollama/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_ollama_api(request: Request, path: str):
    """Проксирование запросов к Ollama API"""
    print(f"🔍 [DEBUG] Gateway: Ollama API route called with path: {path}")
    
    service_url = SERVICES["ollama"]
    return await proxy_request(request, service_url, f"/{path}")

# Проксирование запросов к Calculation Service
@app.api_route("/calculation/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_calculation_api(request: Request, path: str):
    """Проксирование запросов к Calculation Service"""
    print(f"🔍 [DEBUG] Gateway: Calculation API route called with path: {path}")
    
    service_url = SERVICES["calculation-service"]
    # Убираем префикс "calculation/" из пути, если он есть
    if path.startswith("calculation/"):
        path = path[12:]  # Убираем "calculation/"
    print(f"🔍 [DEBUG] Gateway: Proxying request to {service_url}/{path}")
    return await proxy_request(request, service_url, f"/{path}")

# Основной роут для всех остальных путей
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_main(request: Request, path: str):
    """Основной роут для всех остальных путей"""
    print(f"🔍 [DEBUG] Gateway: Main route called with path: {path}")
    
    # Проверяем специальные случаи для outgoing-control
    if path.startswith("api/outgoing-control") or path.startswith("outgoing-control"):
        print(f"🔍 [DEBUG] Gateway: Detected outgoing-control path: {path}")
        service_url = SERVICES["outgoing-control-service"]
        print(f"🔍 [DEBUG] Gateway: Routing outgoing-control to service: {service_url}")
        # Убираем префикс api/ если есть, но оставляем outgoing-control
        clean_path = path.replace("api/", "") if path.startswith("api/") else path
        return await proxy_request(request, service_url, f"/{clean_path}")
    
    # Определяем сервис на основе пути
    if path == "metrics":
        # Используем собственный эндпоинт metrics
        return await metrics()
    elif path.startswith("checkable-documents") or path.startswith("settings"):
        service_url = SERVICES["document-parser"]
        print(f"🔍 [DEBUG] Gateway: Routing to document-parser: {service_url}")
        return await proxy_request(request, service_url, f"/{path}")
    elif path.startswith("upload/checkable"):
        service_url = SERVICES["document-parser"]
        print(f"🔍 [DEBUG] Gateway: Routing upload/checkable to document-parser: {service_url}")
        return await proxy_request(request, service_url, f"/{path}")
    elif path.startswith("upload"):
        service_url = SERVICES["rag-service"]
        print(f"🔍 [DEBUG] Gateway: Routing upload to rag-service: {service_url}")
        return await proxy_request(request, service_url, f"/{path}")
    elif path.startswith("documents"):
        service_url = SERVICES["rag-service"]
        print(f"🔍 [DEBUG] Gateway: Routing to rag-service: {service_url}")
        return await proxy_request(request, service_url, f"/{path}")
    elif path.startswith("reindex"):
        service_url = SERVICES["rag-service"]
        print(f"🔍 [DEBUG] Gateway: Routing reindex to rag-service: {service_url}")
        # Преобразуем путь для RAG сервиса
        if path == "reindex-documents":
            clean_path = "reindex"
        elif path == "reindex-documents/async":
            clean_path = "reindex/async"
        elif path.startswith("reindex-documents/status/"):
            task_id = path.replace("reindex-documents/status/", "")
            clean_path = f"reindex/status/{task_id}"
        else:
            clean_path = path.replace("reindex-documents", "reindex")
        print(f"🔍 [DEBUG] Gateway: Cleaned path for RAG service: {clean_path}")
        return await proxy_request(request, service_url, f"/{clean_path}")
    elif path.startswith("ntd-consultation"):
        service_url = SERVICES["rag-service"]
        print(f"🔍 [DEBUG] Gateway: Routing NTD consultation to rag-service: {service_url}")
        return await proxy_request(request, service_url, f"/{path}")
    elif path.startswith("rag/"):
        service_url = SERVICES["rag-service"]
        # Убираем префикс "rag/" из пути
        path = path[4:]  # Убираем "rag/"
        print(f"🔍 [DEBUG] Gateway: Routing to rag-service: {service_url} with path: {path}")
        return await proxy_request(request, service_url, f"/{path}")
    elif path.startswith("rules"):
        service_url = SERVICES["rule-engine"]
        print(f"🔍 [DEBUG] Gateway: Routing to rule-engine: {service_url}")
        return await proxy_request(request, service_url, f"/{path}")
    elif path.startswith("calculations") or path.startswith("calculation"):
        service_url = SERVICES["calculation-service"]
        print(f"🔍 [DEBUG] Gateway: Routing to calculation-service: {service_url}")
        return await proxy_request(request, service_url, f"/{path}")
    elif path.startswith("chat/health"):
        service_url = SERVICES["vllm"]
        print(f"🔍 [DEBUG] Gateway: Routing chat/health to vllm service: {service_url}")
        return await proxy_request(request, service_url, "/health")
    elif path.startswith("chat/tags"):
        service_url = SERVICES["vllm"]
        print(f"🔍 [DEBUG] Gateway: Routing chat/tags to vllm service: {service_url}")
        return await proxy_request(request, service_url, "/models")
    elif path.startswith("chat") or path.startswith("generate"):
        service_url = SERVICES["vllm"]
        print(f"🔍 [DEBUG] Gateway: Routing to vllm service: {service_url} with path: {path}")
        # Для чата передаем путь без префикса api/
        clean_path = path.replace("api/", "") if path.startswith("api/") else path
        return await proxy_request(request, service_url, f"/{clean_path}")
    elif path.startswith("outgoing-control") or path.startswith("api/outgoing-control"):
        service_url = SERVICES["outgoing-control-service"]
        print(f"🔍 [DEBUG] Gateway: Routing outgoing-control to service: {service_url}")
        # Убираем префикс api/ если есть, но оставляем outgoing-control
        clean_path = path.replace("api/", "") if path.startswith("api/") else path
        return await proxy_request(request, service_url, f"/{clean_path}")
    else:
        print(f"🔍 [DEBUG] Gateway: Unknown path, defaulting to document-parser")
        service_url = SERVICES["document-parser"]
        return await proxy_request(request, service_url, f"/{path}")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Проверка здоровья gateway"""
    print("🔍 [DEBUG] Gateway: Health check requested")
    
    health_status = {
        "status": "healthy",
        "service": "gateway",
        "timestamp": time.time()
    }
    
    print(f"🔍 [DEBUG] Gateway: Health check response: {health_status}")
    return health_status


# Metrics endpoint
@app.get("/metrics")
async def metrics():
    """Метрики gateway в формате Prometheus"""
    print("🔍 [DEBUG] Gateway: Metrics requested")
    
    # Формируем метрики в формате Prometheus
    metrics_lines = []
    
    # Базовые метрики gateway
    metrics_lines.append(f"# HELP gateway_up Gateway service is up")
    metrics_lines.append(f"# TYPE gateway_up gauge")
    metrics_lines.append(f"gateway_up 1")
    
    metrics_lines.append(f"# HELP gateway_uptime_seconds Gateway uptime in seconds")
    metrics_lines.append(f"# TYPE gateway_uptime_seconds gauge")
    metrics_lines.append(f"gateway_uptime_seconds {time.time()}")
    
    metrics_lines.append(f"# HELP gateway_requests_processed_total Total requests processed")
    metrics_lines.append(f"# TYPE gateway_requests_processed_total counter")
    metrics_lines.append(f"gateway_requests_processed_total 0")
    
    print(f"🔍 [DEBUG] Gateway: Metrics response generated")
    
    # Возвращаем метрики в формате Prometheus
    from fastapi.responses import Response
    return Response(
        content="\n".join(metrics_lines),
        media_type="text/plain; version=0.0.4; charset=utf-8"
    )

# VLLM Models endpoint
@app.get("/api/vllm/models")
async def get_vllm_models():
    """Получение списка моделей от VLLM сервиса"""
    print("🔍 [DEBUG] Gateway: VLLM models requested")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{SERVICES['vllm']}/models")
            if response.status_code == 200:
                models_data = response.json()
                print(f"🔍 [DEBUG] Gateway: VLLM models response: {models_data}")
                return models_data
            else:
                print(f"🔍 [DEBUG] Gateway: VLLM models error: {response.status_code}")
                return {"error": "VLLM service unavailable", "status": "error"}
    except Exception as e:
        print(f"🔍 [DEBUG] Gateway: VLLM models exception: {e}")
        return {"error": str(e), "status": "error"}

# Archive Service endpoints
@app.api_route("/api/archive/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def archive_proxy(path: str, request: Request):
    """Проксирование запросов к сервису архива"""
    print(f"🔍 [DEBUG] Gateway: Archive proxy request to path: {path}")
    
    try:
        # Получаем URL сервиса архива
        service_url = SERVICES.get("archive-service")
        if not service_url:
            raise HTTPException(status_code=503, detail="Archive service not available")
        
        # Формируем полный URL
        full_url = f"{service_url}/archive/{path}"
        
        # Получаем тело запроса
        body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            body = await request.body()
        
        # Получаем заголовки
        headers = dict(request.headers)
        
        # Удаляем заголовки, которые могут вызвать проблемы
        headers_to_remove = ["host", "content-length"]
        for header in headers_to_remove:
            headers.pop(header, None)
        
        print(f"🔍 [DEBUG] Gateway: Forwarding to {full_url}")
        
        # Выполняем запрос к сервису архива
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.request(
                method=request.method,
                url=full_url,
                headers=headers,
                content=body,
                params=request.query_params
            )
            
            print(f"🔍 [DEBUG] Gateway: Archive service response: {response.status_code}")
            
            # Возвращаем ответ
            if response.headers.get("content-type", "").startswith("application/json"):
                return JSONResponse(
                    content=response.json(),
                    status_code=response.status_code,
                    headers=dict(response.headers)
                )
            else:
                from fastapi.responses import Response
                return Response(
                    content=response.content,
                    status_code=response.status_code,
                    headers=dict(response.headers)
                )
            
    except httpx.TimeoutException:
        print(f"🔍 [DEBUG] Gateway: Archive service timeout")
        raise HTTPException(status_code=504, detail="Archive service timeout")
    except httpx.ConnectError:
        print(f"🔍 [DEBUG] Gateway: Archive service connection error")
        raise HTTPException(status_code=503, detail="Archive service unavailable")
    except Exception as e:
        print(f"🔍 [DEBUG] Gateway: Archive proxy exception: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# NormControl2 Service endpoints
@app.api_route("/api/normcontrol2/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def normcontrol2_proxy(path: str, request: Request):
    """Проксирование запросов к сервису Нормоконтроль - 2"""
    print(f"🔍 [DEBUG] Gateway: NormControl2 proxy request to path: {path}")
    
    try:
        # Получаем URL сервиса normcontrol2
        service_url = SERVICES.get("normcontrol2-service")
        if not service_url:
            raise HTTPException(status_code=503, detail="NormControl2 service not available")
        
        # Формируем полный URL
        full_url = f"{service_url}/normcontrol2/{path}"
        
        # Получаем тело запроса
        body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            body = await request.body()
        
        # Получаем заголовки
        headers = dict(request.headers)
        
        # Удаляем заголовки, которые могут вызвать проблемы
        headers_to_remove = ["host", "content-length"]
        for header in headers_to_remove:
            headers.pop(header, None)
        
        print(f"🔍 [DEBUG] Gateway: Forwarding to {full_url}")
        
        # Выполняем запрос к сервису normcontrol2
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.request(
                method=request.method,
                url=full_url,
                headers=headers,
                content=body,
                params=request.query_params
            )
            
            print(f"🔍 [DEBUG] Gateway: NormControl2 service response: {response.status_code}")
            
            # Возвращаем ответ
            if response.headers.get("content-type", "").startswith("application/json"):
                return JSONResponse(
                    content=response.json(),
                    status_code=response.status_code,
                    headers=dict(response.headers)
                )
            else:
                from fastapi.responses import Response
                return Response(
                    content=response.content,
                    status_code=response.status_code,
                    headers=dict(response.headers)
                )
            
    except httpx.TimeoutException:
        print(f"🔍 [DEBUG] Gateway: NormControl2 service timeout")
        raise HTTPException(status_code=504, detail="NormControl2 service timeout")
    except httpx.ConnectError:
        print(f"🔍 [DEBUG] Gateway: NormControl2 service connection error")
        raise HTTPException(status_code=503, detail="NormControl2 service unavailable")
    except Exception as e:
        print(f"🔍 [DEBUG] Gateway: NormControl2 proxy exception: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    print("🔍 [DEBUG] Gateway: Starting FastAPI application")
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8443)