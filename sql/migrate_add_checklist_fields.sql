-- Миграция для добавления полей чек-листа в таблицу norm_control_results

-- Добавляем поле compliance_score (процент соответствия)
ALTER TABLE norm_control_results 
ADD COLUMN IF NOT EXISTS compliance_score FLOAT DEFAULT 0.0;

-- Добавляем поле recommendations (общие рекомендации)
ALTER TABLE norm_control_results 
ADD COLUMN IF NOT EXISTS recommendations TEXT;

-- Добавляем поле checklist_results (результаты чек-листа по разделам)
ALTER TABLE norm_control_results 
ADD COLUMN IF NOT EXISTS checklist_results JSONB;

-- Добавляем поле overall_status если его нет
ALTER TABLE norm_control_results 
ADD COLUMN IF NOT EXISTS overall_status VARCHAR(50) DEFAULT 'uncertain';

-- Добавляем поле confidence если его нет
ALTER TABLE norm_control_results 
ADD COLUMN IF NOT EXISTS confidence FLOAT DEFAULT 0.0;

-- Добавляем поле findings_details если его нет
ALTER TABLE norm_control_results 
ADD COLUMN IF NOT EXISTS findings_details JSONB;

-- Добавляем поле summary если его нет
ALTER TABLE norm_control_results 
ADD COLUMN IF NOT EXISTS summary TEXT;

-- Обновляем комментарии к таблице
COMMENT ON COLUMN norm_control_results.compliance_score IS 'Процент соответствия документа требованиям (0-100)';
COMMENT ON COLUMN norm_control_results.recommendations IS 'Общие рекомендации по улучшению документации';
COMMENT ON COLUMN norm_control_results.checklist_results IS 'Результаты проверки по разделам чек-листа';
COMMENT ON COLUMN norm_control_results.overall_status IS 'Общий статус проверки: pass, fail, uncertain';
COMMENT ON COLUMN norm_control_results.confidence IS 'Уверенность в результатах проверки (0.0-1.0)';
COMMENT ON COLUMN norm_control_results.findings_details IS 'Детали найденных нарушений в формате JSON';
COMMENT ON COLUMN norm_control_results.summary IS 'Общий вывод по проверке';
