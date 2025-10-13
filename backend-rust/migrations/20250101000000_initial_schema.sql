-- Initial schema migration
-- Create users table
CREATE TABLE IF NOT EXISTS user (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    role VARCHAR(255) NOT NULL,
    profile_image_url TEXT NOT NULL,
    timestamp BIGINT NOT NULL,
    api_key VARCHAR(255),
    settings TEXT,
    info TEXT,
    oauth_sub VARCHAR(255),
    last_active_at BIGINT
);

-- Create auth table
CREATE TABLE IF NOT EXISTS auth (
    id VARCHAR(255) PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    password TEXT NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at BIGINT NOT NULL
);

-- Create chat table
CREATE TABLE IF NOT EXISTS chat (
    id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    title TEXT NOT NULL,
    chat TEXT NOT NULL,
    created_at BIGINT NOT NULL,
    updated_at BIGINT NOT NULL,
    share_id VARCHAR(255),
    archived BOOLEAN DEFAULT FALSE,
    pinned BOOLEAN DEFAULT FALSE,
    meta TEXT,
    folder_id VARCHAR(255)
);

-- Create message table  
CREATE TABLE IF NOT EXISTS message (
    id VARCHAR(255) PRIMARY KEY,
    chat_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    role VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    created_at BIGINT NOT NULL,
    updated_at BIGINT NOT NULL,
    model VARCHAR(255),
    parent_id VARCHAR(255),
    tool_calls TEXT,
    tool_call_id VARCHAR(255)
);

-- Create model table
CREATE TABLE IF NOT EXISTS model (
    id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    base_model_id VARCHAR(255),
    name VARCHAR(255) NOT NULL,
    params TEXT,
    meta TEXT,
    created_at BIGINT NOT NULL,
    updated_at BIGINT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    access_control TEXT
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_user_email ON user(email);
CREATE INDEX IF NOT EXISTS idx_auth_email ON auth(email);
CREATE INDEX IF NOT EXISTS idx_chat_user_id ON chat(user_id);
CREATE INDEX IF NOT EXISTS idx_message_chat_id ON message(chat_id);
CREATE INDEX IF NOT EXISTS idx_model_user_id ON model(user_id);
