# Отчет об интеграции LanguageTool и исправлении RAG сервиса

## Дата: 14 сентября 2025

## Проблемы, которые были решены

### 1. Ошибка 502 (Bad Gateway) для эндпоинта `/rag/reasoning-modes`

**Проблема:** Фронтенд получал ошибку 502 при обращении к `https://localhost/rag/reasoning-modes`

**Причина:** 
- Эндпоинт `/rag/reasoning-modes` не был добавлен в список публичных путей в Gateway
- Gateway требовал авторизацию для этого эндпоинта

**Решение:**
- Добавлен путь `/api/rag/reasoning-modes` в список публичных путей в `gateway/app.py`
- Перезапущен Gateway сервис

### 2. Отсутствие LanguageTool сервера

**Проблема:** 
- Spellchecker сервис не мог подключиться к LanguageTool на `localhost:8081`
- LanguageTool сервер не был настроен в docker-compose.yaml

**Решение:**
- Добавлен LanguageTool сервер в `docker-compose.yaml`:
  ```yaml
  languagetool:
    image: silviof/docker-languagetool:latest
    ports:
      - "8082:8010"
    environment:
      - TZ=Europe/Moscow
    volumes:
      - /etc/localtime:/etc/localtime:ro
      - /etc/timezone:/etc/timezone:ro
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G
          cpus: '1.0'
    cpu_shares: 256
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8010/v2/languages"]
      interval: 30s
      timeout: 10s
      retries: 3
  ```

- Обновлен spellchecker сервис для использования переменной окружения `LANGUAGETOOL_URL`
- Добавлена зависимость `depends_on: - languagetool` в spellchecker-service

### 3. Конфликт портов

**Проблема:** Keycloak использовал порт 8081, который мы пытались использовать для LanguageTool

**Решение:** Изменен внешний порт LanguageTool с 8081 на 8082

## Изменения в файлах

### 1. `docker-compose.yaml`
- Добавлен сервис `languagetool`
- Обновлен `spellchecker-service` с зависимостью от LanguageTool
- Добавлена переменная окружения `LANGUAGETOOL_URL=http://languagetool:8010`

### 2. `gateway/app.py`
- Добавлен путь `/api/rag/reasoning-modes` в список публичных путей

### 3. `spellchecker_service/spell_checker.py`
- Обновлен URL LanguageTool для использования переменной окружения:
  ```python
  self.language_tool_url = os.getenv("LANGUAGETOOL_URL", "http://localhost:8081")
  ```

## Результаты

### ✅ Все сервисы работают корректно:
- **LanguageTool**: `http://localhost:8082` - доступен
- **Spellchecker**: `http://localhost:8007` - healthy, подключен к LanguageTool
- **RAG Service**: `http://localhost:8003` - healthy
- **Outgoing Control**: `http://localhost:8006` - healthy
- **Gateway**: `https://localhost:8443` - эндпоинт `/api/rag/reasoning-modes` работает

### ✅ Проверка функциональности:
```bash
# LanguageTool
curl -s http://localhost:8082/v2/languages | head -5
# Возвращает список поддерживаемых языков

# Spellchecker
curl -s http://localhost:8007/health
# {"status":"healthy","service":"spellchecker","hunspell_available":true,"languagetool_available":true,"version":"1.0.0"}

# RAG Reasoning Modes через Gateway
curl -s -k https://localhost:8443/api/rag/reasoning-modes
# Возвращает 4 режима рассуждения: fast, balanced, deep, turbo
```

## Статус сервисов

| Сервис | Порт | Статус | LanguageTool |
|--------|------|--------|--------------|
| LanguageTool | 8082 | ✅ Healthy | - |
| Spellchecker | 8007 | ✅ Healthy | ✅ Connected |
| RAG Service | 8003 | ✅ Healthy | - |
| Outgoing Control | 8006 | ✅ Healthy | - |
| Gateway | 8443 | ✅ Running | - |

## Заключение

Все проблемы успешно решены:
1. ✅ Эндпоинт `/rag/reasoning-modes` теперь доступен через Gateway
2. ✅ LanguageTool сервер интегрирован и работает
3. ✅ Spellchecker сервис подключен к LanguageTool
4. ✅ Все сервисы работают стабильно

Фронтенд теперь должен корректно получать режимы рассуждения и использовать проверку орфографии через LanguageTool.
