-- Инициализация базы данных нормативных документов
-- Поддержка pgvector для векторного поиска

-- Создание расширения pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Таблица нормативных документов
CREATE TABLE IF NOT EXISTS normative_documents (
    id SERIAL PRIMARY KEY,
    document_type VARCHAR(50) NOT NULL, -- ГОСТ, СП, ТР ТС, корп-стандарт
    document_number VARCHAR(100) NOT NULL,
    document_name TEXT NOT NULL,
    version VARCHAR(20),
    publication_date DATE,
    effective_date DATE,
    status VARCHAR(50) DEFAULT 'active', -- active, deprecated, draft
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица фрагментов нормативных документов
CREATE TABLE IF NOT EXISTS document_clauses (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES normative_documents(id) ON DELETE CASCADE,
    clause_id VARCHAR(100) NOT NULL, -- Уникальный идентификатор пункта
    clause_number VARCHAR(50), -- Номер пункта (например, "5.2.1")
    page_number INTEGER,
    section_title TEXT,
    clause_title TEXT,
    clause_text TEXT NOT NULL,
    clause_type VARCHAR(50), -- requirement, recommendation, note, example
    importance_level INTEGER DEFAULT 1, -- 1-5, где 5 - критически важно
    embedding vector(1536), -- Векторное представление текста
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица атрибутов и метаданных
CREATE TABLE IF NOT EXISTS clause_attributes (
    id SERIAL PRIMARY KEY,
    clause_id INTEGER REFERENCES document_clauses(id) ON DELETE CASCADE,
    attribute_name VARCHAR(100) NOT NULL,
    attribute_value TEXT,
    attribute_type VARCHAR(50), -- text, number, date, boolean, reference
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица связей между пунктами
CREATE TABLE IF NOT EXISTS clause_relations (
    id SERIAL PRIMARY KEY,
    source_clause_id INTEGER REFERENCES document_clauses(id) ON DELETE CASCADE,
    target_clause_id INTEGER REFERENCES document_clauses(id) ON DELETE CASCADE,
    relation_type VARCHAR(50) NOT NULL, -- references, contradicts, extends, replaces
    relation_strength FLOAT DEFAULT 1.0, -- 0.0-1.0
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица загруженных документов для анализа
CREATE TABLE IF NOT EXISTS uploaded_documents (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(20) NOT NULL, -- pdf, dwg, ifc, docx
    file_size BIGINT NOT NULL,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processing_status VARCHAR(50) DEFAULT 'pending', -- pending, processing, completed, failed
    processing_error TEXT,
    document_hash VARCHAR(64) UNIQUE, -- SHA-256 хеш для дедупликации
    category VARCHAR(50) DEFAULT 'other', -- gost, sp, snip, tr, corporate, other
    document_type VARCHAR(50) DEFAULT 'normative', -- normative, checkable
    token_count INTEGER DEFAULT 0 -- Количество токенов в документе
);

-- Таблица проверяемых документов
CREATE TABLE IF NOT EXISTS checkable_documents (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(20) NOT NULL, -- pdf, dwg, ifc, docx
    file_size BIGINT NOT NULL,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processing_status VARCHAR(50) DEFAULT 'pending', -- pending, processing, completed, failed
    processing_error TEXT,
    document_hash VARCHAR(64) UNIQUE, -- SHA-256 хеш для дедупликации
    category VARCHAR(50) DEFAULT 'other', -- gost, sp, snip, tr, corporate, other
    review_deadline TIMESTAMP NOT NULL, -- Дата автоматического удаления (upload_date + 2 дня)
    review_status VARCHAR(50) DEFAULT 'pending', -- pending, in_review, completed, rejected
    assigned_reviewer VARCHAR(100), -- Назначенный рецензент
    review_notes TEXT, -- Заметки рецензента
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица извлеченных элементов из документов
CREATE TABLE IF NOT EXISTS extracted_elements (
    id SERIAL PRIMARY KEY,
    uploaded_document_id INTEGER REFERENCES uploaded_documents(id) ON DELETE CASCADE,
    element_type VARCHAR(50) NOT NULL, -- text, table, image, stamp, attribute
    element_content TEXT,
    element_metadata JSONB, -- Дополнительные метаданные
    page_number INTEGER,
    bounding_box JSONB, -- Координаты элемента на странице
    confidence_score FLOAT DEFAULT 1.0, -- Уверенность в извлечении
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица извлеченных элементов из проверяемых документов
CREATE TABLE IF NOT EXISTS checkable_elements (
    id SERIAL PRIMARY KEY,
    checkable_document_id INTEGER REFERENCES checkable_documents(id) ON DELETE CASCADE,
    element_type VARCHAR(50) NOT NULL, -- text, table, image, stamp, attribute
    element_content TEXT,
    element_metadata JSONB, -- Дополнительные метаданные
    page_number INTEGER,
    bounding_box JSONB, -- Координаты элемента на странице
    confidence_score FLOAT DEFAULT 1.0, -- Уверенность в извлечении
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица результатов нормоконтроля
CREATE TABLE IF NOT EXISTS norm_control_results (
    id SERIAL PRIMARY KEY,
    uploaded_document_id INTEGER REFERENCES uploaded_documents(id) ON DELETE CASCADE,
    checkable_document_id INTEGER REFERENCES checkable_documents(id) ON DELETE CASCADE,
    analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    analysis_type VARCHAR(50) NOT NULL, -- full, quick, targeted
    model_used VARCHAR(100),
    total_findings INTEGER DEFAULT 0,
    critical_findings INTEGER DEFAULT 0,
    warning_findings INTEGER DEFAULT 0,
    info_findings INTEGER DEFAULT 0,
    analysis_status VARCHAR(50) DEFAULT 'completed',
    report_file_path VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица отчетов о проверке документов
CREATE TABLE IF NOT EXISTS review_reports (
    id SERIAL PRIMARY KEY,
    checkable_document_id INTEGER REFERENCES checkable_documents(id) ON DELETE CASCADE,
    norm_control_result_id INTEGER REFERENCES norm_control_results(id) ON DELETE CASCADE,
    report_number VARCHAR(50) UNIQUE, -- Уникальный номер отчета
    report_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewer_name VARCHAR(100),
    review_type VARCHAR(50) NOT NULL, -- automated, manual, combined
    overall_status VARCHAR(50) NOT NULL, -- approved, rejected, needs_revision
    compliance_score FLOAT DEFAULT 0.0, -- Процент соответствия (0-100)
    total_violations INTEGER DEFAULT 0,
    critical_violations INTEGER DEFAULT 0,
    major_violations INTEGER DEFAULT 0,
    minor_violations INTEGER DEFAULT 0,
    recommendations TEXT,
    conclusion TEXT,
    report_file_path VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица найденных проблем (findings)
CREATE TABLE IF NOT EXISTS findings (
    id SERIAL PRIMARY KEY,
    norm_control_result_id INTEGER REFERENCES norm_control_results(id) ON DELETE CASCADE,
    finding_type VARCHAR(50) NOT NULL, -- violation, warning, recommendation, info
    severity_level INTEGER NOT NULL, -- 1-5, где 5 - критически
    category VARCHAR(100) NOT NULL, -- formatting, content, compliance, technical
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    recommendation TEXT,
    related_clause_id INTEGER REFERENCES document_clauses(id),
    related_clause_text TEXT,
    element_reference JSONB, -- Ссылка на элемент в документе
    rule_applied VARCHAR(100), -- Название примененного правила
    confidence_score FLOAT DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Индексы для оптимизации поиска
CREATE INDEX IF NOT EXISTS idx_document_clauses_document_id ON document_clauses(document_id);
CREATE INDEX IF NOT EXISTS idx_document_clauses_clause_id ON document_clauses(clause_id);
CREATE INDEX IF NOT EXISTS idx_document_clauses_clause_number ON document_clauses(clause_number);
CREATE INDEX IF NOT EXISTS idx_document_clauses_embedding ON document_clauses USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_clause_attributes_clause_id ON clause_attributes(clause_id);
CREATE INDEX IF NOT EXISTS idx_clause_relations_source ON clause_relations(source_clause_id);
CREATE INDEX IF NOT EXISTS idx_clause_relations_target ON clause_relations(target_clause_id);

CREATE INDEX IF NOT EXISTS idx_uploaded_documents_status ON uploaded_documents(processing_status);
CREATE INDEX IF NOT EXISTS idx_uploaded_documents_hash ON uploaded_documents(document_hash);
CREATE INDEX IF NOT EXISTS idx_extracted_elements_document ON extracted_elements(uploaded_document_id);
CREATE INDEX IF NOT EXISTS idx_extracted_elements_type ON extracted_elements(element_type);
CREATE INDEX IF NOT EXISTS idx_checkable_elements_document ON checkable_elements(checkable_document_id);
CREATE INDEX IF NOT EXISTS idx_checkable_elements_type ON checkable_elements(element_type);

CREATE INDEX IF NOT EXISTS idx_norm_control_results_document ON norm_control_results(uploaded_document_id);
CREATE INDEX IF NOT EXISTS idx_norm_control_results_checkable ON norm_control_results(checkable_document_id);
CREATE INDEX IF NOT EXISTS idx_findings_result ON findings(norm_control_result_id);
CREATE INDEX IF NOT EXISTS idx_findings_type ON findings(finding_type);
CREATE INDEX IF NOT EXISTS idx_findings_severity ON findings(severity_level);

-- Индексы для проверяемых документов
CREATE INDEX IF NOT EXISTS idx_checkable_documents_status ON checkable_documents(processing_status);
CREATE INDEX IF NOT EXISTS idx_checkable_documents_hash ON checkable_documents(document_hash);
CREATE INDEX IF NOT EXISTS idx_checkable_documents_deadline ON checkable_documents(review_deadline);
CREATE INDEX IF NOT EXISTS idx_checkable_documents_review_status ON checkable_documents(review_status);

-- Индексы для отчетов о проверке
CREATE INDEX IF NOT EXISTS idx_review_reports_document ON review_reports(checkable_document_id);
CREATE INDEX IF NOT EXISTS idx_review_reports_result ON review_reports(norm_control_result_id);
CREATE INDEX IF NOT EXISTS idx_review_reports_status ON review_reports(overall_status);
CREATE INDEX IF NOT EXISTS idx_review_reports_date ON review_reports(report_date);

-- Триггер для обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_normative_documents_updated_at BEFORE UPDATE ON normative_documents FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_document_clauses_updated_at BEFORE UPDATE ON document_clauses FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_checkable_documents_updated_at BEFORE UPDATE ON checkable_documents FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_review_reports_updated_at BEFORE UPDATE ON review_reports FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_system_settings_updated_at BEFORE UPDATE ON system_settings FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Функция для автоматического удаления просроченных документов
CREATE OR REPLACE FUNCTION cleanup_expired_checkable_documents()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER := 0;
BEGIN
    -- Удаляем документы, у которых истек срок рассмотрения
    DELETE FROM checkable_documents 
    WHERE review_deadline < CURRENT_TIMESTAMP 
    AND review_status IN ('pending', 'in_review');
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Логируем удаление
    INSERT INTO system_logs (action, details, affected_rows) 
    VALUES ('cleanup_expired_documents', 
            'Удалено просроченных документов: ' || deleted_count, 
            deleted_count);
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Таблица для логирования системных операций
CREATE TABLE IF NOT EXISTS system_logs (
    id SERIAL PRIMARY KEY,
    action VARCHAR(100) NOT NULL,
    details TEXT,
    affected_rows INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица для настроек системы
CREATE TABLE IF NOT EXISTS system_settings (
    id SERIAL PRIMARY KEY,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT,
    setting_description TEXT,
    setting_type VARCHAR(50) DEFAULT 'text', -- text, number, boolean, json
    is_public BOOLEAN DEFAULT true, -- доступно ли настройка через API
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Индексы для настроек
CREATE INDEX IF NOT EXISTS idx_system_settings_key ON system_settings(setting_key);
CREATE INDEX IF NOT EXISTS idx_system_settings_public ON system_settings(is_public);

-- Представления для удобного доступа к данным
CREATE OR REPLACE VIEW document_clauses_with_metadata AS
SELECT 
    dc.*,
    nd.document_type,
    nd.document_number,
    nd.document_name,
    nd.version
FROM document_clauses dc
JOIN normative_documents nd ON dc.document_id = nd.id;

-- Представление для статистики нормоконтроля
CREATE OR REPLACE VIEW norm_control_statistics AS
SELECT 
    ud.original_filename,
    ud.file_type,
    ncr.analysis_date,
    ncr.total_findings,
    ncr.critical_findings,
    ncr.warning_findings,
    ncr.info_findings,
    CASE 
        WHEN ncr.critical_findings > 0 THEN 'critical'
        WHEN ncr.warning_findings > 0 THEN 'warning'
        WHEN ncr.info_findings > 0 THEN 'info'
        ELSE 'clean'
    END as overall_status
FROM norm_control_results ncr
JOIN uploaded_documents ud ON ncr.uploaded_document_id = ud.id;

-- Вставка тестовых данных
INSERT INTO normative_documents (document_type, document_number, document_name, version, publication_date, effective_date) VALUES
('ГОСТ', 'ГОСТ Р 21.1101-2013', 'Система проектной документации для строительства. Основные требования к проектной и рабочей документации', '2013', '2013-12-01', '2014-07-01'),
('СП', 'СП 48.13330.2019', 'Организация строительства. Актуализированная редакция СНиП 12-01-2004', '2019', '2019-12-27', '2020-06-28'),
('ТР ТС', 'ТР ТС 004/2011', 'О безопасности низковольтного оборудования', '2011', '2011-08-16', '2013-02-15');

-- Вставка тестовых пунктов
INSERT INTO document_clauses (document_id, clause_id, clause_number, page_number, clause_title, clause_text, clause_type, importance_level) VALUES
(1, 'gost_21.1101_5.1', '5.1', 15, 'Общие требования к оформлению', 'Все листы проектной документации должны быть оформлены в соответствии с требованиями настоящего стандарта.', 'requirement', 5),
(1, 'gost_21.1101_5.2', '5.2', 16, 'Основная надпись', 'Основная надпись должна содержать все необходимые реквизиты согласно приложению А.', 'requirement', 5),
(2, 'sp_48.13330_4.1', '4.1', 8, 'Организация строительного производства', 'Строительное производство должно быть организовано с учетом требований безопасности и охраны труда.', 'requirement', 4),
(3, 'tr_ts_004_3.1', '3.1', 5, 'Требования к маркировке', 'Низковольтное оборудование должно иметь четкую и долговечную маркировку.', 'requirement', 4);

-- Вставка начальных настроек системы
INSERT INTO system_settings (setting_key, setting_value, setting_description, setting_type) VALUES
('norm_control_checklist_message', 
 'Проведите проверку нормоконтроля с применением Чек-листа. Проверьте соответствие документа требованиям нормативных документов, правильность оформления, наличие всех необходимых разделов и соответствие стандартам проектирования.',
 'Сообщение для системы о проведении проверки нормоконтроля с применением Чек-листа',
 'text'),
('norm_control_auto_check', 
 'true',
 'Автоматическая проверка нормоконтроля при загрузке документов',
 'boolean'),
('norm_control_severity_levels', 
 '{"critical": "Критические нарушения", "warning": "Предупреждения", "info": "Информационные замечания"}',
 'Уровни серьезности нарушений нормоконтроля',
 'json'),
('document_retention_days', 
 '730',
 'Количество дней хранения документов (по умолчанию 2 года)',
 'number');
