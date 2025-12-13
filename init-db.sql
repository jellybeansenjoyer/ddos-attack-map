-- PostgreSQL Initialization Script
-- This runs automatically when the container first starts

-- Create the application user (only if doesn't exist)
DO
$$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_roles WHERE rolname = 'dos_user'
   ) THEN
      CREATE USER dos_user WITH PASSWORD 'dos_password';
   END IF;
END
$$;

-- Create the database (only if doesn't exist)
SELECT 'CREATE DATABASE dos_attack_map OWNER dos_user'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'dos_attack_map')\gexec

-- Grant all privileges
GRANT ALL PRIVILEGES ON DATABASE dos_attack_map TO dos_user;

-- Connect to the new database
\c dos_attack_map

-- Grant schema privileges
GRANT ALL PRIVILEGES ON SCHEMA public TO dos_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO dos_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO dos_user;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO dos_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO dos_user;
