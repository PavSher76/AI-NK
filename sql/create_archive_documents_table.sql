-- Создание таблицы для архива технической документации
-- Поддержка пакетной загрузки ПД, РД, ТЭО с группировкой по ШИФР проекта

-- Таблица архива документов
CREATE TABLE IF NOT EXISTS archive_documents (
    id SERIAL PRIMARY KEY,
    project_code VARCHAR(100) NOT NULL, -- ШИФР проекта (основной ключ группировки)
    document_type VARCHAR(50) NOT NULL, -- ПД, РД, ТЭО, чертеж, спецификация
    document_number VARCHAR(100), -- Номер документа
    document_name TEXT NOT NULL, -- Название документа
    original_filename VARCHAR(255) NOT NULL, -- Оригинальное имя файла
    file_type VARCHAR(20) NOT NULL, -- pdf, dwg, ifc, docx, xlsx
    file_size BIGINT NOT NULL,
    file_path VARCHAR(500), -- Путь к файлу в файловой системе
    document_hash VARCHAR(64) UNIQUE, -- SHA-256 хеш для дедупликации
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processing_status VARCHAR(50) DEFAULT 'pending', -- pending, processing, completed, failed
    processing_error TEXT,
    token_count INTEGER DEFAULT 0, -- Количество токенов в документе
    version VARCHAR(20) DEFAULT '1.0', -- Версия документа
    revision_date DATE, -- Дата пересмотра
    author VARCHAR(100), -- Автор документа
    department VARCHAR(100), -- Отдел/подразделение
    status VARCHAR(50) DEFAULT 'active', -- active, archived, deprecated
    metadata JSONB, -- Дополнительные метаданные
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица разделов документов в архиве
CREATE TABLE IF NOT EXISTS archive_document_sections (
    id SERIAL PRIMARY KEY,
    archive_document_id INTEGER REFERENCES archive_documents(id) ON DELETE CASCADE,
    section_number VARCHAR(50), -- Номер раздела (например, "1.1", "2.3.1")
    section_title TEXT, -- Заголовок раздела
    section_content TEXT NOT NULL, -- Содержимое раздела
    page_number INTEGER, -- Номер страницы
    section_type VARCHAR(50) DEFAULT 'text', -- text, table, image, drawing, formula
    importance_level INTEGER DEFAULT 1, -- 1-5, где 5 - критически важно
    embedding vector(1536), -- Векторное представление текста
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица связей между документами в проекте
CREATE TABLE IF NOT EXISTS archive_document_relations (
    id SERIAL PRIMARY KEY,
    source_document_id INTEGER REFERENCES archive_documents(id) ON DELETE CASCADE,
    target_document_id INTEGER REFERENCES archive_documents(id) ON DELETE CASCADE,
    relation_type VARCHAR(50) NOT NULL, -- references, depends_on, supersedes, related_to
    relation_description TEXT, -- Описание связи
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица метаданных проектов
CREATE TABLE IF NOT EXISTS archive_projects (
    id SERIAL PRIMARY KEY,
    project_code VARCHAR(100) UNIQUE NOT NULL, -- ШИФР проекта
    project_name TEXT NOT NULL, -- Название проекта
    project_description TEXT, -- Описание проекта
    project_manager VARCHAR(100), -- Руководитель проекта
    department VARCHAR(100), -- Отдел/подразделение
    start_date DATE, -- Дата начала проекта
    end_date DATE, -- Дата окончания проекта
    status VARCHAR(50) DEFAULT 'active', -- active, completed, suspended, cancelled
    total_documents INTEGER DEFAULT 0, -- Общее количество документов в проекте
    total_sections INTEGER DEFAULT 0, -- Общее количество разделов в проекте
    metadata JSONB, -- Дополнительные метаданные проекта
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Индексы для оптимизации запросов
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

-- Триггеры для автоматического обновления статистики проектов
CREATE OR REPLACE FUNCTION update_project_stats()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE archive_projects 
        SET total_documents = (
            SELECT COUNT(*) FROM archive_documents 
            WHERE project_code = NEW.project_code
        ),
        total_sections = (
            SELECT COUNT(*) FROM archive_document_sections ads
            JOIN archive_documents ad ON ads.archive_document_id = ad.id
            WHERE ad.project_code = NEW.project_code
        ),
        updated_at = CURRENT_TIMESTAMP
        WHERE project_code = NEW.project_code;
        
        -- Создаем запись проекта, если её нет
        INSERT INTO archive_projects (project_code, project_name, total_documents, total_sections)
        VALUES (NEW.project_code, COALESCE(NEW.document_name, 'Проект ' || NEW.project_code), 1, 0)
        ON CONFLICT (project_code) DO NOTHING;
        
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE archive_projects 
        SET total_documents = (
            SELECT COUNT(*) FROM archive_documents 
            WHERE project_code = OLD.project_code
        ),
        total_sections = (
            SELECT COUNT(*) FROM archive_document_sections ads
            JOIN archive_documents ad ON ads.archive_document_id = ad.id
            WHERE ad.project_code = OLD.project_code
        ),
        updated_at = CURRENT_TIMESTAMP
        WHERE project_code = OLD.project_code;
        
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_project_stats
    AFTER INSERT OR DELETE ON archive_documents
    FOR EACH ROW EXECUTE FUNCTION update_project_stats();

-- Триггер для обновления статистики разделов
CREATE OR REPLACE FUNCTION update_section_stats()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE archive_projects 
        SET total_sections = (
            SELECT COUNT(*) FROM archive_document_sections ads
            JOIN archive_documents ad ON ads.archive_document_id = ad.id
            WHERE ad.project_code = (
                SELECT project_code FROM archive_documents WHERE id = NEW.archive_document_id
            )
        ),
        updated_at = CURRENT_TIMESTAMP
        WHERE project_code = (
            SELECT project_code FROM archive_documents WHERE id = NEW.archive_document_id
        );
        
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE archive_projects 
        SET total_sections = (
            SELECT COUNT(*) FROM archive_document_sections ads
            JOIN archive_documents ad ON ads.archive_document_id = ad.id
            WHERE ad.project_code = (
                SELECT project_code FROM archive_documents WHERE id = OLD.archive_document_id
            )
        ),
        updated_at = CURRENT_TIMESTAMP
        WHERE project_code = (
            SELECT project_code FROM archive_documents WHERE id = OLD.archive_document_id
        );
        
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_section_stats
    AFTER INSERT OR DELETE ON archive_document_sections
    FOR EACH ROW EXECUTE FUNCTION update_section_stats();
