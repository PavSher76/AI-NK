-- Настройка логирования PostgreSQL для отладки подключений
-- Этот скрипт выполняется после инициализации базы данных

-- Включаем логирование всех запросов
ALTER SYSTEM SET log_statement = 'all';

-- Настраиваем префикс строк логов с IP-адресом клиента
ALTER SYSTEM SET log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h ';

-- Логируем все запросы независимо от времени выполнения
ALTER SYSTEM SET log_min_duration_statement = 0;

-- Включаем логирование подключений и отключений
ALTER SYSTEM SET log_connections = on;
ALTER SYSTEM SET log_disconnections = on;

-- Включаем логирование времени выполнения запросов
ALTER SYSTEM SET log_duration = on;

-- Включаем логирование ожиданий блокировок
ALTER SYSTEM SET log_lock_waits = on;

-- Включаем логирование временных файлов
ALTER SYSTEM SET log_temp_files = 0;

-- Включаем логирование контрольных точек
ALTER SYSTEM SET log_checkpoints = on;

-- Включаем логирование автовакуума
ALTER SYSTEM SET log_autovacuum_min_duration = 0;

-- Перезагружаем конфигурацию
SELECT pg_reload_conf();
