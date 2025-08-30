# Анализ использования VLLM сервиса в проекте AI-NK

## 📋 Обзор архитектуры

VLLM сервис используется в проекте как **адаптер для Ollama**, предоставляющий OpenAI-совместимый API для работы с локальными LLM моделями.

## 🏗️ Архитектура VLLM сервиса

### 1. Компоненты системы
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Gateway       │    │   VLLM Adapter  │
│   (React)       │───▶│   (FastAPI)     │───▶│   (FastAPI)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Nginx         │    │   Ollama        │
                       │   (Frontend)    │    │   (LLM Model)   │
                       └─────────────────┘    └─────────────────┘
```

### 2. Конфигурация в Docker Compose
```yaml
# vLLM адаптер для Ollama
vllm:
  build: ./ollama_adapter
  ports:
    - "8000:8000"
  environment:
    - OLLAMA_BASE_URL=http://ollama:11434
    - OLLAMA_MODEL=llama3.1:8b
  depends_on:
    - ollama
  restart: unless-stopped
```

## 🔄 Маршрутизация запросов

### 1. Через Gateway (основной путь)
```
Frontend → Gateway (/v1/*) → VLLM Adapter → Ollama
```

**Конфигурация Gateway:**
```python
# gateway/app.py
SERVICES = {
    "vllm": "http://vllm:8000"
}

@app.api_route("/v1/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_vllm(request: Request, path: str):
    """Проксирование запросов к VLLM"""
    service_url = SERVICES["vllm"]
    return await proxy_request(request, service_url, f"/api/{path}")
```

### 2. Прямой доступ через Nginx
```
Frontend → Nginx (/v1/*) → VLLM Adapter → Ollama
```

**Конфигурация Nginx:**
```nginx
# frontend/nginx-simple.conf
location /v1/ {
    proxy_pass http://vllm:8000/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    
    # Настройки для длительных запросов
    proxy_connect_timeout 300s;
    proxy_send_timeout 300s;
    proxy_read_timeout 300s;
    proxy_buffering off;
}
```

## 🎯 Использование в сервисах

### 1. Rule Engine
**Файл:** `rule_engine/main.py`

**Использование:**
```python
# Отправка запроса к LLM через Gateway
response = await client.post(
    f"{GATEWAY_URL}/v1/chat/completions",
    headers={"Authorization": f"Bearer {auth_token}"},
    json={
        "model": "llama3:8b",
        "messages": [
            {
                "role": "system",
                "content": "Вы - эксперт по нормоконтролю документов..."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.3,
        "max_tokens": 2000
    }
)
```

**Конфигурация:**
- **GATEWAY_URL:** `https://gateway:8443`
- **Модель:** `llama3:8b`
- **Температура:** 0.3
- **Максимум токенов:** 2000

### 2. Document Parser (нормоконтроль)
**Файл:** `document_parser/services/norm_control_service.py`

**Статус:** ❌ **НЕ ИСПОЛЬЗУЕТ VLLM**
- В текущей реализации используется заглушка
- LLM анализ не реализован
- Возвращает фиктивные результаты

### 3. RAG Service (консультации)
**Файл:** `rag_service/ntd_consultation.py`

**Статус:** ❌ **НЕ ИСПОЛЬЗУЕТ VLLM**
- Прямое обращение к Ollama API
- Обходит VLLM адаптер

## 🔧 VLLM Adapter API

### 1. Доступные endpoints

#### `/v1/models`
```bash
GET http://localhost:8000/v1/models
```
**Ответ:**
```json
{
  "object": "list",
  "data": [
    {
      "id": "llama3.1:8b",
      "object": "model",
      "created": 1677610602,
      "owned_by": "ollama"
    }
  ]
}
```

#### `/v1/chat/completions`
```bash
POST http://localhost:8000/v1/chat/completions
```
**Запрос:**
```json
{
  "model": "llama3.1:8b",
  "messages": [
    {"role": "user", "content": "Hello"}
  ],
  "temperature": 0.7
}
```

**Ответ:**
```json
{
  "id": "chatcmpl-316266",
  "object": "chat.completion",
  "created": 28330,
  "model": "llama3.1:8b",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello! How are you today?"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 3,
    "completion_tokens": 19,
    "total_tokens": 22
  }
}
```

#### `/v1/completions`
```bash
POST http://localhost:8000/v1/completions
```
- Поддержка текстовых завершений
- Конвертация в Ollama формат

### 2. Поддерживаемые модели
- `llama3.1:8b` (основная)
- `llama3.1-optimized:latest`
- `llama3.1-optimized-v2:latest`

## 📊 Статус использования

### ✅ Активно используется:
1. **Rule Engine** - анализ документов на соответствие нормам
2. **Gateway маршрутизация** - проксирование запросов
3. **Nginx проксирование** - прямой доступ к VLLM

### ❌ Не используется:
1. **Document Parser** - нормоконтроль использует заглушки
2. **RAG Service** - консультации обходят VLLM

### 🔄 Потенциальное использование:
1. **Иерархическая проверка** - может использовать VLLM
2. **Генерация отчетов** - может использовать VLLM
3. **Анализ контента** - может использовать VLLM

## 🚀 Производительность

### 1. Текущие настройки
```yaml
deploy:
  resources:
    limits:
      memory: 1G
      cpus: '1.0'
    reservations:
      memory: 512M
      cpus: '0.5'
```

### 2. Оптимизация для разных платформ
- **MacBook Pro:** 2G RAM, 1 CPU
- **M3 Pro:** 2G RAM, 1 CPU  
- **70B модель:** 4G RAM, 2 CPU

## 🔍 Мониторинг и логирование

### 1. Логи VLLM Adapter
```bash
docker logs ai-nk-vllm-1
```

### 2. Health Check
```bash
curl http://localhost:8000/health
```

### 3. Проверка моделей
```bash
curl http://localhost:8000/v1/models
```

## 🛠️ Рекомендации по улучшению

### 1. Унификация использования
- **Document Parser:** Реализовать LLM анализ через VLLM
- **RAG Service:** Перевести на использование VLLM вместо прямого Ollama
- **Иерархическая проверка:** Интегрировать с VLLM

### 2. Оптимизация производительности
- Настроить кэширование запросов
- Оптимизировать размер промптов
- Добавить batch processing

### 3. Мониторинг
- Добавить метрики использования
- Мониторинг времени ответа
- Логирование ошибок

### 4. Безопасность
- Добавить rate limiting
- Валидация промптов
- Логирование запросов

## 📈 Статистика использования

### Текущие метрики:
- **Активные сервисы:** 1 из 4 (Rule Engine)
- **Модели:** 3 доступных модели
- **Порты:** 8000 (VLLM), 11434 (Ollama)
- **Статус:** ✅ Работает корректно

## Заключение

VLLM сервис в проекте AI-NK представляет собой **функциональный адаптер** для Ollama, предоставляющий OpenAI-совместимый API. Однако его использование **ограничено только Rule Engine**, в то время как другие сервисы либо не используют LLM, либо обходят VLLM адаптер.

**Основные выводы:**
1. ✅ VLLM сервис работает стабильно
2. ✅ API совместим с OpenAI
3. ❌ Недостаточное использование в проекте
4. 🔄 Потенциал для расширения функциональности

**Приоритетные задачи:**
1. Интеграция VLLM в Document Parser
2. Унификация использования LLM в проекте
3. Оптимизация производительности
4. Расширение мониторинга
