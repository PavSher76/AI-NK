# AI-NK Document Utils

Универсальный модуль для извлечения и обработки текста из документов различных форматов.

## Возможности

- **Поддержка форматов**: PDF, DOCX, DOC, TXT
- **Улучшенное извлечение текста**: Использует pdfminer для более точного извлечения из PDF
- **Очистка текста**: Автоматическая очистка и нормализация извлеченного текста
- **Иерархическое разделение**: Разделение текста на чанки с сохранением структуры
- **Обратная совместимость**: Функции для легкой миграции существующего кода

## Установка

```bash
pip install -r requirements.txt
```

## Быстрый старт

### Базовое использование

```python
from utils import parse_document

# Парсинг документа
result = parse_document("document.pdf")

if result["success"]:
    print(f"Извлеченный текст: {result['text']}")
    print(f"Количество страниц: {result['total_pages']}")
    print(f"Количество чанков: {len(result['chunks'])}")
else:
    print(f"Ошибка: {result['error']}")
```

### Парсинг из байтов

```python
from utils import parse_document_from_bytes

# Чтение файла в байты
with open("document.pdf", "rb") as f:
    content = f.read()

# Парсинг из байтов
result = parse_document_from_bytes(content, "document.pdf")
```

### Настройка параметров

```python
from utils import UniversalDocumentParser

# Создание парсера с настройками
parser = UniversalDocumentParser(
    prefer_pdfminer=True,      # Использовать pdfminer для PDF
    extract_tables=True,       # Извлекать таблицы из DOCX
    extract_headers=True,      # Извлекать заголовки отдельно
    create_hierarchical_chunks=True  # Создавать иерархические чанки
)

# Парсинг документа
result = parser.parse_document("document.docx")
```

## Структура модуля

```
utils/
├── __init__.py              # Основные экспорты
├── document_parser.py       # Универсальный парсер документов
├── pdf_utils.py            # Функции для работы с PDF
├── docx_utils.py           # Функции для работы с DOCX
├── text_processing.py      # Обработка и очистка текста
├── requirements.txt        # Зависимости
└── README.md              # Документация
```

## API Reference

### UniversalDocumentParser

Основной класс для парсинга документов.

#### Методы

- `parse_document(file_path: str) -> Dict[str, Any]` - Парсинг документа по пути
- `parse_document_from_bytes(file_content: bytes, filename: str) -> Dict[str, Any]` - Парсинг из байтов
- `get_supported_formats() -> List[str]` - Получение поддерживаемых форматов
- `get_text_statistics(text: str) -> Dict[str, Any]` - Статистика по тексту

### PDFTextExtractor

Класс для извлечения текста из PDF документов.

#### Методы

- `extract_text_from_file(file_path: str) -> Dict[str, Any]` - Извлечение из файла
- `extract_text_from_bytes(file_content: bytes) -> Dict[str, Any]` - Извлечение из байтов
- `create_chunks(text: str, chunk_size: int = 1000, overlap: int = 100) -> List[Dict[str, Any]]` - Создание чанков

### DOCXTextExtractor

Класс для извлечения текста из DOCX документов.

#### Методы

- `extract_text_from_file(file_path: str) -> Dict[str, Any]` - Извлечение из файла
- `extract_text_from_bytes(file_content: bytes) -> Dict[str, Any]` - Извлечение из байтов
- `create_chunks(text: str, chunk_size: int = 1000, overlap: int = 100) -> List[Dict[str, Any]]` - Создание чанков

### TextProcessor

Класс для обработки и очистки текста.

#### Методы

- `clean_text(text: str, preserve_structure: bool = True) -> str` - Очистка текста
- `hierarchical_chunking(text: str) -> List[TextChunk]` - Иерархическое разделение
- `create_fixed_size_chunks(text: str, chunk_size: int = 1000, overlap: int = 100) -> List[TextChunk]` - Чанки фиксированного размера
- `get_text_statistics(text: str) -> Dict[str, Any]` - Статистика по тексту

## Формат результата

Все функции парсинга возвращают словарь со следующей структурой:

```python
{
    "success": bool,           # Успешность операции
    "text": str,              # Извлеченный текст
    "pages": List[Dict],      # Страницы (для PDF)
    "paragraphs": List[Dict], # Параграфы (для DOCX)
    "chunks": List[Dict],     # Чанки текста
    "method": str,            # Метод извлечения
    "metadata": Dict,         # Метаданные
    "file_name": str,         # Имя файла
    "file_extension": str,    # Расширение файла
    "file_size": int,         # Размер файла
    "error": str              # Ошибка (если есть)
}
```

## Обратная совместимость

Модуль предоставляет функции для обратной совместимости с существующим кодом:

```python
# Старые функции (рекомендуется заменить на новые)
from utils import (
    extract_text_from_pdf_file,
    extract_text_from_docx_file,
    clean_text,
    hierarchical_text_chunking
)
```

## Примеры использования

### Обработка PDF с улучшенным извлечением

```python
from utils import PDFTextExtractor

extractor = PDFTextExtractor(prefer_pdfminer=True)
result = extractor.extract_text_from_file("document.pdf")

print(f"Метод извлечения: {result['method']}")
print(f"Количество страниц: {result['total_pages']}")
print(f"Точность извлечения: {result['metadata']['avg_chars_per_page']} символов на страницу")
```

### Обработка DOCX с таблицами и заголовками

```python
from utils import DOCXTextExtractor

extractor = DOCXTextExtractor(extract_tables=True, extract_headers=True)
result = extractor.extract_text_from_file("document.docx")

print(f"Параграфов: {result['metadata']['total_paragraphs']}")
print(f"Заголовков: {result['metadata']['total_headers']}")
print(f"Таблиц: {result['metadata']['total_tables']}")
```

### Иерархическое разделение текста

```python
from utils import TextProcessor

processor = TextProcessor()
chunks = processor.hierarchical_chunking(text)

for chunk in chunks:
    print(f"Чанк {chunk.chunk_id}: {chunk.content[:50]}...")
    print(f"Раздел: {chunk.hierarchy['section_title']}")
    print(f"Абзац: {chunk.hierarchy['paragraph_number']}")
    print(f"Предложение: {chunk.hierarchy['sentence_number']}")
```

## Требования

- Python 3.7+
- PyPDF2>=3.0.0
- pdfminer.six>=20221105
- python-docx>=0.8.11

## Лицензия

Этот модуль является частью проекта AI-NK и распространяется под той же лицензией.
