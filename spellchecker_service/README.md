# SpellChecker Service

Сервис проверки орфографии и грамматики с использованием Hunspell + LanguageTool.

## Возможности

- ✅ **Проверка орфографии** с помощью Hunspell
- ✅ **Проверка грамматики** с помощью LanguageTool
- ✅ **Комплексная проверка** орфографии и грамматики
- ✅ **Поддержка русского языка** (ru-RU)
- ✅ **Поддержка английского языка** (en-US)
- ✅ **Fallback режим** при недоступности внешних библиотек
- ✅ **REST API** для интеграции
- ✅ **Docker контейнер** для развертывания

## API Endpoints

### Health Check
```http
GET /health
```

### Проверка орфографии
```http
POST /spellcheck
Content-Type: application/json

{
    "text": "текст для проверки",
    "language": "ru",
    "check_spelling": true,
    "check_grammar": false
}
```

### Проверка грамматики
```http
POST /grammar-check
Content-Type: application/json

{
    "text": "текст для проверки",
    "language": "ru",
    "check_spelling": false,
    "check_grammar": true
}
```

### Комплексная проверка
```http
POST /comprehensive-check
Content-Type: application/json

{
    "text": "текст для проверки",
    "language": "ru",
    "check_spelling": true,
    "check_grammar": true
}
```

### Поддерживаемые языки
```http
GET /languages
```

### Статистика сервиса
```http
GET /stats
```

## Установка и запуск

### Docker Compose
```bash
docker compose up -d spellchecker-service
```

### Прямой запуск
```bash
cd spellchecker_service
pip install -r requirements.txt
python main.py
```

## Конфигурация

### Переменные окружения
- `LANGUAGETOOL_HOME` - путь к LanguageTool (по умолчанию: `/opt/languagetool`)
- `HUNSPELL_DICT_PATH` - путь к словарям Hunspell (по умолчанию: `/usr/share/hunspell`)

### Ресурсы
- **Память**: 2GB (лимит), 1GB (резерв)
- **CPU**: 0.5 CPU (резерв)
- **Порт**: 8007

## Архитектура

### Компоненты
1. **FastAPI** - веб-фреймворк
2. **Hunspell** - проверка орфографии
3. **LanguageTool** - проверка грамматики
4. **Fallback система** - упрощенная проверка при недоступности внешних библиотек

### Алгоритм работы
1. **Инициализация** - загрузка словарей и библиотек
2. **Проверка орфографии** - Hunspell или fallback
3. **Проверка грамматики** - LanguageTool или fallback
4. **Объединение результатов** - создание комплексного отчета

## Примеры использования

### Python
```python
import requests

# Проверка орфографии
response = requests.post(
    "https://localhost:8443/api/spellchecker/spellcheck",
    json={
        "text": "Привет! Это тестовый текст с ошибками.",
        "language": "ru"
    },
    verify=False
)

result = response.json()
print(f"Найдено ошибок: {result['spelling']['misspelled_count']}")
```

### cURL
```bash
curl -k -X POST https://localhost:8443/api/spellchecker/comprehensive-check \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Привет! Это тестовый текст с ошибками.",
    "language": "ru"
  }'
```

## Тестирование

```bash
python test_spellchecker_service.py
```

## Логирование

Логи сохраняются в `/app/logs/` внутри контейнера.

## Мониторинг

- **Health check**: `GET /health`
- **Статистика**: `GET /stats`
- **Метрики**: доступны через Prometheus

## Ограничения

1. **Производительность** - LanguageTool может быть медленным
2. **Память** - требует значительных ресурсов
3. **Словари** - ограниченный набор языков
4. **Точность** - автоматическая проверка не идеальна

## Развитие

### Планируемые улучшения
- [ ] Кэширование результатов
- [ ] Асинхронная обработка
- [ ] Дополнительные языки
- [ ] Пользовательские словари
- [ ] Машинное обучение

### Интеграция
- [ ] Outgoing Control Service
- [ ] Document Parser
- [ ] RAG Service
- [ ] Frontend компоненты

## Поддержка

При возникновении проблем:
1. Проверьте логи: `docker logs ai-nk-spellchecker-service-1`
2. Проверьте health check: `curl -k https://localhost:8443/api/spellchecker/health`
3. Проверьте статистику: `curl -k https://localhost:8443/api/spellchecker/stats`
