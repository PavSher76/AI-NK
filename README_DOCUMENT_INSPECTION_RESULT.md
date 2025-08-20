# DocumentInspectionResult - Структура данных проверяемого документа

## 📋 Обзор

`DocumentInspectionResult` - это основная структура данных для хранения результатов проверки документа в системе AI-NK. Она содержит полную информацию о документе, его страницах и выявленных отклонениях.

## 🏗️ Структура классов

### 1. DocumentInspectionResult

Основной класс для результата проверки документа.

#### Основная информация о документе
```python
document_id: int                    # ID документа
document_name: str                  # Наименование документа
document_type: str                  # pdf, docx, dwg, txt
document_engineering_stage: str     # ПД, РД, ТЭО
document_mark: str                  # Марка комплекта документации
document_number: str                # Номер комплекта документации
document_date: str                  # Дата комплекта документации
document_author: str                # РАЗРАБОТАЛ комплект документации
document_reviewer: str              # ПРОВЕРИЛ комплект документации
document_approver: str              # ГИП комплекта документации
document_status: str                # Статус комплекта документации
document_size: int                  # Размер файла в байтах
```

#### Информация о страницах
```python
document_pages: int                 # Количество страниц в документе
document_pages_vector: int          # Количество векторных страниц
document_pages_scanned: int         # Количество сканированных страниц
document_pages_unknown: int         # Количество неизвестных страниц
document_pages_total: int           # Общее количество страниц
document_pages_total_a4_sheets_equivalent: float  # Эквивалент листов А4
```

#### Статистика по страницам
```python
document_pages_with_violations: int # Количество страниц с отклонениями
document_pages_clean: int           # Количество страниц без отклонений
```

#### Общие показатели отклонений
```python
document_total_violations: int      # Общее количество выявленных отклонений
document_critical_violations: int   # Критические отклонения
document_major_violations: int      # Значительные отклонения
document_minor_violations: int      # Мелкие отклонения
document_info_violations: int       # Информационные замечания
```

#### Процентные показатели
```python
document_compliance_percentage: float  # Процент соответствия (0-100)
document_violations_per_page_avg: float  # Среднее отклонений на страницу
```

#### Устаревшие поля (для обратной совместимости)
```python
document_total_errors_count: int    # Общее количество ошибок
document_total_warnings_count: int  # Общее количество предупреждений
document_total_info_count: int      # Общее количество информационных сообщений
document_total_suggestions_count: int  # Общее количество предложений
document_total_corrections_count: int  # Общее количество исправлений
```

#### Результаты проверки
```python
document_pages_results: List[DocumentPageInspectionResult]  # Результаты проверки листов
```

### 2. DocumentPageInspectionResult

Класс для результата проверки отдельной страницы документа.

#### Основная информация о странице
```python
page_number: int                    # Номер страницы
page_type: str                      # vector, scanned, unknown
page_format: str                    # A0, A1, A2, A3, A4, A5, A6, A7, A8, A9, A10, B0-B10
page_width_mm: float                # Ширина страницы в мм
page_height_mm: float               # Высота страницы в мм
page_orientation: str               # portrait, landscape
page_a4_sheets_equivalent: float    # Эквивалент листов А4
```

#### Информация о тексте страницы
```python
page_text: str                      # Текст листа документа
page_text_confidence: float         # Уверенность в тексте (0-1)
page_text_method: str               # Метод извлечения текста
page_text_length: int               # Длина текста в символах
```

#### Результаты OCR (для сканированных страниц)
```python
page_ocr_confidence: float          # Уверенность OCR
page_ocr_method: str                # Метод OCR
page_ocr_all_results: List[Dict]    # Все результаты OCR
```

#### Показатели отклонений на странице
```python
page_violations_count: int          # Общее количество отклонений
page_critical_violations: int       # Критические отклонения
page_major_violations: int          # Значительные отклонения
page_minor_violations: int          # Мелкие отклонения
page_info_violations: int           # Информационные замечания
page_compliance_percentage: float   # Процент соответствия страницы
```

#### Детали отклонений
```python
page_violations_details: List[DocumentViolationDetail]  # Детали отклонений
```

### 3. DocumentViolationDetail

Класс для детальной информации об отклонении.

```python
violation_type: str                 # critical, major, minor, info
violation_category: str             # general_requirements, text_part, graphical_part, specifications, assembly_drawings, detail_drawings, schemes
violation_description: str          # Описание отклонения
violation_clause: str               # Пункт нормы (например: ГОСТ Р 21.1101-2013 п.5.2)
violation_severity: int             # Серьезность (1-5)
violation_recommendation: str       # Рекомендация по исправлению
violation_location: str             # Местоположение на странице
violation_confidence: float         # Уверенность в отклонении (0-1)
```

## 🔧 Использование

### Создание объекта результата
```python
result = DocumentInspectionResult()
result.document_id = 1
result.document_name = "A9.5.MTH.04"
result.document_type = "pdf"
# ... заполнение остальных полей
```

### Создание результата страницы
```python
page_result = DocumentPageInspectionResult()
page_result.page_number = 1
page_result.page_type = "vector"
page_result.page_text = "Содержимое страницы"
# ... заполнение остальных полей
```

### Создание детали отклонения
```python
violation = DocumentViolationDetail()
violation.violation_type = "critical"
violation.violation_category = "general_requirements"
violation.violation_description = "Отсутствует штамп документа"
# ... заполнение остальных полей
```

## 📊 API Endpoints

### Получение статистики форматов документа
```http
GET /checkable-documents/{document_id}/format-statistics
```

**Ответ:**
```json
{
  "status": "success",
  "statistics": {
    "total_pages": 16,
    "total_a4_sheets": 32.0,
    "formats": {
      "A4": 12,
      "A3": 4
    },
    "orientations": {
      "portrait": 14,
      "landscape": 2
    },
    "page_types": {
      "vector": 10,
      "scanned": 6,
      "unknown": 0
    },
    "pages": [
      {
        "page_number": 1,
        "format": "A4",
        "width_mm": 210.0,
        "height_mm": 297.0,
        "orientation": "portrait",
        "a4_sheets": 1.0
      }
    ]
  }
}
```

## 🔄 Миграция данных

При переходе на новую структуру данных:

1. **Обратная совместимость**: Старые поля сохранены для совместимости
2. **Постепенная миграция**: Новые поля заполняются по мере обработки документов
3. **Автоматическое преобразование**: Старые форматы данных автоматически конвертируются в новые

## 📈 Преимущества новой структуры

1. **Детальная информация**: Полная информация о каждой странице документа
2. **Статистика отклонений**: Структурированные данные о выявленных проблемах
3. **Форматная информация**: Автоматическое определение форматов страниц
4. **OCR поддержка**: Интеграция с технологиями распознавания текста
5. **Масштабируемость**: Легкое добавление новых типов данных

## 🚀 Будущие улучшения

- [ ] Добавление поддержки таблиц и изображений
- [ ] Интеграция с системами контроля версий
- [ ] Автоматическое определение штампов документов
- [ ] Расширенная аналитика отклонений
- [ ] Интеграция с внешними системами нормоконтроля
