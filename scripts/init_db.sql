-- MySQL 会话数据库初始化脚本
-- 使用方法：mysql -u root -p < scripts/init_db.sql

-- 创建数据库
CREATE DATABASE IF NOT EXISTS qrc_session
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE qrc_session;

-- sessions 表
CREATE TABLE IF NOT EXISTS sessions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    user_id VARCHAR(100) NOT NULL,
    channel_id VARCHAR(100) NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    expires_at DATETIME NOT NULL,
    summary TEXT,
    INDEX idx_user_id (user_id),
    INDEX idx_channel_id (channel_id),
    INDEX idx_expires_at (expires_at),
    INDEX idx_user_channel (user_id, channel_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- turns 表
CREATE TABLE IF NOT EXISTS turns (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    turn_id VARCHAR(255) UNIQUE NOT NULL,
    session_id VARCHAR(255) NOT NULL,
    agent_name VARCHAR(100) NOT NULL,
    messages TEXT NOT NULL,
    final_reply TEXT,
    created_at DATETIME NOT NULL,
    is_compressed BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE,
    INDEX idx_session_id (session_id),
    INDEX idx_turn_id (turn_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SELECT 'Database initialized successfully!' AS status;
