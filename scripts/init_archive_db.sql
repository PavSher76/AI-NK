-- Инициализация базы данных для сервиса архива технической документации
-- Выполнить после создания основных таблиц системы

-- Подключаемся к базе данных норм
\c norms_db;

-- Создаем таблицы архива документов
\i ../sql/create_archive_documents_table.sql

-- Создаем индексы для оптимизации
CREATE INDEX IF NOT EXISTS idx_archive_documents_project_code ON archive_documents(project_code);
CREATE INDEX IF NOT EXISTS idx_archive_documents_document_type ON archive_documents(document_type);
CREATE INDEX IF NOT EXISTS idx_archive_documents_status ON archive_documents(processing_status);
CREATE INDEX IF NOT EXISTS idx_archive_documents_upload_date ON archive_documents(upload_date);
CREATE INDEX IF NOT EXISTS idx_archive_documents_hash ON archive_documents(document_hash);

CREATE INDEX IF NOT EXISTS idx_archive_sections_document_id ON archive_document_sections(archive_document_id);
CREATE INDEX IF NOT EXISTS idx_archive_sections_section_number ON archive_document_sections(section_number);
CREATE INDEX IF NOT EXISTS idx_archive_sections_page_number ON archive_document_sections(page_number);

CREATE INDEX IF NOT EXISTS idx_archive_relations_source ON archive_document_relations(source_document_id);
CREATE INDEX IF NOT EXISTS idx_archive_relations_target ON archive_document_relations(target_document_id);
CREATE INDEX IF NOT EXISTS idx_archive_relations_type ON archive_document_relations(relation_type);

CREATE INDEX IF NOT EXISTS idx_archive_projects_code ON archive_projects(project_code);
CREATE INDEX IF NOT EXISTS idx_archive_projects_status ON archive_projects(status);

-- Создаем представления для удобства
CREATE OR REPLACE VIEW archive_projects_summary AS
SELECT 
    p.project_code,
    p.project_name,
    p.status as project_status,
    p.total_documents,
    p.total_sections,
    p.created_at as project_created,
    p.updated_at as project_updated,
    COUNT(d.id) as actual_documents,
    COALESCE(SUM(d.file_size), 0) as total_size,
    MAX(d.upload_date) as last_upload
FROM archive_projects p
LEFT JOIN archive_documents d ON p.project_code = d.project_code
GROUP BY p.project_code, p.project_name, p.status, p.total_documents, p.total_sections, p.created_at, p.updated_at;

CREATE OR REPLACE VIEW archive_documents_detailed AS
SELECT 
    d.id,
    d.project_code,
    d.document_type,
    d.document_number,
    d.document_name,
    d.original_filename,
    d.file_type,
    d.file_size,
    d.upload_date,
    d.processing_status,
    d.author,
    d.department,
    d.version,
    d.status,
    p.project_name,
    COUNT(s.id) as sections_count,
    COALESCE(SUM(s.importance_level), 0) as total_importance
FROM archive_documents d
LEFT JOIN archive_projects p ON d.project_code = p.project_code
LEFT JOIN archive_document_sections s ON d.id = s.archive_document_id
GROUP BY d.id, d.project_code, d.document_type, d.document_number, d.document_name, 
         d.original_filename, d.file_type, d.file_size, d.upload_date, d.processing_status,
         d.author, d.department, d.version, d.status, p.project_name;

-- Создаем функции для работы с архивом
CREATE OR REPLACE FUNCTION get_project_documents_count(project_code_param VARCHAR(100))
RETURNS INTEGER AS $$
BEGIN
    RETURN (
        SELECT COUNT(*) 
        FROM archive_documents 
        WHERE project_code = project_code_param
    );
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_project_total_size(project_code_param VARCHAR(100))
RETURNS BIGINT AS $$
BEGIN
    RETURN (
        SELECT COALESCE(SUM(file_size), 0) 
        FROM archive_documents 
        WHERE project_code = project_code_param
    );
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION cleanup_old_archives(days_old INTEGER DEFAULT 365)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    -- Удаляем старые архивы (по умолчанию старше года)
    DELETE FROM archive_documents 
    WHERE upload_date < NOW() - INTERVAL '1 day' * days_old
    AND status = 'archived';
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Обновляем статистику проектов
    UPDATE archive_projects 
    SET 
        total_documents = get_project_documents_count(project_code),
        total_sections = (
            SELECT COUNT(*) 
            FROM archive_document_sections s
            JOIN archive_documents d ON s.archive_document_id = d.id
            WHERE d.project_code = archive_projects.project_code
        ),
        updated_at = CURRENT_TIMESTAMP;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Создаем права доступа
GRANT SELECT, INSERT, UPDATE, DELETE ON archive_documents TO norms_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON archive_document_sections TO norms_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON archive_document_relations TO norms_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON archive_projects TO norms_user;

GRANT USAGE ON SEQUENCE archive_documents_id_seq TO norms_user;
GRANT USAGE ON SEQUENCE archive_document_sections_id_seq TO norms_user;
GRANT USAGE ON SEQUENCE archive_document_relations_id_seq TO norms_user;
GRANT USAGE ON SEQUENCE archive_projects_id_seq TO norms_user;

-- Создаем комментарии к таблицам
COMMENT ON TABLE archive_documents IS 'Архив технических документов с группировкой по ШИФР проекта';
COMMENT ON TABLE archive_document_sections IS 'Разделы документов для детального поиска';
COMMENT ON TABLE archive_document_relations IS 'Связи между документами в проекте';
COMMENT ON TABLE archive_projects IS 'Метаданные проектов';

COMMENT ON COLUMN archive_documents.project_code IS 'ШИФР проекта - основной ключ группировки';
COMMENT ON COLUMN archive_documents.document_type IS 'Тип документа: ПД, РД, ТЭО, чертеж, спецификация';
COMMENT ON COLUMN archive_documents.document_hash IS 'SHA-256 хеш для дедупликации';
COMMENT ON COLUMN archive_documents.processing_status IS 'Статус обработки: pending, processing, completed, failed';

-- Выводим информацию о созданных объектах
SELECT 'Archive database initialized successfully' as status;
SELECT COUNT(*) as tables_created FROM information_schema.tables 
WHERE table_schema = 'public' AND table_name LIKE 'archive_%';
