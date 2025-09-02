# Детальные диаграммы потоков данных фронтэнда AI-NK

## 🔄 Общий поток данных в системе

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                USER INTERFACE                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │   Input     │  │   Action    │  │   State     │  │   Display   │          │
│  │   Forms     │  │   Buttons   │  │   Update    │  │   Results   │          │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘          │
└─────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              COMPONENT LOGIC                                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │ Event       │  │ Validation  │  │ State       │  │ API         │          │
│  │ Handler     │  │ Logic       │  │ Management  │  │ Preparation │          │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘          │
└─────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              API LAYER                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │ HTTP        │  │ Headers     │  │ Body        │  │ Error       │          │
│  │ Request     │  │ (Auth)      │  │ (Data)      │  │ Handling    │          │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘          │
└─────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              BACKEND PROCESSING                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │ Gateway     │  │ Service     │  │ Database    │  │ Response    │          │
│  │ (Auth/Rate) │  │ (Business)  │  │ (Storage)   │  │ (Data)      │          │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘          │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🏠 Dashboard Module - Детальный поток

### 1. Инициализация страницы
```
DashboardPage Mount → useEffect → API Calls → State Update → Render
       │               │           │           │            │
       ▼               ▼           ▼           ▼            ▼
┌─────────────┐ ┌─────────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│ Component   │ │ Lifecycle   │ │ Stats   │ │ Metrics │ │ UI      │
│  Mount      │ │  Hook       │ │  Fetch  │ │  State  │ │ Update  │
└─────────────┘ └─────────────┘ └─────────┘ └─────────┘ └─────────┘
```

### 2. Загрузка метрик
```
DashboardMetrics → useEffect → API Calls → Data Processing → Display
       │             │           │           │               │
       ▼             ▼           ▼           ▼               ▼
┌─────────────┐ ┌─────────────┐ ┌─────────┐ ┌─────────────┐ ┌─────────┐
│ Component   │ │ Dependency  │ │ Gateway │ │ Transform   │ │ Render  │
│  Init       │ │  Array      │ │  Route  │ │  & Format   │ │ Metrics │
└─────────────┘ └─────────────┘ └─────────┘ └─────────────┘ └─────────┘
```

### 3. Обновление статуса системы
```
StatusIndicator → Timer → API Check → Status Update → Icon Change
       │           │         │           │             │
       ▼           ▼         ▼           ▼             ▼
┌─────────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────┐ ┌─────────┐
│ Status      │ │ Interval│ │ Health  │ │ State       │ │ Visual  │
│  Display    │ │  (30s)  │ │  Check  │ │  Update     │ │ Update  │
└─────────────┘ └─────────┘ └─────────┘ └─────────────┘ └─────────┘
```

---

## 💬 Chat Module - Детальный поток

### 1. Отправка сообщения
```
User Input → Form Submit → Event Handler → API Call → Response → UI Update
     │           │            │            │          │          │
     ▼           ▼            ▼            ▼          ▼          ▼
┌─────────┐ ┌─────────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│ Text    │ │ Button      │ │ Handle  │ │ POST    │ │ LLM     │ │ Message │
│ Input   │ │  Click      │ │ Submit  │ │ /chat   │ │ Response│ │ Display │
└─────────┘ └─────────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘
```

### 2. Потоковая генерация
```
Stream Request → WebSocket → Chunk Processing → Real-time Update → Complete
       │            │            │                │                │
       ▼            ▼            ▼                ▼                ▼
┌─────────────┐ ┌─────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────┐
│ Stream      │ │ Socket  │ │ Chunk       │ │ State       │ │ Final   │
│  Init       │ │  Connect│ │  Handler    │ │  Update     │ │ Message │
└─────────────┘ └─────────┘ └─────────────┘ └─────────────┘ └─────────┘
```

### 3. Выбор модели
```
Model Select → Dropdown → State Update → API Config → Request Headers
     │           │           │            │            │
     ▼           ▼           ▼            ▼            ▼
┌─────────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────┐ ┌─────────┐
│ Model       │ │ Change  │ │ Selected│ │ API         │ │ Headers │
│  List       │ │  Event  │ │  Model  │ │  Config     │ │ Update  │
└─────────────┘ └─────────┘ └─────────┘ └─────────────┘ └─────────┘
```

---

## 🤖 NTD Consultation Module - Детальный поток

### 1. Консультация по НТД
```
User Query → Form Submit → API Call → RAG Search → Document Retrieval → Response
     │           │            │          │            │                │
     ▼           ▼            ▼          ▼            ▼                ▼
┌─────────┐ ┌─────────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────┐ ┌─────────┐
│ Question│ │ Submit      │ │ POST    │ │ Vector  │ │ Content     │ │ Answer  │
│  Input  │ │  Handler    │ │ /ntd    │ │ Search  │ │  Fetch      │ │ Display │
└─────────┘ └─────────────┘ └─────────┘ └─────────┘ └─────────────┘ └─────────┘
```

### 2. Поиск документов
```
Query → Embedding → Vector Search → Similarity → Document Fetch → Context
  │        │           │            │           │                │
  ▼        ▼           ▼            ▼           ▼                ▼
┌─────────┐ ┌─────────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────┐ ┌─────────┐
│ Text    │ │ BGE-M3      │ │ Qdrant  │ │ Score   │ │ PostgreSQL  │ │ Context │
│ Query   │ │  Model      │ │  Search │ │  Rank   │ │  Content    │ │  Build  │
└─────────┘ └─────────────┘ └─────────┘ └─────────┘ └─────────────┘ └─────────┘
```

### 3. Генерация ответа
```
Context + Query → Prompt → LLM → Response → Format → Display
     │              │       │        │          │        │
     ▼              ▼       ▼        ▼          ▼        ▼
┌─────────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│ Document    │ │ System  │ │ GPT-OSS │ │ Generated│ │ Markdown│ │ UI      │
│  Context    │ │ Prompt  │ │  Model  │ │  Text    │ │  Format │ │ Update  │
└─────────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘
```

---

## 🧮 Calculations Module - Детальный поток

### 1. Структурные расчеты
```
Form Input → Validation → API Call → Calculation Engine → Result → Display
     │           │            │            │                │        │
     ▼           ▼            ▼            ▼                ▼        ▼
┌─────────┐ ┌─────────────┐ ┌─────────┐ ┌─────────────┐ ┌─────────┐ ┌─────────┐
│ User    │ │ Input       │ │ POST    │ │ Engineering │ │ Math    │ │ Result  │
│  Data   │ │  Check      │ │ /calc   │ │  Formulas   │ │ Result  │ │  Show   │
└─────────┘ └─────────────┘ └─────────┘ └─────────────┘ └─────────┘ └─────────┘
```

### 2. Электрические расчеты
```
Electrical Data → Form Submit → API → Calculation Service → Database → Result
       │             │           │           │                │        │
       ▼             ▼           ▼           ▼                ▼        ▼
┌─────────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────┐ ┌─────────┐ ┌─────────┐
│ Voltage,    │ │ Submit  │ │ Gateway │ │ Electrical  │ │ Store   │ │ Display │
│ Current,    │ │  Form   │ │  Route  │ │  Formulas   │ │ Result  │ │ Result  │
│ Power       │ │         │ │         │ │             │ │         │ │         │
└─────────────┘ └─────────┘ └─────────┘ └─────────────┘ └─────────┘ └─────────┘
```

### 3. Тепловые расчеты
```
Thermal Data → Validation → API → Calculation Engine → Heat Transfer → Result
      │           │          │           │                │            │
      ▼           ▼          ▼           ▼                ▼            ▼
┌─────────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────┐
│ Temperature,│ │ Input   │ │ Gateway │ │ Thermal     │ │ Heat        │ │ Display │
│ Heat Flux,  │ │ Check   │ │  Route  │ │  Analysis   │ │ Transfer    │ │ Result  │
│ Material    │ │         │ │         │ │             │ │ Calculation │ │         │
└─────────────┘ └─────────┘ └─────────┘ └─────────────┘ └─────────────┘ └─────────┘
```

---

## 📋 Normcontrol Module - Детальный поток

### 1. Загрузка документа для проверки
```
File Upload → Form Submit → API → Document Parser → Chunking → Storage
     │           │            │         │              │          │
     ▼           ▼            ▼         ▼              ▼          ▼
┌─────────┐ ┌─────────────┐ ┌─────────┐ ┌─────────────┐ ┌─────────┐ ┌─────────┐
│ PDF/    │ │ Submit      │ │ POST    │ │ Parse       │ │ Text    │ │ Save to │
│ DOC     │ │  Handler    │ │ /upload │ │ Content     │ │ Chunks  │ │ Database│
└─────────┘ └─────────────┘ └─────────┘ └─────────────┘ └─────────┘ └─────────┘
```

### 2. Проверка норм
```
Document → Rule Engine → Norm Checking → Violation Detection → Report → Display
    │           │            │                │                │        │
    ▼           ▼            ▼                ▼                ▼        ▼
┌─────────┐ ┌─────────────┐ ┌─────────┐ ┌─────────────┐ ┌─────────┐ ┌─────────┐
│ Content │ │ Rule        │ │ Norm    │ │ Violation  │ │ Report  │ │ UI      │
│  Chunks │ │  Processing │ │  Check  │ │  Detection  │ │ Generate│ │ Update  │
└─────────┘ └─────────────┘ └─────────┘ └─────────────┘ └─────────┘ └─────────┘
```

### 3. Результаты проверки
```
Check Results → Database → API → Frontend → State Update → Display
      │           │          │         │           │            │
      ▼           ▼          ▼         ▼           ▼            ▼
┌─────────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│ Violations, │ │ Store   │ │ GET     │ │ Receive │ │ Update  │ │ Show    │
│ Warnings,   │ │ Results │ │ /results│ │ Data    │ │ State   │ │ Results │
│ Compliance  │ │         │ │         │ │         │ │         │ │         │
└─────────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘
```

---

## 📚 Documents Module - Детальный поток

### 1. Управление документами
```
Document CRUD → API → Gateway → RAG Service → Database → Response → UI Update
       │         │       │           │           │          │            │
       ▼         ▼       ▼           ▼           ▼          ▼            ▼
┌─────────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────┐ ┌─────────┐ ┌─────────┐
│ Create,     │ │ HTTP    │ │ Auth &  │ │ Document    │ │ Store/  │ │ Success │
│ Read,       │ │ Request │ │ Route   │ │ Processing  │ │ Retrieve│ │ Error   │
│ Update,     │ │         │ │         │ │             │ │         │ │ Message │
│ Delete      │ │         │ │         │ │             │ │         │ │         │
└─────────────┘ └─────────┘ └─────────┘ └─────────────┘ └─────────┘ └─────────┘
```

### 2. Переиндексация документов
```
Reindex Request → API → RAG Service → Document Processing → Vector Update → Status
       │            │         │              │                │            │
       ▼            ▼         ▼              ▼                ▼            ▼
┌─────────────┐ ┌─────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────┐ ┌─────────┐
│ Reindex     │ │ POST    │ │ Document    │ │ Chunking &  │ │ Qdrant  │ │ Progress│
│ Button      │ │ /reindex│ │ Fetch       │ │ Embedding   │ │ Update  │ │ Display │
└─────────────┘ └─────────┘ └─────────────┘ └─────────────┘ └─────────┘ └─────────┘
```

### 3. Поиск документов
```
Search Query → API → RAG Service → Vector Search → Document Fetch → Results
      │          │         │            │              │                │
      ▼          ▼         ▼            ▼              ▼                ▼
┌─────────────┐ ┌─────────┐ ┌─────────────┐ ┌─────────┐ ┌─────────────┐ ┌─────────┐
│ Search      │ │ GET     │ │ Query       │ │ Vector  │ │ Content     │ │ Display │
│ Input       │ │ /search │ │ Processing  │ │ Search  │ │ Retrieval   │ │ Results │
└─────────────┘ └─────────┘ └─────────────┘ └─────────┘ └─────────────┘ └─────────┘
```

---

## 🔍 Ollama Monitor Module - Детальный поток

### 1. Проверка статуса Ollama
```
Status Check → Timer → API Call → Ollama Check → Response → State Update → Display
      │          │         │            │            │          │            │
      ▼          ▼         ▼            ▼            ▼          ▼            ▼
┌─────────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│ Component   │ │ 30s     │ │ GET     │ │ Ollama      │ │ Status  │ │ Update  │ │ Visual  │
│  Mount      │ │ Interval│ │ /health │ │ API Check   │ │ Data    │ │ State   │ │ Update  │
└─────────────┘ └─────────┘ └─────────┘ └─────────────┘ └─────────┘ └─────────┘ └─────────┘
```

### 2. Получение списка моделей
```
Models Request → API → Ollama API → Model Info → Processing → Display
      │          │         │            │            │            │
      ▼          ▼         ▼            ▼            ▼            ▼
┌─────────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────┐ ┌─────────┐ ┌─────────┐
│ Models      │ │ GET     │ │ Ollama  │ │ Model       │ │ Format  │ │ Model   │
│ Button      │ │ /models │ │ /api/tags│ │ Information │ │ Data    │ │ List    │
└─────────────┘ └─────────┘ └─────────┘ └─────────────┘ └─────────┘ └─────────┘
```

### 3. Тестирование чата
```
Chat Test → Form Submit → API → Ollama Generate → Response → Display
     │           │            │         │              │          │
     ▼           ▼            ▼         ▼              ▼          ▼
┌─────────┐ ┌─────────────┐ ┌─────────┐ ┌─────────────┐ ┌─────────┐ ┌─────────┐
│ Test    │ │ Submit      │ │ POST    │ │ GPT-OSS     │ │ Generated│ │ Show    │
│ Message │ │  Handler    │ │ /chat   │ │  Model      │ │ Response │ │ Result  │
└─────────┘ └─────────────┘ └─────────┘ └─────────────┘ └─────────┘ └─────────┘
```

---

## 🔐 Authentication Module - Детальный поток

### 1. Вход в систему
```
Login Form → Submit → Keycloak → OAuth Flow → JWT Token → Frontend State → Redirect
     │         │         │           │            │            │            │
     ▼         ▼         ▼           ▼            ▼            ▼            ▼
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│ Username│ │ Form    │ │ OAuth   │ │ Redirect│ │ Token   │ │ Store   │ │ Navigate│
│ Password│ │ Submit  │ │ 2.0     │ │  Flow   │ │ Receive │ │ Token   │ │ to App  │
└─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘
```

### 2. Проверка токена
```
Token Check → API Call → Gateway → JWT Validation → Response → State Update
      │          │         │            │              │          │
      ▼          ▼         ▼            ▼              ▼          ▼
┌─────────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────┐ ┌─────────┐ ┌─────────┐
│ Stored      │ │ GET     │ │ Gateway │ │ JWT         │ │ Valid/  │ │ Update  │
│ Token       │ │ /api    │ │ Route   │ │ Decode      │ │ Invalid │ │ State   │
└─────────────┘ └─────────┘ └─────────┘ └─────────────┘ └─────────┘ └─────────┘
```

### 3. Обновление токена
```
Token Expiry → Refresh Request → Keycloak → New Token → Update State → Continue
      │            │               │           │            │            │
      ▼            ▼               ▼           ▼            ▼            ▼
┌─────────────┐ ┌─────────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│ Expiry      │ │ Refresh     │ │ OAuth   │ │ New     │ │ Update  │ │ Resume  │
│ Check       │ │ Token       │ │ Token   │ │ Token   │ │ State   │ │ Session │
└─────────────┘ └─────────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘
```

---

## 📊 Error Handling - Детальный поток

### 1. Обработка API ошибок
```
API Error → Error Handler → Error State → User Notification → Recovery Action
     │           │              │              │                │
     ▼           ▼              ▼              ▼                ▼
┌─────────┐ ┌─────────────┐ ┌─────────┐ ┌─────────────┐ ┌─────────────┐
│ HTTP    │ │ Try-Catch   │ │ Error   │ │ Toast/Alert │ │ Retry/      │
│ Error   │ │ Block       │ │ State   │ │ Display     │ │ Fallback    │
└─────────┘ └─────────────┘ └─────────┘ └─────────────┘ └─────────────┘
```

### 2. Обработка сетевых ошибок
```
Network Error → Connection Check → Retry Logic → Fallback → User Notification
       │            │               │           │          │
       ▼            ▼               ▼           ▼          ▼
┌─────────────┐ ┌─────────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────┐
│ Connection  │ │ Ping        │ │ Retry   │ │ Offline │ │ Error       │
│ Failed      │ │ Check       │ │ Attempt │ │ Mode    │ │ Message     │
└─────────────┘ └─────────────┘ └─────────┘ └─────────┘ └─────────────┘
```

---

## 🚀 Performance Optimization - Детальный поток

### 1. Lazy Loading
```
Route Change → Component Check → Dynamic Import → Loading State → Component Render
      │            │                │              │              │
      ▼            ▼                ▼              ▼              ▼
┌─────────────┐ ┌─────────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────┐
│ Navigation  │ │ Component   │ │ Import  │ │ Loading │ │ Render      │
│  Event      │ │  Check      │ │  Code   │ │ Spinner │ │ Component   │
└─────────────┘ └─────────────┘ └─────────┘ └─────────┘ └─────────────┘
```

### 2. Caching
```
API Request → Cache Check → Cache Hit/Miss → API Call → Cache Update → Response
      │           │            │              │           │            │
      ▼           ▼            ▼              ▼           ▼            ▼
┌─────────────┐ ┌─────────┐ ┌─────────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│ Request     │ │ Cache   │ │ Hit: Return│ │ Miss:   │ │ Store   │ │ Return  │
│ Initiated   │ │ Lookup  │ │ Cached     │ │ API     │ │ Result  │ │ Data    │
│             │ │         │ │ Data       │ │ Call    │ │ in Cache│ │         │
└─────────────┘ └─────────┘ └─────────────┘ └─────────┘ └─────────┘ └─────────┘
```

### 3. Debouncing
```
User Input → Timer Start → Timer Reset → Timer Complete → API Call → Response
      │          │            │            │            │          │
      ▼          ▼            ▼            ▼            ▼          ▼
┌─────────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│ Key Press   │ │ Start   │ │ New     │ │ Timer   │ │ Make    │ │ Update  │
│ Event       │ │ Timer   │ │ Input   │ │ Expires │ │ API     │ │ UI      │
└─────────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘
```

---

## 📝 Заключение

Эти детальные диаграммы потоков данных показывают, как каждый функциональный модуль фронтэнда AI-NK обрабатывает пользовательские запросы, взаимодействует с backend сервисами и обновляет пользовательский интерфейс.

Ключевые особенности архитектуры:

1. **Модульность**: Каждый модуль имеет четко определенные потоки данных
2. **Единообразие**: Все модули следуют схожим паттернам обработки
3. **Обработка ошибок**: Централизованная обработка ошибок на всех уровнях
4. **Производительность**: Оптимизация через кэширование, lazy loading и debouncing
5. **Масштабируемость**: Легкое добавление новых модулей и функций

Такая архитектура обеспечивает надежную, производительную и легко поддерживаемую систему.
