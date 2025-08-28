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
VALID_TOKENS = ["test-token", "admin-token", "user-token", "demo-token"]

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
            
            # Проверяем простые токены (fallback)
            if token in VALID_TOKENS:
                print(f"🔍 [DEBUG] Gateway: Token matched VALID_TOKENS: {token}")
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
            
            print(f"🔍 [DEBUG] Gateway: Token not in VALID_TOKENS and not valid JWT: {token}")
            return False
        else:
            print(f"🔍 [DEBUG] Gateway: Authorization header doesn't start with 'Bearer ': {authorization_header}")
            return False
    except Exception as e:
        print(f"🔍 [DEBUG] Gateway: Token verification error: {e}")
        logger.error(f"Token verification error: {e}")
        return False

app = FastAPI(title="AI-NK Gateway", version="1.0.0")

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
    "ollama": "http://ollama:11434",
    "vllm": "http://vllm:8000"
}

print("🔍 [DEBUG] Gateway: Starting with services configuration:", SERVICES)

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    """Middleware для проверки авторизации"""
    print(f"🔍 [DEBUG] Gateway: Auth middleware - {request.method} {request.url.path}")
    
    # Пропускаем health check и metrics без авторизации
    if request.url.path in ["/health", "/metrics"]:
        print(f"🔍 [DEBUG] Gateway: Skipping auth for {request.url.path}")
        return await call_next(request)
    
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
    
    # Подготавливаем URL
    target_url = f"{service_url}{path}"
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

# Проксирование запросов к API v1 (должен быть перед /api/{path:path})
@app.api_route("/api/v1/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_api_v1(request: Request, path: str):
    """Проксирование запросов к API v1"""
    print(f"🔍 [DEBUG] Gateway: API v1 route called with path: {path}")
    
    # Определяем сервис на основе пути
    if path.startswith("documents") or path.startswith("checkable-documents"):
        service_url = SERVICES["document-parser"]
        print(f"🔍 [DEBUG] Gateway: Routing API v1 to document-parser: {service_url}")
        return await proxy_request(request, service_url, f"/{path}")
    elif path.startswith("calculations"):
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

# Проксирование запросов к document-parser
@app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_api(request: Request, path: str):
    """Проксирование API запросов к document-parser"""
    print(f"🔍 [DEBUG] Gateway: API route called with path: {path}")
    print(f"🔍 [DEBUG] Gateway: Full URL: {request.url}")
    
    # Определяем сервис на основе пути
    print(f"🔍 [DEBUG] Gateway: Checking path: '{path}'")
    
    # Проверяем новые endpoints отдельно
    if path.startswith("ollama/"):
        print(f"🔍 [DEBUG] Gateway: Routing ollama endpoint to document-parser with /api prefix")
        service_url = SERVICES["document-parser"]
        return await proxy_request(request, service_url, f"/api/{path}")
    
    if path.startswith("normcontrol/"):
        print(f"🔍 [DEBUG] Gateway: Routing normcontrol endpoint to document-parser with /api prefix")
        service_url = SERVICES["document-parser"]
        return await proxy_request(request, service_url, f"/api/{path}")
    
    if path.startswith("upload") or path.startswith("documents") or path.startswith("checkable-documents") or path.startswith("settings"):
        service_url = SERVICES["document-parser"]
        print(f"🔍 [DEBUG] Gateway: Routing to document-parser: {service_url}")
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
    elif path.startswith("calculations"):
        service_url = SERVICES["calculation-service"]
        print(f"🔍 [DEBUG] Gateway: Routing to calculation-service: {service_url}")
        return await proxy_request(request, service_url, f"/{path}")
    elif path.startswith("chat") or path.startswith("generate"):
        service_url = SERVICES["ollama"]
        print(f"🔍 [DEBUG] Gateway: Routing to ollama: {service_url} with path: {path}")
        return await proxy_request(request, service_url, f"/api/{path}")
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

# Основной роут для всех остальных путей
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_main(request: Request, path: str):
    """Основной роут для всех остальных путей"""
    print(f"🔍 [DEBUG] Gateway: Main route called with path: {path}")
    
    # Определяем сервис на основе пути
    if path.startswith("upload") or path.startswith("documents") or path.startswith("checkable-documents") or path.startswith("settings"):
        service_url = SERVICES["document-parser"]
        print(f"🔍 [DEBUG] Gateway: Routing to document-parser: {service_url}")
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
    elif path.startswith("calculations"):
        service_url = SERVICES["calculation-service"]
        print(f"🔍 [DEBUG] Gateway: Routing to calculation-service: {service_url}")
        return await proxy_request(request, service_url, f"/{path}")
    elif path.startswith("chat") or path.startswith("generate"):
        service_url = SERVICES["ollama"]
        print(f"🔍 [DEBUG] Gateway: Routing to ollama: {service_url} with path: {path}")
        return await proxy_request(request, service_url, f"/api/{path}")
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

if __name__ == "__main__":
    print("🔍 [DEBUG] Gateway: Starting FastAPI application")
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8443)