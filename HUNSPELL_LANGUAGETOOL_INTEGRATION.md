# Интеграция Hunspell + LanguageTool для проверки орфографии и грамматики

## Обзор

Данная интеграция добавляет продвинутую проверку орфографии и грамматики в модуль "Выходной контроль корреспонденции" с использованием:

- **Hunspell** - для проверки орфографии
- **LanguageTool** - для проверки грамматики и стиля

## Архитектура

### Компоненты

1. **AdvancedSpellChecker** (`spell_checker.py`) - основной класс для проверки
2. **API Endpoints** - REST API для взаимодействия
3. **Docker Integration** - контейнеризация с необходимыми зависимостями

### API Endpoints

#### 1. Проверка орфографии
```http
POST /api/outgoing-control/spellcheck
Content-Type: application/json

{
    "document_id": "uuid",
    "text": "текст для проверки"
}
```

**Ответ:**
```json
{
    "status": "success",
    "spell_check_results": {
        "total_words": 150,
        "misspelled_count": 3,
        "errors": [
            {
                "word": "ошибка",
                "position": 5,
                "context": "...текст с ошибка...",
                "suggestions": ["ошибка", "ошибки"],
                "type": "spelling"
            }
        ],
        "accuracy": 98.0
    }
}
```

#### 2. Проверка грамматики
```http
POST /api/outgoing-control/grammar-check
Content-Type: application/json

{
    "document_id": "uuid",
    "text": "текст для проверки"
}
```

**Ответ:**
```json
{
    "status": "success",
    "grammar_results": {
        "errors": [
            {
                "message": "Избыточность: 'это есть'",
                "context": "...это есть ошибка...",
                "offset": 10,
                "length": 8,
                "replacements": ["это", "есть"],
                "rule_id": "RU_REDUNDANCY",
                "type": "grammar"
            }
        ],
        "total_errors": 1
    }
}
```

#### 3. Комплексная проверка
```http
POST /api/outgoing-control/comprehensive-check
Content-Type: application/json

{
    "document_id": "uuid",
    "text": "текст для проверки"
}
```

**Ответ:**
```json
{
    "status": "success",
    "comprehensive_results": {
        "spelling": { /* результаты проверки орфографии */ },
        "grammar": { /* результаты проверки грамматики */ },
        "total_errors": 5,
        "all_errors": [ /* объединенный список ошибок */ ],
        "overall_accuracy": 96.7
    }
}
```

## Установка и настройка

### 1. Системные зависимости

В Dockerfile установлены:
- `hunspell` - основной движок проверки орфографии
- `hunspell-ru` - русский словарь
- `openjdk-11-jre-headless` - для LanguageTool
- `wget`, `unzip` - для загрузки LanguageTool

### 2. Python зависимости

```bash
pip install -r requirements.txt
```

Включает:
- `hunspell==0.5.1` - Python обертка для Hunspell
- `language-tool-python==2.7.1` - Python клиент для LanguageTool
- `nltk==3.8.1` - обработка естественного языка
- `spacy==3.7.2` - продвинутая обработка текста

### 3. Словари Hunspell

Словари устанавливаются автоматически через пакет `hunspell-ru`:
- `/usr/share/hunspell/ru_RU.aff` - аффиксы
- `/usr/share/hunspell/ru_RU.dic` - словарь

### 4. LanguageTool

LanguageTool загружается и устанавливается в `/opt/languagetool`:
- Версия: 6.1
- Язык: русский (ru-RU)
- Переменная окружения: `LANGUAGETOOL_HOME`

## Использование

### 1. Запуск сервиса

```bash
docker compose build --no-cache outgoing-control-service
docker compose up -d outgoing-control-service
```

### 2. Тестирование

```bash
python test_hunspell_languagetool.py
```

### 3. Интеграция в фронтенд

Обновить `OutgoingControlPage.js` для использования новых эндпоинтов:

```javascript
// Комплексная проверка
const comprehensiveCheck = async (documentId, text) => {
    const response = await fetch(`${API_BASE}/outgoing-control/comprehensive-check`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${authToken}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            document_id: documentId,
            text: text
        })
    });
    
    return await response.json();
};
```

## Возможности

### Hunspell
- ✅ Проверка орфографии русского языка
- ✅ Предложения по исправлению
- ✅ Морфологический анализ
- ✅ Быстрая работа
- ✅ Легковесность

### LanguageTool
- ✅ Проверка грамматики
- ✅ Проверка пунктуации
- ✅ Стилистические правила
- ✅ Согласование слов
- ✅ Избыточность и повторы

### Комбинированный подход
- ✅ Объединение результатов
- ✅ Сортировка ошибок по позиции
- ✅ Общая оценка качества
- ✅ Детальная отчетность

## Ограничения

1. **Размер словарей** - Hunspell словари могут быть большими
2. **Производительность** - LanguageTool требует Java и может быть медленным
3. **Точность** - Автоматическая проверка не всегда идеальна
4. **Контекст** - Некоторые ошибки требуют человеческого понимания

## Рекомендации

1. **Кэширование** - Кэшировать результаты проверки
2. **Асинхронность** - Использовать асинхронные вызовы
3. **Мониторинг** - Отслеживать производительность
4. **Настройка** - Настраивать правила под конкретные задачи

## Альтернативы

1. **Yandex Speller API** - облачный сервис
2. **Grammarly API** - коммерческий сервис
3. **Custom ML models** - собственные модели
4. **Rule-based systems** - системы на правилах

## Заключение

Интеграция Hunspell + LanguageTool обеспечивает мощную проверку орфографии и грамматики для русского языка, подходящую для корпоративного использования в системе выходного контроля корреспонденции.
