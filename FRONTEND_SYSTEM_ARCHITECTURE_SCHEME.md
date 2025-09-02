# Схема обработки документов и запросов системой AI-NK

## 🏗️ Общая архитектура системы

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                FRONTEND (Port 443)                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                │
│  │   App.js        │  │   Sidebar.js    │  │   Header.js     │                │
│  │   (Main App)    │  │   (Navigation)  │  │   (Top Bar)     │                │
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
│                              BACKEND SERVICES                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │ RAG Service │  │ Calculation │  │ Document    │  │ Rule Engine │          │
│  │ (Port 8003) │  │ Service    │  │ Parser      │  │ (Port 8002) │          │
│  └─────────────┘  │(Port 8004) │  │(Port 8001)  │  └─────────────┘          │
└─────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              DATA LAYER                                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │ PostgreSQL  │  │   Qdrant    │  │   Redis     │  │   Prometheus│          │
│  │ (Port 5432) │  │(Port 6333)  │  │(Port 6379)  │  │(Port 9090)  │          │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘          │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 🤖 VLLM + Ollama Integration Layer

### 🏗️ Архитектура интеграции с моделями

```
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

### 🔄 Потоки взаимодействия с моделями

#### 1. 💬 Чат с ИИ через Ollama
```
Frontend Chat → VLLM+Ollama Service → Ollama API → GPT-OSS Model → Response
      │               │                    │            │              │
      ▼               ▼                    ▼            ▼              ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ User        │ │ FastAPI     │ │ Ollama      │ │ GPT-OSS     │ │ Generated   │
│ Message     │ │ Endpoint    │ │ /api/generate│ │ 20B Model   │ │ Response    │
└─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘
```

#### 2. 🔍 Векторный поиск через BGE-M3
```
NTD Query → RAG Service → BGE-M3 Model → Vector Embedding → Qdrant Search
     │           │            │              │                │
     ▼           ▼            ▼              ▼                ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ User        │ │ RAG         │ │ BGE-M3      │ │ Embedding   │ │ Similarity  │
│ Query       │ │ Service     │ │ Model       │ │ Generation  │ │ Search      │
└─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘
```

#### 3. 📊 Мониторинг моделей
```
OllamaMonitor → Status Check → Ollama API → Model Info → Display Status
      │              │              │            │              │
      ▼              ▼              ▼            ▼              ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ Frontend    │ │ Timer       │ │ /api/tags   │ │ Model       │ │ Visual      │
│ Component   │ │ (30s)       │ │ Endpoint    │ │ Information │ │ Indicators  │
└─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘
```

### 🧠 Модели и их назначение

#### 1. 🤖 GPT-OSS 20B (gpt-oss:20b)
- **Назначение**: Генерация текстовых ответов
- **Использование**: Чат, анализ документов, генерация контента
- **Параметры**: max_tokens=2048, temperature=0.7, top_p=0.9

#### 2. 🔍 BGE-M3 (bge-m3:latest)
- **Назначение**: Векторные эмбеддинги
- **Использование**: RAG, семантический поиск, кластеризация
- **Параметры**: dimensions=1024, normalize=True

### 🔌 API интеграции с моделями

#### Ollama API Endpoints
```bash
# Генерация текста
POST http://localhost:11434/api/generate
{
    "model": "gpt-oss:20b",
    "prompt": "User message",
    "stream": false,
    "options": {
        "temperature": 0.7,
        "top_p": 0.9,
        "num_predict": 2048
    }
}

# Список моделей
GET http://localhost:11434/api/tags

# Информация о модели
GET http://localhost:11434/api/show
```

#### VLLM+Ollama Service Endpoints
```bash
# Чат
POST http://localhost:8005/chat
{
    "message": "User message",
    "model": "gpt-oss:20b",
    "max_tokens": 2048
}

# Статус сервиса
GET http://localhost:8005/health

# Список моделей
GET http://localhost:8005/models

# Статистика
GET http://localhost:8005/stats
```

## 🤖 VLLM + Ollama Integration Layer

### 🏗️ Архитектура интеграции с моделями

```
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

### 🔄 Потоки взаимодействия с моделями

#### 1. 💬 Чат с ИИ через Ollama
```
Frontend Chat → VLLM+Ollama Service → Ollama API → GPT-OSS Model → Response
      │               │                    │            │              │
      ▼               ▼                    ▼            ▼              ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ User        │ │ FastAPI     │ │ Ollama      │ │ GPT-OSS     │ │ Generated   │
│ Message     │ │ Endpoint    │ │ /api/generate│ │ 20B Model   │ │ Response    │
└─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘
```

#### 2. 🔍 Векторный поиск через BGE-M3
```
NTD Query → RAG Service → BGE-M3 Model → Vector Embedding → Qdrant Search
     │           │            │              │                │
     ▼           ▼            ▼              ▼                ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ User        │ │ RAG         │ │ BGE-M3      │ │ Embedding   │ │ Similarity  │
│ Query       │ │ Service     │ │ Model       │ │ Generation  │ │ Search      │
└─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘
```

#### 3. 📊 Мониторинг моделей
```
OllamaMonitor → Status Check → Ollama API → Model Info → Display Status
      │              │              │            │              │
      ▼              ▼              ▼            ▼              ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ Frontend    │ │ Timer       │ │ /api/tags   │ │ Model       │ │ Visual      │
│ Component   │ │ (30s)       │ │ Endpoint    │ │ Information │ │ Indicators  │
└─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘
```

### 🧠 Модели и их назначение

#### 1. 🤖 GPT-OSS 20B (gpt-oss:20b)
- **Назначение**: Генерация текстовых ответов
- **Использование**: Чат, анализ документов, генерация контента
- **Параметры**: max_tokens=2048, temperature=0.7, top_p=0.9

#### 2. 🔍 BGE-M3 (bge-m3:latest)
- **Назначение**: Векторные эмбеддинги
- **Использование**: RAG, семантический поиск, кластеризация
- **Параметры**: dimensions=1024, normalize=True

### 🔌 API интеграции с моделями

#### Ollama API Endpoints
```bash
# Генерация текста
POST http://localhost:11434/api/generate
{
    "model": "gpt-oss:20b",
    "prompt": "User message",
    "stream": false,
    "options": {
        "temperature": 0.7,
        "top_p": 0.9,
        "num_predict": 2048
    }
}

# Список моделей
GET http://localhost:11434/api/tags

# Информация о модели
GET http://localhost:11434/api/show
```

#### VLLM+Ollama Service Endpoints
```bash
# Чат
POST http://localhost:8005/chat
{
    "message": "User message",
    "model": "gpt-oss:20b",
    "max_tokens": 2048
}

# Статус сервиса
GET http://localhost:8005/health

# Список моделей
GET http://localhost:8005/models

# Статистика
GET http://localhost:8005/stats
```

## 📱 Функциональные модули фронтэнда

### 1. 🏠 Dashboard (Главная страница)
**Файл**: `pages/DashboardPage.js`

#### Обработка запросов:
```
DashboardPage → API Calls → Gateway → Backend Services
     │              │           │           │
     ▼              ▼           ▼           ▼
┌─────────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│   Metrics   │ │  Stats  │ │  Auth   │ │  Data   │
│  Display    │ │  Fetch  │ │  Check  │ │  Query  │
└─────────────┘ └─────────┘ └─────────┘ └─────────┘
```

#### API эндпоинты:
- `GET /api/documents/stats` - Статистика документов
- `GET /api/calculations/stats` - Статистика расчетов
- `GET /api/system/status` - Статус системы

#### Компоненты:
- `DashboardMetrics.js` - Метрики и статистика
- `StatusIndicator.js` - Индикаторы состояния

---

### 2. 💬 Chat with AI (Чат с ИИ)
**Файл**: `pages/ChatPage.js`

#### Обработка запросов:
```
ChatPage → ChatInterface → API → Gateway → VLLM+Ollama Service → Ollama → GPT-OSS
    │           │           │       │              │              │        │
    ▼           ▼           ▼       ▼              ▼              ▼        ▼
┌─────────┐ ┌─────────┐ ┌─────┐ ┌─────┐ ┌─────────────┐ ┌─────────┐ ┌─────────┐
│ Message │ │  Input  │ │POST │ │Auth │ │  FastAPI    │ │ Ollama  │ │ GPT-OSS │
│  State  │ │ Handler │ │/chat│ │Check│ │  Service    │ │  API    │ │  Model  │
└─────────┘ └─────────┘ └─────┘ └─────┘ └─────────────┘ └─────────┘ └─────────┘
```

#### API эндпоинты:
- `POST /api/chat` - Отправка сообщения через Gateway
- `POST http://localhost:8005/chat` - Прямой доступ к VLLM+Ollama
- `POST /api/chat/stream` - Потоковая генерация
- `GET /api/models` - Список доступных моделей

#### Компоненты:
- `ChatInterface.js` - Интерфейс чата
- `ModelSelector.js` - Выбор модели
- `SettingsPanel.js` - Настройки чата

---

### 3. 🤖 NTD Consultation (Консультация НТД от ИИ)
**Файл**: `components/NTDConsultation.js`

#### Обработка запросов:
```
NTDConsultation → API → Gateway → RAG Service → BGE-M3 → Qdrant + GPT-OSS → Response
       │           │       │         │           │        │              │
       ▼           ▼       ▼         ▼           ▼        ▼              ▼
┌─────────────┐ ┌─────┐ ┌─────┐ ┌─────────┐ ┌─────────┐ ┌─────────────┐ ┌─────────┐
│ User Query  │ │POST │ │Auth │ │ RAG     │ │ BGE-M3  │ │ Vector      │ │ Answer  │
│  Input      │ │/ntd │ │Check│ │ Service │ │ Model   │ │ Search +    │ │ Display │
└─────────────┘ └─────┘ └─────┘ └─────────┘ └─────────┘ └─────────────┘ └─────────┘
```

#### API эндпоинты:
- `POST /api/ntd-consultation/chat` - Консультация по НТД
- `GET /api/ntd-consultation/stats` - Статистика консультаций

#### Особенности:
- Интеграция с RAG сервисом
- Поиск по нормативным документам через BGE-M3
- Генерация ответов на основе найденных документов через GPT-OSS

---

### 4. 🧮 Calculations (Расчеты)
**Файл**: `pages/CalculationsPage.js`

#### Обработка запросов:
```
CalculationsPage → API → Gateway → Calculation Service → PostgreSQL
        │           │       │           │              │
        ▼           ▼       ▼           ▼              ▼
┌─────────────┐ ┌─────┐ ┌─────┐ ┌─────────────┐ ┌─────────┐
│ Calculation │ │POST │ │Auth │ │ Engineering │ │  Data   │
│   Form      │ │/calc│ │Check│ │ Calculation │ │ Storage │
└─────────────┘ └─────┘ └─────┘ └─────────────┘ └─────────┘
```

#### API эндпоинты:
- `POST /api/calculations/structural` - Структурные расчеты
- `POST /api/calculations/electrical` - Электрические расчеты
- `POST /api/calculations/mechanical` - Механические расчеты
- `POST /api/calculations/thermal` - Тепловые расчеты
- `POST /api/calculations/safety` - Расчеты безопасности

#### Компоненты:
- `StructuralCalculationModal.js` - Модальное окно расчетов
- Различные формы для типов расчетов

---

### 5. 📋 Normcontrol (Нормоконтроль)
**Файл**: `pages/NormcontrolPage.js`

#### Обработка запросов:
```
NormcontrolPage → API → Gateway → RAG Service + Rule Engine → BGE-M3 + GPT-OSS
        │           │       │           │
        ▼           ▼       ▼           ▼
┌─────────────┐ ┌─────┐ ┌─────┐ ┌─────────────┐
│ Document    │ │POST │ │Auth │ │  Norm       │
│  Upload     │ │/norm│ │Check│ │  Control    │
└─────────────┘ └─────┘ └─────┘ └─────────────┘
```

#### API эндпоинты:
- `POST /api/normcontrol/check` - Проверка документа
- `GET /api/normcontrol/results` - Результаты проверки
- `POST /api/normcontrol/upload` - Загрузка документа

#### Компоненты:
- `CheckableDocuments.js` - Проверяемые документы
- `NormativeDocuments.js` - Нормативные документы

---

### 6. 📚 Documents (Нормативные документы)
**Файл**: `pages/DocumentsPage.js`

#### Обработка запросов:
```
DocumentsPage → API → Gateway → RAG Service → PostgreSQL + Qdrant + BGE-M3
        │           │       │         │           │
        ▼           ▼       ▼         ▼           ▼
┌─────────────┐ ┌─────┐ ┌─────┐ ┌─────────┐ ┌─────────┐
│ Document    │ │GET  │ │Auth │ │ Document│ │  Data   │
│  Management │ │/docs│ │Check│ │  CRUD   │ │ Storage │
└─────────────┘ └─────┘ └─────┘ └─────────┘ └─────────┘
```

#### API эндпоинты:
- `GET /api/documents` - Список документов
- `POST /api/documents/upload` - Загрузка документа
- `DELETE /api/documents/{id}` - Удаление документа
- `GET /api/documents/{id}` - Получение документа
- `POST /api/documents/reindex` - Переиндексация

#### Компоненты:
- `NormativeDocuments.js` - Управление документами
- `CheckableDocuments.js` - Проверяемые документы

---

### 7. 🔍 Ollama Monitor (Мониторинг Ollama)
**Файл**: `pages/OllamaMonitor.js`

#### Обработка запросов:
```
OllamaMonitor → OllamaStatusChecker → API → VLLM+Ollama Service → Ollama → Model Info
       │               │               │           │              │            │
       ▼               ▼               ▼           ▼              ▼            ▼
┌─────────────┐ ┌─────────────┐ ┌─────┐ ┌─────────────┐ ┌─────────┐ ┌─────────────┐
│   Monitor   │ │ Status      │ │GET  │ │  VLLM+      │ │ Local   │ │ Model       │
│   Display   │ │ Checker     │ │/8005│ │  Ollama     │ │ Ollama  │ │ Information │
└─────────────┘ └─────────────┘ └─────┘ └─────────────┘ └─────────┘ └─────────────┘
```

#### API эндпоинты:
- `GET http://localhost:8005/health` - Статус VLLM+Ollama
- `GET http://localhost:8005/models` - Модели Ollama
- `POST http://localhost:8005/chat` - Тест чата
- `GET http://localhost:11434/api/tags` - Прямой доступ к Ollama

#### Компоненты:
- `OllamaStatusChecker.js` - Проверка статуса
- Тестирование чата через веб-интерфейс
- Мониторинг доступности моделей GPT-OSS и BGE-M3

---

## 🔄 Потоки обработки данных

### 1. 🔐 Аутентификация
```
User Login → AuthModal → Keycloak → Gateway → Frontend State
     │           │          │          │          │
     ▼           ▼          ▼          ▼          ▼
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│  Input  │ │  Form   │ │  OAuth  │ │  JWT    │ │  Token  │
│Credentials│ │ Submit │ │  Flow   │ │  Check  │ │ Storage │
└─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘
```

### 2. 📄 Загрузка документа
```
File Upload → Document Parser → RAG Service → BGE-M3 → Vector DB + PostgreSQL
      │            │               │              │              │
      ▼            ▼               ▼              ▼              ▼
┌─────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│  File   │ │  Parse &    │ │  Embedding  │ │  Vector     │ │  Storage   │
│  Input  │ │  Chunking   │ │  Generation │ │  Generation │ │  & Index   │
└─────────┘ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘
```

### 3. 🔍 Поиск по документам
```
Search Query → RAG Service → BGE-M3 → Vector Search → Document Retrieval → Response
      │            │             │        │              │                │
      ▼            ▼             ▼        ▼              ▼                ▼
┌─────────┐ ┌─────────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────┐ ┌─────────┐
│  Query  │ │  Query      │ │ BGE-M3  │ │ Qdrant  │ │ Content     │ │ Result │
│  Input  │ │  Processing │ │  Model  │ │ Search  │ │  Fetch      │ │ Display │
└─────────┘ └─────────────┘ └─────────┘ └─────────┘ └─────────────┘ └─────────┘
```

### 4. 💬 Генерация ответа
```
User Message → Chat Service → VLLM+Ollama → Ollama → GPT-OSS → Response → Display
      │            │              │            │        │          │        │
      ▼            ▼              ▼            ▼        ▼          ▼        ▼
┌─────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│ Message │ │  Message    │ │  FastAPI    │ │ Ollama  │ │ GPT-OSS │ │ Generated│ │ UI      │
│  Input  │ │  Processing │ │  Service    │ │  API    │ │  Model  │ │  Text    │ │ Update  │
└─────────┘ └─────────────┘ └─────────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘
```

---

## 🗄️ Хранение данных

### Frontend State Management
```javascript
// Основное состояние приложения
const [currentPage, setCurrentPage] = useState('dashboard');
const [isAuthenticated, setIsAuthenticated] = useState(false);
const [authToken, setAuthToken] = useState('');
const [userInfo, setUserInfo] = useState(null);
const [systemStatus, setSystemStatus] = useState({});
const [models, setModels] = useState([]);
const [messages, setMessages] = useState([]);
```

### Local Storage
- `userInfo` - Информация о пользователе и токен
- `chatHistory` - История чата
- `userPreferences` - Пользовательские настройки

### Session Storage
- `currentSession` - Текущая сессия
- `tempData` - Временные данные

---

## 🔌 API интеграции

### Gateway Endpoints
```
/api/v1/* → Gateway (Port 8443) → Backend Services
    │              │                    │
    ▼              ▼                    ▼
┌─────────┐ ┌─────────────┐ ┌─────────────────────────┐
│ Frontend│ │  Auth &     │ │  RAG | Calc | Doc | Rule│
│ Requests│ │  Routing    │ │  Services                │
└─────────┘ └─────────────┘ └─────────────────────────┘
```

### Direct Service Endpoints
```
Frontend → Direct Service (для специальных случаев)
    │              │
    ▼              ▼
┌─────────┐ ┌─────────────┐
│ Ollama  │ │  VLLM+      │
│ Monitor │ │  Ollama     │
│         │ │  Service    │
└─────────┘ └─────────────┘
```

### Model Integration Endpoints
```
Frontend → VLLM+Ollama Service → Ollama Models
    │              │                │
    ▼              ▼                ▼
┌─────────┐ ┌─────────────┐ ┌─────────────┐
│ Chat    │ │  FastAPI    │ │  GPT-OSS    │
│ UI      │ │  Service    │ │  BGE-M3     │
└─────────┘ └─────────────┘ └─────────────┘
```

---

## 📊 Мониторинг и логирование

### Frontend Logging
```javascript
console.log('🔍 [DEBUG] Component: Action description');
console.log('✅ [SUCCESS] Operation completed');
console.log('❌ [ERROR] Error description');
console.log('⚠️ [WARNING] Warning description');
```

### Model Monitoring
```python
# Статус моделей
{
    "status": "healthy",
    "services": {
        "ollama": {
            "status": "healthy",
            "available_models": ["gpt-oss:20b", "bge-m3:latest"],
            "total_models": 2,
            "response_time_ms": 45.2,
            "gpt_oss_available": true,
            "bge_m3_available": true
        },
        "vllm": {
            "status": "healthy",
            "url": "http://localhost:8000"
        }
    },
    "timestamp": "2025-08-31T10:30:00.000Z"
}
```

### Model Performance Metrics
```python
# Метрики производительности моделей
{
    "gpt-oss:20b": {
        "requests_total": 1250,
        "errors_total": 12,
        "avg_response_time_ms": 2340,
        "tokens_generated": 45678,
        "last_used": "2025-08-31T10:25:00.000Z"
    },
    "bge-m3:latest": {
        "embeddings_generated": 890,
        "avg_embedding_time_ms": 45,
        "last_used": "2025-08-31T10:28:00.000Z"
    }
}
```
            "total_models": 2,
            "response_time_ms": 45.2
        },
        "vllm": {
            "status": "healthy",
            "url": "http://localhost:8000"
        }
    }
}
```

### Performance Monitoring
- Время загрузки страниц
- Время ответа API
- Время генерации моделей
- Статус компонентов
- Ошибки пользователя

### Error Handling
```javascript
try {
  // API call
} catch (error) {
  console.error('❌ [ERROR] API call failed:', error);
  setError(error.message);
}
```

---

## 🚀 Оптимизация производительности

### 1. Lazy Loading
- Компоненты загружаются по требованию
- Страницы рендерятся при переходе

### 2. Caching
- Кэширование API ответов
- Кэширование статуса моделей (30 сек)
- Локальное хранение данных
- Оптимизация повторных запросов

### 3. Debouncing
- Поиск с задержкой
- Автосохранение форм
- Оптимизация ввода

### 4. Model Optimization
- Параллельные запросы к моделям
- Потоковая генерация
- Кэширование эмбеддингов

---

## 🔒 Безопасность

### 1. Аутентификация
- JWT токены
- Keycloak интеграция
- Автоматическое обновление токенов

### 2. Авторизация
- Проверка прав доступа
- Роли пользователей
- Защищенные эндпоинты

### 3. Валидация
- Проверка входных данных
- Санитизация контента
- Защита от XSS

### 4. Model Security
- Валидация параметров моделей
- Rate limiting для генерации
- Логирование запросов к моделям
- Защита от prompt injection

### 4. Model Security
- Валидация параметров моделей
- Rate limiting для генерации
- Логирование запросов к моделям

---

## 📈 Масштабируемость

### 1. Компонентная архитектура
- Переиспользуемые компоненты
- Модульная структура
- Легкое добавление новых функций

### 2. API версионирование
- Поддержка разных версий API
- Обратная совместимость
- Плавная миграция

### 3. Конфигурация
- Переменные окружения
- Настройки для разных сред
- Гибкая конфигурация

### 4. Model Scaling
- Поддержка множественных моделей
- Горизонтальное масштабирование
- Load balancing для моделей
- Динамическое переключение между моделями

### 4. Model Scaling
- Поддержка множественных моделей
- Горизонтальное масштабирование
- Load balancing для моделей

---

## 🛠️ Разработка и отладка

### 1. Development Tools
- React Developer Tools
- Redux DevTools (если используется)
- Network monitoring
- Performance profiling

### 2. Testing
- Unit tests для компонентов
- Integration tests для API
- Model testing
- E2E tests для пользовательских сценариев

### 3. Debugging
- Console logging
- Error boundaries
- Performance monitoring
- User analytics
- Model performance tracking

---

## 📝 Заключение

Фронтэнд система AI-NK представляет собой комплексное React-приложение с модульной архитектурой, которое обеспечивает:

- **Единообразный интерфейс** для всех функциональных модулей
- **Централизованную аутентификацию** через Keycloak
- **Интеграцию с backend сервисами** через API Gateway
- **Мониторинг и управление** локальными моделями Ollama
- **Эффективную работу с ИИ моделями** через vLLM+Ollama интеграцию
- **Масштабируемую архитектуру** для добавления новых функций

### 🔑 Ключевые особенности интеграции с моделями:

1. **Гибкость**: Поддержка различных моделей через единый интерфейс
2. **Производительность**: Оптимизированная работа с локальными моделями
3. **Надежность**: Обработка ошибок и fallback механизмы
4. **Масштабируемость**: Легкое добавление новых моделей
5. **Мониторинг**: Полный контроль над состоянием сервисов и моделей

Каждый модуль имеет четко определенные API эндпоинты, обработку ошибок и интеграцию с соответствующими backend сервисами и моделями ИИ, что обеспечивает надежную и эффективную работу системы.
