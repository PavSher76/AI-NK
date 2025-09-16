# Модуль "Нормоконтроль - 2"

Расширенная система проверки формата и оформления документов на соответствие требованиям ЕСКД и СПДС.

## 🎯 Основные возможности

### 1. Проверка соответствия ЕСКД/СПДС
- **ГОСТ 21.501-2018** - Правила выполнения архитектурно-строительных чертежей
- **ГОСТ Р 21.101-2020** - Система проектной документации для строительства
- **СП 48.13330.2019** - Организация строительства
- **СП 70.13330.2012** - Несущие и ограждающие конструкции

### 2. Проверка основной надписи и спецификаций
- Наличие и правильность заполнения основной надписи
- Соответствие позиции и размеров стандарту
- Проверка обязательных полей
- Валидация форматов данных

### 3. Проверка единиц измерений
- Соответствие метрической системе
- Стандартность единиц измерений
- Согласованность единиц в документе
- Проверка форматов записи

### 4. Проверка шрифтов
- Соответствие стандартным шрифтам
- Правильность размеров шрифтов
- Согласованность шрифтов в документе
- Проверка стилей и весов

### 5. Проверка масштабов
- Стандартность масштабов
- Правильность формата записи
- Соответствие типу чертежа
- Проверка позиции масштаба

### 6. Проверка обозначений
- Стандартность символов и сокращений
- Правильность ссылок на нормативные документы
- Полнота обозначений для типа документа
- Согласованность обозначений

## 🏗️ Архитектура модуля

```
normcontrol2_service/
├── __init__.py              # Инициализация модуля
├── main.py                  # Основной сервис
├── api.py                   # API интерфейс
├── config.py                # Конфигурация
├── models.py                # Модели данных
├── validators/              # Валидаторы
│   ├── __init__.py
│   ├── eskd_validator.py    # Валидатор ЕСКД
│   ├── spds_validator.py    # Валидатор СПДС
│   ├── title_block_validator.py  # Валидатор основной надписи
│   ├── units_validator.py   # Валидатор единиц измерений
│   ├── fonts_validator.py   # Валидатор шрифтов
│   ├── scales_validator.py  # Валидатор масштабов
│   └── notations_validator.py  # Валидатор обозначений
├── example_usage.py         # Примеры использования
└── README.md               # Документация
```

## 🚀 Быстрый старт

### Установка

```bash
# Установка зависимостей
pip install fastapi uvicorn pydantic

# Или использование существующего окружения проекта
cd /path/to/AI-NK
```

### Базовое использование

```python
from normcontrol2_service import NormControl2Service

# Инициализация сервиса
service = NormControl2Service()

# Валидация документа
result = service.validate_document("path/to/document.pdf")

# Проверка результатов
print(f"Статус: {result.overall_status}")
print(f"Оценка: {result.compliance_score}%")
print(f"Проблем: {result.total_issues}")
```

### API использование

```python
import requests

# Валидация через API
response = requests.post(
    "http://localhost:8000/normcontrol2/validate",
    data={"file_path": "path/to/document.pdf"}
)

result = response.json()
print(f"Статус: {result['overall_status']}")
```

## 📋 Поддерживаемые форматы

- **PDF** - Документы в формате PDF
- **DWG** - Чертежи AutoCAD
- **DXF** - Обменный формат чертежей
- **DOCX** - Документы Word
- **XLSX** - Таблицы Excel

## 🔧 Конфигурация

### Переменные окружения

```bash
# Пороги для классификации проблем
NORM2_CRITICAL_THRESHOLD=1
NORM2_HIGH_THRESHOLD=5
NORM2_MEDIUM_THRESHOLD=10

# Настройки файлов
NORM2_MAX_FILE_SIZE_MB=100
NORM2_TIMEOUT_SECONDS=300

# Включение/отключение стандартов
NORM2_ESKD_21_501_ENABLED=true
NORM2_ESKD_R_21_101_ENABLED=true
NORM2_SPDS_48_13330_ENABLED=true
NORM2_SPDS_70_13330_ENABLED=true

# Настройки шрифтов
NORM2_MIN_FONT_SIZE=2.5
NORM2_MAX_FONT_SIZE=14.0

# Настройки масштабов
NORM2_ALLOW_CUSTOM_SCALES=false
NORM2_MAX_SCALE_VALUE=10000

# Настройки единиц измерений
NORM2_METRIC_SYSTEM_REQUIRED=true
```

### Конфигурационный файл

```json
{
  "validation": {
    "critical_issues_threshold": 1,
    "high_issues_threshold": 5,
    "medium_issues_threshold": 10,
    "compliance_score_weights": {
      "critical": 0.0,
      "high": 0.3,
      "medium": 0.6,
      "low": 0.8,
      "info": 1.0
    }
  },
  "fonts": {
    "min_font_size": 2.5,
    "max_font_size": 14.0,
    "standard_fonts": ["Arial", "Times New Roman", "Calibri"]
  }
}
```

## 📊 Результаты валидации

### Статусы соответствия

- **COMPLIANT** - Полностью соответствует требованиям
- **COMPLIANT_WITH_WARNINGS** - Соответствует с предупреждениями
- **NON_COMPLIANT** - Не соответствует требованиям
- **CRITICAL_ISSUES** - Критические нарушения
- **NEEDS_REVIEW** - Требует дополнительной проверки

### Уровни серьезности проблем

- **CRITICAL** - Критическая (блокирует приемку)
- **HIGH** - Высокая (требует исправления)
- **MEDIUM** - Средняя (рекомендуется исправить)
- **LOW** - Низкая (информационная)
- **INFO** - Информационная

### Структура результата

```python
ValidationResult(
    document_id="doc_001",
    document_name="project_drawing.pdf",
    document_format=DocumentFormat.PDF,
    validation_time=datetime.now(),
    overall_status=ComplianceStatus.COMPLIANT,
    compliance_score=95.5,
    total_issues=3,
    critical_issues=0,
    high_issues=1,
    medium_issues=2,
    low_issues=0,
    info_issues=0,
    issues=[...],  # Список проблем
    categories={...},  # Проблемы по категориям
    recommendations=[...],  # Рекомендации
    metadata={...}  # Дополнительная информация
)
```

## 🔍 API Endpoints

### POST /normcontrol2/validate
Валидация документа

**Параметры:**
- `file_path` (string) - Путь к файлу
- `document_id` (string, optional) - ID документа
- `validation_options` (string, optional) - JSON с опциями

**Ответ:**
```json
{
  "success": true,
  "document_id": "doc_001",
  "overall_status": "compliant",
  "compliance_score": 95.5,
  "total_issues": 3,
  "critical_issues": 0,
  "high_issues": 1,
  "medium_issues": 2,
  "low_issues": 0,
  "info_issues": 0,
  "categories": {...},
  "recommendations": [...],
  "validation_time": "2024-01-01T12:00:00Z",
  "metadata": {...}
}
```

### GET /normcontrol2/validate/{document_id}/issues
Получение списка проблем для документа

### GET /normcontrol2/validate/{document_id}/status
Получение статуса валидации документа

### GET /normcontrol2/validate/{document_id}/report
Получение отчета о валидации документа

### POST /normcontrol2/batch_validate
Пакетная валидация документов

### GET /normcontrol2/health
Проверка состояния сервиса

### GET /normcontrol2/rules
Получение правил валидации

### GET /normcontrol2/statistics
Получение статистики валидации

## 🧪 Тестирование

### Запуск примеров

```bash
cd normcontrol2_service
python example_usage.py
```

### Тестовые документы

Поместите тестовые документы в корневую папку проекта:
- `test_document.pdf`
- `test_document.dwg`
- `test_document.dxf`
- `test_document.docx`

## 🔧 Интеграция с существующей системой

### Интеграция с document_parser

```python
# В document_parser/app.py
from normcontrol2_service import NormControl2Service

# Инициализация сервиса
normcontrol2 = NormControl2Service()

# Валидация документа
def validate_document_normcontrol2(document_id: int, file_path: str):
    result = normcontrol2.validate_document(file_path, str(document_id))
    return result
```

### Интеграция с gateway

```python
# В gateway/app.py
from normcontrol2_service.api import router as normcontrol2_router

# Добавление роутера
app.include_router(normcontrol2_router)
```

## 📈 Мониторинг и логирование

### Логирование

```python
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('normcontrol2_service')
```

### Метрики

- Время валидации
- Количество обработанных документов
- Статистика по типам проблем
- Оценки соответствия

## 🚨 Обработка ошибок

### Типы ошибок

- **ValidationError** - Ошибки валидации
- **DocumentProcessingError** - Ошибки обработки документа
- **ConfigurationError** - Ошибки конфигурации
- **APIError** - Ошибки API

### Обработка исключений

```python
try:
    result = service.validate_document(file_path)
except ValidationError as e:
    logger.error(f"Ошибка валидации: {e}")
except DocumentProcessingError as e:
    logger.error(f"Ошибка обработки документа: {e}")
except Exception as e:
    logger.error(f"Неожиданная ошибка: {e}")
```

## 🔄 Обновления и версионирование

### Версия 2.0.0
- Первоначальный релиз
- Поддержка основных форматов документов
- Валидация по ЕСКД и СПДС
- API интерфейс
- Конфигурируемые правила

### Планы развития
- Интеграция с OCR для сканированных документов
- Машинное обучение для улучшения точности
- Поддержка дополнительных форматов
- Веб-интерфейс для настройки правил

## 📞 Поддержка

Для получения поддержки обращайтесь к команде разработки AI-NK или создавайте issues в репозитории проекта.

## 📄 Лицензия

Модуль распространяется под лицензией проекта AI-NK.
