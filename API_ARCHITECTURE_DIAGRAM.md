# 🏗️ Диаграмма архитектуры API проекта AI-NK

## 📊 Общая схема

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                FRONTEND (React)                                │
│                              https://localhost:443                             │
└─────────────────────────────────────────┬───────────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              API GATEWAY (FastAPI)                             │
│                              https://localhost:8443                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │ /health         │  │ /api/health     │  │ /metrics        │  │ /api/*      │ │
│  │ /api/analog-*   │  │ /api/v1/*       │  │ /api/normcontrol2│  │ /v1/*       │ │
│  │ /api/archive/*  │  │ /ollama/*       │  │ /calculation/*  │  │ /{path:path}│ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────┘ │
└─────────────────────────────────────────┬───────────────────────────────────────┘
                                          │
                    ┌─────────────────────┼─────────────────────┐
                    │                     │                     │
                    ▼                     ▼                     ▼
    ┌─────────────────────────┐ ┌─────────────────────────┐ ┌─────────────────────────┐
    │     RAG SERVICE         │ │  CALCULATION SERVICE    │ │   NORMCONTROL2 SERVICE  │
    │   (Port: 8003)          │ │    (Port: 8002)         │ │     (Port: 8010)        │
    │                         │ │                         │ │                         │
    │ • /documents            │ │ • /calculations         │ │ • /health               │
    │ • /upload               │ │ • /token                │ │ • /                     │
    │ • /chat                 │ │ • /me                   │ │                         │
    │ • /search               │ │ • /calculations/*/types │ │                         │
    │ • /ntd-consultation/*   │ │ • /calculations/*/execute│ │                         │
    │ • /reindex              │ │ • /metrics              │ │                         │
    │ • /models               │ │ • /health               │ │                         │
    │ • /embeddings           │ │                         │ │                         │
    │ • /health               │ │                         │ │                         │
    └─────────────────────────┘ └─────────────────────────┘ └─────────────────────────┘
                    │                     │                     │
                    ▼                     ▼                     ▼
    ┌─────────────────────────┐ ┌─────────────────────────┐ ┌─────────────────────────┐
    │  OUTGOING CONTROL       │ │    SPELLCHECKER         │ │      VLLM SERVICE       │
    │   (Port: 8006)          │ │    (Port: 8007)         │ │     (Port: 8005)        │
    │                         │ │                         │ │                         │
    │ • /upload               │ │ • /spellcheck           │ │ • /models               │
    │ • /documents            │ │ • /grammar-check        │ │ • /chat                 │
    │ • /spellcheck           │ │ • /comprehensive-check  │ │ • /upload_document      │
    │ • /grammar-check        │ │ • /languages            │ │ • /chat_with_document   │
    │ • /comprehensive-check  │ │ • /stats                │ │ • /stats                │
    │ • /expert-analysis      │ │ • /health               │ │ • /health               │
    │ • /settings             │ │                         │ │                         │
    │ • /health               │ │                         │ │                         │
    └─────────────────────────┘ └─────────────────────────┘ └─────────────────────────┘
                    │
                    ▼
    ┌─────────────────────────────────────────────────────────────────────────────────┐
    │                              OLLAMA (Local)                                   │
    │                            http://localhost:11434                             │
    │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
    │  │ /api/tags       │  │ /api/generate   │  │ /api/chat       │  │ /api/pull   │ │
    │  │ /api/models     │  │ /api/embeddings │  │ /api/show       │  │ /api/ps     │ │
    │  └─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────┘ │
    └─────────────────────────────────────────────────────────────────────────────────┘
```

## 🔄 Потоки данных

### 1. Загрузка документа
```
Frontend → Gateway → RAG Service → Qdrant + PostgreSQL
```

### 2. Чат с ИИ
```
Frontend → Gateway → RAG Service → Ollama → Response
```

### 3. Инженерные расчеты
```
Frontend → Gateway → Calculation Service → PostgreSQL
```

### 4. Проверка орфографии
```
Frontend → Gateway → Spellchecker Service → LanguageTool
```

### 5. Нормоконтроль
```
Frontend → Gateway → NormControl2 Service → Validation
```

## 🛡️ Безопасность

### Аутентификация
- **JWT токены** для Calculation Service
- **Bearer tokens** для остальных сервисов
- **Public paths** для открытых эндпоинтов

### CORS
- Все сервисы настроены на CORS
- Разрешенные origins: `["*"]`
- Поддерживаемые методы: `["*"]`

## 📊 Мониторинг

### Health Checks
- **Gateway**: `/health`, `/api/health`
- **RAG Service**: `/health`
- **Calculation Service**: `/health`
- **Все остальные сервисы**: `/health`

### Метрики
- **Gateway**: `/metrics`
- **Calculation Service**: `/metrics`
- **RAG Service**: `/metrics`

## 🔧 Конфигурация

### Порты
| Сервис | Порт | Протокол |
|--------|------|----------|
| Frontend | 443 | HTTPS |
| Gateway | 8443 | HTTPS |
| RAG Service | 8003 | HTTP |
| Calculation Service | 8002 | HTTP |
| NormControl2 Service | 8010 | HTTP |
| Outgoing Control | 8006 | HTTP |
| Spellchecker | 8007 | HTTP |
| VLLM Service | 8005 | HTTP |
| Ollama | 11434 | HTTP |

### Переменные окружения
- **OLLAMA_URL**: URL для подключения к Ollama
- **DATABASE_URL**: URL базы данных PostgreSQL
- **QDRANT_URL**: URL векторной базы данных
- **JWT_SECRET**: Секретный ключ для JWT

## 🚀 Масштабирование

### Горизонтальное масштабирование
- Каждый сервис может быть запущен в нескольких экземплярах
- Gateway автоматически балансирует нагрузку
- Stateless архитектура для всех сервисов

### Вертикальное масштабирование
- Настройка ресурсов через Docker Compose
- Мониторинг использования ресурсов
- Автоматическое масштабирование на основе метрик
