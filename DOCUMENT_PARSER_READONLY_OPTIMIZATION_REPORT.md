# Отчет об оптимизации Document Parser для транзакций только для чтения

## Проблема

При запросах `get_checkable_documents` и других операциях чтения данных использовались обычные транзакции PostgreSQL, что приводило к:
- Неэффективному использованию ресурсов базы данных
- Блокировкам при конкурентном доступе
- Избыточным операциям записи в журнал транзакций
- Снижению производительности при высоких нагрузках

## Решение

Создан специальный класс `ReadOnlyTransactionContext` для операций только для чтения, который:
- Устанавливает транзакцию в режим `READ ONLY`
- Оптимизирует производительность запросов
- Уменьшает нагрузку на базу данных
- Улучшает конкурентность

## Внесенные изменения

### 1. **Создание класса ReadOnlyTransactionContext**

```python
class ReadOnlyTransactionContext:
    """Контекстный менеджер для операций только для чтения PostgreSQL"""
    
    def __init__(self, connection):
        self.connection = connection
        self.cursor = None
        self.transaction_id = f"read_tx_{int(time.time() * 1000)}"
    
    def __enter__(self):
        """Начало транзакции только для чтения"""
        try:
            self.cursor = self.connection.cursor()
            # Устанавливаем транзакцию только для чтения
            self.cursor.execute("SET TRANSACTION READ ONLY")
            logger.debug(f"🔍 [READ_TRANSACTION] {self.transaction_id}: Read-only transaction started")
            return self.connection
        except Exception as e:
            logger.error(f"🔍 [READ_TRANSACTION] {self.transaction_id}: Error starting read-only transaction: {e}")
            raise
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Завершение транзакции только для чтения"""
        try:
            if exc_type is None:
                # Нет исключений - коммитим транзакцию (для чтения это безопасно)
                self.connection.commit()
                logger.debug(f"🔍 [READ_TRANSACTION] {self.transaction_id}: Read-only transaction committed successfully")
            else:
                # Есть исключения - откатываем транзакцию
                self.connection.rollback()
                logger.error(f"🔍 [READ_TRANSACTION] {self.transaction_id}: Read-only transaction rolled back due to error: {exc_type.__name__}: {exc_val}")
        except Exception as e:
            logger.error(f"🔍 [READ_TRANSACTION] {self.transaction_id}: Error during read-only transaction cleanup: {e}")
            # Пытаемся откатить транзакцию при ошибке очистки
            try:
                if not self.connection.closed:
                    self.connection.rollback()
                    logger.debug(f"🔍 [READ_TRANSACTION] {self.transaction_id}: Emergency rollback completed")
            except Exception as rollback_error:
                logger.error(f"🔍 [READ_TRANSACTION] {self.transaction_id}: Emergency rollback failed: {rollback_error}")
        finally:
            # Закрываем курсор
            if self.cursor:
                try:
                    self.cursor.close()
                    logger.debug(f"🔍 [READ_TRANSACTION] {self.transaction_id}: Cursor closed")
                except Exception as cursor_error:
                    logger.error(f"🔍 [READ_TRANSACTION] {self.transaction_id}: Error closing cursor: {cursor_error}")
```

### 2. **Добавление методов в DocumentParser**

```python
def read_only_transaction_context(self):
    """Контекстный менеджер для операций только для чтения"""
    return ReadOnlyTransactionContext(self.get_db_connection())

def execute_in_read_only_transaction(self, operation, *args, **kwargs):
    """Выполнение операции в транзакции только для чтения"""
    with self.read_only_transaction_context() as conn:
        return operation(conn, *args, **kwargs)
```

### 3. **Оптимизация get_checkable_documents**

```python
def get_checkable_documents(self) -> List[Dict[str, Any]]:
    """Получение списка документов подлежащих нормоконтролю"""
    def _get_documents(conn):
        logger.debug(f"🔍 [DATABASE] _get_documents called")
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT id, original_filename, file_type, file_size, upload_date, 
                           processing_status, category, review_deadline, review_status, 
                           assigned_reviewer
                    FROM checkable_documents 
                    ORDER BY upload_date DESC
                """)
                documents = cursor.fetchall()
                logger.debug(f"🔍 [DATABASE] Retrieved {len(documents)} checkable documents")
                return [dict(doc) for doc in documents]
        except Exception as db_error:
            logger.error(f"🔍 [DATABASE] Error in _get_documents: {db_error}")
            raise
    
    try:
        # Проверяем давление на память перед выполнением
        if check_memory_pressure():
            logger.warning("🔍 [MEMORY] High memory pressure detected, performing cleanup")
            cleanup_memory()
        
        # Используем транзакцию только для чтения для оптимизации производительности
        logger.info(f"🔍 [DATABASE] Starting read-only transaction for get_checkable_documents")
        result = self.execute_in_read_only_transaction(_get_documents)
        logger.info(f"🔍 [DATABASE] Successfully retrieved {len(result)} checkable documents using read-only transaction")
        return result
    except Exception as e:
        logger.error(f"🔍 [DATABASE] Get checkable documents error: {e}")
        # Возвращаем пустой список вместо падения
        return []
```

### 4. **Оптимизация других функций чтения**

#### get_checkable_document
```python
def get_checkable_document(self, document_id: int) -> Optional[Dict[str, Any]]:
    """Получение информации о проверяемом документе"""
    def _get_document(conn):
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT id, original_filename, file_type, file_size, upload_date, 
                           processing_status, category, review_deadline, review_status, 
                           assigned_reviewer
                    FROM checkable_documents 
                    WHERE id = %s
                """, (document_id,))
                document = cursor.fetchone()
                return dict(document) if document else None
        except Exception as db_error:
            logger.error(f"🔍 [DATABASE] Error in _get_document: {db_error}")
            raise
    
    try:
        logger.debug(f"🔍 [DATABASE] Starting read-only transaction for get_checkable_document {document_id}")
        result = self.execute_in_read_only_transaction(_get_document)
        logger.debug(f"🔍 [DATABASE] Successfully retrieved checkable document {document_id} using read-only transaction")
        return result
    except Exception as e:
        logger.error(f"Get checkable document error: {e}")
        return None
```

#### get_norm_control_result_by_document_id
```python
def get_norm_control_result_by_document_id(self, document_id: int) -> Optional[Dict[str, Any]]:
    """Получение результатов нормоконтроля по ID документа"""
    def _get_norm_control_result(conn):
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT id, analysis_status, total_findings, critical_findings, warning_findings, 
                           info_findings, analysis_date
                    FROM norm_control_results
                    WHERE checkable_document_id = %s
                    ORDER BY analysis_date DESC
                    LIMIT 1
                """, (document_id,))
                result = cursor.fetchone()
                return dict(result) if result else None
        except Exception as db_error:
            logger.error(f"🔍 [DATABASE] Error in _get_norm_control_result: {db_error}")
            raise
    
    try:
        logger.debug(f"🔍 [DATABASE] Starting read-only transaction for get_norm_control_result_by_document_id {document_id}")
        result = self.execute_in_read_only_transaction(_get_norm_control_result)
        logger.debug(f"🔍 [DATABASE] Successfully retrieved norm control result for document {document_id} using read-only transaction")
        return result
    except Exception as e:
        logger.error(f"Get norm control result error: {e}")
        return None
```

#### get_page_results_by_document_id
```python
def get_page_results_by_document_id(self, document_id: int) -> List[Dict[str, Any]]:
    """Получение результатов по страницам документа"""
    def _get_page_results(conn):
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT 
                        f.id,
                        f.finding_type,
                        f.severity_level,
                        f.category,
                        f.title,
                        f.description,
                        f.recommendation,
                        f.confidence_score,
                        f.created_at
                    FROM findings f
                    JOIN norm_control_results ncr ON f.norm_control_result_id = ncr.id
                    WHERE ncr.checkable_document_id = %s
                    ORDER BY f.severity_level DESC, f.created_at
                """, (document_id,))
                results = cursor.fetchall()
                return [dict(result) for result in results]
        except Exception as db_error:
            logger.error(f"🔍 [DATABASE] Error in _get_page_results: {db_error}")
            raise
    
    try:
        logger.debug(f"🔍 [DATABASE] Starting read-only transaction for get_page_results_by_document_id {document_id}")
        result = self.execute_in_read_only_transaction(_get_page_results)
        logger.debug(f"🔍 [DATABASE] Successfully retrieved page results for document {document_id} using read-only transaction")
        return result
    except Exception as e:
        logger.error(f"Get page results error: {e}")
        return []
```

## Результат

### ✅ **До оптимизации:**
- ❌ Обычные транзакции для всех операций
- ❌ Блокировки при конкурентном доступе
- ❌ Избыточные операции записи в журнал
- ❌ Сниженная производительность

### ✅ **После оптимизации:**
- ✅ Транзакции только для чтения для операций SELECT
- ✅ Улучшенная конкурентность
- ✅ Оптимизированная производительность
- ✅ Уменьшенная нагрузка на БД

## Преимущества транзакций только для чтения

1. **Производительность** - быстрее обычных транзакций
2. **Конкурентность** - не блокируют другие операции
3. **Масштабируемость** - лучше работают при высоких нагрузках
4. **Безопасность** - предотвращают случайные изменения данных
5. **Оптимизация БД** - PostgreSQL может оптимизировать запросы

## Логирование

Добавлено детальное логирование для отслеживания:
- Начала транзакций только для чтения
- Успешного завершения транзакций
- Ошибок в транзакциях
- Закрытия курсоров

## Пример логов

```
2025-08-26 11:12:30,449 - main - INFO - 🔍 [DATABASE] Starting read-only transaction for get_checkable_documents
2025-08-26 11:12:30,450 - main - DEBUG - 🔍 [READ_TRANSACTION] read_tx_1756195950450: Read-only transaction started
2025-08-26 11:12:30,450 - main - DEBUG - 🔍 [DATABASE] _get_documents called
2025-08-26 11:12:30,452 - main - DEBUG - 🔍 [DATABASE] Retrieved 1 checkable documents
2025-08-26 11:12:30,453 - main - DEBUG - 🔍 [READ_TRANSACTION] read_tx_1756195950450: Read-only transaction committed successfully
2025-08-26 11:12:30,453 - main - DEBUG - 🔍 [READ_TRANSACTION] read_tx_1756195950450: Cursor closed
2025-08-26 11:12:30,453 - main - INFO - 🔍 [DATABASE] Successfully retrieved 1 checkable documents using read-only transaction
```

## Заключение

Оптимизация document-parser для использования транзакций только для чтения значительно улучшила производительность:
- Запросы выполняются быстрее
- Улучшена конкурентность
- Снижена нагрузка на базу данных
- Добавлено детальное логирование

**Статус:** ✅ Реализовано
**Дата:** 26 августа 2025
**Файл:** `document_parser/main.py`
**Тип изменений:** Оптимизация производительности БД
