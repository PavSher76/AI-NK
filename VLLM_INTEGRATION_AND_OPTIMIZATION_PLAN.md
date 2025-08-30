# План интеграции и оптимизации VLLM сервиса

## 🎯 Цели интеграции

### 1. Унификация LLM использования
- Заменить все прямые обращения к Ollama на VLLM API
- Стандартизировать интерфейс взаимодействия с LLM
- Упростить конфигурацию и мониторинг

### 2. Повышение функциональности
- Интеграция LLM анализа в Document Parser
- Улучшение иерархической проверки документов
- Расширение возможностей RAG сервиса

### 3. Оптимизация производительности
- Кэширование запросов
- Batch processing
- Оптимизация промптов

## 🏗️ Архитектурные улучшения

### 1. Централизованный LLM сервис
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Все сервисы   │───▶│   VLLM Adapter  │───▶│   Ollama        │
│   (унифицирован)│    │   (централизован)│    │   (оптимизирован)│
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 2. Улучшенная маршрутизация
```python
# gateway/app.py - расширенная конфигурация
SERVICES = {
    "document-parser": "http://document-parser:8001",
    "rag-service": "http://rag-service:8003",
    "rule-engine": "http://rule-engine:8004",
    "calculation-service": "http://calculation-service:8002",
    "vllm": "http://vllm:8000",
    "ollama": "http://ollama:11434"  # только для прямого доступа
}

# Унифицированный LLM endpoint
@app.api_route("/llm/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_llm(request: Request, path: str):
    """Унифицированный LLM endpoint"""
    service_url = SERVICES["vllm"]
    return await proxy_request(request, service_url, f"/api/{path}")
```

## 📋 План интеграции по сервисам

### 1. Document Parser - Нормоконтроль

#### Текущее состояние:
```python
# document_parser/services/norm_control_service.py
async def perform_norm_control_check_for_page(self, document_id: int, page_data: Dict[str, Any]):
    # ❌ Заглушка - возвращает фиктивные результаты
    findings = []
    # ... фиктивная логика
```

#### Целевое состояние:
```python
# document_parser/services/norm_control_service.py
async def perform_norm_control_check_for_page(self, document_id: int, page_data: Dict[str, Any]):
    """LLM анализ страницы документа"""
    try:
        # Получение промпта из настроек
        prompt_template = await self.get_normcontrol_prompt_template()
        
        # Форматирование промпта с контекстом страницы
        formatted_prompt = prompt_template.format(
            page_content=page_data["content"],
            page_number=page_data["page_number"],
            document_id=document_id
        )
        
        # Отправка запроса к VLLM через Gateway
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{GATEWAY_URL}/llm/chat/completions",
                headers={"Authorization": f"Bearer {auth_token}"},
                json={
                    "model": "llama3.1:8b",
                    "messages": [
                        {
                            "role": "system",
                            "content": "Вы - эксперт по нормоконтролю документов. Анализируйте контент на соответствие нормативным требованиям."
                        },
                        {
                            "role": "user",
                            "content": formatted_prompt
                        }
                    ],
                    "temperature": 0.3,
                    "max_tokens": 2000
                },
                timeout=120.0
            )
            
            if response.status_code == 200:
                data = response.json()
                llm_response = data["choices"][0]["message"]["content"]
                
                # Парсинг результатов
                findings = self.parse_llm_response(llm_response)
                
                return {
                    "status": "success",
                    "findings": findings,
                    "llm_response": llm_response
                }
            else:
                logger.error(f"LLM request failed: {response.status_code}")
                return {"status": "error", "error": "LLM request failed"}
                
    except Exception as e:
        logger.error(f"LLM analysis error: {e}")
        return {"status": "error", "error": str(e)}
```

#### Преимущества:
- ✅ Реальный LLM анализ вместо заглушек
- ✅ Использование настроек промптов
- ✅ Унифицированный API через VLLM
- ✅ Обработка ошибок и таймаутов

### 2. RAG Service - Консультации

#### Текущее состояние:
```python
# rag_service/ntd_consultation.py
async def _generate_response(self, question: str, context: str):
    # ❌ Прямое обращение к Ollama
    response = await client.post(
        f"{self.ollama_url}/api/generate",
        json={
            "model": "llama3.2:3b",
            "prompt": prompt,
            # ...
        }
    )
```

#### Целевое состояние:
```python
# rag_service/ntd_consultation.py
async def _generate_response(self, question: str, context: str, history: List[Dict[str, str]] = None):
    """Генерация ответа через VLLM"""
    try:
        # Формирование промпта
        prompt = self._build_prompt(question, context, history)
        
        # Отправка запроса к VLLM через Gateway
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{GATEWAY_URL}/llm/chat/completions",
                headers={"Authorization": f"Bearer {self.auth_token}"},
                json={
                    "model": "llama3.1:8b",
                    "messages": [
                        {
                            "role": "system",
                            "content": "Вы - эксперт по нормативным документам. Отвечайте на вопросы пользователей на основе предоставленного контекста."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.7,
                    "max_tokens": 2000
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"]
            else:
                logger.error(f"VLLM request failed: {response.status_code}")
                return "Произошла ошибка при генерации ответа."
                
    except Exception as e:
        logger.error(f"VLLM generation error: {e}")
        return "Произошла ошибка при генерации ответа."
```

#### Преимущества:
- ✅ Унифицированный API через VLLM
- ✅ Лучшая модель (llama3.1:8b вместо llama3.2:3b)
- ✅ Стандартизированная обработка ошибок
- ✅ Возможность использования истории диалога

### 3. Иерархическая проверка

#### Новый функционал:
```python
# document_parser/services/hierarchical_check_service.py
class HierarchicalCheckService:
    async def perform_hierarchical_check(self, document_id: int) -> Dict[str, Any]:
        """Иерархическая проверка документа с использованием VLLM"""
        try:
            # Получение документа
            document = await self.get_document(document_id)
            
            # Анализ структуры документа
            structure_analysis = await self.analyze_document_structure(document)
            
            # Проверка на уровне разделов
            section_analysis = await self.analyze_sections(document, structure_analysis)
            
            # Проверка на уровне параграфов
            paragraph_analysis = await self.analyze_paragraphs(document, section_analysis)
            
            # Синтез результатов
            final_result = await self.synthesize_results(
                structure_analysis, section_analysis, paragraph_analysis
            )
            
            return final_result
            
        except Exception as e:
            logger.error(f"Hierarchical check error: {e}")
            return {"status": "error", "error": str(e)}
    
    async def analyze_document_structure(self, document: Dict) -> Dict[str, Any]:
        """Анализ структуры документа через VLLM"""
        prompt = f"""
        Проанализируйте структуру документа и выделите:
        1. Основные разделы и подразделы
        2. Иерархию заголовков
        3. Логические связи между разделами
        4. Соответствие стандартам оформления
        
        Документ: {document['content'][:5000]}
        """
        
        response = await self.llm_request(prompt, "structure_analysis")
        return self.parse_structure_response(response)
    
    async def analyze_sections(self, document: Dict, structure: Dict) -> Dict[str, Any]:
        """Анализ разделов документа"""
        results = []
        for section in structure.get("sections", []):
            prompt = f"""
            Проанализируйте раздел документа на соответствие нормативным требованиям:
            
            Раздел: {section['title']}
            Содержание: {section['content']}
            
            Проверьте:
            1. Соответствие содержания заголовку
            2. Логическую структуру
            3. Нормативные требования
            4. Качество изложения
            """
            
            response = await self.llm_request(prompt, "section_analysis")
            results.append(self.parse_section_response(response, section))
        
        return {"sections": results}
    
    async def llm_request(self, prompt: str, analysis_type: str) -> str:
        """Унифицированный запрос к VLLM"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{GATEWAY_URL}/llm/chat/completions",
                headers={"Authorization": f"Bearer {self.auth_token}"},
                json={
                    "model": "llama3.1:8b",
                    "messages": [
                        {
                            "role": "system",
                            "content": f"Вы - эксперт по анализу документов. Выполняйте {analysis_type}."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.3,
                    "max_tokens": 3000
                },
                timeout=180.0
            )
            
            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"]
            else:
                raise Exception(f"LLM request failed: {response.status_code}")
```

## 🚀 Оптимизация производительности

### 1. Кэширование запросов

#### Redis кэш для VLLM:
```python
# ollama_adapter/cache.py
import redis
import hashlib
import json
from typing import Optional

class VLLMCache:
    def __init__(self):
        self.redis_client = redis.Redis(
            host='redis',
            port=6379,
            db=1,  # Отдельная БД для VLLM кэша
            decode_responses=True
        )
        self.ttl = 3600  # 1 час
    
    def get_cache_key(self, model: str, messages: list, temperature: float) -> str:
        """Генерация ключа кэша"""
        content = json.dumps({
            "model": model,
            "messages": messages,
            "temperature": temperature
        }, sort_keys=True)
        return f"vllm:{hashlib.md5(content.encode()).hexdigest()}"
    
    async def get_cached_response(self, model: str, messages: list, temperature: float) -> Optional[str]:
        """Получение кэшированного ответа"""
        cache_key = self.get_cache_key(model, messages, temperature)
        cached = self.redis_client.get(cache_key)
        return cached
    
    async def cache_response(self, model: str, messages: list, temperature: float, response: str):
        """Сохранение ответа в кэш"""
        cache_key = self.get_cache_key(model, messages, temperature)
        self.redis_client.setex(cache_key, self.ttl, response)
```

#### Интеграция в VLLM Adapter:
```python
# ollama_adapter/ollama_adapter.py
from cache import VLLMCache

cache = VLLMCache()

@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    body = await request.json()
    messages = body.get("messages", [])
    model = body.get("model", "llama2:7b")
    temperature = body.get("temperature", 0.7)
    
    # Проверка кэша
    cached_response = await cache.get_cached_response(model, messages, temperature)
    if cached_response:
        logger.info("Cache hit for LLM request")
        return json.loads(cached_response)
    
    # Выполнение запроса к Ollama
    # ... существующий код ...
    
    # Сохранение в кэш
    await cache.cache_response(model, messages, temperature, json.dumps(openai_response))
    
    return openai_response
```

### 2. Batch Processing

#### Batch API endpoint:
```python
# ollama_adapter/ollama_adapter.py
@app.post("/v1/chat/completions/batch")
async def chat_completions_batch(request: Request):
    """Batch обработка запросов"""
    body = await request.json()
    requests = body.get("requests", [])
    
    results = []
    for req in requests:
        try:
            # Обработка каждого запроса
            response = await process_single_request(req)
            results.append({
                "status": "success",
                "response": response
            })
        except Exception as e:
            results.append({
                "status": "error",
                "error": str(e)
            })
    
    return {"results": results}
```

### 3. Оптимизация промптов

#### Промпт менеджер:
```python
# ollama_adapter/prompt_manager.py
class PromptManager:
    def __init__(self):
        self.prompt_templates = {
            "norm_control": {
                "system": "Вы - эксперт по нормоконтролю документов.",
                "user_template": "Проанализируйте документ на соответствие нормативным требованиям: {content}"
            },
            "document_analysis": {
                "system": "Вы - эксперт по анализу документов.",
                "user_template": "Проанализируйте структуру документа: {content}"
            },
            "consultation": {
                "system": "Вы - эксперт по нормативным документам.",
                "user_template": "Ответьте на вопрос на основе контекста: {question}\n\nКонтекст: {context}"
            }
        }
    
    def get_optimized_prompt(self, prompt_type: str, **kwargs) -> dict:
        """Получение оптимизированного промпта"""
        template = self.prompt_templates.get(prompt_type)
        if not template:
            raise ValueError(f"Unknown prompt type: {prompt_type}")
        
        return {
            "system": template["system"],
            "user": template["user_template"].format(**kwargs)
        }
```

## 📊 Мониторинг и метрики

### 1. VLLM метрики
```python
# ollama_adapter/metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Метрики
vllm_requests_total = Counter('vllm_requests_total', 'Total VLLM requests', ['model', 'endpoint'])
vllm_request_duration = Histogram('vllm_request_duration_seconds', 'VLLM request duration', ['model'])
vllm_cache_hits = Counter('vllm_cache_hits_total', 'VLLM cache hits')
vllm_cache_misses = Counter('vllm_cache_misses_total', 'VLLM cache misses')
vllm_active_requests = Gauge('vllm_active_requests', 'Active VLLM requests')

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    if request.url.path.startswith("/v1/"):
        vllm_active_requests.inc()
        start_time = time.time()
        
        response = await call_next(request)
        
        duration = time.time() - start_time
        vllm_request_duration.observe(duration)
        vllm_active_requests.dec()
        
        return response
    
    return await call_next(request)
```

### 2. Health Check с детализацией
```python
# ollama_adapter/ollama_adapter.py
@app.get("/health")
async def health():
    """Расширенный health check"""
    try:
        # Проверка подключения к Ollama
        async with httpx.AsyncClient() as client:
            ollama_response = await client.get(f"{OLLAMA_URL}/api/tags", timeout=5.0)
            ollama_healthy = ollama_response.status_code == 200
        
        # Проверка Redis кэша
        redis_healthy = cache.redis_client.ping()
        
        # Проверка доступных моделей
        models = await get_available_models()
        
        return {
            "status": "healthy" if ollama_healthy and redis_healthy else "unhealthy",
            "components": {
                "ollama": "healthy" if ollama_healthy else "unhealthy",
                "redis_cache": "healthy" if redis_healthy else "unhealthy"
            },
            "models": models,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
```

## 🔧 Конфигурация и развертывание

### 1. Обновленная конфигурация Docker Compose
```yaml
# docker-compose.yaml
vllm:
  build: 
    context: ./ollama_adapter
    dockerfile: Dockerfile.optimized
  ports:
    - "8000:8000"
  environment:
    - OLLAMA_BASE_URL=http://ollama:11434
    - OLLAMA_MODEL=llama3.1:8b
    - REDIS_URL=redis://redis:6379/1
    - CACHE_TTL=3600
    - ENABLE_CACHE=true
    - ENABLE_METRICS=true
    - LOG_LEVEL=INFO
  volumes:
    - ./ollama_adapter/prompts:/app/prompts:ro
  depends_on:
    - ollama
    - redis
  restart: unless-stopped
  deploy:
    resources:
      limits:
        memory: 2G
        cpus: '1.5'
      reservations:
        memory: 1G
        cpus: '0.75'
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
    interval: 30s
    timeout: 10s
    retries: 3
```

### 2. Переменные окружения
```bash
# .env
VLLM_MODEL=llama3.1:8b
VLLM_CACHE_TTL=3600
VLLM_ENABLE_CACHE=true
VLLM_ENABLE_METRICS=true
VLLM_REQUEST_TIMEOUT=120
VLLM_MAX_TOKENS=2000
VLLM_TEMPERATURE=0.3
```

## 📈 Ожидаемые результаты

### 1. Производительность
- **Кэширование:** 40-60% снижение времени ответа для повторных запросов
- **Batch processing:** 30-50% увеличение пропускной способности
- **Оптимизация промптов:** 20-30% снижение времени обработки

### 2. Функциональность
- **Document Parser:** Реальный LLM анализ вместо заглушек
- **RAG Service:** Улучшенные консультации с лучшей моделью
- **Иерархическая проверка:** Новый функционал анализа структуры документов

### 3. Надежность
- **Мониторинг:** Полная видимость работы VLLM
- **Health checks:** Автоматическое обнаружение проблем
- **Обработка ошибок:** Стандартизированная обработка сбоев

## 🚀 План внедрения

### Этап 1: Базовая интеграция (1-2 недели)
1. Обновление VLLM Adapter с кэшированием
2. Интеграция в Document Parser
3. Базовый мониторинг

### Этап 2: Расширение функциональности (2-3 недели)
1. Интеграция в RAG Service
2. Реализация иерархической проверки
3. Batch processing

### Этап 3: Оптимизация (1-2 недели)
1. Тонкая настройка промптов
2. Оптимизация производительности
3. Расширенный мониторинг

### Этап 4: Тестирование и развертывание (1 неделя)
1. Комплексное тестирование
2. Документация
3. Продакшн развертывание

## Заключение

Интеграция VLLM сервиса в проект AI-NK значительно повысит функциональность и производительность системы. Основные преимущества:

1. **Унификация** - единый интерфейс для всех LLM операций
2. **Производительность** - кэширование и оптимизация
3. **Функциональность** - реальный LLM анализ во всех сервисах
4. **Надежность** - мониторинг и обработка ошибок
5. **Масштабируемость** - готовность к расширению функциональности

Реализация этого плана превратит VLLM из вспомогательного компонента в центральный элемент архитектуры проекта.
