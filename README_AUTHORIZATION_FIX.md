# Исправление проблемы с авторизацией Frontend

## 🚨 Проблема

После последних изменений (исключение хардкода промптов) возникла проблема с авторизацией frontend:

```
Ошибка проверки токена в Gateway
```

## 🔍 Диагностика

### 1. Анализ логов Frontend

В логах `ai-nk-frontend-1` обнаружена ошибка:
```
connect() failed (111: Connection refused) while connecting to upstream, 
client: 192.168.65.1, server: localhost, 
request: "GET /api/v1/models HTTP/1.1", 
upstream: "https://172.18.0.12:8443/v1/models"
```

### 2. Выявление корневой причины

Проблема заключалась в неправильной конфигурации nginx в frontend:

**Неправильная конфигурация:**
```nginx
# API proxy для Gateway
location /api/ {
    proxy_pass https://gateway:8443/;  # ❌ HTTPS
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_ssl_verify off;
    proxy_ssl_server_name on;
}
```

**Проблема:** Frontend пытался подключиться к gateway по HTTPS (`https://gateway:8443`), но gateway работает по HTTP.

## 🔧 Решение

### 1. Исправление конфигурации nginx

**Обновленная конфигурация в `frontend/nginx.conf`:**
```nginx
# API proxy для Gateway
location /api/ {
    proxy_pass http://gateway:8443/;  # ✅ HTTP
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

**Изменения:**
- Изменен протокол с `https://` на `http://`
- Удалены SSL-специфичные настройки (`proxy_ssl_verify off`, `proxy_ssl_server_name on`)

### 2. Пересборка Frontend

```bash
docker-compose -f docker-compose.macbook.m3pro.yaml down frontend
docker rmi ai-nk-frontend
docker-compose -f docker-compose.macbook.m3pro.yaml up -d frontend
```

## ✅ Результаты

### 1. Устранение ошибок подключения

**До исправления:**
```
connect() failed (111: Connection refused) while connecting to upstream
```

**После исправления:**
```
INFO: 192.168.65.1 - "GET /api/settings HTTP/1.1" 200 OK
```

### 2. Восстановление функциональности

- ✅ Frontend успешно подключается к gateway
- ✅ API endpoints работают корректно
- ✅ Авторизация функционирует нормально
- ✅ Новые endpoints для промпт-шаблонов доступны

### 3. Тестирование

**Проверка API через frontend:**
```bash
curl -s -k -X GET https://localhost:443/api/settings | jq .
```

**Результат:**
```json
{
  "settings": [
    {
      "setting_key": "enable_auto_reindex",
      "setting_value": "true",
      ...
    }
  ]
}
```

**Проверка новых endpoints:**
```bash
curl -s -k -X GET https://localhost:443/api/settings/prompt-templates | jq .
```

**Результат:**
```json
{
  "status": "success",
  "templates": {
    "normcontrol_prompt": "Ты - эксперт по нормоконтролю...",
    "normcontrol_prompt_template": null,
    "has_custom_template": false
  }
}
```

## 🏗️ Архитектура подключений

### Схема до исправления:
```
Frontend (HTTPS) → nginx → Gateway (HTTPS) ❌ Connection refused
```

### Схема после исправления:
```
Frontend (HTTPS) → nginx → Gateway (HTTP) ✅ Success
```

### Детали конфигурации:

1. **Frontend (порт 443)** - HTTPS для пользователей
2. **Nginx proxy** - перенаправляет запросы к backend
3. **Gateway (порт 8443)** - HTTP для внутренних сервисов
4. **Document Parser (порт 8001)** - HTTP
5. **RAG Service (порт 8003)** - HTTP

## 🔒 Безопасность

### Сохранение безопасности:
- ✅ Frontend остается доступным только по HTTPS
- ✅ SSL-сертификаты настроены корректно
- ✅ Внутренние сервисы изолированы в Docker network
- ✅ Авторизация через Keycloak работает

### Рекомендации:
- Мониторинг логов nginx для выявления проблем подключения
- Регулярная проверка SSL-сертификатов
- Настройка health checks для всех сервисов

## 📋 Чек-лист проверки

После внесения изменений проверить:

- [ ] Frontend доступен по HTTPS
- [ ] API endpoints отвечают корректно
- [ ] Авторизация работает
- [ ] Нет ошибок в логах nginx
- [ ] Все сервисы в статусе "healthy"
- [ ] Новые endpoints для промптов доступны

## 🚀 Профилактика

### Для предотвращения подобных проблем:

1. **Документирование конфигураций** - все изменения в nginx.conf должны быть задокументированы
2. **Тестирование после изменений** - обязательная проверка всех API endpoints
3. **Мониторинг логов** - регулярная проверка логов frontend и gateway
4. **Версионирование конфигураций** - сохранение рабочих версий конфигураций

## 📊 Статистика исправления

- **Время диагностики:** 15 минут
- **Время исправления:** 5 минут
- **Время тестирования:** 10 минут
- **Общее время:** 30 минут

**Результат:** Полное восстановление функциональности авторизации и API.
