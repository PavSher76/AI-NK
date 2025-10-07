# 🗺️ Карта API эндпоинтов проекта AI-NK

## 📋 Общая информация
- **Версия API**: 1.0.0
- **Базовый URL**: `https://localhost:8443`
- **Аутентификация**: Bearer Token (`Authorization: Bearer disabled-auth`)

## 🚪 API Gateway (Порт: 8443)

### Основные эндпоинты
| Метод | Путь | Описание | Статус |
|-------|------|----------|--------|
| `GET` | `/health` | Проверка здоровья Gateway | ✅ |
| `GET` | `/api/health` | Проверка здоровья API через RAG | ✅ |
| `GET` | `/metrics` | Метрики Gateway | ✅ |

### Прокси-маршруты
| Префикс | Назначение | Сервис |
|---------|------------|--------|
| `/api/analog-objects/*` | Объекты-аналоги | analog-objects-service |
| `/api/v1/*` | API v1 | rag-service, document-parser, calculation-service |
| `/api/normcontrol2/*` | Нормоконтроль-2 | normcontrol2-service |
| `/api/archive/*` | Архив | archive-service |
| `/api/{path:path}` | Общие API | document-parser (по умолчанию) |
| `/v1/*` | VLLM API | vllm-service |
| `/ollama/*` | Ollama API | ollama (localhost:11434) |
| `/calculation/*` | Расчеты | calculation-service |

## 🧠 RAG Service (Порт: 8003)

### Документы и индексация
| Метод | Путь | Описание | Параметры |
|-------|------|----------|-----------|
| `GET` | `/` | Информация о сервисе | - |
| `GET` | `/documents` | Список документов | - |
| `GET` | `/documents/stats` | Статистика документов | - |
| `GET` | `/documents/{id}/chunks` | Чанки документа | `document_id: int` |
| `DELETE` | `/documents/{id}` | Удаление документа | `document_id: int` |
| `DELETE` | `/documents/{id}/indexes` | Удаление индексов | `document_id: int` |
| `POST` | `/reindex` | Синхронная реиндексация | - |
| `POST` | `/reindex/async` | Асинхронная реиндексация | - |
| `GET` | `/reindex/status/{task_id}` | Статус реиндексации | `task_id: str` |

### Загрузка и поиск
| Метод | Путь | Описание | Параметры |
|-------|------|----------|-----------|
| `POST` | `/upload` | Загрузка документа | `file: UploadFile` |
| `POST` | `/search` | Поиск по нормам | `query: str, k: int` |

### Чат и консультации
| Метод | Путь | Описание | Параметры |
|-------|------|----------|-----------|
| `POST` | `/chat` | Чат с ИИ | `message: str, model: str` |
| `POST` | `/ntd-consultation/chat` | Консультация НТД | `message: str, user_id: str` |
| `GET` | `/ntd-consultation/stats` | Статистика консультаций | - |
| `DELETE` | `/ntd-consultation/cache` | Очистка кэша | - |
| `GET` | `/ntd-consultation/cache/stats` | Статистика кэша | - |

### Модели и эмбеддинги
| Метод | Путь | Описание | Параметры |
|-------|------|----------|-----------|
| `GET` | `/models` | Доступные модели | - |
| `GET` | `/reasoning-modes` | Режимы рассуждения | - |
| `POST` | `/api/embeddings` | Создание эмбеддингов | `text: str` |
| `GET` | `/api/embeddings` | Получение эмбеддингов | `text: str` |

### Мониторинг и управление
| Метод | Путь | Описание | Параметры |
|-------|------|----------|-----------|
| `GET` | `/health` | Проверка здоровья | - |
| `GET` | `/metrics` | Метрики сервиса | - |
| `GET` | `/stats` | Статистика | - |
| `POST` | `/clear-collection` | Очистка коллекции | - |

### Индексация (устойчивая)
| Метод | Путь | Описание | Параметры |
|-------|------|----------|-----------|
| `POST` | `/indexing/start` | Запуск индексации | - |
| `POST` | `/indexing/stop` | Остановка индексации | - |
| `GET` | `/indexing/status` | Статус индексации | - |
| `POST` | `/indexing/retry-failed` | Повтор неудачных | `max_retries: int` |
| `GET` | `/indexing/pending` | Ожидающие документы | - |
| `GET` | `/indexing/failed` | Неудачные документы | `max_retries: int` |

### Тестирование
| Метод | Путь | Описание | Параметры |
|-------|------|----------|-----------|
| `POST` | `/test-chunking` | Тест чанкинга | - |
| `POST` | `/test-reranker` | Тест ранжирования | - |
| `POST` | `/test-turbo-reasoning` | Тест турбо-рассуждений | - |

## 🧮 Calculation Service (Порт: 8002)

### Аутентификация
| Метод | Путь | Описание | Параметры |
|-------|------|----------|-----------|
| `POST` | `/token` | Получение токена | `username, password` |
| `GET` | `/me` | Информация о пользователе | `Authorization: Bearer` |

### CRUD операции
| Метод | Путь | Описание | Параметры |
|-------|------|----------|-----------|
| `POST` | `/calculations` | Создание расчета | `calculation_data` |
| `GET` | `/calculations` | Список расчетов | `skip, limit, user_id` |
| `GET` | `/calculations/{id}` | Получение расчета | `calculation_id: int` |
| `PUT` | `/calculations/{id}` | Обновление расчета | `calculation_id: int` |
| `DELETE` | `/calculations/{id}` | Удаление расчета | `calculation_id: int` |

### Типы расчетов
| Метод | Путь | Описание | Параметры |
|-------|------|----------|-----------|
| `GET` | `/calculations/structural/types` | Структурные расчеты | - |
| `GET` | `/calculations/degasification/types` | Расчеты дегазации | - |
| `GET` | `/calculations/electrical/types` | Электротехнические | - |
| `GET` | `/calculations/thermal/types` | Теплотехнические | - |
| `GET` | `/calculations/ventilation/types` | Вентиляционные | - |
| `GET` | `/calculations/water_supply/types` | Водоснабжение | - |
| `GET` | `/calculations/fire_safety/types` | Пожарная безопасность | - |
| `GET` | `/calculations/acoustic/types` | Акустические | - |
| `GET` | `/calculations/lighting/types` | Освещение | - |
| `GET` | `/calculations/geological/types` | Геологические | - |
| `GET` | `/calculations/uav_protection/types` | Защита от БПЛА | - |

### Выполнение расчетов
| Метод | Путь | Описание | Параметры |
|-------|------|----------|-----------|
| `POST` | `/calculations/structural/execute` | Структурные | `input_data` |
| `POST` | `/calculations/degasification/execute` | Дегазация | `input_data` |
| `POST` | `/calculations/electrical/execute` | Электротехнические | `input_data` |
| `POST` | `/calculations/thermal/execute` | Теплотехнические | `input_data` |
| `POST` | `/calculations/ventilation/execute` | Вентиляционные | `input_data` |
| `POST` | `/calculations/water_supply/execute` | Водоснабжение | `input_data` |
| `POST` | `/calculations/fire_safety/execute` | Пожарная безопасность | `input_data` |
| `POST` | `/calculations/acoustic/execute` | Акустические | `input_data` |
| `POST` | `/calculations/lighting/execute` | Освещение | `input_data` |
| `POST` | `/calculations/geological/execute` | Геологические | `input_data` |
| `POST` | `/calculations/uav_protection/execute` | Защита от БПЛА | `input_data` |
| `POST` | `/calculations/{id}/execute` | Общий расчет | `calculation_id: int` |

### Экспорт и метрики
| Метод | Путь | Описание | Параметры |
|-------|------|----------|-----------|
| `GET` | `/calculations/{id}/export-docx` | Экспорт в DOCX | `calculation_id: int` |
| `GET` | `/metrics` | Метрики сервиса | - |
| `GET` | `/health` | Проверка здоровья | - |

## 🔍 NormControl2 Service (Порт: 8010)

### Основные эндпоинты
| Метод | Путь | Описание | Параметры |
|-------|------|----------|-----------|
| `GET` | `/` | Информация о сервисе | - |
| `GET` | `/health` | Проверка здоровья | - |

## 📤 Outgoing Control Service (Порт: 8006)

### Управление документами
| Метод | Путь | Описание | Параметры |
|-------|------|----------|-----------|
| `POST` | `/upload` | Загрузка документа | `file: UploadFile` |
| `GET` | `/documents` | Список документов | - |
| `GET` | `/documents/{id}` | Получение документа | `document_id: str` |
| `DELETE` | `/documents/{id}` | Удаление документа | `document_id: str` |
| `GET` | `/report/{id}` | Получение отчета | `document_id: str` |

### Проверки
| Метод | Путь | Описание | Параметры |
|-------|------|----------|-----------|
| `POST` | `/spellcheck` | Проверка орфографии | `text: str` |
| `POST` | `/grammar-check` | Проверка грамматики | `text: str` |
| `POST` | `/comprehensive-check` | Комплексная проверка | `text: str` |
| `POST` | `/expert-analysis` | Экспертный анализ | `text: str` |
| `POST` | `/consolidate` | Консолидация результатов | `results: list` |

### Настройки и статус
| Метод | Путь | Описание | Параметры |
|-------|------|----------|-----------|
| `GET` | `/settings` | Получение настроек | - |
| `POST` | `/settings` | Обновление настроек | `settings: dict` |
| `GET` | `/spellchecker-status` | Статус проверки орфографии | - |
| `GET` | `/spellchecker-stats` | Статистика проверки | - |
| `GET` | `/health` | Проверка здоровья | - |

### Отладка
| Метод | Путь | Описание | Параметры |
|-------|------|----------|-----------|
| `GET` | `/debug/documents` | Отладочная информация | - |

## ✍️ Spellchecker Service (Порт: 8007)

### Проверки
| Метод | Путь | Описание | Параметры |
|-------|------|----------|-----------|
| `POST` | `/spellcheck` | Проверка орфографии | `text: str, language: str` |
| `POST` | `/grammar-check` | Проверка грамматики | `text: str, language: str` |
| `POST` | `/comprehensive-check` | Комплексная проверка | `text: str, language: str` |

### Информация
| Метод | Путь | Описание | Параметры |
|-------|------|----------|-----------|
| `GET` | `/languages` | Поддерживаемые языки | - |
| `GET` | `/stats` | Статистика сервиса | - |
| `GET` | `/health` | Проверка здоровья | - |

## 🚀 VLLM Service (Порт: 8005)

### Основные функции
| Метод | Путь | Описание | Параметры |
|-------|------|----------|-----------|
| `GET` | `/` | Информация о сервисе | - |
| `GET` | `/health` | Проверка здоровья | - |
| `GET` | `/models` | Доступные модели | - |
| `POST` | `/chat` | Чат с ИИ | `message: str, model: str` |

### Работа с документами
| Метод | Путь | Описание | Параметры |
|-------|------|----------|-----------|
| `POST` | `/upload_document` | Загрузка документа | `file: UploadFile` |
| `POST` | `/chat_with_document` | Чат с документом | `message: str, document_id: str` |

### Статистика и мониторинг
| Метод | Путь | Описание | Параметры |
|-------|------|----------|-----------|
| `GET` | `/stats` | Статистика сервиса | - |
| `GET` | `/logs/stats` | Статистика логов | - |
| `GET` | `/chat_documents_stats` | Статистика чата с документами | - |

## 🔧 Ollama (Порт: 11434)

### Управление моделями
| Метод | Путь | Описание | Параметры |
|-------|------|----------|-----------|
| `GET` | `/api/tags` | Список моделей | - |
| `POST` | `/api/generate` | Генерация текста | `model: str, prompt: str` |
| `POST` | `/api/chat` | Чат с моделью | `model: str, messages: list` |

## 📊 Статус коды

| Код | Описание |
|-----|----------|
| `200` | Успешный запрос |
| `201` | Ресурс создан |
| `400` | Неверный запрос |
| `401` | Не авторизован |
| `403` | Доступ запрещен |
| `404` | Ресурс не найден |
| `422` | Ошибка валидации |
| `500` | Внутренняя ошибка сервера |
| `503` | Сервис недоступен |

## 🔐 Аутентификация

### Получение токена
```bash
curl -X POST "https://localhost:8443/calculation/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin"
```

### Использование токена
```bash
curl -X GET "https://localhost:8443/calculation/me" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 📝 Примеры использования

### Загрузка документа в RAG
```bash
curl -X POST "https://localhost:8443/api/upload" \
  -H "Authorization: Bearer disabled-auth" \
  -F "file=@document.pdf"
```

### Чат с ИИ
```bash
curl -X POST "https://localhost:8443/api/rag/chat" \
  -H "Authorization: Bearer disabled-auth" \
  -H "Content-Type: application/json" \
  -d '{"message": "Привет", "model": "llama3.1:8b"}'
```

### Создание расчета
```bash
curl -X POST "https://localhost:8443/calculation/calculations" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Тестовый расчет", "type": "structural"}'
```

## 🚨 Важные замечания

1. **Порты**: Убедитесь, что все порты доступны
2. **SSL**: Используйте HTTPS для всех запросов
3. **Таймауты**: Некоторые операции могут занимать время
4. **Размер файлов**: Ограничения на размер загружаемых файлов
5. **Аутентификация**: Некоторые эндпоинты требуют токен

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи сервисов: `docker-compose logs [service-name]`
2. Убедитесь в доступности всех сервисов: `docker-compose ps`
3. Проверьте конфигурацию в `docker-compose.yaml`
