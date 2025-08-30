-- Таблица для хранения консультаций НТД
CREATE TABLE IF NOT EXISTS ntd_consultations (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    question TEXT NOT NULL,
    response TEXT NOT NULL,
    sources JSONB,
    confidence_score DECIMAL(3,2) DEFAULT 0.0,
    documents_used INTEGER DEFAULT 0,
    processing_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Индексы для оптимизации запросов
CREATE INDEX IF NOT EXISTS idx_ntd_consultations_user_id ON ntd_consultations(user_id);
CREATE INDEX IF NOT EXISTS idx_ntd_consultations_created_at ON ntd_consultations(created_at);
CREATE INDEX IF NOT EXISTS idx_ntd_consultations_confidence_score ON ntd_consultations(confidence_score);

-- Комментарии к таблице
COMMENT ON TABLE ntd_consultations IS 'Таблица для хранения консультаций по нормативным документам';
COMMENT ON COLUMN ntd_consultations.user_id IS 'ID пользователя, задавшего вопрос';
COMMENT ON COLUMN ntd_consultations.question IS 'Вопрос пользователя';
COMMENT ON COLUMN ntd_consultations.response IS 'Ответ ИИ';
COMMENT ON COLUMN ntd_consultations.sources IS 'Источники, использованные для ответа (JSON)';
COMMENT ON COLUMN ntd_consultations.confidence_score IS 'Уверенность в ответе (0.0-1.0)';
COMMENT ON COLUMN ntd_consultations.documents_used IS 'Количество документов, использованных для ответа';
COMMENT ON COLUMN ntd_consultations.processing_time_ms IS 'Время обработки запроса в миллисекундах';
COMMENT ON COLUMN ntd_consultations.created_at IS 'Дата и время создания записи';
COMMENT ON COLUMN ntd_consultations.updated_at IS 'Дата и время последнего обновления записи';

-- Триггер для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
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
    COUNT(*) as total_consultations,
    COUNT(DISTINCT user_id) as unique_users,
    AVG(confidence_score) as avg_confidence,
    AVG(processing_time_ms) as avg_processing_time,
    COUNT(*) FILTER (WHERE confidence_score >= 0.7) as high_confidence_consultations,
    COUNT(*) FILTER (WHERE confidence_score < 0.3) as low_confidence_consultations,
    MAX(created_at) as last_consultation,
    MIN(created_at) as first_consultation
FROM ntd_consultations;

-- Функция для получения статистики за период
CREATE OR REPLACE FUNCTION get_ntd_consultations_stats(
    days_back INTEGER DEFAULT 30
)
RETURNS TABLE (
    total_consultations BIGINT,
    unique_users BIGINT,
    avg_confidence DECIMAL(3,2),
    avg_processing_time DECIMAL(10,2),
    high_confidence_count BIGINT,
    low_confidence_count BIGINT,
    last_consultation TIMESTAMP WITH TIME ZONE,
    first_consultation TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::BIGINT as total_consultations,
        COUNT(DISTINCT user_id)::BIGINT as unique_users,
        AVG(confidence_score)::DECIMAL(3,2) as avg_confidence,
        AVG(processing_time_ms)::DECIMAL(10,2) as avg_processing_time,
        COUNT(*) FILTER (WHERE confidence_score >= 0.7)::BIGINT as high_confidence_count,
        COUNT(*) FILTER (WHERE confidence_score < 0.3)::BIGINT as low_confidence_count,
        MAX(created_at) as last_consultation,
        MIN(created_at) as first_consultation
    FROM ntd_consultations
    WHERE created_at >= NOW() - INTERVAL '1 day' * days_back;
END;
$$ LANGUAGE plpgsql;
