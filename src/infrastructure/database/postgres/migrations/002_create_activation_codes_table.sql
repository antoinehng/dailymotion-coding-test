-- Migration: Create activation_codes table

CREATE TABLE IF NOT EXISTS activation_codes (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id),
    code VARCHAR(4) NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
    UNIQUE(user_id, code)
);

CREATE INDEX IF NOT EXISTS idx_activation_codes_user_id ON activation_codes(user_id);
CREATE INDEX IF NOT EXISTS idx_activation_codes_user_id_code ON activation_codes(user_id, code);
