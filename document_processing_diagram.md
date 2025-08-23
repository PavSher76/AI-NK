# Диаграмма потоков обработки документов

## 1. Нормативный документ

```mermaid
graph TD
    A[Фронтенд: Загрузка файла] --> B[Gateway: /api/upload]
    B --> C[Document Parser: upload_document]
    C --> D{Проверка дубликатов}
    D -->|Новый| E[Сохранение файла]
    D -->|Существующий| F[Ошибка: Документ уже существует]
    E --> G[Создание записи в БД]
    G --> H[Фоновая задача: process_document_async]
    H --> I[Парсинг документа]
    I --> J[Определение категории]
    J --> K[save_normative_document]
    K --> L[Сохранение в extracted_elements]
    L --> M[RAG Service: /index]
    M --> N[Чанкинг документа]
    N --> O[Создание эмбеддингов BGE-M3]
    O --> P[Индексация в Qdrant]
    O --> Q[Индексация в PostgreSQL]
    P --> R[Готов к поиску]
    Q --> R
```

## 2. Проверяемый документ

```mermaid
graph TD
    A[Фронтенд: Загрузка файла] --> B[Gateway: /api/upload/checkable]
    B --> C[Document Parser: upload_checkable_document]
    C --> D{Проверка дубликатов}
    D -->|Новый| E[Парсинг документа]
    D -->|Существующий| F[Ошибка: Документ уже существует]
    E --> G[Определение категории]
    G --> H[save_checkable_document]
    H --> I[Сохранение в checkable_documents]
    I --> J[Сохранение в checkable_elements]
    J --> K[Автоматическая проверка нормоконтроля]
    K --> L[Разбиение на страницы]
    L --> M[Для каждой страницы]
    M --> N[Получение промпта из настроек]
    N --> O[Форматирование промпта]
    O --> P[LLM: /v1/chat/completions]
    P --> Q[VLLM Adapter]
    Q --> R[Ollama: llama3.1:8b]
    R --> S[Парсинг ответа LLM]
    S --> T[Сохранение в norm_control_results]
    T --> U[Создание review_report]
    U --> V[Готов к просмотру результатов]
```

## 3. Поиск по нормативным документам

```mermaid
graph TD
    A[Запрос поиска] --> B[RAG Service: /search]
    B --> C[Создание эмбеддинга запроса]
    C --> D[Векторный поиск в Qdrant]
    C --> E[BM25 поиск в PostgreSQL]
    D --> F[Результаты векторного поиска]
    E --> G[Результаты BM25 поиска]
    F --> H[Объединение результатов]
    G --> H
    H --> I[Применение фильтров]
    I --> J[Сортировка по релевантности]
    J --> K[Возврат результатов]
```

## 4. Архитектура системы

```mermaid
graph TB
    subgraph "Frontend"
        A[React App]
    end
    
    subgraph "Gateway"
        B[API Gateway]
    end
    
    subgraph "Services"
        C[Document Parser]
        D[RAG Service]
        E[Rule Engine]
        F[VLLM Adapter]
    end
    
    subgraph "Databases"
        G[PostgreSQL]
        H[Qdrant]
    end
    
    subgraph "LLM"
        I[Ollama]
    end
    
    A --> B
    B --> C
    B --> D
    B --> E
    B --> F
    C --> G
    D --> G
    D --> H
    E --> G
    F --> I
```

## 5. Поток данных в системе

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant G as Gateway
    participant DP as Document Parser
    participant RAG as RAG Service
    participant DB as PostgreSQL
    participant QD as Qdrant
    participant LLM as LLM (Ollama)
    
    Note over U,LLM: Нормативный документ
    U->>F: Загружает файл
    F->>G: POST /api/upload
    G->>DP: Проксирование
    DP->>DB: Сохранение метаданных
    DP->>RAG: POST /index
    RAG->>RAG: Чанкинг + эмбеддинги
    RAG->>QD: Индексация векторов
    RAG->>DB: Индексация чанков
    
    Note over U,LLM: Проверяемый документ
    U->>F: Загружает файл
    F->>G: POST /api/upload/checkable
    G->>DP: Проксирование
    DP->>DB: Сохранение документа
    DP->>LLM: Автоматическая проверка
    LLM->>DP: Результаты проверки
    DP->>DB: Сохранение результатов
```

## 6. Компоненты и их взаимодействие

```mermaid
graph LR
    subgraph "Входные данные"
        A[PDF/DOCX/TXT файлы]
        B[DWG/IFC файлы]
    end
    
    subgraph "Обработка"
        C[Document Parser]
        D[RAG Service]
        E[LLM Analysis]
    end
    
    subgraph "Хранение"
        F[PostgreSQL - метаданные]
        G[PostgreSQL - чанки]
        H[Qdrant - векторы]
    end
    
    subgraph "Результаты"
        I[Индексированные документы]
        J[Результаты нормоконтроля]
        K[Отчеты]
    end
    
    A --> C
    B --> C
    C --> D
    C --> E
    D --> G
    D --> H
    E --> J
    F --> I
    G --> I
    H --> I
    J --> K
```
