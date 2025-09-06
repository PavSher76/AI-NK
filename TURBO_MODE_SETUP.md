# 🚀 Настройка турбо режима с GPT-4o-mini

## 📋 Обзор

Турбо режим в чате с ИИ использует модель **GPT-4o-mini** от OpenAI для максимально быстрых ответов. В обычном режиме используется локальная модель **GPT-OSS** через Ollama.

## 🔧 Настройка

### 1. Получение API ключа OpenAI

1. Зарегистрируйтесь на [OpenAI Platform](https://platform.openai.com/)
2. Перейдите в раздел [API Keys](https://platform.openai.com/api-keys)
3. Создайте новый API ключ
4. Скопируйте ключ (он начинается с `sk-`)

### 2. Настройка переменных окружения

#### Для Docker (рекомендуется):

Создайте файл `.env` в корне проекта:

```bash
# OpenAI API Configuration
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_BASE_URL=https://api.openai.com/v1

# Другие настройки...
POSTGRES_USER=norms_user
POSTGRES_PASSWORD=norms_password
POSTGRES_DB=norms_db
REDIS_PASSWORD=redispass
```

#### Для локальной разработки:

```bash
export OPENAI_API_KEY=sk-your-api-key-here
export OPENAI_BASE_URL=https://api.openai.com/v1
```

### 3. Перезапуск сервисов

```bash
# Перезапуск RAG-сервиса
docker-compose restart rag-service

# Или полный перезапуск
docker-compose down && docker-compose up -d
```

## 🧪 Тестирование

### Автоматическое тестирование:

```bash
# Установите API ключ
export OPENAI_API_KEY=sk-your-api-key-here

# Запустите тест
python test_turbo_chat.py
```

### Ручное тестирование:

```bash
# Тест турбо режима
curl -X POST http://localhost:8003/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Привет! Как дела?",
    "model": "gpt-oss:latest",
    "turbo_mode": true,
    "reasoning_depth": "balanced"
  }'

# Тест обычного режима
curl -X POST http://localhost:8003/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Привет! Как дела?",
    "model": "gpt-oss:latest",
    "turbo_mode": false,
    "reasoning_depth": "balanced"
  }'
```

## 🎯 Как это работает

### Турбо режим (turbo_mode: true):
- ✅ Использует **GPT-4o-mini** через OpenAI API
- ✅ Максимально быстрые ответы (3-10 секунд)
- ✅ Краткие и точные ответы
- ✅ Fallback на локальную модель при ошибках

### Обычный режим (turbo_mode: false):
- ✅ Использует **GPT-OSS** через Ollama
- ✅ Настраиваемая глубина рассуждения
- ✅ Полностью локальная обработка
- ✅ Поддержка длинных контекстов

## 🔄 Режимы рассуждения

### Доступные режимы (только в обычном режиме):

1. **fast** - Быстрые ответы
   - Время: 5-15 секунд
   - Токены: до 1024
   - Температура: 0.4

2. **balanced** - Сбалансированные ответы
   - Время: 15-30 секунд
   - Токены: до 2048
   - Температура: 0.6

3. **deep** - Глубокие ответы
   - Время: 30-60 секунд
   - Токены: до 3072
   - Температура: 0.7

## 🎨 Использование в фронтенде

### В интерфейсе чата:

1. **Включение турбо режима**: Нажмите кнопку "Турбо" в заголовке чата
2. **Выбор глубины рассуждения**: Доступно только когда турбо режим выключен
3. **Индикация режима**: Интерфейс показывает текущий режим

### Программное использование:

```javascript
// Турбо режим
const response = await fetch('/rag/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    message: 'Ваш вопрос',
    model: 'gpt-oss:latest',
    turbo_mode: true,
    reasoning_depth: 'balanced'
  })
});

// Обычный режим
const response = await fetch('/rag/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    message: 'Ваш вопрос',
    model: 'gpt-oss:latest',
    turbo_mode: false,
    reasoning_depth: 'deep'
  })
});
```

## 🔍 Мониторинг

### Проверка статуса:

```bash
# Проверка здоровья RAG-сервиса
curl http://localhost:8003/health

# Проверка статистики
curl http://localhost:8003/stats
```

### Логи:

```bash
# Просмотр логов RAG-сервиса
docker logs ai-nk-rag-service-1 --tail 50

# Фильтрация логов турбо режима
docker logs ai-nk-rag-service-1 | grep -E "(TURBO_REASONING|OpenAI)"
```

## ⚠️ Устранение проблем

### Проблема: "OpenAI API ключ не настроен"

**Решение:**
1. Проверьте переменную окружения `OPENAI_API_KEY`
2. Убедитесь, что ключ начинается с `sk-`
3. Перезапустите RAG-сервис

### Проблема: "OpenAI API error: 401"

**Решение:**
1. Проверьте правильность API ключа
2. Убедитесь, что у вас есть доступ к GPT-4o-mini
3. Проверьте баланс аккаунта OpenAI

### Проблема: "Timeout error"

**Решение:**
1. Проверьте интернет-соединение
2. Увеличьте timeout в настройках
3. Проверьте доступность api.openai.com

### Проблема: Турбо режим не работает

**Решение:**
1. Проверьте логи RAG-сервиса
2. Убедитесь, что файл `openai_service.py` скопирован в контейнер
3. Пересоберите контейнер: `docker-compose build --no-cache rag-service`

## 💰 Стоимость

### GPT-4o-mini:
- **Входные токены**: $0.15 за 1M токенов
- **Выходные токены**: $0.60 за 1M токенов
- **Примерная стоимость**: ~$0.001 за запрос

### Мониторинг использования:

1. Перейдите в [OpenAI Usage Dashboard](https://platform.openai.com/usage)
2. Настройте лимиты расходов
3. Включите уведомления о превышении лимитов

## 🔒 Безопасность

### Рекомендации:

1. **Никогда не коммитьте API ключи** в репозиторий
2. **Используйте переменные окружения** для хранения ключей
3. **Регулярно ротируйте API ключи**
4. **Настройте лимиты расходов** в OpenAI
5. **Мониторьте использование** API

### Файлы для исключения из Git:

```gitignore
.env
.env.local
.env.production
*.key
secrets/
```

## 📚 Дополнительные ресурсы

- [OpenAI API Documentation](https://platform.openai.com/docs)
- [GPT-4o-mini Model Details](https://platform.openai.com/docs/models/gpt-4o-mini)
- [OpenAI Pricing](https://openai.com/pricing)
- [Best Practices for API Key Security](https://platform.openai.com/docs/guides/production-best-practices/api-keys)

---

*Документация обновлена: $(date)*
*Автор: AI Assistant*




