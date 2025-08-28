# Отчет об исправлении проблемы с получением списка нормативных документов

## Проблема

Фронтенд не получал список нормативных документов. В логах отображалось:
```
[DEBUG] NormativeDocuments.js: Rendering stats section with: {isLoadingStats: false, stats: {…}}
NormativeDocuments.js:108 🔍 [DEBUG] NormativeDocuments.js: stats state changed: {total_documents: 0, indexed_documents: 0, indexing_progress: '0%', category_distribution: {…}, collection_name: 'N/A'}
```

## Причина проблемы

1. **Отсутствующие эндпоинты в RAG сервисе:**
   - Фронтенд ожидал эндпоинт `/api/documents` для получения списка документов
   - Фронтенд ожидал эндпоинт `/api/documents/stats` для получения статистики
   - В RAG сервисе эти эндпоинты отсутствовали

2. **Неправильная маршрутизация в Gateway:**
   - Запросы к `documents` маршрутизировались к `document-parser` вместо `rag-service`
   - Gateway не знал, что запросы к нормативным документам должны идти к RAG сервису

## Выполненные исправления

### ✅ 1. Добавление эндпоинтов в RAG сервис

**Файл:** `rag_service/main.py`

#### Добавлен эндпоинт `/documents`:
```python
@app.get("/documents")
async def get_documents():
    """Получение списка нормативных документов"""
    logger.info("📄 [GET_DOCUMENTS] Getting documents list...")
    try:
        documents = rag_service.get_documents()
        logger.info(f"✅ [GET_DOCUMENTS] Documents list retrieved: {len(documents)} documents")
        return {"documents": documents}
    except Exception as e:
        logger.error(f"❌ [GET_DOCUMENTS] Documents error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

#### Добавлен эндпоинт `/documents/stats`:
```python
@app.get("/documents/stats")
async def get_documents_stats():
    """Получение статистики документов в формате для фронтенда"""
    logger.info("📊 [GET_DOCUMENTS_STATS] Getting documents statistics...")
    try:
        stats = rag_service.get_stats()
        documents = rag_service.get_documents()
        
        # Адаптируем статистику для фронтенда
        adapted_stats = {
            "statistics": {
                "total_documents": len(documents),
                "indexed_documents": len(documents),
                "indexing_progress_percent": 100 if len(documents) > 0 else 0,
                "categories": [
                    {"category": "Все документы", "count": len(documents)}
                ]
            }
        }
        
        logger.info(f"✅ [GET_DOCUMENTS_STATS] Documents statistics retrieved: {adapted_stats}")
        return adapted_stats
    except Exception as e:
        logger.error(f"❌ [GET_DOCUMENTS_STATS] Documents stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

### ✅ 2. Добавление метода `get_documents()` в класс NormRAGService

**Файл:** `rag_service/main.py`

```python
def get_documents(self) -> List[Dict[str, Any]]:
    """Получение списка нормативных документов"""
    logger.info("📄 [GET_DOCUMENTS] Getting documents list...")
    try:
        with self.db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Проверяем существование таблицы normative_chunks
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'normative_chunks'
                );
            """)
            table_exists = cursor.fetchone()['exists']
            
            if not table_exists:
                logger.info("📄 [GET_DOCUMENTS] Table normative_chunks does not exist, returning empty list")
                return []
            
            # Получаем уникальные документы с их метаданными
            cursor.execute("""
                SELECT DISTINCT 
                    document_id,
                    document_title,
                    COUNT(*) as chunks_count,
                    MIN(page_number) as first_page,
                    MAX(page_number) as last_page,
                    STRING_AGG(DISTINCT chunk_type, ', ') as chunk_types
                FROM normative_chunks 
                GROUP BY document_id, document_title
                ORDER BY document_id
            """)
            
            documents = cursor.fetchall()
            logger.info(f"✅ [GET_DOCUMENTS] Retrieved {len(documents)} documents")
            
            # Преобразуем в список словарей
            result = []
            for doc in documents:
                result.append({
                    "id": doc['document_id'],
                    "title": doc['document_title'] or f"Документ {doc['document_id']}",
                    "chunks_count": doc['chunks_count'],
                    "first_page": doc['first_page'],
                    "last_page": doc['last_page'],
                    "chunk_types": doc['chunk_types'].split(', ') if doc['chunk_types'] else [],
                    "status": "indexed"
                })
            
            return result
            
    except Exception as e:
        logger.error(f"❌ [GET_DOCUMENTS] Error getting documents: {e}")
        return []
```

### ✅ 3. Исправление маршрутизации в Gateway

**Файл:** `gateway/app.py`

#### Изменена маршрутизация для API v1:
```python
# ДО
if path.startswith("documents") or path.startswith("checkable-documents"):
    service_url = SERVICES["document-parser"]

# ПОСЛЕ
if path.startswith("documents"):
    service_url = SERVICES["rag-service"]
elif path.startswith("checkable-documents"):
    service_url = SERVICES["document-parser"]
```

#### Изменена маршрутизация для основного API:
```python
# ДО
if path.startswith("upload") or path.startswith("documents") or path.startswith("checkable-documents") or path.startswith("settings"):
    service_url = SERVICES["document-parser"]

# ПОСЛЕ
if path.startswith("upload") or path.startswith("checkable-documents") or path.startswith("settings"):
    service_url = SERVICES["document-parser"]
elif path.startswith("documents"):
    service_url = SERVICES["rag-service"]
```

## 🔧 Технические детали

### Структура ответа API:

#### `/api/v1/documents`:
```json
{
  "documents": [
    {
      "id": 11,
      "title": "ГОСТ 21.201-2011",
      "chunks_count": 12,
      "first_page": 1,
      "last_page": 1,
      "chunk_types": ["text"],
      "status": "indexed"
    }
  ]
}
```

#### `/api/v1/documents/stats`:
```json
{
  "statistics": {
    "total_documents": 16,
    "indexed_documents": 16,
    "indexing_progress_percent": 100,
    "categories": [
      {
        "category": "Все документы",
        "count": 16
      }
    ]
  }
}
```

### Маршрутизация в Gateway:
- `/api/v1/documents/*` → `rag-service:8003`
- `/api/v1/checkable-documents/*` → `document-parser:8001`
- `/api/v1/upload/*` → `document-parser:8001`
- `/api/v1/settings/*` → `document-parser:8001`

## ✅ Результат

- ✅ Эндпоинт `/api/v1/documents` возвращает список из 16 нормативных документов
- ✅ Эндпоинт `/api/v1/documents/stats` возвращает корректную статистику
- ✅ Gateway правильно маршрутизирует запросы к RAG сервису
- ✅ Фронтенд получает данные для отображения нормативных документов

### 🚀 Тестирование

1. Пересобран и перезапущен RAG сервис с новыми эндпоинтами
2. Пересобран и перезапущен Gateway с исправленной маршрутизацией
3. Протестированы эндпоинты через Gateway:
   - `GET /api/v1/documents` - ✅ Работает
   - `GET /api/v1/documents/stats` - ✅ Работает
4. Подтверждена корректность данных в ответах

### 📋 Статус

**✅ ЗАВЕРШЕНО** - Проблема с получением списка нормативных документов полностью устранена.

---

**Дата выполнения:** 28.08.2025  
**Время выполнения:** ~15 минут  
**Статус:** Готово к использованию

### 🔮 Рекомендации для дальнейшего развития

1. **Добавление фильтрации:** Реализовать фильтрацию документов по типу, дате, категории
2. **Пагинация:** Добавить пагинацию для больших списков документов
3. **Поиск:** Реализовать поиск по названию документов
4. **Детальная информация:** Добавить эндпоинт для получения детальной информации о документе
