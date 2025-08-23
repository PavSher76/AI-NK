-- Настройка PostgreSQL для работы с Keycloak аутентификацией
-- Этот скрипт настраивает PostgreSQL для проверки JWT токенов от Keycloak

-- Создаем функцию для проверки JWT токенов
CREATE OR REPLACE FUNCTION verify_jwt_token(token text)
RETURNS json AS $$
DECLARE
    header json;
    payload json;
    signature text;
    expected_signature text;
    keycloak_url text := 'https://keycloak:8443';
    realm text := 'ai-nk';
BEGIN
    -- Разбираем JWT токен (упрощенная версия)
    -- В реальной реализации нужно добавить проверку подписи
    
    -- Извлекаем payload из токена
    payload := convert_from(decode(split_part(token, '.', 2), 'base64'), 'utf8')::json;
    
    -- Проверяем, что токен не истек
    IF (payload->>'exp')::bigint < extract(epoch from now()) THEN
        RAISE EXCEPTION 'Token expired';
    END IF;
    
    -- Проверяем issuer
    IF payload->>'iss' != keycloak_url || '/realms/' || realm THEN
        RAISE EXCEPTION 'Invalid issuer';
    END IF;
    
    -- Проверяем audience
    IF payload->>'aud' != 'postgresql-client' THEN
        RAISE EXCEPTION 'Invalid audience';
    END IF;
    
    RETURN payload;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Создаем функцию для получения пользователя из JWT токена
CREATE OR REPLACE FUNCTION get_user_from_jwt()
RETURNS text AS $$
DECLARE
    token text;
    payload json;
BEGIN
    -- Получаем токен из переменной окружения или заголовка
    token := current_setting('jwt.token', true);
    
    IF token IS NULL THEN
        RETURN NULL;
    END IF;
    
    -- Проверяем токен
    payload := verify_jwt_token(token);
    
    -- Возвращаем username из токена
    RETURN payload->>'preferred_username';
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Создаем функцию для проверки ролей пользователя
CREATE OR REPLACE FUNCTION check_user_role(required_role text)
RETURNS boolean AS $$
DECLARE
    token text;
    payload json;
    roles json;
    role text;
BEGIN
    -- Получаем токен
    token := current_setting('jwt.token', true);
    
    IF token IS NULL THEN
        RETURN false;
    END IF;
    
    -- Проверяем токен
    payload := verify_jwt_token(token);
    
    -- Получаем роли из токена
    roles := payload->'realm_access'->'roles';
    
    -- Проверяем наличие требуемой роли
    FOR role IN SELECT json_array_elements_text(roles)
    LOOP
        IF role = required_role THEN
            RETURN true;
        END IF;
    END LOOP;
    
    RETURN false;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Создаем пользователей для Keycloak
DO $$
BEGIN
    -- Создаем пользователя admin если не существует
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'keycloak_admin') THEN
        CREATE ROLE keycloak_admin LOGIN PASSWORD 'keycloak_admin_password';
    END IF;
    
    -- Создаем пользователя user если не существует
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'keycloak_user') THEN
        CREATE ROLE keycloak_user LOGIN PASSWORD 'keycloak_user_password';
    END IF;
    
    -- Создаем роль для администраторов
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'admin_role') THEN
        CREATE ROLE admin_role;
    END IF;
    
    -- Создаем роль для обычных пользователей
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'user_role') THEN
        CREATE ROLE user_role;
    END IF;
    
    -- Назначаем роли пользователям
    GRANT admin_role TO keycloak_admin;
    GRANT user_role TO keycloak_user;
    
    -- Даем права на базу данных
    GRANT CONNECT ON DATABASE norms_db TO keycloak_admin, keycloak_user;
    GRANT USAGE ON SCHEMA public TO keycloak_admin, keycloak_user;
    
    -- Даем права на таблицы
    GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO admin_role;
    GRANT SELECT ON ALL TABLES IN SCHEMA public TO user_role;
    
    -- Даем права на последовательности
    GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO admin_role;
    GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO user_role;
END
$$;

-- Создаем политики безопасности
CREATE POLICY admin_policy ON uploaded_documents
    FOR ALL TO admin_role USING (true);

CREATE POLICY user_policy ON uploaded_documents
    FOR SELECT TO user_role USING (true);

-- Включаем RLS на таблицах
ALTER TABLE uploaded_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE checkable_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE extracted_elements ENABLE ROW LEVEL SECURITY;
ALTER TABLE checkable_elements ENABLE ROW LEVEL SECURITY;
ALTER TABLE norm_control_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE review_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE findings ENABLE ROW LEVEL SECURITY;
ALTER TABLE system_settings ENABLE ROW LEVEL SECURITY;

-- Создаем функцию для получения текущего пользователя
CREATE OR REPLACE FUNCTION current_user_from_jwt()
RETURNS text AS $$
BEGIN
    RETURN get_user_from_jwt();
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Логируем успешную настройку
SELECT 'Keycloak authentication configured successfully' as status;
