-- Обновление схемы базы данных
-- Добавление недостающих колонок

-- Добавляем колонку document_type в uploaded_documents
ALTER TABLE uploaded_documents ADD COLUMN IF NOT EXISTS document_type VARCHAR(50) DEFAULT 'normative';

-- Проверяем, что все таблицы существуют
SELECT 'uploaded_documents' as table_name, COUNT(*) as column_count 
FROM information_schema.columns 
WHERE table_name = 'uploaded_documents'
UNION ALL
SELECT 'checkable_documents' as table_name, COUNT(*) as column_count 
FROM information_schema.columns 
WHERE table_name = 'checkable_documents'
UNION ALL
SELECT 'review_reports' as table_name, COUNT(*) as column_count 
FROM information_schema.columns 
WHERE table_name = 'review_reports';
