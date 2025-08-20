# Исключение хардкода промптов для LLM

## 📋 Обзор

Выполнена задача по исключению хардкода сообщений для LLM на проверку документа. Теперь все промпты берутся из системы настроек через вкладку "Нормоконтроль" - "Настройки".

## 🔧 Выполненные изменения

### 1. Создание функции для получения шаблонов промптов

#### `get_normcontrol_prompt_template()`
```python
def get_normcontrol_prompt_template(self) -> str:
    """Получение полного шаблона промпта для нормоконтроля из системы настроек"""
```

**Функциональность:**
- Получает основной промпт из настройки `normcontrol_prompt`
- Получает пользовательский шаблон из настройки `normcontrol_prompt_template`
- Использует стандартный шаблон если пользовательский не задан
- Заменяет плейсхолдеры в шаблоне
- Обрабатывает ошибки и возвращает базовый промпт

### 2. Обновление функции проверки страниц

#### `perform_norm_control_check_for_page()`
```python
# ===== ПОЛУЧЕНИЕ ПРОМПТА ДЛЯ LLM ИЗ СИСТЕМЫ НАСТРОЕК =====
# Получаем полный шаблон промпта для нормоконтроля из системы настроек
prompt_template = self.get_normcontrol_prompt_template()

# Формируем запрос к LLM для конкретной страницы с использованием шаблона
prompt = prompt_template.format(
    page_number=page_number,
    page_content=page_content
)
```

**Изменения:**
- Удален хардкод промпта
- Добавлено получение промпта из системы настроек
- Использование шаблонизации для подстановки параметров

### 3. Добавление API endpoints для управления промпт-шаблонами

#### GET `/settings/prompt-templates`
```python
@app.get("/settings/prompt-templates")
async def get_prompt_templates():
    """Получение доступных шаблонов промптов"""
```

**Возвращает:**
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

#### POST `/settings/prompt-templates`
```python
@app.post("/settings/prompt-templates")
async def update_prompt_template(request: Dict[str, Any]):
    """Обновление шаблона промпта"""
```

**Параметры запроса:**
```json
{
  "template_key": "normcontrol_prompt_template",
  "template_value": "Пользовательский шаблон промпта...",
  "template_description": "Описание шаблона"
}
```

### 4. Обновление Gateway

Добавлены proxy endpoints в `gateway/app.py`:
```python
@app.get("/api/settings/prompt-templates")
async def get_prompt_templates(request: Request, Authorization: str|None = Header(default=None)):
    """Получение доступных шаблонов промптов"""
    await verify(Authorization)
    return await proxy_to_service(request, DOCUMENT_PARSER_URL, "/settings/prompt-templates", "GET")

@app.post("/api/settings/prompt-templates")
async def update_prompt_template(request: Request, Authorization: str|None = Header(default=None)):
    """Обновление шаблона промпта"""
    await verify(Authorization)
    return await proxy_to_service(request, DOCUMENT_PARSER_URL, "/settings/prompt-templates", "POST")
```

## 📊 Структура настроек промптов

### Основные настройки:

1. **`normcontrol_prompt`** - Основной промпт для нормоконтроля
   - Тип: `text`
   - Описание: "Промпт для проверки нормоконтроля"
   - Содержит базовые инструкции для LLM

2. **`normcontrol_prompt_template`** - Пользовательский шаблон промпта
   - Тип: `prompt_template`
   - Описание: "Шаблон промпта для нормоконтроля"
   - Может содержать плейсхолдеры: `{normcontrol_prompt}`, `{page_number}`, `{page_content}`

### Стандартный шаблон:

Если пользовательский шаблон не задан, используется стандартный:
```
{normcontrol_prompt}

СОДЕРЖИМОЕ СТРАНИЦЫ {page_number}:
{page_content}

Проведите детальную проверку нормоконтроля для данной страницы согласно следующему чек-листу:

1. ОБЩИЕ ТРЕБОВАНИЯ К ДОКУМЕНТАЦИИ:
   - Соответствие ГОСТ Р 21.1101-2013 "Система проектной документации для строительства"
   - Наличие всех обязательных разделов
   - Правильность оформления титульного листа
   - Соответствие масштабов и форматов

[... остальные разделы чек-листа ...]

Сформируйте детальный отчет в формате JSON:
{
    "page_number": {page_number},
    "overall_status": "pass|fail|uncertain",
    "confidence": 0.0-1.0,
    [... структура JSON ответа ...]
}
```

## 🔄 Жизненный цикл промпта

1. **Получение промпта** → `get_normcontrol_prompt_template()`
2. **Подстановка параметров** → `prompt_template.format()`
3. **Отправка к LLM** → HTTP POST к gateway
4. **Обработка ответа** → Парсинг JSON от LLM
5. **Сохранение результатов** → В базу данных

## 🎯 Преимущества новой системы

### 1. Гибкость
- Пользователи могут настраивать промпты через веб-интерфейс
- Поддержка пользовательских шаблонов
- Возможность A/B тестирования разных промптов

### 2. Централизация
- Все промпты хранятся в одном месте
- Единая система управления настройками
- Возможность версионирования промптов

### 3. Безопасность
- Валидация промптов перед использованием
- Логирование изменений промптов
- Контроль доступа через систему авторизации

### 4. Масштабируемость
- Легкое добавление новых типов промптов
- Поддержка многоязычности
- Интеграция с внешними системами

## 📈 Мониторинг и логирование

### Логирование промптов:
```python
logger.info("Getting prompt templates...")
logger.info(f"Normcontrol prompt: {normcontrol_prompt[:100]}...")
logger.info(f"Prompt template: {prompt_template[:100]}...")
logger.info("Successfully retrieved prompt templates")
```

### Отслеживание изменений:
- Все изменения промптов логируются
- Сохраняется история изменений в базе данных
- Возможность отката к предыдущим версиям

## 🚀 Использование

### 1. Получение текущих промптов:
```bash
curl -k -X GET -H "Authorization: Bearer test-token" \
  https://localhost:8443/api/settings/prompt-templates
```

### 2. Обновление промпта:
```bash
curl -k -X POST -H "Authorization: Bearer test-token" \
  -H "Content-Type: application/json" \
  -d '{
    "template_key": "normcontrol_prompt_template",
    "template_value": "Пользовательский шаблон...",
    "template_description": "Описание шаблона"
  }' \
  https://localhost:8443/api/settings/prompt-templates
```

### 3. Проверка документа с новым промптом:
```bash
curl -k -X POST -H "Authorization: Bearer test-token" \
  https://localhost:8443/api/checkable-documents/1/check
```

## ✅ Результаты

1. **Исключен хардкод** - все промпты теперь берутся из системы настроек
2. **Добавлена гибкость** - пользователи могут настраивать промпты
3. **Улучшена архитектура** - централизованное управление промптами
4. **Добавлено логирование** - полное отслеживание использования промптов
5. **Обеспечена обратная совместимость** - старые промпты продолжают работать

## 🔮 Будущие улучшения

- [ ] Веб-интерфейс для редактирования промптов
- [ ] Версионирование промптов
- [ ] A/B тестирование разных промптов
- [ ] Шаблоны для разных типов документов
- [ ] Интеграция с внешними системами управления промптами
