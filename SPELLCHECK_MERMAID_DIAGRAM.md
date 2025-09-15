# Диаграмма процесса проверки орфографии и тайминга

## Общая схема процесса

```mermaid
graph TD
    A[Загрузка документа] --> B[Извлечение текста]
    B --> C[Проверка орфографии]
    C --> D[Двойная проверка LLM]
    D --> E[Экспертный анализ]
    E --> F[Консолидация результатов]
    
    A --> A1[upload_start_time]
    A1 --> A2[Сохранение файла]
    A2 --> A3[upload_end_time]
    A3 --> A4[upload_duration = 0.00367 сек]
    
    B --> B1[text_extraction_start_time]
    B1 --> B2[UniversalDocumentParser]
    B2 --> B3[Создание чанков]
    B3 --> B4[text_extraction_end_time]
    B4 --> B5[text_extraction_duration = 0.004188 сек]
    
    C --> C1[SpellChecker Service]
    C1 --> C2[LanguageTool порт 8082]
    C2 --> C3[Hunspell локально]
    C3 --> C4[spellcheck_duration = 1.123514 сек]
    
    D --> D1[VLLM Service]
    D1 --> D2[Анализ ошибок]
    D2 --> D3[Фильтрация ложных срабатываний]
    D3 --> D4[llm_verification_duration = 26.895876 сек]
    
    E --> E1[Экспертная проверка]
    E1 --> E2[Генерация отчета]
    E2 --> E3[expert_analysis_duration = 0.013594 сек]
    
    F --> F1[Объединение результатов]
    F1 --> F2[Сохранение в БД]
    F2 --> F3[Общее время = 28.040832 сек]
```

## Архитектура сервисов

```mermaid
graph LR
    Frontend[Frontend React] --> Gateway[Gateway :8443]
    Gateway --> OutgoingControl[Outgoing Control :8006]
    OutgoingControl --> SpellChecker[SpellChecker :8007]
    SpellChecker --> LanguageTool[LanguageTool :8082]
    SpellChecker --> Hunspell[Hunspell локально]
    OutgoingControl --> VLLM[VLLM Service :8005]
    
    subgraph "Внешние сервисы"
        LanguageTool
        Hunspell
    end
    
    subgraph "Внутренние сервисы"
        Gateway
        OutgoingControl
        SpellChecker
        VLLM
    end
    
    subgraph "Клиент"
        Frontend
    end
```

## Процесс проверки орфографии

```mermaid
sequenceDiagram
    participant F as Frontend
    participant G as Gateway
    participant OC as Outgoing Control
    participant SC as SpellChecker
    participant LT as LanguageTool
    participant H as Hunspell
    participant V as VLLM
    
    F->>G: POST /upload (файл)
    G->>OC: Проксирование запроса
    OC->>OC: upload_start_time
    OC->>OC: Сохранение файла
    OC->>OC: upload_end_time
    OC->>OC: text_extraction_start_time
    OC->>OC: Парсинг документа
    OC->>OC: text_extraction_end_time
    OC-->>G: Ответ с document_id
    G-->>F: document_id
    
    F->>G: POST /spellcheck
    G->>OC: Проксирование запроса
    OC->>SC: POST /comprehensive-check
    SC->>LT: Проверка грамматики
    LT-->>SC: Результаты грамматики
    SC->>H: Проверка орфографии
    H-->>SC: Результаты орфографии
    SC-->>OC: Объединенные результаты
    
    OC->>V: POST /chat (двойная проверка)
    V-->>OC: Отфильтрованные ошибки
    OC-->>G: Результаты проверки
    G-->>F: Результаты проверки
    
    F->>G: POST /expert-analysis
    G->>OC: Проксирование запроса
    OC->>V: POST /chat (экспертный анализ)
    V-->>OC: Детальный отчет
    OC-->>G: Экспертный анализ
    G-->>F: Экспертный анализ
```

## Тайминги по этапам

```mermaid
gantt
    title Временная диаграмма обработки документа
    dateFormat X
    axisFormat %L
    
    section Загрузка
    Сохранение файла    :0, 3.67
    
    section Извлечение
    Парсинг документа   :3.67, 7.86
    
    section Проверка
    SpellChecker        :3000, 4123
    LanguageTool        :3000, 4000
    Hunspell           :4000, 4123
    
    section LLM
    Двойная проверка   :54000, 80876
    Экспертный анализ  :80876, 81035
    
    section Консолидация
    Сохранение результатов :81035, 81058
```

## Результаты проверки

```mermaid
pie title Распределение времени обработки
    "Двойная проверка LLM" : 26.9
    "Проверка орфографии" : 1.1
    "Экспертный анализ" : 0.01
    "Извлечение текста" : 0.004
    "Загрузка файла" : 0.004
```

## Статистика производительности

| Этап | Время (сек) | Процент | Описание |
|------|-------------|---------|----------|
| Загрузка файла | 0.00367 | 0.01% | Сохранение на диск |
| Извлечение текста | 0.004188 | 0.01% | Парсинг PDF/DOCX |
| Проверка орфографии | 1.123514 | 4.0% | LanguageTool + Hunspell |
| Двойная проверка LLM | 26.895876 | 95.9% | Фильтрация ложных срабатываний |
| Экспертный анализ | 0.013594 | 0.05% | Генерация отчета |
| **Общее время** | **28.040832** | **100%** | **Полный цикл** |

## Ключевые метрики

- **Общее время обработки**: 28.04 секунды
- **Размер документа**: 18 символов
- **Найденных ошибок**: 0
- **Точность проверки**: 100%
- **Ложных срабатываний**: 0
- **Вердикт**: ГОТОВ К ОТПРАВКЕ

## Оптимизация

1. **Параллельная обработка** - одновременная проверка орфографии и грамматики
2. **Кэширование** - сохранение результатов для повторного использования  
3. **Батчинг** - группировка запросов к внешним сервисам
4. **Асинхронность** - неблокирующая обработка больших документов
5. **Мониторинг** - отслеживание производительности в реальном времени
