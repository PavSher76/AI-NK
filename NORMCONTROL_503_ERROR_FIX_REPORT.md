# Отчет о решении проблемы с ошибкой 503 на странице "Нормоконтроль"

## Проблема

Пользователь получал ошибку 503 (Service Unavailable) при попытке загрузить список документов на странице "Нормоконтроль":

```
CheckableDocuments.js:68 🔍 [DEBUG] CheckableDocuments.js: fetchDocuments failed with status: 503
GET https://localhost/api/checkable-documents 503 (Service Unavailable)
```

## Диагностика

### 1. Анализ логов

**Gateway логи показали:**
```
🔍 [DEBUG] Gateway: Connection error to http://document-parser:8001: All connection attempts failed
🔍 [DEBUG] Gateway: Request processed in 0.009s - Status: 503
```

**Document-parser логи показали:**
- Сервис перезапускался
- Статус: "health: starting"
- После перезапуска endpoint `/checkable-documents` работал корректно

### 2. Проверка сетевого подключения

**Статус контейнеров:**
- ✅ Gateway: Up 9 hours
- ✅ Frontend: Up 9 hours (healthy)
- ⚠️ Document-parser: Up 13 seconds (health: starting)
- ✅ Все контейнеры подключены к сети `ai-nk-network`

**Проверка endpoint:**
```bash
curl -f http://localhost:8001/checkable-documents
# ✅ Возвращает данные корректно

curl -k -H "Authorization: Bearer test-token" https://localhost:8443/api/checkable-documents
# ✅ Возвращает данные корректно
```

### 3. Анализ конфигурации

**Gateway маршрутизация:**
- ✅ Правильно настроена для `/api/checkable-documents`
- ✅ Направляет запросы к `http://document-parser:8001`
- ✅ Обрабатывает JWT токены от Keycloak

**Document-parser endpoints:**
- ✅ `GET /checkable-documents` - существует и работает
- ✅ `GET /checkable-documents/{id}/report` - существует
- ✅ `GET /checkable-documents/{id}/download-report` - существует
- ✅ `POST /checkable-documents/{id}/check` - существует

## Причина проблемы

Проблема была **временной** и связана с перезапуском сервиса `document-parser`:

1. **Перезапуск сервиса** - document-parser перезапускался и был недоступен несколько секунд
2. **Health check статус** - сервис имел статус "health: starting" во время перезапуска
3. **Сетевая недоступность** - gateway не мог подключиться к document-parser во время перезапуска

## Решение

### 1. Улучшена обработка ошибок

Добавлены более информативные сообщения об ошибках в `CheckableDocuments.js`:

```javascript
if (response.status === 503) {
  setError('Сервис временно недоступен. Попробуйте обновить страницу через несколько секунд.');
} else if (response.status === 401) {
  setError('Ошибка авторизации. Пожалуйста, войдите в систему заново.');
} else if (response.status === 500) {
  setError('Внутренняя ошибка сервера. Попробуйте позже.');
} else {
  setError(`Ошибка загрузки документов (код ${response.status})`);
}
```

### 2. Добавлена автоматическая повторная попытка

Реализован механизм автоматической повторной попытки при ошибке 503:

```javascript
if (response.status === 503) {
  if (retryCount < 3) {
    console.log(`🔍 [DEBUG] CheckableDocuments.js: Retrying fetchDocuments (attempt ${retryCount + 1}/3)`);
    setTimeout(() => {
      fetchDocuments(retryCount + 1);
    }, 2000 * (retryCount + 1)); // Увеличиваем задержку с каждой попыткой
    setError('Сервис временно недоступен. Повторная попытка...');
    return;
  } else {
    setError('Сервис временно недоступен. Попробуйте обновить страницу через несколько секунд.');
  }
}
```

### 3. Улучшено логирование

Добавлены отладочные логи для отслеживания повторных попыток и ошибок.

## Результат

### До исправления:
- ❌ Ошибка 503 без объяснения
- ❌ Нет автоматической повторной попытки
- ❌ Неинформативные сообщения об ошибках

### После исправления:
- ✅ Информативные сообщения об ошибках
- ✅ Автоматическая повторная попытка (до 3 раз)
- ✅ Прогрессивная задержка между попытками (2с, 4с, 6с)
- ✅ Улучшенное логирование для отладки
- ✅ Пользователь видит статус повторных попыток

## Мониторинг

### Рекомендации для предотвращения подобных проблем:

1. **Health checks** - убедиться, что все сервисы имеют корректные health checks
2. **Graceful shutdown** - настроить graceful shutdown для document-parser
3. **Load balancing** - рассмотреть возможность использования нескольких экземпляров document-parser
4. **Circuit breaker** - добавить circuit breaker pattern в gateway для защиты от каскадных сбоев

## Заключение

Проблема с ошибкой 503 была временной и связана с перезапуском сервиса. Реализованные улучшения делают систему более устойчивой к временным сбоям и предоставляют пользователю лучший опыт взаимодействия.

**Статус:** ✅ Решено
**Дата:** $(date)
**Файл:** `frontend/src/components/CheckableDocuments.js`
**Тип проблемы:** Временная недоступность сервиса
**Решение:** Автоматическая повторная попытка + улучшенная обработка ошибок
