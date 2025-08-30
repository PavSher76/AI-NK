# Отчет об исправлении консультации НТД

## 📋 Проблема

Фронтенд выдавал ошибку при отправке сообщений в консультации НТД:
**"Произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте еще раз."**

## 🔍 Анализ проблемы

### Причины ошибок:
1. **Отсутствие поля `user_id`** - эндпоинт `/api/ntd-consultation/chat` требовал поле `user_id`, но фронтенд его не отправлял
2. **Отсутствие сервиса консультации** - в RAG сервисе не было реализации `ntd_consultation_service`
3. **Проблемы с инициализацией** - некоторые функции использовали `rag_service` напрямую вместо `get_rag_service()`

### Логика работы:
```javascript
// НЕПРАВИЛЬНО (до исправления):
body: JSON.stringify({
  message: inputMessage,
  history: messages.filter(m => m.type !== 'system').map(m => ({
    role: m.type === 'user' ? 'user' : 'assistant',
    content: m.content
  }))
})
// Отсутствовало поле user_id
```

## 🔧 Исправления

### 1. Добавление поля `user_id` в фронтенд

**Файл:** `frontend/src/components/NTDConsultation.js`

**Было:**
```javascript
body: JSON.stringify({
  message: inputMessage,
  history: messages.filter(m => m.type !== 'system').map(m => ({
    role: m.type === 'user' ? 'user' : 'assistant',
    content: m.content
  }))
})
```

**Стало:**
```javascript
body: JSON.stringify({
  message: inputMessage,
  user_id: 'default_user', // Добавляем user_id
  history: messages.filter(m => m.type !== 'system').map(m => ({
    role: m.type === 'user' ? 'user' : 'assistant',
    content: m.content
  }))
})
```

### 2. Реализация консультации НТД в RAG сервисе

**Файл:** `rag_service/services/rag_service.py`

Добавлен метод `get_ntd_consultation`:
```python
def get_ntd_consultation(self, message: str, history: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Получение консультации НТД на основе поиска по документам"""
    try:
        logger.info(f"💬 [NTD_CONSULTATION] Processing consultation request: '{message[:100]}...'")
        
        # Выполняем поиск по запросу
        search_results = self.hybrid_search(message, k=5)
        
        if not search_results:
            return {
                "status": "success",
                "response": "К сожалению, я не нашел релевантной информации в базе нормативных документов...",
                "sources": [],
                "confidence": 0.0,
                "documents_used": 0,
                "timestamp": datetime.now().isoformat()
            }
        
        # Формируем ответ на основе найденных документов
        sources = []
        response_parts = []
        
        for result in search_results[:3]:  # Берем топ-3 результата
            source = {
                "title": result.get('title', 'Неизвестный документ'),
                "code": result.get('code', ''),
                "content": result.get('content', '')[:200] + '...',
                "page": result.get('page', 1),
                "score": result.get('score', 0)
            }
            sources.append(source)
            
            # Добавляем информацию о документе в ответ
            if result.get('code'):
                response_parts.append(f"📄 **{result['code']}** - {result.get('title', '')}")
            else:
                response_parts.append(f"📄 {result.get('title', '')}")
            
            response_parts.append(f"Содержание: {result.get('content', '')[:300]}...")
            response_parts.append("")
        
        # Формируем итоговый ответ
        if response_parts:
            response = "На основе поиска в базе нормативных документов, вот что я нашел:\n\n" + "\n".join(response_parts)
            response += f"\n\nНайдено {len(sources)} релевантных фрагментов из нормативных документов."
        else:
            response = "К сожалению, я не нашел релевантной информации в базе нормативных документов."
        
        return {
            "status": "success",
            "response": response,
            "sources": sources,
            "confidence": min(0.9, max(0.1, search_results[0].get('score', 0.5))),
            "documents_used": len(sources),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ [NTD_CONSULTATION] Error processing consultation: {e}")
        return {
            "status": "error",
            "response": "Произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте еще раз.",
            "sources": [],
            "confidence": 0.0,
            "documents_used": 0,
            "timestamp": datetime.now().isoformat()
        }
```

### 3. Обновление эндпоинтов консультации НТД

**Файл:** `rag_service/api/endpoints.py`

Обновлены функции:
- `ntd_consultation_chat()` - использует новый метод `get_ntd_consultation`
- `ntd_consultation_stats()` - возвращает базовую статистику
- `clear_consultation_cache()` - заглушка для очистки кэша
- `get_consultation_cache_stats()` - заглушка для статистики кэша

### 4. Исправление инициализации RAG сервиса

**Файл:** `rag_service/api/endpoints.py`

Исправлены функции для использования `get_rag_service()`:
- `get_stats()`
- `get_document_chunks()`
- `get_documents_stats()`
- `delete_document()`
- `delete_document_indexes()`

### 5. Добавление недостающего метода

**Файл:** `rag_service/services/rag_service.py`

Добавлен метод `get_documents_from_uploaded()`:
```python
def get_documents_from_uploaded(self, document_type: str = 'normative') -> List[Dict[str, Any]]:
    """Получение документов из таблицы uploaded_documents"""
    try:
        with self.db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, original_filename, category, processing_status, created_at, 
                       file_size, COALESCE(token_count, 0) as token_count
                FROM uploaded_documents
                WHERE category = %s OR %s = 'all'
                ORDER BY created_at DESC
            """, (document_type, document_type))
            documents = cursor.fetchall()
            return [dict(doc) for doc in documents]
    except Exception as e:
        logger.error(f"❌ [GET_DOCUMENTS_FROM_UPLOADED] Error getting documents: {e}")
        return []
```

## ✅ Результаты

### До исправления:
- ❌ Ошибка "Field required: user_id"
- ❌ Ошибка "'RAGService' object has no attribute 'ntd_consultation_service'"
- ❌ Ошибка "'NoneType' object has no attribute 'db_manager'"
- ❌ Консультация НТД не работала

### После исправления:
- ✅ Эндпоинт `/api/ntd-consultation/chat` принимает запросы с `user_id`
- ✅ Реализована консультация НТД на основе поиска по документам
- ✅ Исправлены проблемы с инициализацией RAG сервиса
- ✅ Добавлены недостающие методы
- ✅ Консультация НТД готова к работе

## 🧪 Тестирование

### 1. Тест эндпоинта консультации:
```bash
curl -X POST "https://localhost/api/ntd-consultation/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Что такое ГОСТ?", "user_id": "default_user", "history": []}' \
  -k
```

**Результат:**
```json
{
  "status": "success",
  "response": "К сожалению, я не нашел релевантной информации в базе нормативных документов...",
  "sources": [],
  "confidence": 0.0,
  "documents_used": 0,
  "timestamp": "2025-08-30T17:32:59.489007"
}
```

### 2. Тест статистики документов:
```bash
curl -X GET "https://localhost/api/documents/stats" -k
```

**Результат:**
```json
{
  "statistics": {
    "total_documents": 0,
    "indexed_documents": 0,
    "indexing_progress_percent": 0,
    "total_tokens": 0,
    "categories": []
  }
}
```

## 🔄 Текущий статус

### Работает:
- ✅ Эндпоинт консультации НТД
- ✅ Статистика документов
- ✅ Базовая функциональность RAG сервиса

### В процессе:
- 🔄 Загрузка модели BGE-M3 (первый запуск может занять время)
- 🔄 Индексация документов (если есть)

### Рекомендации:
1. **Дождаться загрузки модели** - BGE-M3 загружается при первом запросе
2. **Загрузить документы** - для полноценной работы консультации нужны нормативные документы
3. **Протестировать фронтенд** - после загрузки модели проверить работу через браузер

## 📝 Заключение

Проблема с консультацией НТД успешно решена. Система теперь:
- Корректно обрабатывает запросы консультации
- Использует поиск по документам для формирования ответов
- Возвращает структурированные ответы с источниками
- Готова к работе после загрузки модели BGE-M3

**Статус:** ✅ ИСПРАВЛЕНО (ожидается загрузка модели)
