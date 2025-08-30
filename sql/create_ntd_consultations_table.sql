-- Создание таблицы для хранения консультаций НТД
-- Используется для сбора статистики и аналитики

CREATE TABLE IF NOT EXISTS ntd_consultations (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    question TEXT NOT NULL,
    response TEXT NOT NULL,
    confidence_score DECIMAL(3,3) DEFAULT 0.0,
    documents_used INTEGER DEFAULT 0,
    processing_time DECIMAL(6,3) DEFAULT 0.0,
    context_length INTEGER DEFAULT 0,
    cached BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Индексы для оптимизации запросов
CREATE INDEX IF NOT EXISTS idx_ntd_consultations_user_id ON ntd_consultations(user_id);
CREATE INDEX IF NOT EXISTS idx_ntd_consultations_created_at ON ntd_consultations(created_at);
CREATE INDEX IF NOT EXISTS idx_ntd_consultations_confidence ON ntd_consultations(confidence_score);
CREATE INDEX IF NOT EXISTS idx_ntd_consultations_cached ON ntd_consultations(cached);

-- Комментарии к таблице
COMMENT ON TABLE ntd_consultations IS 'Таблица для хранения консультаций по нормативным документам';
COMMENT ON COLUMN ntd_consultations.id IS 'Уникальный идентификатор консультации';
COMMENT ON COLUMN ntd_consultations.user_id IS 'Идентификатор пользователя';
COMMENT ON COLUMN ntd_consultations.question IS 'Вопрос пользователя';
COMMENT ON COLUMN ntd_consultations.response IS 'Ответ ИИ';
COMMENT ON COLUMN ntd_consultations.confidence_score IS 'Уверенность в ответе (0-1)';
COMMENT ON COLUMN ntd_consultations.documents_used IS 'Количество использованных документов';
COMMENT ON COLUMN ntd_consultations.processing_time IS 'Время обработки запроса в секундах';
COMMENT ON COLUMN ntd_consultations.context_length IS 'Длина контекста в символах';
COMMENT ON COLUMN ntd_consultations.cached IS 'Флаг использования кэша';
COMMENT ON COLUMN ntd_consultations.created_at IS 'Дата и время создания записи';
COMMENT ON COLUMN ntd_consultations.updated_at IS 'Дата и время обновления записи';

-- Триггер для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_ntd_consultations_updated_at 
    BEFORE UPDATE ON ntd_consultations 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Представление для статистики консультаций
CREATE OR REPLACE VIEW ntd_consultations_stats AS
SELECT 
    DATE(created_at) as consultation_date,
    COUNT(*) as total_consultations,
    COUNT(DISTINCT user_id) as unique_users,
    AVG(confidence_score) as avg_confidence,
    AVG(processing_time) as avg_processing_time,
    AVG(documents_used) as avg_documents_used,
    AVG(context_length) as avg_context_length,
    COUNT(CASE WHEN cached = true THEN 1 END) as cached_consultations,
    COUNT(CASE WHEN cached = false THEN 1 END) as non_cached_consultations
FROM ntd_consultations
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(created_at)
ORDER BY consultation_date DESC;

-- Представление для топ пользователей
CREATE OR REPLACE VIEW ntd_consultations_top_users AS
SELECT 
    user_id,
    COUNT(*) as consultation_count,
    AVG(confidence_score) as avg_confidence,
    AVG(processing_time) as avg_processing_time,
    MAX(created_at) as last_consultation
FROM ntd_consultations
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY user_id
ORDER BY consultation_count DESC
LIMIT 20;

-- Представление для качества ответов
CREATE OR REPLACE VIEW ntd_consultations_quality AS
SELECT 
    CASE 
        WHEN confidence_score >= 0.8 THEN 'Высокое'
        WHEN confidence_score >= 0.6 THEN 'Среднее'
        WHEN confidence_score >= 0.4 THEN 'Низкое'
        ELSE 'Очень низкое'
    END as quality_level,
    COUNT(*) as consultation_count,
    AVG(processing_time) as avg_processing_time,
    AVG(documents_used) as avg_documents_used
FROM ntd_consultations
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY 
    CASE 
        WHEN confidence_score >= 0.8 THEN 'Высокое'
        WHEN confidence_score >= 0.6 THEN 'Среднее'
        WHEN confidence_score >= 0.4 THEN 'Низкое'
        ELSE 'Очень низкое'
    END
ORDER BY 
    CASE quality_level
        WHEN 'Высокое' THEN 1
        WHEN 'Среднее' THEN 2
        WHEN 'Низкое' THEN 3
        WHEN 'Очень низкое' THEN 4
    END;
