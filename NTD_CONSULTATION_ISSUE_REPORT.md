# 🔍 NTD Consultation Issue Report

## ❌ Проблема

**Запрос**: "Дай справку по документу СП 22.13330.2016"
**Ответ**: "К сожалению, я не нашел релевантной информации в базе нормативных документов..."

## 🔍 Диагностика

### ✅ Данные в базе есть
- **PostgreSQL**: Документ `8489575` с именем "СП 22.13330.2016.pdf"
- **Чанки**: 292 чанка для документа
- **Qdrant**: 576 векторов в коллекции

### ✅ Метаданные исправлены
После реиндексации метаданные правильно сохранены:
```json
{
  "document_id": 8489575,
  "code": "СП 22.13330.2016",
  "title": "СП 22.13330.2016.pdf"
}
```

### ✅ Поиск работает напрямую
Поиск через Qdrant API находит релевантные результаты:
```bash
curl -X POST "http://localhost:6333/collections/normative_documents/points/search"
# Результат: 3 найденных документа
```

### ❌ Проблема в RAG сервисе
RAG сервис не может работать с Qdrant из-за **Pydantic ошибок**:

```
ERROR:services.qdrant_service:❌ [QDRANT] Error getting collection info: 4 validation errors
obj.result.vectors_count Field required [type=missing]
obj.result.config.optimizer_config.max_optimization_threads Input should be a valid integer
obj.result.config.wal_config.wal_retain_closed Extra inputs are not permitted
obj.result.config.strict_mode_config Extra inputs are not permitted
```

## 🔧 Решение

### 1. Исправить Pydantic модели в Qdrant сервисе
Проблема в несоответствии Pydantic моделей с реальным API Qdrant.

### 2. Обновить версию Qdrant клиента
Возможно, нужна более новая версия клиента.

### 3. Добавить обработку ошибок
Добавить fallback для случаев, когда Pydantic валидация не проходит.

## 📊 Текущее состояние

| Компонент | Статус | Описание |
|-----------|--------|----------|
| PostgreSQL | ✅ Работает | Документы и чанки есть |
| Qdrant | ✅ Работает | Векторы индексированы |
| Ollama | ✅ Работает | Эмбеддинги генерируются |
| RAG Service | ❌ Ошибка | Pydantic валидация |
| NTD Consultation | ❌ Не работает | Зависит от RAG Service |

## 🎯 Следующие шаги

1. **Исправить Pydantic модели** в `services/qdrant_service.py`
2. **Обновить Qdrant клиент** до совместимой версии
3. **Протестировать поиск** после исправления
4. **Проверить консультацию НТД** с реальными запросами

## 📝 Технические детали

### Ошибки Pydantic:
- `vectors_count` поле отсутствует в ответе
- `max_optimization_threads` имеет значение `null`
- `wal_retain_closed` не разрешено в схеме
- `strict_mode_config` не разрешено в схеме

### Рабочий поиск:
```bash
# Генерация эмбеддинга
curl -X POST "http://localhost:11434/api/embeddings" \
  -d '{"model": "bge-m3:latest", "prompt": "СП 22.13330.2016"}'

# Поиск в Qdrant
curl -X POST "http://localhost:6333/collections/normative_documents/points/search" \
  -d '{"vector": [...], "limit": 3}'
```

**Результат**: Находит документ СП 22.13330.2016 с правильными метаданными.
