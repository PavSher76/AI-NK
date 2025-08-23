# Отчет о исправлении статистики на странице "Нормативные документы"

## 🚨 Выявленные проблемы

### **Проблемы со статистикой:**
- **Всего документов**: Неправильно отображалось
- **Проиндексировано**: Неправильно отображалось  
- **Прогресс индексации**: Неправильно отображался
- **Категорий**: Неправильно отображалось

### **Причина проблем:**
- Фронтенд использовал endpoint `/api/rag/stats` вместо правильного endpoint для документов
- Отсутствовал специальный endpoint для статистики нормативных документов
- Неправильная структура данных между backend и frontend

## 🔧 Реализованные исправления

### 1. **Создание нового endpoint для статистики документов**

#### **Добавлен endpoint `/api/documents/stats` в `document_parser/main.py`:**
```python
@app.get("/documents/stats")
async def get_documents_stats():
    """Получение статистики нормативных документов"""
    try:
        with parser.db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Общая статистика по документам
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_documents,
                    COUNT(CASE WHEN processing_status = 'completed' THEN 1 END) as completed_documents,
                    COUNT(CASE WHEN processing_status = 'pending' THEN 1 END) as pending_documents,
                    COUNT(CASE WHEN processing_status = 'error' THEN 1 END) as error_documents,
                    COUNT(DISTINCT category) as unique_categories,
                    SUM(token_count) as total_tokens
                FROM uploaded_documents
            """)
            doc_stats = cursor.fetchone()
            
            # Статистика по категориям
            cursor.execute("""
                SELECT 
                    category,
                    COUNT(*) as count,
                    SUM(token_count) as total_tokens
                FROM uploaded_documents
                WHERE category IS NOT NULL AND category != ''
                GROUP BY category
                ORDER BY count DESC
            """)
            categories = cursor.fetchall()
            
            # Статистика по извлеченным элементам
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_elements,
                    COUNT(DISTINCT uploaded_document_id) as documents_with_elements
                FROM extracted_elements
            """)
            elements_stats = cursor.fetchone()
            
            # Вычисляем прогресс индексации
            total_docs = doc_stats["total_documents"] or 0
            completed_docs = doc_stats["completed_documents"] or 0
            indexing_progress = (completed_docs / total_docs * 100) if total_docs > 0 else 0
            
        return {
            "status": "success",
            "statistics": {
                "total_documents": total_docs,
                "indexed_documents": completed_docs,
                "indexing_progress_percent": round(indexing_progress, 1),
                "categories_count": doc_stats["unique_categories"] or 0,
                "total_tokens": doc_stats["total_tokens"] or 0,
                "total_elements": elements_stats["total_elements"] or 0,
                "documents_with_elements": elements_stats["documents_with_elements"] or 0,
                "categories": [dict(cat) for cat in categories]
            }
        }
```

### 2. **Исправление фронтенда**

#### **Изменение endpoint в `NormativeDocuments.js`:**
```javascript
// БЫЛО:
const response = await fetch('/api/rag/stats', {

// СТАЛО:
const response = await fetch('/api/documents/stats', {
```

#### **Адаптация структуры данных:**
```javascript
// Адаптируем данные для совместимости с фронтендом
const adaptedStats = {
  total_documents: data.statistics.total_documents,
  indexed_documents: data.statistics.indexed_documents,
  indexing_progress: `${data.statistics.indexing_progress_percent}%`,
  category_distribution: data.statistics.categories.reduce((acc, cat) => {
    acc[cat.category] = cat.count;
    return acc;
  }, {}),
  collection_name: 'normative_documents'
};
```

### 3. **Пересборка и перезапуск сервисов**
```bash
# Пересборка document-parser
docker-compose build document-parser
docker-compose up -d --force-recreate document-parser

# Пересборка frontend
docker-compose build frontend
docker-compose up -d --force-recreate frontend
```

## 📊 Результаты тестирования

### ✅ **Новый endpoint работает корректно:**
```bash
curl -k -H "Authorization: Bearer test-token" "https://localhost/api/documents/stats"
```

### ✅ **Ответ API:**
```json
{
  "status": "success",
  "statistics": {
    "total_documents": 3,
    "indexed_documents": 3,
    "indexing_progress_percent": 100.0,
    "categories_count": 1,
    "total_tokens": 23005,
    "total_elements": 30,
    "documents_with_elements": 3,
    "categories": [
      {
        "category": "gost",
        "count": 3,
        "total_tokens": 23005
      }
    ]
  }
}
```

### ✅ **Исправленная статистика:**
- **Всего документов**: 3 ✅
- **Проиндексировано**: 3 ✅
- **Прогресс индексации**: 100% ✅
- **Категорий**: 1 (gost) ✅

## 🎯 Ключевые улучшения

### 1. **Точная статистика документов**
- Подсчет основан на реальных данных из базы данных
- Учитываются только нормативные документы
- Правильный подсчет статусов обработки

### 2. **Корректный прогресс индексации**
- Вычисляется как процент завершенных документов
- Учитывает статус `processing_status = 'completed'`
- Отображается в процентах

### 3. **Детальная статистика по категориям**
- Подсчет уникальных категорий
- Распределение документов по категориям
- Общее количество токенов по категориям

### 4. **Дополнительная информация**
- Общее количество токенов: 23,005
- Общее количество элементов: 30
- Количество документов с элементами: 3

## 🚀 Влияние на фронтенд

### **Фронтенд теперь корректно отображает:**
- ✅ **Всего документов**: 3 (вместо неправильного значения)
- ✅ **Проиндексировано**: 3 (вместо неправильного значения)
- ✅ **Прогресс индексации**: 100% (вместо неправильного значения)
- ✅ **Категорий**: 1 (вместо неправильного значения)

### **Дополнительные возможности:**
- Детализированная статистика по категориям
- Информация о токенах и элементах
- Корректное отображение прогресса обработки

## 📈 Заключение

**Статистика на странице "Нормативные документы" полностью исправлена:**

- ✅ **Всего документов**: 3 (корректно)
- ✅ **Проиндексировано**: 3 (корректно)
- ✅ **Прогресс индексации**: 100% (корректно)
- ✅ **Категорий**: 1 (корректно)

**Создан новый endpoint `/api/documents/stats`** для получения точной статистики нормативных документов с детальной информацией о категориях, токенах и элементах.

**Фронтенд теперь отображает корректную статистику!** 🚀
