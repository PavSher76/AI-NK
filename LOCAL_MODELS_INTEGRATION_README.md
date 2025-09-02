# Интеграция локальных моделей Ollama и vLLM

Этот документ описывает, как интегрировать локально установленные модели Ollama (BGE-M3) и vLLM (GPT-OSS) в проект AI-NK вместо использования контейнеров.

## 🎯 Преимущества интеграции

- **Лучшая производительность** - модели работают локально без накладных расходов контейнеризации
- **Простота управления** - прямое управление моделями через командную строку
- **Гибкость настройки** - возможность настройки параметров моделей под конкретные задачи
- **Экономия ресурсов** - нет необходимости в дополнительных контейнерах

## 🤖 Требования

### 1. Ollama
- Установленный Ollama (https://ollama.ai/)
- Модель BGE-M3 для эмбеддингов

### 2. vLLM
- Установленный vLLM (`pip install vllm`)
- Модель GPT-OSS для генерации ответов

### 3. Системные требования
- Python 3.8+
- Достаточно RAM для загрузки моделей
- GPU (опционально, для ускорения vLLM)

## 🚀 Установка и настройка

### Шаг 1: Установка Ollama

```bash
# macOS
curl -fsSL https://ollama.ai/install.sh | sh

# Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Windows
# Скачайте установщик с https://ollama.ai/download
```

### Шаг 2: Загрузка модели BGE-M3

```bash
# Запускаем Ollama
ollama serve

# В новом терминале загружаем модель
ollama pull bge-m3
```

### Шаг 3: Установка vLLM

```bash
# Установка vLLM
pip install vllm

# Для GPU ускорения (CUDA)
pip install vllm[all]
```

### Шаг 4: Загрузка модели GPT-OSS

```bash
# Скачиваем модель GPT-OSS (если еще не скачана)
# Модель должна быть доступна в Ollama
ollama pull gpt-oss:20b
```

## 🔧 Запуск сервисов

### 1. Запуск vLLM

```bash
# Запуск vLLM с GPT-OSS моделью
./scripts/start_vllm.sh

# Или вручную
vllm serve --model gpt-oss:20b --port 8000 --host 0.0.0.0
```

### 2. Запуск интегрированного RAG сервиса

```bash
# Запуск интегрированного RAG сервиса
./scripts/start_integrated_rag.sh

# Или вручную
cd rag_service
python integrated_main.py
```

## 📁 Структура файлов

```
rag_service/
├── services/
│   ├── ollama_rag_service.py      # RAG сервис с Ollama BGE-M3
│   └── integrated_rag_service.py  # Интегрированный RAG сервис
├── chat_service/
│   └── vllm_chat_service.py      # Сервис чатов с vLLM GPT-OSS
├── ollama_main.py                 # Main для Ollama RAG
└── integrated_main.py             # Main для интегрированного RAG

scripts/
├── start_vllm.sh                  # Скрипт запуска vLLM
└── start_integrated_rag.sh        # Скрипт запуска интегрированного RAG
```

## 🔌 API эндпоинты

### Основные эндпоинты

- `GET /` - Информация о сервисе
- `GET /health` - Проверка здоровья сервиса
- `GET /metrics` - Метрики Prometheus
- `GET /stats` - Статистика сервиса

### Документы

- `GET /documents` - Список документов
- `GET /documents/stats` - Статистика документов
- `GET /documents/{id}/chunks` - Чанки документа
- `DELETE /documents/{id}` - Удаление документа
- `DELETE /documents/{id}/indexes` - Удаление индексов

### Поиск и консультации

- `POST /search` - Поиск по документам
- `POST /ntd-consultation/chat` - Консультация НТД
- `GET /ntd-consultation/stats` - Статистика консультаций
- `POST /reindex` - Переиндексация документов

## 🧪 Тестирование

### 1. Проверка Ollama

```bash
# Проверка доступности
curl http://localhost:11434/api/tags

# Проверка модели BGE-M3
ollama list | grep bge-m3
```

### 2. Проверка vLLM

```bash
# Проверка доступности
curl http://localhost:8000/v1/models

# Тест генерации
curl -X POST "http://localhost:8000/v1/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-oss:20b",
    "prompt": "Привет, как дела?",
    "max_tokens": 50
  }'
```

### 3. Проверка интегрированного RAG сервиса

```bash
# Проверка здоровья
curl http://localhost:8003/health

# Тест поиска
curl -X POST "http://localhost:8003/search" \
  -F "query=Что такое ГОСТ?" \
  -F "k=5"

# Тест консультации
curl -X POST "http://localhost:8003/ntd-consultation/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Что такое ГОСТ?", "user_id": "test"}'
```

## 🔍 Мониторинг

### Логи

- **Ollama**: Логи в терминале, где запущен `ollama serve`
- **vLLM**: Логи в терминале, где запущен `vllm serve`
- **RAG сервис**: Логи в терминале, где запущен `integrated_main.py`

### Метрики

- **Prometheus метрики**: `http://localhost:8003/metrics`
- **Статистика**: `http://localhost:8003/stats`
- **Здоровье**: `http://localhost:8003/health`

## 🛠️ Устранение неполадок

### Проблема: Ollama не отвечает

```bash
# Проверка статуса
ollama list

# Перезапуск
ollama serve
```

### Проблема: vLLM не отвечает

```bash
# Проверка процессов
ps aux | grep vllm

# Остановка и перезапуск
pkill -f "vllm serve"
./scripts/start_vllm.sh
```

### Проблема: RAG сервис не запускается

```bash
# Проверка зависимостей
python -c "import qdrant_client, psycopg2, requests"

# Проверка подключений
curl http://localhost:6333/collections  # Qdrant
curl http://localhost:11434/api/tags    # Ollama
curl http://localhost:8000/v1/models    # vLLM
```

### Проблема: Модели не загружены

```bash
# Проверка доступных моделей Ollama
ollama list

# Проверка доступных моделей vLLM
curl http://localhost:8000/v1/models

# Загрузка недостающих моделей
ollama pull bge-m3
ollama pull gpt-oss:20b
```

## 📊 Производительность

### Рекомендуемые настройки

- **BGE-M3**: Минимум 4GB RAM
- **GPT-OSS 20B**: Минимум 16GB RAM
- **Qdrant**: Минимум 2GB RAM
- **PostgreSQL**: Минимум 1GB RAM

### Оптимизация

- Используйте GPU для vLLM (CUDA)
- Настройте размер батча для эмбеддингов
- Оптимизируйте размер чанков документов
- Используйте индексацию в Qdrant

## 🔄 Миграция с контейнеров

### 1. Остановка контейнеров

```bash
docker-compose down
```

### 2. Запуск локальных сервисов

```bash
# Запуск Qdrant и PostgreSQL
docker-compose up qdrant norms-db -d

# Запуск vLLM
./scripts/start_vllm.sh

# Запуск интегрированного RAG
./scripts/start_integrated_rag.sh
```

### 3. Обновление конфигурации

- Обновите URL в Gateway для RAG сервиса
- Проверьте настройки CORS
- Обновите переменные окружения

## 📝 Заключение

Интеграция локальных моделей Ollama и vLLM предоставляет значительные преимущества в производительности и простоте управления. Система становится более гибкой и эффективной, позволяя настраивать параметры моделей под конкретные задачи.

Для получения дополнительной помощи обратитесь к:
- [Документация Ollama](https://ollama.ai/docs)
- [Документация vLLM](https://docs.vllm.ai/)
- [Issues проекта](https://github.com/your-repo/issues)
