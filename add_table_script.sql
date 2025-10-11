-- SQL-скрипт для создания таблицы profiles

CREATE TABLE IF NOT EXISTS profiles (
    -- 1. ID (Персональный ключ пользователя)
    id BIGSERIAL PRIMARY KEY,

    -- 2. Email (Основной уникальный идентификатор)
    email VARCHAR(255) UNIQUE NOT NULL,

    -- 3. Pass (Хеш пароля)
    -- VARCHAR(255) достаточно для большинства современных хешей (напр., bcrypt)
    password_hash VARCHAR(255) NOT NULL,

    -- 4. isConfirmed (Статус подтверждения email)
    is_confirmed BOOLEAN NOT NULL DEFAULT FALSE,

    -- 5. request_history (Хранит json ответы)
    -- JSONB лучше, чем JSON, для индексации и производительности запросов
    request_history JSONB
);

-- Дополнительные комментарии для документации
COMMENT ON TABLE profiles IS 'Персональные данные пользователей, включая хеш пароля, статус подтверждения и историю запросов для персонализации.';
COMMENT ON COLUMN profiles.email IS 'Уникальный email пользователя, используемый как логин.';
COMMENT ON COLUMN profiles.password_hash IS 'Хеш пароля пользователя (рекомендуется bcrypt или Argon2).';
COMMENT ON COLUMN profiles.request_history IS 'История запросов и ответов, полученных пользователем, в формате JSONB.';

-- Рекомендация: Индекс для быстрого поиска по подтвержденным/неподтвержденным пользователям
CREATE INDEX idx_profiles_is_confirmed ON profiles (is_confirmed);