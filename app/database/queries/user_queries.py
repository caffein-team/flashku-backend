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

UPDATE_USER_PROFILE = """
UPDATE users
SET name = COALESCE(%(name)s, name),
    username = COALESCE(%(username)s, username),
    updated_at = CURRENT_TIMESTAMP
WHERE id = %(id)s
RETURNING id, name, email, username, password, avatar, level, is_active, is_verified, created_at, updated_at;
"""

UPDATE_USER_AVATAR = """
UPDATE users
SET avatar = %(avatar)s,
    updated_at = CURRENT_TIMESTAMP
WHERE id = %(id)s
RETURNING id, name, email, username, password, avatar, level, is_active, is_verified, created_at, updated_at;
"""

CHECK_USERNAME_TAKEN = """
SELECT 1 FROM users WHERE username = %(username)s AND id != %(id)s LIMIT 1;
"""

UPDATE_USER_PASSWORD = """
UPDATE users
SET password = %(password)s,
    updated_at = CURRENT_TIMESTAMP
WHERE id = %(id)s;
"""

DELETE_USER = """
DELETE FROM users
WHERE id = %(id)s;
"""

CREATE_PASSWORD_RESET_OTPS_TABLE = """
CREATE TABLE IF NOT EXISTS password_reset_otps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    otp_code VARCHAR(6) NOT NULL,
    is_used BOOLEAN DEFAULT FALSE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_password_reset_user ON password_reset_otps(user_id, otp_code, is_used);
"""

CREATE_REVOKED_TOKENS_TABLE = """
CREATE TABLE IF NOT EXISTS revoked_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    token_jti VARCHAR(255) NOT NULL UNIQUE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_revoked_tokens_jti ON revoked_tokens(token_jti);
"""

INSERT_PASSWORD_RESET_OTP = """
INSERT INTO password_reset_otps (user_id, otp_code, expires_at)
VALUES (%(user_id)s, %(otp_code)s, %(expires_at)s)
RETURNING id, otp_code, expires_at;
"""

INVALIDATE_PREVIOUS_OTPS = """
UPDATE password_reset_otps
SET is_used = TRUE
WHERE user_id = %(user_id)s AND is_used = FALSE;
"""

GET_VALID_OTP = """
SELECT id, user_id, otp_code, is_used, expires_at
FROM password_reset_otps
WHERE user_id = %(user_id)s
  AND otp_code = %(otp_code)s
  AND is_used = FALSE
  AND expires_at > CURRENT_TIMESTAMP
ORDER BY created_at DESC
LIMIT 1;
"""

MARK_OTP_USED = """
UPDATE password_reset_otps
SET is_used = TRUE
WHERE id = %(id)s;
"""

REVOKE_TOKEN = """
INSERT INTO revoked_tokens (token_jti, user_id, expires_at)
VALUES (%(token_jti)s, %(user_id)s, %(expires_at)s)
ON CONFLICT (token_jti) DO NOTHING;
"""

IS_TOKEN_REVOKED = """
SELECT 1 FROM revoked_tokens
WHERE token_jti = %(token_jti)s LIMIT 1;
"""
