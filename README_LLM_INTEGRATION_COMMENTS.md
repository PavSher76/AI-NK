# Комментарии для LLM интеграции в Document Parser

## 📋 Обзор

В файле `document_parser/main.py` добавлены подробные комментарии, отмечающие все места отправки запросов к LLM и получения результатов проверки. Это помогает лучше понимать процесс интеграции с языковыми моделями.

## 🔍 Отмеченные места LLM интеграции

### 1. Основная функция проверки нормоконтроля

#### `perform_norm_control_check()`
```python
async def perform_norm_control_check(self, document_id: int, document_content: str) -> Dict[str, Any]:
    """Выполнение проверки нормоконтроля для документа по страницам с применением LLM"""
    try:
        # ===== ОСНОВНАЯ ФУНКЦИЯ ПРОВЕРКИ НОРМОКОНТРОЛЯ С LLM =====
```

**Назначение**: Главная функция, которая координирует процесс проверки документа с использованием LLM.

### 2. Проверка отдельных страниц

#### `perform_norm_control_check_for_page()`
```python
async def perform_norm_control_check_for_page(self, document_id: int, page_data: Dict[str, Any]) -> Dict[str, Any]:
    """Выполнение проверки нормоконтроля для одной страницы документа"""
```

**Места отправки запросов к LLM**:
```python
# ===== ОТПРАВКА ЗАПРОСА К LLM ДЛЯ ПРОВЕРКИ СТРАНИЦЫ =====
# Отправляем запрос к LLM через gateway для выполнения нормоконтроля
logger.info(f"Sending request to LLM for page {page_number}...")

async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
    response = await client.post(
        "http://gateway:8443/v1/chat/completions",
        headers={
            "Authorization": "Bearer test-token",
            "Content-Type": "application/json"
        },
        json={
            "model": "llama3.1:8b",
            "messages": [
                {"role": "system", "content": "Ты — эксперт по нормоконтролю проектной документации."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1
        }
    )
```

**Места получения результатов**:
```python
# ===== ПОЛУЧЕНИЕ РЕЗУЛЬТАТА ПРОВЕРКИ ОТ LLM =====
if response.status_code == 200:
    result = response.json()
    content = result["choices"][0]["message"]["content"]
    
    # Парсим JSON ответ от LLM
    try:
        # ... парсинг JSON ответа
```

### 3. Вызов проверки страниц

```python
# ===== ВЫЗОВ ПРОВЕРКИ СТРАНИЦЫ С ПРИМЕНЕНИЕМ LLM =====
# Выполняем проверку для каждой страницы с использованием LLM
page_result = await self.perform_norm_control_check_for_page(document_id, page_data)
```

### 4. Сохранение результатов

```python
# ===== СОХРАНЕНИЕ РЕЗУЛЬТАТОВ ПРОВЕРКИ LLM =====
# Сохраняем общий результат проверки в базу данных
await self.save_norm_control_result(document_id, combined_result)
```

#### `save_norm_control_result()`
```python
async def save_norm_control_result(self, document_id: int, check_result: Dict[str, Any]):
    """Сохранение результата проверки нормоконтроля от LLM в базу данных"""
```

### 5. Создание отчетов

```python
# ===== СОЗДАНИЕ ОТЧЕТА О ПРОВЕРКЕ LLM =====
# Создаем отчет о проверке на основе результатов LLM
await self.create_review_report(document_id, result_id, check_result)
```

#### `create_review_report()`
```python
async def create_review_report(self, document_id: int, result_id: int, check_result: Dict[str, Any]):
    """Создание отчета о проверке на основе результатов LLM"""
```

### 6. API Endpoint для запуска проверки

```python
@app.post("/checkable-documents/{document_id}/check")
async def trigger_norm_control_check(document_id: int):
    # ===== ЗАПУСК ПРОВЕРКИ НОРМОКОНТРОЛЯ С ПРИМЕНЕНИЕМ LLM =====
    # Выполняем проверку документа с использованием LLM
    result = await parser.perform_norm_control_check(document_id, document_content)
```

## 🔧 Технические детали

### Параметры запроса к LLM

- **Модель**: `llama3.1:8b`
- **Endpoint**: `http://gateway:8443/v1/chat/completions`
- **Температура**: `0.1` (низкая для более детерминированных результатов)
- **Таймаут**: `30.0` секунд
- **Формат**: OpenAI Chat Completions API

### Структура промпта

Промпт для LLM включает:
1. **Системное сообщение**: Роль эксперта по нормоконтролю
2. **Пользовательское сообщение**: Детальный чек-лист проверки
3. **Содержимое страницы**: Текст для анализа
4. **Требования к формату ответа**: JSON структура

### Обработка ответов

1. **Парсинг JSON**: Извлечение структурированных данных из ответа LLM
2. **Валидация**: Проверка корректности полученных данных
3. **Сохранение**: Запись результатов в базу данных
4. **Создание отчетов**: Формирование отчетов на основе результатов

## 📊 Логирование

Все этапы работы с LLM логируются:

```python
logger.info(f"Sending request to LLM for page {page_number}...")
logger.info(f"Prompt length: {len(prompt)} characters")
logger.info(f"Successfully processed page {page_number}")
logger.error(f"LLM request failed: {response.status_code}")
```

## 🚀 Преимущества добавленных комментариев

1. **Прозрачность**: Четкое понимание где происходит взаимодействие с LLM
2. **Отладка**: Легче находить проблемы в LLM интеграции
3. **Документация**: Код самодокументирован
4. **Поддержка**: Упрощено сопровождение и развитие функциональности

## 📈 Мониторинг

Комментарии помогают отслеживать:
- Количество запросов к LLM
- Время выполнения проверок
- Успешность обработки ответов
- Ошибки в LLM интеграции

## 🔄 Жизненный цикл проверки с LLM

1. **Запуск проверки** → `trigger_norm_control_check()`
2. **Разбиение на страницы** → `split_document_into_pages()`
3. **Проверка каждой страницы** → `perform_norm_control_check_for_page()`
4. **Отправка запроса к LLM** → HTTP POST к gateway
5. **Получение ответа** → Парсинг JSON от LLM
6. **Сохранение результатов** → `save_norm_control_result()`
7. **Создание отчета** → `create_review_report()`

Все эти этапы отмечены соответствующими комментариями для лучшего понимания процесса.
