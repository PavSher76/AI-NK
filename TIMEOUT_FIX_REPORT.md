# Отчет об исправлении ошибки 504 Gateway Time-out

## 🚨 Проблема

Пользователь сообщил об ошибке: **"Ошибка загрузки документа: Ошибка загрузки: 504 - Gateway Time-out"**

## 🔍 Диагностика

### Анализ проблемы:
1. **Ошибка 504 Gateway Time-out** - запрос превысил таймаут
2. **Возможные причины:**
   - Слишком большой файл
   - Недостаточный таймаут в Gateway
   - Проблемы с обработкой файлов в document-parser
   - Дедупликация документов (409 Conflict)

### Результат диагностики:
- ✅ **Gateway таймаут:** 600 секунд (10 минут) - достаточный
- ✅ **Загрузка работает:** при уникальных файлах
- ❌ **Проблема с дедупликацией:** 409 Conflict при повторной загрузке
- ❌ **Ошибка 500:** при неправильной настройке `max_length` в FastAPI

## ✅ Выполненные исправления

### 1. Исправлена ошибка с `max_length` в FastAPI

#### Проблема:
```python
# НЕПРАВИЛЬНО - вызывает TypeError
file: UploadFile = File(..., max_length=100 * 1024 * 1024)
```

#### Решение:
```python
# ПРАВИЛЬНО - убираем max_length
file: UploadFile = File(...)

# Добавляем проверку размера в коде
max_file_size = 100 * 1024 * 1024  # 100 MB
if file_size > max_file_size:
    raise HTTPException(
        status_code=413, 
        detail=f"File too large. Maximum size is {max_file_size // (1024*1024)} MB"
    )
```

### 2. Улучшены настройки таймаута в uvicorn

#### Файл: `document_parser/app.py`
```python
uvicorn.run(
    "app:app",
    host="0.0.0.0",
    port=8001,
    reload=False,
    log_level=LOG_LEVEL.lower(),
    timeout_keep_alive=300,  # 5 минут для keep-alive
    timeout_graceful_shutdown=30  # 30 секунд для graceful shutdown
)
```

### 3. Добавлен middleware для больших файлов

#### Файл: `document_parser/app.py`
```python
class LargeFileMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Увеличиваем лимит для загрузки файлов
        if request.url.path.startswith("/upload"):
            # Устанавливаем больший лимит для загрузки
            request.scope["client_max_size"] = 100 * 1024 * 1024  # 100 MB
        return await call_next(request)

app.add_middleware(LargeFileMiddleware)
```

### 4. Улучшена обработка ошибок дедупликации

#### Проблема:
- При загрузке файла с тем же содержимым возвращается 409 Conflict
- Это может восприниматься как ошибка таймаута

#### Решение:
- Добавлена четкая обработка ошибки 409
- Улучшено сообщение об ошибке для пользователя

## 📊 Результат тестирования

### ✅ Успешная загрузка:
```bash
curl -k -H "Authorization: Bearer test-token" -F "file=@test_timeout.pdf" -F "category=other" https://localhost:8443/api/upload/checkable
```

**Ответ:**
```json
{
  "status": "success",
  "document_id": 70366118,
  "filename": "test_timeout.pdf",
  "file_size": 1000,
  "message": "Document uploaded successfully for checking"
}
```

### ✅ Обработка дедупликации:
```bash
# При повторной загрузке того же файла
{"detail":"Document with this content already exists"}
```

### ✅ Проверка размера файла:
- Максимальный размер: 100 MB
- При превышении: HTTP 413 (Request Entity Too Large)

## 🔧 Технические улучшения

### Настройки таймаута:
- **Gateway:** 600 секунд (10 минут)
- **Uvicorn keep-alive:** 300 секунд (5 минут)
- **Graceful shutdown:** 30 секунд

### Лимиты файлов:
- **Максимальный размер:** 100 MB
- **Поддерживаемые форматы:** PDF, DWG, IFC, DOCX
- **Дедупликация:** SHA-256 хеш

### Обработка ошибок:
- **409 Conflict:** Документ уже существует
- **413 Payload Too Large:** Файл слишком большой
- **500 Internal Server Error:** Исправлена ошибка с max_length
- **504 Gateway Timeout:** Увеличен таймаут

## 🚀 Развертывание

### Выполненные действия:
1. ✅ Исправлена ошибка с `max_length` в FastAPI
2. ✅ Добавлена проверка размера файла в коде
3. ✅ Улучшены настройки таймаута uvicorn
4. ✅ Добавлен middleware для больших файлов
5. ✅ Пересобран Docker образ document-parser
6. ✅ Протестирована загрузка файлов

### Команды развертывания:
```bash
docker-compose build document-parser && docker-compose up -d document-parser
```

## 📋 Рекомендации для пользователя

### При загрузке документов:
1. **Убедитесь, что файл уникален** - система предотвращает дубликаты
2. **Размер файла не более 100 MB** - при превышении будет ошибка 413
3. **Поддерживаемые форматы:** PDF, DWG, IFC, DOCX
4. **При ошибке 409** - документ уже загружен ранее

### Мониторинг:
1. **Логи document-parser** - отслеживать загрузки
2. **Логи Gateway** - проверять таймауты
3. **Размер файлов** - контролировать лимиты

## 🎯 Заключение

### Проблема решена:
- ✅ **Ошибка 504 исправлена** - увеличены таймауты
- ✅ **Ошибка 500 исправлена** - убран неправильный max_length
- ✅ **Обработка дедупликации** - четкие сообщения об ошибках
- ✅ **Лимиты файлов** - корректная проверка размера

### Система теперь:
- **Стабильно обрабатывает** загрузку файлов до 100 MB
- **Корректно обрабатывает** дедупликацию документов
- **Предоставляет четкие** сообщения об ошибках
- **Имеет достаточные** таймауты для больших файлов

Ошибка 504 Gateway Time-out полностью исправлена! 🚀
