# Архитектура интеграции Ollama в системе AI-NK

## 🏗️ Общая архитектура интеграции

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                FRONTEND (Port 443)                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                │
│  │   ChatPage      │  │   OllamaMonitor │  │   NTDConsultation│                │
│  │   (Chat UI)     │  │   (Status UI)   │  │   (RAG UI)      │                │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘                │
└─────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              GATEWAY (Port 8443)                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                │
│  │ Authentication  │  │   Rate Limiting │  │   Routing       │                │
│  │   (Keycloak)    │  │   (Redis)       │  │   (Load Bal.)   │                │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘                │
└─────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              VLLM+OLLAMA SERVICE (Port 8005)                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                │
│  │   FastAPI       │  │   VLLM          │  │   Ollama        │                │
│  │   Integration   │  │   Service       │  │   Service       │                │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘                │
└─────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              LOCAL MODELS LAYER                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │   vLLM      │  │   Ollama    │  │   BGE-M3    │  │   GPT-OSS   │          │
│  │ (Port 8000) │  │(Port 11434) │  │(Embedding)  │  │(Generation) │          │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘          │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 🤖 Ollama Integration Service

### 📁 Структура сервиса

```
vllm_service/
├── main.py                    # FastAPI приложение
├── vllm_ollama_service.py     # Основная логика интеграции
└── requirements.txt           # Зависимости
```

### 🔧 Основные компоненты

#### 1. OllamaService Class
```python
class OllamaService:
    def __init__(self, ollama_url="http://localhost:11434"):
        self.ollama_url = ollama_url
        self.ollama_checker = OllamaStatusChecker(ollama_url)
```

#### 2. OllamaStatusChecker Class
```python
class OllamaStatusChecker:
    def check_ollama_status(self) -> Dict[str, Any]:
        # Проверка доступности Ollama
        # Проверка доступных моделей
        # Кэширование результатов
```

## 🔄 Потоки взаимодействия с моделями

### 1. 💬 Чат с ИИ (Chat Generation)

```
Frontend Chat → Ollama Integration Service → Ollama API → GPT-OSS Model → Response
      │               │                        │            │              │
      ▼               ▼                        ▼            ▼              ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ User        │ │ FastAPI     │ │ Ollama      │ │ GPT-OSS     │ │ Generated   │
│ Message     │ │ Endpoint    │ │ /api/generate│ │ 20B Model   │ │ Response    │
└─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘
```

#### Детальный процесс:
1. **Frontend** отправляет POST запрос на `/chat`
2. **Ollama Integration Service** получает сообщение и модель
3. **OllamaStatusChecker** проверяет доступность модели
4. **Ollama API** вызывается с параметрами генерации
5. **GPT-OSS 20B** генерирует ответ
6. **Response** возвращается через цепочку обратно

#### API эндпоинт:
```python
@app.post("/chat")
async def chat(request: ChatRequest):
    response = ollama_service.generate_response_with_ollama(
        message=request.message,
        model_name=request.model,
        history=request.history,
        max_tokens=request.max_tokens
    )
    return response
```

### 2. 🔍 Векторный поиск (RAG)

```
NTD Query → RAG Service → BGE-M3 Model → Vector Embedding → Qdrant Search
     │           │            │              │                │
     ▼           ▼            ▼              ▼                ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ User        │ │ RAG         │ │ BGE-M3      │ │ Embedding   │ │ Similarity  │
│ Query       │ │ Service     │ │ Model       │ │ Generation  │ │ Search      │
└─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘
```

#### Детальный процесс:
1. **NTD Consultation** отправляет запрос
2. **RAG Service** получает текст запроса
3. **BGE-M3 Model** генерирует векторное представление
4. **Qdrant** выполняет поиск похожих документов
5. **Результаты** возвращаются для генерации ответа

### 3. 📊 Мониторинг моделей

```
OllamaMonitor → Status Check → Ollama API → Model Info → Display Status
      │              │              │            │              │
      ▼              ▼              ▼            ▼              ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ Frontend    │ │ Timer       │ │ /api/tags   │ │ Model       │ │ Visual      │
│ Component   │ │ (30s)       │ │ Endpoint    │ │ Information │ │ Indicators  │
└─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘
```

#### API эндпоинты:
```python
@app.get("/health")      # Статус сервиса
@app.get("/models")      # Список доступных моделей
@app.get("/stats")       # Статистика использования
```

## 🧠 Модели и их назначение

### 1. 🤖 GPT-OSS 20B (gpt-oss:20b)
**Назначение**: Генерация текстовых ответов
**Использование**: 
- Чат с пользователем
- Генерация ответов на основе контекста
- Анализ документов

**Параметры модели**:
```python
{
    "model": "gpt-oss:20b",
    "max_tokens": 2048,
    "temperature": 0.7,
    "top_p": 0.9,
    "repeat_penalty": 1.1
}
```

### 2. 🔍 BGE-M3 (bge-m3:latest)
**Назначение**: Векторные эмбеддинги
**Использование**:
- Семантический поиск документов
- RAG (Retrieval-Augmented Generation)
- Кластеризация документов

**Параметры модели**:
```python
{
    "model": "bge-m3:latest",
    "dimensions": 1024,
    "normalize": True,
    "device": "cpu"  # или "cuda"
}
```

## 🔌 API интеграции

### Ollama API Endpoints

#### 1. Генерация текста
```bash
POST http://localhost:11434/api/generate
Content-Type: application/json

{
    "model": "gpt-oss:20b",
    "prompt": "User message here",
    "stream": false,
    "options": {
        "temperature": 0.7,
        "top_p": 0.9,
        "num_predict": 2048
    }
}
```

#### 2. Получение списка моделей
```bash
GET http://localhost:11434/api/tags
```

#### 3. Получение информации о модели
```bash
GET http://localhost:11434/api/show
Content-Type: application/json

{
    "name": "gpt-oss:20b"
}
```

### VLLM API Endpoints (если используется)

#### 1. Генерация через vLLM
```bash
POST http://localhost:8000/v1/completions
Content-Type: application/json

{
    "model": "gpt-oss:20b",
    "prompt": "User message",
    "max_tokens": 2048,
    "temperature": 0.7
}
```

#### 2. Список моделей vLLM
```bash
GET http://localhost:8000/v1/models
```

## 📊 Мониторинг и логирование

### Статус сервисов
```python
{
    "status": "healthy",  # healthy, degraded, unhealthy
    "services": {
        "ollama": {
            "status": "healthy",
            "available_models": ["gpt-oss:20b", "bge-m3:latest"],
            "total_models": 2,
            "response_time_ms": 45.2
        },
        "vllm": {
            "status": "healthy",
            "url": "http://localhost:8000"
        }
    },
    "timestamp": "2025-08-31T10:30:00.000Z"
}
```

### Логирование
```python
# Уровни логирования
logger.info("🤖 [VLLM_OLLAMA] Service initialized")
logger.info("💬 [OLLAMA_GENERATION] Generating response")
logger.warning("⚠️ [OLLAMA_STATUS] Model not available")
logger.error("❌ [OLLAMA_GENERATION] Generation failed")
```

## 🔄 Потоки обработки ошибок

### 1. Модель недоступна
```
Model Check → Not Found → Fallback → Error Response → User Notification
      │           │           │            │              │
      ▼           ▼           ▼            ▼              ▼
┌─────────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────┐ ┌─────────────┐
│ Check       │ │ Model   │ │ Try     │ │ Error       │ │ Show        │
│ Model       │ │ Missing │ │ Default │ │ Message     │ │ Alert       │
└─────────────┘ └─────────┘ └─────────┘ └─────────────┘ └─────────────┘
```

### 2. Ollama недоступен
```
Service Check → Connection Failed → Retry Logic → Fallback Mode → Status Update
      │              │                │            │              │
      ▼              ▼                ▼            ▼              ▼
┌─────────────┐ ┌─────────────┐ ┌─────────┐ ┌─────────────┐ ┌─────────────┐
│ Health      │ │ Network     │ │ Retry   │ │ Offline     │ │ UI          │
│ Check       │ │ Error       │ │ Attempt │ │ Mode        │ │ Update      │
└─────────────┘ └─────────────┘ └─────────┘ └─────────────┘ └─────────────┘
```

### 3. Таймаут генерации
```
Generation → Timeout → Retry → Success/Failure → Response
     │          │        │         │              │
     ▼          ▼        ▼         ▼              ▼
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────┐ ┌─────────────┐
│ Start   │ │ 60s     │ │ Retry   │ │ Success/    │ │ Return      │
│ Gen     │ │ Timeout │ │ Logic   │ │ Error       │ │ Result      │
└─────────┘ └─────────┘ └─────────┘ └─────────────┘ └─────────────┘
```

## 🚀 Оптимизация производительности

### 1. Кэширование статуса
```python
class OllamaStatusChecker:
    def __init__(self):
        self.cache_duration = 30  # секунды
        self.status_cache = None
        self.last_check = None
```

### 2. Параллельные запросы
```python
async def generate_response_parallel(self, messages: List[str]):
    tasks = [self.generate_response_with_ollama(msg) for msg in messages]
    responses = await asyncio.gather(*tasks)
    return responses
```

### 3. Потоковая генерация
```python
async def generate_stream(self, message: str):
    async for chunk in self.ollama_stream_generate(message):
        yield chunk
```

## 🔧 Конфигурация

### Переменные окружения
```bash
OLLAMA_URL=http://localhost:11434
VLLM_URL=http://localhost:8000
OLLAMA_TIMEOUT=60
CACHE_DURATION=30
LOG_LEVEL=INFO
```

### Конфигурация моделей
```python
MODEL_CONFIG = {
    "gpt-oss:20b": {
        "max_tokens": 2048,
        "temperature": 0.7,
        "top_p": 0.9,
        "repeat_penalty": 1.1
    },
    "bge-m3:latest": {
        "dimensions": 1024,
        "normalize": True,
        "device": "cpu"
    }
}
```

## 📈 Метрики и мониторинг

### Prometheus метрики
```python
# Счетчики
ollama_requests_total = Counter('ollama_requests_total', 'Total Ollama requests')
ollama_errors_total = Counter('ollama_errors_total', 'Total Ollama errors')

# Гистограммы
ollama_response_time = Histogram('ollama_response_time', 'Ollama response time')

# Gauge
ollama_models_available = Gauge('ollama_models_available', 'Available Ollama models')
```

### Grafana дашборд
- Количество запросов к моделям
- Время ответа моделей
- Доступность сервисов
- Использование ресурсов

## 🔒 Безопасность

### 1. Валидация входных данных
```python
class ChatRequest(BaseModel):
    message: str
    model: str = "gpt-oss:20b"
    max_tokens: int = Field(ge=1, le=4096)
    temperature: float = Field(ge=0.0, le=2.0)
```

### 2. Rate Limiting
```python
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Проверка лимитов запросов
    # Блокировка при превышении
```

### 3. Логирование безопасности
```python
logger.warning(f"🚨 [SECURITY] Rate limit exceeded for IP: {client_ip}")
logger.error(f"🚨 [SECURITY] Invalid model request: {model_name}")
```

## 📝 Заключение

Интеграция vLLM и Ollama в системе AI-NK обеспечивает:

1. **Гибкость**: Поддержка различных моделей через единый интерфейс
2. **Производительность**: Оптимизированная работа с локальными моделями
3. **Надежность**: Обработка ошибок и fallback механизмы
4. **Масштабируемость**: Легкое добавление новых моделей
5. **Мониторинг**: Полный контроль над состоянием сервисов

Эта архитектура позволяет эффективно использовать локальные модели для генерации текста и векторного поиска, обеспечивая высокое качество ответов при сохранении конфиденциальности данных.
