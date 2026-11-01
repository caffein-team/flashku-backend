CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    avatar VARCHAR(500) NULL,
    level INT DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_USER = """
INSERT INTO users (name, email, username, password, avatar)
VALUES (%(name)s, %(email)s, %(username)s, %(password)s, %(avatar)s)
RETURNING id, name, email, username, password, avatar, level, is_active, is_verified, created_at, updated_at;
"""

GET_USER_BY_ID = """
SELECT id, name, email, username, password, avatar, level, is_active, is_verified, created_at, updated_at
FROM users
WHERE id = %(id)s;
"""

GET_USER_BY_EMAIL = """
SELECT id, name, email, username, password, avatar, level, is_active, is_verified, created_at, updated_at
FROM users
WHERE email = %(email)s;
"""

GET_USER_BY_USERNAME = """
SELECT id, name, email, username, password, avatar, level, is_active, is_verified, created_at, updated_at
FROM users
WHERE username = %(username)s;
"""

GET_USER_BY_EMAIL_OR_USERNAME = """
SELECT id, name, email, username, password, avatar, level, is_active, is_verified, created_at, updated_at
FROM users
WHERE email = %(identifier)s OR username = %(identifier)s;
"""
