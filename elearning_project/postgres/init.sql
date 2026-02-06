CREATE USER IF NOT EXISTS elearning_backup WITH PASSWORD 'chisekele';
ALTER USER elearning_backup SET default_transaction_read_only = on;

-- Grant permissions
GRANT CONNECT ON DATABASE elearning TO elearning_backup;
GRANT USAGE ON SCHEMA public TO elearning_backup;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO elearning_backup;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO elearning_backup;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";