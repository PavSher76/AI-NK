# Схема представления ответа на запрос "Консультация НТД"

## Общая структура ответа

```json
{
  "status": "success" | "warning" | "error",
  "response": "string",
  "sources": [
    {
      "title": "string",
      "filename": "string", 
      "page": "string",
      "section": "string",
      "document_code": "string",
      "content_preview": "string",
      "relevance_score": "number"
    }
  ],
  "confidence": "number",
  "documents_used": "number",
  "structured_context": {
    "query": "string",
    "timestamp": "string",
    "context": [
      {
        "id": "string",
        "score": "number",
        "document_id": "number",
        "chunk_id": "string",
        "content": "string",
        "metadata": "object",
        "document_title": "string",
        "chapter": "string",
        "section": "string",
        "page": "number",
        "doc": "number",
        "snippet": "string"
      }
    ],
    "meta_summary": {
      "total_results": "number",
      "avg_score": "number",
      "search_method": "string"
    }
  },
  "timestamp": "string",
  "missing_document": "string" // только при status: "warning"
}
```

## Детальное описание полей

### Основные поля

| Поле | Тип | Описание |
|------|-----|----------|
| `status` | string | Статус обработки запроса: `success`, `warning`, `error` |
| `response` | string | Основной ответ системы на вопрос пользователя |
| `sources` | array | Массив источников (до 3 элементов) с релевантными документами |
| `confidence` | number | Уровень уверенности системы (0.0 - 1.0) |
| `documents_used` | number | Количество документов, использованных для формирования ответа |
| `timestamp` | string | Временная метка ответа в формате ISO 8601 |

### Поле sources (источники)

| Поле | Тип | Описание |
|------|-----|----------|
| `title` | string | Очищенное название документа |
| `filename` | string | Имя файла документа |
| `page` | string | Номер страницы |
| `section` | string | Раздел документа |
| `document_code` | string | Код документа (ГОСТ, СП и т.д.) |
| `content_preview` | string | Превью содержимого (до 200 символов) |
| `relevance_score` | number | Оценка релевантности (0.0 - 1.0) |

### Поле structured_context (структурированный контекст)

| Поле | Тип | Описание |
|------|-----|----------|
| `query` | string | Исходный запрос пользователя |
| `timestamp` | string | Временная метка поиска |
| `context` | array | Массив найденных фрагментов документов |
| `meta_summary` | object | Метаинформация о поиске |

### Поле context (фрагменты документов)

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | string | Уникальный идентификатор фрагмента |
| `score` | number | Оценка релевантности фрагмента |
| `document_id` | number | ID документа в базе данных |
| `chunk_id` | string | ID чанка в документе |
| `content` | string | Полное содержимое фрагмента |
| `metadata` | object | Дополнительные метаданные |
| `document_title` | string | Название документа |
| `chapter` | string | Глава документа |
| `section` | string | Раздел документа |
| `page` | number | Номер страницы |
| `doc` | number | ID документа (дублирует document_id) |
| `snippet` | string | Сниппет содержимого (дублирует content) |

### Поле meta_summary (метаинформация)

| Поле | Тип | Описание |
|------|-----|----------|
| `total_results` | number | Общее количество найденных результатов |
| `avg_score` | number | Средняя оценка релевантности |
| `search_method` | string | Метод поиска (например, "direct_hybrid_search") |

## Специальные случаи

### 1. Документ не найден (status: "warning")

```json
{
  "status": "warning",
  "response": "⚠️ **Внимание!** Запрашиваемый документ **ГОСТ 12345** отсутствует в системе...",
  "sources": [...],
  "confidence": 0.5,
  "documents_used": 1,
  "missing_document": "ГОСТ 12345",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### 2. Нет релевантной информации (status: "success")

```json
{
  "status": "success",
  "response": "К сожалению, я не нашел релевантной информации в базе нормативных документов...",
  "sources": [],
  "confidence": 0.0,
  "documents_used": 0,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### 3. Ошибка обработки (status: "error")

```json
{
  "status": "error",
  "response": "Произошла ошибка при обработке вашего запроса: ...",
  "sources": [],
  "confidence": 0.0,
  "documents_used": 0,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## Пример полного ответа

```json
{
  "status": "success",
  "response": "Согласно ГОСТ 2.306-68, графические обозначения материалов в сечениях должны соответствовать приведенным в таблице 1. Для металлов и твердых сплавов используется стандартное обозначение...",
  "sources": [
    {
      "title": "ГОСТ 2.306-68 Единая система конструкторской документации",
      "filename": "ГОСТ 2.306-68 Единая система конструкторской документации",
      "page": "1",
      "section": "1. Общие положения",
      "document_code": "ГОСТ 2.306-68",
      "content_preview": "Настоящий стандарт устанавливает графические обозначения материалов в сечениях и на фасадах...",
      "relevance_score": 0.95
    }
  ],
  "confidence": 0.95,
  "documents_used": 1,
  "structured_context": {
    "query": "как обозначать материалы в чертежах",
    "timestamp": "2024-01-01T12:00:00Z",
    "context": [
      {
        "id": "80693921_1_1",
        "score": 0.95,
        "document_id": 80693921,
        "chunk_id": "80693921_1_1",
        "content": "Настоящий стандарт устанавливает графические обозначения материалов...",
        "metadata": {},
        "document_title": "ГОСТ 2.306-68 Единая система конструкторской документации",
        "chapter": "1",
        "section": "1. Общие положения",
        "page": 1,
        "doc": 80693921,
        "snippet": "Настоящий стандарт устанавливает графические обозначения материалов..."
      }
    ],
    "meta_summary": {
      "total_results": 1,
      "avg_score": 0.95,
      "search_method": "direct_hybrid_search"
    }
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```
