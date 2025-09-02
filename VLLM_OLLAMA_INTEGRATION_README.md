# VLLM + Ollama Integration Service

## 📋 Обзор

VLLM + Ollama Integration Service - это сервис, который обеспечивает интеграцию между vLLM и локально установленным Ollama. Сервис предоставляет единый API для работы с моделями Ollama, включая проверку статуса, генерацию ответов и мониторинг.

## 🏗️ Архитектура

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │───▶│  VLLM Service   │───▶│   Ollama        │
│   (Port 443)    │    │   (Port 8005)   │    │  (Port 11434)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Быстрый старт

### 1. Запуск Ollama

```bash
# Запуск Ollama сервиса
ollama serve

# Проверка доступности
curl http://localhost:11434/api/tags
```

### 2. Запуск VLLM + Ollama Service

```bash
# Использование скрипта (рекомендуется)
./scripts/start_vllm_ollama.sh

# Или ручной запуск
cd vllm_service
python main.py
```

### 3. Проверка работы

```bash
# Проверка здоровья сервиса
curl http://localhost:8005/health

# Список доступных моделей
curl http://localhost:8005/models

# Тест чата
curl -X POST "http://localhost:8005/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Привет!", "model": "gpt-oss:20b"}'
```

## 📁 Структура проекта

```
vllm_service/
├── main.py                    # FastAPI приложение
├── vllm_ollama_service.py    # Основная логика сервиса
└── requirements.txt           # Зависимости

frontend/src/
├── components/
│   └── OllamaStatusChecker.js # Компонент проверки статуса
└── pages/
    └── OllamaMonitor.js       # Страница мониторинга

scripts/
└── start_vllm_ollama.sh      # Скрипт запуска
```

## 🔧 API Endpoints

### Основные эндпоинты

| Метод | Endpoint | Описание |
|-------|----------|----------|
| `GET` | `/` | Информация о сервисе |
| `GET` | `/health` | Проверка здоровья |
| `GET` | `/models` | Список моделей Ollama |
| `POST` | `/chat` | Генерация ответа |
| `GET` | `/stats` | Статистика сервиса |

### Детальное описание

#### `GET /health`
Проверка здоровья сервиса и всех компонентов.

**Ответ:**
```json
{
  "status": "healthy",
  "services": {
    "ollama": {
      "status": "healthy",
      "ollama_url": "http://localhost:11434",
      "available_models": ["bge-m3", "gpt-oss:20b"],
      "bge_m3_available": true,
      "gpt_oss_available": true,
      "total_models": 2
    },
    "vllm": {
      "status": "healthy",
      "url": "http://localhost:8000"
    }
  },
  "timestamp": "2025-08-31T10:00:00"
}
```

#### `GET /models`
Получение списка доступных моделей Ollama с детальной информацией.

**Ответ:**
```json
{
  "status": "success",
  "models": [
    {
      "name": "bge-m3",
      "size": "1.5GB",
      "parameters": "1024",
      "template": "embedding"
    }
  ],
  "total_count": 1,
  "timestamp": "2025-08-31T10:00:00"
}
```

#### `POST /chat`
Генерация ответа через выбранную модель Ollama.

**Запрос:**
```json
{
  "message": "Расскажи о машинном обучении",
  "model": "gpt-oss:20b",
  "history": [
    {"role": "user", "content": "Привет"},
    {"role": "assistant", "content": "Здравствуйте!"}
  ],
  "max_tokens": 2048
}
```

**Ответ:**
```json
{
  "status": "success",
  "response": "Машинное обучение - это подраздел искусственного интеллекта...",
  "model": "gpt-oss:20b",
  "prompt_tokens": 45,
  "response_tokens": 128,
  "total_tokens": 173,
  "timestamp": "2025-08-31T10:00:00"
}
```

## 🎯 Функциональность

### 1. Проверка статуса Ollama
- Автоматическая проверка доступности
- Кэширование результатов (30 секунд)
- Детальная информация о моделях
- Время отклика API

### 2. Интеграция с vLLM
- Проверка статуса vLLM сервиса
- Совместимость с vLLM API
- Fallback на Ollama при недоступности vLLM

### 3. Генерация ответов
- Поддержка истории чата
- Настраиваемые параметры генерации
- Обработка ошибок
- Логирование операций

### 4. Мониторинг
- Статус всех компонентов
- Статистика использования
- Автоматические проверки
- Уведомления об ошибках

## 🖥️ Frontend интеграция

### Компонент OllamaStatusChecker

```jsx
import OllamaStatusChecker from '../components/OllamaStatusChecker';

// Использование в компоненте
<OllamaStatusChecker />
```

**Возможности:**
- Автоматическая проверка статуса каждые 30 секунд
- Визуальные индикаторы состояния
- Детальная информация о моделях
- Тестирование чата
- Обновление в реальном времени

### Страница мониторинга

```jsx
import OllamaMonitor from '../pages/OllamaMonitor';

// Использование в роутере
<Route path="/ollama-monitor" element={<OllamaMonitor />} />
```

**Функции:**
- Общий обзор системы
- Статус всех сервисов
- Инструкции по использованию
- Информация о конфигурации

## ⚙️ Конфигурация

### Переменные окружения

```bash
# URL Ollama (по умолчанию: http://localhost:11434)
OLLAMA_URL=http://localhost:11434

# URL vLLM (по умолчанию: http://localhost:8000)
VLLM_URL=http://localhost:8000

# Порт сервиса (по умолчанию: 8005)
VLLM_OLLAMA_PORT=8005
```

### Настройка моделей

```bash
# Установка BGE-M3 для эмбеддингов
ollama pull bge-m3

# Установка GPT-OSS для чата
ollama pull gpt-oss:20b

# Проверка установленных моделей
ollama list
```

## 🔍 Мониторинг и отладка

### Логи

```bash
# Просмотр логов сервиса
tail -f vllm_service.log

# Логи Ollama
ollama logs

# Логи vLLM
vllm logs
```

### Метрики

```bash
# Статус здоровья
curl http://localhost:8005/health

# Статистика
curl http://localhost:8005/stats

# Список моделей
curl http://localhost:8005/models
```

### Диагностика

```bash
# Проверка процессов
ps aux | grep -E "(ollama|vllm|main.py)"

# Проверка портов
lsof -i :11434  # Ollama
lsof -i :8005   # VLLM + Ollama Service
lsof -i :8000   # vLLM (если запущен)

# Проверка сетевых соединений
netstat -an | grep -E "(11434|8001|8000)"
```

## 🛠️ Устранение неполадок

### Частые проблемы

#### 1. Ollama не отвечает
```bash
# Проверка статуса
ollama list

# Перезапуск
pkill ollama
ollama serve

# Проверка порта
lsof -i :11434
```

#### 2. Модели не найдены
```bash
# Установка моделей
ollama pull bge-m3
ollama pull gpt-oss:20b

# Проверка
ollama list
```

#### 3. Сервис не запускается
```bash
# Проверка зависимостей
pip install -r vllm_service/requirements.txt

# Проверка Python версии
python --version

# Запуск с отладкой
python -u main.py
```

#### 4. Ошибки CORS
```bash
# Проверка настроек CORS в main.py
# Убедитесь, что allow_origins=["*"]
```

### Отладка

```bash
# Запуск с подробными логами
export PYTHONPATH="$PWD/vllm_service:$PYTHONPATH"
cd vllm_service
python -u main.py

# Проверка API вручную
curl -v http://localhost:8005/health
```

## 📊 Производительность

### Оптимизация

1. **Кэширование статуса**: 30 секунд для избежания частых запросов
2. **Асинхронная обработка**: Неблокирующие операции
3. **Таймауты**: Настроенные таймауты для API вызовов
4. **Логирование**: Структурированные логи для анализа

### Мониторинг

- Время отклика API
- Количество запросов
- Статус моделей
- Использование ресурсов

## 🔐 Безопасность

### Рекомендации

1. **Ограничение доступа**: Настройка firewall для портов
2. **Аутентификация**: Добавление JWT токенов при необходимости
3. **Валидация**: Проверка входных данных
4. **Логирование**: Аудит всех операций

## 📈 Развитие

### Планируемые улучшения

- [ ] Поддержка WebSocket для real-time обновлений
- [ ] Интеграция с Prometheus для метрик
- [ ] Поддержка дополнительных моделей
- [ ] Автоматическое масштабирование
- [ ] Интеграция с системой уведомлений

### API версионирование

```bash
# Текущая версия
GET /v1/health

# Будущие версии
GET /v2/health
GET /v3/health
```

## 📚 Дополнительные ресурсы

- [Документация Ollama](https://ollama.ai/docs)
- [Документация vLLM](https://docs.vllm.ai/)
- [FastAPI документация](https://fastapi.tiangolo.com/)
- [React документация](https://react.dev/)

## 🤝 Поддержка

### Сообщение об ошибках

При возникновении проблем:

1. Проверьте логи сервиса
2. Убедитесь в доступности Ollama
3. Проверьте конфигурацию
4. Создайте issue с описанием проблемы

### Контакты

- **Проект**: AI-NK
- **Версия**: 1.0.0
- **Дата**: Август 2025

---

**Примечание**: Этот сервис предназначен для локального использования и интеграции с Ollama. Для production окружения рекомендуется дополнительная настройка безопасности и мониторинга.
