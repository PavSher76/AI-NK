# Отчет об исправлении разделения коллекций Qdrant

## ✅ Проблема решена

Созданы две отдельные коллекции в Qdrant:
- **`checkable_documents`** - для документов на проверку нормоконтроля
- **`normative_documents`** - для нормативных документов

## 🔧 Выполненные исправления

### 1. Добавлен эндпоинт загрузки в document-parser
- `POST /upload/checkable` - загрузка документов для проверки
- Поддержка PDF, DWG, IFC, DOCX
- Дедупликация по SHA-256 хешу
- Сохранение в таблицу `checkable_documents`

### 2. Исправлена маршрутизация в Gateway
- `/api/upload/checkable` → document-parser
- `/api/upload` → rag-service

### 3. Создана коллекция `checkable_documents` в Qdrant
- Автоматическое создание при инициализации RAG сервиса
- Отдельная коллекция для проверяемых документов

## ✅ Результат тестирования

**Загрузка документа для проверки:**
```bash
curl -k -H "Authorization: Bearer test-token" -F "file=@test.pdf" -F "category=other" https://localhost:8443/api/upload/checkable
```

**Ответ:**
```json
{
  "status": "success",
  "document_id": 68905333,
  "filename": "test.pdf",
  "file_size": 1000,
  "message": "Document uploaded successfully for checking"
}
```

**Коллекции в Qdrant:**
```json
"checkable_documents"
"normative_documents"
```

## 🎯 Заключение

Разделение коллекций полностью функционально! 🚀
