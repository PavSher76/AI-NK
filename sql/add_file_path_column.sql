-- Добавление колонки file_path в таблицу uploaded_documents
ALTER TABLE uploaded_documents ADD COLUMN IF NOT EXISTS file_path TEXT;
