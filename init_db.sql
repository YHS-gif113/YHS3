-- 创建用户表
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id TEXT UNIQUE NOT NULL, -- 学（工）号，唯一
    name TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('student', 'teacher', 'admin')),
    department TEXT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT DEFAULT 'self_register'
);
 
-- 创建证书信息表
CREATE TABLE certificates (
    cert_id INTEGER PRIMARY KEY AUTOINCREMENT,
    submitter_id INTEGER NOT NULL,
    submitter_role TEXT NOT NULL CHECK(submitter_role IN ('student', 'teacher')),
    student_id TEXT NOT NULL, -- 13位学号
    student_name TEXT NOT NULL,
    department TEXT,
    competition_name TEXT,
    award_category TEXT,
    award_level TEXT,
    competition_type TEXT,
    organizer TEXT,
    award_date TEXT,
    advisor TEXT,
    file_path TEXT,
    extraction_method TEXT,
    extraction_confidence REAL,
    status TEXT DEFAULT 'draft' CHECK(status IN ('draft', 'submitted')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    submitted_at TIMESTAMP
);
 
-- 创建文件表
CREATE TABLE files (
    file_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_size INTEGER,
    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
 
-- 创建系统配置表
CREATE TABLE system_config (
    config_id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_key TEXT UNIQUE NOT NULL,
    config_value TEXT,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by INTEGER
);