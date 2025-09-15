-- Создание таблиц для системы объектов аналогов
-- Этот файл содержит SQL скрипты для создания всех необходимых таблиц

-- Таблица для хранения основных данных об объектах аналогах
CREATE TABLE IF NOT EXISTS analog_objects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL, -- Название объекта
    type VARCHAR(50) NOT NULL, -- Тип объекта (Жилой, Коммерческий, Промышленный, Социальный)
    region VARCHAR(100) NOT NULL, -- Регион
    city VARCHAR(100), -- Город
    year INTEGER, -- Год постройки
    status VARCHAR(50), -- Статус (Проектируется, Строится, Завершен, В эксплуатации)
    
    -- Технические характеристики
    area DECIMAL(12,2), -- Общая площадь в м²
    floors INTEGER, -- Количество этажей
    apartments INTEGER, -- Количество квартир (для жилых объектов)
    
    -- Информация о застройщике
    developer VARCHAR(255), -- Название компании-застройщика
    developer_contact VARCHAR(255), -- Контактное лицо
    developer_phone VARCHAR(50), -- Телефон
    developer_email VARCHAR(255), -- Email
    
    -- Дополнительная информация
    description TEXT, -- Описание объекта
    coordinates POINT, -- Географические координаты (широта, долгота)
    
    -- Метаданные
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100), -- Пользователь, создавший запись
    is_active BOOLEAN DEFAULT TRUE -- Активность записи
);

-- Таблица для хранения дополнительных характеристик объектов
CREATE TABLE IF NOT EXISTS analog_object_characteristics (
    id SERIAL PRIMARY KEY,
    object_id INTEGER REFERENCES analog_objects(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL, -- Название характеристики
    value TEXT NOT NULL, -- Значение характеристики
    unit VARCHAR(50), -- Единица измерения
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица для хранения файлов (изображения, документы)
CREATE TABLE IF NOT EXISTS analog_object_files (
    id SERIAL PRIMARY KEY,
    object_id INTEGER REFERENCES analog_objects(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL, -- Имя файла
    original_filename VARCHAR(255) NOT NULL, -- Оригинальное имя файла
    file_path VARCHAR(500) NOT NULL, -- Путь к файлу
    file_type VARCHAR(50) NOT NULL, -- Тип файла (image, document, etc.)
    file_size BIGINT NOT NULL, -- Размер файла в байтах
    mime_type VARCHAR(100), -- MIME тип
    description TEXT, -- Описание файла
    uploaded_by VARCHAR(100), -- Кто загрузил
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица для хранения связей между объектами (аналоги, похожие объекты)
CREATE TABLE IF NOT EXISTS analog_object_relations (
    id SERIAL PRIMARY KEY,
    source_object_id INTEGER REFERENCES analog_objects(id) ON DELETE CASCADE,
    target_object_id INTEGER REFERENCES analog_objects(id) ON DELETE CASCADE,
    relation_type VARCHAR(50) NOT NULL, -- Тип связи (similar, analog, reference)
    similarity_score DECIMAL(5,2), -- Оценка схожести (0-100)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    UNIQUE(source_object_id, target_object_id, relation_type)
);

-- Таблица для хранения поисковых запросов и результатов
CREATE TABLE IF NOT EXISTS analog_search_queries (
    id SERIAL PRIMARY KEY,
    query_text TEXT NOT NULL, -- Текст поискового запроса
    filters JSONB, -- Примененные фильтры в формате JSON
    results_count INTEGER, -- Количество найденных результатов
    search_type VARCHAR(50), -- Тип поиска (text, similarity, advanced)
    user_id VARCHAR(100), -- Пользователь, выполнивший поиск
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    execution_time_ms INTEGER -- Время выполнения поиска в миллисекундах
);

-- Таблица для хранения аналитических данных
CREATE TABLE IF NOT EXISTS analog_analytics (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(100) NOT NULL, -- Название метрики
    metric_value DECIMAL(15,2) NOT NULL, -- Значение метрики
    metric_type VARCHAR(50) NOT NULL, -- Тип метрики (count, sum, avg, etc.)
    dimension_name VARCHAR(100), -- Название измерения (region, type, year, etc.)
    dimension_value VARCHAR(255), -- Значение измерения
    period_start DATE, -- Начало периода
    period_end DATE, -- Конец периода
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица для хранения импортов данных
CREATE TABLE IF NOT EXISTS analog_imports (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL, -- Имя файла
    file_path VARCHAR(500) NOT NULL, -- Путь к файлу
    file_size BIGINT NOT NULL, -- Размер файла
    import_type VARCHAR(50) NOT NULL, -- Тип импорта (csv, excel, manual)
    records_total INTEGER, -- Общее количество записей
    records_processed INTEGER DEFAULT 0, -- Обработано записей
    records_success INTEGER DEFAULT 0, -- Успешно обработано
    records_failed INTEGER DEFAULT 0, -- Ошибок
    status VARCHAR(50) DEFAULT 'pending', -- Статус (pending, processing, completed, failed)
    error_message TEXT, -- Сообщение об ошибке
    imported_by VARCHAR(100), -- Кто импортировал
    started_at TIMESTAMP, -- Время начала импорта
    completed_at TIMESTAMP, -- Время завершения импорта
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица для хранения логов действий пользователей
CREATE TABLE IF NOT EXISTS analog_activity_log (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL, -- ID пользователя
    action VARCHAR(100) NOT NULL, -- Действие (create, update, delete, view, search)
    object_type VARCHAR(50), -- Тип объекта (analog_object, file, etc.)
    object_id INTEGER, -- ID объекта
    details JSONB, -- Дополнительные детали в формате JSON
    ip_address INET, -- IP адрес пользователя
    user_agent TEXT, -- User Agent браузера
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Создание индексов для оптимизации поиска
CREATE INDEX IF NOT EXISTS idx_analog_objects_type ON analog_objects(type);
CREATE INDEX IF NOT EXISTS idx_analog_objects_region ON analog_objects(region);
CREATE INDEX IF NOT EXISTS idx_analog_objects_city ON analog_objects(city);
CREATE INDEX IF NOT EXISTS idx_analog_objects_year ON analog_objects(year);
CREATE INDEX IF NOT EXISTS idx_analog_objects_status ON analog_objects(status);
CREATE INDEX IF NOT EXISTS idx_analog_objects_developer ON analog_objects(developer);
CREATE INDEX IF NOT EXISTS idx_analog_objects_created_at ON analog_objects(created_at);
CREATE INDEX IF NOT EXISTS idx_analog_objects_is_active ON analog_objects(is_active);

-- Индекс для полнотекстового поиска
CREATE INDEX IF NOT EXISTS idx_analog_objects_search ON analog_objects USING gin(
    to_tsvector('russian', name || ' ' || COALESCE(description, '') || ' ' || COALESCE(developer, ''))
);

-- Индексы для связанных таблиц
CREATE INDEX IF NOT EXISTS idx_analog_object_characteristics_object_id ON analog_object_characteristics(object_id);
CREATE INDEX IF NOT EXISTS idx_analog_object_files_object_id ON analog_object_files(object_id);
CREATE INDEX IF NOT EXISTS idx_analog_object_files_file_type ON analog_object_files(file_type);
CREATE INDEX IF NOT EXISTS idx_analog_object_relations_source ON analog_object_relations(source_object_id);
CREATE INDEX IF NOT EXISTS idx_analog_object_relations_target ON analog_object_relations(target_object_id);
CREATE INDEX IF NOT EXISTS idx_analog_search_queries_created_at ON analog_search_queries(created_at);
CREATE INDEX IF NOT EXISTS idx_analog_analytics_metric_name ON analog_analytics(metric_name);
CREATE INDEX IF NOT EXISTS idx_analog_analytics_period ON analog_analytics(period_start, period_end);
CREATE INDEX IF NOT EXISTS idx_analog_activity_log_user_id ON analog_activity_log(user_id);
CREATE INDEX IF NOT EXISTS idx_analog_activity_log_created_at ON analog_activity_log(created_at);

-- Создание триггеров для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_analog_objects_updated_at 
    BEFORE UPDATE ON analog_objects 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Создание представлений для удобства работы
CREATE OR REPLACE VIEW analog_objects_with_stats AS
SELECT 
    ao.*,
    COUNT(DISTINCT aoc.id) as characteristics_count,
    COUNT(DISTINCT aof.id) as files_count,
    COUNT(DISTINCT aor.id) as relations_count
FROM analog_objects ao
LEFT JOIN analog_object_characteristics aoc ON ao.id = aoc.object_id
LEFT JOIN analog_object_files aof ON ao.id = aof.object_id
LEFT JOIN analog_object_relations aor ON ao.id = aor.source_object_id
WHERE ao.is_active = TRUE
GROUP BY ao.id;

-- Представление для аналитики по типам объектов
CREATE OR REPLACE VIEW analog_objects_by_type AS
SELECT 
    type,
    COUNT(*) as count,
    AVG(area) as avg_area,
    AVG(floors) as avg_floors,
    AVG(apartments) as avg_apartments,
    MIN(year) as min_year,
    MAX(year) as max_year
FROM analog_objects
WHERE is_active = TRUE
GROUP BY type;

-- Представление для аналитики по регионам
CREATE OR REPLACE VIEW analog_objects_by_region AS
SELECT 
    region,
    COUNT(*) as count,
    AVG(area) as avg_area,
    AVG(floors) as avg_floors,
    MIN(year) as min_year,
    MAX(year) as max_year
FROM analog_objects
WHERE is_active = TRUE
GROUP BY region;

-- Представление для аналитики по годам
CREATE OR REPLACE VIEW analog_objects_by_year AS
SELECT 
    year,
    COUNT(*) as count,
    AVG(area) as avg_area,
    AVG(floors) as avg_floors,
    AVG(apartments) as avg_apartments
FROM analog_objects
WHERE is_active = TRUE AND year IS NOT NULL
GROUP BY year
ORDER BY year DESC;

-- Вставка начальных данных для тестирования
INSERT INTO analog_objects (name, type, region, city, year, status, area, floors, apartments, developer, description, created_by) VALUES
('Жилой комплекс "Северный"', 'Жилой', 'Московская область', 'Химки', 2023, 'Завершен', 45000, 25, 320, 'ООО "Северстрой"', 'Многоэтажный жилой комплекс с развитой инфраструктурой', 'system'),
('Бизнес-центр "Деловой"', 'Коммерческий', 'Москва', 'Москва', 2022, 'В эксплуатации', 25000, 15, NULL, 'ООО "Деловые центры"', 'Современный бизнес-центр класса А', 'system'),
('Жилой дом "Солнечный"', 'Жилой', 'Санкт-Петербург', 'Санкт-Петербург', 2021, 'В эксплуатации', 32000, 18, 240, 'ООО "Солнечный дом"', 'Энергоэффективный жилой дом с современными технологиями', 'system'),
('Промышленный комплекс "Технопарк"', 'Промышленный', 'Московская область', 'Подольск', 2020, 'В эксплуатации', 150000, 3, NULL, 'ООО "Технопарк"', 'Современный промышленный комплекс', 'system'),
('Школа №1234', 'Социальный', 'Москва', 'Москва', 2023, 'Завершен', 8000, 4, NULL, 'ООО "Образование"', 'Современная школа с инновационными технологиями', 'system');

-- Добавление характеристик для тестовых объектов
INSERT INTO analog_object_characteristics (object_id, name, value, unit) VALUES
(1, 'Площадь застройки', '12000', 'м²'),
(1, 'Парковочные места', '400', 'шт'),
(1, 'Стоимость за м²', '85000', '₽'),
(2, 'Площадь застройки', '8000', 'м²'),
(2, 'Офисные помещения', '20000', 'м²'),
(2, 'Парковочные места', '150', 'шт'),
(3, 'Площадь застройки', '9000', 'м²'),
(3, 'Парковочные места', '300', 'шт'),
(3, 'Энергоэффективность', 'A+', 'класс'),
(4, 'Площадь застройки', '50000', 'м²'),
(4, 'Производственные площади', '120000', 'м²'),
(5, 'Площадь застройки', '2000', 'м²'),
(5, 'Количество классов', '30', 'шт'),
(5, 'Спортивный зал', '1', 'шт');

-- Комментарии к таблицам
COMMENT ON TABLE analog_objects IS 'Основная таблица объектов аналогов';
COMMENT ON TABLE analog_object_characteristics IS 'Дополнительные характеристики объектов';
COMMENT ON TABLE analog_object_files IS 'Файлы, прикрепленные к объектам';
COMMENT ON TABLE analog_object_relations IS 'Связи между объектами';
COMMENT ON TABLE analog_search_queries IS 'История поисковых запросов';
COMMENT ON TABLE analog_analytics IS 'Аналитические данные';
COMMENT ON TABLE analog_imports IS 'История импортов данных';
COMMENT ON TABLE analog_activity_log IS 'Лог действий пользователей';
