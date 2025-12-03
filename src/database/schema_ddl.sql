-- src/database/schema_ddl.sql
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    signup_date DATE NOT NULL,
    country VARCHAR(100),
    acquisition_channel VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);