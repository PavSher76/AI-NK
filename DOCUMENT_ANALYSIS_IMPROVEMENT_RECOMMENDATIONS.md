# Рекомендации по настройке анализа проверки документа

## 🎯 **Цель улучшений**

Создать комплексную систему анализа проектной документации, которая будет выполнять следующие задачи:

1. **Анализ первой страницы** - извлечение ключевой информации о проекте
2. **Проверка подписей** - анализ списка исполнителей и УКЭП
3. **Проверка орфографии** - выявление опечаток и ошибок
4. **Анализ листа "Общие данные"** - проверка соответствия НТД
5. **Проверка остальных листов** - комплексный анализ на соответствие НТД

## 📋 **1. Анализ первой страницы документа**

### **1.1 Требуемые элементы для извлечения:**

#### **Основная информация:**
- **Название проекта** - полное наименование проекта
- **Стадия проектирования** - "Проектная документация" или "Рабочая документация"
- **Марка комплекта** - "Архитектурные решения", "Конструктивные решения", "Технологические решения" и т.д.
- **Шифр документа** - уникальный идентификатор документа

#### **Рекомендуемые изменения в коде:**

```python
def extract_first_page_info(self, page_content: str) -> Dict[str, Any]:
    """Извлечение ключевой информации с первой страницы документа"""
    
    # Создаем специализированный промпт для первой страницы
    first_page_prompt = """
    Ты - эксперт по анализу проектной документации. Проанализируй первую страницу документа и извлеки следующую информацию:
    
    ДОКУМЕНТ ДЛЯ АНАЛИЗА:
    {page_content}
    
    ИНСТРУКЦИИ:
    1. Найди и извлеки название проекта
    2. Определи стадию проектирования (Проектная документация / Рабочая документация)
    3. Найди марку комплекта (Архитектурные решения, Конструктивные решения, Технологические решения и т.д.)
    4. Извлеки шифр документа
    
    ВОЗВРАТИ JSON В ФОРМАТЕ:
    {
        "project_name": "название проекта",
        "design_stage": "Проектная документация|Рабочая документация",
        "document_mark": "марка комплекта",
        "document_code": "шифр документа",
        "confidence": 0.0-1.0,
        "extraction_notes": "заметки по извлечению"
    }
    """
    
    # Отправляем запрос к LLM
    response = await self.send_llm_request(first_page_prompt.format(page_content=page_content))
    return json.loads(response)
```

### **1.2 Интеграция в основной процесс:**

```python
async def perform_norm_control_check(self, document_id: int, document_content: str) -> Dict[str, Any]:
    """Выполнение проверки нормоконтроля для документа"""
    
    # Шаг 1: Анализ первой страницы
    first_page_info = await self.extract_first_page_info(pages[0]['content'])
    
    # Сохраняем информацию о проекте
    await self.save_project_info(document_id, first_page_info)
    
    # Продолжаем с остальными проверками...
```

## 🔍 **2. Анализ списка исполнителей и подписей**

### **2.1 Требуемые проверки:**

#### **Элементы для анализа:**
- **Список исполнителей** - поиск и извлечение списка
- **Подписанты документа** - определение кто подписал документ
- **УКЭП проверка** - наличие электронной подписи
- **Соответствие требованиям** - проверка обязательных подписей

#### **Рекомендуемые изменения:**

```python
def analyze_executors_and_signatures(self, page_content: str) -> Dict[str, Any]:
    """Анализ списка исполнителей и подписей документа"""
    
    signature_prompt = """
    Ты - эксперт по проверке подписей в проектной документации. Проанализируй документ и найди:
    
    ДОКУМЕНТ ДЛЯ АНАЛИЗА:
    {page_content}
    
    ИНСТРУКЦИИ:
    1. Найди "Список исполнителей" или аналогичный раздел
    2. Извлеки всех исполнителей проекта
    3. Определи кто подписал документ
    4. Проверь наличие УКЭП (усиленной квалифицированной электронной подписи)
    5. Проверь соответствие требованиям по подписям
    
    ВОЗВРАТИ JSON В ФОРМАТЕ:
    {
        "executors_found": true/false,
        "executors_list": ["исполнитель1", "исполнитель2"],
        "signatures_found": true/false,
        "signers": ["подписант1", "подписант2"],
        "ukep_present": true/false,
        "ukep_details": "информация об УКЭП",
        "compliance_status": "соответствует|не соответствует|частично соответствует",
        "missing_signatures": ["отсутствующие подписи"],
        "recommendations": "рекомендации по исправлению"
    }
    """
    
    response = await self.send_llm_request(signature_prompt.format(page_content=page_content))
    return json.loads(response)
```

### **2.2 Интеграция в процесс:**

```python
# В основной функции проверки
signature_analysis = await self.analyze_executors_and_signatures(document_content)

# Сохраняем результаты анализа подписей
await self.save_signature_analysis(document_id, signature_analysis)
```

## 📝 **3. Проверка орфографии и опечаток**

### **3.1 Требуемые проверки:**

#### **Типы ошибок для выявления:**
- **Орфографические ошибки** - неправильное написание слов
- **Опечатки** - случайные ошибки в тексте
- **Пунктуационные ошибки** - неправильная расстановка знаков препинания
- **Технические термины** - проверка корректности специальной терминологии

#### **Рекомендуемые изменения:**

```python
def check_spelling_and_typos(self, page_content: str) -> Dict[str, Any]:
    """Проверка орфографии и опечаток в документе"""
    
    spelling_prompt = """
    Ты - эксперт по проверке орфографии и грамматики в проектной документации. Проверь документ на ошибки:
    
    ДОКУМЕНТ ДЛЯ ПРОВЕРКИ:
    {page_content}
    
    ИНСТРУКЦИИ:
    1. Найди все орфографические ошибки
    2. Выяви опечатки и описки
    3. Проверь пунктуацию
    4. Проверь корректность технических терминов
    5. Обрати внимание на названия нормативных документов
    
    ВОЗВРАТИ JSON В ФОРМАТЕ:
    {
        "spelling_errors": [
            {
                "error": "неправильное слово",
                "correction": "правильное слово",
                "context": "контекст ошибки",
                "severity": "critical|warning|info"
            }
        ],
        "typos": [
            {
                "error": "опечатка",
                "correction": "исправление",
                "context": "контекст",
                "severity": "critical|warning|info"
            }
        ],
        "punctuation_errors": [...],
        "technical_term_errors": [...],
        "total_errors": число,
        "error_summary": "общая оценка качества текста"
    }
    """
    
    response = await self.send_llm_request(spelling_prompt.format(page_content=page_content))
    return json.loads(response)
```

### **3.2 Интеграция:**

```python
# Проверка орфографии для всего документа
spelling_analysis = await self.check_spelling_and_typos(document_content)

# Сохраняем результаты
await self.save_spelling_analysis(document_id, spelling_analysis)
```

## 📊 **4. Анализ листа "Общие данные"**

### **4.1 Требуемые проверки:**

#### **Элементы для анализа:**
- **Наличие листа "Общие данные"** - поиск и идентификация
- **Соответствие НТД** - проверка всех требований
- **Заполненность разделов** - полнота информации
- **Актуальность данных** - соответствие современным нормам

#### **Рекомендуемые изменения:**

```python
def analyze_general_data_sheet(self, page_content: str) -> Dict[str, Any]:
    """Анализ листа "Общие данные" на соответствие НТД"""
    
    general_data_prompt = """
    Ты - эксперт по проверке листа "Общие данные" в проектной документации. Проанализируй лист на соответствие НТД:
    
    ДОКУМЕНТ ДЛЯ АНАЛИЗА:
    {page_content}
    
    ИНСТРУКЦИИ:
    1. Определи является ли это листом "Общие данные"
    2. Проверь наличие всех обязательных разделов
    3. Проверь соответствие требованиям НТД
    4. Выяви нарушения и несоответствия
    5. Проверь актуальность используемых нормативов
    
    ВОЗВРАТИ JSON В ФОРМАТЕ:
    {
        "is_general_data_sheet": true/false,
        "required_sections": {
            "section_name": "present|missing|incomplete"
        },
        "ntd_compliance": {
            "overall_status": "соответствует|не соответствует|частично соответствует",
            "violations": [
                {
                    "requirement": "требование НТД",
                    "violation": "описание нарушения",
                    "severity": "critical|warning|info",
                    "ntd_reference": "ссылка на НТД"
                }
            ]
        },
        "data_completeness": "полная|частичная|неполная",
        "normative_actualization": "актуально|требует обновления",
        "recommendations": "рекомендации по исправлению"
    }
    """
    
    response = await self.send_llm_request(general_data_prompt.format(page_content=page_content))
    return json.loads(response)
```

## 📋 **5. Анализ остальных листов документа**

### **5.1 Требуемые проверки:**

#### **Комплексный анализ:**
- **Соответствие НТД** - проверка всех листов
- **Техническая корректность** - проверка расчетов и решений
- **Согласованность** - соответствие между листами
- **Полнота информации** - отсутствие пропусков

#### **Рекомендуемые изменения:**

```python
def analyze_remaining_sheets(self, page_content: str, sheet_type: str) -> Dict[str, Any]:
    """Анализ остальных листов документа на соответствие НТД"""
    
    sheet_analysis_prompt = """
    Ты - эксперт по проверке проектной документации. Проанализируй лист на соответствие НТД:
    
    ТИП ЛИСТА: {sheet_type}
    ДОКУМЕНТ ДЛЯ АНАЛИЗА:
    {page_content}
    
    ИНСТРУКЦИИ:
    1. Определи тип листа (чертеж, спецификация, расчет и т.д.)
    2. Проверь соответствие требованиям НТД для данного типа
    3. Выяви технические ошибки и нарушения
    4. Проверь согласованность с другими листами
    5. Оцените полноту и качество информации
    
    ВОЗВРАТИ JSON В ФОРМАТЕ:
    {
        "sheet_type": "тип листа",
        "ntd_compliance": {
            "overall_status": "соответствует|не соответствует|частично соответствует",
            "compliance_percentage": 0-100,
            "violations": [
                {
                    "ntd_requirement": "требование НТД",
                    "violation_description": "описание нарушения",
                    "severity": "critical|warning|info",
                    "ntd_reference": "ссылка на НТД",
                    "recommendation": "рекомендация по исправлению"
                }
            ]
        },
        "technical_errors": [...],
        "consistency_issues": [...],
        "completeness_assessment": "полная|частичная|неполная",
        "quality_score": 0-100,
        "summary": "общий вывод по листу"
    }
    """
    
    response = await self.send_llm_request(sheet_analysis_prompt.format(
        sheet_type=sheet_type, 
        page_content=page_content
    ))
    return json.loads(response)
```

## 🔧 **6. Архитектурные изменения**

### **6.1 Новая структура процесса анализа:**

```python
async def perform_comprehensive_document_analysis(self, document_id: int, document_content: str) -> Dict[str, Any]:
    """Комплексный анализ документа с новыми требованиями"""
    
    # Шаг 1: Анализ первой страницы
    first_page_info = await self.extract_first_page_info(pages[0]['content'])
    
    # Шаг 2: Анализ подписей и исполнителей
    signature_analysis = await self.analyze_executors_and_signatures(document_content)
    
    # Шаг 3: Проверка орфографии
    spelling_analysis = await self.check_spelling_and_typos(document_content)
    
    # Шаг 4: Анализ листа "Общие данные"
    general_data_analysis = None
    for page in pages:
        if await self.is_general_data_sheet(page['content']):
            general_data_analysis = await self.analyze_general_data_sheet(page['content'])
            break
    
    # Шаг 5: Анализ остальных листов
    remaining_sheets_analysis = []
    for page in pages[1:]:  # Пропускаем первую страницу
        if not await self.is_general_data_sheet(page['content']):
            sheet_type = await self.determine_sheet_type(page['content'])
            sheet_analysis = await self.analyze_remaining_sheets(page['content'], sheet_type)
            remaining_sheets_analysis.append(sheet_analysis)
    
    # Шаг 6: Объединение результатов
    comprehensive_result = {
        "first_page_info": first_page_info,
        "signature_analysis": signature_analysis,
        "spelling_analysis": spelling_analysis,
        "general_data_analysis": general_data_analysis,
        "remaining_sheets_analysis": remaining_sheets_analysis,
        "overall_assessment": await self.generate_overall_assessment(
            first_page_info, signature_analysis, spelling_analysis, 
            general_data_analysis, remaining_sheets_analysis
        )
    }
    
    return comprehensive_result
```

### **6.2 Новые таблицы в базе данных:**

```sql
-- Таблица для информации о проекте
CREATE TABLE project_info (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES checkable_documents(id),
    project_name VARCHAR(500),
    design_stage VARCHAR(100),
    document_mark VARCHAR(200),
    document_code VARCHAR(100),
    confidence FLOAT,
    extraction_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица для анализа подписей
CREATE TABLE signature_analysis (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES checkable_documents(id),
    executors_found BOOLEAN,
    executors_list JSONB,
    signatures_found BOOLEAN,
    signers JSONB,
    ukep_present BOOLEAN,
    ukep_details TEXT,
    compliance_status VARCHAR(50),
    missing_signatures JSONB,
    recommendations TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица для проверки орфографии
CREATE TABLE spelling_analysis (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES checkable_documents(id),
    spelling_errors JSONB,
    typos JSONB,
    punctuation_errors JSONB,
    technical_term_errors JSONB,
    total_errors INTEGER,
    error_summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица для анализа листа "Общие данные"
CREATE TABLE general_data_analysis (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES checkable_documents(id),
    is_general_data_sheet BOOLEAN,
    required_sections JSONB,
    ntd_compliance JSONB,
    data_completeness VARCHAR(50),
    normative_actualization VARCHAR(50),
    recommendations TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица для анализа остальных листов
CREATE TABLE sheet_analysis (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES checkable_documents(id),
    page_number INTEGER,
    sheet_type VARCHAR(100),
    ntd_compliance JSONB,
    technical_errors JSONB,
    consistency_issues JSONB,
    completeness_assessment VARCHAR(50),
    quality_score INTEGER,
    summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🎯 **7. Обновление промптов**

### **7.1 Новый основной промпт:**

```python
def get_enhanced_normcontrol_prompt(self) -> str:
    """Улучшенный промпт для комплексного анализа документа"""
    
    return """
    Ты - эксперт по комплексному анализу проектной документации. Твоя задача - провести полную проверку документа по всем аспектам.
    
    ИНСТРУКЦИЯ ДЛЯ КОМПЛЕКСНОГО АНАЛИЗА:
    
    1. АНАЛИЗ ПЕРВОЙ СТРАНИЦЫ:
    - Извлеки название проекта
    - Определи стадию проектирования (Проектная/Рабочая документация)
    - Найди марку комплекта (АР, КР, ТР и т.д.)
    - Извлеки шифр документа
    
    2. ПРОВЕРКА ПОДПИСЕЙ И ИСПОЛНИТЕЛЕЙ:
    - Найди "Список исполнителей"
    - Определи подписантов документа
    - Проверь наличие УКЭП
    - Оцени соответствие требованиям по подписям
    
    3. ПРОВЕРКА ОРФОГРАФИИ:
    - Выяви орфографические ошибки
    - Найди опечатки и описки
    - Проверь пунктуацию
    - Проверь корректность технических терминов
    
    4. АНАЛИЗ ЛИСТА "ОБЩИЕ ДАННЫЕ":
    - Определи является ли это листом "Общие данные"
    - Проверь наличие всех обязательных разделов
    - Проверь соответствие НТД
    - Оцени актуальность нормативов
    
    5. АНАЛИЗ ОСТАЛЬНЫХ ЛИСТОВ:
    - Определи тип каждого листа
    - Проверь соответствие НТД для данного типа
    - Выяви технические ошибки
    - Проверь согласованность между листами
    
    ВОЗВРАТИ ДЕТАЛЬНЫЙ JSON ОТЧЕТ СО ВСЕМИ НАЙДЕННЫМИ ПРОБЛЕМАМИ И РЕКОМЕНДАЦИЯМИ.
    """
```

## 🚀 **8. План внедрения**

### **8.1 Этапы реализации:**

#### **Этап 1: Подготовка (1-2 дня)**
- Создание новых таблиц в базе данных
- Разработка новых функций анализа
- Обновление промптов

#### **Этап 2: Реализация (3-5 дней)**
- Интеграция новых функций в основной процесс
- Тестирование на реальных документах
- Отладка и оптимизация

#### **Этап 3: Внедрение (1-2 дня)**
- Обновление фронтенда для отображения новых результатов
- Создание новых отчетов
- Обучение пользователей

### **8.2 Приоритеты разработки:**

1. **Высокий приоритет:**
   - Анализ первой страницы
   - Проверка орфографии
   - Анализ листа "Общие данные"

2. **Средний приоритет:**
   - Анализ подписей и УКЭП
   - Анализ остальных листов

3. **Низкий приоритет:**
   - Дополнительные улучшения интерфейса
   - Расширенная аналитика

## ✅ **9. Ожидаемые результаты**

### **9.1 Улучшения качества анализа:**
- ✅ **Полнота проверки** - охват всех аспектов документа
- ✅ **Точность результатов** - специализированные промпты для каждого типа анализа
- ✅ **Структурированность** - четкая организация результатов
- ✅ **Практичность** - конкретные рекомендации по исправлению

### **9.2 Преимущества для пользователей:**
- ✅ **Экономия времени** - автоматическая проверка всех аспектов
- ✅ **Повышение качества** - выявление всех типов ошибок
- ✅ **Соответствие стандартам** - проверка по актуальным НТД
- ✅ **Детальная отчетность** - полная информация о найденных проблемах

**Эти рекомендации позволят создать комплексную систему анализа проектной документации, которая будет соответствовать всем современным требованиям и стандартам.**
