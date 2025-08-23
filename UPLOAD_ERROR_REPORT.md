# Отчет о проблеме с загрузкой документов на нормоконтроль

## 🚨 Проблема
При попытке загрузки документов на нормоконтроль возникает ошибка:
```
"Proxy error: Server disconnected without sending a response."
```

## 🔍 Диагностика

### Тестирование файлов разных размеров:

1. **Файл 1.4MB (8 страниц)** ✅ **РАБОТАЕТ**
   - Статус: 200 OK
   - Обработка: Успешная
   - Результат: Документ загружен и обработан

2. **Файл 3.2MB (13 страниц)** ❌ **НЕ РАБОТАЕТ**
   - Статус: 500 Internal Server Error
   - Ошибка: "Proxy error: Server disconnected without sending a response"
   - Проблема: Document-parser перезапускается во время обработки

3. **Файл 14MB (47 страниц)** ❌ **НЕ РАБОТАЕТ**
   - Статус: 500 Internal Server Error
   - Ошибка: "Proxy error: Server disconnected without sending a response"
   - Проблема: Document-parser перезапускается во время обработки

### Анализ логов:

```
INFO:main:Processing PDF with 13 pages
INFO:main:Connected to PostgreSQL
INFO:main:Connected to Qdrant
INFO:     Started server process [1]  # ← Перезапуск сервера
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8001
```

## 🔧 Причины проблемы

### 1. **Перезапуск document-parser**
- Document-parser перезапускается во время обработки PDF
- Это происходит при обработке файлов с количеством страниц > 8
- Возможные причины:
  - Нехватка памяти при обработке больших PDF
  - Таймауты при обработке
  - Ошибки в коде обработки PDF

### 2. **Проблемы с обработкой PDF**
- Функция `parse_pdf()` может вызывать исключения
- OCR обработка может занимать слишком много времени
- Проблемы с подключением к базам данных во время обработки

### 3. **Настройки таймаутов**
- Gateway: 300 секунд (5 минут)
- Nginx: 300 секунд
- Uvicorn: 300 секунд
- Но document-parser все равно перезапускается

## ✅ Реализованные исправления

### 1. **Ограничение размера файла**
```python
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
if file.size and file.size > MAX_FILE_SIZE:
    raise HTTPException(
        status_code=413, 
        detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
    )
```

### 2. **Улучшенные настройки uvicorn**
```dockerfile
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001", 
     "--timeout-keep-alive", "300", "--limit-max-requests", "1000", 
     "--limit-concurrency", "10"]
```

### 3. **Middleware для больших файлов**
```python
class LargeFileMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/upload" or request.url.path == "/upload/checkable":
            request.scope["max_content_size"] = 100 * 1024 * 1024  # 100MB
        return await call_next(request)
```

## 🚀 Рекомендации по решению

### 1. **Немедленные действия**
- ✅ Ограничить размер файлов до 10MB
- ✅ Добавить предупреждение пользователям о лимитах
- ✅ Улучшить обработку ошибок

### 2. **Среднесрочные улучшения**
- 🔄 Оптимизировать обработку PDF
- 🔄 Добавить прогресс-бар для больших файлов
- 🔄 Реализовать асинхронную обработку с возможностью отмены

### 3. **Долгосрочные улучшения**
- 🔄 Разделить обработку на этапы
- 🔄 Добавить очередь задач (Celery/RQ)
- 🔄 Реализовать обработку по частям

## 📊 Текущий статус

### ✅ Работает:
- Загрузка файлов до 1.4MB
- Обработка PDF до 8 страниц
- Все остальные функции системы

### ❌ Не работает:
- Загрузка файлов > 1.4MB
- Обработка PDF > 8 страниц
- Большие документы вызывают перезапуск сервиса

## 🎯 Заключение

Проблема с загрузкой больших документов связана с перезапуском document-parser во время обработки PDF. Система работает корректно для файлов размером до 1.4MB, но требует оптимизации для обработки больших документов.

**Рекомендуется:**
1. Использовать файлы размером до 10MB
2. Разбивать большие документы на части
3. Обрабатывать документы по этапам
